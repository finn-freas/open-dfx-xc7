"""LUT-pin experiments (docs/wip/router.md): nextpnr runs of the dp0 command with another binary, chipdb and extra
options, written where flow/exact_src.py finds them (build/qor/oxc7/<variant>/<design>_p5/s<seed>).

  lpa_bench.py --variants lp0 lpA --designs rv_soc bram --seeds 1 2 3 [--run]
"""
import argparse
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "build" / "nextpnr-build"
CONFIG = {
    "base_variant": "dp0",
    "max_parallel": 3,
    "variants": {
        "lp0": {"bin": NB / "lpa" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal-a6/chipdb-xc7a50t.bin", "args": []},
        "lpA": {"bin": NB / "lpa" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal-a6/chipdb-xc7a50t.bin",
                "args": ["-o", "lut-a6-perm"]},
        "lpB": {"bin": NB / "lpa" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal-a6pd/chipdb-xc7a50t.bin", "args": []},
        "lpAB": {"bin": NB / "lpa" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal-a6pd/chipdb-xc7a50t.bin",
                 "args": ["-o", "lut-a6-perm"]},
        "lpX": {"bin": NB / "lpb" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal/on/chipdb-xc7a50t.bin",
                "args": ["-o", "lut6-first"]},
        "lpXAB": {"bin": NB / "lpb" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal-a6pd/chipdb-xc7a50t.bin",
                  "args": ["-o", "lut6-first", "-o", "lut-a6-perm"]},
        "lpX2AB": {"bin": NB / "lpc" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal-a6pd/chipdb-xc7a50t.bin",
                   "args": ["-o", "lut6-first=2", "-o", "lut-a6-perm"]},
        "lpX0": {"bin": NB / "lpb" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal/on/chipdb-xc7a50t.bin", "args": []},
        "lpR": {"bin": NB / "lpa" / "nextpnr-himbaechel", "chipdb": ROOT / "build/chipdb-rcal/on/chipdb-xc7a50t.bin", "args": []},
    },
}


def rdir(v, d, s):
    return ROOT / "build" / "qor" / "oxc7" / v / f"{d}_p5" / f"s{s}"


def one(v, d, s, dry):
    out = rdir(v, d, s)
    if (out / "status.json").exists():
        return f"[cached] {out}"
    st = json.loads((rdir(CONFIG["base_variant"], d, s) / "status.json").read_text())
    cmd = list(st["cmd"])
    spec = CONFIG["variants"][v]
    cmd[0] = str(spec["bin"])
    cmd[cmd.index("--chipdb") + 1] = str(spec["chipdb"])
    old = str(rdir(CONFIG["base_variant"], d, s))
    cmd = [c.replace(old, str(out)) for c in cmd] + spec["args"]
    if dry:
        return "[dry] " + " ".join(cmd)
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OFX_NEXTPNR_BIN=cmd[0], OFX_MAX_NEXTPNR="3")
    with open(out / "nextpnr.log", "w") as lf:
        rc = subprocess.run([str(ROOT / "ofx" / "npwait.sh")] + cmd[1:], stdout=lf, stderr=subprocess.STDOUT, env=env).returncode
    st2 = dict(st, cmd=cmd, variant=v, pnr={"rc": rc, "ok": rc == 0})
    (out / "status.json").write_text(json.dumps(st2, indent=1) + "\n")
    return f"{v} {d} s{s} rc {rc}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--designs", nargs="+", default=["rv_soc", "bram", "rv_mul", "rv_big"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    jobs = [(v, d, s) for s in a.seeds for d in a.designs for v in a.variants]
    with ThreadPoolExecutor(CONFIG["max_parallel"]) as ex:
        for r in ex.map(lambda j: one(*j, not a.run), jobs):
            print(r, flush=True)


if __name__ == "__main__":
    main()
