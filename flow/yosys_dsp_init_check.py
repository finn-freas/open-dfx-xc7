import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "dry_run": True,
    "src": ROOT / "build" / "ofx" / "vhdl" / "yosys_dsp_init_assert",
    "out": ROOT / "build" / "yosys_dsp_init",
    "yosys": {
        "stock": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "yosys",
        "fixed": ROOT / "build" / "yosys-build" / "yosys-dspinit" / "yosys",
    },
    "datdir": ROOT / "toolchain" / "oss-cad-suite" / "share" / "yosys",
    "iverilog": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "iverilog",
    "vvp": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "vvp",
    "synth": "synth_xilinx -flatten -abc9 -arch xc7 -top {top}",
    "cases": {
        "rep": "16 bits of q (init 32'h1, bit 0 set) feed the multiplier; the set bit is outside them",
        "rep2": "the same with init 0 (passed before the fix)",
        "rep_in1": "the multiplier's A bits themselves have a 1 init: the register must stay in the fabric",
        "rep_p1": "the product register shares a cell with a bit whose init is 1",
        "rep_p1in": "a product register whose own bits have a 1 init: it must stay in the fabric",
    },
    "cycles": 5000,
    "x_init": "INIT(1'hx)",
    "x_init_as": "INIT(1'h0)",
    "seq": 12,
    "sat_timeout_s": 900,
    "noop": {
        "blinky": (["designs/blinky/blinky.v"], "blinky"),
        "rv_soc": (["build/qor/src/rv_soc_p5/qor_rv_soc.v", "build/qor/src/rv_soc_p5/picorv32.v",
                    "build/qor/src/rv_soc_p5/uart.v"], "qor_rv_soc"),
        "qor_rv_mul": (["build/qor/src/rv_mul_p5/qor_rv_mul.v", "build/qor/src/rv_mul_p5/picorv32.v",
                        "build/qor/src/rv_mul_p5/uart.v"], "qor_rv_mul"),
    },
    "creator_re": re.compile(r'^\s*"creator": .*$', re.M),
    "share": {
        "stock": f"{ROOT}/toolchain/oss-cad-suite/lib/../share/yosys/",
        "fixed": f"{ROOT}/build/yosys-build/yosys-dspinit/share/",
    },
}

EXTRA = {
    "rep_in1": """module rep_in1(input wire clk, input wire en, output wire [3:0] led);
    reg [31:0] q = 32'h00010000;
    reg [15:0] acc = 16'h0;
    reg [31:0] prod = 32'h0;
    always @(posedge clk) if (en) begin
        q <= {q[30:0], q[31] ^ q[21] ^ q[1] ^ q[0]};
        acc <= acc + q[15:0];
        prod <= q[31:16] * acc;
    end
    assign led = prod[3:0] ^ prod[31:28];
endmodule
""",
    "rep_p1": """module rep_p1(input wire clk, input wire en, input wire [15:0] a, input wire [15:0] b, output wire [3:0] led);
    reg [15:0] ra = 16'h0, rb = 16'h0;
    reg [32:0] r = 33'h100000000;
    always @(posedge clk) begin
        ra <= a;
        rb <= b;
        r <= {r[32] ^ en, ra * rb};
    end
    assign led = r[3:0] ^ r[31:28] ^ {3'b0, r[32]};
endmodule
""",
    "rep_p1in": """module rep_p1in(input wire clk, input wire en, input wire [15:0] a, input wire [15:0] b, output wire [3:0] led);
    reg [15:0] ra = 16'h0, rb = 16'h0;
    reg [31:0] r = 32'h00000005;
    always @(posedge clk) begin
        ra <= a;
        rb <= b;
        r <= ra * rb;
    end
    assign led = r[3:0] ^ r[31:28];
endmodule
""",
}

TB = """`timescale 1ns/1ps
module tb;
    reg clk = 0, en = 0;
    reg [15:0] a = 0, b = 0;
    wire [3:0] lg, ln;
    integer i, bad = 0;
    gold_top g(.clk(clk), .en(en){ab}, .led(lg));
    gate_top n(.clk(clk), .en(en){ab}, .led(ln));
    initial begin
        for (i = 0; i < {cycles}; i = i + 1) begin
            en = $random; a = $random; b = $random;
            #1;
            if (g.led !== n.led) begin
                bad = bad + 1;
                if (bad < 5) $display("mismatch cycle %0d gold %h gate %h", i, g.led, n.led);
            end
            #4 clk = 1; #5 clk = 0;
        end
        $display("RESULT cycles %0d mismatches %0d", {cycles}, bad);
        $finish;
    end
endmodule
"""


def run(cmd, log, dry, cwd=ROOT):
    print(f"[{'dry' if dry else 'run'}] {' '.join(str(c) for c in cmd)} > {log}")
    if dry:
        return 0
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w") as f:
        return subprocess.run([str(c) for c in cmd], stdout=f, stderr=subprocess.STDOUT, cwd=cwd).returncode


def source(case):
    f = CONFIG["src"] / f"{case}.v"
    if f.exists():
        return f
    g = CONFIG["out"] / "src" / f"{case}.v"
    g.parent.mkdir(parents=True, exist_ok=True)
    g.write_text(EXTRA[case])
    return g


def synth(case, which, dry):
    o = CONFIG["out"] / which / case
    net = o / f"{case}.v"
    if net.exists():
        return o, 0
    src = source(case)
    s = CONFIG["synth"].format(top=case)
    ys = (f"read_verilog {src}; {s}; tee -o {o / 'stat.txt'} stat;"
          f" write_json {o / (case + '.json')}; write_verilog -noattr {net}")
    if not dry:
        o.mkdir(parents=True, exist_ok=True)
    rc = run([CONFIG["yosys"][which], "-p", ys], o / "yosys.log", dry)
    return o, rc


def dsp_params(o, case):
    j = json.loads((o / f"{case}.json").read_text())
    m = j["modules"][case]
    out = []
    for n, c in m["cells"].items():
        if c["type"] == "DSP48E1":
            p = c["parameters"]
            out.append({k: int(p[k], 2) for k in ("AREG", "BREG", "MREG", "PREG") if k in p})
    ffs = [c for c in m["cells"].values() if c["type"].startswith("FD")]
    init1 = sum(1 for c in ffs if c["parameters"].get("INIT", "0").lstrip("0") == "1")
    return {"dsp": out, "ffs": len(ffs), "ffs_init1": init1}


def simulate(case, o, dry):
    res = o / "sim.result"
    if res.exists():
        return res.read_text().strip()
    if dry:
        return "dry"
    src = source(case)
    gold = o / "gold.v"
    gate = o / "gate.v"
    gold.write_text(re.sub(rf"\bmodule\s+{case}\b", "module gold_top", src.read_text()))
    net = re.sub(rf"\bmodule\s+{case}\b", "module gate_top", (o / f"{case}.v").read_text())
    gate.write_text(net.replace(CONFIG["x_init"], CONFIG["x_init_as"]))
    ab = ", .a(a), .b(b)" if "input wire [15:0] a" in src.read_text() else ""
    tb = o / "tb.v"
    tb.write_text(TB.replace("{cycles}", str(CONFIG["cycles"])).replace("{ab}", ab))
    cells = CONFIG["datdir"] / "xilinx" / "cells_sim.v"
    rc = run([CONFIG["iverilog"], "-g2012", "-o", o / "sim.vvp", "-DNO_ICE40_DEFAULT_ASSIGNMENTS", tb, gold, gate, cells],
             o / "iverilog.log", dry)
    if rc:
        out = f"iverilog failed ({o / 'iverilog.log'})"
    else:
        run([CONFIG["vvp"], "-n", o / "sim.vvp"], o / "sim.log", dry)
        lines = [ln for ln in (o / "sim.log").read_text().splitlines() if ln.startswith("RESULT")]
        out = lines[-1] if lines else f"no result ({o / 'sim.log'})"
    res.write_text(out + "\n")
    return out


def equiv(case, dry):
    o = CONFIG["out"] / "equiv" / case
    res = o / "result.txt"
    if res.exists():
        return res.read_text().strip()
    src = source(case)
    y = CONFIG["yosys"]["fixed"]
    s = CONFIG["synth"].format(top=case)
    if not dry:
        o.mkdir(parents=True, exist_ok=True)
    for side, stop in (("gold", "begin:map_dsp"), ("gate", "begin:coarse")):
        run([y, "-q", "-p", f"read_verilog {src}; {s} -run {stop}; rename {case} {side}; select {side}; "
                            f"write_rtlil -selected {o / (side + '.il')}"], o / f"{side}.log", dry)
    prep = (f"read_rtlil {o / 'gold.il'}; read_rtlil {o / 'gate.il'}; read_verilog -lib +/xilinx/cells_sim.v; "
            f"techmap -autoproc -map +/xilinx/cells_sim.v t:DSP48E1; proc; opt_clean; "
            f"miter -equiv -flatten -make_assert gold gate miter; hierarchy -top miter; "
            f"sat -verify -tempinduct -prove-asserts -set-init-zero -seq 1 -maxsteps {CONFIG['seq']} miter")
    log = o / "equiv.log"
    rc = 0 if log.exists() else run(["timeout", str(CONFIG["sat_timeout_s"]), y, "-p", prep], log, dry)
    if dry:
        return "dry"
    text = log.read_text(errors="replace")
    base = [int(n) for n in re.findall(r"Base case for induction length (\d+) proven", text)]
    if "Induction step proven: SUCCESS" in text:
        out = "proven (miter, temporal induction from the init state)"
    elif re.search(r"Base case for induction length \d+ failed|counter-?example", text, re.I):
        out = "FAIL: counterexample"
    elif rc == 124 or ("End of script" not in text and "Reached maximum number of time steps" not in text):
        out = f"timeout after {CONFIG['sat_timeout_s']} s; base case proven to length {max(base, default=0)}"
    else:
        out = (f"bounded: no counterexample in {max(base, default=0)} cycles from the init state "
               f"(induction does not close)")
    out += f" ({log})"
    res.write_text(out + "\n")
    return out


def noop(name, dry):
    files, top = CONFIG["noop"][name]
    rows = {}
    for which in ("stock", "fixed"):
        o = CONFIG["out"] / "noop" / name / which
        js = o / f"{top}.json"
        if not js.exists():
            if not dry:
                o.mkdir(parents=True, exist_ok=True)
            run([CONFIG["yosys"][which], "-p", f"read_verilog -sv {' '.join(str(ROOT / f) for f in files)}; "
                 f"{CONFIG['synth'].format(top=top)}; write_json {js}"], o / "yosys.log", dry,
                cwd=ROOT / Path(files[0]).parent)
        rows[which] = js
    if dry:
        return "dry"
    a, b = (CONFIG["creator_re"].sub("", rows[w].read_text()).replace(str(CONFIG["share"][w]), "SHARE/")
            for w in ("stock", "fixed"))
    return (f"identical apart from the creator line and the share directory in src attributes: {a == b} "
            f"({rows['stock']} vs {rows['fixed']})")


def main():
    ap = argparse.ArgumentParser(description="xilinx_dsp init fix: repro cases with the stock and fixed yosys, "
                                             "simulation and equivalence of the fixed result, no-op designs")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    report = {"cases": {}, "noop": {}}
    for case, what in CONFIG["cases"].items():
        r = {"what": what}
        for which in ("stock", "fixed"):
            o, rc = synth(case, which, dry)
            r[which] = {"rc": rc, "log": str(o / "yosys.log")}
            if not dry and rc == 0:
                r[which].update(dsp_params(o, case))
                r[which]["sim"] = simulate(case, o, dry)
            elif not dry:
                t = (o / "yosys.log").read_text(errors="replace")
                r[which]["error"] = next((ln for ln in t.splitlines() if "ERROR" in ln), "")
        r["equiv"] = equiv(case, dry)
        report["cases"][case] = r
    for name in CONFIG["noop"]:
        report["noop"][name] = noop(name, dry)
    print(json.dumps(report, indent=1))
    if not dry:
        (CONFIG["out"] / "report.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
