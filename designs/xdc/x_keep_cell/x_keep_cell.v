module x_keep_cell (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg [15:0] s = 16'd0;
    always @(posedge clk) s <= s + {12'd0, sw} + 16'd1;
    wire [15:0] t0 = (s ^ {s[0:0], s[15:1]}) + s + 16'd0;
    wire [15:0] t1 = (t0 ^ {t0[3:0], t0[15:4]}) + t0 + 16'd31153;
    reg [15:0] dq = 16'd0;
    always @(posedge clk) dq <= t1;
    assign led = dq[15:12];
endmodule
