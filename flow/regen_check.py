import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "dirs": ["build/partials/rv_native", "build/patched/partials/rv_b_native", "build/patched/partials/rv_c_native",
             "build/patched/partials/rv_m_native"],
    "out": "build/phase10/regen",
    "dry_run": True,
}


def command(rec, out):
    full = Path(rec["from_full"])
    cmd = [sys.executable, "flow/partial.py", str(full), str(out), "--design", full.stem, "--region", rec["region"],
           "--fasm", str(full.with_suffix(".fasm")), "--static-pips", str(full.parent.parent / "static.prerouted")]
    if rec.get("simulated"):
        cmd += ["--base", rec["simulated"]["base"], "--simulate"]
    return cmd


def main():
    ap = argparse.ArgumentParser(description="Regenerate every partial that has a .check.json record with the current "
                                             "partial.py and compare the .bin sha256 with the record")
    ap.add_argument("--dirs", nargs="*", default=CONFIG["dirs"])
    ap.add_argument("--out", default=CONFIG["out"])
    ap.add_argument("--extra", default="", help="extra partial.py arguments as one string, e.g. --extra=\"--compress\"")
    ap.add_argument("--match", default="", help="only records whose file name matches this regex")
    ap.add_argument("--run", action="store_true", help="run (default is a dry run that prints the commands)")
    a = ap.parse_args()
    root = CONFIG["root"]
    same = differ = failed = 0
    for d in a.dirs:
        for rec_path in sorted((root / d).glob("*.check.json")):
            if not re.search(a.match, rec_path.name):
                continue
            rec = json.loads(rec_path.read_text())
            out = root / a.out / Path(d).name / rec_path.name.replace(".check.json", "")
            cmd = command(rec, out) + shlex.split(a.extra)
            if CONFIG["dry_run"] and not a.run:
                print("[dry]", " ".join(cmd))
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
            out.with_suffix(".out").write_text(r.stdout + r.stderr)
            if r.returncode or not out.with_suffix(".bin").exists():
                print(f"FAIL {d}/{rec_path.name} ({out.with_suffix('.out')})")
                failed += 1
                continue
            h = hashlib.sha256(out.with_suffix(".bin").read_bytes()).hexdigest()
            ok = h == rec["sha256"]
            same += ok
            differ += not ok
            print(f"{'same' if ok else 'DIFF'} {d}/{rec_path.stem.replace('.check', '')} {h[:16]}")
    if not (CONFIG["dry_run"] and not a.run):
        print(f"summary: {same} identical, {differ} differ, {failed} failed")
        sys.exit(1 if differ or failed else 0)


if __name__ == "__main__":
    main()
