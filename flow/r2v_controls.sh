#!/usr/bin/env bash
BIT="${BIT:-build/patched/rv_m_native/replay/tbl_n/rv_soc.bit}"
RM="${RM:-tbl}"
SYNTH="${SYNTH:-build/patched/rv_m_native/replay/rm_tbl_synth.json}"
SHELLV="${SHELLV:-build/patched/rv_m_native/replay/rm_shell_native.v}"
REGION="${REGION:-SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59}"
BRAM_TILE="${BRAM_TILE:-BRAM_L_X6Y125}"
OUT="${OUT:-build/patched/controls/rv_m}"
cd "$(dirname "$0")/.."
mkdir -p "$OUT"
fasm=$(python3 -c 'import sys; sys.path.insert(0, "flow"); import region2v; print(region2v.bit_to_fasm(sys.argv[1]))' "$BIT")
cp "$fasm" "$OUT/decoded.fasm"
python3 - "$OUT" "$BRAM_TILE" <<'EOF'
import re, sys
from pathlib import Path
out, tile = Path(sys.argv[1]), sys.argv[2]
src = (out / "decoded.fasm").read_text().splitlines()
def write(name, f):
    lines, hit = [], 0
    for l in src:
        n = f(l)
        hit += n != l
        lines.append(n)
    (out / f"{name}.fasm").write_text("\n".join(lines) + "\n")
    print(f"{name}: {hit} line(s) changed")
def dsp(l):
    m = re.match(r"(DSP_[LR]_X\d+Y\d+\.DSP48\.DSP_[01]\.ZIS_OPMODE_INVERTED\[6:0\] = 7'b)([01]{7})\s*$", l)
    return m.group(1) + m.group(2)[:6] + str(1 - int(m.group(2)[6])) if m else l
def bram(l):
    m = re.match(rf"({tile}\.RAMB18_Y0\.INIT_00\[\d+:0\] = \d+'b)([01]+)\s*$", l)
    return m.group(1) + m.group(2)[:-1] + str(1 - int(m.group(2)[-1])) if m else l
def mreg(l):
    m = re.match(r"(DSP_[LR]_X\d+Y\d+\.DSP48\.DSP_[01])\.ZPREG\[0\]\s*$", l)
    return l + "\n" + m.group(1) + ".ZMREG[0]" if m else l
write("corrupt_dsp_opmode0", dsp)
write("corrupt_dsp_mreg0", mreg)
write("corrupt_bram_init00_bit0", bram)
EOF
for c in corrupt_dsp_opmode0 corrupt_dsp_mreg0 corrupt_bram_init00_bit0; do
  python3 flow/region2v.py check "$OUT/$c.fasm" "$REGION" --shell "$SHELLV" --rm "$RM" --tag "ctl_$c" --sweep 1024 > "$OUT/$c.check.log" 2>&1
  python3 flow/region2v.py bram "$OUT/$c.fasm" "$REGION" --synth-json "$SYNTH" --tag "ctl_$c" > "$OUT/$c.bram.log" 2>&1
  echo "$c: check -> $(head -n 1 "$OUT/$c.check.log" | cut -c1-170)"
  echo "$c: bram  -> $(head -n 1 "$OUT/$c.bram.log" | cut -c1-220)"
done
python3 flow/region2v.py check "$BIT" "$REGION" --shell "$SHELLV" --rm "$RM" --tag "ctl_lut" --corrupt > "$OUT/corrupt_lut.check.log" 2>&1
echo "corrupt_lut: $(head -n 2 "$OUT/corrupt_lut.check.log" | cut -c1-220 | tr '\n' ' ')"
