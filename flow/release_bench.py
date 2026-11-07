import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import qor_bench as qb
from ofx import defaults

PREFIX = Path(os.environ.get("OFX_PREFIX", Path.home() / ".local" / "ofx"))
TMG = ["-o", "hardblock-timing"]
DCP = ["-o", "dsp-cascade-place"]
STATIC = ["--placer", "static"]

CONFIG = {
    "dry_run": True,
    "prefix": PREFIX,
    "designs": ["blinky", "rv_soc", "rv_mul", "rv_big", "bram", "fir"],
    "periods_ns": [5],
    "seeds": [1, 2, 3],
    "nextpnr": {
        "rel": ("bin/nextpnr-himbaechel", "share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin"),
        "rel_ofx": ("bin/nextpnr-himbaechel", "share/nextpnr/himbaechel/xilinx/ofx/chipdb-xc7a50t.bin"),
        "rel_cal": ("bin/nextpnr-himbaechel", "share/nextpnr/himbaechel/xilinx/cal/chipdb-xc7a50t.bin"),
    },
    "variants": {
        "rel_old": {"nextpnr": "rel", "args": [], "synth": "base"},
        "rel_tmg": {"nextpnr": "rel", "args": TMG, "synth": "base"},
        "rel_new": {"nextpnr": "rel", "args": DCP + STATIC, "synth": "defaults"},
        "rel_new_tmg": {"nextpnr": "rel", "args": TMG + DCP + STATIC, "synth": "defaults"},
        "rel_qor": {"nextpnr": "rel_cal", "args": TMG + DCP + STATIC, "synth": "qor"},
        "rel_qor_heap": {"nextpnr": "rel_cal", "args": TMG + DCP, "synth": "qor"},
        "rel_qor_stub": {"nextpnr": "rel", "args": TMG + DCP + STATIC, "synth": "qor"},
        "rel_qor_nopipe": {"nextpnr": "rel_cal", "args": TMG + DCP + STATIC, "synth": "base"},
    },
    "qor_options": {"hardblock_timing": True, "dsp_pipeline": True, "cell_timing": "auto"},
    "out": "build/qor/release_0_1.json",
    "npwait": Path(__file__).resolve().parent.parent / "ofx" / "npwait.sh",
}

ROOT = qb.ROOT


def setup():
    p = Path(CONFIG["prefix"])
    os.environ["OFX_NEXTPNR_BIN"] = str(p / "bin" / "nextpnr-himbaechel")
    for k, (b, c) in CONFIG["nextpnr"].items():
        qb.CONFIG["nextpnr"][k] = (str(CONFIG["npwait"]), p / c)
    qb.DB = p / "share" / "nextpnr" / "external" / "prjxray-db"
    plugins = p / "share" / "ofx" / "yosys-plugins"
    for name, v in CONFIG["variants"].items():
        qb.CONFIG["variants"][name] = {"nextpnr": v["nextpnr"], "args": v["args"], "seeds": CONFIG["seeds"],
                                       "synth_mode": v["synth"], "plugins": str(plugins)}
    base_variant = qb.variant

    def variant(name):
        v = base_variant(name)
        if v.get("synth_mode") in ("defaults", "qor"):
            opts = dict(defaults.CONFIG["defaults"])
            if v["synth_mode"] == "qor":
                opts.update(CONFIG["qor_options"])
            v["synth"], _ = defaults.synth_script(opts, CONFIG["_xdc"], Path(v["plugins"]))
        return v
    qb.variant = variant


def main():
    ap = argparse.ArgumentParser(description="ofx 0.1 defaults against the previous defaults on the qor designs "
                                             "(nextpnr timer; results under build/qor/oxc7/<variant>)")
    ap.add_argument("--designs", nargs="+", default=CONFIG["designs"])
    ap.add_argument("--variants", nargs="+", default=list(CONFIG["variants"]))
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    setup()
    rows = []
    for period in CONFIG["periods_ns"]:
        for d in a.designs:
            CONFIG["_xdc"] = qb.prepare_src(d, period) / "constraints.xdc"
            for v in a.variants:
                r = qb.pnr(d, period, v, dry)
                if dry:
                    continue
                runs = [{"seed": x.get("seed"), "fmax": x.get("result", {}).get("fmax"),
                         "pnr_ok": x.get("pnr", {}).get("ok"), "bit_ok": x.get("bitstream", {}).get("ok"),
                         "seconds": x.get("pnr", {}).get("seconds"),
                         "log": x.get("pnr", {}).get("log")} for x in r.get("runs", [])]
                fm = sorted(x["fmax"] for x in runs if x["fmax"])
                rows.append({"design": d, "period_ns": period, "variant": v, "stat": r["synth"].get("stat"),
                             "synth_log": r["synth"].get("log"), "runs": runs,
                             "mean": round(sum(fm) / len(fm), 2) if fm else None,
                             "min": fm[0] if fm else None, "max": fm[-1] if fm else None})
                print(f"{d:8s} {v:16s} " + " / ".join(f"{x:.2f}" for x in fm) + (f"  mean {rows[-1]['mean']}" if fm else " FAIL"),
                      flush=True)
    if not dry:
        (ROOT / CONFIG["out"]).write_text(json.dumps(rows, indent=1) + "\n")
        print(f"wrote {CONFIG['out']}")


if __name__ == "__main__":
    main()
