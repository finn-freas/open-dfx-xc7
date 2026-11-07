import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gap_report

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "tile_type": "MONITOR_BOT",
    "nbits": 9,
    "regs": list(range(0x40, 0x60)),
    "check": {"xadc": {0x40: 0x0003, 0x41: 0x2000, 0x42: 0x0400, 0x48: 0x0100}},
    "out": "docs/drafts/prjxray-db-xadc-init.segbits",
    "evidence": "build/gap/xadc_segbits.json",
}

ROOT = CONFIG["root"]


def bits(name):
    rep = json.loads((ROOT / "build" / "gap" / name / "report.json").read_text())
    vf = ROOT / "build" / "gap" / name / "viv" / f"{name}.viv.fasm"
    return {(t, b) for t, b in gap_report.unknown_bits(vf)}, rep["viv"]["unknown_bits"]


def main():
    allb, n_all = bits("xadc_fz_all")
    noneb, n_none = bits("xadc_fz_none")
    init = sorted(b for b in allb - noneb)
    code = defaultdict(int)
    per_k = {}
    for k in range(CONFIG["nbits"]):
        kb, _ = bits(f"xadc_fz_{k}")
        per_k[k] = len(kb - noneb)
        for b in kb - noneb:
            code[b] |= 1 << k
    rev = defaultdict(list)
    for b in init:
        rev[code[b]].append(b)
    collisions = {j: v for j, v in rev.items() if len(v) != 1}
    mapping = {}
    for j, v in rev.items():
        if len(v) == 1:
            reg, bit = CONFIG["regs"][0] + j // 16, j % 16
            mapping[(reg, bit)] = v[0]
    tiles = {t for t, _ in init}
    lines = []
    for (reg, bit), (tile, segbit) in sorted(mapping.items()):
        lines.append(f"{CONFIG['tile_type']}.XADC.INIT_{reg:02X}[{bit}] {segbit}")
    checks = {}
    for name, regs in CONFIG["check"].items():
        got, _ = bits(name)
        want = {mapping[(r, b)] for r, v in regs.items() for b in range(16) if (v >> b) & 1 and (r, b) in mapping}
        checks[name] = {"expected_bits": len(want), "match": sorted(got - noneb) == sorted(want),
                        "observed_minus_base": len(got - noneb)}
    ev = {"all_unknown": n_all, "none_unknown": n_none, "base_bits": sorted(f"{t}:{b}" for t, b in noneb),
          "init_bits": len(init), "tiles": sorted(tiles), "per_k": per_k, "mapped": len(mapping),
          "collisions": {str(j): [f"{t}:{b}" for t, b in v] for j, v in collisions.items()}, "checks": checks}
    (ROOT / CONFIG["evidence"]).write_text(json.dumps(ev, indent=1) + "\n")
    (ROOT / CONFIG["out"]).write_text("\n".join(lines) + "\n")
    print(json.dumps(ev, indent=1))
    print(f"wrote {len(lines)} segbits to {CONFIG['out']}")


if __name__ == "__main__":
    main()
