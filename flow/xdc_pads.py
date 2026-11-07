"""Pad buffer delays per I/O standard, drive and slew, from Vivado's timing arcs (docs/xdc-coverage.md, xdc4).

vivado/build_xdc4.tcl writes pad_arcs.txt for x_pad_a / x_pad_b: for every port, its IBUF/OBUF/IBUFDS/OBUFDS cell's
timing arcs with DELAY_{SLOW,FAST}_{MAX,MIN}_{RISE,FALL}. This prints, per key, the Slow-corner max delay (the worse of
rise and fall, the value report_timing uses for setup at the Slow corner), whether it differs between pins of one
key, and the C++ table lines for the nextpnr xdc4 draft (keys as nextpnr builds them: input "STD", output
"STD/DRIVE/SLEW" with DRIVE 12 when the standard takes none).
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

CONFIG = {
    "vivado": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/xdc4"),
    "designs": ["x_pad_a", "x_pad_b"],
    "line": re.compile(r"port (\S+) cell (\S+) ref (\S+) site (\S*) iostd (\S*) drive (\S*) slew (\S*) from (\S+) to (\S+) (.*)"),
}


def read(d):
    rows = []
    f = CONFIG["vivado"] / d / "pad_arcs.txt"
    if not f.exists():
        return rows
    for ln in f.read_text().splitlines():
        m = CONFIG["line"].match(ln)
        if not m:
            continue
        port, cell, ref, site, std, drive, slew, frm, to, rest = m.groups()
        vals = {k: (float(v) if v not in ("", "{}") else None) for k, v in (kv.split("=", 1) for kv in rest.split())}
        rows.append({"port": port, "ref": ref, "site": site, "std": std, "drive": drive, "slew": slew,
                     "from": frm.split("/")[-1], "to": to.split("/")[-1], **vals})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", help="write the table here")
    a = ap.parse_args()
    table = {"input": defaultdict(list), "output": defaultdict(list)}
    for d in CONFIG["designs"]:
        for r in read(d):
            if r["ref"] in ("BUFG", "BUFGCTRL") or r["from"] not in ("I",) or r["to"] not in ("O",):
                continue
            smax = [v for v in (r.get("DELAY_SLOW_MAX_RISE"), r.get("DELAY_SLOW_MAX_FALL")) if v is not None]
            if not smax:
                continue
            if r["ref"].startswith("IBUF"):
                if r["port"].startswith("clk"):
                    continue
                key, kind = r["std"], "input"
            else:
                drive = r["drive"] if r["drive"] not in ("", "{}") else "12"
                key, kind = f"{r['std']}/{drive}/{r['slew'] or 'SLOW'}", "output"
            table[kind][key].append((max(smax), r["port"], r["site"], r))
    out = {}
    for kind in ("input", "output"):
        print(f"{kind}:")
        for key in sorted(table[kind]):
            vs = table[kind][key]
            v = max(x[0] for x in vs)
            spread = max(x[0] for x in vs) - min(x[0] for x in vs)
            r = vs[0][3]
            print(f"  {key:24s} {v:.3f}  (rise {r.get('DELAY_SLOW_MAX_RISE')}, fall {r.get('DELAY_SLOW_MAX_FALL')}; "
                  f"{len(vs)} pin(s), spread {spread:.3f}; {', '.join(x[1] + '@' + x[2] for x in vs)})")
            out.setdefault(kind, {})[key] = round(v, 3)
    for kind in ("input", "output"):
        items = ", ".join(f'{{"{k}", {v:.3f}}}' for k, v in sorted(out.get(kind, {}).items()))
        print(f"static const dict<std::string, double> {kind}_ns = {{{items}}};")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
