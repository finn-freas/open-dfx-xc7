import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_xtime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ofx import timing

CONFIG = {
    "dry_run": True,
    "out": ROOT / "build" / "timing",
    "xtime_src": ROOT / "build" / "timing" / "xtime" / "src",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "chipdb": ROOT / "toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin",
    "part": "xc7a35tcsg324-1",
    "seed": 1,
    "report_paths": 10,
    "npr_args": ["--timing-allow-fail"],
    "binaries": {
        "xdc2": ROOT / "build/nextpnr-build/xdc2/nextpnr-himbaechel",
        "timrep": ROOT / "build/nextpnr-build/timrep/nextpnr-himbaechel",
    },
    "release_binaries": {
        "xdc2": ROOT / "build/nextpnr-build/rel01/nextpnr-himbaechel",
        "timrep": ROOT / "build/nextpnr-build/rel01tr/nextpnr-himbaechel",
    },
    "release_args": ["-o", "hardblock-timing"],
    "variants": {
        "xdc2": ("xdc2", False),
        "timrep": ("timrep", False),
        "timrep_paths": ("timrep", True),
    },
    "new_keys": ("clocks", "endpoints", "paths"),
    "fasm_version": "# nextpnr-himbaechel ",
    "designs": {
        "blinky": {"json": "build/xdc_noop/blinky/xdc2/blinky.json", "xdc": "designs/blinky/arty_a7_35t.xdc",
                   "top": "blinky", "freq": 100, "vivado": False},
        "rv_soc": {"json": "build/qor/synth/rv_soc/69e28e77cdb928ff/qor_rv_soc.json",
                   "xdc": "build/qor/src/rv_soc_p5/constraints.xdc", "top": "qor_rv_soc", "freq": 200, "vivado": True},
        "x_mmcm_none": {"json": "build/xdc/x_mmcm_none/xdc2/x_mmcm_none.json",
                        "xdc": "designs/xdc/x_mmcm_none/x_mmcm_none.xdc", "top": "x_mmcm_none", "freq": 100,
                        "vivado": True},
        "x_iodly": {"json": "build/xdc/x_iodly/xdc2/x_iodly.json", "xdc": "designs/xdc/x_iodly/x_iodly.xdc",
                    "top": "x_iodly", "freq": 100, "vivado": True},
        "x_gen_none": {"json": "build/xdc/x_gen_none/xdc2/x_gen_none.json",
                       "xdc": "designs/xdc/x_gen_none/x_gen_none.xdc", "top": "x_gen_none", "freq": 100,
                       "vivado": True},
        "rv_mul": {"json": "build/qor/synth/rv_mul/dc7ff3318d25ef8d/qor_rv_mul.json",
                   "xdc": "build/qor/src/rv_mul_p5/constraints.xdc", "top": "qor_rv_mul", "freq": 200, "vivado": True},
        "rv_mul_hb": {"json": "build/qor/synth/rv_mul/dc7ff3318d25ef8d/qor_rv_mul.json",
                      "xdc": "build/qor/src/rv_mul_p5/constraints.xdc", "top": "qor_rv_mul", "freq": 200,
                      "vivado": True, "release": True},
        "rv_soc_hb": {"json": "build/qor/synth/rv_soc/69e28e77cdb928ff/qor_rv_soc.json",
                      "xdc": "build/qor/src/rv_soc_p5/constraints.xdc", "top": "qor_rv_soc", "freq": 200,
                      "vivado": True, "release": True},
        "dfx_rv_pr_xor_n": {"json": "build/timing/dfx_rv_pr/rel01tr_p10/rel01tr/cfg_xor_linked.json",
                            "xdc": "build/timing/dfx_rv_pr/rel01tr_p10/rel01tr/replay.xdc", "top": "rv_soc",
                            "vivado": True, "run": "build/timing/dfx_rv_pr/rel01tr_p10/rel01tr/xor_n"},
        **{n: {"json": f"build/xdc/{n}/xdc2/{n}.json", "xdc": f"designs/xdc/{n}/{n}.xdc", "top": n, "freq": 100,
               "vivado": True}
           for n in ("x_cdc_none", "x_cdc_groups", "x_cdc_fpclk", "x_cdc_maxdly", "x_async_rtl", "x_async_none",
                     "x_iodly_minmax", "x_mmcm_groups", "x_gen_div")},
        "x_iodly_partial": {"json": "build/xdc/x_iodly_minmax/xdc2/x_iodly_minmax.json",
                            "xdc": "designs/timing/x_iodly_partial.xdc", "top": "x_iodly_minmax", "freq": 100,
                            "vivado": True},
    },
}


def pnr(name, d, variant, dry):
    binary, with_paths = CONFIG["variants"][variant]
    out = CONFIG["out"] / name / variant
    top = d["top"]
    fasm = out / f"{top}.fasm"
    cmd = [str(CONFIG["npwait"]), "--chipdb", str(CONFIG["chipdb"]), "--device", CONFIG["part"],
           "--json", str(ROOT / d["json"]), "-o", f"xdc={ROOT / d['xdc']}", "--seed", str(CONFIG["seed"]),
           "--freq", str(d["freq"]), "--write", str(out / f"{top}_routed.json"), "-o", f"fasm={fasm}",
           "--report", str(out / "report.json")] + CONFIG["npr_args"]
    if with_paths:
        cmd += ["--report-paths", str(CONFIG["report_paths"])]
    binaries = CONFIG["release_binaries" if d.get("release") else "binaries"]
    cmd += CONFIG["release_args"] if d.get("release") else []
    if fasm.exists():
        print(f"[skip] {name}/{variant}: {fasm.name} exists")
        return out
    print(f"[{'dry' if dry else 'run'}] {name}/{variant}: {' '.join(cmd)}")
    if dry:
        return out
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(binaries[binary]))
    with open(out / "nextpnr.log", "w") as f:
        rc = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
    (out / "status.json").write_text(json.dumps({"rc": rc, "cmd": cmd, "binary": str(binaries[binary])},
                                                indent=1) + "\n")
    if rc:
        print(f"FAIL {name}/{variant}: rc {rc}, {out / 'nextpnr.log'}")
    return out


def strip_version(text):
    return "\n".join(ln for ln in text.splitlines() if not ln.startswith(CONFIG["fasm_version"]))


def noop(name, d):
    top = d["top"]
    dirs = {v: CONFIG["out"] / name / v for v in CONFIG["variants"]}
    if not all((x / f"{top}.fasm").exists() for x in dirs.values()):
        return {"design": name, "done": False}
    fasm = {v: strip_version((x / f"{top}.fasm").read_text()) for v, x in dirs.items()}
    rep = {v: json.loads((x / "report.json").read_text()) for v, x in dirs.items()}
    stripped = {k: v for k, v in rep["timrep_paths"].items() if k not in CONFIG["new_keys"]}
    return {"design": name, "done": True,
            "fasm_timrep_eq_xdc2": fasm["timrep"] == fasm["xdc2"],
            "fasm_paths_eq_xdc2": fasm["timrep_paths"] == fasm["xdc2"],
            "report_timrep_eq_xdc2": rep["timrep"] == rep["xdc2"],
            "report_paths_old_keys_eq_xdc2": stripped == rep["xdc2"],
            "new_keys": sorted(k for k in rep["timrep_paths"] if k in CONFIG["new_keys"]),
            "endpoints": len(rep["timrep_paths"].get("endpoints", [])),
            "paths": len(rep["timrep_paths"].get("paths", []))}


def xtime_prep(name, d, dry):
    run = ROOT / d["run"] if d.get("run") else CONFIG["out"] / name / "timrep_paths"
    src = CONFIG["xtime_src"] / f"{name}_tr_placed"
    if dry:
        print(f"[dry] xtime source {src}")
        return src.name
    src.mkdir(parents=True, exist_ok=True)
    qor_xtime.write_netlist(ROOT / d["json"], src / "netlist.edf", dry)
    (src / "top.txt").write_text(d["top"] + "\n")
    (src / "mode.txt").write_text("placed\n")
    (src / "constraints.xdc").write_text((ROOT / d["xdc"]).read_text())
    rows, skipped = qor_xtime.placement(run / f"{d['top']}_routed.json")
    (src / "place.txt").write_text("".join(f"{qor_xtime.tcl_quote(n)} {b}\n" for n, b in rows))
    (src / "endpoints.flag").write_text("dump every setup and hold endpoint\n")
    (src / "place_info.json").write_text(json.dumps({"rows": len(rows), "skipped": skipped, "from": str(run)}) + "\n")
    rep = json.loads((run / "report.json").read_text())
    paths = sorted((p for p in rep.get("paths", []) if p["check"] == "setup"), key=lambda p: p["slack"])
    (src / "paths.txt").write_text("".join(
        f"{qor_xtime.tcl_quote(timing.path_start(p)['cell'])} {timing.path_start(p)['port']} "
        f"{qor_xtime.tcl_quote(p['endpoint']['cell'])} {p['endpoint']['port']} {p['slack']:.3f}\n" for p in paths))
    return src.name


def main():
    ap = argparse.ArgumentParser(description="nextpnr --report-paths: no-op check against xdc2, and the Vivado "
                                             "(qor_xtime method) sources for the timing-report comparison")
    ap.add_argument("--designs", nargs="+", default=list(CONFIG["designs"]))
    ap.add_argument("--out", type=Path, help="output root (default build/timing); a fresh one re-runs every build")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.out:
        CONFIG["out"] = a.out.resolve()
        CONFIG["xtime_src"] = CONFIG["out"] / "xtime" / "src"
    dry = CONFIG["dry_run"] and not a.run
    results, names = [], []
    for name in a.designs:
        d = CONFIG["designs"][name]
        for v in CONFIG["variants"] if not d.get("run") else ():
            pnr(name, d, v, dry)
        if not dry and not d.get("run"):
            results.append(noop(name, d))
        if not dry and d["vivado"]:
            names.append(xtime_prep(name, d, dry))
    for r in results:
        print(json.dumps(r))
    if not dry and results:
        (CONFIG["out"] / "noop.json").write_text(json.dumps(results, indent=1) + "\n")
    print("vivado: vivado/run_qor.ps1 -Tag timing_xtime -Script build_xtime.tcl -SrcRel build\\timing\\xtime\\src "
          f"-Names {','.join(names)} -Run")


if __name__ == "__main__":
    main()
