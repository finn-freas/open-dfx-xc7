module drc_dsp_nopipe (input wire clk, input wire [1:0] sw, output wire [3:0] led);
    reg [23:0] c = 24'd0;
    always @(posedge clk) c <= c + 24'd1 + sw;
    reg [29:0] a = 30'd0;
    reg [17:0] b = 18'd0;
    always @(posedge clk) begin a <= {c[5:0], c}; b <= c[17:0]; end
    wire [47:0] p;
    DSP48E1 #(.AREG(0), .BREG(0), .ACASCREG(0), .BCASCREG(0), .MREG(0), .PREG(0), .CREG(0), .USE_MULT("MULTIPLY"),
              .OPMODEREG(0), .ALUMODEREG(0), .INMODEREG(0), .CARRYINREG(0), .CARRYINSELREG(0)) u_dsp (
        .CLK(clk), .A(a), .B(b), .C(48'd0), .D(25'd0), .OPMODE(7'b0000101), .ALUMODE(4'd0), .INMODE(5'd0),
        .CARRYIN(1'b0), .CARRYINSEL(3'd0), .CEA1(1'b0), .CEA2(1'b0), .CEB1(1'b0), .CEB2(1'b0), .CEC(1'b0),
        .CED(1'b0), .CEAD(1'b0), .CEM(1'b0), .CEP(1'b0), .CECTRL(1'b0), .CEALUMODE(1'b0), .CEINMODE(1'b0),
        .CECARRYIN(1'b0), .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0),
        .RSTCTRL(1'b0), .RSTALLCARRYIN(1'b0), .RSTALUMODE(1'b0), .RSTINMODE(1'b0), .ACIN(30'd0), .BCIN(18'd0),
        .PCIN(48'd0), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .P(p));
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= p[3:0] ^ p[47:44];
    assign led = l;
endmodule
