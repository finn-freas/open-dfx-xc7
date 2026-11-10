"""Table of Vivado's timer on DFX builds (flow/dfx_exact_vivado.sh outputs, slack.txt): Fmax overall and without
ICAPE2 paths, at the export period, per name. Usage: dfx_exact_table.py [NAME...] (default: every result)."""
import re
import sys
from pathlib import Path

OUT = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/dfx_exact")


def fmax(period, wns):
    return round(1000.0 / (period - wns), 2)


def main():
    names = sys.argv[1:] or sorted(p.name for p in OUT.iterdir() if (p / "slack.txt").exists())
    print("| build | period ns | Vivado Fmax all | Vivado Fmax without ICAPE2 | worst path without ICAPE2 |")
    print("|---|---|---|---|---|")
    for n in names:
        f = OUT / n / "slack.txt"
        if not f.exists():
            print(f"| {n} | | not run | | |")
            continue
        t = dict(l.split(None, 1) for l in f.read_text().splitlines() if " " in l)
        period = float(re.search(r"_p([\d.]+)$", n).group(1))
        wns, wnsn = float(t["wns"]), float(t["wns_noicap"])
        print(f"| {n} | {period:g} | {fmax(period, wns)} | {fmax(period, wnsn)} | {t.get('noicap_path', '').strip()} |")


if __name__ == "__main__":
    main()
