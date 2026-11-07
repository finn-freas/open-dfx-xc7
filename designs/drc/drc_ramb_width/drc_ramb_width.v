module drc_ramb_width (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    reg en = 1'b0;
    always @(posedge clk or posedge sw[1]) if (sw[1]) en <= 1'b0; else en <= c[2];
    wire [15:0] doa, dob;
    RAMB18E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(36), .WRITE_WIDTH_A(18), .READ_WIDTH_B(18), .WRITE_WIDTH_B(18)) u_ram (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(c[0]), .ENBWREN(c[1]), .REGCEAREGCE(1'b1), .REGCEB(1'b1),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .ADDRARDADDR({c[13:4], 4'b0000}), .ADDRBWRADDR({c[13:4], 4'b0000}), .DIADI({2{c[7:0]}}), .DIBDI({2{c[15:8]}}), .DIPADIP(2'd0), .DIPBDIP(2'd0),
        .WEA({2{c[3]}}), .WEBWE(4'd0), .DOADO(doa), .DOBDO(dob));
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= doa[3:0] ^ dob[3:0];
    assign led = l;
endmodule
