"""Global-placement diagnosis: Vivado's own placement (a "free" dump) vs ours (our placement imposed on Vivado, a
"placed" dump). Spread/density, critical-path compactness, connectivity locality, carry-chain ordering. Read-only
on existing dumps.
Default (no arguments): rv_soc, place_dump/rv_soc_p5_fix_static_{free,placed} -> build/qor/place/diag/rv_soc.json.
--ours NAME: a flow/place_vivado.sh run with dump.flag (build/place_xtime2/NAME/{cells,paths}.txt, after Vivado's
route); the design, the yosys netlist and the Vivado reference dump follow from NAME; output diag/NAME.json."""
import argparse, json, re, statistics, sys
from collections import defaultdict, Counter
from pathlib import Path
R = Path.home() / "open-dfx-xc7"
sys.path.insert(0, str(R / "flow"))
import place_compare as pc
VW = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build")
CONFIG = {"design": "rv_soc", "dump": VW / "place_dump", "xtime": VW / "place_xtime2",
          "out": R / "build/qor/place/diag", "bin": 4, "top_paths": 100,
          "yosys_json": R / "build/qor/synth/rv_soc/69e28e77cdb928ff/qor_rv_soc.json"}
ap = argparse.ArgumentParser()
ap.add_argument("--ours", help="build/place_xtime/<NAME> with cells.txt and paths.txt")
ap.add_argument("--vivado", help="Vivado's own placement dump dir (default place_dump/<design>_p5_fix_static_free)")
args = ap.parse_args()
OUT_NAME = "rv_soc"
if args.ours:
    CONFIG["design"] = re.match(r"^(.*?)_p\d+_", args.ours).group(1)
    info = json.loads((R / "build/qor/place/xsrc" / args.ours / "place_info.json").read_text())
    st = json.loads((R / info["from"] / "status.json").read_text())
    CONFIG["yosys_json"] = Path(st["cmd"][st["cmd"].index("--json") + 1])
    OUT_NAME = args.ours
grid = pc.site_grid()
def load_dir(d, cells_fn, paths_fn):
    cells = pc.read_cells(d / cells_fn)
    pos = {n: grid[c["site"]] for n, c in cells.items() if c["site"] in grid}
    paths = []
    for ln in (d / paths_fn).read_text().splitlines():
        p = ln.split("\t")
        if len(p) >= 7:
            paths.append((float(p[0]), p[6].split()))
    return cells, pos, paths
def load(tag):
    d = CONFIG["dump"] / f"{CONFIG['design']}_p5_fix_static_{tag}"
    if tag == "free" and args.vivado:
        d = Path(args.vivado)
    if tag == "placed" and args.ours:
        return load_dir(CONFIG["xtime"] / args.ours, "cells.txt", "paths.txt")
    cells_fn = "cells_placed.txt" if tag == "placed" and (d / "cells_placed.txt").exists() else "cells.txt"
    paths_fn = "paths_placed.txt" if tag == "placed" and (d / "paths_placed.txt").exists() else "paths.txt"
    return load_dir(d, cells_fn, paths_fn)
res = {}
V = load("free"); N = load("placed")
def st(xs): return {"n": len(xs), "mean": round(statistics.mean(xs), 2), "median": round(statistics.median(xs), 2)} if xs else {}
def spread(pos, cells):
    logic = [p for n, p in pos.items() if re.match(r"^(LUT|FD|CARRY|RAM[DS]|MUXF|SRL)", cells[n]["type"])]
    xs, ys = [p[0] for p in logic], [p[1] for p in logic]
    b = CONFIG["bin"]; occ = Counter((x // b, y // b) for x, y in logic)
    sites = Counter(cells[n]["site"] for n, p in pos.items() if re.match(r"^(LUT|FD|CARRY|RAM[DS]|MUXF)", cells[n]["type"]))
    return {"cells": len(logic), "x_range": [min(xs), max(xs)], "y_range": [min(ys), max(ys)],
            "sd_x": round(statistics.pstdev(xs), 1), "sd_y": round(statistics.pstdev(ys), 1),
            "bins_used": len(occ), "bin_cells_mean": round(statistics.mean(occ.values()), 1),
            "bin_cells_p90": sorted(occ.values())[int(0.9 * len(occ))], "slices": len(sites)}
res["spread"] = {"vivado": spread(V[1], V[0]), "ours": spread(N[1], N[0])}
def path_stats(paths, pos, k):
    hops, bbox = [], []
    for slack, cl in paths[:k]:
        pts = [pos[c] for c in cl if c in pos]
        if len(pts) < 2: continue
        hops.append(sum(abs(a[0]-b[0]) + abs(a[1]-b[1]) for a, b in zip(pts, pts[1:])))
        bbox.append((max(p[0] for p in pts) - min(p[0] for p in pts)) + (max(p[1] for p in pts) - min(p[1] for p in pts)))
    return {"hops": st(hops), "bbox": st(bbox)}
k = CONFIG["top_paths"]
res["critical_paths"] = {"vivado_own_paths_in_vivado": path_stats(V[2], V[1], k), "vivado_own_paths_in_ours": path_stats(V[2], N[1], k),
                         "our_paths_in_ours": path_stats(N[2], N[1], k), "our_paths_in_vivado": path_stats(N[2], V[1], k)}
y = json.loads(CONFIG["yosys_json"].read_text()); m = next(iter(y["modules"].values()))
nets = defaultdict(list)
for cn, c in m["cells"].items():
    for p, bits in c["connections"].items():
        for bt in bits:
            if isinstance(bt, int): nets[bt].append(cn)
def esc(n): return n
def hpwl_all(pos):
    out = {}
    for bt, cl in nets.items():
        pts = [pos[c] for c in cl if c in pos]
        if 2 <= len(pts) <= 64:
            out[bt] = (max(p[0] for p in pts) - min(p[0] for p in pts)) + (max(p[1] for p in pts) - min(p[1] for p in pts))
    return out
hv, hn = hpwl_all(V[1]), hpwl_all(N[1])
common = [b for b in hv if b in hn]
res["matched_cells"] = sum(1 for c in m["cells"] if c in V[1] and c in N[1])
res["hpwl_nets_2_64"] = {"nets": len(common), "vivado": sum(hv[b] for b in common), "ours": sum(hn[b] for b in common)}
byf = defaultdict(lambda: [0, 0, 0])
for b in common:
    f = len(nets[b]); cls = "2" if f == 2 else "3-4" if f <= 4 else "5-16" if f <= 16 else "17-64"
    byf[cls][0] += 1; byf[cls][1] += hv[b]; byf[cls][2] += hn[b]
res["hpwl_by_fanout"] = {k: {"nets": v[0], "vivado": v[1], "ours": v[2], "ratio": round(v[2] / max(1, v[1]), 2)} for k, v in sorted(byf.items())}
ch = defaultdict(dict)
for n in V[1]:
    mm = re.match(r"^(.*)\.genblk1\.slice\[(\d+)\]\.genblk1\.carry4$", n)
    if mm: ch[mm.group(1)][int(mm.group(2))] = n
def chain_ok(pos):
    ok = bad = 0
    for k2, sl in ch.items():
        idx = sorted(sl); ys = [pos[sl[i]][1] for i in idx if sl[i] in pos]; xs = {pos[sl[i]][0] for i in idx if sl[i] in pos}
        if len(ys) >= 2 and len(xs) == 1 and (all(b - a == 1 for a, b in zip(ys, ys[1:])) or all(a - b == 1 for a, b in zip(ys, ys[1:]))): ok += 1
        else: bad += 1
    return {"contiguous_columns": ok, "other": bad}
res["carry_chains"] = {"vivado": chain_ok(V[1]), "ours": chain_ok(N[1])}
def locality(pos):
    nb = defaultdict(set)
    for bt, cl in nets.items():
        if 2 <= len(cl) <= 16:
            for c in cl:
                nb[c].update(x for x in cl if x != c)
    d = []
    for c, s in nb.items():
        if c not in pos: continue
        pts = [pos[x] for x in s if x in pos]
        if not pts: continue
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        d.append(abs(pos[c][0] - cx) + abs(pos[c][1] - cy))
    return st(d)
res["neighbour_centroid_distance"] = {"vivado": locality(V[1]), "ours": locality(N[1])}
CONFIG["out"].mkdir(parents=True, exist_ok=True)
(CONFIG["out"] / f"{OUT_NAME}.json").write_text(json.dumps(res, indent=1) + "\n")
print(json.dumps(res, indent=1))
