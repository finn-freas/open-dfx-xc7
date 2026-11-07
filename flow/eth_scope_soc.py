import os
import sys

from migen import Signal

import litex_boards.targets.digilent_arty as arty
from litescope import LiteScopeAnalyzer

CONFIG = {
    "depth": 1024,
    "clock_domain": "eth_rx",
    "samplerate": 25e6,
    "csv_name": "analyzer.csv",
    "rx_pads": ["rx_dv", "rx_er", "rx_data", "crs", "col"],
}


def output_dir(argv):
    for i, a in enumerate(argv):
        if a == "--output-dir" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--output-dir="):
            return a.split("=", 1)[1]
    return "build"


class ScopeSoC(arty.BaseSoC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pads = self.platform.lookup_request("eth")
        src = self.ethphy.source
        frame_count = Signal(8)
        self.sync.eth_rx += frame_count.eq(frame_count + (src.valid & src.last))
        signals = [getattr(pads, n) for n in CONFIG["rx_pads"]] + [src.valid, src.last, src.data, frame_count]
        csv = os.path.join(os.path.abspath(output_dir(sys.argv)), CONFIG["csv_name"])
        os.makedirs(os.path.dirname(csv), exist_ok=True)
        self.analyzer = LiteScopeAnalyzer(signals,
            depth        = CONFIG["depth"],
            clock_domain = CONFIG["clock_domain"],
            samplerate   = CONFIG["samplerate"],
            csr_csv      = csv)


if __name__ == "__main__":
    arty.BaseSoC = ScopeSoC
    arty.main()
