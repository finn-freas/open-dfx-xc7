import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse
import gap_build

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "out": "build/xdc_noop",
    "npwait": "ofx/npwait.sh",
    "chipdb": "toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin",
    "variants": {
        "router": "build/nextpnr-build/router/nextpnr-himbaechel",
        "xdc": "build/nextpnr-build/xdc/nextpnr-himbaechel",
        "xdc2": "build/nextpnr-build/xdc2/nextpnr-himbaechel",
        "xdc3": "build/nextpnr-build/xdc3/nextpnr-himbaechel",
        "corners": "build/nextpnr-build/corners/nextpnr-himbaechel",
    },
    "reference": "router",
    "new": "xdc2",
    "yosys": "toolchain/oss-cad-suite/bin/yosys",
    "yosys_plugin": ("build/yosys-plugin/asyncreg/xilinx_asyncreg.so", "xilinx_asyncreg"),
    "yosys_designs": {
        "blinky": (["designs/blinky/blinky.v"], "designs/blinky/arty_a7_35t.xdc", "blinky"),
        "rv_soc": (["designs/rv_soc/rv_soc.v", "designs/rv_soc/uart.v", "designs/rv_soc/picorv32.v",
                    "designs/rv_soc/sim/rm_add.v"], "designs/rv_soc/arty_a7_35t.xdc", "rv_soc"),
    },
    "flat": {
        "blinky": "build/openxc7/blinky/xc7a35tcsg324-1_s1/blinky.json",
        "rv_soc": "build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.json",
    },
    "native": {
        "rv_pr": {"argv": ["--rms", "xor", "andn", "add", "rot", "popc", "minmax", "--timing-allow-fail", "popc",
                           "minmax"],
                  "reference": "build/patched/rv_pr_native/router", "base_variant": "router"},
    },
    "dry_run": True,
}

ROOT = CONFIG["root"]


def frames_differ(a, b):
    part = bitparse.Part()
    fa, fb = bitparse.parse(str(a), part)["frames"], bitparse.parse(str(b), part)["frames"]
    zero = [0] * 101
    return sum(fa.get(k, zero) != fb.get(k, zero) for k in set(fa) | set(fb))


def run(cmd, log, env, dry):
    print(f"[{'dry' if dry else 'run'}] {' '.join(cmd)}")
    if dry:
        return 0
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w") as f:
        return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=ROOT).returncode


def flat(name, dry):
    res = {}
    for v in (CONFIG["reference"], CONFIG["new"]):
        binary = CONFIG["variants"][v]
        out = ROOT / CONFIG["out"] / name / v
        env = dict(os.environ, OFX_NEXTPNR_BIN=str(ROOT / binary))
        cmd = [sys.executable, str(ROOT / "flow" / "build_openxc7.py"), name, "--json", str(ROOT / CONFIG["flat"][name]),
               "--nextpnr", str(ROOT / CONFIG["npwait"]), "--chipdb", str(ROOT / CONFIG["chipdb"]),
               "--out", str(out), "--run"]
        run(cmd, ROOT / CONFIG["out"] / f"{name}_{v}.log", env, dry)
        res[v] = out / f"{name}.bit"
    if dry or not all(p.exists() for p in res.values()):
        return {"done": False}
    a, b = res.values()
    return {"variant": CONFIG["new"], "bits": [str(p.relative_to(ROOT)) for p in res.values()],
            "frames_differ": frames_differ(a, b)}


def yosys_noop(name, dry):
    files, xdc_file, top = CONFIG["yosys_designs"][name]
    rtl = [str(ROOT / f) for f in files]
    xdc = ROOT / xdc_file
    out = ROOT / CONFIG["out"] / "yosys" / name
    base = f"synth_xilinx -flatten -abc9 -arch xc7 -top {top}"
    plugin, cmd = CONFIG["yosys_plugin"]
    runs_pass = gap_build.uses_async_reg(rtl + [xdc])
    read = f"read_verilog -sv {' '.join(rtl)}"
    split = f"{base} -run :coarse; {cmd} -xdc {xdc}; {base} -run coarse:"
    scripts = {
        "plain": f"{read}; {base}; write_json {out / 'plain.json'}",
        "flow": f"{read}; {split if runs_pass else base}; write_json {out / 'flow.json'}",
        "split_pass": f"{read}; {split}; write_json {out / 'split_pass.json'}",
        "split_only": f"{read}; {base} -run :coarse; {base} -run coarse:; write_json {out / 'split_only.json'}",
    }
    for k, ys in scripts.items():
        if (out / f"{k}.json").exists():
            continue
        if not dry:
            out.mkdir(parents=True, exist_ok=True)
        run([str(ROOT / CONFIG["yosys"]), "-m", str(ROOT / plugin), "-p", ys], out / f"{k}.log", dict(os.environ),
            dry)
    if dry:
        return {"done": False}
    plain = (out / "plain.json").read_bytes()
    return {"flow_runs_pass": runs_pass,
            **{f"{k}_identical_to_plain": (out / f"{k}.json").read_bytes() == plain for k in scripts if k != "plain"},
            "dir": str(out.relative_to(ROOT))}

def native(name, dry):
    spec = CONFIG["native"][name]
    new = CONFIG["new"]
    out = ROOT / CONFIG["out"] / name / new
    job = ROOT / CONFIG["out"] / f"{name}_{new}_job.py"
    text = (f"import os, sys\nsys.path.insert(0, {str(ROOT / 'flow')!r})\n"
            f"sys.argv = ['build_pr_native.py', '--design', {name!r}, '--variant', {new!r}, '--out', {str(out)!r}] + "
            f"{spec['argv']!r} + ['--run']\n"
            "import build_pr_native as b\n"
            f"var = dict(b.CONFIG['variants'][{spec['base_variant']!r}])\n"
            f"var['nextpnr'] = {CONFIG['npwait']!r}\n"
            f"b.CONFIG['variants'][{new!r}] = var\n"
            f"os.environ['OFX_NEXTPNR_BIN'] = {str(ROOT / CONFIG['variants'][new])!r}\n"
            "b.main()\n")
    if not dry:
        job.parent.mkdir(parents=True, exist_ok=True)
        job.write_text(text)
    run([sys.executable, str(job)], ROOT / CONFIG["out"] / f"{name}_{new}.log", dict(os.environ), dry)
    if dry:
        return {"done": False}
    ref = ROOT / spec["reference"]
    cmp = {}
    for nb in sorted(out.rglob("*.bit")):
        if "icapbits" in nb.name:
            continue
        rel = nb.relative_to(out / new)
        ob = ref / rel
        cmp[str(rel)] = frames_differ(nb, ob) if ob.exists() else "new-only"
    return {"variant": new, "reference": spec["reference"], "frames_differ": cmp}


def main():
    ap = argparse.ArgumentParser(description="no-op check: frames with the xdc variant vs the router variant")
    ap.add_argument("names", nargs="*", default=list(CONFIG["flat"]) + list(CONFIG["native"]))
    ap.add_argument("--yosys", action="store_true", help="the yosys no-op check of the ASYNC_REG pass instead")
    ap.add_argument("--new", default=CONFIG["new"], choices=sorted(CONFIG["variants"]))
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    CONFIG["new"] = a.new
    dry = CONFIG["dry_run"] and not a.run
    result = {}
    for n in a.names:
        if a.yosys:
            if n in CONFIG["yosys_designs"]:
                result[f"yosys_{n}"] = yosys_noop(n, dry)
                print(n, json.dumps(result[f"yosys_{n}"]))
            continue
        key = n if CONFIG["new"] == "xdc" else f"{n}_{CONFIG['new']}"
        result[key] = flat(n, dry) if n in CONFIG["flat"] else native(n, dry)
        n = key
        print(n, json.dumps(result[n]))
    if not dry:
        f = ROOT / CONFIG["out"] / "noop.json"
        old = json.loads(f.read_text()) if f.exists() else {}
        old.update(result)
        f.write_text(json.dumps(old, indent=2) + "\n")


if __name__ == "__main__":
    main()
