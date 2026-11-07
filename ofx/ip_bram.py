"""ofx ip bram: Block Memory Generator equivalent (RAMB36E1 / RAMB18E1 instances with INIT from .coe/.mem).

Memory types as Vivado's blk_mem_gen: Single_Port_RAM, Simple_Dual_Port_RAM, True_Dual_Port_RAM,
Single_Port_ROM, Dual_Port_ROM. Same widths on both ports. The memory is tiled into primitives
(minimum area: fewest RAMB18 units, then fewest primitives), every primitive gets its INIT_xx/INITP_xx from the
init file, and the ports are wired the way the 7-series primitives expect (unused low address bits tied to 1,
parity bits carrying data bits 8, 17, ...). Module and port names follow blk_mem_gen so a design can swap them.
"""
import re
from pathlib import Path

CONFIG = {
    "shapes": [
        ("RAMB18E1", "TDP", 1, 16384, 1), ("RAMB18E1", "TDP", 2, 8192, 1), ("RAMB18E1", "TDP", 4, 4096, 1),
        ("RAMB18E1", "TDP", 9, 2048, 1), ("RAMB18E1", "TDP", 18, 1024, 1), ("RAMB18E1", "SDP", 36, 512, 1),
        ("RAMB36E1", "TDP", 1, 32768, 2), ("RAMB36E1", "TDP", 2, 16384, 2), ("RAMB36E1", "TDP", 4, 8192, 2),
        ("RAMB36E1", "TDP", 9, 4096, 2), ("RAMB36E1", "TDP", 18, 2048, 2), ("RAMB36E1", "TDP", 36, 1024, 2),
        ("RAMB36E1", "SDP", 72, 512, 2),
    ],
    "types": ("Single_Port_RAM", "Simple_Dual_Port_RAM", "True_Dual_Port_RAM", "Single_Port_ROM", "Dual_Port_ROM"),
    "write_mode": "WRITE_FIRST",
}


class BramError(Exception):
    pass


def read_init(path, width, depth):
    """.coe (memory_initialization_radix / _vector) or .mem ($readmemh-style, @addr allowed). Returns depth ints."""
    text = Path(path).read_text()
    vals = [0] * depth
    if str(path).endswith(".coe"):
        t = re.sub(r";.*?$", lambda m: m.group(0)[0], text, flags=re.M)
        m = re.search(r"memory_initialization_radix\s*=\s*(\d+)", t, re.I)
        radix = int(m[1]) if m else 16
        v = re.search(r"memory_initialization_vector\s*=\s*(.*?);", t, re.I | re.S)
        if not v:
            raise BramError(f"{path}: no memory_initialization_vector")
        toks = [x for x in re.split(r"[\s,]+", v[1]) if x]
        if len(toks) > depth:
            raise BramError(f"{path}: {len(toks)} words for depth {depth}")
        for i, x in enumerate(toks):
            vals[i] = int(x, radix)
    else:
        addr = 0
        for ln in text.splitlines():
            ln = ln.split("//")[0].split("#")[0]
            for tok in ln.split():
                if tok.startswith("@"):
                    addr = int(tok[1:], 16)
                    continue
                if addr >= depth:
                    raise BramError(f"{path}: address {addr} beyond depth {depth}")
                vals[addr] = int(tok.replace("_", ""), 16)
                addr += 1
    mask = (1 << width) - 1
    if any(x & ~mask for x in vals):
        raise BramError(f"{path}: a value is wider than {width} bits")
    return vals


def tile(width, depth, sdp_ok):
    best = None
    for prim, mode, w, d, units in CONFIG["shapes"]:
        if mode == "SDP" and not sdp_ok:
            continue
        cols = -(-width // w)
        rows = -(-depth // d)
        if rows > 1 and depth % d:
            continue
        key = (cols * rows * units, cols * rows, rows, -w)
        if best is None or key < best[0]:
            best = (key, {"prim": prim, "mode": mode, "w": w, "d": d, "cols": cols, "rows": rows})
    if best is None:
        raise BramError(f"no primitive tiling for {width}x{depth}")
    return best[1]


def bit_layout(w):
    """data bits / parity bits per word of a primitive port width."""
    if w < 9:
        return w, 0
    return w * 8 // 9, w // 9


def slice_bits(width, w):
    """Columns of the user word: (lo, n) per primitive column of width w."""
    out, lo = [], 0
    while lo < width:
        n = min(w, width - lo)
        out.append((lo, n))
        lo += n
    return out


def prim_init(words, w, prim):
    """INIT_xx / INITP_xx dicts for one primitive column of width-w words (list of ints, each < 2**w)."""
    D, P = bit_layout(w)
    data, par = 0, 0
    for a, v in enumerate(words):
        dpart, ppart = split_word(v, w)
        data |= dpart << (a * D)
        par |= ppart << (a * P) if P else 0
    n_init = 128 if prim == "RAMB36E1" else 64
    n_initp = 16 if prim == "RAMB36E1" else 8
    init = {f"INIT_{i:02X}": (data >> (256 * i)) & ((1 << 256) - 1) for i in range(n_init)}
    initp = {f"INITP_{i:02X}": (par >> (256 * i)) & ((1 << 256) - 1) for i in range(n_initp)}
    return init, initp


def split_word(v, w):
    """User bits of one primitive word -> (data part, parity part): as blk_mem_gen, the low D bits go to DI and
    the top P bits to DIP (an 18-bit word is {DIP[1:0], DI[15:0]})."""
    D, P = bit_layout(w)
    return v & ((1 << D) - 1), v >> D


def join_expr(sig, w):
    """Verilog: the w-bit user slice `sig` -> (data bus, parity bus) for the primitive."""
    D, P = bit_layout(w)
    if not P:
        return sig, None
    return f"{sig}[{D - 1}:0]", f"{sig}[{w - 1}:{D}]"


def build(name, mem_type, width, depth, init=None, reg_a=False, reg_b=False, write_mode=None):
    if mem_type not in CONFIG["types"]:
        raise BramError(f"memory type {mem_type}: one of {CONFIG['types']}")
    if depth & (depth - 1):
        raise BramError(f"depth {depth} must be a power of two")
    write_mode = write_mode or CONFIG["write_mode"]
    t = tile(width, depth, sdp_ok=(mem_type == "Simple_Dual_Port_RAM"))
    words = read_init(init, width, depth) if init else [0] * depth
    aw = max(1, (depth - 1).bit_length())
    return {"name": name, "type": mem_type, "width": width, "depth": depth, "aw": aw, "tile": t, "words": words,
            "reg_a": reg_a, "reg_b": reg_b, "write_mode": write_mode, "init_file": str(init) if init else None}


def ports(cfg):
    t, w, aw = cfg["type"], cfg["width"], cfg["aw"]
    a = [("input", "clka", 1)]
    if t in ("Single_Port_RAM", "True_Dual_Port_RAM", "Simple_Dual_Port_RAM"):
        a += [("input", "wea", 1)]
    a += [("input", "addra", aw)]
    if t in ("Single_Port_RAM", "True_Dual_Port_RAM", "Simple_Dual_Port_RAM"):
        a += [("input", "dina", w)]
    if t != "Simple_Dual_Port_RAM":
        a += [("output", "douta", w)]
    if t in ("True_Dual_Port_RAM", "Simple_Dual_Port_RAM", "Dual_Port_ROM"):
        a += [("input", "clkb", 1)]
        if t == "True_Dual_Port_RAM":
            a += [("input", "web", 1)]
        a += [("input", "addrb", aw)]
        if t == "True_Dual_Port_RAM":
            a += [("input", "dinb", w)]
        a += [("output", "doutb", w)]
    return a


def verilog(cfg):
    t = cfg["tile"]
    prim, mode, w, d = t["prim"], t["mode"], t["w"], t["d"]
    mt = cfg["type"]
    W, aw = cfg["width"], cfg["aw"]
    is36 = prim == "RAMB36E1"
    abits = 16 if is36 else 14
    pw = max(1, (d - 1).bit_length())
    has_b = mt in ("True_Dual_Port_RAM", "Dual_Port_ROM")
    sdp = mode == "SDP"
    L = [f"// generated by ofx ip bram: {mt} {W}x{cfg['depth']}, {t['cols']}x{t['rows']} {prim} {mode} "
         f"width {w} depth {d}" + (f", init {Path(cfg['init_file']).name}" if cfg["init_file"] else "")]
    pl = ports(cfg)
    L.append(f"module {cfg['name']} (\n" + ",\n".join(
        f"    {d_} wire{f' [{n - 1}:0]' if n > 1 else ''} {p}" for d_, p, n in pl) + "\n);")
    names = {p for _, p, _ in pl}
    rd_a = "addrb" if mt == "Simple_Dual_Port_RAM" else "addra"
    rd_clk = "clkb" if mt == "Simple_Dual_Port_RAM" else "clka"
    reg_rd = cfg["reg_b"] if mt == "Simple_Dual_Port_RAM" else cfg["reg_a"]
    rows = t["rows"]
    lat = 1 + (1 if reg_rd else 0)
    sel_bits = (rows - 1).bit_length() if rows > 1 else 0
    for port in (["a"] + (["b"] if has_b else [])):
        if rows > 1:
            src = rd_a if port == "a" else "addrb"
            ck = rd_clk if port == "a" else "clkb"
            L.append(f"    reg [{sel_bits - 1}:0] sel{port}_q [0:{lat - 1}];")
            L.append(f"    always @(posedge {ck}) begin sel{port}_q[0] <= {src}[{aw - 1}:{aw - sel_bits}];" +
                     "".join(f" sel{port}_q[{i}] <= sel{port}_q[{i - 1}];" for i in range(1, lat)) + " end")
    for r in range(rows):
        for c, (lo, n) in enumerate(slice_bits(W, w)):
            words = [(cfg["words"][r * d + a] >> lo) & ((1 << n) - 1) for a in range(min(d, cfg["depth"] - r * d))]
            init, initp = prim_init(words, w, prim)
            inst = f"u_r{r}_c{c}"
            slc = f"{lo + n - 1}:{lo}"
            L.append(f"    wire [{w - 1}:0] {inst}_qa, {inst}_qb, {inst}_wa, {inst}_wb;")
            if "dina" in names:
                L.append(f"    assign {inst}_wa = {{{'{' + str(w - n) + '{1' + chr(39) + 'b0}}, ' if w > n else ''}dina[{slc}]}};")
            else:
                L.append(f"    assign {inst}_wa = {w}'d0;")
            if "dinb" in names:
                L.append(f"    assign {inst}_wb = {{{'{' + str(w - n) + '{1' + chr(39) + 'b0}}, ' if w > n else ''}dinb[{slc}]}};")
            else:
                L.append(f"    assign {inst}_wb = {w}'d0;")
            row_we = f" && addra[{aw - 1}:{aw - sel_bits}] == {sel_bits}'d{r}" if rows > 1 else ""
            row_web = f" && addrb[{aw - 1}:{aw - sel_bits}] == {sel_bits}'d{r}" if rows > 1 else ""
            wea = f"(wea{row_we})" if "wea" in names else "1'b0"
            web = f"(web{row_web})" if "web" in names else "1'b0"
            low = (15 if is36 else 14) - pw
            lsb_tie = f", {low}'h{(1 << low) - 1:x}" if low > 0 else ""

            def addr(sig):
                top = f"1'b1, " if is36 else ""
                ub = min(pw, aw)
                pad = f"{pw - ub}'d0, " if pw > ub else ""
                return f"{{{top}{pad}{sig}[{ub - 1}:0]{lsb_tie}}}"
            p = {"READ_WIDTH_A": w if not sdp else w, "WRITE_WIDTH_A": w if not sdp else 0,
                 "READ_WIDTH_B": w if has_b else 0, "WRITE_WIDTH_B": w if (has_b or sdp) else 0}
            if sdp:
                p = {"READ_WIDTH_A": w, "WRITE_WIDTH_B": w, "READ_WIDTH_B": 0, "WRITE_WIDTH_A": 0}
            if mt in ("Single_Port_RAM", "Single_Port_ROM"):
                p["READ_WIDTH_B"] = 0
                p["WRITE_WIDTH_B"] = 0
            prm = [f'.RAM_MODE("{mode}")'] + [f".{k}({v})" for k, v in p.items()]
            prm += [f".DOA_REG({1 if reg_rd else 0})", f".DOB_REG({1 if ((has_b and cfg['reg_b']) or (sdp and reg_rd)) else 0})",
                    f'.WRITE_MODE_A("{"READ_FIRST" if sdp else cfg["write_mode"]}")',
                    f'.WRITE_MODE_B("{"READ_FIRST" if sdp else cfg["write_mode"]}")']
            if is36:
                prm += ['.RAM_EXTENSION_A("NONE")', '.RAM_EXTENSION_B("NONE")']
            prm += [f".{k}(256'h{v:064X})" for k, v in init.items()]
            prm += [f".{k}(256'h{v:064X})" for k, v in initp.items()]
            D, P = bit_layout(w)
            dbus = 32 if is36 else 16
            pbus = 4 if is36 else 2
            wexp_a, wexp_ap = join_expr(f"{inst}_wa", w)
            wexp_b, wexp_bp = join_expr(f"{inst}_wb", w)
            qa_d, qa_p = f"{inst}_doa", f"{inst}_dopa"
            qb_d, qb_p = f"{inst}_dob", f"{inst}_dopb"
            L.append(f"    wire [{dbus - 1}:0] {qa_d}, {qb_d};\n    wire [{pbus - 1}:0] {qa_p}, {qb_p};")
            wen = 4 if is36 else 2
            web_n = 8 if is36 else 4
            if sdp:
                half = D // 2
                hp = P // 2
                dd, pp = join_expr(f"{inst}_wa", w)
                L.append(f"    wire [{D - 1}:0] {inst}_sd; wire [{max(P, 1) - 1}:0] {inst}_sp;")
                L.append(f"    assign {inst}_sd = {dd};")
                L.append(f"    assign {inst}_sp = {pp};")
                conns = [f".CLKARDCLK({rd_clk})", f".CLKBWRCLK(clka)", f".ENARDEN(1'b1)", f".ENBWREN(1'b1)",
                         f".ADDRARDADDR({addr(rd_a)})", f".ADDRBWRADDR({addr('addra')})",
                         f".DIADI({inst}_sd[{half - 1}:0])", f".DIBDI({inst}_sd[{D - 1}:{half}])",
                         f".DIPADIP({inst}_sp[{hp - 1}:0])", f".DIPBDIP({inst}_sp[{P - 1}:{hp}])",
                         f".WEA({wen}'h0)", f".WEBWE({{{web_n}{{{wea}}}}})",
                         f".DOADO({qa_d})", f".DOBDO({qb_d})", f".DOPADOP({qa_p})", f".DOPBDOP({qb_p})"]
                L.append(f"    assign {inst}_qa = {{{qb_p}[{hp - 1}:0], {qa_p}[{hp - 1}:0], {qb_d}[{half - 1}:0], {qa_d}[{half - 1}:0]}};")
            else:
                def dio(wexp, wexpp):
                    dd = f"{{{dbus - D}'d0, {wexp}}}" if D < dbus else wexp
                    pp = (f"{{{pbus - P}'d0, {wexpp}}}" if P < pbus else wexpp) if P else f"{pbus}'d0"
                    return dd, pp
                da, dap = dio(wexp_a, wexp_ap)
                db, dbp = dio(wexp_b, wexp_bp)
                ck_b = "clkb" if has_b else "clka"
                conns = [f".CLKARDCLK(clka)", f".CLKBWRCLK({ck_b})", ".ENARDEN(1'b1)", f".ENBWREN(1'b{1 if has_b else 0})",
                         f".ADDRARDADDR({addr('addra')})",
                         f".ADDRBWRADDR({addr('addrb') if has_b else (str(abits) + chr(39) + 'h' + format((1 << abits) - 1, 'x'))})",
                         f".DIADI({da})", f".DIBDI({db})", f".DIPADIP({dap})", f".DIPBDIP({dbp})",
                         f".WEA({{{wen}{{{wea}}}}})", f".WEBWE({{{web_n}{{{web}}}}})",
                         f".DOADO({qa_d})", f".DOBDO({qb_d})", f".DOPADOP({qa_p})", f".DOPBDOP({qb_p})"]

                def rd(qd, qp):
                    if not P:
                        return f"{qd}[{w - 1}:0]"
                    return f"{{{qp}[{P - 1}:0], {qd}[{D - 1}:0]}}"
                L.append(f"    assign {inst}_qa = {rd(qa_d, qa_p)};")
                L.append(f"    assign {inst}_qb = {rd(qb_d, qb_p)};")
            conns += [".RSTRAMARSTRAM(1'b0)", ".RSTRAMB(1'b0)", ".RSTREGARSTREG(1'b0)", ".RSTREGB(1'b0)",
                      ".REGCEAREGCE(1'b1)", ".REGCEB(1'b1)"]
            if is36:
                conns += [".CASCADEINA(1'b0)", ".CASCADEINB(1'b0)", ".CASCADEOUTA()", ".CASCADEOUTB()",
                          ".INJECTDBITERR(1'b0)", ".INJECTSBITERR(1'b0)", ".DBITERR()", ".SBITERR()", ".ECCPARITY()",
                          ".RDADDRECC()"]
            L.append(f"    {prim} #(\n        " + ",\n        ".join(prm) + f"\n    ) {inst} (\n        " +
                     ",\n        ".join(conns) + "\n    );")
    for port, outn in (("a", "douta" if "douta" in names else "doutb" if mt == "Simple_Dual_Port_RAM" else None),
                       ("b", "doutb" if has_b else None)):
        if not outn:
            continue
        cols = slice_bits(W, w)
        if rows == 1:
            parts = [f"u_r0_c{c}_q{port}[{n - 1}:0]" for c, (lo, n) in reversed(list(enumerate(cols)))]
            L.append(f"    assign {outn} = {{{', '.join(parts)}}};")
        else:
            L.append(f"    reg [{W - 1}:0] {outn}_m;")
            L.append("    always @* begin")
            L.append(f"        case (sel{port}_q[{lat - 1}])")
            for r in range(rows):
                parts = [f"u_r{r}_c{c}_q{port}[{n - 1}:0]" for c, (lo, n) in reversed(list(enumerate(cols)))]
                L.append(f"        {sel_bits}'d{r}: {outn}_m = {{{', '.join(parts)}}};")
            L.append(f"        default: {outn}_m = {W}'d0;\n        endcase\n    end")
            L.append(f"    assign {outn} = {outn}_m;")
    L.append("endmodule\n")
    return "\n".join(L)


def summary(cfg):
    t = cfg["tile"]
    return (f"{cfg['name']}: {cfg['type']} {cfg['width']}x{cfg['depth']} -> {t['cols'] * t['rows']} x {t['prim']} "
            f"({t['mode']} {t['w']}x{t['d']}, {t['cols']} columns x {t['rows']} rows)"
            + (f", init {cfg['init_file']}" if cfg["init_file"] else ""))
