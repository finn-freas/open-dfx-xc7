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
    feat = defaultdict(float)
    counts = defaultdict(int)
    for name, c in net.cells.items():
        t = c["type"]
        outs = [b for p, bits in c["conns"].items() for b in bits.values()
                if any(d[0] == name and d[1] == p for d in net.drivers.get(b, []))]
        fo = max([data_f(b) for b in outs] or [0.0])
        if t in CONFIG["lut_types"]:
            feat["lut"] += a * fo
            counts["LUT"] += 1
        elif t in CONFIG["ff_types"]:
            feat["ff"] += a * cell_clock.get(name, 0.0)
            counts["FF"] += 1
        elif t == "CARRY4":
            feat["carry"] += a * fo
            counts["CARRY4"] += 1
        elif t in ("MUXF7", "MUXF8"):
            feat["mux"] += a * fo
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
        f = data_f(b)
        feat["sig_pips"] += a * f * pips
        feat["sig_fanout"] += a * f * fan
    pins, sites = D.package_pins(D.CONFIG["default_part"])
    ios = drc.io_ports(net, xdc, pins, sites)
    vcco = defaultdict(float)
    for p, io in ios.items():
        s = drc.IOSTD.get((io["props"].get("IOSTANDARD") or "LVCMOS33").upper()) or drc.IOSTD["LVCMOS33"]
        if io["dir"] in ("output", "inout"):
            src = [x for c in io["cells"] for port, bits in net.cells[c]["conns"].items() for x in bits.values()
                   if any(sk[0] == c for sk in net.sinks.get(x, []))]
            f = max([data_f(x) for x in src] or [0.0])
            w = a * f * s["vcco"] ** 2
            feat["io_out_cv2"] += w
            vcco[s["vcco"]] += w
            if s["kind"] == "diff":
                feat["io_diff_out"] += 0.5
        else:
            feat["io_in"] += 1
        if s["vref"] or s["kind"] == "diff" and s["vcco"] < 2.0:
            feat["io_vref"] += 1
    return {"features": dict(feat), "counts": dict(counts), "vcco_cv2": {f"{k:g}": v for k, v in vcco.items()},
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
