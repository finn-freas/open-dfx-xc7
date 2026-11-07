"""Incremental place and route against a reference build (like Vivado's read_checkpoint -incremental).

Given the reference build's yosys JSON and nextpnr --write JSON and the yosys JSON of a changed design, this
matches the changed design's cells and nets to the reference's by structure anchored on hierarchical (public)
net names, renames the matched ones to their reference names, and writes the files nextpnr-xilinx's
-o preplaced / -o prerouted replay takes, restricted to what is unchanged:

  <out>/<top>.json          the new netlist, matched cells and nets under their reference names
  <out>/inc.preplaced       reference bels of the matched cells (and the packer cells built from them)
  <out>/inc.prerouted       reference routes of the nets whose driver is matched
  <out>/inc.xdc             the user XDC plus LOC lines for matched block RAM / DSP / BUFG cells
  <out>/match.json          what was matched and why the rest was not

Why structure and not just cell names: yosys numbers its internal cells and nets ($abc$123$...), and a small
RTL edit renumbers most of them. Register outputs and ports keep their HDL names, so a cell's identity here is
its type, parameters, the names of the nets it reads, and (through unnamed nets) the cells feeding it, up to
CONFIG["rounds"] levels: a cell whose function and inputs did not change keeps its label.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

CONFIG = {
    "rounds": 8,
    "new_suffix": "$ofx_inc_new",
    "loc_site_prefixes": ["RAMB", "DSP48", "BUFGCTRL"],
    "skip_cell_types": ["$scopeinfo"],
    "ripple": 0,
    "ripple_max_fanout": 16,
}


def H(*parts):
    return hashlib.blake2b(repr(parts).encode(), digest_size=10).hexdigest()


def top_module(d, top=None):
    mods = d["modules"]
    if top and top in mods:
        return top, mods[top]
    for name, m in mods.items():
        if str(m.get("attributes", {}).get("top", "0")).strip("0") != "":
            return name, m
    cand = [(n, m) for n, m in mods.items() if m.get("cells")]
    return cand[-1]


def bit_name(base, i, width, offset=0, upto=False):
    if width == 1 and offset == 0:
        return base
    return f"{base}[{offset + width - i - 1 if upto else offset + i}]"


def nn_offset(nn):
    return int(nn.get("offset", 0))


def nn_upto(nn):
    return bool(int(nn.get("upto", 0)))


def lut_canonical(c, ins):
    """A LUT's function with its inputs sorted by label, so a LUT whose pins abc permuted keeps its identity"""
    m = re.fullmatch(r"LUT([1-6])", c["type"])
    init = str(c.get("parameters", {}).get("INIT", ""))
    if not m or not init or set(init) - {"0", "1"}:
        return None
    k = int(m.group(1))
    labs = dict(ins)
    pins = [labs.get(f"I{i}", ("?",))[0] for i in range(k)]
    v = int(init, 2)
    perm = sorted(range(k), key=lambda i: pins[i])
    out = 0
    for idx in range(1 << k):
        old = sum(((idx >> j) & 1) << perm[j] for j in range(k))
        if (v >> old) & 1:
            out |= 1 << idx
    return ("LUT", k, out, tuple(pins[i] for i in perm))


class Netlist:
    def __init__(self, mod):
        self.mod = mod
        self.cells = {n: c for n, c in mod["cells"].items() if c["type"] not in CONFIG["skip_cell_types"]}
        self.anchor = {}
        for name, nn in sorted(mod["netnames"].items()):
            if name.startswith("$"):
                continue
            bits = nn["bits"]
            for i, b in enumerate(bits):
                if isinstance(b, int):
                    s = "N:" + bit_name(name, i, len(bits), nn_offset(nn), nn_upto(nn))
                    if b not in self.anchor or s < self.anchor[b]:
                        self.anchor[b] = s
        for pname, p in mod.get("ports", {}).items():
            for i, b in enumerate(p["bits"]):
                if isinstance(b, int):
                    self.anchor[b] = "P:" + bit_name(pname, i, len(p["bits"]))
        self.driver = {}
        self.sinks = defaultdict(list)
        for cn, c in self.cells.items():
            for p, bits in c["connections"].items():
                d = c.get("port_directions", {}).get(p, "input")
                for i, b in enumerate(bits):
                    if not isinstance(b, int):
                        continue
                    if d in ("output", "inout"):
                        self.driver[b] = (cn, p, i)
                    if d in ("input", "inout"):
                        self.sinks[b].append((cn, p, i))

    def labels(self, rounds):
        lab = dict(self.anchor)
        cl = {}
        static = {}
        for cn, c in self.cells.items():
            static[cn] = (c["type"], json.dumps(c.get("parameters", {}), sort_keys=True))
        for _ in range(rounds):
            for cn, c in self.cells.items():
                ins, outs = [], []
                for p in sorted(c["connections"]):
                    bits = c["connections"][p]
                    d = c.get("port_directions", {}).get(p, "input")
                    if d == "input":
                        ins.append((p, tuple(lab.get(b, "?") if isinstance(b, int) else "C" + b for b in bits)))
                    else:
                        outs.append((p, tuple(self.anchor.get(b, "") if isinstance(b, int) else "C" + b
                                              for b in bits)))
                lut = lut_canonical(c, ins)
                cl[cn] = H(lut, tuple(outs)) if lut else H(static[cn], tuple(ins), tuple(outs))
            for b, (cn, p, i) in self.driver.items():
                if b not in self.anchor:
                    lab[b] = H(cl[cn], p, i)
        return cl, lab

    def fanout_labels(self, cl, lab):
        out = {}
        for cn, c in self.cells.items():
            fo = []
            for p in sorted(c["connections"]):
                d = c.get("port_directions", {}).get(p, "input")
                if d == "input":
                    continue
                for b in c["connections"][p]:
                    if isinstance(b, int):
                        fo.append(tuple(sorted((cl[s], sp, si) for s, sp, si in self.sinks.get(b, []))))
            out[cn] = H(cl[cn], tuple(fo))
        return out


def match(ref, new, rounds):
    rl, _ = ref.labels(rounds)
    nl, _ = new.labels(rounds)
    pairs = {}
    reasons = defaultdict(int)

    def unique_pairs(rlab, nlab, rset, nset):
        rg, ng = defaultdict(list), defaultdict(list)
        for c in rset:
            rg[rlab[c]].append(c)
        for c in nset:
            ng[nlab[c]].append(c)
        got, amb = {}, []
        for k, rs in rg.items():
            ns = ng.get(k)
            if not ns:
                continue
            if len(rs) == 1 and len(ns) == 1:
                got[ns[0]] = rs[0]
            elif len(rs) == len(ns):
                byname = set(rs) & set(ns)
                for n in byname:
                    got[n] = n
                if len(rs) - len(byname) > 0:
                    amb.append(k)
            else:
                amb.append(k)
        return got, amb

    got, amb = unique_pairs(rl, nl, ref.cells, new.cells)
    pairs.update(got)
    if amb:
        rfo = ref.fanout_labels(rl, None)
        nfo = new.fanout_labels(nl, None)
        rleft = [c for c in ref.cells if c not in set(pairs.values())]
        nleft = [c for c in new.cells if c not in pairs]
        got2, amb2 = unique_pairs(rfo, nfo, rleft, nleft)
        pairs.update(got2)
        reasons["ambiguous_label_groups"] = len(amb2)
    return pairs, rl, nl


def bitmap_of(ref, new, pairs):
    m = {}
    for nc, rc in pairs.items():
        rcell, ncell = ref.cells[rc], new.cells[nc]
        for p, rbits in rcell["connections"].items():
            if rcell.get("port_directions", {}).get(p) not in ("output", "inout"):
                continue
            nbits = ncell["connections"].get(p, [])
            for rb, nb in zip(rbits, nbits):
                if isinstance(rb, int) and isinstance(nb, int):
                    m[rb] = nb
    for pname, p in ref.mod.get("ports", {}).items():
        np_ = new.mod.get("ports", {}).get(pname)
        if np_ and np_.get("direction") == p.get("direction"):
            for rb, nb in zip(p["bits"], np_["bits"]):
                if isinstance(rb, int) and isinstance(nb, int):
                    m.setdefault(rb, nb)
    return m


def rewrite(ref, new, pairs, bmap):
    mod = json.loads(json.dumps(new.mod))
    ref_names = set(ref.mod["cells"])
    taken = set(pairs.values())
    cells = {}
    renamed_new = 0
    for name, c in mod["cells"].items():
        if name in pairs:
            cells[pairs[name]] = c
        elif name in ref_names or name in taken:
            cells[name + CONFIG["new_suffix"]] = c
            renamed_new += 1
        else:
            cells[name] = c
    mod["cells"] = cells
    mapped_new_bits = set(bmap.values())
    nets = {}
    for name, nn in ref.mod["netnames"].items():
        bits = [bmap.get(b, "x") if isinstance(b, int) else b for b in nn["bits"]]
        if any(isinstance(b, int) for b in bits):
            e = dict(nn)
            e["bits"] = bits
            nets[name] = e
    for name, nn in new.mod["netnames"].items():
        bits = ["x" if (isinstance(b, int) and b in mapped_new_bits) else b for b in nn["bits"]]
        if not any(isinstance(b, int) for b in bits):
            continue
        if name in nets:
            old = nets[name]
            same_shape = (len(old["bits"]) == len(bits) and nn_offset(old) == nn_offset(nn)
                          and nn_upto(old) == nn_upto(nn))
            if same_shape:
                merged = [ob if isinstance(ob, int) else b for ob, b in zip(old["bits"], bits)]
                clash = any(isinstance(ob, int) and isinstance(b, int) for ob, b in zip(old["bits"], bits))
                if not clash:
                    old["bits"] = merged
                    continue
            name = name + CONFIG["new_suffix"]
        e = dict(nn)
        e["bits"] = bits
        nets[name] = e
    mod["netnames"] = nets
    return mod, renamed_new


def routed_top(path):
    _, m = top_module(json.loads(Path(path).read_text()))
    if not any("NEXTPNR_BEL" in c.get("attributes", {}) for c in m["cells"].values()):
        for mm in json.loads(Path(path).read_text())["modules"].values():
            if any("NEXTPNR_BEL" in c.get("attributes", {}) for c in mm.get("cells", {}).values()):
                return mm
    return m


def net_drivers(m):
    drv = {}
    for cn, c in m["cells"].items():
        for p, bits in c.get("connections", {}).items():
            if c.get("port_directions", {}).get(p) == "output":
                for b in bits:
                    if isinstance(b, int):
                        drv[b] = cn
    return drv


def write_replay(routed, ref, pairs, out, xdc_text, ripple=0, whole_tiles=False):
    import replay_dump as rd
    import region
    smap = rd.site_map(region.load_grid())
    smap.update(rd.learn_sites(routed))
    unmatched_ref = set(ref.cells) - set(pairs.values())
    matched_ref = set(pairs.values())
    stats = defaultdict(int)
    drv = net_drivers(routed)
    cells = routed["cells"]
    keep = {n for n in cells if n in matched_ref or cells[n]["type"].startswith("PSEUDO_")}
    packer = [n for n in cells if n not in ref.cells and n not in keep]
    changed = True
    while changed:
        changed = False
        for n in packer:
            if n in keep:
                continue
            bits = [b for bits in cells[n].get("connections", {}).values() for b in bits if isinstance(b, int)]
            if all(drv.get(b) is None or drv.get(b) in keep or drv.get(b) == n for b in bits):
                keep.add(n)
                changed = True
    site_of = {n: c.get("attributes", {}).get("NEXTPNR_BEL", "").split("/")[0] for n, c in cells.items()}
    bad_sites = {site_of[n] for n in cells if n not in keep and site_of[n]}
    stats["packer_cells_dropped"] = sum(1 for n in packer if n not in keep)
    stats["sites_with_a_change"] = len(bad_sites)
    on_net = defaultdict(set)
    for n, c in cells.items():
        for bits in c.get("connections", {}).values():
            for b in bits:
                if isinstance(b, int):
                    on_net[b].add(n)
    frontier = {n for n in cells if n not in keep}
    for _ in range(ripple):
        nxt = set()
        for n in frontier:
            for bits in cells[n].get("connections", {}).values():
                for b in bits:
                    if isinstance(b, int) and len(on_net[b]) <= CONFIG["ripple_max_fanout"]:
                        nxt |= on_net[b]
        nxt -= frontier
        for n in nxt:
            if site_of.get(n) and not cells[n]["type"].startswith(("PSEUDO_", "PAD", "IOB")):
                bad_sites.add(site_of[n])
        frontier |= nxt
    tile_of = {s: (smap[s][0] if s in smap else s) for s in set(site_of.values()) if s}
    bad_tiles = {tile_of[s] for s in bad_sites if s in tile_of} if whole_tiles else set()
    chain = {}

    def root(n):
        while chain.get(n, n) != n:
            n = chain[n]
        return n
    carries = [n for n, c in cells.items() if c["type"] == "CARRY4"]
    co_of = {}
    for n in carries:
        for p, bits in cells[n].get("connections", {}).items():
            if p.startswith("CO") or p == "COUT":
                for b in bits:
                    if isinstance(b, int):
                        co_of[b] = n
    for n in carries:
        for p, bits in cells[n].get("connections", {}).items():
            if p in ("CI", "CIN"):
                for b in bits:
                    if isinstance(b, int) and b in co_of:
                        chain[root(n)] = root(co_of[b])
    members = defaultdict(list)
    for n in carries:
        members[root(n)].append(n)
    grew = True
    while grew:
        grew = False
        for ms in members.values():
            ss = {site_of[m] for m in ms if site_of.get(m)}
            ts = {tile_of.get(s) for s in ss}
            if whole_tiles and ts & bad_tiles and not ts <= bad_tiles:
                bad_tiles |= ts
                grew = True
            if not whole_tiles and ss & bad_sites and not ss <= bad_sites:
                bad_sites |= ss
                grew = True
    bad_sites |= {s for s, t in tile_of.items() if t in bad_tiles}
    stats["sites_replaced"] = len(bad_sites)
    stats["tiles_replaced"] = len(bad_tiles)
    keep_cells = set()
    locs = []
    with open(out / "inc.preplaced", "w") as f:
        for name, c in routed["cells"].items():
            bel = c.get("attributes", {}).get("NEXTPNR_BEL")
            if not bel:
                continue
            if name in unmatched_ref:
                stats["cells_changed"] += 1
                continue
            if name not in keep:
                continue
            if site_of[name] in bad_sites:
                stats["cells_in_a_changed_site"] += 1
                continue
            keep_cells.add(name)
            if any(bel.startswith(p) for p in CONFIG["loc_site_prefixes"]):
                locs.append(f"set_property LOC {bel.split('/')[0]} [get_cells {{{name}}}]")
            if not any(bel.startswith(p) for p in rd.CONFIG["pin_site_prefixes"]):
                stats["cells_kept_other"] += 1
                continue
            f.write(f"{name}\t{rd.to_generic_bel(bel, smap)}\n")
            stats["cells_preplaced" if name in matched_ref else "packer_cells_preplaced"] += 1
    drv = net_drivers(routed)
    st = {"site_wires": 0, "pip_agree": 0, "pip_mismatch": 0}
    with open(out / "inc.prerouted", "w") as f:
        for name, n in routed["netnames"].items():
            r = n.get("attributes", {}).get("ROUTING")
            if not r:
                continue
            bits = [b for b in n["bits"] if isinstance(b, int)]
            d = drv.get(bits[0]) if bits else None
            if d is None or d not in keep_cells:
                stats["nets_rerouted"] += 1
                continue
            f.write(f"{name}\t{rd.convert_routing(r, smap, st)}\n")
            stats["nets_prerouted"] += 1
    (out / "inc.xdc").write_text(xdc_text.rstrip("\n") + "\n" + "".join(l + "\n" for l in locs))
    stats["locs"] = len(locs)
    return dict(stats)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ref_dir", help="reference build directory (holds <top>.json and <top>_routed.json)")
    ap.add_argument("new_json", help="yosys JSON of the changed design")
    ap.add_argument("out", help="output directory")
    ap.add_argument("--top", required=True)
    ap.add_argument("--xdc", required=True, help="the changed design's XDC")
    ap.add_argument("--rounds", type=int, default=CONFIG["rounds"])
    ap.add_argument("--ripple", type=int, default=CONFIG["ripple"],
                    help="also place again the slices within this many nets of a changed cell (0: only changed slices)")
    ap.add_argument("--whole-tiles", action="store_true",
                    help="place a whole tile again when one of its slices changed (and every carry chain through it), "
                         "so new cells can use the freed slices; replays fewer cells")
    a = ap.parse_args()
    ref_dir, out = Path(a.ref_dir), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ref_json = json.loads((ref_dir / f"{a.top}.json").read_text())
    new_json = json.loads(Path(a.new_json).read_text())
    rname, rmod = top_module(ref_json, a.top)
    nname, nmod = top_module(new_json, a.top)
    ref, new = Netlist(rmod), Netlist(nmod)
    pairs, _, _ = match(ref, new, a.rounds)
    bmap = bitmap_of(ref, new, pairs)
    mod, renamed_new = rewrite(ref, new, pairs, bmap)
    new_json["modules"][nname] = mod
    (out / f"{a.top}.json").write_text(json.dumps(new_json))
    routed = routed_top(ref_dir / f"{a.top}_routed.json")
    stats = write_replay(routed, ref, pairs, out, Path(a.xdc).read_text(), a.ripple, a.whole_tiles)
    same_name = sum(1 for n, r in pairs.items() if n == r)
    by_type = defaultdict(lambda: [0, 0])
    for n, c in new.cells.items():
        by_type[c["type"]][1] += 1
        if n in pairs:
            by_type[c["type"]][0] += 1
    res = {"ref_cells": len(ref.cells), "new_cells": len(new.cells), "matched": len(pairs),
           "matched_same_name": same_name, "new_unmatched": len(new.cells) - len(pairs),
           "ref_unmatched": len(ref.cells) - len(pairs), "renamed_new_to_avoid_clash": renamed_new,
           "mapped_bits": len(bmap), "rounds": a.rounds, "ripple": a.ripple, "whole_tiles": a.whole_tiles, "by_type_matched_of_new": dict(by_type), **stats,
           "unmatched_new_cells": sorted(set(new.cells) - set(pairs))[:200],
           "unmatched_ref_cells": sorted(set(ref.cells) - set(pairs.values()))[:200]}
    (out / "match.json").write_text(json.dumps(res, indent=1) + "\n")
    print(f"incremental: {len(pairs)}/{len(new.cells)} cells of the new netlist matched to the reference "
          f"({same_name} under the same name), {res['ref_unmatched']} reference cells changed or gone; "
          f"preplaced {stats.get('cells_preplaced', 0)} + {stats.get('packer_cells_preplaced', 0)} packer cells, "
          f"prerouted {stats.get('nets_prerouted', 0)} nets, {stats.get('nets_rerouted', 0)} left to the router")


if __name__ == "__main__":
    main()
