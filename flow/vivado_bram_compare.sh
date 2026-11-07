#!/usr/bin/env bash
V="${V:-build/vivado/dfx_bram}"
OUT="${OUT:-build/patched/vivado_compare/dfx_bram}"
REGION="${REGION:-SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59}"
CFGS="${CFGS:-rm_lut rm_lutmul grey}"
TABBY="${TABBY:-toolchain/openxc7/libexec/tabbypy3}"
cd "$(dirname "$0")/.."
mkdir -p "$OUT"
for c in $CFGS; do
  [ -f "$OUT/cfg_$c.fasm" ] || "$TABBY" flow/bit2fasm.py "$V/cfg_$c.bit" "$OUT/cfg_$c.fasm" > "$OUT/cfg_$c.bit2fasm.log" 2>&1
done
fasms=$(for c in $CFGS; do echo "$OUT/cfg_$c.fasm"; done)
for c in $CFGS; do
  python3 flow/partial.py "$V/cfg_$c.bit" "$OUT/open_$c" --design top --region "$REGION" --fasm "$OUT/cfg_$c.fasm" \
    --configs $fasms > "$OUT/open_$c.log" 2>&1 || echo "partial.py failed for $c ($OUT/open_$c.log)"
  python3 flow/partial_compare.py "$V/cfg_${c}_pblock_rm_partial.bit" "$OUT/open_$c.bit" --json "$OUT/compare_$c.json"
done
