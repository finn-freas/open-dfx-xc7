import argparse
import json
import os

from migen import ClockDomain, Signal

from litex.build.generic_platform import IOStandard, Pins, Subsignal
from litex.build.xilinx.platform import XilinxPlatform
from litex.soc.integration.builder import Builder
from litex.soc.integration.soc_core import SoCMini
from litescope import LiteScopeAnalyzer

CONFIG = {
    "device": "xc7a35tcsg324-1",
    "name": "scope_core",
    "bridges": ("uart", "jtag"),
    "baudrate": 115200,
}


def ios(probe_width, bridge):
    io = [("dbg_clk", 0, Pins(1)), ("dbg_probe", 0, Pins(probe_width))]
    if bridge == "uart":
        io.append(("dbg_serial", 0, Subsignal("tx", Pins(1)), Subsignal("rx", Pins(1)), IOStandard("LVCMOS33")))
    return io


class ScopeCore(SoCMini):
    def __init__(self, platform, spec):
        self.cd_sys = ClockDomain()
        self.comb += self.cd_sys.clk.eq(platform.request("dbg_clk"))
        SoCMini.__init__(self, platform, clk_freq=spec["clk_freq"], ident="open-dfx-xc7 MARK_DEBUG scope")
        if spec["bridge"] == "uart":
            self.add_uartbone(name="uartbone", uart_name="dbg_serial", baudrate=spec.get("baudrate", CONFIG["baudrate"]))
        else:
            self.add_jtagbone(chain=spec.get("jtag_chain", 1))
        probe = platform.request("dbg_probe")
        signals, pos = [], 0
        for name, width in spec["probes"]:
            s = Signal(width, name=name)
            self.comb += s.eq(probe[pos:pos + width])
            signals.append(s)
            pos += width
        self.analyzer = LiteScopeAnalyzer(signals,
            depth        = spec["depth"],
            clock_domain = "sys",
            samplerate   = spec["clk_freq"],
            csr_csv      = os.path.join(spec["out_dir"], "analyzer.csv"))


def main():
    ap = argparse.ArgumentParser(description="Standalone LiteScope analyzer core (UARTBone or JTAGBone bridge) "
                                             "with one probe bus, for netlist-level MARK_DEBUG insertion")
    ap.add_argument("spec", help="JSON: probes [[name, width]], depth, clk_freq, bridge, out_dir")
    a = ap.parse_args()
    spec = json.loads(open(a.spec).read())
    assert spec["bridge"] in CONFIG["bridges"]
    os.makedirs(spec["out_dir"], exist_ok=True)
    width = sum(w for _, w in spec["probes"])
    platform = XilinxPlatform(CONFIG["device"], io=ios(width, spec["bridge"]), toolchain="vivado")
    soc = ScopeCore(platform, spec)
    builder = Builder(soc, output_dir=spec["out_dir"], gateware_dir=spec["out_dir"], compile_software=False,
                      compile_gateware=False, csr_csv=os.path.join(spec["out_dir"], "csr.csv"))
    builder.build(build_name=CONFIG["name"], run=False)


if __name__ == "__main__":
    main()
