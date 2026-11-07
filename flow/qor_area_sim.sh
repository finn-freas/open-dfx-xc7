#!/usr/bin/env bash
DRY_RUN="${DRY_RUN:-1}"
DESIGNS="${DESIGNS:-rv_soc rv_mul rv_big}"
PERIOD="${PERIOD:-p5}"
OUT="${OUT:-build/qor/area/sim}"
YOSYS="${YOSYS:-build/yosys-build/yosys-area/yosys}"
GATE_OPTS="${GATE_OPTS:--share_aggressive -carry_minwidth 5}"
NVEC="${NVEC:-11}"
GOLD_JSON="${GOLD_JSON:-}"
GATE_JSON="${GATE_JSON:-}"
TB=designs/rv_soc/tb/b2n_tb_rv_soc.v
PRIMS="designs/rv_soc/tb/gl_ramb36e1.v designs/rv_soc/tb/icape2_model.v"
TOOLS=toolchain/oss-cad-suite
declare -A TOP=([rv_soc]=qor_rv_soc [rv_mul]=qor_rv_mul [rv_big]=qor_rv_big)

cd "$(dirname "$0")/.."
ROOT=$PWD
export PATH=$ROOT/$TOOLS/bin:$PATH
CELLS_SIM=$TOOLS/share/yosys/xilinx/cells_sim.v
SIM_LIB=$OUT/cells_sim_area.v

pair_top() {
  cat <<'EOF'
module pair_top(input clk, input uart_txd_in, output uart_rxd_out, output [3:0] led);
    wire tx_b;
    wire [3:0] led_b;
    gold_top g(.clk(clk), .uart_txd_in(uart_txd_in), .uart_rxd_out(uart_rxd_out), .led(led));
    gate_top h(.clk(clk), .uart_txd_in(uart_txd_in), .uart_rxd_out(tx_b), .led(led_b));
    integer cyc = 0, mism = 0, tx_edges = 0;
    reg tx_q = 1'b1;
    always @(negedge clk) begin
        cyc = cyc + 1;
        if (uart_rxd_out !== tx_q) tx_edges = tx_edges + 1;
        tx_q = uart_rxd_out;
        if (cyc > 2 && (tx_b !== uart_rxd_out || led_b !== led)) begin
            mism = mism + 1;
            if (mism <= 5) $display("LOCKSTEP-MISMATCH cycle %0d tx %b %b led %b %b", cyc, uart_rxd_out, tx_b, led, led_b);
        end
    end
    final $display("LOCKSTEP cycles %0d mismatches %0d tx_edges %0d", cyc, mism, tx_edges);
endmodule
EOF
}

run_one() {
  local d=$1 top=${TOP[$1]} src=build/qor/src/${1}_${PERIOD} o=$OUT/$1
  if [ "$DRY_RUN" = 1 ]; then echo "[dry] $d: gold = ${GOLD_JSON:-default synth_xilinx}, gate = ${GATE_JSON:-synth_xilinx $GATE_OPTS}; lockstep under $TB"; return; fi
  mkdir -p "$o"
  local files; files=$(cd "$src" && ls *.v *.sv 2>/dev/null | tr '\n' ' ')
  for side in gold gate; do
    local opts=""; [ "$side" = gate ] && opts="$GATE_OPTS"
    local js=""; [ "$side" = gold ] && js="$GOLD_JSON"; [ "$side" = gate ] && js="$GATE_JSON"
    [ -f "$o/$side.v" ] && continue
    local rd="read_verilog -sv $files; synth_xilinx -flatten -abc9 -arch xc7 -top $top $opts"
    [ -n "$js" ] && rd="read_json $js; delete t:\$scopeinfo"
    (cd "$src" && "$ROOT/$YOSYS" -q -p "$rd; rename $top ${side}_top; tee -q -o $ROOT/$o/$side.stat stat -tech xilinx; write_verilog -noattr $ROOT/$o/$side.v") \
      > "$o/$side.log" 2>&1 || { echo "FAIL $d: yosys $side ($o/$side.log)"; return 1; }
  done
  for side in gold gate; do
    awk '/^ *FD(RE|CE)(_1)? #\(/ {v="0"} /^ *FD(SE|PE)(_1)? #\(/ {v="1"} /\.INIT\(1.hx\)/ {sub(/1.hx/, "1'"'"'h" v)} {print}' \
      "$o/$side.v" > "$o/$side.init.v"
  done
  pair_top > "$o/pair_top.v"
  local over; over=$(sed -nE 's/^module ([A-Za-z0-9_]+).*/\1/p' $PRIMS | paste -sd'|')
  awk -v re="^module ($over)[ (#]" '$0 ~ re {skip=1} !skip {print} skip && /^endmodule/ {skip=0}' "$CELLS_SIM" > "$SIM_LIB"
  iverilog -g2012 -o "$o/sim.vvp" -s b2n_tb_rv_soc -DB2N_DUT=pair_top "$o/gold.init.v" "$o/gate.init.v" "$o/pair_top.v" "$SIM_LIB" $PRIMS "$TB" \
    > "$o/iverilog.log" 2>&1 || { echo "FAIL $d: iverilog ($o/iverilog.log)"; return 1; }
  vvp -n "$o/sim.vvp" +RM=xor +TAG="$d" +NVEC="$NVEC" > "$o/sim.log" 2>&1
  local done_line lock carry_g carry_h
  done_line=$(grep -E '^DONE ' "$o/sim.log")
  lock=$(grep -E '^LOCKSTEP cycles' "$o/sim.log")
  carry_g=$(grep -E ' CARRY4$' "$o/gold.stat" | awk '{print $1}'); carry_h=$(grep -E ' CARRY4$' "$o/gate.stat" | awk '{print $1}')
  echo "$d: $done_line | $lock | CARRY4 gold $carry_g gate $carry_h | log $o/sim.log"
}

for d in $DESIGNS; do run_one "$d"; done
