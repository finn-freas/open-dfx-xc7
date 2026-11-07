module ramb36e1 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [71:0] y;

    wire [31:0] doa, dob;
    wire [3:0] dopa, dopb;
    RAMB36E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(36), .WRITE_WIDTH_A(36), .READ_WIDTH_B(36), .WRITE_WIDTH_B(36),
               .DOA_REG(1), .DOB_REG(1),
               .INIT_00(256'h0123_4567_89ab_cdef_fedc_ba98_7654_3210_0011_2233_4455_6677_8899_aabb_ccdd_eeff),
               .INITP_00(256'h5555_aaaa)) u_ram (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(s[0]), .ENBWREN(s[1]), .REGCEAREGCE(s[2]), .REGCEB(s[3]),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .INJECTDBITERR(1'b0), .INJECTSBITERR(1'b0),
        .ADDRARDADDR({1'b1, s[13:4], 5'b11111}), .ADDRBWRADDR({1'b1, s[23:14], 5'b11111}),
        .DIADI({s[31:0]}), .DIBDI(s[63:32]), .DIPADIP(s[27:24]), .DIPBDIP(s[47:44]),
        .WEA({4{s[60]}}), .WEBWE({4'b0000, {4{s[61]}}}),
        .CASCADEINA(1'b0), .CASCADEINB(1'b0),
        .DOADO(doa), .DOBDO(dob), .DOPADOP(dopa), .DOPBDOP(dopb));
    assign y = {doa, dob, dopa, dopb};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 72; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
