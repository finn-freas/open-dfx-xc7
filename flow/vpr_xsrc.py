"""Vivado "placed"-mode source (vivado/build_xtime.tcl, flow/vpr_vivado.sh) straight from VPR's placement, without
nextpnr: VPR's bel for every yosys-netlist cell it placed (import_vpr.txt from flow/vpr_import.py, CARRY4 under its
netlist name), Vivado places the rest (distributed RAM, I/O, BUFG, DSP48E1, ICAPE2) and routes. Same netlist.edf
and constraints as flow/place_bench.py's xprep of the base run, so it compares with the base's placed-mode numbers.
usage: vpr_xsrc.py DESIGN SEED [--tag hi]"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb
import qor_bench
import qor_xtime as qx

ap = argparse.ArgumentParser()
ap.add_argument("design")
ap.add_argument("seed", type=int)
ap.add_argument("--tag", default="")
a = ap.parse_args()
d = a.design
vd = pb.ROOT / "build" / "vpr" / d / (f"{a.tag}_s{a.seed}" if a.tag else f"s{a.seed}")
name = f"{d}_p5_vpr{a.tag}_s{a.seed}_placed"
out = pb.CONFIG["out"] / "xsrc" / name
st = json.loads((pb.run_dir(d, 5, "pl14_off_stub", 1) / "status.json").read_text())
syn = Path(st["cmd"][st["cmd"].index("--json") + 1])
top = qor_bench.CONFIG["designs"][d]["top"]
out.mkdir(parents=True, exist_ok=True)
qx.write_netlist(syn, out / "netlist.edf", False)
(out / "top.txt").write_text(top + "\n")
(out / "mode.txt").write_text("placed\n")
(out / "constraints.xdc").write_text((qor_bench.CONFIG["out"] / "src" / f"{d}_p5" / "constraints.xdc").read_text())
(out / "dump.flag").touch()
rows = []
for ln in (vd / "import_vpr.txt").read_text().splitlines():
    c, b = ln.split("\t")
    rows.append((qx.CARRY_SPLIT.sub("", c), b))
(out / "place.txt").write_text("".join(f"{qx.tcl_quote(c)} {b}\n" for c, b in rows))
(out / "place_info.json").write_text(json.dumps({"rows": len(rows), "from": str(vd)}) + "\n")
print(name, len(rows))
