#!/usr/bin/env bash
DRY_RUN="${DRY_RUN:-1}"
OUT="${OUT:-build/qor/synx/lutram/sim}"
CYCLES="${CYCLES:-200000}"
YSTOCK=toolchain/oss-cad-suite/bin/yosys
YSYNX=build/yosys-build/yosys-synx/yosys
CELLS=toolchain/oss-cad-suite/share/yosys/xilinx/cells_sim.v
cd "$(dirname "$0")/.."
[ "$DRY_RUN" = 1 ] && { echo "[dry] tm2 lockstep, $CYCLES cycles -> $OUT; DRY_RUN=0 to run"; exit 0; }
export PATH=$PWD/toolchain/oss-cad-suite/bin:$PATH
mkdir -p "$OUT"
cat > "$OUT/ramb18e1_sdp36.v" <<'EOF'
module RAMB18E1 (
    output reg [15:0] DOADO, output reg [15:0] DOBDO, output reg [1:0] DOPADOP, output reg [1:0] DOPBDOP,
    input CLKARDCLK, input CLKBWRCLK, input ENARDEN, input ENBWREN, input REGCEAREGCE, input REGCEB,
    input RSTRAMARSTRAM, input RSTRAMB, input RSTREGARSTREG, input RSTREGB,
    input [13:0] ADDRARDADDR, input [13:0] ADDRBWRADDR, input [15:0] DIADI, input [15:0] DIBDI,
    input [1:0] DIPADIP, input [1:0] DIPBDIP, input [1:0] WEA, input [3:0] WEBWE);
    parameter integer DOA_REG = 0, DOB_REG = 0, READ_WIDTH_A = 0, READ_WIDTH_B = 0, WRITE_WIDTH_A = 0, WRITE_WIDTH_B = 0;
    parameter RAM_MODE = "TDP", WRITE_MODE_A = "WRITE_FIRST", WRITE_MODE_B = "WRITE_FIRST", SIM_DEVICE = "7SERIES";
    parameter [71:0] INIT_A = 0, INIT_B = 0, SRVAL_A = 0, SRVAL_B = 0;
    parameter IS_CLKARDCLK_INVERTED = 0, IS_CLKBWRCLK_INVERTED = 0, IS_ENARDEN_INVERTED = 0, IS_ENBWREN_INVERTED = 0;
    parameter IS_RSTRAMARSTRAM_INVERTED = 0, IS_RSTRAMB_INVERTED = 0, IS_RSTREGARSTREG_INVERTED = 0, IS_RSTREGB_INVERTED = 0;
    parameter RDADDR_COLLISION_HWCONFIG = "DELAYED_WRITE", SIM_COLLISION_CHECK = "ALL", INIT_FILE = "NONE";
    parameter RSTREG_PRIORITY_A = "RSTREG", RSTREG_PRIORITY_B = "RSTREG";
    reg [35:0] mem [0:511];
    initial if (RAM_MODE != "SDP" || READ_WIDTH_A != 36 || WRITE_WIDTH_B != 36 || DOA_REG != 0) begin
        $display("ramb18e1_sdp36: unsupported mode %s %0d %0d", RAM_MODE, READ_WIDTH_A, WRITE_WIDTH_B); $finish;
    end
    wire [31:0] di = {DIBDI, DIADI};
    wire [3:0] dip = {DIPBDIP, DIPADIP};
    integer b;
    always @(posedge CLKARDCLK) if (ENARDEN) {DOPBDOP, DOPADOP, DOBDO, DOADO} <= {mem[ADDRARDADDR[13:5]][35:32], mem[ADDRARDADDR[13:5]][31:0]};
    always @(posedge CLKBWRCLK) if (ENBWREN)
        for (b = 0; b < 4; b = b + 1)
            if (WEBWE[b]) begin mem[ADDRBWRADDR[13:5]][8*b +: 8] <= di[8*b +: 8]; mem[ADDRBWRADDR[13:5]][32+b] <= dip[b]; end
endmodule
EOF
P=$(for i in $(seq 0 63); do printf 'parameter [255:0] INIT_%02X = 0; ' "$i"; done; for i in $(seq 0 7); do printf 'parameter [255:0] INITP_%02X = 0; ' "$i"; done)
sed -i "s|^    reg \[35:0\] mem \[0:511\];|    $P\n    reg [35:0] mem [0:511];|" "$OUT/ramb18e1_sdp36.v"
CELLS_NOB18="$OUT/cells_sim_nob18.v"
awk '/^module RAMB18E1[ (]/ {skip=1} !skip {print} skip && /^endmodule/ {skip=0}' "$CELLS" > "$CELLS_NOB18"
CELLS="$CELLS_NOB18 $OUT/ramb18e1_sdp36.v"
for m in tm tm2; do
  src=build/qor/synx/lutram/$m.v
  $YSTOCK -q -p "read_verilog $src; synth_xilinx -flatten -abc9 -arch xc7 -top $m; rename $m ${m}_stock; write_verilog -noattr $OUT/${m}_stock.v"
  $YSYNX -q -p "scratchpad -set opt_dff.keep_memrd_regs 1; read_verilog $src; synth_xilinx -flatten -abc9 -arch xc7 -top $m; rename $m ${m}_synx; tee -q -o $OUT/${m}_synx.stat stat -tech xilinx; write_verilog -noattr $OUT/${m}_synx.v"
  cat > "$OUT/tb_$m.v" <<EOF
\`timescale 1ns/1ps
module tb;
  reg clk = 0, we = 0; reg [8:0] adr = 0; reg [21:0] dw = 0;
  wire [21:0] r_rtl, r_stock, r_synx;
  $m u0(.clk(clk), .we(we), .adr(adr), .dw(dw), .dr(r_rtl));
  ${m}_stock u1(.clk(clk), .we(we), .adr(adr), .dw(dw), .dr(r_stock));
  ${m}_synx u2(.clk(clk), .we(we), .adr(adr), .dw(dw), .dr(r_synx));
  integer i, mism = 0, checked = 0, seed = 1;
  initial begin
    // fill every address first, so no read returns the undefined power-up contents
    for (i = 0; i < 512; i = i + 1) begin we = 1; adr = i; dw = \$random(seed); #5 clk = 1; #5 clk = 0; end
    for (i = 0; i < $CYCLES; i = i + 1) begin
      we = (\$random(seed) & 3) == 0; adr = (\$random(seed) & 1) ? \$random(seed) : adr; dw = \$random(seed);
      #5 clk = 1; #1;
      checked = checked + 1;
      if (r_rtl !== r_stock || r_rtl !== r_synx) begin
        mism = mism + 1;
        if (mism <= 5) \$display("MISMATCH cycle %0d rtl %h stock %h synx %h", i, r_rtl, r_stock, r_synx);
      end
      #4 clk = 0;
    end
    \$display("RESULT $m cycles %0d mismatches %0d", checked, mism);
    \$finish;
  end
endmodule
EOF
  iverilog -g2012 -o "$OUT/$m.vvp" -s tb "$OUT/tb_$m.v" "$src" "$OUT/${m}_stock.v" "$OUT/${m}_synx.v" $CELLS > "$OUT/$m.iverilog.log" 2>&1 \
    || { echo "FAIL iverilog $m ($OUT/$m.iverilog.log)"; continue; }
  vvp -n "$OUT/$m.vvp" > "$OUT/$m.sim.log" 2>&1
  grep -E "RESULT|MISMATCH" "$OUT/$m.sim.log" | head -6
  grep -E "RAMB18E1|RAM256X1S" "$OUT/${m}_stock.v" | sort | uniq -c | head -2; grep -E "^ +[0-9]+ +(RAMB18E1|RAM256X1S|LUT|FDRE)" "$OUT/${m}_synx.stat"
done
