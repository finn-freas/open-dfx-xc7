import json
import sys
from pathlib import Path

CONFIG = {
    "overrides": ("rtl_dir", "ports_json", "fabric"),
}


def main():
    job = json.loads(Path(sys.argv[1]).read_text())
    flow = Path(job["flow"])
    sys.path.insert(0, str(flow))
    sys.argv = [str(flow / "region2v.py")] + job["argv"]
    import region2v
    for k in CONFIG["overrides"]:
        if k in job:
            region2v.CONFIG[k] = Path(job[k]) if k != "fabric" else job[k]
    region2v.main()


if __name__ == "__main__":
    main()
