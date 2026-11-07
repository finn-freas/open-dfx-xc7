import argparse
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "out": "designs/xdc",
    "clk_pin": "E3",
    "clk_b_pin": "D15",
    "leds": ("H5", "J5", "T9", "T10"),
    "sw": ("A8", "C11", "C10", "A10"),
    "btn": ("D9", "C9", "B9", "B8"),
    "ja": ("G13", "B11", "A11", "D12", "D13", "B18", "A18", "K16"),
    "jb": ("E15", "E16", "C15", "J17", "J18", "K15", "J15", "U12"),
    "bank34_in": "K3",
}

DESIGNS = {}


def design(name, rtl, xdc):
    DESIGNS[name] = (rtl.strip() + "\n", xdc.strip() + "\n")


def pins(port, plist, iostd="LVCMOS33"):
    return "\n".join(f"set_property -dict {{ PACKAGE_PIN {p} IOSTANDARD {iostd} }} [get_ports {{{port}[{i}]}}]"
                     for i, p in enumerate(plist))


def clk_xdc(period=10.0, port="clk", pin=None, name=None):
    nm = f"-name {name} " if name else ""
    return (f"set_property -dict {{ PACKAGE_PIN {pin or CONFIG['clk_pin']} IOSTANDARD LVCMOS33 }} [get_ports {port}]\n"
            f"create_clock {nm}-period {period:.3f} [get_ports {port}]")


def chain(src, n, w=16, prefix="t"):
    lines, prev = [], src
    for i in range(n):
        rot = (3 * i) % (w - 1) + 1
        lines.append(f"    wire [{w - 1}:0] {prefix}{i} = ({prev} ^ {{{prev}[{rot - 1}:0], {prev}[{w - 1}:{rot}]}}) + "
                     f"{prev} + {w}'d{(i * 2654435761) % (1 << w)};")
        prev = f"{prefix}{i}"
    return "\n".join(lines), prev


LED_XDC = pins("led", CONFIG["leds"])
SW_XDC = pins("sw", CONFIG["sw"])


def cdc_rtl(name, stages=4):
    body, last = chain("a", stages)
    return f"""
module {name} (input wire clk_a, input wire clk_b, input wire [3:0] sw, output wire [3:0] led);
    reg [15:0] a = 16'd0;
    always @(posedge clk_a) a <= a + {{12'd0, sw}} + 16'd1;
{body}
    reg [15:0] bq = 16'd0;
    always @(posedge clk_b) bq <= {last};
    reg [15:0] bs = 16'd0;
    always @(posedge clk_b) bs <= bs + bq;
    assign led = bs[15:12];
endmodule
"""


CDC_XDC = "\n".join([clk_xdc(10.0, "clk_a"), clk_xdc(8.0, "clk_b", CONFIG["clk_b_pin"]), SW_XDC, LED_XDC])
for nm, extra in [
    ("x_cdc_none", ""),
    ("x_cdc_groups", "set_clock_groups -asynchronous -group [get_clocks clk_a] -group [get_clocks clk_b]"),
    ("x_cdc_fpclk", "set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b]"),
    ("x_cdc_fpcell", "set_false_path -to [get_cells {bq_reg[*]}]"),
    ("x_cdc_maxdly", "set_max_delay -datapath_only 5.000 -from [get_clocks clk_a] -to [get_clocks clk_b]"),
]:
    design(nm, cdc_rtl(nm), CDC_XDC + ("\n" + extra if extra else ""))


def mmcm_rtl(name, stages=3):
    body, last = chain("a", stages)
    return f"""
module {name} (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    wire clk_ibuf, fb, c1_mmcm, c2_mmcm, c1, c2;
    IBUF u_ibuf (.I(clk), .O(clk_ibuf));
    MMCME2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT_F(10.0), .DIVCLK_DIVIDE(1),
                  .CLKOUT0_DIVIDE_F(10.0), .CLKOUT1_DIVIDE(5))
        u_mmcm (.CLKIN1(clk_ibuf), .CLKFBIN(fb), .CLKFBOUT(fb), .CLKOUT0(c1_mmcm), .CLKOUT1(c2_mmcm),
                .RST(1'b0), .PWRDWN(1'b0), .LOCKED());
    BUFG u_bg1 (.I(c1_mmcm), .O(c1));
    BUFG u_bg2 (.I(c2_mmcm), .O(c2));
    reg [15:0] a = 16'd0;
    always @(posedge c1) a <= a + {{12'd0, sw}} + 16'd1;
{body}
    reg [15:0] dq = 16'd0;
    always @(posedge c2) dq <= {last};
    reg [15:0] ds = 16'd0;
    always @(posedge c2) ds <= ds ^ dq;
    assign led = ds[15:12];
endmodule
"""


MMCM_XDC = "\n".join([clk_xdc(10.0), SW_XDC, LED_XDC])
for nm, extra in [
    ("x_mmcm_none", ""),
    ("x_mmcm_mcp", "set_multicycle_path 2 -setup -to [get_cells {dq_reg[*]}]\n"
                   "set_multicycle_path 1 -hold -end -to [get_cells {dq_reg[*]}]"),
    ("x_mmcm_groups", "set_clock_groups -asynchronous -group [get_clocks c1_mmcm] -group [get_clocks c2_mmcm]"),
]:
    design(nm, mmcm_rtl(nm), MMCM_XDC + ("\n" + extra if extra else ""))


def gen_rtl(name, stages=7):
    body, last = chain("x", stages)
    return f"""
module {name} (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg div = 1'b0;
    always @(posedge clk) div <= ~div;
    wire clk_div;
    BUFG u_bgdiv (.I(div), .O(clk_div));
    reg [15:0] x = 16'd0;
    always @(posedge clk_div) x <= x + {{12'd0, sw}} + 16'd1;
{body}
    reg [15:0] y = 16'd0;
    always @(posedge clk_div) y <= {last};
    assign led = y[15:12];
endmodule
"""


GEN_XDC = "\n".join([clk_xdc(10.0), SW_XDC, LED_XDC])
for nm, extra in [
    ("x_gen_none", ""),
    ("x_gen_div", "create_generated_clock -name clk_div -source [get_ports clk] -divide_by 2 [get_pins div_reg/Q]"),
]:
    design(nm, gen_rtl(nm), GEN_XDC + ("\n" + extra if extra else ""))


def mcp_rtl(name, stages=8):
    body, last = chain("s", stages)
    return f"""
module {name} (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg [15:0] s = 16'd0;
    always @(posedge clk) s <= s + {{12'd0, sw}} + 16'd1;
{body}
    reg [15:0] dq = 16'd0;
    always @(posedge clk) dq <= {last};
    assign led = dq[15:12];
endmodule
"""


MCP_XDC = "\n".join([clk_xdc(10.0), SW_XDC, LED_XDC])
for nm, extra in [
    ("x_mcp_none", ""),
    ("x_mcp_to", "set_multicycle_path 2 -setup -to [get_cells {dq_reg[*]}]\n"
                 "set_multicycle_path 1 -hold -end -to [get_cells {dq_reg[*]}]"),
    ("x_mcp_fromto", "set_multicycle_path 2 -setup -from [get_cells {s_reg[*]}] -to [get_cells {dq_reg[*]}]\n"
                     "set_multicycle_path 1 -hold -end -from [get_cells {s_reg[*]}] -to [get_cells {dq_reg[*]}]"),
    ("x_uncert", "set_clock_uncertainty 1.000 [get_clocks clk]"),
]:
    design(nm, mcp_rtl(nm), MCP_XDC + ("\n" + extra if extra else ""))


def io_rtl(name):
    body, last = chain("r", 2, 8, "u")
    return f"""
module {name} (input wire clk, input wire [3:0] sw, output wire [7:0] ja, output wire [3:0] led);
    reg [7:0] r = 8'd0;
    always @(posedge clk) r <= {{sw, sw}};
{body}
    reg [7:0] o = 8'd0;
    always @(posedge clk) o <= {last};
    assign ja = o;
    assign led = r[3:0];
endmodule
"""


IODLY_XDC = "\n".join([clk_xdc(10.0), SW_XDC, LED_XDC, pins("ja", CONFIG["ja"])])
for nm, extra in [
    ("x_iodly_none", ""),
    ("x_iodly", "set_input_delay -clock [get_clocks clk] 7.000 [get_ports {sw[*]}]\n"
                "set_output_delay -clock [get_clocks clk] 7.000 [get_ports {ja[*]}]"),
]:
    design(nm, io_rtl(nm), IODLY_XDC + ("\n" + extra if extra else ""))

design("x_io_drive", io_rtl("x_io_drive"), "\n".join([clk_xdc(), SW_XDC, LED_XDC, pins("ja", CONFIG["ja"][:6]),
    "set_property -dict { PACKAGE_PIN A18 IOSTANDARD LVTTL } [get_ports {ja[6]}]",
    "set_property -dict { PACKAGE_PIN K16 IOSTANDARD LVCMOS33 } [get_ports {ja[7]}]",
    "set_property DRIVE 4 [get_ports {ja[0]}]",
    "set_property DRIVE 8 [get_ports {ja[1]}]",
    "set_property DRIVE 12 [get_ports {ja[2]}]",
    "set_property DRIVE 16 [get_ports {ja[3]}]",
    "set_property SLEW FAST [get_ports {ja[4]}]",
    "set_property -dict { SLEW FAST DRIVE 16 } [get_ports {ja[5]}]",
    "set_property DRIVE 24 [get_ports {ja[6]}]"]))


def pull_rtl(name):
    return f"""
module {name} (input wire clk, input wire [3:0] btn, output wire [3:0] led);
    reg [3:0] q = 4'd0;
    always @(posedge clk) q <= btn;
    assign led = q;
endmodule
"""


design("x_io_pull", pull_rtl("x_io_pull"), "\n".join([clk_xdc(), LED_XDC, pins("btn", CONFIG["btn"]),
    "set_property PULLUP TRUE [get_ports {btn[0]}]",
    "set_property PULLDOWN TRUE [get_ports {btn[1]}]",
    "set_property KEEPER TRUE [get_ports {btn[2]}]",
    "set_property PULLTYPE PULLUP [get_ports {btn[3]}]"]))

design("x_io_iob", pull_rtl("x_io_iob"), "\n".join([clk_xdc(), LED_XDC, pins("btn", CONFIG["btn"]),
    "set_property IOB TRUE [get_ports {led[0]}]",
    "set_property IOB TRUE [get_ports {led[1]}]",
    "set_property IOB TRUE [get_ports {btn[0]}]"]))

design("x_io_noiob", pull_rtl("x_io_noiob"), "\n".join([clk_xdc(), LED_XDC, pins("btn", CONFIG["btn"])]))


def interm_rtl(name):
    return f"""
module {name} (input wire clk, input wire din, output wire [3:0] led);
    reg [3:0] q = 4'd0;
    always @(posedge clk) q <= {{q[2:0], din}};
    assign led = q;
endmodule
"""


design("x_interm", interm_rtl("x_interm"), "\n".join([clk_xdc(), LED_XDC,
    f"set_property -dict {{ PACKAGE_PIN {CONFIG['bank34_in']} IOSTANDARD SSTL135 IN_TERM UNTUNED_SPLIT_50 }} [get_ports din]",
    "set_property INTERNAL_VREF 0.675 [get_iobanks 34]"]))
design("x_interm_none", interm_rtl("x_interm_none"), "\n".join([clk_xdc(), LED_XDC,
    f"set_property -dict {{ PACKAGE_PIN {CONFIG['bank34_in']} IOSTANDARD SSTL135 }} [get_ports din]",
    "set_property INTERNAL_VREF 0.675 [get_iobanks 34]"]))

design("x_syn_glob", io_rtl("x_syn_glob"), "\n".join([clk_xdc(), SW_XDC, LED_XDC,
    "\n".join(f"set_property PACKAGE_PIN {p} [get_ports {{ja[{i}]}}]" for i, p in enumerate(CONFIG["ja"])),
    "set_property IOSTANDARD LVCMOS33 [get_ports {ja[*]}]",
    "set_property DRIVE 4 [get_ports {ja[*]}]"]))
design("x_syn_list", io_rtl("x_syn_list"), "\n".join([clk_xdc(), SW_XDC, LED_XDC, pins("ja", CONFIG["ja"]),
    "set_property DRIVE 4 [get_ports {ja[0] ja[1] ja[2] ja[3]}]",
    "set_property DRIVE 4 [get_ports ja[4]] [get_ports ja[5]]"]))
design("x_syn_cont", io_rtl("x_syn_cont"), "\n".join([clk_xdc(), SW_XDC, LED_XDC, "\n".join(f"set_property -dict {{ PACKAGE_PIN {p} IOSTANDARD LVCMOS33 }} [get_ports {{ja[{i}]}}]"
              for i, p in enumerate(CONFIG["ja"]) if i > 0),
    "set_property -dict { \\\n    PACKAGE_PIN G13 \\\n    IOSTANDARD LVCMOS33 \\\n    DRIVE 4 \\\n} [get_ports {ja[0]}]"]))


def loc_rtl(name):
    return f"""
module {name} (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    wire clk_ibuf, gclk;
    IBUF u_ibuf (.I(clk), .O(clk_ibuf));
    BUFG u_bufg (.I(clk_ibuf), .O(gclk));
    reg [3:0] q = 4'd0;
    always @(posedge gclk) q <= sw;
    assign led = q;
endmodule
"""


design("x_loc", loc_rtl("x_loc"), "\n".join([clk_xdc(), SW_XDC, LED_XDC,
    "set_property LOC SLICE_X10Y20 [get_cells {q_reg[0]}]",
    "set_property BEL CFF [get_cells {q_reg[0]}]",
    "set_property LOC BUFGCTRL_X0Y5 [get_cells u_bufg]"]))
design("x_loc2", loc_rtl("x_loc2"), "\n".join([clk_xdc(), SW_XDC, LED_XDC,
    "set_property LOC SLICE_X10Y120 [get_cells {q_reg[0]}]",
    "set_property BEL CFF [get_cells {q_reg[0]}]",
    "set_property LOC BUFGCTRL_X0Y20 [get_cells u_bufg]"]))


def async_rtl(name, attr=False):
    a = '(* ASYNC_REG = "TRUE" *) ' if attr else ""
    return f"""
module {name} (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    {a}reg s1 = 1'b0;
    {a}reg s2 = 1'b0;
    {a}reg s3 = 1'b0;
    always @(posedge clk) begin
        s1 <= sw[0];
        s2 <= s1;
        s3 <= s2;
    end
    assign led = {{3'd0, s3}};
endmodule
"""


design("x_async_none", async_rtl("x_async_none"), "\n".join([clk_xdc(), SW_XDC, LED_XDC]))
design("x_async_xdc", async_rtl("x_async_xdc"), "\n".join([clk_xdc(), SW_XDC, LED_XDC,
    "set_property ASYNC_REG TRUE [get_cells s1_reg]",
    "set_property ASYNC_REG TRUE [get_cells s2_reg]",
    "set_property ASYNC_REG TRUE [get_cells s3_reg]"]))
design("x_async_rtl", async_rtl("x_async_rtl", True), "\n".join([clk_xdc(), SW_XDC, LED_XDC]))

design("x_dbg_net", mcp_rtl("x_dbg_net", 2), "\n".join([MCP_XDC, "set_property MARK_DEBUG true [get_nets {dq[*]}]"]))
design("x_keep_cell", mcp_rtl("x_keep_cell", 2), "\n".join([MCP_XDC,
    "set_property DONT_TOUCH true [get_cells {dq_reg[*]}]",
    "set_property KEEP true [get_cells {dq_reg[*]}]"]))
design("x_cdr", mcp_rtl("x_cdr", 2), "\n".join([MCP_XDC, "set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets clk]"]))


def blinky_rtl(name):
    return f"""
module {name} (input wire clk, output wire [3:0] led);
    reg [27:0] count = 28'd0;
    always @(posedge clk) count <= count + 28'd1;
    assign led = count[27:24];
endmodule
"""


design("x_cfg_none", blinky_rtl("x_cfg_none"), "\n".join([clk_xdc(), LED_XDC]))
design("x_cfg", blinky_rtl("x_cfg"), "\n".join([clk_xdc(), LED_XDC,
    "set_property CFGBVS VCCO [current_design]",
    "set_property CONFIG_VOLTAGE 3.3 [current_design]",
    "set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]",
    "set_property BITSTREAM.CONFIG.CONFIGRATE 33 [current_design]",
    "set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]",
    "set_property BITSTREAM.CONFIG.USR_ACCESS 0x12345678 [current_design]"]))


def oreg_rtl(name):
    return f"""
module {name} (input wire clk, input wire [3:0] btn, output wire [3:0] led);
    reg [3:0] c = 4'd0;
    always @(posedge clk) c <= c + btn;
    reg [3:0] q = 4'd0;
    always @(posedge clk) q <= c;
    assign led = q;
endmodule
"""


design("x_io_oiob", oreg_rtl("x_io_oiob"), "\n".join([clk_xdc(), LED_XDC, pins("btn", CONFIG["btn"]),
    "set_property IOB TRUE [get_ports {led[*]}]"]))
design("x_io_onoiob", oreg_rtl("x_io_onoiob"), "\n".join([clk_xdc(), LED_XDC, pins("btn", CONFIG["btn"])]))
design("x_io_iiob", pull_rtl("x_io_iiob"), "\n".join([clk_xdc(), LED_XDC, pins("btn", CONFIG["btn"]),
    "set_property IOB TRUE [get_ports {btn[*]}]"]))
design("x_iodly_minmax", io_rtl("x_iodly_minmax"), "\n".join([IODLY_XDC,
    "set_input_delay -clock [get_clocks clk] -max 4.000 [get_ports {sw[*]}]",
    "set_input_delay -clock [get_clocks clk] -min 1.000 [get_ports {sw[*]}]",
    "set_output_delay -clock [get_clocks clk] -max 3.000 [get_ports {ja[*]}]",
    "set_output_delay -clock [get_clocks clk] -min -1.000 [get_ports {ja[*]}]"]))
design("x_iodly_fall", io_rtl("x_iodly_fall"), "\n".join([IODLY_XDC,
    "set_input_delay -clock [get_clocks clk] -clock_fall 2.000 [get_ports {sw[*]}]",
    "set_output_delay -clock [get_clocks clk] 2.000 [get_ports {ja[*]}]"]))
for nm, extra in [
    ("x_mcp_from", "set_multicycle_path 2 -setup -from [get_cells {s_reg[*]}]\n"
                   "set_multicycle_path 1 -hold -end -from [get_cells {s_reg[*]}]"),
    ("x_mcp_thru", "set_multicycle_path 2 -setup -through [get_pins {dq_reg[*]/D}]\n"
                   "set_multicycle_path 1 -hold -end -through [get_pins {dq_reg[*]/D}]"),
    ("x_fp_thru", "set_false_path -from [get_cells {s_reg[*]}] -through [get_pins {dq_reg[*]/D}]"),
]:
    design(nm, mcp_rtl(nm), MCP_XDC + "\n" + extra)
design("x_maxdly_cells", cdc_rtl("x_maxdly_cells"), CDC_XDC + "\nset_max_delay -datapath_only 5.000 "
       "-from [get_cells {a_reg[*]}] -to [get_cells {bq_reg[*]}]")
design("x_maxdly_dp", mcp_rtl("x_maxdly_dp"), MCP_XDC + "\nset_max_delay 6.000 -to [get_cells {dq_reg[*]}]")

design("x_clk_noncc", loc_rtl("x_clk_noncc"), "\n".join([clk_xdc(pin="B11"), SW_XDC, LED_XDC]))
design("x_clk_nside", loc_rtl("x_clk_nside"), "\n".join([clk_xdc(pin="A8"), "\n".join(
    f"set_property -dict {{ PACKAGE_PIN {p} IOSTANDARD LVCMOS33 }} [get_ports {{sw[{i}]}}]"
    for i, p in enumerate(("D9", "C11", "C10", "A10"))), LED_XDC]))
design("x_clk_noncc_cdr", loc_rtl("x_clk_noncc_cdr"), "\n".join([clk_xdc(pin="B11"), SW_XDC, LED_XDC,
    "set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets clk_ibuf]"]))

CFG_SETTINGS = {
    "x_cfg_compress": ["BITSTREAM.GENERAL.COMPRESS TRUE"],
    "x_cfg_rate": ["BITSTREAM.CONFIG.CONFIGRATE 33"],
    "x_cfg_spi4": ["BITSTREAM.CONFIG.SPI_BUSWIDTH 4"],
    "x_cfg_usr": ["BITSTREAM.CONFIG.USR_ACCESS 0x12345678"],
    "x_cfg_startclk": ["BITSTREAM.STARTUP.STARTUPCLK JtagClk"],
    "x_cfg_cycles": ["BITSTREAM.STARTUP.DONE_CYCLE 6", "BITSTREAM.STARTUP.GTS_CYCLE 4",
                     "BITSTREAM.STARTUP.GWE_CYCLE 5"],
    "x_cfg_spifall": ["BITSTREAM.CONFIG.SPI_FALL_EDGE YES"],
    "x_cfg_extclk": ["BITSTREAM.CONFIG.EXTMASTERCCLK_EN DIV-1"],
    "x_cfg_nocrc": ["BITSTREAM.GENERAL.CRC DISABLE"],
}
for nm, props in CFG_SETTINGS.items():
    design(nm, blinky_rtl(nm), "\n".join([clk_xdc(), LED_XDC] +
                                         [f"set_property {p} [current_design]" for p in props]))

IODLY7 = ("set_input_delay -clock [get_clocks clk] 7.000 [get_ports {sw[*]}]\n"
          "set_output_delay -clock [get_clocks clk] 7.000 [get_ports {ja[*]}]")
for nm, extra in [
    ("x_lat_src", "set_clock_latency -source 1.000 [get_clocks clk]"),
    ("x_lat_net", "set_clock_latency 1.000 [get_clocks clk]"),
    ("x_lat_early", "set_clock_latency -source -early 0.400 [get_clocks clk]\n"
                    "set_clock_latency -source -late 1.000 [get_clocks clk]"),
]:
    design(nm, io_rtl(nm), "\n".join([IODLY_XDC, IODLY7, extra]))
design("x_lat_xsrc", cdc_rtl("x_lat_xsrc"), CDC_XDC + "\nset_clock_latency -source 0.500 [get_clocks clk_b]")
for nm, extra in [
    ("x_jit_in", "set_input_jitter [get_clocks clk] 0.300"),
    ("x_jit_sys", "set_system_jitter 0.200"),
    ("x_jit_both", "set_input_jitter [get_clocks clk] 0.300\nset_system_jitter 0.200"),
]:
    design(nm, mcp_rtl(nm), MCP_XDC + "\n" + extra)
design("x_jit_two", cdc_rtl("x_jit_two"), CDC_XDC + "\nset_input_jitter [get_clocks clk_a] 0.200\n"
       "set_input_jitter [get_clocks clk_b] 0.100")


def keep_rtl(name, attr=""):
    return f"""
module {name} (input wire clk, input wire [3:0] sw, output wire [3:0] led);
    reg [15:0] s = 16'd0;
    always @(posedge clk) s <= s + {{12'd0, sw}} + 16'd1;
    wire [15:0] t0 = (s ^ {{s[0:0], s[15:1]}}) + s;
    {attr}reg [15:0] dq = 16'd0;
    always @(posedge clk) dq <= t0;
    reg [15:0] dd = 16'd0;
    always @(posedge clk) dd <= t0;
    assign led = dq[15:12] ^ dd[15:12];
endmodule
"""


KEEP_XDC = "\n".join([clk_xdc(), SW_XDC, LED_XDC])
design("x_keep_none", keep_rtl("x_keep_none"), KEEP_XDC)
design("x_keep_dt", keep_rtl("x_keep_dt"), KEEP_XDC + "\nset_property DONT_TOUCH true [get_cells {dq_reg[*]}]")
design("x_keep_k", keep_rtl("x_keep_k"), KEEP_XDC + "\nset_property KEEP true [get_cells {dd_reg[*]}]")
design("x_dbg_rtl", keep_rtl("x_dbg_rtl", '(* mark_debug = "true" *) '), KEEP_XDC)

PAD_PAIRS = {
    "35": ["C6 C5", "B7 B6", "A6 A5", "D8 C7", "E6 E5", "C4 B4", "A4 A3", "B1 A1", "B3 B2", "D5 D4", "F4 F3"],
    "14": ["K17 K18", "L14 M14", "L15 L16", "L18 M18", "R12 R13", "R18 T18", "N14 P14", "N17 P18", "M16 M17",
           "N15 N16", "P17 R17", "P15 R15"],
    "15": ["D14 C14", "B13 B14", "C12 B12", "B11 A11", "F13 F14", "B16 B17", "A15 A16", "A13 A14", "B18 A18",
           "E15 E16", "D15 C15", "H16 G16"],
    "34": ["L1 M1", "K3 L3", "N2 N1", "M3 M2", "K5 L4", "U1 V1", "U4 U3", "U2 V2", "V5 V4", "R3 T3", "T5 T4",
           "N5 P5", "P4 P3"],
    "16": ["C9 B9", "B8 A8", "C11 C10", "A10 A9"],
}


def pad_design(name, specs, vrefs):
    pairs = {b: [p.split() for p in v] for b, v in PAD_PAIRS.items()}
    singles = {}
    ports = {"i": [], "o": [], "di": [], "do": []}
    for kind, std, drive, slew, bank in sorted(specs, key=lambda s: s[0] not in ("di", "do")):
        if kind in ("di", "do"):
            ports[kind].append((std, None, slew, pairs[bank].pop(0)))
        else:
            if not singles.get(bank):
                singles[bank] = pairs[bank].pop(0)
            ports[kind].append((std, drive, slew, [singles[bank].pop(0)]))
    ni, no, ndi, ndo = (len(ports[k]) for k in ("i", "o", "di", "do"))
    hdr = ["input wire clk", f"input wire [{ni - 1}:0] i", f"output wire [{no - 1}:0] o"]
    if ndi:
        hdr += [f"input wire [{ndi - 1}:0] dip", f"input wire [{ndi - 1}:0] din"]
    if ndo:
        hdr += [f"output wire [{ndo - 1}:0] dop", f"output wire [{ndo - 1}:0] don"]
    body = [f"    wire [{max(ndi, 1) - 1}:0] di;"]
    body += [f"    IBUFDS u_ibd{k} (.I(dip[{k}]), .IB(din[{k}]), .O(di[{k}]));" for k in range(ndi)]
    if not ndi:
        body.append("    assign di = 1'b0;")
    body += [f"    reg [{ni + max(ndi, 1) - 1}:0] r = 0;", "    always @(posedge clk) r <= {di, i};",
             f"    reg [{no + ndo - 1}:0] q = 0;", "    always @(posedge clk) q <= q + {{" + str(no + ndo - 1)
             + "{1'b0}}, ^r} + 1'b1;", f"    assign o = q[{no - 1}:0];"]
    body += [f"    OBUFDS u_obd{k} (.I(q[{no + k}]), .O(dop[{k}]), .OB(don[{k}]));" for k in range(ndo)]
    rtl = f"module {name} ({', '.join(hdr)});\n" + "\n".join(body) + "\nendmodule\n"
    x = [clk_xdc()]
    for kind, plist in ports.items():
        for k, (std, drive, slew, pins_) in enumerate(plist):
            if kind in ("i", "o"):
                props = f"PACKAGE_PIN {pins_[0]} IOSTANDARD {std}"
                if drive:
                    props += f" DRIVE {drive}"
                if slew and kind == "o":
                    props += f" SLEW {slew}"
                x.append(f"set_property -dict {{ {props} }} [get_ports {{{kind}[{k}]}}]")
            else:
                p = "dip" if kind == "di" else "dop"
                n = "din" if kind == "di" else "don"
                sl = f" SLEW {slew}" if slew and kind == "do" else ""
                x.append(f"set_property -dict {{ PACKAGE_PIN {pins_[0]} IOSTANDARD {std}{sl} }} [get_ports {{{p}[{k}]}}]")
                x.append(f"set_property -dict {{ PACKAGE_PIN {pins_[1]} IOSTANDARD {std}{sl} }} [get_ports {{{n}[{k}]}}]")
    for bank, v in vrefs.items():
        x.append(f"set_property INTERNAL_VREF {v} [get_iobanks {bank}]")
    ins = "i[*]" + (" dip[*]" if ndi else "")
    outs = "o[*]" + (" dop[*]" if ndo else "")
    x.append(f"set_input_delay -clock [get_clocks clk] 1.000 [get_ports {{{ins}}}]")
    x.append(f"set_output_delay -clock [get_clocks clk] 1.000 [get_ports {{{outs}}}]")
    design(name, rtl, "\n".join(x))


def lvcmos(std, drives, bank, slews=("SLOW", "FAST")):
    return [("o", std, d, s, bank) for d in drives for s in slews] + [("i", std, None, None, bank)]


pad_design("x_pad_a",
           lvcmos("LVCMOS33", (4, 8, 12, 16), "35") + [("o", "LVTTL", 12, "SLOW", "35"), ("o", "LVTTL", 24, "FAST", "35"),
                                                      ("i", "LVTTL", None, None, "35")]
           + lvcmos("LVCMOS18", (4, 8, 12, 16, 24), "14")
           + [("o", "HSTL_I_18", None, "SLOW", "14"), ("i", "HSTL_I_18", None, None, "14"),
              ("o", "SSTL18_I", None, "SLOW", "14"), ("i", "SSTL18_I", None, None, "14")]
           + lvcmos("LVCMOS25", (4, 8, 12, 16), "15") + [("di", "LVDS_25", None, None, "15"),
                                                        ("do", "LVDS_25", None, None, "15")]
           + lvcmos("LVCMOS15", (4, 8, 12, 16), "34")
           + [("o", "SSTL15", None, "SLOW", "34"), ("o", "SSTL15", None, "FAST", "34"), ("i", "SSTL15", None, None, "34"),
              ("o", "HSTL_I", None, "SLOW", "34"), ("i", "HSTL_I", None, None, "34"),
              ("di", "DIFF_SSTL15", None, None, "34"), ("do", "DIFF_SSTL15", None, "SLOW", "34")]
           + lvcmos("LVCMOS12", (4, 8, 12), "16"),
           {"14": 0.9, "34": 0.75})
pad_design("x_pad_b",
           [("o", "LVCMOS33", 12, "SLOW", "35"), ("i", "LVCMOS33", None, None, "35"),
            ("o", "SSTL135", None, "SLOW", "34"), ("o", "SSTL135", None, "FAST", "34"), ("i", "SSTL135", None, None, "34"),
            ("di", "DIFF_SSTL135", None, None, "34"), ("do", "DIFF_SSTL135", None, "SLOW", "34"),
            ("o", "HSUL_12", None, "SLOW", "14"), ("i", "HSUL_12", None, None, "14"),
            ("o", "LVCMOS25", 12, "SLOW", "15"), ("i", "LVCMOS25", None, None, "15")],
           {"34": 0.675, "14": 0.6})


def main():
    ap = argparse.ArgumentParser(description="write the XDC coverage test designs into designs/xdc/<name>/")
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    out = CONFIG["root"] / CONFIG["out"]
    for name in a.names or sorted(DESIGNS):
        rtl, xdc = DESIGNS[name]
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.v").write_text(rtl)
        (d / f"{name}.xdc").write_text(xdc)
    print(f"{len(a.names or DESIGNS)} designs in {out}")


if __name__ == "__main__":
    main()
