module drc_lvds_vcco (input wire clk, input wire [1:0] sw, output wire [3:0] led, output wire dp, output wire dn);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    OBUFDS u_ob (.I(c[4]), .O(dp), .OB(dn));
    assign led = c[23:20];
endmodule
