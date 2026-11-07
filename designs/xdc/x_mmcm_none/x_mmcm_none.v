module x_mmcm_none (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    wire clk_ibuf, fb, c1_mmcm, c2_mmcm, c1, c2;
    IBUF u_ibuf (.I(clk), .O(clk_ibuf));
    MMCME2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT_F(10.0), .DIVCLK_DIVIDE(1),
                  .CLKOUT0_DIVIDE_F(10.0), .CLKOUT1_DIVIDE(5))
        u_mmcm (.CLKIN1(clk_ibuf), .CLKFBIN(fb), .CLKFBOUT(fb), .CLKOUT0(c1_mmcm), .CLKOUT1(c2_mmcm),
                .RST(1'b0), .PWRDWN(1'b0), .LOCKED());
    BUFG u_bg1 (.I(c1_mmcm), .O(c1));
    BUFG u_bg2 (.I(c2_mmcm), .O(c2));
    reg [15:0] a = 16'd0;
    always @(posedge c1) a <= a + {12'd0, sw} + 16'd1;
    wire [15:0] t0 = (a ^ {a[0:0], a[15:1]}) + a + 16'd0;
    wire [15:0] t1 = (t0 ^ {t0[3:0], t0[15:4]}) + t0 + 16'd31153;
    wire [15:0] t2 = (t1 ^ {t1[6:0], t1[15:7]}) + t1 + 16'd62306;
    reg [15:0] dq = 16'd0;
    always @(posedge c2) dq <= t2;
    reg [15:0] ds = 16'd0;
    always @(posedge c2) ds <= ds ^ dq;
    assign led = ds[15:12];
endmodule
