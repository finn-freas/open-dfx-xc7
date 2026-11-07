CONFIG = {
    "out": __import__("os").path.dirname(__import__("os").path.abspath(__file__)),
    "regs": ["AREG", "BREG", "ACASCREG", "BCASCREG", "MREG", "PREG", "CREG", "DREG", "ADREG",
             "INMODEREG", "OPMODEREG", "ALUMODEREG", "CARRYINREG", "CARRYINSELREG"],
    "zero": dict(AREG=0, BREG=0, ACASCREG=0, BCASCREG=0, MREG=0, PREG=0, CREG=0, DREG=0, ADREG=0,
                 INMODEREG=0, OPMODEREG=0, ALUMODEREG=0, CARRYINREG=0, CARRYINSELREG=0),
    "rms": {
        "rm_dspa": [
            ("a0b0", {}),
            ("a1b1", dict(AREG=1, BREG=1, ACASCREG=1, BCASCREG=1)),
            ("a2b2c2", dict(AREG=2, BREG=2, ACASCREG=2, BCASCREG=2)),
            ("a2b2c1", dict(AREG=2, BREG=2, ACASCREG=1, BCASCREG=1)),
            ("m1", dict(MREG=1)),
            ("p1", dict(PREG=1)),
            ("a1b0", dict(AREG=1, ACASCREG=1)),
            ("a0b2", dict(BREG=2, BCASCREG=2)),
            ("other1", dict(CREG=1, DREG=1, ADREG=1, INMODEREG=1, OPMODEREG=1, ALUMODEREG=1, CARRYINREG=1, CARRYINSELREG=1)),
            ("defaults", dict(AREG=1, BREG=1, ACASCREG=1, BCASCREG=1, MREG=1, PREG=1, CREG=1, DREG=1, ADREG=1,
                              INMODEREG=1, OPMODEREG=1, ALUMODEREG=1, CARRYINREG=1, CARRYINSELREG=1)),
            ("a1b1ce", dict(AREG=1, BREG=1, ACASCREG=1, BCASCREG=1, _ce=True)),
            ("casc", "chain2"),
        ],
        "rm_dspb": [
            ("casc3", "chain3"),
            ("a2b1", dict(AREG=2, BREG=1, ACASCREG=2, BCASCREG=1)),
            ("a1b2", dict(AREG=1, BREG=2, ACASCREG=1, BCASCREG=1)),
            ("a0b1m1p1", dict(BREG=1, BCASCREG=1, MREG=1, PREG=1)),
            ("a1b1alu", dict(AREG=1, BREG=1, ACASCREG=1, BCASCREG=1, PREG=1, _nomult=True)),
            ("a1b1clkinv", dict(AREG=1, BREG=1, ACASCREG=1, BCASCREG=1, _clkinv=True)),
            ("a1b1", dict(AREG=1, BREG=1, ACASCREG=1, BCASCREG=1)),
        ],
    },
}


def dsp(name, p, k, ain="DIRECT", bin_="DIRECT", acin="30'd0", bcin="18'd0", pcin="48'd0", zsel="000"):
    q = dict(CONFIG["zero"])
    q.update({x: v for x, v in p.items() if not x.startswith("_")})
    nomult = p.get("_nomult", False)
    opmode = f"7'b{zsel}{'0011' if nomult else '0101'}"
    params = ",\n        ".join(f".{r}({q[r]})" for r in CONFIG["regs"])
    params += f",\n        .A_INPUT(\"{ain}\"), .B_INPUT(\"{bin_}\"), .USE_MULT(\"{'NONE' if nomult else 'MULTIPLY'}\")"
    if p.get("_clkinv"):
        params += ",\n        .IS_CLK_INVERTED(1'b1)"
    ce = lambda s: f"din[{s}]" if p.get("_ce") else "1'b1"
    rot = lambda w, s: "{" + ",".join(f"din[{(i + s) % 16}]" for i in reversed(range(w))) + "}"
    return f"""    wire [29:0] acout_{name}; wire [17:0] bcout_{name}; wire [47:0] pcout_{name}; wire [47:0] p_{name};
    DSP48E1 #(
        {params}
    ) u_{name} (
        .CLK(clk), .A({rot(30, k)}), .B({rot(18, k + 3)}), .C({rot(48, k + 7)}), .D({rot(25, k + 11)}),
        .ACIN({acin}), .BCIN({bcin}), .PCIN({pcin}), .CARRYCASCIN(1'b0), .MULTSIGNIN(1'b0), .CARRYIN(1'b0),
        .OPMODE({opmode}), .ALUMODE(4'b0000), .INMODE(5'b00000), .CARRYINSEL(3'b000),
        .CEA1({ce(1)}), .CEA2({ce(2)}), .CEB1({ce(3)}), .CEB2({ce(4)}), .CEC(1'b1), .CED(1'b1), .CEAD(1'b1), .CEM(1'b1), .CEP(1'b1),
        .CEALUMODE(1'b1), .CECTRL(1'b1), .CECARRYIN(1'b1), .CEINMODE(1'b1),
        .RSTA(1'b0), .RSTB(1'b0), .RSTC(1'b0), .RSTD(1'b0), .RSTM(1'b0), .RSTP(1'b0), .RSTALLCARRYIN(1'b0),
        .RSTALUMODE(1'b0), .RSTCTRL(1'b0), .RSTINMODE(1'b0),
        .ACOUT(acout_{name}), .BCOUT(bcout_{name}), .PCOUT(pcout_{name}), .P(p_{name}),
        .CARRYCASCOUT(), .MULTSIGNOUT(), .CARRYOUT(), .OVERFLOW(), .UNDERFLOW(), .PATTERNDETECT(), .PATTERNBDETECT()
    );
"""


def chain(name, n, k):
    out, names = "", []
    base = dict(AREG=1, BREG=1, ACASCREG=1, BCASCREG=1, PREG=1)
    for i in range(n):
        nm = f"{name}{i}"
        if i == 0:
            out += dsp(nm, base, k + i)
        else:
            prev = names[-1]
            out += dsp(nm, base, k + i, "CASCADE", "CASCADE", f"acout_{prev}", f"bcout_{prev}", f"pcout_{prev}", "001")
        names.append(nm)
    return out, [names[-1]]


def rm(cells):
    body, outs = "", []
    for k, (name, p) in enumerate(cells):
        if isinstance(p, str):
            b, o = chain(name, int(p[-1]), k * 5)
        else:
            b, o = dsp(name, p, k * 5), [name]
        body += b
        outs += o
    x = " ^ ".join(f"p_{o}[15:0] ^ p_{o}[31:16]" for o in outs)
    return ("module rm_slot (input wire clk, input wire [15:0] din, output reg [15:0] dout);\n" + body +
            f"    always @(posedge clk) dout <= {x};\nendmodule\n")


def main():
    import os
    os.makedirs(CONFIG["out"], exist_ok=True)
    for n, cells in CONFIG["rms"].items():
        open(f"{CONFIG['out']}/{n}.v", "w").write(rm(cells))
    open(f"{CONFIG['out']}/rm_nodsp.v", "w").write(
        "module rm_slot (input wire clk, input wire [15:0] din, output reg [15:0] dout);\n"
        "    always @(posedge clk) dout <= {din[6:0], din[15:7]} ^ (din + 16'h1234);\nendmodule\n")


if __name__ == "__main__":
    main()
