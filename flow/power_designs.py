import argparse
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "out": "designs/power",
    "clk_pin": "E3",
    "leds": ("H5", "J5", "T9", "T10"),
    "pmod": ("G13", "B11", "A11", "D12", "D13", "B18", "A18", "K16",
             "E15", "E16", "D15", "C15", "J17", "J18", "K15", "J15",
             "U12", "V12", "V10", "V11", "U14", "V14", "T13", "U13"),
    "cfg": ("set_property CFGBVS VCCO [current_design]", "set_property CONFIG_VOLTAGE 3.3 [current_design]"),
}

DESIGNS = {}


def pin(port, p, iostd="LVCMOS33"):
    return f"set_property -dict {{ PACKAGE_PIN {p} IOSTANDARD {iostd} }} [get_ports {{{port}}}]"


def xdc(period=10.0, extra=()):
    out = [pin("clk", CONFIG["clk_pin"]), f"create_clock -name clk -period {period:.3f} [get_ports clk]"]
    out += [pin(f"led[{i}]", p) for i, p in enumerate(CONFIG["leds"])]
    out += list(extra) + list(CONFIG["cfg"])
    return "\n".join(out) + "\n"


XS = """    reg [31:0] s [0:{n1}];
    integer k;
    initial for (k = 0; k <= {n1}; k = k + 1) s[k] = 32'h1234567 + k * 32'h9e3779b9;
    genvar i;
    generate for (i = 0; i <= {n1}; i = i + 1) begin : xs
        wire [31:0] a = s[i] ^ (s[i] << 13);
        wire [31:0] b = a ^ (a >> 17);
        always @(posedge {clk}) s[i] <= b ^ (b << 5);
    end endgenerate"""


def lanes(n, clk="clk"):
    return XS.format(n1=n - 1, clk=clk)


def reduce_expr(name, n):
    return " ^ ".join(f"{name}[{i}]" for i in range(n))


def add(name, rtl, x):
    DESIGNS[name] = (rtl.replace("TOP", name), x)


def xor_design(n, period=10.0, tag=""):
    rtl = f"""module TOP (input wire clk, output wire [3:0] led);
{lanes(n)}
    wire [31:0] r = {reduce_expr("s", n)};
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= r[3:0] ^ r[31:28];
    assign led = l;
endmodule
"""
    add(f"pw_xor{n}{tag}", rtl, xdc(period))


def dsp_design(n, period=10.0, tag=""):
    nl = (n + 1) // 2 + 1
    rtl = f"""module TOP (input wire clk, output wire [3:0] led);
{lanes(nl)}
    reg [47:0] p [0:{n - 1}];
    reg [24:0] a [0:{n - 1}];
    reg [17:0] b [0:{n - 1}];
    reg [42:0] m [0:{n - 1}];
    integer j;
    initial for (j = 0; j < {n}; j = j + 1) p[j] = 48'd0;
    generate for (i = 0; i < {n}; i = i + 1) begin : mac
        always @(posedge clk) begin
            a[i] <= s[i / 2][24:0];
            b[i] <= s[i / 2 + 1][31:14];
            m[i] <= $signed(a[i]) * $signed(b[i]);
            p[i] <= p[i] + {{{{5{{m[i][42]}}}}, m[i]}};
        end
    end endgenerate
    wire [47:0] r = {reduce_expr("p", n)};
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= r[3:0] ^ r[47:44];
    assign led = l;
endmodule
"""
    add(f"pw_dsp{n}{tag}", rtl, xdc(period))


def bram_design(n, period=10.0, tag=""):
    nl = n + 1
    rtl = f"""module TOP (input wire clk, output wire [3:0] led);
{lanes(nl)}
    wire [31:0] q [0:{n - 1}];
    generate for (i = 0; i < {n}; i = i + 1) begin : ram
        (* ram_style = "block" *) reg [31:0] mem [0:1023];
        reg [31:0] rd = 32'd0;
        always @(posedge clk) begin
            if (s[i][0]) mem[s[i][10:1]] <= s[i + 1];
            rd <= mem[s[i][20:11]];
        end
        assign q[i] = rd;
    end endgenerate
    wire [31:0] r = {reduce_expr("q", n)};
    reg [3:0] l = 4'd0;
    always @(posedge clk) l <= r[3:0] ^ r[31:28];
    assign led = l;
endmodule
"""
    add(f"pw_bram{n}{tag}", rtl, xdc(period))


def io_design(n, period=10.0, tag=""):
    nl = (n + 31) // 32
    rtl = f"""module TOP (input wire clk, output wire [3:0] led, output wire [{n - 1}:0] io);
{lanes(nl)}
    reg [{n - 1}:0] o = {n}'d0;
    always @(posedge clk) o <= s[0][{n - 1}:0];
    assign io = o;
    assign led = s[0][31:28];
endmodule
"""
    extra = [pin(f"io[{i}]", CONFIG["pmod"][i]) for i in range(n)]
    add(f"pw_io{n}{tag}", rtl, xdc(period, extra))


def mmcm_design(n, mult, div, tag=""):
    rtl = f"""module TOP (input wire clk, output wire [3:0] led);
    wire fb, co, fclk;
    MMCME2_BASE #(.CLKIN1_PERIOD(10.0), .CLKFBOUT_MULT_F({mult:.1f}), .CLKOUT0_DIVIDE_F({div:.1f})) u_mmcm (
        .CLKIN1(clk), .CLKFBIN(fb), .CLKFBOUT(fb), .CLKOUT0(co), .RST(1'b0), .PWRDWN(1'b0), .LOCKED());
    BUFG u_bg (.I(co), .O(fclk));
{lanes(n, "fclk")}
    wire [31:0] r = {reduce_expr("s", n)};
    reg [3:0] l = 4'd0;
    always @(posedge fclk) l <= r[3:0] ^ r[31:28];
    assign led = l;
endmodule
"""
    add(f"pw_mmcm{n}{tag}", rtl, xdc(10.0))


for n in (8, 32, 128):
    xor_design(n)
xor_design(32, 5.0, "_p5")
xor_design(128, 20.0, "_p20")
for n in (8, 32, 64):
    dsp_design(n)
dsp_design(32, 5.0, "_p5")
for n in (4, 16, 40):
    bram_design(n)
bram_design(16, 5.0, "_p5")
for n in (8, 24):
    io_design(n)
io_design(24, 5.0, "_p5")
mmcm_design(32, 10.0, 5.0, "_200")
mmcm_design(32, 12.0, 8.0, "_150")


def main():
    ap = argparse.ArgumentParser(description="write the power calibration designs into designs/power/<name>/")
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
    print(f"{len(a.names or DESIGNS)} designs in {out}")


if __name__ == "__main__":
    main()
