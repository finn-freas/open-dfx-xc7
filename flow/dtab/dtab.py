"""Python twin of the nextpnr table model (reads a fit.py table file)."""
import math, os, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import dl


class Table:
    def __init__(self, fn):
        it = iter(open(fn).read().splitlines())
        self.fo = []
        for ln in it:
            p = ln.split()
            if not p:
                continue
            if p[0] == "ix": self.ix = list(map(int, p[1:]))
            elif p[0] == "iy": self.iy = list(map(int, p[1:]))
            elif p[0] == "intx": self.intx = list(map(int, p[1:]))
            elif p[0] == "cx": self.cx = list(map(float, p[1:]))
            elif p[0] == "cy": self.cy = list(map(float, p[1:]))
            elif p[0] == "g":
                self.gx, self.gy, self.ex, self.ey = int(p[1]), int(p[2]), float(p[3]), float(p[4])
                self.g = [list(map(float, next(it).split())) for _ in range(self.gx)]
            elif p[0] == "src": self.src = {k: float(v) for k, v in (t.split("=") for t in p[1:])}
            elif p[0] == "dst": self.dst = {k: float(v) for k, v in (t.split("=") for t in p[1:])}
            elif p[0] == "direct": self.direct = float(p[1])
            elif p[0] in ("site", "tile"):
                vals = list(map(float, p[1:])); n = len(dl.DST)
                setattr(self, p[0], {(sc, dc): vals[i * n + j] for i, sc in enumerate(dl.SRC) for j, dc in enumerate(dl.DST)})
            elif p[0] == "fo": self.fo = list(map(float, p[1:]))

    def geo(self, sx, sy, dx, dy):
        i = abs(self.ix[dx] - self.ix[sx]); j = abs(self.iy[dy] - self.iy[sy])
        e = 0.0
        if i >= self.gx: e += (i - self.gx + 1) * self.ex; i = self.gx - 1
        if j >= self.gy: e += (j - self.gy + 1) * self.ey; j = self.gy - 1
        a, b = self.intx[sx], self.intx[dx]
        lo, hi = min(a, b), max(a, b)
        c = (self.cx[hi] - self.cx[lo + 1]) if hi > lo else 0.0
        lo, hi = min(sy, dy), max(sy, dy)
        c += (self.cy[hi] - self.cy[lo + 1]) if hi > lo else 0.0
        return self.g[i][j] + e + c

    def __call__(self, a, use_fo=True):
        if dl.is_carry_cascade(a): return 0.0
        if a["rel"] == "site":
            if dl.direct(a): return self.direct
            return self.site[(a["sc"], a["dc"])]
        if a["rel"] == "tile": return self.tile[(a["sc"], a["dc"])]
        d = self.geo(a["sx"], a["sy"], a["dx"], a["dy"]) + self.src[a["sc"]] + self.dst[a["dc"]]
        if use_fo and self.fo and any(self.fo):
            d += self.fo[min(int(math.log2(max(a["fo"], 1))), 7)]
        return d


_T = {}


def model(fn):
    if fn not in _T:
        _T[fn] = Table(fn)
    return _T[fn]


def m_tab(a):
    return model(os.environ.get("DTAB", "/home/finnf/open-dfx-xc7/build/dtab/t_mean.txt"))(a)


def m_tab2(a):
    return model(os.environ.get("DTAB2", "/home/finnf/open-dfx-xc7/build/dtab/t_crit.txt"))(a)


T_DIR = "/home/finnf/open-dfx-xc7/build/dtab/"


def m_mean(a):
    return model(T_DIR + "t_mean.txt")(a)


def m_crit(a):
    return model(T_DIR + "t_crit.txt")(a)


def m_fo(a):
    return model(T_DIR + "t_fo.txt")(a)
