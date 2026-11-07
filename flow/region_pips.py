import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "rm_prefix": "u_rm.",
    "max_listed": 10,
}


def top_module(d):
    for m in d["modules"].values():
        if any("NEXTPNR_BEL" in c.get("attributes", {}) for c in m.get("cells", {}).values()):
            return m
    sys.exit("no placed module in json")


def pips_of(routing):
    parts = routing.split(";")
    return [parts[i + 1] for i in range(0, len(parts) - 2, 3) if parts[i + 1]]


def classify(m, prefix):
    users = {}
    for name, c in m["cells"].items():
        rm = name.startswith(prefix)
        for bits in c.get("connections", {}).values():
            for b in bits:
                if isinstance(b, int):
                    users.setdefault(b, set()).add(rm)
    out = {}
    for name, n in m["netnames"].items():
        if "ROUTING" not in n.get("attributes", {}):
            continue
        kinds = set()
        for b in n["bits"]:
            kinds |= users.get(b, set())
        out[name] = "rm" if kinds == {True} else "static" if kinds == {False} else "boundary" if kinds else "none"
    return out


def main():
    ap = argparse.ArgumentParser(description="Count routed pips per net class (static, boundary, RM) inside and outside a region's tiles")
    ap.add_argument("routed_json")
    ap.add_argument("--region", default=CONFIG["region"])
    ap.add_argument("--rm-prefix", default=CONFIG["rm_prefix"])
    ap.add_argument("--json")
    a = ap.parse_args()
    grid = region.load_grid()
    tiles = region.region_tiles(grid, a.region)
    xy = {f"X{t['grid_x']}Y{t['grid_y']}": n for n, t in tiles.items()}
    int_xy = {k for k, n in xy.items() if tiles[n]["type"].startswith("INT_")}
    m = top_module(json.loads(Path(a.routed_json).read_text()))
    cls = classify(m, a.rm_prefix)
    stats = {}
    examples = {}
    for name, kind in cls.items():
        s = stats.setdefault(kind, {"nets": 0, "pips": 0, "pips_in_region": 0, "pips_in_region_int": 0,
                                    "pips_outside_region": 0, "nets_in_region": 0, "nets_outside_region": 0})
        s["nets"] += 1
        inside = outside = 0
        for p in pips_of(m["netnames"][name]["attributes"]["ROUTING"]):
            t = p.split("/", 1)[0]
            s["pips"] += 1
            if t in xy:
                inside += 1
                s["pips_in_region_int"] += t in int_xy
            else:
                outside += 1
        s["pips_in_region"] += inside
        s["pips_outside_region"] += outside
        s["nets_in_region"] += inside > 0
        s["nets_outside_region"] += outside > 0
        if kind == "static" and inside:
            examples.setdefault("static_in_region", []).append(name)
        if kind == "rm" and outside:
            examples.setdefault("rm_outside_region", []).append(name)
    print(f"{a.routed_json}")
    print(f"region {a.region}: {len(xy)} tiles ({len(int_xy)} INT)")
    for kind in ("static", "boundary", "rm", "none"):
        if kind in stats:
            print(f"  {kind:8s} {stats[kind]}")
    for k, v in examples.items():
        print(f"  {k}: {len(v)} nets, e.g. {v[:CONFIG['max_listed']]}")
    if a.json:
        Path(a.json).write_text(json.dumps({"routed_json": a.routed_json, "region": a.region, "stats": stats,
                                            "examples": {k: v[:100] for k, v in examples.items()}}, indent=1))


if __name__ == "__main__":
    main()
