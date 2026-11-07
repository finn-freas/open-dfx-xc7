import argparse
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import device

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "dry_run": True,
    "ports_json": "ps7_ports.json",
    "port_classes": ("normal", "mio"),
    "tools": ROOT / "toolchain" / "oss-cad-suite" / "bin",
    "cells_sim": ROOT / "toolchain" / "oss-cad-suite" / "share" / "yosys" / "xilinx" / "cells_sim.v",
    "b2n_py": ROOT / "toolchain" / "fasm2bels" / "venv" / "bin" / "python",
    "trace_py": ROOT / "toolchain" / "zynq" / "venv" / "bin" / "python",
    "conn_db_dir": ROOT / "build" / "b2n",
    "min_free_gb": 4,
    "f2b_stubs": "rr_graph rr_graph.capnp rr_graph.capnp.graph2 fpga_interchange fpga_interchange.interchange_capnp "
                 "fpga_interchange.logical_netlist fpga_interchange.physical_netlist",
    "bfm": "sim/ps7_bfm.v",
    "tb": "sim/tb_ps7_axi_z7.v",
}

F2B = r"""
import sys, types
def stub(n):
    m = types.ModuleType(n)
    def ga(a):
        if a.startswith("__"):
            raise AttributeError(a)
        def init(self, *x, **k):
            raise RuntimeError(n + "." + a + " is not installed")
        return type(a, (), {"__init__": init})
    m.__getattr__ = ga
    m.__path__ = []
    sys.modules[n] = m
for n in sys.argv[1].split():
    stub(n)
if sys.argv[2] == "db":
    from fasm2bels.database.create_channels import create_channels
    create_channels(*sys.argv[3:6])
else:
    from fasm2bels.fasm2bels import main
    sys.argv = ["fasm2bels"] + sys.argv[3:]
    main()
"""


def env(extra=None):
    e = dict(os.environ)
    e["PATH"] = f"{CONFIG['tools']}:{e['PATH']}"
    e.update(extra or {})
    return e


def run(cmd, dry, log=None, extra_env=None, check=True):
    shown = ["<fasm2bels wrapper>" if c is F2B else ("<stubs>" if c is CONFIG["f2b_stubs"] else str(c)) for c in cmd]
    print(f"[{'dry' if dry else 'run'}] {' '.join(shown)}" + (f"  > {log}" if log else ""), flush=True)
    if dry:
        return 0
    with open(log, "w") if log else open(os.devnull, "w") as f:
        r = subprocess.run([str(c) for c in cmd], env=env(extra_env), stdout=f if log else None,
                           stderr=subprocess.STDOUT if log else None, cwd=ROOT)
    if check and r.returncode:
        sys.exit(f"zynq_pl_sim: failed (exit {r.returncode}): {cmd[0]}" + (f", see {log}" if log else ""))
    return r.returncode


def ports_vh(db_family, out):
    ports = json.loads((db_family / CONFIG["ports_json"]).read_text())
    lines = []
    for name in sorted(ports):
        p = ports[name]
        if p["class"] not in CONFIG["port_classes"]:
            continue
        rng = f"[{p['max']}:{p['min']}] " if p["width"] > 1 else ""
        lines.append(f"    {p['direction']} wire {rng}{name}")
    out.write_text(",\n".join(lines) + "\n")
    return len(lines)


def free_gb():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    return 0.0


def sim(name, sources, top, trace, out, dry):
    vvp = out / f"{name}.vvp"
    run(["iverilog", "-g2012", "-I", out, "-s", top, "-o", vvp] + sources, dry, log=out / f"{name}_iverilog.log")
    log = out / f"{name}_sim.log"
    run(["vvp", "-n", vvp, f"+TRACE={trace}"], dry, log=log, check=False)
    if dry:
        return {"name": name}
    text = log.read_text()
    res = next((l for l in text.splitlines() if l.startswith("PS7 BFM:")), "PS7 BFM: no result")
    return {"name": name, "log": str(log), "result": res, "fails": [l for l in text.splitlines() if l.startswith("FAIL")],
            "pass": res.endswith("PASS")}


def main():
    ap = argparse.ArgumentParser(description="Simulate the ps7_axi_z7 PL against a PS7 bus-functional model that replays "
                                 "the bare-metal app's M_AXI_GP0 accesses: RTL, and the netlist decoded from the bitstream")
    ap.add_argument("project", help="ofx.toml (examples/ps7_axi_z7)")
    ap.add_argument("--elf", help="app ELF (default: <build>/boot/app.elf)")
    ap.add_argument("--no-netlist", action="store_true", help="RTL only")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    pf = Path(a.project).resolve()
    if pf.is_dir():
        pf = pf / "ofx.toml"
    proj = tomllib.loads(pf.read_text())
    pdir = pf.parent
    p = proj["project"]
    build = pdir / p.get("build_dir", "build")
    board = tomllib.loads((ROOT / "boards" / f"{p['board']}.toml").read_text())
    part = board["board"]["part"]
    dev = device.resolve(part)
    db_family = ROOT / device.CONFIG["db"] / dev["family"]
    out = build / "plsim"
    elf = Path(a.elf) if a.elf else build / "boot" / "app.elf"
    bit = build / "impl" / f"{p['top']}.bit"
    if not dry:
        out.mkdir(parents=True, exist_ok=True)
        print(f"ps7_ports.vh: {ports_vh(db_family, out / 'ps7_ports.vh')} ports from {db_family / CONFIG['ports_json']}")
    trace = out / "trace.hex"
    run([CONFIG["trace_py"], "-I", ROOT / "flow" / "zynq_app_trace.py", elf, trace], dry, log=out / "trace.log")
    bfm, tb = pdir / CONFIG["bfm"], pdir / CONFIG["tb"]
    rtl = [pdir / s for s in p["sources"]]
    results = {"trace": json.loads(trace.with_suffix(".json").read_text()) if not dry else None, "sims": []}
    results["sims"].append(sim("rtl", [tb, bfm, CONFIG["cells_sim"]] + rtl, "tb", trace, out, dry))
    if not a.no_netlist:
        d = out / "b2n"
        conn = CONFIG["conn_db_dir"] / f"conn_{part}.db"
        if not dry:
            d.mkdir(exist_ok=True)
        if not conn.exists():
            if not dry and free_gb() < CONFIG["min_free_gb"]:
                sys.exit(f"zynq_pl_sim: {free_gb():.1f} GB available, need {CONFIG['min_free_gb']} GB to build {conn}")
            run([CONFIG["b2n_py"], "-W", "ignore", "-c", F2B, CONFIG["f2b_stubs"], "db", db_family, part,
                 f"{conn}.tmp"], dry, log=f"{conn}.log")
            if not dry:
                Path(f"{conn}.tmp").rename(conn)
        penv = device.env(part)
        fasm = d / "design.fasm"
        run([CONFIG["b2n_py"], "-W", "ignore", ROOT / "flow" / "bit2fasm.py", bit, fasm], dry, log=d / "bit2fasm.log",
            extra_env=penv)
        net = d / "design.v"
        run([CONFIG["b2n_py"], "-W", "ignore", "-c", F2B, CONFIG["f2b_stubs"], "run",
             "--connection_database", conn, "--db_root", db_family, "--part", part, "--fasm_file", fasm,
             "--verilog_file", net, "--xdc_file", d / "design.xdc", "--allow_orphan_sinks", "--top", p["top"],
             "--input_xdc", pdir / p["constraints"][0]], dry, log=d / "fasm2bels.log", extra_env=penv)
        results["sims"].append(sim("netlist", [tb, bfm, CONFIG["cells_sim"], net], "tb", trace, out, dry))
        if not dry:
            txt = net.read_text()
            results["netlist"] = {"file": str(net), "has_ps7": "PS7 " in txt,
                                  "orphan_sinks": (d / "fasm2bels.log").read_text().count("failed to find source")}
    if dry:
        print("DRY RUN: nothing simulated. Add --run.")
        return
    (out / "result.json").write_text(json.dumps(results, indent=1) + "\n")
    print(f"trace: {results['trace']['ops']} M_AXI_GP0 accesses from {elf} (app result in Unicorn: "
          f"{'PASS' if results['trace']['pass'] else 'FAIL'})")
    for s in results["sims"]:
        print(f"{s['name']}: {s['result']}")
        for f in s["fails"][:10]:
            print(f"   {f}")
    if "netlist" in results:
        print(f"netlist: PS7 instance {'present' if results['netlist']['has_ps7'] else 'MISSING'}, "
              f"{results['netlist']['orphan_sinks']} orphan sinks")
    ok = results["trace"]["pass"] and all(s["pass"] for s in results["sims"]) and \
        results.get("netlist", {}).get("has_ps7", True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
