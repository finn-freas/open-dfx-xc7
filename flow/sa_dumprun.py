"""Re-run a finished place_bench run with the current SA binary (build/nextpnr-build/sa) and the model endpoint dump:
the run's own sa-refine options + dump=FILE, or (no SA in the run) sa-refine=temps=0:dump=FILE, which leaves the
placement unchanged. usage: sa_dumprun.py RUN_DIR OUT_DIR"""
import json, os, subprocess, sys, time
from pathlib import Path
R = Path.home() / "open-dfx-xc7"
run, out = R / sys.argv[1], Path(sys.argv[2]).resolve()
st = json.loads((run / "status.json").read_text())
cmd = list(st["cmd"])
cmd[0] = str(R / "build/nextpnr-build/sa/nextpnr-himbaechel")
out.mkdir(parents=True, exist_ok=True)
dump = out / "endpoints.txt"
new, k, have = [], 1, False
while k < len(cmd):
    a = cmd[k]
    if a in ("--write", "--report"):
        k += 2
        continue
    if a == "-o" and cmd[k + 1].startswith("fasm="):
        k += 2
        continue
    if a == "-o" and cmd[k + 1].startswith("sa-refine"):
        v = cmd[k + 1]
        new += ["-o", (v + ":" if "=" in v else v + "=") + f"dump={dump}"]
        have = True
        k += 2
        continue
    new.append(a)
    k += 1
if not have:
    new += ["-o", f"sa-refine=temps=0:dump={dump}"]
new += ["--no-route"] if False else []
env = dict(os.environ, OFX_NEXTPNR_BIN=cmd[0], OFX_MAX_NEXTPNR="3")
t = time.time()
with open(out / "nextpnr.log", "w") as f:
    rc = subprocess.run([str(R / "ofx/npwait.sh")] + new, stdout=f, stderr=subprocess.STDOUT, env=env).returncode
print(run.name, "rc", rc, round(time.time() - t, 1), "s")
