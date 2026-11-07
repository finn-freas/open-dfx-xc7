import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_designs as gd

CONFIG = {
    "root": gd.CONFIG["root"],
    "out": "designs/gap",
    "dt_a": [("D14", "C14"), ("A15", "A16"), ("K13", "J13"), ("C11", "C10"), ("L1", "M1"), ("V5", "V4"), ("R6", "R5")],
    "dt_b": [("B13", "B14"), ("D15", "C15"), ("G18", "F18"), ("C9", "B9"), ("K5", "L4"), ("P4", "P3"), ("R7", "T6")],
    "dt_xdc": [("C16", "C17"), ("U4", "U3")],
    "dt_iobufds": ("A10", "A9"),
}

NEW = []


def design(name, width, body, ports=(), xdc_extra=""):
    gd.design(name, width, body, ports=ports, xdc_extra=xdc_extra)
    NEW.append(name)


def diff_inputs(pairs, term, std="LVDS_25"):
    ports, lines = [], []
    for i, (p, n) in enumerate(pairs):
        ports += [("input", 1, f"rx{i}_p", p, std), ("input", 1, f"rx{i}_n", n, std)]
        attr = "" if term is None else f', .DIFF_TERM("{term}")'
        lines.append(f'    IBUFDS #(.IOSTANDARD("{std}"){attr}) u_ibufds{i} (.I(rx{i}_p), .IB(rx{i}_n), .O(di[{i}]));')
    return ports, lines


def dt_design(name, pairs, term, xdc_extra=""):
    ports, lines = diff_inputs(pairs, term)
    body = f"    wire [{len(pairs) - 1}:0] di;\n" + "\n".join(lines) + f"""
    reg [{len(pairs) - 1}:0] q = 0;
    always @(posedge clk) q <= di ^ s[{len(pairs) - 1}:0];
    assign y = q;
"""
    design(name, len(pairs), body, ports=tuple(ports), xdc_extra=xdc_extra)


dt_design("dt_a", CONFIG["dt_a"], "TRUE")
dt_design("dt_a_none", CONFIG["dt_a"], "FALSE")
dt_design("dt_b", CONFIG["dt_b"], "TRUE")

_xp, _xl = diff_inputs(CONFIG["dt_xdc"], None)
_ip, _in = CONFIG["dt_iobufds"]
design("dt_xdc", 3, f"""
    wire [1:0] di;
{chr(10).join(_xl)}
    wire bo;
    IOBUFDS #(.IOSTANDARD("LVDS_25"), .DIFF_TERM("TRUE")) u_iobufds (.I(s[4]), .T(s[5]), .O(bo), .IO(io_p), .IOB(io_n));
    reg [2:0] q = 0;
    always @(posedge clk) q <= {{bo, di}} ^ s[2:0];
    assign y = q;
""", ports=tuple(_xp) + (("inout", 1, "io_p", _ip, "LVDS_25"), ("inout", 1, "io_n", _in, "LVDS_25")),
       xdc_extra="".join(f"set_property DIFF_TERM TRUE [get_ports rx{i}_{s}]\n" for i in range(len(CONFIG["dt_xdc"])) for s in "pn"))

design("drv_obuf", 2, """
    OBUF #(.IOSTANDARD("LVCMOS33"), .DRIVE(4), .SLEW("FAST")) u_o4 (.I(s[0]), .O(o4));
    OBUF #(.IOSTANDARD("LVCMOS33"), .DRIVE(16)) u_o16 (.I(s[1]), .O(o16));
    assign y = s[3:2];
""", ports=(("output", 1, "o4", "D14"), ("output", 1, "o16", "A15")))

design("drv_xdc_over", 1, """
    OBUF #(.IOSTANDARD("LVCMOS33"), .DRIVE(4), .SLEW("SLOW")) u_o (.I(s[0]), .O(o));
    assign y = s[1];
""", ports=(("output", 1, "o", "D14"),), xdc_extra="set_property -dict { DRIVE 16 SLEW FAST } [get_ports o]\n")

for _w in ("X8", "X16"):
    design(f"icape2_{_w.lower()}", 32, gd.DESIGNS["icape2"]["body"].replace('"X32"', f'"{_w}"'))

design("icap_dna", 33, gd.DESIGNS["icape2"]["body"].replace("assign y = o;", """wire d;
    DNA_PORT #(.SIM_DNA_VALUE(57'h0)) u_dna (.CLK(clk), .READ(s[0]), .SHIFT(s[1]), .DIN(s[2]), .DOUT(d));
    assign y = {o, d};"""))

design("dna_port2", 2, """
    reg div = 1'b0;
    always @(posedge clk) div <= ~div;
    wire gd, d;
    BUFG u_bufg (.I(div), .O(gd));
    reg rd = 1'b1, sh = 1'b0;
    always @(posedge gd) begin rd <= 1'b0; sh <= ~sh; end
    DNA_PORT u_dna (.CLK(gd), .READ(rd), .SHIFT(sh), .DIN(d), .DOUT(d));
    assign y = {d, sh};
""")

FIFO18_IO = """
    wire [31:0] dout;
    wire [3:0] dop;
    wire empty, full, aempty, afull, rderr, wrerr;
    wire [11:0] rdc, wrc;
    reg [3:0] rst = 4'hf;
    always @(posedge clk) rst <= {rst[2:0], 1'b0};
"""

FIFO18_PORTS = """
        .RDCLK(clk), .WRCLK(clk), .RST(rst[3]), .RSTREG(1'b0), .REGCE(1'b1),
        .RDEN(s[0] & ~rst[3]), .WREN(s[1] & ~rst[3]), .DI(s[63:32]), .DIP(s[5:2]),
        .DO(dout), .DOP(dop), .EMPTY(empty), .FULL(full), .ALMOSTEMPTY(aempty), .ALMOSTFULL(afull),
        .RDCOUNT(rdc), .WRCOUNT(wrc), .RDERR(rderr), .WRERR(wrerr));"""


def fifo18(name, params, loc=None):
    design(name, 32, FIFO18_IO + f"    FIFO18E1 #({params}) u_fifo (" + FIFO18_PORTS + """
    assign y = {dout[23:0], dop[1:0], empty, full, aempty, afull, rderr, wrerr} ^ {rdc, wrc, 8'd0};
""", xdc_extra=f"set_property LOC {loc} [get_cells u_fifo]\n" if loc else "")


fifo18("f18_w4", '.DATA_WIDTH(4), .FIFO_MODE("FIFO18"), .EN_SYN("TRUE"), .DO_REG(0), '
       ".ALMOST_EMPTY_OFFSET(13'h0010), .ALMOST_FULL_OFFSET(13'h0020)")
fifo18("f18_w9_fwft", '.DATA_WIDTH(9), .FIFO_MODE("FIFO18"), .EN_SYN("FALSE"), .FIRST_WORD_FALL_THROUGH("TRUE"), .DO_REG(1), '
       ".ALMOST_EMPTY_OFFSET(13'h0006), .ALMOST_FULL_OFFSET(13'h0040)")
fifo18("f18_w36", '.DATA_WIDTH(36), .FIFO_MODE("FIFO18_36"), .EN_SYN("TRUE"), .DO_REG(0), '
       ".ALMOST_EMPTY_OFFSET(13'h0011), .ALMOST_FULL_OFFSET(13'h0022)", "RAMB18_X2Y4")
fifo18("f18_async_o", '.DATA_WIDTH(18), .FIFO_MODE("FIFO18"), .EN_SYN("FALSE"), .DO_REG(1), '
       ".ALMOST_EMPTY_OFFSET(13'h0100), .ALMOST_FULL_OFFSET(13'h0055)")

FIFO36_IO = """
    wire [63:0] dout;
    wire [7:0] dop;
    wire empty, full, aempty, afull, rderr, wrerr;
    wire [12:0] rdc, wrc;
    reg [3:0] rst = 4'hf;
    always @(posedge clk) rst <= {rst[2:0], 1'b0};
"""

FIFO36_PORTS = """
        .RDCLK(clk), .WRCLK(clk), .RST(rst[3]), .RSTREG(1'b0), .REGCE(1'b1),
        .RDEN(s[0] & ~rst[3]), .WREN(s[1] & ~rst[3]), .DI({s[31:0], s[63:32]}), .DIP(s[9:2]),
        .INJECTDBITERR(1'b0), .INJECTSBITERR(1'b0),
        .DO(dout), .DOP(dop), .EMPTY(empty), .FULL(full), .ALMOSTEMPTY(aempty), .ALMOSTFULL(afull),
        .RDCOUNT(rdc), .WRCOUNT(wrc), .RDERR(rderr), .WRERR(wrerr));"""


def fifo36(name, params, loc=None):
    design(name, 48, FIFO36_IO + f"    FIFO36E1 #({params}) u_fifo (" + FIFO36_PORTS + """
    assign y = {dout[39:0], dop[1:0], empty, full, aempty, afull, rderr, wrerr} ^ {rdc, wrc, 22'd0};
""", xdc_extra=f"set_property LOC {loc} [get_cells u_fifo]\n" if loc else "")


fifo36("f36_w72", '.DATA_WIDTH(72), .FIFO_MODE("FIFO36_72"), .EN_SYN("TRUE"), .DO_REG(0), '
       ".ALMOST_EMPTY_OFFSET(13'h0012), .ALMOST_FULL_OFFSET(13'h0034)")
fifo36("f36_w9_async", '.DATA_WIDTH(9), .FIFO_MODE("FIFO36"), .EN_SYN("FALSE"), .FIRST_WORD_FALL_THROUGH("TRUE"), .DO_REG(1), '
       ".ALMOST_EMPTY_OFFSET(13'h0033), .ALMOST_FULL_OFFSET(13'h0101)", "RAMB36_X2Y2")
fifo36("f36_w18", '.DATA_WIDTH(18), .FIFO_MODE("FIFO36"), .EN_SYN("TRUE"), .DO_REG(1), '
       ".ALMOST_EMPTY_OFFSET(13'h0123), .ALMOST_FULL_OFFSET(13'h0045)")

design("plle2_base", 17, """
    wire fb, o0, o1, locked, g0, g1;
    PLLE2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT(12), .CLKOUT0_DIVIDE(6), .CLKOUT1_DIVIDE(24)) u_pll (
        .CLKIN1(clk), .CLKFBIN(fb), .CLKFBOUT(fb), .RST(1'b0), .PWRDWN(1'b0),
        .CLKOUT0(o0), .CLKOUT1(o1), .LOCKED(locked));
    BUFG u_b0 (.I(o0), .O(g0));
    BUFG u_b1 (.I(o1), .O(g1));
""" + gd.COUNTERS + """
    assign y = {c0, c1, locked};
""")

design("xadc_idle", 18, gd.DESIGNS["xadc"]["body"].replace(".DCLK(clk), .DEN(s[0]), .DWE(1'b0), .DADDR(s[7:1])",
                                                         ".DCLK(1'b0), .DEN(1'b0), .DWE(1'b0), .DADDR(7'd0)"))

design("mmcme2_base_rst", 17, gd.DESIGNS["mmcme2_base"]["body"].replace(
    "wire fb,", "reg [3:0] r = 4'hf;\n    always @(posedge clk) r <= {r[2:0], s[5]};\n    wire fb,").replace(
    ".RST(1'b0)", ".RST(r[3])"))


def main():
    ap = argparse.ArgumentParser(description="write the primitive-gap designs (DIFF_TERM, DRIVE, ICAP/DNA, FIFO, PLL/MMCM base) under designs/gap")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print(" ".join(NEW))
        return
    for name in NEW:
        out = CONFIG["root"] / CONFIG["out"] / name
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{name}.v").write_text(gd.verilog(name, gd.DESIGNS[name]))
        (out / "arty_a7_35t.xdc").write_text(gd.xdc(gd.DESIGNS[name]))
    print(f"wrote {len(NEW)} designs")


if __name__ == "__main__":
    main()
