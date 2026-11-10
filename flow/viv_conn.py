"""Connection-level comparisons for the Vivado placement-strategy study (docs/vivado-placement-strategy.md).
Same exported netlist: Vivado's own placement (build/exact/<d>_p5_vref_exact) against exact imports of ours.
A RUN is a build/exact directory name (or a short variant like pl14_off_stub_s1); runs without cells.txt are
read from build/viv_strategy/xdump/<RUN> (flow/exact_dump.py output plus net_delays.txt / slack.txt).

  viv_conn.py classes DESIGN RUN...    all connections by (driver -> sink pin, fanout): mean distance / net delay
  viv_conn.py distance DESIGN RUN...   net delay against Manhattan distance (all sinks, LUT-input sinks)
  viv_conn.py arcs DESIGN RUN...       cell arc delays on reported paths, by bel (6LUT/5LUT, xFF/x5FF)
  viv_conn.py bels DESIGN RUN...       lone 5LUTs, x5FF use, 5LUT/x5FF share on the worst 100 paths
  viv_conn.py steps DESIGN RUN...      worst-100 path hops / net delay by step class and fanout, delay-distance fit
  viv_conn.py startff DESIGN RUN...    start FFs of the worst paths: next to their D-LUT or their first load
The first RUN's export (designs/exact/<RUN>/netlist.json) gives the connectivity."""
import argparse
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import viv_strategy as vs

E = vs.CONFIG["exact_out"]
S = vs.CONFIG["exact_src"]
X = vs.CONFIG["out"] / "xdump"


def full(d, r):
    return r if r.startswith(d) else f"{d}_p5_{r}_exact"


def base(d, r):
    n = full(d, r)
    return E / n if (E / n / "cells.txt").exists() else X / n


def nd(fn):
    out = {}
    for ln in Path(fn).read_text().splitlines():
        p = ln.split("\t")
        if len(p) >= 2:
            out[p[0]] = int(p[1])
    return out


def kind(t):
    return "LUT" if vs.LUT_RE.match(t or "") else "FF" if vs.FF_RE.match(t or "") else (t or "?")


def fo_bucket(f):
    return "1" if f == 1 else "2-8" if f <= 8 else "9-32" if f <= 32 else ">32"


def load(d, runs):
    nl = vs.Netlist(S / full(d, runs[0]) / "netlist.json")
    places = {"vivado": base(d, "vref")}
    for r in runs:
        places[r] = base(d, r)
    return nl, places


def classes(a):
    nl, places = load(a.design, a.runs)
    res = {}
    for k, b in places.items():
        C = vs.read_cells(b / "cells.txt")
        dl = nd(b / "net_delays.txt")
        acc = defaultdict(lambda: [0, 0.0, 0.0, 0])
        for bit, (dc, dp) in nl.driver.items():
            sk = nl.sinks.get(bit, [])
            if not sk or dc not in C or len(sk) > 200 or nl.type(dc) in ("BUFG", "IBUF"):
                continue
            pa = vs.pos_of(C, dc)
            for sc, sp in sk:
                t = nl.type(sc)
                if t is None or t in ("OBUF", "RAM32M"):
                    continue
                pb = vs.pos_of(C, sc)
                if not pa or not pb:
                    continue
                key = f"{kind(nl.type(dc))}->{kind(t)}{'.' + re.sub(r'\[.*', '', sp) if kind(t) == 'FF' else ''} fo{fo_bucket(len(sk))}"
                q = acc[key]
                q[0] += 1
                q[1] += abs(pa[0] - pb[0]) + abs(pa[1] - pb[1])
                de = dl.get(f"{sc}/{sp}")
                if de is not None:
                    q[2] += de
                    q[3] += 1
        res[k] = acc
    keys = sorted(res["vivado"], key=lambda k: -res["vivado"][k][0])
    print("| connection class | n | " + " | ".join(f"{x} dist / ps" for x in res) + " |")
    print("|---|---|" + "---|" * len(res))
    for k in keys:
        if res["vivado"][k][0] < a.min:
            continue
        print(f"| {k} | {res['vivado'][k][0]} | " + " | ".join(
            f"{res[x][k][1] / max(1, res[x][k][0]):.1f} / {res[x][k][2] / max(1, res[x][k][3]):.0f}" for x in res) + " |")
    for x in res:
        n = sum(q[0] for q in res[x].values())
        m = sum(q[3] for q in res[x].values())
        print(f"{x}: all connections mean distance {sum(q[1] for q in res[x].values()) / n:.2f}, "
              f"mean net delay {sum(q[2] for q in res[x].values()) / m:.1f} ps")


def distance(a):
    nl, places = load(a.design, a.runs)
    order = ["0 same slice", "0 same tile", "1", "2", "3-4", "5-8", "9-16", "17-32", ">32"]

    def db(x):
        return order[0] if x < 0 else order[1] if x == 0 else "1" if x == 1 else "2" if x == 2 else "3-4" if x <= 4 \
            else "5-8" if x <= 8 else "9-16" if x <= 16 else "17-32" if x <= 32 else ">32"
    for lut_only in (False, True):
        res = {}
        for k, b in places.items():
            C = vs.read_cells(b / "cells.txt")
            dl = nd(b / "net_delays.txt")
            acc = defaultdict(lambda: [0, 0])
            for bit, (dc, dp) in nl.driver.items():
                sk = nl.sinks.get(bit, [])
                if dc not in C or len(sk) > 200 or nl.type(dc) in ("BUFG", "IBUF"):
                    continue
                for sc, sp in sk:
                    if lut_only and not vs.LUT_RE.match(nl.type(sc) or ""):
                        continue
                    pa, pb = vs.pos_of(C, dc), vs.pos_of(C, sc)
                    de = dl.get(f"{sc}/{sp}")
                    if not pa or not pb or de is None:
                        continue
                    x = abs(pa[0] - pb[0]) + abs(pa[1] - pb[1])
                    if x == 0 and C[dc][1] == C[sc][1]:
                        x = -1
                    q = acc[db(x)]
                    q[0] += 1
                    q[1] += de
            res[k] = acc
        print("sinks:", "LUT inputs only" if lut_only else "all")
        print("| distance | " + " | ".join(f"{x} n / mean ps" for x in res) + " |")
        print("|---|" + "---|" * len(res))
        for k in order:
            print(f"| {k} | " + " | ".join(f"{res[x][k][0]} / {res[x][k][1] / max(1, res[x][k][0]):.0f}" for x in res) + " |")


def arcs(a):
    for r in ["vref"] + a.runs:
        b = base(a.design, r)
        C = vs.read_cells(b / "cells.txt")
        acc = defaultdict(list)
        txt = "".join((E / full(a.design, r) / f).read_text() for f in ("paths_noicap.rpt", "paths_setup.rpt")
                      if (E / full(a.design, r) / f).exists())
        for m in re.finditer(r"\((Prop_lut\d_I\d_O|Prop_fdre_C_Q|Setup_fdre_C_\w+)\)\s+([\d.]+)\s+[\d.]+\s+[rf]?\s+(\S+)", txt):
            arc, dly, pin = m.groups()
            cell = pin.rsplit("/", 1)[0]
            if cell not in C:
                continue
            bel = C[cell][2]
            if arc.startswith("Prop_lut"):
                k = "LUT@5LUT" if bel.endswith("5LUT") else "LUT@6LUT"
            else:
                k = ("FF@x5FF" if bel.endswith("5FF") else "FF@xFF") + (" clk-q" if "C_Q" in arc else " setup")
            acc[k].append(float(dly))
        print(full(a.design, r), {k: (len(v), round(st.mean(v), 3)) for k, v in sorted(acc.items())})


def bels(a):
    for r in ["vref"] + a.runs:
        b = base(a.design, r)
        C = vs.read_cells(b / "cells.txt")
        occ = {(s, bl): ref for n, (ref, s, bl) in C.items()}
        lone = Counter(ref for n, (ref, s, bl) in C.items()
                       if bl.endswith("5LUT") and vs.LUT_RE.match(ref) and (s, bl[0] + "6LUT") not in occ)
        ff5 = sum(1 for n, (ref, s, bl) in C.items() if vs.FF_RE.match(ref) and bl.endswith("5FF"))
        ffa = sum(1 for n, (ref, s, bl) in C.items() if vs.FF_RE.match(ref))
        P = vs.read_pin_paths(E / full(a.design, r) / "paths_noicap.txt", 100)
        l5 = lt = f5 = ft = 0
        for *_, pins in P:
            for c, _, _ in vs.cell_seq(pins):
                ref, s, bl = C.get(c, ("", "", ""))
                if vs.LUT_RE.match(ref):
                    lt += 1
                    l5 += bl.endswith("5LUT")
                if vs.FF_RE.match(ref):
                    ft += 1
                    f5 += bl.endswith("5FF")
        print(f"{full(a.design, r)}: lone 5LUT (6LUT empty) {sum(lone.values())} {dict(lone)}; FFs on x5FF {ff5}/{ffa}; "
              f"worst-100 paths: LUTs on 5LUT {l5}/{lt}, FFs on x5FF {f5}/{ft}")


def steps(a):
    nl, places = load(a.design, a.runs)
    K = 100
    res = {}
    for k, b in places.items():
        C = vs.read_cells(b / "cells.txt")
        dl = nd(b / "net_delays.txt")
        P = vs.read_pin_paths(E / full(a.design, "vref" if k == "vivado" else k) / "paths_noicap.txt", 200)
        hop = defaultdict(float)
        dsum = defaultdict(float)
        xs, ys = [], []
        for _, _, _, pins in P[:K]:
            seq = vs.cell_seq(pins)
            for (u, ui, uo), (v, vi, vo) in zip(seq, seq[1:]):
                pa, pb = vs.pos_of(C, u), vs.pos_of(C, v)
                if not pa or not pb:
                    continue
                bit = nl.pin.get((u, uo))
                f = len(nl.sinks.get(bit, [])) if bit is not None else 0
                kv = kind(nl.type(v) or C[v][0])
                cls = f"{kind(nl.type(u) or C[u][0])}->{kv}{'.' + re.sub(r'\[.*', '', vi or '') if kv == 'FF' else ''}"
                dist = abs(pa[0] - pb[0]) + abs(pa[1] - pb[1])
                de = dl.get(f"{v}/{vi}")
                for key in (cls, "fo" + fo_bucket(max(1, f))):
                    hop[key] += dist / K
                    if de is not None:
                        dsum[key] += de / K
                if de is not None and C[u][1] != C[v][1]:
                    xs.append(dist)
                    ys.append(de)
        mx, my = st.mean(xs), st.mean(ys)
        sl = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / max(1e-9, sum((x - mx) ** 2 for x in xs))
        print(f"{k}: fit on {len(xs)} critical inter-slice steps: net ps = {my - sl * mx:.0f} + {sl:.1f} x distance")
        res[k] = (hop, dsum)
    keys = sorted({k for h, _ in res.values() for k in h}, key=lambda k: -max(res[x][0].get(k, 0) for x in res))
    print(f"per path (own worst {K}): hops / net ps by step class")
    print("| class | " + " | ".join(res) + " |")
    print("|---|" + "---|" * len(res))
    for k in keys:
        print(f"| {k} | " + " | ".join(f"{res[x][0].get(k, 0):.1f} / {res[x][1].get(k, 0):.0f}" for x in res) + " |")


def startff(a):
    nl, places = load(a.design, a.runs)
    for k, b in places.items():
        C = vs.read_cells(b / "cells.txt")
        P = vs.read_pin_paths(E / full(a.design, "vref" if k == "vivado" else k) / "paths_noicap.txt", 200)
        rows = {}
        for *_, pins in P[:100]:
            seq = vs.cell_seq(pins)
            s = seq[0][0]
            if len(seq) < 2 or not vs.FF_RE.match(C.get(s, ("",))[0]):
                continue
            nxt = seq[1][0]
            dd = nl.drv_of(s, "D")
            pa, pb, pd = vs.pos_of(C, s), vs.pos_of(C, nxt), vs.pos_of(C, dd) if dd in C else None
            rows[s] = (C[s][1] == C[nxt][1], bool(dd in C and vs.LUT_RE.match(C[dd][0]) and C[dd][1] == C[s][1]),
                       abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]), pd and abs(pd[0] - pb[0]) + abs(pd[1] - pb[1]))
        n = max(1, len(rows))
        print(f"{k}: {len(rows)} distinct start FFs on the worst 100 paths; first load in the FF's slice "
              f"{sum(r[0] for r in rows.values())}, D-LUT in the FF's slice {sum(r[1] for r in rows.values())}; "
              f"mean FF->first-load distance {sum(r[2] for r in rows.values()) / n:.1f}; "
              f"D-LUT -> first-load distances {[r[3] for r in rows.values()]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["classes", "distance", "arcs", "bels", "steps", "startff"])
    ap.add_argument("design")
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--min", type=int, default=30, help="classes: smallest class shown")
    a = ap.parse_args()
    globals()[a.cmd](a)


if __name__ == "__main__":
    main()
