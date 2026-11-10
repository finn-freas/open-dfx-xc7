"""Cell-by-cell composition of the worst Vivado paths of an exact-import / build_rte run (Finding 17).

  path_cells.py RUN_DIR [RUN_DIR ...] [--n 100] [--json OUT] [--show K]

Reads paths_noicap.txt (slack, net, logic, then the pins of the path in order; ICAP paths already excluded) and the
run's EDIF (cell types). Each path's cells are its pins grouped by cell, in order. Kinds: src, end, carry (CARRY4),
muxf, lut_xr (LUTs nextpnr made: feed-throughs and carry splits, exported as xr_*), lut1 (other LUT1), lut (LUT2-6),
other. "cells/path" counts every cell including start and end.
"""
import argparse
import json
import re
import statistics
from collections import Counter
from pathlib import Path


def edif_types(edf):
    types = {}
    cur = None
    inst = re.compile(r'\(instance\s+(?:\(rename\s+(\S+)\s+"((?:[^"\\]|\\.)*)"\)|(\S+))')
    cref = re.compile(r"\(cellRef\s+(\S+)")
    for ln in Path(edf).read_text(errors="replace").splitlines():
        m = inst.search(ln)
        if m:
            cur = m.group(2) if m.group(2) is not None else m.group(3)
            cur = cur.replace('\\"', '"')
        m = cref.search(ln)
        if m and cur is not None:
            types[cur] = m.group(1).strip(")")
            cur = None
    return types


def kind(t, name):
    if t is None:
        return "unknown"
    if t == "CARRY4":
        return "carry"
    if t.startswith("MUXF"):
        return "muxf"
    if t.startswith("LUT"):
        if name.split("/")[-1].startswith("xr_"):
            return "lut_xr"
        return "lut1" if t == "LUT1" else "lut"
    return "other"


def parse(run, n):
    run = Path(run)
    edf = next(iter(sorted(run.glob("*.edf"))), None)
    types = edif_types(edf) if edf else {}
    out = []
    for ln in (run / "paths_noicap.txt").read_text(errors="replace").splitlines():
        f = ln.split("\t")
        if len(f) < 4:
            continue
        pins = f[3].split()
        cells = []
        for p in pins:
            c = p.rsplit("/", 1)[0]
            if not cells or cells[-1] != c:
                cells.append(c)
        tys = [types.get(c) or types.get(c.split("/")[-1]) for c in cells]
        kinds = Counter()
        for i, (c, t) in enumerate(zip(cells, tys)):
            kinds["src" if i == 0 else "end" if i == len(cells) - 1 else kind(t, c)] += 1
        out.append({"slack": float(f[0]), "net": float(f[1]), "logic": float(f[2]), "n_cells": len(cells),
                    "kinds": dict(kinds), "cells": cells, "types": tys})
        if len(out) >= n:
            break
    return out


def summary(paths):
    tot = Counter()
    for p in paths:
        tot.update(p["kinds"])
    k = len(paths) or 1
    return {"paths": len(paths), "cells_per_path": round(statistics.mean(p["n_cells"] for p in paths), 2) if paths else None,
            "per_path": {x: round(v / k, 2) for x, v in sorted(tot.items())},
            "lut_types": dict(Counter(t for p in paths for t in p["types"][1:-1] if t and t.startswith("LUT")))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--json")
    ap.add_argument("--show", type=int, default=0)
    a = ap.parse_args()
    res = {}
    for r in a.runs:
        ps = parse(r, a.n)
        res[r] = {"summary": summary(ps), "paths": ps}
        s = res[r]["summary"]
        print(f"{Path(r).name}: {s['paths']} paths, {s['cells_per_path']} cells/path, per path {s['per_path']}, LUT sizes {s['lut_types']}")
        for p in ps[: a.show]:
            print("   ", p["slack"], " -> ".join(f"{(t or '?')}:{c[-38:]}" for c, t in zip(p["cells"], p["types"])))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
