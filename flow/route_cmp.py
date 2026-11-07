import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route_xtime

CONFIG = {
    "top_paths": 50,
}


def net_delays(name):
    d = {}
    f = route_xtime.CONFIG["win_out"] / name / "net_delays.txt"
    if not f.exists():
        return None
    for ln in f.read_text().splitlines():
        p, _, v = ln.partition("\t")
        try:
            d[p] = float(v)
        except ValueError:
            pass
    return d


def paths(name):
    f = route_xtime.CONFIG["win_out"] / name / "paths_noicap.txt"
    if not f.exists():
        return None
    out = []
    for ln in f.read_text().splitlines():
        s, nd, ld, pins = ln.split("\t")
        out.append((float(s), float(nd), float(ld), pins.split()))
    return out


def path_net_delay(pins, nd):
    total, missing = 0.0, 0
    for p in pins:
        if p in nd:
            total += nd[p]
    for p in pins[1:]:
        if p not in nd and not p.endswith("/O") and not p.endswith("/Q"):
            missing += 1
    return total, missing


def compare(a, b):
    """Paths of run a; their net delay under a's routing and under b's routing (same pins)."""
    pa, na, nb = paths(a), net_delays(a), net_delays(b)
    if not pa or na is None or nb is None:
        return None
    rows = []
    for s, ndly, ldly, pins in pa[:CONFIG["top_paths"]]:
        da, _ = path_net_delay(pins, na)
        db, _ = path_net_delay(pins, nb)
        rows.append((da, db))
    return {"paths": len(rows), "net_delay_own_mean": statistics.mean(r[0] for r in rows),
            "net_delay_other_mean": statistics.mean(r[1] for r in rows),
            "delta_mean": statistics.mean(r[1] - r[0] for r in rows)}


def main():
    ap = argparse.ArgumentParser(description="Per-path routing delay on identical placement and LUT pins: Vivado's "
                                             "worst non-ICAP paths with Vivado's routes against the same pins' arcs "
                                             "with nextpnr's routes (Vivado timer, slow max), and the converse")
    ap.add_argument("pairs", nargs="+", help="NPR_NAME (compared with NPR_NAME_vr)")
    a = ap.parse_args()
    out = {}
    for n in a.pairs:
        out[n] = {"vivado_paths": compare(n + "_vr", n), "nextpnr_paths": compare(n, n + "_vr")}
        print(n, json.dumps(out[n]))


if __name__ == "__main__":
    main()
