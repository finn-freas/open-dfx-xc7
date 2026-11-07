import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import device

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "part": device.get("part"),
    "family": device.get("family"),
    "seed": 1,
    "freq_mhz": os.environ.get("OFX_FREQ_MHZ") or 100,
    "dry_run": True,
    "nextpnr": None,
    "chipdb": None,
}

ROOT = CONFIG["root"]
OXC7 = ROOT / "toolchain" / "openxc7"
OCS = ROOT / "toolchain" / "oss-cad-suite"
DB = OXC7 / "share" / "nextpnr" / "external" / "prjxray-db"


def tool(name):
    for base in (OXC7 / "bin", OCS / "bin"):
        if (base / name).exists():
            return str(base / name)
    sys.exit(f"missing tool {name}")


def stage(name, out, cmd, log, dry):
    if out.exists():
        print(f"[skip] {name}: {out.name} exists")
        return
    print(f"[{'dry' if dry else 'run'}] {name}: {' '.join(cmd)}")
    if dry:
        return
    t0 = time.time()
    with open(log, "w") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    print(f"        {time.time() - t0:.1f}s, log {log.name}")
    if r.returncode != 0 or not out.exists():
        sys.exit(f"{name} failed, see {log}")


def versions():
    info = json.loads((ROOT / "toolchain" / "openxc7-BUILD-INFO.json").read_text())
    ys = subprocess.run([tool("yosys"), "-V"], capture_output=True, text=True).stdout.strip()
    return {
        "yosys": ys,
        "oss_cad_suite": (OCS / "VERSION").read_text().strip(),
        "openxc7_release": info["release-tag"],
        "nextpnr_xilinx": info["nextpnr-xilinx-revision"],
        "prjxray": info["prjxray-revision"],
        "prjxray_db": info["prjxray-db-revision"],
        "fasm": info["fasm-revision"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design")
    ap.add_argument("--top")
    ap.add_argument("--xdc")
    ap.add_argument("--part", default=CONFIG["part"])
    ap.add_argument("--family", help="prjxray-db family (default: the configured family, or looked up for a --part "
                                     "other than the configured one)")
    ap.add_argument("--freq", default=CONFIG["freq_mhz"], help="nextpnr --freq target in MHz")
    ap.add_argument("--seed", type=int, default=CONFIG["seed"])
    ap.add_argument("--rtl", nargs="+", help="source files relative to the design dir (default: all .v/.sv)")
    ap.add_argument("--name", help="build name (default: <part>_s<seed>)")
    ap.add_argument("--opt", action="append", default=[], help="extra nextpnr -o option, e.g. preplaced=FILE")
    ap.add_argument("--stop-after", choices=["yosys"], help="stop after this stage")
    ap.add_argument("--json", help="use this synthesized json instead of running yosys")
    ap.add_argument("--nextpnr", default=CONFIG["nextpnr"], help="nextpnr binary to use instead of the toolchain's nextpnr-xilinx")
    ap.add_argument("--chipdb", default=CONFIG["chipdb"], help="chipdb file passed to nextpnr as --chipdb")
    ap.add_argument("--out", help="output directory (default: build/openxc7/<design>/<name>)")
    ap.add_argument("--nextpnr-arg", action="append", default=[], help="extra nextpnr argument, e.g. --nextpnr-arg=--router2-region-keep-out")
    ap.add_argument("--synth", help="yosys synthesis commands instead of 'synth_xilinx -flatten -abc9 -arch xc7 -top TOP' "
                                     "({top} is replaced)")
    ap.add_argument("--db-root", help="prjxray-db root (with the family directories) for fasm2frames and xc7frames2bit")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    family = a.family or (CONFIG["family"] if a.part == CONFIG["part"] else device.resolve(a.part)["family"])
    src = ROOT / "designs" / a.design
    top = a.top or a.design
    xdc = Path(a.xdc) if a.xdc else next(src.glob("*.xdc"))
    out = Path(a.out).resolve() if a.out else ROOT / "build" / "openxc7" / a.design / (a.name or f"{a.part}_s{a.seed}")
    out.mkdir(parents=True, exist_ok=True)
    if a.rtl:
        rtl = [str(src / p) for p in a.rtl]
    else:
        rtl = sorted(str(p) for p in src.glob("*.v")) + sorted(str(p) for p in src.glob("*.sv"))
    extra = [x for o in a.opt for x in ("-o", o)] + a.nextpnr_arg
    npnr = str(Path(a.nextpnr).resolve()) if a.nextpnr else tool("nextpnr-xilinx")
    if a.chipdb:
        extra += ["--chipdb", str(Path(a.chipdb).resolve())]
    js, rjs, fasm, frames, bit = (out / f"{top}{e}" for e in (".json", "_routed.json", ".fasm", ".frames", ".bit"))
    synth = a.synth.replace("{top}", top) if a.synth else f"synth_xilinx -flatten -abc9 -arch xc7 -top {top}"
    ys = f"read_verilog -sv {' '.join(rtl)}; {synth}; write_json {js}"
    db = Path(a.db_root).resolve() if a.db_root else DB
    if a.json:
        stage("copy-json", js, ["cp", a.json, str(js)], out / "copy.log", dry)
    else:
        stage("yosys", js, [tool("yosys"), "-p", ys], out / "yosys.log", dry)
    if a.stop_after == "yosys":
        return
    stage("nextpnr", fasm, [npnr, "--device", a.part, "--json", str(js), "-o", f"xdc={xdc}",
                            "--seed", str(a.seed), "--freq", str(a.freq),
                            "--write", str(rjs), "-o", f"fasm={fasm}", "--report", str(out / "report.json")] + extra,
          out / "nextpnr.log", dry)
    stage("fasm2frames", frames, ["bash", "-c", f"{tool('fasm2frames')} --part {a.part} --db-root {db / family} {fasm} > {frames}"],
          out / "fasm2frames.log", dry)
    stage("xc7frames2bit", bit, [tool("xc7frames2bit"), f"--part_file={db / family / a.part / 'part.yaml'}",
                                 f"--part_name={a.part}", f"--frm_file={frames}", f"--output_file={bit}"],
          out / "xc7frames2bit.log", dry)
    if not dry:
        v = versions()
        if a.nextpnr:
            v["nextpnr_binary"] = npnr
            v["nextpnr_version"] = subprocess.run([npnr, "--version"], capture_output=True, text=True).stderr.strip()
        if a.chipdb:
            v["chipdb"] = str(Path(a.chipdb).resolve())
        if a.synth:
            v["synth"] = synth
        if a.db_root:
            v["prjxray_db_root"] = str(db)
        (out / "versions.json").write_text(json.dumps(v, indent=2) + "\n")
        print(f"bitstream: {bit}")


if __name__ == "__main__":
    main()
