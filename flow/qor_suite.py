"""Artix-7 QoR suite: open-source designs built by Vivado 2025.2 and by the open flow, compared per design.

Steps (each is a sub-command; all are dry runs unless --run is given):
  fetch    clone the pinned upstream sources into build/src/suite (official GitHub repos only)
  wrap     write build/qor_suite/<design>/src: sources, a suite_top wrapper (LFSR-driven inputs, XOR-reduced
           registered outputs, one clock pin, one output pin) and an XDC template
  probe    yosys-only synthesis of each wrapped design: cell counts (utilisation check, >= 10 %)
  open     the open flow (flow/build_openxc7.py: yosys, nextpnr through ofx/npwait.sh, fasm2frames, xc7frames2bit),
           with an Fmax sweep driven by nextpnr's timer; per-stage wall-clock times; placement metrics
  vivado   Vivado alone (synth_design, opt/place/route, write_bitstream, report_power) with an Fmax sweep driven by
           Vivado's timer, plus our placement timed by Vivado (place_cell of every nextpnr cell, Vivado routes)
           -- one batch session under the machine-wide Vivado lock
  report   docs/qor-scoreboard.md

Quick mode (--quick): the QUICK subset, one seed, one Vivado run per design at its start period.
Variant runs (placement/router agents): --variant NAME [--nextpnr BIN] [--np-arg ARG] [--np-opt K=V] [--synth CMDS]
puts the open-flow results under build/qor_suite/<design>/open/NAME and the report in
build/qor_suite/scoreboard_NAME.md (with a column against base). Example:
  qor_suite.py open --quick --variant anc20 --np-arg=--placer-static-anchor-init --np-arg=20 --run
  qor_suite.py vivado --quick --variant anc20 --modes placed --run    (Vivado timer on the variant's placement)
  qor_suite.py report --quick --variant anc20 --run
"""
import argparse
import collections
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "flow"))

SRC = ROOT / "build" / "src" / "suite"
VTR = SRC / "vtr" / "vtr_flow" / "benchmarks" / "verilog"
EPFL = SRC / "benchmarks" / "arithmetic"
VEX = ROOT / "toolchain" / "litex" / "src" / "pythondata-cpu-vexriscv" / "pythondata_cpu_vexriscv" / "verilog"

CONFIG = {
    "out": ROOT / "build" / "qor_suite",
    "doc": ROOT / "docs" / "qor-scoreboard.md",
    "win_work": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado"),
    "win_work_ps": r"C:\Users\finnf\open-dfx-xc7-vivado",
    "vivado_tag": "qor_suite",
    "slot_helper": ROOT / "vivado" / "vivado_slot.sh",
    "slot1_only": True,
    "yield_queues": [ROOT / "build" / "qor" / "place" / "gp" / "vq" / "names.txt"],
    "yield_procs": r"place_vqueue.sh worke[r]|dpl_vivad[o].sh|route_xtime.py vivad[o]|run_polit[e]|breadth_queu[e]",
    "yield_poll_s": 120,
    "vivado_budget_s": 1000000000,
    "vivado_bat": r"C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat",
    "tcl": ROOT / "vivado" / "qor_suite.tcl",
    "build_openxc7": ROOT / "flow" / "build_openxc7.py",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "nextpnr": ROOT / "toolchain" / "openxc7" / "bin" / "nextpnr-xilinx",
    "max_nextpnr": os.environ.get("OFX_MAX_NEXTPNR", "2"),
    "release": None,
    "mem_gb": 4,
    "dry_run": True,
    "sweep_runs": 3,
    "seeds": [1],
    "default_part": "xc7a35tcsg324-1",
    "pins": {"csg324": {"clk": "E3", "out": "H5"}},
    "util_min": 0.10,
    "capacity": {"xc7a35t": {"LUT": 20800, "FF": 41600, "BRAM36": 50, "DSP": 90},
                 "xc7a100t": {"LUT": 63400, "FF": 126800, "BRAM36": 135, "DSP": 240}},
    "weights": {"fmax": 1, "area": 1, "power": 1, "build_time": 1, "routability": 1},
    "verdict": {"better": 1.05, "par": 0.95},
    "quick": ["rv_big", "serv", "aes", "sha256", "bram", "axi_xbar"],
    "repos": {
                "serv": ("https://github.com/olofk/serv", "f200eb2ed7b69ac1c6b8eddd47654522aeee5ce8"),
        "aes": ("https://github.com/secworks/aes", "80dc4718e1dcbbdb4b0dd1bdb393d8f7b98981dc"),
        "sha256": ("https://github.com/secworks/sha256", "837c5cc396f001d18f2c765721c585716eb439ae"),
        "sha512": ("https://github.com/secworks/sha512", "e4cdf33418a3aa95cee25e1f0b1d8a6ede51c1bd"),
                "verilog-axi": ("https://github.com/alexforencich/verilog-axi", "516bd5dadc3365b7f9e225d2af8fe0b8d804fe53"),
        "benchmarks": ("https://github.com/lsils/benchmarks", "82d8cc6910419298e713a46644ed59fd3df53038"),
        "vtr": ("https://github.com/verilog-to-routing/vtr-verilog-to-routing", "8e1dfbb305a6d78da4e1641cdc09ff8cf2f05973"),
    },
    "vtr_ram": ROOT / "designs" / "qor_suite" / "vtr_ram.v",
}

DESIGNS = {
    "vexriscv": {"kind": "cpu", "origin": "pythondata-cpu-vexriscv (litex-hub, 642ecfed)", "files": [VEX / "VexRiscv_Full.v"],
                 "top": "VexRiscv", "reset": {"reset": 1}, "period": 6.0, "tie_undriven": True},
    "serv": {"kind": "cpu", "origin": "serv", "files": sorted((SRC / "serv/rtl").glob("serv_*.v")), "top": "serv_rf_top",
             "exclude": ["serv_synth_wrapper.v", "serv_debug.v"], "copies": 16, "reset": {"i_rst": 1}, "clock": "clk",
             "period": 5.0},
    "or1200": {"kind": "cpu", "origin": "vtr", "files": [VTR / "or1200.v"], "top": "or1200_flat", "ram": True,
               "period": 10.0},
    "aes": {"kind": "crypto", "origin": "aes", "files": [SRC / f"aes/src/rtl/{f}.v" for f in
            ("aes_core", "aes_encipher_block", "aes_decipher_block", "aes_key_mem", "aes_sbox", "aes_inv_sbox")],
            "top": "aes_core", "reset": {"reset_n": 0}, "period": 6.0},
    "sha256": {"kind": "crypto", "origin": "sha256", "files": [SRC / f"sha256/src/rtl/{f}.v" for f in
               ("sha256_core", "sha256_k_constants", "sha256_w_mem")], "top": "sha256_core", "reset": {"reset_n": 0},
               "copies": 2, "period": 6.0},
    "sha512": {"kind": "crypto", "origin": "sha512", "files": [SRC / f"sha512/src/rtl/{f}.v" for f in
               ("sha512_core", "sha512_h_constants", "sha512_k_constants", "sha512_w_mem")], "top": "sha512_core",
               "reset": {"reset_n": 0}, "period": 8.0},
    "vtr_sha": {"kind": "crypto", "origin": "vtr", "files": [VTR / "sha.v"], "top": "sha1", "copies": 4, "clock": "clk_i",
                "reset": {"rst_i": 1}, "period": 8.0},
    "bgm": {"kind": "dsp", "origin": "vtr", "files": [VTR / "bgm.v"], "top": "bgm", "clock": "clock", "reset": {"reset": 1},
            "period": 10.0},
    "diffeq2": {"kind": "dsp", "origin": "vtr", "files": [VTR / "diffeq2.v"], "top": "diffeq_f_systemC", "copies": 4,
                "reset": {"reset": 1}, "period": 10.0},
    "stereovision1": {"kind": "dsp", "origin": "vtr", "files": [VTR / "stereovision1.v"], "top": "sv_chip1_hierarchy_no_mem",
                      "clock": "tm3_clk_v0", "part": "xc7a100tcsg324-1", "period": 6.0},
    "blob_merge": {"kind": "logic", "origin": "vtr", "files": [VTR / "blob_merge.v"], "top": "RLE_BlobMerging",
                   "period": 8.0},
    "raygentop": {"kind": "memory", "origin": "vtr", "files": [VTR / "raygentop.v"], "top": "paj_raygentop_hierarchy_no_mem",
                  "ram": True, "copies": 2, "period": 8.0},
    "mkpktmerge": {"kind": "memory", "origin": "vtr", "files": [VTR / "mkPktMerge.v"], "top": "mkPktMerge", "ram": True,
                   "clock": "CLK", "reset": {"RST_N": 0}, "copies": 8, "period": 6.0},
    "axi_xbar": {"kind": "interconnect", "origin": "verilog-axi", "files": [SRC / f"verilog-axi/rtl/{f}.v" for f in
                 ("axi_crossbar", "axi_crossbar_addr", "axi_crossbar_rd", "axi_crossbar_wr", "axi_register_rd",
                  "axi_register_wr", "arbiter", "priority_encoder")], "top": "axi_crossbar",
                 "params": {"S_COUNT": 4, "M_COUNT": 4, "DATA_WIDTH": 64, "S_ID_WIDTH": 8}, "reset": {"rst": 1}, "period": 5.0},
    "epfl_sqrt": {"kind": "arith", "origin": "benchmarks", "files": [EPFL / "sqrt.v"], "top": "top", "clock": None, "period": 50.0},
    "epfl_log2": {"kind": "arith", "origin": "benchmarks", "files": [EPFL / "log2.v"], "top": "top", "clock": None, "period": 30.0},
    "epfl_sin": {"kind": "arith", "origin": "benchmarks", "files": [EPFL / "sin.v"], "top": "top", "clock": None, "copies": 2,
                 "period": 20.0},
    "epfl_mult": {"kind": "arith", "origin": "benchmarks", "files": [EPFL / "multiplier.v"], "top": "top", "clock": None,
                  "period": 20.0},
    "fir": {"kind": "dsp", "native": "designs/qor/qor_fir", "top": "qor_fir", "period": 5.0},
    "bram": {"kind": "memory", "native": "designs/qor/qor_bram", "top": "qor_bram", "period": 6.0},
    "rv_big": {"kind": "cpu", "native": "designs/qor/qor_rv_big", "top": "qor_rv_big", "period": 8.0},
}


def say(dry, msg):
    print(f"[{'dry' if dry else 'run'}] {msg}", flush=True)


def ptag(p):
    return f"p{p:g}".replace(".", "_")


def ddir(name):
    return CONFIG["out"] / name


def part_of(name):
    return DESIGNS[name].get("part", CONFIG["default_part"])


def mem_wait():
    while True:
        avail = int(re.search(r"MemAvailable:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1)) / 1048576
        if avail >= CONFIG["mem_gb"]:
            return
        time.sleep(20)



def cmd_fetch(a, dry):
    SRC.mkdir(parents=True, exist_ok=True)
    for name, (url, commit) in CONFIG["repos"].items():
        d = SRC / name
        if d.exists():
            have = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
            print(f"{name}: {have} {'(pinned)' if have == commit else '(pinned ' + commit + ')'}")
            continue
        sparse = name == "vtr"
        cmds = [["git", "clone", "-q", "--filter=blob:none", "--no-checkout"] + (["--sparse"] if sparse else []) + [url, str(d)]]
        if sparse:
            cmds.append(["git", "-C", str(d), "sparse-checkout", "set", "vtr_flow/benchmarks/verilog"])
        cmds.append(["git", "-C", str(d), "checkout", "-q", commit])
        for c in cmds:
            say(dry, " ".join(c))
            if not dry:
                subprocess.run(c, check=True)



def files_of(name):
    d = DESIGNS[name]
    fs = [Path(f) for f in d["files"] if Path(f).name not in d.get("exclude", [])]
    if d.get("ram"):
        fs.append(CONFIG["vtr_ram"])
    return fs


def yosys_bin():
    from build_openxc7 import tool
    return tool("yosys")


def dut_ports(name, workdir):
    d = DESIGNS[name]
    chp = " ".join(f"-chparam {k} {v}" for k, v in d.get("params", {}).items())
    js = workdir / "ports.json"
    script = (f"read_verilog -sv {' '.join(str(f) for f in files_of(name))}; hierarchy -top {d['top']} {chp}; "
              f"proc; select -module {d['top']}; write_json -selected {js}")
    r = subprocess.run([yosys_bin(), "-q", "-p", script], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{name}: yosys port read failed: {r.stderr[-2000:]}")
    mods = json.loads(js.read_text())["modules"]
    m = mods.get(d["top"]) or next(iter(mods.values()))
    return [(p, v["direction"], len(v["bits"])) for p, v in m["ports"].items()]


def vid(p):
    return p if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", p) else "\\" + p + " "


def wrapper(name, ports):
    d = DESIGNS[name]
    clock = d.get("clock", "clk")
    resets = d.get("reset", {})
    copies = d.get("copies", 1)
    ins = [(p, w) for p, dr, w in ports if dr == "input" and p != clock and p not in resets]
    outs = [(p, w) for p, dr, w in ports if dr == "output"]
    bad = [p for p, dr, w in ports if dr not in ("input", "output")]
    if bad:
        raise RuntimeError(f"{name}: inout ports {bad}")
    if clock is not None and clock not in [p for p, _, _ in ports]:
        raise RuntimeError(f"{name}: no clock port {clock}")
    ni = max(1, sum(w for _, w in ins))
    no = sum(w for _, w in outs)
    params = d.get("params", {})
    pstr = (" #(" + ", ".join(f".{k}({v})" for k, v in params.items()) + ")") if params else ""
    v = [f"// generated by flow/qor_suite.py wrap: {copies} x {d['top']}, inputs from an LFSR, outputs XOR-reduced",
         "module suite_top (input wire clk, output reg dout);",
         "    reg [31:0] lfsr = 32'h1;",
         "    always @(posedge clk) lfsr <= {lfsr[30:0], lfsr[31] ^ lfsr[21] ^ lfsr[1] ^ lfsr[0]};",
         "    reg [7:0] rcnt = 8'd0;",
         "    wire rst = rcnt != 8'hff;",
         "    always @(posedge clk) if (rst) rcnt <= rcnt + 8'd1;"]
    nout = no * copies
    v.append(f"    wire [{nout - 1}:0] q;")
    for c in range(copies):
        v.append(f"    reg [{ni - 1}:0] din{c} = {ni}'d{c};")
        if ni <= 32:
            v.append(f"    always @(posedge clk) din{c} <= lfsr[{ni - 1}:0] ^ {ni}'d{c};")
        else:
            v.append(f"    always @(posedge clk) din{c} <= {{din{c}[{ni - 33}:0], lfsr ^ 32'd{c}}};")
        conns, off, qo = [], 0, c * no
        if clock is not None:
            conns.append(f".{clock}(clk)")
        for r, lvl in resets.items():
            conns.append(f".{r}({'rst' if lvl else '~rst'})")
        for p, w in ins:
            conns.append(f".{vid(p)}(din{c}[{off + w - 1}:{off}])")
            off += w
        for p, w in outs:
            conns.append(f".{vid(p)}(q[{qo + w - 1}:{qo}])")
            qo += w
        v.append(f"    {d['top']}{pstr} u{c} (" + ", ".join(conns) + ");")
    v.append(f"    reg [{nout - 1}:0] qr;")
    v.append("    always @(posedge clk) qr <= q;")
    n1 = (nout + 31) // 32
    v.append(f"    reg [{n1 - 1}:0] x1;")
    v.append(f"    genvar g;")
    v.append(f"    generate for (g = 0; g < {n1}; g = g + 1) begin : l1")
    v.append(f"        always @(posedge clk) x1[g] <= ^qr[(g * 32 + 31 < {nout} ? g * 32 + 31 : {nout - 1}):g * 32];")
    v.append("    end endgenerate")
    n2 = (n1 + 31) // 32
    v.append(f"    reg [{n2 - 1}:0] x2;")
    v.append(f"    generate for (g = 0; g < {n2}; g = g + 1) begin : l2")
    v.append(f"        always @(posedge clk) x2[g] <= ^x1[(g * 32 + 31 < {n1} ? g * 32 + 31 : {n1 - 1}):g * 32];")
    v.append("    end endgenerate")
    v.append("    always @(posedge clk) dout <= ^x2;")
    v.append("endmodule")
    return "\n".join(v) + "\n", {"inputs": ni, "outputs": no, "copies": copies}


def xdc_text(name, period):
    pk = re.search(r"(csg324|cpg236|fgg484|ftg256|sbg484|csg325)", part_of(name)).group(1)
    pins = CONFIG["pins"][pk]
    d = DESIGNS[name]
    if d.get("native"):
        t = (ddir(name) / "src" / "constraints.xdc.in").read_text()
        return re.sub(r"(create_clock[^\n]*-period\s+)[\d.]+", lambda m: f"{m.group(1)}{period:.3f}", t)
    return (f"set_property -dict {{ PACKAGE_PIN {pins['clk']} IOSTANDARD LVCMOS33 }} [get_ports clk]\n"
            f"create_clock -period {period:.3f} [get_ports clk]\n"
            f"set_property -dict {{ PACKAGE_PIN {pins['out']} IOSTANDARD LVCMOS33 }} [get_ports dout]\n")


def tie_undriven(name, s):
    """Undriven internal wires (VexRiscv's generated RTL has 18 bits) are x to yosys and 0 to Vivado (Synth 8-3295
    ties undriven pins to GND), so the two tools would build different logic. Tie them to 0 in the shared source copy,
    which is what Vivado does anyway."""
    d = DESIGNS[name]
    files = [f for f in (s / "files.txt").read_text().split() if f != "suite_top.v"]
    r = subprocess.run([yosys_bin(), "-q", "-p", f"read_verilog -sv {' '.join(files)}; hierarchy -top {d['top']}; proc; "
                        "opt_clean; check"], cwd=s, capture_output=True, text=True)
    und = collections.defaultdict(list)
    for mod, wire, bit in re.findall(r"Wire (\w+)\.\\(\S+)(?: \[(\d+)\])? is used but has no driver", r.stdout + r.stderr):
        und[mod].append((wire, bit))
    tied = 0
    for f in files:
        t = (s / f).read_text()
        for mod, ws in und.items():
            m = re.search(rf"^module {re.escape(mod)}\b.*?^endmodule", t, re.S | re.M)
            if not m:
                continue
            body = "".join(f"  assign {w}{'[' + b + ']' if b else ''} = 1'b0;  // tied by qor_suite.py (undriven)\n"
                           for w, b in ws)
            end = m.end() - len("endmodule")
            t = t[:end] + body + t[end:]
            tied += len(ws)
        (s / f).write_text(t)
    print(f"{name}: tied {tied} undriven wire bits to 0")
    return tied


def cmd_wrap(names, dry):
    for name in names:
        d = DESIGNS[name]
        s = ddir(name) / "src"
        say(dry, f"wrap {name} -> {s}")
        if dry:
            continue
        if s.exists():
            shutil.rmtree(s)
        s.mkdir(parents=True)
        info = {"design": name, "kind": d["kind"], "part": part_of(name)}
        if d.get("native"):
            src = ROOT / d["native"]
            for f in src.iterdir():
                if f.suffix in (".v", ".hex"):
                    shutil.copy(f, s / f.name)
            shutil.copy(next(src.glob("*.xdc")), s / "constraints.xdc.in")
            info.update(top=d["top"], files=sorted(f.name for f in s.glob("*.v")), origin=f"repo {d['native']}")
        else:
            for f in files_of(name):
                shutil.copy(f, s / f.name)
            try:
                ports = dut_ports(name, s)
                text, winfo = wrapper(name, ports)
            except RuntimeError as e:
                print(f"WRAP FAILED {e}")
                ports = [(p, dr, w) for p, dr, w in (dut_ports(name, s) if "no clock" in str(e) else [])]
                if ports:
                    print("   ports: " + " ".join(f"{p}:{dr[0]}{w}" for p, dr, w in ports)[:400])
                continue
            (s / "ports.json").unlink()
            (s / "suite_top.v").write_text(text)
            (s / "files.txt").write_text("\n".join(sorted(f.name for f in s.glob("*.v"))) + "\n")
            if d.get("tie_undriven"):
                winfo["tied_undriven"] = tie_undriven(name, s)
            url, commit = CONFIG["repos"].get(d["origin"], (d["origin"], ""))
            info.update(top="suite_top", files=sorted(f.name for f in s.glob("*.v")), dut=d["top"],
                        params=d.get("params", {}), origin=f"{url} {commit}".strip(), **winfo)
        (s / "files.txt").write_text("\n".join(info["files"]) + "\n")
        (s / "top.txt").write_text(info["top"] + "\n")
        (s / "part.txt").write_text(info["part"] + "\n")
        (s / "info.json").write_text(json.dumps(info, indent=1) + "\n")



def stat_cells(js):
    m = json.loads(Path(js).read_text())["modules"]
    top = next(k for k, v in m.items() if v.get("attributes", {}).get("top"))
    c = collections.Counter(v["type"] for v in m[top]["cells"].values())
    lut = sum(n for t, n in c.items() if re.fullmatch(r"LUT\d|LUT6_2", t))
    lutram = sum(n for t, n in c.items() if t.startswith(("RAM32", "RAM64", "RAM128", "RAM256", "SRL")))
    ff = sum(n for t, n in c.items() if re.fullmatch(r"FD[CPRS]E(_1)?|LD[CP]E", t))
    bram = sum(n * (1 if t.startswith("RAMB36") else 0.5) for t, n in c.items() if t.startswith("RAMB"))
    dsp = sum(n for t, n in c.items() if t.startswith("DSP48"))
    carry = sum(n for t, n in c.items() if t == "CARRY4")
    return {"LUT": lut, "LUTRAM": lutram, "FF": ff, "BRAM36": bram, "DSP": dsp, "CARRY4": carry}


def util_frac(name, cells):
    die = re.match(r"(xc7a\d+t)", part_of(name)).group(1)
    die = "xc7a35t" if die in ("xc7a35t", "xc7a50t") else die
    cap = CONFIG["capacity"][die]
    return max(cells.get(k, 0) / cap[k] for k in cap)


def cmd_probe(names, dry):
    for name in names:
        s = ddir(name) / "src"
        js = ddir(name) / "probe.json"
        say(dry, f"probe {name}")
        if dry:
            continue
        files = (s / "files.txt").read_text().split()
        top = (s / "top.txt").read_text().strip()
        t0 = time.time()
        r = subprocess.run([yosys_bin(), "-q", "-l", str(ddir(name) / "probe.log"), "-p",
                            f"read_verilog -sv {' '.join(files)}; synth_xilinx -flatten -abc9 -arch xc7 -top {top}; "
                            f"write_json {js}"], cwd=s, capture_output=True, text=True)
        if r.returncode:
            print(f"{name}: yosys failed: {(r.stderr or '')[-600:]}")
            continue
        c = stat_cells(js)
        print(f"{name}: {c} util {util_frac(name, c) * 100:.1f}% of {part_of(name)} ({time.time() - t0:.0f} s)")



def run_dir(name, period, seed, label):
    return ddir(name) / "open" / label / f"{ptag(period)}_s{seed}"


def parse_stage_times(log):
    t, cur = {}, None
    for line in log.splitlines():
        m = re.match(r"\[run\] (\w+):", line)
        if m:
            cur = m.group(1)
        m = re.match(r"\s+([\d.]+)s, log", line)
        if m and cur:
            t[cur] = float(m.group(1))
    return t


def nextpnr_metrics(log_text):
    fm = re.findall(r"Max frequency for clock\s+'([^']+)': ([\d.]+) MHz", log_text)
    route = sum(float(x) for x in re.findall(r"Router[12] time ([\d.]+)s", log_text))
    util = {}
    for k, n in re.findall(r"^Info:\s+(\w+):\s+(\d+)/\s*\d+", log_text, re.M):
        util[k] = int(n)
    return {"fmax_nextpnr": float(fm[-1][1]) if fm else None, "route_s_log": route, "util_nextpnr": util}


_GRID = {}


def grid(part):
    import device
    r = device.resolve(part)
    if r["fabric"] not in _GRID:
        tg = json.loads((Path(r["db_root"]) / r["family"] / r["fabric"] / "tilegrid.json").read_text())
        site, tile_xy, xy_type = {}, {}, {}
        for tn, t in tg.items():
            xy = (t["grid_x"], t["grid_y"])
            tile_xy[tn] = xy
            xy_type[xy] = t["type"]
            for s in t.get("sites", {}):
                site[s] = xy
        _GRID[r["fabric"]] = {"site": site, "tile": tile_xy, "type": xy_type}
    return _GRID[r["fabric"]]


def place_metrics(nets_sites, int_pips, part):
    """nets_sites: list of site lists (one per signal net); int_pips: Counter tile (x, y) -> used pips in INT tiles."""
    g = grid(part)
    hpwl, n = 0, 0
    for sites in nets_sites:
        xy = [g["site"][s] for s in sites if s in g["site"]]
        if len(xy) < 2:
            continue
        xs, ys = [p[0] for p in xy], [p[1] for p in xy]
        hpwl += (max(xs) - min(xs)) + (max(ys) - min(ys))
        n += 1
    vals = sorted(int_pips.values())
    pct = lambda q: vals[min(len(vals) - 1, int(q * len(vals)))] if vals else 0
    return {"hpwl": hpwl, "hpwl_nets": n, "routed_int_pips": sum(vals), "int_tiles_used": len(vals),
            "int_pips_peak": vals[-1] if vals else 0, "int_pips_p99": pct(0.99), "int_pips_mean": (sum(vals) / len(vals)) if vals else 0}


def open_place_metrics(routed, part):
    j = json.loads(Path(routed).read_text())
    m = j["modules"][next(iter(j["modules"]))]
    g = grid(part)
    cell_site = {}
    glob_types = {"BUFGCTRL", "BUFG", "PSEUDO_GND", "PSEUDO_VCC"}
    glob_nets = set()
    bits_cells = collections.defaultdict(set)
    for cn, c in m["cells"].items():
        bel = c["attributes"].get("NEXTPNR_BEL")
        if not bel:
            continue
        site = bel.split("/")[0]
        for p, bits in c["connections"].items():
            for b in bits:
                if isinstance(b, int):
                    bits_cells[b].add(site)
                    if c["type"] in glob_types and c.get("port_directions", {}).get(p) == "output":
                        glob_nets.add(b)
    nets_sites, pips = [], collections.Counter()
    seen = set()
    for nn, nv in m["netnames"].items():
        bits = nv["bits"]
        if len(bits) != 1 or not isinstance(bits[0], int) or bits[0] in seen:
            continue
        b = bits[0]
        seen.add(b)
        if b in glob_nets:
            continue
        nets_sites.append(sorted(bits_cells.get(b, ())))
        rt = nv["attributes"].get("ROUTING", "").split(";")
        for i in range(1, len(rt), 3):
            mm = re.match(r"X(\d+)Y(\d+)/([^/.]+)/([^/.]+)$", rt[i])
            if mm:
                xy = (int(mm.group(1)), int(mm.group(2)))
                if g["type"].get(xy, "").startswith("INT_"):
                    pips[xy] += 1
    return place_metrics(nets_sites, pips, part)


def release_args(name, xdc):
    """build_openxc7 arguments for the release defaults of CONFIG["release"] (an install prefix)."""
    sys.path.insert(0, str(ROOT))
    from ofx import defaults
    pre = Path(CONFIG["release"])
    opts = dict(defaults.CONFIG["defaults"])
    synth, _ = defaults.synth_script(opts, xdc, pre / defaults.CONFIG["plugins"])
    fabric = "xc7a100t" if part_of(name).startswith(("xc7a75t", "xc7a100t")) else "xc7a50t"
    placer, _ = defaults.placer_args(opts)
    args = ["--chipdb", str(pre / "share/nextpnr/himbaechel/xilinx" / f"chipdb-{fabric}.bin"),
            "--db-root", str(pre / "share/nextpnr/external/prjxray-db")]
    if synth:
        args += ["--synth", synth]
    return args + [f"--nextpnr-arg={x}" for x in defaults.nextpnr_args(opts) + (placer or [])]


def open_one(name, period, seed, label, extra, dry):
    s = ddir(name) / "src"
    d = run_dir(name, period, seed, label)
    res_f = d / "result.json"
    if res_f.exists():
        return json.loads(res_f.read_text())
    say(dry, f"open {name} {period} ns seed {seed} [{label}] -> {d}")
    if dry:
        return None
    d.mkdir(parents=True, exist_ok=True)
    (d / "constraints.xdc").write_text(xdc_text(name, period))
    files = (s / "files.txt").read_text().split()
    top = (s / "top.txt").read_text().strip()
    if CONFIG["release"]:
        extra = release_args(name, d / "constraints.xdc") + extra
    cmd = [sys.executable, str(CONFIG["build_openxc7"]), str(s), "--top", top, "--xdc", str(d / "constraints.xdc"),
           "--part", part_of(name), "--seed", str(seed), "--freq", f"{1000.0 / period:.3f}", "--out", str(d / "impl"),
           "--nextpnr", str(CONFIG["npwait"]), "--nextpnr-arg=--timing-allow-fail", "--run", "--rtl"] + files + extra
    wl = d / "npwait.log"
    if wl.exists():
        wl.unlink()
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(CONFIG["nextpnr"]), OFX_MAX_NEXTPNR=CONFIG["max_nextpnr"],
               OFX_NPWAIT_LOG=str(wl))
    mem_wait()
    load0 = loadavg()
    t0 = time.time()
    r = subprocess.run(["/usr/bin/time", "-v"] + cmd, cwd=s, env=env, capture_output=True, text=True)
    wall = time.time() - t0
    load1 = loadavg()
    waited = sum(float(x) for x in re.findall(r"waited (\d+)", wl.read_text())) if wl.exists() else None
    (d / "build.log").write_text(r.stdout + r.stderr)
    impl = d / "impl"
    st = parse_stage_times(r.stdout)
    npl = (impl / "nextpnr.log").read_text(errors="replace") if (impl / "nextpnr.log").exists() else ""
    nm = nextpnr_metrics(npl)
    rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", r.stderr)
    cpu = time_v_cpu(r.stderr)
    res = {"design": name, "period": period, "seed": seed, "label": label, "ok": r.returncode == 0 and (impl / f"{top}.bit").exists(),
           "wall_s": wall, "stage_s": {"synth": st.get("yosys"), "place": (st["nextpnr"] - nm["route_s_log"]) if "nextpnr" in st else None,
                                       "route": nm["route_s_log"] if "nextpnr" in st else None,
                                       "bitstream": (st.get("fasm2frames") or 0) + (st.get("xc7frames2bit") or 0)},
           "peak_rss_gb": int(rss.group(1)) / 1048576 if rss else None, "fmax_nextpnr": nm["fmax_nextpnr"],
           "util_nextpnr": nm["util_nextpnr"], "extra": extra, "queue_wait_s": waited, "cpu_s": cpu,
           "loadavg": [load0, load1], "nextpnr_bin": str(CONFIG["nextpnr"]), "nproc": os.cpu_count()}
    if (impl / f"{top}.json").exists():
        res["cells"] = stat_cells(impl / f"{top}.json")
    if res["ok"]:
        res["place_metrics"] = open_place_metrics(impl / f"{top}_routed.json", part_of(name))
        pw = subprocess.run([sys.executable, str(ROOT / "bin" / "ofx"), "power", "--build", str(impl), "--json",
                             str(d / "power.json"), "--xdc", str(d / "constraints.xdc")], capture_output=True, text=True)
        if pw.returncode == 0 and (d / "power.json").exists():
            est = json.loads((d / "power.json").read_text())["estimate"]
            res["power_w"] = est.get("total") or est.get("total_w")
            res["power_detail"] = est
        else:
            res["power_w"] = None
            res["power_note"] = (pw.stderr or pw.stdout).strip().splitlines()[-1:] if (pw.stderr or pw.stdout) else []
    res_f.write_text(json.dumps(res, indent=1) + "\n")
    return res


def seeds_of(a):
    """Open-flow runs per design. nextpnr-xilinx's placer and router use criticality relative to the worst slack, so the
    target period does not change the result (aes at 6 ns and 11.08 ns: bit-identical FASM, 2026-11-08); a period sweep
    like Vivado's is therefore flat. The open flow gets the same number of runs as Vivado's sweep, as seeds."""
    if a.seeds:
        return a.seeds
    return [1] if a.quick or a.no_sweep else list(range(1, CONFIG["sweep_runs"] + 1))


def sweep_open(name, a, dry, label, extra):
    """Seed sweep at the design's start period; Fmax = best of the runs."""
    runs = []
    p = a.period or DESIGNS[name]["period"]
    for seed in seeds_of(a):
        r = open_one(name, p, seed, label, extra, dry)
        if r is None:
            continue
        runs.append(r)
        if not r["ok"]:
            break
    return runs


def loadavg():
    try:
        return float(Path("/proc/loadavg").read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def time_v_cpu(text):
    u = re.search(r"User time \(seconds\): ([\d.]+)", text)
    sy = re.search(r"System time \(seconds\): ([\d.]+)", text)
    return float(u.group(1)) + float(sy.group(1)) if u and sy else None


def open_runs(name, label, period=None):
    """result.json of the open runs at the start period (older runs at other periods are bit-identical duplicates)."""
    p0 = period or DESIGNS[name]["period"]
    out = []
    for f in sorted((ddir(name) / "open" / label).glob("*/result.json")):
        r = json.loads(f.read_text())
        if abs(r["period"] - p0) < 1e-6:
            r["dir"] = f.parent.name
            if r.get("cpu_s") is None and (f.parent / "build.log").exists():
                r["cpu_s"] = time_v_cpu((f.parent / "build.log").read_text(errors="replace"))
            out.append(r)
    return out


def cmd_open(names, a, dry):
    label = a.label
    extra = []
    for o in a.np_opt:
        extra += ["--opt", o]
    for o in a.np_arg:
        extra += [f"--nextpnr-arg={o}"]
    if a.synth:
        extra += ["--synth", a.synth]
    out = {}
    for name in names:
        runs = sweep_open(name, a, dry, label, extra)
        ok = [r for r in runs if r["ok"]]
        if not dry:
            best = max(ok, key=lambda r: r["fmax_nextpnr"] or 0) if ok else None
            print(f"{name}: {len(ok)}/{len(runs)} ok; best nextpnr Fmax "
                  f"{best['fmax_nextpnr'] if best else '-'} MHz at {best['period'] if best else '-'} ns")
            out[name] = runs
    return out



def winpath(p):
    s = str(p)
    m = re.match(r"/mnt/([a-z])/(.*)", s)
    return f"{m.group(1).upper()}:/{m.group(2)}" if m else s


def vivado_jobs(names, a):
    """jobs.txt lines: name mode period runs [placefile]; mode free = Vivado alone, placed = our placement."""
    lines = []
    for name in names:
        p = a.period or DESIGNS[name]["period"]
        nrun = 1 if a.quick or a.no_sweep else CONFIG["sweep_runs"]
        if "free" in a.modes:
            lines.append(f"{name} free {p:g} {nrun}")
        if "placed" in a.modes:
            for r in open_runs(name, a.label, a.period):
                if r["ok"] and r["fmax_nextpnr"] and r["seed"] in seeds_of(a):
                    lines.append(f"{name} placedx {round(1000.0 / r['fmax_nextpnr'], 2):g} 1 {a.label}_{r['dir']}")
    return lines


CARRY_SPLIT = re.compile(r"\$split\$muxcy\d+\$PACKED_CARRY4\$$")


def exact_export(name, rd, top, pd):
    """Exact import of an open run for Vivado (flow/xroute.py export, the method of flow/exact_src.py): the netlist
    is nextpnr's physical netlist (its feed-through LUT1s and split CARRY4s are cells), LUTRAM macros are placed sub-cell
    by sub-cell, LUT pins are locked as nextpnr used them. Vivado then only routes (and places what place_cell refuses,
    counted as missed). The older 'placed' mode (placement_rows) imposed only cells of the yosys netlist and let Vivado
    choose LUT pins and LUTRAM sites: 7-21 % optimistic on rv_soc against this import (packing agent, 2026-11-08)."""
    import device
    import xroute
    tmp = CONFIG["out"] / "exact" / pd.name
    (tmp / "run").mkdir(parents=True, exist_ok=True)
    (tmp / "run" / "status.json").write_text(json.dumps({"cmd": ["--json", str(rd / "impl" / f"{top}.json")]}))
    npr = tmp / "npr"
    npr.mkdir(exist_ok=True)
    if not (npr / "routed.json").exists():
        (npr / "routed.json").symlink_to(rd / "impl" / f"{top}_routed.json")
    r = device.resolve(part_of(name))
    xroute.CONFIG["tilegrid"] = Path(r["db_root"]) / r["family"] / r["fabric"] / "tilegrid.json"
    xroute.CONFIG["out"] = tmp / "x"
    xroute.name_of = lambda d, c="cal": pd.name
    xroute.src_run = lambda d: tmp / "run"
    xroute.dinfo = lambda d: {"top": top, "xdc": str(rd / "constraints.xdc")}
    d = xroute.export(name, npr, False, "cal")
    for f in ("netlist.edf", "place.txt", "macros.txt", "lockpins.txt", "export.json"):
        shutil.copy(d / f, pd / f)
    ex = json.loads((d / "export.json").read_text())
    return {k: ex[k] for k in ("stats", "place", "macros", "lockpins")}


def placement_rows(routed, netlist_cells):
    """nextpnr placement as (cell, BEL) rows for Vivado's place_cell, named as in the synthesized netlist. CARRY4s
    carry nextpnr's packing suffix ($split$muxcy<N>$PACKED_CARRY4$, any N). Cells absent from the synthesized netlist
    are nextpnr-only physical cells (carry DI route-through LUTs `$LUT$`, constant feeds `$feed$`, duplicates `_DUP`);
    they are not placed (Vivado makes its own) and counted in place_info.json."""
    j = json.loads(Path(routed).read_text())
    m = j["modules"][next(iter(j["modules"]))]
    rows, info, seen = [], collections.Counter(), {}
    for name, c in m["cells"].items():
        bel = c["attributes"].get("NEXTPNR_BEL")
        if not bel or c["type"] in {"PAD", "PSEUDO_GND", "PSEUDO_VCC", "BUFGCTRL", "ICAP_ICAP"} or c["type"].startswith("IOB33"):
            info["skipped_io_global"] += 1
            continue
        n = CARRY_SPLIT.sub("", name) if c["type"] == "CARRY4" else name
        if n not in netlist_cells:
            info["physical_only"] += 1
            continue
        if n in seen:
            info["carry_split"] += 1
            if "$muxcy0$" in name:
                rows[seen[n]] = (n, bel)
            continue
        seen[n] = len(rows)
        rows.append((n, bel))
    info["rows"] = len(rows)
    return rows, dict(info)


def stage_vivado(names, a, dry):
    """Copy sources and our placements to the Windows work tree; returns the job file path."""
    w = CONFIG["win_work"] / "designs" / CONFIG["vivado_tag"]
    jobs = vivado_jobs(names, a)
    for line in jobs:
        f = line.split()
        name, mode = f[0], f[1]
        dst = w / name
        say(dry, f"stage {name} {mode} -> {dst}")
        if dry:
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for x in (ddir(name) / "src").iterdir():
            if x.is_file():
                shutil.copy(x, dst / x.name)
        (dst / "constraints.xdc.tpl").write_text(re.sub(r"(create_clock[^\n]*-period\s+)[\d.]+", r"\1@PERIOD@",
                                                        xdc_text(name, 10.0)))
        if mode == "placedx":
            rd = ddir(name) / "open" / a.label / f[4][len(a.label) + 1:]
            top = (ddir(name) / "src" / "top.txt").read_text().strip()
            pd = w / f"{name}__placedx_{f[4]}"
            pd.mkdir(parents=True, exist_ok=True)
            info = exact_export(name, rd, top, pd)
            info.update(source=str(rd), nextpnr_bin=json.loads((rd / "result.json").read_text()).get("nextpnr_bin"))
            (pd / "place_info.json").write_text(json.dumps(info) + "\n")
            shutil.copy(dst / "constraints.xdc.tpl", pd / "constraints.xdc.tpl")
            (pd / "top.txt").write_text(top + "\n")
            (pd / "part.txt").write_text(part_of(name) + "\n")
    jf = CONFIG["win_work"] / "build" / CONFIG["vivado_tag"] / f"jobs_{a.label}_{os.getpid()}.txt"
    if not dry:
        jf.parent.mkdir(parents=True, exist_ok=True)
        jf.write_text("\n".join(jobs) + "\n")
        (CONFIG["win_work"] / "vivado").mkdir(parents=True, exist_ok=True)
        shutil.copy(CONFIG["tcl"], CONFIG["win_work"] / "vivado" / CONFIG["tcl"].name)
    for j in jobs:
        print("  job: " + j)
    return jf


def vivado_running():
    r = subprocess.run(["tasklist.exe"], capture_output=True, text=True)
    return "vivado.exe" in r.stdout.lower()


def others_waiting():
    for q in CONFIG["yield_queues"]:
        if q.exists() and q.read_text().strip():
            return f"queue {q}"
    r = subprocess.run(["pgrep", "-af", CONFIG["yield_procs"]], capture_output=True, text=True)
    lines = [l for l in r.stdout.splitlines() if "qor_suite" not in l]
    return f"process {lines[0][:80]}" if lines else None


def yield_to_others():
    t0, last = time.time(), None
    while True:
        w = others_waiting()
        if not w:
            if last:
                print(f"  yielded {time.time() - t0:.0f} s", flush=True)
            return
        if w != last:
            print(f"  yielding to {w}", flush=True)
            last = w
        time.sleep(CONFIG["yield_poll_s"])


def cmd_vivado(names, a, dry):
    """One Vivado invocation per job line (design), each under the machine-wide lock, released between batches.
    The whole sweep of a design runs in one invocation, however long it takes."""
    import signal
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    signal.signal(signal.SIGHUP, lambda *_: sys.exit(129))
    jf = stage_vivado(names, a, dry)
    out = CONFIG["win_work"] / "build" / CONFIG["vivado_tag"]
    jobs = [] if dry else [l for l in jf.read_text().splitlines() if l.strip()]
    for k, job in enumerate(jobs or ["(dry)"]):
        one = jf.with_name(f"{jf.stem}_{k}.txt")
        log = out / f"vivado_{a.label}_{job.split()[0]}_{time.strftime('%Y%m%d_%H%M%S')}.log"
        args = ["cmd.exe", "/c", CONFIG["vivado_bat"], "-mode", "batch", "-nojournal", "-log", winpath(log), "-source",
                winpath(CONFIG["win_work"] / "vivado" / CONFIG["tcl"].name), "-tclargs",
                winpath(CONFIG["win_work"] / "designs" / CONFIG["vivado_tag"]), winpath(out), winpath(one),
                str(CONFIG["vivado_budget_s"])]
        dl = os.environ.get("QOR_DEADLINE")
        if dl and not dry and time.strftime("%H%M") >= dl:
            print(f"  deadline {dl} reached: not starting {job}", flush=True)
            break
        say(dry, f"vivado batch {k}: {job}")
        if dry:
            print("  " + " ".join(args[2:]))
            continue
        one.write_text(job + chr(10))
        while True:
            yield_to_others()
            sh = (f"{'export VIV_SLOT1_ONLY=1; ' if CONFIG['slot1_only'] else ''}"
                  f"source {CONFIG['slot_helper']}; trap 'exit 143' TERM HUP INT; vivado_acquire; "
                  f"echo \"slot $VIV_HELD $(date '+%F %T')\"; t0=$(date +%s); " + " ".join(f"'{x}'" for x in args)
                  + "; rc=$?; echo \"vivado rc=$rc $(( $(date +%s) - t0 )) s\"; vivado_release; exit $rc")
            subprocess.run(["bash", "-c", sh], cwd="/mnt/c/Users/finnf")
            print(f"  {job.split()[0]}: log {log}", flush=True)
            if not (out / "budget_hit.txt").exists():
                break
            (out / "budget_hit.txt").unlink()



def vivado_results(name, mode="free"):
    """mode: free, or placed_<label> (Vivado timer on that label's placements)."""
    d = CONFIG["win_work"] / "build" / CONFIG["vivado_tag"]
    out = []
    pat = f"{name}__free/run*/result.txt" if mode == "free" else f"{name}__{mode}_*/run*/result.txt"
    for f in sorted(d.glob(pat)):
        r = {}
        for line in f.read_text().splitlines():
            k, _, v = line.partition(" ")
            r[k] = v.strip()
        r["dir"] = f.parent
        out.append(r)
    return out


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def viv_place_metrics(rdir, part):
    nf, pf = rdir / "nets_sites.txt", rdir / "pips_int.txt"
    if not nf.exists() or not pf.exists():
        return None
    nets = [l.split()[1:] for l in nf.read_text().splitlines() if l.strip()]
    g = grid(part)
    pips = collections.Counter()
    for l in pf.read_text().splitlines():
        t, n = l.split()
        if t in g["tile"]:
            pips[g["tile"][t]] += int(n)
    return place_metrics(nets, pips, part)


def gmean(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def placed_info(dirname):
    f = CONFIG["win_work"] / "designs" / CONFIG["vivado_tag"] / dirname / "place_info.json"
    return json.loads(f.read_text()) if f.exists() else {}


def summarize(name, label):
    runs = open_runs(name, label)
    ok = [r for r in runs if r["ok"]]
    s = {"design": name, "kind": DESIGNS[name]["kind"], "part": part_of(name), "open_runs": len(runs), "open_ok": len(ok),
         "open_seeds": sorted(r["seed"] for r in runs)}
    if ok:
        best = max(ok, key=lambda r: r["fmax_nextpnr"] or 0)
        first = min(ok, key=lambda r: r["seed"])
        known = [r for r in ok if r.get("queue_wait_s") is not None]
        tw = [r["wall_s"] - r["queue_wait_s"] for r in known] if known else [r["wall_s"] for r in ok]
        s["open"] = {"fmax_nextpnr": best["fmax_nextpnr"], "best_seed": best["seed"], "cells": first.get("cells"),
                     "stage_s": first["stage_s"], "wall_s": median(tw), "wall_raw_s": median([r["wall_s"] for r in ok]),
                     "queue_s": median([r.get("queue_wait_s") for r in known]) if known else None,
                     "queue_known": len(known), "cpu_s": median([r.get("cpu_s") for r in ok]),
                     "loadavg": median([x for r in known for x in (r.get("loadavg") or []) if x is not None]),
                     "power_w": first.get("power_w"), "place": first.get("place_metrics"), "period": first["period"],
                     "fmax_seeds": {r["seed"]: r["fmax_nextpnr"] for r in ok}}
    vr = vivado_results(name, "free")
    vok = [r for r in vr if r.get("rc") == "0"]
    p0 = DESIGNS[name]["period"]
    if vok:
        fm = [1000.0 / (num(r["period"]) - num(r["wns"])) for r in vok if num(r.get("wns")) is not None]
        v0 = next((r for r in vok if abs(num(r["period"]) - p0) < 1e-6), vok[0])
        s["vivado"] = {"fmax": max(fm) if fm else None, "util": {k: num(v0.get(k)) for k in ("LUT", "FF", "BRAM36", "DSP", "LUTRAM")},
                       "stage_s": {k: num(v0.get(f"t_{k}")) for k in ("synth", "place", "route", "bitstream")},
                       "wall_s": num(v0.get("t_total")), "cpu_s": num(v0.get("cpu_total")),
                       "cpu_s_runs": [num(r.get("cpu_total")) for r in vok if r.get("cpu_total")],
                       "wall_s_runs": [num(r.get("t_total")) for r in vok],
                       "power_w": num(v0.get("power_total")),
                       "power_dynamic_w": num(v0.get("power_dynamic")), "threads": v0.get("threads"),
                       "place": viv_place_metrics(v0["dir"], part_of(name)), "period": num(v0["period"]), "runs": len(vok)}
    s["vivado_runs"], s["vivado_ok"] = len(vr), len(vok)
    xr = [r for r in vivado_results(name, f"placedx_{label}") if r.get("rc") == "0" and num(r.get("wns")) is not None]
    if xr:
        fx = {r["dir"].parent.name: 1000.0 / (num(r["period"]) - num(r["wns"])) for r in xr}
        bt = max(fx, key=fx.get)
        rb = next(r for r in xr if r["dir"].parent.name == bt)
        pi = placed_info(bt)
        s["open_vivado_timer_fmax"] = fx[bt]
        s["placed"] = {"runs": len(xr), "fmax_runs": sorted(round(v, 1) for v in fx.values()),
                       "placed": num(rb.get("placed")), "missed": num(rb.get("missed")), "rows": pi.get("rows"),
                       "lutram_macros": pi.get("macros"), "lockpins": num(rb.get("lockpins"))}
    return s


def goodness(s):
    o, v = s.get("open"), s.get("vivado")
    g = {}
    if not o or not v:
        return g
    fo = s.get("open_vivado_timer_fmax") or o["fmax_nextpnr"]
    s["fmax_timer"] = "Vivado" if s.get("open_vivado_timer_fmax") else "nextpnr"
    g["fmax"] = fo / v["fmax"] if fo and v["fmax"] else None
    ar = []
    c = o.get("cells") or {}
    for k in ("LUT", "FF", "BRAM36", "DSP"):
        a, b = c.get(k), v["util"].get(k)
        if a and b:
            ar.append(b / a)
        elif (a or 0) == 0 and (b or 0) == 0:
            continue
        elif not a and b:
            ar.append(1.25)
        elif a and not b:
            ar.append(0.8)
    g["area"] = gmean(ar)
    g["power"] = (v["power_w"] / o["power_w"]) if o.get("power_w") and v.get("power_w") else None
    g["build_time"] = (v["wall_s"] / o["wall_s"]) if o.get("wall_s") and v.get("wall_s") else None
    po, pv = o.get("place") or {}, v.get("place") or {}
    g["routability"] = (pv["routed_int_pips"] / po["routed_int_pips"]) if po.get("routed_int_pips") and pv.get("routed_int_pips") else None
    return g


def score(g):
    w = {k: CONFIG["weights"][k] for k in CONFIG["weights"] if g.get(k)}
    if not w:
        return None
    return math.exp(sum(w[k] * math.log(g[k]) for k in w) / sum(w.values()))


def verdict(sc):
    if sc is None:
        return "incomplete"
    if sc >= CONFIG["verdict"]["better"]:
        return "better"
    if sc >= CONFIG["verdict"]["par"]:
        return "on par"
    return "worse"


def fmt(x, nd=2):
    return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def machine():
    cpu = re.search(r"model name\s*:\s*(.*)", Path("/proc/cpuinfo").read_text())
    return {"cpu": cpu.group(1) if cpu else "?", "threads_wsl": os.cpu_count(),
            "mem_gb_wsl": round(int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1)) / 1048576, 1)}


def open_failure(name, label):
    for f in sorted((ddir(name) / "open" / label).glob("*/build.log")):
        t = f.read_text(errors="replace")
        for log in ("yosys", "nextpnr", "fasm2frames", "xc7frames2bit"):
            if f"{log} failed" in t:
                lf = f.parent / "impl" / f"{log}.log"
                err = [l for l in lf.read_text(errors="replace").splitlines() if "ERROR" in l] if lf.exists() else []
                return f"{log}: {err[0].strip()[:140]}" if err else log
    return "?"


def cmd_report(names, a, dry):
    rows = [summarize(n, a.label) for n in names]
    for r in rows:
        r["g"] = goodness(r)
        r["score"] = score(r["g"])
        r["verdict"] = verdict(r["score"])
        why = DESIGNS[r["design"]].get("exclude_reason")
        if why:
            r["g"], r["score"], r["verdict"] = {}, None, f"excluded ({why})"
            continue
        if r["open_runs"] and not r["open_ok"]:
            r["g"]["routability"], r["score"] = 0.0, 0.0
            r["verdict"] = "worse (open build failed: " + open_failure(r["design"], a.label) + ")"
    rows.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    (CONFIG["out"] / f"scoreboard_{a.label}.json").write_text(json.dumps(rows, indent=1, default=str) + "\n")
    mc = machine()
    threads = sorted({r["vivado"]["threads"] for r in rows if r.get("vivado") and r["vivado"].get("threads")})
    L = []
    L.append("# Artix-7 QoR scoreboard: open flow vs Vivado 2025.2\n")
    L.append(f"Generated by `python3 flow/qor_suite.py report{' --label ' + a.label if a.label != 'base' else ''}` "
             f"({time.strftime('%Y-%m-%d %H:%M')}). Raw data: `build/qor_suite/scoreboard_{a.label}.json`.\n")
    L.append("## Method\n")
    L.append(f"- Machine: {mc['cpu']}, {mc['threads_wsl']} hardware threads; the open flow runs in WSL2 with "
             f"{mc['mem_gb_wsl']} GB, Vivado 2025.2 on Windows on the same CPU. Vivado runs with its default thread count "
             f"(`general.maxThreads` = {', '.join(threads) or '?'}, confirmed per run in result.txt and by place_design's "
             "\"maximum of 2 CPUs\"); yosys and nextpnr run single-threaded. Other agents' jobs shared the machine. Build "
             "time is therefore given three ways: wall clock (Vivado: the start-period run; open flow: median over the seeds "
             "of wall clock minus the time queued for a nextpnr slot in ofx/npwait.sh, which is not tool time), CPU seconds "
             "(Vivado: the process's TotalProcessorTime from Windows; open flow: user + system of the whole build from "
             "`/usr/bin/time`), and the WSL 1-minute load average during the open runs. CPU seconds are not inflated by "
             "waiting for a core, so they are the load-robust check; g build time uses the wall clock.")
    L.append("- Every design builds from the same RTL in both tools. A wrapped design is the upstream core inside `suite_top`: "
             "its inputs come from a 32-bit LFSR shift chain, its outputs are registered and XOR-reduced to one pin, so nothing "
             "is optimised away and the I/O count fits any package. Native designs (fir, bram, rv_big) use their own top.")
    L.append("- Vivado alone: `synth_design`, `opt_design`, `place_design`, `route_design`, `write_bitstream`, default "
             "strategies. Fmax sweep: run at the design's start period, then at the achieved period (period - WNS), up to "
             f"{CONFIG['sweep_runs']} runs; Fmax = max over runs of 1000 / (period - WNS), Vivado's timer.")
    L.append(f"- Open flow runs: {CONFIG['sweep_runs']} seeds at the design's start period (the same number of runs as "
             "Vivado's sweep). A period sweep does not work for nextpnr-xilinx: its placer and router weight paths by "
             "criticality relative to the worst slack, so the target period does not change the result (aes at 6 ns and "
             "at 11.08 ns gave bit-identical FASM, 2026-11-08); seeds are the only knob that changes the result.")
    L.append("- Open flow: `flow/build_openxc7.py` (the plain `ofx build` flow: yosys `synth_xilinx -flatten -abc9`, "
             "nextpnr-xilinx, fasm2frames, xc7frames2bit). "
             "\"ours, Vivado timer\" (placed mode, exact import) is Vivado's timer on the open flow's implementation: "
             "nextpnr's physical netlist (its feed-through LUT1s and split CARRY4s included) exported by flow/xroute.py, "
             "every cell fixed at nextpnr's BEL, LUTRAM macros placed sub-cell by sub-cell, LUT pins locked as nextpnr "
             "used them; Vivado then only routes (`route_design`) and times. One Vivado run per seed at the period "
             "nextpnr reported for that seed, best over the seeds. Cells place_cell refuses are left to Vivado and "
             "counted. This is the like-for-like Fmax; where it is missing g Fmax falls back to the nextpnr timer and the "
             "table says so. An earlier import (yosys-netlist cells only, Vivado's LUT pins and LUTRAM sites) read 7-21 % "
             "optimistic on rv_soc and is not used.")
    L.append("- Area: LUT (logic LUTs), FF, BRAM (36 Kb equivalents), DSP after implementation (Vivado: report_utilization; "
             "open: cell counts of the yosys netlist). Power: Vivado `report_power` (vectorless defaults) and `ofx power` "
             "(the open estimate); `-` where the open power model is not installed.")
    L.append("- Placement quality, computed the same way for both tools' implementations at the start period: HPWL = sum "
             "over signal nets (no global clocks, no constants) of the half-perimeter of the nets' sites in prjxray tile-grid "
             "units; routed wirelength = used pips in INT tiles; congestion = peak and 99th-percentile used pips per INT tile.")
    W = CONFIG["weights"]
    L.append(f"- Score: per metric a goodness g (> 1 = open flow better): Fmax ours/Vivado; area = geometric mean of "
             f"Vivado/ours over LUT, FF, BRAM, DSP; power Vivado/ours; build time Vivado/ours (total wall clock); "
             f"routability Vivado/ours routed INT pips (0 if the open build failed). Weights: "
             + ", ".join(f"{k} {v}" for k, v in W.items())
             + f" (equal, user 2026-11-06). Overall = weighted geometric mean over the metrics present; verdict better if "
             f">= {CONFIG['verdict']['better']}, on par if >= {CONFIG['verdict']['par']}, else worse.\n")
    L.append("## Verdicts\n")
    L.append("| design | kind | part | verdict | score | g Fmax | g area | g power | g build time | g routability |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        g = r["g"]
        L.append(f"| {r['design']} | {r['kind']} | {r['part']} | {r['verdict']} | {fmt(r['score'])} | {fmt(g.get('fmax'))} | "
                 f"{fmt(g.get('area'))} | {fmt(g.get('power'))} | {fmt(g.get('build_time'))} | {fmt(g.get('routability'))} |")
    gm = {k: gmean([r["g"].get(k) for r in rows if r["open_ok"]]) for k in W}
    nfail = sum(1 for r in rows if r["open_runs"] and not r["open_ok"])
    L.append(f"| **geometric mean** (designs the open flow built) | | | {verdict(score(gm))} | {fmt(score(gm))} | "
             + " | ".join(fmt(gm[k]) for k in W) + " |\n")
    L.append(f"Open-flow build failures: {nfail} of {len(rows)} designs (scored 0, not in the geometric mean).\n")
    L.append("## Fmax and area\n")
    L.append("| design | Vivado Fmax | ours, Vivado timer | ours, nextpnr timer | g Fmax timer | our cells at nextpnr BEL | LUT V / ours | FF V / ours | BRAM V / ours | DSP V / ours | power V / ours (W) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        o, v = r.get("open") or {}, r.get("vivado") or {}
        c, u = o.get("cells") or {}, v.get("util") or {}
        pl = r.get("placed") or {}
        cov = (f"{int(pl['placed'])} / {int(pl['placed'] + pl['missed'])}"
               if pl.get("placed") is not None and pl.get("missed") is not None else "-")
        L.append(f"| {r['design']} | {fmt(v.get('fmax'), 1)} | {fmt(r.get('open_vivado_timer_fmax'), 1)} | {fmt(o.get('fmax_nextpnr'), 1)} | "
                 f"{r.get('fmax_timer', '-') if r['g'].get('fmax') else '-'} | {cov} | "
                 + " | ".join(f"{fmt(u.get(k), 0) if u.get(k) is not None else '-'} / {c.get(k, '-')}" for k in ("LUT", "FF", "BRAM36", "DSP"))
                 + f" | {fmt(v.get('power_w'), 3)} / {fmt(o.get('power_w'), 3)} |")
    L.append("\n## Build time by stage (seconds, start period)\n")
    L.append("| design | Vivado synth | place | route | bitstream | total | ours synth | place | route | bitstream | total (queue removed) | ours queued | CPU s V / ours | load avg (open runs) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        o, v = r.get("open") or {}, r.get("vivado") or {}
        vs, os_ = v.get("stage_s") or {}, o.get("stage_s") or {}
        L.append(f"| {r['design']} | " + " | ".join(fmt(vs.get(k), 1) for k in ("synth", "place", "route", "bitstream"))
                 + f" | {fmt(v.get('wall_s'), 1)} | " + " | ".join(fmt(os_.get(k), 1) for k in ("synth", "place", "route", "bitstream"))
                 + f" | {fmt(o.get('wall_s'), 1)} | {fmt(o.get('queue_s'), 0) if o.get('queue_known') else 'not logged'} | "
                 f"{fmt(v.get('cpu_s'), 0)} / {fmt(o.get('cpu_s'), 0)} | {fmt(o.get('loadavg'), 1)} |")
    L.append("\n## Placement quality (start period)\n")
    L.append("| design | HPWL V / ours | routed INT pips V / ours | peak pips per INT tile V / ours | p99 V / ours | place time V / ours (s) | builds ok V / ours |")
    L.append("|---|---|---|---|---|---|---|")
    for r in rows:
        o, v = r.get("open") or {}, r.get("vivado") or {}
        po, pv = o.get("place") or {}, v.get("place") or {}
        L.append(f"| {r['design']} | {pv.get('hpwl', '-')} / {po.get('hpwl', '-')} | {pv.get('routed_int_pips', '-')} / {po.get('routed_int_pips', '-')} | "
                 f"{pv.get('int_pips_peak', '-')} / {po.get('int_pips_peak', '-')} | {pv.get('int_pips_p99', '-')} / {po.get('int_pips_p99', '-')} | "
                 f"{fmt((v.get('stage_s') or {}).get('place'), 1)} / {fmt((o.get('stage_s') or {}).get('place'), 1)} | "
                 f"{r['vivado_ok']}/{r['vivado_runs']} / {r['open_ok']}/{r['open_runs']} |")
    L.append("\n## Running it, and quick runs of a variant\n")
    L.append("- Full scoreboard: `python3 flow/qor_suite.py open --run` (3 seeds per design), `vivado --modes free --run` "
             "(Vivado alone), `vivado --modes placed --run` (Vivado timer on every open run), `report --run`. Finished runs "
             "are cached and skipped. nextpnr runs only through ofx/npwait.sh with OFX_MAX_NEXTPNR=2; every Vivado "
             "invocation (one per design) takes a slot with vivado/vivado_slot.sh `vivado_acquire` and releases it after.")
    L.append(f"- Quick mode (`--quick`): designs {', '.join(CONFIG['quick'])}, seed 1, start period, one Vivado run. "
             "Variant runs keep their results apart from base under a name (`--variant NAME`, same as `--label`):")
    L.append("")
    L.append("```")
    L.append("python3 flow/qor_suite.py open   --quick --variant NAME [--nextpnr /path/to/nextpnr-xilinx] \\")
    L.append("        [--np-arg=--placer-static-anchor-init --np-arg=20] [--np-opt key=value] [--synth 'yosys cmds'] --run")
    L.append("python3 flow/qor_suite.py vivado --quick --variant NAME --modes placed --run   # Vivado timer on NAME's placements")
    L.append("python3 flow/qor_suite.py report --quick --variant NAME --run                 # build/qor_suite/scoreboard_NAME.md")
    L.append("```")
    L.append("")
    L.append("- The variant report has the same tables plus \"Variant NAME against base\" (Fmax by both timers for the "
             "same seeds). The Vivado-alone reference (`--modes free`) does not depend on the variant and is shared; run it "
             "once for designs that lack it. `--nextpnr` needs `--variant` (base is the reference flow). Add `--seeds 1 2 3` "
             "for a seed sweep instead of seed 1. Without `--run` every step is a dry run that prints what it would do.")
    if a.label != "base":
        L.append(f"\n## Variant `{a.label}` against base\n")
        L.append("Best over the variant's seeds, base restricted to the same seeds. Vivado Fmax is the Vivado-alone reference.\n")
        L.append("| design | Vivado Fmax | ours, Vivado timer: base / variant | ours, nextpnr timer: base / variant | seeds |")
        L.append("|---|---|---|---|---|")
        for r in rows:
            seeds = sorted(set(r["open_seeds"]))
            ob = {x["seed"]: x["fmax_nextpnr"] for x in open_runs(r["design"], "base") if x["ok"] and x["seed"] in seeds}
            xb = [1000.0 / (num(x["period"]) - num(x["wns"])) for x in vivado_results(r["design"], "placedx_base")
                  if x.get("rc") == "0" and num(x.get("wns")) is not None
                  and any(x["dir"].parent.name.endswith(f"_s{sd}") for sd in seeds)]
            L.append(f"| {r['design']} | {fmt((r.get('vivado') or {}).get('fmax'), 1)} | {fmt(max(xb) if xb else None, 1)} / "
                     f"{fmt(r.get('open_vivado_timer_fmax'), 1)} | {fmt(max(ob.values()) if ob else None, 1)} / "
                     f"{fmt((r.get('open') or {}).get('fmax_nextpnr'), 1)} | {','.join(map(str, seeds)) or '-'} |")
    text = "\n".join(L) + "\n"
    if dry:
        print(text)
        return
    if a.label == "base" and not a.quick and not a.designs:
        CONFIG["doc"].write_text(text)
        print(f"wrote {CONFIG['doc']}")
    else:
        p = CONFIG["out"] / f"scoreboard_{a.label}{'_quick' if a.quick else ''}.md"
        p.write_text(text)
        print(f"wrote {p}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", choices=["fetch", "wrap", "probe", "open", "vivado", "report", "all"])
    ap.add_argument("designs", nargs="*")
    ap.add_argument("--quick", action="store_true", help="QUICK subset, one seed, fixed period, no sweep, no xtime")
    ap.add_argument("--no-sweep", action="store_true")
    ap.add_argument("--period", type=float, help="fixed period in ns for every design (default: per design)")
    ap.add_argument("--seeds", type=int, nargs="+", help="open-flow seeds (default 1..3, quick: 1)")
    ap.add_argument("--label", default="base", help="result label for a variant of the open flow (default base)")
    ap.add_argument("--variant", help="same as --label: name of a variant of the open flow")
    ap.add_argument("--nextpnr", help="nextpnr-xilinx binary for the open runs (default toolchain/openxc7/bin)")
    ap.add_argument("--np-opt", action="append", default=[], help="extra nextpnr -o option (variant runs)")
    ap.add_argument("--np-arg", action="append", default=[], help="extra nextpnr argument (variant runs)")
    ap.add_argument("--synth", help="yosys synthesis commands instead of the default ({top} is replaced)")
    ap.add_argument("--release", help="install prefix: open runs with its nextpnr, chipdb, plugins and the ofx build "
                                      "defaults (needs --variant)")
    ap.add_argument("--modes", nargs="+", default=["free", "placed"], help="vivado step: free and/or placed")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    if a.variant:
        a.label = a.variant
    if a.release:
        if a.label == "base":
            sys.exit("--release needs --variant NAME (base results are the reference flow)")
        CONFIG["release"] = Path(a.release).expanduser().resolve()
        CONFIG["nextpnr"] = CONFIG["release"] / "bin" / "nextpnr-himbaechel"
    if a.nextpnr:
        if a.label == "base":
            sys.exit("--nextpnr needs --variant NAME (base results are the reference flow)")
        CONFIG["nextpnr"] = Path(a.nextpnr).resolve()
    names = a.designs or (CONFIG["quick"] if a.quick else list(DESIGNS))
    unknown = [n for n in names if n not in DESIGNS]
    if unknown:
        sys.exit(f"unknown designs {unknown}; known: {list(DESIGNS)}")
    steps = ["wrap", "open", "vivado", "report"] if a.step == "all" else [a.step]
    for st in steps:
        if st == "fetch":
            cmd_fetch(a, dry)
        elif st == "wrap":
            cmd_wrap(names, dry)
        elif st == "probe":
            cmd_probe(names, dry)
        elif st == "open":
            cmd_open(names, a, dry)
        elif st == "vivado":
            cmd_vivado(names, a, dry)
        elif st == "report":
            cmd_report(names, a, dry)


if __name__ == "__main__":
    main()
