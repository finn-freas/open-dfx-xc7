module ramb36_cascade (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [0:0] y;

    wire ca, cb, dlo, dup;
    wire [31:0] dol, dou;
    RAMB36E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(1), .WRITE_WIDTH_A(1), .READ_WIDTH_B(0), .WRITE_WIDTH_B(0),
               .RAM_EXTENSION_A("LOWER"), .RAM_EXTENSION_B("NONE"),
               .INIT_00(256'h0123_4567_89ab_cdef)) u_lo (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(s[0]), .ENBWREN(s[1]), .REGCEAREGCE(s[2]), .REGCEB(s[3]),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .INJECTDBITERR(1'b0), .INJECTSBITERR(1'b0),
        .ADDRARDADDR(s[19:4]), .ADDRBWRADDR(16'hffff), .DIADI({31'd0, s[20]}), .DIBDI(32'd0), .DIPADIP(4'd0), .DIPBDIP(4'd0),
        .WEA({4{s[21]}}), .WEBWE(8'd0), .CASCADEINA(1'b0), .CASCADEINB(1'b0), .CASCADEOUTA(ca), .CASCADEOUTB(cb), .DOADO(dol));
    RAMB36E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(1), .WRITE_WIDTH_A(1), .READ_WIDTH_B(0), .WRITE_WIDTH_B(0),
               .RAM_EXTENSION_A("UPPER"), .RAM_EXTENSION_B("NONE"),
               .INIT_00(256'hfedc_ba98_7654_3210)) u_up (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(s[0]), .ENBWREN(s[1]), .REGCEAREGCE(s[2]), .REGCEB(s[3]),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .INJECTDBITERR(1'b0), .INJECTSBITERR(1'b0),
        .ADDRARDADDR(s[19:4]), .ADDRBWRADDR(16'hffff), .DIADI({31'd0, s[20]}), .DIBDI(32'd0), .DIPADIP(4'd0), .DIPBDIP(4'd0),
        .WEA({4{s[21]}}), .WEBWE(8'd0), .CASCADEINA(ca), .CASCADEINB(1'b0), .DOADO(dou));
    assign y = dou[0];
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 1; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
