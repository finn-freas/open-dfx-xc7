module drc_ramb36_async (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    reg en = 1'b0;
    always @(posedge clk or posedge sw[1]) if (sw[1]) en <= 1'b0; else en <= c[2];
    wire [31:0] doa, dob;
    RAMB36E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(18), .WRITE_WIDTH_A(18), .READ_WIDTH_B(18), .WRITE_WIDTH_B(18)) u_ram (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(en), .ENBWREN(c[1]), .REGCEAREGCE(1'b1), .REGCEB(1'b1),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .ADDRARDADDR({1'b1, c[13:4], 5'b00000}), .ADDRBWRADDR({1'b1, c[13:4], 5'b00000}), .DIADI({4{c[7:0]}}), .DIBDI({4{c[15:8]}}), .DIPADIP(4'd0), .DIPBDIP(4'd0),
        .WEA({4{c[3]}}), .WEBWE(8'd0), .DOADO(doa), .DOBDO(dob), .CASCADEINA(1'b0), .CASCADEINB(1'b0), .INJECTDBITERR(1'b0), .INJECTSBITERR(1'b0));
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= doa[3:0] ^ dob[3:0];
    assign led = l;
endmodule
