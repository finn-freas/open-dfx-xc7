"""Legalisation cost of the static placer, from nextpnr's log: HPWL before and after the logic legalisation step (the
last "HPWL after legalise" line), seed means; plus nextpnr's final Fmax (nextpnr timer) and run time.
usage: legal_cost.py --designs rv_soc bram --variants A B [--seeds 1 2 3]"""
import argparse, json, re, statistics
from pathlib import Path

RUNS = Path.home() / "open-dfx-xc7/build/qor/oxc7"


def one(run):
    t = (run / "nextpnr.log").read_text(errors="replace") if (run / "nextpnr.log").exists() else ""
    m = re.findall(r"HPWL after legalise: ([0-9.]+) \(delta: ([-0-9.]+)\)", t)
    if not m:
        return None
    post, delta = float(m[-1][0]), float(m[-1][1])
    fm = re.findall(r"Max frequency for clock\s+'[^']+': ([0-9.]+) MHz", t)
    ring = re.findall(r"Ring legaliser placed (\d+) cells", t)
    st = json.loads((run / "status.json").read_text()) if (run / "status.json").exists() else {}
    return {"pre": post - delta, "post": post, "pct": 100.0 * delta / (post - delta), "fmax": float(fm[-1]) if fm else None,
            "ring": int(ring[-1]) if ring else None, "s": st.get("pnr", {}).get("seconds")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", required=True)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    a = ap.parse_args()
    print("| design | variant | HPWL before legalisation | after | increase | ring-placed cells | nextpnr Fmax (nextpnr timer) | nextpnr s | seeds |")
    print("|---|---|---|---|---|---|---|---|---|")
    for d in a.designs:
        for v in a.variants:
            rows = [r for s in a.seeds for r in [one(RUNS / v / f"{d}_p5" / f"s{s}")] if r]
            if not rows:
                continue
            m = lambda k: statistics.mean(r[k] for r in rows if r[k] is not None) if any(r[k] is not None for r in rows) else float("nan")
            print(f"| {d} | {v} | {m('pre'):.0f} | {m('post'):.0f} | {m('pct'):+.1f} % | {m('ring'):.0f} | {m('fmax'):.2f} | {m('s'):.0f} | {len(rows)} |")


if __name__ == "__main__":
    main()
