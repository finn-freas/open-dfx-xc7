import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import netlist_depth
import qor_bench
from build_openxc7 import tool

ROOT = qor_bench.ROOT

CONFIG = {
    "out": ROOT / "build" / "qor" / "synx" / "synth",
    "period_ns": 5,
    "dry_run": True,
    "timeout_s": 7200,
    "ulimit_kb": 6_000_000,
    "lutlib_dir": ROOT / "build" / "qor" / "synx" / "lutlib",
    "litex": {
        "arty_ddr3": {"src": ROOT / "designs" / "ddr3" / "arty_ddr3", "top": "digilent_arty", "period_ns": 10,
                      "plugin": ROOT / "build" / "yosys-plugin" / "clkbufmap_gapfix.so", "clkbuf_pass": "clkbufmap_gapfix"},
    },
}

DEFAULTS = {
    "yosys": None,
    "plugin": None,
    "flags": "",
    "dff": False,
    "split_map_luts": False,
    "lutlib": None,
    "W": None,
    "D_frac": None,
    "abc9_script": None,
    "pre_abc": "",
    "fsm": None,
    "retime": False,
    "dspq": False,
    "prep": None,
    "scratch": None,
}

YOSYS_SYNX = "build/yosys-build/yosys-synx/yosys"

PREP = {
    "manual": "proc; check; flatten; tribuf -logic; deminout; opt_expr; check; opt_clean; opt -nodffe -nosdff; "
              "fsm; opt; wreduce; peepopt; opt_clean; pmux2shiftx; clean; sort",
    "memdff": "proc; check; flatten; tribuf -logic; deminout; opt_expr; check; opt_clean; opt -nodffe -nosdff; "
              "memory_dff; fsm; opt; wreduce; peepopt; opt_clean; pmux2shiftx; clean; sort",
    "nosdff": "proc; check; flatten; tribuf -logic; deminout; opt_expr; check; opt_clean; opt -nodffe -nosdff; "
              "fsm; opt -nosdff; wreduce; peepopt; opt_clean; pmux2shiftx; clean; sort",
}
PREP["keepmul"] = ("proc; check; flatten; tribuf -logic; deminout; opt_expr; check; opt_clean; setattr -set keep 1 t:$mul; "
                   "opt -nodffe -nosdff; fsm; opt; wreduce; peepopt; opt_clean; pmux2shiftx; clean; sort; "
                   "setattr -unset keep t:$mul")

COARSE = {
    "nosdff": "techmap -map +/cmp2lut.v -map +/cmp2lcu.v -D LUT_WIDTH=6; alumacc; share; opt -nosdff; memory -nomap; opt_clean",
}

RETIME_EXCLUDE_WIRE_ATTRS = ["keep", "ASYNC_REG", "async_reg", "DONT_TOUCH", "dont_touch"]

LUTLIBS = {
    "flat200": {"lut": [200] * 6, "lut_size_scaled": False},
    "flat124": {"lut": [124] * 6, "lut_size_scaled": False},
}

SCRIPTS = {
    "dch2": "+&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} {R} -v; &mfs; &ps; &dch -f -r; &if {W} {D} {R} -v; &mfs",
    "syn2": "+&scorr; &sweep; &syn2; &dc2; &dch -f -r; &ps; &if {W} {D} {R} -v; &mfs",
    "synch2": "+&scorr; &sweep; &synch2; &if {W} {D} {R} -v; &mfs",
    "satlut": "+&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} {R} -v; &mfs; &satlut -d",
    "noarea": "+&scorr; &sweep; &dc2; &dch -f -r; &ps; &if {W} {D} {R} -v",
}

VARIANTS = {
    "viv": {"vivado_synth": True},
    "viv_retime": {"vivado_synth": True, "synth_opts": "-retiming"},
    "viv_nofsm": {"vivado_synth": True, "synth_opts": "-fsm_extraction off"},
    "viv_noshare": {"vivado_synth": True, "synth_opts": "-resource_sharing off"},
    "viv_share": {"vivado_synth": True, "synth_opts": "-resource_sharing on"},
    "ys": {"qor_variant": "fix_static"},
    "ys_dspq": {"qor_variant": "dspq", "skip": ("rv_soc", "bram", "arty_ddr3")},
    "t_split": {"split_map_luts": True},
    "t_cal": {"split_map_luts": True, "lutlib": "flat200", "W": 450},
    "t_dff": {"dff": True},
    "t_cal_dff": {"split_map_luts": True, "lutlib": "flat200", "W": 450, "dff": True},
    "t_cal_w300": {"lutlib": "flat200", "W": 300},
    "t_cal_w600": {"lutlib": "flat200", "W": 600},
    "t_cal_w1000": {"lutlib": "flat200", "W": 1000},
    "t_c124": {"lutlib": "flat124", "W": 450},
    "t_cal_dch2": {"lutlib": "flat200", "W": 450, "abc9_script": "dch2"},
    "t_cal_syn2": {"lutlib": "flat200", "W": 450, "abc9_script": "syn2"},
    "t_cal_synch2": {"lutlib": "flat200", "W": 450, "abc9_script": "synch2"},
    "t_cal_satlut": {"lutlib": "flat200", "W": 450, "abc9_script": "satlut"},
    "t_cal_noarea": {"lutlib": "flat200", "W": 450, "abc9_script": "noarea"},
    "t_cal_D": {"lutlib": "flat200", "W": 450, "D_frac": 0.5},
    "t_nofsm": {"fsm": "none"},
    "d_split": {"dspq": True, "split_map_luts": True},
    "d_cal": {"dspq": True, "lutlib": "flat200", "W": 450},
    "d_cal_w600": {"dspq": True, "lutlib": "flat200", "W": 600},
    "d_cal_w1000": {"dspq": True, "lutlib": "flat200", "W": 1000},
    "d_cal_dch2": {"dspq": True, "lutlib": "flat200", "W": 450, "abc9_script": "dch2"},
    "d_cal_dff": {"dspq": True, "lutlib": "flat200", "W": 450, "dff": True},
    "d_dff": {"dspq": True, "dff": True},
    "d_nofsm": {"dspq": True, "fsm": "none"},
    "d_retime_full": {"dspq": True, "retime": "full"},
    "s_share": {"yosys": qor_bench.YOSYS_AREA, "flags": "-share_aggressive"},
    "s_cal_share": {"yosys": qor_bench.YOSYS_AREA, "flags": "-share_aggressive", "lutlib": "flat200", "W": 450},
    "t_retime": {"retime": True},
    "t_cal_retime": {"lutlib": "flat200", "W": 450, "retime": True},
    "t_retime_full": {"retime": "full"},
    "t_cal_retime_full": {"lutlib": "flat200", "W": 450, "retime": "full"},
    "t_prep": {"prep": "manual"},
    "m_memdff": {"prep": "memdff"},
    "m_memdff_dspq": {"prep": "memdff", "dspq": True},
    "m_nosdff": {"prep": "nosdff"},
    "m_synxref": {"yosys": YOSYS_SYNX},
    "m_keepmem": {"yosys": YOSYS_SYNX, "scratch": "opt_dff.keep_memrd_regs 1"},
    "m_keepmem_dspq": {"yosys": YOSYS_SYNX, "scratch": "opt_dff.keep_memrd_regs 1", "dspq": True},
    "x1": {"scratch": "abc9.xaiger 1"},
    "k_mul": {"prep": "keepmul"},
    "k_mul_dspq": {"prep": "keepmul", "dspq": True},
    "x1_cal": {"scratch": "abc9.xaiger 1", "lutlib": "flat200", "W": 450},
    "x1_cal_dff": {"scratch": "abc9.xaiger 1", "lutlib": "flat200", "W": 450, "dff": True},
    "dx1": {"scratch": "abc9.xaiger 1", "dspq": True},
    "dx1_cal": {"scratch": "abc9.xaiger 1", "dspq": True, "lutlib": "flat200", "W": 450},
    "dx1_cal_dff": {"scratch": "abc9.xaiger 1", "dspq": True, "lutlib": "flat200", "W": 450, "dff": True},
}


def opts_of(vname):
    o = dict(DEFAULTS)
    o.update({k: v for k, v in VARIANTS[vname].items() if k in DEFAULTS})
    assert not (o["dspq"] and o["prep"] in COARSE), "dspq with a manual coarse step is not wired up"
    return o


def sha(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, bytes) else str(p).encode())
        h.update(b"\0")
    return h.hexdigest()[:16]


def lutlib_file(name):
    lib = LUTLIBS[name]
    out = CONFIG["lutlib_dir"] / f"{name}.v"
    lines = []
    for k in range(1, 7):
        d = lib["lut"][k - 1]
        area = {1: 1, 2: 2, 3: 3, 4: 3, 5: 3, 6: 5}[k]
        ins = ", ".join(f"input I{i}" for i in range(k))
        lines.append(f"(* abc9_lut={area} *)\nmodule LUT{k}(output O, {ins});\n  parameter [{(1 << k) - 1}:0] INIT = 0;\n"
                     f"  specify\n" + "".join(f"    (I{i} => O) = {d};\n" for i in range(k)) + "  endspecify\nendmodule\n")
    txt = "".join(lines)
    if not out.exists() or out.read_text() != txt:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt)
    return out


def abc_script_file(name, w, dtarget):
    txt = SCRIPTS[name].lstrip("+").replace("{W}", f"-W {w}").replace("{D}", f"-D {dtarget}" if dtarget else "")
    txt = txt.replace("{R}", "") + "\n"
    out = CONFIG["lutlib_dir"] / f"abc_{name}_{sha(txt)}.abc"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt)
    return out


def map_luts(o, period_ps):
    cmds = ["opt_expr -mux_undef -noclkinv", "read_verilog -icells -lib -specify +/xilinx/abc9_model.v"]
    if o["lutlib"]:
        cmds.append(f"read_verilog -lib -specify -overwrite {lutlib_file(o['lutlib'])}")
    dtarget = int(round(period_ps * o["D_frac"])) if o["D_frac"] else None
    if o["abc9_script"]:
        cmds.append(f"scratchpad -set abc9.script {abc_script_file(o['abc9_script'], o['W'] or 300, dtarget)}")
    elif dtarget:
        cmds.append(f"scratchpad -set abc9.D {dtarget}")
    if o["pre_abc"]:
        cmds.append(o["pre_abc"])
    cmds.append(f"abc9 -W {o['W'] if o['W'] else 300}" + (" -dff" if o["dff"] else ""))
    cmds += ["clean", "xilinx_srl -fixed -minlen 3", "techmap -map +/xilinx/lut_map.v -map +/xilinx/cells_map.v -D LUT_WIDTH=6",
             "xilinx_dffopt", "opt_lut_ins -tech xilinx"]
    return "; ".join(cmds)


def retime_cmds(mode):
    cmds = [f"select -set rt_ex t:$_*DFF* a:keep %i {' '.join(f'w:* a:{a} %i' + (' %u' if i else '') for i, a in enumerate(RETIME_EXCLUDE_WIRE_ATTRS))} "
            "%x1 t:$_*DFF* %i %u",
            "select -set rt_sel * @rt_ex %d"]
    if mode == "full":
        cmds.append("dfflegalize -cell $_DFF_P_ 01 -cell $_DFF_N_ 01 @rt_sel")
    cmds.append("abc -dff @rt_sel")
    if mode == "full":
        cmds.append("opt_dff")
    cmds.append("opt_clean")
    return "; ".join(cmds)


def script(top, o, period_ps, clkbuf_pass=None):
    sx = f"synth_xilinx -flatten -abc9 -arch xc7 -top {top}" + (f" {o['flags']}" if o["flags"] else "") + (" -dff" if o["dff"] else "")
    pre = 'setattr -set fsm_encoding "none" w:*; ' if o["fsm"] == "none" else ""
    for s in ([o["scratch"]] if isinstance(o["scratch"], str) else (o["scratch"] or [])):
        pre += f"scratchpad -set {s}; "
    custom = o["split_map_luts"] or o["lutlib"] or o["W"] or o["D_frac"] or o["abc9_script"] or o["pre_abc"] or o["retime"]
    tail = f"{clkbuf_pass} -buf BUFG O:I; clean; {sx} -run check:" if clkbuf_pass else None

    first = "map_dsp" if o["prep"] else "begin"
    head0 = f"{sx} -run :prepare; {PREP[o['prep']]}; " if o["prep"] else ""

    def upto(label):
        if o["dspq"]:
            return (f"{head0}{sx} -run {first}:map_dsp; {qor_bench.MAP_DSP_XC7.replace('{opt}', ' -pipeline')}; "
                    f"{sx} -run coarse:{label}")
        if o["prep"] in COARSE:
            return (f"{head0}{sx} -run {first}:coarse; {COARSE[o['prep']]}; "
                    + (f"{sx} -run map_memory:{label}" if label else f"{sx} -run map_memory:"))
        if o["prep"]:
            return f"{head0}{sx} -run {first}:{label}" if label else f"{head0}{sx} -run {first}:"
        return f"{sx} -run :{label}" if label else sx

    if not custom:
        if tail:
            return f"{pre}{upto('finalize')}; {tail}"
        return pre + upto("")
    if o["retime"]:
        head = f"{pre}{upto('map_ffs')}; {retime_cmds(o['retime'])}; {sx} -run map_ffs:map_luts; "
    else:
        head = f"{pre}{upto('map_luts')}; "
    return head + f"{map_luts(o, period_ps)}; " + (tail if tail else f"{sx} -run finalize:")


def synth(design, vname, dry):
    o = opts_of(vname)
    if design in CONFIG["litex"]:
        lx = CONFIG["litex"][design]
        top, src, period = lx["top"], lx["src"], lx["period_ns"]
        rtl = [src / f"{top}.v", *sorted(p for p in src.glob("*.v") if p.name != f"{top}.v")]
        files = " ".join(str(p) for p in rtl)
        plugin = lx["plugin"]
        scr = script(top, o, period * 1000, lx["clkbuf_pass"])
        cwd = ROOT
    else:
        top = qor_bench.CONFIG["designs"][design]["top"]
        period = CONFIG["period_ns"]
        src = qor_bench.prepare_src(design, period)
        rtl = qor_bench.rtl_files(src)
        files = " ".join(f.name for f in rtl)
        plugin = ROOT / (o["plugin"] or (qor_bench.DSP_PLUGIN if o["dspq"] else "")) if (o["plugin"] or o["dspq"]) else None
        scr = script(top, o, period * 1000)
        cwd = src
    ys_bin = str(ROOT / o["yosys"]) if o["yosys"] else tool("yosys")
    libtxt = lutlib_file(o["lutlib"]).read_text() if o["lutlib"] else ""
    key = sha(ys_bin, Path(ys_bin).stat().st_size, scr, libtxt, *[f.name + sha(f.read_bytes()) for f in rtl],
              *([sha(plugin.read_bytes())] if plugin else []))
    out = CONFIG["out"] / design / key
    js = out / f"{top}.json"
    meta = out / "meta.json"
    if meta.exists() and json.loads(meta.read_text()).get("ok"):
        return json.loads(meta.read_text())
    ys = f"read_verilog -sv {files}; {scr}; tee -o {out / 'stat.txt'} stat -tech xilinx; write_json {js}"
    cmd = [ys_bin] + (["-m", str(plugin)] if plugin else []) + ["-p", ys]
    if dry:
        print(f"[dry] synth {design} {vname} -> {out.relative_to(ROOT)}: {scr}")
        return {"ok": None, "dry": True, "json": str(js), "key": key}
    out.mkdir(parents=True, exist_ok=True)
    print(f"[run] synth {design} {vname}", flush=True)
    shell = f"ulimit -v {CONFIG['ulimit_kb']}; exec " + " ".join(_q(c) for c in cmd)
    rc, secs = qor_bench.run_logged(["bash", "-c", shell], out / "yosys.log", cwd)
    rec = {"ok": rc == 0 and js.exists(), "rc": rc, "seconds": secs, "json": str(js), "key": key, "variant": vname,
           "script": scr, "yosys": ys_bin, "plugin": str(plugin) if plugin else None, "log": str((out / "yosys.log").relative_to(ROOT)),
           "error": qor_bench.first_error(out / "yosys.log"), "stat": qor_bench.parse_yosys_stat(out / "stat.txt")}
    meta.write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def _q(s):
    return "'" + str(s).replace("'", "'\\''") + "'"


def main():
    ap = argparse.ArgumentParser(description="Timing-oriented yosys synthesis options for xc7 (opt-in; default = synth_xilinx "
                                             "unchanged): abc9 delay model, scripts, -dff, FSM encoding")
    ap.add_argument("--designs", nargs="+", default=["rv_soc"])
    ap.add_argument("--variants", nargs="+", default=["t_split"])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    for d in a.designs:
        for v in a.variants:
            r = synth(d, v, dry)
            st = r.get("stat") or {}
            dep = netlist_depth.analyse(r["json"]) if r.get("ok") else {}
            print(f"{d:10s} {v:14s} ok={r.get('ok')} s={r.get('seconds')} lut={st.get('luts')} ff={st.get('ffs')} "
                  f"carry4={st.get('carry4')} muxf7={st.get('muxf7')} maxlut={dep.get('max_lut_levels')} "
                  f"maxlogic={dep.get('max_logic_levels')} top100={dep.get('mean_lut_levels_top')} hist={dep.get('hist')}",
                  flush=True)


if __name__ == "__main__":
    main()
