module drc_idelay_ref200g (input wire clk, input wire [1:0] sw, output wire [3:0] led, input wire din);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    wire fb, c200, r200, rdy, dd;
    MMCME2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT_F(10.0), .CLKOUT0_DIVIDE_F(5.0)) u_mmcm (
        .CLKIN1(clk), .CLKFBIN(fb), .CLKFBOUT(fb), .CLKOUT0(c200), .RST(1'b0), .PWRDWN(1'b0), .LOCKED());
    BUFG u_bg (.I(c200), .O(r200));
    (* IODELAY_GROUP = "g0" *) IDELAYCTRL u_ctrl (.REFCLK(r200), .RST(1'b0), .RDY(rdy));
    (* IODELAY_GROUP = "g0" *) IDELAYE2 #(.IDELAY_TYPE("FIXED"), .IDELAY_VALUE(5), .DELAY_SRC("IDATAIN"), .REFCLK_FREQUENCY(200.0)) u_dly (
        .IDATAIN(din), .DATAOUT(dd), .C(1'b0), .CE(1'b0), .INC(1'b0), .LD(1'b0), .LDPIPEEN(1'b0),
        .REGRST(1'b0), .CINVCTRL(1'b0), .CNTVALUEIN(5'd0), .DATAIN(1'b0), .CNTVALUEOUT());
    reg r = 1'b0;
    always @(posedge clk) r <= dd ^ rdy;
    assign led = {c[23:21], r};
endmodule
