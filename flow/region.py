import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse
import device

CONFIG = {
    "fabric": device.get("fabric"),
    "words_per_frame": 101,
    "site_prefixes": ("SLICE", "RAMB36", "RAMB18", "DSP48"),
    "tall_types": ("BRAM_", "DSP_"),
    "tall_rows": 5,
    "max_interface_hops": 1,
}

DB = bitparse.DB


def load_grid():
    return json.loads((DB / CONFIG["fabric"] / "tilegrid.json").read_text())


def parse_ranges(spec):
    out = []
    for part in spec.replace(" ", ",").split(","):
        if not part:
            continue
        ends = part.split(":")
        ms = [re.fullmatch(r"([A-Z0-9]+?)_X(\d+)Y(\d+)", e) for e in ends]
        if len(ends) > 2 or not all(ms) or len({m.group(1) for m in ms}) != 1:
            sys.exit(f"bad range {part}")
        if ms[0].group(1) not in CONFIG["site_prefixes"]:
            sys.exit(f"bad range {part}: site type {ms[0].group(1)} not in {CONFIG['site_prefixes']}")
        xs = [int(m.group(2)) for m in ms]
        ys = [int(m.group(3)) for m in ms]
        out.append((ms[0].group(1), min(xs), min(ys), max(xs), max(ys)))
    if not out:
        sys.exit(f"bad range {spec}")
    return out


def parse_slice_range(spec):
    slices = [r[1:] for r in parse_ranges(spec) if r[0] == "SLICE"]
    if len(slices) != 1:
        sys.exit(f"bad range {spec}: expected exactly one SLICE range")
    return slices[0]


def pblock_ranges(spec):
    out = []
    for pre, x0, y0, x1, y1 in parse_ranges(spec):
        out.append(f"{pre}_X{x0}Y{y0}:{pre}_X{x1}Y{y1}")
        if pre == "RAMB36":
            out.append(f"RAMB18_X{x0}Y{2 * y0}:RAMB18_X{x1}Y{2 * y1 + 1}")
    return out


def in_ranges(site, ranges):
    m = re.fullmatch(r"([A-Z0-9]+?)_X(\d+)Y(\d+)", site)
    if not m:
        return False
    pre, x, y = m.group(1), int(m.group(2)), int(m.group(3))
    return any(pre == r[0] and r[1] <= x <= r[3] and r[2] <= y <= r[4] for r in ranges)


def region_tiles(grid, spec):
    ranges = parse_ranges(spec)
    sites = {name: t for name, t in grid.items() if any(in_ranges(s, ranges) for s in t.get("sites", {}))}
    by_xy = {(t["grid_x"], t["grid_y"]): n for n, t in grid.items()}
    tiles = dict(sites)
    for name, t in sites.items():
        side = -1 if t["type"].endswith("_R") else 1
        rows = CONFIG["tall_rows"] if t["type"].startswith(CONFIG["tall_types"]) else 1
        for dy in range(rows):
            for k in range(1, CONFIG["max_interface_hops"] + 2):
                nb = by_xy.get((t["grid_x"] + side * k, t["grid_y"] - dy))
                if not nb or not grid[nb]["type"].startswith(("INT_", "BRAM_INT_INTERFACE", "INT_INTERFACE")):
                    break
                tiles[nb] = grid[nb]
                if grid[nb]["type"] in ("INT_L", "INT_R"):
                    break
    return tiles


def region_bits(tiles):
    words = {}
    for name, t in tiles.items():
        for bt, b in t.get("bits", {}).items():
            base = int(b["baseaddr"], 16)
            for minor in range(b["frames"]):
                words.setdefault(base + minor, set()).update(range(b["offset"], b["offset"] + b["words"]))
    return words


def shared_frame_tiles(grid, spec):
    tiles = region_tiles(grid, spec)
    fars = set(region_bits(tiles))
    shared = set()
    for name, t in grid.items():
        if name in tiles:
            continue
        for b in t.get("bits", {}).values():
            base = int(b["baseaddr"], 16)
            if any(base + m in fars for m in range(b["frames"])):
                shared.add(name)
    return shared


def column_owned_words(grid, far_set):
    owned = {}
    for name, t in grid.items():
        for bt, b in t.get("bits", {}).items():
            base = int(b["baseaddr"], 16)
            for minor in range(b["frames"]):
                if base + minor in far_set:
                    owned.setdefault(base + minor, set()).update(range(b["offset"], b["offset"] + b["words"]))
    return owned


def pair_violations(grid, spec):
    tiles = region_tiles(grid, spec)
    bad = []
    for name in sorted(tiles):
        m = re.fullmatch(r"INT_([LR])_X(\d+)Y(\d+)", name)
        if not m:
            continue
        side, x, y = m.group(1), int(m.group(2)), int(m.group(3))
        partner = f"INT_R_X{x + 1}Y{y}" if side == "L" else f"INT_L_X{x - 1}Y{y}"
        if partner in grid and partner not in tiles:
            bad.append((name, partner))
    return bad


def check(bitfile, spec, part, grid, verbose=False):
    tiles = region_tiles(grid, spec)
    allowed = region_bits(tiles)
    r = bitparse.parse(bitfile, part)
    written = r["frames"]
    outside = sorted(f for f in written if f not in allowed)
    missing = sorted(f for f in allowed if f not in written)
    owned = column_owned_words(grid, set(written))
    foreign_words = {}
    for far in written:
        if far not in allowed:
            continue
        extra = owned.get(far, set()) - allowed[far]
        if extra:
            foreign_words[far] = sorted(extra)
    rep = {
        "file": str(bitfile),
        "region": spec,
        "tiles": sorted(tiles),
        "allowed_frames": len(allowed),
        "written_frames": len(written),
        "outside_frames": [bitparse.far_str(f) for f in outside],
        "allowed_not_written": len(missing),
        "frames_with_words_of_tiles_outside_region": {bitparse.far_str(k): v for k, v in foreign_words.items()},
        "inside": not outside,
    }
    return rep


def main():
    ap = argparse.ArgumentParser(description="Check a partial bitstream's frames against an allowed region")
    ap.add_argument("region", help="e.g. SLICE_X12Y100:SLICE_X15Y149 or SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,"
                                   "DSP48_X0Y40:DSP48_X0Y59 (comma-separated site ranges)")
    ap.add_argument("bit", nargs="*")
    ap.add_argument("--list", action="store_true", help="print the region's tiles and frames")
    ap.add_argument("--drc", action="store_true", help="check that no INT_L/INT_R pair is split by the region edge")
    a = ap.parse_args()
    grid = load_grid()
    part = bitparse.Part()
    if a.drc:
        viol = pair_violations(grid, a.region)
        print(f"drc: {len(viol)} INT pair(s) split by the region edge")
        for t, partner in viol[:20]:
            print(f"   {t} in region, partner {partner} outside")
        if viol:
            sys.exit(1)
    if a.list or not a.bit:
        tiles = region_tiles(grid, a.region)
        allowed = region_bits(tiles)
        print(f"{len(tiles)} tiles, {len(allowed)} frames")
        for col, frames in bitparse.column_ranges({f: 1 for f in allowed}).items():
            print(f"  {col[0]} {'B' if col[1] else 'T'} r{col[2]} c{col[3]}: minors {min(frames)}..{max(frames)} ({len(frames)})")
    bad = 0
    for b in a.bit:
        rep = check(b, a.region, part, grid)
        status = "INSIDE" if rep["inside"] else "OUTSIDE"
        print(f"{status} {b}: {rep['written_frames']} frames written, {len(rep['outside_frames'])} outside, "
              f"{rep['allowed_not_written']} region frames not written, "
              f"{len(rep['frames_with_words_of_tiles_outside_region'])} frames also carry other tiles' words")
        for f in rep["outside_frames"][:40]:
            print(f"   outside {f}")
        bad += not rep["inside"]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
