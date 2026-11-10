"""One row per Vivado dump of the dpl study: Vivado's timer (WNS, Fmax, Fmax without the ICAP endpoint) and the
packing metrics of flow/dpl_metrics.py.

  dpl_summary.py NAME...      (names under the dpl_xtime dump root; globs allowed)
"""
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dpl_metrics

ROOT = Path(__file__).resolve().parent.parent
DUMP = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/" + os.environ.get("DPL_XTIME", "dpl_xtime2"))
XSRC = ROOT / "build" / "qor" / "dpl" / "xsrc"
CACHE = ROOT / "build" / "qor" / "dpl" / "metrics"


def period(name):
    return 10.0 if name.startswith(("eth", "ddr")) else 5.0


def row(name):
    d = DUMP / name
    st = d / "status.txt"
    if not st.exists():
        return None
    if not st.read_text().startswith("rc 0"):
        return {"name": name, "error": st.read_text().strip().replace("\n", " ")[:120]}
    design = name.split("_p")[0]
    free = next(XSRC.glob(f"{design}_p*_free"))
    netlist = Path((free / "netlist.txt").read_text().strip())
    cache = CACHE / f"{name}.json"
    if cache.exists() and cache.stat().st_mtime > st.stat().st_mtime:
        m = json.loads(cache.read_text())
    else:
        m = dpl_metrics.metrics(d, netlist)
        CACHE.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(m, indent=1) + "\n")
    p = period(name)
    r = {"name": name, "wns": m.get("wns"), "fmax": round(1000 / (p - m["wns"]), 2) if m.get("wns") is not None else None}
    wp = d / "worst_paths.txt"
    if wp.exists():
        sl = [float(x.split()[0]) for x in wp.read_text().splitlines() if len(x.split()) == 3 and "u_icap" not in x]
        if sl:
            r["fmax_noicap"] = round(1000 / (p - min(sl)), 2)
    pm = d / "place_missed.txt"
    if pm.exists():
        r["imposed"] = int(pm.read_text().split("\n", 1)[0].split()[1])
    for k in ("util_slices", "slices", "lut_per_slice", "ff_per_slice", "lutff_direct_pct", "hpwl_total", "signal_pips",
              "crit_net_hpwl_mean", "crit_hop_mean", "crit_net_delay_mean", "ff_slice_cs_pairs", "hard_dist_mean",
              "vivado_place_s", "vivado_route_s"):
        r[k] = m.get(k)
    r["carry_s_in_slice"] = m.get("carry", {}).get("s_lut_in_carry_slice_pct")
    return r


def main():
    names = []
    for pat in sys.argv[1:]:
        names += sorted(n.name for n in DUMP.iterdir() if fnmatch.fnmatch(n.name, pat)) if any(ch in pat for ch in "*?[") else [pat]
    rows = [r for r in (row(n) for n in names) if r]
    keys = ["name", "wns", "fmax", "fmax_noicap", "imposed", "util_slices", "lut_per_slice", "ff_per_slice", "lutff_direct_pct",
            "carry_s_in_slice", "hpwl_total", "signal_pips", "crit_net_hpwl_mean", "crit_hop_mean", "crit_net_delay_mean",
            "ff_slice_cs_pairs", "hard_dist_mean", "vivado_place_s", "vivado_route_s"]
    print("| " + " | ".join(keys) + " |")
    print("|" + "---|" * len(keys))
    for r in rows:
        if "error" in r:
            print(f"| {r['name']} | error: {r['error']} |")
            continue
        print("| " + " | ".join("-" if r.get(k) is None else str(r.get(k)) for k in keys) + " |")


if __name__ == "__main__":
    main()
