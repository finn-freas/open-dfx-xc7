"""Packing / detailed-placement experiments (docs/drafts/nextpnr-carry-di-bypass.md and the dpl Finding in
docs/qor-vivado.md). nextpnr runs go through flow/place_bench.py (ofx/npwait.sh), Vivado's timer through
vivado/dpl_dump.tcl (flow/dpl_vivado.sh, Vivado lock), metrics through flow/dpl_metrics.py.

  dpl_bench.py --designs rv_soc bram --variants dp0 dp1 [--seeds 1 2 3] [--run] [--xprep] [--vivado] [--report]
Dry run unless --run. --xprep also writes one 'free' source per design (Vivado places the same netlist itself).
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb
import qor_bench
import dpl_metrics

ROOT = pb.ROOT
TMG = ["-o", "hardblock-timing", "--placer", "static"]

CONFIG = {
    "out": ROOT / "build" / "qor" / "dpl",
    "vivado_tag": "dpl_xtime2",
    "vivado_chunk_minutes": 18,
    "vivado_minutes": {"eth": 9, "default": 2.5},
    "binaries": {
        "dpl0": "build/nextpnr-build/dpl0/nextpnr-himbaechel",
        "dpl1": "build/nextpnr-build/dpl1/nextpnr-himbaechel",
        "dpl2": "build/nextpnr-build/dpl2/nextpnr-himbaechel",
    },
    "variants": {
        "dp0": {"bin": "dpl0", "args": TMG, "cal": True, "rcal": True},
        "dp1off": {"bin": "dpl1", "args": TMG, "cal": True, "rcal": True},
        "dp1": {"bin": "dpl1", "args": TMG + ["-o", "carry-di-bypass"], "cal": True, "rcal": True},
        "dp2off": {"bin": "dpl2", "args": TMG, "cal": True, "rcal": True},
        "dp2cb": {"bin": "dpl2", "args": TMG + ["-o", "carry-di-bypass"], "cal": True, "rcal": True},
        "dp2dp": {"bin": "dpl2", "args": TMG + ["-o", "carry-di-bypass", "-o", "dpl"], "cal": True, "rcal": True},
        "dp3": {"bin": "dpl2", "args": TMG + ["-o", "carry-di-bypass", "-o", "dpl=2,2,0,1"], "cal": True, "rcal": True},
        "dp4": {"bin": "dpl2", "args": TMG + ["-o", "carry-di-bypass", "-o", "dpl=2,2,0,1,1"], "cal": True, "rcal": True},
        "dp2w": {"bin": "dpl2", "args": TMG + ["-o", "carry-di-bypass", "-o", "dpl=3,4,0.5,3"], "cal": True, "rcal": True},
    },
}

pb.CONFIG["binaries"].update(CONFIG["binaries"])
pb.CONFIG["variants"].update(CONFIG["variants"])
pb.CONFIG["out"] = CONFIG["out"]
pb.CONFIG["vivado_tag"] = CONFIG["vivado_tag"]


def top_of(design):
    return pb.CONFIG["socs"][design]["top"] if design in pb.CONFIG["socs"] else qor_bench.CONFIG["designs"][design]["top"]


def period_of(design, period):
    return pb.CONFIG["socs"][design]["period"] if design in pb.CONFIG["socs"] else period


def syn_json(design, period, vname, seed):
    st = json.loads((pb.run_dir(design, period, vname, seed) / "status.json").read_text())
    return Path(st["cmd"][st["cmd"].index("--json") + 1])


def free_name(design, period):
    tag = f"{design}_p10" if design in pb.CONFIG["socs"] else f"{design}_{qor_bench.ptag(period)}"
    return f"{tag}_free"


def xprep_free(design, period, vname, seed):
    name = free_name(design, period)
    d = CONFIG["out"] / "xsrc" / name
    d.mkdir(parents=True, exist_ok=True)
    pb.qx.write_netlist(syn_json(design, period, vname, seed), d / "netlist.edf", False)
    (d / "top.txt").write_text(top_of(design) + "\n")
    (d / "mode.txt").write_text("free\n")
    if design in pb.CONFIG["socs"]:
        xdc = pb.CONFIG["socs"][design]["vivado_xdc"].read_text()
    else:
        xdc = (qor_bench.CONFIG["out"] / "src" / f"{design}_{qor_bench.ptag(period)}" / "constraints.xdc").read_text()
    (d / "constraints.xdc").write_text(xdc)
    (d / "netlist.txt").write_text(str(syn_json(design, period, vname, seed)) + "\n")
    return name


def vdir(name):
    return pb.CONFIG["vivado_root"] / CONFIG["vivado_tag"] / name


def vivado_fmax(design, period, name):
    if design in pb.CONFIG["socs"]:
        return pb.soc_vivado(name, pb.CONFIG["socs"][design]["vivado_clock"])
    return pb.vivado_result(name, period)


def nextpnr_info(design, period, vname, seed):
    d = pb.run_dir(design, period, vname, seed)
    st = d / "status.json"
    if not st.exists():
        return {}
    r = json.loads(st.read_text())
    out = {"fmax": r.get("result", {}).get("fmax"), "seconds": r.get("pnr", {}).get("seconds")}
    if design in pb.CONFIG["socs"]:
        out["fmax"] = pb.parse_clock(ROOT / r["pnr"]["log"], pb.CONFIG["socs"][design]["clock"]).get("fmax")
    log = (d / "nextpnr.log")
    if log.exists():
        t = log.read_text(errors="replace")
        m = re.findall(r"Info: Program finished normally|ERROR", t)
        out["ok"] = bool(m) and m[-1] != "ERROR"
    rj = d / f"{top_of(design)}_routed.json"
    if rj.exists():
        j = json.loads(rj.read_text())
        m = j["modules"][next(iter(j["modules"]))]
        out["luts"] = sum(1 for c in m["cells"].values() if c["type"] == "SLICE_LUTX")
        sites = set()
        pips = 0
        for c in m["cells"].values():
            bel = c.get("attributes", {}).get("NEXTPNR_BEL", "")
            if bel.startswith("SLICE"):
                sites.add(bel.split("/")[0])
        for n in m["netnames"].values():
            r_ = n.get("attributes", {}).get("ROUTING", "")
            if r_:
                parts = r_.split(";")
                pips += sum(1 for i in range(1, len(parts), 3) if parts[i] and "/" in parts[i] and not parts[i - 1].startswith("SITEWIRE"))
        out["slices"] = len(sites)
        out["pips"] = pips
    return out


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None


def fmt(x, nd=2):
    return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def metrics_of(design, period, name, netlist):
    d = vdir(name)
    st = d / "status.txt"
    if not st.exists() or not st.read_text().startswith("rc 0"):
        return None
    cache = CONFIG["out"] / "metrics" / f"{name}.json"
    if cache.exists() and cache.stat().st_mtime > (d / "status.txt").stat().st_mtime:
        return json.loads(cache.read_text())
    r = dpl_metrics.metrics(d, netlist)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(r, indent=1) + "\n")
    return r


def report(designs, periods, vnames, seeds):
    rows = ["| design | variant | Vivado Fmax per seed (Vivado timer) | mean | nextpnr Fmax mean (nextpnr timer) | "
            "slices (Vivado count) | Vivado routed PIPs | HPWL | crit. net HPWL | LUT-FF direct % | carry S-LUT in slice % | "
            "nextpnr s | Vivado route s |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    data = {}
    for design in designs:
        for period in ([10] if design in pb.CONFIG["socs"] else periods):
            fn = free_name(design, period)
            ntxt = CONFIG["out"] / "xsrc" / fn / "netlist.txt"
            netlist = Path(ntxt.read_text().strip()) if ntxt.exists() else None
            fr = vivado_fmax(design, period, fn) if (vdir(fn) / "status.txt").exists() else None
            fm = metrics_of(design, period, fn, netlist) if netlist else None
            if fr or fm:
                fm = fm or {}
                rows.append(f"| {design} | Vivado places | {fmt(fr.get('fmax') if fr else None)} | {fmt(fr.get('fmax') if fr else None)} | - | "
                            f"{fmt(fm.get('util_slices'))} | {fmt(fm.get('signal_pips'))} | {fmt(fm.get('hpwl_total'))} | "
                            f"{fmt(fm.get('crit_net_hpwl_mean'))} | {fmt(fm.get('lutff_direct_pct'))} | "
                            f"{fmt(fm.get('carry', {}).get('s_lut_in_carry_slice_pct'))} | - | {fmt(fm.get('vivado_route_s'))} |")
                data[(design, "free")] = {"vivado": [fr.get("fmax") if fr else None], "metrics": [fm]}
            for v in vnames:
                viv, npr, ms, secs = [], [], [], []
                for s in seeds:
                    name = pb.xname(design, period, v, s)
                    x = vivado_fmax(design, period, name)
                    viv.append(x.get("fmax") if x and "fmax" in x else None)
                    ni = nextpnr_info(design, period, v, s)
                    npr.append(ni.get("fmax"))
                    secs.append(ni.get("seconds"))
                    ms.append(metrics_of(design, period, name, netlist) if netlist else None)
                data[(design, v)] = {"vivado": viv, "nextpnr": npr, "metrics": ms, "seconds": secs}
                mm = [m for m in ms if m]
                g = lambda k: mean([m.get(k) for m in mm])
                gc = mean([m.get("carry", {}).get("s_lut_in_carry_slice_pct") for m in mm])
                rows.append(f"| {design} | {v} | {' / '.join(fmt(x) for x in viv)} | {fmt(mean(viv))} | {fmt(mean(npr))} | "
                            f"{fmt(g('util_slices'), 0)} | {fmt(g('signal_pips'), 0)} | {fmt(g('hpwl_total'), 0)} | "
                            f"{fmt(g('crit_net_hpwl_mean'))} | {fmt(g('lutff_direct_pct'), 1)} | {fmt(gc, 1)} | "
                            f"{fmt(mean(secs), 1)} | {fmt(g('vivado_route_s'), 1)} |")
    return "\n".join(rows) + "\n", data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", nargs="+", default=["rv_soc", "rv_mul", "rv_big", "bram"])
    ap.add_argument("--periods", nargs="+", type=float, default=[5])
    ap.add_argument("--variants", nargs="+", default=["dp0"])
    ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--xprep", action="store_true")
    ap.add_argument("--vivado", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--noop", nargs=2, metavar=("A", "B"))
    a = ap.parse_args()
    dry = not a.run
    if a.noop:
        for d in a.designs:
            for p in ([10] if d in pb.CONFIG["socs"] else a.periods):
                for s in a.seeds:
                    fa, ma = pb.frames_of(d, p, a.noop[0], s)
                    fb, mb = pb.frames_of(d, p, a.noop[1], s)
                    strip = lambda t: [l for l in t.splitlines() if not l.startswith("#")]
                    same = ma.exists() and mb.exists() and strip(ma.read_text()) == strip(mb.read_text())
                    print(f"{d} s{s}: FASM {'identical' if same else 'DIFFERENT'} ({len(strip(ma.read_text())) if ma.exists() else 0} lines)")
        return
    names = []
    for d in a.designs:
        for p in ([10] if d in pb.CONFIG["socs"] else a.periods):
            for v in a.variants:
                for s in a.seeds:
                    if not a.xprep and not a.vivado and not a.report:
                        pb.pnr_one(d, p, v, s, dry)
                    if a.xprep and not dry:
                        ni = nextpnr_info(d, p, v, s)
                        if ni.get("fmax") is None:
                            print(f"[skip] {d} {v} s{s}: no finished run")
                            continue
                        if not (CONFIG["out"] / "xsrc" / free_name(d, p)).exists():
                            names.append(xprep_free(d, p, v, s))
                        names.append(pb.xprep(d, p, v, s, False))
                    if a.vivado:
                        names.append(pb.xname(d, p, v, s))
            if a.vivado:
                names.append(free_name(d, p))
    if a.vivado:
        todo = [n for n in dict.fromkeys(names) if (CONFIG["out"] / "xsrc" / n).exists() and not (vdir(n) / "status.txt").exists()]
        chunks, cur, w = [], [], 0
        for n in todo:
            nw = CONFIG["vivado_minutes"].get(n.split("_p")[0], CONFIG["vivado_minutes"]["default"])
            if cur and w + nw > CONFIG["vivado_chunk_minutes"]:
                chunks.append(cur)
                cur, w = [], 0
            cur.append(n)
            w += nw
        if cur:
            chunks.append(cur)
        for ch in chunks:
            cmd = [str(ROOT / "flow" / "dpl_vivado.sh")] + (["--run"] if not dry else []) + ch
            print(f"Vivado invocation: {len(ch)} names ({ch[0]} ...)", flush=True)
            subprocess.run(cmd, check=False)
    if a.report:
        txt, _ = report(a.designs, a.periods, a.variants, a.seeds)
        out = CONFIG["out"] / f"table_{'_'.join(a.variants)}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt)
        print(txt)


if __name__ == "__main__":
    main()
