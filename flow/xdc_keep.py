"""KEEP, DONT_TOUCH and MARK_DEBUG for yosys, as Vivado's synthesis applies them.

Vivado reads the XDC before synthesis, so `set_property DONT_TOUCH|KEEP true [get_cells x_reg[*]]` or
`[get_nets x]` keeps those registers and nets through optimisation, and an RTL `(* mark_debug = "true" *)`
keeps its net. The open flow reads the XDC only in nextpnr, after synthesis, where nothing can be kept any more.
This module turns those properties into yosys commands run on the flattened design before synth_xilinx's
optimisation (`synth_xilinx -run :prepare; proc; flatten; <these>; synth_xilinx -run prepare:`):
each named wire, and the cells that drive it, get `keep`.

Names: a Vivado register `a/b/q_reg[3]` is the flattened yosys wire `a.b.q` (the whole wire is kept, every bit);
a net `a/b/n` is `a.b.n`. Globs (`*`) are passed to yosys's select. A name that matches nothing in yosys is a
warning in the yosys log (select -list), as in Vivado.
"""
import re
import sys
from pathlib import Path

CONFIG = {
    "props": ("KEEP", "DONT_TOUCH", "MARK_DEBUG"),
    "true": ("true", "1", "yes"),
    "rtl_attr_re": re.compile(r"\(\*[^)]*\b(mark_debug|dont_touch)\s*=\s*\"?(true|1|yes)\"?", re.IGNORECASE),
    "prop_re": re.compile(r"^\s*set_property\s+(?:-dict\s+)?(.*)$"),
}


def tcl_words(s):
    out, cur, depth = [], "", 0
    for ch in s:
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        if ch.isspace() and depth == 0:
            if cur:
                out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def xdc_targets(text):
    found = []
    joined = re.sub(r"\\\n", " ", text)
    for lineno, line in enumerate(joined.splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line.startswith("set_property"):
            continue
        w = tcl_words(line)
        if len(w) < 4:
            continue
        if w[1] == "-dict":
            kv = tcl_words(w[2].strip("{}"))
            pairs = list(zip(kv[0::2], kv[1::2]))
            target = w[3]
        else:
            pairs = [(w[1], w[2])]
            target = w[3]
        props = [p.upper() for p, v in pairs if p.upper() in CONFIG["props"] and v.strip('"').lower() in CONFIG["true"]]
        if not props:
            continue
        m = re.fullmatch(r"\[\s*(get_cells|get_nets)\s+(.*)\]", target.strip())
        if not m:
            continue
        kind, rest = m.group(1), m.group(2)
        names = [n for n in tcl_words(rest.strip()) if not n.startswith("-")]
        flat = []
        for n in names:
            flat += tcl_words(n.strip("{}")) if n.startswith("{") else [n]
        for n in flat:
            found.append((lineno, props, kind, n))
    return found


def yosys_wire(kind, name):
    n = name.strip("{}\"")
    n = re.sub(r"\[[^\]]*\]$", "", n)
    if kind == "get_cells":
        n = re.sub(r"_reg$", "", n)
        n = n.replace("_reg/", "/")
    return n.replace("/", ".")


def commands(rtl_files, xdc_file):
    """yosys commands for the flattened design, or None when nothing asks for KEEP/DONT_TOUCH/MARK_DEBUG"""
    cmds = []
    xdc = Path(xdc_file).read_text(errors="replace") if xdc_file else ""
    for lineno, props, kind, name in xdc_targets(xdc):
        w = yosys_wire(kind, name)
        sel = f"w:{w}" if not any(c in w for c in " ") else f"w:{w.split()[0]}"
        cmds.append(f"select -list {sel}")
        cmds.append(f"setattr -set keep 1 {sel} {sel} %ci1 %u")
    if any(CONFIG["rtl_attr_re"].search(Path(f).read_text(errors="replace")) for f in rtl_files):
        for a in ("mark_debug", "dont_touch"):
            for v in ("true", "TRUE", "1"):
                sel = f'w:* a:{a}={v} %i'
                cmds.append(f"setattr -set keep 1 {sel} {sel} %ci1 %u")
    if not cmds:
        return None
    return ["proc", "flatten"] + cmds


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("xdc")
    ap.add_argument("rtl", nargs="*")
    a = ap.parse_args()
    c = commands(a.rtl, a.xdc)
    print("; ".join(c) if c else "(nothing to keep)")


if __name__ == "__main__":
    sys.exit(main())
