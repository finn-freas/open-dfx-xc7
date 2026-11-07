import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_xtime as qx

ROOT = qx.ROOT

CONFIG = {
    "design": "arty_ddr3",
    "top": "digilent_arty",
    "variant": "gapfix",
    "build": ROOT / "build" / "ddr3",
    "xdc": ROOT / "designs" / "ddr3" / "arty_ddr3" / "digilent_arty.xdc",
    "out": ROOT / "build" / "ddr3" / "xtime" / "src",
    "modes": ("free", "placed"),
    "dry_run": True,
}


def prep(variant, dry):
    run = CONFIG["build"] / CONFIG["design"] / variant
    top = CONFIG["top"]
    made = []
    for mode in CONFIG["modes"]:
        d = CONFIG["out"] / f"{CONFIG['design']}_{variant}_{mode}"
        made.append(d.name)
        if dry:
            print(f"[dry] {d.relative_to(ROOT)}: netlist from {run.relative_to(ROOT)}/{top}.json, mode {mode}")
            continue
        d.mkdir(parents=True, exist_ok=True)
        qx.write_netlist(run / f"{top}.json", d / "netlist.edf", dry)
        (d / "top.txt").write_text(top + "\n")
        (d / "mode.txt").write_text(mode + "\n")
        (d / "constraints.xdc").write_text(CONFIG["xdc"].read_text())
        paths = qx.crit_paths(run / "report.json")
        (d / "paths.txt").write_text("".join(f"{qx.tcl_quote(a[0])} {a[1]} {qx.tcl_quote(b[0])} {b[1]} {dly:.3f}\n"
                                             for _, _, a, b, dly in paths))
        if mode == "placed":
            rows, skipped = qx.placement(run / f"{top}_routed.json")
            (d / "place.txt").write_text("".join(f"{qx.tcl_quote(n)} {b}\n" for n, b in rows))
            (d / "place_info.json").write_text(json.dumps({"rows": len(rows), "skipped": skipped,
                                                           "from": str(run.relative_to(ROOT))}) + "\n")
    return made


def main():
    ap = argparse.ArgumentParser(description="Vivado's timer on the openXC7 DDR3 build: the yosys netlist placed and "
                                             "routed by Vivado (free), and with nextpnr's placement imposed (placed)")
    ap.add_argument("--variant", default=CONFIG["variant"])
    ap.add_argument("--design", default=CONFIG["design"])
    ap.add_argument("--modes", nargs="+", default=list(CONFIG["modes"]))
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    CONFIG["design"], CONFIG["modes"] = a.design, a.modes
    CONFIG["xdc"] = ROOT / "designs" / "ddr3" / a.design / "digilent_arty.xdc"
    names = prep(a.variant, CONFIG["dry_run"] and not a.run)
    print("names: " + " ".join(names))
    print(f"vivado: run_ddr3.ps1 -Script build_xtime.tcl -SrcSub build\\ddr3\\xtime\\src -Tag ddr3_xtime -Names {' '.join(names)} -Run")


if __name__ == "__main__":
    main()
