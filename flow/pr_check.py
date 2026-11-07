import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse
import region

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "max_listed": 30,
}


def frame_diff(fa, fb):
    keys = set(fa) | set(fb)
    zero = [0] * bitparse.CONFIG["words_per_frame"]
    out = {}
    for k in sorted(keys):
        a, b = bitparse.without_ecc(fa.get(k, zero)), bitparse.without_ecc(fb.get(k, zero))
        if a != b:
            out[k] = [i for i in range(len(a)) if a[i] != b[i]]
    return out


def main():
    ap = argparse.ArgumentParser(description="Compare two full bitstreams: every differing frame must lie in the region")
    ap.add_argument("bit_a")
    ap.add_argument("bit_b")
    ap.add_argument("--region", default=CONFIG["region"])
    ap.add_argument("--json")
    ap.add_argument("--hclk-full-column", action="store_true",
                    help="accept a difference in the HCLK word of a region frame whose other words all belong to the "
                         "region: that HCLK row serves region tiles only (Vivado DFX changes these clock leaf bits "
                         "between modules); reported separately")
    a = ap.parse_args()
    part = bitparse.Part()
    grid = region.load_grid()
    allowed = region.region_bits(region.region_tiles(grid, a.region))
    fa = bitparse.parse(a.bit_a, part)["frames"]
    fb = bitparse.parse(a.bit_b, part)["frames"]
    for name, fr in (("a", fa), ("b", fb)):
        bad = [k for k, v in fr.items() if any(v) and (v[bitparse.ECC_WORD] & bitparse.ECC_MASK) != bitparse.frame_ecc(v)]
        print(f"ecc check {name}: {len(bad)} of {sum(1 for v in fr.values() if any(v))} non-zero frames mismatch")
    d = frame_diff(fa, fb)
    inside = {k: v for k, v in d.items() if k in allowed}
    outside = {k: v for k, v in d.items() if k not in allowed}
    hclk_word = bitparse.CONFIG["words_per_frame"] // 2
    foreign = {k: [w for w in v if w not in allowed[k]] for k, v in inside.items()}
    foreign = {k: v for k, v in foreign.items() if v}
    nwords = bitparse.CONFIG["words_per_frame"]
    hclk_owned = {}
    if a.hclk_full_column:
        hclk_owned = {k: v for k, v in foreign.items()
                      if v == [hclk_word] and set(range(nwords)) - {hclk_word} <= allowed[k]}
        foreign = {k: v for k, v in foreign.items() if k not in hclk_owned}
    print(f"frames differing: {len(d)}; inside region: {len(inside)}; outside region: {len(outside)}")
    print(f"region frames whose differing words belong to tiles outside the region: {len(foreign)}"
          + (f" (word {hclk_word} is the HCLK word)" if foreign else ""))
    if a.hclk_full_column:
        print(f"region frames differing only in the HCLK word of a column the region fills: {len(hclk_owned)}"
              + "".join(f"\n  HCLK-OWNED {bitparse.far_str(k)}" for k in list(hclk_owned)[:CONFIG["max_listed"]]))
    for k, v in list(outside.items())[:CONFIG["max_listed"]]:
        print(f"  OUTSIDE {bitparse.far_str(k)} words {v[:12]}")
    for k, v in list(foreign.items())[:CONFIG["max_listed"]]:
        print(f"  FOREIGN-WORDS {bitparse.far_str(k)} words {v[:12]}")
    if a.json:
        Path(a.json).write_text(json.dumps({
            "a": a.bit_a, "b": a.bit_b, "region": a.region, "differing": len(d),
            "inside": [bitparse.far_str(k) for k in inside], "outside": [bitparse.far_str(k) for k in outside],
            "foreign_words": {bitparse.far_str(k): v for k, v in foreign.items()},
            "hclk_full_column": a.hclk_full_column, "hclk_owned": [bitparse.far_str(k) for k in hclk_owned]}, indent=1))
    ok = not outside and not foreign
    print("STATIC IDENTICAL OUTSIDE REGION" if ok else "STATIC DIFFERS")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
