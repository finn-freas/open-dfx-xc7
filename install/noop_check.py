import argparse
import filecmp
import json
import os
import subprocess
import sys
import time
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "dry_run": True,
    "candidate": "build/nextpnr-build/ofx/nextpnr-himbaechel",
    "chipdb": "toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin",
    "candidate_chipdb": None,
    "candidate_db": None,
    "expected_fasm": {"CFG_CENTER_MID_X46Y32.ICAP.IN_USE"},
    "part": "xc7a35tcsg324-1",
    "out": "build/ofx_noop",
    "max_nextpnr": int(os.environ.get("OFX_MAX_NEXTPNR", 2)),
    "wait_for_builds": os.environ.get("OFX_NOOP_WAIT_BUILDS", "1") == "1",
    "npwait": Path(__file__).resolve().parent.parent / "ofx" / "npwait.sh",
    "native": [
        {"design": "rv_pr", "variant": "router", "rms": ["xor", "andn", "add", "rot", "popc", "minmax"],
         "taf": ["popc", "minmax"]},
        {"design": "rv_b", "variant": "router"},
        {"design": "rv_c", "variant": "router"},
        {"design": "rv_m", "variant": "replay"},
        {"design": "rv2", "variant": "rtkeep"},
        {"design": "rv_pp", "variant": "partpin"},
        {"design": "rv_ppa", "variant": "partpin2", "rerun_nextpnr": "build/nextpnr-build/partpin3/nextpnr-himbaechel"},
        {"design": "rv_ppt", "variant": "partpin3"},
    ],
    "stock": [
        {"design": "blinky", "ref": "build/patched/baseline/blinky_stock",
         "nextpnr": "build/nextpnr-build/stock/nextpnr-himbaechel"},
        {"design": "rv_soc", "ref": "build/patched/baseline/rv_soc_stock",
         "nextpnr": "build/nextpnr-build/stock/nextpnr-himbaechel"},
    ],
}

ROOT = CONFIG["root"]
sys.path.insert(0, str(ROOT / "flow"))


def capture_native(job):
    import build_pr_native as bpn
    cmds = []

    def run(name, out, cmd, dry, ok=(0,)):
        if name.startswith("pnr "):
            cmds.append((name[4:], cmd))
        elif not Path(out).exists():
            sys.exit(f"{job['design']}/{job['variant']}: {out} is missing; build the reference first")

    bpn.run = run
    bpn.write = lambda name, out, text, dry: None
    argv = ["build_pr_native.py", "--design", job["design"], "--variant", job["variant"], "--run"]
    if job.get("rms"):
        argv += ["--rms"] + job["rms"]
    if job.get("taf"):
        argv += ["--timing-allow-fail"] + job["taf"]
    saved = dict(bpn.CONFIG)
    sys.argv = argv
    try:
        bpn.main()
    finally:
        bpn.CONFIG.clear()
        bpn.CONFIG.update(saved)
    return cmds


def arg_of(cmd, flag):
    return cmd[cmd.index(flag) + 1]


def with_args(cmd, nextpnr, out, candidate=False):
    c = list(cmd)
    c[c.index("--nextpnr") + 1] = str(nextpnr)
    c[c.index("--out") + 1] = str(out)
    if candidate and CONFIG["candidate_chipdb"]:
        c[c.index("--chipdb") + 1] = str(ROOT / CONFIG["candidate_chipdb"])
    if candidate and CONFIG["candidate_db"]:
        c[-1:-1] = ["--db-root", str(ROOT / CONFIG["candidate_db"])]
    return c


def fasm_lines(p):
    return {l.strip() for l in Path(p).read_text().splitlines() if l.strip() and not l.startswith("#")}


def frame_bits(p):
    bits = set()
    for ln in Path(p).read_text().splitlines():
        parts = ln.split()
        if len(parts) < 2:
            continue
        for i, w in enumerate(parts[1].split(",")):
            v = int(w, 16)
            bits.update((parts[0], i, b) for b in range(32) if v >> b & 1)
    return bits


def explain(row, cand, ref):
    a, b = fasm_lines(cand.with_suffix(".fasm")), fasm_lines(ref.with_suffix(".fasm"))
    row["fasm_only_candidate"] = sorted(a - b)
    row["fasm_only_reference"] = sorted(b - a)
    if cand.exists() and cand.stat().st_size > 0:
        fa, fb = frame_bits(cand), frame_bits(ref)
        row["frame_bits_only_candidate"] = len(fa - fb)
        row["frame_bits_only_reference"] = len(fb - fa)
    return not row["fasm_only_reference"] and set(row["fasm_only_candidate"]) <= CONFIG["expected_fasm"]


def wait_for_slot():
    while True:
        n = int(subprocess.run(["pgrep", "-c", "nextpnr"], capture_output=True, text=True).stdout.strip() or 0)
        busy = CONFIG["wait_for_builds"] and subprocess.run(["pgrep", "-x", "make|ninja"], capture_output=True).returncode == 0
        if n < CONFIG["max_nextpnr"] and not busy:
            return
        time.sleep(30)


def build(cmd, out, top, dry):
    frames = out / f"{top}.frames"
    if frames.exists():
        return frames
    print(f"[{'dry' if dry else 'run'}] {' '.join(cmd)}", flush=True)
    if dry:
        return frames
    wait_for_slot()
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    gated = list(cmd)
    gated[gated.index("--nextpnr") + 1] = str(CONFIG["npwait"])
    env = dict(os.environ, OFX_NEXTPNR_BIN=arg_of(cmd, "--nextpnr"), OFX_MAX_NEXTPNR=str(CONFIG["max_nextpnr"]))
    with open(out.parent / f"{out.name}.out", "w") as f:
        r = subprocess.run(gated, stdout=f, stderr=subprocess.STDOUT, env=env)
    print(f"        {time.time() - t0:.0f}s exit {r.returncode}", flush=True)
    return frames


def compare(rows, key, top, ref_dir, cmd, ref_npnr, out, dry):
    cand = build(with_args(cmd, ROOT / CONFIG["candidate"], out / "ofx", True), out / "ofx", top, dry)
    ref = Path(ref_dir) / f"{top}.frames"
    if dry:
        return
    row = {"build": key, "ref": str(ref), "ofx": str(cand), "ofx_log": str(out / "ofx" / "nextpnr.log")}
    if not cand.with_suffix(".fasm").exists():
        row["result"] = "ofx-build-failed"
    elif cand.exists() and filecmp.cmp(cand, ref, shallow=False):
        row["result"] = "identical"
    elif explain(row, cand, ref):
        row["result"] = "expected-difference"
    else:
        rerun = build(with_args(cmd, ref_npnr, out / "ref_rerun"), out / "ref_rerun", top, dry)
        row["ref_rerun"] = str(rerun)
        row["ref_rerun_nextpnr"] = str(ref_npnr)
        same_rerun = rerun.exists() and filecmp.cmp(cand, rerun, shallow=False)
        exp_rerun = rerun.exists() and not same_rerun and explain({}, cand, rerun)
        row["result"] = "identical-to-rerun" if same_rerun else "expected-difference-to-rerun" if exp_rerun else "differs"
    print(f"{row['result']:>20}  {key}", flush=True)
    rows.append(row)


def main():
    ap = argparse.ArgumentParser(description="ofx nextpnr vs each variant's binary on the same inputs (.frames)")
    ap.add_argument("--only", nargs="+", help="design names to check")
    ap.add_argument("--candidate", default=CONFIG["candidate"], help="nextpnr binary to check")
    ap.add_argument("--candidate-chipdb", default=CONFIG["candidate_chipdb"], help="chipdb for the candidate's builds")
    ap.add_argument("--candidate-db", default=CONFIG["candidate_db"], help="prjxray-db root for the candidate's builds")
    ap.add_argument("--out", default=CONFIG["out"])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    CONFIG.update(candidate=a.candidate, candidate_chipdb=a.candidate_chipdb, candidate_db=a.candidate_db, out=a.out)
    dry = CONFIG["dry_run"] and not a.run
    out_root = ROOT / CONFIG["out"]
    rows = []
    for job in CONFIG["stock"]:
        if a.only and job["design"] not in a.only:
            continue
        ref = ROOT / job["ref"]
        top = job["design"]
        cmd = [sys.executable, str(ROOT / "flow" / "build_openxc7.py"), top, "--json", str(ref / f"{top}.json"),
               "--nextpnr", str(ROOT / job["nextpnr"]), "--chipdb", str(ROOT / CONFIG["chipdb"]), "--out", "", "--run"]
        compare(rows, f"{top}/stock", top, ref, cmd, ROOT / job["nextpnr"], out_root / f"{top}_stock", dry)
    for job in CONFIG["native"]:
        if a.only and job["design"] not in a.only:
            continue
        for name, cmd in capture_native(job):
            ref_dir = Path(arg_of(cmd, "--out"))
            top = arg_of(cmd, "--top")
            ref_npnr = ROOT / job["rerun_nextpnr"] if job.get("rerun_nextpnr") else arg_of(cmd, "--nextpnr")
            out = out_root / job["design"] / job["variant"] / name
            compare(rows, f"{job['design']}/{job['variant']}/{name}", top, ref_dir, cmd, ref_npnr, out, dry)
    if dry:
        return
    out_root.mkdir(parents=True, exist_ok=True)
    tag = "_".join(a.only) if a.only else "all"
    (out_root / f"summary_{tag}.json").write_text(json.dumps(rows, indent=1) + "\n")
    n_same = sum(r["result"] in ("identical", "identical-to-rerun") for r in rows)
    n_exp = sum(r["result"].startswith("expected-difference") for r in rows)
    n_bad = len(rows) - n_same - n_exp
    print(f"{n_same}/{len(rows)} builds give identical .frames, {n_exp} differ only by {sorted(CONFIG['expected_fasm'])}, "
          f"{n_bad} differ otherwise or failed; summary {out_root / f'summary_{tag}.json'}")
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
