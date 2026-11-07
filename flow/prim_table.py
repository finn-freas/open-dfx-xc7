import argparse
import json
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "results": "build/gap/prim_eval_ofx-prim.json",
    "out": "build/gap/prim_table.md",
    "base": "ofx",
    "variant": "ofx-prim",
}

ROOT = CONFIG["root"]


def stage(r, v):
    st = r.get(f"stages_{v}") or {}
    if not st:
        return "-"
    failed = next((k for k, ok in st.items() if ok is False), None)
    return f"**FAIL** ({failed})" if failed else "ok"


def diff(r, v):
    d = r.get(f"diff_{v}")
    if not d:
        return "-"
    e, t = d["exact"], d["by_tile_type"]
    return f"{len(e['viv_only'])} / {len(e['oxc7_only'])} ({len(t['viv_only'])} / {len(t['oxc7_only'])})"


def main():
    ap = argparse.ArgumentParser(description="markdown table of flow/prim_eval.py results")
    ap.parse_args()
    rows = json.loads((ROOT / CONFIG["results"]).read_text())
    b, v = CONFIG["base"], CONFIG["variant"]
    out = [f"| design | Vivado tag | Vivado unknown bits (draft db) | {b} | {b} vs Vivado exact (by type) | {v} | "
           f"{v} vs Vivado exact (by type) | .frames {v} = {b} |",
           "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda x: x["design"]):
        same = r.get("frames_identical_to_base")
        out.append(f"| {r['design']} | {r.get('viv_tag') or '-'} | {r.get('viv_unknown_bits', '-')} | {stage(r, b)} | "
                   f"{diff(r, b)} | {stage(r, v)} | {diff(r, v)} | {'-' if same is None else ('yes' if same else 'no')} |")
    (ROOT / CONFIG["out"]).write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
