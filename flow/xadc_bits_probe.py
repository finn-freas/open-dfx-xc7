"""Which Vivado XADC bits that prjxray-db does not decode follow the XADC clock pins.

Variants of designs/gap/xadc_fz_none built by Vivado (vivado/run_gap.ps1 -Tag xadcinv):
  xadc_inv_dclk  IS_DCLK_INVERTED=1          xadc_inv_cclk  IS_CONVSTCLK_INVERTED=1
  xadc_cclk_clk  CONVSTCLK driven by clk     xadc_dclk0     DCLK tied to 0 (no DRP clock)
The base (xadc_fz_none, gap2 build) sets 3 undecoded bits: INT_L_X18Y79 26_00, 27_40 and HCLK_L_X49Y78 25_13.
Prints, per design, the undecoded bits (tile segbit and raw frame/word/bit) and the HCLK/INT clock features
around the XADC, so each bit can be tied to a pin and a polarity.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_report

CONFIG = {
    "tag": "xadcinv",
    "designs": ["xadc_fz_none", "xadc_inv_dclk", "xadc_inv_cclk", "xadc_cclk_clk", "xadc_dclk0"],
    "base_tag": {"xadc_fz_none": "gap2"},
    "near": re.compile(r"^(HCLK_L_X49Y78|INT_L_X18Y(7[5-9]|8[0-4])|MONITOR_BOT_X46Y79)\."),
}
ROOT = gap_report.ROOT


def raw(fasm_file):
    return re.findall(r'unknown_bit = "([0-9a-f]{8})_(\d+)_(\d+)"', fasm_file.read_text())


def main():
    rows = {}
    for d in CONFIG["designs"]:
        dst = gap_report.ingest(d, CONFIG["base_tag"].get(d, CONFIG["tag"]))
        if dst is None:
            print(f"{d}: no Vivado build")
            continue
        bit = dst / f"{d}.bit"
        fasm = gap_report.decode(bit, dst / f"{d}.viv.fasm")
        unk = gap_report.unknown_bits(fasm)
        feats = [l.strip() for l in fasm.read_text().splitlines()
                 if CONFIG["near"].match(l.strip()) and "INIT_" not in l]
        rows[d] = set(f"{t}:{b}" for t, b in unk)
        print(f"== {d}")
        print("   undecoded:", " ".join(sorted(rows[d])) or "-")
        print("   raw:", " ".join("_".join(x) for x in raw(fasm)) or "-")
        for f in feats:
            print("   ", f)
    if "xadc_fz_none" in rows:
        base = rows["xadc_fz_none"]
        print("\ndelta vs xadc_fz_none:")
        for d, s in rows.items():
            if d != "xadc_fz_none":
                print(f"  {d}: +{sorted(s - base)} -{sorted(base - s)}")


if __name__ == "__main__":
    main()
