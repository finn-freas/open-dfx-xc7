"""Random-stimulus lockstep simulation of two yosys xc7 netlists of the same design (Finding 14): every input port
except the clock gets random values each cycle, every output is compared each cycle. Block RAMs use Xilinx's unisim
models from the local Vivado install (glbl holds GSR for 100 ns: inputs are held at 0 for the first 16 cycles and the
first 64 cycles are not compared).

  netlist_randsim.py GOLD.json GATE.json OUTDIR [--cycles 100000] [--clock clk] [--run]
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "yosys": ROOT / "toolchain/oss-cad-suite/bin/yosys",
    "bin": ROOT / "toolchain/oss-cad-suite/bin",
    "cells": ROOT / "toolchain/oss-cad-suite/share/yosys/xilinx/cells_sim.v",
    "unisim": Path("/mnt/c/AMDDesignTools/2025.2/Vivado/data/verilog/src"),
    "unisim_cells": ["RAMB18E1", "RAMB36E1"],
    "dry_run": True,
}


def top_ports(js):
    j = json.loads(Path(js).read_text())
    name, m = next((n, m) for n, m in j["modules"].items() if m.get("attributes", {}).get("top"))
    return name, {p: (v["direction"], len(v["bits"])) for p, v in m["ports"].items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold")
    ap.add_argument("gate")
    ap.add_argument("out")
    ap.add_argument("--cycles", type=int, default=100000)
    ap.add_argument("--clock", default="clk")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    top, ports = top_ports(a.gold)
    if CONFIG["dry_run"] and not a.run:
        print(f"[dry] {top}: {a.gold} vs {a.gate}, {a.cycles} cycles -> {out}")
        return
    out.mkdir(parents=True, exist_ok=True)
    for side, js in (("gold", a.gold), ("gate", a.gate)):
        v = out / f"{side}.v"
        subprocess.run([str(CONFIG["yosys"]), "-q", "-p", f"read_json {js}; hierarchy -top {top}; rename {top} {top}_{side}; "
                        f"write_verilog -noattr -selected {v}"], check=True)
    ins = [(p, w) for p, (d, w) in ports.items() if d == "input" and p != a.clock]
    outs = [(p, w) for p, (d, w) in ports.items() if d == "output"]
    decl = "".join(f"  reg [{w - 1}:0] {p} = 0;\n" for p, w in ins)
    decl += "".join(f"  wire [{w - 1}:0] g_{p}, h_{p};\n" for p, w in outs)
    conn = lambda pre: ", ".join([f".{a.clock}(clk)"] + [f".{p}({p})" for p, _ in ins] + [f".{p}({pre}_{p})" for p, _ in outs])
    rnd = "".join(f"      {p} = (i < 16) ? 0 : {{" + ", ".join(["$random(seed)"] * ((w + 31) // 32)) + "};\n" for p, w in ins)
    cmp = " || ".join(f"g_{p} !== h_{p}" for p, _ in outs) or "0"
    tb = f"""`timescale 1ns/1ps
module tb;
  reg clk = 0;
{decl}  {top}_gold u0({conn('g')});
  {top}_gate u1({conn('h')});
  integer i, mism = 0, seed = 11, changes = 0; reg [31:0] last = 0;
  initial begin
    for (i = 0; i < {a.cycles}; i = i + 1) begin
{rnd}      #5 clk = 1; #1;
      if (i > 64 && ({cmp})) begin mism = mism + 1; if (mism <= 3) $display("MISMATCH cycle %0d", i); end
      #4 clk = 0;
    end
    $display("RESULT {top} cycles %0d mismatches %0d", {a.cycles}, mism);
    $finish;
  end
endmodule
"""
    (out / "tb.v").write_text(tb)
    cells = out / "cells.v"
    txt, skip = [], False
    for ln in CONFIG["cells"].read_text().splitlines():
        if any(ln.startswith(f"module {c}") and ln[len(f"module {c}"):len(f"module {c}") + 1] in " (#" for c in CONFIG["unisim_cells"]):
            skip = True
        if not skip:
            txt.append(ln)
        elif ln.startswith("endmodule"):
            skip = False
    cells.write_text("\n".join(txt) + "\n")
    uni = []
    for c in CONFIG["unisim_cells"]:
        dst = out / f"{c}.v"
        if not dst.exists():
            dst.write_bytes((CONFIG["unisim"] / "unisims" / f"{c}.v").read_bytes())
        uni.append(str(dst))
    glbl = out / "glbl.v"
    if not glbl.exists():
        glbl.write_bytes((CONFIG["unisim"] / "glbl.v").read_bytes())
    env = {"PATH": f"{CONFIG['bin']}:/usr/bin:/bin"}
    r = subprocess.run(["iverilog", "-g2012", "-o", str(out / "sim.vvp"), "-s", "tb", "-s", "glbl", str(out / "tb.v"),
                        str(out / "gold.v"), str(out / "gate.v"), str(cells)] + uni + [str(glbl)],
                       capture_output=True, text=True, env=env)
    (out / "iverilog.log").write_text(r.stdout + r.stderr)
    if r.returncode:
        print("FAIL iverilog", out / "iverilog.log")
        return
    r = subprocess.run(["vvp", "-n", str(out / "sim.vvp")], capture_output=True, text=True, env=env)
    (out / "sim.log").write_text(r.stdout + r.stderr)
    print("\n".join(ln for ln in r.stdout.splitlines() if ln.startswith(("RESULT", "MISMATCH")))[:2000])


if __name__ == "__main__":
    main()
