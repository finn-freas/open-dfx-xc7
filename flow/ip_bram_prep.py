"""Write the .coe init files and the test tops for the ofx ip bram vs Vivado blk_mem_gen comparison.

The same top (designs/ip/bram/<name>_top.v) instantiates <name>_mem, which is Vivado's blk_mem_gen in the
Vivado build and `ofx ip bram` output in the open build (same module name and ports).
"""
import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "configs": ROOT / "designs" / "ip" / "bram_configs.txt",
    "out": ROOT / "designs" / "ip" / "bram",
    "seed": 7,
    "pins": {"clk": "E3", "sw": "A8", "led": "H5"},
    "period_ns": 10.0,
    "dry_run": True,
}


def read_cfg(path):
    out = {}
    for ln in Path(path).read_text().splitlines():
        ln = ln.split("#")[0].strip()
        if not ln:
            continue
        name, *kv = ln.split()
        out[name] = dict(x.split("=", 1) for x in kv)
    return out


def geom(p):
    w = int(p["Write_Width_A"])
    d = int(p["Write_Depth_A"])
    return w, d, max(1, (d - 1).bit_length())


def coe(name, p):
    w, d, _ = geom(p)
    rnd = random.Random(f"{CONFIG['seed']}:{name}")
    digits = (w + 3) // 4
    vals = [rnd.getrandbits(w) for _ in range(d)]
    body = ",\n".join(f"{v:0{digits}x}" for v in vals)
    return f"memory_initialization_radix=16;\nmemory_initialization_vector=\n{body};\n"


def top(name, p):
    w, d, aw = geom(p)
    t = p["Memory_Type"]
    din = f"{{{(w + aw - 1) // aw}{{a}}}}"
    L = [f"module {name}_top (input wire clk, input wire sw, output wire led);",
         f"    reg [{aw - 1}:0] a = 0;",
         "    always @(posedge clk) a <= a + 1'b1;",
         f"    wire [{(w + aw - 1) // aw * aw - 1}:0] wd = {din};"]
    if t == "Single_Port_RAM":
        L += [f"    wire [{w - 1}:0] qa;",
              f"    {name}_mem u_mem (.clka(clk), .wea(sw), .addra(a), .dina(wd[{w - 1}:0]), .douta(qa));",
              "    wire x = ^qa;"]
    elif t == "Single_Port_ROM":
        L += [f"    wire [{w - 1}:0] qa;", f"    {name}_mem u_mem (.clka(clk), .addra(a), .douta(qa));", "    wire x = ^qa;"]
    elif t == "True_Dual_Port_RAM":
        L += [f"    wire [{w - 1}:0] qa, qb;",
              f"    {name}_mem u_mem (.clka(clk), .wea(sw), .addra(a), .dina(wd[{w - 1}:0]), .douta(qa),",
              f"                      .clkb(clk), .web(~sw), .addrb(~a), .dinb(~wd[{w - 1}:0]), .doutb(qb));",
              "    wire x = ^qa ^ ^qb;"]
    elif t == "Simple_Dual_Port_RAM":
        L += [f"    wire [{w - 1}:0] qb;",
              f"    {name}_mem u_mem (.clka(clk), .wea(sw), .addra(a), .dina(wd[{w - 1}:0]),",
              "                      .clkb(clk), .addrb(~a), .doutb(qb));",
              "    wire x = ^qb;"]
    else:
        raise ValueError(t)
    L += ["    reg r = 1'b0;", "    always @(posedge clk) r <= x;", "    assign led = r;", "endmodule", ""]
    return "\n".join(L)


def xdc():
    pins = CONFIG["pins"]
    return "".join(f"set_property -dict {{PACKAGE_PIN {pins[k]} IOSTANDARD LVCMOS33}} [get_ports {k}]\n" for k in pins) + \
        f"create_clock -name clk -period {CONFIG['period_ns']:.3f} [get_ports clk]\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    cfg = read_cfg(CONFIG["configs"])
    files = {CONFIG["out"] / "top.xdc": xdc()}
    for name, p in cfg.items():
        files[CONFIG["out"] / f"{name}.coe"] = coe(name, p)
        files[CONFIG["out"] / f"{name}_top.v"] = top(name, p)
    for f, text in files.items():
        print(f"[{'dry' if dry else 'run'}] write {f.relative_to(ROOT)} ({len(text)} bytes)")
        if not dry:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)


if __name__ == "__main__":
    sys.exit(main())
