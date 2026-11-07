import argparse
import json
import struct
import sys
from pathlib import Path

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_CPU_ARM_CORTEX_A9

CONFIG = {
    "ram": (0x04000000, 0x00100000),
    "axi": (0x40000000, 0x1000),
    "uart": (0xE0001000, 0x1000),
    "slcr": (0xF8000000, 0x1000),
    "devcfg": (0xF8007000, 0x1000),
    "uart_fifo": 0x30,
    "devcfg_int_sts": 0x0C,
    "pcfg_done": 1 << 2,
    "id": 0x0F5A7020,
    "count_step": 7,
    "loop_writes": 3,
    "max_insns": 200_000_000,
    "slcr_reset": {0x170: 0x00400500, 0x900: 0x0000000F, 0x240: 0x00000000},
}


class Model:
    def __init__(self):
        self.regs = {0: 0, 4: 0}
        self.count = 1000
        self.ops = []
        self.uart = ""
        self.slcr = dict(CONFIG["slcr_reset"])
        self.led_writes_after_done = 0

    def axi_read(self, uc, off, size, ud):
        r = off & 0xC
        if r == 0x8:
            self.count += CONFIG["count_step"]
            v = self.count
        elif r == 0xC:
            v = CONFIG["id"]
        else:
            v = self.regs[r]
        self.ops.append(("R", CONFIG["axi"][0] + off, v))
        return v

    def axi_write(self, uc, off, size, value, ud):
        if size != 4:
            raise RuntimeError(f"AXI write of {size} bytes at +{off:#x}: the trace format is 32-bit only")
        r = off & 0xC
        if r in self.regs:
            self.regs[r] = value
        self.ops.append(("W", CONFIG["axi"][0] + off, value))
        if r == 0 and "ofx-app: PASS" in self.uart:
            self.led_writes_after_done += 1
            if self.led_writes_after_done >= CONFIG["loop_writes"]:
                uc.emu_stop()

    def uart_read(self, uc, off, size, ud):
        return 0

    def uart_write(self, uc, off, size, value, ud):
        if off == CONFIG["uart_fifo"]:
            self.uart += chr(value & 0xFF)
            if "ofx-app: FAIL" in self.uart or "TRAP" in self.uart:
                uc.emu_stop()

    def slcr_read(self, uc, off, size, ud):
        return self.slcr.get(off, 0)

    def slcr_write(self, uc, off, size, value, ud):
        self.slcr[off] = value

    def dev_read(self, uc, off, size, ud):
        return CONFIG["pcfg_done"] if off == CONFIG["devcfg_int_sts"] else 0

    def dev_write(self, uc, off, size, value, ud):
        pass


def load_elf(uc, path):
    d = Path(path).read_bytes()
    entry, phoff = struct.unpack_from("<II", d, 24)
    phentsize, phnum = struct.unpack_from("<HH", d, 42)
    for i in range(phnum):
        p_type, off, _, paddr, filesz, memsz = struct.unpack_from("<IIIIII", d, phoff + i * phentsize)
        if p_type == 1 and filesz:
            uc.mem_write(paddr, d[off:off + filesz])
    return entry


def main():
    ap = argparse.ArgumentParser(description="run the bare-metal app in Unicorn (Cortex-A9) against a register model of "
                                 "the PL AXI block and write its M_AXI_GP0 access trace for the PS7 BFM")
    ap.add_argument("elf")
    ap.add_argument("out", help="trace hex for $readmemh: <op> <addr> <data> per line, op 1=write 2=read")
    a = ap.parse_args()
    m = Model()
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
    uc.mem_map(*CONFIG["ram"])
    uc.mmio_map(*CONFIG["axi"], m.axi_read, None, m.axi_write, None)
    uc.mmio_map(*CONFIG["uart"], m.uart_read, None, m.uart_write, None)
    uc.mmio_map(*CONFIG["slcr"], m.slcr_read, None, m.slcr_write, None)
    uc.mmio_map(*CONFIG["devcfg"], m.dev_read, None, m.dev_write, None)
    entry = load_elf(uc, a.elf)
    err = None
    try:
        uc.emu_start(entry, 0, count=CONFIG["max_insns"])
    except UcError as e:
        err = f"{e} at pc 0x{uc.reg_read(UC_ARM_REG_PC):08x}"
    lines = []
    for op, addr, v in m.ops:
        lines.append(f"{1 if op == 'W' else 2} {addr:08x} {v:08x}")
    Path(a.out).write_text("\n".join(lines) + "\n")
    res = {"elf": a.elf, "trace": a.out, "ops": len(m.ops), "error": err, "uart": m.uart,
           "pass": "ofx-app: PASS" in m.uart and err is None and m.led_writes_after_done >= CONFIG["loop_writes"]}
    Path(a.out).with_suffix(".json").write_text(json.dumps(res, indent=1) + "\n")
    print(m.uart)
    print(json.dumps({k: v for k, v in res.items() if k != "uart"}))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
