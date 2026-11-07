import argparse
import json
import sys
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "viv_tags": ("gap", "gap2", "gap3", "gap4", "gap5"),
    "before": "oxc7",
    "after": "gapfix",
    "stages": ("synth", "pnr", "fasm", "bitstream"),
    "skip_prefix": ("xadc_fz_",),
}

ROOT = CONFIG["root"]
GAP = ROOT / "build" / "gap"


def first_fail(st):
    for k in CONFIG["stages"]:
        s = st.get("stages", {}).get(k)
        if s is None:
            return k, "-"
        if not s.get("ok"):
            return k, s.get("error", "")
    return None, ""


def cell(name, tag):
    d = GAP / name
    stf = d / tag / "status.json"
    if not stf.exists():
        return "-", None, ""
    st = json.loads(stf.read_text())
    fail, err = first_fail(st)
    sfx = "" if tag == "oxc7" else f"_{tag}"
    rep = d / f"report{sfx}.json"
    diff = json.loads(rep.read_text()).get("diff") if rep.exists() else None
    if fail and not (fail == "pnr" and (d / tag / f"{name}.bit").exists()):
        return f"**FAIL** ({fail})", None, err
    return "ok", diff, ""


def fmt(diff):
    if not diff:
        return "-"
    e, t = diff["exact"], diff["by_tile_type"]
    return f"{e['viv_only']} / {e['oxc7_only']} ({t['viv_only']} / {t['oxc7_only']})"


def main():
    ap = argparse.ArgumentParser(description="before/after table of openXC7 gap builds against Vivado")
    ap.add_argument("--before", default=CONFIG["before"])
    ap.add_argument("--after", default=CONFIG["after"])
    ap.add_argument("--out", default=str(GAP / "before_after.md"))
    a = ap.parse_args()
    order = []
    for t in CONFIG["viv_tags"]:
        for f in (GAP / f"summary_{t}.json", GAP / f"summary_{t}_{a.after}.json"):
            if f.exists():
                order += [r["design"] for r in json.loads(f.read_text()) if r["design"] not in order]
    order = [n for n in order if not n.startswith(CONFIG["skip_prefix"])]
    rows = [f"| design | before ({a.before}) | diff before | after ({a.after}) | diff after |", "|---|---|---|---|---|"]
    notes = []
    for n in order:
        sb, db, eb = cell(n, a.before)
        sa, da, ea = cell(n, a.after)
        rows.append(f"| {n} | {sb} | {fmt(db)} | {sa} | {fmt(da)} |")
        if ea:
            notes.append(f"- {n} after: {ea}")
    text = "\n".join(rows) + "\n\n" + "\n".join(notes) + "\n"
    Path(a.out).write_text(text)
    print(text)


if __name__ == "__main__":
    sys.exit(main())
