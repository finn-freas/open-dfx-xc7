module ramb36_ecc2 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [79:0] y;

    wire [31:0] dlo, dhi;
    wire [3:0] plo, phi;
    wire sbit, dbit;
    wire [7:0] eccp = 8'd0;
    wire [8:0] rdaddr;
    RAMB36E1 #(.RAM_MODE("SDP"), .READ_WIDTH_A(72), .WRITE_WIDTH_B(72), .READ_WIDTH_B(0), .WRITE_WIDTH_A(0),
               .EN_ECC_READ("TRUE"), .EN_ECC_WRITE("TRUE"), .DOA_REG(1), .DOB_REG(1)) u_ram (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(s[0]), .ENBWREN(s[1]), .REGCEAREGCE(s[2]), .REGCEB(1'b0),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .INJECTDBITERR(s[3]), .INJECTSBITERR(s[4]),
        .ADDRARDADDR({1'b1, s[14:6], 6'b111111}), .ADDRBWRADDR({1'b1, s[23:15], 6'b111111}),
        .DIADI(s[63:32]), .DIBDI(s[31:0]), .DIPADIP(4'd0), .DIPBDIP(4'd0),
        .WEA(4'd0), .WEBWE(8'hff), .CASCADEINA(1'b0), .CASCADEINB(1'b0),
        .DOADO(dlo), .DOBDO(dhi), .DOPADOP(plo), .DOPBDOP(phi),
        .SBITERR(sbit), .DBITERR(dbit), .RDADDRECC(rdaddr));
    assign y = {dlo, dhi, sbit, dbit, eccp, plo[0], phi[0], rdaddr[3:0]};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 80; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
