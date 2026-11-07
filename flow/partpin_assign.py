import argparse
import collections
import json
import pickle
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import partpins
import region
import region2v
import replay_dump

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "rm_inst": "u_rm",
    "spec": Path(__file__).resolve().parent.parent / "designs" / "rv_soc" / "pr" / "ports.json",
    "pin_tile_types": ["INT_L", "INT_R"],
    "wire_class": r"(EE|WW|NN|SS|NE|NW|SE|SW|EL|ER|WL|WR|NL|NR|SL|SR)\d",
    "logic_inputs": ("IMUX", "BYP_ALT"),
    "logic_outputs": ("LOGIC_OUTS",),
    "require_direct": True,
    "exclude_wires": r".*_[NS]\d.*",
    "tile_cap": 3,
    "w_static": 1.0,
    "w_slice": 1.0,
    "w_load": 2.0,
    "module_ends": False,
    "w_module": 1.0,
    "exclude_wrap_exits": False,
    "band_slack": 1.25,
    "bus_min_width": 8,
    "keep_per_net": 400,
    "proxy_top": "pp_proxy",
    "proxy_pblock": "pblock_rm",
    "proxy_lanes": "ABCD",
    "cache": region2v.CONFIG["cache"] / "partpin_assign",
}

XY_RE = re.compile(r"X(\d+)Y(\d+)")


def xy_name(t):
    return f"X{t['grid_x']}Y{t['grid_y']}"


def candidates(grid, spec):
    f = CONFIG["cache"] / f"cand3_{region2v.sanitize(spec)}_m{partpins.CONFIG['margin']}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    rtiles = region.region_tiles(grid, spec)
    inside = {xy_name(grid[t]) for t in rtiles}
    xys = [(grid[t]["grid_x"], grid[t]["grid_y"]) for t in rtiles]
    nodes = partpins.Nodes(grid, xys)
    m = partpins.CONFIG["margin"]
    x0, x1 = min(x for x, _ in xys) - m, max(x for x, _ in xys) + m
    y0, y1 = min(y for _, y in xys) - m, max(y for _, y in xys) + m
    rnodes = set()
    for t in rtiles:
        for w in region2v.tile_type(grid[t]["type"])["wires"]:
            rnodes.add(nodes.of(xy_name(grid[t]), w))
    info = collections.defaultdict(lambda: {"drv_in": [], "drv_out": [], "use_in": [], "use_out": [], "names": set(),
                                                 "direct": set()})
    for name, t in grid.items():
        if not (x0 <= t["grid_x"] <= x1 and y0 <= t["grid_y"] <= y1):
            continue
        xy = xy_name(t)
        tin = xy in inside
        for (src, dst), p in region2v.tile_type(t["type"])["pips"].items():
            if str(p.get("is_pseudo")) == "1" or str(p.get("is_directional")) == "0":
                continue
            ns, nd = nodes.of(xy, src), nodes.of(xy, dst)
            if nd in rnodes:
                info[nd]["drv_in" if tin else "drv_out"].append((xy, dst))
                if tin and src.startswith(CONFIG["logic_outputs"]):
                    info[nd]["direct"].add(xy)
                info[nd]["names"].add(dst)
            if ns in rnodes:
                info[ns]["use_in" if tin else "use_out"].append((xy, src))
                if tin and dst.startswith(CONFIG["logic_inputs"]):
                    info[ns]["direct"].add(xy)
                info[ns]["names"].add(src)
    cls = re.compile(CONFIG["wire_class"])
    pin_types = set(CONFIG["pin_tile_types"])
    tile_of_xy = {xy_name(grid[t]): t for t in rtiles}
    out = []
    for n, d in info.items():
        if not all(cls.match(w) for w in d["names"]):
            continue
        if d["drv_out"] and d["use_in"] and not d["drv_in"]:
            direction, inner, outer = "in", d["use_in"], d["drv_out"]
        elif d["drv_in"] and d["use_out"] and not d["drv_out"]:
            direction, inner, outer = "out", d["drv_in"], d["use_out"]
        else:
            continue
        inner = [(xy, w) for xy, w in inner if grid[tile_of_xy[xy]]["type"] in pin_types]
        if not inner:
            continue
        counts = collections.Counter(inner)
        (pxy, pw), _ = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        sx = sorted({tuple(map(int, XY_RE.fullmatch(xy).groups())) for xy, _ in outer})
        out.append({"dir": direction, "wire": f"{pxy}/{pw}", "tile_xy": pxy, "tile": tile_of_xy[pxy],
                    "xy": tuple(map(int, XY_RE.fullmatch(pxy).groups())), "static_xys": sx,
                    "cls": re.match(r"[A-Z]+\d", pw).group(0), "node": n, "direct": pxy in d["direct"],
                    "outer_wires": sorted({w for _, w in outer})})
    out.sort(key=lambda c: (c["dir"], c["tile_xy"], c["wire"]))
    res = {"region": spec, "candidates": out,
           "pin_tiles": sorted({xy_name(grid[t]) for t in rtiles if grid[t]["type"] in pin_types})}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(pickle.dumps(res))
    return res


def usable(cand):
    skip = re.compile(CONFIG["exclude_wires"])
    wrap_only = lambda c: CONFIG["exclude_wrap_exits"] and all(skip.fullmatch(w) for w in c["outer_wires"])
    return [c for c in cand["candidates"] if (c["direct"] or not CONFIG["require_direct"])
            and not skip.fullmatch(c["wire"].split("/", 1)[1]) and not wrap_only(c)]


def capacity(cand):
    cap = {t: {"in": 0, "out": 0, "in_by_class": collections.Counter(), "out_by_class": collections.Counter()}
           for t in cand["pin_tiles"]}
    for c in usable(cand):
        cap[c["tile_xy"]][c["dir"]] += 1
        cap[c["tile_xy"]][c["dir"] + "_by_class"][c["cls"]] += 1
    return cap


def json_net_names(m):
    return {n: v["bits"][0] for n, v in m["netnames"].items() if len(v["bits"]) == 1 and isinstance(v["bits"][0], int)}


def boundary_nets(m, static_synth, spec):
    ports = partpins.port_names(static_synth, CONFIG["rm_inst"])
    widths = dict(spec["inputs"] + spec["outputs"])
    dirs = {n: "in" for n, _ in spec["inputs"]} | {n: "out" for n, _ in spec["outputs"]}
    have = json_net_names(m)
    by_port = {}
    for name, (port, bit, _) in ports.items():
        if port not in dirs or name not in have:
            continue
        by_port.setdefault((port, bit), []).append(name)
    nets = []
    for (port, bit), names in sorted(by_port.items()):
        name = min(names, key=lambda n: (n.startswith("$"), len(n), n))
        nets.append({"net": name, "port": port, "bit": bit, "width": widths[port], "dir": dirs[port],
                     "id": have[name]})
    missing = [f"{p}[{i}]" for p, w in widths.items() for i in range(w) if (p, i) not in by_port]
    if missing:
        sys.exit(f"ports with no net in the placed json: {missing[:10]}")
    return nets


def endpoints(m, nets, smap):
    drv, users = {}, collections.defaultdict(list)
    drv_cell, user_cells = {}, collections.defaultdict(list)
    for name, c in m["cells"].items():
        bel = c.get("attributes", {}).get("NEXTPNR_BEL")
        if not bel:
            continue
        site = bel.split("/", 1)[0]
        xy = smap.get(site, (None,))[0]
        if xy is None:
            continue
        xy = tuple(map(int, XY_RE.fullmatch(xy).groups()))
        for port, bits in c.get("connections", {}).items():
            for b in bits:
                if not isinstance(b, int):
                    continue
                if c.get("port_directions", {}).get(port) == "output":
                    drv[b] = xy
                    drv_cell[b] = name
                else:
                    users[b].append(xy)
                    user_cells[b].append(name)
    rm = CONFIG["rm_inst"] + "."
    for n in nets:
        pts = [drv[n["id"]]] if n["dir"] == "in" and n["id"] in drv else users.get(n["id"], [])
        if not pts:
            sys.exit(f"{n['net']}: no placed static {'driver' if n['dir'] == 'in' else 'sink'}")
        n["endpoint"] = (round(sum(p[0] for p in pts) / len(pts)), round(sum(p[1] for p in pts) / len(pts)))
        cells = [drv_cell[n["id"]]] if n["dir"] == "in" and n["id"] in drv_cell else user_cells.get(n["id"], [])
        n["endpoint_cells"] = sorted(c for c in cells if not c.startswith(rm))
        if n["dir"] == "in":
            mod = [xy for xy, c in zip(users.get(n["id"], []), user_cells.get(n["id"], [])) if c.startswith(rm)]
        else:
            mod = [drv[n["id"]]] if drv_cell.get(n["id"], "").startswith(rm) else []
        n["module_end"] = (sum(p[0] for p in mod) / len(mod), sum(p[1] for p in mod) / len(mod)) if mod else None


def static_dist(n, c):
    ex, ey = n["endpoint"]
    return min(abs(ex - x) + abs(ey - y) for x, y in c["static_xys"])


def assign(nets, cand):
    pin_tiles = cand["pin_tiles"]
    ys = sorted({int(XY_RE.fullmatch(t).group(2)) for t in pin_tiles})
    cols = len({XY_RE.fullmatch(t).group(1) for t in pin_tiles})
    rows_needed = min(len(ys), int(-(-len(nets) // (cols * CONFIG["tile_cap"])) * CONFIG["band_slack"]) + 1)
    ey = sorted(n["endpoint"][1] for n in nets)[len(nets) // 2]
    start = min(range(len(ys) - rows_needed + 1),
                key=lambda k: (abs((ys[k] + ys[k + rows_needed - 1]) / 2 - ey), k))
    band = ys[start:start + rows_needed]
    near_end_is_low = abs(band[0] - ey) <= abs(band[-1] - ey)
    for n in nets:
        n["target_y"] = None
        if n["width"] >= CONFIG["bus_min_width"]:
            frac = (n["bit"] + 0.5) / n["width"]
            lo, hi = band[0], band[-1]
            n["target_y"] = hi - frac * (hi - lo) if near_end_is_low else lo + frac * (hi - lo)
    by_dir = collections.defaultdict(list)
    for c in usable(cand):
        by_dir[c["dir"]].append(c)
    lists = {}
    for n in nets:
        scored = []
        me = n.get("module_end") if CONFIG["module_ends"] else None
        for k, c in enumerate(by_dir[n["dir"]]):
            s = CONFIG["w_static"] * static_dist(n, c)
            if me is not None:
                t = CONFIG["w_module"] * (abs(c["xy"][0] - me[0]) + abs(c["xy"][1] - me[1]))
            elif n["target_y"] is not None:
                t = CONFIG["w_slice"] * abs(c["xy"][1] - n["target_y"])
            else:
                t = 0.0
            scored.append((s + t, k, s, t))
        scored.sort()
        lists[n["net"]] = [(cost, by_dir[n["dir"]][k], s, t) for cost, k, s, t in scored[:CONFIG["keep_per_net"]]]
    load = collections.Counter()
    used = set()
    todo = {n["net"]: n for n in nets}
    out = {}
    while todo:
        pick = None
        for name in sorted(todo):
            best = []
            for cost, c, s, t in lists[name]:
                if c["wire"] in used or load[c["tile_xy"]] >= CONFIG["tile_cap"]:
                    continue
                best.append((cost + CONFIG["w_load"] * load[c["tile_xy"]], c, s, t))
                if len(best) == 2:
                    break
            if not best:
                sys.exit(f"{name}: no free candidate within the {CONFIG['keep_per_net']} nearest; raise tile_cap "
                         f"or keep_per_net")
            best.sort(key=lambda b: b[0])
            regret = best[1][0] - best[0][0] if len(best) > 1 else float("inf")
            key = (-regret, best[0][0], name)
            if pick is None or key < pick[0]:
                pick = (key, name, best[0])
        _, name, (cost, c, s, t) = pick
        used.add(c["wire"])
        load[c["tile_xy"]] += 1
        out[name] = (c, cost, s, t)
        del todo[name]
    return out, band


def cmd_assign(a):
    outs = [Path(a.out_prefix + s) for s in (".partpins", ".json")]
    if all(o.exists() for o in outs):
        print(f"[skip] {', '.join(o.name for o in outs)} exist")
        return
    grid = region.load_grid()
    spec = json.loads(Path(a.spec).read_text())
    cand = candidates(grid, a.region)
    cap = capacity(cand)
    m = partpins.top_module(json.loads(Path(a.placed_json).read_text()))
    nets = boundary_nets(m, a.static_synth, spec)
    endpoints(m, nets, replay_dump.site_map(grid))
    res, band = assign(nets, cand)
    pins = []
    for n in nets:
        c, cost, s, t = res[n["net"]]
        pins.append({"net": n["net"], "dir": n["dir"], "port": n["port"], "bit": n["bit"], "wire": c["wire"],
                     "tile": c["tile"], "tile_xy": c["tile_xy"], "class": c["cls"], "endpoint": n["endpoint"],
                     "target_y": n["target_y"], "static_dist": s, "slice_dev": t, "cost": cost})
        if CONFIG["module_ends"]:
            pins[-1]["module_end"] = n["module_end"]
    per_tile = collections.Counter(p["tile_xy"] for p in pins)
    summary = {
        "region": a.region, "placed_json": a.placed_json, "config": {k: (str(v) if isinstance(v, Path) else v)
                                                                    for k, v in CONFIG.items()
                                                                    if CONFIG["module_ends"] or CONFIG["exclude_wrap_exits"]
                                                                    or k not in ("module_ends", "w_module",
                                                                                 "exclude_wrap_exits")},
        "band_rows": [band[0], band[-1]], "pins": pins,
        "capacity": {t: {"in": v["in"], "out": v["out"], "in_by_class": dict(sorted(v["in_by_class"].items())),
                         "out_by_class": dict(sorted(v["out_by_class"].items()))} for t, v in cap.items()},
        "tiles_used": len(per_tile), "max_pins_per_tile": max(per_tile.values()),
        "static_dist_mean": sum(p["static_dist"] for p in pins) / len(pins),
        "static_dist_max": max(p["static_dist"] for p in pins),
    }
    outs[0].write_text("".join(f"{p['net']}\t{p['wire']}\n" for p in pins))
    outs[1].write_text(json.dumps(summary, indent=1) + "\n")
    if a.endpoint_cells:
        cells = sorted({c for n in nets for c in n["endpoint_cells"]})
        Path(a.endpoint_cells).write_text("".join(c + "\n" for c in cells))
        print(f"wrote {Path(a.endpoint_cells).name}: {len(cells)} static endpoint cells")
    cin = [v["in"] for v in cap.values()]
    cout = [v["out"] for v in cap.values()]
    print(f"capacity: {len(cap)} pin tiles; boundary wires per tile: in {min(cin)}..{max(cin)} (total {sum(cin)}), "
          f"out {min(cout)}..{max(cout)} (total {sum(cout)})")
    print(f"wrote {outs[0].name}, {outs[1].name}: {len(pins)} pins ({sum(p['dir'] == 'in' for p in pins)} in, "
          f"{sum(p['dir'] == 'out' for p in pins)} out) in {len(per_tile)} tiles, at most {max(per_tile.values())} "
          f"per tile; band rows {band[0]}..{band[-1]}; static distance mean {summary['static_dist_mean']:.1f}, "
          f"max {summary['static_dist_max']} tiles")


def cmd_capacity(a):
    grid = region.load_grid()
    cap = capacity(candidates(grid, a.region))
    tot = collections.Counter()
    for t, v in sorted(cap.items(), key=lambda kv: (int(XY_RE.fullmatch(kv[0]).group(2)), kv[0])):
        tot["in"] += v["in"]
        tot["out"] += v["out"]
        if a.verbose:
            print(f"{t}: in {v['in']} {dict(sorted(v['in_by_class'].items()))}; out {v['out']} "
                  f"{dict(sorted(v['out_by_class'].items()))}")
    cin = [v["in"] for v in cap.values()]
    cout = [v["out"] for v in cap.values()]
    print(f"{len(cap)} pin tiles; in per tile {min(cin)}..{max(cin)}, total {tot['in']}; "
          f"out per tile {min(cout)}..{max(cout)}, total {tot['out']}")
    if a.json:
        Path(a.json).write_text(json.dumps({t: {"in": v["in"], "out": v["out"],
                                                "in_by_class": dict(v["in_by_class"]),
                                                "out_by_class": dict(v["out_by_class"])}
                                            for t, v in cap.items()}, indent=1) + "\n")


def cmd_export(a):
    outs = [Path(a.out_prefix + s) for s in (".prerouted", ".partpins", ".json")]
    if all(o.exists() for o in outs):
        print(f"[skip] {', '.join(o.name for o in outs)} exist")
        return
    grid = region.load_grid()
    rtiles = region.region_tiles(grid, a.region)
    inside = {xy_name(grid[t]) for t in rtiles}
    nodes = partpins.Nodes(grid, [(grid[t]["grid_x"], grid[t]["grid_y"]) for t in rtiles])
    asg = json.loads(Path(a.assign_json).read_text())
    replay = dict(l.split("\t", 1) for l in Path(a.prerouted).read_text().splitlines() if "\t" in l)
    node_of = lambda w: nodes.of(*w.split("/", 1))
    pins, lines, errors = [], {}, []
    for p in asg["pins"]:
        r = replay.get(p["net"])
        if r is None:
            errors.append(f"{p['net']}: no route in {a.prerouted}")
            continue
        ents = partpins.entries(r)
        pn = node_of(p["wire"])
        at = [k for k, (w, _, _) in enumerate(ents) if not w.startswith("SITEWIRE") and node_of(w) == pn]
        if len(at) != 1:
            errors.append(f"{p['net']}: pin {p['wire']} on the route {len(at)} times")
            continue
        inner = [pip for _, pip, _ in ents if pip and pip.split("/", 1)[0] in inside]
        if inner:
            errors.append(f"{p['net']}: {len(inner)} pip(s) in the region, e.g. {inner[0]}")
            continue
        k = at[0]
        if p["dir"] == "out":
            if ents[k][1]:
                errors.append(f"{p['net']}: output pin {ents[k][0]} is not the route's source")
                continue
            kept = [e for j, e in enumerate(ents) if j != k]
        else:
            kept = ents
        lines[p["net"]] = ";".join(";".join(e) for e in kept)
        tile, wire = p["wire"].split("/", 1)
        pins.append({"net": p["net"], "dir": p["dir"], "port": p["port"], "bit": p["bit"], "wire": ents[k][0],
                     "alias_tile": p["tile"], "alias_wire": wire, "entries_kept": len(kept),
                     "entries_dropped": len(ents) - len(kept), "crossings_in_reference": 1,
                     "assigned_wire": p["wire"]})
    if errors:
        for e in errors[:20]:
            print("ERROR " + e)
        sys.exit(1)
    with open(outs[0], "w") as f:
        for line in Path(a.prerouted).read_text().splitlines():
            name = line.split("\t", 1)[0]
            f.write(f"{name}\t{lines[name]}\n" if name in lines else line + "\n")
    outs[1].write_text("".join(f"{p['net']}\t{p['wire']}\n" for p in pins))
    summary = {"region": a.region, "routed_json": a.routed_json, "assign_json": a.assign_json, "pins": pins,
               "inputs": sum(p["dir"] == "in" for p in pins), "outputs": sum(p["dir"] == "out" for p in pins),
               "input_nets_entering_more_than_once": 0}
    outs[2].write_text(json.dumps(summary, indent=1) + "\n")
    print(f"wrote {outs[0].name}, {outs[1].name}, {outs[2].name}: {summary['inputs']} input and "
          f"{summary['outputs']} output partition pins, every static route outside the region and through its pin")


def cmd_proxy(a):
    outs = [Path(a.out_prefix + s) for s in (".v", ".xdc")]
    if all(o.exists() for o in outs):
        print(f"[skip] {', '.join(o.name for o in outs)} exist")
        return
    grid = region.load_grid()
    rtiles = region.region_tiles(grid, a.region)
    at = {(grid[t]["grid_x"], grid[t]["grid_y"]): grid[t] for t in rtiles}
    spec = json.loads(Path(a.spec).read_text())
    pins = json.loads(Path(a.partpins_json).read_text())["pins"]
    widths = dict(spec["inputs"] + spec["outputs"])
    used = collections.Counter()
    bel_of = {}
    for p in sorted(pins, key=lambda p: (p["assigned_wire"], p["net"])):
        x, y = map(int, XY_RE.fullmatch(p["assigned_wire"].split("/", 1)[0]).groups())
        clb = [(x + dx, y) for dx in (-1, 1) if (x + dx, y) in at and at[(x + dx, y)]["type"].startswith("CLB")]
        if len(clb) != 1:
            sys.exit(f"{p['net']}: pin tile X{x}Y{y} has {len(clb)} logic tiles beside it in the region")
        k = used[clb[0]]
        if k >= 2 * len(CONFIG["proxy_lanes"]):
            sys.exit(f"{p['net']}: more than {2 * len(CONFIG['proxy_lanes'])} pins beside X{clb[0][0]}Y{clb[0][1]}")
        used[clb[0]] += 1
        bel_of[(p["port"], p["bit"])] = (f"X{clb[0][0]}Y{clb[0][1]}/SLICE_X{k // len(CONFIG['proxy_lanes'])}Y0."
                                         f"{CONFIG['proxy_lanes'][k % len(CONFIG['proxy_lanes'])]}6LUT")
    ref = lambda n, i: n if widths[n] == 1 else f"{n}[{i}]"
    clk = spec["clk"]
    lines = [f"module {CONFIG['proxy_top']} (input wire {clk});", f"    wire {clk}_i, {clk}_g;",
             f"    IBUF ibuf_{clk} (.I({clk}), .O({clk}_i));", f"    BUFG bufg_{clk} (.I({clk}_i), .O({clk}_g));"]
    for n, w in spec["inputs"] + spec["outputs"]:
        lines.append(f"    wire {'' if w == 1 else f'[{w - 1}:0] '}{n};")
    conns = [f".{clk}({clk}_g)"] + [f".{n}({n})" for n, _ in spec["inputs"] + spec["outputs"]]
    lines.append(f"    rm_slot {CONFIG['rm_inst']} ({', '.join(conns)});")
    for n, w in spec["inputs"]:
        for i in range(w):
            lines.append(f'    (* keep, BEL = "{bel_of[(n, i)]}" *) LUT1 #(.INIT(2\'b01)) px_{n}_{i} '
                         f"(.I0(1'b0), .O({ref(n, i)}));")
    for n, w in spec["outputs"]:
        for i in range(w):
            lines.append(f'    (* keep, BEL = "{bel_of[(n, i)]}" *) LUT1 #(.INIT(2\'b10)) px_{n}_{i} '
                         f"(.I0({ref(n, i)}), .O());")
    lines.append("endmodule")
    outs[0].write_text("\n".join(lines) + "\n")
    xdc = [l for l in Path(a.xdc).read_text().splitlines() if re.search(rf"get_ports\s+{clk}\b", l)]
    p = CONFIG["proxy_pblock"]
    xdc += [f"create_pblock {p}", f"add_cells_to_pblock [get_pblocks {p}] [get_cells {CONFIG['rm_inst']}]",
            f"resize_pblock [get_pblocks {p}] -add {{{' '.join(region.pblock_ranges(a.region))}}}"]
    outs[1].write_text("\n".join(xdc) + "\n")
    print(f"wrote {outs[0].name}, {outs[1].name}: {len(bel_of)} placement proxies at the logic tiles beside their "
          f"pins ({len(used)} tiles, at most {max(used.values())} per tile); placement only, never in a module build")


def main():
    ap = argparse.ArgumentParser(description="Place partition pins without a reference build: candidate boundary "
                                             "wires per region INT tile from prjxray-db, one pin per boundary net "
                                             "near its placed static endpoint, buses bit-sliced along the edge, "
                                             "a per-tile cap; then turn the greybox build routed to them "
                                             "(nextpnr -o partition-pins-route) into the module builds' inputs")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capacity", help="boundary-crossing wires per pin tile")
    c.add_argument("--region", default=CONFIG["region"])
    c.add_argument("--json")
    c.add_argument("-v", "--verbose", action="store_true")
    s = sub.add_parser("assign", help="pins from a placed (greybox) static build")
    s.add_argument("placed_json")
    s.add_argument("static_synth", help="static synthesis json with the RM instance as a blackbox (port names)")
    s.add_argument("out_prefix")
    s.add_argument("--region", default=CONFIG["region"])
    s.add_argument("--spec", default=str(CONFIG["spec"]))
    s.add_argument("--tile-cap", type=int, default=CONFIG["tile_cap"])
    s.add_argument("--endpoint-cells", help="also write the names of the static cells at the boundary nets' ends")
    s.add_argument("--module-ends", action="store_true",
                   help="the placed json has a module in the pblock: cost each pin by its distance to the net's "
                        "module-side cells (w_module) instead of a bit-slice target row")
    s.add_argument("--w-module", type=float, default=CONFIG["w_module"])
    s.add_argument("--keep-per-net", type=int, default=CONFIG["keep_per_net"])
    s.add_argument("--exclude-wrap-exits", action="store_true",
                   help="also drop a candidate whose wires outside the region are all _N/_S wrap aliases (nextpnr's "
                        "node has no such wire, so the pin has no route out)")
    e = sub.add_parser("export", help="the greybox build routed to the pins -> .prerouted/.partpins/.json for the "
                                      "module builds (same format as flow/partpins.py)")
    e.add_argument("routed_json")
    e.add_argument("prerouted", help="replay_dump.py's .prerouted of that build (boundary nets kept)")
    e.add_argument("assign_json")
    e.add_argument("out_prefix")
    e.add_argument("--region", default=CONFIG["region"])
    x = sub.add_parser("proxy", help="a placement-only netlist for one module: the module with a BEL-fixed LUT1 "
                                     "beside each partition pin, standing in for the static side")
    x.add_argument("partpins_json", help="export's .json")
    x.add_argument("xdc", help="the design's xdc (the clock lines are kept)")
    x.add_argument("out_prefix")
    x.add_argument("--region", default=CONFIG["region"])
    x.add_argument("--spec", default=str(CONFIG["spec"]))
    a = ap.parse_args()
    if a.cmd == "assign":
        CONFIG["tile_cap"] = a.tile_cap
        CONFIG["module_ends"] = a.module_ends
        CONFIG["w_module"] = a.w_module
        CONFIG["keep_per_net"] = a.keep_per_net
        CONFIG["exclude_wrap_exits"] = a.exclude_wrap_exits
    {"capacity": cmd_capacity, "assign": cmd_assign, "export": cmd_export, "proxy": cmd_proxy}[a.cmd](a)


if __name__ == "__main__":
    main()
