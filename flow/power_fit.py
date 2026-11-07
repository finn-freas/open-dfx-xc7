import argparse
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ofx import design as D
from ofx import power as P

CONFIG = {
    "dry_run": True,
    "viv": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "viv_tags": ("drcpow", "drcpow2"),
    "cache": ROOT / "build" / "power" / "features",
    "out_model": ROOT / "ofx" / "power_model.json",
    "out_md": ROOT / "build" / "power" / "fit.md",
    "heldout": ("fir_p5", "fir_p10", "rv_mul_p5", "rv_mul_p10", "arty_eth", "mmcme2_adv", "ramb36e1", "dsp_cascade",
                "oserdes", "drc_pll_vco", "drc_gated", "srl"),
    "less_than": 0.0005,
    "row_re": re.compile(r"^\|\s*(\S.*?)\s*\|\s*(<?[\d.]+)\s*\|", re.M),
    "supply_re": re.compile(r"^\|\s*(Vcc\w+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|", re.M),
    "summary_keys": {"Total On-Chip Power (W)": "total", "Dynamic (W)": "dynamic", "Device Static (W)": "static",
                     "Effective TJA (C/W)": "theta_ja", "Junction Temperature (C)": "tj"},
}


def lstsq(X, y):
    n = len(X[0]) if X else 0
    A = [[sum(r[i] * r[j] for r in X) for j in range(n)] for i in range(n)]
    b = [sum(r[i] * v for r, v in zip(X, y)) for i in range(n)]
    for i in range(n):
        A[i][i] += 1e-12 * (A[i][i] or 1.0)
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(A[r][c]))
        A[c], A[piv], b[c], b[piv] = A[piv], A[c], b[piv], b[c]
        if abs(A[c][c]) < 1e-300:
            continue
        for r in range(n):
            if r != c and A[r][c]:
                f = A[r][c] / A[c][c]
                A[r] = [a - f * x for a, x in zip(A[r], A[c])]
                b[r] -= f * b[c]
    return [b[i] / A[i][i] if abs(A[i][i]) > 1e-300 else 0.0 for i in range(n)]


def nnls(X, y, iters=200):
    n = len(X[0]) if X else 0
    P, x = [], [0.0] * n
    for _ in range(iters):
        r = [v - sum(a * b for a, b in zip(row, x)) for row, v in zip(X, y)]
        w = [sum(row[j] * rv for row, rv in zip(X, r)) for j in range(n)]
        cand = [j for j in range(n) if j not in P and w[j] > 1e-12]
        if not cand:
            break
        P.append(max(cand, key=lambda j: w[j]))
        while True:
            z = [0.0] * n
            for j, v in zip(P, lstsq([[row[j] for j in P] for row in X], y)):
                z[j] = v
            if all(z[j] > 0 for j in P):
                x = z
                break
            alpha = min(x[j] / (x[j] - z[j]) for j in P if z[j] <= 0)
            x = [xi + alpha * (zi - xi) for xi, zi in zip(x, z)]
            P = [j for j in P if x[j] > 1e-15]
            if not P:
                break
    return x


def builds():
    out = {}
    for d in sorted((ROOT / "designs" / "drc").iterdir()):
        out[d.name] = (ROOT / "build" / "drc" / d.name, [d / f"{d.name}.xdc"])
    for d in sorted((ROOT / "designs" / "gap").iterdir()):
        out[d.name] = (ROOT / "build" / "gap" / d.name / "ofx", sorted(d.glob("*.xdc")))
    for d in sorted((ROOT / "build" / "qor" / "src").iterdir()):
        out[d.name] = (ROOT / "build" / "qor" / "oxc7" / "base" / d.name / "s1", sorted(d.glob("*.xdc")))
    out["arty_ddr3"] = (ROOT / "build/ddr3/arty_ddr3/gapfix", sorted((ROOT / "designs/ddr3/arty_ddr3").glob("*.xdc")))
    out["arty_eth"] = (ROOT / "build/eth/arty_eth/gapfix", sorted((ROOT / "designs/eth/arty_eth").glob("*.xdc")))
    return out


def val(s):
    return CONFIG["less_than"] if s.startswith("<") else float(s)


def parse_power(f):
    t = f.read_text(errors="replace")
    rec = {"classes": {}, "sub": {}, "rails": {}}
    sec = t.split("1.1 On-Chip Components", 1)
    head = sec[0]
    for name, v in CONFIG["row_re"].findall(head):
        if name in CONFIG["summary_keys"]:
            rec[CONFIG["summary_keys"][name]] = val(v)
    if len(sec) > 1:
        body = sec[1].split("1.2 Power Supply Summary", 1)[0]
        for line in body.splitlines():
            m = re.match(r"^\|( *)(\S.*?)\s*\|\s*(<?[\d.]+)\s*\|", line)
            if not m:
                continue
            (rec["sub"] if m.group(1).startswith("   ") or len(m.group(1)) > 1 else rec["classes"])[m.group(2)] = val(m.group(3))
    for r, v, tot, dyn, st in CONFIG["supply_re"].findall(t):
        rec["rails"][r] = {"voltage": float(v), "total": float(tot), "dynamic": float(dyn), "static": float(st)}
    return rec


def vivado_power():
    out = {}
    for tag in CONFIG["viv_tags"]:
        for f in sorted((CONFIG["viv"] / tag).glob("*/power.rpt")):
            out[f.parent.name] = parse_power(f)
    return out


def feats(name, build, xdcs, dry):
    c = CONFIG["cache"] / f"{name}.json"
    if c.exists():
        return json.loads(c.read_text())
    np_ = D.find_netlist(build) if build.exists() else None
    if np_ is None or dry:
        return None
    f = P.features(np_, [str(x) for x in xdcs])
    if not f["routed"]:
        return None
    c.parent.mkdir(parents=True, exist_ok=True)
    c.write_text(json.dumps(f, indent=1) + "\n")
    return f


def fit_class(rows, k):
    names = P.CONFIG["class_features"][k]
    X = [[r["f"]["features"].get(n, 0.0) for n in names] for r in rows]
    y = [r["v"]["classes"].get(k, 0.0) * 1000.0 for r in rows]
    keep = [j for j in range(len(names)) if any(row[j] for row in X)]
    coef = [0.0] * len(names)
    if keep and any(y):
        scale = [max(row[j] for row in X) for j in keep]
        c = nnls([[row[j] / s for j, s in zip(keep, scale)] for row in X], y)
        for j, s, v in zip(keep, scale, c):
            coef[j] = v / s
    return dict(zip(names, coef))


def fit(rows):
    coef = {k: fit_class(rows, k) for k in P.CONFIG["class_features"]}
    dyn = [r["v"].get("dynamic", 0.0) for r in rows]
    st = [r["v"].get("static", 0.0) for r in rows]
    s = lstsq([[1.0, d] for d in dyn], st)
    share = {}
    classes = list(P.CONFIG["class_features"])
    for rail in list(P.CONFIG["rails"]) + ["Vcco"]:
        if rail.startswith("Vcco") and rail != "Vcco":
            continue
        y = []
        for r in rows:
            if rail == "Vcco":
                y.append(sum(v["dynamic"] * v["voltage"] for n, v in r["v"]["rails"].items() if n.startswith("Vcco")))
            else:
                v = r["v"]["rails"].get(rail)
                y.append(v["dynamic"] * v["voltage"] if v else 0.0)
        X = [[r["v"]["classes"].get(k, 0.0) for k in classes] for r in rows]
        keep = [j for j in range(len(classes)) if any(row[j] for row in X)]
        c = [0.0] * len(classes)
        if keep and any(y):
            for j, v in zip(keep, nnls([[row[j] for j in keep] for row in X], y)):
                c[j] = v
        share[rail] = {k: float(min(v, 1.0)) for k, v in zip(classes, c) if v > 1e-6}
    base = min(rows, key=lambda r: r["v"].get("dynamic", 1.0))
    rail_static = {n: v["static"] * s[0] / max(base["v"].get("static", 1e-9), 1e-9)
                   for n, v in base["v"]["rails"].items()}
    tja = statistics.mean([r["v"].get("theta_ja", 4.6) for r in rows])
    return {"coef": coef, "static": {"s0": s[0], "s1": s[1]}, "rail_share": share,
            "rail_static": rail_static, "theta_ja": tja}


def evaluate(rows, model):
    out = []
    for r in rows:
        e = P.estimate(r["f"], model)
        v = r["v"]
        out.append({"name": r["name"], "viv_total": v.get("total", 0.0), "ofx_total": e["total_w"],
                    "viv_dynamic": v.get("dynamic", 0.0), "ofx_dynamic": e["dynamic_w"],
                    "viv_static": v.get("static", 0.0), "ofx_static": e["static_w"],
                    "classes": {k: (v["classes"].get(k, 0.0), e["classes"][k]) for k in e["classes"]},
                    "rails": {n: (x["total"], e["rails"].get(n, {}).get("total_a", 0.0)) for n, x in v["rails"].items()
                              if x["total"] > 0}})
    return out


def pct(a, b):
    return 100.0 * abs(b - a) / a if a else 0.0


def summary(ev, min_dyn=0.0):
    sel = [e for e in ev if e["viv_dynamic"] >= min_dyn]
    if not sel:
        return {}
    tot = [pct(e["viv_total"], e["ofx_total"]) for e in sel]
    return {"n": len(sel),
            "total_mape": statistics.mean(tot),
            "total_max": max(tot),
            "dynamic_mape": statistics.mean([pct(e["viv_dynamic"], e["ofx_dynamic"]) for e in sel]),
            "dynamic_mae_mw": statistics.mean([1000 * abs(e["viv_dynamic"] - e["ofx_dynamic"]) for e in sel]),
            "static_mape": statistics.mean([pct(e["viv_static"], e["ofx_static"]) for e in sel])}


def markdown(train_ev, test_ev, model):
    def rows(ev):
        out = ["| Design | Vivado total W | ofx total W | err % | Vivado dynamic W | ofx dynamic W | err % | "
               "worst class (Vivado W / ofx W) |", "|---|---|---|---|---|---|---|---|"]
        for e in ev:
            wk = max(e["classes"].items(), key=lambda kv: abs(kv[1][0] - kv[1][1]))
            out.append(f"| {e['name']} | {e['viv_total']:.3f} | {e['ofx_total']:.3f} | "
                       f"{pct(e['viv_total'], e['ofx_total']):.1f} | {e['viv_dynamic']:.3f} | {e['ofx_dynamic']:.3f} | "
                       f"{pct(e['viv_dynamic'], e['ofx_dynamic']):.0f} | {wk[0]} {wk[1][0]:.3f} / {wk[1][1]:.3f} |")
        return out
    s_te, s_tr = summary(test_ev), summary(train_ev)
    s_te10 = summary(test_ev, 0.010)
    md = ["# ofx power fit", "", f"Held-out ({s_te.get('n')}): total {s_te.get('total_mape', 0):.1f} % mean abs error "
          f"(max {s_te.get('total_max', 0):.1f} %), dynamic {s_te.get('dynamic_mape', 0):.0f} % mean abs "
          f"({s_te.get('dynamic_mae_mw', 0):.1f} mW mean abs)",
          f"Held-out with Vivado dynamic >= 10 mW ({s_te10.get('n', 0)}): dynamic "
          f"{s_te10.get('dynamic_mape', 0):.0f} % mean abs",
          f"Training ({s_tr.get('n')}): total {s_tr.get('total_mape', 0):.1f} %, dynamic {s_tr.get('dynamic_mape', 0):.0f} %",
          "", "## Held-out designs", ""] + rows(test_ev) + ["", "## Training designs", ""] + rows(train_ev)
    md += ["", "## Coefficients (mW per feature unit; features are MHz-weighted, see ofx/power.py)", "",
           "```", json.dumps(model["coef"], indent=1), json.dumps(model["static"]), json.dumps(model["rail_share"]), "```"]
    return "\n".join(md) + "\n"


def main():
    ap = argparse.ArgumentParser(description="fit the ofx power model to Vivado report_power and test it on held-out designs")
    ap.add_argument("--run", action="store_true", help="extract missing features and write ofx/power_model.json")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    viv = vivado_power()
    bs = builds()
    rows = []
    for name, v in sorted(viv.items()):
        if name not in bs or "dynamic" not in v:
            continue
        f = feats(name, *bs[name], dry)
        if f is None:
            print(f"skip {name}: no routed open build" + (" (or dry run)" if dry else ""))
            continue
        rows.append({"name": name, "v": v, "f": f})
    train = [r for r in rows if r["name"] not in CONFIG["heldout"]]
    test = [r for r in rows if r["name"] in CONFIG["heldout"]]
    print(f"{len(rows)} designs with Vivado power and an open build: {len(train)} train, {len(test)} held out")
    if not train:
        return
    model = fit(train)
    tr_ev, te_ev = evaluate(train, model), evaluate(test, model)
    model.update({"name": "power_model.json", "train": [r["name"] for r in train], "heldout": [r["name"] for r in test],
                  "heldout_error": summary(te_ev), "train_error": summary(tr_ev),
                  "vivado": "Vivado 2025.2 report_power, vectorless defaults, xc7a35tcsg324-1, 25 C ambient"})
    md = markdown(tr_ev, te_ev, model)
    print(md)
    if dry:
        print("[dry] add --run to write the model")
        return
    CONFIG["out_md"].parent.mkdir(parents=True, exist_ok=True)
    CONFIG["out_md"].write_text(md)
    CONFIG["out_model"].write_text(json.dumps(model, indent=1) + "\n")
    print(f"wrote {CONFIG['out_model']} and {CONFIG['out_md']}")


if __name__ == "__main__":
    main()
