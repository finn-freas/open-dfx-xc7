import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_openxc7
import device

CONFIG = {
    "part": device.get("part"),
    "carry_suffix": "$split$muxcy0$PACKED_CARRY4$",
    "lanes": "ABCD",
}


def main():
    ap = argparse.ArgumentParser(description="Pin the cells nextpnr's carry packer creates (CARRY4, DI/S feed-through "
                                             "LUTs) to the carry slices rm_place chose; append to a preplaced file")
    ap.add_argument("linked_json")
    ap.add_argument("xdc")
    ap.add_argument("placed_rm_json", help="rm_place output (its CARRY4 BEL attributes)")
    ap.add_argument("preplaced", help="RM preplaced file to append to")
    ap.add_argument("--prefix", default="u_rm.")
    a = ap.parse_args()
    rm = [v for v in json.loads(Path(a.placed_rm_json).read_text())["modules"].values() if v.get("cells")]
    c4_bel = {}
    for mod in rm:
        for n, c in mod["cells"].items():
            if c["type"] == "CARRY4" and "BEL" in c["attributes"]:
                c4_bel[a.prefix + n] = c["attributes"]["BEL"]
    if not c4_bel:
        print("packer_pins: no CARRY4 in this RM")
        return
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "packed.json"
        r = subprocess.run([build_openxc7.tool("nextpnr-xilinx"), "--device", CONFIG["part"], "--json", a.linked_json,
                            "-o", f"xdc={a.xdc}", "--pack-only", "--write", str(out)], capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            sys.exit("packer_pins: nextpnr --pack-only failed\n" + r.stdout[-2000:] + r.stderr[-2000:])
        packed = [v for v in json.loads(out.read_text())["modules"].values() if v.get("cells")][0]["cells"]
    lines = []
    for n in packed:
        if n.endswith(CONFIG["carry_suffix"]):
            orig = n[: -len(CONFIG["carry_suffix"])]
            if orig in c4_bel:
                lines.append((n, c4_bel[orig]))
            continue
        m = re.match(r".*\$LUT\$(.*\$PACKED_CARRY4\$)\$(DI|S)\[(\d)\]$", n)
        if not m:
            continue
        orig = m.group(1)[: -len(CONFIG["carry_suffix"])]
        if orig not in c4_bel:
            continue
        slice_ = c4_bel[orig].rpartition(".")[0]
        lane = CONFIG["lanes"][int(m.group(3))]
        lines.append((n, f"{slice_}.{lane}{'5' if m.group(2) == 'DI' else '6'}LUT"))
    pre = Path(a.preplaced)
    text = pre.read_text()
    have = {l.split("\t")[0] for l in text.splitlines() if "\t" in l}
    add = [f"{n}\t{b}\n" for n, b in lines if n not in have]
    pre.write_text(text + "".join(add))
    print(f"packer_pins: {len(add)} packer cells pinned ({sum(1 for n, _ in lines if n.endswith(CONFIG['carry_suffix']))} CARRY4)")


if __name__ == "__main__":
    main()
