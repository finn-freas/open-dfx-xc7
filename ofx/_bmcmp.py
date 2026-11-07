import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "flow"))
import bitparse


def main():
    applied, target, base = sys.argv[1:4]
    p = bitparse.Part()
    a = bitparse.parse(applied, p)["frames"]
    t = bitparse.parse(target, p)["frames"]
    b = bitparse.parse(base, p)["frames"]
    z = [0] * bitparse.CONFIG["words_per_frame"]
    fill = [k for k in b if k not in a]
    if any(bitparse.without_ecc(b[k]) != bitparse.without_ecc(t.get(k, z)) for k in fill):
        print("filled-frame-mismatch")
        sys.exit(1)
    a = {**{k: b[k] for k in fill}, **a}
    d = sum(bitparse.without_ecc(a.get(x, z)) != bitparse.without_ecc(t.get(x, z)) for x in set(a) | set(t))
    print(f"{d} frames differ from the original target ({len(fill)} frames byteman omits kept from the base)")
    sys.exit(1 if d else 0)


if __name__ == "__main__":
    main()
