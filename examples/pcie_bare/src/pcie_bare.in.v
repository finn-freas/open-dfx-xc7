module pcie_bare (
    input  wire       clk,
    input  wire       rst_n,
    output wire [3:0] led
);
    wire uclk;
    BUFG u_bufg (.I(clk), .O(uclk));
    wire lnkup, rstn_o, rdy;
    wire [5:0] ltssm;
    PCIE_2_1 #(
        .PL_FAST_TRAIN("FALSE")
    ) u_pcie (
        .PIPECLK(uclk), .USERCLK(uclk), .USERCLK2(uclk), .DRPCLK(uclk),
        .CMRSTN(rst_n), .CMSTICKYRSTN(rst_n), .FUNCLVLRSTN(rst_n), .PLRSTN(rst_n), .SYSRSTN(rst_n),
        .TLRSTN(rst_n), .DLRSTN(rst_n),
        .TRNLNKUP(lnkup), .RECEIVEDFUNCLVLRSTN(rstn_o), .TRNTDSTRDY(rdy), .PLLTSSMSTATE(ltssm)
    );
    assign led = {lnkup, rstn_o, rdy, ^ltssm};
endmodule
