#!/usr/bin/env bash
NAT="${NAT:-build/patched/rv2_native/replay}"
OUT="${OUT:-build/patched/rv2_native/b2n}"
CONN_DB="${CONN_DB:-build/b2n/conn_xc7a35tcsg324-1.db}"
SIM_LIB="${SIM_LIB:-build/b2n/cells_sim_b2n.v}"
BRAM_CORE="${BRAM_CORE:-build/b2n/b2n_ramb36e1_core.v}"
SIM_TB="${SIM_TB:-designs/rv_soc2/tb/b2n_tb_rv_soc2.v}"
SIM_TOP="${SIM_TOP:-b2n_tb_rv_soc2}"
SIM_PRIMS="${SIM_PRIMS:-designs/rv_soc2/tb/b2n_ramb36e1.v designs/rv_soc2/tb/icape2_model.v}"
TOP="${TOP:-rv_soc}"
NVEC="${NVEC:-11}"
CFGS="${CFGS:-andn_grey}"
NEG="${NEG-andn_grey:andn:add}"
TOOLS=toolchain/oss-cad-suite
cd "$(dirname "$0")/.."
export PATH=$PWD/$TOOLS/bin:$PATH
for f in "$CONN_DB" "$SIM_LIB" "$BRAM_CORE"; do
  [ -f "$f" ] || { echo "FAIL missing $f (run flow/bit2netlist.sh --batch once)"; exit 2; }
done
mkdir -p "$OUT"
fail=0
sim() {
  local name=$1 cfg=$2 rm1=$3 rm2=$4 expect=$5
  local d=$OUT/$cfg
  vvp -n "$d/sim.vvp" +RM1="$rm1" +RM2="$rm2" +TAG="$name" +NVEC="$NVEC" > "$OUT/$name.sim.log" 2>&1
  local done_line nf
  done_line=$(grep -E '^DONE ' "$OUT/$name.sim.log")
  nf=$(grep -c '^FAIL ' "$OUT/$name.sim.log")
  if [ -z "$done_line" ]; then echo "FAIL $name: simulation did not finish ($OUT/$name.sim.log)"; return 1; fi
  if [ "$expect" = pass ] && [ "$nf" = 0 ]; then echo "PASS $name: $done_line"; return 0; fi
  if [ "$expect" = fail ] && [ "$nf" -gt 0 ]; then echo "PASS $name (negative control, $nf FAIL lines): $done_line"; return 0; fi
  echo "FAIL $name (expected $expect): $done_line ($OUT/$name.sim.log)"; return 1
}
for c in $CFGS; do
  bit=$NAT/${c}_n/$TOP.bit
  OUT=$OUT CONN_DB=$CONN_DB bash flow/bit2netlist.sh "$c" "$bit" rv_soc - > "$OUT/$c.decode.log" 2>&1 \
    || { echo "FAIL decode $c ($OUT/$c.decode.log)"; fail=1; continue; }
  grep -E '^(ok|info|note)' "$OUT/$c.decode.log" | sed "s/^/  /"
  iverilog -g2012 -o "$OUT/$c/sim.vvp" -s "$SIM_TOP" -DB2N_DUT="$TOP" "$OUT/$c/design.v" "$SIM_LIB" $SIM_PRIMS "$BRAM_CORE" "$SIM_TB" \
    > "$OUT/$c/iverilog.log" 2>&1 || { echo "FAIL iverilog $c ($OUT/$c/iverilog.log)"; fail=1; continue; }
  sim "$c" "$c" "$(echo $c | cut -d_ -f1)" "$(echo $c | cut -d_ -f2)" pass || fail=1
done
for x in $NEG; do
  IFS=: read -r c rm1 rm2 <<< "$x"
  [ -f "$OUT/$c/sim.vvp" ] || { echo "FAIL neg $x: no netlist for $c"; fail=1; continue; }
  sim "neg_${c}_as_${rm1}_${rm2}" "$c" "$rm1" "$rm2" fail || fail=1
done
exit $fail
