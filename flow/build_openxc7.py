import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import device
import dm_cache

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "part": device.get("part"),
    "family": device.get("family"),
    "seed": 1,
    "freq_mhz": os.environ.get("OFX_FREQ_MHZ") or 100,
    "dry_run": True,
    "nextpnr": None,
    "chipdb": None,
    "seed_jobs": int(os.environ.get("OFX_SEED_JOBS") or 4),
    "fmax_re": r"Max frequency for clock '([^']+)': ([\d.]+) MHz \((?:PASS|FAIL) at ([\d.]+) MHz\)",
    "drop": (".fasm", "_routed.json", "delay_matrix.txt"),
}

ROOT = CONFIG["root"]
OXC7 = ROOT / "toolchain" / "openxc7"
OCS = ROOT / "toolchain" / "oss-cad-suite"
DB = OXC7 / "share" / "nextpnr" / "external" / "prjxray-db"


def tool(name):
    for base in (OXC7 / "bin", OCS / "bin"):
        if (base / name).exists():
            return str(base / name)
    sys.exit(f"missing tool {name}")


def stage(name, out, cmd, log, dry):
    if out.exists():
        print(f"[skip] {name}: {out.name} exists")
        return
    print(f"[{'dry' if dry else 'run'}] {name}: {' '.join(cmd)}")
    if dry:
        return
    t0 = time.time()
    with open(log, "w") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    print(f"        {time.time() - t0:.1f}s, log {log.name}")
    if r.returncode != 0 or not out.exists():
        sys.exit(f"{name} failed, see {log}")


def seed_score(log):
    """Worst routed Fmax / target over the clocks (last report per clock), or None without a timing report."""
    try:
        text = Path(log).read_text(errors="ignore")
    except OSError:
        return None, {}
    clocks = {c: (float(f), float(t)) for c, f, t in re.findall(CONFIG["fmax_re"], text)}
    if not clocks:
        return None, {}
    return min(f / t for f, t in clocks.values()), {c: f for c, (f, _) in clocks.items()}


def best_of_seeds(a, npnr, js, xdc, top, out, extra, dm_key, dry):
    """Place and route seeds a.seed .. a.seed+a.seeds-1 in parallel (out/seeds/s<N>), keep the one with the best
    worst-clock routed Fmax / target, and copy its nextpnr outputs into out. Measured on the exact placement import
    (Vivado routes our placement): best of 3 +2.8 % mean Fmax over rv_soc/bram/rv_big/rv_mul, best of 4 +3.7 %.
    With a.seeds_auto, a.seed runs alone first and the other seeds only run when it misses timing or fails."""
    seeds = list(range(a.seed, a.seed + a.seeds))
    batches = [seeds[:1], seeds[1:]] if a.seeds_auto else [seeds]
    names = (f"{top}_routed.json", f"{top}.fasm", "report.json", "nextpnr.log")

    def one(s):
        d = out / "seeds" / f"s{s}"
        d.mkdir(parents=True, exist_ok=True)
        ex = list(extra)
        dm = dm_cache.prepare(dm_key, d)
        if dm:
            ex += ["-o", f"delay-matrix={dm}"]
        cmd = [npnr, "--device", a.part, "--json", str(js), "-o", f"xdc={xdc}", "--seed", str(s), "--freq", str(a.freq),
               "--write", str(d / names[0]), "-o", f"fasm={d / names[1]}", "--report", str(d / names[2])] + ex
        if dry:
            print(f"[dry] nextpnr seed {s}: {' '.join(cmd)}")
            return s, False, None, {}, None
        with open(d / names[3], "w") as f:
            rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode
        done = rc == 0 and (d / names[1]).exists()
        if done:
            dm_cache.publish(dm_key, d)
        return s, done, *seed_score(d / names[3]), rc

    def show(r):
        s, done, score, clk, rc = r
        txt = ", ".join(f"{c} {f:.2f} MHz" for c, f in clk.items()) or "no clock report"
        if not done:
            txt = f"failed (rc {rc}" + ("; misses timing: " + txt if score is not None and score < 1.0 else "") + ")"
        return txt

    def record(best):
        (out / "seeds.json").write_text(json.dumps({"kept": best, "auto": bool(a.seeds_auto), "max": a.seeds, "runs": [
            {"seed": s, "ok": done, "score": score, "fmax_mhz": clk or None, "rc": rc}
            for s, done, score, clk, rc in res]}, indent=1) + "\n")

    how = "the others only if it misses timing" if a.seeds_auto else "keeping the best routed Fmax"
    print(f"[{'dry' if dry else 'run'}] nextpnr: seeds {seeds[0]}..{seeds[-1]}, {how}")
    t0 = time.time()
    res = []
    for i, batch in enumerate(batches):
        if not batch:
            break
        if i:
            if dry:
                print(f"[dry] seeds {batch[0]}..{batch[-1]} only if seed {seeds[0]} misses timing or fails")
                break
            _, done, score, _, _ = res[0]
            if done and (score is None or score >= 1.0):
                break
            why = f"misses timing ({score:.3f} of the target)" if score is not None and score < 1.0 else "failed"
            print(f"        seed {seeds[0]} {why}, trying seeds {batch[0]}..{batch[-1]}")
        with ThreadPoolExecutor(max_workers=max(1, min(CONFIG["seed_jobs"], len(batch)))) as ex:
            res += list(ex.map(one, batch))
    if dry:
        return
    ok = [r for r in res if r[1]]
    if not ok:
        for r in res:
            print(f"        seed {r[0]}: {show(r)}")
        record(None)
        sys.exit(f"nextpnr failed for every seed, see {out / 'seeds'}/s*/nextpnr.log and {out / 'seeds.json'}")
    best = max(ok, key=lambda r: (r[2] if r[2] is not None else float("-inf"), -r[0]))[0]
    for r in res:
        print(f"        seed {r[0]}: {show(r)}" + ("  <- kept" if r[0] == best else ""))
    src = out / "seeds" / f"s{best}"
    for n in names:
        shutil.copyfile(src / n, out / n)
    for s, *_ in res:
        if s != best:
            for p in (out / "seeds" / f"s{s}").iterdir():
                if p.name.endswith(CONFIG["drop"]):
                    p.unlink()
    record(best)
    print(f"        {time.time() - t0:.1f}s, kept seed {best}")


def versions():
    info = json.loads((ROOT / "toolchain" / "openxc7-BUILD-INFO.json").read_text())
    ys = subprocess.run([tool("yosys"), "-V"], capture_output=True, text=True).stdout.strip()
    return {
        "yosys": ys,
        "oss_cad_suite": (OCS / "VERSION").read_text().strip(),
        "openxc7_release": info["release-tag"],
        "nextpnr_xilinx": info["nextpnr-xilinx-revision"],
        "prjxray": info["prjxray-revision"],
        "prjxray_db": info["prjxray-db-revision"],
        "fasm": info["fasm-revision"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design")
    ap.add_argument("--top")
    ap.add_argument("--xdc")
    ap.add_argument("--part", default=CONFIG["part"])
    ap.add_argument("--family", help="prjxray-db family (default: the configured family, or looked up for a --part "
                                     "other than the configured one)")
    ap.add_argument("--freq", default=CONFIG["freq_mhz"], help="nextpnr --freq target in MHz")
    ap.add_argument("--seed", type=int, default=CONFIG["seed"])
    ap.add_argument("--seeds", type=int, default=1, help="place and route this many seeds (--seed upwards) in "
                    "parallel and keep the one with the best routed Fmax")
    ap.add_argument("--seeds-auto", action="store_true", help="with --seeds N: run --seed alone first, and the "
                    "other N-1 seeds only if it misses timing (or fails)")
    ap.add_argument("--rtl", nargs="+", help="source files relative to the design dir (default: all .v/.sv)")
    ap.add_argument("--name", help="build name (default: <part>_s<seed>)")
    ap.add_argument("--opt", action="append", default=[], help="extra nextpnr -o option, e.g. preplaced=FILE")
    ap.add_argument("--stop-after", choices=["yosys"], help="stop after this stage")
    ap.add_argument("--json", help="use this synthesized json instead of running yosys")
    ap.add_argument("--nextpnr", default=CONFIG["nextpnr"], help="nextpnr binary to use instead of the toolchain's nextpnr-xilinx")
    ap.add_argument("--chipdb", default=CONFIG["chipdb"], help="chipdb file passed to nextpnr as --chipdb")
    ap.add_argument("--out", help="output directory (default: build/openxc7/<design>/<name>)")
    ap.add_argument("--nextpnr-arg", action="append", default=[], help="extra nextpnr argument, e.g. --nextpnr-arg=--router2-region-keep-out")
    ap.add_argument("--synth", help="yosys synthesis commands instead of 'synth_xilinx -flatten -abc9 -arch xc7 -top TOP' "
                                     "({top} is replaced)")
    ap.add_argument("--db-root", help="prjxray-db root (with the family directories) for fasm2frames and xc7frames2bit")
    ap.add_argument("--frontend", choices=["builtin", "slang"], default="builtin",
                    help="SystemVerilog front end: yosys read_verilog -sv (builtin) or the yosys-slang plugin shipped "
                         "with oss-cad-suite (slang: plugin -i slang; read_slang); docs/sv-frontend.md")
    ap.add_argument("--slang-arg", action="append", default=[],
                    help="extra read_slang option, e.g. --slang-arg=--ignore-initial")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    family = a.family or (CONFIG["family"] if a.part == CONFIG["part"] else device.resolve(a.part)["family"])
    src = ROOT / "designs" / a.design
    top = a.top or a.design
    xdc = Path(a.xdc) if a.xdc else next(src.glob("*.xdc"))
    out = Path(a.out).resolve() if a.out else ROOT / "build" / "openxc7" / a.design / (a.name or f"{a.part}_s{a.seed}")
    out.mkdir(parents=True, exist_ok=True)
    if a.rtl:
        rtl = [str(src / p) for p in a.rtl]
    else:
        rtl = sorted(str(p) for p in src.glob("*.v")) + sorted(str(p) for p in src.glob("*.sv"))
    extra = [x for o in a.opt for x in ("-o", o)] + a.nextpnr_arg
    npnr = str(Path(a.nextpnr).resolve()) if a.nextpnr else tool("nextpnr-xilinx")
    if a.chipdb:
        extra += ["--chipdb", str(Path(a.chipdb).resolve())]
    js, rjs, fasm, frames, bit = (out / f"{top}{e}" for e in (".json", "_routed.json", ".fasm", ".frames", ".bit"))
    synth = a.synth.replace("{top}", top) if a.synth else f"synth_xilinx -flatten -abc9 -arch xc7 -top {top}"
    if a.frontend == "slang":
        sargs = " ".join(["-DSYNTHESIS", "--top", top] + a.slang_arg)
        ys = f"plugin -i slang; read_slang {sargs} {' '.join(rtl)}; {synth}; write_json {js}"
    else:
        ys = f"read_verilog -sv {' '.join(rtl)}; {synth}; write_json {js}"
    db = Path(a.db_root).resolve() if a.db_root else DB
    if a.json:
        stage("copy-json", js, ["cp", a.json, str(js)], out / "copy.log", dry)
    else:
        stage("yosys", js, [tool("yosys"), "-p", ys], out / "yosys.log", dry)
    if not dry and js.exists() and not fasm.exists() and os.environ.get("OFX_GT_DEFAULTS") != "0":
        subprocess.run([sys.executable, str(ROOT / "flow" / "gt_json_defaults.py"), str(js)], check=True)
    if a.stop_after == "yosys":
        return
    dm_key = None
    base_extra = extra
    if not dry and not fasm.exists():
        try:
            dm_key = dm_cache.key(npnr, a.part, device.resolve(a.part)["fabric"], extra, a.chipdb)
        except (ValueError, OSError):
            dm_key = None
        dm_file = dm_cache.prepare(dm_key, out)
        if dm_file:
            extra = extra + ["-o", f"delay-matrix={dm_file}"]
    if a.seeds > 1 and not fasm.exists():
        best_of_seeds(a, npnr, js, xdc, top, out, base_extra, dm_key, dry)
        if dry:
            return
    stage("nextpnr", fasm, [npnr, "--device", a.part, "--json", str(js), "-o", f"xdc={xdc}",
                            "--seed", str(a.seed), "--freq", str(a.freq),
                            "--write", str(rjs), "-o", f"fasm={fasm}", "--report", str(out / "report.json")] + extra,
          out / "nextpnr.log", dry)
    dm_cache.publish(dm_key, out)
    f2f = tool("fasm2frames")
    py, script = OXC7 / "libexec" / "tabbypy3", OXC7 / "libexec" / "fasm2frames"
    if os.environ.get("OFX_FAST_F2F") != "0" and Path(f2f) == OXC7 / "bin" / "fasm2frames" and py.exists() and script.exists():
        f2f = (f"PATH={OXC7 / 'bin'}:$PATH PYTHONEXECUTABLE={py} {py} {ROOT / 'flow' / 'fasm2frames_fast.py'} {script}")
    stage("fasm2frames", frames, ["bash", "-c", f"{f2f} --part {a.part} --db-root {db / family} {fasm} > {frames}"],
          out / "fasm2frames.log", dry)
    stage("xc7frames2bit", bit, [tool("xc7frames2bit"), f"--part_file={db / family / a.part / 'part.yaml'}",
                                 f"--part_name={a.part}", f"--frm_file={frames}", f"--output_file={bit}"],
          out / "xc7frames2bit.log", dry)
    if not dry:
        v = versions()
        if a.nextpnr:
            v["nextpnr_binary"] = npnr
            v["nextpnr_version"] = subprocess.run([npnr, "--version"], capture_output=True, text=True).stderr.strip()
        if a.chipdb:
            v["chipdb"] = str(Path(a.chipdb).resolve())
        if a.synth:
            v["synth"] = synth
        if a.db_root:
            v["prjxray_db_root"] = str(db)
        if a.frontend != "builtin":
            v["frontend"] = a.frontend
            v["slang_args"] = a.slang_arg
        (out / "versions.json").write_text(json.dumps(v, indent=2) + "\n")
        print(f"bitstream: {bit}")


if __name__ == "__main__":
    main()
