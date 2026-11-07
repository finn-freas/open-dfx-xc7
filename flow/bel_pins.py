import argparse
import json
import sys
from pathlib import Path

CONFIG = {
    "prefix": "u_rm.",
}


def main():
    ap = argparse.ArgumentParser(description="List cells carrying a BEL attribute in a yosys json, as a -o preplaced file")
    ap.add_argument("synth_json")
    ap.add_argument("out")
    ap.add_argument("--prefix", default=CONFIG["prefix"])
    a = ap.parse_args()
    d = json.loads(Path(a.synth_json).read_text())
    n = 0
    with open(a.out, "w") as f:
        for mod in d["modules"].values():
            for name, c in mod.get("cells", {}).items():
                b = c.get("attributes", {}).get("BEL")
                if b and name.startswith(a.prefix):
                    f.write(f"{name}\t{b}\n")
                    n += 1
    print(f"wrote {n} pinned cells to {a.out}")
    if not n:
        sys.exit(1)


if __name__ == "__main__":
    main()
