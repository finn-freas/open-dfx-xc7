module drc_bufg_over (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    reg [32:0] dv = 33'd0;
    always @(posedge clk) dv <= dv + {{(32){1'b0}}, 1'b1};
    wire [32:0] gc;
    reg [32:0] t = 33'd0;
    genvar i;
    generate for (i = 0; i < 33; i = i + 1) begin : g
        BUFG u_bg (.I(dv[i]), .O(gc[i]));
        always @(posedge gc[i]) t[i] <= ~t[i] ^ sw[0];
    end endgenerate
    assign led = {c[23:21], ^t};
endmodule
