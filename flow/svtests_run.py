"""SystemVerilog front-end coverage on chipsalliance/sv-tests: yosys read_verilog -sv vs yosys-slang vs Vivado.

Selection and pass/fail rules follow sv-tests (tools/runner, tools/runners/Yosys.py, yosys_slang.py):
  - only tests whose :type: includes "elaboration" (the mode both yosys runners can share),
  - unsynthesizable tests skipped,
  - pass = tool exit code says success XOR the test is a should_fail test; exit >= 126 is a crash and fails.
Every front end runs the same elaboration script as the sv-tests runner (hierarchy, proc, check, memory_dff,
memory_collect, stat, check); yosys-slang gets the sv-tests runner's flags. Vivado runs synth_design -rtl
(RTL elaboration) on the same files, include dirs and defines, from vivado/svtests_elab.tcl.

  svtests_run.py run [--jobs N] [--only REGEX]   run yosys and yosys-slang, write build/svtests/results.json
  svtests_run.py vivado-manifest                write the Vivado manifest and copy the sources for Windows
  svtests_run.py vivado-ingest LOG              merge the Vivado log into results.json
  svtests_run.py report                         print the summary tables (markdown)
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "svtests": ROOT / "upstream" / "chipsalliance_sv-tests",
    "yosys": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "yosys",
    "out": ROOT / "build" / "svtests",
    "jobs": 6,
    "win_root": "C:/Users/finnf/open-dfx-xc7-vivado/svtests",
    "win_mnt": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/svtests"),
    "part": "xc7a35tcsg324-1",
}
PARAMS = ["name", "tags", "description", "files", "incdirs", "top_module", "timeout", "type", "should_fail",
          "should_fail_because", "defines", "compatible-runners", "unsynthesizable", "results_group", "simvariants"]
EXTS = (".v", ".sv", ".vh", ".svh")


def parse(test):
    p = {}
    with open(test, errors="replace") as f:
        for line in f:
            m = re.search(r"^:([a-zA-Z_-]+):\s*(.+)", line)
            if not m:
                continue
            k = m.group(1).lower()
            if k in PARAMS:
                p[k] = m.group(2)
            if not set(PARAMS) - set(p):
                break
    p.setdefault("name", str(test))
    p.setdefault("files", str(test))
    p.setdefault("incdirs", os.path.dirname(test))
    p.setdefault("top_module", "")
    p.setdefault("timeout", "30")
    p.setdefault("type", "parsing elaboration")
    p.setdefault("should_fail", "1" if "should_fail_because" in p else "0")
    p.setdefault("should_fail_because", "")
    p.setdefault("defines", "")
    p.setdefault("compatible-runners", "all")
    p.setdefault("unsynthesizable", "0")
    if p["should_fail"] == "0" and p["should_fail_because"]:
        p["should_fail"] = "1"
    tests_dir = CONFIG["svtests"] / "tests"
    p["files"] = [f if os.path.isabs(f) else str((tests_dir / f).resolve()) if (tests_dir / f).exists() else f
                  for f in p["files"].split()]
    p["files"] = [f for f in p["files"] if os.path.splitext(f)[1] in EXTS]
    p["incdirs"] = [os.path.abspath(os.path.join(tests_dir, x)) for x in p["incdirs"].split()]
    p["defines"] = p["defines"].split()
    p["tags"] = p.get("tags", "")
    return p


def selected(p):
    runners = p["compatible-runners"].split()
    if "all" not in runners and not ({"yosys", "yosys-slang"} & set(runners)):
        return False
    return "elaboration" in p["type"].split() and p["unsynthesizable"].strip() == "0"


def guess_top(p):
    rx = re.compile(r"module\s+(\w+)\s*[#(;]")
    for fn in p["files"]:
        try:
            mods = rx.findall(Path(fn).read_text(errors="replace"))
        except OSError:
            continue
        if mods:
            return "top" if "top" in mods else mods[0]
    return None


ELAB = "proc\ncheck\nclean\nmemory_dff\nmemory_collect\nstat\ncheck\n"


def script_builtin(p):
    inc = "".join(f" -I {d}" for d in p["incdirs"])
    defs = "".join(f" -D {d}" for d in p["defines"])
    s = "".join(f"read_verilog -sv{inc}{defs} {f}\n" for f in p["files"])
    top = p["top_module"].strip()
    return s + (f"hierarchy -top \\{top}\n" if top else "hierarchy -auto-top\n") + ELAB


def script_slang(p):
    a = ["-DSYNTHESIS", "--ignore-timing", "--ignore-initial", "--ignore-assertions", "--single-unit",
         "--timescale=1ns/1ns"]
    top = p["top_module"].strip()
    if top:
        a.append("--top=" + top)
    for d in p["incdirs"]:
        a += ["-I", d]
    for d in p["defines"]:
        a += ["-D", d]
    a += ["-Wno-error=index-oob", "-Wno-error=range-oob", "-Wno-error=range-width-oob"]
    if "ariane" in p["tags"].split():
        a.append("-DVERILATOR")
    if "black-parrot" in p["tags"].split():
        a.append("--allow-use-before-declare")
    if "fx68k" in p["tags"].split():
        a.append("--allow-dup-initial-drivers")
    a += p["files"]
    s = "plugin -i slang\nread_slang " + " ".join(a) + "\n"
    s += (f"hierarchy -top \\{top}\n" if top else "hierarchy -auto-top\n") + ELAB.replace("clean\n", "")
    return s


FRONTENDS = {"yosys": script_builtin, "slang": script_slang}


def first_error(log):
    for line in log.splitlines():
        if re.search(r"\bERROR\b|error:|Assert|terminate called|Segmentation", line):
            return line.strip()[:300]
    return log.strip().splitlines()[-1][:300] if log.strip() else ""


TIMEOUT = None


def run_one(rel, p, fe):
    with tempfile.TemporaryDirectory(dir=CONFIG["out"] / "tmp") as td:
        scr = Path(td) / "s.ys"
        scr.write_text(FRONTENDS[fe](p))
        t0 = time.time()
        try:
            r = subprocess.run([str(CONFIG["yosys"]), "-Q", "-T", "-s", str(scr)], cwd=td, capture_output=True,
                               text=True, errors="replace", timeout=TIMEOUT or int(p["timeout"]))
            rc, log = r.returncode, r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            rc, log = 71, f"Timeout: > {TIMEOUT or p['timeout']}s"
    sf = p["should_fail"] == "1"
    passed = rc < 126 and (rc != 0) == sf and rc != 71
    top = None
    m = re.search(r"Automatically selected (\S+) as design top module", log) or re.search(r"Top module:\s+\\?(\S+)", log)
    if m:
        top = m.group(1).lstrip("\\")
    return {"rc": rc, "pass": passed, "secs": round(time.time() - t0, 2), "top": top, "timeout": TIMEOUT or int(p["timeout"]),
            "error": "" if rc == 0 else first_error(log)}


def all_tests(only=None):
    tests = sorted((CONFIG["svtests"] / "tests").rglob("*.sv"))
    out = {}
    for t in tests:
        rel = str(t.relative_to(CONFIG["svtests"] / "tests"))
        if only and not re.search(only, rel):
            continue
        p = parse(t)
        if selected(p):
            out[rel] = p
    return out


def group(rel, p):
    if rel.startswith("generated/"):
        return "core:" + rel.split("/")[1]
    return rel.split("/")[0]


def cmd_run(a):
    global TIMEOUT
    TIMEOUT = a.timeout
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    (CONFIG["out"] / "tmp").mkdir(exist_ok=True)
    tests = all_tests(a.only)
    res_path = CONFIG["out"] / "results.json"
    res = json.loads(res_path.read_text()) if res_path.exists() else {}
    jobs = [(rel, p, fe) for rel, p in tests.items() for fe in FRONTENDS if fe in a.frontends]
    print(f"{len(tests)} tests, {len(jobs)} runs, {a.jobs} workers", flush=True)
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(run_one, rel, p, fe): (rel, fe) for rel, p, fe in jobs}
        for i, f in enumerate(cf.as_completed(futs)):
            rel, fe = futs[f]
            p = tests[rel]
            e = res.setdefault(rel, {})
            e.update({"group": group(rel, p), "should_fail": p["should_fail"] == "1", "tags": p["tags"],
                      "top_module": p["top_module"].strip()})
            e[fe] = f.result()
            if (i + 1) % 200 == 0:
                print(f"  {i + 1}/{len(jobs)}", flush=True)
    res_path.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"wrote {res_path}")


def win(path):
    s = str(path)
    base = str(CONFIG["svtests"])
    if s.startswith(base):
        return CONFIG["win_root"] + s[len(base):]
    raise ValueError(f"path outside sv-tests: {s}")


def cmd_manifest(a):
    tests = all_tests(a.only)
    res = json.loads((CONFIG["out"] / "results.json").read_text())
    lines = []
    for rel, p in tests.items():
        r = res.get(rel, {})
        top = p["top_module"].strip() or (r.get("yosys") or {}).get("top") or (r.get("slang") or {}).get("top") \
            or guess_top(p) or ""
        defs = ["SYNTHESIS"] + p["defines"]
        lines.append("\t".join([rel, top, " ".join(win(f) for f in p["files"]),
                                " ".join(win(d) for d in p["incdirs"]), " ".join(defs)]))
    dst = CONFIG["win_mnt"]
    dst.mkdir(parents=True, exist_ok=True)
    for sub in ("tests", "third_party/cores"):
        print(f"copying {sub}", flush=True)
        (dst / sub).mkdir(parents=True, exist_ok=True)
        subprocess.run(["rsync", "-a", "--delete", "--exclude", ".git", f"{CONFIG['svtests'] / sub}/", f"{dst / sub}/"],
                       check=True)
    (dst / "manifest.tsv").write_text("\n".join(lines) + "\n")
    shutil.copy(ROOT / "vivado" / "svtests_elab.tcl", dst / "svtests_elab.tcl")
    print(f"{len(lines)} tests in {dst / 'manifest.tsv'}")


def cmd_ingest(a):
    res_path = CONFIG["out"] / "results.json"
    res = json.loads(res_path.read_text())
    cur, buf, n = None, [], 0
    for line in Path(a.log).read_text(errors="replace").splitlines():
        m = re.match(r"SVT_BEGIN (\S+)", line)
        if m:
            cur, buf = m.group(1), []
            continue
        m = re.match(r"SVT_END (\S+) (\d+) ([\d.]+)", line)
        if m and cur == m.group(1):
            rc = int(m.group(2))
            e = res.get(cur)
            if e is not None:
                err = next((x.strip()[:300] for x in buf if x.startswith("ERROR")), "")
                e["vivado"] = {"rc": rc, "pass": (rc != 0) == e["should_fail"], "secs": float(m.group(3)),
                               "error": err if rc else ""}
                n += 1
            cur = None
            continue
        if cur:
            buf.append(line)
    res_path.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"merged {n} Vivado results")


def cmd_report(a):
    res = json.loads((CONFIG["out"] / "results.json").read_text())
    fes = ["yosys", "slang", "vivado"]
    groups = {}
    for rel, e in res.items():
        groups.setdefault(e["group"], []).append(e)
    print("| group | tests | yosys read_verilog -sv | yosys-slang | Vivado 2025.2 synth_design -rtl |")
    print("|---|---|---|---|---|")
    tot = {fe: [0, 0] for fe in fes}
    for g in sorted(groups, key=lambda x: (x.startswith("core:"), int(x.split("-")[1]) if x.startswith("chapter-") else 0, x)):
        es = groups[g]
        cells = []
        for fe in fes:
            ran = [e for e in es if fe in e]
            ok = sum(e[fe]["pass"] for e in ran)
            tot[fe][0] += ok
            tot[fe][1] += len(ran)
            cells.append(f"{ok}/{len(ran)}" if ran else "-")
        print(f"| {g} | {len(es)} | " + " | ".join(cells) + " |")
    print("| **total** | %d | " % len(res) + " | ".join(f"**{tot[fe][0]}/{tot[fe][1]}**" for fe in fes) + " |")
    both = [e for e in res.values() if all(fe in e for fe in fes)]
    def cls(e):
        return "".join("P" if e[fe]["pass"] else "f" for fe in fes)
    from collections import Counter
    c = Counter(cls(e) for e in both)
    print(f"\npattern over {len(both)} tests with all three results (yosys, slang, vivado; P pass, f fail):")
    for k, v in sorted(c.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    if a.list:
        for rel, e in sorted(res.items()):
            if all(fe in e for fe in fes) and re.search(a.list, cls(e)):
                print(f"{cls(e)} {rel} sf={int(e['should_fail'])}")
                for fe in fes:
                    if not e[fe]["pass"]:
                        print(f"    {fe}: rc={e[fe]['rc']} {e[fe]['error'][:200]}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--jobs", type=int, default=CONFIG["jobs"])
    r.add_argument("--only")
    r.add_argument("--timeout", type=int, help="override the per-test sv-tests timeout (seconds)")
    r.add_argument("--frontends", nargs="+", default=list(FRONTENDS))
    m = sub.add_parser("vivado-manifest")
    m.add_argument("--only")
    i = sub.add_parser("vivado-ingest")
    i.add_argument("log")
    rp = sub.add_parser("report")
    rp.add_argument("--list", help="regex over the yosys/slang/vivado pattern, e.g. '^f.P' for yosys-only failures")
    a = ap.parse_args()
    {"run": cmd_run, "vivado-manifest": cmd_manifest, "vivado-ingest": cmd_ingest, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
