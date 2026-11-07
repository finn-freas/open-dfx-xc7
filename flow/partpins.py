import argparse
import collections
import json
import pickle
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import region2v

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "rm_prefix": "u_rm.",
    "rm_inst": "u_rm",
    "margin": 8,
    "skip_net_prefixes": ["$PACKER_"],
    "global_driver_types": ["BUFGCTRL", "BUFG", "BUFG_BUFG", "BUFGCE", "BUFHCE"],
    "cache": region2v.CONFIG["cache"] / "partpins",
}

XY_RE = re.compile(r"X(\d+)Y(\d+)")


def top_module(d):
    for m in d["modules"].values():
        if any("NEXTPNR_BEL" in c.get("attributes", {}) for c in m.get("cells", {}).values()):
            return m
    sys.exit("no placed module in json")


def entries(routing):
    parts = routing.split(";")
    return [(parts[i], parts[i + 1], parts[i + 2]) for i in range(0, len(parts) - 2, 3)]


class Nodes:
    def __init__(self, grid, xys):
        self.grid = grid
        self.name_at = {(t["grid_x"], t["grid_y"]): n for n, t in grid.items()}
        m = CONFIG["margin"]
        xs = [x for x, _ in xys]
        ys = [y for _, y in xys]
        box = (min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m)
        f = CONFIG["cache"] / f"uf_{box[0]}_{box[1]}_{box[2]}_{box[3]}.pkl"
        if f.exists():
            self.parent = pickle.loads(f.read_bytes())
            return
        at = {xy: (n, self.grid[n]["type"]) for xy, n in self.name_at.items()
              if box[0] <= xy[0] <= box[1] and box[2] <= xy[1] <= box[3]}
        by_type = collections.defaultdict(list)
        for xy, (n, ty) in at.items():
            by_type[ty].append((xy, n))
        tc = json.loads((region2v.DB / region2v.CONFIG["fabric"] / "tileconn.json").read_text())
        uf = region2v.UF()
        for rule in tc:
            dx, dy = rule["grid_deltas"]
            ta, tb = rule["tile_types"]
            for (x, y), n in by_type.get(ta, []):
                other = at.get((x + dx, y + dy))
                if not other or other[1] != tb:
                    continue
                for wa, wb in rule["wire_pairs"]:
                    uf.union((n, wa), (other[0], wb))
        for k in list(uf.p):
            uf.find(k)
        self.parent = uf.p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(pickle.dumps(self.parent))

    def tile(self, xyname):
        x, y = map(int, XY_RE.fullmatch(xyname).groups())
        return self.name_at[(x, y)]

    def of(self, xyname, wire):
        if not XY_RE.fullmatch(xyname):
            return (xyname, wire)
        k = (self.tile(xyname), wire)
        p = self.parent
        while p.get(k, k) != k:
            k = p[k]
        return k


def drivers_and_users(m, prefix):
    drv, users = {}, collections.defaultdict(set)
    for name, c in m["cells"].items():
        rm = name.startswith(prefix)
        dirs = c.get("port_directions", {})
        for port, bits in c.get("connections", {}).items():
            for b in bits:
                if not isinstance(b, int):
                    continue
                if dirs.get(port) == "output":
                    drv[b] = (name, c["type"], rm)
                else:
                    users[b].add(rm)
    return drv, users


def port_names(static_synth, inst):
    d = json.loads(Path(static_synth).read_text())
    for m in d["modules"].values():
        if inst in m.get("cells", {}):
            break
    else:
        sys.exit(f"{static_synth}: no cell {inst}")
    names_of = collections.defaultdict(list)
    for n, v in m["netnames"].items():
        for j, b in enumerate(v["bits"]):
            names_of[b].append(n if len(v["bits"]) == 1 else f"{n}[{j}]")
    out = {}
    cell = m["cells"][inst]
    for port, bits in cell["connections"].items():
        for i, b in enumerate(bits):
            for n in names_of.get(b, []):
                out.setdefault(n, (port, i, cell["port_directions"][port]))
    return out


class Tree:
    def __init__(self, ents, nodes):
        self.ents = ents
        self.idx_of_node = {}
        for k, (w, p, s) in enumerate(ents):
            t, wn = w.split("/", 1)
            self.idx_of_node[nodes.of(t, wn)] = k
        self.parent = [None] * len(ents)
        self.children = collections.defaultdict(list)
        for k, (w, p, s) in enumerate(ents):
            if not p:
                continue
            t, _, src = p.split("/")
            par = self.idx_of_node.get(nodes.of(t, src))
            if par is None:
                raise ValueError(f"pip {p} of wire {w}: source not on this route")
            self.parent[k] = par
            self.children[par].append(k)
        roots = [k for k in range(len(ents)) if self.parent[k] is None]
        if len(roots) != 1:
            raise ValueError(f"{len(roots)} roots")
        self.root = roots[0]

    def pip_tile(self, k):
        return self.ents[k][1].split("/", 1)[0]

    def below(self, k):
        out, q = [], [k]
        while q:
            x = q.pop()
            out.append(x)
            q += self.children[x]
        return out

    def above(self, k):
        out = []
        while k is not None:
            out.append(k)
            k = self.parent[k]
        return out


def input_pin(tree, inside):
    static = set()
    q = [tree.root]
    while q:
        k = q.pop()
        static.add(k)
        q += [c for c in tree.children[k] if tree.pip_tile(c) not in inside]
    cands = {}
    for k in static:
        entry = [c for c in tree.children[k] if tree.pip_tile(c) in inside]
        if entry:
            cands[k] = entry
    if not cands:
        raise ValueError("route never enters the region")
    leaves = lambda k: sum(1 for x in tree.below(k) if not tree.children[x])
    pp = max(cands, key=lambda k: (sum(leaves(c) for c in cands[k]), -k))
    static_leaves = [k for k in static if not any(c in static for c in tree.children[k]) and k not in cands]
    through = [k for k in range(len(tree.ents))
               if k not in static and not tree.children[k] and tree.pip_tile(k) not in inside]
    if through:
        raise ValueError(f"{len(through)} sink(s) outside the region are reached through it, e.g. {tree.ents[through[0]][0]}")
    keep = set(tree.above(pp))
    for k in static_leaves:
        keep |= set(tree.above(k))
    alias_pip = tree.ents[cands[pp][0]][1].split("/")
    return pp, sorted(keep), (alias_pip[0], alias_pip[2]), len(cands)


def output_pin(tree, inside):
    in_r = lambda k: k == tree.root or tree.pip_tile(k) in inside
    has_r_below = {k: any(tree.pip_tile(x) in inside for x in tree.below(k)) for k in range(len(tree.ents))}
    exits = [c for c in range(len(tree.ents))
             if not in_r(c) and not has_r_below[c] and in_r(tree.parent[c])]
    cands = sorted({tree.parent[c] for c in exits})
    if len(cands) != 1:
        raise ValueError(f"route leaves the region for good at {len(cands)} wires: "
                         + ", ".join(tree.ents[k][0] for k in cands[:4]))
    pp = cands[0]
    if pp == tree.root:
        raise ValueError("route leaves the region straight from its source pin")
    below = sorted(k for c in tree.children[pp] if c in exits for k in tree.below(c))
    leaves_out = {k for k in range(len(tree.ents)) if not tree.children[k] and not in_r(k)}
    stranded = leaves_out - set(below)
    if stranded:
        raise ValueError(f"{len(stranded)} sink(s) outside the region are not below the pin, e.g. "
                         f"{tree.ents[min(stranded)][0]}")
    alias_pip = tree.ents[pp][1].split("/")
    return pp, below, (alias_pip[0], alias_pip[1]), len(exits)


def main():
    ap = argparse.ArgumentParser(description="Choose a partition pin per net that crosses the region's edge in a reference "
                                             "build, and cut that net's locked route at it (nextpnr -o prerouted / "
                                             "-o partition-pins)")
    ap.add_argument("routed_json", help="the reference build's routed json")
    ap.add_argument("prerouted", help="replay_dump.py's .prerouted of the same build (boundary nets kept)")
    ap.add_argument("static_synth", help="static synthesis json with the RM instance as a blackbox (port names)")
    ap.add_argument("out_prefix")
    ap.add_argument("--region", default=CONFIG["region"])
    ap.add_argument("--rm-prefix", default=CONFIG["rm_prefix"])
    ap.add_argument("--rm-inst", default=CONFIG["rm_inst"])
    a = ap.parse_args()
    outs = [Path(a.out_prefix + s) for s in (".prerouted", ".partpins", ".json")]
    if all(o.exists() for o in outs):
        print(f"[skip] {', '.join(o.name for o in outs)} exist")
        return
    grid = region.load_grid()
    tiles = region.region_tiles(grid, a.region)
    inside = {f"X{t['grid_x']}Y{t['grid_y']}" for t in tiles.values()}
    m = top_module(json.loads(Path(a.routed_json).read_text()))
    drv, users = drivers_and_users(m, a.rm_prefix)
    ports = port_names(a.static_synth, a.rm_inst)
    replay = dict(l.split("\t", 1) for l in Path(a.prerouted).read_text().splitlines() if "\t" in l)
    boundary = {}
    for name, n in m["netnames"].items():
        r = replay.get(name)
        if not r or len(n["bits"]) != 1 or any(name.startswith(p) for p in CONFIG["skip_net_prefixes"]):
            continue
        b = n["bits"][0]
        if b not in drv or drv[b][1] in CONFIG["global_driver_types"]:
            continue
        rm_drv = drv[b][2]
        if (rm_drv and False in users[b]) or (not rm_drv and True in users[b]):
            boundary[name] = (r, "out" if rm_drv else "in")
    xys = set()
    for r, _ in boundary.values():
        for w, p, _ in entries(r):
            for tok in (w, p):
                xy = XY_RE.fullmatch(tok.split("/", 1)[0])
                if xy:
                    xys.add(tuple(map(int, xy.groups())))
    nodes = Nodes(grid, xys)
    pins, errors, lines = [], [], {}
    for name, (r, direction) in sorted(boundary.items()):
        ents = entries(r)
        try:
            tree = Tree(ents, nodes)
            pp, keep, alias, ncand = (input_pin if direction == "in" else output_pin)(tree, inside)
        except ValueError as e:
            errors.append(f"{name}: {e}")
            continue
        lines[name] = ";".join(";".join(ents[k]) for k in keep)
        port = ports.get(name)
        pins.append({"net": name, "dir": direction, "port": port[0] if port else None, "bit": port[1] if port else None,
                     "wire": ents[pp][0], "alias_tile": nodes.tile(alias[0]), "alias_wire": alias[1],
                     "entries_kept": len(keep), "entries_dropped": len(ents) - len(keep),
                     "crossings_in_reference": ncand})
    unnamed = [p["net"] for p in pins if p["port"] is None]
    if errors or unnamed:
        for e in errors[:20]:
            print("ERROR " + e)
        if unnamed:
            print(f"ERROR nets with no {a.rm_inst} port in {a.static_synth}: {unnamed[:10]}")
        sys.exit(1)
    seen = set()
    with open(outs[0], "w") as f:
        for line in Path(a.prerouted).read_text().splitlines():
            name = line.split("\t", 1)[0]
            if name in lines:
                f.write(f"{name}\t{lines[name]}\n")
                seen.add(name)
            else:
                f.write(line + "\n")
    missing = sorted(set(lines) - seen)
    if missing:
        sys.exit(f"boundary nets not in {a.prerouted}: {missing[:10]}")
    outs[1].write_text("".join(f"{p['net']}\t{p['wire']}\n" for p in pins))
    summary = {"region": a.region, "routed_json": a.routed_json, "pins": pins,
               "inputs": sum(p["dir"] == "in" for p in pins), "outputs": sum(p["dir"] == "out" for p in pins),
               "input_nets_entering_more_than_once": sum(p["crossings_in_reference"] > 1 for p in pins if p["dir"] == "in")}
    outs[2].write_text(json.dumps(summary, indent=1) + "\n")
    print(f"wrote {outs[0].name}, {outs[1].name}, {outs[2].name}: {summary['inputs']} input and {summary['outputs']} "
          f"output partition pins; {summary['input_nets_entering_more_than_once']} input net(s) entered the region "
          f"more than once in the reference (one entry kept, the rest dropped)")


if __name__ == "__main__":
    main()
