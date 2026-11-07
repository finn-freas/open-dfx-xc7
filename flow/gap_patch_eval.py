import argparse
import difflib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_build
import gap_report

CONFIG = {
    "root": gap_build.ROOT,
    "chipdb": "toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin",
    "nextpnr": "build/nextpnr-build/{variant}/nextpnr-himbaechel",
    "base_variant": "stock",
    "json_from": "oxc7",
    "viv_tags": ("gap", "gap2", "gap3", "gap4", "gap5"),
    "jobs": 4,
    "dry_run": True,
    "diff_lines_kept": 60,
}

ROOT = CONFIG["root"]
GAP = ROOT / "build" / "gap"


def viv_tag(name):
    tag = None
    for t in CONFIG["viv_tags"]:
        f = GAP / f"summary_{t}.json"
        if f.exists() and any(r["design"] == name for r in json.loads(f.read_text())):
            tag = t
    return tag


def build_one(name, variant, dry, synth=None, npr_variant=None):
    src = ROOT / "designs" / "gap" / name
    rtl = sorted(src.glob("*.v")) + sorted(src.glob("*.sv"))
    xdc = next(src.glob("*.xdc"))
    tools = {"nextpnr": str(ROOT / CONFIG["nextpnr"].format(variant=npr_variant or variant)), "chipdb": str(ROOT / CONFIG["chipdb"])}
    if synth:
        tools.update(synth)
    else:
        tools["json_from"] = CONFIG["json_from"]
    return gap_build.build(name, src, name, rtl, xdc, GAP / name / variant, gap_build.CONFIG["freq_mhz"], dry, (), tools)


def fasm_lines(p):
    return [ln for ln in p.read_text().splitlines() if ln.strip() and not ln.startswith("#")] if p.exists() else None


def compare(name, variant, base):
    d = GAP / name
    res = {"design": name, "variant": variant, "base": base}
    st = json.loads((d / variant / "status.json").read_text()) if (d / variant / "status.json").exists() else {}
    res["stages"] = {k: v.get("ok") for k, v in st.get("stages", {}).items()}
    res["error"] = next((v.get("error") for v in st.get("stages", {}).values() if v.get("ok") is False), "")
    fa, fb = fasm_lines(d / variant / f"{name}.fasm"), fasm_lines(d / base / f"{name}.fasm")
    if fa is not None and fb is not None:
        sa, sb = set(fa), set(fb)
        res["fasm_identical"] = sorted(fa) == sorted(fb)
        res["fasm_only_variant"] = sorted(sa - sb)[:CONFIG["diff_lines_kept"]]
        res["fasm_only_base"] = sorted(sb - sa)[:CONFIG["diff_lines_kept"]]
        res["fasm_counts"] = {"variant_only": len(sa - sb), "base_only": len(sb - sa), "common": len(sa & sb)}
    fr_a, fr_b = d / variant / f"{name}.frames", d / base / f"{name}.frames"
    if fr_a.exists() and fr_b.exists():
        res["frames_identical"] = fr_a.read_bytes() == fr_b.read_bytes()
        if not res["frames_identical"]:
            la, lb = fr_a.read_text().splitlines(), fr_b.read_text().splitlines()
            res["frames_differing"] = sum(1 for ln in difflib.unified_diff(lb, la, n=0) if ln[:1] in "+-") // 2
    tag = viv_tag(name)
    res["viv_tag"] = tag
    if tag:
        for v in (variant, base):
            if (d / v / f"{name}.bit").exists():
                r = gap_report.report(name, tag, v)
                res[f"viv_diff_{v}"] = r.get("diff")
        fd = d / f"fasm_diff_{variant}.json"
        if fd.exists():
            res["viv_diff_list"] = json.loads(fd.read_text())["by_tile_type"]
    return res


def main():
    ap = argparse.ArgumentParser(description="build gap designs with a patched nextpnr (or yosys) and compare with stock and Vivado")
    ap.add_argument("variant", help="build/nextpnr-build/<variant>; also the output tag build/gap/<design>/<variant>")
    ap.add_argument("designs", nargs="+")
    ap.add_argument("--base", default=CONFIG["base_variant"], help="variant to compare against (built the same way)")
    ap.add_argument("--yosys-plugin", help="run yosys with this plugin instead of copying the oxc7 json (for yosys patches)")
    ap.add_argument("--clkbuf-pass", help="pass that replaces clkbufmap in synth_xilinx (with --yosys-plugin)")
    ap.add_argument("--nextpnr-variant", help="nextpnr build for both runs (default: each run's own variant name)")
    ap.add_argument("--base-synth", action="store_true", help="also run yosys for the base variant, with the stock clkbufmap split the same way")
    ap.add_argument("--out", help="summary json (default build/gap/patch_eval_<variant>.json)")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    synth = {"yosys_plugin": str(Path(a.yosys_plugin).resolve()), "clkbuf_pass": a.clkbuf_pass} if a.yosys_plugin else None
    base_synth = {"clkbuf_pass": "clkbufmap"} if a.base_synth else None
    jobs = [(n, v, synth if v == a.variant else base_synth) for n in a.designs for v in dict.fromkeys((a.base, a.variant))]
    with ThreadPoolExecutor(max_workers=1 if dry else CONFIG["jobs"]) as ex:
        list(ex.map(lambda j: build_one(j[0], j[1], dry, j[2], a.nextpnr_variant), jobs))
    if dry:
        return
    res = [compare(n, a.variant, a.base) for n in a.designs]
    out = Path(a.out) if a.out else GAP / f"patch_eval_{a.variant}.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    for r in res:
        dv, db = r.get(f"viv_diff_{a.variant}"), r.get(f"viv_diff_{a.base}")
        fmt = lambda x: f"{x['by_tile_type']['viv_only']}/{x['by_tile_type']['oxc7_only']}" if x else "-"
        print(f"{r['design']}: stages={r['stages']} fasm_identical={r.get('fasm_identical')} "
              f"frames_identical={r.get('frames_identical')} fasm +{r.get('fasm_counts', {}).get('variant_only')} "
              f"-{r.get('fasm_counts', {}).get('base_only')} viv-by-type {a.base}={fmt(db)} {a.variant}={fmt(dv)}")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
