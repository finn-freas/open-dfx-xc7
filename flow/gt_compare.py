import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import device_vivado_compare as dvc

CONFIG = {
    "tiles": re.compile(r"^(GTP_CHANNEL_\d|GTP_COMMON|GTP_INT_INTERFACE|PCIE_BOT|PCIE_TOP|PCIE_INT_INTERFACE)"),
}


def group(feats):
    tiles = collections.defaultdict(lambda: collections.defaultdict(set))
    for f in feats:
        tile, _, rest = f.partition(".")
        if not CONFIG["tiles"].match(tile):
            continue
        m = re.match(r"(.*)\[(\d+)\]$", rest)
        if m:
            tiles[tile][m.group(1)].add(int(m.group(2)))
        else:
            tiles[tile][rest].add(None)
    return tiles


def val(bits):
    if None in bits:
        return "set"
    return hex(sum(1 << b for b in bits))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("part")
    ap.add_argument("ours")
    ap.add_argument("vivado")
    ap.add_argument("outdir")
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    fo, uo = dvc.fasm(Path(a.ours), a.part, out / "ours.fasm")
    fv, uv = dvc.fasm(Path(a.vivado), a.part, out / "vivado.fasm")
    go, gv = group(fo), group(fv)
    rows, summary = [], collections.Counter()
    for tile in sorted(set(go) | set(gv)):
        ao, av = go.get(tile, {}), gv.get(tile, {})
        for attr in sorted(set(ao) | set(av)):
            o, v = ao.get(attr), av.get(attr)
            if o == v:
                summary["equal"] += 1
                continue
            kind = "only_ours" if v is None else "only_vivado" if o is None else "differs"
            summary[kind] += 1
            rows.append({"tile": tile, "attr": attr, "kind": kind,
                         "ours": None if o is None else val(o), "vivado": None if v is None else val(v)})
    res = {"part": a.part, "unknown_bits": {"ours": uo, "vivado": uv}, "summary": dict(summary), "rows": rows,
           "tiles_ours": sorted(go), "tiles_vivado": sorted(gv)}
    (out / "gt_compare.json").write_text(json.dumps(res, indent=1))
    lines = [f"part {a.part}; unknown bits ours {uo} vivado {uv}; attributes equal {summary['equal']}, "
             f"differ {summary['differs']}, only ours {summary['only_ours']}, only vivado {summary['only_vivado']}"]
    for r in rows:
        lines.append(f"  {r['kind']:<12} {r['tile']}.{r['attr']}: ours {r['ours']} vivado {r['vivado']}")
    (out / "gt_compare.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
