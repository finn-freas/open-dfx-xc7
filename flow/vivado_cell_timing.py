import argparse
import collections
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "arcs": [Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/qor_arcs3")],
    "out": ROOT / "build" / "chipdb-cal" / "cell_timing_xc7a35t_1.json",
    "report": ROOT / "build" / "chipdb-cal" / "cell_timing_xc7a35t_1.txt",
    "dry_run": True,
    "ff_types": {"FDRE", "FDSE", "FDCE", "FDPE"},
}


def read_arcs(dirs):
    rows = []
    for d in dirs:
        for f in sorted(d.glob("*/arcs.txt")):
            for ln in f.read_text(errors="replace").splitlines():
                p = ln.split()
                if len(p) not in (11, 12, 13) or p[0] != "ARC":
                    continue
                _, ref, frm, to, belpin, typ, bel, *vals = p[:11]
                nums = [float(v) for v in vals if v != "-"]
                if len(nums) != 4:
                    continue
                smr, smf, fmr, fmf = nums
                rows.append({"ref": ref, "from": frm, "to": to, "belpin": belpin, "type": typ.replace("_", " "),
                             "bel": bel, "slow_max": max(smr, smf), "fast_min": min(fmr, fmf), "src": f.parent.name,
                             "ext": int(p[11]) if len(p) > 11 else None, "sense": p[12] if len(p) > 12 else None})
    return rows


def ps(x):
    return int(round(x * 1000))


def med(rs, key):
    return statistics.median(r[key] for r in rs)


def build(rows):
    lut = collections.defaultdict(list)
    ff = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        if r["ref"].startswith("LUT") and r["type"] == "combinational":
            if r["belpin"].startswith("A") and r["belpin"][1:].isdigit():
                lut["O5" if r["bel"].endswith("5LUT") else "O6"].append(r)
        if r["ref"] in CONFIG["ff_types"]:
            side = "ext" if r["ext"] else "int"
            if r["from"] == "C" and r["to"] == "Q":
                ff["CK_Q"]["int"].append(r)
            for pin in ("D", "CE"):
                if r["to"] == pin and "setup" in r["type"]:
                    ff[f"{pin}_setup"][side].append(r)
    cal = {"lut": {}, "ff": {}, "site_pips": {}}
    lines = []
    for out, npins in (("O6", 6), ("O5", 5)):
        rs = lut[out]
        if not rs:
            continue
        hi = statistics.mean(r["slow_max"] for r in rs)
        lo = statistics.mean(r["fast_min"] for r in rs)
        for i in range(1, npins + 1):
            cal["lut"][f"A{i}_{out}"] = [ps(lo), ps(hi)]
        fast = sum(1 for r in rs if r["slow_max"] < 0.2)
        lines.append(f"lut {out}: n={len(rs)} arcs, slow_max mean {hi:.3f} (median {med(rs, 'slow_max'):.3f}, "
                     f"{fast} below 0.2 ns, {len(rs) - fast} at 0.2 ns or more), fast_min mean {lo:.3f}")
        by_pin = collections.defaultdict(list)
        for r in rs:
            by_pin[r["belpin"]].append(r["slow_max"])
        lines.append(f"lut {out} slow_max mean per bel pin: " +
                     ", ".join(f"{p} {statistics.mean(v):.3f}" for p, v in sorted(by_pin.items())))
    ck = ff["CK_Q"]["int"]
    if ck:
        cal["ff"]["CK_Q"] = [ps(med(ck, "fast_min")), ps(med(ck, "slow_max"))]
        lines.append(f"ff CK_Q: n={len(ck)} slow_max median {med(ck, 'slow_max'):.3f} "
                     f"(min {min(r['slow_max'] for r in ck):.3f}, max {max(r['slow_max'] for r in ck):.3f})")
    i, e = ff["D_setup"]["int"], ff["D_setup"]["ext"]
    if i:
        cal["ff"]["D_setup"] = [max(ps(med(i, "fast_min")), 1), max(ps(med(i, "slow_max")), 1)]
        lines.append(f"ff D_setup, D from the slice's own LUT: n={len(i)} slow_max median {med(i, 'slow_max'):.3f} "
                     f"(clamped to >= 1 ps)")
    if i and e:
        lo = med(e, "fast_min") - med(i, "fast_min")
        hi = med(e, "slow_max") - med(i, "slow_max")
        cal["site_pips"]["SLICE_FF_BYPASS"] = [max(ps(lo), 1), max(ps(hi), 1)]
        lines.append(f"ff D_setup, D from outside the slice (AX..DX bypass): n={len(e)} slow_max median "
                     f"{med(e, 'slow_max'):.3f}; difference {hi:.3f} goes on the SLICE_FF_BYPASS site pip")
    ce = max((ff["CE_setup"]["int"], ff["CE_setup"]["ext"]), key=len)
    if ce:
        cal["ff"]["CE_setup"] = [max(ps(med(ce, "fast_min")), 1), max(ps(med(ce, "slow_max")), 1)]
        lines.append(f"ff CE_setup: n={len(ce)} slow_max median {med(ce, 'slow_max'):.3f}")
    return cal, lines


def main():
    ap = argparse.ArgumentParser(description="LUT and FF delays from Vivado timing arcs (vivado/build_arcs.tcl) "
                                             "as a --cell-timing file for the nextpnr-xilinx chipdb generator")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    rows = read_arcs(CONFIG["arcs"])
    cal, lines = build(rows)
    print(f"{len(rows)} arcs from {', '.join(str(d) for d in CONFIG['arcs'])}")
    print("\n".join(lines))
    if CONFIG["dry_run"] and not a.run:
        print(f"[dry] would write {CONFIG['out']}")
        return
    CONFIG["out"].parent.mkdir(parents=True, exist_ok=True)
    CONFIG["out"].write_text(json.dumps(cal, indent=1, sort_keys=True) + "\n")
    CONFIG["report"].write_text("\n".join(lines) + "\n")
    print(f"wrote {CONFIG['out']}")


if __name__ == "__main__":
    main()
