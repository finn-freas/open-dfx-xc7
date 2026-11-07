#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../.."
export PATH=$PWD/toolchain/oss-cad-suite/bin:$PATH
D=designs/rv_soc2
P=designs/rv_soc/pr
B=build/rv_soc2
RP1="${RP1:-xor andn}"
RP2="${RP2:-add grey}"
mkdir -p $B
python3 flow/rvasm.py $D/fw/main.s -o $D/fw/main.hex --lst $B/main.lst
RTL="$D/rv_soc.v $D/uart.v $D/picorv32.v $D/tb/icape2_model.v $D/tb/slot_models.v"
for r2 in $RP2; do
  sed 's/module rm_core\b/module rm_core2/' $P/rm_core_$r2.v > $B/rm_core2_$r2.v
done
for r1 in $RP1; do
  for r2 in $RP2; do
    n=${r1}_${r2}
    iverilog -g2005 -o $B/tb_rv_soc2_$n.vvp -s tb_rv_soc2 $RTL $P/rm_core_$r1.v $B/rm_core2_$r2.v $D/tb/tb_rv_soc2.v
    vvp -n $B/tb_rv_soc2_$n.vvp +RM1=$r1 +RM2=$r2 > $B/tb_rv_soc2_$n.log
  done
done
grep -h -E '^(PASS|FAIL)' $B/tb_rv_soc2_*.log
