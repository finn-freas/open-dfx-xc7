import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import replay_dump

CONFIG = {
    "routethru": re.compile(r"(CLBL[LM]_(?:L|LL|M)_[A-D])/(CLBL[LM]_(?:L|LL|M)_[A-D])[1-6]$"),
    "max_listed": 10,
}


def main():
    ap = argparse.ArgumentParser(description="List LUT route-through pips inside reconfigurable regions, per net class "
                                             "(held: every cell on the net placed in that region; crossing: anything else)")
    ap.add_argument("routed_json", nargs="+")
    ap.add_argument("--rp", nargs=2, action="append", required=True, metavar=("NAME", "REGION"))
    ap.add_argument("--json")
    a = ap.parse_args()
    grid = region.load_grid()
    tiles = {pfx: {f"X{t['grid_x']}Y{t['grid_y']}" for t in region.region_tiles(grid, spec).values()} for pfx, spec in a.rp}
    ranges = {pfx: region.parse_ranges(spec) for pfx, spec in a.rp}
    report = {}
    bad = 0
    for js in a.routed_json:
        m = replay_dump.top_module(json.loads(Path(js).read_text()))
        owner = {}
        for name, c in m["cells"].items():
            site = c.get("attributes", {}).get("NEXTPNR_BEL", "").split("/")[0]
            where = next((p for p, spec in a.rp if region.in_ranges(site, ranges[p])), None)
            for bits in c.get("connections", {}).values():
                for b in bits:
                    if isinstance(b, int):
                        owner.setdefault(b, set()).add(where)
        held = crossing = 0
        examples = []
        for name, n in m["netnames"].items():
            r = n.get("attributes", {}).get("ROUTING")
            if not r:
                continue
            parts = r.split(";")
            for i in range(0, len(parts) - 2, 3):
                p = parts[i + 1]
                if not p or p.count("/") != 2:
                    continue
                t, rest = p.split("/", 1)
                rp = next((pfx for pfx, ts in tiles.items() if t in ts), None)
                if rp is None or not CONFIG["routethru"].match(rest):
                    continue
                m1 = CONFIG["routethru"].match(rest)
                if m1.group(1) != m1.group(2):
                    continue
                kinds = set()
                for b in n["bits"]:
                    kinds |= owner.get(b, set())
                if kinds == {rp}:
                    held += 1
                else:
                    crossing += 1
                    examples.append(f"{name}: {p}")
        bad += crossing
        report[js] = {"held": held, "crossing": crossing, "examples": examples[:100]}
        print(f"{js}: LUT route-throughs in regions: {held} on nets held in their region, {crossing} on other nets"
              + "".join(f"\n   {e}" for e in examples[:CONFIG["max_listed"]]))
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
