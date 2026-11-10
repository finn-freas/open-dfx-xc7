import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ofx import defaults

CONFIG = {
    "prefix": Path(os.environ.get("OFX_PREFIX", Path.home() / ".local" / "ofx")),
    "suite": ROOT / "build" / "qor_suite",
    "out": ROOT / "build" / "synth_noop_suite",
    "extra": {"blinky": (["designs/blinky/blinky.v"], "blinky"),
              "rv_soc": (["designs/rv_soc/rv_soc.v", "designs/rv_soc/uart.v", "designs/rv_soc/picorv32.v",
                          "designs/rv_soc/pr/rm_stub.v"], "rv_soc")},
}


def designs():
    out = {k: ([ROOT / f for f in fs], top) for k, (fs, top) in CONFIG["extra"].items()}
    for d in sorted(CONFIG["suite"].iterdir()):
        s = d / "src"
        if (s / "files.txt").exists() and (s / "top.txt").exists():
            files = [s / f for f in (s / "files.txt").read_text().split()]
            out[d.name] = (files, (s / "top.txt").read_text().strip())
    return out


def synth(yosys, files, top, script, out):
    js = out / "net.json"
    if js.exists() and js.stat().st_size:
        return js, 0.0
    out.mkdir(parents=True, exist_ok=True)
    rtl = " ".join(str(f) for f in files)
    ys = f"read_verilog -sv {rtl}; {script.replace('{top}', top)}; write_json {js}"
    t0 = time.time()
    with open(out / "yosys.log", "w") as f:
        r = subprocess.run([str(yosys), "-p", ys], stdout=f, stderr=subprocess.STDOUT)
    if r.returncode:
        js.unlink(missing_ok=True)
    return js, time.time() - t0


def body(p):
    return [l for l in p.read_text().splitlines() if '"creator":' not in l]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("option", help="ofx [build] option to switch on, e.g. dsp_init or clkbuf_keep_buffer_inputs")
    ap.add_argument("--prefix", default=str(CONFIG["prefix"]))
    ap.add_argument("--plugins", default=None)
    ap.add_argument("--out", default=str(CONFIG["out"]))
    ap.add_argument("--designs", nargs="*", default=None)
    a = ap.parse_args()
    prefix = Path(a.prefix).resolve()
    yosys = prefix / "opt" / "oss-cad-suite" / "bin" / "yosys"
    plugins = Path(a.plugins).resolve() if a.plugins else prefix / "share" / "ofx" / "yosys-plugins"
    base = dict(defaults.CONFIG["defaults"], **{a.option: False})
    on = dict(base, **{a.option: True})
    out = Path(a.out).resolve() / a.option
    res, ok = {}, True
    for name, (files, top) in designs().items():
        if a.designs and name not in a.designs:
            continue
        xdc = next(iter(sorted(files[0].parent.glob("*.xdc"))), Path("/dev/null"))
        s0, _ = defaults.synth_script(base, xdc, plugins)
        s1, _ = defaults.synth_script(on, xdc, plugins)
        j0, _ = synth(yosys, files, top, s0, out / name / "defaults")
        j1, _ = synth(yosys, files, top, s1, out / name / "option")
        b0, b1 = j0.exists() and j0.stat().st_size, j1.exists() and j1.stat().st_size
        if b0 and b1:
            same = body(j0) == body(j1)
            ok &= same
            res[name] = "identical" if same else "DIFFERS"
            print(f"{'PASS' if same else 'FAIL'} {name}: yosys JSON with {a.option} "
                  f"{'identical to' if same else 'differs from'} the defaults'", flush=True)
        elif not b0:
            res[name] = f"defaults fail, option {'synthesizes' if b1 else 'fails'}"
            print(f"INFO {name}: the defaults do not synthesize; with {a.option}: "
                  f"{'synthesizes' if b1 else 'fails too'}", flush=True)
        else:
            ok = False
            res[name] = "option fails"
            print(f"FAIL {name}: synthesizes with the defaults but not with {a.option}", flush=True)
    (out / "summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print(f"== {a.option}: {'PASS' if ok else 'FAIL'} ({sum(v == 'identical' for v in res.values())} identical)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
