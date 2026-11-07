import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import replay_dump
import xroute

CONFIG = {
    "place_prefixes": ("SLICE_", "RAMB", "DSP48"),
    "skip_net_types": {"VCC", "GND"},
}


def load_tsv(p):
    return [ln.split("\t") for ln in Path(p).read_text().splitlines() if ln]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_dir")
    ap.add_argument("ref_routed_json")
    ap.add_argument("out_prefix")
    a = ap.parse_args()
    ex = Path(a.export_dir)
    grid = region.load_grid()
    tile_xy = {k: f"X{v['grid_x']}Y{v['grid_y']}" for k, v in grid.items()}
    m = replay_dump.top_module(json.loads(Path(a.ref_routed_json).read_text()))
    smap = replay_dump.site_map(grid)
    smap.update(replay_dump.learn_sites(m))
    st = Counter()

    vc = {}
    for f in load_tsv(ex / "cells.tsv"):
        name, typ, site, bel, stype, rthru = f[:6]
        if rthru == "1":
            continue
        vc[name] = (typ, site, bel)
    macro_site = {}
    for name, (typ, site, bel) in vc.items():
        if "/" in name:
            macro_site.setdefault(name.rsplit("/", 1)[0], site)
    lines = []
    for n, c in m["cells"].items():
        nbel = c["attributes"].get("NEXTPNR_BEL", "")
        if not nbel.startswith(CONFIG["place_prefixes"]):
            st["cell_skip_type"] += 1
            continue
        key = n
        mc = re.match(xroute.CONFIG["carry_re"], n)
        if c["type"] == "CARRY4" and mc:
            key = mc.group(1) if mc.group(2) == "0" else None
            if key is None:
                st["cell_carry_split"] += 1
                continue
        if key in vc:
            _, site, bel = vc[key]
            if site.startswith("RAMB") and "~" not in bel:
                pass
            st["cell_direct"] += 1
        elif "/" in n and n.rsplit("/", 1)[0] in macro_site:
            site, bel = macro_site[n.rsplit("/", 1)[0]], nbel.split("/")[1]
            st["cell_macro"] += 1
        else:
            st["cell_nextpnr_only"] += 1
            continue
        lines.append(f"{n}\t{replay_dump.to_generic_bel(f'{site}/{bel}', smap)}\n")
    Path(a.out_prefix + ".preplaced").write_text("".join(lines))

    src_wire = {}
    for f in load_tsv(ex / "cells.tsv"):
        if len(f) > 7 and f[7]:
            for item in f[7].split(","):
                lp, sw, net = item.split(":", 2)
                if net:
                    src_wire.setdefault(net, f"SITEWIRE/{f[2]}/{sw}")
    site_pips = defaultdict(list)
    for f in load_tsv(ex / "sitepips.tsv"):
        site, _, _, _, _, net, win, wout = f
        if not net or site not in smap:
            continue
        xy, local = smap[site]
        site_pips[net].append((f"SITEWIRE/{site}/{wout}", f"{xy}/{local}.{wout}/{local}.{win}"))
    pins = defaultdict(list)
    for f in load_tsv(ex / "pins.tsv"):
        net, site, pin, d, tile, tw, sw = (f + [""] * 7)[:7]
        if site not in smap or not sw or tile not in tile_xy:
            st["pin_unmapped"] += 1
            continue
        xy, local = smap[site]
        txy = tile_xy[tile]
        if d == "out":
            pins[net].append((f"{txy}/{tw}", f"{txy}/{tw}/{local}.{sw}"))
        else:
            pins[net].append((f"{f'SITEWIRE/{site}/{sw}'}", f"{xy}/{local}.{sw}/{tw}"))
    names = set(m["netnames"])
    out = []
    for f in load_tsv(ex / "nets.tsv"):
        net, typ, pips = f[0], f[1], f[2:]
        if typ in CONFIG["skip_net_types"] or not pips:
            st["net_skip_static_or_unrouted"] += 1
            continue
        if net not in names:
            st["net_not_in_nextpnr"] += 1
            continue
        if net not in src_wire:
            st["net_no_source_wire"] += 1
            continue
        parts = [src_wire[net], "", "1"]
        for w, p in site_pips.get(net, []):
            parts += [w, p, "1"]
        for w, p in pins.get(net, []):
            parts += [w, p, "1"]
        bad = False
        for p in pips:
            rev = "<" in p
            tile, rest = p.split("/", 1)
            w0, w1 = re.split(r"[/<]", rest, maxsplit=1)
            if rev:
                w0, w1 = w1, w0
            if tile not in tile_xy:
                bad = True
                break
            parts += [f"{tile_xy[tile]}/{w1}", f"{tile_xy[tile]}/{w1}/{w0}", "1"]
        if bad:
            st["net_unmapped_tile"] += 1
            continue
        out.append(f"{net}\t{';'.join(parts)}\n")
        st["net_written"] += 1
        st["pips_written"] += len(pips)
    Path(a.out_prefix + ".prerouted").write_text("".join(out))
    Path(a.out_prefix + ".stats.json").write_text(json.dumps(dict(st), indent=1) + "\n")
    print(dict(st))


if __name__ == "__main__":
    main()
