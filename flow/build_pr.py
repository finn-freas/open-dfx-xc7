import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "design": "pr_open",
    "designs": {
        "rv_flash": {"top": "rv_flash", "rm_dir": "rv_soc/pr", "static_rtl": ["../common/dfx_decoupler.v", "rv_flash.v", "rm_bridge_fenced.v", "spi_master.v", "uart.v", "picorv32.v", "../rv_soc/pr/rm_stub.v"], "rms": {"andn": "rm_core_andn.v", "xor": "rm_core_xor.v", "add": "rm_core_add.v"}, "rm_ports": ["clk", "valid", r"funct\[\d+\]", r"rs1\[\d+\]", r"rs2\[\d+\]", r"rd\[\d+\]", "ready"]},
        "pr_open": {"static_rtl": ["top.v", "rm_stub.v"]},
        "pr_uart": {"static_rtl": ["top.v", "uart_icap.v", "../pr_open/rm_stub.v"]},
        "pr_add": {"src": "pr_open", "static_rtl": ["top.v", "rm_stub.v"], "rm_shell": "rm_shell_oa.v",
                   "rms": {"count": "rm_core_count.v", "add": "rm_core_add.v"}},
        "pr_xor": {"src": "pr_open", "static_rtl": ["top.v", "rm_stub.v"], "rm_shell": "rm_shell_oa.v",
                   "rms": {"count": "rm_core_count.v", "xor": "rm_core_xor.v"}},
        "rv_pr": {"src": "rv_soc", "top": "rv_soc", "rm_dir": "rv_soc/pr",
                  "static_rtl": ["rv_soc.v", "uart.v", "picorv32.v", "pr/rm_stub.v"],
                  "rms": {"xor": "rm_core_xor.v", "andn": "rm_core_andn.v", "add": "rm_core_add.v", "grey": "rm_core_grey.v"},
                  "rm_ports": ["clk", "valid", r"funct\[\d+\]", r"rs1\[\d+\]", r"rs2\[\d+\]", r"rd\[\d+\]", "ready"]},
        "rv_d": {"src": "rv_soc", "top": "rv_soc", "rm_dir": "rv_soc/pr", "detour": True,
                 "static_rtl": ["rv_soc.v", "uart.v", "picorv32.v", "pr/rm_stub.v"],
                 "rms": {"xor": "rm_core_xor.v", "andn": "rm_core_andn.v", "add": "rm_core_add.v",
                         "rot": "rm_core_rot.v", "popc": "rm_core_popc.v", "minmax": "rm_core_minmax.v"},
                 "rm_ports": ["clk", "valid", r"funct\[\d+\]", r"rs1\[\d+\]", r"rs2\[\d+\]", r"rd\[\d+\]", "ready"]},
        "rv_b": {"src": "rv_soc", "top": "rv_soc", "rm_dir": "rv_soc/pr", "region": "SLICE_X12Y0:SLICE_X15Y49",
                 "shell_spec": "ports.json", "static_rtl": ["rv_soc.v", "uart.v", "picorv32.v", "pr/rm_stub.v"],
                 "rms": {"xor": "rm_core_xor.v", "add": "rm_core_add.v"},
                 "rm_ports": ["clk", "valid", r"funct\[\d+\]", r"rs1\[\d+\]", r"rs2\[\d+\]", r"rd\[\d+\]", "ready"]},
        "rv_c": {"src": "rv_soc", "top": "rv_soc", "rm_dir": "rv_soc/pr", "region": "SLICE_X12Y75:SLICE_X15Y124",
                 "shell_spec": "ports.json", "static_rtl": ["rv_soc.v", "uart.v", "picorv32.v", "pr/rm_stub.v"],
                 "rms": {"xor": "rm_core_xor.v", "add": "rm_core_add.v"},
                 "rm_ports": ["clk", "valid", r"funct\[\d+\]", r"rs1\[\d+\]", r"rs2\[\d+\]", r"rd\[\d+\]", "ready"]},
    },
    "top": "top",
    "rm_dir": "pr_open",
    "rm_shell": "rm_shell.v",
    "rms": {"count": "rm_core_count.v", "shift": "rm_core_shift.v"},
    "rm_inst": "u_rm",
    "rm_ports": ["clk", r"din\[\d+\]", r"dout\[\d+\]"],
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "confine": True,
    "detour": False,
    "dry_run": True,
}

ROOT = CONFIG["root"]
FLOW = ROOT / "flow"
sys.path.insert(0, str(FLOW))
import build_openxc7


def run(name, out, cmd, dry):
    if out.exists():
        print(f"[skip] {name}: {out.name} exists")
        return
    print(f"[{'dry' if dry else 'run'}] {name}")
    if dry:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    log = out.with_suffix(".log")
    with open(log, "w") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONHASHSEED": "0"})
    if r.returncode != 0 or not out.exists():
        sys.exit(f"{name} failed, see {log}")


def yosys(script):
    return [build_openxc7.tool("yosys"), "-p", script]


def main():
    ap = argparse.ArgumentParser(description="Open-tools partial reconfiguration build: static once, RMs out of context, replayed static")
    ap.add_argument("--design", default=CONFIG["design"], choices=sorted(CONFIG["designs"]))
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    CONFIG["design"] = a.design
    dcfg = CONFIG["designs"][a.design]
    for k in ("top", "rm_dir", "rm_shell", "rm_ports", "rm_inst", "region"):
        if k in dcfg:
            CONFIG[k] = dcfg[k]
    import region
    viol = region.pair_violations(region.load_grid(), CONFIG["region"])
    if viol:
        sys.exit(f"region {CONFIG['region']} splits {len(viol)} INT_L/INT_R pair(s), e.g. {viol[0]}; Vivado rejects such pblocks")
    src_name = dcfg.get("src", a.design)
    rms = dcfg.get("rms", CONFIG["rms"])
    src = ROOT / "designs" / src_name
    rmsrc = ROOT / "designs" / CONFIG["rm_dir"]
    out = ROOT / "build" / "pr" / CONFIG["design"]
    out.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    static = out / "static_synth.json"
    rtl = " ".join(str(src / f) for f in CONFIG["designs"][a.design]["static_rtl"])
    run("synth static", static, yosys(f"read_verilog -sv {rtl}; synth_xilinx -flatten -abc9 -arch xc7 -top {CONFIG['top']}; "
                                      f"write_json {static}"), dry)
    (out / "region.txt").write_text(CONFIG["region"] + "\n")
    shell = rmsrc / dcfg.get("rm_shell", CONFIG["rm_shell"])
    if "shell_spec" in dcfg:
        shell = out / "rm_shell.v"
        run("gen shell", shell, [py, str(FLOW / "gen_shell2.py"), str(rmsrc / dcfg["shell_spec"]), str(shell),
                                 "--region", CONFIG["region"]], dry)
    names = list(rms)
    linked = {}
    for rm in names:
        rj = out / f"rm_{rm}_synth.json"
        rtl = f"{shell} {rmsrc / rms[rm]}"
        run(f"synth rm {rm}", rj, yosys(f"read_verilog -sv {rtl}; synth_xilinx -flatten -abc9 -arch xc7 -noiopad -noclkbuf "
                                        f"-top rm_slot; rename -enumerate -pattern rmx_% rm_slot; write_json {rj}"), dry)
        rp = out / f"rm_{rm}_placed.json"
        run(f"place rm {rm}", rp, [py, str(FLOW / "rm_place.py"), str(rj), str(rp), "--region", CONFIG["region"]], dry)
        lj = out / f"cfg_{rm}_linked.json"
        run(f"link {rm}", lj, yosys(f"read_json {static}; delete =A:blackbox; read_json {rp}; delete =A:blackbox; "
                                    f"read_verilog -lib +/xilinx/cells_sim.v +/xilinx/cells_xtra.v; hierarchy -top {CONFIG['top']}; "
                                    f"flatten; select {CONFIG['top']}; write_json -selected {lj}"), dry)
        linked[rm] = lj
        pins = out / f"cfg_{rm}.rm.preplaced"
        run(f"pins {rm}", pins, [py, str(FLOW / "bel_pins.py"), str(lj), str(pins), "--prefix", CONFIG["rm_inst"] + "."], dry)
        pk = out / f"cfg_{rm}.packer.done"
        run(f"packer pins {rm}", pk, ["bash", "-c", f"{py} {FLOW / 'packer_pins.py'} {lj} {next(src.glob('*.xdc'))} {rp} {pins} "
                                                     f"--prefix {CONFIG['rm_inst']}. && touch {pk}"], dry)
    keep = [x for p in CONFIG["rm_ports"] for x in ("--keep", rf"{CONFIG['rm_inst']}\.{p}")]
    first = names[0]
    bdir = ROOT / "build" / "openxc7" / src_name
    prefix = "pr" if src_name == a.design else a.design

    def pnr(rm, opts, extra=(), suffix=""):
        name = f"{prefix}_{rm}{suffix}"
        cmd = [py, str(FLOW / "build_openxc7.py"), src_name, "--top", CONFIG["top"], "--name", name,
               "--json", str(linked[rm])] + [x for o in opts for x in ("--opt", o)] + list(extra) + ["--run"]
        run(f"pnr {rm}{suffix}", bdir / name / f"{CONFIG['top']}.bit", cmd, dry)

    pnr(first, [f"preplaced={out / f'cfg_{first}.rm.preplaced'}"])
    ref = out / "static"
    run("dump static", Path(str(ref) + ".prerouted"),
        [py, str(FLOW / "replay_dump.py"), str(bdir / f"{prefix}_{first}" / f"{CONFIG['top']}_routed.json"), str(ref),
         "--exclude", CONFIG["rm_inst"] + "."] + keep, dry)
    sroute = Path(str(ref) + ".prerouted")
    if dcfg.get("detour", CONFIG["detour"]):
        sroute = out / "static.detour.prerouted"
        run("static detour", sroute, [py, str(FLOW / "static_detour.py"), str(ref) + ".prerouted", str(sroute),
                                      "--region", CONFIG["region"], "--keep", re.escape(CONFIG["rm_inst"] + ".")], dry)
    xdc = next(src.glob("*.xdc"))
    loc = Path(str(ref) + ".loc.xdc")
    bxdc = out / "replay.xdc"
    if not dry and not bxdc.exists():
        bxdc.write_text(xdc.read_text() + (loc.read_text() if loc.exists() else ""))
    for rm in names[1:]:
        allp = out / f"cfg_{rm}.all.preplaced"
        if not dry and not allp.exists():
            allp.write_text(Path(str(ref) + ".preplaced").read_text() + (out / f"cfg_{rm}.rm.preplaced").read_text())
        pnr(rm, [f"preplaced={allp}", f"prerouted={sroute}"], ["--xdc", str(bxdc)])
    if CONFIG["confine"]:
        for rm in names:
            rr = out / f"rm_{rm}.region.prerouted"
            run(f"region route {rm}", rr, [py, str(FLOW / "region_route.py"),
                                            str(bdir / f"{prefix}_{rm}" / f"{CONFIG['top']}_routed.json"),
                                            str(sroute), str(rr), "--region", CONFIG["region"]], dry)
            cp, cr = out / f"cfg_{rm}.c.preplaced", out / f"cfg_{rm}.c.prerouted"
            if not dry and not cr.exists():
                cp.write_text(Path(str(ref) + ".preplaced").read_text() + (out / f"cfg_{rm}.rm.preplaced").read_text())
                cr.write_text(sroute.read_text() + rr.read_text())
            pnr(rm, [f"preplaced={cp}", f"prerouted={cr}"], ["--xdc", str(bxdc)], suffix="_c")
        print(f"region-confined bitstreams under {bdir}/{prefix}_*_c")
    print(f"bitstreams under {bdir}/{prefix}_*")


if __name__ == "__main__":
    main()
