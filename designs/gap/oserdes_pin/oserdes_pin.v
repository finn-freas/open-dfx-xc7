module oserdes_pin (input wire clk, input wire cin, output wire dout, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [0:0] y;

    wire cio, cdiv;
    BUFIO u_bufio (.I(cin), .O(cio));
    BUFR #(.BUFR_DIVIDE("4"), .SIM_DEVICE("7SERIES")) u_bufr (.I(cin), .CE(1'b1), .CLR(1'b0), .O(cdiv));

    reg [3:0] d = 4'd0;
    always @(posedge cdiv) d <= d + 4'd3;
    wire oq;
    OSERDESE2 #(.DATA_RATE_OQ("SDR"), .DATA_RATE_TQ("SDR"), .DATA_WIDTH(4), .TRISTATE_WIDTH(1), .SERDES_MODE("MASTER")) u_oserdes (
        .CLK(cio), .CLKDIV(cdiv), .D1(d[0]), .D2(d[1]), .D3(d[2]), .D4(d[3]), .D5(1'b0), .D6(1'b0), .D7(1'b0), .D8(1'b0),
        .OCE(1'b1), .RST(1'b0), .T1(1'b0), .T2(1'b0), .T3(1'b0), .T4(1'b0), .TCE(1'b0), .TBYTEIN(1'b0),
        .SHIFTIN1(1'b0), .SHIFTIN2(1'b0), .OQ(oq));
    assign dout = oq;
    assign y = s[0];
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
