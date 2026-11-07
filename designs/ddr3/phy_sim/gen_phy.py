import json
import sys
from pathlib import Path

from migen import *
from migen.fhdl.verilog import convert

from litex.build.generic_platform import Pins, Subsignal
from litedram.phy import s7ddrphy

CONFIG = {
    "out": Path(__file__).resolve().parent / "phy_top.v",
    "settings": Path(__file__).resolve().parent / "phy_settings.json",
    "sys_clk_freq": 100e6,
    "addressbits": 14,
    "bankbits": 3,
    "databits": 16,
    "strobes": 2,
}


class Pads:
    def __init__(self):
        c = CONFIG
        self.a = Signal(c["addressbits"], name="ddram_a")
        self.ba = Signal(c["bankbits"], name="ddram_ba")
        self.ras_n = Signal(name="ddram_ras_n")
        self.cas_n = Signal(name="ddram_cas_n")
        self.we_n = Signal(name="ddram_we_n")
        self.cs_n = Signal(name="ddram_cs_n")
        self.dm = Signal(c["strobes"], name="ddram_dm")
        self.dq = Signal(c["databits"], name="ddram_dq")
        self.dqs_p = Signal(c["strobes"], name="ddram_dqs_p")
        self.dqs_n = Signal(c["strobes"], name="ddram_dqs_n")
        self.clk_p = Signal(name="ddram_clk_p")
        self.clk_n = Signal(name="ddram_clk_n")
        self.cke = Signal(name="ddram_cke")
        self.odt = Signal(name="ddram_odt")
        self.reset_n = Signal(name="ddram_reset_n")


class PHYTop(Module):
    def __init__(self):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_idelay = ClockDomain()
        self.pads = pads = Pads()
        self.submodules.phy = phy = s7ddrphy.A7DDRPHY(pads, memtype="DDR3", nphases=4,
                                                       sys_clk_freq=CONFIG["sys_clk_freq"])
        self.specials += Instance("IDELAYCTRL", i_REFCLK=ClockSignal("idelay"), i_RST=ResetSignal("idelay"))
        self.ios = {self.cd_sys.clk, self.cd_sys.rst, self.cd_sys4x.clk, self.cd_sys4x_dqs.clk,
                    self.cd_idelay.clk, self.cd_idelay.rst}
        self.ios |= {getattr(pads, n) for n in vars(pads)}
        ctl = {}
        for n in ("dly_sel",):
            s = Signal(len(getattr(phy, "_" + n).storage), name=n)
            self.comb += getattr(phy, "_" + n).storage.eq(s)
            ctl[n] = s
        for n in ("rst", "wlevel_en"):
            self.comb += getattr(phy, "_" + n).storage.eq(0)
        for n in ("rdly_dq_rst", "rdly_dq_inc", "rdly_dq_bitslip_rst", "rdly_dq_bitslip", "wlevel_strobe",
                  "wdly_dq_bitslip_rst", "wdly_dq_bitslip"):
            s = Signal(name=n)
            self.comb += getattr(phy, "_" + n).wr_stb.eq(s)
            ctl[n] = s
        self.comb += [phy._rdphase.storage.eq(phy._rdphase.storage.reset),
                      phy._wrphase.storage.eq(phy._wrphase.storage.reset),
                      phy._half_sys8x_taps.storage.eq(phy._half_sys8x_taps.storage.reset)]
        self.ios |= set(ctl.values())
        for i, p in enumerate(phy.dfi.phases):
            for name, width, _ in p.layout:
                s = Signal(width, name=f"dfi_p{i}_{name}", reset=getattr(p, name).reset)
                if name in ("rddata", "rddata_valid"):
                    self.comb += s.eq(getattr(p, name))
                else:
                    self.comb += getattr(p, name).eq(s)
                self.ios.add(s)


def main():
    top = PHYTop()
    out = convert(top, ios=top.ios, name="phy_top")
    CONFIG["out"].write_text(str(out))
    st = top.phy.settings
    keys = ("cl", "cwl", "read_latency", "write_latency", "nphases", "databits", "dfi_databits", "delays", "bitslips")
    rec = {k: getattr(st, k) for k in keys}
    rec["rdphase"] = top.phy._rdphase.storage.reset.value
    rec["wrphase"] = top.phy._wrphase.storage.reset.value
    CONFIG["settings"].write_text(json.dumps(rec, indent=1) + "\n")
    print(rec)


if __name__ == "__main__":
    main()
