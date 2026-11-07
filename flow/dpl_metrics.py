"""Packing and detailed-placement metrics of one placement, Vivado's own or ours imposed in Vivado
(vivado/dpl_dump.tcl outputs: cells.txt, paths.txt, wirelength.txt, util.rpt, congestion.rpt, times.txt),
measured on the yosys netlist the placement was made from.

  dpl_metrics.py DUMP_DIR NETLIST_JSON [--top-paths N] [--json OUT]
Distances are in prjxray tile-grid units (one CLB column with its interconnect is 2 in x).
"""
import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_openxc7 import DB

CONFIG = {
    "tilegrid": DB / "artix7" / "xc7a50t" / "tilegrid.json",
    "top_paths": 200,
    "ff_types": {"FDRE", "FDSE", "FDCE", "FDPE", "LDCE", "LDPE"},
    "big_fanout": 400,
}

_GRID = None


def grid():
    global _GRID
    if _GRID is None:
        tg = json.loads(CONFIG["tilegrid"].read_text())
        _GRID = {s: (t["grid_x"], t["grid_y"]) for t in tg.values() for s in t.get("sites", {})}
    return _GRID


def read_cells(fn):
    cells = {}
    for ln in Path(fn).read_text().splitlines():
        p = ln.split("\t")
        if len(p) >= 4 and p[2]:
            cells[p[0]] = {"type": p[1], "site": p[2], "bel": p[3]}
    return cells


def read_paths(fn, n):
    out = []
    for ln in Path(fn).read_text().splitlines():
        p = ln.split("\t")
        if len(p) < 8:
            continue
        out.append({"slack": float(p[0]), "delay": float(p[1]), "logic": float(p[2]), "net": float(p[3]),
                    "start": p[4], "end": p[5], "clock": p[6], "pins": p[7].split(" ")})
        if len(out) >= n:
            break
    return out


class Netlist:
    def __init__(self, fn):
        j = json.loads(Path(fn).read_text())
        mods = j["modules"]
        top = next(k for k, m in mods.items() if m.get("attributes", {}).get("top"))
        m = mods[top]
        self.cells = {}
        self.drv = {}
        self.sinks = defaultdict(list)
        self.out_pin = {}
        for name, c in m["cells"].items():
            if c["type"].startswith("$"):
                continue
            self.cells[name] = c
            for port, bits in c["connections"].items():
                d = c.get("port_directions", {}).get(port, "input")
                for i, b in enumerate(bits):
                    if isinstance(b, str):
                        continue
                    pn = port if len(bits) == 1 else f"{port}[{i}]"
                    if d == "output":
                        self.drv[b] = (name, pn)
                        self.out_pin[(name, pn)] = b
                    else:
                        self.sinks[b].append((name, pn))
        self.clock_bits = {b for c in self.cells.values() if c["type"] in CONFIG["ff_types"]
                           for b in c["connections"].get("C", c["connections"].get("G", [])) if not isinstance(b, str)}

    def port_bit(self, cell, port):
        bits = self.cells[cell]["connections"].get(port)
        return bits[0] if bits and not isinstance(bits[0], str) else None


def letter(bel):
    b = bel.split(".")[-1]
    return b[0] if b[:1] in ("A", "B", "C", "D") and ("LUT" in b or "FF" in b) else None


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def path_cells(pins):
    cells = []
    for pin in pins:
        c = pin.rsplit("/", 1)[0]
        if not cells or cells[-1] != c:
            cells.append(c)
    return cells


def metrics(dump, netlist_fn, top_paths=None):
    top_paths = top_paths or CONFIG["top_paths"]
    g = grid()
    nl = Netlist(netlist_fn)
    place = read_cells(Path(dump) / "cells.txt")
    pos = {c: g[v["site"]] for c, v in place.items() if v["site"] in g}
    res = {}

    per = defaultdict(Counter)
    lutsites = defaultdict(set)
    for c, v in place.items():
        if not v["site"].startswith("SLICE"):
            continue
        b = v["bel"].split(".")[-1]
        kind = "lut" if "LUT" in b else ("ff" if "FF" in b else ("carry" if "CARRY" in b else ("mux" if "MUX" in b else "other")))
        per[v["site"]][kind] += 1
        if kind == "lut":
            lutsites[(v["site"], b[0])].add(b[1:])
    lut = [c["lut"] for c in per.values() if c["lut"]]
    ff = [c["ff"] for c in per.values() if c["ff"]]
    res["slices"] = len(per)
    res["slicem"] = len({v["site"] for v in place.values() if v["bel"].startswith("SLICEM.")})
    res["lut_per_slice"] = round(statistics.mean(lut), 2) if lut else 0
    res["ff_per_slice"] = round(statistics.mean(ff), 2) if ff else 0
    res["lut_sites"] = len(lutsites)
    res["lut_sites_dual"] = sum(1 for v in lutsites.values() if len(v) == 2)
    res["f7f8_bels"] = sum(1 for v in place.values() if re.search(r"\.F[78]", v["bel"]))

    pair = Counter()
    for name, c in nl.cells.items():
        if c["type"] not in CONFIG["ff_types"] or name not in place:
            continue
        b = nl.port_bit(name, "D")
        if b is None or b not in nl.drv:
            continue
        dcell = nl.drv[b][0]
        if not nl.cells[dcell]["type"].startswith("LUT") or dcell not in place:
            continue
        pf, pd = place[name], place[dcell]
        if pf["site"] != pd["site"]:
            pair["other_slice"] += 1
        elif letter(pf["bel"]) == letter(pd["bel"]):
            pair["direct"] += 1
        else:
            pair["same_slice"] += 1
    tot = sum(pair.values()) or 1
    res["lutff"] = {k: pair[k] for k in ("direct", "same_slice", "other_slice")}
    res["lutff_direct_pct"] = round(100 * pair["direct"] / tot, 1)

    nxt = {}
    carries = [n for n, c in nl.cells.items() if c["type"] == "CARRY4"]
    for n in carries:
        co = nl.cells[n]["connections"].get("CO", [])
        if len(co) == 4 and not isinstance(co[3], str):
            for s, p in nl.sinks.get(co[3], []):
                if p == "CI" and nl.cells[s]["type"] == "CARRY4":
                    nxt[n] = s
    tails = set(nxt.values())
    chains, broken, s_local, s_tot = 0, 0, 0, 0
    for h in carries:
        if h in tails:
            continue
        chain = [h]
        while chain[-1] in nxt:
            chain.append(nxt[chain[-1]])
        if len(chain) < 2:
            continue
        chains += 1
        for a, b in zip(chain, chain[1:]):
            if a in place and b in place:
                ma = re.match(r"SLICE_X(\d+)Y(\d+)", place[a]["site"])
                mb = re.match(r"SLICE_X(\d+)Y(\d+)", place[b]["site"])
                if ma and mb and not (ma.group(1) == mb.group(1) and int(mb.group(2)) == int(ma.group(2)) + 1):
                    broken += 1
    for n in carries:
        for b in nl.cells[n]["connections"].get("S", []):
            if isinstance(b, str) or b not in nl.drv:
                continue
            d = nl.drv[b][0]
            if nl.cells[d]["type"].startswith("LUT") and d in place and n in place:
                s_tot += 1
                s_local += place[d]["site"] == place[n]["site"]
    res["carry"] = {"chains": chains, "links_not_aligned": broken,
                    "s_lut_in_carry_slice_pct": round(100 * s_local / max(s_tot, 1), 1)}

    hpwl_tot, nnets = 0, 0
    net_hpwl = {}
    hard = []
    for b, (dc, dp) in nl.drv.items():
        if b in nl.clock_bits:
            continue
        pins = [dc] + [s for s, _ in nl.sinks.get(b, [])]
        pts = [pos[c] for c in pins if c in pos]
        if len(pts) < 2 or len(pins) > CONFIG["big_fanout"]:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        h = (max(xs) - min(xs)) + (max(ys) - min(ys))
        net_hpwl[b] = h
        hpwl_tot += h
        nnets += 1
        dt = nl.cells[dc]["type"]
        for s, _ in nl.sinks.get(b, []):
            st = nl.cells[s]["type"]
            hb_d, hb_s = dt.startswith(("RAMB", "DSP")), st.startswith(("RAMB", "DSP"))
            if (hb_d != hb_s) and dc in pos and s in pos:
                hard.append(dist(pos[dc], pos[s]))
    res["hpwl_total"] = hpwl_tot
    res["nets"] = nnets
    res["hard_conn"] = len(hard)
    res["hard_dist_mean"] = round(statistics.mean(hard), 2) if hard else None

    cs = defaultdict(list)
    for name, c in nl.cells.items():
        if c["type"] in CONFIG["ff_types"] and name in place and place[name]["site"].startswith("SLICE"):
            con = c["connections"]
            key = tuple(str(con.get(p, ["-"])[0]) for p in ("C", "CE", "R", "S", "CLR", "PRE", "G", "GE"))
            cs[key].append(place[name]["site"])
    res["control_sets"] = len(cs)
    res["ff_slice_cs_pairs"] = sum(len(set(v)) for v in cs.values())
    res["ff_slice_cs_min"] = sum(-(-len(v) // 8) for v in cs.values())

    paths = read_paths(Path(dump) / "paths.txt", top_paths)
    hops, nets_on, segs, pathhpwl = [], set(), [], []
    for p in paths:
        cells = path_cells(p["pins"])
        pts = [pos[c] for c in cells if c in pos]
        if len(pts) >= 2:
            hops.append(sum(dist(a, b) for a, b in zip(pts, pts[1:])))
        for a, b in zip(cells, cells[1:]):
            if a in pos and b in pos:
                segs.append(dist(pos[a], pos[b]))
        ph = 0
        for pin in p["pins"]:
            if "/" not in pin:
                continue
            c, pn = pin.rsplit("/", 1)
            bt = nl.out_pin.get((c, pn))
            if bt is not None and bt in net_hpwl:
                nets_on.add(bt)
                ph += net_hpwl[bt]
        pathhpwl.append(ph)
    res["crit_paths"] = len(paths)
    res["crit_wns"] = paths[0]["slack"] if paths else None
    res["crit_hop_mean"] = round(statistics.mean(hops), 1) if hops else None
    res["crit_seg_mean"] = round(statistics.mean(segs), 2) if segs else None
    res["crit_nets"] = len(nets_on)
    res["crit_net_hpwl_mean"] = round(statistics.mean(net_hpwl[b] for b in nets_on), 2) if nets_on else None
    res["crit_path_hpwl_mean"] = round(statistics.mean(pathhpwl), 1) if pathhpwl else None
    res["crit_net_delay_mean"] = round(statistics.mean(p["net"] for p in paths), 3) if paths else None
    res["crit_logic_delay_mean"] = round(statistics.mean(p["logic"] for p in paths), 3) if paths else None
    pc = Counter()
    for p in paths:
        f = p["end"].rsplit("/", 1)[0]
        if f not in nl.cells or nl.cells[f]["type"] not in CONFIG["ff_types"]:
            continue
        b = nl.port_bit(f, "D")
        d = nl.drv.get(b, (None,))[0]
        if d and nl.cells[d]["type"].startswith("LUT") and d in place and f in place:
            ok = place[d]["site"] == place[f]["site"] and letter(place[d]["bel"]) == letter(place[f]["bel"])
            pc["direct" if ok else "not"] += 1
    res["crit_end_lutff"] = sum(pc.values())
    res["crit_end_lutff_direct_pct"] = round(100 * pc["direct"] / max(sum(pc.values()), 1), 1)

    wl = Path(dump) / "wirelength.txt"
    if wl.exists():
        for ln in wl.read_text().splitlines():
            k, v = ln.split()
            res[k] = int(v)
    tm = Path(dump) / "times.txt"
    if tm.exists():
        for ln in tm.read_text().splitlines():
            k, v = ln.split()
            res[f"vivado_{k}_s"] = float(v)
    cg = Path(dump) / "congestion.rpt"
    if cg.exists():
        t = cg.read_text(errors="replace")
        res["congestion_rows"] = [ln.strip() for ln in t.splitlines()
                                  if re.match(r"\|\s*(North|South|East|West)\s*\|", ln.strip())][:8]
    u = Path(dump) / "util.rpt"
    if u.exists():
        t = u.read_text(errors="replace")
        m = re.search(r"\|\s*Slice\s*\|\s*(\d+)", t)
        if m:
            res["util_slices"] = int(m.group(1))
        m = re.search(r"\|\s*Slice LUTs\*?\s*\|\s*(\d+)", t)
        if m:
            res["util_luts"] = int(m.group(1))
    tr = Path(dump) / "timing.rpt"
    if tr.exists():
        m = re.search(r"WNS\(ns\).*?\n[- ]+\n\s*(-?[0-9.]+)\s+(-?[0-9.]+)\s+(\d+)", tr.read_text(errors="replace"))
        if m:
            res["wns"] = float(m.group(1))
            res["tns"] = float(m.group(2))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("netlist")
    ap.add_argument("--top-paths", type=int, default=CONFIG["top_paths"])
    ap.add_argument("--json")
    a = ap.parse_args()
    r = metrics(a.dump, a.netlist, a.top_paths)
    s = json.dumps(r, indent=1)
    if a.json:
        Path(a.json).write_text(s + "\n")
    print(s)


if __name__ == "__main__":
    main()
