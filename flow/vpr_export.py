"""Export a synthesized netlist (yosys JSON, Xilinx unisim cells) to VPR's eblif for F4PGA's xc7a50t_test architecture.

No re-synthesis: the netlist's LUT/FF/CARRY4/RAM cells are only techmapped with F4PGA's xc7_vpr techmaps
(carry_map.v, fix_xc7_carry.py, clean_carry_map.v, cells_map.v), so every VPR atom traces back to one of our cells.
Private cell names ($abc$...) are made public first (prefix PFX) so the sub-cells a techmap makes keep the parent's
name as "<parent>.<sub>". Cells VPR's xc7 architecture has no model for (DSP48E1, ICAPE2) are dropped from the VPR
copy; nextpnr places them on import. Writes <out>/design.eblif, design.sdc, prep.json and export.json.
usage: vpr_export.py NETLIST.json TOP CONSTRAINTS.xdc OUTDIR [--period NS]"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VTR = ROOT / "toolchain" / "vtr"
TECHMAP = VTR / "arch" / "share" / "f4pga" / "techmaps" / "xc7_vpr" / "techmap"
FIX_CARRY = VTR / "f4pga" / "f4pga" / "utils" / "xc7" / "fix_xc7_carry.py"
YOSYS = ROOT / "toolchain" / "oss-cad-suite" / "bin" / "yosys"
PFX = "ofxP"
DROP = {"DSP48E1", "ICAPE2", "$scopeinfo"}


def prep(netlist, top, out):
    j = json.loads(Path(netlist).read_text())
    m = j["modules"][top]
    cells, dropped, renamed = {}, {}, 0
    for n, c in m["cells"].items():
        if c["type"] in DROP:
            dropped[n] = c["type"]
            continue
        if n.startswith("$"):
            n = PFX + n
            renamed += 1
        cells[n] = c
    m["cells"] = cells
    (out / "prep.json").write_text(json.dumps({"creator": j.get("creator", ""), "modules": {top: m}}))
    return dropped, renamed


YS = """
read_verilog -lib -specify +/xilinx/cells_sim.v
read_verilog -lib +/xilinx/cells_xtra.v
read_verilog -lib -overwrite {T}/iobs.v
read_json {out}/prep.json
hierarchy -check -top {top}
read_verilog -specify -lib {T}/cells_sim.v
techmap -map {T}/carry_map.v
proc
select {top}
write_json -selected {out}/carry_fixup.json
"""

YS2 = """
read_json {out}/carry_fixup_out.json
techmap -map {T}/clean_carry_map.v
read_verilog -lib -specify +/xilinx/cells_sim.v
read_verilog -lib +/xilinx/cells_xtra.v
read_verilog -lib -overwrite {T}/iobs.v
read_verilog -specify -lib {T}/cells_sim.v
hierarchy -check -top {top}
chtype -map CARRY4_VPR CARRY4_FIX
techmap -map {T}/cells_map.v
opt_expr -undriven
opt_clean
setundef -zero -params
attrmap -remove hdlname
proc
stat
select {top}
write_json -selected {out}/vpr.json
select -clear
write_blif -attr -cname -param -true VCC VCC -false GND GND -undef VCC VCC {out}/design.eblif
"""


def run_yosys(script, log):
    p = subprocess.run([str(YOSYS), "-q", "-l", str(log), "-s", "/dev/stdin"], input=script, text=True,
                       capture_output=True)
    if p.returncode:
        raise SystemExit(f"yosys failed ({log}): {p.stderr[-2000:]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("netlist")
    ap.add_argument("top")
    ap.add_argument("xdc")
    ap.add_argument("out")
    ap.add_argument("--period", type=float, default=5.0)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    dropped, renamed = prep(a.netlist, a.top, out)
    run_yosys(YS.format(T=TECHMAP, out=out, top=a.top), out / "yosys1.log")
    with open(out / "carry_fixup.json") as fi, open(out / "carry_fixup_out.json", "w") as fo:
        subprocess.run(["python3", "-I", str(FIX_CARRY)], stdin=fi, stdout=fo, check=True)
    run_yosys(YS2.format(T=TECHMAP, out=out, top=a.top), out / "yosys2.log")
    (out / "design.sdc").write_text(f"create_clock -period {a.period:g} *\n")
    pins = {}
    for ln in Path(a.xdc).read_text().splitlines():
        mm = re.search(r"PACKAGE_PIN\s+(\S+).*get_ports\s+(?:\{([^}]+)\}|([^\s\]]+))", ln)
        if mm:
            pins[(mm.group(2) or mm.group(3)).strip()] = mm.group(1)
    (out / "export.json").write_text(json.dumps({"netlist": str(Path(a.netlist).resolve()), "top": a.top,
                                                 "dropped": dropped, "renamed": renamed, "pins": pins,
                                                 "period": a.period}, indent=1) + "\n")
    print(f"exported {a.top}: dropped {len(dropped)} ({sorted(set(dropped.values()))}), renamed {renamed}, "
          f"pins {len(pins)}")


if __name__ == "__main__":
    main()
