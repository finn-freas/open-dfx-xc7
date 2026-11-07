import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ddr_build as db
import gap_build

ROOT = gap_build.ROOT
LX = ROOT / "toolchain" / "litex"

CONFIG = {
    "dry_run": True,
    "python": LX / "venv" / "bin" / "python3",
    "core_gen": ROOT / "flow" / "scope_core_gen.py",
    "yosys": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "yosys",
    "src_dir": ROOT / "designs" / "dbg",
    "out_dir": ROOT / "build" / "dbg",
    "default_depth": 1024,
    "default_clk_freq": 100e6,
    "uart_pins": {"dbg_uart_tx": "D10", "dbg_uart_rx": "A9"},
    "uart_iostandard": "LVCMOS33",
    "vivado_suffix": re.compile(r"(_IBUF_BUFG|_IBUF|_BUFG|_OBUF|_reg)$"),
    "debug_cmd": re.compile(r"^\s*(create_debug_core|connect_debug_port|create_debug_port|set_property\s+.*"
                            r"get_debug_(cores|ports)|set_property\s+MARK_DEBUG\b)"),
    "core_timing": re.compile(r"^\s*(set_false_path|set_max_delay|set_clock_groups)\b"),
    "jtag_tck_pin": "u_dbg/BSCANE2/TCK",
    "jtag_tck_period_ns": 50.0,
    "designs": {
        "x_dbg_net_uart": {"rtl": ["designs/xdc/x_dbg_net/x_dbg_net.v"], "top": "x_dbg_net",
                           "xdc": "designs/xdc/x_dbg_net/x_dbg_net.xdc", "bridge": "uart"},
        "x_dbg_net_jtag": {"rtl": ["designs/xdc/x_dbg_net/x_dbg_net.v"], "top": "x_dbg_net",
                           "xdc": "designs/xdc/x_dbg_net/x_dbg_net.xdc", "bridge": "jtag"},
        "x_dbg_ila_uart": {"rtl": ["designs/xdc/x_dbg_net/x_dbg_net.v"], "top": "x_dbg_net",
                           "xdc": "designs/dbg/src/x_dbg_ila.xdc", "bridge": "uart"},
    },
}


def nets_in(text):
    m = re.search(r"get_nets\s+(?:\[list\s+)?(.*?)\]+\s*$", text)
    if not m:
        return []
    return [t.strip("{}") for t in re.findall(r"\{[^}]*\}|\S+", m[1]) if t.strip("{}")]


def vivado_to_rtl(net):
    base = re.sub(r"\[[^\]]*\]$", "", net)
    base = CONFIG["vivado_suffix"].sub("", base)
    return base.replace("/", ".")


def parse_xdc(path):
    marked, clk, depth, clocks = [], None, None, []
    for ln in Path(path).read_text().splitlines():
        s = ln.split("#")[0].strip()
        if re.match(r"set_property\s+MARK_DEBUG\s+(true|1)\b", s, re.I):
            marked += nets_in(s)
        elif re.match(r"connect_debug_port\s+\S+/clk\b", s):
            clk = (nets_in(s) or [None])[0]
        elif re.match(r"connect_debug_port\s+\S+/probe\d+\b", s):
            marked += nets_in(s)
        elif m := re.match(r"set_property\s+C_DATA_DEPTH\s+(\d+)", s):
            depth = int(m[1])
        elif m := re.match(r"create_clock\b.*-period\s+([\d.]+).*get_ports\s+\{?(\w+)", s):
            clocks.append((m[2], float(m[1])))
    nets = list(dict.fromkeys(vivado_to_rtl(n) for n in marked))
    clk = vivado_to_rtl(clk) if clk else (clocks[0][0] if clocks else None)
    period = dict(clocks).get(clk)
    return {"nets": nets, "clk": clk, "depth": depth or CONFIG["default_depth"],
            "clk_freq": 1e9 / period if period else CONFIG["default_clk_freq"]}


def yosys_expose(rtl, top, nets, clk, out):
    exposed = [n for n in nets + [clk] if n]
    sel = " ".join(f"w:{n}" for n in exposed)
    js = out / "inner_ports.json"
    script = (f"read_verilog -sv {' '.join(str(ROOT / r) for r in rtl)}; hierarchy -top {top}; proc; flatten; "
              f"select -assert-min 1 {sel}; expose {sel}; rename {top} {top}_dbg_inner; "
              f"write_verilog -noattr {out / 'inner.v'}; write_json {js}")
    (out / "expose.ys").write_text(script.replace("; ", "\n") + "\n")
    r = subprocess.run([str(CONFIG["yosys"]), "-q", "-l", str(out / "expose.log"), "-s", str(out / "expose.ys")],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"yosys expose failed, see {out / 'expose.log'}")
    mod = json.loads(js.read_text())["modules"][f"{top}_dbg_inner"]
    return {n: (p["direction"], len(p["bits"])) for n, p in mod["ports"].items()}


def orig_ports(rtl, top, out):
    js = out / "orig_ports.json"
    script = f"read_verilog -sv {' '.join(str(ROOT / r) for r in rtl)}; hierarchy -top {top}; proc; write_json {js}"
    subprocess.run([str(CONFIG["yosys"]), "-q", "-p", script], check=True)
    mod = json.loads(js.read_text())["modules"][top]
    return {n: (p["direction"], len(p["bits"])) for n, p in mod["ports"].items()}


def vid(n):
    return n if re.fullmatch(r"[A-Za-z_]\w*", n) else f"\\{n} "


def decl(d, w):
    return {"input": "input wire", "output": "output wire", "inout": "inout wire"}[d] + (f" [{w - 1}:0]" if w > 1 else "")


def wrapper(top, ports, inner, probes, clk, bridge):
    taps = probes + ([(clk, 1)] if clk not in ports and clk not in dict(probes) else [])
    io = [f"    {decl(d, w)} {vid(n)}" for n, (d, w) in ports.items()]
    if bridge == "uart":
        io += ["    input wire dbg_uart_rx", "    output wire dbg_uart_tx"]
    wires = [f"    wire{f' [{w - 1}:0]' if w > 1 else ''} {vid('dbg_' + n.replace('.', '_'))};"
             for n, w in taps if n not in ports]
    conn = [f".{vid(n)}({vid(n)})" for n in ports] + [f".{vid(n)}({vid('dbg_' + n.replace('.', '_'))})"
                                                     for n, _ in taps if n not in ports]
    sig = lambda n: vid(n) if n in ports else vid("dbg_" + n.replace(".", "_"))
    cat = ", ".join(sig(n) for n, _ in reversed(probes))
    br = ", .dbg_serial_rx(dbg_uart_rx), .dbg_serial_tx(dbg_uart_tx)" if bridge == "uart" else ""
    return "\n".join([f"module {top} (", ",\n".join(io), ");"] + wires + [
        f"    {top}_dbg_inner u_dut ({', '.join(conn)});",
        f"    scope_core u_dbg (.dbg_clk({sig(clk)}), .dbg_probe({{{cat}}}){br});",
        "endmodule", ""])


def xdc_out(src_xdc, bridge):
    keep = [ln for ln in Path(src_xdc).read_text().splitlines() if not CONFIG["debug_cmd"].match(ln)]
    if bridge == "uart":
        used = set(re.findall(r"PACKAGE_PIN\s+(\w+)|LOC\s+(\w+)", "\n".join(keep)))
        flat = {p for t in used for p in t if p}
        for port, pin in CONFIG["uart_pins"].items():
            if pin in flat:
                sys.exit(f"{pin} for {port} is already used in {src_xdc}")
            keep.append(f"set_property -dict {{ PACKAGE_PIN {pin} IOSTANDARD {CONFIG['uart_iostandard']} }} "
                        f"[get_ports {port}]")
    return "\n".join(keep) + "\n"


def vivado_timing(core_xdc, bridge, clk):
    keep = [ln for ln in Path(core_xdc).read_text().splitlines() if CONFIG["core_timing"].match(ln)]
    if bridge == "jtag":
        keep += [f"create_clock -name jtag_tck -period {CONFIG['jtag_tck_period_ns']} "
                 f"[get_pins {CONFIG['jtag_tck_pin']}]",
                 f"set_clock_groups -asynchronous -group [get_clocks jtag_tck] "
                 f"-group [get_clocks -of_objects [get_ports {clk}]]"]
    return "\n".join(keep) + "\n"


def prepare(name, cfg, dry):
    src = CONFIG["src_dir"] / name
    spec = parse_xdc(ROOT / cfg["xdc"])
    print(f"[{'dry' if dry else 'run'}] {name}: nets {spec['nets']} clk {spec['clk']} depth {spec['depth']} "
          f"bridge {cfg['bridge']} -> {src.relative_to(ROOT)}")
    if dry:
        return src
    work = CONFIG["out_dir"] / name / "prep"
    work.mkdir(parents=True, exist_ok=True)
    src.mkdir(parents=True, exist_ok=True)
    (src / "nextpnr").mkdir(exist_ok=True)
    ports = orig_ports(cfg["rtl"], cfg["top"], work)
    inner = yosys_expose(cfg["rtl"], cfg["top"], spec["nets"], spec["clk"], work)
    probes = [(n, inner[n][1]) for n in spec["nets"]]
    core = work / "core"
    js = {"probes": [[n.replace(".", "_"), w] for n, w in probes], "depth": spec["depth"],
          "clk_freq": spec["clk_freq"], "bridge": cfg["bridge"], "out_dir": str(core)}
    (work / "core_spec.json").write_text(json.dumps(js, indent=1) + "\n")
    with open(work / "core_gen.log", "w") as f:
        r = subprocess.run([str(CONFIG["python"]), str(CONFIG["core_gen"]), str(work / "core_spec.json")],
                           stdout=f, stderr=subprocess.STDOUT, env=db.env(), cwd=work)
    if r.returncode:
        sys.exit(f"core generation failed, see {work / 'core_gen.log'}")
    shutil.copy2(work / "inner.v", src / "inner.v")
    for f in ("scope_core.v", "scope_core_mem.init", "csr.csv", "analyzer.csv"):
        shutil.copy2(core / f, src / f)
    (src / "wrapper.v").write_text(wrapper(cfg["top"], ports, inner, probes, spec["clk"], cfg["bridge"]))
    x = xdc_out(ROOT / cfg["xdc"], cfg["bridge"])
    (src / f"{cfg['top']}.xdc").write_text(x + vivado_timing(core / "scope_core.xdc", cfg["bridge"], spec["clk"]))
    (src / "nextpnr" / f"{cfg['top']}.xdc").write_text(x)
    (src / "top.txt").write_text(cfg["top"] + "\n")
    (src / "SOURCE.txt").write_text(f"generated by flow/mark_debug.py from {cfg['xdc']} and {' '.join(cfg['rtl'])}\n"
                                    f"probes: {probes}, clock {spec['clk']}, depth {spec['depth']}, "
                                    f"bridge {cfg['bridge']}\n")
    return src


def main():
    ap = argparse.ArgumentParser(description="MARK_DEBUG / Vivado debug-core XDC -> LiteScope analyzer inserted on "
                                             "the marked nets (yosys expose + standalone LiteScope core)")
    ap.add_argument("designs", nargs="*", default=list(CONFIG["designs"]))
    ap.add_argument("--variant", action="append", help=f"one of {list(db.CONFIG['variants'])} (default gapfix)")
    ap.add_argument("--prep-only", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    for name in a.designs:
        cfg = CONFIG["designs"][name]
        src = prepare(name, cfg, dry)
        if a.prep_only:
            continue
        for variant in a.variant or ["gapfix"]:
            v = db.CONFIG["variants"][variant]
            absp = lambda p: str(ROOT / p) if p else None
            tools = {"nextpnr": absp(v["nextpnr"]), "chipdb": absp(v["chipdb"]),
                     "yosys_plugin": absp(v["yosys_plugin"]), "clkbuf_pass": v["clkbuf_pass"]}
            if not dry:
                db.wait_gate()
            rtl = [src / "wrapper.v", src / "inner.v", src / "scope_core.v"]
            gap_build.build(name, src, cfg["top"], rtl, src / "nextpnr" / f"{cfg['top']}.xdc",
                            CONFIG["out_dir"] / name / variant, 100, dry, v["npr_args"], tools)


if __name__ == "__main__":
    main()
