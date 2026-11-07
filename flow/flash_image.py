import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "flash_base": 0x400000,
    "slot_size": 0x10000,
    "max_slots": 16,
    "flash_bytes": 16 * 1024 * 1024,
    "protect_below": 0x400000,
    "full_bitstream_bytes": 2192181,
    "magic": 0x50524631,
    "header_bytes": 16,
    "erased": 0xFF,
    "board": "arty_a7_35t",
    "loader": "openFPGALoader",
}


def die(msg):
    sys.exit(f"REFUSED: {msg}")


def check_record(binp):
    rec = binp.with_suffix(".check.json")
    if not rec.exists():
        die(f"{binp} has no safety record {rec.name}")
    r = json.loads(rec.read_text())
    sha = hashlib.sha256(binp.read_bytes()).hexdigest()
    if sha != r["sha256"]:
        die(f"{binp} sha256 {sha} does not match its safety record")
    if not r.get("outside_are_static_pads", False):
        die(f"{binp} safety record does not clear frames outside the region")
    sim = r.get("simulated", {})
    if sim and not (sim.get("crc_ok") and sim.get("frames_differ") == 0):
        die(f"{binp} safety record shows a failed simulated load")
    return r


def slot_image(data):
    if len(data) % 4:
        die(f"partial length {len(data)} is not a multiple of 4")
    words = struct.unpack(f">{len(data) // 4}I", data)
    total = sum(words) & 0xFFFFFFFF
    return struct.pack(">4I", CONFIG["magic"], len(data), total, 0) + data, total


def main():
    ap = argparse.ArgumentParser(description="Pack checked partial bitstreams into SPI flash slots for the rv_flash loader")
    ap.add_argument("--slot", action="append", default=[], metavar="N=PATH.bin", help="partial for slot N")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--sim-hex", help="also write a byte hex of the slot window for the iverilog flash model")
    ap.add_argument("--sim-words", help="also write slot 0 partial words (big-endian) as hex for the testbench")
    ap.add_argument("--sim-corrupt", type=int, action="append", default=[],
                    help="sim hex only: flip one data byte in slot N after the checksum is computed")
    ap.add_argument("--no-check", action="store_true", help="skip the .check.json safety records (simulation only)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    slots = {}
    for s in a.slot:
        n, p = s.split("=", 1)
        n = int(n, 0)
        if not 0 <= n < CONFIG["max_slots"]:
            die(f"slot {n} outside 0..{CONFIG['max_slots'] - 1}")
        slots[n] = Path(p)
    if not slots:
        die("no --slot given")
    if CONFIG["flash_base"] < CONFIG["protect_below"]:
        die("flash_base is below the protected configuration area")
    if CONFIG["flash_base"] < CONFIG["full_bitstream_bytes"]:
        die("flash_base overlaps the full bitstream")
    manifest = {"flash_base": hex(CONFIG["flash_base"]), "slot_size": hex(CONFIG["slot_size"]),
                "magic": hex(CONFIG["magic"]), "slots": []}
    window = bytearray([CONFIG["erased"]]) * (CONFIG["slot_size"] * (max(slots) + 1))
    for n in sorted(slots):
        binp = slots[n]
        rec = None if a.no_check else check_record(binp)
        data = binp.read_bytes()
        if len(data) + CONFIG["header_bytes"] > CONFIG["slot_size"]:
            die(f"{binp} ({len(data)} bytes) does not fit a {CONFIG['slot_size']}-byte slot")
        img, total = slot_image(data)
        off = CONFIG["flash_base"] + n * CONFIG["slot_size"]
        if off < CONFIG["protect_below"] or off + len(img) > CONFIG["flash_bytes"]:
            die(f"slot {n} offset {off:#x} outside the allowed flash range")
        dst = out / f"slot{n}.bin"
        dst.write_bytes(img)
        window[n * CONFIG["slot_size"]:n * CONFIG["slot_size"] + len(img)] = img
        if n in a.sim_corrupt:
            k = n * CONFIG["slot_size"] + CONFIG["header_bytes"] + len(data) // 2
            window[k] ^= 0x01
        manifest["slots"].append({
            "slot": n, "offset": hex(off), "file": dst.name, "bytes": len(img), "partial": str(binp),
            "partial_bytes": len(data), "partial_sha256": hashlib.sha256(data).hexdigest(),
            "image_sha256": hashlib.sha256(img).hexdigest(), "sum32": hex(total), "checked": rec is not None,
            "write_cmd": f"{CONFIG['loader']} -b {CONFIG['board']} -f -o {off:#x} --verify {dst.name}",
        })
        print(f"slot {n}: {binp} -> {dst} at {off:#x}, {len(img)} bytes, sum32 {total:#010x}")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    if a.sim_hex:
        Path(a.sim_hex).write_text("".join(f"{b:02x}\n" for b in window))
    if a.sim_words:
        data = slots[min(slots)].read_bytes()
        Path(a.sim_words).write_text("".join(f"{w:08x}\n" for w in struct.unpack(f">{len(data) // 4}I", data)))
    print(f"wrote {out / 'manifest.json'}")


if __name__ == "__main__":
    main()
