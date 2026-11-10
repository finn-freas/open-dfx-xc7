module x_jit_two (input wire clk_a, input wire clk_b, input wire [3:0] sw, output wire [3:0] led);
    reg [15:0] a = 16'd0;
    always @(posedge clk_a) a <= a + {12'd0, sw} + 16'd1;
    wire [15:0] t0 = (a ^ {a[0:0], a[15:1]}) + a + 16'd0;
    wire [15:0] t1 = (t0 ^ {t0[3:0], t0[15:4]}) + t0 + 16'd31153;
    wire [15:0] t2 = (t1 ^ {t1[6:0], t1[15:7]}) + t1 + 16'd62306;
    wire [15:0] t3 = (t2 ^ {t2[9:0], t2[15:10]}) + t2 + 16'd27923;
    reg [15:0] bq = 16'd0;
    always @(posedge clk_b) bq <= t3;
    reg [15:0] bs = 16'd0;
    always @(posedge clk_b) bs <= bs + bq;
    assign led = bs[15:12];
endmodule
