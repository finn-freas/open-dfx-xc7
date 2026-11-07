module drc_dfx_nopb_rm (input wire clk, input wire [1:0] sw, output wire [1:0] q);
    reg [15:0] r = 16'd0;
    always @(posedge clk) r <= r + {14'd0, sw};
    assign q = r[15:14];
endmodule
module drc_dfx_nopb (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    wire [1:0] q;
    (* keep_hierarchy = "yes" *) drc_dfx_nopb_rm u_rp (.clk(clk), .sw(sw), .q(q));
    assign led = {c[23:22], q};
endmodule
