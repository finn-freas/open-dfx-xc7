import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
import region
import replay_dump
import xroute
from build_openxc7 import tool

ROOT = qor_bench.ROOT
NB = ROOT / "build" / "nextpnr-build"

CONFIG = {
    "out": ROOT / "build" / "rte",
    "win_src": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/rte"),
    "win_out": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/rte"),
    "tcl": ROOT / "vivado" / "build_rte.tcl",
    "vivado_bat": Path("/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"),
    "slot_helper": ROOT / "vivado" / "vivado_slot.sh",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "max_nextpnr": "3",
    "dry_run": True,
    "vivado_chunk": 2,
    "period": 5.0,
    "designs": {
        "rv_soc": "cal_static",
        "rv_mul": "dspq_cal",
        "rv_big": "dspq_cal",
        "bram": "cal_static",
    },
    "variants": {
        "own": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": False, "args": []},
        "vimp": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True, "args": []},
        "vimp_crr3": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                      "args": ["--router2-opt", "critRipupIters=3"]},
        "vimp_cexp8": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                       "args": ["--router2-opt", "critExp=8", "--router2-opt", "critFloor=0.01"]},
        "vimp_ew1": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                     "args": ["--router2-opt", "critEstWeight=1.0"]},
        "vimp_crk3": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                      "args": ["--router2-opt", "critRipupIters=3", "--router2-opt", "critRipupKeepBest=1"]},
        "vimp_crn3": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                      "args": ["--router2-opt", "critRipupIters=3", "--router2-opt", "critRipupResetCong=0"]},
        "vimp_sd1": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                     "args": ["--router2-opt", "critSeedDelay=1.0"]},
        "vimp_sd1crk3": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                         "args": ["--router2-opt", "critSeedDelay=1.0", "--router2-opt", "critRipupIters=3"]},
        "vimp_sd2crk3": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                      "args": ["--router2-opt", "critSeedDelay=2.0", "--router2-opt", "critRipupIters=3"]},
        "vimp_sd1crk5": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                      "args": ["--router2-opt", "critSeedDelay=1.0", "--router2-opt", "critRipupIters=5"]},
        "vimp_sd1crk3t8": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                      "args": ["--router2-opt", "critSeedDelay=1.0", "--router2-opt", "critRipupIters=3", "--router2-opt", "critRipupThresh=0.8"]},
        "vimp_sd1crk3ew1": {"bin": NB / "rte-run" / "nextpnr-himbaechel", "import": True,
                      "args": ["--router2-opt", "critSeedDelay=1.0", "--router2-opt", "critRipupIters=3", "--router2-opt", "critEstWeight=1.0"]},
    },
    "chipdbs": {
        "cal": ROOT / "build/chipdb-cal/on/chipdb-xc7a50t.bin",
        "rcal": ROOT / "build/chipdb-rcal/on/chipdb-xc7a50t.bin",
    },
    "drop_args": {"--placer": 1, "--seed": 1, "--write": 1, "--report": 1, "--chipdb": 1},
    "macro_types": {"RAM32M", "RAM64M", "RAM32X1D", "RAM64X1D"},
}


for _k in [k for k in CONFIG["variants"] if k.startswith("vimp_")]:
    CONFIG["variants"]["own_" + _k[5:]] = dict(CONFIG["variants"][_k], **{"import": False})


def say(dry, msg):
    print(f"[{'dry' if dry else 'run'}] {msg}")


def src_status(design):
    run = qor_bench.CONFIG["out"] / "oxc7" / CONFIG["designs"][design] / f"{design}_{qor_bench.ptag(CONFIG['period'])}" / "s1"
    return run, json.loads((run / "status.json").read_text())


def syn_json(design):
    _, st = src_status(design)
    return Path(st["cmd"][st["cmd"].index("--json") + 1])


def xdc_of(design):
    _, st = src_status(design)
    for a in st["cmd"]:
        if a.startswith("xdc="):
            return Path(a[4:])
    raise SystemExit(f"no xdc in {design}")


def top_of(design):
    return qor_bench.CONFIG["designs"][design]["top"]


def vref_name(design):
    return f"{design}_vref"


def write_vref_src(design, dry):
    d = CONFIG["win_src"] / vref_name(design)
    if (d / "netlist.edf").exists():
        return
    say(dry, f"vref src {d}")
    if dry:
        return
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run([tool("yosys"), "-q", "-p", f"read_json {syn_json(design)}; delete t:$scopeinfo; "
                    f"write_edif -pvector bra {d / 'netlist.edf'}"], check=True)
    (d / "top.txt").write_text(top_of(design) + "\n")
    (d / "mode.txt").write_text("vref\n")
    shutil.copy(xdc_of(design), d / "constraints.xdc")


def run_vivado(names, dry):
    todo = [n for n in names if not (CONFIG["win_out"] / n / "status.txt").exists()]
    k = CONFIG["vivado_chunk"]
    for i in range(0, len(todo), k):
        run_vivado_once(todo[i:i + k], dry)


def run_vivado_once(todo, dry):
    if not todo:
        return
    log = CONFIG["win_out"] / f"vivado_{time.strftime('%Y%m%d_%H%M%S')}.log"
    cmd = ["cmd.exe", "/c", subprocess.check_output(["wslpath", "-w", str(CONFIG["vivado_bat"])], text=True).strip(),
           "-mode", "batch", "-nojournal", "-log", wm(log), "-source", wm(CONFIG["win_src"] / "build_rte.tcl"),
           "-tclargs", wm(CONFIG["win_src"]), wm(CONFIG["win_out"])] + todo
    say(dry, f"vivado {' '.join(todo)} (log {log})")
    if dry:
        return
    CONFIG["win_out"].mkdir(parents=True, exist_ok=True)
    shutil.copy(CONFIG["tcl"], CONFIG["win_src"] / "build_rte.tcl")
    import shlex
    script = (f"source {shlex.quote(str(CONFIG['slot_helper']))}; vivado_acquire; cd /mnt/c/Users/finnf; "
              f"{' '.join(shlex.quote(c) for c in cmd)} >> {shlex.quote(str(CONFIG['win_out'] / 'stdout.txt'))} 2>&1; "
              f"vivado_release")
    subprocess.run(["bash", "-c", script])


def wm(p):
    return subprocess.check_output(["wslpath", "-m", str(p)], text=True).strip()


def vivado_cells(design):
    rows = {}
    for ln in (CONFIG["win_out"] / vref_name(design) / "cells.txt").read_text().splitlines():
        f = ln.split("\t")
        if len(f) == 4 and f[2]:
            rows[f[0]] = (f[1], f[2], f[3].split(".")[-1])
    return rows


def run_name(design, variant, chipdb, seed):
    return f"{design}_{variant}_{chipdb}_s{seed}"


def ref_routed(design, chipdb):
    return CONFIG["out"] / "npr" / run_name(design, "own", "cal", 1) / "routed.json"


def write_import(design, chipdb, dry):
    out = CONFIG["out"] / "import" / f"{design}.place"
    if out.exists():
        return out
    say(dry, f"import {out.relative_to(ROOT)}")
    if dry:
        return out
    vc = vivado_cells(design)
    j = json.loads(ref_routed(design, chipdb).read_text())
    m = replay_dump.top_module(j)
    smap = replay_dump.site_map(region.load_grid())
    smap.update(replay_dump.learn_sites(m))
    macro_site = {}
    for name, (ref, loc, bel) in vc.items():
        if "/" in name:
            macro_site.setdefault(name.rsplit("/", 1)[0], loc)
    stats = Counter()
    lines = []
    for n, c in m["cells"].items():
        t = c["type"]
        nbel = c["attributes"].get("NEXTPNR_BEL", "")
        if not (nbel.startswith("SLICE_") or nbel.startswith("RAMB") or nbel.startswith("DSP48")):
            stats["skip_type"] += 1
            continue
        key = n
        mc = re.match(xroute.CONFIG["carry_re"], n)
        if t == "CARRY4" and mc:
            key = mc.group(1) if mc.group(2) == "0" else None
            if key is None:
                stats["carry_split_offset"] += 1
                continue
        if key in vc:
            ref, loc, bel = vc[key]
            vbel = f"{loc}/{bel}"
            stats["direct"] += 1
        elif "/" in n and n.rsplit("/", 1)[0] in macro_site:
            vbel = f"{macro_site[n.rsplit('/', 1)[0]]}/{nbel.split('/')[1]}"
            stats["macro"] += 1
        else:
            stats["nextpnr_only"] += 1
            continue
        lines.append(f"{n}\t{replay_dump.to_generic_bel(vbel, smap)}\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines))
    out.with_suffix(".json").write_text(json.dumps(dict(stats), indent=1) + "\n")
    print(f"  {design}: {dict(stats)}")
    return out


def nextpnr_cmd(design, variant, chipdb, seed, out):
    _, st = src_status(design)
    v = CONFIG["variants"][variant]
    cmd = [str(v["bin"]), "--chipdb", str(CONFIG["chipdbs"][chipdb])]
    src = st["cmd"][1:]
    i = 0
    while i < len(src):
        a = src[i]
        if a in CONFIG["drop_args"]:
            i += 1 + CONFIG["drop_args"][a]
            continue
        if a == "-o" and src[i + 1].startswith("fasm="):
            i += 2
            continue
        cmd.append(a)
        i += 1
    cmd += ["--placer", "static", "--seed", str(seed), "--write", str(out / "routed.json"), "--report",
            str(out / "report.json"), "-o", f"fasm={out / 'npr.fasm'}"]
    if v["import"]:
        cmd += ["-o", f"place-import={CONFIG['out'] / 'import' / f'{design}.place'}"]
    return cmd + list(v["args"])


def run_nextpnr(design, variant, chipdb, seed, dry):
    out = CONFIG["out"] / "npr" / run_name(design, variant, chipdb, seed)
    if (out / "done.json").exists():
        return out
    cmd = nextpnr_cmd(design, variant, chipdb, seed, out)
    say(dry, f"nextpnr {out.relative_to(ROOT)}")
    if dry:
        return out
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OFX_NEXTPNR_BIN=cmd[0], OFX_MAX_NEXTPNR=CONFIG["max_nextpnr"])
    t0 = time.time()
    with open(out / "nextpnr.log", "w") as lf:
        rc = subprocess.run([str(CONFIG["npwait"])] + cmd[1:], stdout=lf, stderr=subprocess.STDOUT, env=env).returncode
    log = (out / "nextpnr.log").read_text(errors="replace")
    info = {"cmd": cmd, "rc": rc, "wall": round(time.time() - t0, 2), **parse_log(log)}
    (out / "done.json").write_text(json.dumps(info, indent=1) + "\n")
    return out


def parse_log(log):
    r = {}
    m = re.findall(r"Max frequency for clock\s+'[^']*': ([0-9.]+) MHz", log)
    if m:
        r["fmax"] = min(float(x) for x in m)
    m = re.search(r"Router2 time ([0-9.]+)s", log)
    if m:
        r["route_s"] = float(m.group(1))
    m = re.findall(r"(\d+(?:\.\d+)?)s\)?\s*$", log)
    m = re.search(r"place-import: .*", log)
    if m:
        r["import"] = m.group(0)
    m = re.search(r"Program finished normally", log)
    r["ok"] = bool(m)
    t = re.findall(r"Info: Placer.*time ([0-9.]+)s", log)
    if t:
        r["place_s"] = float(t[-1])
    return r


def export_run(design, npr, name, dry):
    dst = CONFIG["win_src"] / name
    if (dst / "netlist.edf").exists():
        return
    say(dry, f"export {name}")
    if dry:
        return
    run, _ = src_status(design)
    xroute.CONFIG["out"] = CONFIG["out"]
    xroute.name_of = lambda d, c="cal": name
    xroute.src_run = lambda d: run
    xroute.dinfo = lambda d: {"top": top_of(d), "xdc": xdc_of(d)}
    d = xroute.export(design, npr, False, "cal")
    shutil.copytree(d, dst)
    (dst / "mode.txt").write_text("fixed\n")
    vr = CONFIG["win_src"] / (name + "_vr")
    shutil.copytree(d, vr)
    (vr / "mode.txt").write_text("fixed\n")
    (vr / "routes.txt").write_text("")
    (vr / "const_routes.txt").write_text("")


def vivado_result(name):
    d = CONFIG["win_out"] / name
    st = d / "status.txt"
    if not st.exists():
        return None
    r = {"rc": st.read_text().split()[1]}
    s = d / "slack.txt"
    if s.exists():
        for ln in s.read_text().splitlines():
            k, _, v = ln.partition(" ")
            r[k] = v
    for k in ("wns", "wns_noicap", "whs", "whs_noicap", "tns_noicap"):
        try:
            r[k] = float(r[k])
        except (KeyError, ValueError):
            r.pop(k, None)
    if "wns_noicap" in r:
        r["fmax_noicap"] = 1000.0 / (CONFIG["period"] - r["wns_noicap"])
    if "wns" in r:
        r["fmax"] = 1000.0 / (CONFIG["period"] - r["wns"])
    t = d / "times.txt"
    if t.exists():
        r["times"] = {a: float(b) for a, b in (ln.split() for ln in t.read_text().splitlines() if ln.strip())}
    rl = d / "route_log.txt"
    if rl.exists():
        m = re.search(r"^ok (\d+) partial (\d+) nonet (\d+)", rl.read_text(), re.M)
        if m:
            r["routes_fixed"], r["routes_partial"], r["routes_nonet"] = map(int, m.groups())
    rs = d / "route_status.rpt"
    if rs.exists():
        m = re.search(r"# of nets with routing errors\.*\s*:\s*(\d+)", rs.read_text())
        if m:
            r["route_errors"] = int(m.group(1))
    return r


def main():
    ap = argparse.ArgumentParser(description="Routing share of the Fmax gap: Vivado's placement routed by nextpnr's "
                                             "router, and nextpnr placements routed by both routers, all timed by "
                                             "Vivado on the identical netlist, placement and (for nextpnr) pips")
    ap.add_argument("stage", choices=["vref", "own", "import", "npr", "export", "vivado", "report"])
    ap.add_argument("--designs", nargs="+", default=list(CONFIG["designs"]))
    ap.add_argument("--variants", nargs="+", default=["vimp"])
    ap.add_argument("--chipdb", default="cal")
    ap.add_argument("--seeds", nargs="+", type=int, default=[1])
    ap.add_argument("--names", nargs="*", default=[])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--no-vr", action="store_true", help="vivado: only the runs with nextpnr's routes imposed")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    if a.stage == "vref":
        for d in a.designs:
            write_vref_src(d, dry)
        run_vivado([vref_name(d) for d in a.designs], dry)
    elif a.stage == "own":
        for d in a.designs:
            run_nextpnr(d, "own", a.chipdb, 1, dry)
    elif a.stage == "import":
        for d in a.designs:
            write_import(d, a.chipdb, dry)
    elif a.stage == "npr":
        for d in a.designs:
            for v in a.variants:
                for s in a.seeds:
                    run_nextpnr(d, v, a.chipdb, s, dry)
    elif a.stage == "export":
        for d in a.designs:
            for v in a.variants:
                for s in a.seeds:
                    n = run_name(d, v, a.chipdb, s)
                    export_run(d, CONFIG["out"] / "npr" / n, n, dry)
    elif a.stage == "vivado":
        names = list(a.names)
        if not names:
            for d in a.designs:
                for v in a.variants:
                    for s in a.seeds:
                        n = run_name(d, v, a.chipdb, s)
                        names += [n] if a.no_vr else [n, n + "_vr"]
        run_vivado(names, dry)
    elif a.stage == "report":
        for d in a.designs:
            print(d, "vref", json.dumps(vivado_result(vref_name(d))))
            for v in a.variants:
                for s in a.seeds:
                    n = run_name(d, v, a.chipdb, s)
                    dj = CONFIG["out"] / "npr" / n / "done.json"
                    npr = json.loads(dj.read_text()) if dj.exists() else {}
                    print(n, "nextpnr", {k: npr.get(k) for k in ("fmax", "wall", "route_s", "import")})
                    print(n, "nextpnr-routed", json.dumps(vivado_result(n)))
                    print(n, "vivado-routed", json.dumps(vivado_result(n + "_vr")))


if __name__ == "__main__":
    main()
