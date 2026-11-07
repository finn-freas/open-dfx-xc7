import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse

CONFIG = {
    "words_per_frame": 101,
    "max_listed": 12,
}


def bursts(path, part):
    words = bitparse.read_bit(path)["words"]
    out = []
    far = None
    last_reg = None
    i = 0
    while i < len(words):
        w = words[i]
        t = w >> 29
        if t == 1:
            op, reg, cnt = (w >> 27) & 3, (w >> 13) & 0x1F, w & 0x7FF
            if op == 2 and cnt and reg == 1:
                far = words[i + cnt]
            if op == 2 and cnt and reg == 2:
                out.append((far, words[i + 1:i + 1 + cnt]))
            if op:
                last_reg = reg
            i += 1 + cnt
        elif t == 2:
            cnt = w & 0x7FFFFFF
            if last_reg == 2:
                out.append((far, words[i + 1:i + 1 + cnt]))
            i += 1 + cnt
        else:
            i += 1
    res = []
    n = CONFIG["words_per_frame"]
    for start, data in out:
        frames = []
        f = start
        for k in range(0, len(data) - len(data) % n, n):
            frames.append((f, data[k:k + n]))
            nxt, _ = part.next_far(f)
            f = nxt
        res.append({"start": start, "frames": frames})
    return res


def describe(path, part, full=None):
    bs = bursts(path, part)
    ref = bitparse.parse(full, part)["frames"] if full else None
    zero = [0] * CONFIG["words_per_frame"]
    runs = {}
    for b in bs:
        runs.setdefault(b["start"], []).append(b)
    rep = {"file": str(path), "bursts": []}
    for idx, b in enumerate(bs):
        fr = b["frames"]
        body, pad = fr[:-1], fr[-1]
        ones = sorted({bitparse.far_str(f) for f, d in body
                       if sum(1 for i, w in enumerate(d) if w == 0xFFFFFFFF and i != bitparse.ECC_WORD) >= 50})
        ent = {"index": idx, "start": bitparse.far_str(b["start"]), "frames": len(fr), "pad": bitparse.far_str(pad[0]),
               "pad_nonzero_words": sum(1 for w in bitparse.without_ecc(pad[1]) if w),
               "nonzero_frames": sum(1 for _, d in body if any(bitparse.without_ecc(d))),
               "frames_mostly_ones": ones}
        if ref is not None:
            ent["frames_differ_from_full"] = [bitparse.far_str(f) for f, d in body
                                              if bitparse.without_ecc(d) != bitparse.without_ecc(ref.get(f, zero))]
            ent["pad_equals_full"] = bitparse.without_ecc(pad[1]) == bitparse.without_ecc(ref.get(pad[0], zero))
        rep["bursts"].append(ent)
    pairs = []
    for start, bl in runs.items():
        if len(bl) == 2:
            a, c = bl
            diff = [bitparse.far_str(f) for (f, d1), (_, d2) in zip(a["frames"][:-1], c["frames"][:-1])
                    if bitparse.without_ecc(d1) != bitparse.without_ecc(d2)]
            pairs.append({"run": bitparse.far_str(start), "pass1_vs_pass2_frames_differ": diff})
    rep["passes"] = pairs
    return rep


def main():
    ap = argparse.ArgumentParser(description="Per-burst view of a partial bitstream: runs, pad frames, pass 1 vs pass 2, "
                                             "and each burst against a full bitstream")
    ap.add_argument("partial")
    ap.add_argument("--full", help="full bitstream of the same configuration")
    ap.add_argument("--json")
    a = ap.parse_args()
    part = bitparse.Part()
    rep = describe(a.partial, part, a.full)
    m = CONFIG["max_listed"]
    print(rep["file"])
    for b in rep["bursts"]:
        line = (f"  burst {b['index']}: start {b['start']}, {b['frames']} frames incl. pad {b['pad']} "
                f"(pad non-zero words {b['pad_nonzero_words']}), non-zero frames {b['nonzero_frames']}, "
                f"mostly-ones frames {len(b['frames_mostly_ones'])}")
        if "frames_differ_from_full" in b:
            line += f", frames differing from full {len(b['frames_differ_from_full'])}, pad equals full {b['pad_equals_full']}"
        print(line)
        for f in b["frames_mostly_ones"][:m]:
            print(f"      ones {f}")
        for f in b.get("frames_differ_from_full", [])[:m]:
            print(f"      differs {f}")
    for p in rep["passes"]:
        print(f"  run {p['run']}: pass 1 vs pass 2 differ in {len(p['pass1_vs_pass2_frames_differ'])} frames "
              f"{p['pass1_vs_pass2_frames_differ'][:m]}")
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
