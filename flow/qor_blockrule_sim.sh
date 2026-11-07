#!/usr/bin/env bash
DRY_RUN="${DRY_RUN:-1}"
OUT="${OUT:-build/qor/synx/blockrule/fifo_sim}"
CYCLES="${CYCLES:-100000}"
cd "$(dirname "$0")/.."
Y=toolchain/oss-cad-suite/bin/yosys
CELLS=toolchain/oss-cad-suite/share/yosys/xilinx/cells_sim.v
UNISIM=${UNISIM:-/mnt/c/AMDDesignTools/2025.2/Vivado/data/verilog/src}
[ "$DRY_RUN" = 1 ] && { echo "[dry] fifo lockstep -> $OUT; DRY_RUN=0 to run"; exit 0; }
export PATH=$PWD/toolchain/oss-cad-suite/bin:$PATH
mkdir -p "$OUT"
for g in "70 4" "12 7" "42 5"; do
  set -- $g; W=$1; A=$2; M=f${W}x$((1 << A))
  cat > "$OUT/$M.v" <<EOF
module $M(input clk, input we, input re, input [$((A-1)):0] wa, input [$((A-1)):0] ra, input [$((W-1)):0] d,
          output [$((W-1)):0] q0, output [$((W-1)):0] q1);
reg [$((W-1)):0] storage[0:$(((1 << A) - 1))];
reg [$((W-1)):0] dat0, dat1;
integer i;
initial for (i = 0; i < $((1 << A)); i = i + 1) storage[i] = 0;
always @(posedge clk) begin
    if (we) storage[wa] <= d;
    dat0 <= storage[wa];
end
always @(posedge clk) if (re) dat1 <= storage[ra];
assign q0 = dat0;
assign q1 = dat1;
endmodule
EOF
  for v in lut block; do
    attr=""; [ $v = block ] && attr="setattr -set ram_style \"block\" $M/storage; "
    $Y -q -p "read_verilog $OUT/$M.v; synth_xilinx -flatten -abc9 -arch xc7 -top $M -run :map_memory; $attr synth_xilinx -flatten -abc9 -arch xc7 -top $M -run map_memory:; rename $M ${M}_$v; tee -q -o $OUT/${M}_$v.stat stat -tech xilinx; write_verilog -noattr $OUT/${M}_$v.v"
  done
  cat > "$OUT/tb_$M.v" <<EOF
\`timescale 1ns/1ps
module tb;
  reg clk = 0, we = 0, re = 0; reg [$((A-1)):0] wa = 0, ra = 0; reg [$((W-1)):0] d = 0;
  wire [$((W-1)):0] a0, a1, b0, b1, c0, c1;
  $M u0(.clk(clk), .we(we), .re(re), .wa(wa), .ra(ra), .d(d), .q0(a0), .q1(a1));
  ${M}_lut u1(.clk(clk), .we(we), .re(re), .wa(wa), .ra(ra), .d(d), .q0(b0), .q1(b1));
  ${M}_block u2(.clk(clk), .we(we), .re(re), .wa(wa), .ra(ra), .d(d), .q0(c0), .q1(c1));
  integer i, mism = 0, seed = 7;
  initial begin
    for (i = 0; i < $CYCLES; i = i + 1) begin
      we = \$random(seed); re = \$random(seed);
      if (i < 16) we = 0; // unisim glbl holds GSR for the first 100 ns; a write then is ignored by the RAM model wa = \$random(seed); ra = \$random(seed);
      d = {\$random(seed), \$random(seed), \$random(seed)};
      #5 clk = 1; #1;
      if (i > 64 && ({a0, a1} !== {b0, b1} || {a0, a1} !== {c0, c1})) begin
        mism = mism + 1; if (mism <= 3) \$display("MISMATCH %0d %h/%h %h/%h %h/%h", i, a0, a1, b0, b1, c0, c1);
      end
      #4 clk = 0;
    end
    \$display("RESULT $M cycles %0d mismatches %0d", $CYCLES, mism);
    \$finish;
  end
endmodule
EOF
  cp -f "$UNISIM/unisims/RAMB18E1.v" "$UNISIM/unisims/RAMB36E1.v" "$UNISIM/glbl.v" "$OUT/"
  awk '/^module (RAMB18E1|RAMB36E1)[ (#]/ {skip=1} !skip {print} skip && /^endmodule/ {skip=0}' "$CELLS" > "$OUT/cells.v"
  iverilog -g2012 -o "$OUT/$M.vvp" -s tb -s glbl "$OUT/tb_$M.v" "$OUT/$M.v" "$OUT/${M}_lut.v" "$OUT/${M}_block.v" "$OUT/cells.v" \
    "$OUT/RAMB18E1.v" "$OUT/RAMB36E1.v" "$OUT/glbl.v" > "$OUT/$M.iverilog.log" 2>&1 \
    || { echo "FAIL iverilog $M ($OUT/$M.iverilog.log)"; continue; }
  vvp -n "$OUT/$M.vvp" > "$OUT/$M.sim.log" 2>&1
  echo "$M: $(grep -E 'RESULT' $OUT/$M.sim.log) | lut: $(grep -E ' RAM' $OUT/${M}_lut.stat | tr -s ' ' | tr '\n' ' ') | block: $(grep -E ' RAM' $OUT/${M}_block.stat | tr -s ' ' | tr '\n' ' ')"
  grep MISMATCH "$OUT/$M.sim.log" | head -2
done
