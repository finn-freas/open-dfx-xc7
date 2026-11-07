import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse
import partial_passes

CONFIG = {
    "max_listed": 10,
}


def packets(path):
    words = bitparse.read_bit(path)["words"]
    return words


def main():
    ap = argparse.ArgumentParser(description="Compare two partial bitstreams: packet words after sync, then each FDRI burst "
                                             "frame by frame (ECC word included)")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--json")
    a = ap.parse_args()
    part = bitparse.Part()
    wa, wb = packets(a.a), packets(a.b)
    diff_words = [i for i in range(min(len(wa), len(wb))) if wa[i] != wb[i]]
    ba, bb = partial_passes.bursts(a.a, part), partial_passes.bursts(a.b, part)
    rep = {"a": a.a, "b": a.b, "words_a": len(wa), "words_b": len(wb), "words_differ": len(diff_words),
           "bursts_a": len(ba), "bursts_b": len(bb), "bursts": []}
    for k, (x, y) in enumerate(zip(ba, bb)):
        fx, fy = x["frames"], y["frames"]
        frames = []
        nw = 0
        for (f1, d1), (f2, d2) in zip(fx, fy):
            w = [i for i in range(len(d1)) if d1[i] != d2[i]]
            if w or f1 != f2:
                frames.append({"far": bitparse.far_str(f1), "far_b": bitparse.far_str(f2), "words": w})
                nw += len(w)
        rep["bursts"].append({"index": k, "start_a": bitparse.far_str(x["start"]), "start_b": bitparse.far_str(y["start"]),
                              "frames_a": len(fx), "frames_b": len(fy), "frames_differ": len(frames), "words_differ": nw,
                              "differing": frames})
    print(f"{a.a} vs {a.b}: {rep['words_a']} vs {rep['words_b']} words after sync, {rep['words_differ']} differ; "
          f"bursts {rep['bursts_a']} vs {rep['bursts_b']}")
    for b in rep["bursts"]:
        print(f"  burst {b['index']}: {b['start_a']} / {b['start_b']}, {b['frames_a']}/{b['frames_b']} frames, "
              f"{b['frames_differ']} frames and {b['words_differ']} words differ")
        for f in b["differing"][:CONFIG["max_listed"]]:
            print(f"      {f['far']} words {f['words'][:12]}")
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
