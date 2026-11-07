import argparse
import contextlib
import importlib.machinery
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import device

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "part": device.get("part"),
    "family": device.get("family"),
}

OXC7 = CONFIG["root"] / "toolchain" / "openxc7"
DB = device.db_root() / CONFIG["family"]


def load_bit2fasm():
    path = str(OXC7.resolve() / "libexec" / "bit2fasm")
    loader = importlib.machinery.SourceFileLoader("bit2fasm_mod", path)
    spec = importlib.util.spec_from_loader("bit2fasm_mod", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description="bit to fasm via prjxray-db, without bit2fasm's shell call")
    ap.add_argument("bit")
    ap.add_argument("out")
    ap.add_argument("--frame-range")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--db-root", help="prjxray-db family directory (default: the toolchain's)")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        print(f"[skip] {out} exists")
        return
    db = Path(a.db_root) if a.db_root else DB
    part_yaml = db / CONFIG["part"] / "part.yaml"
    with tempfile.NamedTemporaryFile(suffix=".bits") as bits:
        cmd = [str(OXC7 / "bin" / "bitread"), "--part_file", str(part_yaml), "-o", bits.name, "-z", "-y"]
        if a.frame_range:
            cmd += ["-F", a.frame_range]
        subprocess.run(cmd + [a.bit], check=True)
        mod = load_bit2fasm()
        with open(out, "w") as f, contextlib.redirect_stdout(f):
            mod.bits_to_fasm(str(db), CONFIG["part"], bits.name, a.verbose, False)
    print(f"wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
