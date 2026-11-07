import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples" / "gtp_b3"))
import gt_params

CONFIG = {
    "prims": ("GTPE2_CHANNEL", "GTPE2_COMMON", "PCIE_2_1"),
}


def fill(src):
    added = {}
    for prim in CONFIG["prims"]:
        defaults = gt_params.params(prim)
        pos = 0
        while True:
            m = re.compile(r"\b%s\s*#\s*\(" % prim).search(src, pos)
            if not m:
                break
            depth, i = 1, m.end()
            while depth:
                depth += {"(": 1, ")": -1}.get(src[i], 0)
                i += 1
            body = src[m.end():i - 1]
            have = set(re.findall(r"\.(\w+)\s*\(", body))
            miss = [(n, v) for n, v in defaults if n not in have]
            if miss:
                extra = "".join(",\n        .%s(%s)" % (n, v) for n, v in miss)
                body = body.rstrip() + extra + "\n    "
                src = src[:m.end()] + body + src[i - 1:]
            added.setdefault(prim, []).append([n for n, _ in miss])
            pos = m.end() + len(body)
    return src, added


def main():
    src, added = fill(Path(sys.argv[1]).read_text())
    Path(sys.argv[2]).write_text(src)
    for prim, lists in added.items():
        for k, names in enumerate(lists):
            print(f"{prim}#{k}: added {len(names)} defaults: {' '.join(names)}")


if __name__ == "__main__":
    main()
