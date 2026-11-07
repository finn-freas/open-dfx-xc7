#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../.."
export PATH=$PWD/toolchain/oss-cad-suite/bin:$PATH
D=designs/rv_soc
B=build/rv_soc
mkdir -p $B
python3 flow/rvasm.py $D/fw/main.s -o $D/fw/main.hex --lst $B/main.lst
python3 flow/rvasm.py $D/fw/isa_test.s -o $B/isa_test.hex --lst $B/isa_test.lst
RTL="$D/rv_soc.v $D/uart.v $D/picorv32.v $D/tb/icape2_model.v"
for v in add:sim/rm_add.v:RM_ADD xor:sim/rm_xor.v:RM_XOR dead:tb/rm_dead.v:RM_DEAD; do
  n=${v%%:*}; r=$(echo $v | cut -d: -f2); def=${v##*:}
  iverilog -g2005 -D$def -o $B/tb_isa_$n.vvp -s tb_isa $RTL $D/$r $D/tb/tb_isa.v
  vvp -n $B/tb_isa_$n.vvp | tee $B/tb_isa_$n.log
done
for v in add:sim/rm_add.v:RM_ADD xor:sim/rm_xor.v:RM_XOR; do
  n=${v%%:*}; r=$(echo $v | cut -d: -f2); def=${v##*:}
  iverilog -g2005 -D$def -o $B/tb_rv_soc_$n.vvp -s tb_rv_soc $RTL $D/$r $D/tb/tb_rv_soc.v
  vvp -n $B/tb_rv_soc_$n.vvp | tee $B/tb_rv_soc_$n.log
done
grep -h -E '^(PASS|FAIL)' $B/tb_*.log
