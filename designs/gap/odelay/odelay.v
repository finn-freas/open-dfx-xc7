module odelay (input wire clk, output wire dout, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [0:0] y;

    wire rdy, odly;
    (* IODELAY_GROUP = "g0" *) IDELAYCTRL u_ctrl (.REFCLK(clk), .RST(1'b0), .RDY(rdy));
    (* IODELAY_GROUP = "g0" *) ODELAYE2 #(.ODELAY_TYPE("FIXED"), .ODELAY_VALUE(5), .DELAY_SRC("ODATAIN"), .REFCLK_FREQUENCY(200.0)) u_dly (
        .C(clk), .REGRST(1'b0), .LD(1'b0), .CE(1'b0), .INC(1'b0), .CINVCTRL(1'b0), .CNTVALUEIN(5'd0),
        .ODATAIN(s[0]), .CLKIN(1'b0), .LDPIPEEN(1'b0), .DATAOUT(odly), .CNTVALUEOUT());
    assign dout = odly;
    assign y = rdy;
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
