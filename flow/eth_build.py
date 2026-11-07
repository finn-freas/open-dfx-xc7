import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ddr_build as db

ROOT = db.ROOT

CONFIG = {
    "dry_run": True,
    "base_args": ["--variant", "a7-35", "--integrated-main-ram-size", "0x10000",
                  "--with-ethernet", "--with-etherbone", "--eth-ip", "192.168.1.50"],
    "designs": {
        "arty_eth": ("litex_boards.targets.digilent_arty", 100),
        "arty_scope": ("flow.eth_scope_soc", 100),
        "arty_eth_s60": ("litex_boards.targets.digilent_arty", 60),
    },
    "gen_dir": ROOT / "build" / "eth" / "gen",
    "src_dir": ROOT / "designs" / "eth",
    "out_dir": ROOT / "build" / "eth",
}


def args(name):
    return CONFIG["base_args"] + ["--sys-clk-freq", f"{CONFIG['designs'][name][1]}e6", "--csr-csv", str(CONFIG["gen_dir"] / name / "csr.csv")]


def setup(name):
    db.CONFIG.update({
        "target": CONFIG["designs"][name][0],
        "designs": {n: args(n) for n in CONFIG["designs"]},
        "gen_dir": CONFIG["gen_dir"],
        "src_dir": CONFIG["src_dir"],
        "out_dir": CONFIG["out_dir"],
        "freq_mhz": CONFIG["designs"][name][1],
    })


def main():
    ap = argparse.ArgumentParser(description="LiteX/LiteEth (MAC + UDP/IP + Etherbone) SoCs for the Arty A7-35T, "
                                             "with and without LiteScope, through the open flow")
    ap.add_argument("designs", nargs="*", default=list(CONFIG["designs"]))
    ap.add_argument("--variant", action="append", help=f"one of {list(db.CONFIG['variants'])} (default gapfix)")
    ap.add_argument("--gen-only", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    CONFIG["out_dir"].mkdir(parents=True, exist_ok=True)
    for name in a.designs:
        setup(name)
        gen = db.generate(name, args(name), dry)
        src = db.stage(name, gen, dry)
        for f in ("csr.csv", "analyzer.csv"):
            if (gen / f).exists() and not dry:
                (src / f).write_text((gen / f).read_text())
        if a.gen_only:
            continue
        for variant in a.variant or ["gapfix"]:
            rec = db.pnr(name, src, variant, dry)
            if not dry:
                print(json.dumps({k: {kk: vv for kk, vv in s.items() if kk in ("ok", "seconds", "error")}
                                  for k, s in rec["stages"].items()}, indent=1))


if __name__ == "__main__":
    main()
