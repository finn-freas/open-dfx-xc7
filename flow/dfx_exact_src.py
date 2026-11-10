"""Exact placement import of DFX configuration builds for Vivado's timer (flow/exact_src.py for build_pr_native
outputs): each build's own placement (every nextpnr cell, LUT pin locks, LUTRAM sub-cells) is imposed by
vivado/build_rte.tcl in "fixed" mode with no routes, so Vivado routes and times our placement.

  dfx_exact_src.py PREFIX BUILD_DIR... [--period 5] [--top rv_soc] [--xdc designs/rv_soc/arty_a7_35t.xdc] [--run]
names: <PREFIX>_<build dir name>_p<period>; then flow/dfx_exact_vivado.sh --run NAME...
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xroute

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "win_src": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/dfx_exact"),
    "tmp": ROOT / "build" / "dfx_exact",
}


def period_xdc(text, period):
    return re.sub(r"(create_clock\b[^\n]*-period\s+)[\d.]+", lambda m: m.group(1) + f"{period:.3f}", text)


def one(prefix, d, top, xdc, period, run):
    name = f"{prefix}_{d.name}_p{period:g}"
    dst = CONFIG["win_src"] / name
    print(f"[{'run' if run else 'dry'}] {d} -> {dst}")
    if not run or (dst / "netlist.edf").exists():
        return name
    fake = CONFIG["tmp"] / "run" / name
    fake.mkdir(parents=True, exist_ok=True)
    (fake / "status.json").write_text(json.dumps({"cmd": ["nextpnr", "--json", str(d / f"{top}.json")]}))
    npr = CONFIG["tmp"] / "npr" / name
    npr.mkdir(parents=True, exist_ok=True)
    rj = npr / "routed.json"
    if not rj.exists():
        rj.symlink_to(d / f"{top}_routed.json")
    px = CONFIG["tmp"] / "xdc" / f"{name}.xdc"
    px.parent.mkdir(parents=True, exist_ok=True)
    px.write_text(period_xdc(Path(xdc).read_text(), period))
    xroute.CONFIG["out"] = CONFIG["tmp"]
    xroute.name_of = lambda design, c="cal": name
    xroute.src_run = lambda design: fake
    xroute.dinfo = lambda design: {"top": top, "xdc": px}
    out = xroute.export(name, npr, False, "cal")
    shutil.copytree(out, dst)
    (dst / "mode.txt").write_text("fixed\n")
    (dst / "routes.txt").write_text("")
    (dst / "const_routes.txt").write_text("")
    print(json.loads((out / "export.json").read_text()).get("stats"))
    return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix")
    ap.add_argument("builds", nargs="+")
    ap.add_argument("--period", type=float, default=5)
    ap.add_argument("--top", default="rv_soc")
    ap.add_argument("--xdc", default=str(ROOT / "designs/rv_soc/arty_a7_35t.xdc"))
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    names = [one(a.prefix, Path(b).resolve(), a.top, a.xdc, a.period, a.run) for b in a.builds]
    print("names: " + " ".join(names))


if __name__ == "__main__":
    main()
