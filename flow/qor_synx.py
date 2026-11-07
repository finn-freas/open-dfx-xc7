import argparse
import json
import os
import re
import shutil
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
import qor_xtime
import synth_timing

ROOT = qor_bench.ROOT

CONFIG = {
    "out": ROOT / "build" / "qor" / "synx",
    "vivado_out": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "vivado_tag": "qor_synx",
    "dry_run": True,
    "period_ns": 5,
    "designs": ["rv_soc", "rv_mul", "rv_big", "bram", "fir", "arty_ddr3"],
    "litex": {
        "arty_ddr3": {"src": ROOT / "designs" / "ddr3" / "arty_ddr3", "top": "digilent_arty", "xdc": "digilent_arty.xdc",
                      "clock": "main_crg_clkout0", "default_json": ROOT / "build" / "ddr3" / "arty_ddr3" / "gapfix" / "digilent_arty.json"},
    },
    "icap_re": re.compile(r"u_icap"),
    "worst_n": 100,
    "directives": ["Default", "Explore", "ExtraTimingOpt"],
    "npwait": "ofx/npwait.sh",
    "npwait_max": "2",
    "nextpnr_build": "qordsp",
    "nextpnr_args": qor_bench.DCP,
    "nextpnr_seeds": [1, 2, 3],
    "nextpnr_designs": ["rv_soc", "rv_mul", "rv_big", "bram", "fir"],
}


def is_litex(design):
    return design in CONFIG["litex"]


def netlist_json(design, vname, dry):
    v = synth_timing.VARIANTS[vname]
    if v.get("qor_variant") and not is_litex(design):
        rec = qor_bench.synth(design, CONFIG["period_ns"], v["qor_variant"], dry)
        return Path(rec["json"]), rec.get("key")
    if v.get("qor_variant") == "fix_static" and is_litex(design):
        return CONFIG["litex"][design]["default_json"], "gapfix"
    rec = synth_timing.synth(design, vname, dry)
    return Path(rec["json"]), rec.get("key")


def src_name(design, vname):
    return f"{design}_{vname}"


def prep_one(design, vname, dry):
    d = CONFIG["out"] / "src" / src_name(design, vname)
    v = synth_timing.VARIANTS[vname]
    if is_litex(design):
        lx = CONFIG["litex"][design]
        top, rtl_dir, xdc = lx["top"], lx["src"], lx["src"] / lx["xdc"]
        extra = sorted(rtl_dir.glob("*.init"))
    else:
        rtl_dir = qor_bench.prepare_src(design, CONFIG["period_ns"])
        top = qor_bench.CONFIG["designs"][design]["top"]
        xdc = rtl_dir / "constraints.xdc"
        extra = sorted(rtl_dir.glob("*.hex"))
    if v.get("vivado_synth"):
        print(f"[{'dry' if dry else 'run'}] {d.name}: Vivado synth_design of the RTL")
        if dry:
            return d.name
        d.mkdir(parents=True, exist_ok=True)
        for f in qor_bench.rtl_files(rtl_dir) + extra:
            shutil.copyfile(f, d / f.name)
        (d / "mode.txt").write_text("rtl\n")
    else:
        js, key = netlist_json(design, vname, dry)
        print(f"[{'dry' if dry else 'run'}] {d.name}: EDIF of {js}")
        if dry:
            return d.name
        d.mkdir(parents=True, exist_ok=True)
        if (d / "netlist.edf").exists() and (d / "key.txt").exists() and (d / "key.txt").read_text().strip() != str(key):
            (d / "netlist.edf").unlink()
        qor_xtime.write_netlist(js, d / "netlist.edf", dry)
        (d / "key.txt").write_text(f"{key}\n")
        (d / "json.txt").write_text(f"{js}\n")
        for f in extra:
            shutil.copyfile(f, d / f.name)
        (d / "mode.txt").write_text("edif\n")
    shutil.copyfile(xdc, d / "constraints.xdc")
    (d / "top.txt").write_text(top + "\n")
    return d.name


def read_paths(p):
    rows = []
    if not p.exists():
        return rows
    for ln in p.read_text().splitlines():
        f = ln.split()
        if len(f) < 13:
            continue
        num = lambda x: float(x) if x not in ("-", "") else None
        rows.append({"slack": num(f[0]), "req": num(f[1]), "levels": int(f[2]), "luts": num(f[3]), "carry": num(f[4]),
                     "muxf": num(f[5]), "delay": num(f[6]), "logic": num(f[7]), "net": num(f[8]), "sclk": f[9], "eclk": f[10],
                     "start": f[11], "end": f[12]})
    return rows


def main_clock(design, rows):
    if is_litex(design):
        return CONFIG["litex"][design]["clock"]
    cnt = {}
    for r in rows:
        if r["sclk"] == r["eclk"]:
            cnt[r["eclk"]] = cnt.get(r["eclk"], 0) + 1
    return max(cnt, key=cnt.get) if cnt else None


def summarize(design, rows):
    clk = main_clock(design, rows)
    intra = [r for r in rows if r["sclk"] == clk and r["eclk"] == clk and r["slack"] is not None]
    if not intra:
        return None
    noicap = [r for r in intra if not CONFIG["icap_re"].search(r["end"]) and not CONFIG["icap_re"].search(r["start"])]
    w = intra[0]
    wn = noicap[0] if noicap else None
    top = noicap[:CONFIG["worst_n"]]
    fm = lambda r: round(1000.0 / (r["req"] - r["slack"]), 2)
    return {"clock": clk, "wns": w["slack"], "fmax": fm(w), "fmax_noicap": fm(wn) if wn else None,
            "worst_levels": wn["levels"] if wn else None, "worst_luts": wn["luts"] if wn else None,
            "worst_carry": wn["carry"] if wn else None, "worst_logic": wn["logic"] if wn else None,
            "worst_net": wn["net"] if wn else None, "worst_end": wn["end"] if wn else None,
            "mean_levels_top": round(statistics.mean(r["levels"] for r in top), 2) if top else None,
            "mean_luts_top": round(statistics.mean(r["luts"] for r in top if r["luts"] is not None), 2) if top else None,
            "max_levels_top": max(r["levels"] for r in top) if top else None,
            "net_per_hop_top": round(statistics.mean(r["net"] / (r["levels"] + 1) for r in top), 3) if top else None}


def util_counts(p):
    if not p.exists():
        return {}
    t = p.read_text(errors="replace")
    out = {}
    for key, pat in (("lut", r"\|\s*Slice LUTs\*?\s*\|\s*(\d+)"), ("ff", r"\|\s*Slice Registers\s*\|\s*(\d+)"),
                     ("carry4", r"\|\s*CARRY4\s*\|\s*(\d+)")):
        m = re.search(pat, t)
        if m:
            out[key] = int(m.group(1))
    return out


def report(designs, vnames):
    root = CONFIG["vivado_out"] / CONFIG["vivado_tag"]
    res = {}
    for d in designs:
        for v in vnames:
            base = root / src_name(d, v)
            rec = {"opt": summarize(d, read_paths(base / "opt_paths.txt")), "util": util_counts(base / "opt_util.rpt"),
                   "status": (base / "status.txt").read_text().split("\n")[0] if (base / "status.txt").exists() else None,
                   "runs": {}}
            for di in CONFIG["directives"]:
                s = summarize(d, read_paths(base / di / "paths.txt"))
                if s:
                    rec["runs"][di] = s
            fms = [s["fmax_noicap"] or s["fmax"] for s in rec["runs"].values()]
            if fms:
                rec["fmax_mean"] = round(statistics.mean(fms), 2)
                rec["fmax_best"] = max(fms)
                rec["fmax_worst"] = min(fms)
                rec["wns_mean"] = round(statistics.mean(s["wns"] for s in rec["runs"].values()), 3)
                rec["levels_mean"] = round(statistics.mean(s["mean_levels_top"] for s in rec["runs"].values()), 2)
                rec["worst_levels"] = [s["worst_levels"] for s in rec["runs"].values()]
            res[f"{d}/{v}"] = rec
    out = CONFIG["out"] / f"report_{'_'.join(vnames)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(f"| design | netlist | Fmax MHz excl. ICAP, mean (best-worst) of {len(CONFIG['directives'])} place directives (Vivado timer) | "
          f"WNS mean ns | worst path: levels (LUT, CARRY4), per directive | mean levels, worst {CONFIG['worst_n']} paths | "
          f"post-opt est.: mean levels | LUT / FF / CARRY4 (post-opt) |")
    print("|---|---|---|---|---|---|---|---|")
    for k, r in res.items():
        d, v = k.split("/")
        if "fmax_mean" not in r:
            print(f"| {d} | {v} | {r['status']} | | | | | |")
            continue
        wl = ", ".join(f"{s['worst_levels']} ({s['worst_luts']:.0f}, {s['worst_carry']:.0f})" for s in r["runs"].values())
        u = r["util"]
        print(f"| {d} | {v} | {r['fmax_mean']} ({r['fmax_best']}-{r['fmax_worst']}) | {r['wns_mean']} | {wl} | {r['levels_mean']} | "
              f"{r['opt']['mean_levels_top'] if r['opt'] else '-'} | {u.get('lut')} / {u.get('ff')} / {u.get('carry4')} |")
    print(f"json: {out}")


def nextpnr_variant(vname):
    name = f"synx_{vname}_noicap"
    np_bin, chipdb = qor_bench.CONFIG["nextpnr"][CONFIG["nextpnr_build"]]
    qor_bench.CONFIG["nextpnr"]["synx_npwait"] = (CONFIG["npwait"], chipdb)
    os.environ["OFX_NEXTPNR_BIN"] = str(ROOT / np_bin)
    os.environ["OFX_MAX_NEXTPNR"] = CONFIG["npwait_max"]
    qor_bench.CONFIG["variants"][name] = {"nextpnr": "synx_npwait", "args": CONFIG["nextpnr_args"],
                                          "seeds": CONFIG["nextpnr_seeds"], "bitstream": False,
                                          "xdc_extra": qor_bench.ICAP_MCP}
    return name


def nextpnr(designs, vnames, dry):
    res = {}
    for d in designs:
        if d not in CONFIG["nextpnr_designs"]:
            continue
        for v in vnames:
            if d in synth_timing.VARIANTS[v].get("skip", ()) or synth_timing.VARIANTS[v].get("vivado_synth"):
                continue
            js, key = netlist_json(d, v, dry)
            qv = nextpnr_variant(v)
            runs = [qor_bench.pnr_one(d, CONFIG["period_ns"], qv, s, {"json": str(js), "key": key}, dry)
                    for s in CONFIG["nextpnr_seeds"]]
            if dry:
                continue
            fm = [r.get("result", {}).get("fmax") for r in runs]
            ok = [f for f in fm if f]
            res[f"{d}/{v}"] = {"fmax": fm, "mean": round(statistics.mean(ok), 2) if ok else None,
                               "best": max(ok) if ok else None, "logs": [r.get("pnr", {}).get("log") for r in runs]}
            print(d, v, json.dumps(res[f"{d}/{v}"]), flush=True)
    if not dry:
        out = CONFIG["out"] / f"nextpnr_{'_'.join(vnames)}.json"
        out.write_text(json.dumps(res, indent=1) + "\n")
        print(f"json: {out}")


def main():
    ap = argparse.ArgumentParser(description="Synthesis-only comparison under Vivado's timer: Vivado's synth_design and yosys "
                                             "netlists (variants of flow/synth_timing.py) through the same Vivado opt/place/route "
                                             "with several place directives (vivado/build_synx.tcl)")
    ap.add_argument("--designs", nargs="+", default=CONFIG["designs"])
    ap.add_argument("--variants", nargs="+", default=["viv", "ys"])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--nextpnr", action="store_true")
    a = ap.parse_args()
    if a.report:
        report(a.designs, a.variants)
        return
    dry = CONFIG["dry_run"] and not a.run
    if a.nextpnr:
        nextpnr(a.designs, a.variants, dry)
        return
    names = []
    for d in a.designs:
        for v in a.variants:
            if d in synth_timing.VARIANTS[v].get("skip", ()):
                continue
            names.append(prep_one(d, v, dry))
    print("names: " + ",".join(names))
    print(f"vivado: vivado\\run_qor.ps1 -Tag {CONFIG['vivado_tag']} -Script build_synx.tcl -SrcRel build\\qor\\synx\\src "
          f"-Names {','.join(names)} -Run")


if __name__ == "__main__":
    main()
