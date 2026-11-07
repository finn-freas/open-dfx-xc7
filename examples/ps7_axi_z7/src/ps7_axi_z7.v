module ps7_axi_z7 (
    output wire [3:0] led
);
    wire [3:0]  fclk;
    wire [3:0]  fclk_rstn;
    wire        clk;
    reg  [1:0]  rst_sync = 2'b00;

    wire [31:0] awaddr, araddr, wdata, rdata;
    wire [11:0] awid, arid, wid, bid, rid;
    wire [3:0]  wstrb, arlen;
    wire [1:0]  bresp, rresp;
    wire        awvalid, awready, wvalid, wready, wlast, bvalid, bready;
    wire        arvalid, arready, rvalid, rready, rlast;

    BUFG fclk0_bufg (.I(fclk[0]), .O(clk));

    always @(posedge clk) rst_sync <= {rst_sync[0], fclk_rstn[0]};

    PS7 ps7_i (
        .FCLKCLK        (fclk),
        .FCLKRESETN     (fclk_rstn),
        .MAXIGP0ACLK    (clk),
        .MAXIGP0AWADDR  (awaddr),
        .MAXIGP0AWID    (awid),
        .MAXIGP0AWVALID (awvalid),
        .MAXIGP0AWREADY (awready),
        .MAXIGP0WDATA   (wdata),
        .MAXIGP0WSTRB   (wstrb),
        .MAXIGP0WID     (wid),
        .MAXIGP0WLAST   (wlast),
        .MAXIGP0WVALID  (wvalid),
        .MAXIGP0WREADY  (wready),
        .MAXIGP0BID     (bid),
        .MAXIGP0BRESP   (bresp),
        .MAXIGP0BVALID  (bvalid),
        .MAXIGP0BREADY  (bready),
        .MAXIGP0ARADDR  (araddr),
        .MAXIGP0ARID    (arid),
        .MAXIGP0ARLEN   (arlen),
        .MAXIGP0ARVALID (arvalid),
        .MAXIGP0ARREADY (arready),
        .MAXIGP0RID     (rid),
        .MAXIGP0RDATA   (rdata),
        .MAXIGP0RRESP   (rresp),
        .MAXIGP0RLAST   (rlast),
        .MAXIGP0RVALID  (rvalid),
        .MAXIGP0RREADY  (rready)
    );

    axi_regs regs_i (
        .clk     (clk),
        .rstn    (rst_sync[1]),
        .awaddr  (awaddr),
        .awid    (awid),
        .awvalid (awvalid),
        .awready (awready),
        .wdata   (wdata),
        .wstrb   (wstrb),
        .wlast   (wlast),
        .wvalid  (wvalid),
        .wready  (wready),
        .bid     (bid),
        .bresp   (bresp),
        .bvalid  (bvalid),
        .bready  (bready),
        .araddr  (araddr),
        .arid    (arid),
        .arlen   (arlen),
        .arvalid (arvalid),
        .arready (arready),
        .rid     (rid),
        .rdata   (rdata),
        .rresp   (rresp),
        .rlast   (rlast),
        .rvalid  (rvalid),
        .rready  (rready),
        .led     (led)
    );
endmodule
