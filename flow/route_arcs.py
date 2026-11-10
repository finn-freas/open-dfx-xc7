import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

CONFIG = {
    "root": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/rte_arcs"),
    "top_paths": 50,
}

CLASSES = [
    ("hex", re.compile(r"^(NN|SS|EE|WW|NE|NW|SE|SW)6")),
    ("quad", re.compile(r"^(EE|WW|NN|SS)4")),
    ("double", re.compile(r"^(NN|SS|EE|WW|NE|NW|SE|SW)2")),
    ("single", re.compile(r"^(NL|NR|SL|SR|EL|ER|WL|WR)1")),
    ("long", re.compile(r"^(LV|LH|LVB)")),
    ("bounce", re.compile(r"(BYP|FAN|GFAN|BOUNCE)")),
    ("imux", re.compile(r"IMUX")),
    ("out", re.compile(r"LOGIC_OUTS")),
    ("clk", re.compile(r"(CLK|GCLK)")),
]
XY = re.compile(r"_X(\d+)Y(\d+)/")
LUT_IN = re.compile(r"CLBL[LM]_(L|LL|M)_[A-D][1-6]$")


def lut_routethru(nodes):
    """A LUT input pin node before the arc's last node: the route passes through an unused LUT."""
    return any(LUT_IN.search(n.split("/")[-1]) for n in nodes[:-1])


def wclass(node):
    b = node.split("/")[-1]
    for c, rx in CLASSES:
        if rx.search(b):
            return c
    return "other"


def xy(node):
    m = XY.search(node)
    return (int(m.group(1)), int(m.group(2))) if m else None


def load_dump(name):
    f = CONFIG["root"] / name / "routes_dump.txt"
    arcs = {}
    net = None
    up = {}
    kids = Counter()
    drv = set()
    sinks = []

    def flush():
        for pin, node in sinks:
            path, n, guard = [], node, 0
            while n and guard < 400:
                path.append(n)
                if n in drv:
                    break
                n = up.get(n)
                guard += 1
            path.reverse()
            arcs[pin] = {"net": net[0], "fanout": net[1], "nodes": path,
                         "branch": sum(max(0, kids[x] - 1) for x in path)}

    for ln in f.read_text().splitlines():
        t = ln.split("\t")
        if t[0] == "N":
            if net:
                flush()
            net, up, kids, drv, sinks = (t[1], int(t[2])), {}, Counter(), set(), []
        elif t[0] == "D" and len(t) > 2:
            drv.add(t[2])
        elif t[0] == "P" and len(t) > 2:
            up[t[2]] = t[1]
            kids[t[1]] += 1
        elif t[0] == "S" and len(t) > 2:
            sinks.append((t[1], t[2]))
    if net:
        flush()
    return arcs


def delays(name):
    d = {}
    for ln in (CONFIG["root"] / name / "net_delays.txt").read_text().splitlines():
        p, _, v = ln.partition("\t")
        try:
            d[p] = float(v)
        except ValueError:
            pass
    return d


def top_pins(name, k):
    pins = []
    for ln in (CONFIG["root"] / name / "paths_noicap.txt").read_text().splitlines()[:k]:
        ps = ln.split("\t")[3].split()
        pins += [p for p in ps[1:] if not re.search(r"/(O|Q|CO\[\d\]|O\[\d\]|DO\w*\[\d+\]|P\[\d+\])$", p)]
    return pins


def feats(a):
    nodes = a["nodes"]
    cls = Counter(wclass(n) for n in nodes)
    pts = [xy(n) for n in nodes if n.startswith("INT_")]
    pts = [p for p in pts if p]
    trav = sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) for p, q in zip(pts, pts[1:]))
    man = abs(pts[0][0] - pts[-1][0]) + abs(pts[0][1] - pts[-1][1]) if len(pts) > 1 else 0
    return cls, len(nodes), trav, man


def compare(npr, k):
    vr = npr + "_vr"
    A, B = load_dump(npr), load_dump(vr)
    dA, dB = delays(npr), delays(vr)
    pins = list(dict.fromkeys(top_pins(npr, k) + top_pins(vr, k)))
    rows = []
    for p in pins:
        if p not in A or p not in B or p not in dA or p not in dB:
            continue
        rows.append((p, A[p], B[p], dA[p], dB[p]))
    tot = Counter()
    out = {"arcs": len(rows), "delay_np": statistics.mean(r[3] for r in rows),
           "delay_vr": statistics.mean(r[4] for r in rows)}
    by = defaultdict(list)
    for p, a, b, da, db in rows:
        ca, na, ta, ma = feats(a)
        cb, nb, tb, mb = feats(b)
        for c in set(ca) | set(cb):
            tot[(c, "np")] += ca[c]
            tot[(c, "vr")] += cb[c]
        by["hops"].append((na, nb))
        by["trav"].append((ta, tb))
        by["man"].append((ma, mb))
        by["branch"].append((a["branch"], b["branch"]))
        by["delta"].append(da - db)
    out["mean"] = {k2: (statistics.mean(x[0] for x in v), statistics.mean(x[1] for x in v))
                   for k2, v in by.items() if k2 != "delta"}
    out["class_per_arc"] = {c: (round(tot[(c, "np")] / len(rows), 3), round(tot[(c, "vr")] / len(rows), 3))
                            for c in sorted({c for c, _ in tot})}
    worse = sorted(rows, key=lambda r: r[4] - r[3])[:15]
    out["worst"] = [(r[0], r[3], r[4], r[1]["fanout"], " ".join(n.split("/")[-1] for n in r[1]["nodes"]),
                     " ".join(n.split("/")[-1] for n in r[2]["nodes"])) for r in worse]
    return out, rows


def bucket_report(rows):
    """Where the extra delay sits: delta split by feature difference."""
    groups = defaultdict(list)
    for p, a, b, da, db in rows:
        ca, na, ta, ma = feats(a)
        cb, nb, tb, mb = feats(b)
        keys = []
        if lut_routethru(a["nodes"]):
            keys.append("np_lut_routethru")
        if lut_routethru(b["nodes"]):
            keys.append("vr_lut_routethru")
        if ca["long"] > cb["long"]:
            keys.append("np_more_long")
        if ca["long"] < cb["long"]:
            keys.append("vr_more_long")
        if ca["bounce"] > cb["bounce"]:
            keys.append("np_more_bounce")
        if ta > tb + 2:
            keys.append("np_detour")
        if a["branch"] > b["branch"] + 2:
            keys.append("np_more_branch")
        if na > nb:
            keys.append("np_more_hops")
        if a["fanout"] >= 8:
            keys.append("fanout>=8")
        if not keys:
            keys.append("same_shape")
        for k2 in keys:
            groups[k2].append(da - db)
    return {k2: (len(v), round(sum(v), 3), round(statistics.mean(v), 4)) for k2, v in sorted(groups.items())}


def main():
    ap = argparse.ArgumentParser(description="Per-arc routing comparison on identical placement: nextpnr's pips "
                                             "(NAME) against Vivado's routes (NAME_vr), both timed by Vivado (slow "
                                             "max per arc); wire classes, hops, detour, branching")
    ap.add_argument("names", nargs="+")
    ap.add_argument("--top", type=int, default=CONFIG["top_paths"])
    a = ap.parse_args()
    for n in a.names:
        out, rows = compare(n, a.top)
        print(f"== {n}: {out['arcs']} arcs on the {a.top} worst paths of either run; mean arc delay "
              f"nextpnr {out['delay_np']:.1f} ps, Vivado {out['delay_vr']:.1f} ps")
        for k2, v in out["mean"].items():
            print(f"  mean {k2}: nextpnr {v[0]:.2f}  vivado {v[1]:.2f}")
        print("  wire class per arc (nextpnr, vivado):", out["class_per_arc"])
        print("  delta (nextpnr - vivado, ps) by feature: (arcs, sum, mean)")
        for k2, v in bucket_report(rows).items():
            print(f"    {k2}: {v}")
        print("  arcs where nextpnr loses most:")
        for w in out["worst"]:
            print(f"    {w[0]} np {w[1]:.0f} vr {w[2]:.0f} fo {w[3]}\n      np: {w[4]}\n      vr: {w[5]}")


if __name__ == "__main__":
    main()
