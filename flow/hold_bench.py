"""Hold fixing against Vivado's timer: nextpnr builds of hold-critical designs with and without
-o hold-fix / -o hold-fix-upstream (docs/drafts/nextpnr-hold-fix-upstream.patch, build `hold`), laid out like
flow/qor_bench.py runs (build/qor/oxc7/<variant>/<design>_p<ns>/s<seed>/status.json) so that flow/xroute.py can
impose each implementation on Vivado pip for pip and time its hold paths.

Steps (dry run by default, --run to execute):
  --pnr      nextpnr runs of CONFIG["variants"] x CONFIG["designs"]
  --noop     FASM of the `hold` binary without options vs the release binary (sorted lines, header aside)
  --xprep    flow/xroute.py rerun (--sdf) + export for every run, prints the Vivado names
  --report   nextpnr hold result per run, and Vivado's WHS/WNS on the imposed implementation when present"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
import xroute

ROOT = qor_bench.ROOT
HOME = Path.home()

CONFIG = {
    "dry_run": True,
    "out": ROOT / "build" / "qor" / "hold",
    "oxc7": qor_bench.CONFIG["out"] / "oxc7",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "max_nextpnr": 3,
    "binaries": {
        "release": HOME / "ofx-test" / "prefix" / "bin" / "nextpnr-himbaechel",
        "hold": ROOT / "build" / "nextpnr-build" / "hold" / "nextpnr-himbaechel",
    },
    "chipdb": HOME / "ofx-test" / "prefix" / "share" / "nextpnr" / "himbaechel" / "xilinx" / "chipdb-xc7a50t.bin",
    "designs": {
        "bufr": (ROOT / "build/qor/hold/src/bufr_keepbuf.json",
                 ROOT / "designs/gap/bufr/arty_a7_35t.xdc", "bufr", 10),
        "rv_soc": (ROOT / "build/qor/synth/rv_soc/69e28e77cdb928ff/qor_rv_soc.json",
                   ROOT / "build/qor/src/rv_soc_p5/constraints.xdc", "qor_rv_soc", 5),
        "bram": (ROOT / "build/qor/synth/bram/fb77231b9c561b55/qor_bram.json",
                 ROOT / "build/qor/src/bram_p5/constraints.xdc", "qor_bram", 5),
    },
    "base_args": ["--device", "xc7a35tcsg324-1", "--seed", "1", "-o", "dsp-cascade-place"],
    "variants": {
        "hold_rel": {"bin": "release", "args": ["--timing-allow-fail"]},
        "hold_off": {"bin": "hold", "args": ["--timing-allow-fail"]},
        "hold_relfix": {"bin": "release", "args": ["-o", "hold-fix"]},
        "hold_fix": {"bin": "hold", "args": ["-o", "hold-fix"]},
        "hold_up": {"bin": "hold", "args": ["-o", "hold-fix", "-o", "hold-fix-upstream"]},
        "hold_ms": {"bin": "hold", "args": ["--timing-allow-fail", "-o", "route-min-scale=0.39"]},
        "hold_msfix": {"bin": "hold", "args": ["-o", "route-min-scale=0.39", "-o", "hold-fix", "-o", "hold-fix-upstream"]},
    },
    "vivado_root": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/xroute"),
}


def run_dir(design, vname):
    return CONFIG["oxc7"] / vname / f"{design}_{qor_bench.ptag(CONFIG['designs'][design][3])}" / "s1"


def pnr(design, vname, dry):
    js, xdc, top, period = CONFIG["designs"][design]
    v = CONFIG["variants"][vname]
    binary = CONFIG["binaries"][v["bin"]]
    out = run_dir(design, vname)
    cmd = [str(binary), "--chipdb", str(CONFIG["chipdb"])] + CONFIG["base_args"] + [
        "--json", str(js), "-o", f"xdc={xdc}", "--freq", f"{1000.0 / period:g}"] + v["args"] + [
        "--write", str(out / f"{top}_routed.json"), "-o", f"fasm={out / (top + '.fasm')}", "--report",
        str(out / "report.json")]
    st = out / "status.json"
    if st.exists() and json.loads(st.read_text()).get("cmd") == cmd:
        return json.loads(st.read_text())
    if dry:
        print(f"[dry] {' '.join(cmd)}")
        return {}
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(binary), OFX_MAX_NEXTPNR=str(CONFIG["max_nextpnr"]))
    with open(out / "nextpnr.log", "w") as lf:
        rc = subprocess.run([str(CONFIG["npwait"])] + cmd[1:], stdout=lf, stderr=subprocess.STDOUT, env=env,
                            cwd=str(out)).returncode
    rec = {"design": design, "variant": vname, "cmd": cmd, "rc": rc, "pnr": {"ok": (out / f"{top}.fasm").exists()},
           "hold": hold_summary(out / "nextpnr.log")}
    st.write_text(json.dumps(rec, indent=1) + "\n")
    print(f"[run] {design} {vname}: rc {rc} {rec['hold']}", flush=True)
    return rec


def hold_summary(log):
    t = log.read_text(errors="replace") if log.exists() else ""
    mins = re.findall(r"Min delay \(hold\) for (.*?) \(worst at .*?\): (-?[0-9.]+) ns", t)
    fix = re.findall(r"Hold-fix(?: pass \d+)?: (.*)", t)
    return {"last_min_delay": mins[-1] if mins else None, "holdfix": fix[-3:],
            "errors": len(re.findall(r"^ERROR:", t, re.M))}


def fasm_body(p):
    return sorted(ln for ln in Path(p).read_text().splitlines() if not ln.startswith("#"))


def xroute_names(design, vname, dry):
    js, xdc, top, period = CONFIG["designs"][design]
    xroute.CONFIG["designs"][design] = (vname, 1, period, top, str(xdc.relative_to(ROOT)) if str(xdc).startswith(str(ROOT)) else str(xdc))
    npr = xroute.rerun_nextpnr(design, "cal", dry)
    if not dry:
        xroute.export(design, npr, dry, "cal")
    return xroute.name_of(design, "cal")


def vivado(name):
    d = CONFIG["vivado_root"] / name
    tr = d / "timing.rpt"
    if not tr.exists():
        return None
    m = re.search(r"WNS\(ns\).*?\n[- ]+\n\s*(-?[0-9.]+)\s+(-?[0-9.]+)\s+(\d+)\s+(\d+)\s+(-?[0-9.]+)\s+(-?[0-9.]+)\s+(\d+)",
                  tr.read_text(errors="replace"))
    return {"wns": float(m.group(1)), "whs": float(m.group(5)), "hold_failing": int(m.group(7))} if m else {"error": "parse"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--designs", nargs="+", default=list(CONFIG["designs"]))
    ap.add_argument("--variants", nargs="+", default=list(CONFIG["variants"]))
    for f in ("pnr", "noop", "xprep", "report", "run"):
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    rows = []
    for d in a.designs:
        top = CONFIG["designs"][d][2]
        if a.noop:
            fa, fb = run_dir(d, "hold_rel") / f"{top}.fasm", run_dir(d, "hold_off") / f"{top}.fasm"
            same = fa.exists() and fb.exists() and fasm_body(fa) == fasm_body(fb)
            print(f"{d}: hold binary without options vs release: fasm {'IDENTICAL' if same else 'DIFFER'}")
        for v in a.variants:
            if a.pnr:
                pnr(d, v, dry)
            if a.xprep:
                print(f"{d} {v}: vivado name {xroute_names(d, v, dry)}")
            if a.report:
                st = run_dir(d, v) / "status.json"
                rec = json.loads(st.read_text()) if st.exists() else {}
                name = f"{d}_{qor_bench.ptag(CONFIG['designs'][d][3])}_{v}_s1"
                rows.append({"design": d, "variant": v, "rc": rec.get("rc"), "nextpnr": rec.get("hold"),
                             "vivado": vivado(name), "vivado_name": name})
    if a.report:
        CONFIG["out"].mkdir(parents=True, exist_ok=True)
        (CONFIG["out"] / "report.json").write_text(json.dumps(rows, indent=1) + "\n")
        for r in rows:
            print(json.dumps(r))


if __name__ == "__main__":
    main()
