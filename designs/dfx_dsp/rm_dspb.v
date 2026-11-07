module rm_slot (input wire clk, input wire [15:0] din, output reg [15:0] dout);
    wire [29:0] acout_casc30; wire [17:0] bcout_casc30; wire [47:0] pcout_casc30; wire [47:0] p_casc30;
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
    ) u_casc30 (
        .CLK(clk), .A({din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0]}), .B({din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3]}), .C({din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7]}), .D({din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_casc30), .BCOUT(bcout_casc30), .PCOUT(pcout_casc30), .P(p_casc30),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_casc31; wire [17:0] bcout_casc31; wire [47:0] pcout_casc31; wire [47:0] p_casc31;
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
    ) u_casc31 (
        .CLK(clk), .A({din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1]}), .B({din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4]}), .C({din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8]}), .D({din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12]}),
        .ACIN(acout_casc30), .BCIN(bcout_casc30), .PCIN(pcout_casc30), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0010101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_casc31), .BCOUT(bcout_casc31), .PCOUT(pcout_casc31), .P(p_casc31),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_casc32; wire [17:0] bcout_casc32; wire [47:0] pcout_casc32; wire [47:0] p_casc32;
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
    ) u_casc32 (
        .CLK(clk), .A({din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2]}), .B({din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5]}), .C({din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9]}), .D({din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13]}),
        .ACIN(acout_casc31), .BCIN(bcout_casc31), .PCIN(pcout_casc31), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0010101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_casc32), .BCOUT(bcout_casc32), .PCOUT(pcout_casc32), .P(p_casc32),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a2b1; wire [17:0] bcout_a2b1; wire [47:0] pcout_a2b1; wire [47:0] p_a2b1;
    DSP48E1 #(
        .AREG(2),
        .BREG(1),
        .ACASCREG(2),
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
    ) u_a2b1 (
        .CLK(clk), .A({din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5]}), .B({din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8]}), .C({din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12]}), .D({din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a2b1), .BCOUT(bcout_a2b1), .PCOUT(pcout_a2b1), .P(p_a2b1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a1b2; wire [17:0] bcout_a1b2; wire [47:0] pcout_a1b2; wire [47:0] p_a1b2;
    DSP48E1 #(
        .AREG(1),
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
    ) u_a1b2 (
        .CLK(clk), .A({din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10]}), .B({din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13]}), .C({din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1]}), .D({din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a1b2), .BCOUT(bcout_a1b2), .PCOUT(pcout_a1b2), .P(p_a1b2),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a0b1m1p1; wire [17:0] bcout_a0b1m1p1; wire [47:0] pcout_a0b1m1p1; wire [47:0] p_a0b1m1p1;
    DSP48E1 #(
        .AREG(0),
        .BREG(1),
        .ACASCREG(0),
        .BCASCREG(1),
        .MREG(1),
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
    ) u_a0b1m1p1 (
        .CLK(clk), .A({din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15]}), .B({din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2]}), .C({din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6]}), .D({din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a0b1m1p1), .BCOUT(bcout_a0b1m1p1), .PCOUT(pcout_a0b1m1p1), .P(p_a0b1m1p1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a1b1alu; wire [17:0] bcout_a1b1alu; wire [47:0] pcout_a1b1alu; wire [47:0] p_a1b1alu;
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
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("NONE")
    ) u_a1b1alu (
        .CLK(clk), .A({din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4]}), .B({din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7]}), .C({din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11]}), .D({din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000011), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a1b1alu), .BCOUT(bcout_a1b1alu), .PCOUT(pcout_a1b1alu), .P(p_a1b1alu),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    wire [29:0] acout_a1b1clkinv; wire [17:0] bcout_a1b1clkinv; wire [47:0] pcout_a1b1clkinv; wire [47:0] p_a1b1clkinv;
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
        .A_INPUT("DIRECT"), .B_INPUT("DIRECT"), .USE_MULT("MULTIPLY"),
        .IS_CLK_INVERTED(1'b1)
    ) u_a1b1clkinv (
        .CLK(clk), .A({din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9]}), .B({din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12]}), .C({din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0]}), .D({din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a1b1clkinv), .BCOUT(bcout_a1b1clkinv), .PCOUT(pcout_a1b1clkinv), .P(p_a1b1clkinv),
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
        .CLK(clk), .A({din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14]}), .B({din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1]}), .C({din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5]}), .D({din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9],din[8],din[7],din[6],din[5],din[4],din[3],din[2],din[1],din[0],din[15],din[14],din[13],din[12],din[11],din[10],din[9]}),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE(7'b0000101), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_a1b1), .BCOUT(bcout_a1b1), .PCOUT(pcout_a1b1), .P(p_a1b1),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
    always @(posedge clk) dout <= p_casc32[15:0] ^ p_casc32[31:16] ^ p_a2b1[15:0] ^ p_a2b1[31:16] ^ p_a1b2[15:0] ^ p_a1b2[31:16] ^ p_a0b1m1p1[15:0] ^ p_a0b1m1p1[31:16] ^ p_a1b1alu[15:0] ^ p_a1b1alu[31:16] ^ p_a1b1clkinv[15:0] ^ p_a1b1clkinv[31:16] ^ p_a1b1[15:0] ^ p_a1b1[31:16];
endmodule
