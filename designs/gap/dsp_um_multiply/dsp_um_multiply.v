module dsp_um_multiply (input wire clk, output wire [3:0] led);
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]};
    wire [47:0] p [0:3];
    (* DONT_TOUCH = "TRUE" *) DSP48E1 #(.AREG(1), .BREG(1), .CREG(1), .MREG(0), .PREG(1), .ACASCREG(1), .BCASCREG(1), .USE_DPORT("FALSE"), .USE_MULT("MULTIPLY")) u_dsp0 (
        .CLK(clk), .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b0), .CEM(1'b0), .CEP(1'b1),
        .CEAD(1'b0), .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0),
        .RSTALLCARRYIN(1'b0), .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .CARRYIN(1'b0), .CARRYINSEL(3'b000), .ALUMODE(4'b0000), .INMODE(5'b00000), .D(25'd0),
        .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0),
        .A({12'd0, s[17:0]}), .B(s[35:18]), .C({s[63:36], s[19:0]}), .OPMODE(7'b0110011),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .P(p[0]));
    (* DONT_TOUCH = "TRUE" *) DSP48E1 #(.AREG(1), .BREG(1), .CREG(1), .MREG(0), .PREG(1), .ACASCREG(1), .BCASCREG(1), .USE_DPORT("FALSE"), .USE_MULT("MULTIPLY")) u_dsp1 (
        .CLK(clk), .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b0), .CEM(1'b0), .CEP(1'b1),
        .CEAD(1'b0), .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0),
        .RSTALLCARRYIN(1'b0), .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .CARRYIN(1'b0), .CARRYINSEL(3'b000), .ALUMODE(4'b0000), .INMODE(5'b00000), .D(25'd0),
        .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0),
        .A({12'd0, s[18:1]}), .B(s[36:19]), .C({s[63:37], s[20:0]}), .OPMODE(7'b0110011),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .P(p[1]));
    (* DONT_TOUCH = "TRUE" *) DSP48E1 #(.AREG(1), .BREG(1), .CREG(1), .MREG(0), .PREG(1), .ACASCREG(1), .BCASCREG(1), .USE_DPORT("FALSE"), .USE_MULT("MULTIPLY")) u_dsp2 (
        .CLK(clk), .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b0), .CEM(1'b0), .CEP(1'b1),
        .CEAD(1'b0), .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0),
        .RSTALLCARRYIN(1'b0), .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .CARRYIN(1'b0), .CARRYINSEL(3'b000), .ALUMODE(4'b0000), .INMODE(5'b00000), .D(25'd0),
        .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0),
        .A({12'd0, s[19:2]}), .B(s[37:20]), .C({s[63:38], s[21:0]}), .OPMODE(7'b0110011),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .P(p[2]));
    (* DONT_TOUCH = "TRUE" *) DSP48E1 #(.AREG(1), .BREG(1), .CREG(1), .MREG(0), .PREG(1), .ACASCREG(1), .BCASCREG(1), .USE_DPORT("FALSE"), .USE_MULT("MULTIPLY")) u_dsp3 (
        .CLK(clk), .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b0), .CEM(1'b0), .CEP(1'b1),
        .CEAD(1'b0), .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0),
        .RSTALLCARRYIN(1'b0), .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .CARRYIN(1'b0), .CARRYINSEL(3'b000), .ALUMODE(4'b0000), .INMODE(5'b00000), .D(25'd0),
        .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0),
        .A({12'd0, s[20:3]}), .B(s[38:21]), .C({s[63:39], s[22:0]}), .OPMODE(7'b0110011),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .P(p[3]));
    reg [3:0] f;
    integer i, j;
    always @* begin
        f = 4'd0;
        for (j = 0; j < 4; j = j + 1) for (i = 0; i < 48; i = i + 1) f[i % 4] = f[i % 4] ^ p[j][i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
