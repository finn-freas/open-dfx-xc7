module dfx_decoupler #(
    parameter W_TO_RP = 1,
    parameter W_FROM_RP = 1,
    parameter [W_TO_RP-1:0] SAFE_TO_RP = {W_TO_RP{1'b0}},
    parameter [W_FROM_RP-1:0] SAFE_FROM_RP = {W_FROM_RP{1'b0}}
) (
    input wire decouple,
    input wire [W_TO_RP-1:0] s_to_rp,
    output wire [W_TO_RP-1:0] rp_in,
    input wire [W_FROM_RP-1:0] rp_out,
    output wire [W_FROM_RP-1:0] s_from_rp,
    output wire decouple_status
);
    assign rp_in = decouple ? SAFE_TO_RP : s_to_rp;
    assign s_from_rp = decouple ? SAFE_FROM_RP : rp_out;
    assign decouple_status = decouple;
endmodule
