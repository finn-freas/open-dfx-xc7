import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse
import partial_passes
import region

CONFIG = {
    "tile_types": r"^DSP_[LR]$",
    "block": "CLB_IO_CLK",
    "summarise": r"\.(MASK|PATTERN)\[\d+\]$",
    "ignore_minors": [24, 25],
    "tieoff": r"\.DSP_(GND|VCC)_[LR]$",
}

_db = {}


def segbits(tile_type):
    if tile_type not in _db:
        feats = {}
        for line in (bitparse.DB / f"segbits_{tile_type.lower()}.db").read_text().splitlines():
            name, *bits = line.split()
            pos = [tuple(int(x) for x in b.split("_")) for b in bits if not b.startswith("!")]
            neg = [tuple(int(x) for x in b[1:].split("_")) for b in bits if b.startswith("!")]
            feats[name.split(".", 1)[1]] = (pos, neg)
        _db[tile_type] = feats
    return _db[tile_type]


def tile_bits(frames, b):
    base, off = int(b["baseaddr"], 16), b["offset"]
    out = set()
    for m in range(b["frames"]):
        fr = frames.get(base + m)
        if fr is None:
            continue
        for w in range(b["words"]):
            v = fr[off + w]
            for k in range(32):
                if v >> k & 1:
                    out.add((m, w * 32 + k))
    return out


def features(bits, tile_type):
    return {f for f, (pos, neg) in segbits(tile_type).items()
            if pos and all(p in bits for p in pos) and not any(n in bits for n in neg)}


def bit_names(tile_type):
    names = {}
    for f, (pos, neg) in segbits(tile_type).items():
        for p in pos + neg:
            names.setdefault(p, []).append(f)
    return names


def passes(partial, part):
    bl = partial_passes.bursts(partial, part)
    by_start = {}
    for b in bl:
        by_start.setdefault(b["start"], []).append(b)
    out = [{}, {}]
    for start, group in by_start.items():
        for k, b in enumerate(group[:2]):
            for far, data in b["frames"][:-1]:
                out[k][far] = data
    return out


def analyse(partial, full, spec, part, grid):
    final = bitparse.parse(full, part)["frames"]
    p1, p2 = passes(partial, part)
    tiles = region.region_tiles(grid, spec)
    rep = []
    for name in sorted(tiles):
        t = grid[name]
        if not re.match(CONFIG["tile_types"], t["type"]):
            continue
        b = t["bits"][CONFIG["block"]]
        b1, b2, bf = tile_bits({**final, **p1}, b), tile_bits({**final, **p2}, b), tile_bits(final, b)
        f1, ff = features(b1, t["type"]), features(bf, t["type"])
        names = bit_names(t["type"])
        diff = sorted((m, k) for m, k in b1 ^ bf if m not in CONFIG["ignore_minors"])
        named = [(m, k) for m, k in diff if (m, k) in names]
        rep.append({
            "tile": name,
            "pass2_equals_final": b2 == bf,
            "final_features": sorted(f for f in ff if not re.search(CONFIG["summarise"], f)),
            "final_mask_pattern_bits": sum(1 for f in ff if re.search(CONFIG["summarise"], f)),
            "held_back": sorted(ff - f1),
            "pass1_only": sorted(f1 - ff),
            "named_bits_final_not_pass1": [f"{m}_{k}" for m, k in named if (m, k) in bf],
            "named_bits_pass1_not_final": [f"{m}_{k}" for m, k in named if (m, k) in b1],
            "unnamed_bits_differ": len(diff) - len(named),
            "bit_features": {f"{m}_{k}": names[(m, k)] for m, k in named},
        })
    return rep


def main():
    ap = argparse.ArgumentParser(description="Per DSP tile of the region: config features and bits in the final "
                                             "bitstream versus pass 1 (first burst) of an uncompressed partial")
    ap.add_argument("partial")
    ap.add_argument("full")
    ap.add_argument("region")
    ap.add_argument("--json")
    a = ap.parse_args()
    part = bitparse.Part()
    grid = region.load_grid()
    rep = analyse(a.partial, a.full, a.region, part, grid)
    for r in rep:
        used = [f for f in r["final_features"] if f.startswith("DSP48.")]
        if not used and not r["held_back"] and not r["named_bits_final_not_pass1"] and not r["named_bits_pass1_not_final"]:
            continue
        print(f"{r['tile']}: pass2==final {r['pass2_equals_final']}")
        print(f"  final: {' '.join(f.replace('DSP48.', '') for f in used)} (+{r['final_mask_pattern_bits']} MASK/PATTERN)")
        held = [f for f in r["held_back"] if not re.search(CONFIG["tieoff"], f)]
        print(f"  held back in pass 1: {' '.join(held) or '-'} (+{len(r['held_back']) - len(held)} tie-off pips)")
        print(f"  pass 1 only: {' '.join(r['pass1_only']) or '-'}")
        tie = {b for b, fs in r["bit_features"].items() if all(re.search(CONFIG["tieoff"], f) for f in fs)}
        print(f"  named bits final-only: {[b for b in r['named_bits_final_not_pass1'] if b not in tie]} "
              f"pass1-only: {[b for b in r['named_bits_pass1_not_final'] if b not in tie]} "
              f"(+{len(tie)} tie-off bits; {r['unnamed_bits_differ']} unnamed bits differ, minors 24/25 ignored)")
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
