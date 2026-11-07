"""`ofx ip ...` and `ofx debug ...` subcommands."""
import json
import subprocess
import sys
from pathlib import Path

from . import FLOW, ROOT
from . import debug as debugmod
from . import ip as ipmod
from . import ip_bram, ip_clk, ip_fifo
from . import project as P
from .stage import vhdl_sources

CONFIG = {
    "dry_run": True,
    "capture": FLOW / "dbg_capture.py",
}


def _proj(a, need=True):
    try:
        return P.Project(P.find(a.project))
    except P.ProjectError as e:
        if need:
            sys.exit(f"ofx: {e}")
        return None


def _dry(a):
    return CONFIG["dry_run"] and not getattr(a, "run", False)


def _write(path, text, dry):
    print(f"[{'dry' if dry else 'run'}] write {path} ({len(text)} bytes)")
    if not dry:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text)


def cmd_ip_clk(a):
    dry = _dry(a)
    proj = _proj(a, need=False)
    part = a.part or (proj.part if proj else "xc7a35tcsg324-1")
    try:
        outs = ip_clk.parse_outs(a.out)
        res = ip_clk.solve(a.input, outs, a.primitive, part, a.jitter)
    except ip_clk.ClkError as e:
        sys.exit(f"ofx ip clk: {e}")
    print(ip_clk.table(res))
    if a.json:
        print(ip_clk.dump(res))
    d = Path(a.dir)
    _write(d / f"{a.name}.v", ip_clk.verilog(a.name, res, in_port=a.in_port, in_buf=a.in_buf), dry)
    _write(d / f"{a.name}.xdc", ip_clk.xdc(res, a.in_port), dry)


def cmd_ip_fifo(a):
    dry = _dry(a)
    t = {"name": a.name, "impl": a.impl, "width": a.width, "depth": a.depth, "fwft": a.fwft}
    for k in ("almost_full", "almost_empty", "valid", "overflow", "underflow", "data_count", "wr_data_count",
              "rd_data_count"):
        if getattr(a, k):
            t[k] = True
    if a.prog_full is not None:
        t["prog_full"] = a.prog_full
    if a.prog_empty is not None:
        t["prog_empty"] = a.prog_empty
    try:
        v, info, _ = ipmod.gen_fifo(t)
    except ip_fifo.FifoError as e:
        sys.exit(f"ofx ip fifo: {e}")
    print(info)
    _write(Path(a.dir) / f"{a.name}.v", v, dry)


def cmd_ip_bram(a):
    dry = _dry(a)
    t = {"name": a.name, "type": a.type, "width": a.width, "depth": a.depth, "init": a.init, "reg_a": a.reg_a,
         "reg_b": a.reg_b}
    try:
        v, info, _ = ipmod.gen_bram(t, Path.cwd())
    except ip_bram.BramError as e:
        sys.exit(f"ofx ip bram: {e}")
    print(info)
    _write(Path(a.dir) / f"{a.name}.v", v, dry)


def cmd_ip_gen(a):
    proj = _proj(a)
    try:
        ipmod.gen_all(proj, proj.build / ipmod.CONFIG["dir"], _dry(a))
    except ipmod.IpError as e:
        sys.exit(f"ofx: {e}")


def cmd_debug_insert(a):
    proj = _proj(a)
    if not proj.raw.get("debug"):
        sys.exit("ofx debug: the project has no [debug] table")
    try:
        srcs = vhdl_sources(proj, proj.build / "stage", _dry(a))
        if proj.raw.get("ip"):
            srcs += ipmod.gen_all(proj, proj.build / ipmod.CONFIG["dir"], _dry(a))[0]
        debugmod.insert(proj, srcs, proj.constraints, proj.build / debugmod.CONFIG["out"], _dry(a))
    except (debugmod.DebugError, P.ProjectError, ipmod.IpError) as e:
        sys.exit(f"ofx debug: {e}")
    if not proj.raw["debug"].get("insert"):
        print("ofx debug: [debug] insert = false, so `ofx build` builds the design without the analyzer")


def cmd_debug_capture(a):
    proj = _proj(a)
    meta = proj.build / debugmod.CONFIG["out"] / "debug.json"
    cmd = [str(debugmod.CONFIG["litex_python"]), str(CONFIG["capture"]), str(meta), "--via", a.via,
           "--vcd", str(Path(a.vcd).resolve()) if a.vcd else str(proj.build / debugmod.CONFIG["out"] / "capture.vcd"), "--offset", str(a.offset)]
    for t in a.trigger:
        cmd += ["--trigger", t]
    for s in a.set:
        cmd += ["--set", s]
    if a.length:
        cmd += ["--length", str(a.length)]
    if a.server:
        cmd += ["--server", a.server]
    if a.uart:
        cmd += ["--uart", a.uart]
    print(f"[{'dry' if _dry(a) else 'run'}] {' '.join(cmd)}")
    if _dry(a):
        return
    if not meta.exists():
        sys.exit(f"ofx debug capture: {meta} missing; run `ofx debug insert --run` (or `ofx build --run`) first")
    sys.exit(subprocess.run(cmd, cwd=ROOT).returncode)


def add_parsers(sub):
    ip = sub.add_parser("ip", help="IP generators: clocking wizard, FIFO generator, block memory generator")
    ips = ip.add_subparsers(dest="icmd", required=True)
    c = ips.add_parser("clk", help="MMCME2/PLLE2 parameters for wanted outputs, Verilog + XDC (write with --run)")
    c.add_argument("--in", dest="input", type=float, required=True, help="input clock MHz")
    c.add_argument("--out", action="append", required=True, help="output freq[@phase][/duty%%], repeatable")
    c.add_argument("--primitive", choices=["auto", "MMCM", "PLL"], default="MMCM")
    c.add_argument("--jitter", choices=["balanced", "power"], default="balanced")
    c.add_argument("--part", help="part (speed grade sets the VCO/PFD limits; default the project's)")
    c.add_argument("--name", default="clk_wiz_0")
    c.add_argument("--in-port", default="clk_in1")
    c.add_argument("--in-buf", choices=["none", "ibuf"], default="none")
    c.add_argument("--dir", default=".")
    c.add_argument("--json", action="store_true")
    c.add_argument("--run", action="store_true")
    c.set_defaults(fn=cmd_ip_clk)
    f = ips.add_parser("fifo", help="fabric (BRAM/LUTRAM) or built-in FIFO18E1/36E1 FIFO (write with --run)")
    f.add_argument("--impl", default="Common_Clock_Block_RAM", choices=ip_fifo.CONFIG["impls"])
    f.add_argument("--width", type=int, required=True)
    f.add_argument("--depth", type=int, required=True)
    f.add_argument("--fwft", action="store_true")
    for k in ("almost_full", "almost_empty", "valid", "overflow", "underflow", "data_count", "wr_data_count",
              "rd_data_count"):
        f.add_argument("--" + k.replace("_", "-"), dest=k, action="store_true")
    f.add_argument("--prog-full", type=int)
    f.add_argument("--prog-empty", type=int)
    f.add_argument("--name", default="fifo_generator_0")
    f.add_argument("--dir", default=".")
    f.add_argument("--run", action="store_true")
    f.set_defaults(fn=cmd_ip_fifo)
    b = ips.add_parser("bram", help="RAMB36E1/RAMB18E1 memory with .coe/.mem init (write with --run)")
    b.add_argument("--type", default="Single_Port_RAM", choices=ip_bram.CONFIG["types"])
    b.add_argument("--width", type=int, required=True)
    b.add_argument("--depth", type=int, required=True)
    b.add_argument("--init", help=".coe or .mem file")
    b.add_argument("--reg-a", action="store_true", help="primitive output register on port A (latency 2)")
    b.add_argument("--reg-b", action="store_true")
    b.add_argument("--name", default="blk_mem_gen_0")
    b.add_argument("--dir", default=".")
    b.add_argument("--run", action="store_true")
    b.set_defaults(fn=cmd_ip_bram)
    g = ips.add_parser("gen", help="generate every [[ip.*]] of ofx.toml into build/ip (ofx build does this too)")
    g.add_argument("--run", action="store_true")
    g.set_defaults(fn=cmd_ip_gen)
    d = sub.add_parser("debug", help="ILA equivalent: LiteScope analyzer on MARK_DEBUG nets over JTAG (BSCANE2)")
    ds = d.add_subparsers(dest="gcmd", required=True)
    i = ds.add_parser("insert", help="synthesize, keep the debug nets, wrap with the analyzer core (--run)")
    i.add_argument("--run", action="store_true")
    i.set_defaults(fn=cmd_debug_insert)
    k = ds.add_parser("capture", help="arm, trigger, upload, write VCD (--via sim simulates the whole design)")
    k.add_argument("--via", choices=["sim", "jtag", "uart"], default="sim")
    k.add_argument("--trigger", action="append", default=[], help="probe=value, e.g. dq=0b1111xxxx0000xxxx")
    k.add_argument("--offset", type=int, default=0, help="samples before the trigger")
    k.add_argument("--length", type=int)
    k.add_argument("--set", action="append", default=[], help="sim: drive top input, e.g. sw=3")
    k.add_argument("--vcd")
    k.add_argument("--server", help="litex_server host:port for --via jtag")
    k.add_argument("--uart", help="serial port for --via uart")
    k.add_argument("--run", action="store_true")
    k.set_defaults(fn=cmd_debug_capture)
