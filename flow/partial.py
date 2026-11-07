import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse
import device
import region

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "part_name": device.part_name(),
    "passes": 2,
    "ctl0_steps": [(0x100, 0x100), (0x400, 0x400)],
    "ctl0_end": (0x100, 0x000),
    "end_far": 0x03BE0000,
    "tail_noops": 16,
    "pass1_ones_minors": [24, 25],
    "pass1_ones_block": 0,
    "pass1_held_pip": r"^INT_[LR]_X\d+Y\d+\.\w+\.\w+$|^DSP_[LR]_X\d+Y\d+\.DSP_[01]_\w+\.DSP_(GND|VCC)_[LR]$",
    "pass1_logic_column_frames": 36,
    "dynamic_feature": r"\.[A-D]LUT\.(RAM|SRL|SMALL)\b|\.SRL\b|^BRAM_[LR]_X\d+Y\d+\.RAMB18_Y[01]\.IN_USE$",
    "dynamic_state": {
        "CLB_IO_CLK": (r"\.[A-D]LUT\.(RAM|SRL|SMALL)\b|\.SRL\b", r"SLICEM_X0\.[A-D]LUT\.INIT\["),
        "BLOCK_RAM": (r"^BRAM_[LR]_X\d+Y\d+\.RAMB18_Y[01]\.IN_USE$", r"RAMB18_Y[01]\.INITP?_"),
    },
    "reset_after_reconfig": False,
    "rar_mask_block": "CFG_CLB",
    "rar_mask_closed": {50: 0xE0000000},
    "rar_open_foreign_types": r"^HCLK_[LR]$",
    "rar_post_shutdown_noops": 4,
    "compress": False,
    "compress_ctl1_steps": [(0x1000, 0x1000)],
    "compress_ctl1_end": (0x1000, 0x000),
    "mfw_noops": 12,
    "mfwr_first_words": 8,
    "mfwr_next_words": 4,
    "mfwr_noops_after": {"CLB_IO_CLK": 0, "BLOCK_RAM": 8, "CFG_CLB": 0},
    "type1_max_words": 0x7FF,
    "compress_flush": "next",
    "pass1_hclk_tile": r"^HCLK_[LR]$",
    "pass1_hclk_pip": r"^HCLK_[LR]_X\d+Y\d+\.(HCLK_LEAF_CLK_B_(BOT|TOP)\d+|ENABLE_BUFFER)\.HCLK_CK_BUFHCLK\d+$",
    "pass1_dsp_feature": r"^DSP_[LR]_X\d+Y\d+\.DSP48\.DSP_[01]\.[AB]REG_1$",
    "pass1_carry_feature": r"^CLBL[LM]_[LR]_X\d+Y\d+\.SLICE[LM]_X[01]\.PRECYINIT\.CIN$",
}

NOOP = 0x20000000
SYNC = 0xAA995566
REG = {"CRC": 0, "FAR": 1, "FDRI": 2, "CMD": 4, "CTL0": 5, "MASK": 6, "MFWR": 10, "IDCODE": 12, "CTL1": 24}
CMD = {"NULL": 0, "WCFG": 1, "MFW": 2, "START": 5, "RCRC": 7, "GRESTORE": 10, "SHUTDOWN": 11, "DESYNC": 13}


def t1(reg, n):
    return 0x30000000 | (reg << 13) | n


class Stream:
    def __init__(self):
        self.words = []
        self.crc = 0

    def noop(self, n=1):
        self.words += [NOOP] * n

    def write(self, reg, values, type2=False):
        if type2:
            self.words += [t1(reg, 0), 0x50000000 | len(values)]
        else:
            self.words.append(t1(reg, len(values)))
        self.words += values
        for v in values:
            self.crc = bitparse.icap_crc(reg, v, self.crc)

    def cmd(self, name):
        self.write(REG["CMD"], [CMD[name]])
        if name == "RCRC":
            self.crc = 0

    def write_crc(self):
        self.words += [t1(REG["CRC"], 1), self.crc]
        self.crc = 0

    def frames_at(self, far, data, type2=None):
        self.cmd("WCFG")
        self.noop()
        self.write(REG["FAR"], [far])
        self.noop()
        self.write(REG["FDRI"], data, type2=len(data) > CONFIG["type1_max_words"] if type2 is None else type2)

    def multi_frame(self, first, rest):
        after = CONFIG["mfwr_noops_after"][bitparse.far_fields(first)["block"]]
        self.cmd("MFW")
        self.noop(CONFIG["mfw_noops"])
        self.write(REG["MFWR"], [0] * CONFIG["mfwr_first_words"])
        self.noop(after)
        for f in rest:
            self.write(REG["FAR"], [f])
            self.write(REG["MFWR"], [0] * CONFIG["mfwr_next_words"])
            self.noop(after)


def compressed_frames(s, order, data, next_fn, content_fn, flush="next"):
    key = {f: tuple(data[f]) for f in order}
    count = {}
    for k in key.values():
        count[k] = count.get(k, 0) + 1
    pos = {f: i for i, f in enumerate(order)}
    written = set()
    outside = []

    def members(k):
        return [g for g in order if g not in written and key[g] == k]

    i = 0
    while i < len(order):
        f = order[i]
        if f in written:
            i += 1
            continue
        if count[key[f]] > 1:
            group = members(key[f])
            s.frames_at(f, list(data[f]))
            s.multi_frame(f, group[1:])
            written.update(group)
            i += 1
            continue
        run = [f]
        while True:
            nxt, pad = next_fn(run[-1])
            if pad or nxt not in pos or nxt in written or count[key[nxt]] > 1:
                break
            run.append(nxt)
        written.update(run)
        nxt, _ = next_fn(run[-1])
        body = [w for g in run for w in data[g]]
        if nxt in pos and nxt not in written and count[key[nxt]] > 1:
            group = members(key[nxt])
            s.frames_at(f, body + list(data[nxt]))
            s.multi_frame(nxt, group[1:])
            written.update(group)
        else:
            zero = [0] * bitparse.CONFIG["words_per_frame"]
            tail = (zero if flush == "zero" else data[nxt]) if nxt in pos else content_fn(nxt)
            if nxt not in pos:
                outside.append((nxt, list(tail)))
            s.frames_at(f, body + list(tail))
        i += 1
    return outside


def runs(fars, part):
    order = sorted(fars, key=part.index.get)
    out, cur = [], [order[0]]
    for f in order[1:]:
        nxt, pad = part.next_far(cur[-1])
        if nxt == f and not pad:
            cur.append(f)
        else:
            out.append(cur)
            cur = [f]
    out.append(cur)
    return out


_state_minors = {}


def state_minors(tile_type, block, bit_re):
    key = (tile_type, block)
    if key not in _state_minors:
        name = f"segbits_{tile_type.lower()}{'.block_ram' if block == 'BLOCK_RAM' else ''}.db"
        f = bitparse.DB / name
        minors = set()
        if f.exists():
            for line in f.read_text().splitlines():
                feat, *bits = line.split()
                if re.search(bit_re, feat):
                    minors.update(int(b.lstrip("!").split("_")[0]) for b in bits)
        _state_minors[key] = minors
    return _state_minors[key]


def dynamic_state_frames(grid, lines, rtiles, written):
    hits = {}
    for l in lines:
        tile = l.split(".")[0]
        if tile in rtiles or tile not in grid:
            continue
        for block, (feat_re, bit_re) in CONFIG["dynamic_state"].items():
            b = grid[tile].get("bits", {}).get(block)
            if b is None or not re.search(feat_re, l):
                continue
            base = int(b["baseaddr"], 16)
            for m in state_minors(grid[tile]["type"], block, bit_re):
                if base + m in written:
                    hits.setdefault(base + m, set()).add(tile)
    return hits


def fasm_lines(path):
    return [l.strip() for l in Path(path).read_text().splitlines() if l.strip() and not l.startswith("#")]


def is_pip(line):
    return re.match(CONFIG["pass1_held_pip"], line) is not None


def static_pip_features(prerouted, grid):
    names = {(t["grid_x"], t["grid_y"]): n for n, t in grid.items()}
    out = set()
    for line in Path(prerouted).read_text().splitlines():
        if "\t" not in line:
            continue
        for tok in line.split("\t", 1)[1].split(";"):
            parts = tok.split("/")
            if len(parts) != 3 or not parts[0].startswith("X"):
                continue
            xy = parts[0][1:].split("Y")
            tile = names.get((int(xy[0]), int(xy[1])))
            if tile:
                out.add(f"{tile}.{parts[1]}.{parts[2]}")
    return out


def hclk_tiles(grid, allowed):
    out = set()
    for name, t in grid.items():
        b = t.get("bits", {}).get("CLB_IO_CLK")
        if b and re.match(CONFIG["pass1_hclk_tile"], t["type"]) and \
                any(int(b["baseaddr"], 16) + m in allowed for m in range(b["frames"])):
            out.add(name)
    return out


def held_feature(line, tiles, features):
    return line.split(".")[0] in tiles and any(re.match(r, line) for r in features)


def held_back(line, tiles, hclk, shared, features=()):
    tile = line.split(".")[0]
    if tile in tiles and is_pip(line):
        return line not in shared
    if held_feature(line, tiles, features):
        return True
    if tile in hclk and re.match(CONFIG["pass1_hclk_pip"], line):
        parts = line.split(".")
        if parts[1] == "ENABLE_BUFFER":
            return not any(x.startswith(tile + ".HCLK_LEAF_CLK_B_") and x.endswith("." + parts[2]) for x in shared)
        return line not in shared
    return False


def fasm_frames(lines):
    oxc7 = bitparse.CONFIG["root"] / "toolchain" / "openxc7"
    with tempfile.TemporaryDirectory() as td:
        fin, fout = Path(td) / "pass1.fasm", Path(td) / "pass1.frames"
        fin.write_text("\n".join(lines) + "\n")
        with open(fout, "w") as f:
            subprocess.run([str(oxc7 / "bin" / "fasm2frames"), "--part", bitparse.CONFIG["part"],
                            "--db-root", str(bitparse.DB), str(fin)], stdout=f, check=True)
        frames = {}
        for line in fout.read_text().splitlines():
            far, data = line.split()
            fr = [int(x, 16) for x in data.split(",")]
            fr[bitparse.ECC_WORD] = (fr[bitparse.ECC_WORD] & ~bitparse.ECC_MASK & 0xFFFFFFFF) | bitparse.frame_ecc(fr)
            frames[int(far, 16)] = fr
    return frames


def unknown_bits(final, modelled, fars):
    zero = [0] * bitparse.CONFIG["words_per_frame"]
    out = {}
    for f in fars:
        a, b = bitparse.without_ecc(final.get(f, zero)), bitparse.without_ecc(modelled.get(f, zero))
        extra = [x & ~y & 0xFFFFFFFF for x, y in zip(a, b)]
        if any(extra):
            out[f] = extra
    return out


def pass1_frames(target_fasm, config_fasms, tiles, static_pips=None, hclk=frozenset(), features=(), final=None,
                 fars=()):
    target = fasm_lines(target_fasm)
    if static_pips is not None:
        shared = static_pips
    else:
        sets = [set(fasm_lines(f)) for f in config_fasms]
        shared = set.intersection(*sets) if sets else set()
    keep = [l for l in target if not held_back(l, tiles, hclk, shared, features)]
    held = sorted(l for l in target if held_feature(l, tiles, features))
    dropped = len(target) - len(keep)
    frames = fasm_frames(keep)
    unknown = {}
    if final is not None:
        unknown = unknown_bits(final, fasm_frames(target), fars)
        zero = [0] * bitparse.CONFIG["words_per_frame"]
        for f, extra in unknown.items():
            fr = [w | x for w, x in zip(frames.get(f, zero), extra)]
            fr[bitparse.ECC_WORD] = (fr[bitparse.ECC_WORD] & ~bitparse.ECC_MASK & 0xFFFFFFFF) | bitparse.frame_ecc(fr)
            frames[f] = fr
    return frames, dropped, held, unknown


def rar_columns(grid, tiles):
    opened, foreign = set(), {}
    for name, t in tiles.items():
        b = t.get("bits", {}).get("CLB_IO_CLK")
        if b:
            f = bitparse.far_fields(int(b["baseaddr"], 16))
            opened.add((f["bottom"], f["row"], f["column"]))
    present = set()
    for name, t in grid.items():
        b = t.get("bits", {}).get("CLB_IO_CLK")
        if not b:
            continue
        f = bitparse.far_fields(int(b["baseaddr"], 16))
        key = (f["bottom"], f["row"], f["column"])
        present.add(key)
        if key in opened and name not in tiles and not re.match(CONFIG["rar_open_foreign_types"], t["type"]):
            foreign.setdefault(key, []).append(name)
    return opened, present, foreign


def rar_mask(part, opened, present):
    zero = [0] * bitparse.CONFIG["words_per_frame"]
    closed = list(zero)
    for w, v in CONFIG["rar_mask_closed"].items():
        closed[w] = v
    closed[bitparse.ECC_WORD] |= bitparse.frame_ecc(closed)
    mask = {}
    for far in part.cfg_order:
        f = bitparse.far_fields(far)
        key = (f["bottom"], f["row"], f["column"])
        mask[far] = list(closed) if key in present and key not in opened else list(zero)
    return mask


def row_groups(fars):
    out = {}
    for f in fars:
        out.setdefault(f >> 17, []).append(f)
    return out


def write_mask(s, part, mask, compress):
    zero = [0] * bitparse.CONFIG["words_per_frame"]
    order = list(part.cfg_order)
    if compress:
        for key, fs in row_groups(order).items():
            compressed_frames(s, fs, mask, part.next_far, lambda f: zero)
    else:
        data = []
        for far in order:
            data += mask[far]
            nxt, pad = part.next_far(far)
            if pad or nxt is None:
                data += zero * bitparse.CONFIG["row_pad_frames"]
        s.frames_at(order[0], data, type2=True)
    s.write_crc()
    s.cmd("SHUTDOWN")
    s.noop()
    s.write_crc()
    s.noop(CONFIG["rar_post_shutdown_noops"])


def build(full_bit, spec, part, grid, fasm=None, configs=(), static_prerouted=None, rar=False, compress=False,
          static_list=None, hold_hclk=False, flush=CONFIG["compress_flush"], hold_dsp=False, hold_carry=False,
          keep_unknown=False):
    full = bitparse.parse(full_bit, part)
    frames = full["frames"]
    tiles = region.region_tiles(grid, spec)
    allowed = region.region_bits(tiles)
    missing = [f for f in allowed if f not in frames]
    if missing:
        sys.exit(f"{full_bit}: {len(missing)} region frames not in the full bitstream")
    zero = [0] * bitparse.CONFIG["words_per_frame"]
    plan = []
    for r in runs(allowed, part):
        nxt, _ = part.next_far(r[-1])
        pad = frames.get(nxt, zero) if nxt is not None else zero
        plan.append((r, nxt, pad))
    sources = [frames] * CONFIG["passes"]
    info = {"pass1_dropped_pips": None, "rar": None}
    if fasm:
        sp = static_pip_features(static_prerouted, grid) if static_prerouted else None
        if static_list:
            sp = (sp or set()) | set(fasm_lines(static_list))
        hc = hclk_tiles(grid, allowed) if hold_hclk else frozenset()
        features = [CONFIG[k] for k, on in (("pass1_dsp_feature", hold_dsp), ("pass1_carry_feature", hold_carry)) if on]
        p1, dropped, held, unknown = pass1_frames(fasm, configs, set(tiles), sp, hc, features,
                                                  frames if keep_unknown else None, allowed)
        info["pass1_dropped_pips"] = dropped
        info["pass1_held_features"] = held
        info["pass1_unknown_bits"] = {bitparse.far_str(f): sum(bin(w).count("1") for w in x) for f, x in unknown.items()}
        if hold_hclk:
            info["pass1_hclk_tiles"] = sorted(hc)
        clb = bitparse.BLOCK_NAMES[CONFIG["pass1_ones_block"]]
        p1 = {f: list(p1.get(f, zero)) if bitparse.far_fields(f)["block"] == clb else list(frames[f]) for f in allowed}
        cols = {}
        for f in allowed:
            cols.setdefault(f & ~0x7F, []).append(f)
        for base, fs in cols.items():
            minors = {f & 0x7F for f in fs}
            if bitparse.far_fields(base)["block"] != bitparse.BLOCK_NAMES[CONFIG["pass1_ones_block"]] or \
                    not set(CONFIG["pass1_ones_minors"]) <= minors:
                continue
            for m in CONFIG["pass1_ones_minors"]:
                fr = [0xFFFFFFFF if i in allowed[base | m] else w for i, w in enumerate(frames[base | m])]
                fr[bitparse.ECC_WORD] = p1[base | m][bitparse.ECC_WORD] & ~bitparse.ECC_MASK & 0xFFFFFFFF
                fr[bitparse.ECC_WORD] |= bitparse.frame_ecc(fr)
                p1[base | m] = fr
        sources = [p1] + [frames] * (CONFIG["passes"] - 1)
        logic_same = all(bitparse.without_ecc(p1[f]) == bitparse.without_ecc(frames[f]) for f in allowed
                         if (f & 0x7F) >= 26 and len(cols[f & ~0x7F]) == CONFIG["pass1_logic_column_frames"])
        info["pass1_ones_minors"] = CONFIG["pass1_ones_minors"]
        info["pass1_logic_frames_equal_final"] = logic_same
    mask = None
    if rar:
        opened, present, foreign = rar_columns(grid, tiles)
        info["rar"] = {"opened_columns": sorted(opened), "foreign_tiles_in_opened_columns": foreign}
        if foreign:
            return None, plan, [], frames, info, None
        mask = rar_mask(part, opened, present)
    s = Stream()
    s.noop()
    s.cmd("RCRC")
    s.noop(2)
    s.write(REG["IDCODE"], [part.idcode])
    if rar:
        write_mask(s, part, mask, compress)
    s.cmd("NULL")
    for m, val in CONFIG["ctl0_steps"]:
        s.write(REG["MASK"], [m])
        s.write(REG["CTL0"], [val])
    if compress:
        for m, val in CONFIG["compress_ctl1_steps"]:
            s.write(REG["MASK"], [m])
            s.write(REG["CTL1"], [val])
    pads = [(nxt, pad) for _, nxt, pad in plan]
    if compress:
        blocks = row_groups(sorted(allowed, key=part.index.get))
        pads = []
        for src in sources:
            for blk in sorted(blocks):
                order = blocks[blk]
                pads += compressed_frames(s, order, {f: src[f] for f in order}, part.next_far,
                                          lambda f: frames.get(f, zero) if f is not None else zero, flush)
    else:
        for src in sources:
            for r, nxt, pad in plan:
                s.frames_at(r[0], [w for f in r for w in src[f]] + list(pad), type2=True)
    if rar:
        s.cmd("GRESTORE")
        s.noop()
    if compress:
        m, val = CONFIG["compress_ctl1_end"]
        s.write(REG["MASK"], [m])
        s.write(REG["CTL1"], [val])
    m, val = CONFIG["ctl0_end"]
    s.write(REG["MASK"], [m])
    s.write(REG["CTL0"], [val])
    if rar:
        s.cmd("START")
        s.noop()
    s.write(REG["FAR"], [CONFIG["end_far"]])
    s.write_crc()
    s.cmd("DESYNC")
    s.noop(CONFIG["tail_noops"])
    return s.words, plan, pads, frames, info, mask


def body_bytes(words):
    pre = [0xFFFFFFFF] * 8 + [0x000000BB, 0x11220044, 0xFFFFFFFF, 0xFFFFFFFF, SYNC]
    return struct.pack(f">{len(pre) + len(words)}I", *(pre + words))


def bit_header(design, nbytes, compress=False):
    def field(k, s):
        b = s.encode() + b"\x00"
        return k.encode() + struct.pack(">H", len(b)) + b
    t = time.localtime()
    h = b"\x00\x09\x0f\xf0\x0f\xf0\x0f\xf0\x0f\xf0\x00\x00\x01"
    h += field("a", f"{design};{'COMPRESS=TRUE;' if compress else ''}UserID=0XFFFFFFFF;PARTIAL=TRUE;"
                   "Generator=open-dfx-xc7/partial.py")
    h += field("b", CONFIG["part_name"])
    h += field("c", time.strftime("%Y/%m/%d", t))
    h += field("d", time.strftime("%H:%M:%S", t))
    h += b"e" + struct.pack(">I", nbytes)
    return h


def is_mask_far(far):
    return (far >> 23) & 7 == bitparse.BLOCKS[CONFIG["rar_mask_block"]]


def simulate(partial_bit, base_bit, target_bit, part, strict=False):
    base = dict(bitparse.parse(base_bit, part)["frames"])
    p = bitparse.parse(partial_bit, part, strict=strict)
    for far, data in p["frames"].items():
        if not is_mask_far(far):
            base[far] = data
    target = bitparse.parse(target_bit, part)["frames"]
    keys = set(base) | set(target)
    zero = [0] * bitparse.CONFIG["words_per_frame"]
    bad = [k for k in keys if base.get(k, zero) != target.get(k, zero)]
    return bad, p


def check_rar_stream(parsed, mask, opened):
    got = {f: d for f, d in parsed["frames"].items() if is_mask_far(f)}
    cmds = [e for e in parsed["events"] if "cmd" in e]
    problems = []
    if mask is None:
        if got:
            problems.append(f"{len(got)} {CONFIG['rar_mask_block']} frames written without RESET_AFTER_RECONFIG")
        extra = [e["cmd"] for e in cmds if e["cmd"] in ("SHUTDOWN", "GRESTORE", "START")]
        if extra:
            problems.append(f"commands {extra} without RESET_AFTER_RECONFIG")
        return problems, None
    if set(got) != set(mask):
        problems.append(f"mask frames written {len(got)}, expected {len(mask)}")
    differ = [bitparse.far_str(f) for f in mask if got.get(f) != mask[f]]
    if differ:
        problems.append(f"mask frames differ from the computed mask: {differ[:3]}")
    zero = [0] * bitparse.CONFIG["words_per_frame"]
    open_in_stream = set()
    for f, d in got.items():
        ff = bitparse.far_fields(f)
        if d == zero:
            open_in_stream.add((ff["bottom"], ff["row"], ff["column"]))
    if not set(opened) <= open_in_stream:
        problems.append("region columns not all opened by the mask")
    want = ["SHUTDOWN", "GRESTORE", "START", "DESYNC"]
    order = [e["cmd"] for e in cmds if e["cmd"] in want]
    if order != want:
        problems.append(f"command order {order}, expected {want}")
    shut = min([e["word"] for e in cmds if e["cmd"] == "SHUTDOWN"] or [-1])
    late = [e for e in parsed["events"] if e.get("reg") == "FAR" and e.get("value")
            and is_mask_far(int(e["value"], 16)) and e["word"] > shut]
    if late:
        problems.append("mask written after SHUTDOWN")
    summary = {"mask_frames": len(got), "closed_frames": sum(1 for d in got.values() if d != zero),
               "zero_frames": sorted(f"{'B' if k[0] else 'T'} r{k[1]} c{k[2]}" for k in open_in_stream),
               "region_columns": sorted(f"{'B' if k[0] else 'T'} r{k[1]} c{k[2]}" for k in opened),
               "commands": order}
    return problems, summary


def other_region_check(grid, spec, others, plan, pads):
    mine = set(region.region_bits(region.region_tiles(grid, spec)))
    written = {f for r, _, _ in plan for f in r} | {n for n, _ in pads if n is not None}
    out = {}
    for o in others:
        theirs = set(region.region_bits(region.region_tiles(grid, o)))
        out[o] = {"common_frames": len(mine & theirs), "frames_written": len(written & theirs)}
    return out


def main():
    ap = argparse.ArgumentParser(description="Write a region-only Series-7 partial bitstream from a full bitstream")
    ap.add_argument("full_bit")
    ap.add_argument("out", help="output path without extension; writes .bit and .bin")
    ap.add_argument("--region", default=CONFIG["region"])
    ap.add_argument("--design", default="partial")
    ap.add_argument("--base", help="full bitstream currently on the device, for --simulate")
    ap.add_argument("--simulate", action="store_true", help="apply the partial to --base and compare with full_bit")
    ap.add_argument("--fasm", help="FASM of full_bit: enables a first pass without the RM's own routing pips")
    ap.add_argument("--configs", nargs="*", default=[],
                    help="FASM of every configuration; first-pass pips are those present in all of them")
    ap.add_argument("--static-pips", help="-o prerouted file of the static nets; first-pass pips are exactly theirs")
    ap.add_argument("--static-pip-list", help="FASM features of the static nets' pips (e.g. from Vivado's static_routed.dcp); "
                                              "first-pass pips are exactly these (added to --static-pips if both)")
    ap.add_argument("--pass1-hold-hclk", action="store_true",
                    help="also hold back HCLK leaf pips of the region's columns that are not static pips (Vivado's pass 1)")
    ap.add_argument("--pass1-hold-dsp", action="store_true",
                    help="also hold back the DSP48E1 AREG_1/BREG_1 configuration features of the region in pass 1 "
                         "(Vivado's pass 1; needs --fasm)")
    ap.add_argument("--pass1-hold-carry", action="store_true",
                    help="also hold back PRECYINIT.CIN (CARRY4 carry-in from the slice below) of the region in pass 1 "
                         "(Vivado's pass 1; needs --fasm)")
    ap.add_argument("--pass1-keep-unknown", action="store_true",
                    help="keep in pass 1 the region bits of the full bitstream that no feature of --fasm explains "
                         "(e.g. DSP48E1 bits prjxray-db does not name); by default they first appear in pass 2 "
                         "(needs --fasm)")
    ap.add_argument("--reset-after-reconfig", action="store_true", default=CONFIG["reset_after_reconfig"],
                    help="Vivado's RESET_AFTER_RECONFIG: GSR mask opened on the region's columns, SHUTDOWN, GRESTORE, START")
    ap.add_argument("--compress", action="store_true", default=CONFIG["compress"],
                    help="Vivado's BITSTREAM.GENERAL.COMPRESS: identical frames written once and copied with MFWR")
    ap.add_argument("--compress-flush", choices=["next", "zero"], default=CONFIG["compress_flush"],
                    help="last (flush) frame of a compressed FDRI run inside the region: the next frame's own data "
                         "(correct whether or not the device commits it) or zeros as Vivado writes (correct only if "
                         "it is not committed); run-end frames outside the region always carry the full bitstream's data")
    ap.add_argument("--other-region", action="append", default=[], metavar="SPEC",
                    help="region of another reconfigurable partition of the same design (repeatable); the partial is "
                         "refused if this region shares a configuration frame with it or writes one of its frames "
                         "(Vivado DRC HDPR-25); recorded in the .check.json as other_regions")
    a = ap.parse_args()
    part = bitparse.Part()
    grid = region.load_grid()
    words, plan, pads, frames, info, mask = build(a.full_bit, a.region, part, grid, a.fasm, a.configs, a.static_pips,
                                                  a.reset_after_reconfig, a.compress, a.static_pip_list,
                                                  a.pass1_hold_hclk, a.compress_flush, a.pass1_hold_dsp,
                                                  a.pass1_hold_carry, a.pass1_keep_unknown)
    if info["rar"] is not None:
        foreign = info["rar"]["foreign_tiles_in_opened_columns"]
        print(f"reset after reconfig: GSR mask opens {len(info['rar']['opened_columns'])} column(s); "
              f"non-region tiles other than HCLK in them: {sum(len(v) for v in foreign.values())}")
        if foreign:
            sys.exit(f"REFUSED: RESET_AFTER_RECONFIG would open the GSR mask on static tiles "
                     f"{sorted(t for v in foreign.values() for t in v)[:5]}; the region must cover whole clock-row "
                     "columns; nothing written")
    site_opts = a.pass1_hold_dsp or a.pass1_hold_carry or a.pass1_keep_unknown
    if site_opts and not a.fasm:
        sys.exit("--pass1-hold-dsp, --pass1-hold-carry and --pass1-keep-unknown need --fasm")
    if site_opts:
        print(f"pass 1: {len(info['pass1_held_features'])} configuration feature(s) held back; "
              f"unknown bits kept: {sum(info['pass1_unknown_bits'].values())} in {len(info['pass1_unknown_bits'])} "
              "frame(s)")
    if info["pass1_dropped_pips"] is not None:
        print(f"pass 1: {info['pass1_dropped_pips']} region pips held back to pass 2; "
              f"logic frames identical to final: {info['pass1_logic_frames_equal_final']}")
    other_regions = None
    if a.other_region:
        other_regions = other_region_check(grid, a.region, a.other_region, plan, pads)
        for spec, o in other_regions.items():
            print(f"other partition {spec}: {o['common_frames']} configuration frame(s) shared with this region, "
                  f"{o['frames_written']} of its frames written by this partial")
        bad = sorted(s for s, o in other_regions.items() if o["common_frames"] or o["frames_written"])
        if bad:
            sys.exit(f"REFUSED: the partial for region {a.region} would write configuration frames of reconfigurable "
                     f"partition(s) {bad} (shared region frames or run-end pad frames; Vivado: DRC HDPR-25, "
                     "reconfigurable Pblocks cannot share a column within a clock region); nothing written")
    out = Path(a.out)
    body = body_bytes(words)
    out.with_suffix(".bin").write_bytes(body)
    out.with_suffix(".bit").write_bytes(bit_header(a.design, len(body), a.compress) + body)
    nfr = sum(len(r) for r, _, _ in plan)
    print(f"wrote {out}.bit/.bin: {len(body)} bytes, {nfr} region frames in {len(plan)} run(s) x {CONFIG['passes']} passes"
          + (", compressed" if a.compress else ""))
    rep = region.check(str(out.with_suffix(".bit")), a.region, part, grid)
    outside = set(rep["outside_frames"])
    rar_summary = None
    if a.reset_after_reconfig or a.compress:
        opened = {tuple(k) for k in info["rar"]["opened_columns"]} if info["rar"] else set()
        problems, rar_summary = check_rar_stream(bitparse.parse(str(out.with_suffix(".bit")), part), mask, opened)
        if rar_summary:
            print(f"reset after reconfig: {rar_summary['mask_frames']} mask frames, {rar_summary['closed_frames']} closed; "
                  f"zero (open) columns {rar_summary['zero_frames']}; commands {rar_summary['commands']}")
        if problems:
            out.with_suffix(".bit").unlink()
            out.with_suffix(".bin").unlink()
            sys.exit(f"REFUSED: {'; '.join(problems)}; outputs deleted")
        outside -= {bitparse.far_str(f) for f in (mask or {})}
    pad_names = {bitparse.far_str(n) for n, _ in pads if n is not None}
    unexpected = outside - pad_names
    pads_static = all(n is None or frames.get(n, [0] * 101) == pad for n, pad in pads)
    print(f"region check: {len(outside)} frame(s) outside region, all of them run-end pad frames: {not unexpected}; "
          f"pad frames carry the full bitstream's own content: {pads_static}")
    if unexpected or not pads_static:
        out.with_suffix(".bit").unlink()
        out.with_suffix(".bin").unlink()
        sys.exit("REFUSED: partial would write frames outside the region; outputs deleted")
    shared, dynamic = region.shared_frame_tiles(grid, a.region), None
    if a.fasm:
        dynamic = sorted({l.split(".")[0] for l in fasm_lines(a.fasm)
                          if l.split(".")[0] in shared and re.search(CONFIG["dynamic_feature"], l)})
        print(f"shared frames: {len(shared)} static tiles share frames with the region; "
              f"with LUTRAM/SRL contents: {len(dynamic)}")
        if dynamic:
            out.with_suffix(".bit").unlink()
            out.with_suffix(".bin").unlink()
            sys.exit(f"REFUSED: rewriting shared frames would reset LUTRAM/SRL/BRAM state in static tiles {dynamic[:5]}; "
                     "outputs deleted")
    state_hits = None
    if a.fasm:
        written = {f for r, _, _ in plan for f in r} | {n for n, _ in pads if n is not None}
        hits = dynamic_state_frames(grid, fasm_lines(a.fasm), set(region.region_tiles(grid, a.region)), written)
        state_hits = {bitparse.far_str(k): sorted(v) for k, v in sorted(hits.items())}
        print(f"state frames: {len(hits)} frame(s) written by the partial (region and pad frames) hold LUTRAM/SRL/BRAM "
              f"state of static tiles")
        if hits:
            out.with_suffix(".bit").unlink()
            out.with_suffix(".bin").unlink()
            sys.exit(f"REFUSED: frames {list(state_hits)[:3]} hold runtime state of static tiles "
                     f"{sorted(set().union(*hits.values()))[:5]}; outputs deleted")
    record = {
        "partial_bin": out.with_suffix(".bin").name,
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "from_full": a.full_bit,
        "region": a.region,
        "region_frames": nfr,
        "outside_frames": sorted(outside),
        "outside_are_static_pads": not unexpected and pads_static,
        "pass1_dropped_pips": info["pass1_dropped_pips"],
        "shared_frame_static_tiles": len(shared),
        "shared_frame_dynamic_tiles": dynamic,
        "static_state_frames_written": state_hits,
        "simulated": None,
    }
    if other_regions is not None:
        record["other_regions"] = other_regions
    if a.reset_after_reconfig:
        record["reset_after_reconfig"] = rar_summary
    if a.compress:
        record["compressed"] = {"flush": a.compress_flush}
    if a.static_pip_list or a.pass1_hold_hclk or site_opts:
        record["pass1"] = {"static_pip_list": a.static_pip_list, "hold_hclk_tiles": info.get("pass1_hclk_tiles")}
        if site_opts:
            record["pass1"].update({"hold_dsp": a.pass1_hold_dsp, "hold_carry": a.pass1_hold_carry,
                                    "held_features": info.get("pass1_held_features"),
                                    "keep_unknown": a.pass1_keep_unknown,
                                    "unknown_bits": info.get("pass1_unknown_bits")})
    if a.simulate:
        if not a.base:
            sys.exit("--simulate needs --base")
        bad, p = simulate(str(out.with_suffix(".bit")), a.base, a.full_bit, part)
        bad_strict, _ = simulate(str(out.with_suffix(".bit")), a.base, a.full_bit, part, strict=True)
        crc = p["crc_checks"]
        crc_ok = bool(crc) and all(c["match"] for c in crc)
        print(f"crc: {'OK' if crc_ok else 'BAD'}; base + partial == target: {not bad} ({len(bad)} frames differ); "
              f"with each burst's last frame left uncommitted: {not bad_strict} ({len(bad_strict)} frames differ)")
        record["simulated"] = {"base": a.base, "crc_ok": crc_ok, "frames_differ": len(bad),
                               "frames_differ_last_frame_uncommitted": len(bad_strict)}
        if a.compress and a.compress_flush == "zero":
            if bad:
                print(f"WARNING: --compress-flush zero: {len(bad)} frame(s) are correct only if the device does not commit "
                      "the last frame of an FDRI write (as Vivado's own compressed partials assume)")
            bad = bad_strict
        else:
            bad = bad or bad_strict
        if bad or not crc_ok:
            for k in sorted(bad)[:10]:
                print("   ", bitparse.far_str(k))
            sys.exit(1)
    rec = out.with_suffix(".check.json")
    rec.write_text(json.dumps(record, indent=1))
    print(f"safety record {rec}")


if __name__ == "__main__":
    main()
