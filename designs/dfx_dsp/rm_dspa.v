module rm_slot (input wire clk, input wire [15:0] din, output reg [15:0] dout);
    wire [29:0] acout_a0b0; wire [17:0] bcout_a0b0; wire [47:0] pcout_a0b0; wire [47:0] p_a0b0;
    DSP48E1 #(
        .AREG(0),
        .BREG(0),
        .ACASCREG(0),
        .BCASCREG(0),
        .MREG(0),
        .PREG(0),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_a0b0 (
        .CLK(clk), .A({din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0]}), .B({din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3]}), .C({din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7]}), .D({din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a0b0), .BCOUT(bcout_a0b0), .PCOUT(pcout_a0b0), .P(p_a0b0),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a1b1; wire [17:0] bcout_a1b1; wire [47:0] pcout_a1b1; wire [47:0] p_a1b1;
    DSP48E1 #(
        .AREG(1),
        .BREG(1),
        .ACASCREG(1),
        .BCASCREG(1),
        .MREG(0),
        .PREG(0),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_a1b1 (
        .CLK(clk), .A({din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5]}), .B({din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8]}), .C({din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12]}), .D({din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a1b1), .BCOUT(bcout_a1b1), .PCOUT(pcout_a1b1), .P(p_a1b1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a2b2c2; wire [17:0] bcout_a2b2c2; wire [47:0] pcout_a2b2c2; wire [47:0] p_a2b2c2;
    DSP48E1 #(
        .AREG(2),
        .BREG(2),
        .ACASCREG(2),
        .BCASCREG(2),
        .MREG(0),
        .PREG(0),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_a2b2c2 (
        .CLK(clk), .A({din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10]}), .B({din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13]}), .C({din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1]}), .D({din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a2b2c2), .BCOUT(bcout_a2b2c2), .PCOUT(pcout_a2b2c2), .P(p_a2b2c2),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a2b2c1; wire [17:0] bcout_a2b2c1; wire [47:0] pcout_a2b2c1; wire [47:0] p_a2b2c1;
    DSP48E1 #(
        .AREG(2),
        .BREG(2),
        .ACASCREG(1),
        .BCASCREG(1),
        .MREG(0),
        .PREG(0),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_a2b2c1 (
        .CLK(clk), .A({din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15]}), .B({din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2]}), .C({din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6]}), .D({din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a2b2c1), .BCOUT(bcout_a2b2c1), .PCOUT(pcout_a2b2c1), .P(p_a2b2c1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_m1; wire [17:0] bcout_m1; wire [47:0] pcout_m1; wire [47:0] p_m1;
    DSP48E1 #(
        .AREG(0),
        .BREG(0),
        .ACASCREG(0),
        .BCASCREG(0),
        .MREG(1),
        .PREG(0),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_m1 (
        .CLK(clk), .A({din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4]}), .B({din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7]}), .C({din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11]}), .D({din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_m1), .BCOUT(bcout_m1), .PCOUT(pcout_m1), .P(p_m1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_p1; wire [17:0] bcout_p1; wire [47:0] pcout_p1; wire [47:0] p_p1;
    DSP48E1 #(
        .AREG(0),
        .BREG(0),
        .ACASCREG(0),
        .BCASCREG(0),
        .MREG(0),
        .PREG(1),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_p1 (
        .CLK(clk), .A({din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9]}), .B({din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12]}), .C({din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0]}), .D({din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_p1), .BCOUT(bcout_p1), .PCOUT(pcout_p1), .P(p_p1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a1b0; wire [17:0] bcout_a1b0; wire [47:0] pcout_a1b0; wire [47:0] p_a1b0;
    DSP48E1 #(
        .AREG(1),
        .BREG(0),
        .ACASCREG(1),
        .BCASCREG(0),
        .MREG(0),
        .PREG(0),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_a1b0 (
        .CLK(clk), .A({din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14]}), .B({din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1]}), .C({din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5]}), .D({din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a1b0), .BCOUT(bcout_a1b0), .PCOUT(pcout_a1b0), .P(p_a1b0),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a0b2; wire [17:0] bcout_a0b2; wire [47:0] pcout_a0b2; wire [47:0] p_a0b2;
    DSP48E1 #(
        .AREG(0),
        .BREG(2),
        .ACASCREG(0),
        .BCASCREG(2),
        .MREG(0),
        .PREG(0),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_a0b2 (
        .CLK(clk), .A({din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3]}), .B({din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6]}), .C({din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10]}), .D({din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a0b2), .BCOUT(bcout_a0b2), .PCOUT(pcout_a0b2), .P(p_a0b2),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_other1; wire [17:0] bcout_other1; wire [47:0] pcout_other1; wire [47:0] p_other1;
    DSP48E1 #(
        .AREG(0),
        .BREG(0),
        .ACASCREG(0),
        .BCASCREG(0),
        .MREG(0),
        .PREG(0),
        .CREG(1),
        .DREG(1),
        .ADREG(1),
        .INMODEREG(1),
        .OPMODEREG(1),
        .ALUMODEREG(1),
        .CARRYINREG(1),
        .CARRYINSELREG(1),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_other1 (
        .CLK(clk), .A({din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8]}), .B({din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11]}), .C({din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15]}), .D({din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_other1), .BCOUT(bcout_other1), .PCOUT(pcout_other1), .P(p_other1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_defaults; wire [17:0] bcout_defaults; wire [47:0] pcout_defaults; wire [47:0] p_defaults;
    DSP48E1 #(
        .AREG(1),
        .BREG(1),
        .ACASCREG(1),
        .BCASCREG(1),
        .MREG(1),
        .PREG(1),
        .CREG(1),
        .DREG(1),
        .ADREG(1),
        .INMODEREG(1),
        .OPMODEREG(1),
        .ALUMODEREG(1),
        .CARRYINREG(1),
        .CARRYINSELREG(1),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_defaults (
        .CLK(clk), .A({din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13]}), .B({din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0]}), .C({din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4]}), .D({din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_defaults), .BCOUT(bcout_defaults), .PCOUT(pcout_defaults), .P(p_defaults),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a1b1ce; wire [17:0] bcout_a1b1ce; wire [47:0] pcout_a1b1ce; wire [47:0] p_a1b1ce;
    DSP48E1 #(
        .AREG(1),
        .BREG(1),
        .ACASCREG(1),
        .BCASCREG(1),
        .MREG(0),
        .PREG(0),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_a1b1ce (
        .CLK(clk), .A({din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2]}), .B({din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5]}), .C({din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9]}), .D({din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(din[1]), .CEA2(din[2]), .CEB1(din[3]), .CEB2(din[4]), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a1b1ce), .BCOUT(bcout_a1b1ce), .PCOUT(pcout_a1b1ce), .P(p_a1b1ce),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_casc0; wire [17:0] bcout_casc0; wire [47:0] pcout_casc0; wire [47:0] p_casc0;
    DSP48E1 #(
        .AREG(1),
        .BREG(1),
        .ACASCREG(1),
        .BCASCREG(1),
        .MREG(0),
        .PREG(1),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY")
    ) u_casc0 (
        .CLK(clk), .A({din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7]}), .B({din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10]}), .C({din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14]}), .D({din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_casc0), .BCOUT(bcout_casc0), .PCOUT(pcout_casc0), .P(p_casc0),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_casc1; wire [17:0] bcout_casc1; wire [47:0] pcout_casc1; wire [47:0] p_casc1;
    DSP48E1 #(
        .AREG(1),
        .BREG(1),
        .ACASCREG(1),
        .BCASCREG(1),
        .MREG(0),
        .PREG(1),
        .CREG(0),
        .DREG(0),
        .ADREG(0),
        .INMODEREG(0),
        .OPMODEREG(0),
        .ALUMODEREG(0),
        .CARRYINREG(0),
        .CARRYINSELREG(0),
        .A_INPUT("CASCADE"), .B_INPUT("CASCADE"), .USE_MULT("MULTIPLY")
    ) u_casc1 (
        .CLK(clk), .A({din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8]}), .B({din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11]}), .C({din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15]}), .D({din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3]}),
        .ACIN(acout_casc0), .BCIN(bcout_casc0), .PCIN(pcout_casc0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0010101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_casc1), .BCOUT(bcout_casc1), .PCOUT(pcout_casc1), .P(p_casc1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    always @(posedge clk) dout <= p_a0b0[15:0] ^ p_a0b0[31:16] ^ p_a1b1[15:0] ^ p_a1b1[31:16] ^ p_a2b2c2[15:0] ^ p_a2b2c2[31:16] ^ p_a2b2c1[15:0] ^ p_a2b2c1[31:16] ^ p_m1[15:0] ^ p_m1[31:16] ^ p_p1[15:0] ^ p_p1[31:16] ^ p_a1b0[15:0] ^ p_a1b0[31:16] ^ p_a0b2[15:0] ^ p_a0b2[31:16] ^ p_other1[15:0] ^ p_other1[31:16] ^ p_defaults[15:0] ^ p_defaults[31:16] ^ p_a1b1ce[15:0] ^ p_a1b1ce[31:16] ^ p_casc1[15:0] ^ p_casc1[31:16];
endmodule
