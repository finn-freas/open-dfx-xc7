import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import replay_dump

CONFIG = {
    "areas": ("outside",),
    "filters": ("all", "static"),
    "max_listed": 10,
}


def tile_xy_set(grid, spec):
    return {f"X{t['grid_x']}Y{t['grid_y']}" for t in region.region_tiles(grid, spec).values()}


def entry_tile(wire, pip):
    return (pip or wire).split("/", 1)[0]


def in_area(tile, area, region_tiles):
    if area == "outside":
        return not any(tile in ts for ts in region_tiles.values())
    return tile in region_tiles[area]


def name_ok(name, flt, prefixes, keep):
    if flt == "all":
        return True
    return not replay_dump.excluded(name, prefixes, keep)


def main():
    ap = argparse.ArgumentParser(description="Write -o preplaced / -o prerouted files that take each area of the device "
                                             "(outside every region, or one region) from its own reference build")
    ap.add_argument("out_prefix")
    ap.add_argument("--region", action="append", required=True, help="every reconfigurable region (repeatable)")
    ap.add_argument("--source", nargs=3, action="append", required=True, metavar=("ROUTED_JSON", "AREA", "FILTER"),
                    help="AREA is 'outside' or one of the --region specs; FILTER is 'all' or 'static' (drops names under "
                         "--rp-prefix unless --keep matches); repeatable, earlier sources win a wire")
    ap.add_argument("--rp-prefix", action="append", default=[])
    ap.add_argument("--keep", action="append", default=[])
    ap.add_argument("--no-cells", action="append", default=[], metavar="AREA",
                    help="take no cells from the sources of this area (repeatable)")
    a = ap.parse_args()
    out_cells = Path(a.out_prefix + ".preplaced")
    out_nets = Path(a.out_prefix + ".prerouted")
    if out_cells.exists() and out_nets.exists():
        print(f"[skip] {out_cells.name}, {out_nets.name} exist")
        return
    grid = region.load_grid()
    region_tiles = {spec: tile_xy_set(grid, spec) for spec in a.region}
    specs = list(region_tiles)
    for i in range(len(specs)):
        for j in range(i + 1, len(specs)):
            common = region_tiles[specs[i]] & region_tiles[specs[j]]
            if common:
                sys.exit(f"regions {specs[i]} and {specs[j]} share {len(common)} tile(s), e.g. {sorted(common)[:3]}")
    for js, area, flt in a.source:
        if area not in CONFIG["areas"] and area not in region_tiles:
            sys.exit(f"area {area} is neither 'outside' nor a --region")
        if flt not in CONFIG["filters"]:
            sys.exit(f"filter {flt} not in {CONFIG['filters']}")
    base_smap = replay_dump.site_map(grid)
    cells = {}
    locs = []
    nets = {}
    conflicts = []
    for js, area, flt in a.source:
        m = replay_dump.top_module(json.loads(Path(js).read_text()))
        smap = dict(base_smap)
        smap.update(replay_dump.learn_sites(m))
        stats = {"site_wires": 0, "pip_agree": 0, "pip_mismatch": 0}
        nc = ne = nn = 0
        take_cells = area not in a.no_cells
        for name, c in m["cells"].items():
            bel = c.get("attributes", {}).get("NEXTPNR_BEL")
            if not take_cells or not bel or not name_ok(name, flt, a.rp_prefix, a.keep):
                continue
            gbel = replay_dump.to_generic_bel(bel, smap)
            if not in_area(gbel.split("/", 1)[0], area, region_tiles):
                continue
            if any(bel.startswith(p) for p in replay_dump.CONFIG["loc_site_prefixes"]):
                locs.append(f"set_property LOC {bel.split('/')[0]} [get_cells {{{name}}}]")
            if not any(bel.startswith(p) for p in replay_dump.CONFIG["pin_site_prefixes"]):
                continue
            if name in cells and cells[name] != gbel:
                conflicts.append(f"cell {name}: {cells[name]} vs {gbel} ({js})")
                continue
            cells[name] = gbel
            nc += 1
        for name, n in m["netnames"].items():
            r = n.get("attributes", {}).get("ROUTING")
            if not r or not name_ok(name, flt, a.rp_prefix, a.keep):
                continue
            parts = replay_dump.convert_routing(r, smap, stats).split(";")
            got = 0
            dst = nets.setdefault(name, {})
            for i in range(0, len(parts) - 2, 3):
                w, p, s = parts[i], parts[i + 1], parts[i + 2]
                if not in_area(entry_tile(w, p), area, region_tiles):
                    continue
                if w in dst:
                    if dst[w][0] != p:
                        conflicts.append(f"net {name} wire {w}: pip {dst[w][0]!r} vs {p!r} ({js})")
                    continue
                dst[w] = (p, s)
                got += 1
            ne += got
            nn += got > 0
        print(f"source {js} area {area} filter {flt}: {nc} cells, {nn} nets, {ne} route entries; "
              f"pip agreement {stats['pip_agree']}, mismatches {stats['pip_mismatch']}")
    if conflicts:
        for c in conflicts[:CONFIG["max_listed"]]:
            print(f"  conflict {c}")
        sys.exit(f"{len(conflicts)} conflict(s) between sources")
    with open(out_cells, "w") as f:
        for name, bel in cells.items():
            f.write(f"{name}\t{bel}\n")
    Path(a.out_prefix + ".loc.xdc").write_text("".join(l + "\n" for l in dict.fromkeys(locs)))
    nn = 0
    with open(out_nets, "w") as f:
        for name, ws in nets.items():
            if not ws:
                continue
            f.write(f"{name}\t" + ";".join(f"{w};{p};{s}" for w, (p, s) in ws.items()) + "\n")
            nn += 1
    print(f"wrote {len(cells)} cells to {out_cells}, {nn} nets to {out_nets}, {len(dict.fromkeys(locs))} LOC constraints")


if __name__ == "__main__":
    main()
