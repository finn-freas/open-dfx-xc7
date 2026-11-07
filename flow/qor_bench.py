import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_openxc7 import CONFIG as OXC7_CONFIG, DB, OXC7, tool

ROOT = OXC7_CONFIG["root"]
NIGHTLY_CHIPDB = OXC7 / "share" / "nextpnr" / "himbaechel" / "xilinx" / "chipdb-xc7a50t.bin"
SYNTH_BASE = "synth_xilinx -flatten -abc9 -arch xc7 -top {top}"
TMG = ["-o", "hardblock-timing"]
ICAP_MCP = "set_multicycle_path -setup 2 -to [get_cells u_icap]\n"
DSP_PLUGIN = "build/yosys-plugin/xilinx_dsp_qor/xilinx_dsp_qor.so"
MAP_DSP_XC7 = ("memory_dff; alumacc -macc-only; maccmap -unmap; opt_clean; techmap -map +/mul2dsp.v -map +/xilinx/xc7_dsp_map.v "
               "-D DSP_A_MAXWIDTH=25 -D DSP_B_MAXWIDTH=18 -D DSP_A_MAXWIDTH_PARTIAL=18 -D DSP_A_MINWIDTH=2 -D DSP_B_MINWIDTH=2 "
               "-D DSP_Y_MINWIDTH=9 -D DSP_SIGNEDONLY=1 -D DSP_NAME=$__MUL25X18; select a:mul2dsp; setattr -unset mul2dsp; "
               "opt_expr -fine; wreduce; select -clear; xilinx_dsp_qor -family xc7{opt}; chtype -set $mul t:$__soft_mul")
SYNTH_DSPQ = SYNTH_BASE + " -run begin:map_dsp; " + MAP_DSP_XC7 + "; " + SYNTH_BASE + " -run coarse:"
SYNTH_DSPQ_OFF = SYNTH_DSPQ.replace("{opt}", "")
SYNTH_DSPQ_ON = SYNTH_DSPQ.replace("{opt}", " -pipeline")
YOSYS_AREA = "build/yosys-build/yosys-area/yosys"
SYNTH_AREA = SYNTH_BASE + " -share_aggressive"
SYNTH_AREA_CMW = SYNTH_BASE + " -carry_minwidth {cmw}"
SYNTH_AREA_BOTH = SYNTH_BASE + " -share_aggressive -carry_minwidth {cmw}"
DCP = TMG + ["--placer", "static", "-o", "dsp-cascade-place"]
DIB = ["-o", "carry-di-bypass"]
LPAIR = ["-o", "lut-pair"]

CONFIG = {
    "part": OXC7_CONFIG["part"],
    "family": OXC7_CONFIG["family"],
    "out": ROOT / "build" / "qor",
    "doc": ROOT / "docs" / "qor-vivado.md",
    "vivado_out": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "vivado_tag": "qor",
    "dry_run": True,
    "timeout_s": 3600,
    "periods_ns": [10, 7, 5],
    "designs": {
        "blinky": {"src": "designs/gap/qor_blinky", "top": "qor_blinky"},
        "rv_soc": {"src": "designs/gap/qor_rv_soc", "top": "qor_rv_soc"},
        "rv_mul": {"src": "designs/gap/qor_rv_mul", "top": "qor_rv_mul"},
        "rv_big": {"src": "designs/qor/qor_rv_big", "top": "qor_rv_big"},
        "fir": {"src": "designs/qor/qor_fir", "top": "qor_fir"},
        "bram": {"src": "designs/qor/qor_bram", "top": "qor_bram"},
    },
    "nextpnr": {
        "nightly": (None, None),
        "stock": ("build/nextpnr-build/stock/nextpnr-himbaechel", NIGHTLY_CHIPDB),
        "gapfix": ("build/nextpnr-build/gapfix/nextpnr-himbaechel", NIGHTLY_CHIPDB),
        "qor": ("build/nextpnr-build/qor/nextpnr-himbaechel", NIGHTLY_CHIPDB),
        "qorfix": ("build/nextpnr-build/qorfix/nextpnr-himbaechel", NIGHTLY_CHIPDB),
        "qordsp": ("build/nextpnr-build/qordsp/nextpnr-himbaechel", NIGHTLY_CHIPDB),
        "qordsp_cal": ("build/nextpnr-build/qordsp/nextpnr-himbaechel", ROOT / "build" / "chipdb-cal" / "on" / "chipdb-xc7a50t.bin"),
        "qorarea": ("build/nextpnr-build/qorarea/nextpnr-himbaechel", NIGHTLY_CHIPDB),
    },
    "variants": {
        "base": {},
        "qor_noopt": {"nextpnr": "qor"},
        "tmg": {"nextpnr": "qor", "args": TMG},
        "tmg_seeds8": {"nextpnr": "qor", "args": TMG, "seeds": list(range(1, 9))},
        "tmg_dff": {"nextpnr": "qor", "args": TMG, "synth": SYNTH_BASE + " -dff"},
        "tmg_wm5": {"nextpnr": "qor", "args": TMG, "synth": SYNTH_BASE + " -widemux 5"},
        "tmg_D25": {"nextpnr": "qor", "args": TMG, "abc9_D_frac": 0.25},
        "tmg_critexp4": {"nextpnr": "qor", "args": TMG + ["--placer-heap-critexp", "4"]},
        "tmg_tw20": {"nextpnr": "qor", "args": TMG + ["--placer-heap-timingweight", "20"]},
        "tmg_tw40": {"nextpnr": "qor", "args": TMG + ["--placer-heap-timingweight", "40"]},
        "tmg_ripup": {"nextpnr": "qor", "args": TMG + ["--tmg-ripup"]},
        "tmg_topt": {"nextpnr": "qor", "args": TMG + ["-o", "timing-opt=4,30"]},
        "tmg_altw": {"nextpnr": "qor", "args": TMG + ["--router2-alt-weights"]},
        "tmg_slack": {"nextpnr": "qor", "args": TMG + ["--router2-slack-order"]},
        "tmg_bbbudget": {"nextpnr": "qor", "args": TMG + ["--router2-bb-budget"]},
        "tmg_s3": {"nextpnr": "qor", "args": TMG, "seeds": [1, 2, 3]},
        "tmg_static": {"nextpnr": "qor", "args": TMG + ["--placer", "static"]},
        "tmg_sa": {"nextpnr": "qor", "args": TMG + ["--placer", "sa"]},
        "tmg_parref": {"nextpnr": "qor", "args": TMG + ["--parallel-refine"]},
        "fix_tmg": {"nextpnr": "qorfix", "args": TMG},
        "fix_tmg_wm5": {"nextpnr": "qorfix", "args": TMG, "synth": SYNTH_BASE + " -widemux 5"},
        "fix_tmg_noicap": {"nextpnr": "qorfix", "args": TMG, "xdc_extra": ICAP_MCP},
        "fix_tmg_noicap_s8": {"nextpnr": "qorfix", "args": TMG, "xdc_extra": ICAP_MCP, "seeds": list(range(1, 9))},
        "fix_tmg_s8": {"nextpnr": "qorfix", "args": TMG, "seeds": list(range(1, 9))},
        "fix_tmg_ce4_s8": {"nextpnr": "qorfix", "args": TMG + ["--placer-heap-critexp", "4"], "seeds": list(range(1, 9))},
        "fix_tmg_bramforce": {"nextpnr": "qorfix", "args": TMG + ["-o", "bram-place=force"]},
        "fix_tmg_ctforce": {"nextpnr": "qorfix", "args": TMG + ["-o", "clock-tree=force"]},
        "fix_tmg_dmoff": {"nextpnr": "qorfix", "args": TMG + ["-o", "delay-matrix=off"]},
        "fix_tmg_notimeout": {"nextpnr": "qorfix", "args": TMG + ["--placer-heap-cell-placement-timeout", "0"]},
        "fix_static": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static"]},
        "fix_static_s8": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static"], "seeds": list(range(1, 9))},
        "fix_static_auto": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static"], "seeds": list(range(1, 9)),
                            "until_met": True},
        "fix_static_noicap": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static"], "xdc_extra": ICAP_MCP},
        "fix_static_noicap_s8": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static"], "xdc_extra": ICAP_MCP,
                                 "seeds": list(range(1, 9))},
        "fix_static_bf": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static", "-o", "bram-place=force"]},
        "fix_heap_bf_s8": {"nextpnr": "qorfix", "args": TMG + ["-o", "bram-place=force"], "seeds": list(range(1, 9))},
        "tmg_auto": {"nextpnr": "qor", "args": TMG, "seeds": list(range(1, 9)), "until_met": True},
        "dspq_off": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static"], "synth": SYNTH_DSPQ_OFF, "plugin": DSP_PLUGIN},
        "dspq": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static"], "synth": SYNTH_DSPQ_ON, "plugin": DSP_PLUGIN},
        "dspq_s8": {"nextpnr": "qorfix", "args": TMG + ["--placer", "static"], "synth": SYNTH_DSPQ_ON, "plugin": DSP_PLUGIN,
                    "seeds": list(range(1, 9))},
        "dspq_heap": {"nextpnr": "qorfix", "args": TMG, "synth": SYNTH_DSPQ_ON, "plugin": DSP_PLUGIN},
        "dcp_noopt": {"nextpnr": "qordsp", "args": TMG + ["--placer", "static"]},
        "cal_static": {"nextpnr": "qordsp_cal", "args": TMG + ["--placer", "static", "-o", "dsp-cascade-place"]},
        "dspq_cal": {"nextpnr": "qordsp_cal", "args": TMG + ["--placer", "static", "-o", "dsp-cascade-place"],
                     "synth": SYNTH_DSPQ_ON, "plugin": DSP_PLUGIN},
        "dcp_static": {"nextpnr": "qordsp", "args": TMG + ["--placer", "static", "-o", "dsp-cascade-place"]},
        "dcp_heap": {"nextpnr": "qordsp", "args": TMG + ["-o", "dsp-cascade-place"]},
        "dspq_dcp": {"nextpnr": "qordsp", "args": TMG + ["--placer", "static", "-o", "dsp-cascade-place"],
                     "synth": SYNTH_DSPQ_ON, "plugin": DSP_PLUGIN},
        "dspq_dcp_heap": {"nextpnr": "qordsp", "args": TMG + ["-o", "dsp-cascade-place"], "synth": SYNTH_DSPQ_ON,
                          "plugin": DSP_PLUGIN},
        "dspq_dcp_s8": {"nextpnr": "qordsp", "args": TMG + ["--placer", "static", "-o", "dsp-cascade-place"],
                        "synth": SYNTH_DSPQ_ON, "plugin": DSP_PLUGIN, "seeds": list(range(1, 9))},
        "area_ref": {"nextpnr": "qorarea", "args": DCP, "seeds": list(range(1, 5))},
        "area_di": {"nextpnr": "qorarea", "args": DCP + DIB},
        "area_pair": {"nextpnr": "qorarea", "args": DCP + LPAIR},
        "area_pnr": {"nextpnr": "qorarea", "args": DCP + DIB + LPAIR, "seeds": list(range(1, 5))},
        "area_ysref": {"nextpnr": "qorarea", "args": DCP, "yosys": YOSYS_AREA},
        "area_share": {"nextpnr": "qorarea", "args": DCP + DIB + LPAIR, "synth": SYNTH_AREA, "yosys": YOSYS_AREA},
        "area_cmw": {"nextpnr": "qorarea", "args": DCP + DIB + LPAIR, "synth": SYNTH_AREA_CMW.replace("{cmw}", "5"),
                     "yosys": YOSYS_AREA},
        "area_all": {"nextpnr": "qorarea", "args": DCP + DIB + LPAIR, "synth": SYNTH_AREA_BOTH.replace("{cmw}", "5"),
                     "yosys": YOSYS_AREA, "seeds": list(range(1, 5))},
        "dcp_wm5": {"nextpnr": "qordsp", "args": DCP, "synth": SYNTH_BASE + " -widemux 5"},
        "area_wm5_ref": {"nextpnr": "qorarea", "args": DCP, "synth": SYNTH_BASE + " -widemux 5"},
        "area_wm5": {"nextpnr": "qorarea", "args": DCP + DIB + LPAIR, "synth": SYNTH_BASE + " -widemux 5"},
    },
    "err_re": re.compile(r"(ERROR|Traceback|terminate called|Assertion|Segmentation|FATAL|abort)"),
}

VARIANT_DEFAULTS = {"synth": SYNTH_BASE, "abc9_D_frac": None, "nextpnr": "nightly", "args": [], "seeds": [1],
                    "bitstream": True, "until_met": False, "xdc_extra": "", "plugin": None, "yosys": None}


def variant(name):
    v = dict(VARIANT_DEFAULTS)
    v.update(CONFIG["variants"][name])
    return v


def sha(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, bytes) else str(p).encode())
        h.update(b"\0")
    return h.hexdigest()[:16]


def ptag(period):
    return f"p{period:g}".replace(".", "_")


def rtl_files(src):
    return sorted(src.glob("*.v")) + sorted(src.glob("*.sv"))


def prepare_src(design, period):
    d = CONFIG["designs"][design]
    src = ROOT / d["src"]
    dst = CONFIG["out"] / "src" / f"{design}_{ptag(period)}"
    dst.mkdir(parents=True, exist_ok=True)
    for f in rtl_files(src) + sorted(src.glob("*.hex")):
        if not (dst / f.name).exists() or (dst / f.name).read_bytes() != f.read_bytes():
            shutil.copyfile(f, dst / f.name)
    xdc = next(src.glob("*.xdc")).read_text()
    xdc, n = re.subn(r"-period\s+[0-9.]+", f"-period {period:.3f}", xdc)
    if n != 1:
        sys.exit(f"{design}: expected one create_clock -period in the xdc, found {n}")
    (dst / "constraints.xdc").write_text(xdc)
    (dst / "top.txt").write_text(d["top"] + "\n")
    return dst


def run_logged(cmd, log, cwd):
    t0 = time.time()
    with open(log, "w") as f:
        try:
            rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=cwd, timeout=CONFIG["timeout_s"]).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    return rc, round(time.time() - t0, 2)


def first_error(log):
    if not log.exists():
        return ""
    for ln in log.read_text(errors="replace").splitlines():
        if CONFIG["err_re"].search(ln):
            return ln.strip()[:300]
    return ""


def synth(design, period, vname, dry):
    v = variant(vname)
    d = CONFIG["designs"][design]
    src = prepare_src(design, period)
    top = d["top"]
    script = v["synth"].format(top=top)
    pre = ""
    if v["abc9_D_frac"]:
        pre = f"scratchpad -set abc9.D {int(round(period * 1000 * v['abc9_D_frac']))}; "
    files = rtl_files(src)
    ys_bin = str(ROOT / v["yosys"]) if v["yosys"] else tool("yosys")
    plugin = ROOT / v["plugin"] if v["plugin"] else None
    key = sha(ys_bin, Path(ys_bin).stat().st_size, pre, script, *[f.name + sha(f.read_bytes()) for f in files],
              *([sha(plugin.read_bytes())] if plugin else []))
    out = CONFIG["out"] / "synth" / design / key
    js = out / f"{top}.json"
    meta = out / "meta.json"
    if meta.exists() and json.loads(meta.read_text()).get("ok"):
        return json.loads(meta.read_text())
    ys = (f"read_verilog -sv {' '.join(f.name for f in files)}; {pre}{script}; "
          f"tee -o {out / 'stat.txt'} stat -tech xilinx; write_json {js}")
    cmd = [ys_bin] + (["-m", str(plugin)] if plugin else []) + ["-p", ys]
    if dry:
        print(f"[dry] synth {design} {vname} -> {out.relative_to(ROOT)}: {pre}{script}")
        return {"ok": None, "dry": True, "json": str(js), "key": key}
    out.mkdir(parents=True, exist_ok=True)
    print(f"[run] synth {design} {ptag(period)} {vname}")
    rc, secs = run_logged(cmd, out / "yosys.log", src)
    rec = {"ok": rc == 0 and js.exists(), "rc": rc, "seconds": secs, "json": str(js), "key": key,
           "script": pre + script, "yosys": ys_bin, "plugin": str(plugin) if plugin else None, "log": str((out / "yosys.log").relative_to(ROOT)),
           "error": first_error(out / "yosys.log"), "stat": parse_yosys_stat(out / "stat.txt")}
    meta.write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def parse_yosys_stat(p):
    if not p.exists():
        return {}
    cells = {}
    for ln in p.read_text().splitlines():
        m = re.match(r"\s+(\d+)\s+(?:\S+\s+)?(\$?\w+)\s*$", ln)
        if m and not m.group(2).startswith("$"):
            cells[m.group(2)] = cells.get(m.group(2), 0) + int(m.group(1))
    luts = sum(n for c, n in cells.items() if re.fullmatch(r"LUT[1-6]", c))
    ffs = sum(n for c, n in cells.items() if re.fullmatch(r"FD[RSCP]E(_1)?", c))
    lutram = sum(n for c, n in cells.items() if c.startswith("RAM") and not c.startswith("RAMB"))
    srl = sum(n for c, n in cells.items() if c.startswith("SRL"))
    return {"luts": luts, "ffs": ffs, "carry4": cells.get("CARRY4", 0), "lutram_cells": lutram, "srl": srl,
            "ramb36": cells.get("RAMB36E1", 0), "ramb18": cells.get("RAMB18E1", 0), "dsp": cells.get("DSP48E1", 0),
            "muxf7": cells.get("MUXF7", 0), "muxf8": cells.get("MUXF8", 0)}


def nextpnr_cmd(vname):
    binary, chipdb = CONFIG["nextpnr"][variant(vname)["nextpnr"]]
    binary = str(ROOT / binary) if binary else tool("nextpnr-xilinx")
    return [binary] + (["--chipdb", str(chipdb)] if chipdb else [])


def pnr_one(design, period, vname, seed, syn, dry):
    v = variant(vname)
    top = CONFIG["designs"][design]["top"]
    src = CONFIG["out"] / "src" / f"{design}_{ptag(period)}"
    out = CONFIG["out"] / "oxc7" / vname / f"{design}_{ptag(period)}" / f"s{seed}"
    js = Path(syn["json"])
    base = nextpnr_cmd(vname)
    xdc = src / "constraints.xdc"
    if v["xdc_extra"]:
        xdc = CONFIG["out"] / "oxc7" / vname / f"{design}_{ptag(period)}" / "constraints.xdc"
        if not dry:
            xdc.parent.mkdir(parents=True, exist_ok=True)
            xdc.write_text((src / "constraints.xdc").read_text() + v["xdc_extra"])
    args = ["--device", CONFIG["part"], "--json", str(js), "-o", f"xdc={xdc}", "--seed", str(seed),
            "--freq", f"{1000.0 / period:g}", "--timing-allow-fail"] + list(v["args"])
    key = sha(*base, Path(base[0]).stat().st_size, *args, syn["key"])
    st = out / "status.json"
    if st.exists():
        rec = json.loads(st.read_text())
        if rec.get("key") == key and rec.get("pnr", {}).get("ok"):
            return rec
    fasm, frames, bit = out / f"{top}.fasm", out / f"{top}.frames", out / f"{top}.bit"
    cmd = base + args + ["--write", str(out / f"{top}_routed.json"), "-o", f"fasm={fasm}",
                         "--report", str(out / "report.json")]
    if dry:
        print(f"[dry] pnr {design} {ptag(period)} {vname} s{seed}: {' '.join(cmd)}")
        return {"dry": True}
    out.mkdir(parents=True, exist_ok=True)
    print(f"[run] pnr {design} {ptag(period)} {vname} s{seed}", flush=True)
    rec = {"design": design, "period_ns": period, "variant": vname, "seed": seed, "key": key, "cmd": cmd,
           "synth": {k: syn.get(k) for k in ("key", "script", "seconds", "log", "stat")}}
    rc, secs = run_logged(cmd, out / "nextpnr.log", src)
    rec["pnr"] = {"ok": rc == 0 and fasm.exists(), "rc": rc, "seconds": secs,
                  "log": str((out / "nextpnr.log").relative_to(ROOT)), "error": first_error(out / "nextpnr.log")}
    if rec["pnr"]["ok"] and v["bitstream"]:
        dbf = DB / CONFIG["family"]
        rc, s1 = run_logged(["bash", "-c", f"{tool('fasm2frames')} --part {CONFIG['part']} --db-root {dbf} {fasm} > {frames}"],
                            out / "fasm2frames.log", src)
        rc2, s2 = run_logged([tool("xc7frames2bit"), f"--part_file={dbf / CONFIG['part'] / 'part.yaml'}",
                              f"--part_name={CONFIG['part']}", f"--frm_file={frames}", f"--output_file={bit}"],
                             out / "xc7frames2bit.log", src)
        rec["bitstream"] = {"ok": rc == 0 and rc2 == 0 and bit.exists(), "seconds": round(s1 + s2, 2)}
    rec["result"] = parse_nextpnr(out)
    st.write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def parse_nextpnr(out):
    res = {}
    rp = out / "report.json"
    if rp.exists():
        r = json.loads(rp.read_text())
        fm = {k: v for k, v in r.get("fmax", {}).items() if "VCC" not in k and "GND" not in k}
        if fm:
            res["fmax"] = min(v["achieved"] for v in fm.values())
            res["fmax_clocks"] = {k: round(v["achieved"], 2) for k, v in fm.items()}
        u = r.get("utilization", {})
        res["util"] = {k: u[k]["used"] for k in u if u[k]["used"]}
    log = out / "nextpnr.log"
    if log.exists():
        txt = log.read_text(errors="replace")
        m = re.findall(r"Max frequency for clock '([^']+)': ([0-9.]+) MHz", txt)
        if m and "fmax" not in res:
            res["fmax"] = float(m[-1][1])
        res["icap_in_log"] = txt.count("u_icap")
    return res


def pnr(design, period, vname, dry):
    v = variant(vname)
    syn = synth(design, period, vname, dry)
    if not syn.get("ok") and not syn.get("dry"):
        return {"design": design, "period_ns": period, "variant": vname, "synth": syn, "runs": []}
    runs = []
    for s in v["seeds"]:
        runs.append(pnr_one(design, period, vname, s, syn, dry))
        if v["until_met"] and not dry and runs[-1].get("result", {}).get("fmax", 0) >= 1000.0 / period:
            break
    if dry:
        return {"dry": True}
    ok = [r for r in runs if r.get("pnr", {}).get("ok") and r["result"].get("fmax")]
    best = max(ok, key=lambda r: r["result"]["fmax"]) if ok else None
    return {"design": design, "period_ns": period, "variant": vname, "synth": syn, "runs": runs, "best": best,
            "pnr_seconds": round(sum(r["pnr"]["seconds"] for r in runs), 2),
            "bit_seconds": round(sum(r.get("bitstream", {}).get("seconds", 0) for r in runs), 2)}


def parse_vivado(design, period):
    d = CONFIG["vivado_out"] / CONFIG["vivado_tag"] / f"{design}_{ptag(period)}"
    st = d / "status.txt"
    if not st.exists():
        return None
    res = {"dir": str(d), "status": st.read_text().strip().splitlines()[0]}
    times = {}
    if (d / "times.txt").exists():
        for ln in (d / "times.txt").read_text().splitlines():
            k, v = ln.split()
            times[k] = float(v)
    res["times"] = times
    res["seconds"] = round(sum(times.values()), 2)
    tr = (d / "timing.rpt").read_text(errors="replace") if (d / "timing.rpt").exists() else ""
    m = re.search(r"WNS\(ns\).*?\n[- ]+\n\s*(-?[0-9.]+)", tr)
    if m:
        wns = float(m.group(1))
        res["wns"] = wns
        res["fmax"] = round(1000.0 / (period - wns), 2)
    wp = d / "worst_paths.txt"
    if wp.exists():
        sl = []
        for ln in wp.read_text().splitlines():
            p = ln.split()
            if len(p) == 3 and "u_icap" not in p[1] and "u_icap" not in p[2]:
                sl.append(float(p[0]))
        if sl:
            res["fmax_noicap"] = round(1000.0 / (period - min(sl)), 2)
    ur = (d / "util.rpt").read_text(errors="replace") if (d / "util.rpt").exists() else ""

    def cell(label):
        m = re.search(r"^\|\s*" + re.escape(label) + r"\s*\|\s*([0-9.]+)", ur, re.M)
        return float(m.group(1)) if m else None
    res["util"] = {"lut_logic": cell("LUT as Logic"), "lut_mem": cell("LUT as Memory"), "ff": cell("Slice Registers"),
                   "bram": cell("Block RAM Tile"), "dsp": cell("DSPs"), "carry4": cell("CARRY4")}
    return res


def fmt(x, nd=2):
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}" if x != int(x) or nd else f"{int(x)}"
    return str(x)


def row_oxc7(r):
    if not r or not r.get("best"):
        return None
    b = r["best"]
    st = r["synth"].get("stat") or {}
    u = b["result"].get("util", {})
    nseeds = len(r["runs"])
    fm = sorted(x["result"]["fmax"] for x in r["runs"] if x.get("result", {}).get("fmax"))
    med = fm[len(fm) // 2] if len(fm) % 2 else (fm[len(fm) // 2 - 1] + fm[len(fm) // 2]) / 2
    seed = f" (best of {nseeds}, seed {b['seed']}; median {med:.2f}, worst {fm[0]:.2f})" if nseeds > 1 else ""
    rt = round((r["synth"].get("seconds") or 0) + r["pnr_seconds"] + r["bit_seconds"], 1)
    return [f"openXC7 {r['variant']}{seed}", f"{b['result']['fmax']:.2f} (nextpnr)", "-",
            f"{st.get('luts')} / {u.get('SLICE_LUTX', '-')}", st.get("ffs"), st.get("carry4"),
            st.get("ramb36", 0) + st.get("ramb18", 0) / 2, st.get("dsp"), rt]


def row_vivado(v):
    if not v:
        return None
    if not v["status"].endswith("0"):
        return ["Vivado", v["status"], "", "", "", "", "", "", ""]
    u = v["util"]
    return ["Vivado", f"{fmt(v.get('fmax'))} (Vivado)", fmt(v.get("fmax_noicap")),
            f"{fmt(u['lut_logic'], 0)} + {fmt(u['lut_mem'], 0)} mem", fmt(u["ff"], 0), fmt(u["carry4"], 0),
            fmt(u["bram"], 1), fmt(u["dsp"], 0), round(v["seconds"], 1)]


def table(results, designs, periods, vnames):
    hdr = ["flow", "Fmax MHz (timer)", "Vivado Fmax excl. ICAP", "LUTs (yosys / nextpnr bels; Vivado logic + mem)",
           "FF", "CARRY4", "BRAM36", "DSP", "runtime s"]
    lines = []
    for d in designs:
        for p in periods:
            lines.append(f"\n**{d} @ {p:g} ns ({1000.0 / p:.1f} MHz)**\n")
            lines.append("| " + " | ".join(hdr) + " |")
            lines.append("|" + "---|" * len(hdr))
            rows = [row_vivado(parse_vivado(d, p))] + [row_oxc7(results.get((d, p, v))) for v in vnames]
            for r in rows:
                if r:
                    lines.append("| " + " | ".join(fmt(x) if not isinstance(x, str) else x for x in r) + " |")
    return "\n".join(lines) + "\n"


def load_result(design, period, vname):
    v = variant(vname)
    out = CONFIG["out"] / "oxc7" / vname / f"{design}_{ptag(period)}"
    runs = []
    for s in v["seeds"]:
        st = out / f"s{s}" / "status.json"
        if st.exists():
            runs.append(json.loads(st.read_text()))
    if not runs:
        return None
    ok = [r for r in runs if r.get("pnr", {}).get("ok") and r["result"].get("fmax")]
    best = max(ok, key=lambda r: r["result"]["fmax"]) if ok else None
    syn = dict(runs[0]["synth"])
    return {"design": design, "period_ns": period, "variant": vname, "synth": syn, "runs": runs, "best": best,
            "pnr_seconds": round(sum(r["pnr"]["seconds"] for r in runs), 2),
            "bit_seconds": round(sum(r.get("bitstream", {}).get("seconds", 0) for r in runs), 2)}


def write_doc(md, tag):
    doc = CONFIG["doc"]
    begin, end = f"<!-- qor_bench:{tag}:begin -->", f"<!-- qor_bench:{tag}:end -->"
    txt = doc.read_text() if doc.exists() else ""
    block = f"{begin}\n{md}{end}"
    if begin in txt and end in txt:
        txt = txt[:txt.index(begin)] + block + txt[txt.index(end) + len(end):]
    else:
        txt = txt + "\n" + block + "\n"
    doc.write_text(txt)


def main():
    ap = argparse.ArgumentParser(description="openXC7 vs Vivado QoR benchmark, into build/qor")
    ap.add_argument("--designs", nargs="+", default=list(CONFIG["designs"]))
    ap.add_argument("--periods", nargs="+", type=float, default=CONFIG["periods_ns"])
    ap.add_argument("--variants", nargs="+", default=["base"])
    ap.add_argument("--prep", action="store_true", help="only write build/qor/src/<design>_p<ns> (input to vivado/run_qor.ps1)")
    ap.add_argument("--report", action="store_true", help="only build the table from cached results")
    ap.add_argument("--synth-only", action="store_true", help="only run yosys and print the cell counts")
    ap.add_argument("--doc-tag", help="also write the table into docs/qor-vivado.md between qor_bench:<tag> markers")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    for v in a.variants:
        variant(v)
    results = {}
    for d in a.designs:
        for p in a.periods:
            prepare_src(d, p)
            if a.prep:
                continue
            for v in a.variants:
                if a.synth_only:
                    r = synth(d, p, v, dry)
                    print(f"synth {d} {ptag(p)} {v}: {r.get('stat')} {r.get('seconds')} s")
                    continue
                results[(d, p, v)] = load_result(d, p, v) if a.report else pnr(d, p, v, dry)
    if a.prep or a.synth_only or (dry and not a.report):
        print("src: " + " ".join(f"{d}_{ptag(p)}" for d in a.designs for p in a.periods))
        return
    md = table(results, a.designs, a.periods, a.variants)
    CONFIG["out"].mkdir(parents=True, exist_ok=True)
    name = "table_" + "_".join(a.variants) + ".md"
    (CONFIG["out"] / name).write_text(md)
    print(md)
    if a.doc_tag:
        write_doc(md, a.doc_tag)


if __name__ == "__main__":
    main()
