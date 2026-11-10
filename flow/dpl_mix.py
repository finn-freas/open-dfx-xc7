"""Mixed placements for Vivado's timer: one placement's slice packing at the other placement's global positions.

  dpl_mix.py --free rv_soc_p5_free --ours rv_soc_p5_dp0_s1_placed [--out-prefix rv_soc_p5_dp0_s1]
Reads both Vivado dumps (vivado/dpl_dump.tcl: cells.txt, and sites.txt of the dump root) and writes two sources for
flow/dpl_vivado.sh into build/qor/dpl/xsrc:
  <prefix>_mix_vpack_nglob : Vivado's slices (which cells share a slice, on which bels), each moved to the mean
                             position its cells have in our placement, legalised to the nearest free slice;
  <prefix>_mix_npack_vglob : our slices at Vivado's positions.
Carry chains move as one column piece. Block RAMs and DSPs keep the global source's sites. I/O and clock buffers are
left to Vivado. A third source, <prefix>_mix_vpack_vglob, runs Vivado's own slices through the same legaliser at
their own positions (a check that the legaliser changes nothing when nothing overlaps).
"""
import argparse
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dpl_metrics

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "dump_root": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/" + os.environ.get("DPL_XTIME", "dpl_xtime2")),
    "xsrc": ROOT / "build" / "qor" / "dpl" / "xsrc",
    "slicem_types": re.compile(r"^(RAM|SRL)"),
    "hard_prefix": ("RAMB", "DSP48"),
}
SITE_RE = re.compile(r"^SLICE_X(\d+)Y(\d+)$")


def load_sites():
    out = {}
    for ln in (CONFIG["dump_root"] / "sites.txt").read_text().splitlines():
        p = ln.split("\t")
        if len(p) >= 2:
            out[p[0]] = p[1]
    return out


def slices_of(place):
    sl = defaultdict(list)
    for c, v in place.items():
        if v["site"].startswith("SLICE_"):
            sl[v["site"]].append(c)
    return sl


def chains_of(place, nl, slices):
    nxt = {}
    for n, c in nl.cells.items():
        if c["type"] != "CARRY4":
            continue
        co = c["connections"].get("CO", [])
        if len(co) == 4 and not isinstance(co[3], str):
            for s, p in nl.sinks.get(co[3], []):
                if p == "CI" and nl.cells[s]["type"] == "CARRY4":
                    nxt[n] = s
    site_next = {}
    for a, b in nxt.items():
        if a in place and b in place:
            site_next[place[a]["site"]] = place[b]["site"]
    heads = set(site_next) - set(site_next.values())
    groups, used = [], set()
    for h in sorted(heads):
        g = [h]
        while g[-1] in site_next:
            g.append(site_next[g[-1]])
        ok = all(SITE_RE.match(s) for s in g)
        xs = {SITE_RE.match(s).group(1) for s in g} if ok else set()
        ys = [int(SITE_RE.match(s).group(2)) for s in g] if ok else []
        if ok and len(xs) == 1 and ys == list(range(ys[0], ys[0] + len(ys))):
            groups.append(g)
            used.update(g)
    for s in slices:
        if s not in used:
            groups.append([s])
    return groups


def build(pack, glob, nl, sites):
    grid = dpl_metrics.grid()
    slices = slices_of(pack)
    groups = chains_of(pack, nl, slices)
    gpos = {c: grid[v["site"]] for c, v in glob.items() if v["site"] in grid}
    slice_sites = {s: t for s, t in sites.items() if t in ("SLICEL", "SLICEM")}
    by_col = defaultdict(dict)
    for s in slice_sites:
        m = SITE_RE.match(s)
        by_col[int(m.group(1))][int(m.group(2))] = s
    free = set(slice_sites)
    out, disp = [], []
    hard = {c: v for c, v in glob.items() if v["site"].startswith(CONFIG["hard_prefix"])}
    for c, v in hard.items():
        out.append((c, v["site"], v["bel"].split(".")[-1]))

    def target(group):
        pts = [gpos[c] for s in group for c in slices[s] if c in gpos]
        if not pts:
            pts = [grid[s] for s in group if s in grid]
        return statistics.mean(p[0] for p in pts), statistics.mean(p[1] for p in pts)

    def needs_m(group):
        return any(CONFIG["slicem_types"].match(pack[c]["type"]) for s in group for c in slices[s])

    order = sorted(groups, key=lambda g: (-len(g), -sum(len(slices[s]) for s in g)))
    for g in order:
        tx, ty = target(g)
        need_m = needs_m(g)
        best, bd = None, None
        for col, ys in by_col.items():
            for y0, s0 in ys.items():
                cand = [ys.get(y0 + k) for k in range(len(g))]
                if any(c is None or c not in free for c in cand):
                    continue
                if need_m and any(slice_sites[c] != "SLICEM" for c in cand):
                    continue
                gx, gy = grid[s0]
                d = abs(gx - tx) + abs(gy - ty)
                if bd is None or d < bd:
                    best, bd = cand, d
        if best is None:
            continue
        disp.append(bd)
        for src, dst in zip(g, best):
            free.discard(dst)
            for c in slices[src]:
                out.append((c, dst, pack[c]["bel"].split(".")[-1]))
    return out, disp


def write_src(name, base, rows, disp):
    d = CONFIG["xsrc"] / name
    d.mkdir(parents=True, exist_ok=True)
    for f in ("netlist.edf", "top.txt", "constraints.xdc"):
        (d / f).write_bytes((CONFIG["xsrc"] / base / f).read_bytes())
    (d / "mode.txt").write_text("placed\n")
    (d / "place.txt").write_text("".join(f"{{{c}}} {s}/{b}\n" for c, s, b in rows))
    info = {"rows": len(rows), "groups": len(disp), "disp_mean": round(statistics.mean(disp), 2) if disp else None,
            "disp_max": max(disp) if disp else None, "from": base}
    (d / "place_info.json").write_text(json.dumps(info) + "\n")
    print(name, info)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--free", required=True)
    ap.add_argument("--ours", required=True)
    ap.add_argument("--out-prefix")
    a = ap.parse_args()
    prefix = a.out_prefix or a.ours.replace("_placed", "")
    free_dir, ours_dir = CONFIG["dump_root"] / a.free, CONFIG["dump_root"] / a.ours
    netlist = Path((CONFIG["xsrc"] / a.free / "netlist.txt").read_text().strip())
    nl = dpl_metrics.Netlist(netlist)
    sites = load_sites()
    V = dpl_metrics.read_cells(free_dir / "cells.txt")
    N = dpl_metrics.read_cells(ours_dir / "cells.txt")
    common = set(V) & set(N)
    V = {c: v for c, v in V.items() if c in common}
    N = {c: v for c, v in N.items() if c in common}
    print(f"cells in both placements: {len(common)}")
    for tag, pack, glob in (("vpack_nglob", V, N), ("npack_vglob", N, V), ("vpack_vglob", V, V)):
        rows, disp = build(pack, glob, nl, sites)
        write_src(f"{prefix}_mix_{tag}", a.ours, rows, disp)


if __name__ == "__main__":
    main()
