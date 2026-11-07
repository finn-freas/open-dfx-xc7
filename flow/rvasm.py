import argparse
import re
import sys

CONFIG = {
    "base": 0x00000000,
    "words": 2048,
    "fill": 0x00000000,
    "custom0_opcode": 0b0001011,
    "custom1_opcode": 0b0101011,
}

REGS = {f"x{i}": i for i in range(32)}
REGS.update({n: i for i, n in enumerate(
    "zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6".split())})
REGS["fp"] = 8

R_OPS = {
    "add": (0x00, 0), "sub": (0x20, 0), "sll": (0x00, 1), "slt": (0x00, 2), "sltu": (0x00, 3),
    "xor": (0x00, 4), "srl": (0x00, 5), "sra": (0x20, 5), "or": (0x00, 6), "and": (0x00, 7),
}
I_ALU = {"addi": 0, "slti": 2, "sltiu": 3, "xori": 4, "ori": 6, "andi": 7}
SHIFT_I = {"slli": (0x00, 1), "srli": (0x00, 5), "srai": (0x20, 5)}
LOADS = {"lb": 0, "lh": 1, "lw": 2, "lbu": 4, "lhu": 5}
STORES = {"sb": 0, "sh": 1, "sw": 2}
BRANCHES = {"beq": 0, "bne": 1, "blt": 4, "bge": 5, "bltu": 6, "bgeu": 7}


class AsmError(Exception):
    pass


def reg(tok):
    t = tok.strip().lower()
    if t not in REGS:
        raise AsmError(f"bad register '{tok}'")
    return REGS[t]


def num(tok, syms, need):
    t = tok.strip()
    terms = re.findall(r"[+-]?\s*[^+\-\s][^+-]*", t)
    if not terms:
        raise AsmError(f"bad expression '{tok}'")
    total = 0
    for term in terms:
        term = term.replace(" ", "")
        sign = -1 if term.startswith("-") else 1
        term = term.lstrip("+-")
        if len(term) == 3 and term[0] == "'" and term[2] == "'":
            v = ord(term[1])
        elif re.fullmatch(r"0[xX][0-9a-fA-F_]+", term):
            v = int(term.replace("_", ""), 16)
        elif re.fullmatch(r"0[bB][01_]+", term):
            v = int(term.replace("_", ""), 2)
        elif re.fullmatch(r"[0-9]+", term):
            v = int(term)
        elif term in syms:
            v = syms[term]
        elif need:
            raise AsmError(f"undefined symbol '{term}'")
        else:
            return None
        total += sign * v
    return total


def fits_signed(v, bits):
    return -(1 << (bits - 1)) <= v < (1 << (bits - 1))


def check_signed(v, bits, what):
    if not fits_signed(v, bits):
        raise AsmError(f"{what} {v} does not fit in {bits}-bit signed")
    return v & ((1 << bits) - 1)


def enc_r(f7, rs2, rs1, f3, rd, op):
    return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op


def enc_i(imm, rs1, f3, rd, op):
    return (check_signed(imm, 12, "I-imm") << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op


def enc_s(imm, rs2, rs1, f3, op):
    u = check_signed(imm, 12, "S-imm")
    return ((u >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((u & 0x1f) << 7) | op


def enc_b(off, rs2, rs1, f3):
    if off & 1:
        raise AsmError(f"branch offset {off} is odd")
    u = check_signed(off, 13, "B-offset")
    return (((u >> 12) & 1) << 31) | (((u >> 5) & 0x3f) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | \
        (((u >> 1) & 0xf) << 8) | (((u >> 11) & 1) << 7) | 0b1100011


def enc_u(imm20, rd, op):
    if not 0 <= imm20 < (1 << 20):
        raise AsmError(f"U-imm {imm20} out of range")
    return (imm20 << 12) | (rd << 7) | op


def enc_j(off, rd):
    if off & 1:
        raise AsmError(f"jump offset {off} is odd")
    u = check_signed(off, 21, "J-offset")
    return (((u >> 20) & 1) << 31) | (((u >> 1) & 0x3ff) << 21) | (((u >> 11) & 1) << 20) | \
        (((u >> 12) & 0xff) << 12) | (rd << 7) | 0b1101111


def hi_lo(v):
    v &= 0xffffffff
    lo = v & 0xfff
    if lo >= 0x800:
        lo -= 0x1000
    hi = ((v - lo) >> 12) & 0xfffff
    return hi, lo


def mem_operand(tok):
    m = re.fullmatch(r"\s*(.*?)\s*\(\s*([A-Za-z0-9]+)\s*\)\s*", tok)
    if not m:
        raise AsmError(f"bad memory operand '{tok}'")
    return (m.group(1) or "0"), m.group(2)


def li_size(args, syms):
    v = num(args[1], syms, False)
    if v is None:
        return 2
    return 1 if fits_signed(v, 12) else 2


def size_of(mn, args, syms):
    if mn == "li":
        return li_size(args, syms)
    if mn == "la":
        return 2
    return 1


def expand(mn, args, pc, syms):
    if mn == "nop":
        return [enc_i(0, 0, 0, 0, 0b0010011)]
    if mn == "mv":
        return [enc_i(0, reg(args[1]), 0, reg(args[0]), 0b0010011)]
    if mn == "not":
        return [enc_i(-1, reg(args[1]), 4, reg(args[0]), 0b0010011)]
    if mn == "j":
        return [enc_j(num(args[0], syms, True) - pc, 0)]
    if mn == "call":
        return [enc_j(num(args[0], syms, True) - pc, 1)]
    if mn == "ret":
        return [enc_i(0, 1, 0, 0, 0b1100111)]
    if mn == "beqz":
        return [enc_b(num(args[1], syms, True) - pc, 0, reg(args[0]), 0)]
    if mn == "bnez":
        return [enc_b(num(args[1], syms, True) - pc, 0, reg(args[0]), 1)]
    if mn in ("li", "la"):
        rd = reg(args[0])
        v = num(args[1], syms, True)
        n = syms["__size__"]
        if n == 1:
            return [enc_i(v, 0, 0, rd, 0b0010011)]
        hi, lo = hi_lo(v)
        return [enc_u(hi, rd, 0b0110111), enc_i(lo, rd, 0, rd, 0b0010011)]
    if mn in R_OPS:
        f7, f3 = R_OPS[mn]
        return [enc_r(f7, reg(args[2]), reg(args[1]), f3, reg(args[0]), 0b0110011)]
    if mn in I_ALU:
        return [enc_i(num(args[2], syms, True), reg(args[1]), I_ALU[mn], reg(args[0]), 0b0010011)]
    if mn in SHIFT_I:
        f7, f3 = SHIFT_I[mn]
        sh = num(args[2], syms, True)
        if not 0 <= sh < 32:
            raise AsmError(f"shift amount {sh} out of range")
        return [enc_r(f7, sh, reg(args[1]), f3, reg(args[0]), 0b0010011)]
    if mn in LOADS:
        off, base = mem_operand(args[1])
        return [enc_i(num(off, syms, True), reg(base), LOADS[mn], reg(args[0]), 0b0000011)]
    if mn in STORES:
        off, base = mem_operand(args[1])
        return [enc_s(num(off, syms, True), reg(args[0]), reg(base), STORES[mn], 0b0100011)]
    if mn in BRANCHES:
        return [enc_b(num(args[2], syms, True) - pc, reg(args[1]), reg(args[0]), BRANCHES[mn])]
    if mn == "lui":
        return [enc_u(num(args[1], syms, True), reg(args[0]), 0b0110111)]
    if mn == "auipc":
        return [enc_u(num(args[1], syms, True), reg(args[0]), 0b0010111)]
    if mn == "jal":
        if len(args) == 1:
            return [enc_j(num(args[0], syms, True) - pc, 1)]
        return [enc_j(num(args[1], syms, True) - pc, reg(args[0]))]
    if mn == "jalr":
        if len(args) == 1:
            return [enc_i(0, reg(args[0]), 0, 1, 0b1100111)]
        off, base = mem_operand(args[1])
        return [enc_i(num(off, syms, True), reg(base), 0, reg(args[0]), 0b1100111)]
    if mn in ("custom0", "custom1"):
        f7 = num(args[3], syms, True)
        f3 = num(args[4], syms, True)
        if not (0 <= f7 < 128 and 0 <= f3 < 8):
            raise AsmError(f"{mn} funct7/funct3 out of range")
        return [enc_r(f7, reg(args[2]), reg(args[1]), f3, reg(args[0]), CONFIG[f"{mn}_opcode"])]
    if mn == "ecall":
        return [0x00000073]
    if mn == "ebreak":
        return [0x00100073]
    if mn == "fence":
        return [0x0ff0000f]
    raise AsmError(f"unknown mnemonic '{mn}'")


def split_args(rest):
    rest = rest.strip()
    if not rest:
        return []
    out, depth, cur, quote = [], 0, "", False
    for ch in rest:
        if ch == "'":
            quote = not quote
        if ch == "," and depth == 0 and not quote:
            out.append(cur.strip())
            cur = ""
            continue
        depth += ch == "("
        depth -= ch == ")"
        cur += ch
    out.append(cur.strip())
    return out


def parse(text):
    items = []
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        while True:
            m = re.match(r"([A-Za-z_.][A-Za-z0-9_.]*)\s*:(.*)", line)
            if not m:
                break
            items.append((ln, raw, "label", m.group(1), []))
            line = m.group(2).strip()
        if not line:
            continue
        parts = line.split(None, 1)
        items.append((ln, raw, "insn", parts[0].lower(), split_args(parts[1] if len(parts) > 1 else "")))
    return items


def assemble(text, base):
    items = parse(text)
    syms = {}
    sizes = []
    pc = base
    for ln, raw, kind, name, args in items:
        try:
            if kind == "label":
                if name in syms:
                    raise AsmError(f"duplicate symbol '{name}'")
                syms[name] = pc
                sizes.append(0)
            elif name == ".equ":
                syms[args[0]] = num(args[1], syms, True)
                sizes.append(0)
            elif name == ".word":
                sizes.append(len(args))
                pc += 4 * len(args)
            elif name == ".org":
                tgt = num(args[0], syms, True)
                if tgt < pc or tgt & 3:
                    raise AsmError(f".org {tgt:#x} behind pc {pc:#x} or unaligned")
                sizes.append((tgt - pc) // 4)
                pc = tgt
            else:
                n = size_of(name, args, syms)
                sizes.append(n)
                pc += 4 * n
        except (AsmError, IndexError) as e:
            raise AsmError(f"line {ln}: {e}: {raw.strip()}")
    words, listing = [], []
    pc = base
    for (ln, raw, kind, name, args), n in zip(items, sizes):
        try:
            if kind == "label" or name == ".equ":
                listing.append((None, None, raw.strip()))
                continue
            if name == ".word":
                ws = [num(a, syms, True) & 0xffffffff for a in args]
            elif name == ".org":
                ws = [CONFIG["fill"]] * n
            else:
                syms["__size__"] = n
                ws = expand(name, args, pc, syms)
                if len(ws) != n:
                    raise AsmError("size changed between passes")
        except (AsmError, IndexError) as e:
            raise AsmError(f"line {ln}: {e}: {raw.strip()}")
        for i, w in enumerate(ws):
            listing.append((pc + 4 * i, w, raw.strip() if i == 0 else ""))
        words.extend(ws)
        pc += 4 * len(ws)
    syms.pop("__size__", None)
    return words, syms, listing


def main():
    ap = argparse.ArgumentParser(description="minimal two-pass RV32I assembler")
    ap.add_argument("src")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--lst")
    ap.add_argument("--base", type=lambda s: int(s, 0), default=CONFIG["base"])
    ap.add_argument("--words", type=int, default=CONFIG["words"])
    a = ap.parse_args()
    try:
        words, syms, listing = assemble(open(a.src).read(), a.base)
    except AsmError as e:
        sys.exit(f"{a.src}: {e}")
    if len(words) > a.words:
        sys.exit(f"program is {len(words)} words, memory is {a.words}")
    with open(a.out, "w") as f:
        for w in words + [CONFIG["fill"]] * (a.words - len(words)):
            f.write(f"{w:08x}\n")
    if a.lst:
        with open(a.lst, "w") as f:
            for addr, w, src in listing:
                if addr is None:
                    f.write(f"{'':19}{src}\n")
                else:
                    f.write(f"{addr:08x}: {w:08x}  {src}\n")
            for k in sorted(syms, key=lambda k: syms[k]):
                f.write(f"; {k} = {syms[k]:#010x}\n")
    print(f"{a.src}: {len(words)} words ({4 * len(words)} bytes) -> {a.out}")


if __name__ == "__main__":
    main()
