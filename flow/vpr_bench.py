"""VPR as placer, timed by Vivado. Per design: export the stub-baseline netlist (pl14_off_stub, same yosys netlist) to
VPR (flow/vpr_export.py), pack + place it per seed (flow/vpr_run.sh), map the placement to nextpnr bels
(flow/vpr_import.py), let nextpnr bind it locked (-o place-import) and place/route the rest, then export the exact
implementation for Vivado (flow/exact_src.py; variant "vpr_imp", "vpr_imp_<tag>" with --tag).
Vivado: flow/rte_dump_vivado.sh.
usage: vpr_bench.py [--designs ...] [--seeds ...] [--tag hi] [--stage export|vpr|import|npr|exact|all]"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb
import qor_bench

ROOT = qor_bench.ROOT
CONFIG = {
    "base": "pl14_off_stub",
    "variant": "vpr_imp",
    "out": ROOT / "build" / "vpr",
    "nextpnr": ROOT / "build" / "nextpnr-build" / "rte-run" / "nextpnr-himbaechel",
    "max_nextpnr": 2,
    "designs": ["rv_soc", "bram", "rv_big"],
    "seeds": [1, 2, 3],
    "tag": "",
    "tags": {"hi": "--inner_num 5"},
}


def sdir(design, seed):
    t = CONFIG["tag"]
    return CONFIG["out"] / design / (f"{t}_s{seed}" if t else f"s{seed}")


def variant():
    return CONFIG["variant"] + (f"_{CONFIG['tag']}" if CONFIG["tag"] else "")


def base_cmd(design):
    st = json.loads((pb.run_dir(design, 5, CONFIG["base"], 1) / "status.json").read_text())
    return st["cmd"]


def arg(cmd, k):
    return cmd[cmd.index(k) + 1]


def export(design):
    cmd = base_cmd(design)
    top = qor_bench.CONFIG["designs"][design]["top"]
    xdc = next(c[4:] for c in cmd if c.startswith("xdc="))
    out = CONFIG["out"] / design
    if (out / "design.eblif").exists():
        return
    subprocess.run([sys.executable, str(ROOT / "flow" / "vpr_export.py"), arg(cmd, "--json"), top, xdc, str(out)],
                   check=True)


def vpr(design, seeds):
    env = dict(os.environ)
    if CONFIG["tag"]:
        env.update(VPR_TAG=CONFIG["tag"], VPR_PLACE_OPTS=CONFIG["tags"][CONFIG["tag"]])
    subprocess.run([str(ROOT / "flow" / "vpr_run.sh"), str(CONFIG["out"] / design)] + [str(s) for s in seeds],
                   check=True, env=env)


def do_import(design, seed):
    d = CONFIG["out"] / design
    sd = sdir(design, seed)
    (sd / "design.net").unlink(missing_ok=True)
    os.symlink(d / "design.net", sd / "design.net")
    (sd / "vpr.json").unlink(missing_ok=True)
    os.symlink(d / "vpr.json", sd / "vpr.json")
    top = qor_bench.CONFIG["designs"][design]["top"]
    ref = pb.run_dir(design, 5, CONFIG["base"], 1) / f"{top}_routed.json"
    r = subprocess.run([sys.executable, str(ROOT / "flow" / "vpr_import.py"), str(sd), str(sd / "import.txt"), str(ref)],
                       check=True, capture_output=True, text=True)
    (sd / "import.log").write_text(r.stdout)
    print(design, seed, r.stdout.strip())


def npr(design, seed):
    cmd0 = base_cmd(design)
    top = qor_bench.CONFIG["designs"][design]["top"]
    out = pb.run_dir(design, 5, variant(), seed)
    out.mkdir(parents=True, exist_ok=True)
    imp = sdir(design, seed) / "import.txt"
    keep = cmd0[1:cmd0.index("--write")]
    keep[keep.index("--seed") + 1] = str(seed)
    cmd = [str(CONFIG["nextpnr"])] + keep + ["-o", f"place-import={imp}", "--write", str(out / f"{top}_routed.json"),
                                              "--report", str(out / "report.json")]
    (out / "npwait.log").unlink(missing_ok=True)
    os.environ.update(OFX_NEXTPNR_BIN=cmd[0], OFX_MAX_NEXTPNR=str(CONFIG["max_nextpnr"]),
                      OFX_NPWAIT_LOG=str(out / "npwait.log"))
    rc, secs = qor_bench.run_logged([str(ROOT / "ofx" / "npwait.sh")] + cmd[1:], out / "nextpnr.log", out)
    log = (out / "nextpnr.log").read_text(errors="replace")
    m = re.search(r"place-import: .*", log)
    rec = {"design": design, "period_ns": 5, "variant": variant(), "seed": seed, "cmd": cmd,
           "pnr": {"ok": rc == 0, "rc": rc, "seconds": secs, "log": str((out / "nextpnr.log").relative_to(ROOT))},
           "import": m.group(0) if m else None, "result": pb.parse_clock(out / "nextpnr.log", "sys_clk")}
    (out / "status.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(design, seed, "nextpnr rc", rc, secs, "s;", rec["import"])


def exact(design, seed):
    subprocess.run([sys.executable, str(ROOT / "flow" / "exact_src.py"), design, variant(), str(seed), "--run"],
                   check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", default=CONFIG["designs"])
    ap.add_argument("--seeds", nargs="+", type=int, default=CONFIG["seeds"])
    ap.add_argument("--stage", default="all")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    CONFIG["tag"] = a.tag
    st = a.stage
    for d in a.designs:
        if st in ("export", "all"):
            export(d)
        if st in ("vpr", "all"):
            vpr(d, a.seeds)
        for s in a.seeds:
            if st in ("import", "all"):
                do_import(d, s)
            if st in ("npr", "all"):
                npr(d, s)
            if st in ("exact", "all"):
                exact(d, s)


if __name__ == "__main__":
    main()
