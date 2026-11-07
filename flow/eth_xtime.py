import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ddr_xtime as dx

ROOT = dx.ROOT

CONFIG = {
    "designs": ["arty_eth", "arty_scope"],
    "variant": "gapfix",
    "build": ROOT / "build" / "eth",
    "src_dir": ROOT / "designs" / "eth",
    "out": ROOT / "build" / "eth" / "xtime" / "src",
    "modes": ["placed", "free"],
    "dry_run": True,
}


def main():
    ap = argparse.ArgumentParser(description="Vivado's timer on the openXC7 LiteEth builds (qor_xtime method): "
                                             "nextpnr's placement imposed (placed) and the yosys netlist alone (free)")
    ap.add_argument("designs", nargs="*", default=CONFIG["designs"])
    ap.add_argument("--variant", default=CONFIG["variant"])
    ap.add_argument("--modes", nargs="+", default=CONFIG["modes"])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    names = []
    for d in a.designs:
        dx.CONFIG.update({"design": d, "modes": a.modes, "build": CONFIG["build"], "out": CONFIG["out"],
                          "xdc": CONFIG["src_dir"] / d / "digilent_arty.xdc"})
        names += dx.prep(a.variant, CONFIG["dry_run"] and not a.run)
    print("names: " + " ".join(names))
    print("vivado: vivado\\run_ddr3.ps1 -Script build_xtime.tcl -SrcSub build\\eth\\xtime\\src -Tag eth_xtime "
          f"-Names {','.join(names)} -Run")


if __name__ == "__main__":
    main()
