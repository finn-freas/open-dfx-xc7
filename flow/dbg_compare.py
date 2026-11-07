import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ddr_compare as dc

ROOT = dc.ROOT

CONFIG = {
    "designs": ["x_dbg_net_uart", "x_dbg_net_jtag", "x_dbg_ila_uart"],
    "top": "x_dbg_net",
    "variant": "gapfix",
    "build": ROOT / "build" / "dbg",
    "src": ROOT / "designs" / "dbg",
    "groups": ("IOB", "IOI", "CFG", "CLK_BUFG", "BRAM"),
}


def main():
    for d in sys.argv[1:] or CONFIG["designs"]:
        b = CONFIG["build"] / d
        dc.CONFIG["xdc"] = CONFIG["src"] / d / f"{CONFIG['top']}.xdc"
        r = dc.compare(b / "viv_dbg" / f"{d}.bit", b / CONFIG["variant"] / f"{CONFIG['top']}.bit",
                       b / f"cmp_{CONFIG['variant']}_vs_dbg")
        print("==", d, {k: sum(v.values()) for k, v in r["unknown_bits"].items()})
        for g in CONFIG["groups"]:
            x = r["groups"][g]
            print(f"  {g}: common {x['common']} viv-only {x['viv_only']} oxc7-only {x['oxc7_only']}; "
                  f"by type viv-only {x['by_type_nonpip']['viv_only'][:6]} oxc7-only {x['by_type_nonpip']['oxc7_only'][:6]}")
            if g in ("IOB", "CFG"):
                for k in ("viv_only_list", "oxc7_only_list"):
                    print("   ", k, [(y["f"], y["pin"]) for y in x[k]][:12])


if __name__ == "__main__":
    main()
