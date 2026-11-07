import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_openxc7 import DB

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "family": "artix7",
    "out": "build/prjxray-db-prim",
    "drafts": ["docs/drafts/prjxray-db-diff-term.segbits", "docs/drafts/prjxray-db-cfg-in-use.segbits",
               "docs/drafts/prjxray-db-fifo.segbits"],
    "dry_run": True,
}

ROOT = CONFIG["root"]


def draft_lines():
    per_file = {}
    for d in CONFIG["drafts"]:
        p = ROOT / d
        if not p.exists():
            continue
        for ln in p.read_text().splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            ttype = ln.split(".", 1)[0]
            kind = "ppips" if d.endswith(".ppips") else "segbits"
            per_file.setdefault(f"{kind}_{ttype.lower()}.db", []).append(ln)
    return per_file


def build(dry):
    src = DB / CONFIG["family"]
    dst = ROOT / CONFIG["out"] / CONFIG["family"]
    per_file = draft_lines()
    for f, lines in per_file.items():
        print(f"{f}: +{len(lines)} lines")
    if dry:
        print(f"[dry] would link {src} into {dst} and write {len(per_file)} segbits files; add --run")
        return
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for p in src.iterdir():
        (dst / p.name).symlink_to(p.resolve(), target_is_directory=p.is_dir())
    for f, lines in per_file.items():
        base = (src / f).read_text() if (src / f).exists() else ""
        have = {ln.split()[0] for ln in base.splitlines() if ln.strip()}
        clash = [ln.split()[0] for ln in lines if ln.split()[0] in have]
        if clash:
            sys.exit(f"{f}: features already in prjxray-db: {clash[:4]}")
        (dst / f).unlink(missing_ok=True)
        (dst / f).write_text(base + "".join(ln + "\n" for ln in lines))
    print(f"wrote {dst}")


def main():
    ap = argparse.ArgumentParser(description="prjxray-db copy (symlinks) with the draft segbits of docs/drafts appended")
    ap.add_argument("--out", default=CONFIG["out"], help="output root (default %(default)s)")
    ap.add_argument("--extra", nargs="*", default=[], help="more segbits drafts, e.g. docs/drafts/prjxray-db-xadc-init.segbits")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    CONFIG["out"] = a.out
    CONFIG["drafts"] = CONFIG["drafts"] + a.extra
    build(CONFIG["dry_run"] and not a.run)


if __name__ == "__main__":
    main()
