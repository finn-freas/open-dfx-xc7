import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import replay_dump

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "rm_prefix": "u_rm.",
    "margin": 24,
    "int_types": ["INT_L", "INT_R"],
}

DB = region.DB


class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        p = self.p
        while p.get(a, a) != a:
            p[a] = p.get(p[a], p[a])
            a = p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def build_graph(grid, spec):
    rtiles = region.region_tiles(grid, spec)
    xs = [grid[t]["grid_x"] for t in rtiles]
    ys = [grid[t]["grid_y"] for t in rtiles]
    m = CONFIG["margin"]
    x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
    at = {(t["grid_x"], t["grid_y"]): (n, t["type"]) for n, t in grid.items()}
    uf = UF()
    tc = json.loads((DB / region.CONFIG["fabric"] / "tileconn.json").read_text())
    for rule in tc:
        dx, dy = rule["grid_deltas"]
        ta, tb = rule["tile_types"]
        for (x, y), (n, ty) in at.items():
            if ty != ta or not (x0 <= x <= x1 and y0 <= y <= y1):
                continue
            other = at.get((x + dx, y + dy))
            if not other or other[1] != tb:
                continue
            for wa, wb in rule["wire_pairs"]:
                uf.union((n, wa), (other[0], wb))
    int_tiles = {n for n in rtiles if grid[n]["type"] in CONFIG["int_types"]}
    pips = {}
    for ty in CONFIG["int_types"]:
        d = json.loads((DB / f"tile_type_{ty}.json").read_text())
        out = collections.defaultdict(list)
        for p in d["pips"].values():
            if p.get("is_pseudo") == "1" or p.get("is_directional") != "1":
                continue
            out[p["src_wire"]].append(p["dst_wire"])
        wires = list(d["wires"])
        pips[ty] = (out, wires)
    members = collections.defaultdict(list)
    for n in int_tiles:
        for w in pips[grid[n]["type"]][1]:
            members[uf.find((n, w))].append((n, w))
    return uf, int_tiles, pips, members


def key(tile, name, uf):
    if "." in name:
        return ("site", tile, name)
    return uf.find((tile, name))


def parse_route(r, xy2tile, uf):
    t = r.split(";")
    root = None
    pips = []
    for i in range(0, len(t) - 2, 3):
        w, p = t[i], t[i + 1]
        if not p:
            root = w
            continue
        parts = p.split("/")
        if len(parts) != 3:
            continue
        m = re.fullmatch(r"X(\d+)Y(\d+)", parts[0])
        tile = xy2tile.get((int(m.group(1)), int(m.group(2)))) if m else None
        if tile is None:
            continue
        pips.append({"name": p, "tile": tile, "dst": key(tile, parts[1], uf), "src": key(tile, parts[2], uf),
                     "fabric": "." not in parts[1] and "." not in parts[2]})
    return root, pips


def main():
    ap = argparse.ArgumentParser(description="Re-route RM nets through region INT tiles only; write -o prerouted lines")
    ap.add_argument("routed_json", help="a build of this configuration (its RM routes give the pin heads/tails)")
    ap.add_argument("static_prerouted", help="the static nets' replay file (their nodes are taken)")
    ap.add_argument("out")
    ap.add_argument("--region", default=CONFIG["region"])
    a = ap.parse_args()
    grid = region.load_grid()
    xy2tile = {(t["grid_x"], t["grid_y"]): n for n, t in grid.items()}
    uf, int_tiles, pips, members = build_graph(grid, a.region)
    taken = set()
    static_names = set()
    for line in Path(a.static_prerouted).read_text().splitlines():
        if "\t" not in line:
            continue
        static_names.add(line.split("\t", 1)[0])
        _, ps = parse_route(line.split("\t", 1)[1], xy2tile, uf)
        for p in ps:
            taken.add(p["dst"])
            taken.add(p["src"])
    m = [v for v in json.loads(Path(a.routed_json).read_text())["modules"].values() if v.get("cells")][0]
    smap = replay_dump.site_map(grid)
    smap.update(replay_dump.learn_sites(m))
    nets = {n: v["attributes"]["ROUTING"] for n, v in m["netnames"].items()
            if n.startswith(CONFIG["rm_prefix"]) and n not in static_names and v["attributes"].get("ROUTING")}
    plans = {}
    for n, r in nets.items():
        root, ps = parse_route(r, xy2tile, uf)
        by_dst = {p["dst"]: p for p in ps}
        srcs = {p["src"] for p in ps}
        leaves = [p for p in ps if p["dst"] not in srcs]
        keep, conns = [], []
        for lf in leaves:
            path, cur = [], lf
            while cur is not None:
                path.append(cur)
                cur = by_dst.get(cur["src"])
            path.reverse()
            fab = [i for i, p in enumerate(path) if p["fabric"] and grid[p["tile"]]["type"] in CONFIG["int_types"]]
            if not fab:
                keep += path
                continue
            keep += path[:fab[0]] + path[fab[-1] + 1:]
            conns.append((path[fab[0]]["src"], path[fab[-1]]["dst"]))
        plans[n] = (root, keep, conns)
        for p in keep:
            taken.add(p["dst"])
    routed = {}
    fails = []
    order = sorted(plans, key=lambda n: -len(plans[n][2]))
    for n in order:
        root, keep, conns = plans[n]
        tree = set()
        new = []
        for s, t in conns:
            starts = {s} | tree
            prev = {x: None for x in starts}
            q = collections.deque(starts)
            found = t in prev
            while q and not found:
                node = q.popleft()
                for tile, w in members.get(node, []):
                    out, _ = pips[grid[tile]["type"]]
                    for d in out.get(w, []):
                        nk = uf.find((tile, d))
                        if nk in prev or (nk in taken and nk != t):
                            continue
                        prev[nk] = (node, f"X{grid[tile]['grid_x']}Y{grid[tile]['grid_y']}/{d}/{w}")
                        if nk == t:
                            found = True
                            break
                        q.append(nk)
                    if found:
                        break
            if not found:
                fails.append((n, s, t))
                continue
            cur = t
            seg = []
            while prev[cur] is not None:
                node, pname = prev[cur]
                seg.append(pname)
                tree.add(cur)
                taken.add(cur)
                cur = node
            tree.add(s)
            taken.add(s)
            new += reversed(seg)
        routed[n] = (replay_dump.to_generic_wire(root, smap) if root else None, [p["name"] for p in keep] + new)
    with open(a.out, "w") as f:
        for n, (root, ps) in routed.items():
            seen, toks = set(), [root, "", "1"] if root else []
            for p in ps:
                if p not in seen:
                    seen.add(p)
                    toks += ["", p, "1"]
            f.write(f"{n}\t{';'.join(toks)}\n")
    nconn = sum(len(p[2]) for p in plans.values())
    print(f"region_route: {len(routed)} RM nets, {nconn} fabric connections, {len(fails)} unroutable inside the region")
    for x in fails[:10]:
        print("   FAIL", x[0])
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
