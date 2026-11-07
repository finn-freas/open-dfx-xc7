import argparse
import json
from pathlib import Path

import qor_bench

CONFIG = {
    "designs": ["rv_soc", "rv_mul", "rv_big", "bram"],
    "period": 5.0,
    "variants": [
        ("base", "nightly nextpnr, blind timer (reference only)"),
        ("tmg", "hardblock-timing (honest timer), heap placer, seed 1"),
        ("tmg_s3", "same, seeds 1-3"),
        ("fix_tmg_s8", "gapfix + hardblock-timing, seeds 1-8"),
        ("tmg_critexp4", "--placer-heap-critexp 4"),
        ("fix_tmg_ce4_s8", "--placer-heap-critexp 4, seeds 1-8"),
        ("tmg_tw20", "--placer-heap-timingweight 20"),
        ("tmg_tw40", "--placer-heap-timingweight 40"),
        ("tmg_topt", "-o timing-opt=4,30"),
        ("tmg_altw", "--router2-alt-weights"),
        ("tmg_slack", "--router2-slack-order"),
        ("tmg_bbbudget", "--router2-bb-budget"),
        ("tmg_ripup", "--tmg-ripup"),
        ("tmg_parref", "--parallel-refine"),
        ("fix_tmg_ctforce", "-o clock-tree=force"),
        ("fix_tmg_dmoff", "-o delay-matrix=off"),
        ("fix_tmg_bramforce", "-o bram-place=force"),
        ("fix_heap_bf_s8", "-o bram-place=force, seeds 1-8"),
        ("tmg_sa", "--placer sa"),
        ("tmg_static", "--placer static"),
        ("fix_static", "gapfix + hardblock-timing + --placer static"),
        ("fix_static_bf", "--placer static -o bram-place=force"),
        ("fix_static_s8", "--placer static, seeds 1-8"),
        ("tmg_dff", "yosys -dff"),
        ("fix_tmg_wm5", "yosys -widemux 5 (gapfix nextpnr)"),
        ("fix_tmg_noicap", "ICAP setup as 2-cycle (nextpnr's non-ICAP Fmax)"),
        ("fix_tmg_noicap_s8", "same, seeds 1-8"),
        ("fix_static_noicap", "--placer static, ICAP 2-cycle"),
        ("fix_static_noicap_s8", "--placer static, ICAP 2-cycle, seeds 1-8"),
    ],
}


def cell(r):
    if r is None:
        return "not run"
    fm = sorted(x["result"]["fmax"] for x in r["runs"] if x.get("result", {}).get("fmax"))
    if not fm:
        return "fail (" + (r["runs"][0]["pnr"].get("error", "")[:40] or "no result") + ")"
    secs = sum(x["pnr"]["seconds"] for x in r["runs"])
    if len(r["runs"]) == 1:
        return f"{fm[0]:.2f} ({secs:.0f} s)"
    med = fm[len(fm) // 2] if len(fm) % 2 else (fm[len(fm) // 2 - 1] + fm[len(fm) // 2]) / 2
    return f"best {fm[-1]:.2f} / median {med:.2f} / worst {fm[0]:.2f} ({secs:.0f} s)"


def main():
    ap = argparse.ArgumentParser(description="experiment table at one period, nextpnr timer, from the qor_bench cache")
    ap.add_argument("--doc-tag")
    a = ap.parse_args()
    p = CONFIG["period"]
    lines = [f"Experiments at {p:g} ns, nextpnr Fmax in MHz (nextpnr timer; all but `base` with hardblock-timing), "
             "nextpnr seconds summed over seeds. Source: build/qor/oxc7/<variant>/<design>_p5/s<seed>/status.json.", "",
             "| variant | what | " + " | ".join(CONFIG["designs"]) + " |", "|---|---|" + "---|" * len(CONFIG["designs"])]
    for v, what in CONFIG["variants"]:
        if v not in qor_bench.CONFIG["variants"]:
            continue
        row = [cell(qor_bench.load_result(d, p, v)) for d in CONFIG["designs"]]
        lines.append(f"| {v} | {what} | " + " | ".join(row) + " |")
    md = "\n".join(lines) + "\n"
    print(md)
    if a.doc_tag:
        qor_bench.write_doc(md, a.doc_tag)


if __name__ == "__main__":
    main()
