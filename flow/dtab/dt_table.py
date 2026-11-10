"""Exact-import results of the delay-table variants against the control, same seed (Vivado timer: wns_noicap of
slack.txt, Fmax = 1000 / (period - WNS)). usage: dt_table.py [--control ua_dxy] [--seeds 1,2,3] VARIANT..."""
import argparse, math
from pathlib import Path

X = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact")
DES = ("rv_soc", "bram", "rv_big", "rv_mul")
VREF = {"rv_soc": 148.8, "bram": 164.1, "rv_big": 110.9, "rv_mul": 159.2}


def fmax(d, v, s):
    vv = f"{v}_dq" if d == "rv_mul" else v
    f = X / f"{d}_p5_{vv}_s{s}_exact" / "slack.txt"
    if not f.exists():
        return None
    kv = dict(l.split(None, 1) for l in f.read_text().splitlines() if " " in l)
    try:
        return 1000.0 / (5.0 - float(kv["wns_noicap"]))
    except (KeyError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="+")
    ap.add_argument("--control", default="ua_dxy")
    ap.add_argument("--seeds", default="1,2,3")
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    print(f"Vivado timer, exact import; Fmax MHz per seed {seeds}; % = mean over seeds of (variant / {a.control} same seed - 1)")
    print("| variant | " + " | ".join(DES) + " | mean % (t) | runs | share of Vivado's own placement |")
    print("|---|" + "---|" * (len(DES) + 3))
    c = {(d, s): fmax(d, a.control, s) for d in DES for s in seeds}
    print(f"| {a.control} | " + " | ".join(" / ".join("-" if c[(d, s)] is None else f"{c[(d, s)]:.1f}" for s in seeds) for d in DES)
          + " | | | " + "/".join(f"{100 * sum(x for x in (c[(d, s)] for s in seeds) if x) / max(1, sum(1 for s in seeds if c[(d, s)])) / VREF[d]:.0f}" for d in DES) + " % |")
    for v in a.variants:
        cells, allp, share = [], [], []
        for d in DES:
            fs = [fmax(d, v, s) for s in seeds]
            ps = [100 * (f / c[(d, s)] - 1) for f, s in zip(fs, seeds) if f and c[(d, s)]]
            allp += ps
            ok = [f for f in fs if f]
            share.append(f"{100 * sum(ok) / len(ok) / VREF[d]:.0f}" if ok else "-")
            cells.append(" / ".join("-" if f is None else f"{f:.1f}" for f in fs) + (f" ({sum(ps) / len(ps):+.1f} %)" if ps else ""))
        n = len(allp)
        if n > 1:
            m = sum(allp) / n
            sd = math.sqrt(sum((p - m) ** 2 for p in allp) / (n - 1))
            t = m / (sd / math.sqrt(n)) if sd else float("nan")
            tail = f"{m:+.1f} ({t:.1f})"
        else:
            tail = "-"
        print(f"| {v} | " + " | ".join(cells) + f" | {tail} | {n} | {'/'.join(share)} % |")


if __name__ == "__main__":
    main()
