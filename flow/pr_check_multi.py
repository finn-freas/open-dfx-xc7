import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse
import pr_check
import region

CONFIG = {
    "max_listed": 10,
}


def main():
    ap = argparse.ArgumentParser(description="Compare full bitstreams of a design with several reconfigurable partitions: "
                                             "between two configurations, frames may differ only in the partitions whose "
                                             "module differs; every other partition's frames and every static frame must "
                                             "be identical (ECC masked)")
    ap.add_argument("--rp", nargs=2, action="append", required=True, metavar=("NAME", "REGION"))
    ap.add_argument("--cfg", nargs=3, action="append", required=True, metavar=("NAME", "RMS", "BIT"),
                    help="RMS: one module name per --rp, comma-separated, in --rp order")
    ap.add_argument("--json")
    a = ap.parse_args()
    part = bitparse.Part()
    grid = region.load_grid()
    rps = [(n, spec, region.region_bits(region.region_tiles(grid, spec))) for n, spec in a.rp]
    for i in range(len(rps)):
        for j in range(i + 1, len(rps)):
            common = set(rps[i][2]) & set(rps[j][2])
            if common:
                sys.exit(f"{rps[i][0]} and {rps[j][0]} share {len(common)} frame(s)")
    owner = {f: k for k, (_, _, fr) in enumerate(rps) for f in fr}
    cfgs = []
    for name, rms, bit in a.cfg:
        rms = rms.split(",")
        if len(rms) != len(rps):
            sys.exit(f"{name}: {len(rms)} module(s) for {len(rps)} partition(s)")
        frames = bitparse.parse(bit, part)["frames"]
        bad = [k for k, v in frames.items() if any(v) and (v[bitparse.ECC_WORD] & bitparse.ECC_MASK) != bitparse.frame_ecc(v)]
        print(f"{name} ({','.join(rms)}): {bit}; ecc mismatches {len(bad)}")
        cfgs.append((name, rms, frames, len(bad)))
    results = []
    fails = 0
    for i in range(len(cfgs)):
        for j in range(i + 1, len(cfgs)):
            na, ra, fa, ea = cfgs[i]
            nb, rb, fb, eb = cfgs[j]
            changed = [k for k in range(len(rps)) if ra[k] != rb[k]]
            d = pr_check.frame_diff(fa, fb)
            per_rp = [0] * len(rps)
            static = []
            locked = []
            foreign = []
            for f, words in d.items():
                k = owner.get(f)
                if k is None:
                    static.append(f)
                    continue
                per_rp[k] += 1
                if k not in changed:
                    locked.append(f)
                    continue
                extra = [w for w in words if w not in rps[k][2][f]]
                if extra:
                    foreign.append((f, extra))
            ok = not static and not locked and not foreign and not ea and not eb
            fails += not ok
            label = "+".join(rps[k][0] for k in changed) or "none"
            print(f"{'PASS' if ok else 'FAIL'} {na} vs {nb}: changed {label}; frames differing {len(d)}: "
                  + ", ".join(f"{rps[k][0]} {per_rp[k]}" for k in range(len(rps)))
                  + f", static {len(static)}; in unchanged partitions {len(locked)}; foreign words {len(foreign)}")
            for f in static[:CONFIG["max_listed"]]:
                print(f"  STATIC {bitparse.far_str(f)} words {d[f][:12]}")
            for f in locked[:CONFIG["max_listed"]]:
                print(f"  LOCKED-RP {rps[owner[f]][0]} {bitparse.far_str(f)} words {d[f][:12]}")
            for f, w in foreign[:CONFIG["max_listed"]]:
                print(f"  FOREIGN-WORDS {bitparse.far_str(f)} words {w[:12]}")
            results.append({"a": na, "b": nb, "rms_a": ra, "rms_b": rb, "changed": [rps[k][0] for k in changed],
                            "differing": len(d), "per_rp": {rps[k][0]: per_rp[k] for k in range(len(rps))},
                            "static": [bitparse.far_str(f) for f in static],
                            "unchanged_rp_frames": [bitparse.far_str(f) for f in locked],
                            "foreign_words": {bitparse.far_str(f): w for f, w in foreign}, "pass": ok})
    print(f"{len(results) - fails}/{len(results)} pairs pass")
    if a.json:
        Path(a.json).write_text(json.dumps({"rps": [{"name": n, "region": s, "frames": len(fr)} for n, s, fr in rps],
                                            "pairs": results}, indent=1))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
