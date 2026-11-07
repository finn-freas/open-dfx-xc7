module xadc_fz_4 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [17:0] y;

    wire [15:0] dout;
    wire drdy, eoc, eos, busy, ot;
    wire [7:0] alm;
    wire [4:0] ch;
    XADC #(.INIT_40(16'h0000), .INIT_41(16'hffff), .INIT_42(16'h0000), .INIT_43(16'hffff), .INIT_44(16'h0000), .INIT_45(16'hffff), .INIT_46(16'h0000), .INIT_47(16'hffff), .INIT_48(16'h0000), .INIT_49(16'hffff), .INIT_4A(16'h0000), .INIT_4B(16'hffff), .INIT_4C(16'h0000), .INIT_4D(16'hffff), .INIT_4E(16'h0000), .INIT_4F(16'hffff), .INIT_50(16'h0000), .INIT_51(16'hffff), .INIT_52(16'h0000), .INIT_53(16'hffff), .INIT_54(16'h0000), .INIT_55(16'hffff), .INIT_56(16'h0000), .INIT_57(16'hffff), .INIT_58(16'h0000), .INIT_59(16'hffff), .INIT_5A(16'h0000), .INIT_5B(16'hffff), .INIT_5C(16'h0000), .INIT_5D(16'hffff), .INIT_5E(16'h0000), .INIT_5F(16'hffff), .SIM_DEVICE("7SERIES")) u_xadc (
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
