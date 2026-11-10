"""Path-depth study summary (Finding 14 round 3): Vivado-timer Fmax (exact import, ICAP paths excluded) and cells per
path on the 100 worst paths, per variant and seed.  usage: depth_summary.py [--json OUT]"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import path_cells

W = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build")
CONFIG = {
    "period_ns": 5.0,
    "design": "rv_soc",
    "designs": {
        "rv_big": [("tu (pl15_tuonly_stub)", "exact_sa", "pl15_tuonly_stub"),
                   ("tu + x1_cal_syn2", "exact", "dp_tu_x1calsyn2")],
        "bram": [("tu (pl15_tuonly_stub)", "exact_sa", "pl15_tuonly_stub"),
                 ("tu + x1_cal_syn2", "exact", "dp_tu_x1calsyn2")],
        "rv_mul": [("tu, DSP draft (pl15_tuonly_dq)", "exact_sa", "pl15_tuonly_dq"),
                   ("tu, DSP draft + x1_cal_syn2", "exact", "dp_tudq_x1calsyn2")],
    },
    "seeds": [1, 2, 3],
    "rows": [("tu (pl15_tuonly_stub)", "exact_sa", "pl15_tuonly_stub"),
             ("tu + x1 (abc9 arrival times)", "exact", "dp_tu_x1"),
             ("tu + x1_cal", "exact", "dp_tu_x1cal"),
             ("tu + x1_cal_syn2", "exact", "dp_tu_x1calsyn2"),
             ("tu + x1_cal + carry-di-bypass", "exact", "dp_tu_x1cal_cdb")],
}


def wns(d):
    p = d / "slack.txt"
    if not p.exists():
        return None
    for ln in p.read_text().splitlines():
        f = ln.split()
        if f and f[0] == "wns_noicap":
            return float(f[1])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--design", default=CONFIG["design"])
    a = ap.parse_args()
    CONFIG["design"] = a.design
    if a.design in CONFIG["designs"]:
        CONFIG["rows"] = CONFIG["designs"][a.design]
    res = {}
    print("| placement + netlist | Vivado Fmax MHz per seed (exact import, Vivado timer) | mean | cells/path (100 worst) | LUT2-6 | nextpnr LUTs | CARRY4 |")
    print("|---|---|---|---|---|---|---|")
    for label, sub, v in CONFIG["rows"]:
        fm, cp, lut, xr, cy = [], [], [], [], []
        for s in CONFIG["seeds"]:
            d = W / sub / f"{CONFIG['design']}_p5_{v}_s{s}_exact"
            if not (d / "slack.txt").exists():
                d = next((W / x / d.name for x in ("exact", "exact_sa") if (W / x / d.name / "slack.txt").exists()), d)
            w = wns(d)
            if w is None:
                fm.append(None)
                continue
            fm.append(round(1000.0 / (CONFIG["period_ns"] - w), 2))
            ps = path_cells.parse(d, 100)
            sm = path_cells.summary(ps)
            cp.append(sm["cells_per_path"])
            lut.append(sm["per_path"].get("lut", 0) + sm["per_path"].get("lut1", 0))
            xr.append(sm["per_path"].get("lut_xr", 0))
            cy.append(sm["per_path"].get("carry", 0))
        ok = [f for f in fm if f]
        mean = lambda x: round(statistics.mean(x), 2) if x else None
        res[v] = {"fmax": fm, "mean": mean(ok), "cells_per_path": mean(cp), "luts": mean(lut), "xr": mean(xr), "carry": mean(cy)}
        print(f"| {label} | {' / '.join(str(f) if f else '-' for f in fm)} | {mean(ok)} | {mean(cp)} | {mean(lut)} | {mean(xr)} | {mean(cy)} |")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
