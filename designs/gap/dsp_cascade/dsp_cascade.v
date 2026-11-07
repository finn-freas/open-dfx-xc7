module dsp_cascade (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [47:0] y;

    wire [47:0] p0, p1, pc;
    wire [29:0] ac;
    DSP48E1 #(.AREG(1), .BREG(1), .CREG(1), .MREG(1), .PREG(1), .ACASCREG(1), .BCASCREG(1), .USE_DPORT("FALSE"), .USE_MULT("MULTIPLY")) u_dsp0 (
        .CLK(clk), .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b0), .CEM(1'b1), .CEP(1'b1),
        .CEAD(1'b0), .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0),
        .RSTALLCARRYIN(1'b0), .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .CARRYIN(1'b0), .CARRYINSEL(3'b000), .ALUMODE(4'b0000), .INMODE(5'b00000), .D(25'd0),
        .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0),
        .A({12'd0, s[17:0]}), .B(s[35:18]), .C(48'd0), .OPMODE(7'b0000101),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .P(p0), .PCOUT(pc), .ACOUT(ac));
    DSP48E1 #(.AREG(1), .A_INPUT("CASCADE"), .BREG(1), .CREG(1), .MREG(1), .PREG(1), .ACASCREG(1), .BCASCREG(1), .USE_DPORT("FALSE"), .USE_MULT("MULTIPLY")) u_dsp1 (
        .CLK(clk), .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b0), .CEM(1'b1), .CEP(1'b1),
        .CEAD(1'b0), .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0),
        .RSTALLCARRYIN(1'b0), .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .CARRYIN(1'b0), .CARRYINSEL(3'b000), .ALUMODE(4'b0000), .INMODE(5'b00000), .D(25'd0),
        .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0),
        .A(30'd0), .B(s[53:36]), .C(48'd0), .OPMODE(7'b0010101),
        .ACIN(ac), .BCIN(18'd0), .PCIN(pc), .P(p1));
    assign y = p1;
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < 48; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
