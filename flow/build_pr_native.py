import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import device

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "dry_run": True,
    "src": "rv_soc",
    "top": "rv_soc",
    "rm_dir": "rv_soc/pr",
    "static_rtl": ["rv_soc.v", "uart.v", "picorv32.v", "pr/rm_stub.v"],
    "rm_shell": "rm_shell.v",
    "rms": {"xor": "rm_core_xor.v", "andn": "rm_core_andn.v", "add": "rm_core_add.v", "rot": "rm_core_rot.v",
            "popc": "rm_core_popc.v", "minmax": "rm_core_minmax.v"},
    "default_rms": ["xor", "andn"],
    "rm_inst": "u_rm",
    "rm_ports": ["clk", "valid", r"funct\[\d+\]", r"rs1\[\d+\]", r"rs2\[\d+\]", r"rd\[\d+\]", "ready"],
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "out": "build/patched/rv_pr_native",
    "design": "rv_pr",
    "designs": {
        "rv_pr": {},
        "rv_b": {"region": "SLICE_X12Y0:SLICE_X15Y49", "shell_spec": "ports.json", "out": "build/patched/rv_b_native",
                 "default_rms": ["xor", "andn", "add"]},
        "rv_c": {"region": "SLICE_X12Y75:SLICE_X15Y124", "shell_spec": "ports.json", "out": "build/patched/rv_c_native",
                 "default_rms": ["xor", "andn", "add"], "shared_frame_pblock": True},
        "rv_m": {"region": "SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59",
                 "shell_spec": "ports_clk.json", "out": "build/patched/rv_m_native",
                 "rms": {"tbl": "rm_core_tbl.v", "tbl2": "rm_core_tbl2.v", "xorc": "rm_core_xorc.v"},
                 "default_rms": ["tbl", "tbl2", "xorc"], "shared_frame_pblock": True, "variant": "replay"},
        "rv2": {"src": "rv_soc2", "static_rtl": ["rv_soc.v", "uart.v", "picorv32.v", "pr/rm_stub.v"],
                "shell_spec": "ports.json", "out": "build/patched/rv2_native", "variant": "rtkeep",
                "rms": {"xor": "rm_core_xor.v", "andn": "rm_core_andn.v", "add": "rm_core_add.v", "grey": "rm_core_grey.v"},
                "partitions": [
                    {"name": "rp1", "inst": "u_rm", "module": "rm_slot", "region": "SLICE_X12Y100:SLICE_X15Y149",
                     "rms": ["xor", "andn"]},
                    {"name": "rp2", "inst": "u_rm2", "module": "rm_slot2", "region": "SLICE_X12Y0:SLICE_X15Y49",
                     "rms": ["add", "grey"]},
                ],
                "configs": [["xor", "add"], ["andn", "add"], ["xor", "grey"], ["andn", "grey"]]},
        "rv_pp": {"shell_spec": "ports.json", "out": "build/patched/rv_pp_native", "variant": "partpin",
                  "partpins": True, "pp_register": ["ready"],
                  "rms": {"xor": "rm_core_xor.v", "andn": "rm_core_andn.v", "add": "rm_core_add.v",
                          "rot": "rm_core_rot.v"},
                  "default_rms": ["xor", "andn", "add", "rot"]},
        "rv_ppa": {"shell_spec": "ports.json", "out": "build/patched/rv_ppa_native", "variant": "partpin2",
                   "partpins": "auto", "pp_register": ["ready"],
                   "rms": {"xor": "rm_core_xor.v", "andn": "rm_core_andn.v", "add": "rm_core_add.v",
                           "rot": "rm_core_rot.v"},
                   "default_rms": ["xor", "andn", "add", "rot"]},
        "rv_ppt": {"shell_spec": "ports.json", "out": "build/patched/rv_ppt_native", "variant": "partpin3",
                   "partpins": "auto", "pp_register": ["ready"],
                   "rms": {"xor": "rm_core_xor.v", "andn": "rm_core_andn.v", "add": "rm_core_add.v",
                           "rot": "rm_core_rot.v"},
                   "default_rms": ["xor", "andn", "add", "rot"],
                   "place_union": ["xor", "andn", "add", "rot"], "grey_clock_leaf": True, "fix_endpoints": True,
                   "pin_module_ends": True, "pin_w_module": 0.5, "pin_exclude_wrap_exits": True},
    },
    "shared_pblock": "pblock_shared_dyn",
    "pblock": "pblock_rm",
    "variants": {
        "router": {"nextpnr": "build/nextpnr-build/router/nextpnr-himbaechel", "contain_routing": True,
                   "args": ["--router2-region-keep-out"]},
        "router_nokeepout": {"nextpnr": "build/nextpnr-build/router/nextpnr-himbaechel", "contain_routing": True,
                             "args": []},
        "pblock": {"nextpnr": "build/nextpnr-build/pblock/nextpnr-himbaechel", "contain_routing": False, "args": []},
        "replay": {"nextpnr": "build/nextpnr-build/replay/nextpnr-himbaechel", "contain_routing": True,
                   "args": ["--router2-region-keep-out"]},
        "rtkeep": {"nextpnr": "build/nextpnr-build/rtkeep/nextpnr-himbaechel", "contain_routing": True,
                   "args": ["--router2-region-keep-out"]},
        "partpin": {"nextpnr": "build/nextpnr-build/partpin/nextpnr-himbaechel", "contain_routing": True,
                    "args": ["--router2-region-keep-out"]},
        "partpin2": {"nextpnr": "build/nextpnr-build/partpin2/nextpnr-himbaechel", "contain_routing": True,
                     "args": ["--router2-region-keep-out"]},
        "partpin3": {"nextpnr": "build/nextpnr-build/partpin3/nextpnr-himbaechel", "contain_routing": True,
                     "args": ["--router2-region-keep-out"]},
        "rkcrit90": {"nextpnr": "build/nextpnr-build/rkcrit/nextpnr-himbaechel", "contain_routing": True,
                     "args": ["--router2-region-keep-out", "--router2-region-keep-out-crit=0.9"]},
        "rel01": {"nextpnr": "build/nextpnr-build/rel01/nextpnr-himbaechel", "contain_routing": True,
                  "args": ["--router2-region-keep-out"], "db_root": "build/prjxray-db-prim-xadc"},
        "rel01tr": {"nextpnr": "build/nextpnr-build/rel01tr/nextpnr-himbaechel", "contain_routing": True,
                    "args": ["--router2-region-keep-out"], "db_root": "build/prjxray-db-prim-xadc"},
    },
    "variant": "router",
    "timing_allow_fail": [],
    "chipdb": f"toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-{device.get('fabric')}.bin",
}

ROOT = CONFIG["root"]
FLOW = ROOT / "flow"
sys.path.insert(0, str(FLOW))
import build_openxc7
import region


def run(name, out, cmd, dry, ok=(0,)):
    if out.exists():
        print(f"[skip] {name}: {out.name} exists")
        return
    print(f"[{'dry' if dry else 'run'}] {name}")
    if dry:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    log = out.with_suffix(".log") if out.suffix else Path(str(out) + ".log")
    with open(log, "w") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode not in ok or not out.exists():
        sys.exit(f"{name} failed, see {log}")
    if r.returncode:
        print(f"        exit {r.returncode}, see {log}")


def write(name, out, text, dry):
    if out.exists():
        print(f"[skip] {name}: {out.name} exists")
        return
    print(f"[{'dry' if dry else 'run'}] {name}")
    if not dry:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)


def yosys(script):
    return [build_openxc7.tool("yosys"), "-p", script]


def shared_slicem_sites(spec):
    grid = region.load_grid()
    sites = []
    for name in region.shared_frame_tiles(grid, spec):
        sites += [s for s, ty in grid[name].get("sites", {}).items() if ty == "SLICEM"]
    cols = {}
    for s in sites:
        x, y = map(int, re.fullmatch(r"SLICE_X(\d+)Y(\d+)", s).groups())
        cols.setdefault(x, []).append(y)
    out = []
    for x, ys in sorted(cols.items()):
        ys.sort()
        start = prev = ys[0]
        for y in ys[1:] + [None]:
            if y is not None and y == prev + 1:
                prev = y
                continue
            out.append(f"SLICE_X{x}Y{start}:SLICE_X{x}Y{prev}")
            if y is not None:
                start = prev = y
    return out, len(sites)


def pblock_xdc(base, contain):
    p = CONFIG["pblock"]
    lines = [f"create_pblock {p}",
             f"add_cells_to_pblock [get_pblocks {p}] [get_cells {CONFIG['rm_inst']}]",
             f"resize_pblock [get_pblocks {p}] -add {{{' '.join(region.pblock_ranges(CONFIG['region']))}}}",
             f"set_property EXCLUDE_PLACEMENT true [get_pblocks {p}]"]
    if contain:
        lines.append(f"set_property CONTAIN_ROUTING true [get_pblocks {p}]")
    if CONFIG.get("shared_frame_pblock"):
        ranges, _ = shared_slicem_sites(CONFIG["region"])
        if ranges:
            s = CONFIG["shared_pblock"]
            lines += [f"create_pblock {s}",
                      f"resize_pblock [get_pblocks {s}] -add {{{' '.join(ranges)}}}",
                      f"set_property EXCLUDE_PLACEMENT true [get_pblocks {s}]",
                      f"set_property CONTAIN_ROUTING false [get_pblocks {s}]"]
    return base + "".join(l + "\n" for l in lines)


def multi_pblock_xdc(base, contain):
    lines = []
    for p in CONFIG["partitions"]:
        n = f"pblock_{p['name']}"
        lines += [f"create_pblock {n}",
                  f"add_cells_to_pblock [get_pblocks {n}] [get_cells {p['inst']}]",
                  f"resize_pblock [get_pblocks {n}] -add {{{' '.join(region.pblock_ranges(p['region']))}}}",
                  f"set_property EXCLUDE_PLACEMENT true [get_pblocks {n}]"]
        if contain:
            lines.append(f"set_property CONTAIN_ROUTING true [get_pblocks {n}]")
    return base + "".join(l + "\n" for l in lines)


def check_partitions(parts):
    grid = region.load_grid()
    sets = []
    for p in parts:
        viol = region.pair_violations(grid, p["region"])
        if viol:
            sys.exit(f"{p['name']}: region {p['region']} splits {len(viol)} INT_L/INT_R pair(s), e.g. {viol[0]}; "
                     f"Vivado rejects such pblocks")
        tiles = region.region_tiles(grid, p["region"])
        sets.append((p, set(tiles), set(region.region_bits(tiles))))
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            (pa, ta, fa), (pb, tb, fb) = sets[i], sets[j]
            if ta & tb or fa & fb:
                sys.exit(f"{pa['name']} and {pb['name']} share {len(ta & tb)} tile(s) and {len(fa & fb)} frame(s); "
                         f"partitions that share frames are not supported")
    return {p["name"]: len(f) for p, _, f in sets}


def main_multi(a, dry, var):
    parts = CONFIG["partitions"]
    src = ROOT / "designs" / CONFIG["src"]
    rmsrc = ROOT / "designs" / CONFIG["rm_dir"]
    out = ROOT / a.out / a.variant
    py = sys.executable
    top = CONFIG["top"]
    tag = lambda cfg: "_".join(cfg)
    static = out / "static_synth.json"
    rtl = " ".join(str(src / f) for f in CONFIG["static_rtl"])
    run("synth static", static, yosys(f"read_verilog -sv {rtl}; synth_xilinx -flatten -abc9 -arch xc7 -top {top}; "
                                      f"write_json {static}"), dry)
    nframes = check_partitions(parts)
    write("region.txt", out / "region.txt", "".join(f"{p['name']} {p['inst']} {p['region']}\n" for p in parts), dry)
    synth = {}
    for p in parts:
        d = out / p["name"]
        shell_src = d / "rm_shell_gen.v"
        run(f"gen shell {p['name']}", shell_src, [py, str(FLOW / "gen_shell2.py"), str(rmsrc / CONFIG["shell_spec"]),
                                                   str(shell_src), "--region", p["region"], "--no-keepout"], dry)
        shell = d / "rm_shell_native.v"
        if shell_src.exists():
            kept = [l for l in shell_src.read_text().splitlines() if not re.search(r"\)\s*blk\d+\s*\(|\)\s*kout\d+\s*\(", l)]
            write(f"shell without blockers {p['name']}", shell, "\n".join(kept) + "\n", dry)
        ren = "" if p["module"] == "rm_slot" else f"rename rm_slot {p['module']}; "
        for rm in p["rms"]:
            rj = d / f"rm_{rm}_synth.json"
            run(f"synth {p['name']} rm {rm}", rj,
                yosys(f"read_verilog -sv {shell} {rmsrc / CONFIG['rms'][rm]}; synth_xilinx -flatten -abc9 -arch xc7 "
                      f"-noiopad -noclkbuf -top rm_slot; rename -enumerate -pattern rmx_% rm_slot; {ren}write_json {rj}"), dry)
            synth[(p["name"], rm)] = rj
    cfg0 = tuple(p["rms"][0] for p in parts)
    configs = [tuple(c) for c in CONFIG["configs"]]
    module_cfgs = []
    for k, p in enumerate(parts):
        for rm in p["rms"][1:]:
            module_cfgs.append((k, rm, cfg0[:k] + (rm,) + cfg0[k + 1:]))
    linked = {}
    for cfg in dict.fromkeys([cfg0] + [c for _, _, c in module_cfgs] + configs):
        lj = out / f"cfg_{tag(cfg)}_linked.json"
        reads = "".join(f"read_json {synth[(p['name'], rm)]}; delete =A:blackbox; " for p, rm in zip(parts, cfg))
        run(f"link {tag(cfg)}", lj, yosys(f"read_json {static}; delete =A:blackbox; {reads}"
                                          f"read_verilog -lib +/xilinx/cells_sim.v +/xilinx/cells_xtra.v; hierarchy -top {top}; "
                                          f"flatten; select {top}; write_json -selected {lj}"), dry)
        linked[cfg] = lj
    xdc_text = next(src.glob("*.xdc")).read_text()
    pxdc = out / "pblock.xdc"
    write("pblock xdc", pxdc, multi_pblock_xdc(xdc_text, var["contain_routing"]), dry)
    npnr = ROOT / var["nextpnr"]
    chipdb = ROOT / CONFIG["chipdb"]

    def pnr(cfg, name, xdcf, opts):
        d = out / name
        cmd = [py, str(FLOW / "build_openxc7.py"), CONFIG["src"], "--top", top, "--json", str(linked[cfg]),
               "--xdc", str(xdcf), "--nextpnr", str(npnr), "--chipdb", str(chipdb), "--out", str(d), "--run"]
        cmd += ["--db-root", str(ROOT / var["db_root"])] if var.get("db_root") else []
        cmd += [x for o in opts for x in ("--opt", o)] + [f"--nextpnr-arg={x}" for x in var["args"]]
        run(f"pnr {name}", d / f"{top}.bit", cmd, dry)
        return d

    def compose(name, sources, no_cells=()):
        prefix = out / name
        cmd = [py, str(FLOW / "replay_compose.py"), str(prefix)] + [x for p in parts for x in ("--region", p["region"])]
        cmd += [x for js, area, flt in sources for x in ("--source", str(js), area, flt)]
        cmd += [x for p in parts for x in ("--rp-prefix", p["inst"] + ".")] + [x for k in keep for x in ("--keep", k)]
        cmd += [x for area in no_cells for x in ("--no-cells", area)]
        run(f"compose {name}", Path(str(prefix) + ".prerouted"), cmd, dry)
        xf = out / f"{name}.xdc"
        loc = Path(str(prefix) + ".loc.xdc")
        if not dry:
            write(f"{name} xdc", xf, multi_pblock_xdc(xdc_text + (loc.read_text() if loc.exists() else ""),
                                                      var["contain_routing"]), dry)
        return [f"preplaced={prefix}.preplaced", f"prerouted={prefix}.prerouted"], xf

    keep = [rf"{p['inst']}\.{port}" for p in parts for port in CONFIG["rm_ports"]]
    da = pnr(cfg0, f"{tag(cfg0)}_a", pxdc, [])
    ra = da / f"{top}_routed.json"
    ref = out / "static"
    run("dump static", Path(str(ref) + ".prerouted"),
        [py, str(FLOW / "replay_dump.py"), str(ra), str(ref)] + [x for p in parts for x in ("--exclude", p["inst"] + ".")]
        + [x for k in keep for x in ("--keep", k)], dry)
    module_src = {(k, cfg0[k]): ra for k in range(len(parts))}
    builds = {}
    for k, rm, cfg in module_cfgs:
        p = parts[k]
        sources = [(ra, "outside", "all")] + [(ra, q["region"], "all") for j, q in enumerate(parts) if j != k]
        sources.append((ra, p["region"], "static"))
        opts, xf = compose(f"lock_{p['name']}", sources, [p["region"]])
        d = pnr(cfg, f"{p['name']}_{rm}_m", xf, opts)
        module_src[(k, rm)] = d / f"{top}_routed.json"
        builds[d.name] = (cfg, d)
    for cfg in configs:
        sources = [(ra, "outside", "all")] + [(module_src[(k, rm)], parts[k]["region"], "all") for k, rm in enumerate(cfg)]
        opts, xf = compose(f"asm_{tag(cfg)}", sources)
        d = pnr(cfg, f"{tag(cfg)}_n", xf, opts)
        builds[d.name] = (cfg, d)
    checks = out / "checks"
    for name, (cfg, d) in [(da.name, (cfg0, da))] + list(builds.items()):
        for p in parts:
            pj = checks / f"pips_{name}_{p['name']}.json"
            run(f"region pips {name} {p['name']}", pj,
                [py, str(FLOW / "region_pips.py"), str(d / f"{top}_routed.json"), "--region", p["region"],
                 "--rm-prefix", p["inst"] + ".", "--json", str(pj)], dry)
    asm = [n for n in builds if n.endswith("_n")]
    for i in range(len(asm)):
        for j in range(i + 1, len(asm)):
            (ca, dA), (cb, dB) = builds[asm[i]], builds[asm[j]]
            diff = [k for k in range(len(parts)) if ca[k] != cb[k]]
            if len(diff) != 1:
                continue
            p = parts[diff[0]]
            pj = checks / f"pr_check_{asm[i]}_{asm[j]}.json"
            run(f"pr_check {asm[i]} vs {asm[j]} ({p['name']})", pj,
                [py, str(FLOW / "pr_check.py"), str(dA / f"{top}.bit"), str(dB / f"{top}.bit"), "--region", p["region"],
                 "--json", str(pj)], dry, ok=(0, 1))
    mj = checks / "pr_check_multi.json"
    cmd = [py, str(FLOW / "pr_check_multi.py"), "--json", str(mj)] + [x for p in parts for x in ("--rp", p["name"], p["region"])]
    cmd += [x for name, (cfg, d) in [(da.name, (cfg0, da))] + list(builds.items())
            for x in ("--cfg", name, ",".join(cfg), str(d / f"{top}.bit"))]
    run("pr_check_multi", mj, cmd, dry, ok=(0, 1))
    rj = checks / "routethru.json"
    cmd = [py, str(FLOW / "routethru_scan.py"), "--json", str(rj)] + [x for p in parts for x in ("--rp", p["name"], p["region"])]
    cmd += [str(d / f"{top}_routed.json") for _, d in [(cfg0, da)] + list(builds.values())]
    run("routethru scan", rj, cmd, dry, ok=(0, 1))
    print("partitions: " + ", ".join(f"{p['name']} {p['inst']} {p['region']} ({nframes[p['name']]} frames)" for p in parts))
    print(f"builds under {out}")


def main_auto(a, dry, var):
    src = ROOT / "designs" / CONFIG["src"]
    rmsrc = ROOT / "designs" / CONFIG["rm_dir"]
    spec = rmsrc / CONFIG["shell_spec"]
    out = ROOT / a.out / a.variant
    py = sys.executable
    top = CONFIG["top"]
    inst = CONFIG["rm_inst"]
    static = out / "static_synth.json"
    rtl = " ".join(str(src / f) for f in CONFIG["static_rtl"])
    run("synth static", static, yosys(f"read_verilog -sv {rtl}; synth_xilinx -flatten -abc9 -arch xc7 -top {top}; "
                                      f"write_json {static}"), dry)
    viol = region.pair_violations(region.load_grid(), CONFIG["region"])
    if viol:
        sys.exit(f"region {CONFIG['region']} splits {len(viol)} INT_L/INT_R pair(s), e.g. {viol[0]}; Vivado rejects such pblocks")
    write("region.txt", out / "region.txt", CONFIG["region"] + "\n", dry)
    rm_shell = out / "rm_shell_pp.v"
    run("gen partition-pin shell", rm_shell,
        [py, str(FLOW / "gen_shell2.py"), str(spec), str(rm_shell), "--partpins"]
        + [x for r in CONFIG.get("pp_register", []) for x in ("--register", r)], dry)

    def link(key, rj):
        lj = out / f"cfg_{key}_linked.json"
        run(f"link {key}", lj, yosys(f"read_json {static}; delete =A:blackbox; read_json {rj}; delete =A:blackbox; "
                                     f"read_verilog -lib +/xilinx/cells_sim.v +/xilinx/cells_xtra.v; hierarchy -top {top}; "
                                     f"flatten; select {top}; write_json -selected {lj}"), dry)
        return lj

    linked = {}
    union = CONFIG.get("place_union")
    grey_flags = ["--greybox"] + (["--clock-leaf"] if CONFIG.get("grey_clock_leaf") else [])
    greys = (("grey", grey_flags),) if union else (("grey", grey_flags), ("greybuf", ["--greybox", "--buffers"]))
    for key, flags in greys:
        gv = out / f"rm_{key}.v"
        run(f"gen {key}", gv, [py, str(FLOW / "gen_shell2.py"), str(spec), str(gv)] + flags, dry)
        rj = out / f"rm_{key}_synth.json"
        run(f"read {key}", rj, yosys(f"read_verilog -lib +/xilinx/cells_sim.v; read_verilog -sv -noblackbox {gv}; "
                                     f"hierarchy -top rm_slot; select rm_slot; write_json -selected {rj}"), dry)
        linked[key] = link(key, rj)
    for rm in a.rms:
        rj = out / f"rm_{rm}_synth.json"
        run(f"synth rm {rm}", rj, yosys(f"read_verilog -sv {rm_shell} {rmsrc / CONFIG['rms'][rm]}; synth_xilinx -flatten "
                                        f"-abc9 -arch xc7 -noiopad -noclkbuf -top rm_slot; rename -enumerate -pattern rmx_% "
                                        f"rm_slot; write_json {rj}"), dry)
        linked[rm] = link(rm, rj)
    place_key, place_name = "greybuf", "greybuf_p"
    if union:
        uv = out / "rm_union_core.v"
        run("gen union core", uv, [py, str(FLOW / "gen_shell2.py"), str(spec), str(uv), "--union"] + union, dry)
        rj = out / "rm_union_synth.json"
        reads = "".join(f"read_verilog -sv {rmsrc / CONFIG['rms'][r]}; rename rm_core rm_core_{r}; " for r in union)
        run("synth union", rj, yosys(f"{reads}read_verilog -sv {rm_shell} {uv}; synth_xilinx -flatten -abc9 -arch xc7 "
                                     f"-noiopad -noclkbuf -top rm_slot; rename -enumerate -pattern rmx_% rm_slot; "
                                     f"write_json {rj}"), dry)
        linked["union"] = link("union", rj)
        place_key, place_name = "union", "union_p"
    xdc = next(src.glob("*.xdc"))
    pxdc = out / "pblock.xdc"
    write("pblock xdc", pxdc, pblock_xdc(xdc.read_text(), var["contain_routing"]), dry)
    npnr = ROOT / var["nextpnr"]
    chipdb = ROOT / CONFIG["chipdb"]

    def pnr(key, name, xdcf, opts, extra=()):
        d = out / name
        cmd = [py, str(FLOW / "build_openxc7.py"), CONFIG["src"], "--top", top, "--json", str(linked[key]),
               "--xdc", str(xdcf), "--nextpnr", str(npnr), "--chipdb", str(chipdb), "--out", str(d), "--run"]
        cmd += ["--db-root", str(ROOT / var["db_root"])] if var.get("db_root") else []
        cmd += [x for o in opts for x in ("--opt", o)] + [f"--nextpnr-arg={x}" for x in list(var["args"]) + list(extra)]
        cmd += ["--seed", str(a.seed)] if a.seed is not None else []
        run(f"pnr {name}", d / f"{top}.bit", cmd, dry)
        return d

    def replay_xdc(name, loc):
        xf = out / name
        if not dry:
            write(name, xf, pblock_xdc(xdc.read_text() + (loc.read_text() if loc.exists() else ""),
                                       var["contain_routing"]), dry)
        return xf

    dp = pnr(place_key, place_name, pxdc, [], CONFIG.get("place_args", []))
    asg = out / "static_pp_assign"
    fix_ep = CONFIG.get("fix_endpoints")
    epc = out / "static_pp_assign.endpoints"
    run("assign partition pins", Path(str(asg) + ".partpins"),
        [py, str(FLOW / "partpin_assign.py"), "assign", str(dp / f"{top}_routed.json"), str(static), str(asg),
         "--region", CONFIG["region"], "--spec", str(spec)] + (["--endpoint-cells", str(epc)] if fix_ep else [])
        + (["--module-ends", "--keep-per-net", "5000"] if CONFIG.get("pin_module_ends") else [])
        + (["--w-module", str(CONFIG["pin_w_module"])] if "pin_w_module" in CONFIG else [])
        + (["--exclude-wrap-exits"] if CONFIG.get("pin_exclude_wrap_exits") else []), dry)
    gp = out / "grey_place"
    run("dump greybox placement", Path(str(gp) + ".preplaced"),
        [py, str(FLOW / "replay_dump.py"), str(dp / f"{top}_routed.json"), str(gp), "--exclude", inst + "."], dry)
    if fix_ep:
        gpe = out / "grey_place_endpoints.preplaced"
        if not dry:
            cells = set(epc.read_text().split())
            lines = [l.split("\t", 1) for l in Path(str(gp) + ".preplaced").read_text().splitlines() if "\t" in l]
            slice_of = lambda bel: bel.rsplit(".", 1)[0]
            sites = {slice_of(b) for c, b in lines if c in cells}
            kept = [f"{c}\t{b}" for c, b in lines if slice_of(b) in sites]
            write("endpoint placement", gpe, "".join(l + "\n" for l in kept), dry)
        gopts, gxdc = [f"preplaced={gpe}"], pxdc
    else:
        gopts, gxdc = [f"preplaced={gp}.preplaced"], replay_xdc("grey_s.xdc", Path(str(gp) + ".loc.xdc"))
    ds = pnr("grey", "grey_s", gxdc, gopts + [f"partition-pins={asg}.partpins", "partition-pins-route"])
    ref = out / "static"
    keep = [x for p in CONFIG["rm_ports"] for x in ("--keep", rf"{inst}\.{p}")]
    run("dump static", Path(str(ref) + ".prerouted"),
        [py, str(FLOW / "replay_dump.py"), str(ds / f"{top}_routed.json"), str(ref), "--exclude", inst + "."] + keep, dry)
    pp = out / "static_pp"
    run("export partition pins", Path(str(pp) + ".partpins"),
        [py, str(FLOW / "partpin_assign.py"), "export", str(ds / f"{top}_routed.json"), str(ref) + ".prerouted",
         str(asg) + ".json", str(pp), "--region", CONFIG["region"]], dry)
    rxdc = replay_xdc("replay.xdc", Path(str(ref) + ".loc.xdc"))
    px = out / "pp_proxy"
    run("placement proxies", Path(str(px) + ".v"),
        [py, str(FLOW / "partpin_assign.py"), "proxy", str(pp) + ".json", str(xdc), str(px), "--region", CONFIG["region"],
         "--spec", str(spec)], dry)
    builds = {}
    for rm in a.rms:
        key = f"{rm}_proxy"
        lj = out / f"cfg_{key}.json"
        run(f"link {key}", lj, yosys(f"read_json {out / f'rm_{rm}_synth.json'}; delete =A:blackbox; read_verilog {px}.v; "
                                     f"read_verilog -lib +/xilinx/cells_sim.v +/xilinx/cells_xtra.v; hierarchy -top pp_proxy; "
                                     f"flatten; select pp_proxy; write_json -selected {lj}"), dry)
        linked[key] = lj
        dpx = pnr(key, f"{rm}_p", Path(str(px) + ".xdc"), [])
        mp = out / f"{rm}_place"
        run(f"dump {rm} placement", Path(str(mp) + ".preplaced"),
            [py, str(FLOW / "replay_dump.py"), str(dpx / f"{top}_routed.json"), str(mp), "--exclude", "",
             "--keep", rf"{inst}\..*"], dry)
        both = out / f"{rm}_static_place.preplaced"
        if not dry:
            write(f"{rm} + static placement", both, Path(str(ref) + ".preplaced").read_text()
                  + Path(str(mp) + ".preplaced").read_text(), dry)
        opts = [f"preplaced={both}", f"prerouted={pp}.prerouted", f"partition-pins={pp}.partpins"]
        builds[rm] = pnr(rm, f"{rm}_n", rxdc, opts)
    checks = out / "checks"
    for d in [dp, ds] + list(builds.values()):
        pj = checks / f"pips_{d.name}.json"
        run(f"region pips {d.name}", pj, [py, str(FLOW / "region_pips.py"), str(d / f"{top}_routed.json"), "--region",
                                          CONFIG["region"], "--rm-prefix", inst + ".", "--json", str(pj)], dry)
    names = [ds] + list(builds.values())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ta, tb = names[i].name, names[j].name
            pj = checks / f"pr_check_{ta}_{tb}.json"
            run(f"pr_check {ta} vs {tb}", pj, [py, str(FLOW / "pr_check.py"), str(names[i] / f"{top}.bit"),
                                               str(names[j] / f"{top}.bit"), "--region", CONFIG["region"],
                                               "--json", str(pj)], dry, ok=(0, 1))
    if CONFIG.get("grey_clock_leaf"):
        for d in builds.values():
            pj = checks / f"pr_check_hclk_{ds.name}_{d.name}.json"
            run(f"pr_check --hclk-full-column {ds.name} vs {d.name}", pj,
                [py, str(FLOW / "pr_check.py"), str(ds / f"{top}.bit"), str(d / f"{top}.bit"), "--region",
                 CONFIG["region"], "--hclk-full-column", "--json", str(pj)], dry, ok=(0, 1))
    pj = checks / "partpin_check.json"
    run("partpin_check", pj, [py, str(FLOW / "partpin_check.py"), str(pp) + ".json", str(pp) + ".prerouted"]
        + [str(d / f"{top}_routed.json") for d in builds.values()] + ["--region", CONFIG["region"], "--rm-prefix",
                                                                       inst + ".", "--json", str(pj)], dry, ok=(0, 1))
    print(f"builds under {out}")


def main():
    ap = argparse.ArgumentParser(description="PR build with in-tool region constraints (patched nextpnr: pblock XDC and router2 "
                                             "region containment) instead of blocker LUTs, rm_place, region_route and static_detour")
    ap.add_argument("--design", default=CONFIG["design"], choices=sorted(CONFIG["designs"]))
    ap.add_argument("--variant", choices=sorted(CONFIG["variants"]))
    ap.add_argument("--rms", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--timing-allow-fail", nargs="+", default=CONFIG["timing_allow_fail"],
                    help="RMs whose replay build passes --timing-allow-fail; the build is named <rm>_n_taf")
    ap.add_argument("--no-shared-frame-pblock", action="store_true",
                    help="negative control: do not close the static SLICEMs that share the region's frames")
    ap.add_argument("--seed", type=int, help="nextpnr seed for every build (default: build_openxc7's); use with --out")
    ap.add_argument("--report-paths", type=int, default=0,
                    help="pass --report-paths N to every nextpnr run (needs a nextpnr with "
                         "docs/drafts/nextpnr-timing-report.patch, e.g. --variant rel01tr); 0 = off")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    CONFIG.update(CONFIG["designs"][a.design])
    a.variant = a.variant or CONFIG["variant"]
    if a.report_paths:
        var = CONFIG["variants"][a.variant]
        var["args"] = list(var["args"]) + ["--report-paths", str(a.report_paths)]
    if a.no_shared_frame_pblock:
        CONFIG["shared_frame_pblock"] = False
    a.rms = a.rms or CONFIG["default_rms"]
    a.out = a.out or CONFIG["out"]
    if "partitions" in CONFIG:
        main_multi(a, CONFIG["dry_run"] and not a.run, CONFIG["variants"][a.variant])
        return
    bad =[r for r in a.rms + a.timing_allow_fail if r not in CONFIG["rms"]]
    if bad:
        sys.exit(f"unknown RM(s) {bad} for {a.design}; choose from {sorted(CONFIG['rms'])}")
    dry = CONFIG["dry_run"] and not a.run
    var = CONFIG["variants"][a.variant]
    if CONFIG.get("partpins") == "auto":
        main_auto(a, dry, var)
        return
    src = ROOT / "designs" / CONFIG["src"]
    rmsrc = ROOT / "designs" / CONFIG["rm_dir"]
    out = ROOT / a.out / a.variant
    py = sys.executable
    top = CONFIG["top"]
    static = out / "static_synth.json"
    rtl = " ".join(str(src / f) for f in CONFIG["static_rtl"])
    run("synth static", static, yosys(f"read_verilog -sv {rtl}; synth_xilinx -flatten -abc9 -arch xc7 -top {top}; "
                                      f"write_json {static}"), dry)
    shell = out / "rm_shell_native.v"
    shell_src = rmsrc / CONFIG["rm_shell"]
    if "shell_spec" in CONFIG:
        shell_src = out / "rm_shell_gen.v"
        run("gen shell", shell_src, [py, str(FLOW / "gen_shell2.py"), str(rmsrc / CONFIG["shell_spec"]), str(shell_src),
                                     "--region", CONFIG["region"], "--no-keepout"], dry)
    if shell_src.exists():
        text = shell_src.read_text()
        kept = [l for l in text.splitlines() if not re.search(r"\)\s*blk\d+\s*\(|\)\s*kout\d+\s*\(", l)]
        write("shell without blockers", shell, "\n".join(kept) + "\n", dry)
    pp_mode = CONFIG.get("partpins", False)
    rm_shell = shell
    if pp_mode:
        rm_shell = out / "rm_shell_pp.v"
        run("gen partition-pin shell", rm_shell,
            [py, str(FLOW / "gen_shell2.py"), str(rmsrc / CONFIG["shell_spec"]), str(rm_shell), "--partpins"]
            + [x for r in CONFIG.get("pp_register", []) for x in ("--register", r)], dry)
    viol = region.pair_violations(region.load_grid(), CONFIG["region"])
    if viol:
        sys.exit(f"region {CONFIG['region']} splits {len(viol)} INT_L/INT_R pair(s), e.g. {viol[0]}; Vivado rejects such pblocks")
    write("region.txt", out / "region.txt", CONFIG["region"] + "\n", dry)
    linked = {}
    synth_list = [(rm, rm, rm_shell) for rm in a.rms]
    if pp_mode:
        synth_list.insert(0, (a.rms[0], f"{a.rms[0]}_ref", shell))
    for rm, key, sh in synth_list:
        rj = out / f"rm_{key}_synth.json"
        run(f"synth rm {key}", rj, yosys(f"read_verilog -sv {sh} {rmsrc / CONFIG['rms'][rm]}; synth_xilinx -flatten -abc9 "
                                         f"-arch xc7 -noiopad -noclkbuf -top rm_slot; rename -enumerate -pattern rmx_% rm_slot; "
                                         f"write_json {rj}"), dry)
        lj = out / f"cfg_{key}_linked.json"
        run(f"link {key}", lj, yosys(f"read_json {static}; delete =A:blackbox; read_json {rj}; delete =A:blackbox; "
                                     f"read_verilog -lib +/xilinx/cells_sim.v +/xilinx/cells_xtra.v; hierarchy -top {top}; "
                                     f"flatten; select {top}; write_json -selected {lj}"), dry)
        linked[key] = lj
    xdc = next(src.glob("*.xdc"))
    pxdc = out / "pblock.xdc"
    write("pblock xdc", pxdc, pblock_xdc(xdc.read_text(), var["contain_routing"]), dry)
    npnr = ROOT / var["nextpnr"]
    chipdb = ROOT / CONFIG["chipdb"]

    def pnr(rm, name, xdcf, opts, extra=()):
        d = out / name
        cmd = [py, str(FLOW / "build_openxc7.py"), CONFIG["src"], "--top", top, "--json", str(linked[rm]),
               "--xdc", str(xdcf), "--nextpnr", str(npnr), "--chipdb", str(chipdb), "--out", str(d), "--run"]
        cmd += ["--db-root", str(ROOT / var["db_root"])] if var.get("db_root") else []
        cmd += [x for o in opts for x in ("--opt", o)] + [f"--nextpnr-arg={x}" for x in list(var["args"]) + list(extra)]
        cmd += ["--seed", str(a.seed)] if a.seed is not None else []
        run(f"pnr {name}", d / f"{top}.bit", cmd, dry)
        return d

    first = a.rms[0]
    da = pnr(f"{first}_ref" if pp_mode else first, f"{first}_a", pxdc, [])
    ref = out / "static"
    keep = [x for p in CONFIG["rm_ports"] for x in ("--keep", rf"{CONFIG['rm_inst']}\.{p}")]
    run("dump static", Path(str(ref) + ".prerouted"),
        [py, str(FLOW / "replay_dump.py"), str(da / f"{top}_routed.json"), str(ref), "--exclude", CONFIG["rm_inst"] + "."] + keep,
        dry)
    rxdc = out / "replay.xdc"
    loc = Path(str(ref) + ".loc.xdc")
    if not dry:
        write("replay xdc", rxdc, pblock_xdc(xdc.read_text() + (loc.read_text() if loc.exists() else ""),
                                             var["contain_routing"]), dry)
    replay_opts = [f"preplaced={ref}.preplaced", f"prerouted={ref}.prerouted"]
    if pp_mode:
        pp = out / "static_pp"
        run("partition pins", Path(str(pp) + ".partpins"),
            [py, str(FLOW / "partpins.py"), str(da / f"{top}_routed.json"), str(ref) + ".prerouted", str(static), str(pp),
             "--region", CONFIG["region"], "--rm-prefix", CONFIG["rm_inst"] + ".", "--rm-inst", CONFIG["rm_inst"]], dry)
        replay_opts = [f"preplaced={ref}.preplaced", f"prerouted={pp}.prerouted", f"partition-pins={pp}.partpins"]
    builds = {}
    for rm in a.rms:
        taf = rm in a.timing_allow_fail
        builds[rm] = pnr(rm, f"{rm}_n_taf" if taf else f"{rm}_n", rxdc, replay_opts,
                         ["--timing-allow-fail"] if taf else [])
    checks = out / "checks"
    for rm, d in [(first, da)] + list(builds.items()):
        tag = d.name
        run(f"region pips {tag}", checks / f"pips_{tag}.json",
            [py, str(FLOW / "region_pips.py"), str(d / f"{top}_routed.json"), "--region", CONFIG["region"],
             "--rm-prefix", CONFIG["rm_inst"] + ".", "--json", str(checks / f"pips_{tag}.json")], dry)
    names = list(builds)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ra, rb = names[i], names[j]
            ta, tb = builds[ra].name, builds[rb].name
            run(f"pr_check {ta} vs {tb}", checks / f"pr_check_{ta}_{tb}.json",
                [py, str(FLOW / "pr_check.py"), str(builds[ra] / f"{top}.bit"), str(builds[rb] / f"{top}.bit"),
                 "--region", CONFIG["region"], "--json", str(checks / f"pr_check_{ta}_{tb}.json")], dry, ok=(0, 1))
    if CONFIG.get("shared_frame_pblock"):
        _, n = shared_slicem_sites(CONFIG["region"])
        print(f"shared-frame pblock {CONFIG['shared_pblock']}: {n} SLICEM site(s) closed to static cells")
    print(f"builds under {out}")


if __name__ == "__main__":
    main()
