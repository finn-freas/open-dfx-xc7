module idelay_nogrp (input wire clk, input wire din, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [6:0] y;

    wire rdy, dly;
    wire [4:0] cnt;
    IDELAYCTRL u_ctrl (.REFCLK(clk), .RST(1'b0), .RDY(rdy));
    IDELAYE2 #(.IDELAY_TYPE("VARIABLE"), .IDELAY_VALUE(5), .DELAY_SRC("IDATAIN"),
               .REFCLK_FREQUENCY(200.0), .HIGH_PERFORMANCE_MODE("FALSE"), .SIGNAL_PATTERN("DATA")) u_dly (
        .C(clk), .REGRST(1'b0), .LD(s[0]), .CE(s[1]), .INC(s[2]), .CINVCTRL(1'b0), .CNTVALUEIN(s[7:3]),
        .IDATAIN(din), .DATAIN(1'b0), .LDPIPEEN(1'b0), .DATAOUT(dly), .CNTVALUEOUT(cnt));
    reg q = 1'b0;
    always @(posedge clk) q <= dly;
    assign y = {q, rdy, cnt};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 7; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
