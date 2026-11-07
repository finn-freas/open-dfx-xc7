import argparse
import csv
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_report as gr

ROOT = gr.ROOT

CONFIG = {
    "design": "arty_ddr3",
    "top": "digilent_arty",
    "variant": "gapfix",
    "viv_tag": "ddr3",
    "win_build": gr.CONFIG["win_build"],
    "out_dir": ROOT / "build" / "ddr3",
    "xdc": ROOT / "designs" / "ddr3" / "arty_ddr3" / "digilent_arty.xdc",
    "package_pins": ROOT / "toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7/xc7a35tcsg324-1/package_pins.csv",
    "groups": [
        ("IOB", re.compile(r"^[LR]IOB33")),
        ("IOI", re.compile(r"^[LR]IOI3")),
        ("HCLK_IOI", re.compile(r"^HCLK_IOI")),
        ("CMT", re.compile(r"^CMT_")),
        ("CLK_BUFG", re.compile(r"^CLK_BUFG")),
        ("CLK_HROW", re.compile(r"^CLK_HROW")),
        ("HCLK_CMT", re.compile(r"^HCLK_CMT")),
        ("BRAM", re.compile(r"^BRAM")),
        ("DSP", re.compile(r"^DSP")),
        ("CFG", re.compile(r"^CFG_")),
    ],
    "site_re": re.compile(r"^(IOB_Y[01]|ILOGIC_Y[01]|OLOGIC_Y[01]|IDELAY_Y[01]|ODELAY_Y[01]|IDELAYCTRL|PLLE2_ADV|MMCME2_ADV|"
                          r"BUFGCTRL|BUFHCE|BUFIO|BUFR|RAMB18_Y[01]|RAMB36|DSP48)$"),
    "leaf_re": re.compile(r"^([LR]IOI3\w*_X\d+Y(\d+))\.IOI_(\w+)\.IOI_LEAF_GCLK(\d+)$"),
    "hclk_re": re.compile(r"^(HCLK_IOI3?_X\d+Y\d+)\.HCLK_IOI_LEAF_GCLK_(TOP|BOT)(\d+)\.HCLK_IOI_CK_IGCLK(\d+)$"),
}


_TG = None


def tilegrid():
    global _TG
    if _TG is None:
        _TG = {k: (v["clock_region"], v["grid_x"], v["grid_y"]) for k, v in
               json.loads((ROOT / gr.CONFIG["tilegrid"]).read_text()).items() if "clock_region" in v}
    return _TG


def clock_partition(feats):
    tg = tilegrid()
    hclk = {}
    for f in feats:
        m = CONFIG["hclk_re"].match(f)
        if m:
            cr, gx, gy = tg[m[1]]
            hclk[(cr, gx, m[2], int(m[3]))] = (cr, gx, int(m[4]))
            hclk.setdefault(("row", cr, gx), gy)
    groups = defaultdict(set)
    for f in feats:
        m = CONFIG["leaf_re"].match(f)
        if m:
            cr, gx, gy = tg[m[1]]
            half = "TOP" if gy < hclk.get(("row", cr, gx), -1) else "BOT"
            key = hclk.get((cr, gx, half, int(m[4])), ("unresolved", cr, half, int(m[4])))
            groups[key].add((m[1], m[3]))
    return {e: frozenset(members) for members in groups.values() for e in members}


def clock_equivalence(sv, so):
    pv, po = clock_partition(sv), clock_partition(so)
    pins = sorted(set(pv) | set(po))
    bad = [e for e in pins if pv.get(e) != po.get(e)]
    groups = lambda p: sorted({tuple(sorted(f"{t}.{k}" for t, k in s)) for s in p.values()}, key=len)
    return {"clock_pins": len(pins), "pins_only_viv": sorted(f"{t}.{k}" for t, k in set(pv) - set(po)),
            "pins_only_oxc7": sorted(f"{t}.{k}" for t, k in set(po) - set(pv)), "mismatch": len(bad),
            "mismatch_list": [f"{t}.{k}" for t, k in bad][:40],
            "classes_viv": [len(g) for g in groups(pv)], "classes_oxc7": [len(g) for g in groups(po)]}


def by_type(s):
    return {re.sub(r"_X\d+Y\d+", "", f) for f in s}


def pins_by_site():
    m = {}
    with open(CONFIG["package_pins"]) as f:
        for r in csv.DictReader(f):
            x = re.search(r"Y(\d+)$", r["site"])
            t = re.search(r"_X(\d+)Y(\d+)$", r["tile"])
            if not (x and t):
                continue
            half = int(x[1]) - int(t[2])
            m[(f"X{t[1]}Y{t[2]}", 1 - half if r["tile"].startswith(("LIOB33_X", "RIOB33_X")) and "SING" not in r["tile"] else half)] = r["pin"]
    return m


def ports_by_pin():
    res = {}
    for ln in CONFIG["xdc"].read_text().splitlines():
        a = re.search(r"set_property LOC (\S+) \[get_ports \{([^}]+)\}\]", ln)
        if a:
            res[a[1]] = a[2]
    return res


def annotate(feature, pins, ports):
    tile, _, rest = feature.partition(".")
    xy = re.search(r"_(X\d+Y\d+)$", tile)
    half = re.search(r"_Y([01])\b", rest)
    if not (xy and half and re.match(r"^[LR]IO[BI]", tile)):
        return ""
    pin = pins.get((xy[1], int(half[1])), "")
    return f"{pin}:{ports.get(pin, 'unused')}" if pin else ""


def group(feature):
    tile = feature.split(".")[0]
    for name, rx in CONFIG["groups"]:
        if rx.match(tile):
            return name
    return None


def is_pip(feature):
    parts = feature.split(".")
    return len(parts) == 3 and not CONFIG["site_re"].match(parts[1])


def load(path):
    out = set()
    for ln in path.read_text().splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#") and not ln.startswith("{"):
            out.add(ln.split()[0])
    return out


def compare(viv_bit, oxc_bit, out):
    out.mkdir(parents=True, exist_ok=True)
    vf = gr.decode(viv_bit, out / "viv.fasm")
    of = gr.decode(oxc_bit, out / "oxc7.fasm")
    cv, co = out / "viv.canon.fasm", out / "oxc7.canon.fasm"
    gr.canon([(vf, cv), (of, co)])
    sv, so = load(cv), load(co)
    pins, ports = pins_by_site(), ports_by_pin()
    res = {"unknown_bits": {"viv": Counter(t for t, _ in gr.unknown_bits(vf)),
                            "oxc7": Counter(t for t, _ in gr.unknown_bits(of))}, "groups": {}}
    for g, _ in CONFIG["groups"]:
        a = {f for f in sv if group(f) == g}
        b = {f for f in so if group(f) == g}
        rec = {"common": len(a & b), "viv_only": len(a - b), "oxc7_only": len(b - a)}
        for kind, s in (("viv_only", a - b), ("oxc7_only", b - a)):
            rec[f"{kind}_list"] = [{"f": f, "pip": is_pip(f), "pin": annotate(f, pins, ports)} for f in sorted(s)]
            rec[f"{kind}_by_feature"] = dict(Counter(re.sub(r"_X\d+Y\d+", "", f) for f in s).most_common())
            rec[f"{kind}_sites"] = sum(not x["pip"] for x in rec[f"{kind}_list"])
        ta = {f for f in by_type(a) if not is_pip(f)}
        tb = {f for f in by_type(b) if not is_pip(f)}
        rec["by_type_nonpip"] = {"common": len(ta & tb), "viv_only": sorted(ta - tb), "oxc7_only": sorted(tb - ta)}
        res["groups"][g] = rec
    res["ioi_clock_equivalence"] = clock_equivalence(sv, so)
    (out / "fasm_compare.json").write_text(json.dumps(res, indent=1, default=dict) + "\n")
    return res


def main():
    ap = argparse.ArgumentParser(description="Decode our and Vivado's DDR3 bitstreams and diff the IO/clocking features")
    ap.add_argument("--variant", default=CONFIG["variant"])
    ap.add_argument("--viv-tag", default=CONFIG["viv_tag"])
    a = ap.parse_args()
    d, top = CONFIG["design"], CONFIG["top"]
    vsrc = CONFIG["win_build"] / a.viv_tag / d
    vdst = CONFIG["out_dir"] / d / f"viv_{a.viv_tag}"
    vdst.mkdir(parents=True, exist_ok=True)
    for pat in ("*.bit", "*.rpt", "times.txt", "status.txt", "worst_paths.txt"):
        for f in vsrc.glob(pat):
            shutil.copy2(f, vdst / f.name)
    for f in ("vivado.log", "version.txt"):
        if (vsrc.parent / f).exists():
            shutil.copy2(vsrc.parent / f, vdst / f)
    res = compare(vdst / f"{d}.bit", CONFIG["out_dir"] / d / a.variant / f"{top}.bit",
                  CONFIG["out_dir"] / d / f"cmp_{a.variant}_vs_{a.viv_tag}")
    print("unknown bits:", {k: sum(v.values()) for k, v in res["unknown_bits"].items()},
          {k: dict(v) for k, v in res["unknown_bits"].items()})
    for g, r in res["groups"].items():
        t = r["by_type_nonpip"]
        print(f"{g:9s} exact: common {r['common']:6d} viv-only {r['viv_only']:5d} ({r['viv_only_sites']} non-pip) "
              f"oxc7-only {r['oxc7_only']:5d} ({r['oxc7_only_sites']} non-pip) | by type, non-pip: common {t['common']} "
              f"viv-only {len(t['viv_only'])} oxc7-only {len(t['oxc7_only'])}")
        if g in ("IOB", "IOI", "HCLK_IOI", "CMT", "CLK_BUFG", "CLK_HROW", "HCLK_CMT"):
            for kind in ("viv_only", "oxc7_only"):
                c = Counter((re.sub(r"_X\d+Y\d+", "", x["f"]), x["pin"].split(":")[-1].split("[")[0])
                            for x in r[f"{kind}_list"] if not x["pip"])
                for (f, p), n in sorted(c.items()):
                    print(f"    exact {kind:9s} {n:3d}  {f}  [{p}]")
                for f in t[kind]:
                    print(f"    type  {kind:9s}      {f}")
    print("IOI clock-pin partition:", {k: v for k, v in res["ioi_clock_equivalence"].items() if k != "mismatch_list"})


if __name__ == "__main__":
    main()
