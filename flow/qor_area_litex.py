import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_build
from qor_area import nextpnr_area, vivado_util

ROOT = gap_build.ROOT
VIV = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build")
NPR = "build/nextpnr-build/qorarea/nextpnr-himbaechel"
YS = "build/yosys-build/yosys-area/yosys"
YS_SYNX = "build/yosys-build/yosys-synx/yosys"
KEEPMEM = "scratchpad -set opt_dff.keep_memrd_regs 1; "
CHIPDB = "toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin"
BASE_ARGS = ["--timing-allow-fail", "-o", "hardblock-timing", "--placer", "static"]

CONFIG = {
    "dry_run": True,
    "out": ROOT / "build" / "qor" / "area" / "litex",
    "max_nextpnr": 3,
    "poll_s": 20,
    "designs": {
        "arty_ddr3": {"src": "designs/ddr3/arty_ddr3", "freq": 100,
                      "vivado_own": VIV / "ddr3" / "arty_ddr3", "vivado_free": VIV / "ddr3_xtime" / "arty_ddr3_gapfix_free"},
        "arty_eth": {"src": "designs/eth/arty_eth", "freq": 100,
                     "vivado_own": VIV / "eth" / "arty_eth", "vivado_free": VIV / "eth_xtime" / "arty_eth_gapfix_free"},
    },
    "variants": {
        "area_ref": {"synth_opts": "", "args": BASE_ARGS},
        "area_pnr": {"synth_opts": "", "args": BASE_ARGS + ["-o", "carry-di-bypass", "-o", "lut-pair"]},
        "area_all": {"synth_opts": "-share_aggressive -carry_minwidth 5",
                     "args": BASE_ARGS + ["-o", "carry-di-bypass", "-o", "lut-pair"]},
        "area_keepmem": {"synth_opts": "", "args": BASE_ARGS, "yosys": YS_SYNX, "yosys_pre": KEEPMEM},
        "area_x1": {"synth_opts": "", "args": BASE_ARGS, "yosys_pre": "scratchpad -set abc9.xaiger 1; "},
        "area_blockrule": {"synth_opts": "", "args": BASE_ARGS, "json_from": "blockrule"},
        "area_pnr_blockrule": {"synth_opts": "", "args": BASE_ARGS + ["-o", "carry-di-bypass", "-o", "lut-pair"],
                               "json_from": "blockrule"},
        "area_pnr_keepmem": {"synth_opts": "", "args": BASE_ARGS + ["-o", "carry-di-bypass", "-o", "lut-pair"],
                             "yosys": YS_SYNX, "yosys_pre": KEEPMEM},
    },
    "npwait": "ofx/npwait.sh",
    "npwait_max": "2",
}


def wait_gate():
    while True:
        n = subprocess.run(["pgrep", "-c", "-f", "^/[^ ]*nextpnr-himbaechel"], capture_output=True, text=True).stdout.strip()
        if int(n or 0) < CONFIG["max_nextpnr"]:
            return
        time.sleep(CONFIG["poll_s"])


def run(design, variant, dry):
    d, v = CONFIG["designs"][design], CONFIG["variants"][variant]
    src = ROOT / d["src"]
    top = (src / "top.txt").read_text().split()[0]
    rtl = [src / f"{top}.v", *sorted(p for p in src.glob("*.v") if p.name != f"{top}.v")]
    out = CONFIG["out"] / design / variant
    os.environ["OFX_NEXTPNR_BIN"] = str(ROOT / NPR)
    os.environ["OFX_MAX_NEXTPNR"] = CONFIG["npwait_max"]
    tools = {"nextpnr": str(ROOT / CONFIG["npwait"]), "chipdb": str(ROOT / CHIPDB), "yosys": str(ROOT / v.get("yosys", YS)),
             "yosys_plugin": str(ROOT / "build/yosys-plugin/clkbufmap_gapfix.so"), "clkbuf_pass": "clkbufmap_gapfix",
             "synth_opts": v["synth_opts"], "yosys_pre": v.get("yosys_pre", ""), "json_from": v.get("json_from")}
    if not dry:
        wait_gate()
    rec = gap_build.build(design, src, top, rtl, src / "nextpnr" / f"{top}.xdc", out, d["freq"], dry, v["args"], tools)
    if dry or not rec["stages"].get("pnr", {}).get("ok"):
        return None
    rp = json.loads((out / "report.json").read_text())
    fm = {k: round(x["achieved"], 2) for k, x in rp.get("fmax", {}).items()}
    area = nextpnr_area(out / f"{top}_routed.json", out / f"{top}.json")
    res = {"design": design, "variant": variant, "fmax_nextpnr": fm, "nextpnr": area,
           "nextpnr_log": str((out / "nextpnr.log").relative_to(ROOT)),
           "vivado_own": vivado_util(d["vivado_own"]), "vivado_free": vivado_util(d["vivado_free"])}
    (out / "area.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def main():
    ap = argparse.ArgumentParser(description="LiteX SoCs (DDR3, Ethernet) through the qorarea tools; area against Vivado")
    ap.add_argument("--designs", nargs="+", default=list(CONFIG["designs"]))
    ap.add_argument("--variants", nargs="+", default=list(CONFIG["variants"]))
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    for d in a.designs:
        for v in a.variants:
            r = run(d, v, dry)
            if r:
                n = r["nextpnr"]
                print(f"{d} {v}: fmax {r['fmax_nextpnr']} LUT sites {n['slice_luts_vivado_rule']} (+{n['sites_only_inserted']} "
                      f"feed-through only, {n['logic_pairs']} O5+O6) FF {n['ff']} CARRY4 {n['carry4']} LUTRAM {n['lut_mem_sites']}")


if __name__ == "__main__":
    main()
