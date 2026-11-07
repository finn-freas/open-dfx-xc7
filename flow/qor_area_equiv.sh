#!/usr/bin/env bash
DRY_RUN="${DRY_RUN:-1}"
DESIGNS="${DESIGNS:-blinky rv_soc rv_mul rv_big bram fir}"
PERIOD="${PERIOD:-p5}"
OUT="${OUT:-build/qor/area/equiv}"
YOSYS="${YOSYS:-build/yosys-build/yosys-area/yosys}"
SEQ="${SEQ:-8}"
CHECKS="${CHECKS:-share cmw}"
CMW="${CMW:-5}"
declare -A TOP=([blinky]=qor_blinky [rv_soc]=qor_rv_soc [rv_mul]=qor_rv_mul [rv_big]=qor_rv_big [bram]=qor_bram [fir]=qor_fir)

cd "$(dirname "$0")/.."
ROOT=$PWD
B() { echo "synth_xilinx -flatten -abc9 -arch xc7 -top $1"; }

stage_script() {
  local top=$1 check=$2 side=$3
  local b; b=$(B "$top")
  case "$check/$side" in
    share/gold) echo "$b -run begin:fine" ;;
    share/gate) echo "$b -share_aggressive -run begin:fine" ;;
    cmw/gold) echo "$b -run begin:map_cells" ;;
    cmw/gate) echo "$b -carry_minwidth $CMW -run begin:map_cells" ;;
    wm5/gold) echo "$b -noiopad -noclkbuf -run begin:map_ffs" ;;
    wm5/gate) echo "$b -noiopad -noclkbuf -widemux 5 -run begin:map_ffs" ;;
  esac
}

run_one() {
  local d=$1 check=$2 top=${TOP[$1]}
  local src=build/qor/src/${d}_${PERIOD} o=$OUT/${d}_${check}
  local files; files=$(cd "$src" && ls *.v *.sv 2>/dev/null | tr '\n' ' ')
  if [ -f "$o.result" ]; then cat "$o.result"; return; fi
  if [ "$DRY_RUN" = 1 ]; then echo "[dry] $d $check: $(stage_script "$top" "$check" gold) | $(stage_script "$top" "$check" gate)"; return; fi
  mkdir -p "$OUT"
  for side in gold gate; do
    (cd "$src" && "$ROOT/$YOSYS" -q -p "read_verilog -sv $files; $(stage_script "$top" "$check" "$side"); rename $top $side; expose -evert $side/t:RAMB36E1 $side/t:RAMB18E1 $side/t:RAM32M $side/t:RAM64M $side/t:RAM32X1D $side/t:RAM64X1D $side/t:RAM128X1D $side/t:SRL16E $side/t:SRLC32E $side/t:ICAPE2 $side/t:DSP48E1; select $side; write_rtlil -selected $ROOT/$o.$side.il") \
      > "$o.$side.log" 2>&1 || { echo "FAIL $d $check: yosys $side ($o.$side.log)" | tee "$o.result"; return; }
  done
  local prep="read_rtlil $o.gold.il; read_rtlil $o.gate.il; read_verilog -lib +/xilinx/cells_sim.v; read_verilog -lib +/xilinx/cells_xtra.v"
  local flat="techmap -autoproc -map +/xilinx/cells_sim.v t:CARRY4 t:MUXCY t:XORCY t:DSP48E1 t:MUXF7 t:MUXF8 t:MUXF6; techmap -map +/simcells.v t:\$_MUX4_ t:\$_MUX8_ t:\$_MUX16_; proc; opt_clean"
  "$ROOT/$YOSYS" -p "$prep; $flat; async2sync; equiv_make gold gate equiv; hierarchy -top equiv; equiv_struct; equiv_simple -seq $SEQ; equiv_induct -seq $SEQ; equiv_status" \
    > "$o.equiv.log" 2>&1
  local line; line=$(grep -E 'Found [0-9]+ \$equiv cells|Of those cells [0-9]+ are proven|unproven' "$o.equiv.log" | tr '\n' ' ')
  local carry_gold carry_gate
  carry_gold=$(grep -cE '^ *cell .*\\CARRY4( |$)' "$o.gold.il"); carry_gate=$(grep -cE '^ *cell .*\\CARRY4( |$)' "$o.gate.il")
  if grep -q 'Equivalence successfully proven' "$o.equiv.log"; then st=PROVEN; else st=NOT-PROVEN; fi
  echo "$st $d $check: $line (CARRY4 cells gold $carry_gold, gate $carry_gate; log $o.equiv.log)" | tee "$o.result"
}

for d in $DESIGNS; do
  for c in $CHECKS; do run_one "$d" "$c"; done
done
