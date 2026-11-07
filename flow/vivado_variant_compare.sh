#!/usr/bin/env bash
DESIGN="${DESIGN:-dfx_ref}"
declare -A REGIONS=([dfx_ref]=SLICE_X12Y100:SLICE_X15Y149 [dfx_bram]=SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59
  [dfx_dsp]=SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59 [dfx_2row]=SLICE_X12Y50:SLICE_X15Y149)
declare -A CFGSETS=([dfx_ref]="rm_count rm_shift grey" [dfx_bram]="rm_lut rm_lutmul grey" [dfx_dsp]="rm_dspa rm_dspb rm_nodsp grey"
  [dfx_2row]="rm_count rm_shift rm_big grey")
REGION="${REGION:-${REGIONS[$DESIGN]}}"
CFGS="${CFGS:-${CFGSETS[$DESIGN]}}"
VARIANTS="${VARIANTS:-base rar cmp rarcmp}"
FLUSHES="${FLUSHES:-zero next}"
EXTRA="${EXTRA:-}"
TABBY="${TABBY:-toolchain/openxc7/libexec/tabbypy3}"
V="${V:-build/vivado/$DESIGN}"
OUT="${OUT:-build/phase10/vivado_compare/$DESIGN}"
cd "$(dirname "$0")/.."
mkdir -p "$OUT"
for c in $CFGS; do
  [ -f "$OUT/cfg_$c.fasm" ] || "$TABBY" flow/bit2fasm.py "$V/cfg_$c.bit" "$OUT/cfg_$c.fasm" > "$OUT/cfg_$c.bit2fasm.log" 2>&1
done
[ -f "$OUT/static_pips.fasm" ] || python3 flow/vivado_pips.py "$V/pips/static_routed.pips.txt" "$OUT/static_pips.fasm"
set -- $CFGS
fail=0
for v in $VARIANTS; do
  case $v in base) opt="";; rar) opt=--reset-after-reconfig;; cmp) opt=--compress;; rarcmp) opt="--reset-after-reconfig --compress";; esac
  for fl in $FLUSHES; do
    case $v in base|rar) [ "$fl" = "${FLUSHES%% *}" ] || continue;; esac
    for c in $CFGS; do
      other=$1; [ "$other" = "$c" ] && other=$2
      n="${v}_${fl}_$c"
      ref="$V/$v/cfg_${c}_pblock_rm_partial.bit"; [ "$v" = base ] && ref="$V/cfg_${c}_pblock_rm_partial.bit"
      python3 flow/partial.py "$V/cfg_$c.bit" "$OUT/$n" --design top --region "$REGION" --fasm "$OUT/cfg_$c.fasm" \
        --static-pip-list "$OUT/static_pips.fasm" --pass1-hold-hclk --compress-flush "$fl" $opt $EXTRA \
        --base "$V/cfg_$other.bit" --simulate > "$OUT/$n.log" 2>&1 || { echo "FAIL partial.py $n ($OUT/$n.log)"; fail=1; }
      sim=$(grep -E "^crc:" "$OUT/$n.log")
      cmpline=$(python3 flow/partial_compare.py "$ref" "$OUT/$n.bit" --json "$OUT/compare_$n.json" | head -1)
      echo "$n | $(echo "$cmpline" | sed -E 's/.*: ([0-9]+ vs [0-9]+ words after sync, [0-9]+ differ).*/\1/') | $sim"
    done
  done
done
exit $fail
