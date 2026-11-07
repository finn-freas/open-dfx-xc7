module f18_w4 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [31:0] y;

    wire [31:0] dout;
    wire [3:0] dop;
    wire empty, full, aempty, afull, rderr, wrerr;
    wire [11:0] rdc, wrc;
    reg [3:0] rst = 4'hf;
    always @(posedge clk) rst <= {rst[2:0], 1'b0};
    FIFO18E1 #(.DATA_WIDTH(4), .FIFO_MODE("FIFO18"), .EN_SYN("TRUE"), .DO_REG(0), .ALMOST_EMPTY_OFFSET(13'h0010), .ALMOST_FULL_OFFSET(13'h0020)) u_fifo (
        .RDCLK(clk), .WRCLK(clk), .RST(rst[3]), .RSTREG(1'b0), .REGCE(1'b1),
        .RDEN(s[0] & ~rst[3]), .WREN(s[1] & ~rst[3]), .DI(s[63:32]), .DIP(s[5:2]),
        .DO(dout), .DOP(dop), .EMPTY(empty), .FULL(full), .ALMOSTEMPTY(aempty), .ALMOSTFULL(afull),
        .RDCOUNT(rdc), .WRCOUNT(wrc), .RDERR(rderr), .WRERR(wrerr));
    assign y = {dout[23:0], dop[1:0], empty, full, aempty, afull, rderr, wrerr} ^ {rdc, wrc, 8'd0};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 32; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
