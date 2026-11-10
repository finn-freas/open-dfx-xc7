import argparse
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import BOARDS, FLOW, ROOT, VERSION
from . import project as P
from . import defaults, reports, runner, templates, timing, vhdl
from . import cli_ip
from . import hls as hlsmod
from . import drc as drcmod
from . import power as powermod
from .stage import stage

CONFIG = {
    "dry_run": True,
    "py": sys.executable,
    "openfpgaloader": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "openFPGALoader",
    "openfpgaloader_partial": ROOT / "build" / "ofl-build" / "partial" / "openFPGALoader",
    "openfpgaloader_release": ROOT / "toolchain" / "openxc7" / "bin" / "openFPGALoader",
    "byteman": ROOT / "toolchain" / "byteman-build" / "byteman",
    "nextpnr_stock": ROOT / "toolchain" / "openxc7" / "bin" / "nextpnr-xilinx",
    "icap_loader": ROOT / "host" / "icap_load.ps1",
    "powershell": "powershell.exe",
    "decoupler_prove": FLOW / "decoupler_prove.sh",
    "formal_timeout_s": 600,
    "formal_mem_kb": 3000000,
    "greybox_builds": ("grey_s", "greybuf_p"),
    "region_tiles_re": r"^(\d+) tiles, (\d+) frames",
}


def load(a):
    try:
        return P.Project(P.find(a.project))
    except P.ProjectError as e:
        sys.exit(f"ofx: {e}")


def is_dry(a):
    return CONFIG["dry_run"] and not getattr(a, "run", False)


def env_for(proj):
    e = proj.env()
    f = proj.freq_mhz()
    if f is not None:
        e["OFX_FREQ_MHZ"] = str(f)
    return e


def npwait_args():
    lim = runner.nextpnr_limit()
    if lim is None:
        return [], {}
    return ["--nextpnr", str(runner.CONFIG["npwait"])], {"OFX_NEXTPNR_BIN": str(CONFIG["nextpnr_stock"])}


def timing_nextpnr_args(proj):
    npa, npe = npwait_args()
    binary = proj.timing["nextpnr"]
    if not binary:
        return npa, npe
    if npa:
        npe = {"OFX_NEXTPNR_BIN": str(binary)}
    else:
        npa = ["--nextpnr", str(binary)]
    npa += ["--chipdb", proj.device["chipdb"]]
    if proj.timing["report_paths"]:
        npa += ["--nextpnr-arg=--report-paths", f"--nextpnr-arg={proj.timing['report_paths']}"]
    return npa, npe


def staged(proj, dry):
    try:
        return stage(proj, False, tool_dry=dry)
    except P.ProjectError as e:
        sys.exit(f"ofx: {e}")


def region_drc(proj, region, dry=False):
    cmd = [CONFIG["py"], runner.flow("region.py"), region, "--drc"]
    print(f"[{'dry' if dry else 'run'}] {runner.show(cmd)}", flush=True)
    if dry:
        return None
    r = subprocess.run([str(c) for c in cmd], env=dict(os.environ, **env_for(proj)), cwd=ROOT, capture_output=True,
                       text=True)
    sys.stdout.write(r.stdout + r.stderr)
    m = re.search(CONFIG["region_tiles_re"], r.stdout, re.M)
    if r.returncode == 0 and m and int(m.group(2)) == 0:
        print(f"ofx: region {region} contains no sites of fabric {proj.device['fabric']} (0 frames)")
        return 1
    return r.returncode


def impl_dir(proj):
    return proj.build / "impl"


def dfx_root(proj):
    return proj.build / "dfx"


def dfx_out(proj):
    return dfx_root(proj) / proj.dfx["variant"]


def cmd_new(a):
    target = a.target
    board = None
    if (BOARDS / f"{target}.toml").exists():
        board = P.load_board(target)
        part = board["board"]["part"]
        tline = f'board = "{target}"'
    else:
        part = target
        tline = f'part = "{target}"'
    try:
        dev = P.device.resolve(part)
    except ValueError as e:
        sys.exit(f"ofx new: {e} (not a board preset either: {sorted(x.stem for x in BOARDS.glob('*.toml'))})")
    d = Path(a.dir or a.name).resolve()
    if (d / P.CONFIG["file"]).exists() and not a.force:
        sys.exit(f"ofx new: {d / P.CONFIG['file']} exists (use --force)")
    name = a.name or d.name
    top = re.sub(r"\W", "_", name)
    period = board["clock"]["period_ns"] if board else 10.0
    files = {"src/" + top + ".v": (templates.DFX_TOP if a.dfx else templates.BLINKY).format(top=top)}
    proj = templates.PROJECT.format(name=name, top=top, target=tline, period=period)
    if a.dfx:
        region = (board or {}).get("dfx", {}).get("example_region")
        if not region:
            sys.exit(f"ofx new --dfx: no example region for {target}; pick a CLB range and check it with "
                     f"`python3 flow/region.py <range> --drc` (OFX_FABRIC={dev['fabric']})")
        proj += templates.DFX.format(region=region, partpins=a.partpins)
        files["rm/ports.json"] = templates.PORTS_JSON
        files["rm/rm_core_xor.v"] = templates.RM_XOR
        files["rm/rm_core_andn.v"] = templates.RM_ANDN
    files[P.CONFIG["file"]] = proj
    files["constraints/" + top + ".xdc"] = xdc_from_board(board, top)
    for rel, text in files.items():
        f = d / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
        print(f"wrote {f}")
    if board and not board["board"].get("pins_verified"):
        print("WARNING: this board preset's pins are not verified against an official board file")
    if not board:
        print(f"WARNING: no board preset: constraints/{top}.xdc has no PACKAGE_PIN lines; add your board's pins")
    print(f"device: part {dev['part']}, family {dev['family']}, fabric {dev['fabric']}, chipdb {dev['chipdb']}")


def xdc_from_board(board, top):
    if not board:
        return "create_clock -name sys_clk -period 10.000 [get_ports clk]\n"
    c = board["clock"]
    lines = [f"set_property -dict {{ PACKAGE_PIN {c['pin']} IOSTANDARD {c.get('iostandard', 'LVCMOS33')} }} "
             f"[get_ports {c['port']}]",
             f"create_clock -name sys_clk -period {c['period_ns']:.3f} [get_ports {c['port']}]"]
    led_std = board["board"].get("led_iostandard", board["board"].get("iostandard", "LVCMOS33"))
    for port, pin in board.get("leds", {}).items():
        lines.append(f"set_property -dict {{ PACKAGE_PIN {pin} IOSTANDARD {led_std} }} [get_ports {{{port}}}]")
    return "\n".join(lines) + "\n"


def cmd_boards(a):
    for name, b in P.boards().items():
        bb = b["board"]
        print(f"{name:16s} {bb['part']:20s} pins {'verified' if bb.get('pins_verified') else 'UNVERIFIED'}  "
              f"source: {bb.get('pin_source', '-')}")


def cmd_device(a):
    try:
        print(json.dumps(P.device.resolve(a.part), indent=1))
    except ValueError as e:
        sys.exit(f"ofx: {e}")


def cmd_build(a):
    proj = load(a)
    dry = is_dry(a)
    st = staged(proj, dry)
    out = impl_dir(proj)
    extra = {"part": proj.part, "seed": proj.seed, "freq": proj.freq_mhz(), "top": proj.top}
    if proj.seeds > 1:
        extra["seeds"] = f"auto:{proj.seeds}" if proj.seeds_auto else proj.seeds
    if st["inputs"] != st["sources"]:
        extra["vhdl"] = {"std": proj.vhdl_std, "units": proj.vhdl_units}
        if proj.vhdl_generics:
            extra["vhdl"]["generics"] = proj.vhdl_generics
    if proj.timing["nextpnr"]:
        extra["timing"] = {"nextpnr": str(proj.timing["nextpnr"]), "report_paths": proj.timing["report_paths"]}
    try:
        dp = defaults.plan(proj, st["xdc"])
    except defaults.DefaultsError as e:
        sys.exit(f"ofx: {e}")
    if dp["release"]:
        extra["defaults"] = dp
    ref = None
    if getattr(a, "incremental", None):
        ref = incremental_ref(proj, Path(a.incremental), dry)
        extra["incremental"] = runner.digest([ref / f"{proj.top}_routed.json"], {}) if not dry else str(ref)
    key = runner.digest(st["inputs"] + [st["xdc"]], extra)
    runner.fresh(out, key, dry)
    npa, npe = timing_nextpnr_args(proj)
    cmd = [CONFIG["py"], runner.flow("build_openxc7.py"), st["dir"], "--top", proj.top, "--xdc", st["xdc"],
           "--part", proj.part, "--seed", str(proj.seed), "--out", out] + npa
    if proj.seeds > 1:
        cmd += ["--seeds", str(proj.seeds)] + (["--seeds-auto"] if proj.seeds_auto else [])
    if proj.device.get("db_extra"):
        cmd += ["--chipdb", proj.device["chipdb"], "--db-root", proj.device["db_root"]]
    cmd += defaults_args(dp)
    rtl = ["--rtl"] + [str(s) for s in st["sources"]]
    for n in dp["notes"]:
        print(f"ofx: {n}")
    if dp["release"]:
        print(f"ofx {dp['release']} defaults: {json.dumps(dp['options'], sort_keys=True)}")
        net = None
        if defaults.needs_netlist(dp):
            runner.run(cmd + ["--stop-after", "yosys"] + ([] if dry else ["--run"]) + rtl, env={**env_for(proj), **npe})
            net = None if dry else defaults.netlist_info(out / f"{proj.top}.json", proj.top)
        dec = defaults.decide(dp, net)
        for w in dec["why"]:
            print(f"ofx: {w}")
        cmd += [f"--nextpnr-arg={x}" for x in dec["nextpnr_args"]]
        if dec["chipdb"]:
            cmd += ["--chipdb", dec["chipdb"]]
        if not dry:
            (out / "ofx_defaults.json").write_text(json.dumps({**dp, "decision": dec}, indent=1) + "\n")
    if ref is not None:
        cmd = incremental_cmd(proj, cmd, rtl, ref, out, st["xdc"], dry, {**env_for(proj), **npe},
                              getattr(a, "incremental_routes", False))
    if not dry:
        cmd.append("--run")
    runner.run(cmd + ([] if ref is not None else rtl), env={**env_for(proj), **npe})
    if not dry:
        reports.print_report([out])


def cmd_hls(a):
    proj = load(a)
    dry = is_dry(a)
    out = proj.build / hlsmod.CONFIG["out_dir"]
    try:
        if not hlsmod.kernels(proj):
            sys.exit("ofx hls: the project has no [[hls]] kernel")
        files, _ = hlsmod.generate(proj, out, dry)
        res = hlsmod.simulate(proj, out, dry) if a.sim else {}
    except hlsmod.HlsError as e:
        sys.exit(f"ofx: {e}")
    for f in files:
        print(f"hls rtl: {f}")
    bad = 0
    for top, r in res.items():
        ok = r["rc"] == 0
        bad += not ok
        print(f"hls sim {top}: {'PASS' if ok else 'FAIL'}" + (f", {r['cycles']} cycles" if r["cycles"] else "")
              + f" ({r['log']})")
    if bad:
        sys.exit(1)


def incremental_ref(proj, ref, dry):
    """The reference build of `ofx build --incremental`: a build directory with <top>.json and <top>_routed.json.
    The project's own impl directory is copied aside first, since this build replaces it."""
    ref = ref.resolve()
    need = [ref / f"{proj.top}.json", ref / f"{proj.top}_routed.json"]
    if not all(f.exists() for f in need):
        if dry:
            return ref
        sys.exit(f"ofx build --incremental: {ref} has no {need[0].name} and {need[1].name} (a finished ofx build)")
    if ref == impl_dir(proj).resolve():
        keep = proj.build / "incremental_ref"
        print(f"[{'dry' if dry else 'run'}] copy the reference {ref} to {keep}", flush=True)
        if not dry:
            keep.mkdir(parents=True, exist_ok=True)
            for f in need:
                shutil.copy(f, keep / f.name)
        ref = keep
    return ref


def incremental_cmd(proj, cmd, rtl, ref, out, xdc, dry, env, routes=False):
    """Synthesize into <impl>/synth, match it to the reference (flow/incremental.py), and return the build
    command that places and routes the matched netlist with the reference's placement replayed (whole tiles),
    and with routes=True its routing too (faster, but worse timing on rv_soc: docs/incremental.md)"""
    syn, inc = out / "synth", out / "incremental"
    i = cmd.index("--out")
    scmd = cmd[:i + 1] + [syn] + cmd[i + 2:]
    runner.run(scmd + ["--stop-after", "yosys"] + ([] if dry else ["--run"]) + rtl, env=env)
    runner.run([CONFIG["py"], runner.flow("incremental.py"), ref, syn / f"{proj.top}.json", inc, "--top", proj.top,
                "--xdc", xdc, "--ripple", "0"] + ([] if routes else ["--whole-tiles"]), dry=dry)
    j = cmd.index("--xdc")
    cmd = cmd[:j + 1] + [inc / "inc.xdc"] + cmd[j + 2:]
    cmd = cmd + ["--json", inc / f"{proj.top}.json", "--opt", f"preplaced={inc / 'inc.preplaced'}"]
    return cmd + (["--opt", f"prerouted={inc / 'inc.prerouted'}"] if routes else [])


def defaults_args(dp):
    args = []
    if dp["synth"]:
        args += ["--synth", dp["synth"]]
    args += [f"--nextpnr-arg={x}" for x in dp["nextpnr_args"]]
    return args


def board_ofl(proj, a):
    if a.board:
        return a.board
    if proj.board and proj.board["board"].get("openfpgaloader_board"):
        return proj.board["board"]["openfpgaloader_board"]
    sys.exit("ofx program: no openFPGALoader board name; give --board or a [project] board with openfpgaloader_board")


def cmd_program(a):
    proj = load(a)
    dry = is_dry(a)
    bit = Path(a.bit) if a.bit else impl_dir(proj) / f"{proj.top}.bit"
    if not bit.exists() and not dry:
        sys.exit(f"ofx program: {bit} does not exist (run `ofx build --run`)")
    cmd = [CONFIG["openfpgaloader"], "-b", board_ofl(proj, a)] + (["-f"] if a.flash else []) + [bit]
    runner.run(cmd, dry=dry)
    if dry:
        print("DRY RUN: nothing sent to a board. Add --run to program it.")


def cmd_boot(a):
    proj = load(a)
    run = [] if is_dry(a) else ["--run"]
    runner.run([CONFIG["py"], runner.flow("zynq_boot.py"), proj.file] + (["--qemu"] if a.qemu else []) + run)
    if a.sim:
        runner.run([CONFIG["py"], runner.flow("zynq_pl_sim.py"), proj.file] + run)


def cmd_timing(a):
    if a.build:
        dirs = reports.build_dirs(a.build)
    else:
        proj = load(a)
        dirs = reports.build_dirs(dfx_out(proj) if a.dfx else impl_dir(proj))
    if not dirs:
        sys.exit("ofx timing: nothing built yet")
    bad = timing.print_timing(dirs, a)
    sys.exit(1 if bad else 0)


def checked_target(a, what):
    if a.build:
        return Path(a.build), [str(x) for x in (a.xdc or [])], a.part
    proj = load(a)
    b = dfx_out(proj) if getattr(a, "dfx", False) else impl_dir(proj)
    if not b.exists():
        sys.exit(f"ofx {what}: nothing built yet in {b}")
    return b, [str(x) for x in (a.xdc or proj.constraints)], a.part or proj.part


def cmd_drc(a):
    b, xdc, part = checked_target(a, "drc")
    rep = drcmod.main(b, xdc, part, a.json)
    errs = drcmod.errors(rep)
    sys.exit(1 if errs and not a.no_fail else 0)


def cmd_power(a):
    b, xdc, _ = checked_target(a, "power")
    powermod.main(b, xdc, a.json, a.model)


def cmd_report(a):
    proj = load(a)
    dirs = reports.build_dirs(dfx_out(proj) if a.dfx else impl_dir(proj))
    if not dirs:
        sys.exit("ofx report: nothing built yet")
    print(f"project {proj.name}: part {proj.part} (family {proj.device['family']}, fabric {proj.device['fabric']})")
    reports.print_report(dirs, [q["inst"] for q in proj.dfx["partitions"]] if a.dfx and proj.dfx else ())


def design_dict(proj, st):
    dfx = proj.dfx
    parts = dfx["partitions"]
    p = parts[0]
    d = {"src": str(st["dir"]), "top": proj.top, "rm_dir": str(proj.dir), "static_rtl": [str(s) for s in st["sources"]],
         "rm_inst": p["inst"], "rm_ports": P.port_regexes(p["spec"]), "region": p["region"],
         "out": str(dfx_root(proj)), "variant": dfx["variant"], "shared_frame_pblock": True,
         "rms": {k: str(v) for q in parts for k, v in st["rms"][q["name"]].items()}, "default_rms": p["default_rms"]}
    if len(parts) > 1:
        specs = {json.dumps(q["spec"], sort_keys=True) for q in parts}
        if len(specs) != 1:
            sys.exit("ofx: the multi-partition flow needs the same port spec for every partition")
        names = [k for q in parts for k in q["rms"]]
        if len(names) != len(set(names)):
            sys.exit("ofx: RM names must be unique across partitions")
        d["shell_spec"] = str(st["specs"][p["name"]])
        d["partitions"] = [{"name": q["name"], "inst": q["inst"], "module": q["module"], "region": q["region"],
                            "rms": list(q["rms"])} for q in parts]
        d["configs"] = dfx["configs"] or [list(c) for c in itertools.product(*[list(q["rms"]) for q in parts])]
        d.pop("shared_frame_pblock")
        return d
    if dfx["partpins"] == "auto":
        d.update({"shell_spec": str(st["specs"][p["name"]]), "partpins": "auto", "pp_register": p["register"]})
        ppx = [str(Path(c).resolve()) for c in proj.constraints if "HD.PARTPIN_" in Path(c).read_text()]
        if len(ppx) > 1:
            sys.exit(f"ofx: HD.PARTPIN constraints in more than one XDC ({ppx}); keep them in one file")
        if ppx:
            d["partpin_xdc"] = ppx[0]
        if dfx.get("timed"):
            d.update({"place_union": list(p["default_rms"]), "grey_clock_leaf": True, "fix_endpoints": True,
                      "pin_module_ends": True, "pin_w_module": 0.5, "pin_exclude_wrap_exits": True,
                      "static_try_unfixed": True, "module_seeds": 2})
    elif p["shell"]:
        d["rm_shell"] = str(p["shell"])
    else:
        d["shell_spec"] = str(st["specs"][p["name"]])
    return d


def dfx_inputs(proj, st):
    files = st["inputs"] + [st["xdc"]] + [v for q in proj.dfx["partitions"] for v in q["rms"].values()]
    files += [st["specs"][q["name"]] for q in proj.dfx["partitions"]] + [q["shell"] for q in proj.dfx["partitions"] if q["shell"]]
    return files


RM_OUTPUTS = ("{rm}_n", "{rm}_n_taf", "{rm}_p", "rm_{rm}_synth.*", "cfg_{rm}_linked.*", "cfg_{rm}_proxy.*",
              "{rm}_place.*", "{rm}_static_place.*", "partials/rm_{rm}_from_*", "partials/rm_*_from_{rm}.*",
              "checks/*_{rm}_n*", "verify/*{rm}*")


def static_rms(proj, a, dd):
    """RMs whose content the static implementation depends on: the first (anchor) RM in anchors mode, none with
    automatic partition pins (static is placed and routed against a greybox)."""
    if dd.get("partpins") == "auto" and not dd.get("place_union"):
        return []
    if dd.get("place_union"):
        return list(dd["place_union"])
    return [(a.rms or proj.dfx["partitions"][0]["default_rms"])[0]]


def multi_outputs(out, rms, cfgs):
    """Outputs of the multi-partition flow that depend on one of the RMs or configurations: every file or directory
    under the build (top level, partition dirs, checks, partials, verify) whose name, split at '_' and '.', contains
    an RM name or a configuration's RM sequence (build_pr_native main_multi and ofx partial names are made of them),
    and the aggregate pr_check_multi.json."""
    if not out.exists():
        return []
    dirs = [out] + [p for p in out.iterdir() if p.is_dir() and not re.search(r"_[amn]$", p.name)]
    seqs = [[r] for r in rms] + [c.split("_") for c in cfgs]
    gone = []
    for d in dirs:
        for x in sorted(d.iterdir()):
            toks = re.split(r"[_.]", x.name)
            if any(toks[i:i + len(s)] == s for s in seqs for i in range(len(toks) - len(s) + 1)) or \
                    (seqs and x.name == "pr_check_multi.json"):
                gone.append(x)
    return gone


def child_runs(proj, st, dd, dkey, key, a, dry):
    """Vivado's child runs: when only RMs were added, removed or changed and the static implementation's inputs are
    the same, keep static (and every unchanged RM build) and remove only the outputs of the changed RMs. Returns True
    when it handled the stamp; otherwise (several partitions, first build, unchanged inputs, changed static inputs)
    the caller's runner.fresh decides, and the stamp gets the per-RM keys."""
    root = dfx_root(proj)
    stamp = root / runner.CONFIG["stamp"]
    multi = len(proj.dfx["partitions"]) > 1
    rms = {r: f for q in proj.dfx["partitions"] for r, f in st["rms"][q["name"]].items()}
    if multi:
        srm = [q["rms"][0] for q in dd["partitions"]]
        sdd = {k: v for k, v in dd.items() if k not in ("rms", "default_rms", "configs", "partitions")}
        sdd["partitions"] = [dict(q, rms=q["rms"][:1]) for q in dd["partitions"]]
    else:
        srm = static_rms(proj, a, dd)
        sdd = {k: v for k, v in dd.items() if k not in ("rms", "default_rms")}
    sdd["static_rms"] = {r: str(rms[r]) for r in srm if r in rms}
    sfiles = [f for f in dfx_inputs(proj, st) if f not in rms.values()] + [rms[r] for r in srm if r in rms]
    skey = runner.digest(sfiles, dict(dkey, design=sdd))
    rkeys = {r: runner.digest([f], {}) for r, f in rms.items()}
    rec = {"inputs": key, "static": skey, "rms": rkeys}
    if multi:
        rec["configs"] = ["_".join(c) for c in dd["configs"]]
    old = json.loads(stamp.read_text()) if stamp.exists() else None
    if old is None or old.get("inputs") == key or old.get("static") != skey:
        if not dry:
            runner.fresh(root, key, dry)
            stamp.write_text(json.dumps(rec) + "\n")
        return False
    changed = sorted(r for r in set(old.get("rms", {})) | set(rkeys) if old.get("rms", {}).get(r) != rkeys.get(r))
    out = dfx_out(proj)
    if multi:
        gone_cfgs = sorted(set(old.get("configs", [])) - set(rec["configs"]))
        gone = multi_outputs(out, changed, gone_cfgs)
        changed += [f"configuration {c}" for c in gone_cfgs]
    else:
        gone = [x for r in changed for pat in RM_OUTPUTS for x in sorted(out.glob(pat.format(rm=r)))]
    print(f"[{'dry' if dry else 'run'}] static inputs unchanged: child runs for RM(s) {changed}; keeping static and "
          f"the other RM builds; removing {len(gone)} output(s) of the changed RMs", flush=True)
    if not dry:
        for x in gone:
            shutil.rmtree(x) if x.is_dir() else x.unlink()
        stamp.write_text(json.dumps(rec) + "\n")
    return True


def cmd_dfx_build(a):
    proj = load(a)
    if not proj.dfx:
        sys.exit("ofx dfx build: the project has no [dfx] section")
    dry = is_dry(a)
    st = staged(proj, dry)
    for q in proj.dfx["partitions"]:
        rc = region_drc(proj, q["region"])
        if rc:
            sys.exit(f"ofx: command failed (exit {rc}): region DRC {q['region']}")
    dd = design_dict(proj, st)
    dkey = {"design": dd, "part": proj.part, "freq": proj.freq_mhz()}
    if st["inputs"] != st["sources"] or any(vhdl.is_vhdl(f) for q in proj.dfx["partitions"] for f in q["rms"].values()):
        dkey["vhdl"] = {"std": proj.vhdl_std, "units": proj.vhdl_units}
        if proj.vhdl_generics:
            dkey["vhdl"]["generics"] = proj.vhdl_generics
    key = runner.digest(dfx_inputs(proj, st), dkey)
    if not child_runs(proj, st, dd, dkey, key, a, dry):
        runner.fresh(dfx_root(proj), key, dry)
    argv = []
    if len(proj.dfx["partitions"]) == 1:
        argv += ["--rms"] + (a.rms or proj.dfx["partitions"][0]["default_rms"])
        if proj.dfx["timing_allow_fail"]:
            argv += ["--timing-allow-fail"] + proj.dfx["timing_allow_fail"]
    if not dry:
        argv.append("--run")
    job = {"flow": str(FLOW), "design": dd, "argv": argv, "chipdb": proj.device["chipdb"],
           "variant": proj.dfx["variant"]}
    if proj.device.get("db_extra"):
        job["db_root"] = proj.device["db_root"]
    if runner.nextpnr_limit() is not None:
        job["npwait"] = str(runner.CONFIG["npwait"])
    jf = dfx_root(proj) / "ofx_job.json"
    jf.parent.mkdir(parents=True, exist_ok=True)
    jf.write_text(json.dumps(job, indent=1) + "\n")
    runner.run([CONFIG["py"], ROOT / "ofx" / "_native_run.py", jf], env=env_for(proj))
    make_partials(proj, a, dry)


def module_builds(proj):
    out = dfx_out(proj)
    found = {}
    for d in sorted(out.glob("*_n")) + sorted(out.glob("*_n_taf")):
        if (d / f"{proj.top}.bit").exists():
            found[re.sub(r"_n(_taf)?$", "", d.name)] = d
    return found


def static_pips(proj):
    out = dfx_out(proj)
    return out / ("static_pp.prerouted" if proj.dfx["partpins"] == "auto" else "static.prerouted")


def partial_args(proj):
    x = []
    if proj.dfx["rar"]:
        x.append("--reset-after-reconfig")
    if proj.dfx["compress"]:
        x.append("--compress")
    return x


def partial_jobs(proj):
    out = dfx_out(proj)
    top = proj.top
    parts = proj.dfx["partitions"]
    jobs = []
    if len(parts) == 1:
        b = module_builds(proj)
        for t, s in itertools.permutations(sorted(b), 2):
            jobs.append((f"rm_{t}_from_{s}", b[t], b[s], parts[0]["region"], []))
        return jobs
    cfgs = {}
    for d in sorted(out.glob("*_n")):
        if (d / f"{top}.bit").exists():
            cfgs[tuple(d.name[:-2].split("_"))] = d
    for ca, cb in itertools.permutations(sorted(cfgs), 2):
        diff = [k for k in range(len(parts)) if ca[k] != cb[k]]
        if len(diff) != 1:
            continue
        k = diff[0]
        others = [q["region"] for j, q in enumerate(parts) if j != k]
        name = f"{parts[k]['name']}_{ca[k]}_from_{cb[k]}_cfg_{'_'.join(ca)}"
        jobs.append((name, cfgs[ca], cfgs[cb], parts[k]["region"], [x for o in others for x in ("--other-region", o)]))
    return jobs


def make_partials(proj, a, dry):
    pd = dfx_out(proj) / "partials"
    jobs = partial_jobs(proj)
    if dry and not jobs:
        print(f"[dry] partials: one per ordered pair of module builds, into {pd} (partial.py, --simulate)")
        return
    top = proj.top
    fail = 0
    for name, t, s, reg, extra in jobs:
        o = pd / name
        if (o.with_suffix(".check.json")).exists() and not getattr(a, "force", False):
            print(f"[skip] partial {name}: {o.name}.check.json exists")
            continue
        cmd = [CONFIG["py"], runner.flow("partial.py"), t / f"{top}.bit", o, "--design", top, "--region", reg,
               "--fasm", t / f"{top}.fasm", "--static-pips", static_pips(proj), "--base", s / f"{top}.bit",
               "--simulate"] + extra + partial_args(proj)
        if not dry:
            pd.mkdir(parents=True, exist_ok=True)
        rc = runner.run(cmd, env=env_for(proj), dry=dry, log=o.with_suffix(".log"), check=False)
        if rc:
            fail += 1
            print(f"FAIL partial {name} ({o.with_suffix('.log')})")
        elif not dry:
            print(f"OK   partial {name}: {last_line(o.with_suffix('.log'), 'crc:')}")
    if fail:
        sys.exit(f"ofx: {fail} partial(s) refused or failed")


def last_line(f, prefix):
    lines = [l for l in Path(f).read_text().splitlines() if l.startswith(prefix)]
    return lines[-1] if lines else ""


def record_ok(rec_path, bin_path):
    import hashlib
    r = json.loads(Path(rec_path).read_text())
    sha = hashlib.sha256(Path(bin_path).read_bytes()).hexdigest()
    problems = []
    if sha != r["sha256"]:
        problems.append("sha256 does not match the safety record")
    if not r.get("outside_are_static_pads"):
        problems.append("the record says frames outside the region")
    sim = r.get("simulated")
    if not sim or sim.get("frames_differ") != 0 or not sim.get("crc_ok"):
        problems.append("not simulated clean")
    return r, problems


def cmd_dfx_partials(a):
    proj = load(a)
    if not proj.dfx:
        sys.exit("ofx: the project has no [dfx] section")
    make_partials(proj, a, is_dry(a))


def cmd_dfx_verify(a):
    proj = load(a)
    if not proj.dfx:
        sys.exit("ofx: the project has no [dfx] section")
    dry = is_dry(a)
    st = staged(proj, dry)
    out = dfx_out(proj)
    env = env_for(proj)
    results = []
    for q in proj.dfx["partitions"]:
        rc = region_drc(proj, q["region"], dry)
        results.append((f"region DRC {q['name']} {q['region']}", rc == 0 if not dry else None))
    for f, ok, ndiff, nin, nout in reports.pr_check_summary(out / "checks"):
        pair = f.stem[9:]
        if any(pair.startswith(g + "_") for g in CONFIG["greybox_builds"]):
            results.append((f"pr_check {pair}: {ndiff} frames differ, {nin} inside, {nout} outside, "
                            f"{'static identical' if ok else 'static differs'} (greybox static build, not a load "
                            f"target; docs/phase14-auto-partpins.md section 6)", "info"))
            continue
        results.append((f"pr_check {pair}: {ndiff} frames differ, {nin} inside, {nout} outside", ok))
    mj = out / "checks" / "pr_check_multi.json"
    if mj.exists():
        pairs = json.loads(mj.read_text()).get("pairs", [])
        npass = sum(1 for x in pairs if x.get("pass"))
        results.append((f"pr_check_multi: {npass}/{len(pairs)} configuration pairs pass ({mj})",
                        bool(pairs) and npass == len(pairs)))
    vd = out / "verify"
    single = len(proj.dfx["partitions"]) == 1
    p0 = proj.dfx["partitions"][0]
    shell = out / ("rm_shell_pp.v" if proj.dfx["partpins"] == "auto" else "rm_shell_native.v")
    pp = ["--partpins", str(out / "static_pp.json")] if proj.dfx["partpins"] == "auto" else []

    def r2v(bit, rm, tag, log):
        job = {"flow": str(FLOW), "argv": ["check", str(bit), p0["region"], "--shell", str(shell), "--rm", rm,
                                           "--tag", tag] + pp + (["--formal"] if a.formal else []),
               "rtl_dir": str(st["r2v_rtl"][p0["name"]]), "ports_json": str(st["specs"][p0["name"]]),
               "fabric": proj.device["fabric"]}
        jf = vd / f"{tag}.r2v.json"
        if not dry:
            vd.mkdir(parents=True, exist_ok=True)
            jf.write_text(json.dumps(job, indent=1) + "\n")
        cmd = [CONFIG["py"], ROOT / "ofx" / "_r2v_run.py", jf]
        if a.formal:
            cmd = ["bash", "-c", f"ulimit -v {CONFIG['formal_mem_kb']}; exec timeout {CONFIG['formal_timeout_s']} "
                   + runner.show(cmd)]
        return runner.run(cmd, env=env, dry=dry, log=log, check=False)

    tagp = re.sub(r"\W", "_", f"ofx_{proj.name}_{proj.dfx['variant']}")
    if single and not a.no_region2v:
        for rm, d in module_builds(proj).items():
            rc = r2v(d / f"{proj.top}.bit", rm, f"{tagp}_{rm}", vd / f"r2v_full_{rm}.log")
            results.append((f"region2v full build {rm}{' (+formal)' if a.formal else ''}", rc == 0 if not dry else None))
    for name, t, s, reg, extra in partial_jobs(proj):
        o = out / "partials" / name
        rec = o.with_suffix(".check.json")
        if not rec.exists():
            results.append((f"partial {name}: no safety record (run `ofx dfx build --run`)", False if not dry else None))
            continue
        r, problems = record_ok(rec, o.with_suffix(".bin"))
        results.append((f"partial {name}: {r['bytes']} B, {r['region_frames']} region frames, outside {r['outside_frames']}"
                        f"{'; ' + '; '.join(problems) if problems else ''}", not problems))
        if not single:
            continue
        bm = vd / f"bm_{name}.bit"
        rc = runner.run([CONFIG["byteman"], "XS7", "-w", "-i", "main", s / f"{proj.top}.bit", "-i", "main",
                         o.with_suffix(".bit"), "-o", "full", bm], dry=dry, log=vd / f"bm_{name}.log", check=False)
        if rc == 0 or dry:
            rc = runner.run([CONFIG["py"], ROOT / "ofx" / "_bmcmp.py", bm, t / f"{proj.top}.bit", s / f"{proj.top}.bit"],
                            env=env, dry=dry, log=vd / f"bmcmp_{name}.log", check=False)
        results.append((f"byteman {name}: base + partial vs original target"
                        + (f": {last_line(vd / f'bmcmp_{name}.log', '')}" if not dry and (vd / f'bmcmp_{name}.log').exists() else ""),
                        rc == 0 if not dry else None))
        if not a.no_region2v:
            rm = name.split("_from_")[0][3:]
            rc = r2v(bm, rm, f"{tagp}_bm_{name}", vd / f"r2v_{name}.log")
            results.append((f"region2v on byteman result {name}", rc == 0 if not dry else None))
    if proj.dfx["decoupler"]:
        spec = p0["spec"]
        w_in, w_out = sum(w for _, w in spec["inputs"]), sum(w for _, w in spec["outputs"])
        rc = runner.run(["bash", CONFIG["decoupler_prove"]], env={"W_TO_RP": str(w_in), "W_FROM_RP": str(w_out)},
                        dry=dry, log=vd / "decoupler_prove.log", check=False)
        results.append((f"dfx_decoupler proof (W_TO_RP={w_in}, W_FROM_RP={w_out})", rc == 0 if not dry else None))
    bad = 0
    for what, ok in results:
        tag = "DRY " if ok is None else "INFO" if ok == "info" else ("PASS" if ok else "FAIL")
        bad += ok is False
        print(f"{tag} {what}")
    if not dry:
        info = sum(1 for _, ok in results if ok == "info")
        print(f"verify: {sum(1 for _, ok in results if ok is True)} PASS, {bad} FAIL"
              f"{f', {info} INFO' if info else ''} (logs under {vd})")
    sys.exit(1 if bad else 0)


def find_partial(proj, name):
    p = Path(name)
    if p.exists():
        return p.with_suffix(".bin")
    q = dfx_out(proj) / "partials" / (name if name.endswith(".bin") else name + ".bin")
    if q.exists():
        return q
    sys.exit(f"ofx dfx load: no partial {name} (looked in {dfx_out(proj) / 'partials'})")


def winpath(p):
    r = subprocess.run(["wslpath", "-w", str(p)], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else str(p)


def cmd_dfx_load(a):
    proj = load(a)
    dry = is_dry(a)
    b = find_partial(proj, a.partial)
    rec = b.with_suffix(".check.json")
    if not rec.exists():
        sys.exit(f"REFUSED: no safety record {rec} (partials must come from `ofx dfx build` / flow/partial.py)")
    r, problems = record_ok(rec, b)
    if problems:
        sys.exit(f"REFUSED: {b}: {'; '.join(problems)}")
    print(f"safety record OK: region {r['region']}, {r['region_frames']} frames, sha256 {r['sha256'][:16]}..., "
          f"simulated from {Path(r['simulated']['base']).parent.name}")
    if a.via == "jtag":
        ofl = next((x for x in (CONFIG["openfpgaloader_release"], CONFIG["openfpgaloader_partial"]) if x.exists()), None)
        if ofl is None:
            sys.exit(f"ofx: no openFPGALoader with --partial: neither the release install's {CONFIG['openfpgaloader_release']} "
                     f"nor {CONFIG['openfpgaloader_partial']} (docs/drafts/openfpgaloader-partial.md)")
        cmd = [ofl, "-b", board_ofl(proj, a), "--partial", b.with_suffix(".bit")]
        runner.run(cmd, dry=dry)
    else:
        cmd = [CONFIG["powershell"], "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", winpath(CONFIG["icap_loader"]),
               "-Partial", winpath(b), "-Target", a.target]
        if not dry:
            if not a.port:
                sys.exit("ofx dfx load --via icap --run needs --port COMx")
            cmd += ["-Run", "-Port", a.port]
        if dry and not shutil.which(CONFIG["powershell"]):
            runner.run(cmd, dry=True)
        else:
            runner.run(cmd)
    if dry:
        print("DRY RUN: nothing sent to a board. Add --run to load it.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ofx", description="open-dfx-xc7 project flow for Xilinx 7-series: synthesis "
                                 "(Yosys), place and route (nextpnr-xilinx), bitstream (Project X-Ray), programming "
                                 "(openFPGALoader) and partial reconfiguration")
    ap.add_argument("--version", action="version", version=f"ofx {VERSION}")
    ap.add_argument("-p", "--project", help="project file or directory (default: search upwards for ofx.toml)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="create a skeleton project for a board preset or a part")
    n.add_argument("target", help="board preset (see `ofx boards`) or part, e.g. xc7a100tcsg324-1")
    n.add_argument("dir", nargs="?")
    n.add_argument("--name")
    n.add_argument("--dfx", action="store_true", help="also create a partition with two RMs")
    n.add_argument("--partpins", choices=["auto", "anchors"], default=P.CONFIG["partpins"])
    n.add_argument("--force", action="store_true")
    n.set_defaults(fn=cmd_new)
    sub.add_parser("boards", help="list board presets").set_defaults(fn=cmd_boards)
    dv = sub.add_parser("device", help="show how a part maps to family, fabric and chipdb")
    dv.add_argument("part")
    dv.set_defaults(fn=cmd_device)
    b = sub.add_parser("build", help="synth, place and route, bitstream (dry run unless --run)")
    b.add_argument("--run", action="store_true")
    b.add_argument("--incremental", metavar="REF",
                   help="reuse the placement and routing of a reference build (its impl directory) for every cell "
                        "and net the design change left alone, like Vivado's read_checkpoint -incremental "
                        "(flow/incremental.py)")
    b.add_argument("--incremental-routes", action="store_true",
                   help="with --incremental, also replay the reference's routes (slice-level reuse)")
    b.set_defaults(fn=cmd_build)
    hl = sub.add_parser("hls", help="high-level synthesis: C/C++ [[hls]] kernels to Verilog with Bambu (ofx build "
                                     "runs it too); --sim co-simulates each kernel's C testbench against its RTL "
                                     "(dry run unless --run)")
    hl.add_argument("--sim", action="store_true", help="also run the C testbench against the RTL (Verilator)")
    hl.add_argument("--run", action="store_true")
    hl.set_defaults(fn=cmd_hls)
    pr = sub.add_parser("program", help="program the board with openFPGALoader (dry run unless --run)")
    pr.add_argument("--flash", action="store_true", help="write the SPI flash instead of SRAM")
    pr.add_argument("--bit")
    pr.add_argument("--board", help="openFPGALoader board name")
    pr.add_argument("--run", action="store_true")
    pr.set_defaults(fn=cmd_program)
    bo = sub.add_parser("boot", help="Zynq PS boot files: U-Boot SPL boot.bin (ps7_init), FIT with the PL bitstream and "
                                     "the [zynq] app, SD image, OpenOCD JTAG script (dry run unless --run)")
    bo.add_argument("--qemu", action="store_true", help="also boot it in QEMU xilinx-zynq-a9 (JTAG and SD modes)")
    bo.add_argument("--sim", action="store_true", help="also simulate the PL (RTL and bitstream netlist) against a PS7 "
                                                       "model replaying the app's M_AXI_GP0 accesses")
    bo.add_argument("--run", action="store_true")
    bo.set_defaults(fn=cmd_boot)
    t = sub.add_parser("timing", help="Vivado-style timing summary (check_timing, WNS/TNS/WHS/THS, clock tables, "
                                      "worst paths) from nextpnr's report")
    t.add_argument("--dfx", action="store_true", help="the DFX builds instead of the flat build")
    t.add_argument("--build", help="a build directory (or a directory of them) instead of the project's")
    t.add_argument("--paths", type=int, default=1, help="worst paths to print per check (default 1)")
    t.add_argument("--hold", action="store_true", help="also hold: histogram and worst hold paths")
    t.add_argument("--from", dest="from_", help="glob on the start cell or launch clock")
    t.add_argument("--to", help="glob on the end cell, cell/pin or capture clock")
    t.add_argument("--list", type=int, default=5, help="items listed per check_timing line (default 5)")
    t.set_defaults(fn=cmd_timing)
    dr = sub.add_parser("drc", help="Vivado-style report_drc on the routed (or synthesized) design; exit 1 on Error rules")
    pw = sub.add_parser("power", help="Vivado-style report_power estimate (vectorless) of the routed design")
    for x in (dr, pw):
        x.add_argument("--build", help="a build directory or netlist JSON instead of the project's")
        x.add_argument("--xdc", nargs="*", help="constraint files (default: the project's)")
        x.add_argument("--json", help="also write the result as JSON")
    dr.add_argument("--part", help="part for package pins/banks (default: the project's)")
    dr.add_argument("--no-fail", action="store_true", help="exit 0 even with Error rules")
    dr.set_defaults(fn=cmd_drc)
    pw.add_argument("--model", help="power model JSON (default ofx/power_model.json)")
    pw.set_defaults(fn=cmd_power, part=None)
    r = sub.add_parser("report", help="report summary from the nextpnr logs")
    r.add_argument("--dfx", action="store_true", help="the DFX builds instead of the flat build")
    r.set_defaults(fn=cmd_report)
    d = sub.add_parser("dfx", help="partial reconfiguration")
    ds = d.add_subparsers(dest="dcmd", required=True)
    db = ds.add_parser("build", help="native DFX flow: every configuration, pr_check, partials (dry run unless --run)")
    db.add_argument("--rms", nargs="+", help="build only these RMs (single partition)")
    db.add_argument("--force", action="store_true", help="rewrite partials that already have a safety record")
    db.add_argument("--run", action="store_true")
    db.set_defaults(fn=cmd_dfx_build)
    dp = ds.add_parser("partials", help="write the partials of finished builds (dry run unless --run)")
    dp.add_argument("--force", action="store_true")
    dp.add_argument("--run", action="store_true")
    dp.set_defaults(fn=cmd_dfx_partials)
    dvf = ds.add_parser("verify", help="region DRC, pr_check, safety records, byteman, region2v (dry run unless --run)")
    dvf.add_argument("--formal", action="store_true", help="also prove region2v equivalence (yosys sat)")
    dvf.add_argument("--no-region2v", action="store_true")
    dvf.add_argument("--run", action="store_true")
    dvf.set_defaults(fn=cmd_dfx_verify)
    dl = ds.add_parser("load", help="send a checked partial over JTAG or the ICAP UART loader (dry run unless --run)")
    dl.add_argument("partial", help="partial name (e.g. rm_xor_from_andn) or path")
    dl.add_argument("--via", choices=["jtag", "icap"], default="icap")
    dl.add_argument("--port", help="COM port for --via icap")
    dl.add_argument("--target", choices=["bridge", "rvsoc"], default="bridge", help="icap_load.ps1 -Target")
    dl.add_argument("--board", help="openFPGALoader board name for --via jtag")
    dl.add_argument("--run", action="store_true")
    dl.set_defaults(fn=cmd_dfx_load)
    cli_ip.add_parsers(sub)
    a = ap.parse_args(argv)
    a.fn(a)
