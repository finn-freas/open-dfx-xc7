"""Critical-path breakdown on Vivado's timer for placement dumps (cells.txt + paths.txt, place_dump.tcl format):
for the K worst paths, mean datapath / logic / net delay, levels (cells on the path), hops (prjxray grid units),
net delay per hop and per net, and how close the steps sit: share of path steps that stay in one slice / one CLB
tile, LUT->FF steps in the same slice, CARRY4->CARRY4 steps in the next slice up.
usage: place_paths.py [-k 100] DUMP_DIR...   (a bare name is looked up in build/place_xtime2, then place_dump)"""
import argparse, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_compare as pc

VW = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build")


def resolve(n):
    p = Path(n)
    if p.is_dir():
        return p
    for d in (VW / "exact", VW / "place_xtime2", VW / "place_dump", VW / "dpl_xtime"):
        if (d / n).is_dir():
            return d / n
    raise SystemExit(f"no dump {n}")


def analyse(d, k, grid):
    cells = pc.read_cells(d / "cells.txt")
    rows = []
    for ln in (d / "paths.txt").read_text().splitlines()[:k]:
        f = ln.split("\t")
        if len(f) < 7:
            continue
        cl = [c for c in f[6].split() if c in cells]
        steps = list(zip(cl, cl[1:]))
        pos = lambda c: grid.get(cells[c]["site"])
        hops = sum(abs(pos(a)[0] - pos(b)[0]) + abs(pos(a)[1] - pos(b)[1]) for a, b in steps if pos(a) and pos(b))
        same_site = sum(cells[a]["site"] == cells[b]["site"] for a, b in steps)
        same_tile = sum(pos(a) == pos(b) for a, b in steps if pos(a) and pos(b))
        lutff = [(a, b) for a, b in steps if cells[a]["type"].startswith("LUT") and cells[b]["type"].startswith("FD")]
        cc = [(a, b) for a, b in steps if cells[a]["type"] == "CARRY4" and cells[b]["type"] == "CARRY4"]
        cc_adj = sum(1 for a, b in cc if pos(a) and pos(b) and pos(a)[0] == pos(b)[0] and abs(pos(a)[1] - pos(b)[1]) == 1)
        xs = [pos(c)[0] for c in cl if pos(c)]
        dx = [b - a for a, b in zip(xs, xs[1:]) if b != a]
        rev = sum(1 for a, b in zip(dx, dx[1:]) if (a > 0) != (b > 0))
        rows.append({"rev": rev, "mono": rev == 0, "slack": float(f[0]), "dp": float(f[1]), "logic": float(f[2]), "net": float(f[3]),
                     "levels": len(cl), "hops": hops, "steps": len(steps), "same_site": same_site,
                     "same_tile": same_tile, "lutff": len(lutff),
                     "lutff_same": sum(cells[a]["site"] == cells[b]["site"] for a, b in lutff),
                     "cc": len(cc), "cc_adj": cc_adj,
                     "luts": sum(cells[c]["type"].startswith("LUT") for c in cl),
                     "carries": sum(cells[c]["type"] == "CARRY4" for c in cl)})
    m = lambda key: statistics.mean(r[key] for r in rows)
    s = lambda key: sum(r[key] for r in rows)
    return {"rev": m("rev"), "mono": m("mono"), "paths": len(rows), "worst_slack": rows[0]["slack"] if rows else None, "dp": m("dp"), "logic": m("logic"),
            "net": m("net"), "levels": m("levels"), "luts": m("luts"), "carries": m("carries"), "hops": m("hops"),
            "net_per_hop": s("net") / max(1, s("hops")), "net_per_step": s("net") / max(1, s("steps")),
            "same_site": s("same_site") / max(1, s("steps")), "same_tile": s("same_tile") / max(1, s("steps")),
            "lutff_same": s("lutff_same") / max(1, s("lutff")), "cc_adj": s("cc_adj") / max(1, s("cc"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", type=int, default=100)
    ap.add_argument("dumps", nargs="+")
    a = ap.parse_args()
    grid = pc.site_grid()
    print(f"| dump | worst slack ns | datapath ns | logic ns | net ns | levels (LUT / CARRY4) | hops | net ps per hop | "
          f"net ps per step | steps in one slice | in one tile | LUT->FF in one slice | CARRY4->CARRY4 adjacent | "
          f"x reversals per path | monotone in x |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for n in a.dumps:
        r = analyse(resolve(n), a.k, grid)
        print(f"| {n} | {r['worst_slack']:.3f} | {r['dp']:.2f} | {r['logic']:.2f} | {r['net']:.2f} | {r['levels']:.1f} "
              f"({r['luts']:.1f} / {r['carries']:.1f}) | {r['hops']:.1f} | {1000 * r['net_per_hop']:.0f} | "
              f"{1000 * r['net_per_step']:.0f} | {100 * r['same_site']:.0f} % | {100 * r['same_tile']:.0f} % | "
              f"{100 * r['lutff_same']:.0f} % | {100 * r['cc_adj']:.0f} % | {r['rev']:.2f} | {100 * r['mono']:.0f} % |")


if __name__ == "__main__":
    main()
