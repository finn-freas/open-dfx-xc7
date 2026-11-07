PORTS_JSON = ('{"clk": "clk", "slice_by": 32, "inputs": [["valid", 1], ["funct", 10], ["rs1", 32], ["rs2", 32]], '
              '"outputs": [["rd", 32], ["ready", 1]]}\n')

BLINKY = """module {top} (
    input  wire       clk,
    output wire [3:0] led
);
    reg [27:0] count = 28'd0;
    always @(posedge clk) count <= count + 28'd1;
    assign led = count[27:24];
endmodule
"""

DFX_TOP = """module {top} (
    input  wire       clk,
    output wire [3:0] led
);
    reg [31:0] a = 32'h00000001;
    reg [31:0] b = 32'h0;
    reg [9:0] f = 10'd0;
    reg v = 1'b0;
    always @(posedge clk) begin
        a <= {{a[30:0], a[31] ^ a[21] ^ a[1] ^ a[0]}};
        b <= b + 32'h9E3779B9;
        f <= f + 10'd1;
        v <= ~v;
    end
    wire [31:0] rd;
    wire ready;
    rm_slot u_rm (.clk(clk), .valid(v), .funct(f), .rs1(a), .rs2(b), .rd(rd), .ready(ready));
    reg [31:0] acc = 32'h0;
    always @(posedge clk) if (ready) acc <= acc ^ rd;
    assign led = acc[3:0] ^ acc[7:4] ^ acc[11:8] ^ acc[15:12] ^ acc[19:16] ^ acc[23:20] ^ acc[27:24] ^ acc[31:28];
endmodule
"""

RM_XOR = """module rm_core (input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output wire [31:0] rd, output wire ready);
    assign rd = rs1 ^ rs2;
    assign ready = valid;
endmodule
"""

RM_ANDN = """module rm_core (input wire valid, input wire [9:0] funct, input wire [31:0] rs1, input wire [31:0] rs2,
                output wire [31:0] rd, output wire ready);
    assign rd = funct[0] ? (rs1 | ~rs2) : (rs1 & ~rs2);
    assign ready = valid;
endmodule
"""

PROJECT = """[project]
name = "{name}"
top = "{top}"
{target}
sources = ["src/{top}.v"]
constraints = ["constraints/{top}.xdc"]
seed = 1

[clocks]
clk = {period}
"""

DFX = """
[dfx]
partpins = "{partpins}"
rar = false
compress = false
decoupler = false

[[dfx.partition]]
name = "rp0"
inst = "u_rm"
region = "{region}"
ports = "rm/ports.json"
register = ["ready"]
rms = {{ xor = "rm/rm_core_xor.v", andn = "rm/rm_core_andn.v" }}
"""
