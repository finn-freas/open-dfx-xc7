import argparse
import json
import re
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "region": (12, 100, 15, 149),
    "near": 4,
    "rm_prefix": "u_rm.",
    "sdf_units_per_ns": 1000.0,
}


def unescape(x):
    return re.sub(r"\\(.)", r"\1", x)


def sdf_arcs(path):
    arcs = {}
    pat = re.compile(r"\(INTERCONNECT\s+(\S+)\s+(\S+)\s+(.*)\)\s*$")
    for ln in path.read_text().splitlines():
        m = pat.search(ln)
        if not m:
            continue
        src, dst = unescape(m.group(1)), unescape(m.group(2))
        nums = [float(x) for x in re.findall(r"-?[0-9]+(?:\.[0-9]+)?", m.group(3))]
        sc, sp = src.rsplit("/", 1)
        dc, dp = dst.rsplit("/", 1)
        arcs[(sc, sp, dc, dp)] = (max(nums) if nums else 0.0) / CONFIG["sdf_units_per_ns"]
    return arcs


def load(build):
    rep = json.loads((build / "report.json").read_text())
    routed = json.loads(next(build.glob("*_routed.json")).read_text())
    m = routed["modules"][next(iter(routed["modules"]))]
    loc = {}
    for name, c in m["cells"].items():
        bel = c["attributes"].get("NEXTPNR_BEL", "")
        mm = re.match(r"SLICE_X(\d+)Y(\d+)/", bel)
        if mm:
            loc[name] = (int(mm.group(1)), int(mm.group(2)))
    arcs = sdf_arcs(next(build.glob("*.sdf")))
    drivers = {}
    pips = {}
    for name, n in m["netnames"].items():
        r = n.get("attributes", {}).get("ROUTING")
        if r:
            pips[name] = r.count(";") // 3
    return rep, loc, arcs, drivers, pips


def classify(a, b):
    x0, y0, x1, y1 = CONFIG["region"]
    if a is None or b is None:
        return "unplaced"
    lx, hx = min(a[0], b[0]), max(a[0], b[0])
    ly, hy = min(a[1], b[1]), max(a[1], b[1])
    inside = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    if inside(a) or inside(b):
        return "touches region"
    if lx < x0 and hx > x1 and ly <= y1 and hy >= y0:
        return "crosses region"
    k = CONFIG["near"]
    if lx <= x1 + k and hx >= x0 - k and ly <= y1 + k and hy >= y0 - k:
        return "near region"
    return "far"


def crit_nets(rep):
    out = []
    for cp in rep["critical_paths"]:
        for s in cp["path"]:
            if s["type"] == "routing":
                out.append((s["net"], (s["from"]["cell"], s["from"]["port"], s["to"]["cell"], s["to"]["port"]), s["delay"]))
    return out


def main():
    ap = argparse.ArgumentParser(description="per-arc routed delay of two builds with the same placement (keep-out vs not)")
    ap.add_argument("keep")
    ap.add_argument("other")
    ap.add_argument("--json")
    a = ap.parse_args()
    rk, lk, ak, dk, pk = load(Path(a.keep))
    ro, lo, ao, do, po = load(Path(a.other))
    moved = sum(1 for c in lk if lo.get(c) != lk[c])
    classes = {}
    for key, dkeep in ak.items():
        if key not in ao:
            continue
        drv, _, cell, _ = key
        if drv.startswith(CONFIG["rm_prefix"]) or cell.startswith(CONFIG["rm_prefix"]):
            cls = "RM arc"
        else:
            cls = classify(lk.get(drv), lk.get(cell))
        c = classes.setdefault(cls, {"arcs": 0, "sum_keep": 0.0, "sum_other": 0.0, "slower_100ps": 0})
        c["arcs"] += 1
        c["sum_keep"] += dkeep
        c["sum_other"] += ao[key]
        c["slower_100ps"] += dkeep - ao[key] > 0.1
    print(f"placement differences: {moved} cells")
    print(f"Fmax: keep {list(rk['fmax'].values())[0]['achieved']:.2f}, other {list(ro['fmax'].values())[0]['achieved']:.2f} MHz")
    print(f"{'class':16s} {'arcs':>6s} {'mean keep':>10s} {'mean other':>10s} {'delta ns':>9s} {'>0.1 ns slower':>15s}")
    for cls, c in sorted(classes.items()):
        n = c["arcs"]
        print(f"{cls:16s} {n:6d} {c['sum_keep'] / n:10.3f} {c['sum_other'] / n:10.3f} {(c['sum_keep'] - c['sum_other']) / n:9.3f} "
              f"{c['slower_100ps']:15d}")
    print("critical path of the keep-out build, net by net (ns):")
    rows = []
    by_cells = {}
    for (sc, _, dc, _), v in ao.items():
        by_cells[(sc, dc)] = max(v, by_cells.get((sc, dc), 0.0))
    for net, key, d in crit_nets(rk):
        drv, _, cell, port = key
        other = by_cells.get((drv, cell))
        cls = classify(lk.get(drv), lk.get(cell))
        rows.append({"net": net, "sink": f"{cell}.{port}", "keep": d, "other": other, "class": cls,
                     "pips_keep": pk.get(net), "pips_other": po.get(net), "from": lk.get(drv), "to": lk.get(cell)})
        print(f"  {d:6.3f} vs {other if other is None else round(other, 3)!s:>6s}  {cls:15s} {lk.get(drv)} -> {lk.get(cell)} "
              f"pips {pk.get(net)}/{po.get(net)}  {net[:60]}")
    if a.json:
        Path(a.json).write_text(json.dumps({"classes": classes, "critical": rows, "moved": moved}, indent=2) + "\n")


if __name__ == "__main__":
    main()
