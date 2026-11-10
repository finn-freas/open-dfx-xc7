"""Step 1: error of the current placer delay estimates against Vivado's routed delay, by arc class.
usage: measure.py [run-regex] [extra model module:function ...]"""
import importlib, math, sys
from collections import defaultdict
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import dl

CLB_S = {"LUT", "MUX", "FF", "CYO", "CYCO"}
CLB_D = {"LUT", "FFD", "CE", "SR", "CYS", "CYDI", "CYCI", "MUXI", "MUXS", "BYP"}
def classes(a):
    out = ["all"]
    if dl.is_carry_cascade(a):
        return out + ["carry CO3->CI"]
    if a["rel"] == "site":
        if dl.direct(a): out.append("same slice, direct")
        elif a["dc"] == "LUT": out.append("same slice, routed to LUT input")
        else: out.append("same slice, routed other")
        return out
    if a["rel"] == "tile":
        return out + ["same tile, other slice"]
    out.append("between tiles")
    d = abs(a["dx"] - a["sx"]) + abs(a["dy"] - a["sy"])
    if a["sc"] in CLB_S and a["dc"] in CLB_D:
        b = "1-2" if d <= 2 else "3-4" if d <= 4 else "5-8" if d <= 8 else "9-16" if d <= 16 else "17-32" if d <= 32 else "33+"
        out.append(f"CLB->CLB d {b}")
    if a["dc"] in ("CYS", "CYDI", "CYCI"): out.append("into CARRY4 (S/DI/CI)")
    if a["sc"] in ("CYO", "CYCO"): out.append("out of CARRY4")
    if a["sc"] == "BRAM": out.append("from BRAM")
    if a["dc"] in ("BRA", "BRD", "BRC"): out.append("to BRAM")
    if a["sc"] == "DSP": out.append("from DSP")
    if a["dc"] == "DSP": out.append("to DSP")
    c = dl.crossings(a["sx"], a["sy"], a["dx"], a["dy"])
    if c["bram"] or c["dsp"]: out.append("crosses BRAM/DSP column")
    if c["hclk"]: out.append("crosses clock row (HCLK)")
    if c["clk"]: out.append("crosses clock spine column")
    if a["fo"] >= 16: out.append("fanout >= 16")
    if 0 <= a["rank"] < 50: out.append("on Vivado's 50 worst paths")
    return out

class Acc:
    __slots__ = ("n", "se", "sae", "see", "sp", "sv", "spp", "svv", "spv")
    def __init__(s): s.n = 0; s.se = s.sae = s.see = s.sp = s.sv = s.spp = s.svv = s.spv = 0.0
    def add(s, p, v):
        e = p - v; s.n += 1; s.se += e; s.sae += abs(e); s.see += e * e
        s.sp += p; s.sv += v; s.spp += p * p; s.svv += v * v; s.spv += p * v
    def r(s):
        n = s.n; cp = s.spp - s.sp ** 2 / n; cv = s.svv - s.sv ** 2 / n
        return (s.spv - s.sp * s.sv / n) / math.sqrt(cp * cv) if cp > 0 and cv > 0 else float("nan")
    def fmt(s):
        if not s.n: return "-"
        return f"{s.se / s.n:+5.0f}/{s.sae / s.n:4.0f}/{s.r():+.2f}"

def run(models, sel, label=""):
    acc = defaultdict(lambda: defaultdict(Acc)); vivm = defaultdict(Acc)
    for r in sel:
        for a in dl.arcs(r):
            cl = classes(a)
            for name, f in models.items():
                p = f(a)
                for c in cl:
                    acc[c][name].add(p, a["viv"])
            for c in cl:
                vivm[c].add(a["viv"], a["viv"])
    order = list(acc)
    print(f"\n{label} runs {len(sel)}; cell = mean error / mean |error| (ps) / Pearson r, error = model - Vivado")
    print("| arc class | n | Vivado mean | " + " | ".join(models) + " |")
    print("|---|---|---|" + "---|" * len(models))
    for c in order:
        print(f"| {c} | {vivm[c].n} | {vivm[c].sv / vivm[c].n:.0f} | " + " | ".join(acc[c][m].fmt() for m in models) + " |")
    return acc

if __name__ == "__main__":
    pat = sys.argv[1] if len(sys.argv) > 1 else None
    models = {"static 816,40,40,18,18": dl.m_static, "sa-refine 313+1.235*matrix": dl.m_sa, "matrix (predictDelay)": dl.m_matrix}
    for spec in sys.argv[2:]:
        mod, fn = spec.split(":")
        models[fn] = getattr(importlib.import_module(mod), fn)
    run(models, dl.runs(pat), pat or "all")
