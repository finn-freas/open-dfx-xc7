import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from . import ROOT

CONFIG = {
    "db": ROOT / "toolchain" / "openxc7" / "share" / "nextpnr" / "external" / "prjxray-db",
    "default_part": "xc7a35tcsg324-1",
    "families": {"xc7a": "artix7", "xc7k": "kintex7", "xc7s": "spartan7", "xc7z": "zynq7"},
    "status": "status.json",
    "routed_glob": "*_routed.json",
    "const_types": ("PSEUDO_VCC", "PSEUDO_GND", "VCC", "GND"),
    "xdc_cmd_re": re.compile(r"^\s*(set_property|create_clock|create_generated_clock)\s+(.*)$"),
    "obj_re": re.compile(r"^\[\s*(get_ports|get_nets|get_pins|get_cells|get_iobanks|current_design)\b(.*)\]$", re.S),
}


def family(part):
    return next((f for p, f in CONFIG["families"].items() if part.startswith(p)), "artix7")


def package_pins(part):
    f = CONFIG["db"] / family(part) / part / "package_pins.csv"
    pins, sites = {}, {}
    if not f.exists():
        return pins, sites
    with open(f) as fh:
        for r in csv.DictReader(fh):
            bank = int(r["bank"]) if r["bank"].isdigit() else r["bank"]
            rec = {"pin": r["pin"], "bank": bank, "site": r["site"], "tile": r["tile"], "function": r["pin_function"]}
            pins[r["pin"]] = rec
            sites[r["site"]] = rec
    return pins, sites


def glob_re(pat):
    return re.escape(pat).replace(r"\*", ".*").replace(r"\?", ".")


def glob_match(name, pat, nocase=False):
    return re.fullmatch(glob_re(pat), name, re.I if nocase else 0) is not None


def bus(name):
    m = re.fullmatch(r"(.*)\[(\d+)\]", name)
    return (m.group(1), int(m.group(2))) if m else (name, None)


def as_int(v, default=0):
    if v is None:
        return default
    s = str(v).strip()
    if re.fullmatch(r"[01]+", s):
        return int(s, 2)
    try:
        return int(float(s))
    except ValueError:
        return default


def as_float(v, default=0.0):
    if v is None:
        return default
    s = str(v).strip()
    if re.fullmatch(r"[01]+", s):
        return float(int(s, 2))
    try:
        return float(s)
    except ValueError:
        return default


def as_str(v, default=""):
    if v is None:
        return default
    s = str(v).strip()
    if re.fullmatch(r"[01]+", s) and len(s) % 8 == 0 and len(s) >= 8:
        b = int(s, 2).to_bytes(len(s) // 8, "big").lstrip(b"\0")
        if b and all(32 <= c < 127 for c in b):
            return b.decode()
    return s


class Netlist:
    def __init__(self, path):
        self.path = Path(path)
        j = json.loads(self.path.read_text())
        mods = j["modules"]
        top = next((m for m in mods.values() if as_int(m.get("attributes", {}).get("top"), 0)), None)
        self.top = top or mods.get("top") or next(iter(mods.values()))
        self.routed = any("NEXTPNR_BEL" in c.get("attributes", {}) for c in self.top["cells"].values())
        self.ports = self.top.get("ports", {})
        self.netname = {}
        self.netattr = {}
        for n, v in self.top.get("netnames", {}).items():
            for b in v["bits"]:
                if isinstance(b, int) and (b not in self.netname or (v.get("hide_name") == 0 and "$" not in n)):
                    self.netname[b] = n if len(v["bits"]) == 1 else f"{n}[{v['bits'].index(b)}]"
                    self.netattr[b] = v.get("attributes", {})
        self.cells = {}
        self.drivers = defaultdict(list)
        self.sinks = defaultdict(list)
        for name, c in self.top["cells"].items():
            a = c.get("attributes", {})
            typ = a.get("X_ORIG_TYPE", c["type"])
            dirs = c.get("port_directions", {})
            conns = defaultdict(dict)
            for p, bits in c.get("connections", {}).items():
                if self.routed and "X_ORIG_TYPE" in a and f"X_ORIG_PORT_{p}" not in a and c["type"] != "PAD":
                    continue
                orig = a.get(f"X_ORIG_PORT_{p}", p) if self.routed else p
                for k, b in enumerate(bits):
                    on = orig.split()[0] if len(bits) == 1 else f"{orig}[{k}]"
                    base, idx = bus(on)
                    conns[base][idx if idx is not None else 0] = b
                    if not isinstance(b, int):
                        continue
                    d = dirs.get(p, "input")
                    if d in ("output", "inout"):
                        self.drivers[b].append((name, base, idx))
                    if d in ("input", "inout"):
                        self.sinks[b].append((name, base, idx))
            self.cells[name] = {"type": typ, "ptype": c["type"], "params": c.get("parameters", {}), "attrs": a,
                                "conns": dict(conns), "bel": a.get("NEXTPNR_BEL")}
        self.port_bits = {}
        for p, v in self.ports.items():
            for k, b in enumerate(v["bits"]):
                self.port_bits[p if len(v["bits"]) == 1 else f"{p}[{k}]"] = (b, v["direction"])
        for p, (b, d) in self.port_bits.items():
            if isinstance(b, int):
                if d in ("input", "inout"):
                    self.drivers[b].append(("<port>", p, None))
                if d in ("output", "inout"):
                    self.sinks[b].append(("<port>", p, None))

    def name(self, b):
        return self.netname.get(b, f"net{b}") if isinstance(b, int) else str(b)

    def pin(self, cell, port, idx=0):
        return self.cells[cell]["conns"].get(port, {}).get(idx)

    def pins(self, cell, port):
        return self.cells[cell]["conns"].get(port, {})

    def is_const(self, b):
        if not isinstance(b, int):
            return True
        return any(c != "<port>" and self.cells[c]["ptype"] in CONFIG["const_types"] for c, _, _ in self.drivers.get(b, []))

    def driver(self, b):
        ds = [d for d in self.drivers.get(b, []) if d[0] == "<port>" or self.cells[d[0]]["ptype"] not in ("PAD",)]
        return ds[0] if ds else (None, None, None)

    def of_type(self, *types):
        return [n for n, c in self.cells.items() if c["type"] in types]

    def param(self, cell, key, default=None):
        p = self.cells[cell]["params"]
        return p[key] if key in p else default


def find_netlist(build):
    b = Path(build)
    if b.is_file():
        return b
    r = sorted(b.glob(CONFIG["routed_glob"]))
    if r:
        return r[0]
    st = b / CONFIG["status"]
    if st.exists():
        top = json.loads(st.read_text()).get("top")
        if top and (b / f"{top}.json").exists():
            return b / f"{top}.json"
    j = [p for p in sorted(b.glob("*.json")) if p.name not in ("report.json", "status.json")]
    return j[0] if j else None


def _split_objs(arg):
    arg = arg.strip()
    out = []
    for tok in re.findall(r"\{[^}]*\}|\S+", arg):
        if tok.startswith("-"):
            continue
        out += tok.strip("{}").split()
    return out


def _tcl_words(s):
    out, i = [], 0
    while i < len(s):
        if s[i].isspace():
            i += 1
            continue
        if s[i] in "{[":
            close = "}" if s[i] == "{" else "]"
            depth, j = 0, i
            while j < len(s):
                if s[j] == s[i]:
                    depth += 1
                elif s[j] == close:
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            out.append(s[i:j + 1])
            i = j + 1
            continue
        if s[i] == '"':
            j = s.index('"', i + 1) if '"' in s[i + 1:] else len(s)
            out.append(s[i + 1:j])
            i = j + 1
            continue
        j = i
        while j < len(s) and not s[j].isspace():
            j += 1
        out.append(s[i:j])
        i = j
    return out


class Xdc:
    def __init__(self, paths):
        self.ports = defaultdict(dict)
        self.design = {}
        self.banks = defaultdict(dict)
        self.nets = []
        self.cells = []
        self.clocks = []
        self.port_patterns = []
        for p in [x for x in (paths or []) if x]:
            self._read(Path(p))

    def _read(self, path):
        text = path.read_text(errors="replace")
        text = re.sub(r"\\\n", " ", text)
        for line in text.splitlines():
            line = line.split(";")[0] if not line.lstrip().startswith("#") else ""
            m = CONFIG["xdc_cmd_re"].match(line)
            if not m:
                continue
            cmd, rest = m.groups()
            words = _tcl_words(rest)
            objs = [CONFIG["obj_re"].match(w) for w in words if w.startswith("[")]
            objs = [o for o in objs if o]
            if cmd == "create_clock":
                per = None
                name = None
                for k, w in enumerate(words):
                    if w == "-period" and k + 1 < len(words):
                        per = float(words[k + 1])
                    if w == "-name" and k + 1 < len(words):
                        name = words[k + 1]
                for o in objs:
                    if o.group(1) == "get_ports":
                        for pat in _split_objs(o.group(2)):
                            self.clocks.append({"port": pat, "period": per, "name": name or pat})
                continue
            if cmd != "set_property":
                continue
            plain = [w for w in words if not w.startswith("[")]
            props = {}
            if plain and plain[0] == "-dict":
                kv = _tcl_words(plain[1].strip("{}")) if len(plain) > 1 else []
                props = {kv[i].upper(): kv[i + 1] for i in range(0, len(kv) - 1, 2)}
            elif len(plain) >= 2:
                props = {plain[0].upper(): plain[1].strip("{}")}
            for o in objs:
                kind, arg = o.group(1), o.group(2)
                if kind == "current_design":
                    self.design.update(props)
                elif kind == "get_iobanks":
                    for b in _split_objs(arg):
                        self.banks[int(b) if b.isdigit() else b].update(props)
                elif kind == "get_ports":
                    for pat in _split_objs(arg):
                        self.port_patterns.append((pat, props))
                elif kind == "get_nets":
                    self.nets.append((_split_objs(arg), props, arg))
                elif kind in ("get_pins", "get_cells"):
                    self.cells.append((_split_objs(arg), props, arg))

    def port_props(self, port):
        out = {}
        for pat, props in self.port_patterns:
            if glob_match(port, pat):
                out.update(props)
        return out

    def net_prop(self, key):
        return [(pats, props[key], raw) for pats, props, raw in self.nets if key in props]

    def clock_period(self, port):
        for c in self.clocks:
            if glob_match(port, c["port"]):
                return c["period"]
        return None


def part_of(build, default=None):
    st = Path(build) / CONFIG["status"] if Path(build).is_dir() else Path(build).parent / CONFIG["status"]
    if st.exists():
        s = json.loads(st.read_text())
        if s.get("part"):
            return s["part"]
    return default or CONFIG["default_part"]


def xdc_of(build):
    b = Path(build) if Path(build).is_dir() else Path(build).parent
    log = b / "nextpnr.log"
    if log.exists():
        m = re.search(r"xdc=(\S+\.xdc)", log.read_text(errors="replace")[:20000])
        if m and Path(m.group(1)).exists():
            return Path(m.group(1))
    return None
