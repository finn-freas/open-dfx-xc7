import argparse
import contextlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bit2fasm
import bitparse
import partial_passes

CONFIG = {
    "pass": 0,
}


def bits_lines(frames):
    out = []
    for far, data in sorted(frames.items()):
        for w, v in enumerate(data):
            if w == bitparse.ECC_WORD:
                v &= ~bitparse.ECC_MASK & 0xFFFFFFFF
            b = 0
            while v:
                if v & 1:
                    out.append(f"bit_{far:08x}_{w:03d}_{b:02d}")
                v >>= 1
                b += 1
    return out


def main():
    ap = argparse.ArgumentParser(description="Decode one pass of a partial: the full bitstream with that pass's frames "
                                             "put in, through prjxray-db, to FASM (run with the openXC7 python, tabbypy3)")
    ap.add_argument("partial")
    ap.add_argument("full")
    ap.add_argument("out")
    ap.add_argument("--pass", dest="pass_", type=int, default=CONFIG["pass"], help="0 for the first pass")
    a = ap.parse_args()
    part = bitparse.Part()
    frames = dict(bitparse.parse(a.full, part)["frames"])
    bursts = partial_passes.bursts(a.partial, part)
    runs = {}
    for b in bursts:
        runs.setdefault(b["start"], []).append(b)
    for start, bl in runs.items():
        for far, data in bl[a.pass_]["frames"][:-1]:
            frames[far] = data
    with tempfile.NamedTemporaryFile("w", suffix=".bits") as f:
        f.write("\n".join(bits_lines(frames)) + "\n")
        f.flush()
        mod = bit2fasm.load_bit2fasm()
        with open(a.out, "w") as o, contextlib.redirect_stdout(o):
            mod.bits_to_fasm(str(bit2fasm.DB), bit2fasm.CONFIG["part"], f.name, False, False)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
