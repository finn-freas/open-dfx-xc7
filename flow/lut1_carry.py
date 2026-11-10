"""Where do LUT1 inverters feed CARRY4 pins in a yosys xc7 netlist (Finding 17)?  usage: lut1_carry.py NETLIST.json"""
import json
import sys
from collections import Counter

j = json.load(open(sys.argv[1]))
m = next(v for v in j["modules"].values() if v.get("attributes", {}).get("top"))
cells = m["cells"]
drv = {}
users = {}
for n, c in cells.items():
    for p, bits in c["connections"].items():
        d = c.get("port_directions", {}).get(p)
        for i, b in enumerate(bits):
            if d == "output":
                drv[b] = (n, p, i)
            else:
                users.setdefault(b, []).append((n, p, i))
lut1 = {n for n, c in cells.items() if c["type"] == "LUT1"}
kinds = Counter()
inv = 0
for n in lut1:
    c = cells[n]
    init = c["parameters"].get("INIT", "")
    o = c["connections"]["O"][0]
    us = users.get(o, [])
    for (un, up, ui) in us:
        if cells[un]["type"] == "CARRY4":
            kinds[(up, init)] += 1
print("LUT1 cells:", len(lut1))
print("LUT1 -> CARRY4 pin uses (pin, INIT):", dict(kinds))
dt = Counter()
for n, c in cells.items():
    if c["type"] != "CARRY4":
        continue
    for p in ("DI", "S"):
        for b in c["connections"].get(p, []):
            if isinstance(b, str):
                dt[(p, "const")] += 1
                continue
            d = drv.get(b)
            dt[(p, cells[d[0]]["type"] if d else "port")] += 1
print("CARRY4 input drivers:", dict(sorted(dt.items())))
