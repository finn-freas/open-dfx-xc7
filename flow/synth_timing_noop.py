import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
import synth_timing

ROOT = qor_bench.ROOT

CONFIG = {
    "ref_variant": "fix_static",
    "drop_attrs": {"src"},
    "out": ROOT / "build" / "qor" / "synx" / "noop.json",
}


def canon(js, strip_src):
    j = json.loads(Path(js).read_text())
    j.pop("creator", None)
    if strip_src:
        for m in j["modules"].values():
            for c in m.get("cells", {}).values():
                for k in CONFIG["drop_attrs"]:
                    c.get("attributes", {}).pop(k, None)
            for n in m.get("netnames", {}).values():
                for k in CONFIG["drop_attrs"]:
                    n.get("attributes", {}).pop(k, None)
    return hashlib.sha256(json.dumps(j, sort_keys=True).encode()).hexdigest()[:16]


def ref_json(design, dry):
    if design in synth_timing.CONFIG["litex"]:
        return ROOT / "build" / "ddr3" / "arty_ddr3" / "gapfix" / "digilent_arty.json"
    return Path(qor_bench.synth(design, synth_timing.CONFIG["period_ns"], CONFIG["ref_variant"], dry)["json"])


def main():
    ap = argparse.ArgumentParser(description="No-op check: a synth_timing variant whose options are all off gives the same "
                                             "yosys JSON (creator line aside) as the default synth_xilinx flow")
    ap.add_argument("--designs", nargs="+", default=["rv_soc"])
    ap.add_argument("--variants", nargs="+", default=["t_split"])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = synth_timing.CONFIG["dry_run"] and not a.run
    res = json.loads(CONFIG["out"].read_text()) if CONFIG["out"].exists() else {}
    for d in a.designs:
        ref = ref_json(d, dry)
        for v in a.variants:
            r = synth_timing.synth(d, v, dry)
            if dry:
                continue
            same = canon(ref, False) == canon(r["json"], False)
            res[f"{d}/{v}"] = {"ref": str(ref), "new": r["json"], "identical_except_creator": same,
                               "identical_except_src": canon(ref, True) == canon(r["json"], True)}
            print(d, v, res[f"{d}/{v}"])
    if not dry:
        CONFIG["out"].write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
