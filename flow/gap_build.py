import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_openxc7 import CONFIG as OXC7_CONFIG, DB, tool, versions

CONFIG = {
    "root": OXC7_CONFIG["root"],
    "part": OXC7_CONFIG["part"],
    "family": OXC7_CONFIG["family"],
    "seed": 1,
    "freq_mhz": 100,
    "jobs": 4,
    "timeout_s": 3600,
    "dry_run": True,
    "nextpnr": None,
    "chipdb": None,
    "yosys": None,
    "async_reg_re": re.compile(r"\bASYNC_REG\b", re.IGNORECASE),
    "err_re": re.compile(r"(ERROR|Error|error:|Traceback|terminate called|Assertion|Segmentation|FATAL|abort)"),
}

ROOT = CONFIG["root"]


def first_error(log):
    if not log.exists():
        return ""
    lines = log.read_text(errors="replace").splitlines()
    for i, ln in enumerate(lines):
        if CONFIG["err_re"].search(ln):
            return " | ".join(x.strip() for x in lines[i:i + 3] if x.strip())[:400]
    tail = [x for x in lines if x.strip()]
    return tail[-1][:400] if tail else ""


def run_stage(name, out, cmd, log, cwd, dry, rec):
    if out.exists() and out.stat().st_size > 0:
        rec["stages"][name] = rec["stages"].get(name) or {"ok": True, "cached": True}
        return True
    if dry:
        print(f"[dry] {name}: {' '.join(cmd)}")
        rec["stages"][name] = {"ok": None, "dry": True}
        return False
    t0 = time.time()
    with open(log, "w") as f:
        try:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=cwd, timeout=CONFIG["timeout_s"])
            rc = r.returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    ok = rc == 0 and out.exists() and out.stat().st_size > 0
    rec["stages"][name] = {"ok": ok, "rc": rc, "seconds": round(time.time() - t0, 2),
                           "log": str(log.relative_to(ROOT)), "error": "" if ok else first_error(log)}
    return ok


def tool_versions(tools):
    v = versions()
    for k in ("nextpnr", "yosys"):
        if tools.get(k):
            v[f"{k}_binary"] = tools[k]
            r = subprocess.run([tools[k], "--version" if k == "nextpnr" else "-V"], capture_output=True, text=True)
            v[f"{k}_version"] = (r.stdout + r.stderr).strip()
    if tools.get("chipdb"):
        v["chipdb"] = tools["chipdb"]
    for k in ("json_from", "yosys_plugin", "clkbuf_pass", "asyncreg_pass", "db", "synth_opts", "xdc_keep"):
        if tools.get(k):
            v[k] = tools[k]
    return v


def uses_async_reg(files):
    return any(CONFIG["async_reg_re"].search(Path(f).read_text(errors="replace")) for f in files)


def build(name, src, top, rtl, xdc, out, freq, dry, npr_extra=(), tools=None):
    tools = tools or {}
    out.mkdir(parents=True, exist_ok=True)
    recf = out / "status.json"
    rec = json.loads(recf.read_text()) if recf.exists() else {}
    rec.update({"design": name, "top": top, "freq_mhz": freq, "stages": rec.get("stages", {})})
    js, rjs, fasm, frames, bit = (out / f"{top}{e}" for e in (".json", "_routed.json", ".fasm", ".frames", ".bit"))
    base = f"synth_xilinx -flatten -abc9 -arch xc7 -top {top}" + (f" {tools['synth_opts']}" if tools.get("synth_opts") else "")
    hooks = []
    if tools.get("xdc_keep"):
        import xdc_keep
        kc = xdc_keep.commands([str(r) for r in rtl], xdc)
        if kc:
            hooks.append(("prepare", "; ".join(kc), "prepare"))
    if tools.get("asyncreg_pass") and uses_async_reg(list(rtl) + [xdc]):
        hooks.append(("coarse", f"{tools['asyncreg_pass']} -xdc {xdc}", "coarse"))
    if tools.get("clkbuf_pass"):
        hooks.append(("finalize", f"{tools['clkbuf_pass']} -buf BUFG O:I; clean", "check"))
    parts, start = [], ""
    for stop, cmd, resume in hooks:
        parts += [f"{base} -run {start}:{stop}", cmd]
        start = resume
    sx = "; ".join(parts + [f"{base} -run {start}:"]) if hooks else base
    ys = (f"{tools.get('yosys_pre', '')}read_verilog -sv {' '.join(str(p) for p in rtl)}; {sx}; "
          f"tee -o {out / 'yosys_stat.txt'} stat; write_json {js}")
    if tools.get("json_from"):
        synth = ["cp", str(ROOT / "build" / "gap" / name / tools["json_from"] / f"{top}.json"), str(js)]
    else:
        plug = ["-m", tools["yosys_plugin"]] if tools.get("yosys_plugin") else []
        synth = [tools.get("yosys") or tool("yosys")] + plug + ["-p", ys]
    npr = [tools.get("nextpnr") or tool("nextpnr-xilinx")] + (["--chipdb", tools["chipdb"]] if tools.get("chipdb") else [])
    db = Path(tools["db"]) if tools.get("db") else DB
    steps = [
        ("synth", js, synth, out / "yosys.log"),
        ("pnr", fasm, npr + ["--device", CONFIG["part"], "--json", str(js), "-o", f"xdc={xdc}",
                             "--seed", str(CONFIG["seed"]), "--freq", str(freq), "--write", str(rjs),
                             "-o", f"fasm={fasm}", "--report", str(out / "report.json")] + list(npr_extra), out / "nextpnr.log"),
        ("fasm", frames, ["bash", "-c", f"{tool('fasm2frames')} --part {CONFIG['part']} --db-root {db / CONFIG['family']} "
                                       f"{fasm} > {frames}"], out / "fasm2frames.log"),
        ("bitstream", bit, [tool("xc7frames2bit"), f"--part_file={db / CONFIG['family'] / CONFIG['part'] / 'part.yaml'}",
                            f"--part_name={CONFIG['part']}", f"--frm_file={frames}", f"--output_file={bit}"],
         out / "xc7frames2bit.log"),
    ]
    for sname, sout, cmd, log in steps:
        if not run_stage(sname, sout, cmd, log, src, dry, rec):
            break
    if not dry:
        rec["versions"] = tool_versions(tools)
        recf.write_text(json.dumps(rec, indent=2) + "\n")
    print(f"{name}: " + " ".join(f"{k}={'ok' if v.get('ok') else ('dry' if v.get('dry') else 'FAIL')}"
                                 for k, v in rec["stages"].items()))
    return rec


def main():
    ap = argparse.ArgumentParser(description="openXC7 builds for the gap analysis, into build/gap/<name>/oxc7")
    ap.add_argument("designs", nargs="*", help="names under designs/gap (default: all)")
    ap.add_argument("--top")
    ap.add_argument("--rtl", nargs="+")
    ap.add_argument("--freq", type=int, default=CONFIG["freq_mhz"])
    ap.add_argument("--tag", default="oxc7", help="output subdir name")
    ap.add_argument("--jobs", type=int, default=CONFIG["jobs"])
    ap.add_argument("--npr-arg", action="append", default=[], help="extra nextpnr argument, e.g. --timing-allow-fail")
    ap.add_argument("--nextpnr", default=CONFIG["nextpnr"], help="nextpnr binary instead of the toolchain's nextpnr-xilinx")
    ap.add_argument("--chipdb", default=CONFIG["chipdb"], help="chipdb file passed to nextpnr as --chipdb")
    ap.add_argument("--yosys", default=CONFIG["yosys"], help="yosys binary instead of the toolchain's")
    ap.add_argument("--yosys-plugin", help="yosys plugin (.so) loaded with -m")
    ap.add_argument("--clkbuf-pass", help="run synth_xilinx up to finalize, then this pass instead of clkbufmap")
    ap.add_argument("--json-from", help="copy the synthesized json from build/gap/<name>/<this tag> instead of running yosys")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    absp = lambda x: str(Path(x).resolve()) if x else None
    tools = {"nextpnr": absp(a.nextpnr), "chipdb": absp(a.chipdb), "yosys": absp(a.yosys), "json_from": a.json_from,
             "yosys_plugin": absp(a.yosys_plugin), "clkbuf_pass": a.clkbuf_pass}
    dry = CONFIG["dry_run"] and not a.run
    gap = ROOT / "designs" / "gap"
    names = a.designs or sorted(p.name for p in gap.iterdir() if p.is_dir())

    def one(name):
        src = gap / name
        top = a.top or name
        rtl = [src / p for p in a.rtl] if a.rtl else sorted(src.glob("*.v")) + sorted(src.glob("*.sv"))
        xdc = next(src.glob("*.xdc"))
        return build(name, src, top, rtl, xdc, ROOT / "build" / "gap" / name / a.tag, a.freq, dry, a.npr_arg, tools)

    with ThreadPoolExecutor(max_workers=1 if dry else a.jobs) as ex:
        list(ex.map(one, names))


if __name__ == "__main__":
    main()
