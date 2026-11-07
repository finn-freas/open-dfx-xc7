import json
import re
import sys
from pathlib import Path

CONFIG = {
    "cells": Path(__file__).resolve().parent.parent / "toolchain/oss-cad-suite/share/yosys/xilinx/cells_xtra.v",
    "prims": ("GTPE2_CHANNEL", "GTPE2_COMMON", "PCIE_2_1"),
}


def literal(rng, kind, val):
    val = val.strip()
    if val.startswith('"'):
        s = val.strip('"')
        return s + " " if s and re.fullmatch(r"[01xz]+", s) else s
    m = re.match(r"\[(\d+):(\d+)\]", rng.strip())
    width = int(m.group(1)) - int(m.group(2)) + 1 if m else 32
    m = re.fullmatch(r"(\d+)'([bhdBHD])([0-9a-fA-F_xzXZ]+)", val)
    if m:
        width = int(m.group(1)) if not rng.strip().startswith("[") else width
        n = int(m.group(3).replace("_", ""), {"b": 2, "h": 16, "d": 10}[m.group(2).lower()])
    elif re.fullmatch(r"-?\d+", val):
        n = int(val)
    else:
        raise ValueError(f"unsupported default {val!r}")
    return format(n & ((1 << width) - 1), f"0{width}b")


def defaults(prim, src):
    body = re.search(r"module %s\b(.*?)endmodule" % prim, src, re.S).group(1)
    out = {}
    for rng, name, val in re.findall(r"parameter\s+(\[[^\]]*\]\s*|integer\s+|real\s+)?(\w+)\s*=\s*([^;]+);", body):
        if rng.strip() == "real":
            continue
        out[name] = literal(rng, None, val)
    return out


def main():
    path = Path(sys.argv[1])
    d = json.loads(path.read_text())
    src = CONFIG["cells"].read_text()
    table, added = {}, 0
    for mod in d.get("modules", {}).values():
        for cell in mod.get("cells", {}).values():
            t = cell.get("type")
            if t not in CONFIG["prims"]:
                continue
            if t not in table:
                table[t] = defaults(t, src)
            params = cell.setdefault("parameters", {})
            for n, v in table[t].items():
                if n not in params:
                    params[n] = v
                    added += 1
    if table:
        path.write_text(json.dumps(d, indent=2) + "\n")
    print(f"gt_json_defaults: {sum(1 for _ in table)} primitive type(s), {added} parameter(s) added")


if __name__ == "__main__":
    main()
