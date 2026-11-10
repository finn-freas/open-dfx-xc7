"""Turn an exact-import Vivado run (flow/exact_src.py source + vivado/build_rte.tcl output) into a flow/place_paths.py
dump: cells.txt from the source's place.txt / macros.txt (the placement is imposed exactly), paths.txt from the run's
paths_noicap.txt (slack, net, logic, pins). Cell types come from the bel (LUT / FD / CARRY4), enough for place_paths.
usage: exact_dump.py SRC_DIR RUN_DIR OUT_DIR"""
import re
import sys
from pathlib import Path

src, run, out = (Path(p) for p in sys.argv[1:4])
out.mkdir(parents=True, exist_ok=True)
place = {}
for ln in (src / "place.txt").read_text().splitlines():
    m = re.match(r"\{(.*)\}\s+(\S+)$", ln)
    if m:
        place[m.group(1)] = m.group(2)
for ln in (src / "macros.txt").read_text().splitlines() if (src / "macros.txt").exists() else []:
    m = re.match(r"\{(.*?)\}\s+(.*)$", ln)
    if m:
        for sub, bel in re.findall(r"\{(\S+?)\}\s+(\S+)", m.group(2)):
            place[f"{m.group(1)}/{sub}"] = bel


def kind(bel):
    b = bel.split("/")[-1]
    if b.endswith("LUT"):
        return "LUT6"
    if b.endswith("FF"):
        return "FDRE"
    return b


with open(out / "cells.txt", "w") as f:
    for c, b in place.items():
        site = b.split("/")[0]
        f.write(f"{c}\t{kind(b)}\t{site}\t{b.split('/')[-1]}\n")
with open(out / "paths.txt", "w") as f:
    for ln in (run / "paths_noicap.txt").read_text().splitlines():
        p = ln.split("\t")
        if len(p) < 4:
            continue
        pins = p[3].split()
        cells = []
        for pin in pins:
            c = pin.rsplit("/", 1)[0]
            if not cells or cells[-1] != c:
                cells.append(c)
        slack, net, logic = float(p[0]), float(p[1]), float(p[2])
        f.write("\t".join([p[0], f"{net + logic:.3f}", p[2], p[1], pins[0], pins[-1], " ".join(cells)]) + "\n")
print(out, len(place), "cells")
