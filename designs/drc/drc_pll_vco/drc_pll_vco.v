module drc_pll_vco (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    wire fb, co, cb;
    PLLE2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT(30), .CLKOUT0_DIVIDE(30)) u_pll (
        .CLKIN1(clk), .CLKFBIN(fb), .CLKFBOUT(fb), .CLKOUT0(co), .RST(1'b0), .PWRDWN(1'b0), .LOCKED());
    BUFG u_bg (.I(co), .O(cb));
    reg [23:0] c = 24'd0;
    always @(posedge cb) c <= c + 24'd1 + sw;
    assign led = c[23:20];
endmodule
