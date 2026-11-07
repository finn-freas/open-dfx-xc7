"""ofx debug: ILA / MARK_DEBUG equivalent.

insert   Synthesize the user design with yosys (synth_xilinx -flatten, no I/O or clock buffers), keeping the
         nets marked for debug (RTL `(* mark_debug = "true" *)`, XDC `set_property MARK_DEBUG true [get_nets ..]`,
         Vivado `connect_debug_port .../probeN`, or `[debug] probes`), expose those nets as ports of the
         synthesized netlist, and wrap it with a LiteScope analyzer core whose host bridge is JTAGBone on a
         BSCANE2 (USER1 by default; no UART pins) or UARTBone. `ofx build` then builds the wrapper.
capture  Host side: arm a trigger, wait, upload the samples and write a VCD. Transports:
           sim   the full design (synthesized netlist + core + BSCANE2) in iverilog with Vivado's JTAG_SIME2
                 TAP model; this tool drives TCK/TMS/TDI through the TAP exactly as a cable would
           jtag  a running `litex_server --jtag` (openocd jtagstream) on the board (not tested on hardware)
           uart  UARTBone on a serial port (not tested on hardware)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import FLOW, ROOT

sys.path.insert(0, str(FLOW))

LX = ROOT / "toolchain" / "litex"
VIV = Path("/mnt/c/AMDDesignTools/2025.2/Vivado/data/verilog/src")
CONFIG = {
    "yosys": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "yosys",
    "iverilog": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "iverilog",
    "vvp": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "vvp",
    "litex_python": LX / "venv" / "bin" / "python3",
    "litex_src": [],
    "core_gen": FLOW / "scope_core_gen.py",
    "unisims": VIV / "unisims",
    "glbl": VIV / "glbl.v",
    "out": "debug",
    "depth": 1024,
    "bridge": "jtag",
    "jtag_chain": 1,
    "user_ir": {1: 0x02, 2: 0x03, 3: 0x22, 4: 0x23},
    "ir_len": 6,
    "jtag_part": {"xc7a35t": "7A35T", "xc7a50t": "7A50T", "xc7a100t": "7A100T", "xc7a200t": "7A200T",
                  "xc7s50": "XC7S50", "xc7z020": "7Z020"},
    "tck_ns": 20,
    "stream_word_bits": 11,
    "poll_words": 16,
    "trigger_latency": 2,
    "vivado_suffix": re.compile(r"(_IBUF_BUFG|_IBUF|_BUFG|_OBUF|_reg)$"),
}


class DebugError(Exception):
    pass


def vivado_to_rtl(net):
    base = re.sub(r"\[[^\]]*\]$", "", net.strip("{}"))
    return CONFIG["vivado_suffix"].sub("", base).replace("/", ".")


def nets_in(text):
    m = re.search(r"get_nets\s+(?:\[list\s+)?(.*?)\]+\s*$", text)
    if not m:
        return []
    return [t.strip("{}") for t in re.findall(r"\{[^}]*\}|\S+", m[1]) if t.strip("{}")]


def xdc_marks(files):
    marked, clk, depth = [], None, None
    for f in files:
        for ln in Path(f).read_text().splitlines():
            s = ln.split("#")[0].strip()
            if re.match(r"set_property\s+MARK_DEBUG\s+(true|1)\b", s, re.I):
                marked += nets_in(s)
            elif re.match(r"connect_debug_port\s+\S+/clk\b", s):
                clk = (nets_in(s) or [None])[0]
            elif re.match(r"connect_debug_port\s+\S+/probe\d+\b", s):
                marked += nets_in(s)
            elif m := re.match(r"set_property\s+C_DATA_DEPTH\s+(\d+)", s):
                depth = int(m[1])
    return [vivado_to_rtl(n) for n in marked], (vivado_to_rtl(clk) if clk else None), depth


def clock_ports(files):
    out = []
    for f in files:
        for m in re.finditer(r"create_clock\b[^\n]*-period\s+([\d.]+)[^\n]*get_ports\s+\{?(\w+)", Path(f).read_text()):
            out.append((m[2], float(m[1])))
    return out


def spec(proj, sources, xdc_files):
    d = proj.raw.get("debug", {})
    marks, xclk, xdepth = xdc_marks(xdc_files)
    probes = list(dict.fromkeys(list(d.get("probes", [])) + marks))
    clocks = clock_ports(xdc_files) + [(k, v) for k, v in proj.clocks.items()]
    clk = d.get("clock") or xclk or (clocks[0][0] if clocks else None)
    if not clk:
        raise DebugError("[debug] needs clock (no create_clock / [clocks] found)")
    period = dict(clocks).get(clk, d.get("period_ns", 10.0))
    bridge = d.get("bridge", CONFIG["bridge"])
    if bridge not in ("jtag", "uart"):
        raise DebugError(f"[debug] bridge must be jtag or uart, not {bridge!r}")
    return {"probes": probes, "rtl_marks": bool(d.get("rtl_marks", True)), "clk": clk, "period_ns": period,
            "depth": int(d.get("depth", xdepth or CONFIG["depth"])), "bridge": bridge,
            "jtag_chain": int(d.get("jtag_chain", CONFIG["jtag_chain"])), "uart_pins": d.get("uart_pins", {})}


def run(cmd, log, env=None, cwd=None):
    with open(log, "w") as f:
        r = subprocess.run([str(c) for c in cmd], stdout=f, stderr=subprocess.STDOUT, env=env, cwd=cwd)
    if r.returncode:
        raise DebugError(f"failed, see {log}: {' '.join(map(str, cmd))}")


def synth_inner(sources, top, sp, out):
    """yosys: synthesize, keep + expose the debug nets. Returns ({port: (dir, width)}, [(probe, width)])."""
    rd = " ".join(str(s) for s in sources)
    keep = " ".join(f"w:{n}" for n in sp["probes"])
    script = [f"read_verilog -sv {rd}", f"hierarchy -top {top}", "proc"]
    if sp["rtl_marks"]:
        script.append("setattr -set keep 1 a:mark_debug=true a:mark_debug=TRUE a:MARK_DEBUG=true a:MARK_DEBUG=TRUE")
    script += ["flatten"]
    if keep:
        script.append(f"setattr -set keep 1 {keep}")
    script += [f"synth_xilinx -flatten -abc9 -arch xc7 -noiopad -noclkbuf -top {top}",
               f"tee -o {out / 'inner_marked.txt'} select -list a:keep w:* %i",
               f"write_json {out / 'inner_pre.json'}"]
    (out / "inner_pre.ys").write_text("\n".join(script) + "\n")
    run([CONFIG["yosys"], "-q", "-s", out / "inner_pre.ys"], out / "inner_pre.log")
    mod = json.loads((out / "inner_pre.json").read_text())["modules"][top]
    names = mod["netnames"]
    want = list(sp["probes"])
    if sp["rtl_marks"]:
        for n, v in names.items():
            a = {k.lower(): str(x).lower() for k, x in v.get("attributes", {}).items()}
            if a.get("mark_debug") in ("true", "1", "00000000000000000000000000000001") and n not in want:
                want.append(n)
    missing = [n for n in want if n not in names]
    if missing:
        raise DebugError(f"debug nets not in the synthesized netlist: {missing} (known: {sorted(names)[:20]} ...)")
    if not want:
        raise DebugError("no debug nets: mark nets MARK_DEBUG (XDC or RTL) or list [debug] probes")
    ports = {n: (p["direction"], len(p["bits"])) for n, p in mod["ports"].items()}
    clk = sp["clk"]
    sel = " ".join(f"w:{_esc(n)}" for n in want + ([clk] if clk not in ports else []))
    s2 = [f"read_json {out / 'inner_pre.json'}", f"select -assert-min 1 {sel}", f"expose {sel}",
          f"rename {top} {top}_dbg_inner", f"write_verilog -noattr {out / 'inner.v'}", f"write_json {out / 'inner.json'}"]
    (out / "inner_expose.ys").write_text("\n".join(s2) + "\n")
    run([CONFIG["yosys"], "-q", "-s", out / "inner_expose.ys"], out / "inner_expose.log")
    m2 = json.loads((out / "inner.json").read_text())["modules"][f"{top}_dbg_inner"]["ports"]
    probes = [(n, len(m2[n]["bits"])) for n in want]
    return ports, probes


def _esc(n):
    return n.replace("[", "\\[").replace("]", "\\]")


def vid(n):
    return n if re.fullmatch(r"[A-Za-z_]\w*", n) else f"\\{n} "


def flat(n):
    return "dbg_" + re.sub(r"\W", "_", n)


def wrapper(top, ports, probes, clk, bridge):
    io = [f"    {d} wire{f' [{w - 1}:0]' if w > 1 else ''} {vid(n)}" for n, (d, w) in ports.items()]
    if bridge == "uart":
        io += ["    input wire dbg_uart_rx", "    output wire dbg_uart_tx"]
    taps = probes + ([(clk, 1)] if clk not in ports and clk not in dict(probes) else [])
    sig = lambda n: vid(n) if n in ports else flat(n)
    wires = [f"    wire{f' [{w - 1}:0]' if w > 1 else ''} {flat(n)};" for n, w in taps if n not in ports]
    conn = [f".{vid(n)}({vid(n)})" for n in ports] + [f".{vid(n)}({flat(n)})" for n, _ in taps if n not in ports]
    cat = ", ".join(sig(n) for n, _ in reversed(probes))
    br = ", .dbg_serial_rx(dbg_uart_rx), .dbg_serial_tx(dbg_uart_tx)" if bridge == "uart" else ""
    return "\n".join([f"// generated by ofx debug insert", f"module {top} (", ",\n".join(io), ");"] + wires + [
        f"    {top}_dbg_inner u_dut ({', '.join(conn)});",
        f"    scope_core u_dbg (.dbg_clk({sig(clk)}), .dbg_probe({{{cat}}}){br});", "endmodule", ""])


def litex_env():
    e = dict(os.environ)
    e["PYTHONPATH"] = ":".join(str(p) for p in CONFIG["litex_src"] if p.exists()) + ":" + e.get("PYTHONPATH", "")
    return e


def core(probes, sp, out):
    cd = out / "core"
    cd.mkdir(parents=True, exist_ok=True)
    js = {"probes": [[re.sub(r"\W", "_", n), w] for n, w in probes], "depth": sp["depth"],
          "clk_freq": 1e9 / sp["period_ns"], "bridge": sp["bridge"], "jtag_chain": sp["jtag_chain"], "out_dir": str(cd)}
    (out / "core_spec.json").write_text(json.dumps(js, indent=1) + "\n")
    run([CONFIG["litex_python"], CONFIG["core_gen"], out / "core_spec.json"], out / "core_gen.log", env=litex_env(),
        cwd=out)
    v = (cd / "scope_core.v").read_text()
    v = v.replace('$readmemh("scope_core_mem.init"', f'$readmemh("{cd / "scope_core_mem.init"}"')
    (out / "scope_core.v").write_text(v)


def xdc_strip(files, sp):
    keep = []
    for f in files:
        for ln in Path(f).read_text().splitlines():
            if re.match(r"^\s*(create_debug_core|connect_debug_port|create_debug_port|set_property\s+.*get_debug_|"
                        r"set_property\s+MARK_DEBUG\b)", ln):
                continue
            keep.append(ln)
    if sp["bridge"] == "uart":
        for port, pin in sp["uart_pins"].items():
            keep.append(f"set_property -dict {{ PACKAGE_PIN {pin} IOSTANDARD LVCMOS33 }} [get_ports {port}]")
    return "\n".join(keep) + "\n"


def insert(proj, sources, xdc_files, out, dry):
    sp = spec(proj, sources, xdc_files)
    print(f"[{'dry' if dry else 'run'}] ofx debug insert: probes {sp['probes'] or '(MARK_DEBUG in RTL)'}, clock "
          f"{sp['clk']} ({sp['period_ns']} ns), depth {sp['depth']}, bridge {sp['bridge']}"
          + (f" (BSCANE2 USER{sp['jtag_chain']})" if sp["bridge"] == "jtag" else "") + f" -> {out}")
    files = [out / "wrapper.v", out / "inner.v", out / "scope_core.v"]
    if dry:
        return files, out / "debug.xdc"
    out.mkdir(parents=True, exist_ok=True)
    key = json.dumps({"sp": sp, "src": [Path(s).read_text() for s in sources],
                      "xdc": [Path(x).read_text() for x in xdc_files], "top": proj.top})
    stamp = out / "inputs.json"
    if stamp.exists() and stamp.read_text() == key and all(f.exists() for f in files):
        print(f"ofx debug: {out} is up to date")
        return files, out / "debug.xdc"
    ports, probes = synth_inner(sources, proj.top, sp, out)
    core(probes, sp, out)
    (out / "wrapper.v").write_text(wrapper(proj.top, ports, probes, sp["clk"], sp["bridge"]))
    (out / "debug.xdc").write_text(xdc_strip(xdc_files, sp))
    meta = {"top": proj.top, "part": proj.part, "probes": probes, "clk": sp["clk"], "period_ns": sp["period_ns"],
            "depth": sp["depth"], "bridge": sp["bridge"], "jtag_chain": sp["jtag_chain"], "ports": ports,
            "csr_csv": str(out / "core" / "csr.csv"), "analyzer_csv": str(out / "core" / "analyzer.csv"),
            "sources": [str(f) for f in files]}
    (out / "debug.json").write_text(json.dumps(meta, indent=1) + "\n")
    stamp.write_text(key)
    print(f"ofx debug: {len(probes)} probes, {sum(w for _, w in probes)} bits: "
          + ", ".join(f"{n}[{w}]" for n, w in probes))
    return files, out / "debug.xdc"


def sim_tb(meta, stim):
    ports = meta["ports"]
    clk = meta["clk"]
    part = CONFIG["jtag_part"].get(re.match(r"(xc7[a-z]\d+t?)", meta["part"])[1], "7A35T")
    half_ps = int(meta["period_ns"] * 500)
    tck_half = CONFIG["tck_ns"] // 2
    L = ["`timescale 1ns/1ps", "module tb_dbg;"]
    for n, (d, w) in ports.items():
        rng = f" [{w - 1}:0]" if w > 1 else ""
        if d == "input":
            L.append(f"    reg{rng} {vid(n)} = {stim.get(n, 0)};")
        else:
            L.append(f"    wire{rng} {vid(n)};")
    L += [f"    always #({half_ps / 1000:.3f}) {vid(clk)} = ~{vid(clk)};",
          f"    {meta['top']} dut (" + ", ".join(f".{vid(n)}({vid(n)})" for n in ports) + ");",
          "    reg tck = 0, tms = 1, tdi = 0; wire tdo;",
          f"    JTAG_SIME2 #(.PART_NAME(\"{part}\")) u_tap (.TCK(tck), .TMS(tms), .TDI(tdi), .TDO(tdo));",
          "    integer pf, cyc = 0;",
          "    initial pf = $fopen(\"probe_trace.txt\", \"w\");",
          f"    always @(posedge {vid(clk)}) begin cyc = cyc + 1; $fdisplay(pf, \"%0d %h\", cyc, dut.\\u_dbg.dbg_probe ); end",
          "    task clk1(input m, input d, output o); begin",
          f"        tms = m; tdi = d; #{tck_half}; o = tdo; tck = 1; #{tck_half}; tck = 0;",
          "    end endtask",
          "    reg [8*2200-1:0] line; reg [8191:0] din, dout; reg [7:0] op; integer r, n, i; reg o;",
          "    task scan(input is_ir, input integer nb); begin",
          "        clk1(1, 0, o); if (is_ir) clk1(1, 0, o); clk1(0, 0, o); clk1(0, 0, o);",
          "        dout = 0;",
          "        for (i = 0; i < nb; i = i + 1) begin clk1(i == nb - 1, din[i], o); dout[i] = o; end",
          "        clk1(1, 0, o); clk1(0, 0, o);",
          "    end endtask",
          "    initial begin",
          "        #200;",
          "        forever begin",
          "            r = $fgets(line, 32'h8000_0000);",
          "            if (r == 0) $finish;",
          "            din = 0; n = 0;",
          "            r = $sscanf(line, \"%c %d %h\", op, n, din);",
          "            if (op == \"R\") begin repeat (6) clk1(1, 0, o); clk1(0, 0, o); $display(\"OK\"); end",
          "            else if (op == \"I\") begin scan(1, n); $display(\"OK %h\", dout); end",
          "            else if (op == \"D\") begin scan(0, n); $display(\"OK %h\", dout); end",
          "            else if (op == \"W\") begin repeat (n) clk1(0, 0, o); $display(\"OK\"); end",
          "            else if (op == \"T\") begin $display(\"OK %0d\", cyc); end",
          "            else if (op == \"Q\") begin $fclose(pf); $display(\"OK\"); $finish; end",
          "            $fflush;",
          "        end",
          "    end",
          "endmodule", ""]
    return "\n".join(L)


class SimJtag:
    """Drives the TB's TAP over stdin/stdout of vvp."""

    def __init__(self, vvp, cwd):
        self.p = subprocess.Popen([str(CONFIG["vvp"]), "-n", str(Path(vvp).resolve())], cwd=cwd, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, bufsize=1)
        self.scans = 0
        self.tck = 0

    def cmd(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()
        while True:
            ln = self.p.stdout.readline()
            if not ln:
                raise DebugError(f"simulation ended on {s!r}")
            if ln.startswith("OK"):
                return ln[2:].strip()

    def reset(self):
        self.cmd("R 0 0")

    def ir(self, bits, val):
        self.scans += 1
        self.tck += bits + 6
        return int(self.cmd(f"I {bits} {val:x}") or "0", 16)

    def dr(self, bits, val):
        self.scans += 1
        self.tck += bits + 5
        return int(self.cmd(f"D {bits} {val:x}") or "0", 16)

    def idle(self, n):
        self.tck += n
        self.cmd(f"W {n} 0")

    def cycle(self):
        return int(self.cmd("T 0 0"))

    def close(self):
        try:
            self.cmd("Q 0 0")
        except DebugError:
            pass
        self.p.wait(timeout=30)


class JtagStreamPort:
    """LiteX JTAGPHY wire format over USER chain DR scans (as openocd jtagstream_poll): 11 bits per word,
    host->target bit0 tx-ready, bits 1-8 data, bit 9 valid; target->host bit0 rx-ready, bits 1-8 data, bit 9 valid."""

    def __init__(self, jtag, chain):
        self.j = jtag
        self.rx = bytearray()
        self.j.reset()
        self.j.ir(CONFIG["ir_len"], CONFIG["user_ir"][chain])
        self.dropped = 0

    def _poll(self, tx):
        n = max(len(tx), CONFIG["poll_words"])
        wb = CONFIG["stream_word_bits"]
        v = 0
        for i in range(n):
            w = (0x201 | (tx[i] << 1)) if i < len(tx) else 0x001
            v |= w << (wb * i)
        r = self.j.dr(wb * n, v)
        got = 0
        for i in range(n):
            w = (r >> (wb * i)) & ((1 << wb) - 1)
            if i < len(tx) and not (w & 1) and self.j.scans > 2:
                self.dropped += 1
            if w & 0x200:
                self.rx.append((w >> 1) & 0xFF)
                got += 1
        return got

    def write(self, data):
        data = bytes(data)
        for k in range(0, len(data), 16):
            self._poll(data[k:k + 16])
        return len(data)

    def read(self, n):
        tries = 0
        while len(self.rx) < n and tries < 2000:
            if not self._poll(b""):
                tries += 1
                self.j.idle(32)
        out, self.rx = bytes(self.rx[:n]), self.rx[n:]
        return out

    def inWaiting(self):
        return len(self.rx)

    def reset_input_buffer(self):
        self.rx.clear()

    def close(self):
        pass


def comm_for_port(port, csr_csv):
    """A litex CommUART (UARTBone protocol) whose byte stream is `port`."""
    from litex.tools.remote.comm_uart import CommUART
    from litex.tools.remote.csr_builder import CSRBuilder

    class CommStream(CommUART):
        def __init__(self):
            CSRBuilder.__init__(self, comm=self, csr_csv=csr_csv)
            self.debug = False
            self.addr_bytes = 4
            self.timeout = 3600.0
            self.max_write_burst_length = 64
            self.port = port

        def _resync(self):
            self.port.reset_input_buffer()
    return CommStream()


def synth_full(meta, out):
    """The whole design as the build synthesizes it (synth_xilinx, I/O and clock buffers), as a netlist of 7-series
    primitives; the analyzer's probe bus is kept so the testbench can record it."""
    script = [f"read_verilog -sv {' '.join(meta['sources'])}", f"hierarchy -top {meta['top']}", "proc", "flatten",
              "setattr -set keep 1 w:u_dbg.dbg_probe",
              f"synth_xilinx -flatten -abc9 -arch xc7 -top {meta['top']}",
              f"write_verilog -noattr {out / 'full_syn.v'}"]
    (out / "full_syn.ys").write_text("\n".join(script) + "\n")
    run([CONFIG["yosys"], "-q", "-s", out / "full_syn.ys"], out / "full_syn.log")
    return out / "full_syn.v"


def build_sim(meta, out, stim):
    """iverilog: synthesized netlist of the full design + Vivado's unisim models (BSCANE2, JTAG_SIME2, LUT/FF/RAM)."""
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    net = synth_full(meta, out)
    (out / "tb_dbg.v").write_text(sim_tb(meta, stim))
    files = [str(net), str(out / "tb_dbg.v"), str(CONFIG["unisims"] / "JTAG_SIME2.v"), str(CONFIG["glbl"])]
    cmd = [CONFIG["iverilog"], "-g2012", "-o", out / "sim.vvp", "-s", "tb_dbg", "-s", "glbl", "-y", CONFIG["unisims"]] + files
    run(cmd, out / "iverilog.log")
    return out / "sim.vvp"


def capture(meta, via, trigger, offset, length, vcd, out, stim=None, server=("localhost", 1234), uart=None,
            baud=115200):
    sys.path[:0] = [str(p) for p in CONFIG["litex_src"]]
    from litescope.software.driver.analyzer import LiteScopeAnalyzerDriver
    t0 = time.time()
    jt = None
    if via == "sim":
        vvp = build_sim(meta, out, stim or {})
        jt = SimJtag(vvp, out)
        port = JtagStreamPort(jt, meta["jtag_chain"])
        bus = comm_for_port(port, meta["csr_csv"])
    elif via == "jtag":
        from litex import RemoteClient
        bus = RemoteClient(host=server[0], port=server[1], csr_csv=meta["csr_csv"])
        bus.open()
    else:
        from litex.tools.remote.comm_uart import CommUART
        bus = CommUART(uart, baudrate=baud, csr_csv=meta["csr_csv"])
        bus.open()
    an = LiteScopeAnalyzerDriver(bus.regs, "analyzer", config_csv=meta["analyzer_csv"], debug=False)
    an.configure_subsampler(1)
    an.configure_group(0)
    for cond in trigger or []:
        an.add_trigger(cond=cond)
    if not trigger:
        an.add_trigger(value=0, mask=0)
    lat = CONFIG["trigger_latency"] if trigger else 0
    off = min(offset + lat, meta["depth"] - 1)
    an.offset, an.length = off, length or meta["depth"]
    an._load_trigger_terms()
    an.storage_offset.write(off)
    an.storage_length.write(an.length)
    an.storage_enable.write(0)
    lo = jt.cycle() if jt else None
    an.storage_enable.write(1)
    an.trigger_enable.write(1)
    if jt:
        start = jt.cycle()
    while not an.done():
        if jt:
            jt.idle(200)
        else:
            time.sleep(0.05)
    data = an.upload()
    an.save(str(vcd))
    res = {"samples": len(data), "vcd": str(vcd), "wall_s": round(time.time() - t0, 1)}
    if jt:
        res.update({"jtag_scans": jt.scans, "tck_cycles": jt.tck, "dropped_tx": port.dropped, "arm_window_cycles": [lo, start]})
        jt.close()
        res["check"] = check_trace(out / "probe_trace.txt", list(data), offset, trigger, meta, lo, start)
    return res


def cond_match(v, cond, layout):
    """cond {probe: "0x..|0b..(x = don't care)|int"} against a sample word with the analyzer's layout."""
    pos = 0
    for name, w in layout:
        if name in cond:
            c = str(cond[name])
            f = (v >> pos) & ((1 << w) - 1)
            m = re.fullmatch(r"0([bx])([0-9a-fA-Fx]+)", c)
            if m:
                step = 1 if m[1] == "b" else 4
                bits = m[2][::-1]
                for i, ch in enumerate(bits):
                    if ch == "x":
                        continue
                    if ((f >> (i * step)) & ((1 << step) - 1)) != int(ch, 16):
                        return False
            elif f != int(c, 0):
                return False
        pos += w
    return True


def check_trace(trace, data, offset, trigger, meta, lo, hi):
    """The analyzer is armed somewhere in clock cycles [lo, hi] (the CSR writes of run()). The capture must be a
    contiguous window of the probe values the simulator recorded at every clock edge, starting at or after lo; with
    a trigger, sample `offset` meets the condition and no sample after hi and before it does (it is the first
    match once armed)."""
    vals = []
    for ln in Path(trace).read_text().splitlines():
        c, v = ln.split()
        vals.append(int(v, 16) if re.fullmatch(r"[0-9a-fA-F]+", v) else None)
    n = len(data)
    layout = [(re.sub(r"\W", "_", nm), w) for nm, w in meta["probes"]]
    hits = [i for i in range(lo - 1, len(vals) - n + 1) if vals[i:i + n] == data]
    out = {"trace_cycles": len(vals), "samples": n, "arm_window": [lo, hi], "windows_matching": len(hits), "pass": False}
    for i in hits:
        if not trigger:
            out.update({"first_sample_cycle": i + 1, "pass": i + 1 <= hi + 4})
            break
        t = i + offset
        if not all(cond_match(vals[t], c, layout) for c in trigger[:1]):
            continue
        if any(cond_match(vals[k], trigger[0], layout) for k in range(hi - 1, t)):
            continue
        out.update({"first_sample_cycle": i + 1, "trigger_cycle": t + 1, "pass": True})
        break
    return out
