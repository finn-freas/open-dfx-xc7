import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
import qor_xtime as qx

ROOT = qor_bench.ROOT
TMG = ["-o", "hardblock-timing", "--placer", "static"]

CONFIG = {
    "dry_run": True,
    "out": ROOT / "build" / "qor" / "place",
    "binaries": {
        "ref": "build/nextpnr-build/place_ref/nextpnr-himbaechel",
        "v1": "build/nextpnr-build/place_v1/nextpnr-himbaechel",
        "v2": "build/nextpnr-build/place_v2/nextpnr-himbaechel",
        "v3": "build/nextpnr-build/place_v3/nextpnr-himbaechel",
        "v4": "build/nextpnr-build/place_v4/nextpnr-himbaechel",
        "perm": "build/nextpnr-build/qorperm/nextpnr-himbaechel",
    },
    "chipdb": qor_bench.NIGHTLY_CHIPDB,
    "chipdb_cal": ROOT / "build" / "chipdb-cal" / "on" / "chipdb-xc7a50t.bin",
    "chipdb_rcal": ROOT / "build" / "chipdb-rcal" / "on" / "chipdb-xc7a50t.bin",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "max_nextpnr": 2,
    "designs": ["rv_soc", "bram", "rv_big", "ddr"],
    "periods": [5],
    "seeds": [1, 2, 3],
    "socs": {
        "ddr": {
            "json": ROOT / "build" / "ddr3" / "arty_ddr3" / "gapfix" / "digilent_arty.json",
            "xdc": ROOT / "designs" / "ddr3" / "arty_ddr3" / "nextpnr" / "digilent_arty.xdc",
            "vivado_xdc": ROOT / "designs" / "ddr3" / "arty_ddr3" / "digilent_arty.xdc",
            "top": "digilent_arty",
            "freq": 100,
            "clock": "sys_clk",
            "vivado_clock": "main_crg_clkout0",
            "period": 10,
        },
        "eth": {
            "json": ROOT / "build" / "eth" / "arty_eth" / "gapfix" / "digilent_arty.json",
            "xdc": ROOT / "designs" / "eth" / "arty_eth" / "nextpnr" / "digilent_arty.xdc",
            "vivado_xdc": ROOT / "designs" / "eth" / "arty_eth" / "digilent_arty.xdc",
            "top": "digilent_arty",
            "freq": 100,
            "clock": "sys_clk",
            "vivado_clock": "main_crg_clkout0",
            "period": 10,
        },
    },
    "variants": {
        "pl_base": {"bin": "ref", "args": TMG},
        "pl_off": {"bin": "v1", "args": TMG},
        "pl_ct10": {"bin": "v1", "args": TMG + ["--tmg-crit-target", "1.0"]},
        "pl_ct10_f7": {"bin": "v1", "args": TMG + ["--tmg-crit-target", "1.0", "--tmg-crit-floor", "0.7"]},
        "pl_ct09": {"bin": "v1", "args": TMG + ["--tmg-crit-target", "0.9"]},
        "pl_sw20": {"bin": "v1", "args": TMG + ["--placer-static-timingweight", "20"]},
        "pl_sw20e4": {"bin": "v1", "args": TMG + ["--placer-static-timingweight", "20", "--placer-static-critexp", "4"]},
        "pl_ct10_sw20": {"bin": "v1", "args": TMG + ["--tmg-crit-target", "1.0", "--placer-static-timingweight", "20"]},
        "pl_r1e4": {"bin": "v1", "args": TMG + ["--placer1-critexp", "4"]},
        "pl_r1t8": {"bin": "v1", "args": TMG + ["--placer1-timing-tradeoff", "0.8"]},
        "pl_ct10_r1t8": {"bin": "v1", "args": TMG + ["--tmg-crit-target", "1.0", "--placer1-timing-tradeoff", "0.8"]},
        "pl_topt": {"bin": "v1", "args": TMG + ["-o", "timing-opt=3,10"]},
        "pl_ct10_topt": {"bin": "v1", "args": TMG + ["--tmg-crit-target", "1.0", "-o", "timing-opt=3,10"]},
        "pl2_off": {"bin": "v2", "args": TMG},
        "pl2_hx1": {"bin": "v2", "args": TMG + ["-o", "static-hpwl-x=1"]},
        "pl2_tu5": {"bin": "v2", "args": TMG + ["--placer-static-target-util", "0.5"]},
        "pl2_tu9": {"bin": "v2", "args": TMG + ["--placer-static-target-util", "0.9"]},
        "pl2_ff1": {"bin": "v2", "args": TMG + ["-o", "static-ff-area=1.0"]},
        "pl2_hx1_ff1": {"bin": "v2", "args": TMG + ["-o", "static-hpwl-x=1", "-o", "static-ff-area=1.0"]},
        "pl2_hx1_ct10": {"bin": "v2", "args": TMG + ["-o", "static-hpwl-x=1", "--tmg-crit-target", "1.0"]},
        "pl3_off": {"bin": "v3", "args": TMG + []},
        "plp_cal": {"bin": "perm", "args": TMG + ["-o", "lut-perm-timing"], "cal": True},
        "plp_rcal": {"bin": "perm", "args": TMG + ["-o", "lut-perm-timing"], "cal": True, "rcal": True},
        "pl4_off_rcal": {"bin": "v4", "args": TMG + [], "cal": True, "rcal": True},
        "pl4_sw20_rcal": {"bin": "v4", "args": TMG + ["--placer-static-timingweight", "20"], "cal": True, "rcal": True},
        "pl4_ce1_rcal": {"bin": "v4", "args": TMG + ["--placer-static-critexp", "1"], "cal": True, "rcal": True},
        "pl4_ce4_rcal": {"bin": "v4", "args": TMG + ["--placer-static-critexp", "4"], "cal": True, "rcal": True},
        "pl4_ipw5_rcal": {"bin": "v4", "args": TMG + ["--placer-static-ip-wait", "0.5"], "cal": True, "rcal": True},
        "pl4_sw20ce1_rcal": {"bin": "v4", "args": TMG + ["--placer-static-timingweight", "20", "--placer-static-critexp", "1"], "cal": True, "rcal": True},
        "pl4_ct10_rcal": {"bin": "v4", "args": TMG + ["--tmg-crit-target", "1.0"], "cal": True, "rcal": True},
        "pl4_r1t8_rcal": {"bin": "v4", "args": TMG + ["--placer1-timing-tradeoff", "0.8"], "cal": True, "rcal": True},
        "pl4_os25_rcal": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.25"], "cal": True, "rcal": True},
        "pl4_hx1_rcal": {"bin": "v4", "args": TMG + ["-o", "static-hpwl-x=1"], "cal": True, "rcal": True},
        "pl4_sw2_rcal": {"bin": "v4", "args": TMG + ["--placer-static-timingweight", "2"], "cal": True, "rcal": True},
        "pl3_off_cal": {"bin": "v3", "args": TMG + [], "cal": True},
        "pl3_off_dq": {"bin": "v3", "args": TMG + [], "dspq": True},
        "pl3_off_dqcal": {"bin": "v3", "args": TMG + [], "dspq": True, "cal": True},
        "pl3_ipw5": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5"]},
        "pl3_ipw5_cal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5"], "cal": True},
        "pl3_ipw5_dq": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5"], "dspq": True},
        "pl3_ipw5_dqcal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5"], "dspq": True, "cal": True},
        "pl3_ipw3": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.3"]},
        "pl3_ipw3_cal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.3"], "cal": True},
        "pl3_ipw3_dq": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.3"], "dspq": True},
        "pl3_ipw3_dqcal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.3"], "dspq": True, "cal": True},
        "pl3_ipw5_ff1": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-ff-area=1.0"]},
        "pl3_ipw5_ff1_cal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-ff-area=1.0"], "cal": True},
        "pl3_ipw5_ff1_dq": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-ff-area=1.0"], "dspq": True},
        "pl3_ipw5_ff1_dqcal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-ff-area=1.0"], "dspq": True, "cal": True},
        "pl3_ipw5_tu9": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-target-util", "0.9"]},
        "pl3_ipw5_tu9_cal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-target-util", "0.9"], "cal": True},
        "pl3_ipw5_tu9_dq": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-target-util", "0.9"], "dspq": True},
        "pl3_ipw5_tu9_dqcal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-target-util", "0.9"], "dspq": True, "cal": True},
        "pl3_ipw5_tu5": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-target-util", "0.5"]},
        "pl3_ipw5_tu5_cal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-target-util", "0.5"], "cal": True},
        "pl3_ipw5_tu5_dq": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-target-util", "0.5"], "dspq": True},
        "pl3_ipw5_tu5_dqcal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-target-util", "0.5"], "dspq": True, "cal": True},
        "pl3_ipw5_hx1": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-hpwl-x=1"]},
        "pl3_ipw5_hx1_cal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-hpwl-x=1"], "cal": True},
        "pl3_ipw5_hx1_dq": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-hpwl-x=1"], "dspq": True},
        "pl3_ipw5_hx1_dqcal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-hpwl-x=1"], "dspq": True, "cal": True},
        "pl3_ipw5_ct10": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--tmg-crit-target", "1.0"]},
        "pl3_ipw5_ct10_cal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--tmg-crit-target", "1.0"], "cal": True},
        "pl3_ipw5_ct10_dq": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--tmg-crit-target", "1.0"], "dspq": True},
        "pl3_ipw5_ct10_dqcal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "--tmg-crit-target", "1.0"], "dspq": True, "cal": True},
        "pl3_ipw5_hxff": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-hpwl-x=1", "-o", "static-ff-area=1.0"]},
        "pl3_ipw5_hxff_cal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-hpwl-x=1", "-o", "static-ff-area=1.0"], "cal": True},
        "pl3_ipw5_hxff_dq": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-hpwl-x=1", "-o", "static-ff-area=1.0"], "dspq": True},
        "pl3_ipw5_hxff_dqcal": {"bin": "v3", "args": TMG + ["--placer-static-ip-wait", "0.5", "-o", "static-hpwl-x=1", "-o", "static-ff-area=1.0"], "dspq": True, "cal": True},
        "pl4_off": {"bin": "v4", "args": TMG + []},
        "pl4_off_cal": {"bin": "v4", "args": TMG + [], "cal": True},
        "pl4_off_dq": {"bin": "v4", "args": TMG + [], "dspq": True},
        "pl4_off_dqcal": {"bin": "v4", "args": TMG + [], "dspq": True, "cal": True},
        "pl4_os25": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.25"]},
        "pl4_os25_cal": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.25"], "cal": True},
        "pl4_os25_dq": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.25"], "dspq": True},
        "pl4_os25_dqcal": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.25"], "dspq": True, "cal": True},
        "pl4_os40": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.4"]},
        "pl4_os40_cal": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.4"], "cal": True},
        "pl4_os40_dq": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.4"], "dspq": True},
        "pl4_os40_dqcal": {"bin": "v4", "args": TMG + ["--placer-static-overlap-stop", "0.4"], "dspq": True, "cal": True},
        "pl4_ipw5_os25": {"bin": "v4", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-overlap-stop", "0.25"]},
        "pl4_ipw5_os25_cal": {"bin": "v4", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-overlap-stop", "0.25"], "cal": True},
        "pl4_ipw5_os25_dq": {"bin": "v4", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-overlap-stop", "0.25"], "dspq": True},
        "pl4_ipw5_os25_dqcal": {"bin": "v4", "args": TMG + ["--placer-static-ip-wait", "0.5", "--placer-static-overlap-stop", "0.25"], "dspq": True, "cal": True},
        "pl2_off_cal": {"bin": "v2", "args": TMG + [], "cal": True},
        "pl2_off_dq": {"bin": "v2", "args": TMG + [], "dspq": True},
        "pl2_off_dqcal": {"bin": "v2", "args": TMG + [], "dspq": True, "cal": True},
        "pl2_ct10": {"bin": "v2", "args": TMG + ["--tmg-crit-target", "1.0"]},
        "pl2_ct10_cal": {"bin": "v2", "args": TMG + ["--tmg-crit-target", "1.0"], "cal": True},
        "pl2_ct10_dq": {"bin": "v2", "args": TMG + ["--tmg-crit-target", "1.0"], "dspq": True},
        "pl2_ct10_dqcal": {"bin": "v2", "args": TMG + ["--tmg-crit-target", "1.0"], "dspq": True, "cal": True},
        "pl2_hx1_cal": {"bin": "v2", "args": TMG + ["-o", "static-hpwl-x=1"], "cal": True},
        "pl2_hx1_dq": {"bin": "v2", "args": TMG + ["-o", "static-hpwl-x=1"], "dspq": True},
        "pl2_hx1_dqcal": {"bin": "v2", "args": TMG + ["-o", "static-hpwl-x=1"], "dspq": True, "cal": True},
        "pl2_tu9_cal": {"bin": "v2", "args": TMG + ["--placer-static-target-util", "0.9"], "cal": True},
        "pl2_tu9_dq": {"bin": "v2", "args": TMG + ["--placer-static-target-util", "0.9"], "dspq": True},
        "pl2_tu9_dqcal": {"bin": "v2", "args": TMG + ["--placer-static-target-util", "0.9"], "dspq": True, "cal": True},
        "pl2_ff1_cal": {"bin": "v2", "args": TMG + ["-o", "static-ff-area=1.0"], "cal": True},
        "pl2_ff1_dq": {"bin": "v2", "args": TMG + ["-o", "static-ff-area=1.0"], "dspq": True},
        "pl2_ff1_dqcal": {"bin": "v2", "args": TMG + ["-o", "static-ff-area=1.0"], "dspq": True, "cal": True},
    },
    "vivado_root": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "vivado_tag": "place_xtime",
}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def variant(name):
    v = dict(CONFIG["variants"][name])
    v["binary"] = ROOT / CONFIG["binaries"][v["bin"]]
    return v


def register(name):
    v = variant(name)
    qor_bench.CONFIG["nextpnr"][name] = (str(v["binary"].relative_to(ROOT)), chipdb_of(v))
    qor_bench.CONFIG["variants"][name] = {"nextpnr": name, "args": v["args"], "seeds": CONFIG["seeds"]}
    if v.get("dspq"):
        qor_bench.CONFIG["variants"][name].update({"synth": qor_bench.SYNTH_DSPQ_ON, "plugin": qor_bench.DSP_PLUGIN})


def chipdb_of(v):
    if v.get("rcal"):
        return CONFIG["chipdb_rcal"]
    return CONFIG["chipdb_cal"] if v.get("cal") else CONFIG["chipdb"]


_run_logged = qor_bench.run_logged


def run_npwait(cmd, log, cwd):
    if Path(cmd[0]).name.startswith("nextpnr"):
        os.environ.update(OFX_NEXTPNR_BIN=cmd[0], OFX_MAX_NEXTPNR=str(CONFIG["max_nextpnr"]))
        cmd = [str(CONFIG["npwait"])] + list(cmd[1:])
    return _run_logged(cmd, log, cwd)


qor_bench.run_logged = run_npwait


def wait_slot():
    while int(subprocess.run(["pgrep", "-c", "nextpnr"], capture_output=True, text=True).stdout.strip() or 0) >= \
            CONFIG["max_nextpnr"]:
        time.sleep(20)


def run_dir(design, period, vname, seed):
    tag = f"{design}_p10" if design in CONFIG["socs"] else f"{design}_{qor_bench.ptag(period)}"
    return qor_bench.CONFIG["out"] / "oxc7" / vname / tag / f"s{seed}"


def pnr_soc(design, vname, seed, dry):
    v = variant(vname)
    d = CONFIG["socs"][design]
    out = run_dir(design, d["period"], vname, seed)
    top = d["top"]
    args = ["--device", qor_bench.CONFIG["part"], "--json", str(d["json"]), "-o", f"xdc={d['xdc']}", "--seed", str(seed),
            "--freq", str(d["freq"]), "--timing-allow-fail"] + v["args"]
    key = qor_bench.sha(sha_file(v["binary"]), *args, sha_file(d["json"]))
    st = out / "status.json"
    if st.exists():
        rec = json.loads(st.read_text())
        if rec.get("key") == key and rec.get("pnr", {}).get("ok"):
            return rec
    args = args + (["--chipdb", str(chipdb_of(v))] if v.get("cal") else [])
    cmd = [str(v["binary"])] + ([] if v.get("cal") else ["--chipdb", str(CONFIG["chipdb"])]) + args + [
        "--write", str(out / f"{top}_routed.json"), "-o", f"fasm={out / (top + '.fasm')}", "--report", str(out / "report.json")]
    if dry:
        print(f"[dry] pnr {design} {vname} s{seed}: {' '.join(cmd)}")
        return {"dry": True}
    out.mkdir(parents=True, exist_ok=True)
    wait_slot()
    print(f"[run] pnr {design} {vname} s{seed}", flush=True)
    rc, secs = qor_bench.run_logged(cmd, out / "nextpnr.log", d["json"].parent)
    rec = {"design": design, "period_ns": d["period"], "variant": vname, "seed": seed, "key": key, "cmd": cmd,
           "pnr": {"ok": rc == 0 and (out / f"{top}.fasm").exists(), "rc": rc, "seconds": secs,
                   "log": str((out / "nextpnr.log").relative_to(ROOT)), "error": qor_bench.first_error(out / "nextpnr.log")},
           "result": parse_clock(out / "nextpnr.log", d["clock"])}
    st.write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def parse_clock(log, clock):
    if not log.exists():
        return {}
    m = re.findall(r"Max frequency for clock\s+'" + re.escape(clock) + r"': ([0-9.]+) MHz", log.read_text(errors="replace"))
    return {"fmax": float(m[-1])} if m else {}


def pnr_one(design, period, vname, seed, dry):
    if design in CONFIG["socs"]:
        return pnr_soc(design, vname, seed, dry)
    register(vname)
    syn = qor_bench.synth(design, period, vname, dry)
    if not dry:
        wait_slot()
    return qor_bench.pnr_one(design, period, vname, seed, syn, dry)


def frames_of(design, period, vname, seed):
    d = run_dir(design, period, vname, seed)
    top = CONFIG["socs"][design]["top"] if design in CONFIG["socs"] else qor_bench.CONFIG["designs"][design]["top"]
    return d / f"{top}.frames", d / f"{top}.fasm"


def xname(design, period, vname, seed):
    tag = f"{design}_p10" if design in CONFIG["socs"] else f"{design}_{qor_bench.ptag(period)}"
    return f"{tag}_{vname}_s{seed}_placed"


def xprep(design, period, vname, seed, dry):
    run = run_dir(design, period, vname, seed)
    name = xname(design, period, vname, seed)
    d = CONFIG["out"] / "xsrc" / name
    if dry:
        print(f"[dry] xtime src {d.relative_to(ROOT)}")
        return name
    st = json.loads((run / "status.json").read_text())
    syn_json = Path(st["cmd"][st["cmd"].index("--json") + 1])
    if design in CONFIG["socs"]:
        top, xdc = CONFIG["socs"][design]["top"], CONFIG["socs"][design]["vivado_xdc"].read_text()
    else:
        top = qor_bench.CONFIG["designs"][design]["top"]
        xdc = (qor_bench.CONFIG["out"] / "src" / f"{design}_{qor_bench.ptag(period)}" / "constraints.xdc").read_text()
    d.mkdir(parents=True, exist_ok=True)
    qx.write_netlist(syn_json, d / "netlist.edf", dry)
    (d / "top.txt").write_text(top + "\n")
    (d / "mode.txt").write_text("placed\n")
    (d / "constraints.xdc").write_text(xdc)
    paths = qx.crit_paths(run / "report.json")
    (d / "paths.txt").write_text("".join(f"{qx.tcl_quote(a[0])} {a[1]} {qx.tcl_quote(b[0])} {b[1]} {dly:.3f}\n"
                                         for _, _, a, b, dly in paths))
    rows, skipped = qx.placement(run / f"{top}_routed.json")
    (d / "place.txt").write_text("".join(f"{qx.tcl_quote(n)} {b}\n" for n, b in rows))
    (d / "place_info.json").write_text(json.dumps({"rows": len(rows), "skipped": skipped,
                                                   "from": str(run.relative_to(ROOT))}) + "\n")
    return name


def vivado_result(name, period):
    d = CONFIG["vivado_root"] / CONFIG["vivado_tag"] / name
    st = d / "status.txt"
    if not st.exists():
        return None
    if not st.read_text().startswith("rc 0"):
        return {"error": st.read_text().strip()}
    tr = (d / "timing.rpt").read_text(errors="replace")
    m = re.search(r"WNS\(ns\).*?\n[- ]+\n\s*(-?[0-9.]+)\s+(-?[0-9.]+)\s+(\d+)", tr)
    if not m:
        return {"error": "no WNS"}
    wns = float(m.group(1))
    res = {"wns": wns, "tns": float(m.group(2)), "failing": int(m.group(3)), "fmax": round(1000.0 / (period - wns), 2),
           "dir": str(d)}
    wp = d / "worst_paths.txt"
    if wp.exists():
        sl = [float(p.split()[0]) for p in wp.read_text().splitlines()
              if len(p.split()) == 3 and "u_icap" not in p]
        if sl:
            res["fmax_noicap"] = round(1000.0 / (period - min(sl)), 2)
    return res


def soc_vivado(name, clock):
    d = CONFIG["vivado_root"] / CONFIG["vivado_tag"] / name
    st = d / "status.txt"
    if not st.exists():
        return None
    if not st.read_text().startswith("rc 0"):
        return {"error": st.read_text().strip()}
    tr = (d / "timing.rpt").read_text(errors="replace")
    m = re.search(r"^\s*" + re.escape(clock) + r"\s+(-?[0-9.]+)\s+(-?[0-9.]+)\s+(\d+)\s+(\d+)", tr[tr.find("Intra Clock Table"):], re.M)
    if not m:
        return {"error": f"no {clock} row"}
    wns = float(m.group(1))
    return {"wns": wns, "tns": float(m.group(2)), "failing": int(m.group(3)), "fmax": round(1000.0 / (10 - wns), 2),
            "dir": str(d)}


def stats(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "-"
    if len(xs) == 1:
        return f"{xs[0]:.2f}"
    return f"{statistics.mean(xs):.2f} ({min(xs):.2f}-{max(xs):.2f})"


def report(designs, periods, vnames, seeds):
    lines = ["| design | period | variant | nextpnr Fmax per seed (nextpnr timer) | mean (min-max) | "
             "Vivado Fmax on nextpnr placement per seed (Vivado timer) | mean (min-max) | Vivado WNS per seed |",
             "|---|---|---|---|---|---|---|---|"]
    data = {}
    for design in designs:
        for period in ([10] if design in CONFIG["socs"] else periods):
            for v in vnames:
                npr, viv, wns = [], [], []
                for s in seeds:
                    st = run_dir(design, period, v, s) / "status.json"
                    r = json.loads(st.read_text()) if st.exists() else {}
                    if design in CONFIG["socs"] and r:
                        r["result"] = parse_clock(ROOT / r["pnr"]["log"], CONFIG["socs"][design]["clock"])
                    npr.append(r.get("result", {}).get("fmax"))
                    x = soc_vivado(xname(design, period, v, s), CONFIG["socs"][design]["vivado_clock"]) if design in CONFIG["socs"] else \
                        vivado_result(xname(design, period, v, s), period)
                    viv.append(x.get("fmax") if x else None)
                    wns.append(x.get("wns") if x else None)
                data[(design, period, v)] = {"nextpnr": npr, "vivado": viv, "wns": wns}
                f = lambda xs: " / ".join("-" if x is None else f"{x:.2f}" for x in xs)
                lines.append(f"| {design} | {period:g} | {v} | {f(npr)} | {stats(npr)} | {f(viv)} | {stats(viv)} | {f(wns)} |")
    return "\n".join(lines) + "\n", data


def main():
    ap = argparse.ArgumentParser(description="placement experiments: nextpnr runs per variant and seed, Vivado-timed "
                                             "sources of nextpnr's placement (vivado/build_xtime.tcl), and the table")
    ap.add_argument("--designs", nargs="+", default=CONFIG["designs"])
    ap.add_argument("--periods", nargs="+", type=float, default=CONFIG["periods"])
    ap.add_argument("--variants", nargs="+", default=["pl_off"])
    ap.add_argument("--seeds", nargs="+", type=int, default=CONFIG["seeds"])
    ap.add_argument("--xprep", action="store_true", help="write Vivado sources of the finished runs into build/qor/place/xsrc")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--noop", nargs=2, metavar=("A", "B"), help="compare the .frames of two variants")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    CONFIG["seeds"] = a.seeds
    if a.noop:
        for design in a.designs:
            for period in ([10] if design in CONFIG["socs"] else a.periods):
                for s in a.seeds:
                    fa, ga = frames_of(design, period, a.noop[0], s)
                    fb, gb = frames_of(design, period, a.noop[1], s)
                    same = fa.exists() and fb.exists() and fa.read_bytes() == fb.read_bytes()
                    print(f"{design} p{period:g} s{s}: frames {'IDENTICAL' if same else 'DIFFER'} ({fa} vs {fb})")
        return
    if a.report:
        md, data = report(a.designs, a.periods, a.variants, a.seeds)
        CONFIG["out"].mkdir(parents=True, exist_ok=True)
        (CONFIG["out"] / ("table_" + "_".join(a.variants) + ".md")).write_text(md)
        (CONFIG["out"] / ("table_" + "_".join(a.variants) + ".json")).write_text(
            json.dumps({f"{k[0]}|{k[1]}|{k[2]}": v for k, v in data.items()}, indent=1) + "\n")
        print(md)
        return
    names = []
    for design in a.designs:
        for period in ([10] if design in CONFIG["socs"] else a.periods):
            for v in a.variants:
                for s in a.seeds:
                    if a.xprep:
                        names.append(xprep(design, period, v, s, dry))
                        continue
                    r = pnr_one(design, period, v, s, dry)
                    if not dry:
                        print(f"  {design} p{period:g} {v} s{s}: {r.get('result', {}).get('fmax')} MHz (nextpnr) "
                              f"{r.get('pnr', {}).get('seconds')} s {r.get('pnr', {}).get('error', '')}", flush=True)
    if names:
        print("names: " + " ".join(names))


if __name__ == "__main__":
    main()
