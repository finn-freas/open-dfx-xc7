module x_keep_k (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg [15:0] s = 16'd0;
    always @(posedge clk) s <= s + {12'd0, sw} + 16'd1;
    wire [15:0] t0 = (s ^ {s[0:0], s[15:1]}) + s;
    reg [15:0] dq = 16'd0;
    always @(posedge clk) dq <= t0;
    reg [15:0] dd = 16'd0;
    always @(posedge clk) dd <= t0;
    assign led = dq[15:12] ^ dd[15:12];
endmodule
