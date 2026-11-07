import argparse
import sys
from pathlib import Path

CONFIG = {
    "icap_used_bits": ["0040091a_68_30", "0040091a_68_31", "0040091b_68_29"],
}


def main():
    ap = argparse.ArgumentParser(description="Set raw bits (prjxray '<far>_<word>_<bit>' form) in a .frames file")
    ap.add_argument("frames_in")
    ap.add_argument("frames_out")
    ap.add_argument("--bit", action="append", default=[], help="bit to set; default: the ICAP bits seen in Vivado")
    a = ap.parse_args()
    out = Path(a.frames_out)
    if out.exists():
        print(f"[skip] {out} exists")
        return
    bits = a.bit or CONFIG["icap_used_bits"]
    frames = {}
    order = []
    for line in Path(a.frames_in).read_text().splitlines():
        far, data = line.split()
        frames[int(far, 16)] = [int(x, 16) for x in data.split(",")]
        order.append(int(far, 16))
    for b in bits:
        far, word, bit = b.split("_")
        far, word, bit = int(far, 16), int(word), int(bit)
        if far not in frames:
            frames[far] = [0] * 101
            order.append(far)
        frames[far][word] |= 1 << bit
    with open(out, "w") as f:
        for far in sorted(set(order)):
            f.write(f"0x{far:08x} " + ",".join(f"0x{x:08x}" for x in frames[far]) + "\n")
    print(f"wrote {out} with {len(bits)} bit(s) set")


if __name__ == "__main__":
    sys.exit(main())
