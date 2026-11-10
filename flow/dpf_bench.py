"""DREAMPlaceFPGA as an external global placer for nextpnr (docs/dreamplace-eval.md).

Per design and seed:
  1. nextpnr (build dpf) --placer-static-gp-dump: the static placer's global-placement problem (once per design).
  2. flow/dpf_bridge.py export -> Bookshelf; DREAMPlaceFPGA (toolchain/dreamplacefpga, CPU) global placement only.
  3. flow/dpf_bridge.py import -> nextpnr --placer-static-gp-import: nextpnr legalises, refines and routes.
  4. --xprep: flow/exact_src.py (exact import of the nextpnr implementation), then
     RTE_OUT=.../build/exact RTE_ROUTE_DUMP=0 SRC=.../designs/exact flow/rte_dump_vivado.sh --run NAME: Vivado routes, times.
usage: python3 flow/dpf_bench.py [--run] [--designs ...] [--seeds ...] [--variant pl_dpf_wl] [--xprep] [--report]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb

ROOT = pb.ROOT
DPF = ROOT / "toolchain" / "dreamplacefpga"
OUT = ROOT / "build" / "dpf"
pb.CONFIG["binaries"]["dpf"] = "build/nextpnr-build/dpf/nextpnr-himbaechel"

VARIANTS = {
    "pl_dpf_wl": {"dpf": {"routability_opt_flag": 1}, "nextpnr": []},
    "pl_dpf_nr": {"dpf": {"routability_opt_flag": 0}, "nextpnr": []},
    "pl_dpf_warm": {"dpf": {"routability_opt_flag": 1}, "nextpnr": ["--placer-static-gp-import-warm"], "gp": "pl_dpf_wl"},
    "pl_dpf_td": {"dpf": {"routability_opt_flag": 1, "timing_driven_flag": 1}, "nextpnr": [], "timing": True},
    "pl_dpf_td_warm": {"dpf": {}, "nextpnr": ["--placer-static-gp-import-warm"], "gp": "pl_dpf_td"},
}


def pow2(n):
    p = 16
    while p < n:
        p *= 2
    return p


def run(cmd, log, cwd=None, env=None):
    t0 = time.time()
    with open(log, "w") as f:
        rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=cwd, env=env).returncode
    return rc, round(time.time() - t0, 2)


def dump(design, dry):
    d = OUT / "dump" / design
    if (d / "gp.dump").exists():
        return d / "gp.dump"
    if dry:
        print(f"[dry] dump {design}")
        return d / "gp.dump"
    st = json.loads((pb.run_dir(design, 5, "pl14_off_stub", 1) / "status.json").read_text())
    cmd, i, src = [], 0, st["cmd"][1:]
    while i < len(src):
        if src[i] in ("--write", "--report") or (src[i] == "-o" and src[i + 1].startswith("fasm=")):
            i += 2
            continue
        cmd.append(src[i])
        i += 1
    d.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(ROOT / pb.CONFIG["binaries"]["dpf"]), OFX_MAX_NEXTPNR="3")
    run([str(ROOT / "ofx" / "npwait.sh")] + cmd + ["--placer-static-gp-dump", str(d / "gp.dump"), "--no-route"],
        d / "nextpnr.log", env=env)
    return d / "gp.dump"


def bookshelf(design, dry):
    bk = OUT / "bk" / design
    if (bk / "design.aux").exists() or dry:
        return bk
    subprocess.run([sys.executable, str(ROOT / "flow" / "dpf_bridge.py"), "export", str(dump(design, dry)), str(bk)],
                   check=True)
    return bk


def dreamplace(design, vname, seed, dry):
    vname = VARIANTS[vname].get("gp", vname)
    bk = bookshelf(design, dry)
    rd = OUT / "gp" / vname / design / f"s{seed}"
    gp = rd / "gp.txt"
    if gp.exists():
        return gp
    if dry:
        print(f"[dry] dreamplace {design} {vname} s{seed}")
        return gp
    ex = json.loads((bk / "export.json").read_text())
    bx, by = pow2(ex["W"]), pow2(ex["H"])
    cfg = {"aux_input": str(bk / "design.aux"), "gpu": 0, "num_threads": 4, "num_bins_x": bx, "num_bins_y": by,
           "global_place_stages": [{"num_bins_x": bx, "num_bins_y": by, "iteration": 2000, "learning_rate": 0.01,
                                    "wirelength": "weighted_average", "optimizer": "nesterov"}],
           "route_num_bins_x": bx, "route_num_bins_y": by,
           "target_density": 1.0, "density_weight": 8e-5, "random_seed": 1000 + seed, "scale_factor": 1.0,
           "global_place_flag": 1, "legalize_flag": 0, "detailed_place_flag": 0, "dtype": "float32",
           "deterministic_flag": 1, "enable_if": 0, "result_dir": str(rd / "results")}
    cfg.update(VARIANTS[vname]["dpf"])
    if VARIANTS[vname].get("timing"):
        cfg.update({"timing_file_dir": str(OUT / "timing7"), "timing_constraint": 5000})
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "params.json").write_text(json.dumps(cfg, indent=1) + "\n")
    env = dict(os.environ, OMP_NUM_THREADS="4")
    rc, secs = run([str(DPF / "env" / "bin" / "python"), str(DPF / "install" / "dreamplacefpga" / "Placer.py"),
                    str(rd / "params.json")], rd / "dreamplace.log", cwd=rd, env=env)
    pl = rd / "results" / "design" / "design.gp.pl"
    info = {"rc": rc, "seconds": secs}
    if rc == 0 and pl.exists():
        subprocess.run([sys.executable, str(ROOT / "flow" / "dpf_bridge.py"), "import", str(bk / "map.json"), str(pl),
                        str(gp)], check=True)
    (rd / "run.json").write_text(json.dumps(info) + "\n")
    return gp


def nextpnr(design, vname, seed, dry):
    gp = dreamplace(design, vname, seed, dry)
    if not dry and not gp.exists():
        print(f"  {design} {vname} s{seed}: no DREAMPlace result")
        return None
    pb.CONFIG["variants"][vname] = {"bin": "dpf", "args": pb.TMG + ["--placer-static-gp-import", str(gp)] +
                                    VARIANTS[vname]["nextpnr"]}
    return pb.pnr_one(design, 5, vname, seed, dry)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--designs", nargs="+", default=["rv_soc", "bram", "rv_big"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--variant", default="pl_dpf_wl")
    ap.add_argument("--xprep", action="store_true")
    a = ap.parse_args()
    dry = not a.run
    pb.CONFIG["seeds"] = a.seeds
    names = []
    for design in a.designs:
        for s in a.seeds:
            if a.xprep:
                subprocess.run([sys.executable, str(ROOT / "flow" / "exact_src.py"), design, a.variant, str(s)] +
                               ([] if dry else ["--run"]), check=True)
                names.append(f"{design}_p5_{a.variant}_s{s}_exact")
                continue
            r = nextpnr(design, a.variant, s, dry)
            if r and not dry:
                print(f"  {design} {a.variant} s{s}: {r.get('result', {}).get('fmax')} MHz (nextpnr timer) "
                      f"{r.get('pnr', {}).get('seconds')} s {r.get('pnr', {}).get('error', '')}", flush=True)
    if names:
        print("names: " + " ".join(names))


if __name__ == "__main__":
    main()
