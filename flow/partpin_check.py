import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import partpins

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "rm_prefix": "u_rm.",
    "lut_types": ["SLICE_LUTX"],
    "ff_types": ["SLICE_FFX"],
}


def pips(routing):
    return {p for _, p, _ in partpins.entries(routing) if p}


def main():
    ap = argparse.ArgumentParser(description="Per build: the partition-pin nets' pips outside the region equal their locked "
                                             "route, the pin wire is on the route, and the module's cells by type")
    ap.add_argument("partpins_json")
    ap.add_argument("prerouted", help="the cut .prerouted the module builds were given")
    ap.add_argument("routed_json", nargs="+")
    ap.add_argument("--region", default=CONFIG["region"])
    ap.add_argument("--rm-prefix", default=CONFIG["rm_prefix"])
    ap.add_argument("--json")
    a = ap.parse_args()
    grid = region.load_grid()
    inside = {f"X{t['grid_x']}Y{t['grid_y']}" for t in region.region_tiles(grid, a.region).values()}
    pins = json.loads(Path(a.partpins_json).read_text())["pins"]
    locked = dict(l.split("\t", 1) for l in Path(a.prerouted).read_text().splitlines() if "\t" in l)
    res = {}
    ok = True
    for rj in a.routed_json:
        m = partpins.top_module(json.loads(Path(rj).read_text()))
        nn = m["netnames"]
        bad_out, bad_pin = [], []
        for p in pins:
            r = nn.get(p["net"], {}).get("attributes", {}).get("ROUTING", "")
            have = pips(r)
            outside = {x for x in have if x.split("/", 1)[0] not in inside}
            want = pips(locked[p["net"]])
            if outside != want:
                bad_out.append(p["net"])
            if p["wire"] not in {w for w, _, _ in partpins.entries(r)}:
                bad_pin.append(p["net"])
        cells = collections.Counter(c["type"] for n, c in m["cells"].items() if n.startswith(a.rm_prefix))
        row = {"nets": len(pins), "nets_outside_route_differs": bad_out, "nets_pin_not_on_route": bad_pin,
               "rm_cells_by_type": dict(sorted(cells.items())),
               "luts": sum(cells[t] for t in CONFIG["lut_types"]), "ffs": sum(cells[t] for t in CONFIG["ff_types"])}
        res[rj] = row
        good = not bad_out and not bad_pin
        ok &= good
        print(f"{'PASS' if good else 'FAIL'} {rj}: {len(pins)} partition-pin nets, outside route == locked route for "
              f"{len(pins) - len(bad_out)}, pin wire on route for {len(pins) - len(bad_pin)}; module cells: LUT {row['luts']}, "
              f"FF {row['ffs']}, {dict(sorted(cells.items()))}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
