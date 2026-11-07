import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qor_bench import CONFIG as QOR, ptag

ROOT = QOR["out"].parent.parent

CONFIG = {
    "oxc7": QOR["out"] / "oxc7",
    "out": QOR["out"] / "area",
    "vivado_out": QOR["vivado_out"],
    "vivado_own": "qor/{design}_{p}",
    "vivado_free": "qor_xtime/{design}_{p}_{vfree}_free",
    "period": 5,
    "seed": 1,
    "dry_run": True,
}

LUT_RE = re.compile(r"LUT[1-6]")


def load_netlist(js):
    j = json.loads(Path(js).read_text())
    mods = j["modules"]
    top = next((m for m in mods.values() if m.get("attributes", {}).get("top")), None) or list(mods.values())[0]
    return top


def nextpnr_area(routed, synth_json):
    cells = load_netlist(routed)["cells"]
    ycells = load_netlist(synth_json)["cells"] if synth_json and Path(synth_json).exists() else {}
    sites = collections.defaultdict(dict)
    kinds = collections.Counter()
    ff_ctrl = set()
    ff = carry = f7 = f8 = 0
    for name, c in cells.items():
        a = c.get("attributes", {})
        bel = a.get("NEXTPNR_BEL", "")
        t = c["type"]
        orig = a.get("X_ORIG_TYPE", "")
        if t == "SLICE_LUTX":
            slc, b = bel.split("/")
            if orig.startswith("RAM") or orig.startswith("SRL"):
                cls = "mem"
            elif name in ycells:
                cls = "logic"
            elif "_DUP" in name:
                cls = "dup"
            else:
                cls = "inserted"
            sites[(slc, b[0])][b[1:]] = (cls, orig, name)
            kinds[(cls, orig)] += 1
        elif t == "SLICE_FFX":
            ff += 1
            conns = c.get("connections", {})
            ff_ctrl.add((orig, tuple(conns.get("CK", [])), tuple(conns.get("CE", [])), tuple(conns.get("SR", []))))
        elif t == "CARRY4":
            carry += 1
        elif t == "SELMUX2_1":
            if "F7" in bel:
                f7 += 1
            else:
                f8 += 1
    occ = collections.Counter()
    for s, bels in sites.items():
        cl = sorted({v[0] for v in bels.values()})
        both = "5LUT" in bels and "6LUT" in bels
        occ[("+".join(cl), "O5+O6" if both else "single")] += 1
    slice_luts = len(sites)
    mem_sites = sum(n for (cl, _), n in occ.items() if "mem" in cl.split("+"))
    only_ins = sum(n for (cl, _), n in occ.items() if set(cl.split("+")) <= {"inserted", "dup"})
    slices = {s for s, _ in sites}
    pairs = sum(n for (cl, k), n in occ.items() if k == "O5+O6" and cl == "logic")
    return {"slice_luts": slice_luts, "slice_luts_vivado_rule": slice_luts - only_ins, "logic_pairs": pairs,
            "lut_mem_sites": mem_sites, "lut_logic_sites": slice_luts - mem_sites,
            "sites_only_inserted": only_ins, "ff": ff, "carry4": carry, "muxf7": f7, "muxf8": f8,
            "control_sets": len(ff_ctrl), "slices_with_lut": len(slices),
            "bels": {f"{k[0]}:{k[1]}": v for k, v in sorted(kinds.items())},
            "site_occupancy": {f"{k[0]}|{k[1]}": v for k, v in sorted(occ.items())}}


def vivado_util(d):
    ur = Path(d) / "util.rpt"
    if not ur.exists():
        return None
    txt = ur.read_text(errors="replace")

    def cell(label, after=None):
        t = txt
        if after and after in t:
            t = t[t.index(after):]
        m = re.search(r"^\|\s*" + re.escape(label) + r"\s*\|\s*([0-9.]+)", t, re.M)
        return int(float(m.group(1))) if m else None
    prim = {}
    if "Primitives" in txt:
        sec = txt[txt.rindex("Primitives"):]
        for m in re.finditer(r"^\|\s*(\w+)\s*\|\s*(\d+)\s*\|", sec, re.M):
            prim[m.group(1)] = int(m.group(2))
    lut_cells = sum(n for k, n in prim.items() if LUT_RE.fullmatch(k))
    return {"slice_luts": cell("Slice LUTs"), "lut_logic_sites": cell("LUT as Logic"), "lut_mem_sites": cell("LUT as Memory"),
            "srl_sites": cell("LUT as Shift Register"),
            "o5o6": cell("using O5 and O6", "2. Slice Logic Distribution"),
            "ff": cell("Slice Registers"), "carry4": prim.get("CARRY4", 0), "muxf7": cell("F7 Muxes"), "muxf8": cell("F8 Muxes"),
            "control_sets": cell("Unique Control Sets"), "slices": cell("Slice", "2. Slice Logic Distribution"),
            "lut_cells": lut_cells, "lut_by_size": {k: prim[k] for k in sorted(prim) if LUT_RE.fullmatch(k)},
            "dir": str(d)}


def yosys_stat(synth_json):
    meta = Path(synth_json).parent / "meta.json"
    if not meta.exists():
        return {}
    m = json.loads(meta.read_text())
    st = dict(m.get("stat") or {})
    sp = Path(synth_json).parent / "stat.txt"
    if sp.exists():
        for ln in sp.read_text().splitlines():
            mm = re.match(r"\s+(\d+)\s+(?:\S+\s+)?(LUT[1-6]|INV)\s*$", ln)
            if mm:
                st.setdefault("lut_by_size", {})
                st["lut_by_size"][mm.group(2)] = st["lut_by_size"].get(mm.group(2), 0) + int(mm.group(1))
    st["luts_incl_inv"] = sum(st.get("lut_by_size", {}).values())
    st["log"] = m.get("log")
    return st


def analyse(design, variant, period, seed, vfree):
    p = ptag(period)
    run = CONFIG["oxc7"] / variant / f"{design}_{p}" / f"s{seed}"
    st = run / "status.json"
    if not st.exists():
        return None
    rec = json.loads(st.read_text())
    top = QOR["designs"][design]["top"]
    routed = run / f"{top}_routed.json"
    sj = rec["cmd"][rec["cmd"].index("--json") + 1]
    res = {"design": design, "variant": variant, "period_ns": period, "seed": seed,
           "fmax_nextpnr": rec.get("result", {}).get("fmax"), "nextpnr_log": rec["pnr"]["log"],
           "yosys": yosys_stat(sj), "synth_json": sj}
    if routed.exists():
        res["nextpnr"] = nextpnr_area(routed, sj)
    res["vivado_own"] = vivado_util(CONFIG["vivado_out"] / CONFIG["vivado_own"].format(design=design, p=p))
    if vfree:
        res["vivado_free"] = vivado_util(CONFIG["vivado_out"] / CONFIG["vivado_free"].format(design=design, p=p, vfree=vfree))
    return res


def row(r):
    n, y, vo, vf = r.get("nextpnr") or {}, r["yosys"], r.get("vivado_own") or {}, r.get("vivado_free") or {}
    g = lambda d, k: "-" if not d or d.get(k) is None else str(d.get(k))
    return [r["design"], r["variant"],
            f"{g(vo, 'slice_luts')} ({g(vo, 'lut_cells')} cells, {g(vo, 'o5o6')} O5+O6)",
            f"{g(vf, 'slice_luts')} ({g(vf, 'lut_cells')} cells, {g(vf, 'o5o6')} O5+O6)",
            f"{g(n, 'slice_luts_vivado_rule')} ({g(n, 'logic_pairs')} O5+O6; + {g(n, 'sites_only_inserted')} feed-through only)",
            f"{g(y, 'luts_incl_inv')} LUT/INV + {g(y, 'lutram_cells')} RAM cells + {g(y, 'srl')} SRL",
            f"{g(vo, 'ff')} / {g(vf, 'ff')} / {g(n, 'ff')}",
            f"{g(vo, 'carry4')} / {g(vf, 'carry4')} / {g(n, 'carry4')}",
            f"{g(vo, 'lut_mem_sites')} / {g(vf, 'lut_mem_sites')} / {g(n, 'lut_mem_sites')}",
            f"{g(vo, 'control_sets')} / {g(vf, 'control_sets')} / {g(n, 'control_sets')}"]


HDR = ["design", "variant", "Vivado own: Slice LUTs", "Vivado P&R of yosys netlist: Slice LUTs", "nextpnr: LUT sites excl. feed-through-only",
       "yosys cells", "FF (own / yosys in Vivado / nextpnr)", "CARRY4", "LUTRAM+SRL sites", "control sets"]


def main():
    ap = argparse.ArgumentParser(description="post-place area: nextpnr routed JSON vs Vivado util.rpt, into build/qor/area")
    ap.add_argument("--designs", nargs="+", default=list(QOR["designs"]))
    ap.add_argument("--variants", nargs="+", default=["fix_static"])
    ap.add_argument("--period", type=float, default=CONFIG["period"])
    ap.add_argument("--seed", type=int, default=CONFIG["seed"])
    ap.add_argument("--vivado-free", default=None, help="qor_xtime tag of a Vivado P&R of the yosys netlist (e.g. tmg)")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    rows, out = [], {}
    for v in a.variants:
        for d in a.designs:
            if dry:
                print(f"[dry] area {d} {v} p{a.period:g} s{a.seed}")
                continue
            r = analyse(d, v, a.period, a.seed, a.vivado_free)
            if not r:
                continue
            out[f"{v}/{d}"] = r
            rows.append(row(r))
    if dry:
        return
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    name = "area_" + "_".join(a.variants) + f"_{ptag(a.period)}"
    (CONFIG["out"] / f"{name}.json").write_text(json.dumps(out, indent=1) + "\n")
    md = "| " + " | ".join(HDR) + " |\n|" + "---|" * len(HDR) + "\n" + "".join("| " + " | ".join(r) + " |\n" for r in rows)
    (CONFIG["out"] / f"{name}.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
