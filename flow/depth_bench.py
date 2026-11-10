"""Path-depth study (Finding 17): nextpnr runs of the tu placer (pl15_tuonly_stub) on synthesis variants that cut
logic depth, for the exact Vivado import (flow/exact_src.py) and flow/path_cells.py.

  depth_bench.py [--designs rv_soc] [--variants dp_tu_x1 ...] [--seeds 1 2 3] [--run]

Variants are added to flow/place_bench.py's table at run time (that file is shared; nothing is written to it):
  dp_tu_x1        abc9 with arrival times (scratchpad abc9.xaiger 1)
  dp_tu_x1cal     + flat Vivado-calibrated LUT delays (flat200, -W 450), as synth_timing.py x1_cal
  dp_tu_x1cal_cdb + nextpnr -o carry-di-bypass (carry DI through the bypass pin, no feed-through LUT)
  dp_tu_x1calsyn2 x1_cal with the ABC script syn2 (&syn2; &dc2; &dch before &if)
Run directories: build/qor/oxc7/<variant>/<design>_p5/s<seed>, like every place_bench variant.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb
import qor_bench
import synth_timing

CONFIG = {
    "dry_run": True,
    "period": 5,
    "base": "pl15_tuonly_stub",
}


def synth_script(vname):
    return synth_timing.script("{top}", synth_timing.opts_of(vname), CONFIG["period"] * 1000)


VARIANTS = {
    "dp_tu_x1": {"synth_variant": "x1", "extra": []},
    "dp_tu_x1cal": {"synth_variant": "x1_cal", "extra": []},
    "dp_tu_x1cal_cdb": {"synth_variant": "x1_cal", "extra": ["-o", "carry-di-bypass"]},
    "dp_tu_x1calsyn2": {"synth_variant": "x1_cal_syn2", "extra": []},
    "dp_tudq_x1calsyn2": {"synth_variant": "dx1_cal_syn2", "extra": [], "base": "pl15_tuonly_dq"},
}


def install():
    for name, v in VARIANTS.items():
        base = pb.CONFIG["variants"][v.get("base", CONFIG["base"])]
        pb.CONFIG["variants"][name] = {"bin": base["bin"], "args": list(base["args"]) + v["extra"]}
    orig = pb.register

    def register(name):
        orig(name)
        if name in VARIANTS:
            sv = VARIANTS[name]["synth_variant"]
            qor_bench.CONFIG["variants"][name]["synth"] = synth_script(sv)
            if synth_timing.opts_of(sv)["dspq"]:
                qor_bench.CONFIG["variants"][name]["plugin"] = qor_bench.DSP_PLUGIN
    pb.register = register


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", default=["rv_soc"])
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    install()
    for d in a.designs:
        for v in a.variants:
            for s in a.seeds:
                r = pb.pnr_one(d, CONFIG["period"], v, s, dry)
                if not dry:
                    print(d, v, s, (r or {}).get("result"), flush=True)


if __name__ == "__main__":
    main()
