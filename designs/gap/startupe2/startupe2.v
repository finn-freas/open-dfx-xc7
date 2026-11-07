module startupe2 (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [2:0] y;

    wire cfgclk, cfgmclk, eos, preq;
    STARTUPE2 #(.PROG_USR("FALSE")) u_startup (.CLK(1'b0), .GSR(1'b0), .GTS(1'b0), .KEYCLEARB(1'b1), .PACK(1'b0),
        .USRCCLKO(s[0]), .USRCCLKTS(1'b0), .USRDONEO(s[1]), .USRDONETS(1'b0),
        .CFGCLK(cfgclk), .CFGMCLK(cfgmclk), .EOS(eos), .PREQ(preq));
    reg [1:0] c = 2'd0;
    always @(posedge cfgmclk) c <= c + 2'd1;
    assign y = {c, eos};
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 3; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
