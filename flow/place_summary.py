"""One row per design x variant of the global-placement study: Vivado-timed Fmax per seed (Vivado routes our
imposed placement, flow/place_vivado.sh), nextpnr's own Fmax (nextpnr timer), HPWL after legalisation, slices,
the logic footprint (sd_x / sd_y), the mean hops of the 100 worst Vivado paths (flow/place_diag.py on the run's
dump) and nextpnr's run time. Seed means.
usage: place_summary.py --designs rv_soc bram --variants pl_base pl11_anc20ipw_stub [--md out.md]"""
import argparse, json, statistics, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb
import place_shape as ps
import place_compare as pc

R = Path.home() / "open-dfx-xc7"
DIAG = R / "build/qor/place/diag"


EXACT = pb.CONFIG["vivado_root"] / "exact"


EXACT_ALT = pb.CONFIG["vivado_root"] / "exact_sa"


def exact_dir(name):
    """build/exact, or build/exact_sa (the same import run by the Vivado-strategy study) when only that has it."""
    if not (EXACT / name / "status.txt").exists() and (EXACT_ALT / name / "status.txt").exists():
        return EXACT_ALT / name
    return EXACT / name


def exact_result(name, period):
    """Vivado timer on the exact import (flow/exact_src.py, vivado/build_rte.tcl fixed mode): WNS from slack.txt."""
    st = exact_dir(name) / "status.txt"
    if not st.exists():
        return None
    if not st.read_text().startswith("rc 0"):
        return {"error": st.read_text().strip()}
    kv = dict(l.split(None, 1) for l in (exact_dir(name) / "slack.txt").read_text().splitlines() if " " in l)
    try:
        wns = float(kv["wns"].split()[0])
    except (KeyError, ValueError):
        return {"error": "no wns"}
    return {"wns": wns, "fmax": round(1000.0 / (period - wns), 2)}


def hops(name):
    j = DIAG / f"{name}.json"
    dump = exact_dir(name) if name.endswith("_exact") else pb.CONFIG["vivado_root"] / pb.CONFIG["vivado_tag"] / name
    if name.endswith("_exact"):
        j = DIAG / "_none_"
    if not j.exists() and (dump / "cells.txt").exists() and (dump / "paths.txt").exists():
        subprocess.run([sys.executable, str(R / "flow/place_diag.py"), "--ours", name], capture_output=True)
    if j.exists():
        return json.loads(j.read_text())["critical_paths"]["our_paths_in_ours"]["hops"].get("mean")
    if not (dump / "cells.txt").exists() or not (dump / "paths.txt").exists():
        return None
    grid = pc.site_grid()
    cells = pc.read_cells(dump / "cells.txt")
    pos = {n: grid[c["site"]] for n, c in cells.items() if c["site"] in grid}
    hs = []
    for ln in (dump / "paths.txt").read_text().splitlines()[:100]:
        f = ln.split("\t")
        if len(f) < 7:
            continue
        pts = [pos[c] for c in f[6].split() if c in pos]
        if len(pts) >= 2:
            hs.append(sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:])))
    return statistics.mean(hs) if hs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", required=True)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--md")
    ap.add_argument("--exact", action="store_true", help="Vivado timer on the exact import (build/exact) instead of placed mode")
    a = ap.parse_args()
    grid = pc.site_grid()
    out = ["| design | variant | Vivado Fmax per seed, MHz (Vivado timer) | mean | nextpnr Fmax mean (nextpnr timer) | "
           "HPWL after legalisation | slices | sd_x / sd_y | worst-100 hops (Vivado paths) | nextpnr s |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    mean = lambda xs: statistics.mean(xs) if xs else None
    f = lambda x, fmt="{:.2f}": "-" if x is None else fmt.format(x)
    for d in a.designs:
        for v in a.variants:
            vf, nf, hp, sl, sx, sy, hz, secs = [], [], [], [], [], [], [], []
            per = []
            for s in (1, 2, 3):
                name = pb.xname(d, 5, v, s)
                if a.exact:
                    name = name.replace("_placed", "_exact")
                r = exact_result(name, 5) if a.exact else pb.vivado_result(name, 5)
                if r and "fmax" in r:
                    vf.append(r["fmax"]); per.append(f"{r['fmax']:.2f}")
                else:
                    per.append("-")
                run = pb.run_dir(d, 5, v, s)
                js = run / f"{ps.TOPS[d]}_routed.json"
                if js.exists():
                    sh = ps.shape(js, grid)
                    sl.append(sh["slices"]); sx.append(sh["sd_x"]); sy.append(sh["sd_y"])
                    h, fm = ps.hpwl_log(run / "nextpnr.log")
                    if h is not None:
                        hp.append(h)
                    if fm is not None:
                        nf.append(fm)
                st = run / "status.json"
                if st.exists():
                    secs.append(json.loads(st.read_text()).get("pnr", {}).get("seconds") or 0)
                hh = hops(name)
                if hh is not None:
                    hz.append(hh)
            if not (vf or nf):
                continue
            out.append(f"| {d} | {v} | {' / '.join(per)} | {f(mean(vf))} | {f(mean(nf))} | {f(mean(hp), '{:.0f}')} | "
                       f"{f(mean(sl), '{:.0f}')} | {f(mean(sx), '{:.1f}')} / {f(mean(sy), '{:.1f}')} | "
                       f"{f(mean(hz), '{:.1f}')}{'' if len(hz) in (0, 3) else f' (n={len(hz)})'} | {f(mean(secs), '{:.0f}')} |")
    md = "\n".join(out) + "\n"
    if a.md:
        Path(a.md).write_text(md)
    print(md)


if __name__ == "__main__":
    main()
