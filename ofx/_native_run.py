import json
import os
import sys
from pathlib import Path

CONFIG = {
    "design_name": "ofx",
}


def main():
    job = json.loads(Path(sys.argv[1]).read_text())
    flow = Path(job["flow"])
    sys.path.insert(0, str(flow))
    sys.argv = [str(flow / "build_pr_native.py"), "--design", CONFIG["design_name"]] + job["argv"]
    import build_pr_native as b
    b.CONFIG["designs"][CONFIG["design_name"]] = job["design"]
    b.CONFIG["chipdb"] = job["chipdb"]
    if job.get("db_root"):
        b.CONFIG["variants"][job["variant"]]["db_root"] = job["db_root"]
    if job.get("npwait"):
        var = b.CONFIG["variants"][job["variant"]]
        os.environ["OFX_NEXTPNR_BIN"] = str(b.ROOT / var["nextpnr"])
        var["nextpnr"] = job["npwait"]
    b.main()


if __name__ == "__main__":
    main()
