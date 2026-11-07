import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "open-dfx-xc7/flow"))
import gap_build
import qor_area_litex as q

q.CONFIG["npwait_max"] = "3"
res = {}
for seed in (2, 3):
    gap_build.CONFIG["seed"] = seed
    for v in ("area_ref", "area_keepmem"):
        q.CONFIG["out"] = gap_build.ROOT / "build" / "qor" / "area" / "litex_seeds" / f"s{seed}"
        r = q.run("arty_ddr3", v, False)
        if r:
            n = r["nextpnr"]
            res[f"{v}/s{seed}"] = {"sys_clk": r["fmax_nextpnr"].get("sys_clk"), "lut_sites": n["slice_luts_vivado_rule"],
                                   "lutram": n["lut_mem_sites"]}
            print(v, seed, res[f"{v}/s{seed}"], flush=True)
out = gap_build.ROOT / "build/qor/area/litex_seeds/summary.json"
out.write_text(json.dumps(res, indent=1) + "\n")
print("end")
