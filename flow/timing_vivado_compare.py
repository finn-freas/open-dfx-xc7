import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ofx import timing

XT2 = ("x_gen_none", "x_mmcm_none", "x_iodly", "rv_soc", "rv_mul", "rv_soc_hb", "rv_mul_hb")
XT3 = ("x_cdc_none", "x_cdc_groups", "x_cdc_fpclk", "x_cdc_maxdly", "x_async_rtl", "x_async_none", "x_iodly_minmax",
       "x_mmcm_groups", "x_gen_div", "x_iodly_partial")

CONFIG = {
    "vivado": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "out": ROOT / "build" / "timing_rv" / "compare.json",
    "designs": {
        **{n: (f"build/timing_rv/{n}/timrep_paths", f"timing_xtime2/{n}_tr_placed") for n in XT2},
        "dfx_rv_pr_xor_n": ("build/timing/dfx_rv_pr/rel01tr_p10/rel01tr/xor_n",
                            "timing_xtime2/dfx_rv_pr_xor_n_tr_placed"),
        **{n: (f"build/timing_rv/{n}/timrep_paths", f"timing_xtime3/{n}_tr_placed") for n in XT3},
        "x_gen_none_own": ("build/timing/x_gen_none/timrep_paths", "xdc/x_gen_none"),
        "x_mmcm_none_own": ("build/timing/x_mmcm_none/timrep_paths", "xdc/x_mmcm_none"),
        "x_iodly_own": ("build/timing/x_iodly/timrep_paths", "xdc/x_iodly"),
    },
    "top": (1, 10, 100),
    "classes": (("FF", r"^FD|^SLICE_FFX$"), ("LUTRAM", r"^RAM(32|64|128|256|D|S)|^SLICE_LUTX$"),
                ("BRAM", r"^RAMB"), ("DSP", r"^DSP"), ("ICAP", r"^ICAP"), ("SRL", r"^SRL"),
                ("port", r"^port$|^IOB")),
    "pulse_labels": {"Min Period": "min_period", "Max Period": "max_period", "Low Pulse Width": "low",
                     "High Pulse Width": "high"},
    "pulse_reports": ("pulse_width_all.rpt", "pulse_width.rpt", "timing.rpt", "timing_full.rpt"),
    "pin_alias": {"BUFG/I": "BUFGCTRL/I0"},
}


def classify(ref):
    return next((name for name, rx in CONFIG["classes"] if re.search(rx, ref)), ref)


def norm(p):
    return p.replace("[", "").replace("]", "")


def num(x):
    return None if x in ("", "-", "NA", "inf") else float(x)


def vivado_endpoints(d, kind):
    f = d / f"endpoints_{kind}.txt"
    if not f.exists():
        return None
    out = {}
    for ln in f.read_text(errors="replace").splitlines():
        m = re.match(r"(\S*) (\S+) (\S+) (\S+) \{(.*?)\} \{(.*?)\}$", ln)
        if not m:
            continue
        slack = num(m.group(1))
        key = norm(m.group(3))
        if key in out and (out[key]["slack"] is None or slack is None or out[key]["slack"] <= slack):
            continue
        out[key] = {"class": classify(m.group(2)), "slack": slack, "start_clock": m.group(5),
                    "end_clock": m.group(6)}
    return out


def class_counts(eps):
    c = defaultdict(int)
    for e in eps.values():
        c[e["class"]] += 1
    return dict(sorted(c.items()))


def section(text, title):
    m = re.search(rf"\|\s*{re.escape(title)}\s*\n\|\s*-+\s*\n-+\n(.*?)(?=\n-{{20,}}\n\||\Z)", text, re.S)
    return m.group(1) if m else ""


def first_path(text):
    m = re.search(r"^Slack \(\w+\) :\s+(-?[\d.]+)ns.*?(?=^Slack \(|\Z)", text, re.S | re.M)
    if not m:
        return None
    b = m.group(0)
    g = lambda rx: (re.search(rx, b, re.M) or [None, None])[1]
    dp = re.search(r"Data Path Delay:\s+(-?[\d.]+)ns\s+\(logic (-?[\d.]+)ns.*?route (-?[\d.]+)ns", b)
    return {"slack": float(m.group(1)), "source": g(r"^\s+Source:\s+(\S+)"), "destination": g(r"^\s+Destination:\s+(\S+)"),
            "requirement": float(g(r"Requirement:\s+(-?[\d.]+)ns")), "data_path": float(dp.group(1)),
            "logic": float(dp.group(2)), "route": float(dp.group(3)), "levels": int(g(r"Logic Levels:\s+(\d+)"))}


def split_cols(ln):
    return [c for c in re.split(r"\s{2,}", ln.strip()) if c != ""]


def pulse_rows(text):
    out, clock = [], None
    for ln in text.splitlines():
        m = re.match(r"^Clock Name:\s+(\S+)", ln)
        if m:
            clock = m.group(1)
            continue
        m = re.match(r"^(Min Period|Max Period|Low Pulse Width|High Pulse Width)\s+(\S+)\s+(\S+)\s+(\S+)\s+"
                     r"(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\S+)\s+(\S+)", ln)
        if m and clock:
            out.append({"clock": clock, "check": m.group(1), "lib_pin": m.group(3), "required": float(m.group(5)),
                        "actual": float(m.group(6)), "slack": float(m.group(7)), "pin": m.group(9)})
    return out


def vivado(d):
    text = (d / "timing.rpt").read_text(errors="replace")
    out = {"check_timing": {k: int(n) for k, n in re.findall(r"^\d+\. checking (\w+) \((\d+)\)", text, re.M)}}
    body = section(text, "Design Timing Summary").splitlines()
    nums = next((ln.split() for ln in body if re.match(r"^\s*-?\d", ln)), [])
    if len(nums) >= 8:
        out["summary"] = {"setup": [num(nums[0]), num(nums[1]), int(nums[2]), int(nums[3])],
                          "hold": [num(nums[4]), num(nums[5]), int(nums[6]), int(nums[7])]}
        if len(nums) >= 12:
            out["summary"]["pw"] = [num(nums[8]), num(nums[9]), int(nums[10]), int(nums[11])]
    for title, key, nclk in (("Intra Clock Table", "intra", 1), ("Inter Clock Table", "inter", 2)):
        rows = {}
        for ln in section(text, title).splitlines():
            parts = ln.split()
            if not parts or parts[0].startswith("-") or parts[0] in ("Clock", "From"):
                continue
            try:
                vals = [float(x) for x in parts[nclk:]]
            except ValueError:
                continue
            name = " -> ".join(parts[:nclk])
            if len(vals) >= 8:
                rows[name] = {"setup": vals[0:4], "hold": vals[4:8]}
                if len(vals) >= 12:
                    rows[name]["pw"] = vals[8:12]
            elif len(vals) == 4 and key == "intra":
                rows[name] = {"pw": vals}
        out[key] = rows
    out["clocks"] = sorted(re.findall(r"^\s*(\S+)\s+\{[\d. ]+\}\s+[\d.]+\s+[\d.]+\s*$",
                                      section(text, "Clock Summary"), re.M))
    out["endpoints"] = {k: vivado_endpoints(d, k) for k in ("setup", "hold")}
    paths = d / "paths.rpt"
    out["worst_path"] = first_path(paths.read_text(errors="replace")) if paths.exists() else None
    wp = d / "worst_paths.txt"
    out["worst_endpoints"] = []
    if wp.exists():
        seen = set()
        for ln in wp.read_text().splitlines():
            s, _, rest = ln.partition(" ")
            end = norm(rest.rsplit(" ", 1)[-1])
            if end not in seen and num(s) is not None:
                seen.add(end)
                out["worst_endpoints"].append([end, float(s)])
    pv = d / "paths_vivado.txt"
    out["same_pairs"] = []
    if pv.exists():
        for ln in pv.read_text().splitlines():
            m = re.match(r"(\S+) (\S*) (\S*) (\S*) (\S*) \{(.*)\}$", ln)
            if not m:
                continue
            out["same_pairs"].append({"nextpnr_slack": float(m.group(1)), "vivado_slack": num(m.group(2)),
                                      "vivado_data_path": num(m.group(3)), "pair": m.group(6)})
    ci = d / "clock_interaction.rpt"
    out["interaction"] = {}
    if ci.exists():
        for ln in ci.read_text(errors="replace").splitlines():
            m = re.match(r"^(\S+)\s+(\S+)\s+((?:rise|fall) - (?:rise|fall))\s+(.*)$", ln)
            if not m:
                continue
            cols = split_cols(m.group(4))
            out["interaction"][f"{m.group(1)} -> {m.group(2)}"] = {"edges": m.group(3), "cols": cols,
                                                                    "constraints": cols[-1] if cols else None}
    cdc = d / "cdc.rpt"
    out["cdc"] = {}
    if cdc.exists():
        for ln in cdc.read_text(errors="replace").splitlines():
            cols = split_cols(ln)
            if len(cols) >= 10 and cols[0] in ("Info", "Warning", "Critical", "Error"):
                out["cdc"][f"{cols[1]} -> {cols[2]}"] = {"severity": cols[0], "type": cols[3], "exceptions": cols[4],
                                                         "endpoints": int(cols[5]), "safe": int(cols[6]),
                                                         "unsafe": int(cols[7]), "unknown": int(cols[8]),
                                                         "no_async_reg": int(cols[9])}
    pw = d / "pulse_width.rpt"
    out["pulse"] = {}
    if pw.exists():
        for r in pulse_rows(pw.read_text(errors="replace")):
            c = out["pulse"].setdefault(r["clock"], {})
            c[r["check"]] = [r["lib_pin"], r["required"], r["slack"]]
    full = d / "timing_full.rpt"
    out["details_groups"] = []
    if full.exists():
        t = full.read_text(errors="replace")
        out["details_groups"] = [f"{a} -> {b}" for a, b in
                                 re.findall(r"^From Clock:[ \t]+(\S+)\n[ \t]+To Clock:[ \t]+(\S+)", t, re.M)]
    return out


def ours(d):
    dd = ROOT / d
    rep, _ = timing.load(dd)
    names = timing.clock_names(rep)
    eps = rep["endpoints"]
    timed = timing.timed_checks(eps, rep, names)
    s = timing.summary_row(timed)
    pw, clocks = timing.pulse_width(dd, rep)
    pw = pw or []
    pack = lambda r: {k: [r[k]["wns"], r[k]["tns"], r[k]["failing"], r[k]["total"]] for k in ("setup", "hold")}
    pwpack = lambda r: [r["wns"], r["tns"], r["failing"], r["total"]]
    by_pair = defaultdict(list)
    for e in timed:
        by_pair[(timing.event_clock(e["from"], names), timing.event_clock(e["to"], names))].append(e)
    pw_by = defaultdict(list)
    for c in pw:
        pw_by[c["clock"]].append(c)
    checks = {name: n for name, n, _, _ in timing.check_timing(dd, rep, eps, names)}
    pads = timing.pad_cells(dd)
    nl = timing.netlist(str(dd))
    ename = {timing.pin(e): timing.endpoint_name(e, pads, nl) for e in eps}
    worst = sorted(((ename[k], v) for k, v in timing.worst_per_pin([e for e in timed if "setup" in e], "setup").items()),
                   key=lambda kv: kv[1])
    typ = {timing.pin(e): e.get("type", "") for e in timed}
    endpoints = {}
    for kind in ("setup", "hold"):
        w = timing.worst_per_pin([e for e in timed if kind in e], kind)
        endpoints[kind] = {norm(ename[p]): {"class": classify(typ[p]), "slack": v} for p, v in w.items()}
    paths = sorted((p for p in rep.get("paths", []) if p["check"] == "setup"
                    and not timing.on_unconstrained_clock(p, rep, names)), key=lambda p: p["slack"])
    wpath = None
    if paths:
        p = paths[0]
        logic, route, levels = timing.path_stats(p)
        st = timing.path_start(p)
        wpath = {"slack": p["slack"], "source": f"{st['cell']}/{st['port']}",
                 "destination": timing.endpoint_name(p["endpoint"], pads, nl), "requirement": p["requirement"],
                 "data_path": logic + route, "logic": logic, "route": route, "levels": levels}
    intra = {}
    for a in sorted(set(clocks) | {a for a, b in by_pair if a == b}):
        row = pack(timing.summary_row(by_pair[(a, a)])) if by_pair.get((a, a)) else {}
        if pw_by.get(a):
            row["pw"] = pwpack(timing.pw_summary(pw_by[a]))
        if row:
            intra[a] = row
    inter_rows = timing.interaction(dd, rep, eps, names)
    order = [r[0].strip() for r in timing.clock_tree_rows(clocks, set())]
    keys = timing.path_groups(timed, names, order)[0]
    groups = ([f"{c} -> {c}" for c in order if (c, c) in by_pair or pw_by.get(c)]
              + [f"{a} -> {b}" for a, b in keys if a != b])
    pulse = {}
    for c in pw:
        k = pulse.setdefault(c["clock"], {})
        if c["check"] not in k or c["slack"] < k[c["check"]][2]:
            k[c["check"]] = [c["lib_pin"], c["required"], c["slack"]]
    return {"check_timing": checks, "summary": {**pack(s), "pw": pwpack(timing.pw_summary(pw))},
            "clocks": sorted(clocks), "endpoints": endpoints, "intra": intra,
            "inter": {f"{a} -> {b}": pack(timing.summary_row(v)) for (a, b), v in by_pair.items() if a != b},
            "interaction": {f"{r['from']} -> {r['to']}": {"edges": r["edges"], "constraints": r["constraints"],
                                                          "total": r["total"], "wns": r["wns"]} for r in inter_rows},
            "cdc": {f"{r[1]} -> {r[2]}": {"severity": r[0], "type": r[3], "exceptions": r[4], "endpoints": r[5],
                                          "safe": r[6], "unsafe": r[7], "unknown": r[8]}
                    for r in timing.cdc_rows(dd, inter_rows)},
            "pulse": pulse, "worst_path": wpath, "worst_endpoints": [[norm(k), v] for k, v in worst],
            "details_groups": groups}


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    if len(xs) < 3:
        return None
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return round(cov / (vx * vy), 4) if vx and vy else None


def endpoint_diff(n, v):
    out = {}
    for kind in ("setup", "hold"):
        a, b = n["endpoints"][kind], v["endpoints"][kind]
        if b is None:
            continue
        b = {k: x for k, x in b.items() if x["slack"] is not None}
        common = sorted(set(a) & set(b))
        only_n = sorted(set(a) - set(b))
        only_v = sorted(set(b) - set(a))
        d = [a[k]["slack"] - b[k]["slack"] for k in common]
        out[kind] = {"nextpnr_total": len(a), "vivado_total": len(b), "common": len(common),
                     "nextpnr_classes": class_counts(a), "vivado_classes": class_counts(b),
                     "only_nextpnr": {"n": len(only_n), "classes": class_counts({k: a[k] for k in only_n}),
                                      "first": only_n[:8]},
                     "only_vivado": {"n": len(only_v), "classes": class_counts({k: b[k] for k in only_v}),
                                     "first": only_v[:8]},
                     "slack_delta_mean": round(sum(d) / len(d), 4) if d else None,
                     "slack_delta_mean_abs": round(sum(abs(x) for x in d) / len(d), 4) if d else None,
                     "slack_delta_max_abs": round(max(abs(x) for x in d), 4) if d else None,
                     "spearman": spearman([a[k]["slack"] for k in common], [b[k]["slack"] for k in common]),
                     "histogram_nextpnr": timing.histogram([a[k]["slack"] for k in a]),
                     "histogram_vivado": timing.histogram([b[k]["slack"] for k in b])}
    return out


def selection(n, v):
    out = {}
    for k in CONFIG["top"]:
        a = {e for e, _ in n["worst_endpoints"][:k]}
        b = {e for e, _ in v["worst_endpoints"][:k]}
        out[f"top{k}_overlap"] = len(a & b) if len(a) == k and len(b) == k else None
    if n["worst_endpoints"]:
        vr = {e: i for i, (e, _) in enumerate(v["worst_endpoints"])}
        out["nextpnr_worst_rank_in_vivado"] = vr.get(n["worst_endpoints"][0][0])
    if v["worst_endpoints"]:
        nr = {e: i for i, (e, _) in enumerate(n["worst_endpoints"])}
        out["vivado_worst_rank_in_nextpnr"] = nr.get(v["worst_endpoints"][0][0])
    out["vivado_endpoints_listed"] = len(v["worst_endpoints"])
    return out


def structure(n, v):
    """Report-structure agreement: check_timing items, endpoint totals, clocks, pulse width, CDC, groups."""
    out = {}
    ct = {}
    for k, vv in v["check_timing"].items():
        ct[k] = {"ofx": n["check_timing"].get(k), "vivado": vv, "equal": n["check_timing"].get(k) == vv}
    out["check_timing"] = ct
    out["check_timing_equal"] = f"{sum(x['equal'] for x in ct.values())}/{len(ct)}"
    sv, sn = v.get("summary", {}), n["summary"]
    out["totals"] = {k: {"ofx": sn[k][3] if k in sn else None, "vivado": sv[k][3] if k in sv else None}
                     for k in ("setup", "hold", "pw")}
    out["wns"] = {k: {"ofx": sn[k][0] if k in sn else None, "vivado": sv[k][0] if k in sv else None}
                  for k in ("setup", "hold", "pw")}
    out["clocks"] = {"ofx": n["clocks"], "vivado": v["clocks"], "equal": n["clocks"] == v["clocks"]}
    pairs = {}
    for key in ("intra", "inter"):
        for p in sorted(set(n[key]) | set(v[key])):
            a, b = n[key].get(p, {}), v[key].get(p, {})
            pairs[f"{key} {p}"] = {k: [a[k][3] if k in a else None, b[k][3] if k in b else None]
                                   for k in ("setup", "hold", "pw") if k in a or k in b}
    out["pair_totals_ofx_vs_vivado"] = pairs
    out["interaction"] = {p: {"ofx": n["interaction"].get(p, {}).get("constraints"),
                              "vivado": v["interaction"].get(p, {}).get("constraints")}
                          for p in sorted(set(n["interaction"]) | set(v["interaction"]))}
    out["cdc"] = {p: {"ofx": n["cdc"].get(p), "vivado": v["cdc"].get(p)}
                  for p in sorted(set(n["cdc"]) | set(v["cdc"]))}
    pw = {}
    for c in sorted(set(n["pulse"]) | set(v["pulse"])):
        a, b = n["pulse"].get(c, {}), v["pulse"].get(c, {})
        pw[c] = {chk: {"ofx": a.get(chk), "vivado": b.get(chk)} for chk in sorted(set(a) | set(b))}
    out["pulse"] = pw
    out["details_groups"] = {"ofx": n["details_groups"], "vivado": v["details_groups"]}
    return out


def pulse_table():
    """Every lib pin Vivado reported a pulse width requirement for (speed -1), against ofx CONFIG pulse_width."""
    seen = defaultdict(dict)
    for f in sorted(CONFIG["vivado"].glob("*/*/*.rpt")):
        if f.name not in CONFIG["pulse_reports"]:
            continue
        txt = f.read_text(errors="replace")
        if not re.search(r"Speed File\s+:\s+-1\s", txt):
            continue
        for r in pulse_rows(txt):
            seen[r["lib_pin"]].setdefault(CONFIG["pulse_labels"][r["check"]], set()).add(r["required"])
    have = timing.CONFIG["pulse_width"]
    res = {}
    for lp, checks in sorted(seen.items()):
        mine = have.get(lp) or have.get(CONFIG["pin_alias"].get(lp, ""), {})
        res[lp] = {k: {"vivado": sorted(vs), "ofx": mine.get(k)} for k, vs in checks.items()}
        res[lp]["status"] = ("missing" if not mine else "ok" if all(
            mine.get(k) is not None and len(vs) == 1 and abs(mine[k] - min(vs)) < 1e-6 for k, vs in checks.items())
            else "differs")
    return res


def main():
    ap = argparse.ArgumentParser(description="ofx timing (nextpnr --report-paths) against Vivado report_timing_summary, "
                                             "report_timing, check_timing, report_clock_interaction, report_cdc, "
                                             "report_pulse_width and get_timing_paths")
    ap.add_argument("--designs", nargs="+", default=list(CONFIG["designs"]))
    ap.add_argument("--pulse-table", action="store_true", help="only check the pulse width table")
    a = ap.parse_args()
    if a.pulse_table:
        res = pulse_table()
        for k, v in res.items():
            print(k, json.dumps(v))
        (CONFIG["out"].parent / "pulse_table.json").write_text(json.dumps(res, indent=1) + "\n")
        return
    res = {}
    for name in a.designs:
        d, rel = CONFIG["designs"][name]
        vd = CONFIG["vivado"] / rel
        if not (vd / "timing.rpt").exists() or not (ROOT / d / "report.json").exists():
            print(f"{name}: missing {vd / 'timing.rpt'} or {ROOT / d / 'report.json'}")
            continue
        n, v = ours(d), vivado(vd)
        res[name] = {"files": {"nextpnr": d, "vivado": str(vd)},
                     "timers": "ofx: nextpnr timer (one corner); Vivado: Vivado 2025.2 timer (slow and fast corners)",
                     "nextpnr": n, "vivado": v, "selection": selection(n, v),
                     "endpoint_diff": endpoint_diff(n, v), "structure": structure(n, v)}
        st = res[name]["structure"]
        print(f"== {name}  (nextpnr {d} | Vivado {vd})")
        print(f"  check_timing equal {st['check_timing_equal']}: "
              + ", ".join(f"{k} {x['ofx']}/{x['vivado']}" for k, x in st["check_timing"].items() if not x["equal"]))
        print(f"  totals {json.dumps(st['totals'])}")
        print(f"  wns    {json.dumps(st['wns'])}")
        print(f"  clocks {json.dumps(st['clocks'])}")
        print(f"  pairs  {json.dumps(st['pair_totals_ofx_vs_vivado'])}")
        print(f"  interaction {json.dumps(st['interaction'])}")
        print(f"  cdc {json.dumps(st['cdc'])}")
        print(f"  groups {json.dumps(st['details_groups'])}")
        print(f"  selection: {json.dumps(res[name]['selection'])}")
        for kind, dd in res[name]["endpoint_diff"].items():
            short = {k: dd[k] for k in ("nextpnr_total", "vivado_total", "common", "slack_delta_mean",
                                         "slack_delta_mean_abs", "slack_delta_max_abs", "spearman")}
            short["only_nextpnr"] = dd["only_nextpnr"]["classes"]
            short["only_vivado"] = dd["only_vivado"]["classes"]
            print(f"  endpoints {kind}: {json.dumps(short)}")
    CONFIG["out"].write_text(json.dumps(res, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
