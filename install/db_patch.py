import argparse
import hashlib
import sys
from pathlib import Path

CONFIG = {
    "dry_run": True,
    "series": Path(__file__).resolve().parent / "patches" / "prjxray-db" / "SERIES",
}


def series(path):
    out = []
    for ln in Path(path).read_text().splitlines():
        if ln.strip() and not ln.startswith("#"):
            fam, name = ln.split()
            out.append((fam, Path(path).parent / name))
    return out


def additions(files):
    per_file = {}
    for f in files:
        kind = "ppips" if f.suffix == ".ppips" else "segbits"
        for ln in f.read_text().splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            ttype = ln.split(".", 1)[0]
            per_file.setdefault(f"{kind}_{ttype.lower()}.db", []).append(ln)
    return per_file


def patch_family(db, files, dry):
    for name, lines in sorted(additions(files).items()):
        target = db / name
        base = target.read_text() if target.exists() else ""
        have = {ln.split()[0] for ln in base.splitlines() if ln.strip()}
        clash = [ln.split()[0] for ln in lines if ln.split()[0] in have]
        if clash:
            sys.exit(f"{target}: features already in the database: {clash[:4]}")
        print(f"[{'dry' if dry else 'run'}] {target}: +{len(lines)} lines{'' if target.exists() else ' (new file)'}")
        if not dry:
            target.write_text(base + "".join(ln + "\n" for ln in lines))


def main():
    ap = argparse.ArgumentParser(description="append the prjxray-db additions of install/patches/prjxray-db to an "
                                             "installed prjxray-db copy (refuses a feature the database already has)")
    ap.add_argument("db", help="prjxray-db root with one directory per family")
    ap.add_argument("--series", default=str(CONFIG["series"]))
    ap.add_argument("--key", action="store_true", help="print the sha256 of the series and its files, then exit")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    items = series(a.series)
    if a.key:
        h = hashlib.sha256(Path(a.series).read_bytes())
        for _, f in items:
            h.update(f.read_bytes())
        print(h.hexdigest())
        return
    dry = CONFIG["dry_run"] and not a.run
    root = Path(a.db)
    for fam in sorted({fam for fam, _ in items}):
        if not (root / fam).is_dir():
            print(f"[skip] {root / fam}: family not installed")
            continue
        patch_family(root / fam, [f for g, f in items if g == fam], dry)


if __name__ == "__main__":
    main()
