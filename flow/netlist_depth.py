import argparse
import json
import re
import statistics
import sys
from pathlib import Path

CONFIG = {
    "comb": re.compile(r"^(LUT[1-6]|INV|MUXF[78]|CARRY4)$"),
    "lut": re.compile(r"^(LUT[1-6]|INV)$"),
    "outputs": {"O", "O5", "O6", "CO", "CO[0]", "CO[1]", "CO[2]", "CO[3]"},
    "top_n": 100,
}


def load(js):
    j = json.loads(Path(js).read_text())
    mods = j["modules"]
    top = next(n for n, m in mods.items() if m.get("attributes", {}).get("top"))
    return mods[top]


def analyse(js):
    m = load(js)
    cells = m["cells"]
    driver = {}
    for name, c in cells.items():
        dirs = c.get("port_directions", {})
        for p, bits in c["connections"].items():
            if dirs.get(p) == "output":
                for b in bits:
                    if isinstance(b, int):
                        driver[b] = (name, p)
    memo = {}
    sys.setrecursionlimit(1000000)

    def arr(bit):
        if not isinstance(bit, int) or bit not in driver:
            return (0, 0)
        name, _ = driver[bit]
        c = cells[name]
        if not CONFIG["comb"].match(c["type"]):
            return (0, 0)
        if name in memo:
            return memo[name]
        memo[name] = (0, 0)
        dirs = c.get("port_directions", {})
        best = (0, 0)
        for p, bits in c["connections"].items():
            if dirs.get(p) != "input":
                continue
            for b in bits:
                a = arr(b)
                if a > best:
                    best = a
        is_lut = 1 if CONFIG["lut"].match(c["type"]) else 0
        memo[name] = (best[0] + is_lut, best[1] + 1)
        return memo[name]

    ends = []
    for name, c in cells.items():
        if CONFIG["comb"].match(c["type"]):
            continue
        dirs = c.get("port_directions", {})
        for p, bits in c["connections"].items():
            if dirs.get(p) != "input" or p in ("C", "CLK", "CLKARDCLK", "CLKBWRCLK", "WCLK"):
                continue
            for b in bits:
                a = arr(b)
                ends.append((a[0], a[1], f"{name}.{p}"))
    ends.sort(reverse=True)
    top = ends[:CONFIG["top_n"]]
    hist = {}
    for lut, _, _ in ends:
        hist[lut] = hist.get(lut, 0) + 1
    return {"max_lut_levels": ends[0][0] if ends else 0, "max_logic_levels": max((e[1] for e in ends), default=0),
            "mean_lut_levels_top": round(statistics.mean(e[0] for e in top), 2) if top else 0,
            "endpoints": len(ends), "hist": dict(sorted(hist.items())), "worst": [e[2] for e in ends[:5]]}


def main():
    ap = argparse.ArgumentParser(description="LUT levels between sequential cells in a yosys xc7 JSON netlist "
                                             "(CARRY4 and MUXF count as logic levels, not LUT levels)")
    ap.add_argument("json", nargs="+")
    a = ap.parse_args()
    for js in a.json:
        print(js, json.dumps(analyse(js)))


if __name__ == "__main__":
    main()
