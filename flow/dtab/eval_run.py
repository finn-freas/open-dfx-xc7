"""Re-run existing placements (same command, nextpnr-dtab binary, --no-route) with -o dtab-eval: the worst setup slack
of the final placement under each arc model. usage: eval_run.py TABLE VARIANT... [--seeds 1,2,3] [--extra '-o ...']"""
import argparse, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

R = Path("/home/finnf/open-dfx-xc7")
BIN = R / "build/nextpnr-build/dtab/nextpnr-himbaechel"
OUT = R / "build/dtab/eval"
DES = ("rv_soc", "bram", "rv_big", "rv_mul")


def job(table, v, d, s, extra, tag):
    vv = f"{v}_dq" if d == "rv_mul" else v
    st = R / "build/qor/oxc7" / vv / f"{d}_p5" / f"s{s}" / "status.json"
    if not st.exists():
        return None
    log = OUT / f"{tag}{vv}_{d}_s{s}.log"
    if log.exists() and "dtab-eval: dtab-nofo" in log.read_text(errors="ignore"):
        return log
    cmd = json.loads(st.read_text())["cmd"]
    args, k = [], 1
    while k < len(cmd):
        if cmd[k] in ("--write", "--report"):
            k += 2
            continue
        if cmd[k] == "-o" and cmd[k + 1].startswith("fasm="):
            k += 2
            continue
        args.append(cmd[k])
        k += 1
    args += ["--no-route", "-o", f"dtab={table}", "-o", "dtab-eval"] + extra
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(BIN), OFX_MAX_NEXTPNR="4")
    with open(log, "w") as f:
        subprocess.run([str(R / "ofx/npwait.sh")] + args, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=str(OUT))
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("table")
    ap.add_argument("variants", nargs="+")
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--designs", default=",".join(DES))
    ap.add_argument("--extra", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("-j", type=int, default=2)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(a.table, v, d, int(s), a.extra.split(), a.tag) for v in a.variants for d in a.designs.split(",")
            for s in a.seeds.split(",")]
    with ThreadPoolExecutor(a.j) as ex:
        for r in ex.map(lambda j: job(*j), jobs):
            print(r, flush=True)


if __name__ == "__main__":
    main()
