import argparse
import collections
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import device

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "out": "build/ofx/devices/bitcheck",
    "tabbypy": "toolchain/openxc7/libexec/tabbypy3",
    "canon": ("import sys, fasm\n"
              "lines = [l for l in fasm.parse_fasm_filename(sys.argv[1]) if l.set_feature]\n"
              "open(sys.argv[2], 'w').write(fasm.fasm_tuple_to_string(lines, canonical=True))\n"),
}


def frames_check(frames_file, bit, part):
    env = dict(os.environ, **device.env(part))
    code = ("import sys, json; sys.path.insert(0, %r); import bitparse; p = bitparse.Part(); "
            "b = bitparse.parse(%r, p)['frames']; w = bitparse.without_ecc; f = {}\n"
            "for line in open(%r):\n"
            "    a, d = line.split()\n"
            "    f[int(a, 16)] = [int(x, 16) for x in d.split(',')]\n"
            "z = [0] * 101\n"
            "diff = [k for k in f if w(f[k]) != w(b.get(k, z))]\n"
            "extra = [k for k in b if k not in f and any(w(b[k]))]\n"
            "missing = [k for k in f if k not in b and any(w(f[k]))]\n"
            "print(json.dumps({'frames_file': len(f), 'frames_bit': len(b), 'nonzero_file': sum(1 for v in f.values() if any(w(v))),"
            " 'differ': len(diff), 'nonzero_not_in_file': len(extra), 'nonzero_not_in_bit': len(missing)}))\n"
            % (str(CONFIG["root"] / "flow"), str(bit), str(frames_file)))
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    if r.returncode:
        return {"error": r.stderr.strip().splitlines()[-1]}
    return json.loads(r.stdout)


def canon(src, dst):
    subprocess.run([str(CONFIG["root"] / CONFIG["tabbypy"]), "-c", CONFIG["canon"], str(src), str(dst)], check=True)
    return {l.strip() for l in dst.read_text().splitlines() if l.strip()}


def fasm_check(fasm_file, frames_file, bit, part, out):
    env = dict(os.environ, **device.env(part))
    raw = out.with_suffix(".decoded.fasm")
    raw.unlink(missing_ok=True)
    r = subprocess.run([str(CONFIG["root"] / CONFIG["tabbypy"]), str(CONFIG["root"] / "flow" / "bit2fasm.py"),
                        "--verbose", str(bit), str(raw)], env=env, capture_output=True, text=True)
    if r.returncode:
        return {"error": (r.stderr.strip().splitlines() or ["?"])[-1]}
    unknown = [l for l in raw.read_text().splitlines() if re.match(r"\s*(#\s*)?(unknown|\{)", l, re.I)]
    dec = canon(raw, out.with_suffix(".decoded.canon.fasm"))
    ours = canon(fasm_file, out.with_suffix(".nextpnr.canon.fasm"))
    ttype = lambda fs: dict(collections.Counter(re.sub(r"_X\d+Y\d+$", "", f.split(".", 1)[0]) for f in fs))
    only_n, only_d = sorted(ours - dec), sorted(dec - ours)
    r = device.resolve(part)
    reenc = out.with_suffix(".reencoded.frames")
    subprocess.run(["bash", "-c", f"{CONFIG['root'] / 'toolchain/openxc7/bin/fasm2frames'} --part {part} "
                    f"--db-root {Path(r['db_root']) / r['family']} {out.with_suffix('.decoded.canon.fasm')} > {reenc}"],
                   check=True, capture_output=True)
    a = {l.split()[0]: l.split()[1] for l in reenc.read_text().splitlines() if l.strip()}
    b = {l.split()[0]: l.split()[1] for l in frames_file.read_text().splitlines() if l.strip()}
    zero = ",".join(["0x00000000"] * 101)
    reenc_diff = sum(1 for k in set(a) | set(b) if a.get(k, zero) != b.get(k, zero))
    return {"reencoded_frames_differ": reenc_diff,"nextpnr_features": len(ours), "decoded_features": len(dec), "common": len(ours & dec),
            "only_nextpnr": len(only_n), "only_decoded": len(only_d), "unknown_bits_lines": len(unknown),
            "only_nextpnr_by_tile_type": ttype(only_n), "only_decoded_by_tile_type": ttype(only_d),
            "only_nextpnr_sample": only_n[:20], "only_decoded_sample": only_d[:20], "unknown_sample": unknown[:10]}


def one(name, impl=None):
    sys.path.insert(0, str(CONFIG["root"]))
    from ofx import project as P
    d = CONFIG["root"] / "examples" / name
    proj = P.Project(P.find(str(d)))
    impl = Path(impl) if impl else d / "build" / "impl"
    top = proj.top
    out = CONFIG["root"] / CONFIG["out"] / name
    out.parent.mkdir(parents=True, exist_ok=True)
    bit, frames, fasm = impl / f"{top}.bit", impl / f"{top}.frames", impl / f"{top}.fasm"
    res = {"design": name, "part": proj.part, "family": proj.device["family"], "bit": str(bit),
           "frames": frames_check(frames, bit, proj.part), "fasm": fasm_check(fasm, frames, bit, proj.part, out)}
    out.with_suffix(".json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def main():
    ap = argparse.ArgumentParser(description="Decode an ofx build's bitstream and check it against the build's own "
                                             ".frames (fasm2frames) and .fasm (nextpnr)")
    ap.add_argument("examples", nargs="+")
    a = ap.parse_args()
    for n in a.examples:
        r = one(n)
        f, m = r["frames"], r["fasm"]
        if "error" in f or "error" in m:
            print(f"{n} {r['part']}: ERROR frames {f.get('error')} fasm {m.get('error')}")
            continue
        ok = f["differ"] == 0 and f["nonzero_not_in_file"] == 0 and f["nonzero_not_in_bit"] == 0
        print(f"{n} {r['part']}: frames {'MATCH' if ok else 'DIFFER'} ({f['nonzero_file']} non-zero, {f['differ']} differ, "
              f"{f['nonzero_not_in_file']}+{f['nonzero_not_in_bit']} unmatched); FASM nextpnr {m['nextpnr_features']} "
              f"decoded {m['decoded_features']} common {m['common']} only-nextpnr {m['only_nextpnr']} "
              f"only-decoded {m['only_decoded']} unknown-bit lines {m['unknown_bits_lines']}; decoded FASM re-encoded: "
              f"{m['reencoded_frames_differ']} frames differ")


if __name__ == "__main__":
    main()
