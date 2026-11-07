import argparse
import collections
import heapq
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import region_route

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "margin": 30,
    "int_types": ["INT_L", "INT_R"],
    "keep": [r"u_rm\."],
    "max_visit": 200000,
    "h_div": 3,
    "ripup_rounds": 8,
    "freeze_after": 2,
}

DB = region.DB


def build_graph(grid, spec):
    rtiles = region.region_tiles(grid, spec)
    xs = [grid[t]["grid_x"] for t in rtiles]
    ys = [grid[t]["grid_y"] for t in rtiles]
    m = CONFIG["margin"]
    x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
    at = {(t["grid_x"], t["grid_y"]): (n, t["type"]) for n, t in grid.items()}
    uf = region_route.UF()
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
    int_tiles = {n for (x, y), (n, ty) in at.items() if ty in CONFIG["int_types"] and x0 <= x <= x1 and y0 <= y <= y1}
    reg_int = {n for n in rtiles if grid[n]["type"] in CONFIG["int_types"]}
    pips = {}
    for ty in CONFIG["int_types"]:
        d = json.loads((DB / f"tile_type_{ty}.json").read_text())
        out = collections.defaultdict(list)
        for p in d["pips"].values():
            if p.get("is_pseudo") == "1" or p.get("is_directional") != "1":
                continue
            out[p["src_wire"]].append(p["dst_wire"])
        pips[ty] = (out, list(d["wires"]))
    members = collections.defaultdict(list)
    forbidden = set()
    for n in int_tiles:
        for w in pips[grid[n]["type"]][1]:
            k = uf.find((n, w))
            members[k].append((n, w))
            if n in reg_int:
                forbidden.add(k)
    return uf, int_tiles, reg_int, pips, members, forbidden


def runs_of(path, int_tiles, rtiles):
    runs, cur = [], []
    for i, p in enumerate(path):
        if (p["fabric"] and p["tile"] in int_tiles) or p["tile"] in rtiles:
            cur.append(i)
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def bfs(starts, t, members, pips, grid, taken, forbidden):
    prev = {x: None for x in starts}
    if t in prev:
        return prev
    goal = [(grid[tile]["grid_x"], grid[tile]["grid_y"]) for tile, _ in members.get(t, [])]
    if not goal:
        return None

    def h(node):
        ms = members.get(node, [])
        if not ms:
            return 0
        return min(abs(grid[tile]["grid_x"] - gx) + abs(grid[tile]["grid_y"] - gy)
                   for tile, _ in ms for gx, gy in goal) / CONFIG["h_div"]

    cost = {x: 0 for x in starts}
    q = [(h(x), 0, i, x) for i, x in enumerate(starts)]
    heapq.heapify(q)
    n = len(q)
    while q and len(prev) < CONFIG["max_visit"]:
        _, g, _, node = heapq.heappop(q)
        if g > cost.get(node, g):
            continue
        for tile, w in members.get(node, []):
            out, _ = pips[grid[tile]["type"]]
            for d in out.get(w, []):
                nk = BFS_UF.find((tile, d))
                if nk != t and (nk in taken or nk in forbidden):
                    continue
                if nk in cost and cost[nk] <= g + 1:
                    continue
                cost[nk] = g + 1
                prev[nk] = (node, f"X{grid[tile]['grid_x']}Y{grid[tile]['grid_y']}/{d}/{w}")
                if nk == t:
                    return prev
                n += 1
                heapq.heappush(q, (g + 1 + h(nk), g + 1, n, nk))
    return None


BFS_UF = None
CONST_RE = re.compile(r"^\$PACKER_(VCC|GND)_NET$")


def main():
    global BFS_UF
    ap = argparse.ArgumentParser(description="Re-route static nets that cross the region's INT tiles around it; "
                                             "write a new -o prerouted file")
    ap.add_argument("static_prerouted")
    ap.add_argument("out")
    ap.add_argument("--region", default=CONFIG["region"])
    ap.add_argument("--keep", action="append", default=None, help="regex of nets left untouched (boundary nets)")
    a = ap.parse_args()
    keep_re = [re.compile(k) for k in (a.keep or CONFIG["keep"])]
    grid = region.load_grid()
    xy2tile = {(t["grid_x"], t["grid_y"]): n for n, t in grid.items()}
    uf, int_tiles, reg_int, pips, members, forbidden = build_graph(grid, a.region)
    rtiles = set(region.region_tiles(grid, a.region))
    inside = lambda k: k in forbidden or (isinstance(k, tuple) and len(k) == 3 and k[0] == "site" and k[1] in rtiles)
    BFS_UF = uf
    lines = [l for l in Path(a.static_prerouted).read_text().splitlines() if "\t" in l]
    parsed = {}
    for l in lines:
        n, r = l.split("\t", 1)
        root, ps = region_route.parse_route(r, xy2tile, uf)
        parsed[n] = (r, root, ps)
    crossing = [n for n, (r, root, ps) in parsed.items()
                if not any(k.match(n) for k in keep_re) and any(p["tile"] in rtiles for p in ps)]
    taken = set()
    plans = {}
    for n, (r, root, ps) in parsed.items():
        if n not in crossing:
            for p in ps:
                taken.add(p["dst"])
                taken.add(p["src"])
            continue
        by_dst = {p["dst"]: p for p in ps}
        srcs = {p["src"] for p in ps}
        leaves = [p for p in ps if p["dst"] not in srcs]
        drop, conns = set(), []
        for lf in leaves:
            path, cur = [], lf
            while cur is not None:
                path.append(cur)
                cur = by_dst.get(cur["src"])
            path.reverse()
            for run in runs_of(path, int_tiles, rtiles):
                if inside(path[run[-1]]["dst"]) or inside(path[run[0]]["src"]):
                    continue
                if any(path[i]["tile"] in rtiles for i in run):
                    drop.update(path[i]["name"] for i in run)
                    conns.append((path[run[0]]["src"], path[run[-1]]["dst"], tuple(path[i]["name"] for i in run)))
        kept = [p for p in ps if p["name"] not in drop]
        for p in kept:
            taken.add(p["dst"])
            taken.add(p["src"])
        plans[n] = (kept, list(dict.fromkeys(conns)))
    base_taken = set(taken)
    frozen = []
    order = sorted(plans, key=lambda n: -len(plans[n][1]))
    for attempt in range(CONFIG["ripup_rounds"]):
        taken = set(base_taken)
        fails, new_pips, nconn, fallback, restored = [], {}, 0, [], []
        for n in order:
            kept, conns = plans[n]
            tree = {p["dst"] for p in kept if p["fabric"]}
            added = []
            for s, t, orig in conns:
                nconn += 1
                if nconn % 200 == 0:
                    print(f"static_detour: {nconn} connections, {len(fails)} failed", flush=True)
                starts = {s} | {x for x in tree if x in members}
                if CONST_RE.match(n) and inside(s):
                    tie = "VCC_WIRE" if "VCC" in n else "GND_WIRE"
                    starts = {uf.find((x, tie)) for x in int_tiles - reg_int} | {x for x in tree if x in members}
                prev = bfs(starts, t, members, pips, grid, taken, forbidden)
                if prev is None:
                    prev = bfs(starts, t, members, pips, grid, taken, set())
                    if prev is not None:
                        fallback.append(n)
                if prev is None:
                    onodes = [q for q in parsed[n][2] if q["name"] in orig]
                    if all(q["dst"] not in taken or q["dst"] in tree for q in onodes):
                        for q in onodes:
                            taken.add(q["dst"])
                            tree.add(q["dst"])
                        added += list(orig)
                        restored.append(n)
                        continue
                    fails.append((n, s, t, inside(s), inside(t)))
                    continue
                cur = t
                seg = []
                while prev[cur] is not None:
                    node, pname = prev[cur]
                    seg.append(pname)
                    tree.add(cur)
                    taken.add(cur)
                    cur = node
                added += reversed(seg)
            new_pips[n] = (kept, added)
        print(f"static_detour: round {attempt + 1}: {len(fails)} failed, {len(fallback)} through region", flush=True)
        if not fails:
            break
        bad = list(dict.fromkeys(x[0] for x in fails + [(f,) for f in fallback]))
        if attempt >= CONFIG["freeze_after"]:
            for n in dict.fromkeys(x[0] for x in fails):
                frozen.append(n)
                plans.pop(n)
                for q in parsed[n][2]:
                    base_taken.add(q["dst"])
                    base_taken.add(q["src"])
        order = [n for n in bad if n in plans] + [n for n in order if n not in bad and n in plans]
    if fails:
        print(f"static_detour: {len(fails)} of {nconn} crossing connections found no path outside the region")
        cat = collections.Counter((CONST_RE.match(x[0]) is not None, x[3], x[4]) for x in fails)
        for (const, sf, tf), k in cat.most_common():
            print(f"   {k} fails: constant net {const}, start in region {sf}, end in region {tf}")
        for nm, k in collections.Counter(x[0] for x in fails).most_common(10):
            print(f"   FAIL {k}x {nm[:100]}")
        sys.exit(1)
    with open(a.out, "w") as f:
        for l in lines:
            n, r = l.split("\t", 1)
            if n not in new_pips:
                f.write(l + "\n")
                continue
            kept, added = new_pips[n]
            dropped = {p["name"] for p in parsed[n][2]} - {p["name"] for p in kept}
            t = r.split(";")
            toks = []
            for i in range(0, len(t) - 2, 3):
                w, p, s = t[i], t[i + 1], t[i + 2]
                if p not in dropped:
                    toks += [w, p, s]
            for p in added:
                toks += ["", p, "1"]
            f.write(f"{n}\t{';'.join(toks)}\n")
    left, const_pips, after = 0, 0, 0
    for l in Path(a.out).read_text().splitlines():
        n, r = l.split("\t", 1)
        if any(k.match(n) for k in keep_re):
            continue
        _, ps = region_route.parse_route(r, xy2tile, uf)
        after += sum(p["tile"] in rtiles for p in ps)
        if CONST_RE.match(n):
            const_pips += sum(p["tile"] in rtiles for p in ps)
            continue
        left += any(p["tile"] in rtiles and not inside(p["dst"]) for p in ps)
    before = sum(q["tile"] in rtiles for n, (r, root, ps) in parsed.items() if not any(k.match(n) for k in keep_re) for q in ps)
    print(f"static_detour: static pips in region tiles {before} -> {after}")
    print(f"static_detour: {len(crossing)} static nets crossed the region; {nconn} connections re-routed around it; "
          f"{left} non-boundary static nets still use region INT pips; "
          f"{const_pips} region pips remain on constant nets delivering to RM pins; "
          f"{len(fallback)} connections had no path outside the region and were re-routed through it; {len(restored)} kept their original route; {len(frozen)} nets left entirely on their original route")
    sys.exit(0)


if __name__ == "__main__":
    main()
