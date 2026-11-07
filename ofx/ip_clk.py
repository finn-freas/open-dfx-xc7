"""ofx ip clk: Clocking Wizard equivalent for 7-series MMCME2_ADV / PLLE2_ADV.

From an input frequency and the wanted outputs (frequency, phase, duty cycle) it searches the legal
D (DIVCLK_DIVIDE), M (CLKFBOUT_MULT[_F]) and O (CLKOUTn_DIVIDE[_F]) for the part's speed grade, ranks the
candidates by frequency error and then by a jitter proxy, and writes Verilog (clk_wiz-like ports) plus XDC.
Limits are the Artix-7/Spartan-7/Zynq-7000 data sheet values (DS181/DS189/DS187, MMCM/PLL switching
characteristics); Kintex-7 has the same counters with higher VCO limits for -2/-3 (DS182), not used here.
"""
import itertools
import json
import math
import re

CONFIG = {
    "limits": {
        "MMCM": {"vco": {1: (600.0, 1200.0), 2: (600.0, 1440.0), 3: (600.0, 1600.0)},
                 "pfd": {1: (10.0, 450.0), 2: (10.0, 500.0), 3: (10.0, 550.0)},
                 "fin": (10.0, 800.0), "fout": {1: (4.69, 800.0), 2: (4.69, 933.0), 3: (4.69, 1066.0)},
                 "d": (1, 106), "m": (2.0, 64.0), "o": (1, 128), "frac": 8, "outs": 7},
        "PLL": {"vco": {1: (800.0, 1600.0), 2: (800.0, 1866.0), 3: (800.0, 2133.0)},
                "pfd": {1: (19.0, 450.0), 2: (19.0, 500.0), 3: (19.0, 550.0)},
                "fin": (19.0, 800.0), "fout": {1: (6.25, 800.0), 2: (6.25, 933.0), 3: (6.25, 1066.0)},
                "d": (1, 56), "m": (2.0, 64.0), "o": (1, 128), "frac": 1, "outs": 6},
    },
    "bufg_fmax": {1: 464.0, 2: 628.0, 3: 628.0},
    "rel_tol": 1e-6,
    "default_in_jitter_ui": 0.010,
}


class ClkError(Exception):
    pass


def speed_grade(part):
    m = re.search(r"-(\d)[a-z]*$", part or "")
    return int(m[1]) if m else 1


def _phase(ph, o, frac):
    """Achievable static phase: steps of 45/O degrees (1/8 VCO period) on an integer divider."""
    step = 45.0 / o
    k = round(ph / step)
    return k * step


def _duty(d, o, frac):
    if frac or o == 1:
        return 0.5
    k = min(max(round(d * 2 * o), 1), 2 * o - 1)
    if o > 64:
        k = max(k, 2 * (o - 64))
    return k / (2.0 * o)


def _divs(lo, hi, frac):
    n = int(round((hi - lo) * frac))
    return [lo + i / frac for i in range(n + 1)]


def solve(fin, outs, primitive="MMCM", part="xc7a35tcsg324-1", jitter_opt="balanced"):
    """outs: [{"freq": MHz, "phase": deg, "duty": 0..1}]. Returns the best configuration dict."""
    if primitive == "auto":
        best = None
        for p in ("PLL", "MMCM"):
            try:
                r = solve(fin, outs, p, part, jitter_opt)
            except ClkError:
                continue
            if best is None or (r["max_err_ppm"], -r["score"]) < (best["max_err_ppm"], -best["score"]):
                best = r
        if not best:
            raise ClkError("no MMCM or PLL configuration")
        return best
    L = CONFIG["limits"][primitive]
    sg = speed_grade(part)
    vlo, vhi = L["vco"][sg]
    plo, phi = L["pfd"][sg]
    if not L["fin"][0] <= fin <= L["fin"][1]:
        raise ClkError(f"input {fin} MHz outside {primitive} range {L['fin']}")
    if not 1 <= len(outs) <= L["outs"]:
        raise ClkError(f"{primitive} has {L['outs']} outputs, {len(outs)} requested")
    flo, fhi = L["fout"][sg]
    for o in outs:
        if not flo <= o["freq"] <= fhi:
            raise ClkError(f"output {o['freq']} MHz outside {primitive} range ({flo}, {fhi}) for speed grade -{sg}")
    msteps = _divs(L["m"][0], L["m"][1], L["frac"])
    cands = []
    for d in range(L["d"][0], L["d"][1] + 1):
        pfd = fin / d
        if not plo <= pfd <= phi:
            continue
        for m in msteps:
            vco = pfd * m
            if not vlo <= vco <= vhi:
                continue
            divs, errs = [], []
            for i, o in enumerate(outs):
                frac = L["frac"] if (i == 0 and primitive == "MMCM" and abs(o.get("duty", 0.5) - 0.5) < 1e-9) else 1
                ideal = vco / o["freq"]
                best = None
                for od in (math.floor(ideal * frac) / frac, math.ceil(ideal * frac) / frac):
                    if frac > 1 and od < 2.0 and od != 1.0:
                        od = 2.0 if ideal >= 1.5 else 1.0
                    if not L["o"][0] <= od <= L["o"][1]:
                        continue
                    e = abs(vco / od - o["freq"]) / o["freq"]
                    if best is None or e < best[1]:
                        best = (od, e)
                if best is None:
                    break
                divs.append(best[0])
                errs.append(best[1])
            else:
                cands.append((d, m, vco, pfd, divs, errs))
    if not cands:
        raise ClkError(f"no legal {primitive} configuration for {fin} MHz -> {[o['freq'] for o in outs]}")
    tol = CONFIG["rel_tol"]
    min_err = min(max(c[5]) for c in cands)
    pool = [c for c in cands if max(c[5]) <= min_err + tol]
    pool.sort(key=lambda c: rank(c, jitter_opt, primitive))
    d, m, vco, pfd, divs, errs = pool[0]
    res = {"primitive": primitive, "part": part, "speed_grade": sg, "fin": fin, "divclk": d, "mult": m,
           "vco": vco, "pfd": pfd, "outputs": [], "max_err_ppm": max(errs) * 1e6,
           "score": -rank(pool[0], jitter_opt, primitive)[0], "candidates": len(cands)}
    for i, (o, od) in enumerate(zip(outs, divs)):
        frac = (od != int(od))
        ph = _phase(o.get("phase", 0.0), od, frac)
        du = _duty(o.get("duty", 0.5), int(od) if not frac else od, frac)
        res["outputs"].append({"index": i, "divide": od, "freq": vco / od, "req_freq": o["freq"],
                               "phase": ph, "req_phase": o.get("phase", 0.0), "duty": du,
                               "req_duty": o.get("duty", 0.5), "err_ppm": errs[i] * 1e6,
                               "bufg_ok": vco / od <= CONFIG["bufg_fmax"][sg]})
    return res


def rank(c, jitter_opt, primitive):
    """Lower is better. Jitter proxy: the PFD frequency first (fewer reference divisions, more phase-detector
    updates per VCO period), then the VCO frequency ("balanced"/"min_jitter": high VCO; "power": low VCO)."""
    d, m, vco, pfd, divs, errs = c
    frac_pen = sum(1 for x in [m] + divs if x != int(x))
    if jitter_opt == "power":
        return (d, vco, frac_pen)
    return (d, frac_pen, -vco)


def fmt(x):
    return f"{x:.3f}"


def verilog(name, res, in_port="clk_in1", out_ports=None, use_reset=True, use_locked=True, in_buf="none",
            out_buf="BUFG", fb_buf="BUFG"):
    mmcm = res["primitive"] == "MMCM"
    prim = "MMCME2_ADV" if mmcm else "PLLE2_ADV"
    n = len(res["outputs"])
    out_ports = out_ports or [f"clk_out{i + 1}" for i in range(n)]
    period = 1000.0 / res["fin"]
    ports = [f"    input  wire {in_port}"] + [f"    output wire {p}" for p in out_ports]
    if use_reset:
        ports.append("    input  wire reset")
    if use_locked:
        ports.append("    output wire locked")
    L = []
    L.append(f"// generated by ofx ip clk: {res['primitive']} fin {res['fin']} MHz, D={res['divclk']} "
             f"M={fmt(res['mult'])} VCO={fmt(res['vco'])} MHz, PFD={fmt(res['pfd'])} MHz")
    for o in res["outputs"]:
        L.append(f"//   CLKOUT{o['index']}: O={fmt(o['divide'])} {o['freq']:.6f} MHz (req {o['req_freq']}, "
                 f"{o['err_ppm']:.1f} ppm) phase {o['phase']:.3f} duty {o['duty'] * 100:.3f}%")
    L.append(f"module {name} (\n" + ",\n".join(ports) + "\n);")
    clkin = in_port
    if in_buf == "ibuf":
        L.append(f"    wire clk_in1_ibuf;\n    IBUF u_ibuf (.I({in_port}), .O(clk_in1_ibuf));")
        clkin = "clk_in1_ibuf"
    L.append("    wire clkfbout, clkfbin;")
    raw = [f"clkout{i}_raw" for i in range(n)]
    L.append("    wire " + ", ".join(raw) + ";")
    if not use_locked:
        L.append("    wire locked;")
    rst = "reset" if use_reset else "1'b0"
    params = [f".DIVCLK_DIVIDE({res['divclk']})",
              f".CLKFBOUT_MULT{'_F' if mmcm else ''}({fmt(res['mult']) if mmcm else int(res['mult'])})",
              f".CLKFBOUT_PHASE(0.000)", f".CLKIN1_PERIOD({period:.3f})",
              '.BANDWIDTH("OPTIMIZED")', '.COMPENSATION("ZHOLD")', ".STARTUP_WAIT(\"FALSE\")"]
    if mmcm:
        params += ['.CLKOUT4_CASCADE("FALSE")', ".CLKFBOUT_USE_FINE_PS(\"FALSE\")", ".REF_JITTER1(0.010)"]
    else:
        params += [".REF_JITTER1(0.010)"]
    for o in res["outputs"]:
        i = o["index"]
        dv = f"{fmt(o['divide'])}" if (mmcm and i == 0) else f"{int(o['divide'])}"
        params += [f".CLKOUT{i}_DIVIDE{'_F' if (mmcm and i == 0) else ''}({dv})", f".CLKOUT{i}_PHASE({o['phase']:.3f})",
                   f".CLKOUT{i}_DUTY_CYCLE({o['duty']:.3f})"]
        if mmcm:
            params.append(f".CLKOUT{i}_USE_FINE_PS(\"FALSE\")")
    conns = [f".CLKIN1({clkin})", ".CLKIN2(1'b0)", ".CLKINSEL(1'b1)", ".CLKFBIN(clkfbin)", ".CLKFBOUT(clkfbout)",
             f".RST({rst})", ".PWRDWN(1'b0)", ".LOCKED(locked)", ".DADDR(7'h0)", ".DCLK(1'b0)", ".DEN(1'b0)",
             ".DI(16'h0)", ".DWE(1'b0)", ".DO()", ".DRDY()"]
    if mmcm:
        conns += [".PSCLK(1'b0)", ".PSEN(1'b0)", ".PSINCDEC(1'b0)", ".PSDONE()", ".CLKINSTOPPED()",
                  ".CLKFBSTOPPED()", ".CLKFBOUTB()"]
    nout = CONFIG["limits"][res["primitive"]]["outs"]
    for i in range(nout):
        conns.append(f".CLKOUT{i}({raw[i] if i < n else ''})")
        if mmcm and i < 4:
            conns.append(f".CLKOUT{i}B()")
    L.append(f"    {prim} #(\n        " + ",\n        ".join(params) + f"\n    ) u_{prim.lower()} (\n        "
             + ",\n        ".join(conns) + "\n    );")
    if fb_buf == "BUFG":
        L.append("    BUFG u_fb_bufg (.I(clkfbout), .O(clkfbin));")
    else:
        L.append("    assign clkfbin = clkfbout;")
    for i, p in enumerate(out_ports):
        if out_buf == "BUFG":
            L.append(f"    BUFG u_out{i}_bufg (.I({raw[i]}), .O({p}));")
        else:
            L.append(f"    assign {p} = {raw[i]};")
    L.append("endmodule\n")
    return "\n".join(L)


def xdc(res, in_port):
    return f"create_clock -name {in_port} -period {1000.0 / res['fin']:.3f} [get_ports {in_port}]\n"


def table(res):
    rows = [f"{res['primitive']} part {res['part']} (-{res['speed_grade']}): fin {res['fin']} MHz  D={res['divclk']}  "
            f"M={fmt(res['mult'])}  PFD={fmt(res['pfd'])} MHz  VCO={fmt(res['vco'])} MHz  ({res['candidates']} legal "
            f"candidates)"]
    rows.append(f"  {'out':<8}{'O':>9}{'req MHz':>12}{'actual MHz':>14}{'ppm':>9}{'phase':>9}{'duty %':>9}  BUFG")
    for o in res["outputs"]:
        rows.append(f"  CLKOUT{o['index']:<2}{fmt(o['divide']):>9}{o['req_freq']:>12}{o['freq']:>14.6f}"
                    f"{o['err_ppm']:>9.1f}{o['phase']:>9.3f}{o['duty'] * 100:>9.3f}  {'ok' if o['bufg_ok'] else 'OVER'}")
    return "\n".join(rows)


def parse_outs(specs):
    """'200' or '100@90' or '33.333@0/40' (freq[@phase][/duty%])."""
    out = []
    for s in specs:
        m = re.fullmatch(r"([\d.]+)(?:@(-?[\d.]+))?(?:/([\d.]+))?", s)
        if not m:
            raise ClkError(f"bad output spec {s!r}: freq[@phase][/duty%]")
        out.append({"freq": float(m[1]), "phase": float(m[2] or 0), "duty": float(m[3] or 50) / 100.0})
    return out


def from_table(t):
    outs = []
    for o in t["outputs"]:
        if isinstance(o, (int, float)):
            outs.append({"freq": float(o), "phase": 0.0, "duty": 0.5})
        else:
            outs.append({"freq": float(o["freq"]), "phase": float(o.get("phase", 0)), "duty": float(o.get("duty", 50)) / 100})
    return outs


def dump(res):
    return json.dumps(res, indent=1)
