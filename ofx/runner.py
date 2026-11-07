import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from . import FLOW, ROOT

CONFIG = {
    "python": sys.executable,
    "npwait": ROOT / "ofx" / "npwait.sh",
    "max_nextpnr_env": "OFX_MAX_NEXTPNR",
    "stamp": ".ofx-inputs.json",
}


def flow(script):
    return str(FLOW / script)


def show(cmd):
    return " ".join(shlex.quote(str(c)) for c in cmd)


def run(cmd, env=None, dry=False, log=None, ok=(0,), cwd=ROOT, check=True):
    print(f"[{'dry' if dry else 'run'}] {show(cmd)}" + (f"  > {log}" if log else ""), flush=True)
    if dry:
        return 0
    e = dict(os.environ, **(env or {}))
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        with open(log, "w") as f:
            r = subprocess.run([str(c) for c in cmd], env=e, cwd=cwd, stdout=f, stderr=subprocess.STDOUT)
    else:
        r = subprocess.run([str(c) for c in cmd], env=e, cwd=cwd)
    if check and r.returncode not in ok:
        sys.exit(f"ofx: command failed (exit {r.returncode})" + (f", see {log}" if log else "") + f": {show(cmd)}")
    return r.returncode


def digest(files, extra):
    h = hashlib.sha256()
    for f in sorted(str(x) for x in files):
        h.update(f.encode())
        h.update(Path(f).read_bytes())
    h.update(json.dumps(extra, sort_keys=True, default=str).encode())
    return h.hexdigest()


def fresh(out, key, dry):
    stamp = Path(out) / CONFIG["stamp"]
    if stamp.exists():
        old = json.loads(stamp.read_text()).get("inputs")
        if old == key:
            return
        print(f"[{'dry' if dry else 'run'}] inputs changed since the last build: clean {out}", flush=True)
        if not dry:
            shutil.rmtree(out)
    if not dry:
        Path(out).mkdir(parents=True, exist_ok=True)
        stamp.write_text(json.dumps({"inputs": key}) + "\n")


def nextpnr_limit():
    v = os.environ.get(CONFIG["max_nextpnr_env"])
    return int(v) if v else None
