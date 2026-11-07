import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region

CONFIG = {
    "exclude_prefixes": [],
    "pin_site_prefixes": ["SLICE_", "RAMB"],
    "tilde_bel_sites": ["RAMB"],
    "loc_site_prefixes": ["RAMB", "DSP48", "BUFGCTRL"],
}

SITE_RE = re.compile(r"([A-Z0-9_]+?)_X(\d+)Y(\d+)")


def top_module(d):
    for name, m in d["modules"].items():
        if any("NEXTPNR_BEL" in c.get("attributes", {}) for c in m.get("cells", {}).values()):
            return m
    sys.exit("no placed module in json")


def site_map(grid):
    out = {}
    for tname, t in grid.items():
        groups = {}
        for s in t.get("sites", {}):
            m = SITE_RE.fullmatch(s)
            if m:
                groups.setdefault(m.group(1), []).append((int(m.group(2)), int(m.group(3)), s))
        for prefix, sites in groups.items():
            x0 = min(x for x, _, _ in sites)
            y0 = min(y for _, y, _ in sites)
            for x, y, s in sites:
                out[s] = (f"X{t['grid_x']}Y{t['grid_y']}", f"{prefix}_X{x - x0}Y{y - y0}")
    return out


def learn_sites(m):
    learned = {}
    for n in m["netnames"].values():
        parts = n.get("attributes", {}).get("ROUTING", "").split(";")
        for i in range(0, len(parts) - 2, 3):
            w, p = parts[i], parts[i + 1]
            if w.startswith("SITEWIRE/") and p.count("/") == 2:
                site = w.split("/")[1]
                tile, dst = p.split("/")[0], p.split("/")[1]
                if "." in dst:
                    learned[site] = (tile, dst.split(".")[0])
    return learned


def to_generic_bel(bel, smap):
    site, _, b = bel.partition("/")
    if site not in smap:
        return bel
    tile, local = smap[site]
    if "~" not in b and any(site.startswith(p) for p in CONFIG["tilde_bel_sites"]):
        b = f"{b}~{b}"
    return f"{tile}/{local}.{b}"


def to_generic_wire(w, smap):
    if not w.startswith("SITEWIRE/"):
        return w
    _, site, pin = w.split("/", 2)
    if site not in smap:
        return w
    tile, local = smap[site]
    return f"{tile}/{local}.{pin}"


def convert_routing(r, smap, stats):
    parts = r.split(";")
    out = []
    for i in range(0, len(parts) - 2, 3):
        w, p, s = parts[i], parts[i + 1], parts[i + 2]
        gw = to_generic_wire(w, smap)
        if w.startswith("SITEWIRE/"):
            stats["site_wires"] += 1
            if p:
                dst = p.split("/")
                if len(dst) == 3 and gw != f"{dst[0]}/{dst[1]}":
                    stats["pip_mismatch"] += 1
                    if stats["pip_mismatch"] <= 5:
                        print(f"  check: wire {w} -> {gw}, pip {p}")
                elif len(dst) == 3:
                    stats["pip_agree"] += 1
        out += [gw, p, s]
    return ";".join(out)


def excluded(name, prefixes, keep):
    if any(re.fullmatch(k, name) for k in keep):
        return False
    return any(name.startswith(p) for p in prefixes)


def main():
    ap = argparse.ArgumentParser(description="Write -o preplaced / -o prerouted files from a nextpnr-xilinx --write json")
    ap.add_argument("routed_json")
    ap.add_argument("out_prefix")
    ap.add_argument("--exclude", action="append", default=list(CONFIG["exclude_prefixes"]),
                    help="drop cells and nets whose name starts with this (repeatable)")
    ap.add_argument("--keep", action="append", default=[],
                    help="regex of names kept even under an excluded prefix (repeatable)")
    a = ap.parse_args()
    out_cells = Path(a.out_prefix + ".preplaced")
    out_nets = Path(a.out_prefix + ".prerouted")
    if out_cells.exists() and out_nets.exists():
        print(f"[skip] {out_cells.name}, {out_nets.name} exist")
        return
    smap = site_map(region.load_grid())
    m = top_module(json.loads(Path(a.routed_json).read_text()))
    learned = learn_sites(m)
    differ = {s: (smap.get(s), v) for s, v in learned.items() if smap.get(s) != v}
    if differ:
        print(f"sites whose tile differs from tilegrid (routing wins): {len(differ)}, e.g. {list(differ.items())[:2]}")
    smap.update(learned)
    stats = {"site_wires": 0, "pip_agree": 0, "pip_mismatch": 0}
    nc = nn = 0
    locs = []
    with open(out_cells, "w") as f:
        for name, c in m["cells"].items():
            bel = c.get("attributes", {}).get("NEXTPNR_BEL")
            if not bel or excluded(name, a.exclude, a.keep):
                continue
            if any(bel.startswith(p) for p in CONFIG["loc_site_prefixes"]):
                locs.append(f"set_property LOC {bel.split('/')[0]} [get_cells {{{name}}}]")
            if not any(bel.startswith(p) for p in CONFIG["pin_site_prefixes"]):
                continue
            f.write(f"{name}\t{to_generic_bel(bel, smap)}\n")
            nc += 1
    Path(a.out_prefix + ".loc.xdc").write_text("".join(l + "\n" for l in locs))
    if locs:
        print(f"wrote {len(locs)} LOC constraints to {a.out_prefix}.loc.xdc")
    with open(out_nets, "w") as f:
        for name, n in m["netnames"].items():
            r = n.get("attributes", {}).get("ROUTING")
            if not r or excluded(name, a.exclude, a.keep):
                continue
            f.write(f"{name}\t{convert_routing(r, smap, stats)}\n")
            nn += 1
    print(f"wrote {nc} cells to {out_cells}, {nn} nets to {out_nets}; site wires {stats['site_wires']}, "
          f"pip agreement {stats['pip_agree']}, mismatches {stats['pip_mismatch']}")


if __name__ == "__main__":
    main()
