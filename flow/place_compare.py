import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_openxc7 import DB

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "tilegrid": DB / "artix7" / "xc7a50t" / "tilegrid.json",
    "dump_root": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/place_dump"),
    "xsrc_root": ROOT / "build" / "qor" / "xtime" / "src",
    "out": ROOT / "build" / "qor" / "place" / "compare",
    "top_paths": 200,
    "slice_re": re.compile(r"^(SLICE_X\d+Y\d+)/([A-H])(6LUT|5LUT|5FF|FF|CARRY4)?"),
}


def site_grid():
    tg = json.loads(CONFIG["tilegrid"].read_text())
    m = {}
    for t in tg.values():
        for s in t.get("sites", {}):
            m[s] = (t["grid_x"], t["grid_y"])
    return m


def read_cells(fn):
    cells = {}
    for ln in Path(fn).read_text().splitlines():
        p = ln.split("\t")
        if len(p) >= 3 and p[2]:
            cells[p[0]] = {"type": p[1], "site": p[2], "bel": p[3] if len(p) > 3 else ""}
    return cells


def read_paths(fn):
    out = []
    for ln in Path(fn).read_text().splitlines():
        p = ln.split("\t")
        if len(p) < 7:
            continue
        out.append({"slack": float(p[0]), "delay": float(p[1]), "logic": float(p[2]), "net": float(p[3]),
                    "start": p[4], "end": p[5], "cells": p[6].split(" ")})
    return out


def read_nextpnr(fn):
    cells = {}
    for ln in Path(fn).read_text().splitlines():
        m = re.match(r"^\{(.*)\} (\S+)$", ln)
        if m:
            site = m.group(2).split("/")[0]
            cells[m.group(1)] = {"site": site, "bel": m.group(2).split("/")[-1]}
    return cells


def hops(cells, place, grid):
    pts = [grid.get(place[c]["site"]) for c in cells if c in place]
    pts = [p for p in pts if p]
    if len(pts) < 2:
        return None
    hop = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:]))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return {"hop": hop, "bbox": (max(xs) - min(xs)) + (max(ys) - min(ys)), "n": len(pts)}


def slice_use(place):
    per = defaultdict(Counter)
    for c, v in place.items():
        if v["site"].startswith("SLICE"):
            b = v["bel"]
            kind = "lut" if "LUT" in b else ("ff" if "FF" in b else ("carry" if "CARRY" in b else "other"))
            per[v["site"]][kind] += 1
    lut = [c["lut"] for c in per.values() if c["lut"]]
    ff = [c["ff"] for c in per.values() if c["ff"]]
    return {"slices": len(per), "slices_with_lut": len(lut), "slices_with_ff": len(ff),
            "lut_per_slice": round(statistics.mean(lut), 2) if lut else 0,
            "ff_per_slice": round(statistics.mean(ff), 2) if ff else 0}


def extent(place, grid):
    pts = [grid[v["site"]] for v in place.values() if v["site"].startswith("SLICE") and v["site"] in grid]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return {"x": [min(xs), max(xs)], "y": [min(ys), max(ys)],
            "x_mean": round(statistics.mean(xs), 1), "y_mean": round(statistics.mean(ys), 1),
            "x_sd": round(statistics.pstdev(xs), 1), "y_sd": round(statistics.pstdev(ys), 1)}


def hard_sites(place):
    return sorted(f"{c} {v['site']}" for c, v in place.items() if v["site"].startswith(("RAMB", "DSP")))


def summarise(rows):
    if not rows:
        return {}
    return {k: round(statistics.mean(r[k] for r in rows), 2) for k in rows[0]}


def compare(design_free, design_placed, xsrc):
    grid = site_grid()
    free = read_cells(CONFIG["dump_root"] / design_free / "cells.txt")
    placed = read_cells(CONFIG["dump_root"] / design_placed / "cells.txt")
    npr = read_nextpnr(CONFIG["xsrc_root"] / xsrc / "place.txt")
    fpaths = read_paths(CONFIG["dump_root"] / design_free / "paths.txt")[:CONFIG["top_paths"]]
    ppaths = read_paths(CONFIG["dump_root"] / design_placed / "paths.txt")[:CONFIG["top_paths"]]
    res = {"vivado_free": {"slices": slice_use(free), "extent": extent(free, grid)},
           "nextpnr": {"slices": slice_use(placed), "extent": extent(placed, grid)}}
    res["vivado_free"]["hard"] = hard_sites(free)
    res["nextpnr"]["hard"] = hard_sites(placed)
    for tag, paths in (("vivado_free_paths", fpaths), ("nextpnr_paths", ppaths)):
        own, other = (free, placed) if tag == "vivado_free_paths" else (placed, free)
        a, b = [], []
        for p in paths:
            h1, h2 = hops(p["cells"], own, grid), hops(p["cells"], other, grid)
            if h1 and h2:
                a.append(dict(h1, delay=p["delay"], logic=p["logic"], net=p["net"]))
                b.append(h2)
        res[tag] = {"n": len(a), "own": summarise(a), "other_placement": summarise(b),
                    "slack": [paths[0]["slack"], paths[-1]["slack"]] if paths else None,
                    "endpoints": Counter(re.sub(r"\d+", "#", p["end"].split("/")[0])[:40] for p in paths).most_common(5),
                    "startpoints": Counter(re.sub(r"\d+", "#", p["start"].split("/")[0])[:40] for p in paths).most_common(5)}
    worst_f = fpaths[0] if fpaths else None
    worst_p = ppaths[0] if ppaths else None
    res["worst"] = {}
    for tag, p in (("vivado_free", worst_f), ("nextpnr", worst_p)):
        if not p:
            continue
        res["worst"][tag] = {"slack": p["slack"], "delay": p["delay"], "logic": p["logic"], "net": p["net"],
                             "cells": [(c, free.get(c, {}).get("site"), placed.get(c, {}).get("site")) for c in p["cells"]]}
    moved = 0
    same = 0
    for c, v in npr.items():
        if c in placed:
            same += placed[c]["site"] == v["site"]
            moved += placed[c]["site"] != v["site"]
    res["check_imposed"] = {"same_site": same, "different_site": moved}
    return res


def main():
    ap = argparse.ArgumentParser(description="compare Vivado's own placement of the yosys netlist with nextpnr's "
                                             "(vivado/place_dump.tcl outputs)")
    ap.add_argument("free")
    ap.add_argument("placed")
    ap.add_argument("xsrc")
    a = ap.parse_args()
    res = compare(a.free, a.placed, a.xsrc)
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    fn = CONFIG["out"] / f"{a.placed}.json"
    fn.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "worst"}, indent=1))
    print(f"written {fn}")


if __name__ == "__main__":
    main()
