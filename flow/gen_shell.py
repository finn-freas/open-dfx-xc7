import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import replay_dump

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "anchor_in": ["SLICE_X12Y120", "SLICE_X12Y121"],
    "ff_slice": "SLICE_X13Y121",
    "n_in": 8,
    "n_out": 4,
    "out_anchors": False,
}


def bel(smap, site, b):
    tile, local = smap[site]
    return f"{tile}/{local}.{b}"


def main():
    ap = argparse.ArgumentParser(description="Write the RM shell: pinned input anchors, output FFs, region blockers")
    ap.add_argument("out")
    ap.add_argument("--ff-slice", default=CONFIG["ff_slice"])
    ap.add_argument("--out-anchors", action="store_true", default=CONFIG["out_anchors"],
                    help="put a pinned LUT1 in front of each output FF, same lane, so nextpnr's LUT-FF pairing agrees")
    a = ap.parse_args()
    grid = region.load_grid()
    smap = replay_dump.site_map(grid)
    x0, y0, x1, y1 = region.parse_slice_range(CONFIG["region"])
    tiles = {}
    for site, (tile, local) in smap.items():
        m = re.fullmatch(r"SLICE_X(\d+)Y(\d+)", site)
        if m and x0 <= int(m.group(1)) <= x1 and y0 <= int(m.group(2)) <= y1:
            tiles.setdefault(tile, []).append(site)
    used = set(CONFIG["anchor_in"]) | {a.ff_slice}
    lanes = "ABCD"
    lines = ["module rm_slot (input wire clk, input wire [7:0] din, output wire [3:0] dout);",
             "    wire [7:0] a;", "    wire [3:0] d;"]
    if a.out_anchors:
        lines.append("    wire [3:0] e;")
    for i in range(CONFIG["n_in"]):
        site = CONFIG["anchor_in"][i // 4]
        lines.append(f'    (* keep, BEL = "{bel(smap, site, lanes[i % 4] + "6LUT")}" *) '
                     f"LUT1 #(.INIT(2'b10)) ain{i} (.I0(din[{i}]), .O(a[{i}]));")
    lines.append("    rm_core core (.a(a), .d(d));")
    for i in range(CONFIG["n_out"]):
        src = f"d[{i}]"
        if a.out_anchors:
            lines.append(f'    (* keep, BEL = "{bel(smap, a.ff_slice, lanes[i] + "6LUT")}" *) '
                         f"LUT1 #(.INIT(2'b10)) aout{i} (.I0(d[{i}]), .O(e[{i}]));")
            src = f"e[{i}]"
        lines.append(f'    (* keep, BEL = "{bel(smap, a.ff_slice, lanes[i] + "FF")}" *) '
                     f"FDRE q{i} (.C(clk), .CE(1'b1), .R(1'b0), .D({src}), .Q(dout[{i}]));")
    n = 0
    for tile in sorted(tiles, key=lambda t: tuple(map(int, re.findall(r"\d+", t)))):
        if used & set(tiles[tile]):
            continue
        site = sorted(tiles[tile])[0]
        lines.append(f'    (* keep, BEL = "{bel(smap, site, "A6LUT")}" *) '
                     f"LUT1 #(.INIT(2'b00)) blk{n} (.I0(), .O());")
        n += 1
    lines.append("endmodule")
    Path(a.out).write_text("\n".join(lines) + "\n")
    print(f"wrote {a.out}: {CONFIG['n_in']} anchors, {CONFIG['n_out']} FFs"
          f"{' with output anchors' if a.out_anchors else ''} at {a.ff_slice}, {n} blockers over {len(tiles)} tiles")


if __name__ == "__main__":
    main()
