r"""DDR3 SoC (designs/ddr3/arty_ddr3, 100 MHz): nextpnr placer settings and seeds on the gapfix netlist, each staged
for Vivado's timer on nextpnr's placement (flow/xtime_prep.py, mode placed). The yosys netlist is the gapfix one
(build/ddr3/arty_ddr3/gapfix/digilent_arty.json), so only placement and routing change.

  ddr_place_sweep.py [--run] [configs...]
Then: vivado\run_ddr3.ps1 -Script build_xtime.tcl -SrcSub build\ddr3\sweep\xtime -Tag ddr3_sweep -Names <names> -Run
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_build

ROOT = gap_build.ROOT

CONFIG = {
    "src": ROOT / "designs" / "ddr3" / "arty_ddr3",
    "json": ROOT / "build" / "ddr3" / "arty_ddr3" / "gapfix" / "digilent_arty.json",
    "out": ROOT / "build" / "ddr3" / "sweep",
    "top": "digilent_arty",
    "nextpnr_bin": ROOT / "build" / "nextpnr-build" / "gapfix" / "nextpnr-himbaechel",
    "chipdb": ROOT / "toolchain" / "openxc7" / "share" / "nextpnr" / "himbaechel" / "xilinx" / "chipdb-xc7a50t.bin",
    "base_args": ["--timing-allow-fail"],
    "configs": {
        "heap_s2": (2, []), "heap_s3": (3, []),
        "static_s1": (1, ["--placer", "static"]), "static_s2": (2, ["--placer", "static"]),
        "static_s3": (3, ["--placer", "static"]),
        "sa_s1": (1, ["--placer", "sa"]),
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("configs", nargs="*", default=list(CONFIG["configs"]))
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    os.environ["OFX_NEXTPNR_BIN"] = str(CONFIG["nextpnr_bin"])
    os.environ.setdefault("OFX_MAX_NEXTPNR", "2")
    tools = {"nextpnr": str(ROOT / "ofx" / "npwait.sh"), "chipdb": str(CONFIG["chipdb"])}
    names = []
    for c in a.configs:
        seed, extra = CONFIG["configs"][c]
        out = CONFIG["out"] / c
        out.mkdir(parents=True, exist_ok=True)
        if not (out / f"{CONFIG['top']}.json").exists():
            shutil.copy2(CONFIG["json"], out / f"{CONFIG['top']}.json")
        gap_build.CONFIG["seed"] = seed
        src = CONFIG["src"]
        rtl = [src / f"{CONFIG['top']}.v"]
        gap_build.build("arty_ddr3", src, CONFIG["top"], rtl, src / "nextpnr" / f"{CONFIG['top']}.xdc", out, 100,
                        not a.run, CONFIG["base_args"] + extra, tools)
        if a.run and (out / f"{CONFIG['top']}_routed.json").exists():
            subprocess.run([sys.executable, str(ROOT / "flow" / "xtime_prep.py"), "--run-dir", str(out), "--top",
                            CONFIG["top"], "--xdc", str(src / f"{CONFIG['top']}.xdc"), "--name", f"ddr3_{c}",
                            "--out", str(CONFIG["out"] / "xtime"), "--modes", "placed"], check=True)
            names.append(f"ddr3_{c}_placed")
    print("names: " + ",".join(names))


if __name__ == "__main__":
    main()
