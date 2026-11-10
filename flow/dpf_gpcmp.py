"""Compare two global placements of one nextpnr GP problem (flow/dpf_bridge.py import format, placer grid units)
on the nets of the gp-dump: HPWL unweighted and with nextpnr's x weight 2, plus footprint (sd_x, sd_y).
usage: python3 flow/dpf_gpcmp.py DUMP NAME=POSFILE...
"""
import statistics
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from dpf_bridge import read_dump


def main():
    d = read_dump(sys.argv[1])
    cells = {c["idx"]: c for c in d["cells"]}
    for arg in sys.argv[2:]:
        name, f = arg.split("=", 1)
        pos = {}
        for line in open(f):
            t = line.split()
            if len(t) == 3:
                pos[t[0]] = (float(t[1]), float(t[2]))
        def at(p):
            if p[1] == "@":
                x, y = map(int, p[2:].split(","))
                return x + 0.5, y + 0.5
            c = cells[int(p[1:].split("|", 1)[0])]
            if c["fixed"]:
                return c["x"], c["y"]
            return pos.get(c["name"])
        h1 = h2 = 0.0
        miss = 0
        for _, pins in d["nets"]:
            pts = [at(p) for p in pins]
            if any(q is None for q in pts):
                miss += 1
                continue
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            h1 += (max(xs) - min(xs)) + (max(ys) - min(ys))
            h2 += 2 * (max(xs) - min(xs)) + (max(ys) - min(ys))
        mv = [pos[c["name"]] for c in d["cells"] if not c["fixed"] and c["name"] in pos]
        sdx = statistics.pstdev([p[0] for p in mv])
        sdy = statistics.pstdev([p[1] for p in mv])
        print(f"{name}: HPWL {h1:.0f} (x weight 2: {h2:.0f}), sd_x {sdx:.1f}, sd_y {sdy:.1f}, nets missing {miss}")


if __name__ == "__main__":
    main()
