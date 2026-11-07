import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from . import ROOT
from . import design as D
from . import drc

CONFIG = {
    "model": ROOT / "ofx" / "power_model.json",
    "toggle": 0.125,
    "vectorless": True,
    "feature_version": 2,
    "ambient_c": 25.0,
    "rails": {"Vccint": 1.0, "Vccaux": 1.8, "Vcco33": 3.3, "Vcco25": 2.5, "Vcco18": 1.8, "Vcco15": 1.5,
              "Vcco135": 1.35, "Vcco12": 1.2, "Vccbram": 1.0, "Vccadc": 1.71},
    "classes": ("Clocks", "Slice Logic", "Signals", "Block RAM", "DSPs", "MMCM", "PLL", "I/O"),
    "class_features": {
        "Clocks": ("clk_loads", "clk_pips", "clk_bufs"),
        "Slice Logic": ("lut", "ff", "carry", "mux", "lutram"),
        "Signals": ("sig_pips", "sig_fanout"),
        "Block RAM": ("bram",),
        "DSPs": ("dsp",),
        "MMCM": ("mmcm_n", "mmcm_vco"),
        "PLL": ("pll_n", "pll_vco"),
        "I/O": ("io_out_cv2", "io_in", "io_vref", "io_diff_out"),
    },
    "lut_types": ("LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6", "LUT6_2", "INV"),
    "ff_types": ("FDRE", "FDSE", "FDCE", "FDPE", "FDRE_1", "FDSE_1", "FDCE_1", "FDPE_1", "LDCE", "LDPE"),
    "lutram_types": ("SRL16E", "SRLC32E", "SRLC16E", "RAM32X1D", "RAM64X1D", "RAM128X1D", "RAM32M", "RAM64M",
                     "RAM32X1S", "RAM64X1S", "RAM128X1S", "RAM256X1S"),
    "bram_units": {"RAMB18E1": 1, "RAMB36E1": 2, "FIFO18E1": 1, "FIFO36E1": 2},
    "pll_out": re.compile(r"^CLK(OUT\d|FBOUT)B?$"),
}


def routing_pips(attr):
    r = attr.get("ROUTING", "")
    if not r:
        return 0
    parts = r.split(";")
    return sum(1 for k in range(1, len(parts), 3) if parts[k])


class Clocks:
    def __init__(self, net, xdc):
        self.net, self.xdc = net, xdc
        self.memo = {}

    def pll_freq(self, c, port):
        net = self.net
        t = drc.CONFIG["pll_alias"].get(net.cells[c]["type"])
        mmcm = t == "MMCME2_ADV"
        per = D.as_float(net.param(c, "CLKIN1_PERIOD", 0.0), 0.0)
        fin = 1000.0 / per if per else self.freq(net.pin(c, "CLKIN1"))
        if not fin:
            return 0.0
        mult = D.as_float(net.param(c, "CLKFBOUT_MULT_F" if mmcm else "CLKFBOUT_MULT", 5.0), 5.0)
        div = D.as_float(net.param(c, "DIVCLK_DIVIDE", 1), 1.0) or 1.0
        vco = fin * mult / div
        m = re.match(r"CLKOUT(\d)", port)
        if not m:
            return vco / mult
        n = m.group(1)
        key = f"CLKOUT{n}_DIVIDE_F" if (mmcm and n == "0") else f"CLKOUT{n}_DIVIDE"
        return vco / (D.as_float(net.param(c, key, 1.0), 1.0) or 1.0)

    def vco(self, c):
        net = self.net
        mmcm = drc.CONFIG["pll_alias"].get(net.cells[c]["type"]) == "MMCME2_ADV"
        per = D.as_float(net.param(c, "CLKIN1_PERIOD", 0.0), 0.0)
        fin = 1000.0 / per if per else self.freq(net.pin(c, "CLKIN1"))
        mult = D.as_float(net.param(c, "CLKFBOUT_MULT_F" if mmcm else "CLKFBOUT_MULT", 5.0), 5.0)
        div = D.as_float(net.param(c, "DIVCLK_DIVIDE", 1), 1.0) or 1.0
        return (fin or 0.0) * mult / div

    def freq(self, b, depth=0):
        if not isinstance(b, int):
            return 0.0
        if b in self.memo:
            return self.memo[b]
        self.memo[b] = 0.0
        net = self.net
        c, port, _ = net.driver(b)
        f = 0.0
        if c == "<port>":
            per = self.xdc.clock_period(port)
            f = 1000.0 / per if per else 0.0
        elif c and depth < 12:
            t = net.cells[c]["type"]
            if t in drc.CONFIG["pll_alias"]:
                f = self.pll_freq(c, port)
            elif t in drc.CONFIG["clock_bufs"] or t in drc.CONFIG["ibuf_types"] or net.cells[c]["ptype"].startswith("IOB"):
                ins = [x for p in ("I", "I0", "I1", "PAD") for x in net.pins(c, p).values()]
                if not ins:
                    for p, (pb, d) in net.port_bits.items():
                        if any(pb in v.values() for v in net.cells[c]["conns"].values()) and d != "output":
                            per = self.xdc.clock_period(p)
                            f = max(f, 1000.0 / per if per else 0.0)
                for x in ins:
                    f = max(f, self.freq(x, depth + 1))
                if t == "BUFR":
                    dv = D.as_str(net.param(c, "BUFR_DIVIDE", "BYPASS"))
                    f = f / int(dv) if dv.isdigit() else f
        self.memo[b] = f
        return f



ACT = {
    "p_in": 0.5,
    "d_in": 0.125,
    "sweeps": 6,
    "damp": 0.5,
    "lut_pins": ("I0", "I1", "I2", "I3", "I4", "I5"),
    "ff_d": {"FDRE": "D", "FDSE": "D", "FDCE": "D", "FDPE": "D", "FDRE_1": "D", "FDSE_1": "D", "FDCE_1": "D",
             "FDPE_1": "D", "LDCE": "D", "LDPE": "D"},
    "passthru": {"IBUF": "I", "OBUF": "I", "OBUFT": "I", "BUFG": "I", "BUFGCTRL": "I0", "BUFH": "I", "BUFR": "I",
                 "IBUFG": "I", "BUFIO": "I", "BUFGCE": "I", "INV": None},
}


def _lut_eval(init, ins):
    """ins: list of (p, d) for I0..I(k-1). Returns (p_out, d_out) of the LUT function INIT."""
    k = len(ins)
    n = 1 << k
    p_out = 0.0
    sens = [0.0] * k
    probs = [x[0] for x in ins]
    for m in range(n):
        w = 1.0
        for i in range(k):
            w *= probs[i] if (m >> i) & 1 else 1.0 - probs[i]
        if w == 0.0:
            continue
        f = (init >> m) & 1
        p_out += w * f
        for i in range(k):
            if not (m >> i) & 1:
                if f != (init >> (m | (1 << i))) & 1:
                    pi = probs[i]
                    sens[i] += w / (1.0 - pi) if pi < 1.0 else 0.0
    d_out = sum(s * x[1] for s, x in zip(sens, ins))
    return min(max(p_out, 0.0), 1.0), min(d_out, 1.0)


def _mux(i0, i1, s):
    p = (1 - s[0]) * i0[0] + s[0] * i1[0]
    d = (1 - s[0]) * i0[1] + s[0] * i1[1] + s[1] * (i0[0] * (1 - i1[0]) + i1[0] * (1 - i0[0]))
    return p, min(d, 1.0)


def _xor(a, b):
    p = a[0] * (1 - b[0]) + b[0] * (1 - a[0])
    return p, min(a[1] + b[1], 1.0)


def activity(net):
    """returns {bit: (p, d)} for every net bit of the netlist"""
    const = {}
    for b, ds in net.drivers.items():
        for c, _, _ in ds:
            if c != "<port>" and net.cells[c]["ptype"] in ("PSEUDO_VCC", "VCC"):
                const[b] = (1.0, 0.0)
            elif c != "<port>" and net.cells[c]["ptype"] in ("PSEUDO_GND", "GND"):
                const[b] = (0.0, 0.0)
    act = {}

    def get(b):
        if not isinstance(b, int):
            return (1.0, 0.0) if str(b) == "1" else (0.0, 0.0)
        if b in const:
            return const[b]
        return act.get(b, (ACT["p_in"], ACT["d_in"]))

    comb, ffs, other = [], [], []
    for name, c in net.cells.items():
        t = c["type"]
        if t.startswith("LUT") or t in ("CARRY4", "MUXF7", "MUXF8", "INV") or t in ACT["passthru"]:
            comb.append(name)
        elif t in ACT["ff_d"]:
            ffs.append(name)
        else:
            other.append(name)
    out_of = {}
    for name in comb:
        for port, bits in net.cells[name]["conns"].items():
            for b in bits.values():
                if isinstance(b, int) and any(d[0] == name and d[1] == port for d in net.drivers.get(b, [])):
                    out_of.setdefault(name, []).append(b)
    comb_set = set(comb)
    indeg = {n: 0 for n in comb}
    fan = {n: [] for n in comb}
    for name in comb:
        for b in out_of.get(name, []):
            for s, _, _ in net.sinks.get(b, []):
                if s in comb_set:
                    indeg[s] += 1
                    fan[name].append(s)
    order = [n for n in comb if indeg[n] == 0]
    k = 0
    while k < len(order):
        for s in fan[order[k]]:
            indeg[s] -= 1
            if indeg[s] == 0:
                order.append(s)
        k += 1
    seen = set(order)
    order += [n for n in comb if n not in seen]

    def ev(name):
        c = net.cells[name]
        t = c["type"]
        conns = c["conns"]
        if t.startswith("LUT") and t != "LUT6_2":
            init = _as_init(net.param(name, "INIT", 0))
            ins = [get(conns[p][0]) if p in conns else (0.0, 0.0) for p in ACT["lut_pins"][:int(t[3])]]
            for b in conns.get("O", {}).values():
                act[b] = _lut_eval(init, ins)
        elif t == "LUT6_2":
            init = _as_init(net.param(name, "INIT", 0))
            ins = [get(conns[p][0]) if p in conns else (0.0, 0.0) for p in ACT["lut_pins"]]
            for b in conns.get("O6", {}).values():
                act[b] = _lut_eval(init, ins)
            for b in conns.get("O5", {}).values():
                act[b] = _lut_eval(init & 0xFFFFFFFF, ins[:5])
        elif t == "INV":
            for b in conns.get("O", {}).values():
                p, d = get(conns.get("I", {}).get(0))
                act[b] = (1.0 - p, d)
        elif t in ("MUXF7", "MUXF8"):
            for b in conns.get("O", {}).values():
                act[b] = _mux(get(conns.get("I0", {}).get(0)), get(conns.get("I1", {}).get(0)),
                              get(conns.get("S", {}).get(0)))
        elif t == "CARRY4":
            ci = get(conns.get("CI", {}).get(0)) if not _is_const_pin(net, conns.get("CI", {}).get(0)) \
                else get(conns.get("CYINIT", {}).get(0))
            if "CYINIT" in conns and not _is_const_pin(net, conns["CYINIT"].get(0)):
                ci = get(conns["CYINIT"][0])
            for i in range(4):
                s = get(conns.get("S", {}).get(i))
                di = get(conns.get("DI", {}).get(i))
                o = _xor(s, ci)
                for b in [conns.get("O", {}).get(i)]:
                    if isinstance(b, int):
                        act[b] = o
                ci = _mux(di, ci, s)
                b = conns.get("CO", {}).get(i)
                if isinstance(b, int):
                    act[b] = ci
        else:
            pin = ACT["passthru"].get(t)
            src = conns.get(pin, {}).get(0) if pin else None
            for b in out_of.get(name, []):
                act[b] = get(src) if src is not None else (ACT["p_in"], ACT["d_in"])

    for _ in range(ACT["sweeps"]):
        for name in order:
            ev(name)
        for name in ffs:
            c = net.cells[name]
            d_in = get(c["conns"].get(ACT["ff_d"][c["type"]], {}).get(0))
            for b in c["conns"].get("Q", {}).values():
                old = act.get(b, (ACT["p_in"], ACT["d_in"]))
                p = d_in[0]
                d = min(d_in[1], 2 * p * (1 - p))
                act[b] = (old[0] + ACT["damp"] * (p - old[0]), old[1] + ACT["damp"] * (d - old[1]))
    for b in list(net.sinks) + list(net.drivers):
        if isinstance(b, int) and b not in act:
            act[b] = get(b)
    return act


def _as_init(v):
    s = str(v).strip()
    if re.fullmatch(r"[01]+", s):
        return int(s, 2)
    m = re.fullmatch(r"\d+'[hH]([0-9a-fA-F]+)", s)
    if m:
        return int(m.group(1), 16)
    try:
        return int(s)
    except ValueError:
        return 0


def _is_const_pin(net, b):
    return b is None or not isinstance(b, int) or net.is_const(b)


def is_clock_net(net, b):
    cp = drc.CONFIG["clock_pins"]
    for s, sp, _ in net.sinks.get(b, []):
        if s != "<port>" and sp in cp.get(net.cells[s]["type"], ()):
            return True
    return False


def features(netlist_path, xdc_paths):
    net = D.Netlist(netlist_path)
    xdc = D.Xdc(xdc_paths)
    clk = Clocks(net, xdc)
    a = CONFIG["toggle"]
    cp = drc.CONFIG["clock_pins"]
    fmax = max([1000.0 / c["period"] for c in xdc.clocks if c["period"]] or [100.0])
    cell_clock = {}
    for name, c in net.cells.items():
        pins = cp.get(c["type"], ())
        fs = [clk.freq(b) for p in pins for b in net.pins(name, p).values()]
        if fs:
            cell_clock[name] = max(fs)
    net_f = {}

    def data_f(b, depth=0):
        if b in net_f:
            return net_f[b]
        net_f[b] = 0.0
        if not isinstance(b, int) or net.is_const(b):
            return 0.0
        c, port, _ = net.driver(b)
        if c == "<port>":
            f = fmax
        elif c is None:
            f = 0.0
        elif c in cell_clock:
            f = cell_clock[c]
        elif depth > 60:
            f = fmax
        else:
            ins = [x for p, bits in net.cells[c]["conns"].items() for x in bits.values()
                   if any(s[0] == c and s[1] == p for s in net.sinks.get(x, []))]
            f = max([data_f(x, depth + 1) for x in ins] or [0.0])
        net_f[b] = f
        return f

    sys.setrecursionlimit(20000)
    act = activity(net) if CONFIG["vectorless"] else {}

    def rate(b):
        """toggles per microsecond (MHz) of a net bit: transition density x the frequency of its clock domain"""
        f = data_f(b)
        if not CONFIG["vectorless"]:
            return a * f
        return act.get(b, (0.5, a))[1] * f

    feat = defaultdict(float)
    counts = defaultdict(int)
    for name, c in net.cells.items():
        t = c["type"]
        outs = [b for p, bits in c["conns"].items() for b in bits.values()
                if any(d[0] == name and d[1] == p for d in net.drivers.get(b, []))]
        fo = max([data_f(b) for b in outs] or [0.0])
        ro = sum(rate(b) for b in outs)
        if t in CONFIG["lut_types"]:
            feat["lut"] += ro
            counts["LUT"] += 1
        elif t in CONFIG["ff_types"]:
            feat["ff"] += ro if CONFIG["vectorless"] else a * cell_clock.get(name, 0.0)
            counts["FF"] += 1
        elif t == "CARRY4":
            feat["carry"] += ro / 2.0 if CONFIG["vectorless"] else a * fo
            counts["CARRY4"] += 1
        elif t in ("MUXF7", "MUXF8"):
            feat["mux"] += ro if CONFIG["vectorless"] else a * fo
            counts["MUXF"] += 1
        elif t in CONFIG["lutram_types"]:
            feat["lutram"] += a * cell_clock.get(name, fo)
            counts["LUTRAM/SRL"] += 1
        elif t in CONFIG["bram_units"]:
            feat["bram"] += CONFIG["bram_units"][t] * cell_clock.get(name, 0.0)
            counts["BRAM18"] += CONFIG["bram_units"][t]
        elif t == "DSP48E1":
            feat["dsp"] += cell_clock.get(name, 0.0)
            counts["DSP48E1"] += 1
        elif t in drc.CONFIG["pll_alias"]:
            k = "mmcm" if drc.CONFIG["pll_alias"][t] == "MMCME2_ADV" else "pll"
            feat[f"{k}_n"] += 1
            feat[f"{k}_vco"] += clk.vco(name) / 1000.0
            counts[k.upper()] += 1
        elif t in drc.CONFIG["clock_bufs"]:
            fb = max([clk.freq(b) for b in net.pins(name, "O").values()] or [0.0])
            feat["clk_bufs"] += fb
            counts[t] += 1
    for b, ss in net.sinks.items():
        if not net.drivers.get(b) or net.is_const(b):
            continue
        fan = sum(1 for s in ss if s[0] != "<port>")
        pips = routing_pips(net.netattr.get(b, {}))
        if is_clock_net(net, b):
            f = clk.freq(b)
            loads = sum(1 for s, sp, _ in ss if s != "<port>" and sp in cp.get(net.cells[s]["type"], ()))
            feat["clk_loads"] += f * loads
            feat["clk_pips"] += f * pips
            continue
        r = rate(b)
        feat["sig_pips"] += r * pips
        feat["sig_fanout"] += r * fan
    pins, sites = D.package_pins(D.CONFIG["default_part"])
    ios = drc.io_ports(net, xdc, pins, sites)
    vcco = defaultdict(float)
    for p, io in ios.items():
        s = drc.IOSTD.get((io["props"].get("IOSTANDARD") or "LVCMOS33").upper()) or drc.IOSTD["LVCMOS33"]
        if io["dir"] in ("output", "inout"):
            src = [x for c in io["cells"] for port, bits in net.cells[c]["conns"].items() for x in bits.values()
                   if any(sk[0] == c for sk in net.sinks.get(x, []))]
            f = max([rate(x) for x in src] or [0.0])
            w = f * s["vcco"] ** 2
            feat["io_out_cv2"] += w
            vcco[s["vcco"]] += w
            if s["kind"] == "diff":
                feat["io_diff_out"] += 0.5
        else:
            feat["io_in"] += 1
        if s["vref"] or s["kind"] == "diff" and s["vcco"] < 2.0:
            feat["io_vref"] += 1
    return {"version": CONFIG["feature_version"], "features": dict(feat), "counts": dict(counts), "vcco_cv2": {f"{k:g}": v for k, v in vcco.items()},
            "netlist": str(netlist_path), "routed": net.routed, "fmax_mhz": fmax}


def load_model(path=None):
    p = Path(path or CONFIG["model"])
    return json.loads(p.read_text()) if p.exists() else None


def estimate(feat, model):
    f = feat["features"]
    cls = {}
    for k, names in CONFIG["class_features"].items():
        co = model["coef"].get(k, {})
        cls[k] = sum(co.get(n, 0.0) * f.get(n, 0.0) for n in names) / 1000.0
    dyn = sum(cls.values())
    st = model["static"]
    static = st["s0"] + st["s1"] * dyn
    rails = {}
    for r, v in CONFIG["rails"].items():
        sh = model["rail_share"].get(r, {})
        idyn = sum(sh.get(k, 0.0) * cls[k] for k in cls) / v
        ist = model["rail_static"].get(r, 0.0) * (static / st["s0"] if st["s0"] else 1.0)
        if r.startswith("Vcco"):
            vv = f"{v:g}"
            tot_cv2 = sum(feat["vcco_cv2"].values()) or 0.0
            frac = feat["vcco_cv2"].get(vv, 0.0) / tot_cv2 if tot_cv2 else (1.0 if r == "Vcco33" else 0.0)
            idyn = cls["I/O"] * model["rail_share"].get("Vcco", {}).get("I/O", 0.0) * frac / v
        if idyn or ist:
            rails[r] = {"voltage": v, "dynamic_a": idyn, "static_a": ist, "total_a": idyn + ist}
    tj = CONFIG["ambient_c"] + model["theta_ja"] * (dyn + static)
    return {"classes": cls, "dynamic_w": dyn, "static_w": static, "total_w": dyn + static, "rails": rails,
            "junction_c": tj}


def format_report(feat, est, model, title):
    out = [f"Report Power (ofx, vectorless estimate) : {title}",
           f"Toggle rate {CONFIG['toggle'] * 100:.1f} % on data nets, clocks at their constrained or derived frequency; "
           f"ambient {CONFIG['ambient_c']:.0f} C; model {model.get('name', 'power_model.json')} "
           f"(fitted to Vivado report_power on {len(model.get('train', []))} designs)", "",
           "1. Summary",
           f"  Total On-Chip Power (W)  {est['total_w']:.3f}",
           f"  Dynamic (W)              {est['dynamic_w']:.3f}",
           f"  Device Static (W)        {est['static_w']:.3f}",
           f"  Junction Temperature (C) {est['junction_c']:.1f}", "",
           "1.1 On-Chip Components",
           f"  {'Component':14s} {'Power (W)':>10s}"]
    for k, v in est["classes"].items():
        out.append(f"  {k:14s} {v:10.4f}")
    out.append(f"  {'Static Power':14s} {est['static_w']:10.4f}")
    out += ["", "1.2 Power Supply Summary", f"  {'Source':9s} {'Voltage':>8s} {'Total (A)':>10s} {'Dynamic (A)':>12s} "
                                                 f"{'Static (A)':>11s}"]
    for r, v in est["rails"].items():
        out.append(f"  {r:9s} {v['voltage']:8.3f} {v['total_a']:10.4f} {v['dynamic_a']:12.4f} {v['static_a']:11.4f}")
    out += ["", "Resources: " + ", ".join(f"{k} {v}" for k, v in sorted(feat["counts"].items()))]
    err = model.get("heldout_error")
    if err:
        out.append(f"Model error on held-out designs vs Vivado: total {err.get('total_mape', 0):.1f} % mean abs, "
                   f"dynamic {err.get('dynamic_mape', 0):.1f} % mean abs (see docs/ofx.md)")
    return "\n".join(out)


def main(build, xdc=None, json_out=None, model_path=None, quiet=False):
    np = D.find_netlist(build)
    if np is None:
        sys.exit(f"ofx power: no netlist in {build}")
    model = load_model(model_path)
    if model is None:
        sys.exit(f"ofx power: no model at {model_path or CONFIG['model']} (run flow/power_fit.py --run)")
    feat = features(np, xdc)
    est = estimate(feat, model)
    if not quiet:
        print(format_report(feat, est, model, str(np)))
    if json_out:
        Path(json_out).write_text(json.dumps({"features": feat, "estimate": est}, indent=1) + "\n")
    return feat, est
