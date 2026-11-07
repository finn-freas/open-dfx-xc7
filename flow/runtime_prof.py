import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "dry_run": True,
    "out": ROOT / "build" / "runtime",
    "nextpnr": ROOT / "toolchain" / "openxc7" / "bin" / "nextpnr-xilinx",
    "max_nextpnr": "3",
    "min_free_mb": 4000,
    "designs": {
        "blinky": {"dir": "designs/blinky", "top": "blinky", "part": "xc7a35tcsg324-1"},
        "rv_soc": {"dir": "designs/rv_soc", "top": "rv_soc", "part": "xc7a35tcsg324-1",
                   "rtl": ["rv_soc.v", "uart.v", "picorv32.v", "sim/rm_add.v"]},
        "litex_ddr3": {"dir": "designs/ddr3/arty_ddr3", "top": "digilent_arty", "part": "xc7a35tcsg324-1",
                       "rtl": ["digilent_arty.v", "VexRiscv.v"], "xdc": "designs/ddr3/arty_ddr3/nextpnr/digilent_arty.xdc",
                       "npr": ["--timing-allow-fail"]},
        "mc12_a100": {"dir": "designs/runtime/mc12_a100", "top": "mc12_a100", "part": "xc7a100tcsg324-1",
                      "rtl": ["mc12_a100.v", "qor_rv_big.v", "picorv32.v", "uart.v"], "npr": ["--timing-allow-fail"]},
    },
    "variants": {
        "base": {"args": [], "env": {"OFX_DM_CACHE": "0"}},
        "dmc": {"args": [], "env": {}},
        "pr": {"args": ["--nextpnr-arg=--parallel-refine"], "env": {}},
        "rtbb_off": {"args": [], "env": {"OFX_NEXTPNR_BIN": str(ROOT / "build/nextpnr-build/rtbb/nextpnr-himbaechel")},
                     "chipdb": True},
        "exitbb": {"args": ["--opt=exit-bb"], "env": {"OFX_NEXTPNR_BIN": str(ROOT / "build/nextpnr-build/rtbb/nextpnr-himbaechel")},
                   "chipdb": True},
        "static": {"args": ["--nextpnr-arg=--placer", "--nextpnr-arg=static"], "env": {}},
        "pr_t4": {"args": ["--nextpnr-arg=--parallel-refine", "--nextpnr-arg=--threads", "--nextpnr-arg=4"], "env": {}},
    },
    "np_phases": [
        ("startup+chipdb+json", None),
        ("pack", r"^Info: Packing constants"),
        ("place", r"^Info: Device utilisation"),
        ("route", r"^Info: Routing global clocks"),
        ("post-route timing+fasm", r"^Info: Critical path report for clock|^Info: Running post-routing"),
    ],
}


def free_mb():
    for ln in Path("/proc/meminfo").read_text().splitlines():
        if ln.startswith("MemAvailable:"):
            return int(ln.split()[1]) // 1024
    return 0


def load():
    la = Path("/proc/loadavg").read_text().split()
    n = subprocess.run(["pgrep", "-c", "nextpnr"], capture_output=True, text=True).stdout.strip() or "0"
    v = subprocess.run(["bash", "-c", "tasklist.exe 2>/dev/null | grep -ci vivado"], capture_output=True, text=True).stdout.strip()
    return {"load1": float(la[0]), "load5": float(la[1]), "nextpnr": int(n), "vivado": int(v or 0)}


def np_phases(ts_file, total):
    rows = [ln.split("\t", 1) for ln in Path(ts_file).read_text().splitlines() if "\t" in ln]
    rows = [(float(t), s) for t, s in rows]
    marks = [0.0]
    for name, rx in CONFIG["np_phases"][1:]:
        t = next((t for t, s in rows if re.search(rx, s) and t >= marks[-1]), None)
        marks.append(t if t is not None else marks[-1])
    marks.append(total)
    out = {name: round(marks[i + 1] - marks[i], 2) for i, (name, _) in enumerate(CONFIG["np_phases"])}
    log = "\n".join(s for _, s in rows)
    for key, rx in (("heap", r"HeAP Placer Time: ([\d.]+)s"), ("sa_refine", r"SA placement time ([\d.]+)s"),
                    ("router2", r"Router2 time ([\d.]+)s"), ("router1", r"Router1 time ([\d.]+)s"),
                    ("static", r"Static placer time: ([\d.]+)"), ("parallel_refine", r"Placement refine time ([\d.]+)s")):
        m = re.search(rx, log)
        if m:
            out["nextpnr_" + key] = float(m.group(1))
    m = re.search(r"Delay matrix: .* in ([\d.]+)s", log)
    if m:
        out["nextpnr_delay_matrix"] = float(m.group(1))
    fm = re.findall(r"Max frequency for clock\s+'([^']+)': ([\d.]+) MHz", log)
    out["fmax"] = {c: float(f) for c, f in fm}
    return out


def yosys_info(log):
    txt = Path(log).read_text(errors="replace")
    out = {}
    m = re.search(r"time: ([\d.]+)s, user: ([\d.]+)s, system: ([\d.]+)s, MEM: ([\d.]+) MB peak", txt)
    if m:
        out["wall"], out["cpu_user"], out["cpu_sys"], out["mem_mb"] = (float(m.group(i)) for i in range(1, 5))
    m = re.search(r"Time spent: (.*)", txt)
    if m:
        out["passes"] = [(int(p), n, int(c), int(s)) for p, c, n, s in
                         re.findall(r"(\d+)% (\d+)x ([\w$.]+) \((\d+) sec\)", m.group(1))]
    return out


def run_one(design, variant, rep, dry):
    d = CONFIG["designs"][design]
    v = CONFIG["variants"][variant]
    out = CONFIG["out"] / variant / design / f"r{rep}"
    cmd = [sys.executable, str(ROOT / "flow" / "build_openxc7.py"), str(Path(d["dir"]).relative_to("designs")),
           "--top", d["top"], "--part", d["part"], "--out", str(out), "--nextpnr", str(ROOT / "flow" / "runtime_np.sh")]
    if d.get("xdc"):
        cmd += ["--xdc", str(ROOT / d["xdc"])]
    cmd += [f"--nextpnr-arg={x}" for x in d.get("npr", [])] + v["args"]
    if v.get("chipdb"):
        sys.path.insert(0, str(ROOT / "flow"))
        import device
        cmd += ["--chipdb", device.resolve(d["part"])["chipdb"]]
    if d.get("rtl"):
        cmd += ["--rtl"] + d["rtl"]
    cmd.append("--run")
    print(f"[{'dry' if dry else 'run'}] {design} {variant} r{rep}: {' '.join(cmd)}", flush=True)
    if dry:
        return None
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    while free_mb() < CONFIG["min_free_mb"]:
        time.sleep(30)
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(CONFIG["nextpnr"]), OFX_MAX_NEXTPNR=CONFIG["max_nextpnr"],
               RT_TS=str(out / "nextpnr.ts"), RT_TIME=str(out / "nextpnr.time"))
    env.update(v["env"])
    before = load()
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    wall = time.time() - t0
    after = load()
    (out / "build.stdout").write_text(r.stdout + r.stderr)
    stages = {}
    cur = None
    for ln in r.stdout.splitlines():
        m = re.match(r"\[run\] ([\w-]+):", ln)
        if m:
            cur = m.group(1)
        m = re.match(r"\s+([\d.]+)s, log", ln)
        if m and cur:
            stages[cur] = float(m.group(1))
    res = {"design": design, "variant": variant, "rep": rep, "rc": r.returncode, "wall": round(wall, 2),
           "stages": stages, "load_before": before, "load_after": after, "cmd": cmd}
    if (out / "nextpnr.time").exists():
        w, u, s, rss = (out / "nextpnr.time").read_text().split()[-4:]
        res["nextpnr_proc"] = {"wall": float(w), "user": float(u), "sys": float(s), "maxrss_mb": int(rss) // 1024}
        res["nextpnr_phases"] = np_phases(out / "nextpnr.ts", float(w))
    if (out / "yosys.log").exists():
        res["yosys"] = yosys_info(out / "yosys.log")
    res["python_overhead"] = round(wall - sum(stages.values()), 2)
    (out / "runtime.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("design", "variant", "rep", "rc", "wall", "stages", "load_before", "load_after")}),
          flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("designs", nargs="*", default=list(CONFIG["designs"]))
    ap.add_argument("--variant", default="base", choices=list(CONFIG["variants"]))
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--first-rep", type=int, default=1)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--reparse", action="store_true", help="recompute nextpnr phases of existing results")
    a = ap.parse_args()
    if a.reparse:
        for f in CONFIG["out"].glob("*/*/r*/runtime.json"):
            res = json.loads(f.read_text())
            if "nextpnr_proc" in res and (f.parent / "nextpnr.ts").exists():
                res["nextpnr_phases"] = np_phases(f.parent / "nextpnr.ts", res["nextpnr_proc"]["wall"])
                f.write_text(json.dumps(res, indent=1) + chr(10))
        return
    dry = CONFIG["dry_run"] and not a.run
    for rep in range(a.first_rep, a.first_rep + a.reps):
        for design in a.designs:
            run_one(design, a.variant, rep, dry)


if __name__ == "__main__":
    main()
