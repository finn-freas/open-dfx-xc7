"""Step 2: fit the (dx, dy) delay table on Vivado-routed arcs and write it for nextpnr (-o dtab=FILE).
delay(between tiles) = G[|dix|][|diy|] + S[src class] + D[dst class] + sum_k cost_k * (k columns/rows crossed)
  dix: INT-column index distance (the switchbox each site connects to), diy: row index distance without HCLK/BRKH rows
same slice: direct path or a routed constant per (src, dst) class; same tile: constant per (src, dst) class.
usage: fit.py OUT [--train REGEX] [--crit W] [--fo]"""
import argparse, math, re, sys
from collections import defaultdict
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import dl

KINDS = ["bram", "dsp", "clk", "vbrk", "vframe", "cmt", "hclk", "brk"]
GX, GY = 48, 160


def geo(a):
    ix = abs(dl.IX[a["dx"]] - dl.IX[a["sx"]]); iy = abs(dl.IY[a["dy"]] - dl.IY[a["sy"]])
    c = dl.crossings(a["sx"], a["sy"], a["dx"], a["dy"])
    return min(ix, GX - 1), min(iy, GY - 1), tuple(c[k] for k in KINDS)


def fobin(fo):
    return min(int(math.log2(max(fo, 1))), 7)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--train", default=r"_s[12456]_exact$")
    ap.add_argument("--crit", type=float, default=1.0, help="weight of arcs on the 50 worst Vivado paths")
    ap.add_argument("--fo", action="store_true", help="fit a per-log2(fanout) term")
    ap.add_argument("--shrink", type=float, default=30.0)
    ap.add_argument("--iters", type=int, default=25)
    a = ap.parse_args()
    runs = dl.runs(a.train)
    bins = defaultdict(lambda: [0.0, 0.0])
    near = defaultdict(lambda: [0.0, 0.0])
    ndir = [0.0, 0.0]
    for r in runs:
        for x in dl.arcs(r):
            w = a.crit if 0 <= x["rank"] < 50 else 1.0
            v = x["viv"]
            if dl.is_carry_cascade(x):
                continue
            if x["rel"] == "site" and dl.direct(x):
                ndir[0] += w; ndir[1] += w * v
                continue
            if x["rel"] in ("site", "tile"):
                for k in ((x["rel"], x["sc"], x["dc"]), (x["rel"], "*", x["dc"]), (x["rel"], "*", "*")):
                    near[k][0] += w; near[k][1] += w * v
                continue
            ix, iy, cr = geo(x)
            k = (x["sc"], x["dc"], ix, iy, cr, fobin(x["fo"]) if a.fo else 0)
            bins[k][0] += w; bins[k][1] += w * v
    print(f"train runs {len(runs)}, inter bins {len(bins)}, arcs {sum(b[0] for b in bins.values()):.0f}", file=sys.stderr)
    B = [(k, w, s / w) for k, (w, s) in bins.items()]
    S = defaultdict(float); Dd = defaultdict(float); K = [0.0] * len(KINDS); F = [0.0] * 8
    G = [[0.0] * GY for _ in range(GX)]; X = [0.0] * GX; Y = [0.0] * GY

    def pred_noG(k):
        sc, dc, ix, iy, cr, fb = k
        return S[sc] + Dd[dc] + sum(c * kk for c, kk in zip(cr, K)) + F[fb]

    for it in range(a.iters):
        for axis in (0, 1):
            acc = defaultdict(lambda: [0.0, 0.0])
            for k, w, v in B:
                ix, iy = k[2], k[3]
                r = v - pred_noG(k) - (Y[iy] if axis == 0 else X[ix])
                key = ix if axis == 0 else iy
                acc[key][0] += w; acc[key][1] += w * r
            T = X if axis == 0 else Y
            for i, (w, s) in acc.items():
                T[i] = s / w
        acc = defaultdict(lambda: [0.0, 0.0])
        for k, w, v in B:
            acc[(k[2], k[3])][0] += w; acc[(k[2], k[3])][1] += w * (v - pred_noG(k))
        for i in range(GX):
            for j in range(GY):
                w, s = acc.get((i, j), (0.0, 0.0))
                G[i][j] = (s + a.shrink * (X[i] + Y[j])) / (w + a.shrink)
        for idx, T in ((0, S), (1, Dd)):
            acc = defaultdict(lambda: [0.0, 0.0])
            for k, w, v in B:
                r = v - G[k[2]][k[3]] - pred_noG(k) + T[k[idx]]
                acc[k[idx]][0] += w; acc[k[idx]][1] += w * r
            for c, (w, s) in acc.items():
                T[c] = s / w
            off = T["LUT"]
            for c in list(T):
                T[c] -= off
        for ci in range(len(KINDS)):
            num = den = 0.0
            for k, w, v in B:
                n = k[4][ci]
                if n:
                    r = v - G[k[2]][k[3]] - pred_noG(k) + K[ci] * n
                    num += w * n * r; den += w * n * n
            K[ci] = num / den if den else 0.0
        if a.fo:
            acc = defaultdict(lambda: [0.0, 0.0])
            for k, w, v in B:
                r = v - G[k[2]][k[3]] - pred_noG(k) + F[k[5]]
                acc[k[5]][0] += w; acc[k[5]][1] += w * r
            for fb, (w, s) in acc.items():
                F[fb] = s / w
            off = F[0]
            F = [f - off for f in F]
        sse = sum(w * (v - G[k[2]][k[3]] - pred_noG(k)) ** 2 for k, w, v in B)
        print(f"iter {it}: rms {math.sqrt(sse / sum(w for _, w, _ in B)):.1f} ps", file=sys.stderr)
    ex = max(5.0, (X[GX - 1] - X[GX - 9]) / 8)
    ey = max(5.0, (Y[GY - 1] - Y[GY - 21]) / 20)
    with open(a.out, "w") as f:
        f.write("dtab 1\n")
        f.write(f"grid {dl.W} {dl.H}\n")
        f.write("ix " + " ".join(map(str, dl.IX)) + "\n")
        f.write("iy " + " ".join(map(str, dl.IY)) + "\n")
        cx = [0.0]; cy = [0.0]
        for x in range(dl.W):
            kind = dl.COLKIND[x]
            cx.append(cx[-1] + (K[KINDS.index(kind)] if kind in KINDS else 0.0))
        for y in range(dl.H):
            v = (K[KINDS.index("hclk")] if y in dl.HROWS else 0.0) + (K[KINDS.index("brk")] if y in dl.BROWS else 0.0)
            cy.append(cy[-1] + v)
        f.write("intx " + " ".join(map(str, dl.INT_OF)) + "\n")
        f.write("cx " + " ".join(f"{v:.1f}" for v in cx) + "\n")
        f.write("cy " + " ".join(f"{v:.1f}" for v in cy) + "\n")
        f.write(f"g {GX} {GY} {ex:.2f} {ey:.2f}\n")
        for i in range(GX):
            f.write(" ".join(f"{G[i][j]:.1f}" for j in range(GY)) + "\n")
        f.write("src " + " ".join(f"{c}={S[c]:.1f}" for c in dl.SRC) + "\n")
        f.write("dst " + " ".join(f"{c}={Dd[c]:.1f}" for c in dl.DST) + "\n")
        f.write(f"direct {ndir[1] / max(ndir[0], 1):.1f}\n")
        for rel in ("site", "tile"):
            vals = []
            for sc in dl.SRC:
                for dc in dl.DST:
                    for k in ((rel, sc, dc), (rel, "*", dc), (rel, "*", "*")):
                        w, s = near.get(k, (0.0, 0.0))
                        if w >= 20 or k == (rel, "*", "*"):
                            vals.append(s / w if w else 700.0); break
            f.write(f"{rel} " + " ".join(f"{v:.1f}" for v in vals) + "\n")
        f.write("fo " + " ".join(f"{v:.1f}" for v in F) + "\n")
        f.write("kinds " + " ".join(f"{k}={v:.1f}" for k, v in zip(KINDS, K)) + "\n")
    print("crossing ps:", {k: round(v, 1) for k, v in zip(KINDS, K)}, file=sys.stderr)
    print("src:", {c: round(S[c]) for c in dl.SRC}, "dst:", {c: round(Dd[c]) for c in dl.DST}, file=sys.stderr)
    print("X (dix 0..29):", [round(X[i] + Y[0]) for i in range(0, 30)], file=sys.stderr)
    print("Y (diy 0..58 step 2):", [round(Y[j] + X[0]) for j in range(0, 60, 2)], file=sys.stderr)
    print(f"direct {ndir[1] / max(ndir[0], 1):.0f} ps, extrapolation {ex:.1f}/{ey:.1f} ps", file=sys.stderr)
    if a.fo:
        print("fo:", [round(v) for v in F], file=sys.stderr)


if __name__ == "__main__":
    main()
