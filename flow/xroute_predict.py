"""Placer delay model against Vivado: nextpnr's pre-route arc prediction (XilinxImpl::predictDelay, the
measured delay matrix built from the chipdb's pip delays) compared with Vivado's routed delay of the same arc on
the identical implementation of flow/xroute.py (nextpnr's placement and routes imposed pip for pip).

Matrices: nextpnr writes its delay matrix with `-o delay-matrix=FILE`; one small run per chipdb (blinky) dumps it.
The prediction is recomputed here from the matrix exactly as predictDelay does (same tile: 0 same site, 700 from
an FF2 bel, else 150; CO3 -> CIN 0; other: matrix[dy][dx] plus the linear extrapolation outside the window).
Clock nets and arcs inside one site are left out, as in flow/xroute_fit.py."""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xroute_cmp

ROOT = xroute_cmp.ROOT

CONFIG = {
    "dry_run": True,
    "out": ROOT / "build" / "xroute" / "predict",
    "names": ["blinky_p5_cal_static_s1", "rv_soc_p5_cal_static_s1", "bram_p5_cal_static_s1",
              "rv_mul_p5_dspq_cal_s1", "rv_big_p5_dspq_cal_s1"],
    "timer": "perm",
    "binary": ROOT / "build" / "nextpnr-build" / "qorperm" / "nextpnr-himbaechel",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "max_nextpnr": 3,
    "chipdbs": {
        "cal": ROOT / "build" / "chipdb-cal" / "on" / "chipdb-xc7a50t.bin",
        "rcal": ROOT / "build" / "chipdb-rcal" / "on" / "chipdb-xc7a50t.bin",
    },
    "matrix_src": ROOT / "build" / "qor" / "oxc7" / "cal_static" / "blinky_p5" / "s1" / "status.json",
    "tilegrid": ROOT / "toolchain" / "openxc7" / "share" / "nextpnr" / "external" / "prjxray-db" / "artix7" / "xc7a50t" / "tilegrid.json",
    "ff2_re": r"^[A-D]5FF$",
    "lut_in_re": r"^A[1-6]$",
    "train": ["blinky_p5_cal_static_s1", "rv_soc_p5_cal_static_s1", "bram_p5_cal_static_s1"],
}


def dump_matrix(tag, dry):
    out = CONFIG["out"] / f"matrix_{tag}.txt"
    if out.exists():
        return out
    st = json.loads(CONFIG["matrix_src"].read_text())
    cmd = list(st["cmd"])
    i = cmd.index("--chipdb")
    cmd[i + 1] = str(CONFIG["chipdbs"][tag])
    drop = {"--write", "--report"}
    args, k = [], 1
    while k < len(cmd):
        if cmd[k] in drop:
            k += 2
            continue
        if cmd[k] == "-o" and cmd[k + 1].startswith("fasm="):
            k += 2
            continue
        args.append(cmd[k])
        k += 1
    args += ["-o", f"delay-matrix={out}"]
    full = [str(CONFIG["npwait"])] + args
    if dry:
        print(f"[dry] OFX_NEXTPNR_BIN={CONFIG['binary']} {' '.join(full)}")
        return None
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(CONFIG["binary"]), OFX_MAX_NEXTPNR=str(CONFIG["max_nextpnr"]))
    with open(CONFIG["out"] / f"matrix_{tag}.log", "w") as lf:
        rc = subprocess.run(full, stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=str(CONFIG["out"])).returncode
    if rc != 0 or not out.exists():
        raise SystemExit(f"matrix {tag}: nextpnr rc {rc}, see {CONFIG['out'] / f'matrix_{tag}.log'}")
    return out


def load_matrix(path):
    toks = path.read_text().split()
    w = int(toks[0])
    side = 2 * w + 1
    tab = [int(t) for t in toks[1:]]
    assert len(tab) == side * side, f"{path}: {len(tab)} entries, expected {side * side}"
    at = lambda x, y: tab[(y + w) * side + (x + w)]
    band, sx, nx, sy, ny = 4, 0.0, 0, 0.0, 0
    for k in range(-w, w + 1):
        for o, i in ((at(w, k), at(w - band, k)), (at(-w, k), at(-(w - band), k))):
            if o >= 0 and i >= 0:
                sx += (o - i) / band
                nx += 1
        for o, i in ((at(k, w), at(k, w - band)), (at(k, -w), at(k, -(w - band)))):
            if o >= 0 and i >= 0:
                sy += (o - i) / band
                ny += 1
    return {"w": w, "side": side, "tab": tab, "rate_x": max(1.0, sx / nx) if nx else 8.0,
            "rate_y": max(1.0, sy / ny) if ny else 8.0}


def lookup(m, dx, dy):
    w = m["w"]
    ex, ey = max(-w, min(w, dx)), max(-w, min(w, dy))
    base = m["tab"][(ey + w) * m["side"] + (ex + w)]
    return base + int((abs(dx) - abs(ex)) * m["rate_x"] + (abs(dy) - abs(ey)) * m["rate_y"])


def site_xy():
    tg = json.loads(CONFIG["tilegrid"].read_text())
    out = {}
    for t in tg.values():
        for s in t.get("sites", {}):
            out[s] = (t["grid_x"], t["grid_y"])
    return out


def arc_kind(sxy, drv, dpin, snk, spin):
    ss, sb = drv.split("/")
    ds, db = snk.split("/")
    if dpin == "CO3" and spin == "CIN":
        return "carry", None
    a, b = sxy.get(ss), sxy.get(ds)
    if a is None or b is None:
        return None, None
    if a == b:
        if ss == ds:
            return ("site_lut" if re.match(CONFIG["lut_in_re"], spin) else "site_other"), None
        return ("tile_ff2" if re.match(CONFIG["ff2_re"], sb) else "tile"), None
    return "inter", (b[0] - a[0], b[1] - a[1])


def predict(m, kind, off, cal=None):
    """predictDelay in ps; cal = None is the current code, else the opt-in model {site, tile, alpha, beta}."""
    if kind == "carry":
        return 0
    if kind in ("site_lut", "site_other"):
        return cal["site"] if cal and kind == "site_lut" else 0
    if kind in ("tile", "tile_ff2"):
        base = cal["tile"] if cal else 150
        return max(base, 700) if kind == "tile_ff2" else base
    raw = lookup(m, *off)
    return int(cal["alpha"] + cal["beta"] * raw) if cal else raw


def routed_index(name, timer):
    d = json.loads((xroute_cmp.npr_dir(name, timer) / "routed.json").read_text())
    m = next(iter(d["modules"].values()))
    drv, bel = {}, {}
    for cn, c in m["cells"].items():
        bel[cn] = c.get("attributes", {}).get("NEXTPNR_BEL")
        for p, bits in c.get("connections", {}).items():
            if c.get("port_directions", {}).get(p) == "output":
                for bt in bits:
                    if isinstance(bt, int):
                        drv[bt] = (cn, p)
    sink_bit = {}
    for cn, c in m["cells"].items():
        for p, bits in c.get("connections", {}).items():
            if c.get("port_directions", {}).get(p) == "input" and bits and isinstance(bits[0], int):
                sink_bit[(cn, p)] = bits[0]
    return drv, bel, sink_bit


def stat(xs):
    return xroute_cmp.stat(xs)


def collect(mats):
    sxy = site_xy()
    arcs, skipped = [], {}
    for name in CONFIG["names"]:
        rows, _ = xroute_cmp.all_net_arcs(name, CONFIG["timer"])
        drv, bel, sink_bit = routed_index(name, CONFIG["timer"])
        sk = 0
        for r in rows:
            if r["cls"] in ("clock", "intrasite"):
                continue
            src = drv.get(sink_bit.get((r["npr_cell"], r["npr_port"])))
            if src is None or not bel.get(src[0]) or not bel.get(r["npr_cell"]):
                sk += 1
                continue
            kind, off = arc_kind(sxy, bel[src[0]], src[1], bel[r["npr_cell"]], r["npr_port"])
            if kind is None:
                sk += 1
                continue
            arcs.append({"design": name, "kind": kind, "off": off, "viv": r["viv"], "npr": r["npr"],
                         "raw": {t: lookup(m, *off) if off else None for t, m in mats.items()}})
        skipped[name] = sk
    return arcs, skipped


def fit_model(arcs, tag):
    """Opt-in placer model fitted against Vivado: same-site LUT-input and same-tile constants (mean Vivado delay),
    and Vivado = alpha + beta * matrix for arcs between tiles (least squares)."""
    tr = [a for a in arcs if a["design"] in CONFIG["train"]]
    mean = lambda xs: sum(xs) / len(xs)
    inter = [a for a in tr if a["kind"] == "inter"]
    X = [[1.0, a["raw"][tag] / 1000.0] for a in inter]
    y = [a["viv"] for a in inter]
    alpha, beta = xroute_cmp.lstsq(X, y)
    return {"site": int(1000 * mean([a["viv"] for a in tr if a["kind"] == "site_lut"])),
            "tile": int(1000 * mean([a["viv"] for a in tr if a["kind"] == "tile"])),
            "alpha": int(1000 * alpha), "beta": round(beta, 3)}


def evaluate(arcs, mats, models):
    res = defaultdict(dict)
    for name in CONFIG["names"] + ["train", "test"]:
        sel = [a for a in arcs if a["design"] == name or (name == "train" and a["design"] in CONFIG["train"])
               or (name == "test" and a["design"] not in CONFIG["train"])]
        for label, (tag, cal) in models.items():
            by = defaultdict(list)
            for a in sel:
                e = predict(mats[tag], a["kind"], a["off"], cal) / 1000.0 - a["viv"]
                by["all"].append(e)
                by[a["kind"]].append(e)
            res[name][label] = {k: stat(v) for k, v in by.items()}
        res[name]["routed_sdf_cal"] = stat([a["npr"] - a["viv"] for a in sel])
    return dict(res)


def table(res, labels):
    f = xroute_cmp.fmt
    lines = ["| arcs | " + " | ".join(labels) + " | nextpnr routed delay (SDF, cal chipdb) |",
             "|---" * (2 + len(labels)) + "|"]
    for n, r in res.items():
        lines.append(f"| {n} | " + " | ".join(f(r[l]["all"]) for l in labels) + f" | {f(r['routed_sdf_cal'])} |")
    lines += ["", "| kind (all designs) | " + " | ".join(labels) + " |", "|---" * (1 + len(labels)) + "|"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    paths = {t: dump_matrix(t, dry) for t in CONFIG["chipdbs"]}
    if dry:
        return
    mats = {t: load_matrix(p) for t, p in paths.items()}
    for t, m in mats.items():
        print(f"matrix {t}: window {m['w']}, (0,1) {lookup(m, 0, 1)} (1,0) {lookup(m, 1, 0)} (2,2) {lookup(m, 2, 2)} "
              f"(10,10) {lookup(m, 10, 10)} rates {m['rate_x']}/{m['rate_y']}")
    arcs, skipped = collect(mats)
    models = {"cal chipdb, current model": ("cal", None), "rcal chipdb, current model": ("rcal", None)}
    fits = {}
    for tag in mats:
        fits[tag] = fit_model(arcs, tag)
        models[f"{tag} chipdb, fitted model"] = (tag, fits[tag])
    print("fitted (ps, train " + ", ".join(CONFIG["train"]) + "):", json.dumps(fits))
    res = evaluate(arcs, mats, models)
    kinds = defaultdict(dict)
    for label, (tag, cal) in models.items():
        for k in ("site_lut", "site_other", "tile", "tile_ff2", "inter", "carry"):
            sel = [a for a in arcs if a["kind"] == k]
            kinds[k][label] = stat([predict(mats[tag], k, a["off"], cal) / 1000.0 - a["viv"] for a in sel])
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    (CONFIG["out"] / "predict.json").write_text(json.dumps({"fits": fits, "skipped": skipped, "res": res,
                                                             "kinds": kinds}, indent=1) + "\n")
    f = xroute_cmp.fmt
    labels = list(models)
    md = table(res, labels)
    md += "".join(f"| {k} | " + " | ".join(f(kinds[k][l]) for l in labels) + " |\n" for k in kinds)
    (CONFIG["out"] / "fit.json").write_text(json.dumps(fits, indent=1) + "\n")
    (CONFIG["out"] / "predict.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
