import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "binary": "build/nextpnr-build/corners/nextpnr-himbaechel",
    "chipdb": "build/chipdb-corners/on/chipdb-xc7a50t.bin",
    "npwait": "ofx/npwait.sh",
    "part": "xc7a35tcsg324-1",
    "variant": "xdc3",
    "out": "build/corners",
    "designs": {
        "x_iodly": ("build/xdc/x_iodly", "designs/xdc/x_iodly/x_iodly.xdc"),
        "x_iodly_minmax": ("build/xdc/x_iodly_minmax", "designs/xdc/x_iodly_minmax/x_iodly_minmax.xdc"),
        "x_iodly_fall": ("build/xdc/x_iodly_fall", "designs/xdc/x_iodly_fall/x_iodly_fall.xdc"),
        "x_mcp_from": ("build/xdc/x_mcp_from", "designs/xdc/x_mcp_from/x_mcp_from.xdc"),
        "x_mcp_thru": ("build/xdc/x_mcp_thru", "designs/xdc/x_mcp_thru/x_mcp_thru.xdc"),
        "x_maxdly_cells": ("build/xdc/x_maxdly_cells", "designs/xdc/x_maxdly_cells/x_maxdly_cells.xdc"),
        "x_maxdly_dp": ("build/xdc/x_maxdly_dp", "designs/xdc/x_maxdly_dp/x_maxdly_dp.xdc"),
        "rv_soc": ("build/xdc_noop/rv_soc", "designs/rv_soc/arty_a7_35t.xdc"),
    },
    "npr_args": ["--seed", "1", "--freq", "100", "--timing-allow-fail"],
    "vivado": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/xdc_xtime"),
    "kinds": {"setup in": "in_setup", "hold in": "in_hold", "setup out": "out_setup", "hold out": "out_hold",
              "setup reg": "reg_setup", "hold reg": "reg_hold"},
    "npr_line": re.compile(r"corner (\w+)\s+(setup|hold)\s+(in|out|reg)\s*: worst slack\s+(-?[\d.]+) ns at (\S+)"),
    "rpt_slack": re.compile(r"^Slack \([A-Z]+\)\s*:\s*(-?[\d.]+)ns", re.M),
    "dry_run": True,
}


def run_one(name, rc_scale, dry):
    src, xdc = CONFIG["designs"][name]
    base = ROOT / src / CONFIG["variant"]
    out = ROOT / CONFIG["out"] / name
    opt = "timing-corners" + (f"={rc_scale}" if rc_scale else "")
    cmd = [str(ROOT / CONFIG["npwait"]), "--chipdb", str(ROOT / CONFIG["chipdb"]), "--device", CONFIG["part"],
           "--json", str(base / f"{name}.json"), "-o", f"xdc={ROOT / xdc}", "--write", str(out / "routed.json"),
           "-o", f"fasm={out / (name + '.fasm')}", "-o", opt] + CONFIG["npr_args"]
    print(f"[{'dry' if dry else 'run'}] {' '.join(cmd)}")
    if dry:
        return
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(ROOT / CONFIG["binary"]), OFX_MAX_NEXTPNR="2")
    with open(out / "nextpnr.log", "w") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=ROOT)


def fasm_lines(path):
    return sorted(ln for ln in Path(path).read_text().splitlines() if ln and not ln.startswith("#"))


def collect(name):
    src, _ = CONFIG["designs"][name]
    out = ROOT / CONFIG["out"] / name
    rec = {"design": name}
    ours, base = out / f"{name}.fasm", ROOT / src / CONFIG["variant"] / f"{name}.fasm"
    rec["fasm_identical_to_" + CONFIG["variant"]] = (ours.exists() and base.exists() and
                                                     fasm_lines(ours) == fasm_lines(base))
    npr = {}
    log = out / "nextpnr.log"
    if log.exists():
        for m in CONFIG["npr_line"].finditer(log.read_text(errors="replace")):
            npr[(m.group(1), f"{m.group(2)} {m.group(3)}")] = (float(m.group(4)), m.group(5))
    viv = CONFIG["vivado"] / f"{name}_{CONFIG['variant']}"
    rows = []
    for corner in ("Slow", "Fast"):
        for kind, stem in CONFIG["kinds"].items():
            rpt = viv / f"{stem}_{corner.lower()}.rpt"
            v = None
            if rpt.exists():
                m = CONFIG["rpt_slack"].search(rpt.read_text(errors="replace"))
                v = float(m.group(1)) if m else None
            n = npr.get((corner, kind))
            if v is None and n is None:
                continue
            rows.append({"corner": corner, "check": kind, "nextpnr": n[0] if n else None,
                         "vivado": v, "error": round(n[0] - v, 3) if n and v is not None else None})
    rec["rows"] = rows
    return rec


def main():
    ap = argparse.ArgumentParser(description="nextpnr two-corner timing against Vivado per corner, same placement")
    ap.add_argument("names", nargs="*")
    ap.add_argument("--rc-scale", default="", help="the Fast corner's factor on the RC part of route delays")
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    names = a.names or list(CONFIG["designs"])
    if a.collect:
        recs = [collect(n) for n in names]
        out = ROOT / CONFIG["out"] / "compare.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(recs, indent=1) + "\n")
        for r in recs:
            print(f"{r['design']}: FASM identical to {CONFIG['variant']}: {r['fasm_identical_to_' + CONFIG['variant']]}")
            for row in r["rows"]:
                print(f"   {row['corner']:4} {row['check']:9} nextpnr {row['nextpnr']!s:>8}  vivado {row['vivado']!s:>8}"
                      f"  error {row['error']!s:>7}")
        return
    dry = CONFIG["dry_run"] and not a.run
    for n in names:
        run_one(n, a.rc_scale, dry)


if __name__ == "__main__":
    main()
