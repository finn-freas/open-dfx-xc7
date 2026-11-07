import argparse
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ddr_compare as dc

ROOT = dc.ROOT

CONFIG = {
    "designs": ["arty_eth", "arty_scope"],
    "top": "digilent_arty",
    "variant": "gapfix",
    "viv_tag": "eth",
    "src_dir": ROOT / "designs" / "eth",
    "out_dir": ROOT / "build" / "eth",
    "eth_port": re.compile(r"^(eth_|eth_clocks_)"),
    "clock_groups": ("CLK_BUFG", "CLK_HROW", "HCLK_CMT", "CMT"),
}


def eth_rows(res, group):
    out = {}
    for kind in ("viv_only", "oxc7_only"):
        c = Counter()
        for x in res["groups"][group][f"{kind}_list"]:
            port = x["pin"].split(":")[-1] if x["pin"] else ""
            if not x["pip"] and CONFIG["eth_port"].match(port):
                c[(re.sub(r"_X\d+Y\d+", "", x["f"]), re.sub(r"\[\d+\]", "[n]", port))] += 1
        out[kind] = [{"feature": f, "port": p, "n": n} for (f, p), n in sorted(c.items())]
    return out


def eth_common(cmp_dir):
    pins, ports = dc.pins_by_site(), dc.ports_by_pin()
    sv, so = dc.load(cmp_dir / "viv.canon.fasm"), dc.load(cmp_dir / "oxc7.canon.fasm")
    c = Counter()
    for f in sv & so:
        if dc.group(f) in ("IOB", "IOI") and not dc.is_pip(f):
            port = dc.annotate(f, pins, ports).split(":")[-1]
            if CONFIG["eth_port"].match(port):
                c[(re.sub(r"_X\d+Y\d+", "", f), re.sub(r"\[\d+\]", "[n]", port))] += 1
    return [{"feature": f, "port": p, "n": n} for (f, p), n in sorted(c.items())]


def run(design, variant, viv_tag):
    top = CONFIG["top"]
    dc.CONFIG.update({"design": design, "xdc": CONFIG["src_dir"] / design / f"{top}.xdc", "out_dir": CONFIG["out_dir"]})
    vsrc = dc.CONFIG["win_build"] / viv_tag / design
    vdst = CONFIG["out_dir"] / design / f"viv_{viv_tag}"
    vdst.mkdir(parents=True, exist_ok=True)
    for pat in ("*.bit", "*.rpt", "times.txt", "status.txt", "worst_paths.txt"):
        for f in vsrc.glob(pat):
            shutil.copy2(f, vdst / f.name)
    for f in ("vivado.log", "version.txt"):
        if (vsrc.parent / f).exists():
            shutil.copy2(vsrc.parent / f, vdst / f)
    cmp_dir = CONFIG["out_dir"] / design / f"cmp_{variant}_vs_{viv_tag}"
    res = dc.compare(vdst / f"{design}.bit", CONFIG["out_dir"] / design / variant / f"{top}.bit", cmp_dir)
    summary = {"design": design, "variant": variant,
               "unknown_bits": {k: sum(v.values()) for k, v in res["unknown_bits"].items()},
               "groups": {g: {k: r[k] for k in ("common", "viv_only", "oxc7_only", "viv_only_sites", "oxc7_only_sites")}
                          for g, r in res["groups"].items()},
               "eth_iob_common": eth_common(cmp_dir),
               "eth_iob_diff": eth_rows(res, "IOB"), "eth_ioi_diff": eth_rows(res, "IOI"),
               "clocking_by_type": {g: res["groups"][g]["by_type_nonpip"] for g in CONFIG["clock_groups"]},
               "clocking_by_feature": {g: {k: res["groups"][g][f"{k}_by_feature"] for k in ("viv_only", "oxc7_only")}
                                       for g in CONFIG["clock_groups"]},
               "ioi_clock_equivalence": {k: v for k, v in res["ioi_clock_equivalence"].items() if k != "mismatch_list"}}
    (cmp_dir / "eth_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main():
    ap = argparse.ArgumentParser(description="Decode our and Vivado's LiteEth bitstreams; diff MII IOs and clocking")
    ap.add_argument("designs", nargs="*", default=CONFIG["designs"])
    ap.add_argument("--variant", default=CONFIG["variant"])
    ap.add_argument("--viv-tag", default=CONFIG["viv_tag"])
    a = ap.parse_args()
    for d in a.designs:
        s = run(d, a.variant, a.viv_tag)
        print(f"== {d} {a.variant} vs Vivado: unknown bits {s['unknown_bits']}")
        for g, r in s["groups"].items():
            print(f"  {g:9s} common {r['common']:6d} viv-only {r['viv_only']:5d} ({r['viv_only_sites']} non-pip) "
                  f"oxc7-only {r['oxc7_only']:5d} ({r['oxc7_only_sites']} non-pip)")
        print("  eth IOB/IOI common:", [(x["feature"], x["port"], x["n"]) for x in s["eth_iob_common"]])
        for k in ("eth_iob_diff", "eth_ioi_diff"):
            for kind, rows in s[k].items():
                for x in rows:
                    print(f"  {k} {kind}: {x['n']} {x['feature']} [{x['port']}]")
        for g, t in s["clocking_by_type"].items():
            print(f"  {g} by type: common {t['common']} viv-only {t['viv_only']} oxc7-only {t['oxc7_only']}")


if __name__ == "__main__":
    main()
