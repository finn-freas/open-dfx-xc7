"""Table for docs/vpr-eval.md: base placer (pl14_off_stub) against VPR's placement (vpr_imp), per design and seed.
Fmax: Vivado's timer on the exact import (flow/exact_src.py + vivado/build_rte.tcl, Vivado routes only), from
slack.txt (wns, wns_noicap). HPWL: sum over non-clock nets of the bounding box of the cells' tile coordinates in the
routed nextpnr JSON (same metric for both). Slices: distinct SLICE sites. Hops etc: flow/place_paths.py on the
exact runs (flow/exact_dump.py). Fidelity: share of VPR's imported cells that ended on VPR's bel.
usage: vpr_report.py [--designs ...] [--seeds ...]"""
import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb
import qor_bench
import place_paths
import place_compare as pc

ROOT = qor_bench.ROOT
EXACT = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact")
EXSRC = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact")
DUMPS = ROOT / "build" / "vpr" / "dumps"
VARIANTS = {"pl14_off_stub": "base (nextpnr static, stub)", "vpr_imp": "VPR (F4PGA options) + nextpnr rest",
            "vpr_imp_hi": "VPR --inner_num 5 + nextpnr rest"}


def vdir(d, v, s):
    tag = v[len("vpr_imp_"):] if v.startswith("vpr_imp_") else ""
    return ROOT / "build" / "vpr" / d / (f"{tag}_s{s}" if tag else f"s{s}")


def name(d, v, s):
    return f"{d}_p5_{v}_s{s}_exact"


def vivado(n):
    st = EXACT / n / "status.txt"
    if not st.exists() or not st.read_text().startswith("rc 0"):
        return None
    kv = {}
    for ln in (EXACT / n / "slack.txt").read_text().splitlines():
        p = ln.split()
        if len(p) == 2:
            try:
                kv[p[0]] = float(p[1])
            except ValueError:
                pass
    return {"fmax": 1000 / (5 - kv["wns"]), "fmax_noicap": 1000 / (5 - kv["wns_noicap"]), "wns": kv["wns"]}


GRID = pc.site_grid()


def tile_xy(bel):
    return GRID.get(bel.split("/")[0]) if bel else None


def placement_metrics(routed):
    j = json.loads(Path(routed).read_text())
    m = j["modules"][next(iter(j["modules"]))]
    pos, slices = {}, set()
    for n, c in m["cells"].items():
        b = c["attributes"].get("NEXTPNR_BEL", "")
        xy = tile_xy(b)
        if xy:
            pos[n] = xy
        if b.startswith("SLICE_"):
            slices.add(b.split("/")[0])
    nets = {}
    clk = set()
    for n, c in m["cells"].items():
        for p, bits in c["connections"].items():
            for b in bits:
                if isinstance(b, int):
                    nets.setdefault(b, []).append(n)
                    if c["type"] in ("BUFGCTRL", "BUFG") and c["port_directions"].get(p) == "output":
                        clk.add(b)
    hpwl = 0
    for b, cs in nets.items():
        if b in clk:
            continue
        pts = [pos[c] for c in set(cs) if c in pos]
        if len(pts) > 1:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            hpwl += max(xs) - min(xs) + max(ys) - min(ys)
    return {"hpwl": hpwl, "slices": len(slices), "bels": {n: c["attributes"].get("NEXTPNR_BEL") for n, c in m["cells"].items()}}


def fidelity(d, v, s, bels):
    imp = vdir(d, v, s) / "import_sites.txt"
    rows = [ln.split("\t") for ln in imp.read_text().splitlines()]
    hit = sum(1 for c, b in rows if bels.get(c) == b)
    return hit / max(1, len(rows))


def hops(d, v, s):
    n = name(d, v, s)
    if not (EXACT / n / "paths_noicap.txt").exists():
        return None
    out = DUMPS / n
    subprocess.run([sys.executable, str(ROOT / "flow" / "exact_dump.py"), str(EXSRC / n), str(EXACT / n), str(out)],
                   check=True, capture_output=True)
    return place_paths.analyse(out, 100, GRID)


def seconds(d, v, s):
    st = json.loads((pb.run_dir(d, 5, v, s) / "status.json").read_text())
    t = st["pnr"]["seconds"]
    w = pb.run_dir(d, 5, v, s) / "npwait.log"
    if w.exists():
        t -= sum(float(x.split()[1]) for x in w.read_text().splitlines() if x.startswith("waited"))
    if v.startswith("vpr_imp"):
        vd = ROOT / "build" / "vpr" / d
        t_v = float((vdir(d, v, s) / "place.time").read_text().split()[0])
        t_p = float((vd / "pack.time").read_text().split()[0])
        return t, t_v, t_p
    return t, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", default=["rv_soc", "bram", "rv_big"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    a = ap.parse_args()
    mean = lambda xs: statistics.mean(xs) if xs else None
    f2 = lambda x, f="{:.2f}": "-" if x is None else f.format(x)
    print("| design | placer | Vivado Fmax per seed (exact import, Vivado timer) | mean | mean, ICAP excluded | HPWL (tile units) | "
          "slices | worst-100 hops | net ns (100 worst) | net ps / step | LUT->FF in one slice | VPR cells kept on VPR's bel | "
          "s: nextpnr / VPR place / VPR pack |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    data = {}
    for d in a.designs:
        for v in a.variants:
            label = VARIANTS[v]
            fm, fn, hp, sl, hs, nt, nps, lf, fid, ts = [], [], [], [], [], [], [], [], [], []
            for s in a.seeds:
                r = vivado(name(d, v, s))
                fm.append(r["fmax"] if r else None)
                if r:
                    fn.append(r["fmax_noicap"])
                rd = pb.run_dir(d, 5, v, s)
                top = qor_bench.CONFIG["designs"][d]["top"]
                if (rd / f"{top}_routed.json").exists():
                    pm = placement_metrics(rd / f"{top}_routed.json")
                    hp.append(pm["hpwl"])
                    sl.append(pm["slices"])
                    if v.startswith("vpr_imp"):
                        fid.append(fidelity(d, v, s, pm["bels"]))
                    ts.append(seconds(d, v, s))
                h = hops(d, v, s)
                if h:
                    hs.append(h["hops"])
                    nt.append(h["net"])
                    nps.append(1000 * h["net_per_step"])
                    lf.append(100 * h["lutff_same"])
            data[(d, v)] = {"fmax": fm, "fmax_noicap": fn, "hpwl": hp, "slices": sl, "hops": hs, "fid": fid, "t": ts}
            per = " / ".join(f2(x) for x in fm)
            tt = (f"{mean([t[0] for t in ts]):.0f}" + (f" / {mean([t[1] for t in ts]):.0f} / {ts[0][2]:.0f}"
                                                         if ts[0][1] else "")) if ts else "-"
            print(f"| {d} | {label} | {per} | {f2(mean([x for x in fm if x]))} | {f2(mean(fn))} | {f2(mean(hp), '{:.0f}')} | "
                  f"{f2(mean(sl), '{:.0f}')} | {f2(mean(hs), '{:.1f}')} | {f2(mean(nt))} | {f2(mean(nps), '{:.0f}')} | "
                  f"{f2(mean(lf), '{:.0f}')} % | {f2(mean(fid) * 100 if fid else None, '{:.0f}')} % | {tt} |")
    (ROOT / "build" / "vpr" / "report.json").write_text(json.dumps({f"{k[0]}|{k[1]}": v for k, v in data.items()},
                                                                   indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
