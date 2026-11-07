"""Per-RM comparison of Vivado's DFX build (vivado/build_dfx_rv.tcl) with the open native DFX builds of the same RTL
and pblock (rv_soc, u_rm, SLICE_X12Y100:SLICE_X15Y149, RMs xor/andn/add/rot).

Columns, every number with its timer or source:
  vivado_fmax        Vivado's timer on Vivado's DFX build: 1000 / (period - WNS), all paths and without ICAP paths
  open_fmax_np       nextpnr's timer on the open build (report.json; ICAPE2 pins untimed)
  open_fmax_np_hb    nextpnr's timer with -o hardblock-timing on the same placement and routing (flow/dfx_retime.py)
  open_fmax_viv      Vivado's timer on the open build's placement, routed by Vivado (flow/xtime_prep.py 'placed')
  area               RM cells in the pblock (Vivado report_utilization -pblocks; open: cells under u_rm. in the
                     routed json)
  partial            partial bitstream size (.bin bytes)
  time               Vivado step seconds (times.txt); open: nextpnr seconds of the module build (rv_soc.log)

  dfx_vivado_compare.py [--json OUT]
"""
import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIN = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build")

CONFIG = {
    "rms": ["xor", "andn", "add", "rot"],
    "vivado": {"p10": WIN / "dfx_rv_p10", "p5": WIN / "dfx_rv_p5"},
    "open": {"anchor": ROOT / "build/patched/rv_pr_native/router", "rv_ppt": ROOT / "build/patched/rv_ppt_native/partpin3"},
    "retime": {"anchor": ROOT / "build/dfxgaps/retime/rv_pr", "rv_ppt": ROOT / "build/dfxgaps/retime/rv_ppt"},
    "xtime": WIN / "dfx_xtime",
    "xtime_names": {"anchor": "anc", "rv_ppt": "ppt"},
    "partials": {"anchor": ROOT / "build/partials/rv_native_rr", "rv_ppt": ROOT / "build/patched/rv_ppt_native/repro_a/partials"},
}


def fmax(period, slack):
    return round(1000.0 / (period - slack), 2) if slack is not None else None


def vivado_cfg(d, rm):
    w = d / f"cfg_{rm}_wns.txt"
    if not w.exists():
        return None
    t = w.read_text()
    period = float(re.search(r"^period (\S+)", t, re.M).group(1))
    g = lambda k: float(m.group(1)) if (m := re.search(rf"^{k} (\S+)", t, re.M)) else None
    rec = {"period": period, "fmax_all": fmax(period, g("wns_all")), "fmax_noicap": fmax(period, g("wns_noicap")),
           "fmax_through_rm": fmax(period, g("wns_through_rm")),
           "worst_noicap": (re.search(r"^wns_noicap \S+ (.*)$", t, re.M) or [None, None])[1]}
    u = d / f"cfg_{rm}_pblock_util.rpt"
    if u.exists():
        ut = u.read_text()
        for key, label in (("lut", r"Slice LUTs\*?"), ("ff", r"Slice Registers"), ("carry", r"CARRY4")):
            m = re.search(rf"^\|\s*{label}\s*\|\s*(\d+)", ut, re.M)
            rec[key] = int(m.group(1)) if m else None
    p = d / f"cfg_{rm}_pblock_rm_partial.bin"
    rec["partial_bytes"] = p.stat().st_size if p.exists() else None
    tt = d / "times.txt"
    if tt.exists():
        times = dict(l.split() for l in tt.read_text().splitlines() if l.strip())
        rec["impl_s"] = float(times.get(f"impl_{rm}", "nan"))
        rec["synth_s"] = float(times.get(f"synth_{rm}", "nan"))
    return rec


def open_cfg(flow, rm):
    d = CONFIG["open"][flow] / f"{rm}_n"
    if not d.exists():
        return None
    rep = json.loads((d / "report.json").read_text())
    rec = {"fmax_np": round(next(iter(rep["fmax"].values()))["achieved"], 2)}
    rt = CONFIG["retime"][flow] / f"{rm}_n" / "retime.json"
    if rt.exists():
        r = json.loads(rt.read_text())
        if r.get("place_route_identical"):
            rec["fmax_np_hb"] = round(next(iter(r["hardblock_fmax"].values())), 2)
    m = json.loads((d / "rv_soc_routed.json").read_text())
    top = next(v for v in m["modules"].values() if v.get("attributes", {}).get("top"))
    cnt = collections.Counter()
    for name, c in top["cells"].items():
        if name.startswith("u_rm."):
            t = c["type"]
            cnt["lut" if "LUT" in t else "ff" if t.startswith("FD") or "FF" in t else "carry" if "CARRY" in t else t] += 1
    rec.update({k: cnt.get(k, 0) for k in ("lut", "ff", "carry")})
    lg = (d / "rv_soc.log").read_text()
    s = re.search(r"\[run\] nextpnr:.*\n\s+([\d.]+)s", lg)
    rec["nextpnr_s"] = float(s.group(1)) if s else None
    return rec


def xtime(flow, rm, tag):
    d = CONFIG["xtime"] / f"{CONFIG['xtime_names'][flow]}_{rm}_{tag}"
    tr = d / "timing.rpt"
    if not tr.exists():
        return None
    t = tr.read_text()
    m = re.search(r"WNS\(ns\).*\n.*\n\s*(-?[\d.]+)", t)
    period = 5.0 if tag == "p5" else 10.0
    rec = {"fmax_all": fmax(period, float(m.group(1))) if m else None}
    wp = d / "worst_paths.txt"
    if wp.exists():
        for l in wp.read_text().splitlines():
            sl, s, e = (l.split() + ["", "", ""])[:3]
            if not s.startswith("u_icap") and not e.startswith("u_icap"):
                rec["fmax_noicap"] = fmax(period, float(sl))
                break
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    out = {}
    for rm in CONFIG["rms"]:
        r = out[rm] = {"vivado": {k: vivado_cfg(v, rm) for k, v in CONFIG["vivado"].items()},
                       "open": {f: open_cfg(f, rm) for f in CONFIG["open"]},
                       "open_xtime": {f: {t: xtime(f, rm, t) for t in ("placed", "p5")} for f in CONFIG["open"]}}
        for f, d in CONFIG["partials"].items():
            ps = sorted(d.glob(f"rm_{rm}_from_*.bin"))
            if r["open"].get(f) and ps:
                r["open"][f]["partial_bytes"] = ps[0].stat().st_size
    print(json.dumps(out, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
