import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_build

CONFIG = {
    "root": gap_build.ROOT,
    "designs": "designs/xdc",
    "out": "build/xdc",
    "variants": {
        "base": "build/nextpnr-build/router/nextpnr-himbaechel",
        "xdc": "build/nextpnr-build/xdc/nextpnr-himbaechel",
        "xdc2": "build/nextpnr-build/xdc2/nextpnr-himbaechel",
        "xdc3": "build/nextpnr-build/xdc3/nextpnr-himbaechel",
    },
    "own_synthesis": {
        "xdc2": {"yosys_plugin": "build/yosys-plugin/asyncreg/xilinx_asyncreg.so", "asyncreg_pass": "xilinx_asyncreg"},
        "xdc3": {"yosys_plugin": "build/yosys-plugin/asyncreg/xilinx_asyncreg.so", "asyncreg_pass": "xilinx_asyncreg"},
    },
    "chipdb": "toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin",
    "npwait": "ofx/npwait.sh",
    "freq_mhz": 100,
    "npr_args": ["--timing-allow-fail"],
    "dry_run": True,
    "xdc_msg": re.compile(r"(on line \d+|XDC|xdc|set_property|create_clock|clock group|false path|generated clock)"),
    "fmax": re.compile(r"Max frequency for clock\s+'([^']+)': ([\d.]+) MHz \((PASS|FAIL) at ([\d.]+) MHz\)"),
    "xpair": re.compile(r"Max (?:frequency|delay) for (.+?) -> (.+?): (.*)$"),
    "xreport": re.compile(r"Critical path report for cross-domain path '([^']+)' -> '([^']+)'"),
    "new_check": re.compile(r"Min delay \(|IOB TRUE|ASYNC_REG chain|clock placement|clock delay from its pad|"
                            r"Max delay for set_"),
    "io_feature": re.compile(r"^(?:LIOB33|RIOB33|LIOI3|RIOI3)[^ ]*\.(?:IOB_Y\d|OLOGIC_Y\d|ILOGIC_Y\d)\.\S+"),
}

ROOT = CONFIG["root"]


def summarize(out):
    log = out / "nextpnr.log"
    rec = {"log": str(log.relative_to(ROOT)) if log.exists() else None}
    if not log.exists():
        return rec
    text = log.read_text(errors="replace").splitlines()
    rec["xdc_messages"] = [ln.strip() for ln in text if ("Warning" in ln or "ERROR" in ln or "Info: set_" in ln or
                                                            "Info: create_" in ln) and CONFIG["xdc_msg"].search(ln)]
    rec["errors"] = [ln.strip() for ln in text if ln.startswith("ERROR")][:5]
    fmax = {}
    for ln in text:
        m = CONFIG["fmax"].search(ln)
        if m:
            fmax[m.group(1)] = {"fmax": float(m.group(2)), "status": m.group(3), "target": float(m.group(4))}
    rec["fmax"] = fmax
    rec["xclock_reports"] = sorted({f"{m.group(1)} -> {m.group(2)}" for ln in text for m in [CONFIG["xreport"].search(ln)] if m})
    rec["xclock_checks"] = [ln.split("Info: ")[-1].split("Warning: ")[-1].strip() for ln in text
                            if CONFIG["xpair"].search(ln)]
    rec["derived"] = [ln.split("Info: ")[-1].strip() for ln in text if "Derived frequency constraint" in ln]
    rec["new_checks"] = [ln.strip() for ln in text if CONFIG["new_check"].search(ln)]
    fasm = next(out.glob("*.fasm"), None)
    if fasm and fasm.exists():
        rec["io_features"] = sorted(ln.strip() for ln in fasm.read_text().splitlines() if CONFIG["io_feature"].match(ln))
    st = out / "status.json"
    if st.exists():
        rec["stages"] = {k: v.get("ok") for k, v in json.loads(st.read_text())["stages"].items()}
    return rec


def build_one(name, variant, binary, dry):
    src = ROOT / CONFIG["designs"] / name
    out = ROOT / CONFIG["out"] / name / variant
    first = ROOT / CONFIG["out"] / name / next(iter(CONFIG["variants"]))
    js = first / f"{name}.json"
    own = CONFIG["own_synthesis"].get(variant)
    if not own and variant != next(iter(CONFIG["variants"])) and js.exists() and not (out / js.name).exists():
        out.mkdir(parents=True, exist_ok=True)
        if not dry:
            shutil.copy(js, out / js.name)
    os.environ["OFX_NEXTPNR_BIN"] = str(ROOT / binary)
    tools = {"nextpnr": str(ROOT / CONFIG["npwait"]), "chipdb": str(ROOT / CONFIG["chipdb"])}
    if own:
        tools.update({"yosys_plugin": str(ROOT / own["yosys_plugin"]), "asyncreg_pass": own["asyncreg_pass"]})
    rtl = sorted(src.glob("*.v"))
    gap_build.build(name, src, name, rtl, next(src.glob("*.xdc")), out, CONFIG["freq_mhz"], dry,
                    CONFIG["npr_args"], tools)
    return summarize(out)


def main():
    ap = argparse.ArgumentParser(description="XDC coverage: build designs/xdc/* with each nextpnr variant")
    ap.add_argument("designs", nargs="*")
    ap.add_argument("--variant", action="append", help="variant key (default: all)")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    names = a.designs or sorted(p.name for p in (ROOT / CONFIG["designs"]).iterdir() if p.is_dir())
    variants = a.variant or list(CONFIG["variants"])
    sumf = ROOT / CONFIG["out"] / "summary.json"
    summary = json.loads(sumf.read_text()) if sumf.exists() else {}
    for v in variants:
        if not (ROOT / CONFIG["variants"][v]).exists():
            print(f"[skip] variant {v}: {CONFIG['variants'][v]} not built")
            continue
        for n in names:
            summary.setdefault(n, {})[v] = build_one(n, v, CONFIG["variants"][v], dry)
    if not dry:
        sumf.parent.mkdir(parents=True, exist_ok=True)
        sumf.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"summary: {sumf}")


if __name__ == "__main__":
    main()
