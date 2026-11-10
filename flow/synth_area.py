import argparse
import collections
import contextlib
import hashlib
import io
import json
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
from build_openxc7 import tool

ROOT = qor_bench.ROOT

CONFIG = {
    "out": ROOT / "build" / "qor" / "synarea",
    "vivado_out": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "vivado_tag": "synarea",
    "dry_run": True,
    "timeout_s": 7200,
    "ulimit_kb": 6_000_000,
    "native_period_ns": 5,
    "suite_src": ROOT / "build" / "qor_suite",
    "suite_xdc": "set_property -dict {{ PACKAGE_PIN E3 IOSTANDARD LVCMOS33 }} [get_ports clk]\n"
                 "create_clock -period {period:.3f} [get_ports clk]\n"
                 "set_property -dict {{ PACKAGE_PIN H5 IOSTANDARD LVCMOS33 }} [get_ports dout]\n",
    "litex": {
        "arty_ddr3": {"src": ROOT / "designs" / "ddr3" / "arty_ddr3", "top": "digilent_arty",
                      "plugin": ROOT / "build" / "yosys-plugin" / "clkbufmap_gapfix.so", "clkbuf_pass": "clkbufmap_gapfix"},
    },
    "designs": ["rv_soc", "rv_mul", "rv_big", "bram", "fir", "aes", "sha256", "sha512", "serv", "axi_xbar", "or1200",
                "vtr_sha", "mkpktmerge", "vexriscv", "blob_merge"],
    "icap_re": re.compile(r"u_icap"),
}

NATIVE = ("rv_soc", "rv_mul", "rv_big", "bram", "fir")
SUITE_PERIOD = {"aes": 6, "sha256": 6, "sha512": 8, "serv": 5, "axi_xbar": 5, "or1200": 10, "vtr_sha": 8, "mkpktmerge": 6,
                "vexriscv": 6, "blob_merge": 8, "raygentop": 8, "diffeq2": 10, "bgm": 10}

SX = "synth_xilinx -flatten -abc9 -arch xc7 -top {top}"
DEFAULT_ABC9 = "&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -v; &mfs"
YOSYS_SYNX = "build/yosys-build/yosys-synx/yosys"
FLAT200 = ROOT / "build" / "qor" / "synx" / "lutlib" / "flat200.v"
COARSE = "techmap -map +/cmp2lut.v -map +/cmp2lcu.v -D LUT_WIDTH=6; alumacc; share{share}; opt; memory -nomap; opt_clean"

VARIANTS = {
    "base": {},
    "syn2": {"scratch": ["abc9.xaiger 1"], "lutlib": FLAT200, "W": 450,
             "abc": "&scorr; &sweep; &syn2; &dc2; &dch -f -r; &ps; &if {W} {D} -v; &mfs"},
}


def add(name, **kw):
    VARIANTS[name] = kw


add("c_unit", luts="1,1,1,1,1,1,2,4")
add("c_flat2", luts="1,1,1,2,2,2,4,8")
add("c_l6", luts="1,2,3,3,3,4,8,16")
add("c_l6b", luts="1,2,2,3,3,4,8,16")
add("a_mfse", abc="&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -v; &mfs -e")
add("a_fa", abc="&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -F 3 -A 4 -C 16 -v; &mfs")
add("a_rep", abc="&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -v; &mfs; &st; &dch -f -r; &if {W} {D} -v; &mfs")
add("a_synch2", abc="&scorr; &sweep; &synch2; &if {W} {D} -v; &mfs")
add("a_dch", abc="&scorr; &sweep; &dc2; &dch -r; &ps; &if {W} {D} -v; &mfs")
add("a_satlut", abc="&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -v; &mfs; &satlut")
add("a_R5", abc="&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -R 5 -v; &mfs")
add("a_R10", abc="&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -R 10 -v; &mfs")
add("a_area", abc="&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -a -v; &mfs")
add("hl1", **{"from": "base", "hlut": 1})
add("hl2", **{"from": "base", "hlut": 2})
add("hl3", **{"from": "base", "hlut": 3})
CU = "1,1,1,1,1,1,2,4"
FA = "&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -F 3 -A 4 -C 16 -v; &mfs"
REP = "&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} -v; &mfs; &st; &dch -f -r; &if {W} {D} -v; &mfs"
add("cu_fa", luts=CU, abc=FA)
add("cu_rep", luts=CU, abc=REP)
add("cu_x1", luts=CU, scratch=["abc9.xaiger 1"])
add("cu_syn2", luts=CU, lut_delay=200, W=450, scratch=["abc9.xaiger 1"], abc="&scorr; &sweep; &syn2; &dc2; &dch -f -r; &ps; &if {W} {D} -v; &mfs")
add("cu_cal", luts=CU, lut_delay=200, W=450, scratch=["abc9.xaiger 1"])
add("c_unit8", luts="1,1,1,1,1,1,1,1")
add("c_u6w", luts="1,1,1,1,1,1,3,6")
add("cu_dff", luts=CU, dff=True)
add("cu_hl1", **{"from": "c_unit", "hlut": 1})
add("cu_hl2", **{"from": "c_unit", "hlut": 2})
add("m_lr1", lutram_scale=1)
add("m_lr4", lutram_scale=4)
add("m_lr6", lutram_scale=6)
add("m_lr8", lutram_scale=8)
CMW = "techmap -map +/techmap.v t:$alu r:Y_WIDTH<{n} %i; techmap -map +/techmap.v t:$lcu r:WIDTH<{n} %i; opt_expr; opt_clean"
add("s_cmw5", pre_fine=CMW.format(n=5))
add("s_cmw8", pre_fine=CMW.format(n=8))
add("cu_fa_cmw5", luts=CU, abc=FA, pre_fine=CMW.format(n=5))
PLAIN = "&scorr; &sweep; &ps; &if {W} {D} -v; &mfs"
add("a_plain", abc=PLAIN)
add("cu_plain", luts=CU, abc=PLAIN)
add("noop", remap=True)
add("noop_abc", abc=DEFAULT_ABC9)
add("s_share", share=" -aggressive")
add("s_nowide", flags="-nowidelut")
add("s_dff", dff=True)


CELLS_SIM = ROOT / "toolchain" / "oss-cad-suite" / "share" / "yosys" / "xilinx" / "cells_sim.v"
LUT_MODS = ["LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6", "\\$__ABC9_LUT7", "\\$__ABC9_LUT8"]


def cost_lutlib(costs, delay=None):
    """LUT models of cells_sim.v (LUT1-6 and the abc9 LUT7/LUT8 of MUXF7/F8) with other abc9_lut area costs; the
    delays stay yosys's own unless `delay` (ps, every LUT1-6 input) is given."""
    txt = CELLS_SIM.read_text()
    out = []
    for name, c in zip(LUT_MODS, [int(x) for x in costs.split(",")]):
        m = re.search(r"\(\* abc9_lut=\d+ \*\)\s*\nmodule " + re.escape(name) + r"[ (].*?\nendmodule", txt, re.S)
        blk = re.sub(r"abc9_lut=\d+", f"abc9_lut={c}", m.group(0))
        if delay is not None and name.startswith("LUT"):
            blk = re.sub(r"(\(I\d => O\) = )[^;]+;", lambda mm: f"{mm.group(1)}{delay};", blk)
        out.append(blk)
    body = "\n".join(out) + "\n"
    f = CONFIG["out"] / "lutlib" / f"cost_{sha(body)}.v"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    return f


def design_info(d):
    """(src dir, top, rtl files, xdc text, extra files to copy for Vivado, yosys plugin, clkbuf pass)"""
    if d in NATIVE:
        src = qor_bench.prepare_src(d, CONFIG["native_period_ns"])
        top = qor_bench.CONFIG["designs"][d]["top"]
        return src, top, qor_bench.rtl_files(src), (src / "constraints.xdc").read_text(), sorted(src.glob("*.hex")), None, None
    if d in CONFIG["litex"]:
        lx = CONFIG["litex"][d]
        src, top = lx["src"], lx["top"]
        rtl = [src / f"{top}.v", *sorted(p for p in src.glob("*.v") if p.name != f"{top}.v")]
        return src, top, rtl, (src / f"{top}.xdc").read_text(), sorted(src.glob("*.init")), lx["plugin"], lx["clkbuf_pass"]
    src = CONFIG["suite_src"] / d / "src"
    top = (src / "top.txt").read_text().strip()
    files = [src / f for f in (src / "files.txt").read_text().split()]
    xdc = CONFIG["suite_xdc"].format(period=SUITE_PERIOD.get(d, 10))
    return src, top, files, xdc, sorted(p for p in src.iterdir() if p.suffix in (".hex", ".mif", ".dat")), None, None


def sha(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, bytes) else str(p).encode())
        h.update(b"\0")
    return h.hexdigest()[:16]


def abc_file(txt):
    out = CONFIG["out"] / "abc" / f"abc_{sha(txt)}.abc"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt + "\n")
    return out


MAP_MEMORY = ("memory_libmap -logic-cost-rom 0.015625 -lib {lib} -lib +/xilinx/brams_xc4v.txt -D HAS_SIZE_36 -D HAS_CASCADE "
              "-D HAS_MIXWIDTH_SDP -no-auto-huge; techmap -map +/xilinx/lutrams_xc5v_map.v; techmap -map +/xilinx/brams_xc6v_map.v")


def lutram_lib(scale):
    """lutrams_xc5v.txt with every LUTRAM cost multiplied by `scale` (1 = yosys's own library): memory_libmap then
    prefers block RAM for synchronous-read memories from about 4096/scale bits (RAMB18 cost 129)."""
    txt = (CELLS_SIM.parent / "lutrams_xc5v.txt").read_text()
    txt = re.sub(r"cost (\d+);", lambda m: f"cost {int(m.group(1)) * scale};", txt)
    f = CONFIG["out"] / "lutlib" / f"lutrams_x{scale}.txt"
    if not f.exists() or f.read_text() != txt:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(txt)
    return f


def script(top, v, clkbuf_pass=None):
    sx = SX.format(top=top) + (f" {v['flags']}" if v.get("flags") else "")
    pre = "".join(f"scratchpad -set {s}; " for s in v.get("scratch", []))
    custom_map = any(v.get(k) for k in ("luts", "lutlib", "W", "abc", "dff", "post", "remap"))
    parts = []
    start = "begin"
    if v.get("prep_extra"):
        parts.append(f"{sx} -run :prepare; {v['prep_extra']}")
        start = "map_dsp"
    if v.get("share"):
        parts.append(f"{sx} -run {start}:coarse; {COARSE.format(share=v['share'])}")
        start = "map_memory"
    if v.get("lutram_scale"):
        parts.append(f"{sx} -run {start}:map_memory; " + MAP_MEMORY.format(lib=lutram_lib(v["lutram_scale"])))
        start = "map_ffram"
    if v.get("pre_fine"):
        parts.append(f"{sx} -run {start}:fine; {v['pre_fine']}")
        start = "fine"
    if custom_map:
        parts.append(f"{sx} -run {start}:map_luts")
        cmds = ["opt_expr -mux_undef -noclkinv", "read_verilog -icells -lib -specify +/xilinx/abc9_model.v"]
        lib = v.get("lutlib") or (cost_lutlib(v["luts"], v.get("lut_delay")) if v.get("luts") else None)
        if lib:
            cmds.append(f"read_verilog -lib -specify -overwrite {lib}")
        if v.get("abc"):
            cmds.append(f"scratchpad -set abc9.script {abc_file(v['abc'].replace('{W}', '-W ' + str(v.get('W') or 300)).replace('{D}', ''))}")
        a9 = f"abc9 -W {v.get('W') or 300}" + (" -dff" if v.get("dff") else "")
        cmds += [a9, "clean", "xilinx_srl -fixed -minlen 3", "techmap -map +/xilinx/lut_map.v -map +/xilinx/cells_map.v -D LUT_WIDTH=6",
                 "xilinx_dffopt", "opt_lut_ins -tech xilinx"]
        if v.get("post"):
            cmds.append(v["post"])
        parts.append("; ".join(cmds))
        start = "finalize"
    if clkbuf_pass:
        parts += [f"{sx} -run {start}:finalize", f"{clkbuf_pass} -buf BUFG O:I; clean", f"{sx} -run check:"]
    else:
        parts.append(f"{sx} -run {start}:" if start != "begin" else sx)
    return pre + "; ".join(parts)


def count_cells(js):
    j = json.loads(Path(js).read_text())
    tops = [m for m in j["modules"].values() if m.get("attributes", {}).get("top")]
    m = tops[0] if tops else next(iter(j["modules"].values()))
    c = collections.Counter(x["type"] for x in m["cells"].values())
    lut = sum(n for t, n in c.items() if re.fullmatch(r"LUT[1-6]", t)) + c.get("INV", 0)
    lutram_sites = {"RAM32M": 4, "RAM64M": 4, "RAM32X1D": 2, "RAM64X1D": 2, "RAM128X1D": 4, "RAM256X1S": 4, "RAM32X1S": 1,
                    "RAM64X1S": 1, "RAM128X1S": 2}
    return {"lut": lut, "lut_by_k": {t: c[t] for t in sorted(c) if re.fullmatch(r"LUT[1-6]|INV", t)},
            "ff": sum(n for t, n in c.items() if re.fullmatch(r"FD[RSCP]E(_1)?", t)),
            "lutram_sites": sum(n * lutram_sites.get(t, 0) for t, n in c.items()),
            "lutram_cells": sum(n for t, n in c.items() if t in lutram_sites),
            "srl": sum(n for t, n in c.items() if t.startswith("SRL")),
            "carry4": c.get("CARRY4", 0), "muxf7": c.get("MUXF7", 0), "muxf8": c.get("MUXF8", 0),
            "ramb36": c.get("RAMB36E1", 0), "ramb18": c.get("RAMB18E1", 0), "dsp": c.get("DSP48E1", 0)}


PAIR_VERSION = 1


def pair_luts(js_in, js_out, min_share, max_fanout_net=64):
    """LUT combining hints: greedy pairs of LUTs (INV counts as a LUT1) with at most 5 inputs each and at most 5
    distinct inputs together (one LUT6_2 site, O6 + O5), sharing at least `min_share` input nets; most shared inputs
    first, then the smallest union. Each pair gets the parameter SOFT_HLUTNM = "ofx_lutpair<N>" (written to EDIF as a
    property). LUTs that drive a MUXF7/MUXF8 input are left alone (they need the O6 output). The netlist logic is
    unchanged."""
    j = json.loads(Path(js_in).read_text())
    tops = [m for m in j["modules"].values() if m.get("attributes", {}).get("top")]
    m = tops[0] if tops else next(iter(j["modules"].values()))
    muxin = set()
    for c in m["cells"].values():
        if c["type"] in ("MUXF7", "MUXF8"):
            for p in ("I0", "I1"):
                muxin |= {x for x in c["connections"].get(p, []) if isinstance(x, int)}
    ins, outs = {}, {}
    for n, c in m["cells"].items():
        t = c["type"]
        if not (re.fullmatch(r"LUT[1-6]", t) or t == "INV"):
            continue
        o = [x for x in c["connections"].get("O", []) if isinstance(x, int)]
        if not o or o[0] in muxin:
            continue
        s = frozenset(x for p, b in c["connections"].items() if p != "O" for x in b if isinstance(x, int))
        if len(s) <= 5:
            ins[n] = s
    by_net = collections.defaultdict(list)
    for n, s in ins.items():
        for x in s:
            by_net[x].append(n)
    cands = set()
    for ns in by_net.values():
        if len(ns) > max_fanout_net:
            continue
        for i in range(len(ns)):
            for k in range(i + 1, len(ns)):
                a, b = sorted((ns[i], ns[k]))
                sh = len(ins[a] & ins[b])
                u = len(ins[a] | ins[b])
                if u <= 5 and sh >= min_share:
                    cands.add((-sh, u, a, b))
    used, npair = set(), 0
    for _, _, a, b in sorted(cands):
        if a in used or b in used:
            continue
        used |= {a, b}
        npair += 1
        for n in (a, b):
            m["cells"][n].setdefault("parameters", {})["SOFT_HLUTNM"] = f"ofx_lutpair{npair}"
    Path(js_out).write_text(json.dumps(j))
    return {"pairs": npair, "candidates": len(ins)}


def synth_derived(d, vname, dry, force):
    v = VARIANTS[vname]
    base = synth(d, v["from"], dry)
    if dry or not base.get("ok"):
        return base
    key = sha(base["key"], json.dumps({k: v[k] for k in sorted(v) if k != "from"}, default=str), PAIR_VERSION)
    out = CONFIG["out"] / "synth" / d / f"{vname}_{key}"
    meta = out / "meta.json"
    if meta.exists() and not force and json.loads(meta.read_text()).get("ok"):
        return json.loads(meta.read_text())
    out.mkdir(parents=True, exist_ok=True)
    js = out / Path(base["json"]).name
    t0 = time.time()
    info = pair_luts(base["json"], js, v["hlut"])
    rec = dict(base, json=str(js), key=key, variant=vname, seconds=round(base["seconds"] + time.time() - t0, 2),
               pairing=info)
    meta.write_text(json.dumps(rec, indent=1) + "\n")
    return rec


def synth(d, vname, dry, force=False):
    v = VARIANTS[vname]
    if v.get("from"):
        return synth_derived(d, vname, dry, force)
    src, top, rtl, _, _, plugin, clkbuf = design_info(d)
    scr = script(top, v, clkbuf)
    ys_bin = str(ROOT / v["yosys"]) if v.get("yosys") else tool("yosys")
    extra = [Path(v["lutlib"]).read_text()] if v.get("lutlib") else []
    key = sha(ys_bin, Path(ys_bin).stat().st_size, scr, *extra, *[f.name + sha(f.read_bytes()) for f in rtl],
              *([sha(Path(plugin).read_bytes())] if plugin else []))
    out = CONFIG["out"] / "synth" / d / f"{vname}_{key}"
    js = out / f"{top}.json"
    meta = out / "meta.json"
    if meta.exists() and not force:
        rec = json.loads(meta.read_text())
        if rec.get("ok"):
            return rec
    files = " ".join(f.name if d not in CONFIG["litex"] else str(f) for f in rtl)
    ys = f"read_verilog -sv {files}; {scr}; tee -o {out / 'stat.txt'} stat -tech xilinx; write_json {js}"
    cmd = [ys_bin] + (["-m", str(plugin)] if plugin else []) + ["-p", ys]
    if dry:
        print(f"[dry] synth {d} {vname} -> {out.relative_to(ROOT)}: {scr}")
        return {"ok": None, "json": str(js), "key": key}
    out.mkdir(parents=True, exist_ok=True)
    shell = f"ulimit -v {CONFIG['ulimit_kb']}; exec " + " ".join(_q(c) for c in cmd)
    cwd = ROOT if d in CONFIG["litex"] else src
    t0 = time.time()
    with open(out / "yosys.log", "w") as f:
        try:
            rc = subprocess.run(["bash", "-c", shell], stdout=f, stderr=subprocess.STDOUT, cwd=cwd, timeout=CONFIG["timeout_s"]).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    secs = round(time.time() - t0, 2)
    ok = rc == 0 and js.exists()
    rec = {"ok": ok, "rc": rc, "seconds": secs, "json": str(js), "key": key, "variant": vname, "design": d, "script": scr,
           "yosys": ys_bin, "log": str((out / "yosys.log").relative_to(ROOT)),
           "load1": round(float(Path("/proc/loadavg").read_text().split()[0]), 2),
           "cells": count_cells(js) if ok else None}
    meta.write_text(json.dumps(rec, indent=1) + "\n")
    return rec


def _q(s):
    return "'" + str(s).replace("'", "'\\''") + "'"


def vname_dir(d, vname):
    return f"{d}_{vname}"


def vivado_prep(d, vname, dry):
    """Source dir for vivado/build_synx.tcl: netlist.edf (or the RTL for vname 'viv'), constraints.xdc, top.txt,
    mode.txt, directives.txt = Default."""
    src, top, rtl, xdc, extra, _, _ = design_info(d)
    dst = CONFIG["out"] / "src" / vname_dir(d, vname)
    if dry:
        print(f"[dry] vivado src {dst.relative_to(ROOT)}")
        return dst.name
    dst.mkdir(parents=True, exist_ok=True)
    if vname == "viv":
        for f in rtl + extra:
            shutil.copyfile(f, dst / f.name)
        (dst / "mode.txt").write_text("rtl\n")
    else:
        rec = synth(d, vname, False)
        if not rec.get("ok"):
            print(f"{d} {vname}: synthesis failed ({rec.get('log')})")
            return None
        edf = dst / "netlist.edf"
        if (dst / "key.txt").exists() and (dst / "key.txt").read_text().strip() != rec["key"]:
            edf.unlink(missing_ok=True)
        if not edf.exists():
            subprocess.run([tool("yosys"), "-q", "-p", f"read_json {rec['json']}; delete t:$scopeinfo; write_edif -pvector bra {edf}"],
                           check=True)
        (dst / "key.txt").write_text(rec["key"] + "\n")
        for f in extra:
            shutil.copyfile(f, dst / f.name)
        (dst / "mode.txt").write_text("edif\n")
    (dst / "constraints.xdc").write_text(xdc)
    (dst / "top.txt").write_text(top + "\n")
    (dst / "directives.txt").write_text("Default\n")
    return dst.name


def read_paths(p):
    rows = []
    if not p.exists():
        return rows
    for ln in p.read_text().splitlines():
        f = ln.split()
        if len(f) < 13:
            continue
        num = lambda x: float(x) if x not in ("-", "") else None
        rows.append({"slack": num(f[0]), "req": num(f[1]), "levels": int(f[2]), "sclk": f[9], "eclk": f[10], "start": f[11], "end": f[12]})
    return rows


def vivado_fmax(rows):
    cnt = collections.Counter(r["eclk"] for r in rows if r["sclk"] == r["eclk"])
    if not cnt:
        return None, None
    clk = cnt.most_common(1)[0][0]
    intra = [r for r in rows if r["sclk"] == clk and r["eclk"] == clk and r["slack"] is not None]
    noicap = [r for r in intra if not CONFIG["icap_re"].search(r["end"]) and not CONFIG["icap_re"].search(r["start"])]
    w = noicap[0] if noicap else (intra[0] if intra else None)
    return (round(1000.0 / (w["req"] - w["slack"]), 2), w["levels"]) if w else (None, None)


def util(p):
    if not p.exists():
        return {}
    t = p.read_text(errors="replace")
    out = {}
    for key, pat in (("lut_sites", r"\|\s*Slice LUTs\*?\s*\|\s*(\d+)"), ("lutram_sites", r"\|\s*LUT as Memory\s*\|\s*(\d+)"),
                     ("ff", r"\|\s*Slice Registers\s*\|\s*(\d+)"), ("carry4", r"\|\s*CARRY4\s*\|\s*(\d+)"),
                     ("slices", r"\|\s*Slice\s*\|\s*(\d+)"), ("bram_tiles", r"\|\s*Block RAM Tile\s*\|\s*([\d.]+)"),
                     ("o5o6", r"using O5 and O6\s*\|\s*(\d+)")):
        m = re.search(pat, t)
        if m:
            out[key] = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
    return out


def vivado_result(d, vname):
    base = CONFIG["vivado_out"] / CONFIG["vivado_tag"] / vname_dir(d, vname)
    st = (base / "status.txt").read_text().split("\n")[0] if (base / "status.txt").exists() else None
    if st != "rc 0":
        return {"status": st}
    fm, lv = vivado_fmax(read_paths(base / "Default" / "paths.txt"))
    times = {}
    if (base / "times.txt").exists():
        for ln in (base / "times.txt").read_text().splitlines():
            k, s = ln.split()
            times[k] = float(s)
    return {"status": st, "fmax": fm, "levels": lv, "util": util(base / "Default" / "util.rpt"),
            "synth_util": util(base / "synth_util.rpt"), "times": times}


def cmd_synth(a, dry):
    for d in a.designs:
        for v in a.variants:
            r = synth(d, v, dry, a.force)
            c = r.get("cells") or {}
            if not dry:
                print(f"{d:11s} {v:10s} ok={r.get('ok')} s={r.get('seconds')} lut={c.get('lut')} ff={c.get('ff')} "
                      f"lutram={c.get('lutram_sites')} srl={c.get('srl')} c4={c.get('carry4')} f7={c.get('muxf7')} f8={c.get('muxf8')} "
                      f"bram={c.get('ramb36')}/{c.get('ramb18')} dsp={c.get('dsp')} k={c.get('lut_by_k')}", flush=True)


def cmd_table(a):
    rows = []
    for d in a.designs:
        base = synth(d, "base", True)
        bc = json.loads((Path(base["json"]).parent / "meta.json").read_text())["cells"] if (Path(base["json"]).parent / "meta.json").exists() else None
        for v in a.variants:
            r = synth(d, v, True)
            m = Path(r["json"]).parent / "meta.json"
            if not m.exists():
                continue
            rec = json.loads(m.read_text())
            c = rec.get("cells") or {}
            rel = f"{100.0 * (c['lut'] - bc['lut']) / bc['lut']:+.1f}%" if bc and c else "-"
            rows.append((d, v, c.get("lut"), rel, c.get("ff"), c.get("lutram_sites"), c.get("carry4"), c.get("muxf7"), rec.get("seconds")))
    print("| design | variant | LUT | vs base | FF | LUTRAM sites | CARRY4 | MUXF7 | yosys s |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")
    if a.summary:
        tot = collections.defaultdict(list)
        for d, v, lut, rel, *_ in rows:
            if rel != "-":
                tot[v].append(float(rel.rstrip("%")))
        for v, xs in tot.items():
            print(f"{v:12s} n={len(xs)} mean {statistics.mean(xs):+.2f}% median {statistics.median(xs):+.2f}% min {min(xs):+.1f} max {max(xs):+.1f}")


def cmd_report(a):
    res = {}
    print("| design | netlist | LUT sites | LUTRAM sites | FF | CARRY4 | slices | Fmax MHz (Vivado timer) | levels | synth s |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for d in a.designs:
        for v in a.variants:
            r = vivado_result(d, v)
            if v != "viv":
                m = Path(synth(d, v, True)["json"]).parent / "meta.json"
                r["yosys_s"] = json.loads(m.read_text()).get("seconds") if m.exists() else None
            res[f"{d}/{v}"] = r
            u = r.get("util", {})
            ss = r.get("times", {}).get("synth") if v == "viv" else r.get("yosys_s")
            print(f"| {d} | {v} | {u.get('lut_sites', r.get('status'))} | {u.get('lutram_sites')} | {u.get('ff')} | {u.get('carry4')} | "
                  f"{u.get('slices')} | {r.get('fmax')} | {r.get('levels')} | {ss} |")
    out = CONFIG["out"] / "report.json"
    old = json.loads(out.read_text()) if out.exists() else {}
    old.update(res)
    out.write_text(json.dumps(old, indent=1) + "\n")


def cmd_equiv(a, dry):
    """Each variant against the base netlist of the same design: lockstep firmware simulation (rv_soc, rv_mul, rv_big;
    flow/qor_area_sim.sh) and, for the others, yosys equiv_struct/induct and a sequential miter proved by ABC dprove
    (flow/synth_timing_equiv.py). Hard blocks (BRAM, DSP, LUTRAM) are cut as free inputs/outputs in the formal checks."""
    import synth_timing_equiv as ste
    ste.CONFIG["out"] = CONFIG["out"] / "equiv"
    resf = CONFIG["out"] / "equiv" / "results.json"
    res = json.loads(resf.read_text()) if resf.exists() else {}
    for d in a.designs:
        ref = synth(d, "base", dry)
        for v in a.variants:
            r = synth(d, v, dry)
            out = CONFIG["out"] / "equiv" / d / f"{v}_{r.get('key')}"
            if dry:
                print(f"[dry] {d} {v}: {ref['json']} vs {r['json']}")
                continue
            out.mkdir(parents=True, exist_ok=True)
            rec = {"gold": ref["json"], "gate": r["json"], "key": r["key"]}
            if d in ste.CONFIG["sim_designs"]:
                rec["sim"] = ste.check_sim(d, out, ref["json"], r["json"])
            else:
                gold = ste.prep_side(ref["json"], "gold", out)
                gate = ste.prep_side(r["json"], "gate", out)
                if "struct" in a.checks:
                    rec["struct"] = ste.check_struct(out, gold, gate)
                if "seq" in a.checks:
                    rec["seq"] = ste.check_seq(out, gold, gate)
            res[f"{d}/{v}"] = rec
            print(d, v, json.dumps({k: rec.get(k) for k in ("sim", "struct", "seq") if k in rec}), flush=True)
            resf.parent.mkdir(parents=True, exist_ok=True)
            resf.write_text(json.dumps(res, indent=1) + "\n")


def cmd_vprep(a, dry):
    names = [n for d in a.designs for v in a.variants if (n := vivado_prep(d, v, dry))]
    print("names: " + " ".join(names))
    print(f"run: bash vivado/slot_run.sh {CONFIG['vivado_tag']} build_synx.tcl build/qor/synarea/src {' '.join(names)}")


VREF_PAT = {"lut_sites": r"\|\s*LUT as Logic\s*\|\s*(\d+)", "lut_mem": r"\|\s*LUT as Memory\s*\|\s*(\d+)",
            "ff": r"\|\s*Slice Registers\s*\|\s*(\d+)", "f7": r"\|\s*F7 Muxes\s*\|\s*(\d+)",
            "ramb36": r"\|\s*RAMB36/FIFO\*?\s*\|\s*(\d+)", "ramb18": r"\|\s*RAMB18\s*\|\s*(\d+)", "dsp": r"\|\s*DSPs\s*\|\s*(\d+)"}
VREF_SRC = [("synth", "qor_synx/{d}_viv/synth_util.rpt"), ("route", "qor_synx/{d}_viv/Default/util.rpt"),
            ("route", "qor_suite/{d}__free/run0/util.rpt")]


def vivado_ref(d):
    """Vivado synth_design reference of design d from report_utilization of an existing run, no new Vivado run.
    lut = LUT1-6 cells of the Primitives table (cells, like the yosys count; 'LUT as Logic' is sites after LUT
    combining once the design is placed)."""
    for stage, rel in VREF_SRC:
        p = CONFIG["vivado_out"] / rel.format(d=d)
        if not p.exists():
            continue
        t = p.read_text(errors="replace")
        out = {"stage": stage, "src": rel.format(d=d)}
        for k, pat in VREF_PAT.items():
            m = re.search(pat, t)
            out[k] = int(m.group(1)) if m else None
        prim = {m.group(1): int(m.group(2)) for m in re.finditer(r"\|\s*(LUT[1-6]|CARRY4|MUXF7|MUXF8)\s*\|\s*(\d+)\s*\|", t)}
        out["lut"] = sum(n for k, n in prim.items() if k.startswith("LUT"))
        out["carry4"] = prim.get("CARRY4", 0)
        out["lut_by_k"] = {k: n for k, n in sorted(prim.items()) if k.startswith("LUT")}
        return out
    return None


def cmd_compare(a):
    """LUT cells (LUT1-6 + INV for yosys, LUT1-6 primitives for Vivado) per design and variant against Vivado's
    synth_design; also FF, CARRY4, MUXF7 of Vivado / base / each variant."""
    print("| design | Vivado LUT (stage) | " + " | ".join(f"{v} LUT (vs Vivado)" for v in a.variants)
          + " | FF V / " + " / ".join(a.variants) + " | CARRY4 V / " + " / ".join(a.variants) + " | MUXF7 V / " + " / ".join(a.variants) + " |")
    print("|---" * (5 + len(a.variants)) + "|")
    ratios = collections.defaultdict(list)
    res = {}
    for d in a.designs:
        ref = vivado_ref(d)
        cs = []
        for v in a.variants:
            with contextlib.redirect_stdout(io.StringIO()):
                m = Path(synth(d, v, True)["json"]).parent / "meta.json"
            cs.append((json.loads(m.read_text()).get("cells") if m.exists() else None) or {})
        res[d] = {"vivado": ref, **{v: c for v, c in zip(a.variants, cs)}}
        cols = []
        for v, c in zip(a.variants, cs):
            if c and ref and ref["lut"]:
                ratios[v].append((d, c["lut"] / ref["lut"]))
                cols.append(f"{c['lut']} ({100.0 * (c['lut'] - ref['lut']) / ref['lut']:+.1f}%)")
            else:
                cols.append(str(c.get("lut", "-")))
        trio = lambda k, rk: " / ".join(str(x) for x in [ref.get(rk) if ref else "-"] + [c.get(k, "-") for c in cs])
        print(f"| {d} | {ref['lut'] if ref else '-'} ({ref['stage'] if ref else '-'}) | " + " | ".join(cols)
              + f" | {trio('ff', 'ff')} | {trio('carry4', 'carry4')} | {trio('muxf7', 'f7')} |")
    common = set.intersection(*[{d for d, _ in ratios[v]} for v in a.variants]) - set(a.exclude) if ratios else set()
    for v in a.variants:
        xs = [r for d, r in ratios[v] if d in common]
        if xs:
            gm = statistics.geometric_mean(xs)
            print(f"{v}: LUT cells vs Vivado, geometric mean over {len(xs)} designs ({' '.join(sorted(common))}): {100.0 * (gm - 1):+.1f}%")
    (CONFIG["out"] / "compare.json").write_text(json.dumps(res, indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser(description="yosys synthesis area variants vs default and Vivado (docs/wip/synthesis-area.md)")
    ap.add_argument("cmd", choices=["synth", "table", "vivado-prep", "report", "script", "equiv", "compare"])
    ap.add_argument("--exclude", nargs="*", default=[], help="compare: designs left out of the geometric mean")
    ap.add_argument("--checks", nargs="+", default=["struct", "seq"])
    ap.add_argument("--designs", nargs="+", default=CONFIG["designs"])
    ap.add_argument("--variants", nargs="+", default=["base"])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    if a.cmd == "synth":
        cmd_synth(a, dry)
    elif a.cmd == "table":
        cmd_table(a)
    elif a.cmd == "vivado-prep":
        cmd_vprep(a, dry)
    elif a.cmd == "report":
        cmd_report(a)
    elif a.cmd == "equiv":
        cmd_equiv(a, dry)
    elif a.cmd == "compare":
        cmd_compare(a)
    elif a.cmd == "script":
        for d in a.designs:
            for v in a.variants:
                _, top, _, _, _, _, clk = design_info(d)
                print(f"{d} {v}: {script(top, VARIANTS[v], clk)}")


if __name__ == "__main__":
    main()
