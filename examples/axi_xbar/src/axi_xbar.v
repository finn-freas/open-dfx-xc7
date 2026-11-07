module axi_xbar (
    input  wire       clk,
    output wire [3:0] led
);
    localparam S = 2, M = 4, AW = 14, DW = 32, SW = DW / 8, SID = 4, MID = SID + 1;

    reg [3:0] por = 4'hf;
    always @(posedge clk) por <= {por[2:0], 1'b0};
    wire rst = por[3];

    wire [S*SID-1:0] s_awid, s_bid, s_arid, s_rid;
    wire [S*AW-1:0]  s_awaddr, s_araddr;
    wire [S*8-1:0]   s_awlen, s_arlen;
    wire [S*3-1:0]   s_awsize, s_arsize;
    wire [S*2-1:0]   s_awburst, s_arburst, s_bresp, s_rresp;
    wire [S-1:0]     s_awvalid, s_awready, s_wlast, s_wvalid, s_wready, s_bvalid, s_bready;
    wire [S-1:0]     s_arvalid, s_arready, s_rlast, s_rvalid, s_rready;
    wire [S*DW-1:0]  s_wdata, s_rdata;
    wire [S*SW-1:0]  s_wstrb;
    wire [S-1:0]     err, done;

    genvar i;
    generate
        for (i = 0; i < S; i = i + 1) begin : g_tg
            axi_tg #(.ADDR_WIDTH(AW), .ID_WIDTH(SID), .ID(i + 1), .SEED(16'hace1 + 16'h1357 * i), .LANE(i)) u_tg (
                .clk(clk), .rst(rst),
                .awid(s_awid[i*SID +: SID]), .awaddr(s_awaddr[i*AW +: AW]), .awlen(s_awlen[i*8 +: 8]),
                .awsize(s_awsize[i*3 +: 3]), .awburst(s_awburst[i*2 +: 2]), .awvalid(s_awvalid[i]),
                .awready(s_awready[i]),
                .wdata(s_wdata[i*DW +: DW]), .wstrb(s_wstrb[i*SW +: SW]), .wlast(s_wlast[i]),
                .wvalid(s_wvalid[i]), .wready(s_wready[i]),
                .bid(s_bid[i*SID +: SID]), .bresp(s_bresp[i*2 +: 2]), .bvalid(s_bvalid[i]), .bready(s_bready[i]),
                .arid(s_arid[i*SID +: SID]), .araddr(s_araddr[i*AW +: AW]), .arlen(s_arlen[i*8 +: 8]),
                .arsize(s_arsize[i*3 +: 3]), .arburst(s_arburst[i*2 +: 2]), .arvalid(s_arvalid[i]),
                .arready(s_arready[i]),
                .rid(s_rid[i*SID +: SID]), .rdata(s_rdata[i*DW +: DW]), .rresp(s_rresp[i*2 +: 2]),
                .rlast(s_rlast[i]), .rvalid(s_rvalid[i]), .rready(s_rready[i]),
                .err(err[i]), .done(done[i]));
        end
    endgenerate

    wire [M*MID-1:0] m_awid, m_bid, m_arid, m_rid;
    wire [M*AW-1:0]  m_awaddr, m_araddr;
    wire [M*8-1:0]   m_awlen, m_arlen;
    wire [M*3-1:0]   m_awsize, m_arsize, m_awprot, m_arprot;
    wire [M*2-1:0]   m_awburst, m_arburst, m_bresp, m_rresp;
    wire [M*4-1:0]   m_awcache, m_arcache;
    wire [M-1:0]     m_awlock, m_arlock;
    wire [M-1:0]     m_awvalid, m_awready, m_wlast, m_wvalid, m_wready, m_bvalid, m_bready;
    wire [M-1:0]     m_arvalid, m_arready, m_rlast, m_rvalid, m_rready;
    wire [M*DW-1:0]  m_wdata, m_rdata;
    wire [M*SW-1:0]  m_wstrb;

    axi_crossbar #(
        .S_COUNT(S), .M_COUNT(M), .DATA_WIDTH(DW), .ADDR_WIDTH(AW), .S_ID_WIDTH(SID), .M_ID_WIDTH(MID),
        .M_REGIONS(1), .M_BASE_ADDR({14'h3000, 14'h2000, 14'h1000, 14'h0000}),
        .M_ADDR_WIDTH({M{32'd12}})
    ) u_xbar (
        .clk(clk), .rst(rst),
        .s_axi_awid(s_awid), .s_axi_awaddr(s_awaddr), .s_axi_awlen(s_awlen), .s_axi_awsize(s_awsize),
        .s_axi_awburst(s_awburst), .s_axi_awlock({S{1'b0}}), .s_axi_awcache({S{4'h3}}), .s_axi_awprot({S{3'h0}}),
        .s_axi_awqos({S{4'h0}}), .s_axi_awuser({S{1'b0}}), .s_axi_awvalid(s_awvalid), .s_axi_awready(s_awready),
        .s_axi_wdata(s_wdata), .s_axi_wstrb(s_wstrb), .s_axi_wlast(s_wlast), .s_axi_wuser({S{1'b0}}),
        .s_axi_wvalid(s_wvalid), .s_axi_wready(s_wready),
        .s_axi_bid(s_bid), .s_axi_bresp(s_bresp), .s_axi_buser(), .s_axi_bvalid(s_bvalid), .s_axi_bready(s_bready),
        .s_axi_arid(s_arid), .s_axi_araddr(s_araddr), .s_axi_arlen(s_arlen), .s_axi_arsize(s_arsize),
        .s_axi_arburst(s_arburst), .s_axi_arlock({S{1'b0}}), .s_axi_arcache({S{4'h3}}), .s_axi_arprot({S{3'h0}}),
        .s_axi_arqos({S{4'h0}}), .s_axi_aruser({S{1'b0}}), .s_axi_arvalid(s_arvalid), .s_axi_arready(s_arready),
        .s_axi_rid(s_rid), .s_axi_rdata(s_rdata), .s_axi_rresp(s_rresp), .s_axi_rlast(s_rlast), .s_axi_ruser(),
        .s_axi_rvalid(s_rvalid), .s_axi_rready(s_rready),
        .m_axi_awid(m_awid), .m_axi_awaddr(m_awaddr), .m_axi_awlen(m_awlen), .m_axi_awsize(m_awsize),
        .m_axi_awburst(m_awburst), .m_axi_awlock(m_awlock), .m_axi_awcache(m_awcache), .m_axi_awprot(m_awprot),
        .m_axi_awqos(), .m_axi_awregion(), .m_axi_awuser(), .m_axi_awvalid(m_awvalid), .m_axi_awready(m_awready),
        .m_axi_wdata(m_wdata), .m_axi_wstrb(m_wstrb), .m_axi_wlast(m_wlast), .m_axi_wuser(),
        .m_axi_wvalid(m_wvalid), .m_axi_wready(m_wready),
        .m_axi_bid(m_bid), .m_axi_bresp(m_bresp), .m_axi_buser({M{1'b0}}), .m_axi_bvalid(m_bvalid),
        .m_axi_bready(m_bready),
        .m_axi_arid(m_arid), .m_axi_araddr(m_araddr), .m_axi_arlen(m_arlen), .m_axi_arsize(m_arsize),
        .m_axi_arburst(m_arburst), .m_axi_arlock(m_arlock), .m_axi_arcache(m_arcache), .m_axi_arprot(m_arprot),
        .m_axi_arqos(), .m_axi_arregion(), .m_axi_aruser(), .m_axi_arvalid(m_arvalid), .m_axi_arready(m_arready),
        .m_axi_rid(m_rid), .m_axi_rdata(m_rdata), .m_axi_rresp(m_rresp), .m_axi_rlast(m_rlast),
        .m_axi_ruser({M{1'b0}}), .m_axi_rvalid(m_rvalid), .m_axi_rready(m_rready));

    generate
        for (i = 0; i < M; i = i + 1) begin : g_ram
            axi_ram #(.DATA_WIDTH(DW), .ADDR_WIDTH(12), .ID_WIDTH(MID)) u_ram (
                .clk(clk), .rst(rst),
                .s_axi_awid(m_awid[i*MID +: MID]), .s_axi_awaddr(m_awaddr[i*AW +: 12]),
                .s_axi_awlen(m_awlen[i*8 +: 8]), .s_axi_awsize(m_awsize[i*3 +: 3]),
                .s_axi_awburst(m_awburst[i*2 +: 2]), .s_axi_awlock(m_awlock[i]), .s_axi_awcache(m_awcache[i*4 +: 4]),
                .s_axi_awprot(m_awprot[i*3 +: 3]), .s_axi_awvalid(m_awvalid[i]), .s_axi_awready(m_awready[i]),
                .s_axi_wdata(m_wdata[i*DW +: DW]), .s_axi_wstrb(m_wstrb[i*SW +: SW]), .s_axi_wlast(m_wlast[i]),
                .s_axi_wvalid(m_wvalid[i]), .s_axi_wready(m_wready[i]),
                .s_axi_bid(m_bid[i*MID +: MID]), .s_axi_bresp(m_bresp[i*2 +: 2]), .s_axi_bvalid(m_bvalid[i]),
                .s_axi_bready(m_bready[i]),
                .s_axi_arid(m_arid[i*MID +: MID]), .s_axi_araddr(m_araddr[i*AW +: 12]),
                .s_axi_arlen(m_arlen[i*8 +: 8]), .s_axi_arsize(m_arsize[i*3 +: 3]),
                .s_axi_arburst(m_arburst[i*2 +: 2]), .s_axi_arlock(m_arlock[i]), .s_axi_arcache(m_arcache[i*4 +: 4]),
                .s_axi_arprot(m_arprot[i*3 +: 3]), .s_axi_arvalid(m_arvalid[i]), .s_axi_arready(m_arready[i]),
                .s_axi_rid(m_rid[i*MID +: MID]), .s_axi_rdata(m_rdata[i*DW +: DW]), .s_axi_rresp(m_rresp[i*2 +: 2]),
                .s_axi_rlast(m_rlast[i]), .s_axi_rvalid(m_rvalid[i]), .s_axi_rready(m_rready[i]));
        end
    endgenerate

    reg [25:0] alive = 26'd0;
    always @(posedge clk) alive <= alive + 26'd1;
    reg [3:0] led_q = 4'd0;
    always @(posedge clk) led_q <= {alive[25], done[1], done[0], |err};
    assign led = led_q;
endmodule
