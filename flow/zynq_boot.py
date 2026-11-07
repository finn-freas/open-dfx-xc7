import argparse
import hashlib
import json
import os
import shlex
import struct
import subprocess
import sys
import time
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ps7init

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "dry_run": True,
    "uboot_src": ROOT / "upstream" / "u-boot_u-boot",
    "uboot_rev": "v2025.10",
    "uboot_defconfig": "xilinx_zynq_virt_defconfig",
    "uboot_fragment": ["# CONFIG_FIT_SIGNATURE is not set",
                       "# CONFIG_TOOLS_MKEFICAPSULE is not set", "# CONFIG_TOOLS_MKFWUMDATA is not set"],
    "uboot_out": ROOT / "build" / "zynq" / "uboot",
    "tools_root": ROOT / "toolchain" / "zynq" / "root",
    "hostlib": ROOT / "build" / "zynq" / "hostlib",
    "hostlib_links": {"libssl.so": "/usr/lib/x86_64-linux-gnu/libssl.so.3",
                      "libcrypto.so": "/usr/lib/x86_64-linux-gnu/libcrypto.so.3", "bin/dd": "/usr/bin/gnudd"},
    "cross": "arm-none-eabi-",
    "jobs": 2,
    "app_cflags": ["-mcpu=cortex-a9", "-marm", "-O2", "-g", "-ffreestanding", "-fno-builtin", "-nostdlib", "-Wall",
                   "-Wextra"],
    "spl_reserved": [(0x00000000, 0x00030000, "SPL in OCM"), (0x00100000, 0x00200000, "SPL BSS"),
                     (0x00200000, 0x02200000, "SPL stack/malloc"), (0x10000000, 0x10800000, "SPL FIT buffer")],
    "ocm_max": 0x30000,
    "fit_addr": 0x10000000,
    "fpga_load": 0x06000000,
    "fit_payload": "u-boot.img",
    "sd_mb": 64,
    "sd_part_start_s": 2048,
    "bit_sync": bytes.fromhex("aa995566"),
    "qemu": "qemu-system-arm",
    "qemu_machine": "xilinx-zynq-a9",
    "qemu_mem": "1G",
    "qemu_timeout_s": 240,
    "qemu_done": "ofx-app: ",
    "qemu_expect": ["U-Boot SPL 2025.10", "ofx-app: ps7_axi_z7 bare-metal test", "FPGA0_CLK_CTRL = 0x00400500"],
    "openocd_board": "interface/ftdi/digilent_jtag_smt2.cfg",
    "openfpgaloader": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "openFPGALoader",
    "openocd": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "openocd",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def env():
    e = dict(os.environ)
    tr = CONFIG["tools_root"]
    e["PATH"] = f"{CONFIG['hostlib'] / 'bin'}:{tr / 'usr' / 'bin'}:{tr / 'usr' / 'sbin'}:{e['PATH']}"
    e["LD_LIBRARY_PATH"] = f"{tr / 'usr' / 'lib' / 'x86_64-linux-gnu'}:{e.get('LD_LIBRARY_PATH', '')}"
    return e


def run(cmd, dry, cwd=None, log=None, check=True):
    print(f"[{'dry' if dry else 'run'}] {' '.join(shlex.quote(str(c)) for c in cmd)}" + (f"  > {log}" if log else ""),
          flush=True)
    if dry:
        return 0
    if log:
        with open(log, "w") as f:
            r = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env(), stdout=f, stderr=subprocess.STDOUT)
    else:
        r = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env())
    if check and r.returncode:
        sys.exit(f"zynq_boot: failed (exit {r.returncode}): {cmd[0]}" + (f", see {log}" if log else ""))
    return r.returncode


def stamp_ok(path, key):
    return path.exists() and json.loads(path.read_text()).get("key") == key


def uboot(board_z, dry):
    out = CONFIG["uboot_out"]
    src = CONFIG["uboot_src"]
    frag = [f'CONFIG_DEFAULT_DEVICE_TREE="{board_z["uboot_dt"]}"', f'CONFIG_OF_LIST="{board_z["uboot_dt"]}"'] + \
        CONFIG["uboot_fragment"]
    rev = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    tag = subprocess.run(["git", "-C", str(src), "describe", "--tags", "--exact-match"], capture_output=True,
                         text=True).stdout.strip()
    if tag != CONFIG["uboot_rev"]:
        sys.exit(f"zynq_boot: {src} is at {tag or rev}, not {CONFIG['uboot_rev']}")
    key = hashlib.sha256(json.dumps([rev, CONFIG["uboot_defconfig"], frag]).encode()).hexdigest()
    stamp = out / ".ofx-uboot.json"
    res = {"rev": rev, "tag": tag, "dir": str(out), "spl_bin": str(out / "spl" / "u-boot-spl.bin"),
           "spl_elf": str(out / "spl" / "u-boot-spl"), "boot_bin": str(out / "spl" / "boot.bin"),
           "mkimage": str(out / "tools" / "mkimage"), "ps_init": str(src / board_z["ps_init"])}
    if stamp_ok(stamp, key) and Path(res["boot_bin"]).exists():
        print(f"[cached] U-Boot {tag} SPL for {board_z['uboot_dt']}: {out}")
        return res
    if not dry:
        out.mkdir(parents=True, exist_ok=True)
        for name, target in CONFIG["hostlib_links"].items():
            link = CONFIG["hostlib"] / name
            link.parent.mkdir(parents=True, exist_ok=True)
            if not link.is_symlink():
                link.symlink_to(target)
        (out / "ofx.fragment").write_text("\n".join(frag) + "\n")
    tr = CONFIG["tools_root"]
    mk = ["make", "-C", src, f"O={out}", f"CROSS_COMPILE={CONFIG['cross']}",
          f"HOSTCFLAGS=-I{tr / 'usr' / 'include'} -I{tr / 'usr' / 'include' / 'x86_64-linux-gnu'}",
          f"HOSTLDFLAGS=-L{CONFIG['hostlib']}"]
    run(mk + [CONFIG["uboot_defconfig"]], dry, log=out / "defconfig.log")
    run([src / "scripts" / "kconfig" / "merge_config.sh", "-m", "-O", out, out / ".config", out / "ofx.fragment"], dry,
        cwd=src, log=out / "merge.log")
    run(mk + ["olddefconfig"], dry, log=out / "olddefconfig.log")
    run(mk + [f"-j{CONFIG['jobs']}"], dry, log=out / "build.log")
    if not dry:
        cfg = (out / ".config").read_text()
        for line in frag:
            if line not in cfg.splitlines():
                sys.exit(f"zynq_boot: U-Boot .config lost fragment line {line!r}")
        stamp.write_text(json.dumps({"key": key, "rev": rev}) + "\n")
    return res


def elf_segments(path):
    d = Path(path).read_bytes()
    if d[:4] != b"\x7fELF" or d[4] != 1 or d[5] != 1:
        sys.exit(f"zynq_boot: {path} is not a 32-bit little-endian ELF")
    entry, phoff = struct.unpack_from("<II", d, 24)
    phentsize, phnum = struct.unpack_from("<HH", d, 42)
    segs = []
    for i in range(phnum):
        p_type, _, _, paddr, filesz, memsz = struct.unpack_from("<IIIIII", d, phoff + i * phentsize)
        if p_type == 1 and memsz:
            segs.append((paddr, paddr + memsz, filesz))
    return entry, segs


def overlaps(a0, a1, b0, b1):
    return a0 < b1 and b0 < a1


def app(proj_dir, z, out, dry):
    srcs = [proj_dir / s for s in z["app"]]
    ld = proj_dir / z["app_ld"]
    elf, binf = out / "app.elf", out / "app.bin"
    run([CONFIG["cross"] + "gcc"] + CONFIG["app_cflags"] + ["-T", ld, "-Wl,-Map," + str(out / "app.map")] + srcs +
        ["-lgcc", "-o", elf], dry)
    run([CONFIG["cross"] + "objcopy", "-O", "binary", elf, binf], dry)
    if dry:
        return {"elf": str(elf), "bin": str(binf)}
    entry, segs = elf_segments(elf)
    lo, hi = min(s[0] for s in segs), max(s[1] for s in segs)
    if entry != lo:
        print(f"zynq_boot: note: app entry 0x{entry:08x} is not its load address 0x{lo:08x}; the FIT jumps to the entry")
    for r0, r1, what in CONFIG["spl_reserved"]:
        if overlaps(lo, hi, r0, r1):
            sys.exit(f"zynq_boot: app 0x{lo:08x}-0x{hi:08x} overlaps {what} 0x{r0:08x}-0x{r1:08x}; move it in {ld}")
    return {"elf": str(elf), "bin": str(binf), "load": lo, "end": hi, "entry": entry, "bin_bytes": binf.stat().st_size}


def bit_payload(data):
    if data[:2] != b"\x00\x09":
        return data
    n = struct.unpack(">H", data[:2])[0]
    p = 2 + n + 2
    while p < len(data):
        k = data[p]
        p += 1
        if k == 0x65:
            ln = struct.unpack(">I", data[p:p + 4])[0]
            return data[p + 4:p + 4 + ln]
        ln = struct.unpack(">H", data[p:p + 2])[0]
        p += 2 + ln
    sys.exit("zynq_boot: .bit header has no data field")


def pl_bin(bit, out, dry):
    dst = out / "pl.bin"
    print(f"[{'dry' if dry else 'run'}] strip the .bit header: {bit} -> {dst}")
    if dry:
        return {"bin": str(dst)}
    raw = bit_payload(Path(bit).read_bytes())
    pos = raw.find(CONFIG["bit_sync"])
    if pos < 0 or pos > 256:
        sys.exit(f"zynq_boot: no sync word near the start of {bit}")
    dst.write_bytes(raw)
    return {"bin": str(dst), "bytes": len(raw), "sync_offset": pos, "bit_sha256": sha(bit)}


ITS = """/dts-v1/;
/ {{
	description = "ofx {name}: PL bitstream and bare-metal app for U-Boot SPL";
	#address-cells = <1>;
	images {{
		app {{
			description = "bare-metal app";
			data = /incbin/("app.bin");
			type = "firmware";
			arch = "arm";
			compression = "none";
			load = <0x{load:08x}>;
			entry = <0x{entry:08x}>;
			hash-1 {{ algo = "crc32"; }};
		}};
		fpga {{
			description = "PL bitstream";
			data = /incbin/("pl.bin");
			type = "fpga";
			arch = "arm";
			compression = "none";
			load = <0x{fpga:08x}>;
			compatible = "u-boot,fpga-legacy";
			hash-1 {{ algo = "crc32"; }};
		}};
	}};
	configurations {{
		default = "conf";
		conf {{
			description = "{name}";
			firmware = "app";
			loadables = "fpga";
		}};
	}};
}};
"""


def fit(name, ub, a, pl, out, dry):
    its, itb = out / "ofx.its", out / "ofx.itb"
    if not dry:
        if overlaps(a["load"], a["end"], CONFIG["fpga_load"], CONFIG["fpga_load"] + pl["bytes"]):
            sys.exit("zynq_boot: the app overlaps the FPGA image load area")
        for r0, r1, what in CONFIG["spl_reserved"]:
            if overlaps(CONFIG["fpga_load"], CONFIG["fpga_load"] + pl["bytes"], r0, r1):
                sys.exit(f"zynq_boot: the FPGA image load area overlaps {what}")
        its.write_text(ITS.format(name=name, load=a["load"], entry=a["entry"], fpga=CONFIG["fpga_load"]))
    run([ub["mkimage"], "-f", its, itb], dry, cwd=out, log=out / "mkimage.log")
    run([ub["mkimage"], "-l", itb], dry, log=out / "fit_list.txt")
    return {"itb": str(itb)}


def zynqimage_check(path):
    d = Path(path).read_bytes()
    w = struct.unpack_from("<12I", d, 0x20)
    width, ident = w[0], w[1]
    src_off, length, load, start, total = w[4], w[5], w[6], w[7], w[8]
    csum = (~sum(w[:10]) & 0xFFFFFFFF)
    return {"width_detect": hex(width), "id": d[0x24:0x28].decode(errors="replace"), "src_offset": hex(src_off),
            "length": length, "load": hex(load), "start": hex(start), "total": total,
            "checksum_ok": csum == w[10], "file_bytes": len(d), "spl_bytes": len(d) - src_off,
            "ok": ident == 0x584C4E58 and width == 0xAA995566 and csum == w[10] and src_off < len(d) <= length
            and len(d) - src_off <= CONFIG["ocm_max"]}


def sdimg(ub, itb, out, dry):
    img = out / "sd.img"
    start = CONFIG["sd_part_start_s"]
    if not dry and img.exists():
        img.unlink()
    run(["truncate", "-s", f"{CONFIG['sd_mb']}M", img], dry)
    if not dry:
        r = subprocess.run(["sfdisk", "-q", str(img)], input=f"start={start}, type=c, bootable\n", text=True,
                           capture_output=True)
        if r.returncode:
            sys.exit(f"zynq_boot: sfdisk: {r.stderr}")
    sectors = CONFIG["sd_mb"] * 2048 - start
    run(["mkfs.vfat", "-F", "32", "-n", "BOOT", "--offset", str(start), img, str(sectors // 2)], dry,
        log=out / "mkfs.log")
    part = f"{img}@@{start * 512}"
    run(["mcopy", "-i", part, ub["boot_bin"], "::boot.bin"], dry)
    run(["mcopy", "-i", part, itb, "::" + CONFIG["fit_payload"]], dry)
    if dry:
        return {"img": str(img)}
    ls = subprocess.run(["mdir", "-i", part, "-b", "::"], capture_output=True, text=True, env=env()).stdout.split()
    return {"img": str(img), "files": ls}


def qemu(mode, ub, itb, sd, out, dry):
    log = out / f"qemu_{mode}_uart1.txt"
    cmd = [CONFIG["qemu"], "-M", f"{CONFIG['qemu_machine']},boot-mode={mode}", "-m", CONFIG["qemu_mem"],
           "-display", "none", "-monitor", "none", "-serial", "null", "-serial", f"file:{log}",
           "-device", f"loader,file={ub['spl_bin']},addr=0x0,force-raw=on"]
    if mode == "jtag":
        cmd += ["-device", f"loader,file={itb},addr=0x{CONFIG['fit_addr']:08x},force-raw=on"]
    else:
        cmd += ["-drive", f"if=sd,format=raw,file={sd}"]
    print(f"[{'dry' if dry else 'run'}] {' '.join(shlex.quote(str(c)) for c in cmd)}", flush=True)
    if dry:
        return {"mode": mode}
    if log.exists():
        log.unlink()
    p = subprocess.Popen([str(c) for c in cmd], env=env(), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    t0 = time.time()
    text = ""
    while time.time() - t0 < CONFIG["qemu_timeout_s"] and p.poll() is None:
        time.sleep(2)
        text = log.read_text(errors="replace") if log.exists() else ""
        if "ofx-app: PASS" in text or "ofx-app: FAIL" in text or "not touching M_AXI_GP0" in text or "TRAP" in text:
            break
    p.terminate()
    p.wait()
    text = log.read_text(errors="replace") if log.exists() else ""
    seen = {e: e in text for e in CONFIG["qemu_expect"]}
    return {"mode": mode, "seconds": round(time.time() - t0, 1), "uart1": str(log), "expect": seen,
            "ok": all(seen.values()), "fpga_load_failed": "Cannot load the image to the FPGA" in text,
            "lines": [l for l in text.splitlines() if l.strip()]}


def jtag_script(board, ub, a, bit, ps7tcl, out, dry):
    s = out / "jtag_boot.tcl"
    text = f"""# ofx JTAG boot for {board['board']['name']}: OpenOCD + ps7_init.tcl (from U-Boot's ps7_init_gpl.c).
# Set the boot-mode jumper to JTAG, then:
#   openocd -f {CONFIG['openocd_board']} -f target/zynq_7000.cfg -f {s}
init
halt
source {ps7tcl}
ps7_init
pld load zynq_pl.pld {bit}
ps7_post_config
load_image {a['elf']}
resume 0x{a.get('entry', 0):08x}
"""
    print(f"[{'dry' if dry else 'run'}] write {s}")
    if not dry:
        s.write_text(text)
    return {"openocd_script": str(s),
            "openocd": f"{CONFIG['openocd']} -f {CONFIG['openocd_board']} -f target/zynq_7000.cfg -f {s}",
            "openfpgaloader_pl_only": f"{CONFIG['openfpgaloader']} -b {board['board'].get('openfpgaloader_board')} {bit}"}


def main():
    ap = argparse.ArgumentParser(description="Zynq-7000 PS boot files from open sources: U-Boot SPL (ps7_init), "
                                 "FIT with the PL bitstream and a bare-metal app, boot.bin, SD image, OpenOCD JTAG script")
    ap.add_argument("project", help="ofx.toml with a [zynq] section")
    ap.add_argument("--bit", help="PL bitstream (default: the project's build/impl/<top>.bit)")
    ap.add_argument("--out", help="output directory (default: <build>/boot)")
    ap.add_argument("--qemu", action="store_true", help="also boot SPL + FIT in QEMU xilinx-zynq-a9 (jtag and sd modes)")
    ap.add_argument("--run", action="store_true", help="do it (default: dry run)")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    pf = Path(a.project).resolve()
    if pf.is_dir():
        pf = pf / "ofx.toml"
    proj = tomllib.loads(pf.read_text())
    z = proj.get("zynq")
    if not z or "app" not in z or "app_ld" not in z:
        sys.exit(f"zynq_boot: {pf} needs [zynq] app = [...] and app_ld = \"...\"")
    board_name = proj["project"].get("board")
    if not board_name:
        sys.exit("zynq_boot: [project] board must be a Zynq preset with a [zynq] section")
    board = tomllib.loads((ROOT / "boards" / f"{board_name}.toml").read_text())
    bz = board.get("zynq")
    if not bz:
        sys.exit(f"zynq_boot: boards/{board_name}.toml has no [zynq] section (PS boot not supported for it)")
    pdir = pf.parent
    build = pdir / proj["project"].get("build_dir", "build")
    bit = Path(a.bit) if a.bit else build / "impl" / f"{proj['project']['top']}.bit"
    out = Path(a.out) if a.out else build / "boot"
    if not dry:
        if not bit.exists():
            sys.exit(f"zynq_boot: {bit} does not exist (run `ofx build --run`)")
        out.mkdir(parents=True, exist_ok=True)
    ub = uboot(bz, dry)
    ap_ = app(pdir, z, out, dry)
    pl = pl_bin(bit, out, dry)
    ft = fit(proj["project"]["name"], ub, ap_, pl, out, dry)
    sd = sdimg(ub, ft["itb"], out, dry)
    ps7tcl = out / "ps7_init.tcl"
    print(f"[{'dry' if dry else 'run'}] ps7_init.tcl from {ub['ps_init']}")
    st = None
    if not dry:
        ps7tcl.write_text(ps7init.tcl(ps7init.parse(ub["ps_init"]), ub["ps_init"]))
        st = ps7init.selftest(ub["ps_init"], ps7tcl, out / "ps7init_selftest")
    jt = jtag_script(board, ub, ap_, bit, ps7tcl, out, dry)
    q = [qemu(m, ub, ft["itb"], sd["img"], out, dry) for m in ("jtag", "sd")] if a.qemu else []
    if dry:
        print("DRY RUN: nothing built. Add --run.")
        return
    files = {k: Path(v) for k, v in (("boot.bin", ub["boot_bin"]), ("ofx.itb", ft["itb"]), ("sd.img", sd["img"]),
                                     ("app.elf", ap_["elf"]), ("pl.bin", pl["bin"]), ("ps7_init.tcl", ps7tcl))}
    man = {"project": str(pf), "board": board_name, "bit": str(bit), "uboot": {"tag": ub["tag"], "rev": ub["rev"]},
           "ps_init": ub["ps_init"], "app": ap_, "pl": pl, "boot_bin": zynqimage_check(ub["boot_bin"]),
           "sd": sd, "ps7init_selftest": st, "jtag": jt, "qemu": q,
           "sha256": {k: sha(v) for k, v in files.items()}}
    (out / "manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    print(f"boot.bin: {ub['boot_bin']} ({json.dumps(man['boot_bin'])})")
    print(f"FIT: {ft['itb']} (app 0x{ap_['load']:08x}, {pl['bytes']} byte PL image at 0x{CONFIG['fpga_load']:08x})")
    print(f"SD image: {sd['img']} {sd['files']}")
    print(f"ps7_init.tcl selftest vs the C tables: {'PASS' if st['ok'] else 'FAIL'} ({st['writes_c']} writes)")
    print(f"JTAG: {jt['openocd']}")
    for r in q:
        print(f"QEMU {r['mode']}: {'PASS' if r['ok'] else 'FAIL'} in {r['seconds']} s; "
              f"FPGA load {'failed (QEMU has no PL and reads IDCODE 0)' if r['fpga_load_failed'] else 'ok'}")
        for l in r["lines"]:
            print(f"   | {l}")
    bad = (not man["boot_bin"]["ok"]) or not st["ok"] or any(not r["ok"] for r in q)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
