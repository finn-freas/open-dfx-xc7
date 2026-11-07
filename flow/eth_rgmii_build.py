"""Gigabit Ethernet (LiteEth RGMII, liteeth.phy.s7rgmii: IDELAYE2 on the RX data, ODDR TX, BUFG RX clock) on the
Digilent Nexys Video (xc7a200tsbg484-1, Realtek RTL8211E RGMII PHY), through the open flow.

The SoC is LiteX's stock digilent_nexys_video target with --with-ethernet (MAC + CPU) and a small integrated
main RAM (no DDR3), generated with --toolchain vivado so the same Verilog/XDC also builds in Vivado.
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ddr_build as db
import gap_build
import device

ROOT = db.ROOT

CONFIG = {
    "dry_run": True,
    "target": "litex_boards.targets.digilent_nexys_video",
    "top": "digilent_nexys_video",
    "part": "xc7a200tsbg484-1",
    "base_args": ["--integrated-main-ram-size", "0x10000", "--with-ethernet",
                  "--eth-ip", "192.168.1.50"],
    "designs": {"nv_rgmii": 100},
    "gen_dir": ROOT / "build" / "eth_rgmii" / "gen",
    "src_dir": ROOT / "designs" / "eth_rgmii",
    "out_dir": ROOT / "build" / "eth_rgmii",
}


def args(name):
    return CONFIG["base_args"] + ["--sys-clk-freq", f"{CONFIG['designs'][name]}e6",
                                  "--csr-csv", str(CONFIG["gen_dir"] / name / "csr.csv")]


def setup(name):
    dev = device.resolve(CONFIG["part"])
    db.CONFIG.update({
        "target": CONFIG["target"], "top": CONFIG["top"],
        "designs": {n: args(n) for n in CONFIG["designs"]},
        "gen_dir": CONFIG["gen_dir"], "src_dir": CONFIG["src_dir"], "out_dir": CONFIG["out_dir"],
        "freq_mhz": CONFIG["designs"][name],
    })
    db.CONFIG["variants"]["stock"]["chipdb"] = str(Path(dev["chipdb"]).relative_to(ROOT))
    db.CONFIG["variants"]["stock"]["nextpnr"] = "ofx/npwait.sh"
    db.CONFIG["gate_busy"] = []
    os.environ.setdefault("OFX_NEXTPNR_BIN", str(ROOT / "toolchain" / "openxc7" / "bin" / "nextpnr-xilinx"))
    os.environ.setdefault("OFX_MAX_NEXTPNR", "2")
    gap_build.CONFIG.update({"part": CONFIG["part"], "family": dev["family"]})


def last_wins(xdc):
    """nextpnr stops on a second set_property of the same property on one port (LiteX's Nexys Video platform gives
    eth_rst_n IOSTANDARD LVCMOS25 from its group and LVCMOS33 from the pin). Vivado applies them in order, so the last
    one wins; keep only the last for nextpnr and report what was dropped."""
    lines = xdc.read_text().splitlines()
    rx = re.compile(r"^\s*set_property\s+(\S+)\s+\S+\s+\[get_ports\s+\{?([^}\]]+)\}?\]\s*$")
    last = {}
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if m:
            last[(m.group(1), m.group(2).strip())] = i
    keep, dropped = [], []
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if m and last[(m.group(1), m.group(2).strip())] != i:
            dropped.append(ln)
            continue
        keep.append(ln)
    if dropped:
        xdc.write_text("\n".join(keep) + "\n")
        for d in dropped:
            print(f"nextpnr xdc: dropped earlier duplicate (Vivado: last wins): {d}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("designs", nargs="*", default=list(CONFIG["designs"]))
    ap.add_argument("--gen-only", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    CONFIG["out_dir"].mkdir(parents=True, exist_ok=True)
    for name in a.designs:
        setup(name)
        gen = db.generate(name, args(name), dry)
        src = db.stage(name, gen, dry)
        if not dry:
            last_wins(src / "nextpnr" / f"{CONFIG['top']}.xdc")
        if a.gen_only:
            continue
        db.pnr(name, src, "stock", dry)


if __name__ == "__main__":
    main()
