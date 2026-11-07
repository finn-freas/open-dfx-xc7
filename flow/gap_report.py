import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "win_build": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "keep": ("*.bit", "*.rpt", "times.txt", "status.txt", "worst_paths.txt"),
    "tabbypy": "toolchain/openxc7/libexec/tabbypy3",
    "tilegrid": "toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7/xc7a50t/tilegrid.json",
    "routing_tiles": re.compile(r"^(CLBL[LM]_[LR]|INT_[LR]|.*INT_INTERFACE.*|CLK_HROW.*|CLK_BUFG.*|HCLK_.*|BRKH.*|VBRK.*|CLK_FEED.*|.*_TERM.*)$"),
    "skip_tiles": {"LIOB33_X0Y43"},
    "viv_util": {"Slice LUTs": "lut", "Slice Registers": "ff", "F7 Muxes": "muxf7", "F8 Muxes": "muxf8",
                 "Block RAM Tile": "bram_tile", "DSPs": "dsp", "Bonded IOB": "iob"},
    "npr_util": {"SLICE_LUTX": "lut_bels", "SLICE_FFX": "ff", "CARRY4": "carry4", "RAMB18E1": "ramb18",
                 "RAMB36E1": "ramb36", "DSP48E1": "dsp"},
}

ROOT = CONFIG["root"]
CANON = """
import sys, fasm
from fasm.output import merge_and_sort
for src, dst in zip(sys.argv[1::2], sys.argv[2::2]):
    lines = [l for l in fasm.parse_fasm_filename(src) if l.set_feature]
    with open(dst, "w") as f:
        f.write(fasm.fasm_tuple_to_string(lines, canonical=True))
"""


def ingest(name, tag):
    src = CONFIG["win_build"] / tag / name
    dst = ROOT / "build" / "gap" / name / "viv"
    if not src.is_dir():
        return None
    dst.mkdir(parents=True, exist_ok=True)
    for pat in CONFIG["keep"]:
        for f in src.glob(pat):
            t = dst / f.name
            if not t.exists() or t.stat().st_mtime < f.stat().st_mtime:
                shutil.copy2(f, t)
    return dst


def ingest_common(tag):
    dst = ROOT / "build" / "gap" / f"vivado_{tag}"
    dst.mkdir(parents=True, exist_ok=True)
    for f in ("vivado.log", "device_sites.txt", "version.txt"):
        s = CONFIG["win_build"] / tag / f
        if s.exists():
            shutil.copy2(s, dst / f)
    return dst


def vivado_log_section(tag, name):
    log = ROOT / "build" / "gap" / f"vivado_{tag}" / "vivado.log"
    if not log.exists():
        return []
    out, on = [], False
    for ln in log.read_text(errors="replace").splitlines():
        if ln.startswith("GAP_BEGIN "):
            on = ln.split()[1] == name
        elif on and (ln.startswith("ERROR") or ln.startswith("CRITICAL WARNING")):
            out.append(ln.strip()[:300])
    return out


def decode(bit, out):
    if not out.exists():
        subprocess.run([str(ROOT / CONFIG["tabbypy"]), str(ROOT / "flow" / "bit2fasm.py"), "--verbose", str(bit), str(out)],
                       check=True, stdout=subprocess.DEVNULL)
    return out


def canon(pairs):
    todo = [x for p in pairs if not p[1].exists() for x in map(str, p)]
    if todo:
        subprocess.run([str(ROOT / CONFIG["tabbypy"]), "-c", CANON] + todo, check=True)


_GRID = None


def grid():
    global _GRID
    if _GRID is None:
        g = json.loads((ROOT / CONFIG["tilegrid"]).read_text())
        idx = {}
        for tile, t in g.items():
            for blk, b in t["bits"].items():
                base = int(b["baseaddr"], 16)
                idx.setdefault(base, []).append((b["offset"], b["words"], b["frames"], tile, t["type"]))
        _GRID = idx
    return _GRID


def unknown_bits(fasm_file):
    res = []
    for m in re.finditer(r'unknown_bit = "([0-9a-f]{8})_(\d+)_(\d+)", unknown_segment = "0x([0-9a-f]{8})", unknown_segbit = "(\d+_\d+)"',
                         fasm_file.read_text()):
        frame, word, bit, seg, segbit = int(m[1], 16), int(m[2]), int(m[3]), int(m[4], 16), m[5]
        tile = "?"
        for off, words, frames, t, ttype in grid().get(seg, []):
            if off <= word < off + words and frame - seg < frames:
                tile = t
                segbit = f"{frame - seg:02d}_{(word - off) * 32 + bit:02d}"
                break
        res.append((tile, segbit))
    return res


def norm(feature):
    tile, _, rest = feature.partition(".")
    ttype = re.sub(r"_X\d+Y\d+$", "", tile)
    rest = re.sub(r"\b(RAMB18_Y|DSP_)[01]\b", r"\1n", rest)
    return ttype, f"{ttype}.{rest}"


def site_features(fasm_file, exact=False):
    out = set()
    for ln in fasm_file.read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.startswith("{"):
            continue
        feat = ln.split()[0]
        if feat.split(".")[0] in CONFIG["skip_tiles"]:
            continue
        ttype, f = norm(feat)
        if not CONFIG["routing_tiles"].match(ttype):
            out.add(feat if exact else f)
    return out


def viv_util(path):
    res = {}
    if not path.exists():
        return res
    for ln in path.read_text().splitlines():
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([\d.]+)\s*\|", ln)
        if m and m[1] in CONFIG["viv_util"] and CONFIG["viv_util"][m[1]] not in res:
            res[CONFIG["viv_util"][m[1]]] = float(m[2])
    return res


def xdc_period(name):
    for x in (ROOT / "designs" / "gap" / name).glob("*.xdc"):
        m = re.search(r"-period\s+([\d.]+)", x.read_text())
        if m:
            return float(m[1])
    return 10.0


def viv_timing(path, period=10.0):
    if not path.exists():
        return {}
    lines = path.read_text().splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().startswith("WNS(ns)") and "TNS(ns)" in ln:
            vals = lines[i + 2].split()
            try:
                wns = float(vals[0])
            except (ValueError, IndexError):
                return {}
            return {"wns_ns": wns, "period_ns": period, "fmax_mhz": round(1000.0 / (period - wns), 2)}
    return {}


def npr_stats(log):
    res = {}
    if not log.exists():
        return res
    text = log.read_text(errors="replace")
    blk = text.split("Device utilisation:", 1)
    if len(blk) == 2:
        for m in re.finditer(r"Info:\s+(\w+):\s+(\d+)/\s*(\d+)", blk[1].split("\n\n", 1)[0]):
            if m[1] in CONFIG["npr_util"]:
                res[CONFIG["npr_util"][m[1]]] = int(m[2])
    fm = {}
    for m in re.finditer(r"Max frequency for clock '([^']+)': ([\d.]+) MHz", text):
        fm[m[1]] = float(m[2])
    if fm:
        res["fmax_mhz"] = fm
    return res


def yosys_stat(path):
    res = Counter()
    if path.exists():
        for m in re.finditer(r"^\s+(\d+)\s+(LUT[1-6]|FD[CPRS]E|CARRY4|RAMB\w+|DSP48E1|MUXF[78]|SRL\w+|RAM\w+)\s*$",
                             path.read_text(), re.M):
            k = "lut" if m[2].startswith("LUT") else ("ff" if m[2].startswith("FD") else m[2])
            res[k] += int(m[1])
    return dict(res)


def report(name, tag, otag="oxc7"):
    d = ROOT / "build" / "gap" / name
    sfx = "" if otag == "oxc7" else f"_{otag}"
    rec = {"design": name, "oxc7_tag": otag}
    st = d / otag / "status.json"
    if st.exists():
        o = json.loads(st.read_text())
        rec["oxc7"] = {k: {"ok": v.get("ok"), "error": v.get("error", ""), "seconds": v.get("seconds")}
                       for k, v in o["stages"].items()}
        rec["oxc7_stats"] = npr_stats(d / otag / "nextpnr.log")
        rec["oxc7_stats"]["yosys"] = yosys_stat(d / otag / "yosys_stat.txt")
    v = ingest(name, tag)
    if v:
        s = (v / "status.txt").read_text().split("\n", 1) if (v / "status.txt").exists() else ["rc ?"]
        rec["viv"] = {"rc": s[0].split()[-1], "detail": s[1].strip()[:400] if len(s) > 1 else "",
                      "errors": vivado_log_section(tag, name)[:6]}
        times = v / "times.txt"
        if times.exists():
            rec["viv"]["seconds"] = {a: float(b) for a, b in (l.split() for l in times.read_text().splitlines() if l.strip())}
        rec["viv"]["util"] = viv_util(v / "util.rpt")
        rec["viv"]["timing"] = viv_timing(v / "timing.rpt", xdc_period(name))
        bit = v / f"{name}.bit"
        if bit.exists():
            vf = decode(bit, v / f"{name}.viv.fasm")
            ub = unknown_bits(vf)
            rec["viv"]["unknown_bits"] = len(ub)
            rec["viv"]["unknown_by_tile"] = dict(Counter(t for t, _ in ub))
            rec["viv"]["unknown_list"] = [f"{t}:{b}" for t, b in ub][:64]
            ob = d / otag / f"{name}.bit"
            if ob.exists():
                of = decode(ob, d / otag / f"{name}.dec.fasm")
                cv, co = v / f"{name}.viv.canon.fasm", d / otag / f"{name}.dec.canon.fasm"
                canon([(vf, cv), (of, co)])
                diff, rec["diff"] = {}, {}
                for mode in ("exact", "by_tile_type"):
                    sv, so = site_features(cv, mode == "exact"), site_features(co, mode == "exact")
                    diff[mode] = {"viv_only": sorted(sv - so), "oxc7_only": sorted(so - sv)}
                    rec["diff"][mode] = {"viv_only": len(sv - so), "oxc7_only": len(so - sv), "common": len(sv & so)}
                (d / f"fasm_diff{sfx}.json").write_text(json.dumps(diff, indent=1) + "\n")
    (d / f"report{sfx}.json").write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def stage_cell(rec, stage):
    s = rec.get("oxc7", {}).get(stage)
    if s is None:
        return "-"
    return "ok" if s["ok"] else "**FAIL**"


def table(recs):
    rows = ["| design | synth | pnr | fasm | bitstream | Vivado | Vivado unknown bits | decoded non-CLB/non-INT features viv-only / oxc7-only |",
            "|---|---|---|---|---|---|---|---|"]
    for r in recs:
        v = r.get("viv", {})
        vs = "-" if not v else ("ok" if v["rc"] == "0" else "**FAIL**")
        ub = v.get("unknown_bits", "-")
        if ub not in ("-", 0):
            ub = f"{ub} ({', '.join(f'{k}:{n}' for k, n in v['unknown_by_tile'].items())})"
        df = r.get("diff")
        dfs = "-"
        if df:
            e, t = df["exact"], df["by_tile_type"]
            dfs = f"{e['viv_only']} / {e['oxc7_only']} (by type {t['viv_only']} / {t['oxc7_only']})"
        rows.append(f"| {r['design']} | {stage_cell(r, 'synth')} | {stage_cell(r, 'pnr')} | {stage_cell(r, 'fasm')} | "
                    f"{stage_cell(r, 'bitstream')} | {vs} | {ub} | {dfs} |")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description="collect openXC7 and Vivado gap results into build/gap/*/report.json")
    ap.add_argument("designs", nargs="*")
    ap.add_argument("--tag", default="gap", help="Vivado build tag under the Windows work dir")
    ap.add_argument("--oxc7-tag", default="oxc7", help="openXC7 build subdir to compare (non-default tags write report_<tag>.json)")
    a = ap.parse_args()
    ingest_common(a.tag)
    gap = ROOT / "build" / "gap"
    names = a.designs or sorted(p.name for p in (ROOT / "designs" / "gap").iterdir() if p.is_dir())
    recs = [report(n, a.tag, a.oxc7_tag) for n in names]
    sfx = "" if a.oxc7_tag == "oxc7" else f"_{a.oxc7_tag}"
    (gap / f"summary_{a.tag}{sfx}.json").write_text(json.dumps(recs, indent=1) + "\n")
    print(table(recs))
    for r in recs:
        for k, s in r.get("oxc7", {}).items():
            if s["ok"] is False:
                print(f"- {r['design']} openXC7 {k}: {s['error']}")
        v = r.get("viv")
        if v and v["rc"] != "0":
            print(f"- {r['design']} Vivado: {v['detail']} {v['errors'][:2]}")


if __name__ == "__main__":
    sys.exit(main())
