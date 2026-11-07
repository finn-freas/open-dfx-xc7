import json
import re
from pathlib import Path

from . import ROOT

SYNTH = "synth_xilinx -flatten -abc9 -arch xc7 -top {top}"
MAP_DSP_XC7 = ("memory_dff; alumacc -macc-only; maccmap -unmap; opt_clean; techmap -map +/mul2dsp.v -map +/xilinx/xc7_dsp_map.v "
               "-D DSP_A_MAXWIDTH=25 -D DSP_B_MAXWIDTH=18 -D DSP_A_MAXWIDTH_PARTIAL=18 -D DSP_A_MINWIDTH=2 -D DSP_B_MINWIDTH=2 "
               "-D DSP_Y_MINWIDTH=9 -D DSP_SIGNEDONLY=1 -D DSP_NAME=$__MUL25X18; select a:mul2dsp; setattr -unset mul2dsp; "
               "opt_expr -fine; wreduce; select -clear; xilinx_dsp_qor -family xc7 -pipeline; chtype -set $mul t:$__soft_mul")

CONFIG = {
    "toolchain": ROOT / "toolchain" / "openxc7",
    "release_file": "share/ofx/VERSION",
    "plugins": "share/ofx/yosys-plugins",
    "cal_chipdb": "share/nextpnr/himbaechel/xilinx/cal/chipdb-{fabric}.bin",
    "ofx_chipdb": "share/nextpnr/himbaechel/xilinx/ofx/chipdb-{fabric}.bin",
    "cal_parts": r"^xc7a35t\w*-1$",
    "static_max_cells": None,
    "defaults": {
        "hardblock_timing": True,
        "dsp_cascade": True,
        "dsp_pipeline": False,
        "async_reg": True,
        "clkbuf_keep_buffer_inputs": False,
        "cell_timing": "stub",
        "placer": "auto",
    },
    "all_off": {
        "hardblock_timing": False,
        "dsp_cascade": False,
        "dsp_pipeline": False,
        "async_reg": False,
        "clkbuf_keep_buffer_inputs": False,
        "cell_timing": "stub",
        "placer": "heap",
    },
    "choices": {"cell_timing": ("auto", "stub"), "placer": ("auto", "static", "heap")},
    "xadc_cell": "XADC",
}


class DefaultsError(Exception):
    pass


def release(toolchain=None):
    f = Path(toolchain or CONFIG["toolchain"]) / CONFIG["release_file"]
    return f.read_text().strip() if f.exists() else None


def options(raw):
    opts = dict(CONFIG["defaults"])
    for k, v in (raw or {}).items():
        if k not in opts:
            raise DefaultsError(f"[build] unknown key {k!r}; known: {sorted(opts)}")
        if k in CONFIG["choices"]:
            if v not in CONFIG["choices"][k]:
                raise DefaultsError(f"[build] {k} must be one of {CONFIG['choices'][k]}, not {v!r}")
        elif not isinstance(v, bool):
            raise DefaultsError(f"[build] {k} must be true or false, not {v!r}")
        opts[k] = v
    return opts


def synth_script(opts, xdc, plugins):
    loads = []
    parts = []
    start = "begin"
    if opts["async_reg"] or opts["dsp_pipeline"]:
        parts.append(f"{SYNTH} -run begin:map_dsp")
        start = "map_dsp"
        if opts["async_reg"]:
            loads.append(plugins / "xilinx_asyncreg.so")
            parts.append(f"xilinx_asyncreg -xdc {xdc}")
        if opts["dsp_pipeline"]:
            loads.append(plugins / "xilinx_dsp_qor.so")
            parts.append(MAP_DSP_XC7)
            start = "coarse"
    if opts["clkbuf_keep_buffer_inputs"]:
        loads.append(plugins / "clkbufmap_gapfix.so")
        parts += [f"{SYNTH} -run {start}:finalize", "clkbufmap_gapfix -buf BUFG O:I; clean"]
        start = "check"
    if not parts:
        return None, []
    parts.append(f"{SYNTH} -run {start}:")
    return "; ".join([f"plugin -i {p}" for p in loads] + parts), loads


def nextpnr_args(opts):
    args = []
    if opts["hardblock_timing"]:
        args += ["-o", "hardblock-timing"]
    if opts["dsp_cascade"]:
        args += ["-o", "dsp-cascade-place"]
    return args


def plan(proj, xdc, toolchain=None):
    tc = Path(toolchain or CONFIG["toolchain"])
    rel = release(tc)
    opts = options(proj.build_opts)
    out = {"release": rel, "options": opts, "synth": None, "nextpnr_args": [], "chipdb": None, "xadc_chipdb": None,
           "placer": None, "notes": []}
    if rel is None:
        out["notes"].append(f"{tc} is not an ofx release install ({CONFIG['release_file']} missing): the release "
                            f"defaults are off and the build is the plain openXC7 flow")
        return out
    synth, loads = synth_script(opts, xdc, tc / CONFIG["plugins"])
    missing = [str(p) for p in loads if not p.exists()]
    if missing:
        raise DefaultsError(f"yosys plugins missing in the toolchain: {missing}")
    out["synth"] = synth
    out["nextpnr_args"] = nextpnr_args(opts)
    cal = tc / CONFIG["cal_chipdb"].format(fabric=proj.device["fabric"])
    ofx_db = tc / CONFIG["ofx_chipdb"].format(fabric=proj.device["fabric"])
    if opts["cell_timing"] == "auto" and re.match(CONFIG["cal_parts"], proj.part) and cal.exists():
        out["chipdb"] = str(cal)
    else:
        if opts["cell_timing"] == "auto":
            out["notes"].append(f"no calibrated cell timing for {proj.part} (measured for xc7a35t-1 only); stub cell timing")
        if ofx_db.exists():
            out["xadc_chipdb"] = str(ofx_db)
    out["placer"] = opts["placer"]
    return out


def needs_netlist(p):
    return p["placer"] == "auto" or bool(p["xadc_chipdb"])


def netlist_info(json_file, top):
    j = json.loads(Path(json_file).read_text())
    cells = j["modules"][top]["cells"]
    return {"cells": len(cells), "types": sorted({c["type"] for c in cells.values()})}


def placer_args(p, cells=None):
    choice = p["placer"]
    if choice == "auto":
        limit = CONFIG["static_max_cells"]
        if limit is None:
            return ["--placer", "static"], "placer: static (auto: static at every size)"
        if cells is None:
            return None, "placer: auto (static up to %d cells, else heap; decided after synthesis)" % limit
        choice = "static" if cells <= limit else "heap"
        why = f"placer: {choice} ({cells} cells, static up to {limit})"
    else:
        why = f"placer: {choice} (set in [build])"
    return (["--placer", "static"] if choice == "static" else []), why


def chipdb_choice(p, types=None):
    if p["chipdb"]:
        return p["chipdb"], f"chipdb: {p['chipdb']} (calibrated cell timing)"
    if not p["xadc_chipdb"]:
        return None, "chipdb: the default one"
    if types is None:
        return None, "chipdb: the default one, or the XADC one if the netlist has an XADC (decided after synthesis)"
    if CONFIG["xadc_cell"] in types:
        return p["xadc_chipdb"], f"chipdb: {p['xadc_chipdb']} (the netlist has an XADC)"
    return None, "chipdb: the default one (no XADC in the netlist)"


def decide(p, net=None):
    pargs, pwhy = placer_args(p, net["cells"] if net else None)
    chipdb, cwhy = chipdb_choice(p, net["types"] if net else None)
    return {"nextpnr_args": pargs or [], "chipdb": chipdb, "why": [pwhy, cwhy]}
