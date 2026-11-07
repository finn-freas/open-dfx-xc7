import argparse
import collections
import csv
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
    "out": "build/ofx/devices/vivado",
    "vivado_build": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/devices"),
    "regs": ("IDCODE", "COR0", "COR1", "CTL0", "CTL1", "MASK", "WBSTAR", "TIMER"),
    "dry_run": True,
    "tabbypy": "toolchain/openxc7/libexec/tabbypy3",
    "canon": ("import sys, fasm\n"
              "lines = [l for l in fasm.parse_fasm_filename(sys.argv[1]) if l.set_feature]\n"
              "open(sys.argv[2], 'w').write(fasm.fasm_tuple_to_string(lines, canonical=True))\n"),
}


def parse_bit(bit, part):
    env = dict(os.environ, **device.env(part))
    code = ("import sys, json; sys.path.insert(0, %r); import bitparse; p = bitparse.Part(); r = bitparse.parse(%r, p); "
            "f = r['frames']; nz = sorted(k for k in f if any(bitparse.without_ecc(f[k]))); "
            "print(json.dumps({'frames': len(f), 'nonzero': nz, 'seq': r.get('sequence', r.get('seq'))}, default=str))"
            % (str(CONFIG["root"] / "flow"), str(bit)))
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
    txt = subprocess.run([sys.executable, str(CONFIG["root"] / "flow" / "bitparse.py"), str(bit)], env=env,
                         capture_output=True, text=True, check=True).stdout
    seq = re.search(r"^sequence: (.*)$", txt, re.M).group(1)
    regs = collections.defaultdict(list)
    for k, v in re.findall(r"(\w+)=(0x[0-9a-f]+)", seq):
        regs[k].append(v)
    d = json.loads(r.stdout)
    return {"frames": d["frames"], "nonzero": d["nonzero"], "regs": dict(regs), "sequence": seq}


def fasm(bit, part, out):
    env = dict(os.environ, **device.env(part))
    py = str(CONFIG["root"] / CONFIG["tabbypy"])
    raw, canon = out.with_suffix(".raw.fasm"), out
    if not raw.exists():
        subprocess.run([py, str(CONFIG["root"] / "flow" / "bit2fasm.py"), "--verbose", str(bit), str(raw)],
                       env=env, check=True, capture_output=True, text=True)
    if not canon.exists():
        subprocess.run([py, "-c", CONFIG["canon"], str(raw), str(canon)], check=True)
    unknown = sum(1 for l in raw.read_text().splitlines() if re.match(r"\s*(#\s*)?(unknown|\{)", l, re.I))
    feats = {l.strip() for l in canon.read_text().splitlines() if l.strip()}
    return feats, unknown


def pin_tiles(part, pins):
    r = device.resolve(part)
    rows = csv.DictReader(open(device.CONFIG["root"] / device.CONFIG["db"] / r["family"] / part / "package_pins.csv"))
    m = {row["pin"]: row for row in rows}
    out = {}
    for p in pins:
        t = m[p]["tile"]
        out[p] = {"tile": t, "site": m[p]["site"], "ioi": re.sub(r"IOB(33|18)", r"IOI\g<1>", t).replace("IOI33", "IOI3")}
    return out


def by_tile(feats):
    d = collections.defaultdict(set)
    for f in feats:
        d[f.split(".", 1)[0]].add(f)
    return d


def compare(name, part, ours, theirs, out):
    pins = re.findall(r"PACKAGE_PIN\s+(\w+)", "".join(p.read_text() for p in (CONFIG["root"] / "examples" / name / "constraints").glob("*.xdc")))
    a, b = parse_bit(ours, part), parse_bit(theirs, part)
    fa, ua = fasm(ours, part, out / f"{name}.ofx.fasm")
    fb, ub = fasm(theirs, part, out / f"{name}.vivado.fasm")
    ta, tb = by_tile(fa), by_tile(fb)
    io = {}
    for p, t in pin_tiles(part, pins).items():
        io[p] = {"tile": t["tile"], "site": t["site"], "same": ta.get(t["tile"], set()) == tb.get(t["tile"], set()),
                 "only_ofx": sorted(ta.get(t["tile"], set()) - tb.get(t["tile"], set())),
                 "only_vivado": sorted(tb.get(t["tile"], set()) - ta.get(t["tile"], set()))}
    gt = {}
    for t in sorted(set(ta) | set(tb)):
        if re.match(r"GT[PX]_(COMMON|CHANNEL)", t):
            gt[t] = {"ofx": len(ta.get(t, ())), "vivado": len(tb.get(t, ())), "common": len(ta.get(t, set()) & tb.get(t, set())),
                     "only_ofx": sorted(ta.get(t, set()) - tb.get(t, set())),
                     "only_vivado": sorted(tb.get(t, set()) - ta.get(t, set()))}
    ttype = lambda feats: collections.Counter(re.sub(r"_X\d+Y\d+$", "", f.split(".", 1)[0]) for f in feats)
    res = {"design": name, "part": part,
           "idcode": {"ofx": a["regs"].get("IDCODE"), "vivado": b["regs"].get("IDCODE"),
                      "prjxray_db": hex(json.loads((device.CONFIG["root"] / device.CONFIG["db"] / device.resolve(part)["family"] / part / "part.json").read_text())["idcode"])},
           "frames": {"ofx": a["frames"], "vivado": b["frames"]},
           "nonzero_frames": {"ofx": len(a["nonzero"]), "vivado": len(b["nonzero"])},
           "regs": {k: {"ofx": a["regs"].get(k), "vivado": b["regs"].get(k)} for k in CONFIG["regs"]},
           "fasm_features": {"ofx": len(fa), "vivado": len(fb), "common": len(fa & fb)},
           "fasm_unknown_lines": {"ofx": ua, "vivado": ub},
           "features_by_tile_type": {"ofx": dict(ttype(fa)), "vivado": dict(ttype(fb))},
           "io_tiles": io, "gt_tiles": gt}
    (out / f"{name}.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def main():
    ap = argparse.ArgumentParser(description="Compare an ofx blinky bitstream with Vivado's for the same design and part")
    ap.add_argument("jobs", nargs="+", help="name:part")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    out = CONFIG["root"] / CONFIG["out"]
    for j in a.jobs:
        name, part = j.split(":")
        ours = CONFIG["root"] / "examples" / name / "build" / "impl" / f"{name}.bit"
        theirs = CONFIG["vivado_build"] / name / f"{name}.bit"
        if CONFIG["dry_run"] and not a.run:
            print(f"[dry] compare {ours} {theirs} ({part})")
            continue
        out.mkdir(parents=True, exist_ok=True)
        r = compare(name, part, ours, theirs, out)
        io_same = sum(v["same"] for v in r["io_tiles"].values())
        print(f"{name} {part}: IDCODE ofx {r['idcode']['ofx']} vivado {r['idcode']['vivado']} db {r['idcode']['prjxray_db']}; "
              f"frames {r['frames']['ofx']} / {r['frames']['vivado']}; non-zero {r['nonzero_frames']['ofx']} / {r['nonzero_frames']['vivado']}; "
              f"fasm {r['fasm_features']['ofx']} / {r['fasm_features']['vivado']} (common {r['fasm_features']['common']}); "
              f"unknown lines {r['fasm_unknown_lines']['ofx']} / {r['fasm_unknown_lines']['vivado']}; "
              f"IO tiles identical {io_same}/{len(r['io_tiles'])}")
        for k, v in r["regs"].items():
            if v["ofx"] != v["vivado"]:
                print(f"  {k}: ofx {v['ofx']} vivado {v['vivado']}")
        for t, v in r["gt_tiles"].items():
            print(f"  GT tile {t}: ofx {v['ofx']} vivado {v['vivado']} common {v['common']} features")
        for p, v in r["io_tiles"].items():
            if not v["same"]:
                print(f"  pin {p} {v['tile']}: only ofx {v['only_ofx']} only vivado {v['only_vivado']}")


if __name__ == "__main__":
    main()
