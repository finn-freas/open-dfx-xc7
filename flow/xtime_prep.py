r"""Stage any openXC7 build for Vivado's timer (vivado/build_xtime.tcl, the qor_xtime method):
'placed' imposes nextpnr's placement on the yosys netlist, 'free' lets Vivado place and route the same netlist.

  xtime_prep.py --run-dir DIR --top TOP --xdc FILE --name NAME [--part PART] [--out DIR] [--modes placed free] [--extra-xdc F]
DIR holds TOP.json, TOP_routed.json and report.json (a build_openxc7.py / ofx output directory).
Then: vivado\run_ddr3.ps1 -Script build_xtime.tcl -SrcSub <out relative to the repo> -Tag <tag> -Names <names> -Run
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_xtime as qx

ROOT = qx.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--top", required=True)
    ap.add_argument("--xdc", required=True)
    ap.add_argument("--extra-xdc", action="append", default=[])
    ap.add_argument("--name", required=True)
    ap.add_argument("--part")
    ap.add_argument("--out", default=str(ROOT / "build" / "xtime" / "src"))
    ap.add_argument("--modes", nargs="+", default=["placed", "free"])
    a = ap.parse_args()
    run = Path(a.run_dir).resolve()
    xdc = "\n".join(Path(f).read_text() for f in [a.xdc] + a.extra_xdc)
    names = []
    for mode in a.modes:
        d = Path(a.out).resolve() / f"{a.name}_{mode}"
        names.append(d.name)
        d.mkdir(parents=True, exist_ok=True)
        qx.write_netlist(run / f"{a.top}.json", d / "netlist.edf", False)
        (d / "top.txt").write_text(a.top + "\n")
        (d / "mode.txt").write_text(mode + "\n")
        if a.part:
            (d / "part.txt").write_text(a.part + "\n")
        (d / "constraints.xdc").write_text(xdc + "\n")
        paths = qx.crit_paths(run / "report.json")
        (d / "paths.txt").write_text("".join(f"{qx.tcl_quote(x[0])} {x[1]} {qx.tcl_quote(y[0])} {y[1]} {dly:.3f}\n"
                                             for _, _, x, y, dly in paths))
        if mode == "placed":
            rows, skipped = qx.placement(run / f"{a.top}_routed.json")
            (d / "place.txt").write_text("".join(f"{qx.tcl_quote(n)} {b}\n" for n, b in rows))
            (d / "place_info.json").write_text(json.dumps({"rows": len(rows), "skipped": skipped,
                                                           "from": str(run)}) + "\n")
    print("names: " + ",".join(names))


if __name__ == "__main__":
    main()
