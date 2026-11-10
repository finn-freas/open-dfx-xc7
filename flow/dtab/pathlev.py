"""Path level: route delay of Vivado's K worst paths (paths_noicap.txt) as each arc model predicts it, against Vivado's
routed net delay of the same paths (logic delay is Vivado's in both). usage: pathlev.py RUN-REGEX [K]"""
import math, re, sys
from collections import defaultdict
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import build_ds as B
import dl, dtab

MODELS = {"static": dl.m_static, "sa": dl.m_sa, "matrix": dl.m_matrix, "dtab": dtab.m_mean, "dtab_fo": dtab.m_fo}
if B.os.environ.get("DTAB"):
    MODELS["dtab_env"] = dtab.m_tab


def run_paths(name, K):
    e = B.E / name
    d = next(x for x in B.DES if name.startswith(x + "_"))
    if "_vref" in name:
        return None
    S = B.S / name
    cells, pin, drv, nsink = B.netlist(S / "netlist.json")
    pl = B.place_txt(S / "place.txt")
    sub = {}
    for k, v in pl.items():
        if "/" in k:
            sub.setdefault(k.rsplit("/", 1)[0], (v[0], "LUTRAM"))
    nd = {}
    for ln in (e / "net_delays.txt").read_text(errors="replace").splitlines():
        f = ln.split("\t")
        if len(f) >= 2 and f[1].strip().lstrip("-").isdigit():
            nd[f[0]] = float(f[1])

    def arc(sinkpin):
        c, p = sinkpin.rsplit("/", 1)
        b = pin.get((c, p))
        if b is None and "/" in c:
            top, sb = c.rsplit("/", 1)
            m = re.match(r"RAM([A-H])(_D1)?$", sb)
            ma, mw = re.match(r"ADR(\d)$", p), re.match(r"WADR(\d)$", p)
            if top in cells and m and (ma or mw or p == "WE"):
                port = f"ADDR{m.group(1)}[{ma.group(1)}]" if ma else (f"ADDRD[{mw.group(1)}]" if mw else "WE")
                b = pin.get((top, port))
                c, p = top, ("LRADR" if ma else "LRWADR" if mw else "LRWE")
        if b is None or b not in drv:
            return None
        dc, dp = drv[b]
        loc = lambda x: pl.get(x) or sub.get(x)
        if loc(dc) is None or loc(c) is None or dc not in cells or c not in cells:
            return None
        (ss, sbel), (ds, dbel) = loc(dc), loc(c)
        a, z = B.site.get(ss), B.site.get(ds)
        if a is None or z is None:
            return None
        rel = "site" if ss == ds else ("tile" if a[2] == z[2] else "inter")
        x = {"design": d, "st": cells[dc]["type"], "sb": sbel, "sp": dp, "dt": cells[c]["type"], "db": dbel, "dp": p,
             "sx": a[0], "sy": a[1], "dx": z[0], "dy": z[1], "rel": rel, "fo": nsink[b], "viv": nd.get(sinkpin, 0.0),
             "rank": 0}
        x["sc"], x["dc"] = dl.src_cls(x["st"], x["sp"]), dl.dst_cls(x["dt"], x["dp"])
        return x

    out = []
    for k, ln in enumerate((e / "paths_noicap.txt").read_text().splitlines()):
        if k >= K:
            break
        f = ln.split("\t")
        if len(f) < 4:
            continue
        net, logic = 1000 * float(f[1]), 1000 * float(f[2])
        pins = f[3].split()
        sums = defaultdict(float)
        miss = 0
        for p0, p1 in zip(pins, pins[1:]):
            if p0.rsplit("/", 1)[0] == p1.rsplit("/", 1)[0]:
                continue
            x = arc(p1)
            if x is None:
                miss += 1
                for m in MODELS:
                    sums[m] += nd.get(p1, 0.0)
                continue
            for m, fn in MODELS.items():
                sums[m] += fn(x)
        out.append((net, logic, dict(sums), miss))
    return out


def main():
    pat = sys.argv[1]
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    acc = defaultdict(lambda: defaultdict(list))
    worst = defaultdict(lambda: defaultdict(list))
    for r in sorted(n for n in B.os.listdir(B.E) if re.search(pat, n) and (B.S / n / "netlist.json").exists()):
        try:
            P = run_paths(r, K)
        except Exception as ex:
            print(r, "ERR", ex, file=sys.stderr)
            continue
        if not P:
            continue
        d = next(x for x in B.DES if r.startswith(x + "_"))
        for i, (net, logic, sums, miss) in enumerate(P):
            for m, s in sums.items():
                acc[d][m].append((s - net, (s + logic) / (net + logic) - 1))
                if i == 0:
                    worst[d][m].append((s + logic) / (net + logic) - 1)
        print(r, "paths", len(P), file=sys.stderr)
    print(f"Vivado's {K} worst paths per run: route delay error (model - Vivado), mean / mean |.| (ps); path delay error "
          "mean / mean |.| (%); worst path only: path delay error mean / mean |.| (%)")
    print("| design | runs x paths | " + " | ".join(MODELS) + " |")
    print("|---|---|" + "---|" * len(MODELS))
    for d in list(acc) + ["all"]:
        cells = []
        for m in MODELS:
            xs = [v for dd in acc for v in acc[dd][m]] if d == "all" else acc[d][m]
            ws = [v for dd in worst for v in worst[dd][m]] if d == "all" else worst[d][m]
            n = len(xs)
            cells.append(f"{sum(x[0] for x in xs)/n:+.0f}/{sum(abs(x[0]) for x in xs)/n:.0f} ps, "
                         f"{100*sum(x[1] for x in xs)/n:+.1f}/{100*sum(abs(x[1]) for x in xs)/n:.1f} %, "
                         f"worst {100*sum(ws)/len(ws):+.1f}/{100*sum(abs(w) for w in ws)/len(ws):.1f} %")
        n = len(acc[d]["static"]) if d != "all" else sum(len(acc[x]["static"]) for x in acc)
        print(f"| {d} | {n} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
