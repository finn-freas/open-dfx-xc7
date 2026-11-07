import argparse
import re
from pathlib import Path

CONFIG = {
    "pip": r"^(?P<tile>[A-Z0-9_]+_X\d+Y\d+)/(?P<type>[A-Z0-9_]+)\.(?P<src>[A-Za-z0-9_]+)(?P<dir><<->>|->>|->)(?P<dst>[A-Za-z0-9_]+)$",
}


def features(path, owner=None):
    out = set()
    for line in Path(path).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) != 3 or (owner and parts[0] != owner):
            continue
        m = re.match(CONFIG["pip"], parts[2])
        if not m:
            continue
        out.add(f"{m['tile']}.{m['dst']}.{m['src']}")
        if m["dir"] == "<<->>":
            out.add(f"{m['tile']}.{m['src']}.{m['dst']}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Convert a Vivado pip dump (vivado/dump_pips.tcl: owner, net, pip per line) "
                                             "to FASM pip features TILE.DST.SRC, for partial.py --static-pip-list")
    ap.add_argument("pips")
    ap.add_argument("out")
    ap.add_argument("--owner", help="keep only lines of this owner column (static or rm)")
    a = ap.parse_args()
    f = sorted(features(a.pips, a.owner))
    Path(a.out).write_text("\n".join(f) + "\n")
    print(f"wrote {a.out}: {len(f)} pip features")


if __name__ == "__main__":
    main()
