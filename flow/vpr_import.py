"""Turn a VPR placement (design.net + design.place from flow/vpr_run.sh) of a flow/vpr_export.py netlist back into
nextpnr bels: "<cell>\t<bel>" lines for nextpnr's -o place-import (SLICE_X..Y../A6LUT, .../AFF, .../CARRY4, .../F7AMUX,
RAMB36_X..Y../RAMB36E1). VPR clusters are mapped to sites with F4PGA's vpr_grid_map.csv; inside a slice the atom's
pb path gives the bel (A5LUT[1] -> A6LUT, A5LUT[0] -> A5LUT, REG_* -> AFF, FF_* -> A5FF). LUT atoms (.names) are named
by their output net in VPR, so they are matched to cells through vpr.json. Distributed RAM, I/O and clock buffers are
left to nextpnr. Bels are written in nextpnr's generic form (TILE/SITE_X0Y0.BEL, flow/replay_dump.py to_generic_bel);
REF_ROUTED (a routed JSON of the same device) supplies the routing-learned site->tile map.
usage: vpr_import.py VPRDIR OUT.txt [REF_ROUTED.json]"""
import collections
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import replay_dump

ROOT = Path(__file__).resolve().parent.parent
GRID = ROOT / "toolchain" / "vtr" / "arch" / "share" / "f4pga" / "arch" / "xc7a50t_test" / "vpr_grid_map.csv"
PFX = "ofxP"
LETTER = "ABCD"


def unpfx(n):
    return n[len(PFX):] if n.startswith(PFX) else n


def grid():
    g = collections.defaultdict(list)
    with open(GRID) as f:
        for r in csv.DictReader(f):
            g[(int(r["vpr_x"]), int(r["vpr_y"]))].append((r["site_name"], r["site_type"]))
    return g


def slice_site(g, x, y, sub):
    s = sorted([(int(re.search(r"X(\d+)", n).group(1)), n, t) for n, t in g[(x, y)] if t in ("SLICEL", "SLICEM")])
    if len(s) != 2:
        return None
    if s[0][2] != s[1][2]:
        want = "SLICEL" if sub == 0 else "SLICEM"
        return next(n for _, n, t in s if t == want)
    return s[sub][1]


def site_of(g, x, y, sub, kind):
    if kind in ("BLK-TL-SLICEL", "BLK-TL-SLICEM"):
        return slice_site(g, x, y, sub)
    if kind == "BLK-TL-BRAM_L":
        return next((n for n, t in g[(x, y)] if t == "RAMBFIFO36E1"), None)
    return None


def lut_nets(vj):
    """output-net name (as write_blif prints it) -> LUT cell name, from the exported netlist."""
    m = vj["modules"][next(iter(vj["modules"]))]
    bit_cell = {}
    for n, c in m["cells"].items():
        if c["type"] == "$lut":
            bit_cell[c["connections"]["Y"][0]] = n
    out = {}
    for name, nn in m["netnames"].items():
        bits = nn["bits"]
        for i, b in enumerate(bits):
            if b in bit_cell:
                out[name if len(bits) == 1 else f"{name}[{i}]"] = bit_cell[b]
    return out


def nextpnr_conventions(rows, ref, stats):
    """Keep VPR's slice for every cell but re-pick bels inside the slice the way nextpnr's packer clusters them
    (pack_lutffs): a lone LUT goes on the 6LUT of its letter, and a flip-flop whose D is the only load of a LUT's
    O6 (or a CARRY4 O output) in the same slice goes on that letter's full FF; other flip-flops keep VPR's bel
    when it is free, else take a free one. ref: nextpnr's packed netlist of the same design (a routed JSON)."""
    rows = dict(rows)
    by_site = collections.defaultdict(list)
    for c, b in rows.items():
        by_site[b.split("/")[0]].append(c)
    for site, cells in by_site.items():
        for x in LETTER:
            six = [c for c in cells if rows[c] == f"{site}/{x}6LUT"]
            five = [c for c in cells if rows[c] == f"{site}/{x}5LUT"]
            if five and not six:
                rows[five[0]] = f"{site}/{x}6LUT"
                stats["lut5_to_6"] += 1
    drv, users = {}, collections.Counter()
    for n, c in ref["cells"].items():
        for p, bits in c["connections"].items():
            for bt in bits:
                if not isinstance(bt, int):
                    continue
                if c["port_directions"].get(p) == "output":
                    drv[bt] = (n, p)
                else:
                    users[bt] += 1
    for site, cells in by_site.items():
        ffs = [c for c in cells if rows[c].endswith("FF")]
        if not ffs:
            continue
        want = {}
        for f in ffs:
            d = ref["cells"].get(f, {}).get("connections", {}).get("D", [None])[0]
            if d not in drv or users[d] != 1:
                continue
            dc, dp = drv[d]
            if dc not in rows or rows[dc].split("/")[0] != site:
                continue
            b = rows[dc].split("/")[1]
            if dp == "O6" and b.endswith("6LUT"):
                want[f] = f"{site}/{b[0]}FF"
            elif b == "CARRY4" and re.fullmatch(r"O[0-3]", dp):
                want[f] = f"{site}/{LETTER[int(dp[1])]}FF"
        taken = {}
        for f, b in want.items():
            if b not in taken:
                taken[b] = f
        free = [f"{site}/{x}FF" for x in LETTER] + [f"{site}/{x}5FF" for x in LETTER]
        rest = [f for f in ffs if f not in taken.values()]
        for f in rest:
            if rows[f] not in taken:
                taken[rows[f]] = f
        for f in rest:
            if taken.get(rows[f]) == f:
                continue
            b = next(b for b in free if b not in taken)
            taken[b] = f
            stats["ff_moved_in_slice"] += 1
        for b, f in taken.items():
            if rows[f] != b and f in want:
                stats["ff_paired"] += 1
            rows[f] = b
    return rows


def leaves(blk, path, cluster, acc):
    inst = blk.get("instance")
    kids = blk.findall("block")
    p = path + [inst]
    if not kids:
        if blk.get("name") != "open":
            acc.append((blk.get("name"), p, cluster))
        return
    for k in kids:
        if k.get("name") == "open":
            continue
        leaves(k, p, cluster, acc)


def main():
    vd, out = Path(sys.argv[1]), Path(sys.argv[2])
    g = grid()
    place = {}
    for ln in (vd / "design.place").read_text().splitlines():
        f = ln.split()
        if len(f) >= 4 and f[1].lstrip("-").isdigit() and not ln.startswith("#"):
            place[f[0]] = (int(f[1]), int(f[2]), int(f[3]))
    net = ET.parse(vd / "design.net").getroot()
    lnet = lut_nets(json.loads((vd / "vpr.json").read_text()))
    rows, stats = {}, collections.Counter()
    for cl in net.findall("block"):
        kind = cl.get("instance").split("[")[0]
        loc = place.get(cl.get("name"))
        if loc is None:
            stats["cluster_unplaced"] += 1
            continue
        site = site_of(g, *loc, kind)
        if site is None:
            stats[f"skip_cluster_{kind}"] += 1
            continue
        acc = []
        leaves(cl, [], cl.get("name"), acc)
        for name, path, _ in acc:
            if path[-1].startswith("lut["):
                path = path[:-1]
            leaf = path[-1].split("[")[0]
            idx = lambda s: int(re.search(r"\[(\d+)\]", s).group(1))
            if leaf.endswith("5LUT"):
                letter = leaf[0]
                cell = lnet.get(name)
                if cell is None:
                    stats["lut_unmatched"] += 1
                    continue
                m6 = re.match(r"(.*)\.fpga_lut_[01]$", cell)
                if m6:
                    rows.setdefault(unpfx(m6.group(1)), f"{site}/{letter}6LUT")
                else:
                    rows[unpfx(cell)] = f"{site}/{letter}{'6' if idx(path[-1]) == 1 else '5'}LUT"
                stats["lut"] += 1
            elif any(p.startswith(("FF_FD", "REG_FD")) for p in path):
                ffp = next(p for p in path if p.startswith(("FF_FD", "REG_FD")))
                rows[unpfx(name)] = f"{site}/{LETTER[idx(ffp)]}{'5' if ffp.startswith('FF_') else ''}FF"
                stats["ff"] += 1
            elif leaf == "CARRY4_VPR":
                rows[unpfx(name) + "$split$muxcy0$PACKED_CARRY4$"] = f"{site}/CARRY4"
                stats["carry4"] += 1
            elif leaf in ("F7AMUX", "F7BMUX", "F8MUX"):
                rows[unpfx(name)] = f"{site}/{leaf}"
                stats["muxf"] += 1
            elif leaf.startswith("RAMB36E1"):
                rows[unpfx(name)] = f"{site}/RAMB36E1"
                stats["ramb36"] += 1
            else:
                stats[f"other_{leaf}"] += 1
    (out.parent / (out.stem + "_vpr.txt")).write_text("".join(f"{c}\t{b}\n" for c, b in rows.items()))
    smap = replay_dump.site_map(region.load_grid())
    if len(sys.argv) > 3:
        ref = replay_dump.top_module(json.loads(Path(sys.argv[3]).read_text()))
        smap.update(replay_dump.learn_sites(ref))
        rows = nextpnr_conventions(rows, ref, stats)
    (out.parent / (out.stem + "_sites.txt")).write_text("".join(f"{c}\t{b}\n" for c, b in rows.items()))
    out.write_text("".join(f"{c}\t{replay_dump.to_generic_bel(b, smap)}\n" for c, b in rows.items()))
    print(f"{len(rows)} rows; " + ", ".join(f"{k} {v}" for k, v in sorted(stats.items())))


if __name__ == "__main__":
    main()
