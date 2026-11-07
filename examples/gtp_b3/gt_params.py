import re
import sys
from pathlib import Path

CONFIG = {
    "cells": Path(__file__).resolve().parents[2] / "toolchain/oss-cad-suite/share/yosys/xilinx/cells_xtra.v",
}


def params(mod):
    src = CONFIG["cells"].read_text()
    body = re.search(r"module %s\b(.*?)endmodule" % mod, src, re.S).group(1)
    return [(n, v.strip()) for _, n, v in
            re.findall(r"parameter\s+(\[[^\]]*\]\s*|integer\s+|real\s+)?(\w+)\s*=\s*([^;]+);", body)]


def main():
    mod, over = sys.argv[1], dict(a.split("=", 1) for a in sys.argv[2:])
    ps = params(mod)
    unknown = set(over) - {n for n, _ in ps}
    if unknown:
        sys.exit(f"{mod}: no parameter(s) {sorted(unknown)}")
    print(",\n".join(f"        .{n}({over.get(n, v)})" for n, v in ps))


if __name__ == "__main__":
    main()
