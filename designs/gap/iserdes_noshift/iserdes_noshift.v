module iserdes_noshift (input wire clk, input wire cin, input wire din, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [3:0] y;

    wire cio, cdiv;
    BUFIO u_bufio (.I(cin), .O(cio));
    BUFR #(.BUFR_DIVIDE("4"), .SIM_DEVICE("7SERIES")) u_bufr (.I(cin), .CE(1'b1), .CLR(1'b0), .O(cdiv));

    wire [3:0] q;
    ISERDESE2 #(.DATA_RATE("SDR"), .DATA_WIDTH(4), .INTERFACE_TYPE("NETWORKING"), .IOBDELAY("NONE"),
                .NUM_CE(1), .SERDES_MODE("MASTER"), .IS_CLKB_INVERTED(1'b1)) u_iserdes (
        .D(din), .DDLY(1'b0), .CLK(cio), .CLKB(cio), .CLKDIV(cdiv), .CLKDIVP(1'b0), 
        .CE1(1'b1), .CE2(1'b1), .RST(1'b0), .BITSLIP(1'b0), .DYNCLKDIVSEL(1'b0), .DYNCLKSEL(1'b0),
        .OFB(1'b0), .Q1(q[0]), .Q2(q[1]), .Q3(q[2]), .Q4(q[3]));
    reg [3:0] r = 4'd0;
    always @(posedge cdiv) r <= q;
    assign y = r;
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 4; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
