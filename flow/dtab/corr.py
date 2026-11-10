"""Placer estimate vs Vivado: worst setup slack (without ICAPE2 paths) of each placement under each arc model
(-o dtab-eval logs, build/dtab/eval) against Vivado's (exact import). Spearman / Pearson over placements per design,
mean |Fmax error|. usage: corr.py [TAG-PREFIX]"""
import math, re, sys
from collections import defaultdict
from pathlib import Path

E = Path("/home/finnf/open-dfx-xc7/build/dtab/eval")
X = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact")
Q = Path("/home/finnf/open-dfx-xc7/build/qor/oxc7")
MODELS = ["static", "sa", "matrix", "dtab", "dtab-nofo"]
tag = sys.argv[1] if len(sys.argv) > 1 else ""


def viv(name):
    f = X / name / "slack.txt"
    if not f.exists():
        return None
    kv = dict(l.split(None, 1) for l in f.read_text().splitlines() if " " in l)
    try:
        return float(kv["wns_noicap"])
    except (KeyError, ValueError):
        return None


def rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0] * len(xs)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and xs[o[j + 1]] == xs[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2
        i = j + 1
    return r


def pearson(a, b):
    n = len(a); ma = sum(a) / n; mb = sum(b) / n
    c = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a); vb = sum((y - mb) ** 2 for y in b)
    return c / math.sqrt(va * vb) if va and vb else float("nan")


fm = lambda wns: 1000.0 / (5.0 - wns)
pts = defaultdict(list)
for f in sorted(E.glob(f"{tag}*.log")):
    m = re.match(rf"{tag}(.+)_(rv_soc|bram|rv_big|rv_mul)_s(\d)\.log$", f.name)
    if not m:
        continue
    vv, d, s = m.groups()
    t = f.read_text(errors="ignore")
    est = {}
    for mm in re.finditer(r"dtab-eval: (\S+)\s+worst setup slack (\S+) ns, without ICAPE2 paths (\S+) ns", t):
        est[mm.group(1)] = float(mm.group(3))
    if len(est) < len(MODELS):
        continue
    v = viv(f"{d}_p5_{vv}_s{s}_exact")
    if v is None:
        continue
    orig = Q / vv / f"{d}_p5" / f"s{s}" / "nextpnr.log"
    fl = re.findall(r"Max frequency for clock '[^']*': ([\d.]+) MHz", orig.read_text(errors="ignore")) if orig.exists() else []
    est["post-place report"] = 1000.0 / float(fl[0]) - 5.0 if fl else None
    pts[d].append((vv, s, v, est))

cols = ["post-place report"] + MODELS
print(f"placements: " + ", ".join(f"{d} {len(p)}" for d, p in pts.items()))
print("| design | n | " + " | ".join(cols) + " |")
print("|---|---|" + "---|" * len(cols))
allerr = defaultdict(list)
for d, P in pts.items():
    vf = [fm(p[2]) for p in P]
    cells = []
    for c in cols:
        ok = [(fm(p[3][c]), fm(p[2])) for p in P if p[3].get(c) is not None]
        e = [100 * (a / b - 1) for a, b in ok]
        allerr[c] += e
        sp = pearson(rank([a for a, _ in ok]), rank([b for _, b in ok]))
        cells.append(f"rho {sp:+.2f}, r {pearson([a for a, _ in ok], [b for _, b in ok]):+.2f}, "
                     f"err {sum(e)/len(e):+.1f}/{sum(map(abs, e))/len(e):.1f} %")
    print(f"| {d} | {len(P)} | " + " | ".join(cells) + " |")
print("| all (error only) | | " + " | ".join(f"{sum(allerr[c])/len(allerr[c]):+.1f}/{sum(map(abs, allerr[c]))/len(allerr[c]):.1f} %" for c in cols) + " |")
