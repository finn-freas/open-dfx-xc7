"""Table of the SA-refinement study (docs/wip/placement-sa.md) on Vivado's timer with the exact placement import
(flow/exact_src.py + flow/sa_xqueue.sh: our nextpnr placement imported cell for cell, Vivado only routes).
Per design x variant, seed means: Vivado Fmax (all paths and without ICAPE2 paths, from slack.txt), and on the
100 worst non-ICAP paths (paths_noicap.txt): net / logic delay, cells per path, grid hops (prjxray grid units,
cell sites from the exact source's place.txt), net ps per step, hops per step; HPWL of nextpnr's final placement
(prjxray grid units, nets of <= 256 sinks, clock nets excluded, from the routed JSON); slices; nextpnr seconds.
usage: sa_summary.py --designs rv_soc ... --variants A B ... [--seeds 1 2 3] [--md FILE]"""
import argparse, json, re, statistics, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb
import place_compare as pc
import place_shape as ps

OUT = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact_sa")
OTHER = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact")
SRC = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact")


def name(d, v, s):
    return f"{d}_p5_{v}_s{s}_exact"


def vivado(d, v, s, grid, k=100):
    o = OUT / name(d, v, s)
    if not (o / "status.txt").exists() and (OTHER / name(d, v, s) / "status.txt").exists():
        o = OTHER / name(d, v, s)
    st = o / "status.txt"
    if not st.exists() or not st.read_text().startswith("rc 0"):
        return None
    sl = dict(l.split(None, 1) for l in (o / "slack.txt").read_text().splitlines() if " " in l)
    wns, wni = float(sl["wns"]), float(sl["wns_noicap"].split()[0])
    r = {"fmax": 1000.0 / (5 - wns), "fmax_noicap": 1000.0 / (5 - wni)}
    site = {}
    for ln in (SRC / name(d, v, s) / "place.txt").read_text().splitlines():
        m = re.match(r"\{?(.*?)\}?\s+(\S+)/(\S+)$", ln)
        if m:
            site[m.group(1)] = m.group(2)
    rows = []
    for ln in (o / "paths_noicap.txt").read_text().splitlines()[:k]:
        f = ln.split("\t")
        if len(f) < 4:
            continue
        cl = []
        for p in f[3].split():
            c = p.rsplit("/", 1)[0]
            if not cl or cl[-1] != c:
                cl.append(c)
        pos = [grid.get(site.get(c)) for c in cl]
        steps = [(a, b) for a, b in zip(pos, pos[1:]) if a and b]
        rows.append({"net": float(f[1]), "logic": float(f[2]), "cells": len(cl), "steps": max(1, len(cl) - 1),
                     "hops": sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in steps)})
    if rows:
        S = lambda key: sum(x[key] for x in rows)
        r.update({"net": S("net") / len(rows), "logic": S("logic") / len(rows), "cells": S("cells") / len(rows),
                  "hops": S("hops") / len(rows), "ps_step": 1000 * S("net") / S("steps"),
                  "hop_step": S("hops") / S("steps")})
    return r


def hpwl(js, grid):
    m = next(iter(json.loads(js.read_text())["modules"].values()))
    sites = {}
    nets = defaultdict(list)
    clk = set()
    for cn, c in m["cells"].items():
        b = c.get("attributes", {}).get("NEXTPNR_BEL")
        g = grid.get(b.split("/")[0]) if b else None
        for p, bits in c.get("connections", {}).items():
            for bt in bits:
                if isinstance(bt, int):
                    if g:
                        nets[bt].append(g)
                    if c["type"] == "BUFGCTRL" or p in ("CLK", "CK", "C"):
                        clk.add(bt)
    t = 0
    for n, pts in nets.items():
        if n in clk or len(pts) < 2 or len(pts) > 257:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        t += max(xs) - min(xs) + max(ys) - min(ys)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", required=True)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--md")
    a = ap.parse_args()
    grid = pc.site_grid()
    mean = lambda xs: statistics.mean(xs) if xs else None
    f = lambda x, fmt="{:.2f}": "-" if x is None else fmt.format(x)
    out = ["| design | variant | Vivado Fmax per seed (Vivado timer, exact import) | mean | excl. ICAP mean | "
           "net ns | logic ns | cells | hops | hops/step | net ps/step | HPWL | slices | nextpnr s |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    data = {}
    for d in a.designs:
        base = None
        for v in a.variants:
            acc = defaultdict(list)
            per = []
            for s in a.seeds:
                r = vivado(d, v, s, grid)
                per.append(f(r["fmax"]) if r else "-")
                if r:
                    for k, x in r.items():
                        acc[k].append(x)
                run = pb.run_dir(d, 5, v, s)
                js = run / f"{ps.TOPS[d]}_routed.json"
                if js.exists():
                    acc["hpwl"].append(hpwl(js, grid))
                    acc["slices"].append(ps.shape(js, grid)["slices"])
                st = run / "status.json"
                if st.exists():
                    acc["secs"].append(json.loads(st.read_text()).get("pnr", {}).get("seconds") or 0)
            mm = {k: mean(x) for k, x in acc.items()}
            data[f"{d}|{v}"] = {"per_seed": {k: x for k, x in acc.items()}, "mean": mm}
            out.append(f"| {d} | {v} | {' / '.join(per)} | {f(mm.get('fmax'))} | {f(mm.get('fmax_noicap'))} | "
                       f"{f(mm.get('net'))} | {f(mm.get('logic'))} | {f(mm.get('cells'), '{:.1f}')} | "
                       f"{f(mm.get('hops'), '{:.1f}')} | {f(mm.get('hop_step'))} | {f(mm.get('ps_step'), '{:.0f}')} | "
                       f"{f(mm.get('hpwl'), '{:.0f}')} | {f(mm.get('slices'), '{:.0f}')} | {f(mm.get('secs'), '{:.0f}')} |")
    md = "\n".join(out) + "\n"
    if a.md:
        Path(a.md).write_text(md)
        Path(a.md).with_suffix(".json").write_text(json.dumps(data, indent=1) + "\n")
    print(md)


if __name__ == "__main__":
    main()
