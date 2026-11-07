"""Vivado's timer on nextpnr builds of the incremental comparison (docs/incremental.md).

For each --run NAME:DIR:JSON (DIR holds <top>_routed.json, JSON is the netlist nextpnr read) it writes
build/incr/xtime/src/<tag>_<NAME>/ in vivado/build_xdctime.tcl's format: EDIF of the netlist with Vivado register
names, nextpnr's placement, the XDC. Vivado places every netlist cell where nextpnr put it and routes. Run Vivado
(under the shared lock, e.g. vivado/run_polite.sh) with
  vivado/run_qor.ps1 -Tag incr_xtime -Script build_xdctime.tcl -SrcRel build\\incr\\xtime\\src -Run
then --collect.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_xtime
import xdc_xtime

ROOT = qor_xtime.ROOT
CONFIG = {
    "out": ROOT / "build" / "incr" / "xtime" / "src",
    "vivado_out": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/incr_xtime"),
    "wns": re.compile(r"WNS\(ns\).*?\n[-\s]+\n\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+\d+\s+\d+\s+(-?\d+\.\d+)", re.S),
}


def prep(tag, top, xdc, runs):
    for spec in runs:
        name, d, js = spec.split(":", 2)
        d, js = Path(d), Path(js)
        o = CONFIG["out"] / f"{tag}_{name}"
        o.mkdir(parents=True, exist_ok=True)
        rn = xdc_xtime.renamed_json(js, o / "renamed.json")
        qor_xtime.write_netlist(o / "renamed.json", o / "netlist.edf", False)
        (o / "top.txt").write_text(top + "\n")
        (o / "mode.txt").write_text("placed\n")
        (o / "constraints.xdc").write_text(Path(xdc).read_text())
        rows, skipped = qor_xtime.placement(d / f"{top}_routed.json")
        rows = [(rn.get(n, n), b) for n, b in rows]
        (o / "place.txt").write_text("".join(f"{qor_xtime.tcl_quote(n)} {b}\n" for n, b in rows))
        (o / "place_info.json").write_text(json.dumps({"rows": len(rows), "skipped": skipped, "from": str(d)}) + "\n")
        print(f"{o}: {len(rows)} placed cells, {skipped} skipped")


def collect(tag):
    for v in sorted(CONFIG["vivado_out"].glob(f"{tag}_*")):
        st = (v / "status.txt").read_text().split("\n")[0] if (v / "status.txt").exists() else None
        rpt = (v / "timing.rpt").read_text(errors="replace") if (v / "timing.rpt").exists() else ""
        m = CONFIG["wns"].search(rpt)
        miss = (v / "place_missed.txt").read_text().count("\n") if (v / "place_missed.txt").exists() else None
        wns = float(m.group(1)) if m else None
        fmax = round(1000 / (10.0 - wns), 2) if wns is not None else None
        print(f"{v.name}: status {st}, WNS {wns} ns (Fmax at 10 ns: {fmax} MHz), WHS {m.group(3) if m else None}, "
              f"cells not placed from nextpnr: {miss}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", action="append", default=[], help="NAME:DIR:JSON")
    ap.add_argument("--tag", default="rv_soc")
    ap.add_argument("--top", default="rv_soc")
    ap.add_argument("--xdc", default=str(ROOT / "designs" / "rv_soc" / "arty_a7_35t.xdc"))
    ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()
    if a.collect:
        return collect(a.tag)
    prep(a.tag, a.top, a.xdc, a.run)


if __name__ == "__main__":
    main()
