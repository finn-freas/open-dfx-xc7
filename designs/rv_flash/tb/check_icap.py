import argparse
import hashlib
import struct
import sys


def unswap(w):
    out = 0
    for i in range(4):
        b = (w >> (8 * i)) & 0xFF
        out |= int(f"{b:08b}"[::-1], 2) << (8 * i)
    return out


def main():
    ap = argparse.ArgumentParser(description="Check that words captured on ICAPE2.I are the per-byte bit-swapped partial")
    ap.add_argument("captured_hex")
    ap.add_argument("partial_bin")
    a = ap.parse_args()
    cap = [int(x, 16) for x in open(a.captured_hex).read().split()]
    data = open(a.partial_bin, "rb").read()
    back = b"".join(struct.pack(">I", unswap(w)) for w in cap)
    same = back == data
    print(f"captured {len(cap)} words, partial {len(data) // 4} words; "
          f"sha256 captured-unswapped {hashlib.sha256(back).hexdigest()[:16]} partial {hashlib.sha256(data).hexdigest()[:16]}; "
          f"{'IDENTICAL' if same else 'DIFFERENT'}")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
