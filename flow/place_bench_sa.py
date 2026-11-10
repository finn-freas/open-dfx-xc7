"""flow/place_bench.py with the variants of the SA refinement study (docs/wip/placement-sa.md): the binary
build/nextpnr-build/sa (place_v17 source + docs/drafts/nextpnr-placer-sa-refine.patch) and its variants are
registered here, so place_bench.py itself is not touched. Same command line as place_bench.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import place_bench as pb

TMG = pb.TMG
TU = ["--placer-static-target-util", "1.0"]
SA1 = "t0=0.01:quant=0.002:exp=8:rmin=3:pcent=0.6"

BINARIES = {"sa": "build/nextpnr-build/sa/nextpnr-himbaechel", "sa_v1": "build/nextpnr-build/sa_v1/nextpnr-himbaechel",
            "sa_v2": "build/nextpnr-build/sa_v2/nextpnr-himbaechel",
            "sa_v3": "build/nextpnr-build/sa_v3/nextpnr-himbaechel",
            "sa_v4": "build/nextpnr-build/sa_v4/nextpnr-himbaechel"}
VARIANTS = {
    "sa_off_stub": {"bin": "sa_v1", "args": TMG},
    "sa_off_tu_stub": {"bin": "sa_v1", "args": TMG + TU},
    "sa1_stub": {"bin": "sa_v1", "args": TMG + ["-o", "sa-refine=" + SA1]},
    "sa1_tu_stub": {"bin": "sa_v1", "args": TMG + TU + ["-o", "sa-refine=" + SA1]},
    "sa1_dq": {"bin": "sa_v1", "args": TMG + ["-o", "sa-refine=" + SA1], "dspq": True},
    "sa1_tu_dq": {"bin": "sa_v1", "args": TMG + TU + ["-o", "sa-refine=" + SA1], "dspq": True},
    "sa2_tu_stub": {"bin": "sa_v2", "args": TMG + TU + ["-o", "sa-refine=" + SA1]},
    "sa2_tu_dq": {"bin": "sa_v2", "args": TMG + TU + ["-o", "sa-refine=" + SA1], "dspq": True},
    "sa3_tu_stub": {"bin": "sa_v3", "args": TMG + TU + ["-o", "sa-refine=" + SA1]},
    "sa3_tu_dq": {"bin": "sa_v3", "args": TMG + TU + ["-o", "sa-refine=" + SA1], "dspq": True},
    "sa3_stub": {"bin": "sa_v3", "args": TMG + ["-o", "sa-refine=" + SA1]},
    "sa3_dq": {"bin": "sa_v3", "args": TMG + ["-o", "sa-refine=" + SA1], "dspq": True},
    "sa4_tu_stub": {"bin": "sa_v4", "args": TMG + TU + ["-o", "sa-refine=" + SA1 + ":site=750:tile=850"]},
    "sa4_tu_dq": {"bin": "sa_v4", "args": TMG + TU + ["-o", "sa-refine=" + SA1 + ":site=750:tile=850"], "dspq": True},
    "sa5_tu_stub": {"bin": "sa_v4", "args": TMG + TU + ["-o", "sa-refine=" + SA1 + ":site=750:tile=950"]},
}

pb.CONFIG["binaries"].update(BINARIES)
pb.CONFIG["variants"].update(VARIANTS)

if __name__ == "__main__":
    pb.main()
