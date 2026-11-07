module x_fp_thru (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg [15:0] s = 16'd0;
    always @(posedge clk) s <= s + {12'd0, sw} + 16'd1;
    wire [15:0] t0 = (s ^ {s[0:0], s[15:1]}) + s + 16'd0;
    wire [15:0] t1 = (t0 ^ {t0[3:0], t0[15:4]}) + t0 + 16'd31153;
    wire [15:0] t2 = (t1 ^ {t1[6:0], t1[15:7]}) + t1 + 16'd62306;
    wire [15:0] t3 = (t2 ^ {t2[9:0], t2[15:10]}) + t2 + 16'd27923;
    wire [15:0] t4 = (t3 ^ {t3[12:0], t3[15:13]}) + t3 + 16'd59076;
    wire [15:0] t5 = (t4 ^ {t4[0:0], t4[15:1]}) + t4 + 16'd24693;
    wire [15:0] t6 = (t5 ^ {t5[3:0], t5[15:4]}) + t5 + 16'd55846;
    wire [15:0] t7 = (t6 ^ {t6[6:0], t6[15:7]}) + t6 + 16'd21463;
    reg [15:0] dq = 16'd0;
    always @(posedge clk) dq <= t7;
    assign led = dq[15:12];
endmodule
