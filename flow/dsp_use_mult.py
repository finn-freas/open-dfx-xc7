"""Decode the DSP48E1 USE_MULT bits that prjxray-db does not name (phase 10 §9: bit 26_277 of DSP_1 with USE_MULT=NONE).

Inputs are Vivado builds of designs/gap/dsp_um_{none,multiply,dynamic}: four DSP48E1 with identical settings
(AREG=BREG=CREG=PREG=1, MREG=0, OPMODE A:B+C) except USE_MULT, LOC'd to DSP48_X0Y0, X0Y1, X1Y0, X1Y1. Each bitstream
is decoded with flow/bit2fasm.py --verbose; prjxray names every bit it knows, the rest are unknown_bit lines
(flow/gap_report.unknown_bits). The script lists, per DSP tile, the named DSP features and the unknown bits of every
variant and the bits that differ between them.

  dsp_use_mult.py [--vivado-build DIR] [--out DIR]
"""
import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_report

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "vivado_build": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/dspum"),
    "out": ROOT / "build" / "dfxgaps" / "dspum",
    "variants": ["none", "multiply", "dynamic"],
    "tabbypy": ROOT / "toolchain" / "openxc7" / "libexec" / "tabbypy3",
}


def decode(bit, fasm):
    if not fasm.exists():
        fasm.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(CONFIG["tabbypy"]), str(ROOT / "flow" / "bit2fasm.py"), "--verbose", str(bit), str(fasm)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    feats = collections.defaultdict(set)
    for ln in fasm.read_text().splitlines():
        m = re.match(r"(DSP_[LR]_X\d+Y\d+)\.(DSP48\.DSP_[01]\.\S+)", ln.strip())
        if m:
            feats[m.group(1)].add(m.group(2))
    unk = collections.defaultdict(set)
    for tile, segbit in gap_report.unknown_bits(fasm):
        if tile.startswith("DSP_"):
            unk[tile].add(segbit)
    return feats, unk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vivado-build", default=str(CONFIG["vivado_build"]))
    ap.add_argument("--out", default=str(CONFIG["out"]))
    a = ap.parse_args()
    vb, out = Path(a.vivado_build), Path(a.out)
    res = {}
    for v in CONFIG["variants"]:
        n = f"dsp_um_{v}"
        feats, unk = decode(vb / n / f"{n}.bit", out / f"{n}.fasm")
        res[v] = {"features": {t: sorted(f) for t, f in feats.items()}, "unknown": {t: sorted(b) for t, b in unk.items()}}
    tiles = sorted({t for r in res.values() for t in r["features"]} | {t for r in res.values() for t in r["unknown"]})
    rep = {"variants": res, "per_tile": {}}
    for t in tiles:
        row = {}
        for v in CONFIG["variants"]:
            row[v] = {"unknown": res[v]["unknown"].get(t, []),
                      "features": [f for f in res[v]["features"].get(t, []) if "MASK" not in f and "PATTERN" not in f]}
        allu = set().union(*[set(row[v]["unknown"]) for v in row])
        row["unknown_by_variant"] = {b: [v for v in CONFIG["variants"] if b in row[v]["unknown"]] for b in sorted(allu)}
        fs = [set(row[v]["features"]) for v in CONFIG["variants"]]
        row["features_differ"] = {v: sorted(fs[k] - set.intersection(*fs)) for k, v in enumerate(CONFIG["variants"])}
        rep["per_tile"][t] = row
        print(f"{t}: unknown bits by variant {row['unknown_by_variant']}; named features only in: "
              f"{ {v: f for v, f in row['features_differ'].items() if f} }")
    out.mkdir(parents=True, exist_ok=True)
    (out / "dsp_use_mult.json").write_text(json.dumps(rep, indent=1) + "\n")


if __name__ == "__main__":
    main()
