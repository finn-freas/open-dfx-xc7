module ramb18e1 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [35:0] y;

    wire [15:0] doa, dob;
    wire [1:0] dopa, dopb;
    RAMB18E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(18), .WRITE_WIDTH_A(18), .READ_WIDTH_B(9), .WRITE_WIDTH_B(9),
               .DOA_REG(1), .DOB_REG(0), .WRITE_MODE_A("READ_FIRST"), .WRITE_MODE_B("WRITE_FIRST"),
               .INIT_A(18'h3_0001), .SRVAL_A(18'h0_0002),
               .INIT_00(256'h0123_4567_89ab_cdef_fedc_ba98_7654_3210_0011_2233_4455_6677_8899_aabb_ccdd_eeff),
               .INITP_00(256'h5555_aaaa)) u_ram (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(s[0]), .ENBWREN(s[1]), .REGCEAREGCE(s[2]), .REGCEB(s[3]),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .ADDRARDADDR({s[23:14], 4'b0000}), .ADDRBWRADDR({s[34:24], 3'b000}),
        .DIADI(s[50:35]), .DIBDI({8'h00, s[58:51]}), .DIPADIP(s[60:59]), .DIPBDIP({1'b0, s[61]}),
        .WEA({s[62], s[62]}), .WEBWE({3'b000, s[63]}),
        .DOADO(doa), .DOBDO(dob), .DOPADOP(dopa), .DOPBDOP(dopb));
    assign y = {doa, dob, dopa, dopb};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 36; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
