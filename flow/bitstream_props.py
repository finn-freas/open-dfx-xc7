import argparse
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bitparse

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "dry_run": True,
    "words_per_frame": 101,
    "cor0": {
        "GWE_CYCLE": (0, 3), "GTS_CYCLE": (3, 3), "LOCK_CYCLE": (6, 3), "MATCH_CYCLE": (9, 3),
        "DONE_CYCLE": (12, 3), "SSCLKSRC": (15, 2), "OSCFSEL": (17, 6), "ECLK_EN": (26, 1),
    },
    "startup_cycle": {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "KEEP": 7, "NOWAIT": 7},
    "startupclk": {"CCLK": 0, "USERCLK": 1, "JTAGCLK": 2},
    "configrate": {"33": 33},
    "bspi": {"4": 0x0000026B},
    "extmasterclk": {"DISABLE": None, "DIV-1": 0x30},
    "spi_fall_edge": {"YES": True, "NO": False},
    "compress_ctl1": 0x00001000,
    "set_property": re.compile(r"^\s*set_property\s+(-dict\s+\{(?P<dict>[^}]*)\}|(?P<key>\S+)\s+(?P<val>\S+))\s+"
                               r"\[current_design\]"),
    "type1": lambda op, reg, n: (1 << 29) | (op << 27) | (reg << 13) | n,
    "type2": lambda op, n: (2 << 29) | (op << 27) | n,
    "noop": 0x20000000,
    "regs": {v: k for k, v in bitparse.REGS.items()},
    "cmds": {v: k for k, v in bitparse.CMDS.items()},
}


def read_props(xdc):
    props = {}
    for ln in Path(xdc).read_text().splitlines():
        m = CONFIG["set_property"].match(ln.split("#")[0])
        if not m:
            continue
        if m.group("dict") is not None:
            kv = m.group("dict").split()
            pairs = zip(kv[0::2], kv[1::2])
        else:
            pairs = [(m.group("key"), m.group("val"))]
        for k, v in pairs:
            if k.upper().startswith("BITSTREAM."):
                props[k.upper()] = v.strip('"')
    return props


def packets(words):
    out, i = [], 0
    while i < len(words):
        w = words[i]
        t = w >> 29
        if t == 1:
            op, reg, n = (w >> 27) & 3, (w >> 13) & 0x1F, w & 0x7FF
            out.append({"t": 1, "op": op, "reg": reg, "data": list(words[i + 1:i + 1 + n])} if op else {"t": 0})
            i += 1 + (n if op else 0)
        elif t == 2:
            n = w & 0x7FFFFFF
            out.append({"t": 2, "op": (w >> 27) & 3, "data": list(words[i + 1:i + 1 + n])})
            i += 1 + n
        else:
            out.append({"t": -1, "word": w})
            i += 1
    return out


def serialize(pkts):
    words = []
    for p in pkts:
        if p["t"] == 0:
            words.append(CONFIG["noop"])
        elif p["t"] == 1:
            words.append(CONFIG["type1"](p["op"], p["reg"], len(p["data"])))
            words += p["data"]
        elif p["t"] == 2:
            words.append(CONFIG["type2"](p["op"], len(p["data"])))
            words += p["data"]
        else:
            words.append(p["word"])
    return words


def wr(reg, *data):
    return {"t": 1, "op": 2, "reg": CONFIG["regs"][reg], "data": list(data)}


def cmd(name):
    return wr("CMD", CONFIG["cmds"][name])


def noops(n):
    return [{"t": 0} for _ in range(n)]


def is_reg(p, reg):
    return p["t"] == 1 and p["op"] == 2 and p["reg"] == CONFIG["regs"][reg]


def is_cmd(p, name):
    return is_reg(p, "CMD") and p["data"] == [CONFIG["cmds"][name]]


def field(word, name, value):
    lo, width = CONFIG["cor0"][name]
    mask = ((1 << width) - 1) << lo
    return (word & ~mask) | ((value << lo) & mask)


def apply_settings(pkts, props, notes):
    pkts = list(pkts)
    unsupported = []
    cor0 = next(i for i, p in enumerate(pkts) if is_reg(p, "COR0"))
    word = pkts[cor0]["data"][0]
    for prop, name in (("BITSTREAM.STARTUP.GWE_CYCLE", "GWE_CYCLE"), ("BITSTREAM.STARTUP.GTS_CYCLE", "GTS_CYCLE"),
                       ("BITSTREAM.STARTUP.DONE_CYCLE", "DONE_CYCLE"), ("BITSTREAM.STARTUP.LCK_CYCLE", "LOCK_CYCLE"),
                       ("BITSTREAM.STARTUP.MATCH_CYCLE", "MATCH_CYCLE")):
        if prop in props:
            v = CONFIG["startup_cycle"].get(props[prop].upper())
            if v is None:
                unsupported.append(prop)
            else:
                word = field(word, name, v)
    if "BITSTREAM.STARTUP.STARTUPCLK" in props:
        v = CONFIG["startupclk"].get(props["BITSTREAM.STARTUP.STARTUPCLK"].upper())
        if v is None:
            unsupported.append("BITSTREAM.STARTUP.STARTUPCLK")
        else:
            word = field(word, "SSCLKSRC", v)
    if "BITSTREAM.CONFIG.CONFIGRATE" in props:
        v = CONFIG["configrate"].get(props["BITSTREAM.CONFIG.CONFIGRATE"])
        if v is None:
            unsupported.append("BITSTREAM.CONFIG.CONFIGRATE")
        else:
            word = field(word, "OSCFSEL", v)
    if "BITSTREAM.CONFIG.EXTMASTERCCLK_EN" in props:
        v = props["BITSTREAM.CONFIG.EXTMASTERCCLK_EN"].upper()
        if v not in CONFIG["extmasterclk"]:
            unsupported.append("BITSTREAM.CONFIG.EXTMASTERCCLK_EN")
        elif CONFIG["extmasterclk"][v] is not None:
            word = field(field(word, "ECLK_EN", 1), "OSCFSEL", CONFIG["extmasterclk"][v])
    if word != pkts[cor0]["data"][0]:
        notes.append(f"COR0 0x{pkts[cor0]['data'][0]:08x} -> 0x{word:08x}")
        pkts[cor0] = wr("COR0", word)
    if "BITSTREAM.CONFIG.USR_ACCESS" in props:
        v = int(props["BITSTREAM.CONFIG.USR_ACCESS"], 16)
        rbcrc = next(i for i, p in enumerate(pkts) if is_reg(p, "RBCRC_SW"))
        pkts.insert(rbcrc, wr("AXSS", v))
        notes.append(f"AXSS 0x{v:08x}")
    if "BITSTREAM.CONFIG.SPI_BUSWIDTH" in props:
        v = CONFIG["bspi"].get(props["BITSTREAM.CONFIG.SPI_BUSWIDTH"])
        if v is None:
            unsupported.append("BITSTREAM.CONFIG.SPI_BUSWIDTH")
        else:
            timer = next(i for i, p in enumerate(pkts) if is_reg(p, "TIMER"))
            pkts[timer:timer] = [wr("BSPI", v), cmd("BSPI_READ"), {"t": 0}]
            notes.append(f"BSPI 0x{v:08x}, CMD BSPI_READ")
    if "BITSTREAM.CONFIG.SPI_FALL_EDGE" in props:
        v = CONFIG["spi_fall_edge"].get(props["BITSTREAM.CONFIG.SPI_FALL_EDGE"].upper())
        if v is None:
            unsupported.append("BITSTREAM.CONFIG.SPI_FALL_EDGE")
        elif v:
            switch = next(i for i, p in enumerate(pkts) if is_cmd(p, "SWITCH"))
            pkts.insert(switch, cmd("FALL_EDGE"))
            notes.append("CMD FALL_EDGE")
    return pkts, unsupported


def compress_ctl1(pkts):
    pkts = list(pkts)
    v = CONFIG["compress_ctl1"]
    i = next(i for i, p in enumerate(pkts) if is_reg(p, "MASK") and i + 1 < len(pkts) and is_reg(pkts[i + 1], "CTL1"))
    pkts[i:i + 2] = [wr("MASK", v), wr("CTL1", v)]
    lfrm = next(i for i, p in enumerate(pkts) if is_cmd(p, "LFRM"))
    pkts[lfrm + 1:lfrm + 1] = [wr("MASK", v), wr("CTL1", 0)]
    return pkts


def keep_length(pkts, words):
    extra = len(serialize(pkts)) - words
    out = list(pkts)
    while extra > 0 and out and out[-1]["t"] == 0:
        out.pop()
        extra -= 1
    return out


def compress(pkts, bit):
    part = bitparse.Part()
    frames = bitparse.parse(str(bit), part, True)["frames"]
    start = next(i for i, p in enumerate(pkts) if is_reg(p, "FAR") and i + 1 < len(pkts) and is_cmd(pkts[i + 1], "WCFG"))
    end = next(i for i in range(start, len(pkts)) if pkts[i]["t"] == 2)
    rows = {}
    for far, fr in frames.items():
        f = bitparse.far_fields(far)
        rows.setdefault((f["block"], f["bottom"], f["row"]), []).append((far, tuple(fr)))
    zero = tuple([0] * CONFIG["words_per_frame"])
    out = []
    first = True

    def fdri(far, data, is_bram):
        nonlocal first
        if first:
            out.extend([wr("FAR", far), cmd("WCFG"), {"t": 0}])
            first = False
        else:
            out.extend([cmd("WCFG"), {"t": 0}, wr("FAR", far), {"t": 0}])
        out.append(wr("FDRI", *[w for fr in data for w in fr]))

    def copies(fars, is_bram):
        settle = noops(8) if is_bram else []
        out.extend([cmd("MFW")] + noops(12) + [wr("MFWR", *([0] * 8))] + settle)
        for far in fars:
            out.extend([wr("FAR", far), wr("MFWR", *([0] * 4))] + settle)

    for key, row in rows.items():
        is_bram = key[0] == "BLOCK_RAM"
        written = set()
        zeros = [far for far, fr in row if fr == zero]
        if len(zeros) > 1:
            fdri(zeros[0], [zero], is_bram)
            copies(zeros[1:], is_bram)
            written.update(zeros)
        order = [far for far, _ in row]
        content = dict(row)
        pos = {far: i for i, far in enumerate(order)}
        i = 0
        while i < len(order):
            if order[i] in written:
                i += 1
                continue
            run = []
            while i < len(order) and order[i] not in written:
                far = order[i]
                run.append(far)
                written.add(far)
                i += 1
                later = [f for f in order[i:] if f not in written and content[f] == content[far]]
                if later:
                    break
                if i < len(order) and part.next_far(far)[0] != order[i]:
                    break
            last = run[-1]
            later = [f for f in order[pos[last] + 1:] if f not in written and content[f] == content[last]]
            fdri(run[0], [content[f] for f in run] + ([] if later else [zero]), is_bram)
            if later:
                copies(later, is_bram)
                written.update(later)
    flush = [] if out[-8:] == noops(8) else noops(8)
    return pkts[:start] + out + flush + pkts[end + 1:]


def crc_words(pkts):
    crc = 0
    out = []
    last = None
    configuring = False
    for p in pkts:
        if is_cmd(p, "WCFG"):
            configuring = True
        if p["t"] == 2:
            reg = last
        elif p["t"] == 1 and p["op"] == 2:
            reg = p["reg"]
            last = reg
        else:
            out.append(p)
            continue
        if is_cmd(p, "RCRC") and configuring:
            out.append(wr("CRC", crc))
            crc = 0
            continue
        for w in p["data"]:
            crc = bitparse.icap_crc(reg, w, crc)
        if is_cmd(p, "RCRC"):
            crc = 0
        out.append(p)
    return out


def write_bit(src, dst, words):
    raw = Path(src).read_bytes()
    pos = 2 + 9 + 2
    while chr(raw[pos]) != "e":
        pos += 3 + struct.unpack(">H", raw[pos + 1:pos + 3])[0]
    sync = raw.find(struct.pack(">I", bitparse.SYNC), pos)
    pre = raw[pos + 5:sync + 4]
    body = pre + struct.pack(f">{len(words)}I", *words)
    out = raw[:pos + 1] + struct.pack(">I", len(body)) + body
    Path(dst).write_bytes(out)
    return len(out)


def frames_of(pkts, frames_bit):
    if frames_bit is None:
        return pkts
    src = next(p for p in packets(bitparse.read_bit(frames_bit)["words"]) if p["t"] == 2)
    return [dict(p, data=src["data"]) if p["t"] == 2 else p for p in pkts]


def build(bit, props, frames_bit, notes):
    words = bitparse.read_bit(bit)["words"]
    pkts = packets(words)
    pkts, unsupported = apply_settings(pkts, props, notes)
    pkts = keep_length(pkts, len(words))
    if props.get("BITSTREAM.GENERAL.COMPRESS", "FALSE").upper() == "TRUE":
        pkts = compress(compress_ctl1(pkts), frames_bit)
        notes.append(f"compressed: identical frames of a row written once, then copied with MFWR; "
                     f"MASK/CTL1 0x{CONFIG['compress_ctl1']:08x}")
    else:
        pkts = frames_of(pkts, None if frames_bit == bit else frames_bit)
    if props.get("BITSTREAM.GENERAL.CRC", "ENABLE").upper() != "DISABLE":
        pkts = crc_words(pkts)
        notes.append("CRC words instead of RCRC")
    return serialize(pkts), unsupported


def process(bit, xdc, out, dry):
    props = read_props(xdc)
    rec = {"bit": str(bit), "xdc": str(xdc), "out": str(out), "props": props}
    if not props:
        rec["result"] = "no BITSTREAM property; nothing to do"
        return rec
    if dry:
        rec["result"] = "dry"
        return rec
    notes = []
    words, unsupported = build(bit, props, bit, notes)
    rec["notes"] = notes
    rec["unsupported"] = unsupported
    rec["bytes"] = write_bit(bit, out, words)
    part = bitparse.Part()
    a, b = bitparse.parse(str(bit), part), bitparse.parse(str(out), part)
    zero = [0] * CONFIG["words_per_frame"]
    rec["frames_differ"] = sum(a["frames"].get(k, zero) != b["frames"].get(k, zero)
                               for k in set(a["frames"]) | set(b["frames"]))
    rec["crc_checks"] = b["crc_checks"]
    sa, sb = bitparse.parse(str(bit), part, True), bitparse.parse(str(out), part, True)
    rec["frames_differ_strict"] = sum(sa["frames"].get(k, zero) != sb["frames"].get(k, zero)
                                      for k in set(sa["frames"]) | set(sb["frames"]))
    return rec


def control_words(bit):
    seq = []
    for p in packets(bitparse.read_bit(bit)["words"]):
        if p["t"] == 0:
            seq.append("NOOP")
        elif p["t"] == 2:
            seq.append(f"FDRI type2 x{len(p['data'])}")
        elif p["t"] == 1:
            name = bitparse.REGS.get(p["reg"], str(p["reg"]))
            if name in ("FDRI", "MFWR", "FAR"):
                seq.append(f"{name} x{len(p['data'])}")
            elif name == "CRC":
                seq.append("CRC <value>")
            else:
                seq.append(f"{name} " + " ".join(f"0x{v:08x}" for v in p["data"]))
        else:
            seq.append(f"word 0x{p['word']:08x}")
    return seq


def compare_vivado(out, vivado):
    a, b = control_words(vivado), control_words(out)
    regs = lambda seq: [s for s in seq if not s.startswith(("NOOP", "FDRI", "MFWR", "FAR"))]
    ra, rb = regs(a), regs(b)
    return {"vivado": str(vivado), "register_writes_identical": ra == rb,
            "only_vivado": [s for s in ra if s not in rb], "only_open": [s for s in rb if s not in ra],
            "packets_identical": a == b, "packets": [len(a), len(b)]}


def compare_on_vivado_frames(bit, xdc, vivado):
    words, _ = build(bit, read_props(xdc), vivado, [])
    ref = bitparse.read_bit(vivado)["words"]
    diff = next((i for i, (a, b) in enumerate(zip(words, ref)) if a != b), None)
    if diff is None and len(words) != len(ref):
        diff = min(len(words), len(ref))
    return {"words_identical": diff is None, "words": [len(ref), len(words)], "first_difference": diff}


def main():
    ap = argparse.ArgumentParser(description="apply the XDC's BITSTREAM.* properties to an xc7frames2bit bitstream")
    ap.add_argument("bit")
    ap.add_argument("xdc")
    ap.add_argument("out")
    ap.add_argument("--vivado", help="a Vivado bitstream of the same settings: compare the register writes")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    rec = process(Path(a.bit), Path(a.xdc), Path(a.out), dry)
    if a.vivado and not dry and Path(a.out).exists():
        rec["compare"] = compare_vivado(Path(a.out), Path(a.vivado))
        rec["compare"]["on_vivado_frames"] = compare_on_vivado_frames(Path(a.bit), Path(a.xdc), Path(a.vivado))
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
