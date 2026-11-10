"""Table for docs/dreamplace-eval.md: per design and variant, Vivado Fmax on the exact nextpnr implementation
(flow/exact_src.py, Vivado routes; Vivado timer), nextpnr Fmax (nextpnr timer), nextpnr HPWL after legalisation,
routed wires, and runtimes (DREAMPlaceFPGA GP, nextpnr total). Vivado's own placement (vref) as reference.
usage: python3 flow/dpf_summary.py [--variants ...] [--designs ...]
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb

EXACT = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact")
GP = pb.ROOT / "build" / "dpf" / "gp"


def viv(name, period=5.0, key="wns"):
    s = EXACT / name / "slack.txt"
    if not s.exists():
        return None
    kv = dict(l.split(None, 1) for l in s.read_text().splitlines() if " " in l)
    try:
        return round(1000.0 / (period - float(kv[key])), 2)
    except (KeyError, ValueError):
        return None


def nlog(design, v, s):
    d = pb.run_dir(design, 5, v, s)
    st = json.loads((d / "status.json").read_text()) if (d / "status.json").exists() else {}
    t = (d / "nextpnr.log").read_text(errors="replace") if (d / "nextpnr.log").exists() else ""
    leg = re.findall(r"HPWL after legalise: ([0-9.]+)", t)
    it = re.findall(r"iter=(\d+) wires=(\d+) overused", t)
    fm = re.findall(r"Max frequency for clock\s+'[^']*': ([0-9.]+) MHz", t)
    return {"fmax": float(fm[-1]) if fm else None, "hpwl": float(leg[-1]) if leg else None,
            "wires": int(it[-1][1]) if it else None, "secs": st.get("pnr", {}).get("seconds")}


def gp_secs(design, v, s):
    v = {"pl_dpf_warm": "pl_dpf_wl", "pl_dpf_td_warm": "pl_dpf_td"}.get(v, v)
    f = GP / v / design / f"s{s}" / "run.json"
    return json.loads(f.read_text()).get("seconds") if f.exists() else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def fmt(x, f="{:.2f}"):
    return "-" if x is None else f.format(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", default=["rv_soc", "bram", "rv_big"])
    ap.add_argument("--variants", nargs="+", default=["pl14_off_stub", "pl_dpf_wl", "pl_dpf_warm"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    a = ap.parse_args()
    rows = ["| design | placer | Vivado Fmax per seed (Vivado timer, exact import) | mean | mean excl. ICAP | nextpnr Fmax mean "
            "(nextpnr timer) | HPWL after legalisation (nextpnr metric) | routed wires | GP s (DREAMPlace, CPU) | "
            "nextpnr s |", "|---|---|---|---|---|---|---|---|---|---|"]
    out = {}
    for d in a.designs:
        ref = viv(f"{d}_p5_vref_exact")
        refn = viv(f"{d}_p5_vref_exact", key="wns_noicap")
        for v in a.variants:
            vf = [viv(f"{d}_p5_{v}_s{s}_exact") for s in a.seeds]
            vn = [viv(f"{d}_p5_{v}_s{s}_exact", key="wns_noicap") for s in a.seeds]
            nl = [nlog(d, v, s) for s in a.seeds]
            g = [gp_secs(d, v, s) for s in a.seeds] if v.startswith("pl_dpf") else [None]
            r = {"vivado": vf, "vivado_mean": mean(vf), "vivado_noicap_mean": mean(vn), "nextpnr_fmax": mean([x["fmax"] for x in nl]),
                 "hpwl": mean([x["hpwl"] for x in nl]), "wires": mean([x["wires"] for x in nl]),
                 "gp_s": mean(g), "nextpnr_s": mean([x["secs"] for x in nl])}
            out[f"{d}|{v}"] = r
            rows.append(f"| {d} | {v} | {' / '.join(fmt(x) for x in vf)} | {fmt(r['vivado_mean'])} | {fmt(r['vivado_noicap_mean'])} | "
                        f"{fmt(r['nextpnr_fmax'])} | {fmt(r['hpwl'], '{:.0f}')} | {fmt(r['wires'], '{:.0f}')} | "
                        f"{fmt(r['gp_s'], '{:.0f}')} | {fmt(r['nextpnr_s'], '{:.0f}')} |")
        out[f"{d}|vref"] = {"vivado": ref, "vivado_noicap": refn}
        rows.append(f"| {d} | Vivado places the same netlist (vref, 1 run) | {fmt(ref)} | {fmt(ref)} | {fmt(refn)} | - | - | "
                    f"- | - | - |")
    print("\n".join(rows))
    (pb.ROOT / "build" / "dpf" / "summary.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
