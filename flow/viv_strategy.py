"""Vivado placement-strategy study (docs/vivado-placement-strategy.md). Black-box: reads only Vivado's outputs
(placements dumped with get_cells/LOC/BEL, timing paths, reports, logs) and our placements of the same netlist.

  viv_strategy.py compare DESIGN [--ours RUN...]   Vivado's own placement of our exported netlist (build/exact/
        <d>_p5_vref_exact) against our exact-imported placements (build/exact/<d>_p5_<RUN>_exact), cell for cell
        (same netlist, same names); paths, packing, density, hard blocks.  -> build/viv_strategy/compare_<d>.json
  viv_strategy.py hier NAME [--dir D]   per-module bounding boxes / overlap / order in a Vivado RTL run
        (build/viv_strategy/<NAME>, vivado/viv_strategy.tcl)                -> build/viv_strategy/hier_<NAME>.json
  viv_strategy.py directives NAME      directive sweep table (slack, slices, footprint, worst-path metrics)
  viv_strategy.py log LOGFILE          place_design phases and their metrics from a Vivado log
Distances are prjxray tile-grid Manhattan units (one CLB column = 2 in x incl. the INT tile... see place_compare)."""
import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_compare as pc

R = Path.home() / "open-dfx-xc7"
VW = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado")
CONFIG = {
    "exact_out": VW / "build" / "exact",
    "exact_src": VW / "designs" / "exact",
    "vs_out": VW / "build" / "viv_strategy",
    "out": R / "build" / "viv_strategy",
    "top_paths": 100,
    "ours_default": ["pl14_off_stub_s1", "pl14_off_stub_s2", "pl14_off_stub_s3"],
}
OUT_PINS = re.compile(r"^(O|O5|O6|Q|CO\[\d\]|O\[\d\]|DO.*|SPO|DPO|DO[A-D]|BUSY|CRC.*|P.*OUT.*|P\[\d+\])$")
LUT_RE = re.compile(r"^LUT\d$")
FF_RE = re.compile(r"^FD[RSCP]E$")


def mean(xs):
    return round(statistics.mean(xs), 3) if xs else None


def median(xs):
    return round(statistics.median(xs), 3) if xs else None


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


GRID = None


def grid():
    global GRID
    if GRID is None:
        GRID = pc.site_grid()
    return GRID


def slice_xy(site):
    m = re.match(r"SLICE_X(\d+)Y(\d+)$", site)
    return (int(m.group(1)), int(m.group(2))) if m else None


class Netlist:
    """Exported netlist (designs/exact/<run>/netlist.json): driver and sinks per net bit, cell pin -> bit."""

    def __init__(self, fn):
        d = json.loads(Path(fn).read_text())
        m = next(v for v in d["modules"].values() if len(v.get("cells", {})) > 10)
        self.cells = {n: c for n, c in m["cells"].items() if not c["type"].startswith("$")}
        self.driver = {}
        self.sinks = defaultdict(list)
        self.pin = {}
        for n, c in self.cells.items():
            pd = c.get("port_directions", {})
            for p, bits in c["connections"].items():
                for i, b in enumerate(bits):
                    if not isinstance(b, int):
                        continue
                    pn = p if len(bits) == 1 else f"{p}[{i}]"
                    self.pin[(n, pn)] = b
                    out = pd.get(p) == "output" if pd else bool(OUT_PINS.match(pn))
                    if out:
                        self.driver[b] = (n, pn)
                    else:
                        self.sinks[b].append((n, pn))

    def type(self, n):
        return self.cells[n]["type"] if n in self.cells else None

    def drv_of(self, n, p):
        b = self.pin.get((n, p))
        return self.driver.get(b, (None, None))[0] if b is not None else None


def read_cells(fn):
    """name -> (ref, site, bel); LUTRAM sub-cells kept by their full name."""
    out = {}
    for ln in Path(fn).read_text().splitlines():
        p = ln.split("\t")
        if len(p) >= 4 and p[2]:
            out[p[0]] = (p[1], p[2], p[3].split(".")[-1])
    return out


def read_pin_paths(fn, k):
    """paths_noicap.txt: slack, net, logic, pins...  -> [(slack, net, logic, [(cell, pin)...])]."""
    out = []
    for ln in Path(fn).read_text().splitlines():
        f = ln.split("\t")
        if len(f) < 4:
            continue
        pins = []
        for tok in f[3].split():
            c, p = tok.rsplit("/", 1)
            pins.append((c, p))
        out.append((float(f[0]), float(f[1]), float(f[2]), pins))
        if len(out) >= k:
            break
    return out


def cell_seq(pins):
    seq = []
    for c, p in pins:
        if not seq or seq[-1][0] != c:
            seq.append([c, p, None])
        else:
            seq[-1][2] = p
    return seq


def pos_of(cells, c):
    v = cells.get(c)
    return grid().get(v[1]) if v else None


def path_metrics(paths, cells, nl):
    """Per path: hops, bbox, zigzag (hops / bbox half-perimeter), x/y reversals, per-step class distances."""
    rows = []
    step_cls = defaultdict(list)
    for slack, net, logic, pins in paths:
        seq = cell_seq(pins)
        pts = [pos_of(cells, c) for c, _, _ in seq]
        if any(p is None for p in pts) or len(pts) < 2:
            continue
        hops = 0
        same_site = 0
        sx = []
        sy = []
        for (a, ai, ao), (b, bi, bo), pa, pb in zip(seq, seq[1:], pts, pts[1:]):
            d = abs(pa[0] - pb[0]) + abs(pa[1] - pb[1])
            hops += d
            ss = cells[a][1] == cells[b][1]
            same_site += ss
            ta, tb = (nl.type(a) or cells[a][0]), (nl.type(b) or cells[b][0])
            ka = "LUT" if LUT_RE.match(ta) else "FF" if FF_RE.match(ta) else ta
            kb = "LUT" if LUT_RE.match(tb) else "FF" if FF_RE.match(tb) else tb
            if kb == "FF":
                kb = "FF." + re.sub(r"\[.*", "", bi or "")
            step_cls[f"{ka}->{kb}"].append((d, ss))
            if pb[0] != pa[0]:
                sx.append(1 if pb[0] > pa[0] else -1)
            if pb[1] != pa[1]:
                sy.append(1 if pb[1] > pa[1] else -1)
        bx = max(p[0] for p in pts) - min(p[0] for p in pts)
        by = max(p[1] for p in pts) - min(p[1] for p in pts)
        rev = lambda s: sum(1 for u, v in zip(s, s[1:]) if u != v)
        rows.append({"slack": slack, "net": net, "logic": logic, "cells": len(seq), "hops": hops,
                     "bbox": bx + by, "zig": hops / max(1, bx + by), "rev_x": rev(sx), "rev_y": rev(sy),
                     "same_site": same_site, "steps": len(seq) - 1, "end_pin": re.sub(r"\[.*", "", seq[-1][1] or "")})
    m = lambda k: mean([r[k] for r in rows])
    out = {"paths": len(rows), "slack_mean": m("slack"), "net_mean": m("net"), "logic_mean": m("logic"),
           "cells_mean": m("cells"), "hops_mean": m("hops"), "bbox_mean": m("bbox"), "zigzag_mean": m("zig"),
           "monotone_paths_pct": pct(sum(r["zig"] <= 1.05 for r in rows), len(rows)),
           "x_reversals_mean": m("rev_x"), "y_reversals_mean": m("rev_y"),
           "hops_per_step": round(sum(r["hops"] for r in rows) / max(1, sum(r["steps"] for r in rows)), 2),
           "same_site_steps_pct": pct(sum(r["same_site"] for r in rows), sum(r["steps"] for r in rows)),
           "end_pins": dict(Counter(r["end_pin"] for r in rows).most_common()),
           "steps": {k: {"n": len(v), "dist_mean": mean([d for d, _ in v]), "dist_median": median([d for d, _ in v]),
                         "same_slice_pct": pct(sum(s for _, s in v), len(v))}
                     for k, v in sorted(step_cls.items(), key=lambda kv: -len(kv[1])) if len(v) >= 5}}
    return out


def critical_cells(paths, k):
    crit = {}
    for slack, _, _, pins in paths[:k]:
        for c, _ in pins:
            crit[c] = min(crit.get(c, 1e9), slack)
    return crit


def packing(cells, nl, crit):
    """Slice composition, dual-output LUT sites, LUT->FF pairing by criticality, control sets, carry neighbourhood."""
    by_site = defaultdict(list)
    for n, (ref, site, bel) in cells.items():
        if site.startswith("SLICE"):
            by_site[site].append((n, ref, bel))
    lut_slices = ff_slices = 0
    luts_per = []
    ffs_per = []
    pos_used = pos_dual = 0
    for s, lst in by_site.items():
        lbel = [b for n, r, b in lst if b.endswith("LUT")]
        fbel = [b for n, r, b in lst if b.endswith("FF")]
        logic_l = [b for n, r, b in lst if b.endswith("LUT") and LUT_RE.match(r)]
        if lbel:
            lut_slices += 1
            luts_per.append(len(lbel))
        if fbel:
            ff_slices += 1
            ffs_per.append(len(fbel))
        letters = Counter(b[0] for b in logic_l)
        pos_used += len(letters)
        pos_dual += sum(1 for v in letters.values() if v == 2)
    pair = defaultdict(lambda: [0, 0, 0])
    for n, (ref, site, bel) in cells.items():
        if not FF_RE.match(ref):
            continue
        d = nl.drv_of(n, "D")
        if d is None or d not in cells or not LUT_RE.match(cells[d][0]):
            continue
        cls = "crit" if n in crit else "other"
        for k in (cls, "all"):
            pair[k][0] += 1
            pair[k][1] += cells[d][1] == site
            pair[k][2] += cells[d][1] == site and cells[d][2][0] == bel[0]
    qside = defaultdict(lambda: [0, 0, 0, 0, 0])
    for n, (ref, site, bel) in cells.items():
        if not FF_RE.match(ref):
            continue
        d = nl.drv_of(n, "D")
        dsame = bool(d and d in cells and LUT_RE.match(cells[d][0]) and cells[d][1] == site)
        b = nl.pin.get((n, "Q"))
        loads = [c for c, _ in nl.sinks.get(b, [])] if b is not None else []
        qsame = any(c in cells and LUT_RE.match(cells[c][0]) and cells[c][1] == site for c in loads)
        for k in ("crit" if n in crit else "other", "all"):
            q = qside[k]
            q[0] += 1
            q[1] += dsame
            q[2] += qsame
            q[3] += qsame and not dsame
            q[4] += not qsame and not dsame
    cs_ff = defaultdict(list)
    for n, (ref, site, bel) in cells.items():
        if FF_RE.match(ref):
            key = (nl.pin.get((n, "C")), nl.pin.get((n, "CE")), nl.pin.get((n, "R"), nl.pin.get((n, "S"))))
            cs_ff[key].append(site)
    cs_pairs = sum(len(set(v)) for v in cs_ff.values())
    cs_min = sum(-(-len(v) // 8) for v in cs_ff.values())
    s_same = s_all = 0
    o_dist = []
    for n, (ref, site, bel) in cells.items():
        if ref != "CARRY4":
            continue
        for i in range(4):
            d = nl.drv_of(n, f"S[{i}]")
            if d and d in cells and LUT_RE.match(cells[d][0]):
                s_all += 1
                s_same += cells[d][1] == site
            b = nl.pin.get((n, f"O[{i}]"))
            if b is not None:
                p0 = grid().get(site)
                for c, _ in nl.sinks.get(b, []):
                    p1 = pos_of(cells, c)
                    if p0 and p1:
                        o_dist.append(abs(p0[0] - p1[0]) + abs(p0[1] - p1[1]))
    return {"slices_with_lut": lut_slices, "slices_with_ff": ff_slices, "slices": len(by_site),
            "luts_per_lut_slice": mean(luts_per), "ffs_per_ff_slice": mean(ffs_per),
            "lut_positions_used": pos_used, "lut_positions_dual_pct": pct(pos_dual, pos_used),
            "lut_ff_pair": {k: {"ffs": v[0], "same_slice_pct": pct(v[1], v[0]), "same_letter_pct": pct(v[2], v[0])}
                            for k, v in pair.items()},
            "ff_side": {k: {"ffs": v[0], "d_lut_same_slice_pct": pct(v[1], v[0]), "q_load_same_slice_pct": pct(v[2], v[0]),
                            "only_q_side_pct": pct(v[3], v[0]), "alone_pct": pct(v[4], v[0])} for k, v in qside.items()},
            "control_sets": len(cs_ff), "cs_slice_pairs": cs_pairs, "cs_slice_pairs_min": cs_min,
            "carry_S_lut_same_slice_pct": pct(s_same, s_all), "carry_O_sink_dist_mean": mean(o_dist)}


def density(cells, crit):
    """LUT/FF occupancy around critical vs other cells: own slice and the 5x5-slice window around it."""
    occ = Counter()
    for n, (ref, site, bel) in cells.items():
        xy = slice_xy(site)
        if xy and (bel.endswith("LUT") or bel.endswith("FF")):
            occ[xy] += 1
    def win(xy, r):
        tot = sum(occ.get((xy[0] + dx, xy[1] + dy), 0) for dx in range(-r, r + 1) for dy in range(-r, r + 1))
        return tot / ((2 * r + 1) ** 2 * 16.0)
    res = {}
    for cls in ("crit", "other"):
        own = []
        w2 = []
        for n, (ref, site, bel) in cells.items():
            xy = slice_xy(site)
            if not xy or not (LUT_RE.match(ref) or FF_RE.match(ref)):
                continue
            if (n in crit) != (cls == "crit"):
                continue
            own.append(occ[xy] / 16.0)
            w2.append(win(xy, 2))
        res[cls] = {"cells": len(own), "own_slice_fill": mean(own), "window5x5_fill": mean(w2)}
    xs = [xy[0] for xy in occ]
    ys = [xy[1] for xy in occ]
    res["slice_bbox"] = [min(xs), max(xs), min(ys), max(ys)]
    res["used_slices"] = len(occ)
    res["bbox_fill_pct"] = pct(len(occ), (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1))
    return res


def hard_blocks(cells, nl):
    out = {}
    for n, (ref, site, bel) in cells.items():
        if not (ref.startswith("RAMB") or ref.startswith("DSP") or ref.startswith("ICAP")):
            continue
        p0 = grid().get(site)
        nb = set()
        for (c, p), b in nl.pin.items():
            if c != n:
                continue
            dv = nl.driver.get(b)
            if dv and dv[0] != n:
                nb.add(dv[0])
            for s, _ in nl.sinks.get(b, []):
                if s != n:
                    nb.add(s)
        pts = [pos_of(cells, c) for c in nb if pos_of(cells, c)]
        if not pts or not p0:
            continue
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        ds = sorted(abs(p[0] - p0[0]) + abs(p[1] - p0[1]) for p in pts)
        out[n] = {"site": site, "neighbours": len(pts), "dist_to_centroid": round(abs(cx - p0[0]) + abs(cy - p0[1]), 1),
                  "neighbour_dist_median": ds[len(ds) // 2], "neighbour_dist_p90": ds[int(0.9 * (len(ds) - 1))]}
    return out


def lut_chains(paths, cells, nl):
    """Consecutive LUT->LUT steps on the paths: same slice / same CLB tile / adjacent tile, and the x-order."""
    n = same_slice = same_tile = near = 0
    dists = []
    for _, _, _, pins in paths:
        seq = cell_seq(pins)
        for (a, _, _), (b, _, _) in zip(seq, seq[1:]):
            if a in cells and b in cells and LUT_RE.match(nl.type(a) or "") and LUT_RE.match(nl.type(b) or ""):
                pa, pb = pos_of(cells, a), pos_of(cells, b)
                if not pa or not pb:
                    continue
                d = abs(pa[0] - pb[0]) + abs(pa[1] - pb[1])
                n += 1
                dists.append(d)
                same_slice += cells[a][1] == cells[b][1]
                same_tile += pa == pb
                near += d <= 3
    return {"lut_lut_steps": n, "same_slice_pct": pct(same_slice, n), "same_tile_pct": pct(same_tile, n),
            "within_3_pct": pct(near, n), "dist_mean": mean(dists), "dist_median": median(dists)}


def compare(a):
    d = a.design
    nlsrc = CONFIG["exact_src"] / f"{d}_p5_{(a.ours or CONFIG['ours_default'])[0]}_exact" / "netlist.json"
    nl = Netlist(nlsrc)
    k = a.k
    vdir = CONFIG["exact_out"] / f"{d}_p5_vref_exact"
    V = read_cells(vdir / "cells.txt")
    Vp = read_pin_paths(vdir / "paths_noicap.txt", 1000)
    res = {"design": d, "netlist": str(nlsrc), "timer": "Vivado (route_design, exact import / own placement)",
           "vivado": {}, "ours": {}}
    vcrit = critical_cells(Vp, k)

    def block(cells, paths, crit, own_paths_label):
        return {"paths_own": path_metrics(paths[:k], cells, nl), "lut_chains_own": lut_chains(paths[:k], cells, nl),
                "packing": packing(cells, nl, crit), "density": density(cells, crit),
                "hard_blocks": hard_blocks(cells, nl)}
    res["vivado"] = block(V, Vp, vcrit, "vivado")
    res["vivado"]["slack"] = (vdir / "slack.txt").read_text()
    for run in a.ours or CONFIG["ours_default"]:
        odir = CONFIG["exact_out"] / f"{d}_p5_{run}_exact"
        if not (odir / "paths_noicap.txt").exists():
            continue
        O = read_cells(odir / "cells.txt")
        Op = read_pin_paths(odir / "paths_noicap.txt", 1000)
        ocrit = critical_cells(Op, k)
        r = block(O, Op, ocrit, run)
        r["slack"] = (odir / "slack.txt").read_text()
        r["vivado_paths_in_ours"] = path_metrics(Vp[:k], O, nl)
        r["ours_paths_in_vivado"] = path_metrics(Op[:k], V, nl)
        r["lut_chains_vivado_paths_in_ours"] = lut_chains(Vp[:k], O, nl)
        res["ours"][run] = r
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    fn = CONFIG["out"] / f"compare_{d}.json"
    fn.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


def module_of(name, depth):
    parts = name.split("/")[:-1]
    return "/".join(parts[:depth]) if parts else "(top)"


def hier(a):
    d = CONFIG["vs_out"] / a.name
    cells = read_cells(d / f"cells_{a.dir}.txt")
    paths = []
    fn = d / f"paths_route_{a.dir}.txt"
    if not fn.exists():
        fn = d / f"paths_place_{a.dir}.txt"
    for ln in fn.read_text().splitlines():
        f = ln.split("\t")
        if len(f) >= 7:
            paths.append((float(f[0]), f[6].split()))
    res = {"name": a.name, "directive": a.dir, "depth": a.depth, "modules": {}}
    mods = defaultdict(list)
    for n, (ref, site, bel) in cells.items():
        xy = slice_xy(site)
        if xy:
            mods[module_of(n, a.depth)].append(xy)
    allx = [p[0] for v in mods.values() for p in v]
    ally = [p[1] for v in mods.values() for p in v]
    occ = {}
    for m, pts in sorted(mods.items(), key=lambda kv: -len(kv[1])):
        if len(pts) < a.min_cells:
            continue
        xs = sorted(p[0] for p in pts)
        ys = sorted(p[1] for p in pts)
        q = lambda s, f: s[int(f * (len(s) - 1))]
        box = (q(xs, .1), q(xs, .9), q(ys, .1), q(ys, .9))
        sl = set(pts)
        res["modules"][m] = {"cells": len(pts), "slices": len(sl), "bbox_full": [xs[0], xs[-1], ys[0], ys[-1]],
                             "bbox_p10_p90": list(box), "centroid": [round(statistics.mean(xs), 1), round(statistics.mean(ys), 1)],
                             "sd": [round(statistics.pstdev(xs), 1), round(statistics.pstdev(ys), 1)],
                             "fill_pct": pct(len(sl), (box[1] - box[0] + 1) * (box[3] - box[2] + 1))}
        occ[m] = sl
    owners = defaultdict(set)
    for m, sl in occ.items():
        for s in sl:
            owners[s].add(m)
    for m, sl in occ.items():
        res["modules"][m]["shared_slices_pct"] = pct(sum(1 for s in sl if len(owners[s]) > 1), len(sl))
    flow = Counter()
    for slack, cl in paths[:a.k]:
        ms = [module_of(c, a.depth) for c in cl]
        for u, v in zip(ms, ms[1:]):
            if u != v:
                flow[f"{u} -> {v}"] += 1
    res["critical_module_crossings"] = dict(flow.most_common(20))
    res["paths_inside_one_module_pct"] = pct(sum(1 for _, cl in paths[:a.k] if len({module_of(c, a.depth) for c in cl}) == 1),
                                             len(paths[:a.k]))
    res["design_slice_bbox"] = [min(allx), max(allx), min(ally), max(ally)]
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    (CONFIG["out"] / f"hier_{a.name}_{a.dir}_d{a.depth}.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


def kv(fn):
    out = {}
    if Path(fn).exists():
        for ln in Path(fn).read_text().splitlines():
            p = ln.split()
            if len(p) >= 2:
                out[p[0]] = p[1]
    return out


def util_slices(fn):
    t = Path(fn).read_text() if Path(fn).exists() else ""
    m = re.search(r"\|\s*Slice\s*\|\s*(\d+)", t)
    return int(m.group(1)) if m else None


def directives(a):
    d = CONFIG["vs_out"] / a.name
    job = (d / "times.txt").read_text() if (d / "times.txt").exists() else ""
    times = kv(d / "times.txt")
    period = None
    xdc = (d / "constraints.xdc").read_text() if (d / "constraints.xdc").exists() else ""
    m = re.search(r"-period\s+([\d.]+)", xdc)
    period = float(m.group(1)) if m else 5.0
    rows = []
    for fn in sorted(d.glob("cells_*.txt")):
        dr = fn.stem[len("cells_"):]
        cells = read_cells(fn)
        sl = [slice_xy(s) for _, s, _ in cells.values() if slice_xy(s)]
        xs = [p[0] for p in sl]
        ys = [p[1] for p in sl]
        est = kv(d / f"place_est_{dr}.txt")
        rt = kv(d / f"slack_{dr}.txt")
        pr = []
        pf = d / f"paths_route_{dr}.txt"
        for ln in (pf.read_text().splitlines() if pf.exists() else [])[:100]:
            f = ln.split("\t")
            pts = [grid().get(cells[c][1]) for c in f[6].split() if c in cells and grid().get(cells[c][1])]
            hops = sum(abs(u[0] - v[0]) + abs(u[1] - v[1]) for u, v in zip(pts, pts[1:]))
            pr.append((float(f[2]), float(f[3]), len(pts), hops))
        w = rt.get("wns_noicap")
        fmax = round(1000.0 / (period - float(w)), 2) if w not in (None, "none") else None
        rows.append({"directive": dr, "est_wns_noicap": est.get("wns_noicap"), "wns_noicap": w, "fmax_noicap": fmax,
                     "tns_noicap": rt.get("tns_noicap"), "slices": util_slices(d / f"util_{dr}.rpt"),
                     "used_slices": len(set(sl)), "sd_x": round(statistics.pstdev(xs), 1) if xs else None,
                     "sd_y": round(statistics.pstdev(ys), 1) if ys else None,
                     "worst100_logic": mean([p[0] for p in pr]), "worst100_net": mean([p[1] for p in pr]),
                     "worst100_cells": mean([p[2] for p in pr]), "worst100_hops": mean([p[3] for p in pr]),
                     "place_s": times.get(f"place_{dr}"), "route_s": times.get(f"route_{dr}")})
    print(f"{a.name}, period {period} ns, Vivado timer (route_design; est = after place_design)")
    print("| directive | est WNS | WNS | Fmax MHz | TNS | slices | sd x/y | worst-100 logic / net ns | cells | hops | place s |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['directive']} | {r['est_wns_noicap']} | {r['wns_noicap']} | {r['fmax_noicap']} | {r['tns_noicap']} | "
              f"{r['slices']} | {r['sd_x']} / {r['sd_y']} | {r['worst100_logic']} / {r['worst100_net']} | "
              f"{r['worst100_cells']} | {r['worst100_hops']} | {r['place_s']} |")
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    (CONFIG["out"] / f"directives_{a.name}.json").write_text(json.dumps(rows, indent=1) + "\n")


def log(a):
    t = Path(a.logfile).read_text(errors="replace").splitlines()
    cur = None
    for ln in t:
        if ln.startswith("VS_BEGIN") or ln.startswith("VS_END"):
            print(ln)
        m = re.match(r"^(Phase [\d.]+ .*?)(?: \| Checksum.*)?$", ln)
        if m and "Checksum" not in ln:
            cur = m.group(1)
        if re.search(r"WNS=|Physopt 32-(1035|1138|1044|232|775)|Place 30-(746|612)|LUT Combining|Total  |Retime|"
                     r"Very High Fanout|Estimated Timing|Global Iteration|Placer 30", ln):
            print(f"  [{cur}] {ln.strip()}")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("compare")
    c.add_argument("design")
    c.add_argument("--ours", nargs="*")
    c.add_argument("-k", type=int, default=CONFIG["top_paths"])
    h = sp.add_parser("hier")
    h.add_argument("name")
    h.add_argument("--dir", default="Default")
    h.add_argument("--depth", type=int, default=1)
    h.add_argument("--min-cells", type=int, default=20)
    h.add_argument("-k", type=int, default=100)
    dd = sp.add_parser("directives")
    dd.add_argument("name")
    lg = sp.add_parser("log")
    lg.add_argument("logfile")
    a = ap.parse_args()
    {"compare": compare, "hier": hier, "directives": directives, "log": log}[a.cmd](a)


if __name__ == "__main__":
    main()
