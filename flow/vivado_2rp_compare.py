import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse
import region

CONFIG = {
    "designs": {
        "dfx_2rp": {"rp1": "SLICE_X12Y100:SLICE_X15Y149", "rp2": "SLICE_X12Y0:SLICE_X15Y49"},
        "dfx_2rp_shared": {"rp1": "SLICE_X12Y100:SLICE_X15Y124", "rp2": "SLICE_X12Y125:SLICE_X15Y149"},
    },
    "variants": {
        "base": [],
        "rar": ["--reset-after-reconfig"],
        "cmp": ["--compress"],
        "rarcmp": ["--reset-after-reconfig", "--compress"],
    },
    "parity_opts": ["--pass1-hold-hclk", "--pass1-hold-dsp", "--pass1-hold-carry", "--pass1-keep-unknown"],
    "flush": "zero",
    "tabby": "toolchain/openxc7/libexec/tabbypy3",
    "vivado_dir": "build/vivado/{design}",
    "out_dir": "build/phase12/compare/{design}",
    "dry_run": True,
}

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, log=None, dry=False):
    if dry:
        print("[dry]", " ".join(str(c) for c in cmd))
        return 0
    with open(log, "w") if log else open("/dev/null", "w") as f:
        return subprocess.run([str(c) for c in cmd], stdout=f, stderr=subprocess.STDOUT, cwd=ROOT).returncode


def configs(vdir):
    out = []
    for p in sorted(vdir.glob("cfg_*.bit")):
        if "_partial" in p.name:
            continue
        m = re.fullmatch(r"cfg_([a-z]+)_([a-z]+)\.bit", p.name)
        if m:
            out.append((p.stem, {"rp1": m.group(1), "rp2": m.group(2)}))
    return out


def base_for(cfg, rp, cfgs):
    other = "rp2" if rp == "rp1" else "rp1"
    rms = dict(cfgs)[cfg]
    for name, r in cfgs:
        if r[other] == rms[other] and r[rp] != rms[rp]:
            return name
    return None


def owner_words(grid, spec):
    return region.region_bits(region.region_tiles(grid, spec))


def touched(partial_bit, rps, rp, part, grid, full_frames):
    p = bitparse.parse(str(partial_bit), part)
    frames = {f: d for f, d in p["frames"].items() if (f >> 23) & 7 != bitparse.BLOCKS["CFG_CLB"]}
    own = owner_words(grid, rps[rp])
    other_rp = "rp2" if rp == "rp1" else "rp1"
    oth = owner_words(grid, rps[other_rp])
    zero = [0] * bitparse.CONFIG["words_per_frame"]
    rep = {"frames": len(frames), "own_only": 0, "other_only": 0, "both": 0, "static": [], "other_words": 0,
           "other_words_equal_full": 0, "other_words_nonzero_full": 0, "other_words_nonzero_partial": 0}
    for f, d in frames.items():
        a, b = f in own, f in oth
        if a and b:
            rep["both"] += 1
        elif a:
            rep["own_only"] += 1
        elif b:
            rep["other_only"] += 1
        else:
            rep["static"].append(bitparse.far_str(f))
        if b:
            full = full_frames.get(f, zero)
            for w in sorted(oth[f]):
                rep["other_words"] += 1
                rep["other_words_equal_full"] += d[w] == full[w]
                rep["other_words_nonzero_full"] += full[w] != 0
                rep["other_words_nonzero_partial"] += d[w] != 0
    return rep


def main():
    ap = argparse.ArgumentParser(description="Per-RP partials from Vivado's own full bitstreams of a two-RP design "
                                             "(partial.py with the Vivado-parity options), compared with Vivado's partials")
    ap.add_argument("--design", default="dfx_2rp", choices=sorted(CONFIG["designs"]))
    ap.add_argument("--variants", nargs="*", default=list(CONFIG["variants"]))
    ap.add_argument("--extra", default="", help="additional partial.py options")
    ap.add_argument("--tag", default="", help="suffix of the output names")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    rps = CONFIG["designs"][a.design]
    vdir = ROOT / CONFIG["vivado_dir"].format(design=a.design)
    out = ROOT / CONFIG["out_dir"].format(design=a.design)
    out.mkdir(parents=True, exist_ok=True)
    cfgs = configs(vdir)
    print(f"configurations: {[c for c, _ in cfgs]}")
    for c, _ in cfgs:
        fasm = out / f"{c}.fasm"
        if not fasm.exists():
            run([CONFIG["tabby"], "flow/bit2fasm.py", vdir / f"{c}.bit", fasm], out / f"{c}.bit2fasm.log", dry)
    sp = out / "static_pips.fasm"
    if not sp.exists():
        run(["python3", "flow/vivado_pips.py", vdir / "pips" / "static_routed.pips.txt", sp], out / "static_pips.log", dry)
    if dry:
        return
    part = bitparse.Part()
    grid = region.load_grid()
    results = []
    fail = 0
    for v in a.variants:
        sub = vdir if v == "base" else vdir / v
        for c, rms in cfgs:
            full_frames = bitparse.parse(str(vdir / f"{c}.bit"), part)["frames"]
            for rp in ("rp1", "rp2"):
                ref = sub / f"{c}_pblock_{rp}_partial.bit"
                base = base_for(c, rp, cfgs)
                n = f"{v}_{c}_{rp}{a.tag}"
                row = {"variant": v, "config": c, "rp": rp, "base": base, "vivado": str(ref.relative_to(ROOT))}
                if not ref.exists():
                    row["missing_vivado_partial"] = True
                    print(f"{n} | Vivado partial missing: {ref}")
                    results.append(row)
                    continue
                row["vivado_frames"] = touched(ref, rps, rp, part, grid, full_frames)
                cmd = ["python3", "flow/partial.py", vdir / f"{c}.bit", out / n, "--design", "top", "--region", rps[rp],
                       "--fasm", out / f"{c}.fasm", "--static-pip-list", sp, "--compress-flush", CONFIG["flush"]]
                cmd += CONFIG["parity_opts"] + CONFIG["variants"][v] + a.extra.split()
                if base:
                    cmd += ["--base", vdir / f"{base}.bit", "--simulate"]
                rc = run(cmd, out / f"{n}.log")
                log = (out / f"{n}.log").read_text()
                row["partial_rc"] = rc
                row["sim"] = next((l for l in log.splitlines() if l.startswith("crc:")), None)
                row["refused"] = next((l for l in log.splitlines() if "REFUSED" in l), None)
                if rc != 0:
                    fail = 1
                if (out / f"{n}.bit").exists():
                    cj = out / f"compare_{n}.json"
                    run(["python3", "flow/partial_compare.py", ref, out / f"{n}.bit", "--json", cj])
                    cmpj = json.loads(cj.read_text())
                    row["words_vivado"], row["words_ours"], row["words_differ"] = \
                        cmpj["words_a"], cmpj["words_b"], cmpj["words_differ"]
                    row["ours_frames"] = touched(out / f"{n}.bit", rps, rp, part, grid, full_frames)
                fr = row["vivado_frames"]
                print(f"{n} | base {base} | words {row.get('words_vivado')} vs {row.get('words_ours')}, "
                      f"differ {row.get('words_differ')} | vivado frames {fr['frames']}: own-only {fr['own_only']}, "
                      f"other-only {fr['other_only']}, shared {fr['both']}, static {fr['static']}; other-RP words "
                      f"{fr['other_words']} (= full {fr['other_words_equal_full']}, non-zero in full "
                      f"{fr['other_words_nonzero_full']}) | {row['sim'] or row['refused'] or 'rc=' + str(rc)}")
                results.append(row)
    (out / f"summary{a.tag}.json").write_text(json.dumps(results, indent=1))
    print(f"summary {out / f'summary{a.tag}.json'}")
    sys.exit(fail)


if __name__ == "__main__":
    main()
