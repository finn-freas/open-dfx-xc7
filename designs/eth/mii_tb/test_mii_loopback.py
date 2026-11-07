import random
import sys
import unittest
import zlib

from migen import *

from litex.gen import LiteXModule
from litex.soc.interconnect import stream

from liteeth.common import eth_phy_description
from liteeth.mac.core import LiteEthMACCore
from liteeth.phy.parallel.mii import LiteEthPHYMIITX, LiteEthPHYMIIRX

CONFIG = {
    "seed": 7,
    "lengths": [60, 61, 64, 100, 257, 1514],
    "clocks": {"sys": 10, "eth_tx": 40, "eth_rx": 40},
    "timeout_cycles": 200000,
}


class MIIPads:
    def __init__(self):
        self.tx_en = Signal()
        self.tx_data = Signal(4)
        self.rx_dv = Signal()
        self.rx_er = Signal()
        self.rx_data = Signal(4)


class LoopPHY(LiteXModule):
    dw = 8
    tx_clk_freq = 25e6
    rx_clk_freq = 25e6

    def __init__(self, pads):
        self.tx = ClockDomainsRenamer("eth_tx")(LiteEthPHYMIITX(pads))
        self.rx = ClockDomainsRenamer("eth_rx")(LiteEthPHYMIIRX(pads))
        self.sink, self.source = self.tx.sink, self.rx.source


class DUT(LiteXModule):
    def __init__(self):
        self.pads = pads = MIIPads()
        self.phy = LoopPHY(pads)
        self.core = LiteEthMACCore(phy=self.phy, dw=8, with_preamble_crc=True, with_store_and_forward=False,
                                   sys_clk_freq=100e6)
        self.comb += [pads.rx_dv.eq(pads.tx_en), pads.rx_data.eq(pads.tx_data)]


def frames():
    rng = random.Random(CONFIG["seed"])
    return [[rng.randrange(256) for _ in range(n)] for n in CONFIG["lengths"]]


def tx_gen(dut, fs):
    for f in fs:
        for i, b in enumerate(f):
            yield dut.core.sink.valid.eq(1)
            yield dut.core.sink.data.eq(b)
            yield dut.core.sink.last.eq(i == len(f) - 1)
            yield dut.core.sink.be.eq(1)
            yield
            while not (yield dut.core.sink.ready):
                yield
        yield dut.core.sink.valid.eq(0)
        for _ in range(50):
            yield


def rx_gen(dut, n, got):
    cur = []
    yield dut.core.source.ready.eq(1)
    for _ in range(CONFIG["timeout_cycles"]):
        yield
        if (yield dut.core.source.valid):
            cur.append((yield dut.core.source.data))
            if (yield dut.core.source.last):
                got.append((cur, (yield dut.core.source.error)))
                cur = []
                if len(got) == n:
                    return


@passive
def wire_gen(dut, wire):
    cur = []
    while True:
        yield
        if (yield dut.pads.tx_en):
            cur.append((yield dut.pads.tx_data))
        elif cur:
            wire.append(cur)
            cur = []


def nibbles_to_bytes(ns):
    return [ns[i] | (ns[i + 1] << 4) for i in range(0, len(ns) - 1, 2)]


class TestMIILoopback(unittest.TestCase):
    def test_mac_over_mii_loopback(self):
        dut = DUT()
        fs, got, wire = frames(), [], []
        run_simulation(dut, {"sys": [tx_gen(dut, fs), rx_gen(dut, len(fs), got)], "eth_tx": wire_gen(dut, wire)},
                       clocks=CONFIG["clocks"], vcd_name=sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".vcd") else None)
        self.assertEqual(len(got), len(fs))
        for f, (g, err) in zip(fs, got):
            self.assertEqual(err, 0)
            self.assertEqual(g, f)
        self.assertEqual(len(wire), len(fs))
        for f, w in zip(fs, wire):
            self.assertEqual(w[:16], [5] * 15 + [0xD])
            b = nibbles_to_bytes(w[16:])
            self.assertEqual(b[:-4], f)
            self.assertEqual(bytes(b[-4:]), (zlib.crc32(bytes(f)) & 0xffffffff).to_bytes(4, "little"))
        print(f"frames {len(fs)} lengths {CONFIG['lengths']}: received equal, no error; wire: preamble+SFD "
              f"5x15,D; CRC32 matches zlib for all")


if __name__ == "__main__":
    unittest.main(argv=sys.argv[:1])
