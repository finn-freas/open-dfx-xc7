"""SA study: the SA's arc-delay model against Vivado's routed net delay on the worst non-ICAP paths of an exact-import
run (Vivado timer). For each path step (driver pin -> load pin) the model delay (same site: 0 dedicated / 665 LUT input
/ 866 other; same tile 682; else 489 + 1.391 * delay matrix, as sa_refine.cc) is compared with Vivado's SLOW_MAX net
delay of that load pin (net_delays.txt).
usage: sa_arcmodel.py NAME [-k 50]"""
import argparse, re, statistics, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path.home() / "open-dfx-xc7" / "flow"))
import xroute_predict as xp

V = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("-k", type=int, default=50)
    a = ap.parse_args()
    out = V / "build/exact_sa" / a.name
    if not (out / "status.txt").exists():
        out = V / "build/exact" / a.name
    src = V / "designs/exact" / a.name
    m = xp.load_matrix(Path.home() / "open-dfx-xc7/build/xroute/predict/matrix_cal.txt")
    sxy = xp.site_xy()
    place = {}
    for ln in (src / "place.txt").read_text().splitlines():
        mm = re.match(r"\{?(.*?)\}?\s+(\S+)/(\S+)$", ln)
        if mm:
            place[mm.group(1)] = (mm.group(2), mm.group(3))
    nd = {}
    for ln in (out / "net_delays.txt").read_text().splitlines():
        f = ln.split("\t")
        if len(f) == 2 and f[1]:
            nd[f[0]] = float(f[1])
    errs, kinds, tot_m, tot_v, big = [], Counter(), [], [], []
    bycls = {}
    kerr = {}
    for ln in (out / "paths_noicap.txt").read_text().splitlines()[:a.k]:
        f = ln.split("\t")
        pins = f[3].split()
        pm, pv = 0, 0
        for drv, ld in zip(pins, pins[1:]):
            dc, lc = drv.rsplit("/", 1)[0], ld.rsplit("/", 1)[0]
            if dc == lc:
                continue
            if ld not in nd or dc not in place or lc not in place:
                continue
            (ds, db), (ls, lb) = place[dc], place[lc]
            lpin = ld.rsplit("/", 1)[1]
            if ds == ls:
                if re.match(r"I[0-5]$", lpin) or re.match(r"[A-D][1-6]$", lpin):
                    mdl, k = 665, "site_lut"
                elif lpin in ("D", "S", "DI", "CI") or lpin.startswith(("S[", "DI[")):
                    mdl, k = 0, "site_ded"
                else:
                    mdl, k = 866, "site_other"
            elif sxy.get(ds) == sxy.get(ls):
                mdl, k = 682, "tile"
            else:
                a_, b_ = sxy.get(ds), sxy.get(ls)
                if a_ is None or b_ is None:
                    continue
                mdl, k = 489 + 1.391 * xp.lookup(m, b_[0] - a_[0], b_[1] - a_[1]), "inter"
            v = nd[ld]
            errs.append(v - mdl)
            kinds[k] += 1
            kerr.setdefault(k, []).append(v - mdl)
            pm += mdl
            pv += v
            big.append((v - mdl, k, drv, ld, ds, ls))
            dcl = "RAM" if db.startswith("RAMB") else "DSP" if db.startswith("DSP") else "CARRY" if "CARRY" in db else "FF" if "FF" in db else "LUT" if "LUT" in db else db
            lcl = "LUTin" if re.match(r"I[0-5]$", lpin) else lpin if lpin in ("CE", "R", "S", "D", "CI") else "RAM" if lb.startswith("RAMB") else "DSP" if lb.startswith("DSP") else "other"
            bycls.setdefault((dcl, lcl, k == "inter"), []).append(v - mdl)
        tot_m.append(pm)
        tot_v.append(pv)
    print(f"{a.name}: {len(errs)} arcs on {a.k} paths; Vivado - model per arc mean {statistics.mean(errs):.0f} ps, "
          f"mean abs {statistics.mean(map(abs, errs)):.0f}; per path model {statistics.mean(tot_m):.0f} ps vs Vivado "
          f"{statistics.mean(tot_v):.0f} ps; kinds {dict(kinds)}")
    print("  by kind: " + ", ".join(f"{k} {statistics.mean(e):+.0f} (n {len(e)})" for k, e in kerr.items()))
    for key in sorted(bycls, key=lambda q: -len(bycls[q])):
        e = bycls[key]
        if len(e) >= 5:
            print(f"  class {key}: n {len(e)}, Vivado - model mean {statistics.mean(e):+.0f} ps")
    seen = set()
    for e in sorted(big, reverse=True):
        if (e[2], e[3]) in seen:
            continue
        seen.add((e[2], e[3]))
        print(f"  +{e[0]:.0f} ps {e[1]} {e[2]} -> {e[3]} ({e[4]} -> {e[5]})")
        if len(seen) >= 3:
            break


if __name__ == "__main__":
    main()
