import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_openxc7 import tool

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "summary": "build/ofx_prim_noop/summary_blinky_rv_soc_rv_ppa.json",
    "db": "build/prjxray-db-prim/artix7",
    "part": "xc7a35tcsg324-1",
    "out": "build/ofx_prim_noop/fasm_check.json",
    "dry_run": True,
}

ROOT = CONFIG["root"]


def fasm_lines(p):
    return {l.strip() for l in Path(p).read_text().splitlines() if l.strip() and not l.startswith("#")}


def frame_bits(p):
    bits = set()
    for ln in Path(p).read_text().splitlines():
        parts = ln.split()
        if len(parts) < 2:
            continue
        addr = parts[0]
        for i, w in enumerate(parts[1].split(",")):
            v = int(w, 16)
            for b in range(32):
                if v >> b & 1:
                    bits.add((addr, i, b))
    return bits


def check(row, dry):
    cand = Path(row["ofx"]).with_suffix(".fasm")
    ref = Path(row["ref"]).with_suffix(".fasm")
    res = {"build": row["build"], "result": row["result"]}
    a, b = fasm_lines(cand), fasm_lines(ref)
    res["fasm_only_candidate"] = sorted(a - b)
    res["fasm_only_reference"] = sorted(b - a)
    frames = cand.parent / (cand.stem + ".prim.frames")
    cmd = f"{tool('fasm2frames')} --part {CONFIG['part']} --db-root {ROOT / CONFIG['db']} {cand} > {frames}"
    if dry:
        print(f"[dry] {cmd}")
        return res
    if not frames.exists() or frames.stat().st_size == 0:
        subprocess.run(["bash", "-c", cmd], check=True)
    fa, fb = frame_bits(frames), frame_bits(Path(row["ref"]))
    res["frame_bits_only_candidate"] = len(fa - fb)
    res["frame_bits_only_reference"] = len(fb - fa)
    return res


def main():
    ap = argparse.ArgumentParser(description="for each no-op build: FASM line difference to the reference, and .frames made with the draft db")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    rows = json.loads((ROOT / CONFIG["summary"]).read_text())
    res = [check(r, dry) for r in rows]
    if dry:
        return
    (ROOT / CONFIG["out"]).write_text(json.dumps(res, indent=1) + "\n")
    for r in res:
        print(f"{r['build']}: {r['result']}; FASM +{len(r['fasm_only_candidate'])}/-{len(r['fasm_only_reference'])} "
              f"{r['fasm_only_candidate'][:2]}; frame bits +{r['frame_bits_only_candidate']}/-{r['frame_bits_only_reference']}")


if __name__ == "__main__":
    main()
