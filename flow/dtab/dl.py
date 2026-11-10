"""Shared helpers: device geometry (INT column / row index, column and row crossings), pin classes, the current
placer delay models, and a streaming reader of the arc dataset (build_ds.py)."""
import gzip, json, math, os, re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, "/home/finnf/open-dfx-xc7/flow")
ARCS = Path("/home/finnf/open-dfx-xc7/build/dtab/arcs")
TG = "/home/finnf/open-dfx-xc7/toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7/xc7a50t/tilegrid.json"

_tg = json.load(open(TG))
W = max(t["grid_x"] for t in _tg.values()) + 1
H = max(t["grid_y"] for t in _tg.values()) + 1
coltypes = defaultdict(set); rowtypes = defaultdict(set)
for t in _tg.values():
    coltypes[t["grid_x"]].add(t["type"]); rowtypes[t["grid_y"]].add(t["type"])
INTX = sorted(x for x in range(W) if coltypes[x] & {"INT_L", "INT_R"})
def _col_kind(x):
    c = coltypes[x]
    if c & {"BRAM_L", "BRAM_R"}: return "bram"
    if c & {"DSP_L", "DSP_R"}: return "dsp"
    if "CLK_FEED" in c or "CLK_BUFG_REBUF" in c: return "clk"
    if "VFRAME" in c: return "vframe"
    if c & {"VBRK"}: return "vbrk"
    if c & {"CMT_FIFO_R", "CMT_FIFO_L", "CMT_TOP_R_LOWER_B", "CMT_TOP_L_LOWER_B"}: return "cmt"
    return ""
COLKIND = [_col_kind(x) for x in range(W)]
HROWS = [y for y in range(H) if any(t.startswith("HCLK_CLB") or t == "HCLK_L" for t in rowtypes[y])]
BROWS = [y for y in range(H) if any(t.startswith("BRKH_CLB") or t == "BRKH_INT" for t in rowtypes[y])]
def _site_int(x):
    if x in INTX: return x
    c = coltypes[x]
    right = any(t.endswith("_L") or t.startswith("LIO") for t in c if t not in ("NULL",))
    cand = [i for i in INTX if (i > x if right else i < x)]
    if not cand: cand = INTX
    return min(cand, key=lambda i: abs(i - x))
INT_OF = [_site_int(x) for x in range(W)]
IX = [INTX.index(INT_OF[x]) for x in range(W)]
SPECIAL_ROWS = set(HROWS) | set(BROWS)
IY = []
k = 0
for y in range(H):
    IY.append(k)
    if y not in SPECIAL_ROWS: k += 1
def _prefix(flags):
    p, s = [0], 0
    for f in flags:
        s += f; p.append(s)
    return p
PX = {kind: _prefix([1 if COLKIND[x] == kind else 0 for x in range(W)]) for kind in ("bram", "dsp", "clk", "vbrk", "vframe", "cmt")}
PY = {"hclk": _prefix([1 if y in HROWS else 0 for y in range(H)]), "brk": _prefix([1 if y in BROWS else 0 for y in range(H)])}
def between(p, a, b):
    lo, hi = (a, b) if a <= b else (b, a)
    return p[hi] - p[lo + 1] if hi > lo else 0
def crossings(sx, sy, dx, dy):
    ia, ib = INT_OF[sx], INT_OF[dx]
    return {k: between(PX[k], ia, ib) for k in PX} | {k: between(PY[k], sy, dy) for k in PY}

SRC = ["LUT", "MUX", "FF", "CYO", "CYCO", "BRAM", "DSP", "IO"]
DST = ["LUT", "FFD", "CE", "SR", "CYS", "CYDI", "CYCI", "MUXI", "MUXS", "BYP", "BRA", "BRD", "BRC", "DSP", "IO"]
def src_cls(t, pin):
    if t.startswith("LUT") or t.startswith(("RAM32", "RAM64", "RAMS", "RAMD", "SRL")): return "LUT"
    if t.startswith("MUXF"): return "MUX"
    if t.startswith("FD"): return "FF"
    if t == "CARRY4": return "CYCO" if pin.startswith("CO") else "CYO"
    if t.startswith("RAMB"): return "BRAM"
    if t.startswith("DSP"): return "DSP"
    return "IO"
def dst_cls(t, pin):
    if t.startswith("LUT"): return "LUT"
    if t.startswith(("RAM32", "RAM64", "RAMS", "RAMD")):
        return {"LRADR": "LUT", "LRWADR": "LUT", "LRWE": "CE"}.get(pin, "BYP")
    if t.startswith("SRL"):
        return "LUT" if pin.startswith("A") else ("CE" if pin == "CE" else "BYP")
    if t.startswith("FD"):
        return "FFD" if pin == "D" else ("CE" if pin == "CE" else "SR")
    if t == "CARRY4":
        return "CYS" if pin.startswith("S") else ("CYDI" if pin.startswith("DI") else "CYCI")
    if t.startswith("MUXF"): return "MUXS" if pin == "S" else "MUXI"
    if t.startswith("RAMB"):
        if pin.startswith("ADDR"): return "BRA"
        if pin.startswith("DI"): return "BRD"
        return "BRC"
    if t.startswith("DSP"): return "DSP"
    return "IO"

import xroute_predict as xp
MAT = xp.load_matrix(Path("/home/finnf/open-dfx-xc7/build/dtab/matrix_a6pd.txt"))
def letter(bel):
    m = re.match(r"([A-H])(5|6)?(LUT|FF)$", bel)
    return m.group(1) if m else None
def is_carry_cascade(a):
    return a["st"] == "CARRY4" and a["sp"] == "CO[3]" and a["dt"] == "CARRY4" and a["dp"] == "CI"
def direct(a):
    """dedicated in-slice connection (no general routing)"""
    if a["rel"] != "site": return False
    if is_carry_cascade(a): return True
    st, dt, dp = a["st"], a["dt"], a["dp"]
    if st.startswith("FD"): return False
    if dt.startswith("FD") and dp == "D": return True
    if dt == "CARRY4" and (dp.startswith("S[") or dp.startswith("DI[")): return True
    if dt.startswith("MUXF") and dp in ("I0", "I1"): return True
    return False
def m_static(a, p=(816, 40, 40, 18, 18)):
    if is_carry_cascade(a): return 0.0
    dx, dy = abs(a["dx"] - a["sx"]), abs(a["dy"] - a["sy"])
    return p[0] + p[1] * min(dy, 6) + p[2] * max(dy - 6, 0) + p[3] * min(dx, 12) + p[4] * max(dx - 12, 0)
def m_sa(a, site=750, site_other=866, tile=850, alpha=313, beta=1.235):
    if is_carry_cascade(a): return 0.0
    if a["rel"] == "site":
        if a["dt"].startswith("LUT") or a["dc"] == "LUT" and not a["dt"].startswith("FD"): return site
        if direct(a): return 0.0
        return site_other
    if a["rel"] == "tile": return tile
    return alpha + beta * xp.lookup(MAT, a["dx"] - a["sx"], a["dy"] - a["sy"])
def m_matrix(a):
    if is_carry_cascade(a): return 0.0
    if a["rel"] in ("site", "tile"):
        ls, ld = letter(a["sb"]), letter(a["db"])
        if a["rel"] == "site" and ls and ld and ls == ld: return 0.0
        return 700.0 if re.match(r"[A-H]5FF$", a["sb"]) else 150.0
    return float(xp.lookup(MAT, a["dx"] - a["sx"], a["dy"] - a["sy"]))

FIELDS = ("design", "st", "sb", "sp", "dt", "db", "dp", "sx", "sy", "dx", "dy", "rel", "fo", "viv", "rank")
def runs(pattern=None):
    out = sorted(f.name[:-7] for f in ARCS.glob("*.tsv.gz"))
    return [r for r in out if not pattern or re.search(pattern, r)]
def arcs(run):
    with gzip.open(ARCS / f"{run}.tsv.gz", "rt") as fh:
        for ln in fh:
            f = ln.rstrip("\n").split("\t")
            if len(f) != len(FIELDS): continue
            a = dict(zip(FIELDS, f))
            for k in ("sx", "sy", "dx", "dy", "fo", "rank"): a[k] = int(a[k])
            a["viv"] = float(a["viv"])
            a["sc"], a["dc"] = src_cls(a["st"], a["sp"]), dst_cls(a["dt"], a["dp"])
            a["run"] = run
            yield a
def seed_of(run):
    m = re.search(r"_s(\d)_exact$", run)
    return int(m.group(1)) if m else 0

_pcols = sorted({t["grid_x"] for t in _tg.values() if any(s != "TIEOFF" for s in t.get("sites", {}).values())})
_prows = sorted({t["grid_y"] for t in _tg.values() if any(s != "TIEOFF" for s in t.get("sites", {}).values())})
PXC = [max([i for i, c in enumerate(_pcols) if c <= x] or [0]) for x in range(W)]
PYC = [max([i for i, c in enumerate(_prows) if c <= y] or [0]) for y in range(H)]
def m_static(a, p=(816, 40, 40, 18, 18)):
    if is_carry_cascade(a): return 0.0
    dx, dy = abs(PXC[a["dx"]] - PXC[a["sx"]]), abs(PYC[a["dy"]] - PYC[a["sy"]])
    return p[0] + p[1] * min(dy, 6) + p[2] * max(dy - 6, 0) + p[3] * min(dx, 12) + p[4] * max(dx - 12, 0)
