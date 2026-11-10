import argparse
import filecmp
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ofx import defaults

CONFIG = {
    "dry_run": True,
    "prefix": Path(os.environ.get("OFX_PREFIX", Path.home() / ".local" / "ofx")),
    "out": ROOT / "build" / "defaults_noop",
    "designs": {
        "blinky": {"top": "blinky", "recorded": "build/patched/baseline/blinky_stock/blinky.json",
                   "changed_by": ["carry_di_bypass"]},
        "rv_soc": {"top": "rv_soc", "recorded": "build/patched/baseline/rv_soc_stock/rv_soc.json",
                   "rtl": ["rv_soc.v", "uart.v", "picorv32.v", "pr/rm_stub.v"],
                   "changed_by": ["hardblock_timing", "carry_di_bypass"]},
        "fir": {"top": "qor_fir", "dir": "designs/qor/qor_fir",
                "recorded": "build/qor/synth/fir/3b84a4562f8f4000/qor_fir.json",
                "changed_by": ["hardblock_timing", "dsp_cascade"],
                "base_args": ["-o", "dsp-cascade-place"]},
    },
    "part": "xc7a35tcsg324-1",
    "max_nextpnr": int(os.environ.get("OFX_MAX_NEXTPNR", 2)),
    "plain_synth": "synth_xilinx -flatten -abc9 -arch xc7 -top {top}",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "candidates": {
        "hardblock_timing": {"noop_pnr": ["blinky"]},
        "clkbuf_keep_buffer_inputs": {"noop_synth": ["blinky", "rv_soc"], "fixes": ["bufr", "bufio_iddr", "oserdes"]},
        "static_all_sizes": {"placer_rule": [100, 3000, 3001, 30000]},
    },
    "gap_dir": "designs/gap",
}

results = []


def result(ok, text):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {text}", flush=True)


def paths(prefix):
    return {"yosys": prefix / "opt" / "oss-cad-suite" / "bin" / "yosys",
            "nextpnr": prefix / "bin" / "nextpnr-himbaechel",
            "chipdb": prefix / "share" / "nextpnr" / "himbaechel" / "xilinx" / "chipdb-xc7a50t.bin",
            "db": prefix / "share" / "nextpnr" / "external" / "prjxray-db",
            "plugins": prefix / "share" / "ofx" / "yosys-plugins"}


def run(cmd, log, dry, env=None):
    print(f"[{'dry' if dry else 'run'}] {' '.join(str(c) for c in cmd)}", flush=True)
    if dry:
        return 0
    log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(log, "w") as f:
        r = subprocess.run([str(c) for c in cmd], stdout=f, stderr=subprocess.STDOUT, cwd=ROOT,
                           env=dict(os.environ, **(env or {})))
    print(f"        {time.time() - t0:.0f}s exit {r.returncode}", flush=True)
    return r.returncode


def auto_name(line):
    return re.sub(r"\$auto\$[A-Za-z0-9_]+\.cc:\d+:", "$auto$", line)


def json_body(p):
    return [l for l in Path(p).read_text().splitlines() if '"creator":' not in l]


def synth(name, d, script, out, p, dry, src=None):
    js = out / f"{d['top']}.json"
    if js.exists() and js.stat().st_size:
        return js
    src = src or ROOT / "designs" / name
    rtl = ([str(src / x) for x in d["rtl"]] if d.get("rtl") else
           sorted(str(x) for x in src.glob("*.v")) + sorted(str(x) for x in src.glob("*.sv")))
    ys = f"read_verilog -sv {' '.join(rtl)}; {script.replace('{top}', d['top'])}; write_json {js}"
    out.mkdir(parents=True, exist_ok=True)
    if run([p["yosys"], "-p", ys], out / "yosys.log", dry) and not dry:
        js.unlink(missing_ok=True)
    return js


def pnr(name, d, args, out, p, dry, json_file=None, xdc=None):
    frames = out / f"{d['top']}.frames"
    if frames.exists() and frames.stat().st_size:
        return frames
    if out.exists() and not dry:
        subprocess.run(["rm", "-rf", str(out)])
    cmd = [sys.executable, ROOT / "flow" / "build_openxc7.py", name, "--top", d["top"],
           "--json", json_file or ROOT / d["recorded"]] + (["--xdc", xdc] if xdc else []) + [
        "--nextpnr", CONFIG["npwait"], "--chipdb", p["chipdb"], "--db-root", p["db"], "--out", out, "--run"]
    cmd += [f"--nextpnr-arg={a}" for a in args]
    env = {"OFX_NEXTPNR_BIN": str(p["nextpnr"]), "OFX_MAX_NEXTPNR": str(CONFIG["max_nextpnr"])}
    if run(cmd, out.parent / f"{out.name}.log", dry, env) and not dry:
        frames.unlink(missing_ok=True)
    return frames


def built(f):
    return f.exists() and f.stat().st_size > 0


def check_all_off(p):
    off = dict(defaults.CONFIG["all_off"])
    s, loads = defaults.synth_script(off, "x.xdc", p["plugins"])
    npa = defaults.nextpnr_args(off)
    pl, _ = defaults.placer_args({"placer": off["placer"]})
    cd, _ = defaults.chipdb_choice({"chipdb": None, "xadc_chipdb": "ofx/chipdb.bin"}, ["FDRE", "LUT6"])
    cx, _ = defaults.chipdb_choice({"chipdb": None, "xadc_chipdb": "ofx/chipdb.bin"}, ["XADC"])
    result(s is None and not loads and npa == [] and pl == [] and cd is None,
           f"all options off is the plain flow: synth script {s!r}, nextpnr args {npa + (pl or [])}, chipdb {cd or 'default'}")
    result(cx == "ofx/chipdb.bin", f"a netlist with an XADC gets the XADC chipdb ({cx})")


def check_candidates(names, p, out, dry):
    base = dict(defaults.CONFIG["defaults"])
    for opt in names:
        spec = CONFIG["candidates"][opt]
        on = dict(base, **{opt: True}) if opt in base else dict(base)
        print(f"== candidate {opt}: on top of the defaults", flush=True)
        for name in spec.get("noop_synth", []):
            d = CONFIG["designs"][name]
            xdc = next((ROOT / d.get("dir", f"designs/{name}")).glob("*.xdc"))
            s0, _ = defaults.synth_script(base, xdc, p["plugins"])
            s1, _ = defaults.synth_script(on, xdc, p["plugins"])
            j0 = synth(name, d, s0 or CONFIG["plain_synth"], out / name / "synth_defaults", p, dry)
            j1 = synth(name, d, s1, out / name / f"synth_{opt}", p, dry)
            if dry:
                continue
            if not (built(j0) and built(j1)):
                result(False, f"{opt} {name}: yosys failed ({j0}, {j1})")
                continue
            b0, b1 = json_body(j0), json_body(j1)
            if b0 == b1:
                result(True, f"{opt} {name}: yosys JSON identical to the defaults' (creator line aside)")
                continue
            names_only = [auto_name(l) for l in b0] == [auto_name(l) for l in b1]
            args = defaults.nextpnr_args(base)
            f0 = pnr(name, d, args, out / name / "pnr_synth_defaults", p, dry, json_file=j0, xdc=xdc)
            f1 = pnr(name, d, args, out / name / f"pnr_synth_{opt}", p, dry, json_file=j1, xdc=xdc)
            same = built(f0) and built(f1) and filecmp.cmp(f0, f1, shallow=False)
            result(same, f"{opt} {name}: yosys JSON differs "
                         f"{'only in $auto$ cell/net names' if names_only else 'in structure'}; .frames after P&R "
                         f"(release nextpnr, {' '.join(args)}) {'identical' if same else 'differ'}")
        for name in spec.get("noop_pnr", []):
            d = CONFIG["designs"][name]
            a0, a1 = defaults.nextpnr_args(base), defaults.nextpnr_args(on)
            f0 = pnr(name, d, a0, out / name / "pnr_on", p, dry)
            f1 = pnr(name, d, a1, out / name / f"pnr_{opt}", p, dry)
            if not dry:
                result(built(f0) and built(f1) and filecmp.cmp(f0, f1, shallow=False),
                       f"{opt} {name}: .frames with {' '.join(a1)} identical to the defaults' ({' '.join(a0)})")
        for cells in spec.get("placer_rule", []):
            old = ["--placer", "static"] if cells <= 3000 else []
            new, why = defaults.placer_args({"placer": "auto"}, cells)
            if cells <= 3000:
                result(new == old, f"{opt} {cells} cells: nextpnr placer arguments {new} = the 3000-cell rule's {old}")
            else:
                print(f"INFO {opt} {cells} cells: {new} instead of the 3000-cell rule's {old or 'HeAP'} ({why}); "
                      f"evidence: Vivado-timer runs in docs/wip/placement-global.md", flush=True)
        for name in spec.get("fixes", []):
            src = ROOT / CONFIG["gap_dir"] / name
            d = {"top": name}
            xdc = next(src.glob("*.xdc"))
            got = {}
            for tag, o in (("defaults", base), (opt, on)):
                script, _ = defaults.synth_script(o, xdc, p["plugins"])
                j = synth(name, d, script or CONFIG["plain_synth"], out / "gap" / name / f"synth_{tag}", p, dry, src=src)
                f = pnr(name, d, defaults.nextpnr_args(o), out / "gap" / name / f"pnr_{tag}", p, dry, json_file=j, xdc=xdc)                     if dry or built(j) else None
                got[tag] = "bitstream" if f is not None and built(f) and any((f.parent).glob("*.bit")) else                     ("no yosys netlist" if not built(j) else "nextpnr/bitstream failed")
            if not dry:
                result(got[opt] == "bitstream", f"{opt} fixes {name}: {got[opt]} with it, {got['defaults']} with the "
                                                f"defaults only")


def main():
    ap = argparse.ArgumentParser(description="ofx release defaults: default-on options are no-ops on designs they must "
                                             "not change; all options off is the plain flow")
    ap.add_argument("--prefix", default=str(CONFIG["prefix"]))
    ap.add_argument("--out", default=str(CONFIG["out"]))
    ap.add_argument("--designs", nargs="+", default=list(CONFIG["designs"]))
    ap.add_argument("--candidates", nargs="*", default=None, choices=list(CONFIG["candidates"]),
                    help="instead of the defaults checks, check these opt-in options for the defaults (no name: all)")
    ap.add_argument("--plugins", default=None, help="yosys plugin directory instead of the prefix's")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    p = paths(Path(a.prefix).resolve())
    if a.plugins:
        p["plugins"] = Path(a.plugins).resolve()
    out = Path(a.out).resolve()
    on = dict(defaults.CONFIG["defaults"])
    print(f"== defaults: {json.dumps(on, sort_keys=True)}")
    if a.candidates is not None:
        check_candidates(a.candidates or list(CONFIG["candidates"]), p, out / "candidates", dry)
        if not dry:
            print(f"== {sum(results)}/{len(results)} checks pass")
            sys.exit(0 if all(results) else 1)
        return
    check_all_off(p)
    for name in a.designs:
        d = CONFIG["designs"][name]
        on_args = defaults.nextpnr_args(dict(on, **{k: False for k in d.get("changed_by", [])}))
        src = ROOT / d.get("dir", f"designs/{name}")
        xdc = next(src.glob("*.xdc"))
        script, _ = defaults.synth_script(on, xdc, p["plugins"])
        if script:
            j0 = synth(name, d, CONFIG["plain_synth"], out / name / "synth_plain", p, dry, src=src)
            j1 = synth(name, d, script, out / name / "synth_defaults", p, dry, src=src)
            if not dry:
                same = built(j0) and built(j1) and json_body(j0) == json_body(j1)
                result(same, f"{name}: yosys JSON with the default synthesis ({script}) identical to plain synth_xilinx "
                             f"(creator line aside)")
        if on_args:
            base_args = d.get("base_args", [])
            pxdc = xdc if d.get("dir") else None
            f0 = pnr(name, d, base_args, out / name / "pnr_off", p, dry, xdc=pxdc)
            f1 = pnr(name, d, base_args + on_args, out / name / "pnr_on", p, dry, xdc=pxdc)
            if not dry:
                same = built(f0) and built(f1) and filecmp.cmp(f0, f1, shallow=False)
                result(same, f"{name}: release nextpnr with {' '.join(on_args)} gives .frames identical to without "
                             f"(recorded netlist {d['recorded']}{', both with ' + ' '.join(base_args) if base_args else ''})")
    if dry:
        return
    print(f"== {sum(results)}/{len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
