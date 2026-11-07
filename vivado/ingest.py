import argparse
import shutil
import sys
from pathlib import Path

CONFIG = {
    "win_work": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "dest": Path(__file__).resolve().parent.parent / "build" / "vivado",
    "keep": ("*.bit", "*.ll", "*.rpt", "vivado.log", "version.txt"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design")
    a = ap.parse_args()
    src = CONFIG["win_work"] / a.design
    if not src.is_dir():
        sys.exit(f"no Vivado output at {src}")
    dst = CONFIG["dest"] / a.design
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for pat in CONFIG["keep"]:
        for f in src.glob(pat):
            target = dst / f.name
            if target.exists() and target.stat().st_mtime >= f.stat().st_mtime:
                continue
            shutil.copy2(f, target)
            n += 1
    print(f"copied {n} files to {dst}")
    v = dst / "version.txt"
    if v.exists():
        print(v.read_text().strip().splitlines()[0])


if __name__ == "__main__":
    main()
