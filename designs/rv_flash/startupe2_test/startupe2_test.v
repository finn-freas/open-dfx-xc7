module startupe2_test (input wire clk, output wire [3:0] led);
    reg [23:0] cnt = 24'd0;
    always @(posedge clk) cnt <= cnt + 24'd1;
    assign led = cnt[23:20];
    wire cfgclk, cfgmclk, eos, preq;
    STARTUPE2 #(.PROG_USR("FALSE"), .SIM_CCLK_FREQ(10.0)) u_startup (
        .CFGCLK(cfgclk), .CFGMCLK(cfgmclk), .EOS(eos), .PREQ(preq),
        .CLK(1'b0), .GSR(1'b0), .GTS(1'b0), .KEYCLEARB(1'b1), .PACK(1'b0),
        .USRCCLKO(cnt[3]), .USRCCLKTS(1'b0), .USRDONEO(1'b1), .USRDONETS(1'b1)
    );
endmodule
