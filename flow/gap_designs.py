import argparse
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "clk_pin": "E3",
    "leds": ("H5", "J5", "T9", "T10"),
    "iostd": "LVCMOS33",
}

DESIGNS = {}


def design(name, width, body, ports=(), clk=True, xdc_extra=""):
    DESIGNS[name] = dict(width=width, body=body, ports=ports, clk=clk, xdc_extra=xdc_extra)


design("lut_ff", 5, """
    wire lo;
    LUT6 #(.INIT(64'h6996_9669_9669_6996)) u_lut (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo));
    wire [3:0] fq;
    FDRE #(.INIT(1'b0)) u_fdre (.C(clk), .CE(s[6]), .R(s[7]), .D(lo), .Q(fq[0]));
    FDSE #(.INIT(1'b1)) u_fdse (.C(clk), .CE(s[8]), .S(s[9]), .D(lo), .Q(fq[1]));
    FDCE #(.INIT(1'b0)) u_fdce (.C(clk), .CE(s[10]), .CLR(s[11]), .D(lo), .Q(fq[2]));
    FDPE #(.INIT(1'b1)) u_fdpe (.C(clk), .CE(s[12]), .PRE(s[13]), .D(lo), .Q(fq[3]));
    assign y = {fq, lo};
""")

design("carry4", 40, """
    wire [3:0] co, o;
    CARRY4 u_c4 (.CI(1'b0), .CYINIT(s[0]), .DI(s[4:1]), .S(s[8:5]), .O(o), .CO(co));
    reg [31:0] acc = 32'd0;
    always @(posedge clk) acc <= acc + s[63:32];
    assign y = {acc, co, o};
""")

design("muxf7f8", 3, """
    wire [3:0] lo;
    LUT6 #(.INIT(64'h0123_4567_89ab_cdef)) u_l0 (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo[0]));
    LUT6 #(.INIT(64'hfedc_ba98_7654_3210)) u_l1 (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo[1]));
    LUT6 #(.INIT(64'h0f0f_3c3c_5a5a_9696)) u_l2 (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo[2]));
    LUT6 #(.INIT(64'hf0f0_c3c3_a5a5_6969)) u_l3 (.I0(s[0]), .I1(s[1]), .I2(s[2]), .I3(s[3]), .I4(s[4]), .I5(s[5]), .O(lo[3]));
    wire m7a, m7b, m8;
    MUXF7 u_m7a (.I0(lo[0]), .I1(lo[1]), .S(s[6]), .O(m7a));
    MUXF7 u_m7b (.I0(lo[2]), .I1(lo[3]), .S(s[6]), .O(m7b));
    MUXF8 u_m8 (.I0(m7a), .I1(m7b), .S(s[7]), .O(m8));
    assign y = {m8, m7b, m7a};
""")

design("srl", 3, """
    wire q16, q32a, q31a, q32b;
    SRL16E #(.INIT(16'h1234)) u_srl16 (.CLK(clk), .CE(s[0]), .D(s[1]), .A0(s[2]), .A1(s[3]), .A2(s[4]), .A3(s[5]), .Q(q16));
    SRLC32E #(.INIT(32'h1234_5678)) u_srl32a (.CLK(clk), .CE(s[6]), .D(s[7]), .A(s[12:8]), .Q(q32a), .Q31(q31a));
    SRLC32E #(.INIT(32'h9abc_def0)) u_srl32b (.CLK(clk), .CE(s[6]), .D(q31a), .A(s[17:13]), .Q(q32b), .Q31());
    assign y = {q16, q32a, q32b};
""")

design("ram32m", 8, """
    wire [1:0] doa, dob, doc, dod;
    RAM32M #(.INIT_A(64'h0123_4567_89ab_cdef), .INIT_B(64'h1), .INIT_C(64'h2), .INIT_D(64'h3)) u_ram (
        .WCLK(clk), .WE(s[0]), .ADDRA(s[5:1]), .ADDRB(s[10:6]), .ADDRC(s[15:11]), .ADDRD(s[20:16]),
        .DIA(s[22:21]), .DIB(s[24:23]), .DIC(s[26:25]), .DID(s[28:27]),
        .DOA(doa), .DOB(dob), .DOC(doc), .DOD(dod));
    assign y = {doa, dob, doc, dod};
""")

design("ram64m", 4, """
    wire doa, dob, doc, dod;
    RAM64M #(.INIT_A(64'h0123_4567_89ab_cdef), .INIT_B(64'h1), .INIT_C(64'h2), .INIT_D(64'h3)) u_ram (
        .WCLK(clk), .WE(s[0]), .ADDRA(s[6:1]), .ADDRB(s[12:7]), .ADDRC(s[18:13]), .ADDRD(s[24:19]),
        .DIA(s[25]), .DIB(s[26]), .DIC(s[27]), .DID(s[28]),
        .DOA(doa), .DOB(dob), .DOC(doc), .DOD(dod));
    assign y = {doa, dob, doc, dod};
""")

design("ram64x1d", 2, """
    wire spo, dpo;
    RAM64X1D #(.INIT(64'h0123_4567_89ab_cdef)) u_ram (.WCLK(clk), .WE(s[0]), .D(s[1]),
        .A0(s[2]), .A1(s[3]), .A2(s[4]), .A3(s[5]), .A4(s[6]), .A5(s[7]),
        .DPRA0(s[8]), .DPRA1(s[9]), .DPRA2(s[10]), .DPRA3(s[11]), .DPRA4(s[12]), .DPRA5(s[13]),
        .SPO(spo), .DPO(dpo));
    assign y = {spo, dpo};
""")

design("ram128x1d", 2, """
    wire spo, dpo;
    RAM128X1D #(.INIT(128'h0123_4567_89ab_cdef_0011_2233_4455_6677)) u_ram (.WCLK(clk), .WE(s[0]), .D(s[1]),
        .A(s[8:2]), .DPRA(s[15:9]), .SPO(spo), .DPO(dpo));
    assign y = {spo, dpo};
""")

design("lutram_infer", 8, """
    reg [7:0] mem [0:63];
    always @(posedge clk) if (s[0]) mem[s[6:1]] <= s[14:7];
    assign y = mem[s[20:15]];
""")

RAMB18_CTRL = """.CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(s[0]), .ENBWREN(s[1]), .REGCEAREGCE(s[2]), .REGCEB(s[3]),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0)"""

design("ramb18e1", 36, f"""
    wire [15:0] doa, dob;
    wire [1:0] dopa, dopb;
    RAMB18E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(18), .WRITE_WIDTH_A(18), .READ_WIDTH_B(9), .WRITE_WIDTH_B(9),
               .DOA_REG(1), .DOB_REG(0), .WRITE_MODE_A("READ_FIRST"), .WRITE_MODE_B("WRITE_FIRST"),
               .INIT_A(18'h3_0001), .SRVAL_A(18'h0_0002),
               .INIT_00(256'h0123_4567_89ab_cdef_fedc_ba98_7654_3210_0011_2233_4455_6677_8899_aabb_ccdd_eeff),
               .INITP_00(256'h5555_aaaa)) u_ram (
        {RAMB18_CTRL},
        .ADDRARDADDR({{s[23:14], 4'b0000}}), .ADDRBWRADDR({{s[34:24], 3'b000}}),
        .DIADI(s[50:35]), .DIBDI({{8'h00, s[58:51]}}), .DIPADIP(s[60:59]), .DIPBDIP({{1'b0, s[61]}}),
        .WEA({{s[62], s[62]}}), .WEBWE({{3'b000, s[63]}}),
        .DOADO(doa), .DOBDO(dob), .DOPADOP(dopa), .DOPBDOP(dopb));
    assign y = {{doa, dob, dopa, dopb}};
""")

RAMB36_CTRL = """.CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(s[0]), .ENBWREN(s[1]), .REGCEAREGCE(s[2]), .REGCEB(s[3]),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .INJECTDBITERR(1'b0), .INJECTSBITERR(1'b0)"""

design("ramb36e1", 72, f"""
    wire [31:0] doa, dob;
    wire [3:0] dopa, dopb;
    RAMB36E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(36), .WRITE_WIDTH_A(36), .READ_WIDTH_B(36), .WRITE_WIDTH_B(36),
               .DOA_REG(1), .DOB_REG(1),
               .INIT_00(256'h0123_4567_89ab_cdef_fedc_ba98_7654_3210_0011_2233_4455_6677_8899_aabb_ccdd_eeff),
               .INITP_00(256'h5555_aaaa)) u_ram (
        {RAMB36_CTRL},
        .ADDRARDADDR({{1'b1, s[13:4], 5'b11111}}), .ADDRBWRADDR({{1'b1, s[23:14], 5'b11111}}),
        .DIADI({{s[31:0]}}), .DIBDI(s[63:32]), .DIPADIP(s[27:24]), .DIPBDIP(s[47:44]),
        .WEA({{4{{s[60]}}}}), .WEBWE({{4'b0000, {{4{{s[61]}}}}}}),
        .CASCADEINA(1'b0), .CASCADEINB(1'b0),
        .DOADO(doa), .DOBDO(dob), .DOPADOP(dopa), .DOPBDOP(dopb));
    assign y = {{doa, dob, dopa, dopb}};
""")

design("ramb36_cascade", 1, f"""
    wire ca, cb, dlo, dup;
    wire [31:0] dol, dou;
    RAMB36E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(1), .WRITE_WIDTH_A(1), .READ_WIDTH_B(0), .WRITE_WIDTH_B(0),
               .RAM_EXTENSION_A("LOWER"), .RAM_EXTENSION_B("NONE"),
               .INIT_00(256'h0123_4567_89ab_cdef)) u_lo (
        {RAMB36_CTRL},
        .ADDRARDADDR(s[19:4]), .ADDRBWRADDR(16'hffff), .DIADI({{31'd0, s[20]}}), .DIBDI(32'd0), .DIPADIP(4'd0), .DIPBDIP(4'd0),
        .WEA({{4{{s[21]}}}}), .WEBWE(8'd0), .CASCADEINA(1'b0), .CASCADEINB(1'b0), .CASCADEOUTA(ca), .CASCADEOUTB(cb), .DOADO(dol));
    RAMB36E1 #(.RAM_MODE("TDP"), .READ_WIDTH_A(1), .WRITE_WIDTH_A(1), .READ_WIDTH_B(0), .WRITE_WIDTH_B(0),
               .RAM_EXTENSION_A("UPPER"), .RAM_EXTENSION_B("NONE"),
               .INIT_00(256'hfedc_ba98_7654_3210)) u_up (
        {RAMB36_CTRL},
        .ADDRARDADDR(s[19:4]), .ADDRBWRADDR(16'hffff), .DIADI({{31'd0, s[20]}}), .DIBDI(32'd0), .DIPADIP(4'd0), .DIPBDIP(4'd0),
        .WEA({{4{{s[21]}}}}), .WEBWE(8'd0), .CASCADEINA(ca), .CASCADEINB(1'b0), .DOADO(dou));
    assign y = dou[0];
""")

design("ramb36_ecc", 80, """
    wire [31:0] dlo, dhi;
    wire [3:0] plo, phi;
    wire sbit, dbit;
    wire [7:0] eccp;
    wire [8:0] rdaddr;
    RAMB36E1 #(.RAM_MODE("SDP"), .READ_WIDTH_A(72), .WRITE_WIDTH_B(72), .READ_WIDTH_B(0), .WRITE_WIDTH_A(0),
               .EN_ECC_READ("TRUE"), .EN_ECC_WRITE("TRUE"), .DOA_REG(1), .DOB_REG(1)) u_ram (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN(s[0]), .ENBWREN(s[1]), .REGCEAREGCE(s[2]), .REGCEB(1'b0),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .INJECTDBITERR(s[3]), .INJECTSBITERR(s[4]),
        .ADDRARDADDR({1'b1, s[14:6], 6'b111111}), .ADDRBWRADDR({1'b1, s[23:15], 6'b111111}),
        .DIADI(s[63:32]), .DIBDI(s[31:0]), .DIPADIP(4'd0), .DIPBDIP(4'd0),
        .WEA(4'd0), .WEBWE({8{s[5]}}), .CASCADEINA(1'b0), .CASCADEINB(1'b0),
        .DOADO(dlo), .DOBDO(dhi), .DOPADOP(plo), .DOPBDOP(phi),
        .SBITERR(sbit), .DBITERR(dbit), .ECCPARITY(eccp), .RDADDRECC(rdaddr));
    assign y = {dlo, dhi, sbit, dbit, eccp, plo[0], phi[0], rdaddr[3:0]};
""")

design("ramb36_ecc2", 80, DESIGNS["ramb36_ecc"]["body"]
       .replace(".WEBWE({8{s[5]}})", ".WEBWE(8'hff)").replace(".ECCPARITY(eccp), ", "")
       .replace("    wire [7:0] eccp;\n", "    wire [7:0] eccp = 8'd0;\n"))

design("fifo18e1", 22, """
    wire [31:0] dout;
    wire [3:0] dop;
    wire empty, full, aempty, afull, rderr, wrerr;
    wire [11:0] rdc, wrc;
    reg [3:0] rst = 4'hf;
    always @(posedge clk) rst <= {rst[2:0], 1'b0};
    FIFO18E1 #(.DATA_WIDTH(18), .FIFO_MODE("FIFO18"), .EN_SYN("TRUE"), .DO_REG(0),
               .ALMOST_EMPTY_OFFSET(13'h0080), .ALMOST_FULL_OFFSET(13'h0080)) u_fifo (
        .RDCLK(clk), .WRCLK(clk), .RST(rst[3]), .RSTREG(1'b0), .REGCE(1'b1),
        .RDEN(s[0] & ~rst[3]), .WREN(s[1] & ~rst[3]), .DI({16'd0, s[17:2]}), .DIP({2'd0, s[19:18]}),
        .DO(dout), .DOP(dop), .EMPTY(empty), .FULL(full), .ALMOSTEMPTY(aempty), .ALMOSTFULL(afull),
        .RDCOUNT(rdc), .WRCOUNT(wrc), .RDERR(rderr), .WRERR(wrerr));
    assign y = {dout[15:0], dop[1:0], empty, full, aempty, afull} ^ {rdc, wrc[9:0]};
""")

design("fifo18e1_async", 22, DESIGNS["fifo18e1"]["body"].replace('.EN_SYN("TRUE"), .DO_REG(0)', '.EN_SYN("FALSE"), .DO_REG(1)'))

design("fifo36e1", 40, """
    wire [63:0] dout;
    wire [7:0] dop;
    wire empty, full, aempty, afull, rderr, wrerr;
    wire [12:0] rdc, wrc;
    reg [3:0] rst = 4'hf;
    always @(posedge clk) rst <= {rst[2:0], 1'b0};
    FIFO36E1 #(.DATA_WIDTH(36), .FIFO_MODE("FIFO36"), .EN_SYN("TRUE"), .DO_REG(0),
               .ALMOST_EMPTY_OFFSET(13'h0080), .ALMOST_FULL_OFFSET(13'h0080)) u_fifo (
        .RDCLK(clk), .WRCLK(clk), .RST(rst[3]), .RSTREG(1'b0), .REGCE(1'b1),
        .RDEN(s[0] & ~rst[3]), .WREN(s[1] & ~rst[3]), .DI({32'd0, s[33:2]}), .DIP({4'd0, s[37:34]}),
        .INJECTDBITERR(1'b0), .INJECTSBITERR(1'b0),
        .DO(dout), .DOP(dop), .EMPTY(empty), .FULL(full), .ALMOSTEMPTY(aempty), .ALMOSTFULL(afull),
        .RDCOUNT(rdc), .WRCOUNT(wrc), .RDERR(rderr), .WRERR(wrerr));
    assign y = {dout[31:0], dop[3:0], empty, full, aempty, afull} ^ {rdc, wrc, 14'd0};
""")

design("bram_infer", 32, """
    reg [31:0] mem [0:1023];
    reg [31:0] q = 32'd0;
    always @(posedge clk) begin
        if (s[0]) mem[s[10:1]] <= s[63:32];
        q <= mem[s[20:11]];
    end
    assign y = q;
""")

DSP_TIES = """.CEA1(1'b1), .CEA2(1'b1), .CEB1(1'b1), .CEB2(1'b1), .CEC(1'b1), .CED(1'b0), .CEM(1'b1), .CEP(1'b1),
        .CEAD(1'b0), .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0),
        .RSTALLCARRYIN(1'b0), .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .CARRYIN(1'b0), .CARRYINSEL(3'b000), .ALUMODE(4'b0000), .INMODE(5'b00000), .D(25'd0),
        .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0)"""

DSP_P = """.AREG(1), .BREG(1), .CREG(1), .MREG(1), .PREG(1), .ACASCREG(1), .BCASCREG(1), .USE_DPORT("FALSE"), .USE_MULT("MULTIPLY")"""

design("dsp48e1", 48, f"""
    wire [47:0] p;
    DSP48E1 #({DSP_P}) u_dsp (
        .CLK(clk), {DSP_TIES},
        .A({{12'd0, s[17:0]}}), .B(s[35:18]), .C({{s[63:36], s[19:0]}}), .OPMODE(7'b0110101),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .P(p));
    assign y = p;
""")

design("dsp_cascade", 48, f"""
    wire [47:0] p0, p1, pc;
    wire [29:0] ac;
    DSP48E1 #({DSP_P}) u_dsp0 (
        .CLK(clk), {DSP_TIES},
        .A({{12'd0, s[17:0]}}), .B(s[35:18]), .C(48'd0), .OPMODE(7'b0000101),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .P(p0), .PCOUT(pc), .ACOUT(ac));
    DSP48E1 #({DSP_P.replace('.AREG(1)', '.AREG(1), .A_INPUT("CASCADE")')}) u_dsp1 (
        .CLK(clk), {DSP_TIES},
        .A(30'd0), .B(s[53:36]), .C(48'd0), .OPMODE(7'b0010101),
        .ACIN(ac), .BCIN(18'd0), .PCIN(pc), .P(p1));
    assign y = p1;
""")

design("dsp_patdet", 2, f"""
    wire pd, pbd;
    wire [47:0] p;
    DSP48E1 #({DSP_P}, .USE_PATTERN_DETECT("PATDET"), .PATTERN(48'h0000_0000_1234), .MASK(48'hffff_ffff_0000),
              .SEL_PATTERN("PATTERN"), .SEL_MASK("MASK"), .AUTORESET_PATDET("NO_RESET")) u_dsp (
        .CLK(clk), {DSP_TIES},
        .A({{12'd0, s[17:0]}}), .B(s[35:18]), .C({{s[63:36], s[19:0]}}), .OPMODE(7'b0110101),
        .ACIN(30'd0), .BCIN(18'd0), .PCIN(48'd0), .P(p), .PATTERNDETECT(pd), .PATTERNBDETECT(pbd));
    assign y = {{pd, pbd}};
""")

design("dsp_infer", 48, """
    reg signed [24:0] a = 0;
    reg signed [17:0] b = 0;
    reg signed [47:0] c = 0, m = 0, p = 0;
    always @(posedge clk) begin
        a <= s[24:0];
        b <= s[42:25];
        c <= {s[63:43], s[26:0]};
        m <= a * b;
        p <= m + c;
    end
    assign y = p;
""")

COUNTERS = """
    reg [7:0] c0 = 8'd0, c1 = 8'd0;
    always @(posedge g0) c0 <= c0 + 8'd1;
    always @(posedge g1) c1 <= c1 + 8'd1;
"""

design("mmcme2_adv", 17, """
    wire fb, o0, o1, locked, g0, g1;
    wire [15:0] dout;
    wire drdy;
    MMCME2_ADV #(.BANDWIDTH("OPTIMIZED"), .CLKIN1_PERIOD(10.0), .DIVCLK_DIVIDE(1), .CLKFBOUT_MULT_F(10.0),
                 .CLKOUT0_DIVIDE_F(5.0), .CLKOUT1_DIVIDE(20), .CLKOUT1_PHASE(90.0), .CLKOUT1_DUTY_CYCLE(0.5)) u_mmcm (
        .CLKIN1(clk), .CLKIN2(1'b0), .CLKINSEL(1'b1), .CLKFBIN(fb), .CLKFBOUT(fb), .RST(1'b0), .PWRDWN(1'b0),
        .DCLK(1'b0), .DEN(1'b0), .DWE(1'b0), .DADDR(7'd0), .DI(16'd0),
        .PSCLK(1'b0), .PSEN(1'b0), .PSINCDEC(1'b0),
        .CLKOUT0(o0), .CLKOUT1(o1), .LOCKED(locked), .DO(dout), .DRDY(drdy));
    BUFG u_b0 (.I(o0), .O(g0));
    BUFG u_b1 (.I(o1), .O(g1));
""" + COUNTERS + """
    assign y = {c0, c1, locked};
""")

design("mmcme2_base", 17, """
    wire fb, o0, o1, locked, g0, g1;
    MMCME2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT_F(8.0), .CLKOUT0_DIVIDE_F(4.0), .CLKOUT1_DIVIDE(16)) u_mmcm (
        .CLKIN1(clk), .CLKFBIN(fb), .CLKFBOUT(fb), .RST(1'b0), .PWRDWN(1'b0),
        .CLKOUT0(o0), .CLKOUT1(o1), .LOCKED(locked));
    BUFG u_b0 (.I(o0), .O(g0));
    BUFG u_b1 (.I(o1), .O(g1));
""" + COUNTERS + """
    assign y = {c0, c1, locked};
""")

design("plle2_adv", 17, """
    wire fb, o0, o1, locked, g0, g1;
    wire [15:0] dout;
    wire drdy;
    PLLE2_ADV #(.BANDWIDTH("OPTIMIZED"), .CLKIN1_PERIOD(10.0), .DIVCLK_DIVIDE(1), .CLKFBOUT_MULT(12),
                .CLKOUT0_DIVIDE(6), .CLKOUT1_DIVIDE(24), .CLKOUT1_PHASE(45.0)) u_pll (
        .CLKIN1(clk), .CLKIN2(1'b0), .CLKINSEL(1'b1), .CLKFBIN(fb), .CLKFBOUT(fb), .RST(1'b0), .PWRDWN(1'b0),
        .DCLK(1'b0), .DEN(1'b0), .DWE(1'b0), .DADDR(7'd0), .DI(16'd0),
        .CLKOUT0(o0), .CLKOUT1(o1), .LOCKED(locked), .DO(dout), .DRDY(drdy));
    BUFG u_b0 (.I(o0), .O(g0));
    BUFG u_b1 (.I(o1), .O(g1));
""" + COUNTERS + """
    assign y = {c0, c1, locked};
""")

design("bufg", 8, """
    wire g0;
    BUFG u_bufg (.I(clk), .O(g0));
    reg [7:0] c0 = 8'd0;
    always @(posedge g0) c0 <= c0 + 8'd1;
    assign y = c0;
""", clk=False)

design("bufgctrl", 16, """
    reg div = 1'b0;
    always @(posedge clk) div <= ~div;
    wire g0, g1;
    BUFGCTRL #(.INIT_OUT(0), .PRESELECT_I0("TRUE"), .PRESELECT_I1("FALSE")) u_bufgctrl (
        .I0(clk), .I1(div), .S0(~s[0]), .S1(s[0]), .CE0(1'b1), .CE1(1'b1), .IGNORE0(1'b0), .IGNORE1(1'b0), .O(g0));
    BUFGCE u_bufgce (.I(clk), .CE(s[1]), .O(g1));
""" + COUNTERS + """
    assign y = {c0, c1};
""")

design("bufh", 16, """
    wire g0, g1;
    BUFH u_bufh (.I(clk), .O(g0));
    BUFHCE u_bufhce (.I(clk), .CE(s[0]), .O(g1));
""" + COUNTERS + """
    assign y = {c0, c1};
""")

design("bufr", 8, """
    wire g0;
    BUFR #(.BUFR_DIVIDE("2"), .SIM_DEVICE("7SERIES")) u_bufr (.I(clk), .CE(1'b1), .CLR(1'b0), .O(g0));
    reg [7:0] c0 = 8'd0;
    always @(posedge g0) c0 <= c0 + 8'd1;
    assign y = c0;
""")

design("bufio_iddr", 2, """
    wire cio, q1, q2;
    BUFIO u_bufio (.I(clk), .O(cio));
    IDDR #(.DDR_CLK_EDGE("SAME_EDGE_PIPELINED")) u_iddr (.C(cio), .CE(1'b1), .D(din), .R(1'b0), .S(1'b0), .Q1(q1), .Q2(q2));
    assign y = {q1, q2};
""", ports=(("input", 1, "din", "D4"),))

design("iddr_oddr", 2, """
    wire q1, q2;
    IDDR #(.DDR_CLK_EDGE("SAME_EDGE")) u_iddr (.C(clk), .CE(1'b1), .D(din), .R(1'b0), .S(1'b0), .Q1(q1), .Q2(q2));
    ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) u_oddr (.C(clk), .CE(1'b1), .D1(s[0]), .D2(s[1]), .R(1'b0), .S(1'b0), .Q(dout));
    assign y = {q1, q2};
""", ports=(("input", 1, "din", "D4"), ("output", 1, "dout", "F4")))

design("idelay", 7, """
    wire rdy, dly;
    wire [4:0] cnt;
    (* IODELAY_GROUP = "g0" *) IDELAYCTRL u_ctrl (.REFCLK(clk), .RST(1'b0), .RDY(rdy));
    (* IODELAY_GROUP = "g0" *) IDELAYE2 #(.IDELAY_TYPE("VARIABLE"), .IDELAY_VALUE(5), .DELAY_SRC("IDATAIN"),
               .REFCLK_FREQUENCY(200.0), .HIGH_PERFORMANCE_MODE("FALSE"), .SIGNAL_PATTERN("DATA")) u_dly (
        .C(clk), .REGRST(1'b0), .LD(s[0]), .CE(s[1]), .INC(s[2]), .CINVCTRL(1'b0), .CNTVALUEIN(s[7:3]),
        .IDATAIN(din), .DATAIN(1'b0), .LDPIPEEN(1'b0), .DATAOUT(dly), .CNTVALUEOUT(cnt));
    reg q = 1'b0;
    always @(posedge clk) q <= dly;
    assign y = {q, rdy, cnt};
""", ports=(("input", 1, "din", "E2"),))

design("idelay_nogrp", 7, DESIGNS["idelay"]["body"].replace('(* IODELAY_GROUP = "g0" *) ', ''),
       ports=DESIGNS["idelay"]["ports"])

design("idelay_loc", 7, DESIGNS["idelay_nogrp"]["body"], ports=DESIGNS["idelay"]["ports"],
       xdc_extra="set_property LOC IDELAYCTRL_X1Y1 [get_cells u_ctrl]\n")

design("odelay", 1, """
    wire rdy, odly;
    (* IODELAY_GROUP = "g0" *) IDELAYCTRL u_ctrl (.REFCLK(clk), .RST(1'b0), .RDY(rdy));
    (* IODELAY_GROUP = "g0" *) ODELAYE2 #(.ODELAY_TYPE("FIXED"), .ODELAY_VALUE(5), .DELAY_SRC("ODATAIN"), .REFCLK_FREQUENCY(200.0)) u_dly (
        .C(clk), .REGRST(1'b0), .LD(1'b0), .CE(1'b0), .INC(1'b0), .CINVCTRL(1'b0), .CNTVALUEIN(5'd0),
        .ODATAIN(s[0]), .CLKIN(1'b0), .LDPIPEEN(1'b0), .DATAOUT(odly), .CNTVALUEOUT());
    assign dout = odly;
    assign y = rdy;
""", ports=(("output", 1, "dout", "E2"),))

SERDES_CLK = """
    wire cio, cdiv;
    BUFIO u_bufio (.I(clk), .O(cio));
    BUFR #(.BUFR_DIVIDE("4"), .SIM_DEVICE("7SERIES")) u_bufr (.I(clk), .CE(1'b1), .CLR(1'b0), .O(cdiv));
"""

design("iserdes", 4, SERDES_CLK + """
    wire [3:0] q;
    ISERDESE2 #(.DATA_RATE("SDR"), .DATA_WIDTH(4), .INTERFACE_TYPE("NETWORKING"), .IOBDELAY("NONE"),
                .NUM_CE(1), .SERDES_MODE("MASTER"), .IS_CLKB_INVERTED(1'b1)) u_iserdes (
        .D(din), .DDLY(1'b0), .CLK(cio), .CLKB(cio), .CLKDIV(cdiv), .CLKDIVP(1'b0), .OCLK(1'b0), .OCLKB(1'b0),
        .CE1(1'b1), .CE2(1'b1), .RST(1'b0), .BITSLIP(1'b0), .DYNCLKDIVSEL(1'b0), .DYNCLKSEL(1'b0),
        .OFB(1'b0), .SHIFTIN1(1'b0), .SHIFTIN2(1'b0), .Q1(q[0]), .Q2(q[1]), .Q3(q[2]), .Q4(q[3]));
    reg [3:0] r = 4'd0;
    always @(posedge cdiv) r <= q;
    assign y = r;
""", ports=(("input", 1, "din", "D4"),))

design("oserdes", 1, SERDES_CLK + """
    reg [3:0] d = 4'd0;
    always @(posedge cdiv) d <= d + 4'd3;
    wire oq;
    OSERDESE2 #(.DATA_RATE_OQ("SDR"), .DATA_RATE_TQ("SDR"), .DATA_WIDTH(4), .TRISTATE_WIDTH(1), .SERDES_MODE("MASTER")) u_oserdes (
        .CLK(cio), .CLKDIV(cdiv), .D1(d[0]), .D2(d[1]), .D3(d[2]), .D4(d[3]), .D5(1'b0), .D6(1'b0), .D7(1'b0), .D8(1'b0),
        .OCE(1'b1), .RST(1'b0), .T1(1'b0), .T2(1'b0), .T3(1'b0), .T4(1'b0), .TCE(1'b0), .TBYTEIN(1'b0),
        .SHIFTIN1(1'b0), .SHIFTIN2(1'b0), .OQ(oq));
    assign dout = oq;
    assign y = s[0];
""", ports=(("output", 1, "dout", "F4"),))

CIN = ("input", 1, "cin", "F4")


def pin_variant(name, base, ports, edits=()):
    d = DESIGNS[base]
    body = d["body"].replace("u_bufio (.I(clk)", "u_bufio (.I(cin)").replace("u_bufr (.I(clk)", "u_bufr (.I(cin)")
    for old, new in edits:
        body = body.replace(old, new)
    design(name, d["width"], body, ports=ports)


pin_variant("bufr_pin", "bufr", (CIN,))
pin_variant("bufio_pin", "bufio_iddr", (CIN, ("input", 1, "din", "D4")))
pin_variant("iserdes_pin", "iserdes", (CIN, ("input", 1, "din", "D4")), ((".OCLK(1'b0), .OCLKB(1'b0),", ""),))
pin_variant("iserdes_min", "iserdes", (CIN, ("input", 1, "din", "D4")),
            ((".OCLK(1'b0), .OCLKB(1'b0),", ""), (".DDLY(1'b0), ", ""), (".CLKDIVP(1'b0), ", ""),
             (".DYNCLKDIVSEL(1'b0), .DYNCLKSEL(1'b0),", ""), (".OFB(1'b0), .SHIFTIN1(1'b0), .SHIFTIN2(1'b0), ", "")))
pin_variant("iserdes_noshift", "iserdes", (CIN, ("input", 1, "din", "D4")),
            ((".OCLK(1'b0), .OCLKB(1'b0),", ""), (".SHIFTIN1(1'b0), .SHIFTIN2(1'b0), ", "")))
pin_variant("oserdes_pin", "oserdes", (CIN, ("output", 1, "dout", "E2")))

design("muxf8_only", 1, DESIGNS["muxf7f8"]["body"].replace("assign y = {m8, m7b, m7a};", "assign y = m8;"))

design("diff_lvds", 1, """
    wire di;
    IBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("TRUE")) u_ibufds (.I(rx_p), .IB(rx_n), .O(di));
    reg q = 1'b0;
    always @(posedge clk) q <= di ^ s[0];
    OBUFDS #(.IOSTANDARD("LVDS_25")) u_obufds (.I(q), .O(tx_p), .OB(tx_n));
    assign y = q;
""", ports=(("input", 1, "rx_p", "B11", "LVDS_25"), ("input", 1, "rx_n", "A11", "LVDS_25"),
            ("output", 1, "tx_p", "D12", "LVDS_25"), ("output", 1, "tx_n", "D13", "LVDS_25")))

design("diff_lvds_noterm", 1, DESIGNS["diff_lvds"]["body"].replace('.DIFF_TERM("TRUE")', '.DIFF_TERM("FALSE")'),
       ports=DESIGNS["diff_lvds"]["ports"])

design("diff_tmds", 1, """
    OBUFDS #(.IOSTANDARD("TMDS_33")) u_obufds (.I(s[0]), .O(tx_p), .OB(tx_n));
    assign y = s[1];
""", ports=(("output", 1, "tx_p", "B11", "TMDS_33"), ("output", 1, "tx_n", "A11", "TMDS_33")))

design("iobufds", 1, """
    wire o;
    IOBUFDS #(.IOSTANDARD("LVDS_25")) u_iobufds (.I(s[0]), .T(s[1]), .O(o), .IO(io_p), .IOB(io_n));
    assign y = o;
""", ports=(("inout", 1, "io_p", "B18", "LVDS_25"), ("inout", 1, "io_n", "A18", "LVDS_25")))

design("iobuf", 1, """
    wire o;
    IOBUF #(.IOSTANDARD("LVCMOS33"), .DRIVE(8), .SLEW("SLOW")) u_iobuf (.I(s[0]), .T(s[1]), .O(o), .IO(io));
    assign y = o;
""", ports=(("inout", 1, "io", "K16"),))

design("startupe2", 3, """
    wire cfgclk, cfgmclk, eos, preq;
    STARTUPE2 #(.PROG_USR("FALSE")) u_startup (.CLK(1'b0), .GSR(1'b0), .GTS(1'b0), .KEYCLEARB(1'b1), .PACK(1'b0),
        .USRCCLKO(s[0]), .USRCCLKTS(1'b0), .USRDONEO(s[1]), .USRDONETS(1'b0),
        .CFGCLK(cfgclk), .CFGMCLK(cfgmclk), .EOS(eos), .PREQ(preq));
    reg [1:0] c = 2'd0;
    always @(posedge cfgmclk) c <= c + 2'd1;
    assign y = {c, eos};
""")

design("icape2", 32, """
    wire [31:0] o;
    ICAPE2 #(.ICAP_WIDTH("X32")) u_icap (.CLK(clk), .CSIB(s[31]), .RDWRB(s[30]), .I(s[63:32]), .O(o));
    assign y = o;
""")

design("frame_ecce2", 55, """
    wire crcerr, eccerr, eccsingle, synvalid;
    wire [25:0] far;
    wire [4:0] synbit;
    wire [12:0] syn;
    wire [6:0] synword;
    FRAME_ECCE2 #(.FARSRC("EFAR"), .FRAME_RBT_IN_FILENAME("NONE")) u_ecc (
        .CRCERROR(crcerr), .ECCERROR(eccerr), .ECCERRORSINGLE(eccsingle), .FAR(far), .SYNBIT(synbit),
        .SYNDROME(syn), .SYNDROMEVALID(synvalid), .SYNWORD(synword));
    assign y = {crcerr, eccerr, eccsingle, synvalid, far, synbit, syn, synword} ^ s[54:0];
""")

design("xadc", 18, """
    wire [15:0] dout;
    wire drdy, eoc, eos, busy, ot;
    wire [7:0] alm;
    wire [4:0] ch;
    XADC #(.INIT_40(16'h0003), .INIT_41(16'h2000), .INIT_42(16'h0400), .INIT_48(16'h0100), .SIM_DEVICE("7SERIES")) u_xadc (
        .DCLK(clk), .DEN(s[0]), .DWE(1'b0), .DADDR(s[7:1]), .DI(16'd0), .RESET(1'b0),
        .CONVST(1'b0), .CONVSTCLK(1'b0),
        .DO(dout), .DRDY(drdy), .EOC(eoc), .EOS(eos), .BUSY(busy), .OT(ot), .ALM(alm), .CHANNEL(ch));
    assign y = {dout, drdy, eoc ^ eos ^ busy ^ ot ^ (^alm) ^ (^ch)};
""")

XADC_REGS = list(range(0x40, 0x60))


def xadc_values(k):
    vals = {}
    for r in XADC_REGS:
        v = 0
        for b in range(16):
            j = (r - 0x40) * 16 + b
            if k == "all" or (k != "none" and (j >> k) & 1):
                v |= 1 << b
        vals[r] = v
    return vals


for k in ["none", "all"] + list(range(9)):
    params = ", ".join(f".INIT_{r:02X}(16'h{v:04x})" for r, v in xadc_values(k).items())
    design(f"xadc_fz_{k}", 18, DESIGNS["xadc"]["body"].replace(
        ".INIT_40(16'h0003), .INIT_41(16'h2000), .INIT_42(16'h0400), .INIT_48(16'h0100)", params))

design("dna_port", 1, """
    wire d;
    DNA_PORT #(.SIM_DNA_VALUE(57'h0)) u_dna (.CLK(clk), .READ(s[0]), .SHIFT(s[1]), .DIN(s[2]), .DOUT(d));
    assign y = d;
""")

design("usr_accesse2", 33, """
    wire [31:0] data;
    wire cfgclk, dv;
    USR_ACCESSE2 u_usr (.CFGCLK(cfgclk), .DATA(data), .DATAVALID(dv));
    assign y = {data, dv};
""")

design("bscane2", 9, """
    wire capture, drck, rst, runtest, sel, shift, tck, tdi, tms, update;
    reg tdo = 1'b0;
    BSCANE2 #(.JTAG_CHAIN(1)) u_bscan (.CAPTURE(capture), .DRCK(drck), .RESET(rst), .RUNTEST(runtest), .SEL(sel),
        .SHIFT(shift), .TCK(tck), .TDI(tdi), .TMS(tms), .UPDATE(update), .TDO(tdo));
    always @(posedge tck) tdo <= tdi ^ sel;
    assign y = {capture, rst, runtest, sel, shift, tdi, tms, update, drck};
""")


def port_decl(p):
    d, w, n = p[:3]
    rng = f"[{w - 1}:0] " if w > 1 else ""
    return f"{d} wire {rng}{n}"


def verilog(name, d):
    ports = ["input wire clk"] + [port_decl(p) for p in d["ports"]] + ["output wire [3:0] led"]
    w = d["width"]
    return f"""module {name} ({', '.join(ports)});
    reg [63:0] s = 64'h0123_4567_89ab_cdef;
    always @(posedge clk) s <= {{s[62:0], s[63] ^ s[62] ^ s[60] ^ s[59]}};
    wire [{w - 1}:0] y;
{d['body'].rstrip()}
    reg [3:0] f;
    integer i;
    always @* begin
        f = 4'd0;
        for (i = 0; i < {w}; i = i + 1) f[i % 4] = f[i % 4] ^ y[i];
    end
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= f;
    assign led = l;
endmodule
"""


def xdc(d):
    lines = [f"set_property -dict {{ PACKAGE_PIN {CONFIG['clk_pin']} IOSTANDARD {CONFIG['iostd']} }} [get_ports clk]",
             "create_clock -name sys_clk -period 10.000 [get_ports clk]"]
    for i, pin in enumerate(CONFIG["leds"]):
        lines.append(f"set_property -dict {{ PACKAGE_PIN {pin} IOSTANDARD {CONFIG['iostd']} }} [get_ports {{led[{i}]}}]")
    for p in d["ports"]:
        std = p[4] if len(p) > 4 else CONFIG["iostd"]
        lines.append(f"set_property -dict {{ PACKAGE_PIN {p[3]} IOSTANDARD {std} }} [get_ports {p[2]}]")
    return "\n".join(lines) + "\n" + d["xdc_extra"]


QOR_SLOT = """
module rm_slot (input wire clk, input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output reg [31:0] rd = 32'd0, output reg ready = 1'b0);
    always @(posedge clk) begin
        ready <= valid;
        rd <= rs1 ^ rs2;
    end
endmodule
"""

QOR = {
    "qor_blinky": ("blinky", {"blinky.v": [("module blinky", "module qor_blinky")]}, {}),
    "qor_rv_soc": ("rv_soc", {"rv_soc.v": [("module rv_soc", "module qor_rv_soc"),
                                           ('"designs/rv_soc/fw/main.hex"', '"main.hex"')]},
                   {"fw/main.hex": "main.hex", "picorv32.v": "picorv32.v", "uart.v": "uart.v"}),
    "qor_rv_mul": ("rv_soc", {"rv_soc.v": [("module rv_soc", "module qor_rv_mul"),
                                           ('"designs/rv_soc/fw/main.hex"', '"main.hex"'),
                                           (".ENABLE_FAST_MUL(0), .ENABLE_DIV(0)", ".ENABLE_FAST_MUL(1), .ENABLE_DIV(1)")]},
                   {"fw/main.hex": "main.hex", "picorv32.v": "picorv32.v", "uart.v": "uart.v"}),
}
QOR_TIGHT = {"period": "5.000", "suffix": "_t5"}
for _n in ("qor_rv_soc", "qor_rv_mul"):
    _b, _e, _c = QOR[_n]
    _t = _n + QOR_TIGHT["suffix"]
    QOR[_t] = (_b, {f: [(o, n.replace(_n, _t)) for o, n in subs] for f, subs in _e.items()}, _c)


def write_qor():
    for name, (base, edits, copies) in QOR.items():
        src = CONFIG["root"] / "designs" / base
        out = CONFIG["root"] / "designs" / "gap" / name
        out.mkdir(parents=True, exist_ok=True)
        for f, subs in edits.items():
            text = (src / f).read_text()
            for old, new in subs:
                if old not in text:
                    raise SystemExit(f"{name}: '{old}' not found in {f}")
                text = text.replace(old, new)
            if "rv_soc" in base:
                text += QOR_SLOT
            (out / f"{name}.v").write_text(text)
        for s, d in copies.items():
            (out / d).write_bytes((src / s).read_bytes())
        x = (src / "arty_a7_35t.xdc").read_text()
        if name.endswith(QOR_TIGHT["suffix"]):
            x = x.replace("-period 10.000", f"-period {QOR_TIGHT['period']}")
        (out / "arty_a7_35t.xdc").write_text(x)
    print(f"wrote {len(QOR)} QoR designs")


def main():
    ap = argparse.ArgumentParser(description="write one tiny design per primitive under designs/gap")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--qor", action="store_true", help="also copy the QoR designs (blinky, rv_soc variants)")
    a = ap.parse_args()
    if a.list:
        print(" ".join(DESIGNS))
        return
    if a.qor:
        write_qor()
    for name, d in DESIGNS.items():
        out = CONFIG["root"] / "designs" / "gap" / name
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{name}.v").write_text(verilog(name, d))
        (out / "arty_a7_35t.xdc").write_text(xdc(d))
    print(f"wrote {len(DESIGNS)} designs")


if __name__ == "__main__":
    main()
