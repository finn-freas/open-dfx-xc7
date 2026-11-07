#!/usr/bin/env bash
W_TO_RP="${W_TO_RP:-75}"
W_FROM_RP="${W_FROM_RP:-33}"
cd "$(dirname "$0")/.."
YOSYS=toolchain/oss-cad-suite/bin/yosys
OUT=build/decoupler_prove
mkdir -p $OUT
cat > $OUT/wrap.v <<V
module wrap (input wire decouple, input wire [$W_TO_RP-1:0] s_to_rp, input wire [$W_FROM_RP-1:0] rp_out, output wire ok, output wire bad_ok);
    wire [$W_TO_RP-1:0] rp_in;
    wire [$W_FROM_RP-1:0] s_from_rp;
    wire st;
    dfx_decoupler #(.W_TO_RP($W_TO_RP), .W_FROM_RP($W_FROM_RP)) dut (.decouple(decouple), .s_to_rp(s_to_rp), .rp_in(rp_in),
        .rp_out(rp_out), .s_from_rp(s_from_rp), .decouple_status(st));
    assign ok = st == decouple && (decouple ? (rp_in == 0 && s_from_rp == 0) : (rp_in == s_to_rp && s_from_rp == rp_out));
    assign bad_ok = decouple ? (s_from_rp == rp_out) : 1'b1;
endmodule
V
$YOSYS -q -l $OUT/prove.log -p "read_verilog designs/common/dfx_decoupler.v $OUT/wrap.v; prep -top wrap; flatten; sat -prove ok 1 -verify -timeout 60" && echo "PROVED: dfx_decoupler contract (W_TO_RP=$W_TO_RP, W_FROM_RP=$W_FROM_RP)" || { echo "FAIL: dfx_decoupler contract"; exit 1; }
if $YOSYS -q -l $OUT/neg.log -p "read_verilog designs/common/dfx_decoupler.v $OUT/wrap.v; prep -top wrap; flatten; sat -prove bad_ok 1 -verify -timeout 60" > /dev/null 2>&1; then
  echo "FAIL: negative control proved (a decoupled output equal to the RP output must be refutable)"; exit 1
else
  echo "ok: negative control refuted (decoupled outputs do not follow the RP)"
fi
