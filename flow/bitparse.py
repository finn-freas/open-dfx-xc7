import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import device

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "part": device.get("part"),
    "family": device.get("family"),
    "words_per_frame": 101,
    "row_pad_frames": 2,
    "mask_columns_from": "CLB_IO_CLK",
}

DB = CONFIG["root"] / "toolchain" / "openxc7" / "share" / "nextpnr" / "external" / "prjxray-db" / CONFIG["family"]

SYNC = 0xAA995566

REGS = {
    0: "CRC", 1: "FAR", 2: "FDRI", 3: "FDRO", 4: "CMD", 5: "CTL0", 6: "MASK", 7: "STAT",
    8: "LOUT", 9: "COR0", 10: "MFWR", 11: "CBC", 12: "IDCODE", 13: "AXSS", 14: "COR1",
    16: "WBSTAR", 17: "TIMER", 19: "RBCRC_SW", 22: "BOOTSTS", 24: "CTL1", 31: "BSPI",
}

CMDS = {
    0: "NULL", 1: "WCFG", 2: "MFW", 3: "LFRM", 4: "RCFG", 5: "START", 6: "RCAP", 7: "RCRC",
    8: "AGHIGH", 9: "SWITCH", 10: "GRESTORE", 11: "SHUTDOWN", 12: "GCAPTURE", 13: "DESYNC",
    15: "IPROG", 16: "CRCC", 17: "LTIMER", 18: "BSPI_READ", 19: "FALL_EDGE",
}

BLOCKS = {"CLB_IO_CLK": 0, "BLOCK_RAM": 1, "CFG_CLB": 2}
BLOCK_NAMES = {v: k for k, v in BLOCKS.items()}

CRC_POLY = 0x82F63B78


def icap_crc(addr, data, prev):
    poly = CRC_POLY << 1
    val = (addr << 32) | data
    crc = prev
    for _ in range(37):
        if (val & 1) != (crc & 1):
            crc ^= poly
        val >>= 1
        crc >>= 1
    return crc


ECC_WORD = 0x32
ECC_MASK = 0x1FFF


def icap_ecc(idx, data, ecc):
    val = idx * 32
    if idx > 0x25:
        val += 0x1360
    elif idx > 0x6:
        val += 0x1340
    else:
        val += 0x1320
    if idx == ECC_WORD:
        data &= ~ECC_MASK & 0xFFFFFFFF
    for i in range(32):
        if data & 1:
            ecc ^= val + i
        data >>= 1
    if idx == 0x64:
        v = ecc & 0xFFF
        v ^= v >> 8
        v ^= v >> 4
        v ^= v >> 2
        v ^= v >> 1
        ecc ^= (v & 1) << 12
    return ecc


def frame_ecc(frame):
    ecc = 0
    for i, w in enumerate(frame):
        ecc = icap_ecc(i, w, ecc)
    return ecc & ECC_MASK


def without_ecc(frame):
    f = list(frame)
    f[ECC_WORD] &= ~ECC_MASK & 0xFFFFFFFF
    return f


def far_fields(far):
    return {
        "block": BLOCK_NAMES.get((far >> 23) & 7, str((far >> 23) & 7)),
        "bottom": (far >> 22) & 1,
        "row": (far >> 17) & 0x1F,
        "column": (far >> 7) & 0x3FF,
        "minor": far & 0x7F,
    }


def far_make(block, bottom, row, column, minor):
    return (block << 23) | (bottom << 22) | (row << 17) | (column << 7) | minor


def far_str(far):
    f = far_fields(far)
    return f"0x{far:08x}({f['block']} {'B' if f['bottom'] else 'T'} r{f['row']} c{f['column']} m{f['minor']})"


class Part:
    def __init__(self, part=CONFIG["part"]):
        d = json.loads((DB / part / "part.json").read_text())
        self.idcode = d["idcode"]
        order = []
        for bname in sorted(BLOCKS, key=BLOCKS.get):
            for half, bottom in (("top", 0), ("bottom", 1)):
                rows = d["global_clock_regions"].get(half, {}).get("rows", {})
                for row in sorted(rows, key=int):
                    bus = rows[row]["configuration_buses"].get(bname)
                    if not bus:
                        continue
                    cols = bus["configuration_columns"]
                    for col in sorted(cols, key=int):
                        for minor in range(cols[col]["frame_count"]):
                            order.append(far_make(BLOCKS[bname], bottom, int(row), int(col), minor))
        self.order = order
        self.index = {f: i for i, f in enumerate(order)}
        cfg = []
        for half, bottom in (("top", 0), ("bottom", 1)):
            rows = d["global_clock_regions"].get(half, {}).get("rows", {})
            for row in sorted(rows, key=int):
                bus = rows[row]["configuration_buses"].get(CONFIG["mask_columns_from"])
                if bus:
                    for col in sorted(bus["configuration_columns"], key=int):
                        cfg.append(far_make(BLOCKS["CFG_CLB"], bottom, int(row), int(col), 0))
        self.cfg_order = cfg
        self.cfg_index = {f: i for i, f in enumerate(cfg)}

    def next_far(self, far):
        if far is None:
            return None, 0
        order, index = (self.cfg_order, self.cfg_index) if (far >> 23) & 7 == BLOCKS["CFG_CLB"] else (self.order, self.index)
        i = index.get(far)
        if i is None or i + 1 >= len(order):
            return None, 0
        nxt = order[i + 1]
        a, b = far_fields(far), far_fields(nxt)
        pad = CONFIG["row_pad_frames"] if (a["block"], a["bottom"], a["row"]) != (b["block"], b["bottom"], b["row"]) else 0
        return nxt, pad


def read_bit(path):
    raw = Path(path).read_bytes()
    header = {}
    if raw[:2] == b"\x00\x09":
        pos = 2 + 9
        pos += 2
        while pos < len(raw):
            key = chr(raw[pos])
            pos += 1
            if key == "e":
                n = struct.unpack(">I", raw[pos:pos + 4])[0]
                pos += 4
                header["e_len"] = n
                break
            n = struct.unpack(">H", raw[pos:pos + 2])[0]
            pos += 2
            header[key] = raw[pos:pos + n].rstrip(b"\x00").decode(errors="replace")
            pos += n
        body = raw[pos:]
    else:
        body = raw
    sync = body.find(struct.pack(">I", SYNC))
    if sync < 0:
        sys.exit(f"{path}: no sync word")
    words = list(struct.unpack(f">{(len(body) - sync - 4) // 4}I", body[sync + 4:sync + 4 + ((len(body) - sync - 4) // 4) * 4]))
    return {"header": header, "file_bytes": len(raw), "pre_sync_bytes": sync, "words": words}


def parse(path, part, strict=False):
    b = read_bit(path)
    words = b["words"]
    events = []
    frames = {}
    pads = []
    mfwr = []
    crc = 0
    crc_checks = []
    far = None
    pad_left = 0
    last_frame = None
    last_far = None
    far_since_fdri = False
    buffered = None
    last_reg = None
    fdri_bursts = []
    burst = None
    i = 0
    n = len(words)

    def write_reg(reg, data, idx):
        nonlocal crc, far, pad_left, last_frame, last_far, far_since_fdri, buffered, burst
        if reg == 0:
            ok = data[0] == crc
            crc_checks.append({"word": idx, "written": f"0x{data[0]:08x}", "computed": f"0x{crc:08x}", "match": ok})
            crc = 0
            return
        for w in data:
            crc = icap_crc(reg, w, crc)
        if reg == 1:
            far = data[-1]
            pad_left = 0
            burst = None
            far_since_fdri = True
            buffered = None
        elif reg == 4:
            name = CMDS.get(data[0], str(data[0]))
            events.append({"word": idx, "cmd": name})
            if name == "RCRC":
                crc = 0
        elif reg == 2:
            if burst is None:
                burst = {"word": idx, "start_far": far, "frames": 0, "pad_frames": 0, "words": 0}
                fdri_bursts.append(burst)
            burst["words"] += len(data)
            for k in range(0, len(data) - len(data) % CONFIG["words_per_frame"], CONFIG["words_per_frame"]):
                fr = data[k:k + CONFIG["words_per_frame"]]
                if strict and (pad_left or far is None) and buffered is not None:
                    frames[buffered[0]] = buffered[1]
                    burst["frames"] += 1
                    buffered = None
                if pad_left:
                    pads.append({"after_far": far, "nonzero": any(fr)})
                    pad_left -= 1
                    burst["pad_frames"] += 1
                    continue
                if far is None:
                    pads.append({"after_far": None, "nonzero": any(fr)})
                    burst["pad_frames"] += 1
                    continue
                if strict and buffered is not None:
                    frames[buffered[0]] = buffered[1]
                    burst["frames"] += 1
                if not strict:
                    frames[far] = fr
                    burst["frames"] += 1
                buffered = (far, fr)
                last_frame = fr
                last_far = far
                far_since_fdri = False
                nxt, pad = part.next_far(far)
                far, pad_left = nxt, pad
            if len(data) % CONFIG["words_per_frame"]:
                burst["partial_words"] = len(data) % CONFIG["words_per_frame"]
        elif reg == 10:
            dest = far if far_since_fdri or strict else last_far
            if strict and not far_since_fdri and buffered is not None:
                dest = buffered[0]
            mfwr.append({"word": idx, "far": dest, "has_data": last_frame is not None})
            if dest is not None and last_frame is not None:
                frames[dest] = last_frame
        if reg != 2:
            val = data[0] if len(data) == 1 else None
            events.append({"word": idx, "reg": REGS.get(reg, str(reg)), "n": len(data),
                           "value": f"0x{val:08x}" if val is not None else None})

    while i < n:
        w = words[i]
        t = w >> 29
        if t == 1:
            op = (w >> 27) & 3
            reg = (w >> 13) & 0x1F
            cnt = w & 0x7FF
            if op == 0:
                i += 1
                continue
            data = words[i + 1:i + 1 + cnt]
            last_reg = reg
            if op == 2 and cnt:
                write_reg(reg, data, i)
            elif op == 1:
                events.append({"word": i, "read": REGS.get(reg, str(reg)), "n": cnt})
            i += 1 + cnt
        elif t == 2:
            op = (w >> 27) & 3
            cnt = w & 0x7FFFFFF
            data = words[i + 1:i + 1 + cnt]
            if op == 2:
                write_reg(last_reg, data, i)
            i += 1 + cnt
        elif w == 0xFFFFFFFF or w == 0:
            i += 1
        else:
            events.append({"word": i, "unknown": f"0x{w:08x}"})
            i += 1
    return {"file": str(path), "header": b["header"], "file_bytes": b["file_bytes"],
            "pre_sync_bytes": b["pre_sync_bytes"], "words_after_sync": n, "events": events,
            "frames": frames, "pads": pads, "mfwr": mfwr, "crc_checks": crc_checks,
            "fdri_bursts": fdri_bursts}


def column_ranges(frames):
    groups = {}
    for far in sorted(frames):
        f = far_fields(far)
        key = (f["block"], f["bottom"], f["row"], f["column"])
        groups.setdefault(key, []).append(f["minor"])
    return groups


def summary(r, part):
    out = []
    h = r["header"]
    out.append(f"file {r['file']} ({r['file_bytes']} bytes)")
    if h:
        out.append(f"header design={h.get('a')} part={h.get('b')} date={h.get('c')} {h.get('d')} data_len={h.get('e_len')}")
    out.append(f"sync at byte {r['pre_sync_bytes']} of body; {r['words_after_sync']} words after sync")
    seq = []
    for e in r["events"]:
        if "cmd" in e:
            seq.append(e["cmd"])
        elif "reg" in e and e["reg"] not in ("CMD",):
            seq.append(f"{e['reg']}={e['value']}" if e["value"] else f"{e['reg']}[{e['n']}]")
        elif "read" in e:
            seq.append(f"read {e['read']}[{e['n']}]")
        elif "unknown" in e:
            seq.append(f"?{e['unknown']}")
    out.append("sequence: " + " ".join(seq))
    out.append(f"fdri bursts: {len(r['fdri_bursts'])}")
    for bst in r["fdri_bursts"]:
        sf = far_str(bst["start_far"]) if bst["start_far"] is not None else "None"
        out.append(f"  @word {bst['word']}: start {sf}, {bst['frames']} frames, {bst['pad_frames']} pad frames, {bst['words']} words"
                   + (f", {bst['partial_words']} trailing words" if bst.get("partial_words") else ""))
    nz = sum(1 for f in r["frames"].values() if any(f))
    out.append(f"frames written: {len(r['frames'])} ({nz} non-zero), mfwr writes: {len(r['mfwr'])}")
    bad_pads = [p for p in r["pads"] if p["nonzero"]]
    out.append(f"pad frames: {len(r['pads'])} ({len(bad_pads)} non-zero)")
    for key, minors in column_ranges(r["frames"]).items():
        out.append(f"  {key[0]} {'B' if key[1] else 'T'} r{key[2]} c{key[3]}: minors {min(minors)}..{max(minors)} ({len(minors)})")
    for c in r["crc_checks"]:
        out.append(f"crc check @word {c['word']}: written {c['written']} computed {c['computed']} {'OK' if c['match'] else 'MISMATCH'}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Series-7 configuration packet parser (UG470 ch.5)")
    ap.add_argument("bit", nargs="+")
    ap.add_argument("--json", help="write per-file summary json here (directory)")
    ap.add_argument("--strict", action="store_true",
                    help="do not commit the last frame of each FDRI write (it stays in the frame buffer until the next "
                         "frame or an MFWR); default commits every frame")
    a = ap.parse_args()
    part = Part()
    for p in a.bit:
        r = parse(p, part, strict=a.strict)
        print(summary(r, part))
        print()
        if a.json:
            d = Path(a.json)
            d.mkdir(parents=True, exist_ok=True)
            o = d / (Path(p).name + ".json")
            j = {k: v for k, v in r.items() if k != "frames"}
            j["frames"] = {f"0x{k:08x}": any(v) for k, v in sorted(r["frames"].items())}
            o.write_text(json.dumps(j, indent=1))


if __name__ == "__main__":
    main()
