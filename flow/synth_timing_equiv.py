import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
import synth_timing
import synth_timing_noop
from build_openxc7 import tool

ROOT = qor_bench.ROOT

CONFIG = {
    "out": ROOT / "build" / "qor" / "synx" / "equiv",
    "dry_run": True,
    "ulimit_kb": 6_000_000,
    "timeout_s": 3600,
    "seq": 8,
    "hard": ["RAMB36E1", "RAMB18E1", "RAM32M", "RAM64M", "RAM32X1D", "RAM64X1D", "RAM128X1D", "RAM256X1S", "RAM32X1S",
             "RAM64X1S", "RAM128X1S", "SRL16E", "SRLC32E", "ICAPE2", "DSP48E1", "IDELAYE2", "ODELAYE2", "ISERDESE2",
             "OSERDESE2", "IDELAYCTRL", "MMCME2_ADV", "PLLE2_ADV", "BUFGCTRL", "IBUF", "OBUF", "IOBUF", "OBUFT",
             "IBUFDS", "OBUFDS", "IOBUFDS", "IOBUFDS_INTERMDISABLE", "IOBUF_INTERMDISABLE", "STARTUPE2", "DNA_PORT", "XADC"],
    "hw_init": {"FDRE": "0", "FDCE": "0", "FDSE": "1", "FDPE": "1"},
    "flat": ["LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6", "INV", "CARRY4", "MUXF7", "MUXF8", "FDRE", "FDSE", "FDCE", "FDPE", "BUFG"],
    "sim_script": ROOT / "flow" / "qor_area_sim.sh",
    "sim_designs": ["rv_soc", "rv_mul", "rv_big"],
    "sim_nvec": 11,
}


def run(cmd, log, cwd=ROOT):
    shell = f"ulimit -v {CONFIG['ulimit_kb']}; exec " + " ".join(synth_timing._q(c) for c in cmd)
    with open(log, "w") as f:
        try:
            return subprocess.run(["bash", "-c", shell], stdout=f, stderr=subprocess.STDOUT, cwd=cwd,
                                  timeout=CONFIG["timeout_s"]).returncode
        except subprocess.TimeoutExpired:
            return "timeout"


def hw_init(js, dst):
    j = json.loads(Path(js).read_text())
    n = 0
    for m in j["modules"].values():
        for c in m.get("cells", {}).values():
            v = CONFIG["hw_init"].get(c["type"])
            if v is None:
                continue
            init = c.get("parameters", {}).get("INIT")
            if init is None or set(str(init)) <= {"x", "X"}:
                c.setdefault("parameters", {})["INIT"] = v
                n += 1
    dst.write_text(json.dumps(j))
    return n


def prep_side(js, side, out):
    il = out / f"{side}.il"
    if il.exists():
        return il
    hard = " ".join(f"t:{t}" for t in CONFIG["hard"])
    flat = " ".join(f"t:{t}" for t in CONFIG["flat"])
    js_hw = out / f"{side}.hw.json"
    n = hw_init(js, js_hw)
    (out / f"{side}.hw_init.txt").write_text(f"{n} flip-flops without INIT given the device power-up value\n")
    js = js_hw
    ys = (f"read_json {js}; hierarchy -auto-top; rename -top {side}; select -set hard {hard}; expose -evert @hard; select -clear; "
          f"read_verilog -lib +/xilinx/cells_xtra.v; techmap -autoproc -map +/xilinx/cells_sim.v {flat}; "
          f"proc; opt_clean; select {side}; write_rtlil -selected {il}")
    rc = run([tool("yosys"), "-p", ys], out / f"{side}.prep.log")
    if rc != 0:
        sys.exit(f"prep {side} failed: {out / (side + '.prep.log')}")
    return il


def check_struct(out, gold, gate):
    log = out / "struct.log"
    if not log.exists() or "Equivalence" not in log.read_text(errors="replace"):
        ys = (f"read_rtlil {gold}; read_rtlil {gate}; async2sync; equiv_make gold gate equiv; hierarchy -top equiv; "
              f"equiv_struct; equiv_simple -seq {CONFIG['seq']}; equiv_induct -seq {CONFIG['seq']}; equiv_status")
        run([tool("yosys"), "-p", ys], log)
    t = log.read_text(errors="replace")
    m = re.search(r"Found (\d+) \$equiv cells.*?Of those cells (\d+) are proven and (\d+) are unproven", t, re.S)
    ok = "Equivalence successfully proven" in t
    return {"proven": ok, "equiv_cells": int(m.group(1)) if m else None, "unproven": int(m.group(3)) if m else None,
            "log": str(log.relative_to(ROOT))}


def check_seq(out, gold, gate):
    log = out / "seq.log"
    aig = out / "miter.aig"
    if not aig.exists():
        ys = (f"read_rtlil {gold}; read_rtlil {gate}; async2sync; miter -equiv -flatten -ignore_gold_x gold gate miter; "
              f"hierarchy -top miter; flatten; opt_clean; dffunmap; simplemap; opt_clean; zinit; aigmap; write_aiger -zinit -map {out / 'miter.map'} {aig}")
        rc = run([tool("yosys"), "-p", ys], out / "miter.log")
        if rc != 0:
            return {"proven": False, "error": f"miter failed ({out / 'miter.log'})"}
    if not log.exists() or "Time" not in log.read_text(errors="replace"):
        run([tool("yosys-abc"), "-c", f"read_aiger {aig}; print_stats; dprove -v"], log)
    t = log.read_text(errors="replace")
    ok = bool(re.search(r"Networks are equivalent|UNSAT|Property proved", t))
    bad = bool(re.search(r"NOT EQUIVALENT|Networks are NOT|asserted|SATISFIABLE|counter-example|fails", t)) and not ok
    return {"proven": ok, "failed": bad, "log": str(log.relative_to(ROOT))}


def check_sim(design, out, ref, gate):
    if design not in CONFIG["sim_designs"]:
        return {"skipped": "no firmware testbench"}
    sim_out = out / "sim"
    log = sim_out / design / "sim.log"
    if not log.exists() or "LOCKSTEP cycles" not in log.read_text(errors="replace"):
        env = {"DRY_RUN": "0", "DESIGNS": design, "OUT": str(sim_out.relative_to(ROOT)), "GOLD_JSON": str(ref),
               "GATE_JSON": str(gate), "NVEC": str(CONFIG["sim_nvec"])}
        subprocess.run(["bash", "-c", " ".join(f"{k}={synth_timing._q(v)}" for k, v in env.items()) + " bash " +
                        synth_timing._q(CONFIG["sim_script"])], cwd=ROOT, timeout=CONFIG["timeout_s"])
    t = log.read_text(errors="replace") if log.exists() else ""
    lock = re.search(r"LOCKSTEP cycles (\d+) mismatches (\d+) tx_edges (\d+)", t)
    done = re.search(r"^DONE .*$", t, re.M)
    if not lock:
        return {"passed": False, "error": "no LOCKSTEP line", "log": str(log.relative_to(ROOT))}
    cyc, mism, edges = (int(x) for x in lock.groups())
    return {"passed": mism == 0 and edges > 0 and bool(done) and " fails=0 " in done.group(0), "cycles": cyc, "mismatches": mism, "tx_edges": edges,
            "done": done.group(0) if done else None, "log": str(log.relative_to(ROOT))}


def main():
    ap = argparse.ArgumentParser(description="Equivalence of a synth_timing variant's netlist against the default yosys netlist: "
                                             "struct (equiv_make/simple/induct, matching registers) and seq (miter + ABC dprove, "
                                             "for retiming); hard blocks are cut as free inputs/outputs")
    ap.add_argument("--designs", nargs="+", default=["rv_soc"])
    ap.add_argument("--variants", nargs="+", default=["t_cal"])
    ap.add_argument("--checks", nargs="+", default=["struct", "seq", "sim"])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    resf = CONFIG["out"] / "results.json"
    res = json.loads(resf.read_text()) if resf.exists() else {}
    for d in a.designs:
        ref = synth_timing_noop.ref_json(d, dry)
        for v in a.variants:
            r = synth_timing.synth(d, v, dry)
            out = CONFIG["out"] / d / f"{v}_{r.get('key')}"
            if dry:
                print(f"[dry] {d} {v}: {ref} vs {r['json']} -> {out.relative_to(ROOT)} ({' '.join(a.checks)})")
                continue
            out.mkdir(parents=True, exist_ok=True)
            gold = prep_side(ref, "gold", out)
            gate = prep_side(r["json"], "gate", out)
            rec = res.get(f"{d}/{v}", {})
            rec.update({"gold": str(ref), "gate": r["json"], "key": r.get("key")})
            if "struct" in a.checks:
                rec["struct"] = check_struct(out, gold, gate)
            if "seq" in a.checks:
                rec["seq"] = check_seq(out, gold, gate)
            if "sim" in a.checks:
                rec["sim"] = check_sim(d, out, ref, r["json"])
            res[f"{d}/{v}"] = rec
            print(d, v, json.dumps({k: rec.get(k) for k in ("struct", "seq", "sim")}), flush=True)
            resf.parent.mkdir(parents=True, exist_ok=True)
            resf.write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
