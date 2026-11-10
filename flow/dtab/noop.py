import json, subprocess, sys, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R = Path("/home/finnf/open-dfx-xc7")
B = R / "build/nextpnr-build/dtab/nextpnr-himbaechel"
out = R / "build/dtab/noop"; out.mkdir(exist_ok=True)
T = str(R / "build/dtab/t_fo.txt")
def prep(d, v, s, tag, extra):
    st = json.loads((R / f"build/qor/oxc7/{v}/{d}_p5/s{s}/status.json").read_text())
    c = list(st["cmd"])
    for i, x in enumerate(c):
        if x == "--write": c[i + 1] = str(out / f"{tag}_routed.json")
        if x == "--report": c[i + 1] = str(out / f"{tag}_report.json")
        if x.startswith("fasm="): c[i] = f"fasm={out / (tag + '.fasm')}"
    return c[1:] + extra, R / f"build/qor/oxc7/{v}/{d}_p5/s{s}/qor_{d}.fasm"
def run(job):
    args, tag = job
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(B), OFX_MAX_NEXTPNR="4")
    with open(out / f"{tag}.log", "w") as f:
        return subprocess.run([str(R / "ofx/npwait.sh")] + args, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=str(out)).returncode
def body(p):
    return [l for l in Path(p).read_text().splitlines() if "version" not in l.lower()]
jobs, refs = [], {}
for d, v, s in (("rv_soc", "ua_dxy", 1), ("rv_mul", "ua_dxy_dq", 1)):
    for tag, extra in (("off", []), ("eval", ["-o", f"dtab={T}", "-o", "dtab-eval"])):
        a, ref = prep(d, v, s, f"{d}_{tag}", extra)
        jobs.append((a, f"{d}_{tag}")); refs[f"{d}_{tag}"] = ref
with ThreadPoolExecutor(2) as ex:
    print("rc", list(ex.map(run, jobs)))
for tag, ref in refs.items():
    a, b = body(out / f"{tag}.fasm"), body(ref)
    print(tag, "lines", len(a), len(b), "IDENTICAL (except version)" if a == b else "DIFFERENT", "full-diff-lines", sum(1 for x, y in zip(Path(out / f'{tag}.fasm').read_text().splitlines(), Path(ref).read_text().splitlines()) if x != y))
