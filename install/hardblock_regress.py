"""Regression evidence for making nextpnr -o hardblock-timing an ofx default.

Inputs are the flow/release_bench.py runs of two variants on the qor designs:
  rel_new      the 0.1 defaults (dsp-cascade-place, static placer, default synthesis); the timer is blind to
               DSP48E1 / ICAPE2 / RAMB36E1 pins
  rel_new_tmg  the same plus -o hardblock-timing
nextpnr's Fmax of the two is not comparable (the blind timer does not see the hard-block paths), so every rel_new
placement and routing is replayed (flow/replay_dump.py, -o preplaced / -o prerouted) with -o hardblock-timing and
timed again. The replay must give placement and routing identical to the original, otherwise the row is not used.
Checks:
  noop        designs without DSP48E1/ICAPE2/RAMB36E1 (blinky): .frames of rel_new and rel_new_tmg identical per seed
  replay      every replayed rel_new build has placement and routing identical to its original (flow/replay_dump.py
              of both routed JSONs equal; the FASM may differ in slice config bits such as NOCLKINV, reported)
  regression  per design, the mean over seeds of the honest Fmax with hardblock-timing is not below the mean honest
              Fmax of the blind placement by more than CONFIG["tolerance"]; every run made a bitstream
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "flow"))
import qor_bench as qb

CONFIG = {
    "dry_run": True,
    "prefix": Path(os.environ.get("OFX_PREFIX", Path.home() / ".local" / "ofx")),
    "bench": ROOT / "build" / "qor" / "oxc7",
    "base": "rel_new",
    "tmg": "rel_new_tmg",
    "designs": ["blinky", "rv_soc", "rv_mul", "rv_big", "bram", "fir"],
    "noop_designs": ["blinky"],
    "period_ns": 5,
    "seeds": [1, 2, 3],
    "tolerance": 0.02,
    "out": ROOT / "build" / "hardblock_regress",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "max_nextpnr": int(os.environ.get("OFX_MAX_NEXTPNR", 2)),
}


def run_dir(variant, design, seed):
    return CONFIG["bench"] / variant / f"{design}_p{CONFIG['period_ns']}" / f"s{seed}"


def status(d):
    f = d / "status.json"
    return json.loads(f.read_text()) if f.exists() else None


def fasm_lines(p):
    return [l for l in Path(p).read_text().splitlines() if l.strip() and not l.startswith("#")] if Path(p).exists() else None


def arg_after(cmd, flag):
    return cmd[cmd.index(flag) + 1]


def opt_value(cmd, key):
    for i, c in enumerate(cmd):
        if c == "-o" and cmd[i + 1].startswith(key + "="):
            return cmd[i + 1].split("=", 1)[1]
    return None


def dump(f):
    return Path(f).read_text() if Path(f).exists() else None


def routes(f):
    """net -> set of (wire, pip); the strength field is dropped (a replayed route comes back locked)"""
    if not Path(f).exists():
        return None
    out = {}
    for line in Path(f).read_text().splitlines():
        net, _, r = line.partition("	")
        x = r.split(";")
        out[net] = {(x[i], x[i + 1]) for i in range(0, len(x) - 2, 3)}
    return out


def replay(design, seed, dry):
    src = run_dir(CONFIG["base"], design, seed)
    st = status(src)
    out = CONFIG["out"] / f"{design}_s{seed}"
    rec = {"design": design, "seed": seed, "src": str(src)}
    if not st or not st.get("pnr", {}).get("ok"):
        rec["error"] = f"no finished {CONFIG['base']} run in {src}"
        return rec
    cmd = st["cmd"]
    top = Path(arg_after(cmd, "--write")).name[:-len("_routed.json")]
    rec["blind_fmax"] = st.get("result", {}).get("fmax")
    ref = out / "ref"
    done = out / "result.json"
    if done.exists():
        old = json.loads(done.read_text())
        if old.get("src_key") == st.get("key") and "place_route_identical" in old:
            return old
    if dry:
        print(f"[dry] replay {design} s{seed}: replay_dump {src}/{top}_routed.json; nextpnr {' '.join(cmd[1:6])} ... "
              f"-o hardblock-timing -o preplaced -o prerouted")
        return rec
    out.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(ROOT / "flow" / "replay_dump.py"), str(src / f"{top}_routed.json"), str(ref)],
                       stdout=open(out / "replay_dump.log", "w"), stderr=subprocess.STDOUT)
    if r.returncode:
        rec["error"] = f"replay_dump exit {r.returncode} ({out / 'replay_dump.log'})"
        return rec
    xdc = out / "replay.xdc"
    loc = Path(str(ref) + ".loc.xdc")
    xdc.write_text(Path(opt_value(cmd, "xdc")).read_text() + (loc.read_text() if loc.exists() else ""))
    fasm = out / f"{top}.fasm"
    new = []
    skip = 0
    for i, c in enumerate(cmd[1:], 1):
        if skip:
            skip -= 1
            continue
        if c in ("--write", "--report"):
            skip = 1
            continue
        if c == "-o" and cmd[i + 1].split("=", 1)[0] in ("xdc", "fasm"):
            skip = 1
            continue
        new.append(c)
    new += ["-o", f"xdc={xdc}", "-o", "hardblock-timing", "-o", f"preplaced={ref}.preplaced",
            "-o", f"prerouted={ref}.prerouted", "--write", str(out / f"{top}_routed.json"), "-o", f"fasm={fasm}",
            "--report", str(out / "report.json")]
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(CONFIG["prefix"] / "bin" / "nextpnr-himbaechel"),
               OFX_MAX_NEXTPNR=str(CONFIG["max_nextpnr"]))
    t0 = time.time()
    with open(out / "nextpnr.log", "w") as f:
        r = subprocess.run([str(CONFIG["npwait"])] + new, stdout=f, stderr=subprocess.STDOUT, env=env)
    rec["seconds"] = round(time.time() - t0, 1)
    rec["cmd"] = [str(CONFIG["npwait"])] + new
    if r.returncode:
        rec["error"] = f"replay nextpnr exit {r.returncode} ({out / 'nextpnr.log'})"
        return rec
    a, b = fasm_lines(src / f"{top}.fasm"), fasm_lines(fasm)
    rec["fasm_identical"] = a is not None and a == b
    if not rec["fasm_identical"] and a is not None and b is not None:
        sa, sb = set(a), set(b)
        rec["fasm_diff"] = len(sa - sb) + len(sb - sa)
    again = out / "again"
    subprocess.run([sys.executable, str(ROOT / "flow" / "replay_dump.py"), str(out / f"{top}_routed.json"), str(again)],
                   stdout=open(out / "replay_dump_again.log", "w"), stderr=subprocess.STDOUT)
    rec["place_route_identical"] = (dump(str(again) + ".preplaced") == dump(str(ref) + ".preplaced") is not None and
                                    routes(str(again) + ".prerouted") == routes(str(ref) + ".prerouted") is not None)
    rec["honest_fmax"] = qb.parse_nextpnr(out).get("fmax")
    rec["src_key"] = st.get("key")
    done.write_text(json.dumps(rec, indent=1) + "\n")
    return rec


def mean(xs):
    xs = [x for x in xs if x]
    return round(sum(xs) / len(xs), 2) if xs else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prefix", default=str(CONFIG["prefix"]))
    ap.add_argument("--designs", nargs="+", default=CONFIG["designs"])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    CONFIG["prefix"] = Path(a.prefix).resolve()
    dry = CONFIG["dry_run"] and not a.run
    ok = True
    rows = []
    for d in a.designs:
        tmg = [status(run_dir(CONFIG["tmg"], d, s)) for s in CONFIG["seeds"]]
        base = [status(run_dir(CONFIG["base"], d, s)) for s in CONFIG["seeds"]]
        if dry:
            print(f"[dry] {d}: {sum(x is not None for x in base)}/{len(base)} {CONFIG['base']} and "
                  f"{sum(x is not None for x in tmg)}/{len(tmg)} {CONFIG['tmg']} runs on disk")
        if d in CONFIG["noop_designs"]:
            if dry:
                continue
            for s, b, t in zip(CONFIG["seeds"], base, tmg):
                top = qb.CONFIG["designs"][d]["top"]
                fa, fb = run_dir(CONFIG["base"], d, s) / f"{top}.frames", run_dir(CONFIG["tmg"], d, s) / f"{top}.frames"
                same = fa.exists() and fb.exists() and fa.stat().st_size > 0 and fa.read_bytes() == fb.read_bytes()
                ok &= same
                print(f"{'PASS' if same else 'FAIL'} noop {d} s{s}: .frames {'identical' if same else 'differ'} with and "
                      f"without -o hardblock-timing ({fa.parent} vs {fb.parent})", flush=True)
            continue
        reps = [replay(d, s, dry) for s in CONFIG["seeds"]]
        if dry:
            continue
        for rep, t in zip(reps, tmg):
            good = "error" not in rep and rep.get("place_route_identical")
            bits = bool(t and t.get("bitstream", {}).get("ok"))
            ok &= bool(good) & bits
            print(f"{'PASS' if good else 'FAIL'} replay {d} s{rep['seed']}: "
                  + (rep["error"] if "error" in rep else
                     f"placement and routing {'identical' if rep['place_route_identical'] else 'DIFFER'} "
                     f"(FASM {'identical' if rep['fasm_identical'] else str(rep.get('fasm_diff')) + ' lines differ'}); "
                     f"blind-timer Fmax {rep['blind_fmax']:.2f}, honest timer on the same placement {rep['honest_fmax']:.2f}")
                  + ("" if bits else f"; FAIL: {CONFIG['tmg']} s{rep['seed']} made no bitstream"), flush=True)
        mb = mean(r.get("honest_fmax") for r in reps if r.get("place_route_identical"))
        mt = mean(t.get("result", {}).get("fmax") for t in tmg if t)
        row = {"design": d, "blind_fmax": [r.get("blind_fmax") for r in reps],
               "blind_placement_honest_fmax": [r.get("honest_fmax") for r in reps],
               "hardblock_fmax": [t.get("result", {}).get("fmax") if t else None for t in tmg],
               "mean_blind_placement_honest": mb, "mean_hardblock": mt}
        good = mb is not None and mt is not None and mt >= mb * (1 - CONFIG["tolerance"])
        row["result"] = "PASS" if good else "FAIL"
        ok &= good
        rows.append(row)
        print(f"{row['result']} regression {d}: honest-timer Fmax, mean of seeds {CONFIG['seeds']}: blind placement "
              f"{mb} MHz, hardblock-timing placement {mt} MHz"
              + (f" ({100 * (mt / mb - 1):+.1f} %)" if mb and mt else ""), flush=True)
    if dry:
        return
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    (CONFIG["out"] / "summary.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(f"== hardblock-timing as default: {'PASS' if ok else 'FAIL'}; summary {CONFIG['out'] / 'summary.json'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
