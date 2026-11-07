module xadc (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [17:0] y;

    wire [15:0] dout;
    wire drdy, eoc, eos, busy, ot;
    wire [7:0] alm;
    wire [4:0] ch;
    XADC #(.INIT_40(16'h0003), .INIT_41(16'h2000), .INIT_42(16'h0400), .INIT_48(16'h0100), .SIM_DEVICE("7SERIES")) u_xadc (
        .DCLK(clk), .DEN(s[0]), .DWE(1'b0), .DADDR(s[7:1]), .DI(16'd0), .RESET(1'b0),
        .CONVST(1'b0), .CONVSTCLK(1'b0),
        .DO(dout), .DRDY(drdy), .EOC(eoc), .EOS(eos), .BUSY(busy), .OT(ot), .ALM(alm), .CHANNEL(ch));
    assign y = {dout, drdy, eoc ^ eos ^ busy ^ ot ^ (^alm) ^ (^ch)};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 18; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
