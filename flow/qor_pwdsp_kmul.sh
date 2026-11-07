#!/usr/bin/env bash
DRY_RUN="${DRY_RUN:-1}"
OUT="${OUT:-build/qor/synx/dspacc}"
CYCLES="${CYCLES:-20000}"
cd "$(dirname "$0")/.."
Y=toolchain/oss-cad-suite/bin/yosys
CELLS=toolchain/oss-cad-suite/share/yosys/xilinx/cells_sim.v
P1='proc; check; flatten; tribuf -logic; deminout; opt_expr; check; opt_clean'
P2='fsm; opt; wreduce; peepopt; opt_clean; pmux2shiftx; clean; sort'
[ "$DRY_RUN" = 1 ] && { echo "[dry] pw_dsp stock vs k_mul -> $OUT; DRY_RUN=0 to run"; exit 0; }
export PATH=$PWD/toolchain/oss-cad-suite/bin:$PATH
mkdir -p "$OUT"
synth() {
  local SX="synth_xilinx -flatten -abc9 -arch xc7 -top $2" s
  if [ "$3" = stock ]; then s="$SX"; else
    s="$SX -run :prepare; $P1; setattr -set keep 1 t:\$mul; opt -nodffe -nosdff; $P2; setattr -unset keep t:\$mul; $SX -run map_dsp:"; fi
  /usr/bin/time -f "%e" -o "$OUT/$2_$3.time" $Y -q -p "read_verilog $1; $s; rename $2 $2_$3; tee -q -o $OUT/$2_$3.stat stat -tech xilinx; write_verilog -noattr $4" > "$OUT/$2_$3.log" 2>&1
}
for d in pw_dsp8 pw_dsp32 pw_dsp32_p5 pw_dsp64; do
  for v in stock k_mul; do
    synth designs/power/$d/$d.v $d $v "$OUT/${d}_$v.v"
    echo "$d $v $(cat $OUT/${d}_$v.time)s: $(grep -E '^ +[0-9]+ +(DSP48E1|CARRY4|FDRE|LUT[1-6]|INV)$' $OUT/${d}_$v.stat | awk '{a[$2]=$1} END {l=0; for (k in a) if (k ~ /LUT|INV/) l+=a[k]; printf "DSP %d CARRY4 %d FF %d LUT %d", a["DSP48E1"], a["CARRY4"], a["FDRE"], l}')"
  done
done
sed 's/module pw_dsp8 /module pw_dsp8h /; s/wire \[47:0\] r = .*/wire [47:0] r = p[0] ^ p[2] ^ p[4] ^ p[6];/; s/initial for (j = 0; j < 8; j = j + 1) p\[j\] = 48.d0;/initial for (j = 0; j < 8; j = j + 1) begin p[j] = 48'"'"'d0; a[j] = 0; b[j] = 0; m[j] = 0; end/' designs/power/pw_dsp8/pw_dsp8.v > "$OUT/pw_dsp8h.v"
for v in stock k_mul; do synth "$OUT/pw_dsp8h.v" pw_dsp8h $v "$OUT/pw_dsp8h_$v.v"; done
cat > "$OUT/tb_pw_dsp8h.v" <<EOF
\`timescale 1ns/1ps
module tb;
  reg clk = 0;
  wire [3:0] l0, l1, l2;
  pw_dsp8h u0(.clk(clk), .led(l0));
  pw_dsp8h_stock u1(.clk(clk), .led(l1));
  pw_dsp8h_k_mul u2(.clk(clk), .led(l2));
  integer i, mism = 0, changes = 0; reg [3:0] last = 0;
  initial begin
    for (i = 0; i < $CYCLES; i = i + 1) begin
      #5 clk = 1; #1;
      if (i > 4 && (l0 !== l1 || l0 !== l2)) begin mism = mism + 1; if (mism <= 5) \$display("MISMATCH %0d %h %h %h", i, l0, l1, l2); end
      if (l0 !== last) changes = changes + 1; last = l0;
      #4 clk = 0;
    end
    \$display("RESULT pw_dsp8h cycles %0d mismatches %0d led_changes %0d", $CYCLES, mism, changes);
    \$finish;
  end
endmodule
EOF
iverilog -g2012 -o "$OUT/pw_dsp8h.vvp" -s tb "$OUT/tb_pw_dsp8h.v" "$OUT/pw_dsp8h.v" "$OUT/pw_dsp8h_stock.v" "$OUT/pw_dsp8h_k_mul.v" "$CELLS" > "$OUT/pw_dsp8h.iverilog.log" 2>&1 \
  || { echo "FAIL iverilog ($OUT/pw_dsp8h.iverilog.log)"; exit 1; }
vvp -n "$OUT/pw_dsp8h.vvp" > "$OUT/pw_dsp8h.sim.log" 2>&1
grep -E "RESULT|MISMATCH" "$OUT/pw_dsp8h.sim.log" | head -6
