import json
import re
from pathlib import Path

from . import ROOT

SYNTH = "synth_xilinx -flatten -abc9 -arch xc7 -top {top}"
MAP_DSP_XC7 = ("memory_dff; alumacc -macc-only; maccmap -unmap; opt_clean; techmap -map +/mul2dsp.v -map +/xilinx/xc7_dsp_map.v "
               "-D DSP_A_MAXWIDTH=25 -D DSP_B_MAXWIDTH=18 -D DSP_A_MAXWIDTH_PARTIAL=18 -D DSP_A_MINWIDTH=2 -D DSP_B_MINWIDTH=2 "
               "-D DSP_Y_MINWIDTH=9 -D DSP_SIGNEDONLY=1 -D DSP_NAME=$__MUL25X18; select a:mul2dsp; setattr -unset mul2dsp; "
               "opt_expr -fine; wreduce; select -clear; {xilinx_dsp}; chtype -set $mul t:$__soft_mul")

CONFIG = {
    "toolchain": ROOT / "toolchain" / "openxc7",
    "release_file": "share/ofx/VERSION",
    "plugins": "share/ofx/yosys-plugins",
    "cal_chipdb": "share/nextpnr/himbaechel/xilinx/cal/chipdb-{fabric}.bin",
    "ofx_chipdb": "share/nextpnr/himbaechel/xilinx/ofx/chipdb-{fabric}.bin",
    "tuned_chipdb": "share/nextpnr/himbaechel/xilinx/tuned/chipdb-{fabric}.bin",
    "cal_parts": r"^xc7a35t\w*-1$",
    "placer_tuning_args": ["--placer-static-anchor-init", "20", "--placer-static-ip-wait", "0.5",
                           "--placer-static-target-util", "1.0",
                           "-o", "sa-refine=t0=0.01:quant=0.002:exp=8:rmin=3:pcent=0.6:site=750:tile=850:alpha=313:beta=1.235",
                           "-o", "lut-a6-perm", "-o", "lut6-first", "-o", "static-delay=816,40,40,18,18"],
    "static_max_cells": None,
    "defaults": {
        "hardblock_timing": True,
        "dsp_cascade": True,
        "dsp_pipeline": False,
        "dsp_init": True,
        "async_reg": True,
        "clkbuf_keep_buffer_inputs": True,
        "carry_di_bypass": False,
        "cell_timing": "stub",
        "placer": "auto",
        "placer_tuning": True,
    },
    "all_off": {
        "hardblock_timing": False,
        "dsp_cascade": False,
        "dsp_pipeline": False,
        "dsp_init": False,
        "async_reg": False,
        "clkbuf_keep_buffer_inputs": False,
        "carry_di_bypass": False,
        "cell_timing": "stub",
        "placer": "heap",
        "placer_tuning": False,
    },
    "choices": {"cell_timing": ("auto", "stub"), "placer": ("auto", "static", "heap")},
    "xadc_cell": "XADC",
    "default_plugins": {"dsp_init": "xilinx_dsp_init.so", "clkbuf_keep_buffer_inputs": "clkbufmap_gapfix.stock-names"},
    "default_nextpnr_options": {"carry_di_bypass": b"carry-di-bypass",
                                "placer_tuning": (b"placer-static-anchor-init", b"sa-refine", b"lut-a6-perm",
                                                  b"lut6-first", b"static-delay")},
    "nextpnr_bin": "bin/nextpnr-himbaechel",
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
    if opts["async_reg"] or opts["dsp_pipeline"] or opts["dsp_init"]:
        parts.append(f"{SYNTH} -run begin:map_dsp")
        start = "map_dsp"
        if opts["async_reg"]:
            loads.append(plugins / "xilinx_asyncreg.so")
            parts.append(f"xilinx_asyncreg -xdc {xdc}")
        if opts["dsp_pipeline"]:
            loads.append(plugins / "xilinx_dsp_qor.so")
            parts.append(MAP_DSP_XC7.format(xilinx_dsp="xilinx_dsp_qor -family xc7 -pipeline"))
            start = "coarse"
        elif opts["dsp_init"]:
            loads.append(plugins / "xilinx_dsp_init.so")
            parts.append(MAP_DSP_XC7.format(xilinx_dsp="xilinx_dsp_init -family xc7"))
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
    if opts.get("carry_di_bypass"):
        args += ["-o", "carry-di-bypass"]
    return args


def nextpnr_has(binary, needle):
    """Whether this nextpnr knows an option: its name is in the binary. A gate wrapper script
    (OFX_NEXTPNR_BIN=<path> ... exec npwait.sh) is followed to the binary it runs."""
    p = Path(binary)
    for _ in range(3):
        if not p.is_file():
            return False
        if p.stat().st_size < 4096:
            m = re.search(r"OFX_NEXTPNR_BIN=(\S+)", p.read_text(errors="replace"))
            if not m:
                return False
            p = Path(m.group(1).strip("'\""))
            continue
        with open(p, "rb") as f:
            tail = b""
            while True:
                chunk = f.read(1 << 22)
                if not chunk:
                    return False
                if needle in tail + chunk:
                    return True
                tail = chunk[-len(needle):]
    return False


def plan(proj, xdc, toolchain=None):
    tc = Path(toolchain or CONFIG["toolchain"])
    rel = release(tc)
    opts = options(proj.build_opts)
    out = {"release": rel, "options": opts, "synth": None, "nextpnr_args": [], "chipdb": None, "xadc_chipdb": None,
           "tuned_chipdb": None, "placer": None, "notes": []}
    if rel is None:
        out["notes"].append(f"{tc} is not an ofx release install ({CONFIG['release_file']} missing): the release "
                            f"defaults are off and the build is the plain openXC7 flow")
        return out
    plugins = tc / CONFIG["plugins"]
    for k, so in CONFIG["default_plugins"].items():
        if opts[k] and k not in (proj.build_opts or {}) and not (plugins / so).exists():
            opts[k] = False
            out["notes"].append(f"{k}: default off, {so} is not in this install (it predates the option; rerun "
                                f"install/install.sh)")
    npnr = tc / CONFIG["nextpnr_bin"]
    for k, needles in CONFIG["default_nextpnr_options"].items():
        needles = needles if isinstance(needles, tuple) else (needles,)
        if opts[k] and k not in (proj.build_opts or {}) and not all(nextpnr_has(npnr, n) for n in needles):
            opts[k] = False
            out["notes"].append(f"{k}: default off, {npnr} predates the option (rerun install/install.sh)")
    if opts["placer_tuning"]:
        tuned = tc / CONFIG["tuned_chipdb"].format(fabric=proj.device["fabric"])
        if re.match(CONFIG["cal_parts"], proj.part) and tuned.exists():
            out["tuned_chipdb"] = str(tuned)
        else:
            opts["placer_tuning"] = False
            why = (f"{tuned} is not in this install (it predates the option; rerun install/install.sh)"
                   if re.match(CONFIG["cal_parts"], proj.part) else
                   f"tuned for xc7a35t-1 only (calibrated chipdb), not {proj.part}")
            out["notes"].append(f"placer_tuning: off, {why}")
    synth, loads = synth_script(opts, xdc, plugins)
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
    if p.get("tuned_chipdb") and pargs == ["--placer", "static"]:
        return {"nextpnr_args": pargs + CONFIG["placer_tuning_args"], "chipdb": p["tuned_chipdb"],
                "why": [pwhy + "; placer_tuning: " + " ".join(CONFIG["placer_tuning_args"]),
                        f"chipdb: {p['tuned_chipdb']} (placer_tuning: cell + route calibration, LUT A6 pins)"]}
    chipdb, cwhy = chipdb_choice(p, net["types"] if net else None)
    if p.get("tuned_chipdb"):
        pwhy += "; placer_tuning: not applied (static placer only)"
    return {"nextpnr_args": pargs or [], "chipdb": chipdb, "why": [pwhy, cwhy]}
