import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_synx

CONFIG = {
    "root": qor_synx.CONFIG["vivado_out"] / qor_synx.CONFIG["vivado_tag"],
    "directive": "Default",
    "synth_root": qor_synx.ROOT / "build" / "qor" / "synx" / "synth",
}


def util(p):
    if not p.exists():
        return {}
    t = p.read_text(errors="replace")
    out = {}
    for k, pat in (("lut_sites", r"\|\s*Slice LUTs\*?\s*\|\s*(\d+)"), ("lutram", r"\|\s*LUT as Memory\s*\|\s*(\d+)"),
                   ("ff", r"\|\s*Slice Registers\s*\|\s*(\d+)"), ("carry4", r"\|\s*CARRY4\s*\|\s*(\d+)"),
                   ("dsp", r"\|\s*DSP48E1\s*\|\s*(\d+)"), ("bram_tile", r"\|\s*Block RAM Tile\s*\|\s*([\d.]+)")):
        m = re.search(pat, t)
        if m:
            out[k] = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
    return out


def times(p):
    if not p.exists():
        return {}
    return {ln.split()[0]: float(ln.split()[1]) for ln in p.read_text().splitlines() if len(ln.split()) == 2}


def yosys_seconds(name):
    src = qor_synx.CONFIG["out"] / "src" / name / "json.txt"
    if not src.exists():
        return None
    js = Path(src.read_text().strip())
    meta = js.parent / "meta.json"
    if meta.exists():
        return json.loads(meta.read_text()).get("seconds")
    return None


def main():
    ap = argparse.ArgumentParser(description="Finding 14 table from the qor_synx Vivado runs")
    ap.add_argument("names", nargs="+", help="<design>_<variant> directory names")
    a = ap.parse_args()
    print(f"| netlist | Fmax MHz excl. ICAP (Vivado timer, {CONFIG['directive']}) | worst path levels (LUT, CARRY4) | "
          "post-route LUT sites | LUTRAM | FF | CARRY4 | synthesis s |")
    print("|---|---|---|---|---|---|---|---|")
    res = {}
    for n in a.names:
        base = CONFIG["root"] / n
        d = n.split("_")[0] + "_" + n.split("_")[1] if n.startswith(("rv_", "arty_")) else n.split("_")[0]
        rows = qor_synx.read_paths(base / CONFIG["directive"] / "paths.txt")
        s = qor_synx.summarize(d, rows) if rows else None
        u = util(base / CONFIG["directive"] / "util.rpt") or util(base / "synth_util.rpt")
        tm = times(base / "times.txt")
        syn = tm.get("synth") if "synth" in tm else yosys_seconds(n)
        res[n] = {"summary": s, "util": u, "times": tm, "synth_s": syn}
        fm = (s["fmax_noicap"] or s["fmax"]) if s else "-"
        lv = f"{s['worst_levels']} ({s['worst_luts']:.0f}, {s['worst_carry']:.0f})" if s and s.get("worst_luts") is not None else "-"
        print(f"| {n} | {fm} | {lv} | {u.get('lut_sites', '-')} | {u.get('lutram', '-')} | {u.get('ff', '-')} | "
              f"{u.get('carry4', '-')} | {syn if syn is not None else '-'} |")
    out = qor_synx.CONFIG["out"] / "finding14_table.json"
    out.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(f"json: {out}")


if __name__ == "__main__":
    main()
