"""Bridge between nextpnr's static placer and DREAMPlaceFPGA (BSD-3, toolchain/dreamplacefpga).

export: nextpnr's global-placement problem (--placer-static-gp-dump FILE, placer grid units) -> ISPD'16-style
        Bookshelf (design.aux/.nodes/.nets/.pl/.scl/.lib/.wts) plus map.json.
        Device model: one Bookshelf SLICE site (16 LUT / 16 FF) per Artix-7 CLB tile (2 slices x 4 LUT6 x 8 FF),
        RAMB36 / DSP48E1 columns as BRAM / DSP sites, one IO site per fixed-cell location. DREAMPlaceFPGA assumes
        UltraScale-like full-height columns (RAM every 5 rows, DSP every 2.5), so every column gets the type of its
        bels over the full height; nextpnr legalises onto the real bels afterwards.
        Nodes: one per packed netlist cell: SLICE_LUTX -> LUT<k> (k = connected A pins, LUTRAM -> LUT6) with pins
        I0..I5 / O; SLICE_FFX -> FDRE with D / Q / C / CE / R (control sets for DREAMPlace's area adjustment);
        CARRY4 -> LUT6, F7/F8 mux -> LUT3; RAMB / DSP one node. Cells of one nextpnr macro chunk are chained by
        2-pin nets without a driver (no timing arc, so no false cycles). Global clock and constant nets are not in the dump.
import: DREAMPlaceFPGA's global-placement .pl -> "<ccell base cell> <x> <y>" per line for
        --placer-static-gp-import (node centres averaged over the netlist cells of one nextpnr cell / chunk).
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


def read_dump(p):
    d = {"area": defaultdict(dict), "bels": [], "cells": [], "nets": [], "groups": {}}
    for line in open(p):
        t = line.split()
        if not t:
            continue
        k = t[0]
        if k == "grid":
            d["W"], d["H"] = int(t[1]), int(t[2])
        elif k == "group":
            d["groups"][int(t[1])] = t[2]
        elif k == "area":
            d["area"][int(t[1])][(int(t[2]), int(t[3]))] = float(t[4])
        elif k == "bel":
            d["bels"].append((int(t[1]), t[2], int(t[3]), int(t[4]), int(t[5]), t[6]))
        elif k == "cell":
            d["cells"].append({"idx": int(t[1]), "group": int(t[2]), "w": float(t[3]), "h": float(t[4]),
                               "fixed": t[5] == "1", "x": float(t[6]), "y": float(t[7]), "macro": int(t[8]),
                               "dx": int(t[9]), "dy": int(t[10]), "type": t[11], "name": t[12]})
        elif k == "net":
            d["nets"].append((t[1], t[3:3 + int(t[2])]))
    return d


N_X, N_Y = 24, 12


def lib_text():
    out = []
    for k in range(1, 7):
        out.append(f"CELL LUT{k}\n  PIN O OUTPUT")
        out += [f"  PIN I{i} INPUT" for i in range(k)]
        out += [f"  PIN X{i} INPUT" for i in range(N_X)] + [f"  PIN Y{i} OUTPUT" for i in range(N_Y)]
        out.append("END CELL\n")
    out.append("CELL FDRE\n  PIN Q OUTPUT\n  PIN D INPUT\n  PIN C INPUT CLOCK\n  PIN R INPUT CTRL\n  PIN CE INPUT CTRL")
    out += [f"  PIN X{i} INPUT" for i in range(4)] + [f"  PIN Y{i} OUTPUT" for i in range(4)]
    out.append("END CELL\n")
    for c in ["DSP48E2", "RAMB36E2"]:
        out.append(f"CELL {c}")
        out += [f"  PIN X{i} INPUT" for i in range(200)] + [f"  PIN Y{i} OUTPUT" for i in range(100)]
        out.append("END CELL\n")
    out.append("CELL IBUF\n  PIN O OUTPUT\n  PIN I INPUT\nEND CELL\n")
    out.append("CELL BUFGCE\n  PIN O OUTPUT\n  PIN I INPUT\nEND CELL\n")
    return "\n".join(out) + "\n"


class Pins:
    """Per-node pin allocation: named pins first (LUT inputs, FF ports), generic X/Y pins for the rest."""

    def __init__(self):
        self.used = defaultdict(set)
        self.gen = defaultdict(lambda: [0, 0])

    def take(self, node, want, drv, nx, ny):
        if want and want not in self.used[node]:
            self.used[node].add(want)
            return want
        g = self.gen[node]
        if drv:
            p = f"Y{g[1] % ny}"
            g[1] += 1
        else:
            p = f"X{g[0] % nx}"
            g[0] += 1
        return p


def export(a):
    d = read_dump(a.dump)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    W, H = d["W"], d["H"]
    gname = {v: k for k, v in d["groups"].items()}
    g_comb, g_ff, g_ram, g_dsp = gname.get("COMB", 0), gname.get("FF", 1), gname.get("RAM", 2), gname.get("DSP", 3)
    coltype = {}
    for (x, y), v in d["area"][g_comb].items():
        if v >= 0.5:
            coltype[x] = "SLICE"
    for g, typ, x, y, z, bn in d["bels"]:
        if g == g_ram and typ.startswith("RAMB36"):
            coltype[x] = "BRAM"
        elif g == g_dsp and typ.startswith("DSP48"):
            coltype[x] = "DSP"
    sites = {}
    for x, t in coltype.items():
        if t == "SLICE":
            ys = range(H)
        elif t == "BRAM":
            ys = range(0, H - 4, 5)
        else:
            ys = [y for k in range(0, H // 5 + 1) for y in (5 * k, 5 * k + 2) if y + 2 < H]
        for y in ys:
            sites[(x, y)] = t

    members = defaultdict(dict)
    ports = defaultdict(set)
    for name, pins in d["nets"]:
        for p in pins:
            if p[1] == "@":
                continue
            idx, port, typ, cname = p[1:].split("|", 3)
            members[int(idx)].setdefault(cname, typ)
            ports[cname].add(port)

    nodes, pl, fixed_at = [], [], {}
    node_of = {}
    cell_nodes = {}
    chains = []

    def fixed_node(x, y):
        if (x, y) not in fixed_at:
            n = f"fx_{x}_{y}"
            fixed_at[(x, y)] = n
            nodes.append((n, "IBUF"))
            pl.append(f"{n} {x} {y} 0 FIXED")
            if sites.get((x, y)) != "SLICE":
                sites[(x, y)] = "IO"
        return fixed_at[(x, y)]

    def node_type(group, typ, cname):
        if group == g_ram:
            return "RAMB36E2"
        if group == g_dsp:
            return "DSP48E2"
        if typ == "SLICE_FFX":
            return "FDRE"
        if typ == "SLICE_LUTX":
            ps = ports[cname]
            if ps & {"WE", "CLK", "DI1", "DI2", "WA1"}:
                return "LUT6"
            k = sum(1 for i in range(1, 7) if f"A{i}" in ps)
            return f"LUT{max(1, k)}"
        if typ == "CARRY4":
            return "LUT6"
        return "LUT3"

    for c in d["cells"]:
        if c["fixed"]:
            cell_nodes[c["idx"]] = [fixed_node(int(c["x"]), int(c["y"]))]
            continue
        mem = members.get(c["idx"]) or {c["name"]: c["type"]}
        names = []
        for i, (cname, typ) in enumerate(mem.items()):
            n = f"c{c['idx']}_{i}"
            nodes.append((n, node_type(c["group"], typ, cname)))
            node_of[(c["idx"], cname)] = n
            names.append(n)
        cell_nodes[c["idx"]] = names
        if len(names) > 1:
            chains.append(names)

    lut_in = {f"A{i}": f"I{i - 1}" for i in range(1, 7)}
    ff_pin = {"D": "D", "Q": "Q", "CK": "C", "CE": "CE", "SR": "R"}
    ntype = dict(nodes)
    alloc = Pins()

    def pin_for(n, port, drv):
        if n.startswith("fx_"):
            return "O" if drv else "I"
        t = ntype[n]
        if t == "FDRE":
            return alloc.take(n, ff_pin.get(port), drv, 4, 4)
        if t.startswith("LUT"):
            want = None
            if port in lut_in and int(lut_in[port][1:]) < int(t[3:]):
                want = lut_in[port]
            elif port in ("O5", "O6"):
                want = "O"
            return alloc.take(n, want, drv, N_X, N_Y)
        return alloc.take(n, None, drv, 200, 100)

    nets = []
    for name, pins in d["nets"]:
        ps, seen = [], set()
        for p in pins:
            drv = p[0] == "O"
            if p[1] == "@":
                x, y = map(int, p[2:].split(","))
                n, port = fixed_node(x, y), ""
            else:
                idx, port, typ, cname = p[1:].split("|", 3)
                idx = int(idx)
                n = node_of.get((idx, cname)) or cell_nodes[idx][0]
            if n in seen:
                continue
            seen.add(n)
            ps.append((n, port, drv))
        if len(ps) >= 2:
            nets.append(ps)
    for names in chains:
        for j in range(len(names) - 1):
            nets.append([(names[j], "", False), (names[j + 1], "", False)])

    with open(out / "design.nodes", "w") as f:
        for n, t in nodes:
            f.write(f"{n} {t}\n")
    with open(out / "design.nets", "w") as f:
        for ni, ps in enumerate(nets):
            f.write(f"net n{ni} {len(ps)}\n")
            for n, port, drv in ps:
                f.write(f"\t{n} {pin_for(n, port, drv)}\n")
            f.write("endnet\n")
    (out / "design.pl").write_text("\n".join(pl) + "\n")
    (out / "design.wts").write_text("")
    (out / "design.lib").write_text(lib_text())
    scl = ["SITE SLICE\n  LUT 16\n  FF 16\n  CARRY8 1\nEND SITE\n", "SITE DSP\n  DSP48E2 1\nEND SITE\n",
           "SITE BRAM\n  RAMB36E2 1\nEND SITE\n", "SITE IO\n  IO 64\nEND SITE\n",
           "RESOURCES\n  LUT LUT1 LUT2 LUT3 LUT4 LUT5 LUT6\n  FF  FDRE\n  CARRY8 CARRY8\n  DSP48E2 DSP48E2\n"
           "  RAMB36E2 RAMB36E2\n  IO IBUF OBUF BUFGCE\nEND RESOURCES\n", f"SITEMAP {W} {H}"]
    for (x, y) in sorted(sites):
        scl.append(f"{x} {y} {sites[(x, y)]}")
    scl.append("END SITEMAP\n")
    (out / "design.scl").write_text("\n".join(scl) + "\n")
    (out / "design.aux").write_text("design : design.nodes design.nets design.wts design.pl design.scl design.lib\n")
    cmap = {c["name"]: cell_nodes[c["idx"]] for c in d["cells"] if not c["fixed"]}
    (out / "map.json").write_text(json.dumps(cmap) + "\n")
    tc = defaultdict(int)
    for n, t in nodes:
        tc[t] += 1
    st = {"W": W, "H": H, "sites": {t: sum(1 for v in sites.values() if v == t) for t in set(sites.values())},
          "nodes": len(nodes), "node_types": dict(tc), "nets": len(nets), "cells": len(d["cells"]),
          "chains": len(chains)}
    (out / "export.json").write_text(json.dumps(st, indent=1) + "\n")
    print(json.dumps(st))


def do_import(a):
    cmap = json.loads(Path(a.map).read_text())
    pos = {}
    for line in open(a.pl):
        t = line.split()
        if len(t) >= 3 and not t[0].startswith("fx_"):
            try:
                x, y = float(t[1]), float(t[2])
            except ValueError:
                continue
            area = float(t[4]) if len(t) >= 5 else 0.0
            pos[t[0]] = (x, y, math.sqrt(area) if area > 0 else 0.0)
    lines = []
    for cell, ns in cmap.items():
        pts = [pos[n] for n in ns if n in pos]
        if not pts:
            continue
        cx = sum(p[0] + p[2] / 2 for p in pts) / len(pts)
        cy = sum(p[1] + p[2] / 2 for p in pts) / len(pts)
        lines.append(f"{cell} {cx:.4f} {cy:.4f}\n")
    Path(a.out).write_text("".join(lines))
    print(f"imported {len(lines)} of {len(cmap)} cells")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd")
    e = sp.add_parser("export")
    e.add_argument("dump")
    e.add_argument("out")
    i = sp.add_parser("import")
    i.add_argument("map")
    i.add_argument("pl")
    i.add_argument("out")
    a = ap.parse_args()
    export(a) if a.cmd == "export" else do_import(a)


if __name__ == "__main__":
    main()
