module x_gen_none (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg div = 1'b0;
    always @(posedge clk) div <= ~div;
    wire clk_div;
    BUFG u_bgdiv (.I(div), .O(clk_div));
    reg [15:0] x = 16'd0;
    always @(posedge clk_div) x <= x + {12'd0, sw} + 16'd1;
    wire [15:0] t0 = (x ^ {x[0:0], x[15:1]}) + x + 16'd0;
    wire [15:0] t1 = (t0 ^ {t0[3:0], t0[15:4]}) + t0 + 16'd31153;
    wire [15:0] t2 = (t1 ^ {t1[6:0], t1[15:7]}) + t1 + 16'd62306;
    wire [15:0] t3 = (t2 ^ {t2[9:0], t2[15:10]}) + t2 + 16'd27923;
    wire [15:0] t4 = (t3 ^ {t3[12:0], t3[15:13]}) + t3 + 16'd59076;
    wire [15:0] t5 = (t4 ^ {t4[0:0], t4[15:1]}) + t4 + 16'd24693;
    wire [15:0] t6 = (t5 ^ {t5[3:0], t5[15:4]}) + t5 + 16'd55846;
    reg [15:0] y = 16'd0;
    always @(posedge clk_div) y <= t6;
    assign led = y[15:12];
endmodule
