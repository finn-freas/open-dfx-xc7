import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_build
import gap_report

CONFIG = {
    "root": gap_build.ROOT,
    "chipdb": "toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin",
    "nextpnr": "build/nextpnr-build/{variant}/nextpnr-himbaechel",
    "npwait": "ofx/npwait.sh",
    "base": "ofx",
    "variant": "ofx-prim",
    "db": "build/prjxray-db-prim",
    "db_tag": "prim",
    "viv_tags": ("gap", "gap2", "gap3", "gap4", "gap5", "prim"),
    "dry_run": True,
}

ROOT = CONFIG["root"]
GAP = ROOT / "build" / "gap"


def viv_tag(name):
    for t in reversed(CONFIG["viv_tags"]):
        if (gap_report.CONFIG["win_build"] / t / name / f"{name}.bit").exists():
            return t
    return None


def build(name, variant, dry):
    src = ROOT / "designs" / "gap" / name
    rtl = sorted(src.glob("*.v")) + sorted(src.glob("*.sv"))
    xdc = next(src.glob("*.xdc"))
    if variant == "oxc7":
        tools = {}
    else:
        os.environ["OFX_NEXTPNR_BIN"] = str(ROOT / CONFIG["nextpnr"].format(variant=variant))
        chipdb = CONFIG.get("variant_chipdb") if variant == CONFIG["variant"] and CONFIG.get("variant_chipdb") else CONFIG["chipdb"]
        tools = {"nextpnr": str(ROOT / CONFIG["npwait"]), "chipdb": str(ROOT / chipdb),
                 "json_from": "oxc7", "db": str(ROOT / CONFIG["db"])}
    return gap_build.build(name, src, name, rtl, xdc, GAP / name / variant, gap_build.CONFIG["freq_mhz"], dry, (), tools)


def decode(bit, out):
    if not out.exists():
        subprocess.run([str(ROOT / gap_report.CONFIG["tabbypy"]), str(ROOT / "flow" / "bit2fasm.py"), "--verbose",
                        "--db-root", str(ROOT / CONFIG["db"] / gap_build.CONFIG["family"]), str(bit), str(out)],
                       check=True, stdout=subprocess.DEVNULL)
    return out


def compare(name, variant, base):
    d = GAP / name
    t = CONFIG["db_tag"]
    res = {"design": name, "variant": variant, "base": base, "db": CONFIG["db"]}
    for v in (base, variant):
        st = d / v / "status.json"
        if st.exists():
            s = json.loads(st.read_text())["stages"]
            res[f"stages_{v}"] = {k: x.get("ok") for k, x in s.items()}
            res[f"error_{v}"] = next((x.get("error") for x in s.values() if x.get("ok") is False), "")
    fa, fb = d / variant / f"{name}.frames", d / base / f"{name}.frames"
    if fa.exists() and fb.exists():
        res["frames_identical_to_base"] = fa.read_bytes() == fb.read_bytes()
    tag = viv_tag(name)
    res["viv_tag"] = tag
    if not tag:
        return res
    vdir = gap_report.ingest(name, tag)
    vf = decode(vdir / f"{name}.bit", vdir / f"{name}.viv.{t}.fasm")
    ub = gap_report.unknown_bits(vf)
    res["viv_unknown_bits"] = len(ub)
    res["viv_unknown_list"] = [f"{a}:{b}" for a, b in ub][:64]
    for v in (base, variant):
        ob = d / v / f"{name}.bit"
        if not ob.exists():
            continue
        of = decode(ob, d / v / f"{name}.dec.{t}.fasm")
        cv, co = vdir / f"{name}.viv.{t}.canon.fasm", d / v / f"{name}.dec.{t}.canon.fasm"
        gap_report.canon([(vf, cv), (of, co)])
        out = {}
        for mode in ("exact", "by_tile_type"):
            sv, so = gap_report.site_features(cv, mode == "exact"), gap_report.site_features(co, mode == "exact")
            out[mode] = {"viv_only": sorted(sv - so), "oxc7_only": sorted(so - sv), "common": len(sv & so)}
        res[f"diff_{v}"] = out
    return res


def fmt(r, v):
    x = r.get(f"diff_{v}")
    if not x:
        return "-"
    e, t = x["exact"], x["by_tile_type"]
    return f"{len(e['viv_only'])}/{len(e['oxc7_only'])} ({len(t['viv_only'])}/{len(t['oxc7_only'])})"


def main():
    ap = argparse.ArgumentParser(description="build gap designs with the ofx and ofx-prim nextpnr and compare both with Vivado, decoded with the draft prjxray-db")
    ap.add_argument("designs", nargs="+")
    ap.add_argument("--base", default=CONFIG["base"])
    ap.add_argument("--variant", default=CONFIG["variant"])
    ap.add_argument("--no-stock", action="store_true", help="do not run the toolchain build (build/gap/<d>/oxc7) first")
    ap.add_argument("--out", help="summary json (default build/gap/prim_eval_<variant>.json)")
    ap.add_argument("--variant-chipdb", help="chipdb for the variant builds only (default: the nightly's for both)")
    ap.add_argument("--db", default=CONFIG["db"], help="prjxray-db root for fasm2frames and decoding (default %(default)s)")
    ap.add_argument("--db-tag", default=CONFIG["db_tag"], help="suffix of the decoded files (default %(default)s)")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    CONFIG.update({"variant_chipdb": a.variant_chipdb, "variant": a.variant, "db": a.db, "db_tag": a.db_tag})
    dry = CONFIG["dry_run"] and not a.run
    for n in a.designs:
        if not a.no_stock:
            build(n, "oxc7", dry)
        for v in dict.fromkeys((a.base, a.variant)):
            build(n, v, dry)
    if dry:
        return
    res = [compare(n, a.variant, a.base) for n in a.designs]
    out = Path(a.out) if a.out else GAP / f"prim_eval_{a.variant}.json"
    old = {r["design"]: r for r in json.loads(out.read_text())} if out.exists() else {}
    old.update({r["design"]: r for r in res})
    out.write_text(json.dumps(list(old.values()), indent=1) + "\n")
    for r in res:
        print(f"{r['design']}: viv={r.get('viv_tag')} unknown={r.get('viv_unknown_bits')} "
              f"{a.base}={r.get('stages_' + a.base)} {a.variant}={r.get('stages_' + a.variant)} "
              f"frames_identical={r.get('frames_identical_to_base')} "
              f"diff exact(by type) {a.base}={fmt(r, a.base)} {a.variant}={fmt(r, a.variant)}")
        if r.get(f"error_{a.variant}"):
            print(f"  {a.variant} error: {r[f'error_{a.variant}']}")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
