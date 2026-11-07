module x_loc (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    wire clk_ibuf, gclk;
    IBUF u_ibuf (.I(clk), .O(clk_ibuf));
    BUFG u_bufg (.I(clk_ibuf), .O(gclk));
    reg [3:0] q = 4'd0;
    always @(posedge gclk) q <= sw;
    assign led = q;
endmodule
