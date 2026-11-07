import collections
import csv
import json
import re
import sys
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "db": "toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7",
    "cells": "toolchain/oss-cad-suite/share/yosys/xilinx/cells_xtra.v",
    "out": "build/ofx/gt/audit.txt",
    "blocks": (
        ("GTPE2_CHANNEL", "segbits_gtp_channel_0.db", "GTP_CHANNEL_0.GTPE2_CHANNEL.", "mask_gtp_channel_0.db"),
        ("GTPE2_COMMON", "segbits_gtp_common.db", "GTP_COMMON.GTPE2_COMMON.", "mask_gtp_common.db"),
        ("IBUFDS_GTE2", "segbits_gtp_common.db", "GTP_COMMON.IBUFDS_GTE2_Y0.", None),
        ("PCIE_2_1", "segbits_pcie_bot.db", "PCIE_BOT.PCIE.", "mask_pcie_bot.db"),
    ),
    "sim_only": re.compile(r"^(SIM_|SIMULATION)"),
}


def unisim(mod, src):
    body = re.search(r"module %s\b(.*?)endmodule" % mod, src, re.S).group(1)
    out = collections.OrderedDict()
    for rng, name, val in re.findall(r"parameter\s+(\[[^\]]*\]\s*|integer\s+|real\s+)?(\w+)\s*=\s*([^;]+);", body):
        m = re.match(r"\[(\d+):(\d+)\]", rng.strip())
        width = int(m.group(1)) - int(m.group(2)) + 1 if m else None
        kind = "int" if rng.strip() == "integer" else "real" if rng.strip() == "real" else \
            "str" if val.strip().startswith('"') else "bits"
        out[name] = (kind, width, val.strip())
    return out


def segbits(path, prefix):
    feats = collections.defaultdict(set)
    bits = {}
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts or not parts[0].startswith(prefix):
            continue
        f = parts[0][len(prefix):]
        base, _, idx = f.partition("[")
        feats[base].add(idx.rstrip("]") if idx else "")
        bits[parts[0]] = parts[1:]
    return feats, bits


def pkg_survey(db):
    rows = []
    for d in sorted(db.iterdir()):
        f = d / "package_pins.csv"
        if not d.name.endswith("-1") or not f.exists():
            continue
        fn = [r["pin_function"] for r in csv.DictReader(open(f))]
        tx = sum(1 for p in fn if re.match(r"MGTPTXP\d", p))
        rc = sum(1 for p in fn if re.match(r"MGTREFCLK\dP", p))
        quads = sorted({p.rsplit("_", 1)[1] for p in fn if p.startswith("MGT")})
        rows.append((d.name[:-2], tx, rc, ",".join(quads) or "-"))
    return rows


def main():
    root = CONFIG["root"]
    db = root / CONFIG["db"]
    src = (root / CONFIG["cells"]).read_text()
    out = []
    for mod, sb, prefix, mask in CONFIG["blocks"]:
        params = unisim(mod, src)
        feats, bits = segbits(db / sb, prefix)
        have, missing, partial, simonly = [], [], [], []
        for n, (kind, width, val) in params.items():
            if CONFIG["sim_only"].match(n):
                simonly.append(n)
                continue
            alias = re.sub(r"^IS_(\w+)_INVERTED$", r"INV_\1", n)
            if n not in feats and alias in feats:
                have.append(n)
                continue
            if n not in feats and any(f.startswith(n + ".") for f in feats):
                have.append(n)
                continue
            if mod == "IBUFDS_GTE2" and n == "CLKSWING_CFG":
                have.append(n)
                continue
            if n not in feats:
                missing.append((n, kind, width, val))
                continue
            idx = feats[n]
            if kind == "bits" and width and "" not in idx:
                got = {int(i) for i in idx if i.isdigit()}
                if len(got) < width:
                    partial.append((n, width, sorted(set(range(width)) - got)))
            have.append(n)
        extra = sorted(f for f in feats if f not in params and f.split(".")[0] not in params
                       and re.sub(r"^INV_(\w+)$", r"IS_\1_INVERTED", f) not in params)
        nbits = len({b for v in bits.values() for b in v})
        mbits = len((db / mask).read_text().splitlines()) if mask else None
        out.append(f"== {mod} ({sb}, prefix {prefix})")
        out.append(f"  UNISIM parameters: {len(params)}; SIM_* (no bits expected): {len(simonly)}")
        out.append(f"  with segbits: {len(have)}; without: {len(missing)}; partially covered vectors: {len(partial)}")
        out.append(f"  segbit features: {len(bits)}; distinct bits: {nbits}; mask bits: {mbits}")
        for n, kind, width, val in missing:
            out.append(f"    MISSING {n} ({kind}{'' if width is None else f'[{width}]'} default {val})")
        for n, width, gone in partial:
            out.append(f"    PARTIAL {n}[{width}] missing bits {gone}")
        if extra:
            out.append(f"    non-UNISIM features ({len(extra)}): {' '.join(extra[:40])}{' ...' if len(extra) > 40 else ''}")
    out.append("== MGT pins bonded per part/package (speed grade -1)")
    out.append("  part             TX lanes  refclk pairs  quads")
    for name, tx, rc, q in pkg_survey(db):
        out.append(f"  {name:<16} {tx:>8}  {rc:>12}  {q}")
    p = root / CONFIG["out"]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
