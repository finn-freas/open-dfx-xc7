"""Shape of a nextpnr placement, from the routed JSON (no Vivado needed): spread and density of the logic cells in
prjxray grid units (one CLB column is 2 in x), as flow/place_diag.py measures Vivado's dumps, plus slices and RAMB
sites. usage: place_shape.py [--seeds 1 2 3] --designs rv_soc bram --variants pl_base pl11_anc20ipw_stub"""
import argparse, json, re, statistics, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_compare as pc

CONFIG = {"runs": Path.home() / "open-dfx-xc7/build/qor/oxc7", "bin": 4}
TOPS = {"rv_soc": "qor_rv_soc", "bram": "qor_bram", "rv_big": "qor_rv_big", "rv_mul": "qor_rv_mul"}
LOGIC = re.compile(r"^(SLICE_LUTX|SLICE_FFX|CARRY4|SELMUX2_1|F7MUX|F8MUX)")


def shape(f, grid):
    m = next(iter(json.loads(f.read_text())["modules"].values()))
    pts, sites, rams = [], set(), []
    for c in m["cells"].values():
        b = c.get("attributes", {}).get("NEXTPNR_BEL", "")
        site = b.split("/")[0]
        if site.startswith("SLICE") and site in grid:
            sites.add(site)
            if LOGIC.match(c.get("type", "")) or c.get("type", "").startswith("SLICE"):
                pts.append(grid[site])
        elif site.startswith("RAMB36") or site.startswith("RAMB18"):
            rams.append(site)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    occ = Counter((x // CONFIG["bin"], y // CONFIG["bin"]) for x, y in pts)
    return {"cells": len(pts), "sd_x": statistics.pstdev(xs), "sd_y": statistics.pstdev(ys),
            "x_range": [min(xs), max(xs)], "y_range": [min(ys), max(ys)], "bins_used": len(occ),
            "bin_cells": statistics.mean(occ.values()), "slices": len(sites), "rams": sorted(set(rams))}


def hpwl_log(log):
    t = log.read_text(errors="replace") if log.exists() else ""
    leg = re.findall(r"HPWL after legalise: ([0-9.]+)", t)
    fm = re.findall(r"Max frequency for clock\s+'[^']+': ([0-9.]+) MHz", t)
    return (float(leg[-1]) if leg else None), (float(fm[-1]) if fm else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", required=True)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--json", help="also write the per-seed rows here")
    a = ap.parse_args()
    grid = pc.site_grid()
    print("| design | variant | nextpnr Fmax (nextpnr timer) | sd_x / sd_y | cells per used 4x4 bin | bins used | slices | HPWL after legalisation | seeds |")
    print("|---|---|---|---|---|---|---|---|---|")
    allrows = {}
    for d in a.designs:
        for v in a.variants:
            rows = []
            for s in a.seeds:
                run = CONFIG["runs"] / v / f"{d}_p5" / f"s{s}"
                f = run / f"{TOPS[d]}_routed.json"
                if not f.exists():
                    continue
                r = shape(f, pc.site_grid() if grid is None else grid)
                r["hpwl"], r["fmax"] = hpwl_log(run / "nextpnr.log")
                rows.append(r)
            if not rows:
                continue
            allrows[f"{d}|{v}"] = rows
            mn = lambda k: statistics.mean([r[k] for r in rows if r[k] is not None]) if any(r[k] is not None for r in rows) else float("nan")
            print(f"| {d} | {v} | {mn('fmax'):.2f} | {mn('sd_x'):.1f} / {mn('sd_y'):.1f} | {mn('bin_cells'):.1f} | "
                  f"{mn('bins_used'):.0f} | {mn('slices'):.0f} | {mn('hpwl'):.0f} | {len(rows)} |")
    if a.json:
        Path(a.json).write_text(json.dumps(allrows, indent=1) + "\n")


if __name__ == "__main__":
    main()
