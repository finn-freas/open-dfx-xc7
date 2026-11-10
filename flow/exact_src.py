"""Exact placement import for Vivado: a nextpnr run of flow/place_bench.py / flow/dpl_bench.py exported with
flow/xroute.py (nextpnr-made cells kept in the netlist, LUTRAM macros placed sub-cell by sub-cell, LUT pin locks),
routes left to Vivado. vivado/build_rte.tcl runs it in its "fixed" mode with an empty routes.txt, so Vivado places
nothing itself except what place_cell refuses (place_log.txt). Compare with the qor_xtime.placement() "placed" mode,
which imposes only cells of the yosys netlist.

  exact_src.py DESIGN VARIANT SEED [--period 5] [--run]   ->  designs/exact/<design>_p<ns>_<variant>_s<seed>_exact
then: RTE_OUT=.../build/exact RTE_ROUTE_DUMP=0 SRC=... flow/rte_dump_vivado.sh --run NAME
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb
import qor_bench
import xroute

CONFIG = {
    "win_src": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact"),
    "tmp": pb.ROOT / "build" / "exact",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design")
    ap.add_argument("variant")
    ap.add_argument("seed", type=int)
    ap.add_argument("--period", type=float, default=5)
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    run = pb.run_dir(a.design, a.period, a.variant, a.seed)
    st = json.loads((run / "status.json").read_text())
    top = qor_bench.CONFIG["designs"][a.design]["top"]
    xdc = next(x[4:] for x in st["cmd"] if x.startswith("xdc="))
    name = f"{a.design}_{qor_bench.ptag(a.period)}_{a.variant}_s{a.seed}_exact"
    dst = CONFIG["win_src"] / name
    print(f"[{'run' if a.run else 'dry'}] {run} -> {dst}")
    if not a.run or (dst / "netlist.edf").exists():
        return
    npr = CONFIG["tmp"] / "npr" / name
    npr.mkdir(parents=True, exist_ok=True)
    rj = npr / "routed.json"
    if not rj.exists():
        rj.symlink_to(run / f"{top}_routed.json")
    xroute.CONFIG["out"] = CONFIG["tmp"]
    xroute.name_of = lambda d, c="cal": name
    xroute.src_run = lambda d: run
    xroute.dinfo = lambda d: {"top": top, "xdc": xdc}
    d = xroute.export(a.design, npr, False, "cal")
    shutil.copytree(d, dst)
    (dst / "mode.txt").write_text("fixed\n")
    (dst / "routes.txt").write_text("")
    (dst / "const_routes.txt").write_text("")
    print(json.loads((d / "export.json").read_text()).get("stats"))


if __name__ == "__main__":
    main()
