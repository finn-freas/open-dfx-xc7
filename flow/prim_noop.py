import subprocess
import sys
import time
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "candidate": "build/nextpnr-build/ofx-prim/nextpnr-himbaechel",
    "out": "build/ofx_prim_noop",
    "designs": ["blinky", "rv_soc", "rv_ppa"],
}

sys.path.insert(0, str(CONFIG["root"] / "install"))
import noop_check


def compare_no_rerun(rows, key, top, ref_dir, cmd, ref_npnr, out, dry):
    cand = noop_check.build(noop_check.with_args(cmd, noop_check.ROOT / CONFIG["candidate"], out / "ofx"), out / "ofx", top, dry)
    ref = Path(ref_dir) / f"{top}.frames"
    if dry:
        return
    same = cand.exists() and cand.stat().st_size > 0 and cand.read_bytes() == ref.read_bytes()
    row = {"build": key, "ref": str(ref), "ofx": str(cand), "ofx_log": str(out / "ofx" / "nextpnr.log"),
           "result": "identical" if same else ("no-frames" if not cand.exists() or cand.stat().st_size == 0 else "differs")}
    print(f"{row['result']:>20}  {key}", flush=True)
    rows.append(row)


def wait_for_nextpnr_slot():
    while int(subprocess.run(["pgrep", "-c", "nextpnr"], capture_output=True, text=True).stdout.strip() or 0) >= 2:
        time.sleep(20)


def main():
    noop_check.compare = compare_no_rerun
    noop_check.wait_for_slot = wait_for_nextpnr_slot
    noop_check.CONFIG["candidate"] = CONFIG["candidate"]
    noop_check.CONFIG["out"] = CONFIG["out"]
    argv = sys.argv[1:]
    if "--only" not in argv:
        argv += ["--only"] + CONFIG["designs"]
    sys.argv = ["noop_check.py"] + argv
    noop_check.main()


if __name__ == "__main__":
    main()
