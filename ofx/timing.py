import fnmatch
import functools
import json
import re
from collections import defaultdict
from pathlib import Path

from . import reports

CONFIG = {
    "report": "report.json",
    "histogram_bins_ns": (-10.0, -5.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 5.0),
    "untimed_ignored": ("false path", "false path between the clocks"),
    "untimed_unconstrained": ("no clock", "no launch clock", "no capture clock", "unrelated clocks"),
    "untimed_no_capture": ("no clock", "no capture clock"),
    "warn_re": re.compile(r"^Warning: (.*)$"),
    "warn_classes": (
        ("generated_clocks", re.compile(r"create_generated_clock")),
        ("no_clock", re.compile(r"has no timing constraint and will be timed at the default")),
        ("ignored_constraints", re.compile(r"NOT applied|NOT created|NOT supported|isn't supported|ignoring|"
                                           r"matches no|matched no|matched nothing|is not timed|none of this design")),
    ),
    "loops_re": re.compile(r"Found (\d+) combinational loops"),
    "pad_types": ("PAD",),
    "default_freq_why": "clock with no create_clock (nextpnr times it at the --freq default)",
    "constant_net": "$PACKER_",
    "io_delay_attrs": {"input": "NEXTPNR_INPUT_DELAY", "output": "NEXTPNR_OUTPUT_DELAY"},
    "xdc_cmd_re": re.compile(r"^\[run\] nextpnr: .*?(?:^|\s)-o xdc=(\S+)", re.M),
    "clock_xdc_re": re.compile(r"create_clock\b.*?\[get_ports\s+\{?\s*([^\]\}]+?)\s*\}?\]"),
    "clock_opt_re": {"name": re.compile(r"-name\s+\{?([^\s}]+)\}?"),
                     "period": re.compile(r"-period\s+([\d.]+)"),
                     "waveform": re.compile(r"-waveform\s+\{\s*([\d.]+)\s+([\d.]+)\s*\}")},
    "io_delay_xdc_re": re.compile(r"^\s*set_(input|output)_delay\b(.*?)\[get_ports\s+\{?\s*([^\]\}]+?)\s*\}?\]"),
    "clock_groups_re": re.compile(r"^\s*set_clock_groups\b(.*)$"),
    "group_clocks_re": re.compile(r"-group\s+(?:\[get_clocks\s+\{?\s*([^\]\}]+?)\s*\}?\]|\{\s*([^}]+?)\s*\})"),
    "logic_types": ("clk-to-q", "source", "logic"),
    "drop_from_data_path": ("setup", "hold", "clk-skew", "clk-to-clk", "clk-latency", "in-delay", "out-delay"),
    "vivado_checks": ("no_clock", "constant_clock", "pulse_width_clock", "unconstrained_internal_endpoints",
                      "no_input_delay", "no_output_delay", "multiple_clock", "generated_clocks", "loops",
                      "partial_input_delay", "partial_output_delay", "latch_loops"),
    "ofx_checks": ("ignored_constraints", "unrelated_clocks", "async_pins_untimed", "sequential_cells_untimed"),
    "clock_pins": ("C", "CLK", "CLKARDCLK", "CLKBWRCLK", "CLKARDCLKL", "CLKARDCLKU", "CLKBWRCLKL", "CLKBWRCLKU"),
    "clock_buffers": {"IBUF": ("I", "O"), "IBUFG": ("I", "O"), "BUFG": ("I", "O"), "BUFGCTRL": ("I0", "O"),
                      "BUFH": ("I", "O"), "BUFHCE": ("I", "O")},
    "clock_managers": ("MMCME2_ADV", "MMCME2_BASE", "PLLE2_ADV", "PLLE2_BASE"),
    "async_pins": {"FDCE": "CLR", "FDPE": "PRE"},
    "latch_types": ("LDCE", "LDPE"),
    "sync_types": ("FDRE", "FDSE", "FDCE", "FDPE"),
    "pulse_width_speed": "-1",
    "pulse_width": {
        "FDRE/C": {"low": 0.500, "high": 0.500, "min_period": 1.000},
        "FDSE/C": {"low": 0.500, "high": 0.500, "min_period": 1.000},
        "FDCE/C": {"low": 0.500, "high": 0.500, "min_period": 1.000},
        "FDPE/C": {"low": 0.500, "high": 0.500, "min_period": 1.000},
        "BUFG/I": {"min_period": 2.155},
        "BUFGCTRL/I0": {"min_period": 2.155},
        "MMCME2_ADV/CLKIN1": {"min_period": 1.249, "max_period": 100.000, "low": 2.000, "high": 2.000},
        "MMCME2_ADV/CLKFBIN": {"min_period": 1.249, "max_period": 100.000},
        "MMCME2_ADV/CLKFBOUT": {"min_period": 1.249, "max_period": 213.360},
        "MMCME2_ADV/CLKOUT0": {"min_period": 1.249, "max_period": 213.360},
        "MMCME2_ADV/CLKOUT1": {"min_period": 1.249, "max_period": 213.360},
        "MMCME2_ADV/CLKOUT2": {"min_period": 1.249, "max_period": 213.360},
        "MMCME2_ADV/CLKOUT3": {"min_period": 1.249, "max_period": 213.360},
        "MMCME2_ADV/CLKOUT4": {"min_period": 1.249, "max_period": 213.360},
        "MMCME2_ADV/CLKOUT5": {"min_period": 1.249, "max_period": 213.360},
        "MMCME2_ADV/CLKOUT6": {"min_period": 1.249, "max_period": 213.360},
        "PLLE2_ADV/CLKIN1": {"max_period": 52.633, "low": 2.000, "high": 2.000},
        "PLLE2_ADV/CLKFBIN": {"max_period": 52.633},
        "PLLE2_ADV/CLKFBOUT": {"min_period": 1.249},
        **{f"PLLE2_ADV/CLKOUT{k}": {"max_period": 160.000} for k in range(6)},
        "RAMD32/CLK": {"low": 1.250, "high": 1.250},
        "RAMS32/CLK": {"low": 1.250, "high": 1.250},
        "RAMD64E/CLK": {"low": 1.250, "high": 1.250},
        "SRL16E/CLK": {"low": 0.980, "high": 0.980},
        "SRLC32E/CLK": {"low": 0.980, "high": 0.980},
        "ICAPE2/CLK": {"min_period": 10.000},
        "DNA_PORT/CLK": {"min_period": 10.000},
        "XADC/DCLK": {"min_period": 4.000},
        "IDELAYCTRL/REFCLK": {"min_period": 3.225, "max_period": 5.264},
        "ISERDESE2/CLKDIV": {"min_period": 1.667},
        "OSERDESE2/CLKDIV": {"min_period": 1.667},
        "FIFO18E1/RDCLK": {"min_period": 2.576},
        "FIFO36E1/RDCLK": {"min_period": 2.576},
        "RAMB18E1/CLKARDCLK": {"min_period": 2.944, "mode_dependent": True},
        "RAMB18E1/CLKBWRCLK": {"min_period": 2.944, "mode_dependent": True},
        "RAMB36E1/CLKARDCLK": {"min_period": 3.361, "mode_dependent": True},
        "RAMB36E1/CLKBWRCLK": {"min_period": 3.361, "mode_dependent": True},
        "DSP48E1/CLK": {"min_period": 3.884, "mode_dependent": True},
    },
    "exception_names": ((r"datapath_only", "Max Delay Datapath Only"), (r"^set_max_delay", "Max Delay"),
                        (r"^set_min_delay", "Min Delay"), (r"^set_multicycle_path", "Multicycle Path"),
                        (r"^set_false_path", "False Path")),
    "cdc_exceptions": {"Timed": "None", "Asynchronous Groups": "Asynch Clock Groups",
                       "Exclusive Groups": "Exclusive Clock Groups", "Not timed (nextpnr: no common primary)": "None"},
    "pulse_checks": (("min_period", "Min Period"), ("max_period", "Max Period"), ("low", "Low Pulse Width"),
                     ("high", "High Pulse Width")),
}


def load(d):
    f = Path(d) / CONFIG["report"]
    if not f.exists():
        return None, f
    return json.loads(f.read_text()), f


def clock_names(rep):
    names = {}
    for c in rep.get("clocks", []):
        names[c["net"]] = c.get("name") or c["net"]
    return names


def event_clock(event, names):
    if event == "<async>":
        return "(none)"
    edge, _, net = event.partition(" ")
    return names.get(net, net)


def event_edge(event):
    return "fall" if event.startswith("negedge") else "rise"


def pin(e):
    return f"{e['cell']}/{e['port']}"


def worst_per_pin(checks, key):
    w = {}
    for c in checks:
        v = c[key][1]
        p = pin(c)
        if p not in w or v < w[p]:
            w[p] = v
    return w


def unconstrained_clocks(rep):
    return {c["net"] for c in rep.get("clocks", []) if "period" not in c}


def on_unconstrained_clock(e, rep, names):
    nets = unconstrained_clocks(rep)
    return any(ev != "<async>" and ev.partition(" ")[2] in nets for ev in (e["from"], e["to"]))


def timed_checks(eps, rep, names):
    return [e for e in eps if ("setup" in e or "hold" in e) and not on_unconstrained_clock(e, rep, names)]


def summary_row(checks):
    out = {}
    for key in ("setup", "hold"):
        w = worst_per_pin([c for c in checks if key in c], key)
        neg = [v for v in w.values() if v < 0]
        out[key] = {"wns": min(w.values()) if w else None, "tns": sum(neg), "failing": len(neg), "total": len(w)}
    return out


@functools.lru_cache(maxsize=4)
def routed_top(d):
    rj = next(iter(sorted(Path(d).glob("*_routed.json"))), None)
    if rj is None:
        return None, None
    m = json.loads(rj.read_text())["modules"]
    top = next((k for k, v in m.items() if v.get("attributes", {}).get("top")), next(iter(m)))
    return m[top], rj


def port_bits(mod):
    out = {}
    for n, p in mod.get("ports", {}).items():
        for i, b in enumerate(p["bits"]):
            out[b] = n if len(p["bits"]) == 1 else f"{n}[{i}]"
    return out


def pad_cells(d):
    mod, _ = routed_top(str(d))
    if mod is None:
        return {}
    bits = port_bits(mod)
    out = {}
    for n, c in mod.get("cells", {}).items():
        dirs = c.get("port_directions", {})
        for p, conn in c.get("connections", {}).items():
            if dirs.get(p) == "output" and any(b in bits for b in conn):
                out[n] = next(bits[b] for b in conn if b in bits)
    return out


def endpoint_name(e, pads, nl=None):
    """Port name for a pad endpoint, else Vivado's cell/pin name when the netlist is known, else nextpnr's."""
    return pads.get(e["cell"]) or (nl.vpin(e["cell"], e["port"]) if nl is not None else pin(e))


def ports_of(d):
    mod, rj = routed_top(str(d))
    if mod is None:
        return None, None
    attrs = {n: c.get("attributes", {}) for n, c in mod.get("cells", {}).items()}
    out = {}
    for n, p in mod.get("ports", {}).items():
        bits = [n] if len(p["bits"]) == 1 else [f"{n}[{i}]" for i in range(len(p["bits"]))]
        for b in bits:
            out[b] = (p["direction"], attrs.get(b, attrs.get(n, {})), n)
    return out, rj


def xdc_of(d):
    st = Path(d) / "status.json"
    if st.exists():
        cmd = json.loads(st.read_text()).get("cmd", [])
        for c in cmd:
            if isinstance(c, str) and c.startswith("xdc="):
                return Path(c[4:])
    for log in sorted(Path(d).glob("*.log")):
        m = CONFIG["xdc_cmd_re"].search(log.read_text(errors="replace"))
        if m:
            return Path(m.group(1))
    for stage in (Path(d).parent / "stage", Path(d).parent.parent / "stage"):
        found = sorted(stage.glob("*.xdc")) if stage.is_dir() else []
        if len(found) == 1:
            return found[0]
    return None


def xdc_lines(d):
    xdc = xdc_of(d)
    if xdc is None or not xdc.exists():
        return [], None
    return xdc.read_text(errors="replace").splitlines(), xdc


def xdc_clocks(d):
    lines, xdc = xdc_lines(d)
    out = []
    for ln in lines:
        mm = CONFIG["clock_xdc_re"].search(ln)
        if not mm:
            continue
        ports = mm.group(1).split()
        opt = {k: rx.search(ln) for k, rx in CONFIG["clock_opt_re"].items()}
        period = float(opt["period"].group(1)) if opt["period"] else None
        wf = ((float(opt["waveform"].group(1)), float(opt["waveform"].group(2))) if opt["waveform"]
              else (0.0, period / 2 if period else 0.0))
        out.append({"name": opt["name"].group(1) if opt["name"] else ports[0], "ports": ports, "period": period,
                    "waveform": wf})
    return out, xdc


def xdc_clock_ports(d):
    clocks, xdc = xdc_clocks(d)
    return {p for c in clocks for p in c["ports"]}, xdc


def xdc_clock_groups(d):
    lines, _ = xdc_lines(d)
    pairs = {}
    for ln in lines:
        m = CONFIG["clock_groups_re"].match(ln)
        if not m:
            continue
        kind = ("Exclusive Groups" if re.search(r"-(logically|physically)_exclusive", m.group(1))
                else "Asynchronous Groups")
        groups = [(a or b).split() for a, b in CONFIG["group_clocks_re"].findall(m.group(1))]
        for i, ga in enumerate(groups):
            for j, gb in enumerate(groups):
                if i != j:
                    for a in ga:
                        for b in gb:
                            pairs[(a, b)] = kind
    return pairs


def partial_io_delays(d):
    """Ports with only -max or only -min set_input/output_delay (Vivado partial_input/output_delay)."""
    lines, _ = xdc_lines(d)
    ports, _ = ports_of(d)
    seen = {"input": defaultdict(set), "output": defaultdict(set)}
    for ln in lines:
        m = CONFIG["io_delay_xdc_re"].match(ln)
        if not m:
            continue
        opts = m.group(2)
        kinds = {k for k in ("max", "min") if re.search(rf"-{k}\b", opts)} or {"max", "min"}
        for pat in m.group(3).split():
            for b in (ports or {}):
                if fnmatch.fnmatchcase(b, pat) or b.split("[")[0] == pat:
                    seen[m.group(1)][b] |= kinds
    return {k: sorted(b for b, s in v.items() if len(s) == 1) for k, v in seen.items()}


def constant_clocked(rep, eps):
    nets = {c["net"] for c in rep.get("clocks", [])
            if "period" not in c and c["net"].startswith(CONFIG["constant_net"])}
    used = {ev.partition(" ")[2] for e in eps for ev in (e["from"], e["to"]) if ev != "<async>"}
    cells = sorted({e["cell"] for e in eps if e["to"] != "<async>" and e["to"].partition(" ")[2] in nets})
    return sorted(nets & used), cells


def log_warnings(text):
    found = defaultdict(list)
    for ln in (text or "").splitlines():
        m = CONFIG["warn_re"].match(ln)
        if not m:
            continue
        for cls, rx in CONFIG["warn_classes"]:
            if rx.search(m.group(1)):
                found[cls].append(m.group(1).strip())
                break
    return found


class Netlist:
    """Routed nextpnr JSON: original cell types and pins, nets by bit, drivers and sinks."""

    def __init__(self, mod):
        self.cells = mod.get("cells", {})
        self.ports = mod.get("ports", {})
        self.netname = {}
        for n, v in mod.get("netnames", {}).items():
            for b in v["bits"]:
                if b not in self.netname or (self.netname[b][1] and not v.get("hide_name")):
                    self.netname[b] = (n, v.get("hide_name", 0))
        self.netname = {b: n for b, (n, _) in self.netname.items()}
        self.driver, self.sinks = {}, defaultdict(list)
        for cn, c in self.cells.items():
            dirs = c.get("port_directions", {})
            for p, conn in c.get("connections", {}).items():
                for b in conn:
                    if not isinstance(b, int):
                        continue
                    if dirs.get(p) == "output":
                        self.driver[b] = (cn, p)
                    else:
                        self.sinks[b].append((cn, p))
        self.port_bits = port_bits(mod)

    def otype(self, cell):
        c = self.cells.get(cell, {})
        return c.get("attributes", {}).get("X_ORIG_TYPE") or c.get("type", "?")

    def oport(self, cell, port):
        return self.cells.get(cell, {}).get("attributes", {}).get(f"X_ORIG_PORT_{port}", port)

    def vcell(self, cell):
        """Vivado's name of a cell: nextpnr splits RAM32M/RAM64M into DPR<k>_<j> LUT cells; Vivado keeps the macro
        and names the parts RAM<A-D>[_D1] after the LUT (5LUT: RAMx, 6LUT: RAMx_D1)."""
        c = self.cells.get(cell, {})
        a = c.get("attributes", {})
        m = re.match(r"^(.*)/DPR\d+_\d+$", cell)
        bel = a.get("NEXTPNR_BEL", "")
        b = re.search(r"/([A-D])([56])LUT$", bel)
        if m and b and a.get("X_LUT_AS_DRAM"):
            return f"{m.group(1)}/RAM{b.group(1)}{'_D1' if b.group(2) == '6' else ''}"
        return cell

    def vpin(self, cell, port):
        return f"{self.vcell(cell)}/{self.oport(cell, port)}"

    def bit(self, cell, port):
        conn = self.cells.get(cell, {}).get("connections", {}).get(port, [])
        return conn[0] if conn and isinstance(conn[0], int) else None

    def bel_port(self, cell, orig):
        c = self.cells.get(cell, {})
        for p in c.get("connections", {}):
            if self.oport(cell, p) == orig:
                return p
        return None

    def param(self, cell, name, default):
        v = self.cells.get(cell, {}).get("parameters", {}).get(name)
        if v is None:
            return default
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().strip('"')
        if re.fullmatch(r"[01]{32}", s):
            return float(int(s, 2))
        try:
            return float(s)
        except ValueError:
            return default


@functools.lru_cache(maxsize=4)
def netlist(d):
    mod, _ = routed_top(str(d))
    return Netlist(mod) if mod is not None else None


def clock_map(d, rep):
    """Clock name per net bit and the clock table (name -> period, high, offset, master, source, derived)."""
    nl = netlist(str(d))
    if nl is None:
        return None, {}
    clocks, by_bit = {}, {}
    for c in rep.get("clocks", []):
        if "period" not in c:
            continue
        name = c.get("name") or c["net"]
        clocks[name] = {"period": c["period"], "high": c["high"], "offset": c.get("offset", 0),
                        "master": c.get("master"), "source": f"net {c['net']}", "derived": False}
        for b, n in nl.netname.items():
            if n == c["net"]:
                by_bit[b] = name
    pb = {v: b for b, v in nl.port_bits.items()}
    xclocks, _ = xdc_clocks(d)
    for c in xclocks:
        if not c["period"]:
            continue
        clocks.setdefault(c["name"], {"period": c["period"], "high": c["waveform"][1] - c["waveform"][0],
                                      "offset": c["waveform"][0], "master": None,
                                      "source": f"port {' '.join(c['ports'])}", "derived": False})
        for p in c["ports"]:
            if p in pb:
                by_bit.setdefault(pb[p], c["name"])
    bufs = CONFIG["clock_buffers"]
    changed = True
    while changed:
        changed = False
        for b, name in list(by_bit.items()):
            for cell, port in nl.sinks.get(b, []):
                t = nl.otype(cell)
                if t in bufs and nl.oport(cell, port) == bufs[t][0]:
                    ob = nl.bit(cell, nl.bel_port(cell, bufs[t][1]) or "")
                    if ob is not None and ob not in by_bit:
                        by_bit[ob] = name
                        changed = True
            drv = nl.driver.get(b)
            if drv:
                t = nl.otype(drv[0])
                if t in bufs and nl.oport(*drv) == bufs[t][1]:
                    ib = nl.bit(drv[0], nl.bel_port(drv[0], bufs[t][0]) or "")
                    if ib is not None and ib not in by_bit:
                        by_bit[ib] = name
                        changed = True
    for cell, c in nl.cells.items():
        t = nl.otype(cell)
        if t not in CONFIG["clock_managers"]:
            continue
        inb = nl.bit(cell, nl.bel_port(cell, "CLKIN1") or "")
        src = by_bit.get(inb)
        if src is None:
            continue
        tin = clocks[src]["period"]
        mult = nl.param(cell, "CLKFBOUT_MULT_F", nl.param(cell, "CLKFBOUT_MULT", 5.0))
        div = nl.param(cell, "DIVCLK_DIVIDE", 1.0)
        tvco = tin * div / mult
        for out, pname in [("CLKFBOUT", None)] + [(f"CLKOUT{k}", f"CLKOUT{k}_DIVIDE") for k in range(7)]:
            ob = nl.bit(cell, nl.bel_port(cell, out) or "")
            if ob is None or ob in by_bit:
                continue
            o = mult if pname is None else nl.param(cell, pname + ("_F" if out == "CLKOUT0" else ""),
                                                      nl.param(cell, pname, 1.0))
            name = nl.netname.get(ob, f"{cell}/{out}")
            per = round(tvco * o, 3)
            clocks[name] = {"period": per, "high": per / 2, "offset": 0.0, "master": src,
                            "source": f"{cell}/{out}", "derived": True}
            by_bit[ob] = name
            for c2, p2 in nl.sinks.get(ob, []):
                t2 = nl.otype(c2)
                if t2 in bufs and nl.oport(c2, p2) == bufs[t2][0]:
                    b2 = nl.bit(c2, nl.bel_port(c2, bufs[t2][1]) or "")
                    if b2 is not None:
                        by_bit.setdefault(b2, name)
    return by_bit, clocks


def pulse_width(d, rep):
    """Vivado-style pulse width checks (min/max period, low/high pulse) for every clock pin with a table entry."""
    nl = netlist(str(d))
    by_bit, clocks = clock_map(d, rep)
    if nl is None:
        return None, clocks
    table = CONFIG["pulse_width"]
    out = []
    for cell, c in nl.cells.items():
        t = nl.otype(cell)
        loc = c.get("attributes", {}).get("NEXTPNR_BEL", "").split("/")[0]
        done = set()
        for p in c.get("connections", {}):
            op = nl.oport(cell, p)
            key = f"{t}/{op}"
            if key not in table or key in done:
                continue
            done.add(key)
            name = by_bit.get(nl.bit(cell, p))
            if name is None:
                continue
            ck = clocks[name]
            actual = {"min_period": ck["period"], "max_period": ck["period"], "low": ck["period"] - ck["high"],
                      "high": ck["high"]}
            for k, label in CONFIG["pulse_checks"]:
                if k not in table[key]:
                    continue
                req = table[key][k]
                slack = req - actual[k] if k == "max_period" else actual[k] - req
                out.append({"clock": name, "check": label, "lib_pin": key, "required": req, "actual": actual[k],
                            "slack": slack, "loc": loc, "pin": f"{cell}/{op}"})
    return out, clocks


def pw_summary(checks):
    pins = defaultdict(lambda: None)
    for c in checks:
        if pins[c["pin"]] is None or c["slack"] < pins[c["pin"]]:
            pins[c["pin"]] = c["slack"]
    neg = [v for v in pins.values() if v < 0]
    return {"wns": min(pins.values()) if pins else None, "tns": sum(neg), "failing": len(neg), "total": len(pins)}


def check_timing(d, rep, eps, names):
    log = reports.nextpnr_log(d)
    warn = log_warnings(log)
    rows = {}
    nets = [c["net"] for c in rep.get("clocks", []) if "period" not in c]
    unconstrained_clocks = [n for n in nets if not n.startswith(CONFIG["constant_net"])]
    constant, constant_cells = constant_clocked(rep, eps)
    no_clock_eps = sorted({pin(e) for e in eps if event_clock(e["to"], names) in unconstrained_clocks})
    rows["no_clock"] = (len(no_clock_eps), f"endpoints clocked by a clock with no create_clock, timed at the "
                        f"--freq default ({len(unconstrained_clocks)} clock(s): {', '.join(unconstrained_clocks) or '-'})",
                        no_clock_eps)
    rows["constant_clock"] = (len(constant_cells), f"endpoint cells clocked by a constant "
                              f"({', '.join(constant) or '-'})", constant_cells)
    rows["pulse_width_clock"] = (None, "not computed: needs clocks with only a pulse width constraint "
                                 "(set_min_pulse_width), which the XDC reader does not support", [])
    timed = {pin(e) for e in eps if "setup" in e}
    internal = sorted({pin(e) for e in eps if pin(e) not in timed and e.get("type") not in CONFIG["pad_types"]
                       and e.get("untimed") in CONFIG["untimed_no_capture"]})
    internal = sorted(set(internal) | set(no_clock_eps))
    rows["unconstrained_internal_endpoints"] = (len(internal), "endpoints with no capture clock, or captured by a "
                                                "clock with no create_clock", internal)
    ports, rj = ports_of(d)
    clk_ports, xdc = xdc_clock_ports(d)
    if ports is None:
        rows["no_input_delay"] = (None, "no routed JSON, ports not checked", [])
        rows["no_output_delay"] = (None, "no routed JSON, ports not checked", [])
    else:
        note = "" if xdc else "; no XDC found, so clock ports are counted too"
        live = live_ports(d)
        for direction, attr in CONFIG["io_delay_attrs"].items():
            miss = sorted(b for b, (dirn, a, base) in ports.items()
                          if dirn == direction and attr not in a and b not in clk_ports and base not in clk_ports
                          and (live is None or b in live))
            rows[f"no_{direction}_delay"] = (len(miss), f"{direction} ports without set_{direction}_delay "
                                             f"(clock ports, unused inputs and constant outputs excluded{note})",
                                             miss)
    caps = defaultdict(set)
    for e in eps:
        if e["to"] != "<async>":
            caps[pin(e)].add(event_clock(e["to"], names))
    multi = sorted(p for p, s in caps.items() if len(s) > 1)
    rows["multiple_clock"] = (len(multi), "endpoints captured by more than one clock", multi)
    rows["generated_clocks"] = (len(warn["generated_clocks"]), "create_generated_clock not applied",
                                warn["generated_clocks"])
    m = CONFIG["loops_re"].search(log or "")
    rows["loops"] = (int(m.group(1)) if m else 0, "combinational loops (nextpnr topological sort)", [])
    partial = partial_io_delays(d) if ports is not None else {"input": [], "output": []}
    for direction in ("input", "output"):
        rows[f"partial_{direction}_delay"] = (len(partial[direction]), f"{direction} ports with only -max or only "
                                              f"-min set_{direction}_delay", partial[direction])
    nl = netlist(str(d))
    latches = sorted(n for n in (nl.cells if nl else {}) if nl.otype(n) in CONFIG["latch_types"])
    rows["latch_loops"] = ((0 if not latches else None), "no latches in the netlist" if not latches else
                           f"{len(latches)} latch(es); latch loops not analysed", latches)
    rows["ignored_constraints"] = (len(warn["ignored_constraints"]), "XDC lines accepted but not applied",
                                   warn["ignored_constraints"])
    unrel = sorted({(event_clock(e["from"], names), event_clock(e["to"], names)) for e in eps
                    if e.get("untimed") == "unrelated clocks"})
    rows["unrelated_clocks"] = (len(unrel), "clock pairs with paths but no common primary and no exception "
                                "(Vivado times these as 'Timed (unsafe)'; nextpnr only with -o vivado-timing)",
                                [f"{a} -> {b}" for a, b in unrel])
    timed_pins = {pin(e) for e in eps if "setup" in e}
    nl_ = netlist(str(d))
    apins = [p for p in async_pins(d) if nl_ is None or
             f"{p.rsplit('/', 1)[0]}/{nl_.bel_port(*p.rsplit('/', 1))}" not in timed_pins]
    rows["async_pins_untimed"] = (len(apins), "asynchronous set/reset pins driven by logic with no timed "
                                  "endpoint (Vivado: recovery/removal in **async_default**)", apins)
    silent = untimed_sequential(d, rep, eps)
    rows["sequential_cells_untimed"] = (len(silent), "clocked cells on a constrained clock with no timed endpoint "
                                        "or path start (SRL16E/SRLC32E have timing arcs only with -o vivado-timing)",
                                        silent)
    return [(k, *rows[k]) for k in CONFIG["vivado_checks"] + CONFIG["ofx_checks"]]


def async_pins(d):
    nl = netlist(str(d))
    if nl is None:
        return []
    out = []
    for cell in nl.cells:
        p = CONFIG["async_pins"].get(nl.otype(cell))
        if p is None:
            continue
        b = nl.bit(cell, nl.bel_port(cell, p) or "")
        drv = nl.driver.get(b)
        if b is not None and drv and nl.cells[drv[0]].get("type") not in ("PSEUDO_VCC", "PSEUDO_GND"):
            out.append(f"{cell}/{p}")
    return sorted(out)


def is_async_check(nl, e):
    """Vivado puts recovery/removal checks (FDCE CLR, FDPE PRE) in the path group **async_default**."""
    return nl is not None and CONFIG["async_pins"].get(nl.otype(e["cell"])) == nl.oport(e["cell"], e["port"])


def untimed_sequential(d, rep, eps):
    nl = netlist(str(d))
    if nl is None:
        return []
    by_bit, _ = clock_map(d, rep)
    seen = {e["cell"] for e in eps}
    seen |= {path_start(p)["cell"] for p in rep.get("paths", [])}
    out = []
    for cell, c in nl.cells.items():
        t = nl.otype(cell)
        if cell in seen or t in CONFIG["clock_buffers"] or t in CONFIG["clock_managers"]:
            continue
        for p in c.get("connections", {}):
            if nl.oport(cell, p) in CONFIG["clock_pins"] and by_bit.get(nl.bit(cell, p)):
                out.append(f"{cell} ({t})")
                break
    return sorted(out)


def vivado_exception(x):
    """Vivado's name for a nextpnr exception string such as 'set_max_delay -datapath_only (line 13)'."""
    for rx, name in CONFIG["exception_names"]:
        if re.search(rx, x or ""):
            return name
    return x


def live_ports(d):
    """Top ports Vivado's check_timing looks at: inputs whose buffer drives logic, outputs not driven by a constant."""
    nl = netlist(str(d))
    if nl is None:
        return None
    out = set()
    for b, name in nl.port_bits.items():
        for cell, port in nl.sinks.get(b, []):
            if nl.otype(cell) in ("IBUF", "IBUFG", "IBUF_INTERMDISABLE", "IBUF_IBUFDISABLE"):
                ob = nl.bit(cell, nl.bel_port(cell, "O") or "")
                if ob is not None and nl.sinks.get(ob):
                    out.add(name)
        drv = nl.driver.get(b)
        cells = [drv] if drv else []
        cells += [x for x in nl.sinks.get(b, [])]
        for cell, port in cells:
            if nl.otype(cell) in ("OBUF", "OBUFT"):
                ib = nl.bit(cell, nl.bel_port(cell, "I") or "")
                d2 = nl.driver.get(ib)
                if d2 and nl.cells[d2[0]].get("type") not in ("PSEUDO_VCC", "PSEUDO_GND"):
                    out.add(name)
    return out


def cdc_class(d, e):
    """Vivado report_cdc-like class of one asynchronous crossing endpoint."""
    nl = netlist(str(d))
    if nl is None:
        return "Unknown"
    t = nl.otype(e["cell"])
    attrs = nl.cells.get(e["cell"], {}).get("attributes", {})
    async_reg = str(attrs.get("ASYNC_REG", "")).upper() in ("TRUE", "1", "00000000000000000000000000000001")
    drv = nl.driver.get(nl.bit(e["cell"], e["port"]))
    direct = drv is not None and nl.otype(drv[0]) in CONFIG["sync_types"]
    if t in CONFIG["sync_types"] and async_reg:
        return "Safe" if direct else "Unsafe"
    return "Unknown"


def histogram(values):
    bins = CONFIG["histogram_bins_ns"]
    counts = [0] * (len(bins) + 1)
    for v in values:
        i = 0
        while i < len(bins) and v >= bins[i]:
            i += 1
        counts[i] += 1
    labels = [f"< {bins[0]:g}"] + [f"[{bins[i]:g}, {bins[i + 1]:g})" for i in range(len(bins) - 1)] + [f">= {bins[-1]:g}"]
    return list(zip(labels, counts))


def fmt(v, w=9):
    return f"{'-':>{w}}" if v is None else f"{v:{w}.3f}"


def table(title, head, rows):
    print(f"\n{title}")
    print("-" * len(title))
    if not rows:
        print("  (none)")
        return
    print("  " + "  ".join(h for h in head))
    for r in rows:
        print("  " + "  ".join(r))


def sum_cols(s, pw=None):
    a, h = s["setup"], s["hold"]
    out = [fmt(a["wns"]), fmt(a["tns"], 10), f"{a['failing']:7d}", f"{a['total']:7d}",
           fmt(h["wns"]), fmt(h["tns"], 10), f"{h['failing']:7d}", f"{h['total']:7d}"]
    if pw is not None:
        out += [fmt(pw["wns"]), fmt(pw["tns"], 10), f"{pw['failing']:7d}", f"{pw['total']:7d}"]
    return out


SUM_HEAD = ["    WNS(ns)", "   TNS(ns)", "TNS Fail", "TNS Tot", "    WHS(ns)", "   THS(ns)", "THS Fail", "THS Tot"]
PW_HEAD = ["   WPWS(ns)", "  TPWS(ns)", "TPWS Fail", "TPWS Tot"]
EMPTY = {"wns": None, "tns": 0.0, "failing": 0, "total": 0}


def match(pattern, *names):
    return pattern is None or any(fnmatch.fnmatchcase(n, pattern) for n in names if n)


def path_start(p):
    body = [s for s in p["path"] if s["type"] not in ("clk-skew", "clk-to-clk")]
    return body[0]["from"] if body else {"cell": "?", "port": "?"}


def path_stats(p):
    data = [s for s in p["path"] if s["type"] not in CONFIG["drop_from_data_path"]]
    logic = sum(s["delay"] for s in data if s["type"] in CONFIG["logic_types"])
    route = sum(s["delay"] for s in data if s["type"] == "routing")
    levels = sum(1 for s in data if s["type"] == "logic")
    return logic, route, levels


def start_name(st, nl=None):
    if not st.get("port"):
        return st["cell"]
    return nl.vpin(st["cell"], st["port"]) if nl is not None else f"{st['cell']}/{st['port']}"


def clock_desc(clocks, name):
    c = clocks.get(name)
    if not c:
        return name
    rise = c["offset"]
    return f"{name}  {{rise@{rise:.3f}ns fall@{rise + c['high']:.3f}ns period={c['period']:.3f}ns}}"


def cell_desc(nl, cell, event, names, clocks):
    t = nl.otype(cell) if nl else "?"
    if event == "<async>":
        return f"(input port{'' if t in ('PAD', 'IBUF') else ' / ' + t})"
    edge = "falling" if event_edge(event) == "fall" else "rising"
    return f"({edge} edge-triggered cell {t} clocked by {clock_desc(clocks, event_clock(event, names))})"


def print_path(p, names, idx, pads, nl=None, clocks=None):
    clocks = clocks or {}
    slack = p["slack"]
    st, en = path_start(p), p["endpoint"]
    logic, route, levels = path_stats(p)
    data = logic + route
    hold = p["check"] != "setup"
    print(f"\n{idx}. Slack ({'VIOLATED' if slack < 0 else 'MET'}) : {slack:.3f}ns  "
          f"({'arrival time - required time' if hold else 'required time - arrival time'})")
    dest = endpoint_name(en, pads, nl)
    via = f", endpoint pin {pin(en)}" if en["cell"] in pads else ""
    print(f"   Source:          {start_name(st, nl)}")
    print(f"                      {cell_desc(nl, st['cell'], p['from'], names, clocks)}")
    print(f"   Destination:     {dest}{via}")
    print(f"                      {cell_desc(nl, en['cell'], p['to'], names, clocks)}")
    group = "**async_default**" if is_async_check(nl, p["endpoint"]) else event_clock(p['to'], names)
    print(f"   Path Group:      {group}")
    print(f"   Path Type:       {'Hold (Min)' if hold else 'Setup (Max)'} (one corner, nextpnr timer)")
    if p.get("exception"):
        print(f"   Timing Exception: {p['exception']}")
    fc, tc = event_clock(p["from"], names), event_clock(p["to"], names)
    edges = ""
    if p["from"] != "<async>" and p["to"] != "<async>" and not p.get("exception"):
        edges = (f"  ({tc} {event_edge(p['to'])}@{p['requirement']:.3f}ns - {fc} {event_edge(p['from'])}@0.000ns)"
                 if not hold else "")
    print(f"   Requirement:     {p['requirement']:.3f}ns{edges}")
    pct = (lambda x: f" ({100 * x / data:.3f}%)") if data > 0 else (lambda x: "")
    print(f"   Data Path Delay: {data:.3f}ns  (logic {logic:.3f}ns{pct(logic)}  route {route:.3f}ns{pct(route)})")
    kinds = defaultdict(int)
    if nl is not None:
        for s in p["path"]:
            if s["type"] == "logic":
                kinds[nl.otype(s["to"]["cell"])] += 1
    br = " ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
    print(f"   Logic Levels:    {levels}{f'  ({br})' if br else ''}")
    skew = sum(s["delay"] for s in p["path"] if s["type"] in ("clk-skew", "clk-to-clk"))
    if skew:
        print(f"   Clock Path Skew: {skew:.3f}ns (nextpnr clk-skew steps)")
    print(f"     {'Delay Type':12s} {'Incr(ns)':>9s} {'Path(ns)':>9s}  {'Location':>10s}  Netlist Resource(s)")
    acc = 0.0
    for s in p["path"]:
        acc += s["delay"]
        loc = s["to"].get("loc")
        where = f"X{loc[0]}Y{loc[1]}" if loc else ""
        if s["type"] == "routing":
            what = s.get("net")
            kind = "net"
        else:
            what = nl.vpin(s["to"]["cell"], s["to"]["port"]) if nl is not None else f"{s['to']['cell']}/{s['to']['port']}"
            kind = s["type"] if nl is None or s["type"] != "logic" else nl.otype(s["to"]["cell"])
        print(f"     {kind:12s} {s['delay']:9.3f} {acc:9.3f}  {where:>10s}  {what}")
    arrival = p["requirement"] - slack if not hold else p["requirement"] + slack
    if abs(arrival - acc) >= 0.0005:
        print(f"     {'clock':12s} {arrival - acc:9.3f} {arrival:9.3f}  {'':>10s}  register clock delays "
              f"(launch minus capture), not itemized by nextpnr")
    print(f"     {'required':12s} {'':9s} {p['requirement']:9.3f}")
    print(f"     {'slack':12s} {'':9s} {slack:9.3f}")


def clock_tree_rows(clocks, masters_used):
    rows, done = [], set()

    def add(name, depth):
        if name in done:
            return
        done.add(name)
        c = clocks[name]
        wf = f"{{{c['offset']:.3f} {c['offset'] + c['high']:.3f}}}"
        note = [f"({c['source']})"]
        if c.get("derived"):
            note.insert(0, "derived by ofx from the clock manager, no endpoints")
        rows.append([f"{'  ' * depth + name:24s}", f"{wf:18s}", f"{c['period']:10.3f}", f"{1000 / c['period']:10.3f}",
                     " ".join(note)])
        for k in sorted(n for n, v in clocks.items() if v.get("master") == name):
            add(k, depth + 1)

    for name in sorted(n for n, v in clocks.items() if not v.get("master") or v["master"] not in clocks):
        add(name, 0)
    for name in sorted(clocks):
        add(name, 0)
    return rows


def interaction(d, rep, eps, names):
    """report_clock_interaction-like rows: one per launch/capture clock pair seen at an endpoint."""
    groups = xdc_clock_groups(d)
    _, clocks = clock_map(d, rep)
    pairs = defaultdict(list)
    for e in eps:
        if e["from"] == "<async>" or e["to"] == "<async>" or on_unconstrained_clock(e, rep, names):
            continue
        pairs[(event_clock(e["from"], names), event_clock(e["to"], names))].append(e)
    rows = []
    for (a, b), v in sorted(pairs.items()):
        timed = [e for e in v if "setup" in e]
        untimed = [e for e in v if "setup" not in e]
        s = summary_row(timed)["setup"]
        req = None
        if timed:
            w = min(timed, key=lambda e: e["setup"][1])
            req = w["setup"][0]
        edges = sorted({f"{event_edge(e['from'])} - {event_edge(e['to'])}" for e in v})
        why = sorted({e.get("untimed") for e in untimed})
        exc = sorted({e.get("exception") for e in timed if e.get("exception")})
        if not untimed and not exc:
            cons = "Timed" if clock_root(clocks, a) == clock_root(clocks, b) else "Timed (unsafe)"
        elif not timed and why == ["unrelated clocks"]:
            cons = "Not timed (nextpnr: no common primary)"
        elif not timed:
            cons = groups.get((a, b)) or "False Path"
        elif untimed:
            cons = "Partial False Path"
        else:
            cons = ", ".join(sorted({vivado_exception(x) for x in exc}))
        rows.append({"from": a, "to": b, "edges": ", ".join(edges), "wns": s["wns"], "tns": s["tns"],
                     "failing": s["failing"], "total": len({pin(e) for e in v}), "req": req, "constraints": cons,
                     "endpoints": v})
    return rows


def clock_root(clocks, name):
    seen = set()
    while name in clocks and clocks[name].get("master") and name not in seen:
        seen.add(name)
        name = clocks[name]["master"]
    return name


def cdc_rows(d, inter, clocks=None):
    clocks = clocks or {}
    out = []
    for r in inter:
        if r["from"] == r["to"]:
            continue
        safe = unsafe = unknown = no_async = 0
        seen = set()
        for e in r["endpoints"]:
            if pin(e) in seen:
                continue
            seen.add(pin(e))
            if "setup" in e and not e.get("exception"):
                safe += 1
                continue
            k = cdc_class(d, e)
            safe += k == "Safe"
            unsafe += k == "Unsafe"
            unknown += k == "Unknown"
        common = clock_root(clocks, r["from"]) == clock_root(clocks, r["to"])
        kind = ("Safely Timed" if r["constraints"] == "Timed" else "User Ignored" if common
                else "No Common Primary Clock")
        exc = CONFIG["cdc_exceptions"].get(r["constraints"], r["constraints"])
        sev = "Critical" if unsafe or unknown else "Warning" if no_async else "Info"
        out.append([sev, r["from"], r["to"], kind, exc, len(seen), safe, unsafe, unknown, no_async])
    return out


def path_groups(timed, names, order):
    by = defaultdict(list)
    for e in timed:
        by[(event_clock(e["from"], names), event_clock(e["to"], names))].append(e)
    rank = {n: i for i, n in enumerate(order)}
    keys = sorted(by, key=lambda k: (k[0] != k[1], rank.get(k[1], 999), rank.get(k[0], 999), k))
    return keys, by


def print_one(d, args):
    rep, rf = load(d)
    log = Path(d) / "nextpnr.log"
    print(f"== {d}")
    print(f"   nextpnr report {rf}{'' if rep else ' (missing)'}, log {log}")
    if rep is None or "endpoints" not in rep:
        bad = reports.print_timing([Path(d)])
        print("   per-endpoint slack, hold and N worst paths need nextpnr with --report-paths "
              "(docs/drafts/nextpnr-timing-report.patch; ofx.toml [timing] nextpnr/report_paths)")
        return bad
    print("   timer: nextpnr (one corner, the chipdb's delays); hold and pulse width are always reported")
    names = clock_names(rep)
    nl = netlist(str(d))
    vp = (lambda c, p: nl.vpin(c, p)) if nl is not None else (lambda c, p: f"{c}/{p}")
    eps = [e for e in rep["endpoints"] if match(args.to, e["cell"], pin(e), vp(e["cell"], e["port"]),
                                                  event_clock(e["to"], names))]
    if args.from_ and not args.to:
        eps = [e for e in eps if match(args.from_, event_clock(e["from"], names))]

    rows = check_timing(d, rep, rep["endpoints"], names)
    print("\ncheck_timing")
    print("------------")
    nviv = len(CONFIG["vivado_checks"])
    for i, (name, n, what, items) in enumerate(rows, 1):
        tag = "" if i <= nviv else " [ofx]"
        print(f"  {i}. checking {name} ({'-' if n is None else n}){tag}: {what}")
        for it in items[:args.list]:
            print(f"       {it}")
        if len(items) > args.list:
            print(f"       ... {len(items) - args.list} more")

    pw, clocks = pulse_width(d, rep)
    pw = pw or []
    timed = timed_checks(eps, rep, names)
    s = summary_row(timed)
    table("Design Timing Summary", SUM_HEAD + PW_HEAD, [sum_cols(s, pw_summary(pw))])
    if not pw:
        print("  pulse width: no clock pin with a table entry (ofx/timing.py CONFIG pulse_width)")

    constant, _ = constant_clocked(rep, rep["endpoints"])
    crows = clock_tree_rows(clocks, set())
    for c in rep.get("clocks", []):
        if "period" not in c and (not c["net"].startswith(CONFIG["constant_net"]) or c["net"] in constant):
            what = "constant" if c["net"].startswith(CONFIG["constant_net"]) else "no create_clock"
            crows.append([f"{c['net']:24s}", f"{'-':18s}", f"{'-':>10s}", f"{'-':>10s}", what])
    table("Clock Summary", ["Clock                   ", "Waveform(ns)      ", "Period(ns)", "Freq(MHz)"], crows)
    order = [r[0].strip() for r in crows]

    async_eps = [e for e in timed if is_async_check(nl, e)]
    keys, by_pair = path_groups([e for e in timed if not is_async_check(nl, e)], names, order)
    pw_by = defaultdict(list)
    for c in pw:
        pw_by[c["clock"]].append(c)
    intra_names = [n for n in order if n in clocks]
    intra = []
    for n in intra_names:
        v = by_pair.get((n, n), [])
        if v or pw_by.get(n):
            intra.append([f"{n:24s}"] + sum_cols(summary_row(v) if v else {"setup": EMPTY, "hold": EMPTY},
                                                 pw_summary(pw_by.get(n, []))))
    for (a, b) in keys:
        if a == b and a not in intra_names:
            intra.append([f"{a:24s}"] + sum_cols(summary_row(by_pair[(a, b)]), pw_summary([])))
    inter = [[f"{a:16s}", f"{b:16s}"] + sum_cols(summary_row(by_pair[(a, b)])) for (a, b) in keys if a != b]
    table("Intra Clock Table", ["Clock                   "] + SUM_HEAD + PW_HEAD, intra)
    table("Inter Clock Table", ["From Clock      ", "To Clock        "] + SUM_HEAD, inter)
    agroups = defaultdict(list)
    for e in async_eps:
        agroups[(event_clock(e["from"], names), event_clock(e["to"], names))].append(e)
    table("Other Path Groups Table (recovery = setup columns, removal = hold columns)",
          ["Path Group         ", "From Clock      ", "To Clock        "] + SUM_HEAD,
          [[f"{'**async_default**':19s}", f"{a:16s}", f"{b:16s}"] + sum_cols(summary_row(v))
           for (a, b), v in sorted(agroups.items())])

    exc = defaultdict(list)
    for e in timed:
        if e.get("exception"):
            exc[e["exception"]].append(e)
    table("Timing Exceptions (paths that an exception constrains)", ["Exception                                 "] + SUM_HEAD,
          [[f"{k:42s}"] + sum_cols(summary_row(v)) for k, v in sorted(exc.items())])

    ignored, uncon = defaultdict(set), defaultdict(set)
    for e in eps:
        u = e.get("untimed") or (CONFIG["default_freq_why"] if on_unconstrained_clock(e, rep, names) else None)
        key = (event_clock(e["from"], names), event_clock(e["to"], names), u)
        if u in CONFIG["untimed_ignored"]:
            ignored[key].add(pin(e))
        elif u in CONFIG["untimed_unconstrained"] + (CONFIG["default_freq_why"],):
            uncon[key].add(pin(e))
    table("User Ignored Paths", ["From Clock      ", "To Clock        ", "Endpoints", "Why"],
          [[f"{a:16s}", f"{b:16s}", f"{len(v):9d}", u] for (a, b, u), v in sorted(ignored.items())])
    table("Unconstrained Paths", ["From Clock      ", "To Clock        ", "Endpoints", "Why"],
          [[f"{a:16s}", f"{b:16s}", f"{len(v):9d}", u] for (a, b, u), v in sorted(uncon.items())])

    inter_rows = interaction(d, rep, eps, names)
    table("Clock Interaction (report_clock_interaction)",
          ["From Clock      ", "To Clock        ", "Edges        ", "  WNS(ns)", "   TNS(ns)", "Fail", "Total",
           "WNS Req(ns)", "Inter-Clock Constraints"],
          [[f"{r['from']:16s}", f"{r['to']:16s}", f"{r['edges']:13s}", fmt(r["wns"]), fmt(r["tns"], 10),
            f"{r['failing']:4d}", f"{r['total']:5d}", fmt(r["req"], 11), r["constraints"]] for r in inter_rows])
    table("CDC (report_cdc-like: Safe = ASYNC_REG capture fed directly by a flip-flop)",
          ["Severity", "Source Clock    ", "Dest Clock      ", "CDC Type                ", "Exceptions          ",
           "Endpoints", "Safe", "Unsafe", "Unknown", "No ASYNC_REG"],
          [[f"{r[0]:8s}", f"{r[1]:16s}", f"{r[2]:16s}", f"{r[3]:24s}", f"{r[4]:20s}", f"{r[5]:9d}", f"{r[6]:4d}",
            f"{r[7]:6d}", f"{r[8]:7d}", f"{r[9]:12d}"] for r in cdc_rows(d, inter_rows, clocks)])

    for key in ("setup", "hold"):
        w = worst_per_pin([e for e in timed if key in e], key)
        table(f"{key.capitalize()} slack histogram (worst slack per endpoint, ns)", ["Slack range       ", "Endpoints"],
              [[f"{lab:18s}", f"{n:9d}"] for lab, n in histogram(w.values())])

    paths = [p for p in rep.get("paths", [])]
    paths = [p for p in paths if match(args.from_, path_start(p)["cell"], event_clock(p["from"], names))
             and match(args.to, p["endpoint"]["cell"], pin(p["endpoint"]), vp(p["endpoint"]["cell"], p["endpoint"]["port"]),
                       event_clock(p["to"], names))]
    untimed = [p for p in paths if on_unconstrained_clock(p, rep, names)]
    paths = [p for p in paths if not on_unconstrained_clock(p, rep, names)]
    paths.sort(key=lambda p: p["slack"])
    per = defaultdict(int)
    for p in rep.get("paths", []):
        per[(p["from"], p["to"], p["check"])] += 1
    print(f"\nTiming Details: per path group, the {args.paths} worst setup (Max Delay) and hold (Min Delay) paths"
          f" (nextpnr wrote up to {max(per.values()) if per else 0} per clock pair and check)")
    print("-" * 60)
    if untimed:
        print(f"  {len(untimed)} path(s) on a clock with no create_clock left out (Unconstrained Paths above)")
    pads = pad_cells(d)
    extra = sorted(({(event_clock(p["from"], names), event_clock(p["to"], names)) for p in paths}
                    | {(r["from"], r["to"]) for r in inter_rows if r["from"] != r["to"]}) - set(keys))
    gkeys = ([(n, n) for n in order if (n, n) in by_pair or pw_by.get(n)]
             + [k for k in keys if k[0] == k[1] and k[0] not in order]
             + [k for k in keys if k[0] != k[1]] + extra)
    shown = 0
    for (a, b) in gkeys:
        v = by_pair.get((a, b), [])
        sr = summary_row(v) if v else None
        print("\n" + "-" * 99)
        print(f"From Clock:  {a}\n  To Clock:  {b}\n")
        for k, lab in (("setup", "Setup"), ("hold", "Hold ")):
            if sr is None:
                print(f"{lab} : {'NA':>12s}  Failing Endpoints,  Worst Slack {'NA':>12s}  ,  Total Violation {'NA':>12s}")
                continue
            x = sr[k]
            print(f"{lab} : {x['failing']:12d}  Failing Endpoints,  Worst Slack {fmt(x['wns'], 12)}ns,  "
                  f"Total Violation {fmt(x['tns'], 12)}ns")
        if a == b:
            x = pw_summary(pw_by.get(a, []))
            print(f"PW    : {x['failing']:12d}  Failing Endpoints,  Worst Slack {fmt(x['wns'], 12)}ns,  "
                  f"Total Violation {fmt(x['tns'], 12)}ns")
        print("-" * 99)
        for check, title in (("setup", "Max Delay Paths"), ("hold", "Min Delay Paths")):
            sel = [p for p in paths if p["check"] == check and event_clock(p["from"], names) == a
                   and event_clock(p["to"], names) == b and not is_async_check(nl, p["endpoint"])][:args.paths]
            if not sel:
                continue
            print(f"\n{title}\n" + "-" * 86)
            for i, p in enumerate(sel, 1):
                shown += 1
                print_path(p, names, i, pads, nl, clocks)
        if a == b and pw_by.get(a):
            print_pulse(a, clocks, pw_by[a])
    for (a, b), v in sorted(agroups.items()):
        sr = summary_row(v)
        print("\n" + "-" * 99)
        print(f"Path Group:  **async_default**\nFrom Clock:  {a}\n  To Clock:  {b}\n")
        for k, lab in (("setup", "Recovery"), ("hold", "Removal ")):
            x = sr[k]
            print(f"{lab} : {x['failing']:9d}  Failing Endpoints,  Worst Slack {fmt(x['wns'], 12)}ns,  "
                  f"Total Violation {fmt(x['tns'], 12)}ns")
        print("-" * 99)
        for check, title in (("setup", "Max Delay Paths (recovery)"), ("hold", "Min Delay Paths (removal)")):
            sel = [p for p in paths if p["check"] == check and event_clock(p["from"], names) == a
                   and event_clock(p["to"], names) == b and is_async_check(nl, p["endpoint"])][:args.paths]
            if sel:
                print(f"\n{title}\n" + "-" * 86)
            for i, p in enumerate(sel, 1):
                shown += 1
                print_path(p, names, i, pads, nl, clocks)
    if not shown:
        print("  (no path matches)")
    return int((s["setup"]["failing"] or 0) > 0 or (s["hold"]["failing"] or 0) > 0)


def print_pulse(name, clocks, checks):
    c = clocks.get(name, {})
    print("\nPulse Width Checks\n" + "-" * 86)
    print(f"Clock Name:         {name}")
    if c:
        print(f"Waveform(ns):       {{ {c['offset']:.3f} {c['offset'] + c['high']:.3f} }}")
        print(f"Period(ns):         {c['period']:.3f}")
        print(f"Sources:            {{ {c['source']} }}")
    print(f"\n{'Check Type':18s}{'Lib Pin':22s}{'Required(ns)':>13s}{'Actual(ns)':>12s}{'Slack(ns)':>11s}  "
          f"{'Location':22s}Pin")
    worst = {}
    for k in checks:
        if k["check"] not in worst or k["slack"] < worst[k["check"]]["slack"]:
            worst[k["check"]] = k
    for _, label in CONFIG["pulse_checks"]:
        k = worst.get(label)
        if k:
            print(f"{label:18s}{k['lib_pin']:22s}{k['required']:13.3f}{k['actual']:12.3f}{k['slack']:11.3f}  "
                  f"{k['loc']:22s}{k['pin']}")


def print_timing(dirs, args):
    bad = 0
    for d in dirs:
        bad += print_one(d, args) or 0
    return bad
