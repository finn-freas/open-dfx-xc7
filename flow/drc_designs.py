import argparse
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "out": "designs/drc",
    "clk_pin": "E3",
    "sw": ("A8", "C11"),
    "leds": ("H5", "J5", "T9", "T10"),
    "noncc_pin": "U12",
    "b34_in": "K3",
    "b34_out": "K5",
    "b34_vref": "L5",
    "diff_p": "T9",
    "diff_n": "T10",
    "cfg_ok": ("set_property CFGBVS VCCO [current_design]", "set_property CONFIG_VOLTAGE 3.3 [current_design]"),
    "flags": {"drc_unrouted": ("noroute",)},
}

DESIGNS = {}


def design(name, rtl, xdc, cfg=True):
    lines = [xdc.strip()] + (list(CONFIG["cfg_ok"]) if cfg else [])
    DESIGNS[name] = (rtl.strip().replace("TOP", name) + "\n", "\n".join(lines) + "\n")


def pin(port, p, iostd="LVCMOS33"):
    return f"set_property -dict {{ PACKAGE_PIN {p} IOSTANDARD {iostd} }} [get_ports {{{port}}}]"


def base_xdc(clk_pin=None, skip=(), override=None):
    o = override or {}
    out = [o.get("clk", pin("clk", clk_pin or CONFIG["clk_pin"])), "create_clock -name clk -period 10.000 [get_ports clk]"]
    for i, p in enumerate(CONFIG["sw"]):
        out.append(o.get(f"sw[{i}]", pin(f"sw[{i}]", p)))
    for i, p in enumerate(CONFIG["leds"]):
        if f"led[{i}]" not in skip:
            out.append(o.get(f"led[{i}]", pin(f"led[{i}]", p)))
    return "\n".join(x for x in out if x)


PORTS = "input wire clk, input wire [1:0] sw, output wire [3:0] led"
COUNTER = "    reg [23:0] c = 24'd0;\n    always @(posedge clk) c <= c + 24'd1 + sw;"


def rtl(body, ports=PORTS, leds="c[23:20]"):
    return f"module TOP ({ports});\n{COUNTER}\n{body}\n    assign led = {leds};\nendmodule"


BASE = rtl("")
design("drc_ok", BASE, base_xdc())
design("drc_cfgbvs", BASE, base_xdc(), cfg=False)
design("drc_ucio", BASE, base_xdc(override={"led[3]": "set_property IOSTANDARD LVCMOS33 [get_ports {led[3]}]"}))
design("drc_nstd", BASE, base_xdc(override={"led[3]": f"set_property PACKAGE_PIN {CONFIG['leds'][3]} [get_ports {{led[3]}}]"}))
design("drc_bivc", BASE, base_xdc(override={"led[1]": pin("led[1]", CONFIG["leds"][1], "LVCMOS18")}))
design("drc_bivc_in", BASE, base_xdc(override={"sw[1]": pin("sw[1]", CONFIG["sw"][1], "LVCMOS18")}))
design("drc_iostdtype", BASE, base_xdc(override={"sw[1]": pin("sw[1]", CONFIG["sw"][1], "LVDS_25")}))

B34 = PORTS + ", input wire d, output wire q"
B34_BODY = "    reg r = 1'b0;\n    always @(posedge clk) r <= d ^ c[3];\n    assign q = r;"
design("drc_dci", rtl(B34_BODY, B34), base_xdc() + "\n" + pin("d", CONFIG["b34_in"], "LVCMOS15") + "\n" +
       pin("q", CONFIG["b34_out"], "LVDCI_15"))
design("drc_vref", rtl(B34_BODY, B34), base_xdc() + "\n" + pin("d", CONFIG["b34_in"], "SSTL15") + "\n" +
       pin("q", CONFIG["b34_vref"], "SSTL15"))
design("drc_vref_int", rtl(B34_BODY, B34), base_xdc() + "\n" + pin("d", CONFIG["b34_in"], "SSTL15") + "\n" +
       pin("q", CONFIG["b34_vref"], "SSTL15") + "\nset_property INTERNAL_VREF 0.750 [get_iobanks 34]")

design("drc_lutlp", rtl("""    wire x, y;
    (* DONT_TOUCH = "yes" *) LUT2 #(.INIT(4'h6)) u_l1 (.O(x), .I0(y), .I1(sw[0]));
    (* DONT_TOUCH = "yes" *) LUT2 #(.INIT(4'h6)) u_l2 (.O(y), .I0(x), .I1(sw[1]));""", leds="{c[23:21], x}"),
       base_xdc())
design("drc_mdrv", rtl("""    wire m;
    (* DONT_TOUCH = "yes" *) LUT1 #(.INIT(2'b10)) u_d1 (.O(m), .I0(sw[0]));
    (* DONT_TOUCH = "yes" *) LUT1 #(.INIT(2'b10)) u_d2 (.O(m), .I0(sw[1]));""", leds="{c[23:21], m}"),
       base_xdc())
design("drc_gated", rtl("""    wire gclk = clk & sw[0];
    reg [3:0] g = 4'd0;
    always @(posedge gclk) g <= g + 4'd1;""", leds="{c[23:22], g[3:2]}"), base_xdc())
design("drc_ffclk", rtl("""    reg div = 1'b0;
    always @(posedge clk) div <= ~div;
    reg [31:0] r = 32'd0;
    always @(posedge div) r <= {r[30:0], sw[0] ^ r[31]};""", leds="r[31:28] ^ c[23:20]"), base_xdc())
design("drc_noncc", BASE, base_xdc(clk_pin=CONFIG["noncc_pin"]))
design("drc_noncc_cdr", BASE, base_xdc(clk_pin=CONFIG["noncc_pin"]) +
       "\nset_property CLOCK_DEDICATED_ROUTE FALSE [get_nets clk_IBUF]")


def mmcm_rtl(prim, mult, div, fb="fb"):
    mf = "_F" if prim == "MMCME2_BASE" else ""
    od = "_F" if prim == "MMCME2_BASE" else ""
    return f"""module TOP ({PORTS});
    wire fb, co, cb;
    {prim} #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT{mf}({mult}), .CLKOUT0_DIVIDE{od}({div})) u_pll (
        .CLKIN1(clk), .CLKFBIN({fb}), .CLKFBOUT(fb), .CLKOUT0(co), .RST(1'b0), .PWRDWN(1'b0), .LOCKED());
    BUFG u_bg (.I(co), .O(cb));
    reg [23:0] c = 24'd0;
    always @(posedge cb) c <= c + 24'd1 + sw;
    assign led = c[23:20];
endmodule"""


design("drc_mmcm_vco", mmcm_rtl("MMCME2_BASE", "64.0", "64.0"), base_xdc())
design("drc_mmcm_vcolow", mmcm_rtl("MMCME2_BASE", "2.0", "2.0"), base_xdc())
design("drc_pll_vco", mmcm_rtl("PLLE2_BASE", "30", "30"), base_xdc())
design("drc_mmcm_nofb", mmcm_rtl("MMCME2_BASE", "8.0", "8.0", fb="1'b0"), base_xdc())


def ramb_rtl(prim, rw, extra="", ctrl="en"):
    a = "ADDRARDADDR({c[13:4], 4'b0000}), .ADDRBWRADDR({c[13:4], 4'b0000})" if prim == "RAMB18E1" else \
        "ADDRARDADDR({1'b1, c[13:4], 5'b00000}), .ADDRBWRADDR({1'b1, c[13:4], 5'b00000})"
    dw, pw, we = (16, 2, 2) if prim == "RAMB18E1" else (32, 4, 4)
    wb = 4 if prim == "RAMB18E1" else 8
    tail = "" if prim == "RAMB18E1" else (", .CASCADEINA(1'b0), .CASCADEINB(1'b0), .INJECTDBITERR(1'b0), "
                                          ".INJECTSBITERR(1'b0)")
    return f"""module TOP ({PORTS});
{COUNTER}
    reg en = 1'b0;
    always @(posedge clk or posedge sw[1]) if (sw[1]) en <= 1'b0; else en <= c[2];
    wire [{dw - 1}:0] doa, dob;
    {prim} #(.RAM_MODE("TDP"), .READ_WIDTH_A({rw}), .WRITE_WIDTH_A(18), .READ_WIDTH_B(18), .WRITE_WIDTH_B(18){extra}) u_ram (
        .CLKARDCLK(clk), .CLKBWRCLK(clk), .ENARDEN({ctrl}), .ENBWREN(c[1]), .REGCEAREGCE(1'b1), .REGCEB(1'b1),
        .RSTRAMARSTRAM(1'b0), .RSTRAMB(1'b0), .RSTREGARSTREG(1'b0), .RSTREGB(1'b0),
        .{a}, .DIADI({{{dw // 8}{{c[7:0]}}}}), .DIBDI({{{dw // 8}{{c[15:8]}}}}), .DIPADIP({pw}'d0), .DIPBDIP({pw}'d0),
        .WEA({{{we}{{c[3]}}}}), .WEBWE({wb}'d0), .DOADO(doa), .DOBDO(dob){tail});
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= doa[3:0] ^ dob[3:0];
    assign led = l;
endmodule"""


design("drc_ramb_async", ramb_rtl("RAMB18E1", 18), base_xdc())
design("drc_ramb36_async", ramb_rtl("RAMB36E1", 18), base_xdc())
design("drc_ramb_width", ramb_rtl("RAMB18E1", 36, ctrl="c[0]"), base_xdc())

design("drc_dsp_nopipe", f"""module TOP ({PORTS});
{COUNTER}
    reg [29:0] a = 30'd0;
    reg [17:0] b = 18'd0;
    always @(posedge clk) begin a <= {{c[5:0], c}}; b <= c[17:0]; end
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
endmodule""", base_xdc())

design("drc_iobuf_noload", rtl("""    wire io_o;
    (* DONT_TOUCH = "yes" *) IOBUF u_io (.IO(pad), .I(c[5]), .T(c[6]), .O(io_o));""",
                              PORTS + ", inout wire pad"), base_xdc() + "\n" + pin("pad", "U12"))
design("drc_unrouted", BASE, base_xdc())
design("drc_cfgbvs_gnd", BASE, base_xdc() + "\nset_property CFGBVS GND [current_design]\n"
       "set_property CONFIG_VOLTAGE 1.8 [current_design]", cfg=False)
design("drc_cfgbvs_v18", BASE, base_xdc() + "\nset_property CFGBVS VCCO [current_design]\n"
       "set_property CONFIG_VOLTAGE 1.8 [current_design]", cfg=False)

DIFF = PORTS + ", output wire dp, output wire dn"
DIFF_BODY = "    OBUFDS u_ob (.I(c[4]), .O(dp), .OB(dn));"
DIFF_LEDS = pin("led[2]", "U12") + "\n" + pin("led[3]", "V12")
design("drc_diff_npin", rtl(DIFF_BODY, DIFF), "\n".join([base_xdc(skip=("led[2]", "led[3]")), DIFF_LEDS,
       pin("dp", CONFIG["diff_n"], "TMDS_33"), pin("dn", CONFIG["diff_p"], "TMDS_33")]))
design("drc_lvds_vcco", rtl(DIFF_BODY, DIFF), "\n".join([base_xdc(skip=("led[2]", "led[3]")), DIFF_LEDS,
       pin("dp", CONFIG["diff_p"], "LVDS_25"), pin("dn", CONFIG["diff_n"], "LVDS_25")]))

design("drc_idelay_noctrl", rtl("""    wire dd;
    reg r = 1'b0;
    (* IODELAY_GROUP = "g0" *) IDELAYE2 #(.IDELAY_TYPE("FIXED"), .IDELAY_VALUE(5), .DELAY_SRC("IDATAIN")) u_dly (
        .IDATAIN(din), .DATAOUT(dd), .C(1'b0), .CE(1'b0), .INC(1'b0), .LD(1'b0), .LDPIPEEN(1'b0),
        .REGRST(1'b0), .CINVCTRL(1'b0), .CNTVALUEIN(5'd0), .DATAIN(1'b0), .CNTVALUEOUT());
    always @(posedge clk) r <= dd;""", PORTS + ", input wire din", leds="{c[23:21], r}"),
       base_xdc() + "\n" + pin("din", "U12"))


BUFG_N = 33
design("drc_bufg_over", f"""module TOP ({PORTS});
{COUNTER}
    reg [{BUFG_N - 1}:0] dv = {BUFG_N}'d0;
    always @(posedge clk) dv <= dv + {{{{({BUFG_N - 1}){{1'b0}}}}, 1'b1}};
    wire [{BUFG_N - 1}:0] gc;
    reg [{BUFG_N - 1}:0] t = {BUFG_N}'d0;
    genvar i;
    generate for (i = 0; i < {BUFG_N}; i = i + 1) begin : g
        BUFG u_bg (.I(dv[i]), .O(gc[i]));
        always @(posedge gc[i]) t[i] <= ~t[i] ^ sw[0];
    end endgenerate
    assign led = {{c[23:21], ^t}};
endmodule""", base_xdc())

DFX_RTL = """module TOP_rm (input wire clk, input wire [1:0] sw, output wire [1:0] q);
    reg [15:0] r = 16'd0;
    always @(posedge clk) r <= r + {14'd0, sw};
    assign q = r[15:14];
endmodule
module TOP (""" + PORTS + """);
""" + COUNTER + """
    wire [1:0] q;
    (* keep_hierarchy = "yes" *) TOP_rm u_rp (.clk(clk), .sw(sw), .q(q));
    assign led = {c[23:22], q};
endmodule"""


def dfx_xdc(pb=None, rar=False, snap=False):
    out = [base_xdc(), "set_property HD.RECONFIGURABLE true [get_cells u_rp]"]
    if pb:
        out += ["create_pblock pb_rp", "add_cells_to_pblock [get_pblocks pb_rp] [get_cells u_rp]",
                f"resize_pblock [get_pblocks pb_rp] -add {{{pb}}}"]
        if rar:
            out.append("set_property RESET_AFTER_RECONFIG true [get_pblocks pb_rp]")
        if snap:
            out.append("set_property SNAPPING_MODE ON [get_pblocks pb_rp]")
    return "\n".join(out)


design("drc_dfx_ok", DFX_RTL, dfx_xdc("SLICE_X0Y50:SLICE_X11Y99", rar=True, snap=True))
design("drc_dfx_nopb", DFX_RTL, dfx_xdc())
design("drc_dfx_rar", DFX_RTL, dfx_xdc("SLICE_X0Y60:SLICE_X11Y80", rar=True))
design("drc_dfx_small", DFX_RTL, dfx_xdc("SLICE_X0Y60:SLICE_X0Y60"))


def idelay_rtl(group):
    g = '(* IODELAY_GROUP = "g0" *) ' if group else ""
    return f"""module TOP ({PORTS}, input wire din);
{COUNTER}
    wire fb, c200, r200, rdy, dd;
    MMCME2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT_F(10.0), .CLKOUT0_DIVIDE_F(5.0)) u_mmcm (
        .CLKIN1(clk), .CLKFBIN(fb), .CLKFBOUT(fb), .CLKOUT0(c200), .RST(1'b0), .PWRDWN(1'b0), .LOCKED());
    BUFG u_bg (.I(c200), .O(r200));
    {g}IDELAYCTRL u_ctrl (.REFCLK(r200), .RST(1'b0), .RDY(rdy));
    {g}IDELAYE2 #(.IDELAY_TYPE("FIXED"), .IDELAY_VALUE(5), .DELAY_SRC("IDATAIN"), .REFCLK_FREQUENCY(200.0)) u_dly (
        .IDATAIN(din), .DATAOUT(dd), .C(1'b0), .CE(1'b0), .INC(1'b0), .LD(1'b0), .LDPIPEEN(1'b0),
        .REGRST(1'b0), .CINVCTRL(1'b0), .CNTVALUEIN(5'd0), .DATAIN(1'b0), .CNTVALUEOUT());
    reg r = 1'b0;
    always @(posedge clk) r <= dd ^ rdy;
    assign led = {{c[23:21], r}};
endmodule"""


design("drc_idelay_ref200", idelay_rtl(False), base_xdc() + "\n" + pin("din", "U12"))
design("drc_idelay_ref200g", idelay_rtl(True), base_xdc() + "\n" + pin("din", "U12"))


def main():
    ap = argparse.ArgumentParser(description="write the DRC test designs (one per Vivado rule) into designs/drc/<name>/")
    ap.add_argument("names", nargs="*")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print(",".join(sorted(DESIGNS)))
        return
    out = CONFIG["root"] / CONFIG["out"]
    for name in a.names or sorted(DESIGNS):
        v, x = DESIGNS[name]
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.v").write_text(v)
        (d / f"{name}.xdc").write_text(x)
        for f in CONFIG["flags"].get(name, ()):
            (d / f"{f}.txt").write_text("1\n")
    print(f"{len(a.names or DESIGNS)} designs in {out}")


if __name__ == "__main__":
    main()
