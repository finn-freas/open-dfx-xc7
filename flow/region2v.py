import argparse
import collections
import hashlib
import json
import pickle
import random
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "fabric": region.CONFIG["fabric"],
    "margin": 8,
    "cache": ROOT / "build" / "region2v" if region.CONFIG["fabric"] == region.device.CONFIG["fabric"]
    else ROOT / "build" / "region2v" / region.CONFIG["fabric"],
    "fasm_python": ROOT / "toolchain" / "openxc7" / "libexec" / "tabbypy3",
    "bit2fasm": ROOT / "flow" / "bit2fasm.py",
    "tools": ROOT / "toolchain" / "oss-cad-suite" / "bin",
    "cells_sim": ROOT / "toolchain" / "oss-cad-suite" / "share" / "yosys" / "xilinx" / "cells_sim.v",
    "rtl_dir": ROOT / "designs" / "rv_soc" / "pr",
    "ports_json": ROOT / "designs" / "rv_soc" / "pr" / "ports.json",
    "clb_types": ("CLBLL_L", "CLBLL_R", "CLBLM_L", "CLBLM_R"),
    "int_types": ("INT_L", "INT_R"),
    "bram_types": ("BRAM_L", "BRAM_R"),
    "dsp_types": ("DSP_L", "DSP_R"),
    "interface_prefixes": ("BRAM_INT_INTERFACE_", "INT_INTERFACE_"),
    "const_wires": {"VCC_WIRE": "1'b1", "GND_WIRE": "1'b0", "DSP_GND_L": "1'b0", "DSP_GND_R": "1'b0",
                    "DSP_VCC_L": "1'b1", "DSP_VCC_R": "1'b1"},
    "bram_model": ROOT / "designs" / "rv_soc" / "tb" / "r2v_ramb36e1.v",
    "clocked_warmup": 1,
    "n_random": 3000,
    "seed": 20261105,
    "edge_words": [0x00000000, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 0x00000001, 0xFFFFFFFE,
                   0x12345678, 0x0F0F0F0F, 0xAAAAAAAA, 0x55555555, 0x0000001F, 0x00000021],
    "edge_functs": [0, 1, 2, 3, 0x3FF, 0x3FE],
}

DB = region.DB

SLICE_FEATURES = [
    (r"(?P<l>[A-D])LUT\.INIT", "lut_init"),
    (r"(?P<l>[A-D])LUT\.DI1MUX\.\w+", "ram_only"),
    (r"(?P<l>[A-D])LUT\.(?P<v>RAM|SRL|SMALL)", "unsupported"),
    (r"(?P<v>WA7USED|WA8USED|WEMUX\.CE|LATCH)", "unsupported"),
    (r"(?P<l>[A-D])FF\.(?P<v>ZINI|ZRST)", "ff"),
    (r"(?P<l>[A-D])5FF\.(?P<v>ZINI|ZRST)", "ff5"),
    (r"(?P<l>[A-D])FFMUX\.(?P<v>O6|O5|XOR|CY|F7|F8|[A-D]X)", "ffmux"),
    (r"(?P<l>[A-D])5FFMUX\.(?P<v>IN_A|IN_B)", "ff5mux"),
    (r"(?P<l>[A-D])OUTMUX\.(?P<v>O6|O5|XOR|CY|F7|F8|[A-D]5Q)", "outmux"),
    (r"CARRY4\.(?P<l>[A-D])CY0", "cy0"),
    (r"PRECYINIT\.(?P<v>C0|C1|AX|CIN)", "precyinit"),
    (r"(?P<v>CEUSEDMUX|SRUSEDMUX|FFSYNC|CLKINV|NOCLKINV)", "ctrl"),
]

MUX_LEGAL = {
    "F7": "AC",
    "F8": "B",
}

FF_PRIMS = {
    (True, True): ("FDRE", "R"),
    (True, False): ("FDSE", "S"),
    (False, True): ("FDCE", "CLR"),
    (False, False): ("FDPE", "PRE"),
}

LETTERS = "ABCD"


class R2VError(Exception):
    pass


def die(msg):
    raise R2VError(msg)


def sanitize(s):
    return re.sub(r"\W", "_", s)


_tt = {}


def tile_type(ty):
    if ty not in _tt:
        d = json.loads((DB / f"tile_type_{ty}.json").read_text())
        pips = {}
        for p in d["pips"].values():
            pips[(p["src_wire"], p["dst_wire"])] = p
        wires = list(d["wires"]) if isinstance(d["wires"], (dict, list)) else []
        ppips = {"always": [], "default": [], "hint": []}
        pp = DB / f"ppips_{ty.lower()}.db"
        if pp.exists():
            for line in pp.read_text().splitlines():
                if not line.strip():
                    continue
                name, kind = line.split()
                _, dst, src = name.split(".", 2)
                ppips.setdefault(kind, []).append((dst, src))
        _tt[ty] = {"pips": pips, "wires": wires, "wire_set": set(wires), "sites": d.get("sites", []), "ppips": ppips}
    return _tt[ty]


_zero = {}


def zero_encoded(ty):
    if ty not in _zero:
        out = set()
        f = DB / f"segbits_{ty.lower()}.db"
        if f.exists():
            for line in f.read_text().splitlines():
                name, *bits = line.split()
                if bits and all(b.startswith("!") for b in bits):
                    out.add(name.split(".", 1)[1])
        _zero[ty] = out
    return _zero[ty]


_st = {}


def site_type(ty):
    if ty not in _st:
        d = json.loads((DB / f"site_type_{ty}.json").read_text())
        _st[ty] = {k: v["direction"] for k, v in d["site_pins"].items()}
    return _st[ty]


def cache_dir(*parts):
    p = CONFIG["cache"].joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def bit_to_fasm(bit):
    out = cache_dir("fasm") / f"{sanitize(Path(bit).stem)}_{file_sha(bit)}.fasm"
    if not out.exists():
        tmp = out.with_suffix(".tmp")
        tmp.unlink(missing_ok=True)
        subprocess.run([str(CONFIG["fasm_python"]), str(CONFIG["bit2fasm"]), "--verbose", str(bit), str(tmp)],
                       check=True, stdout=subprocess.DEVNULL)
        tmp.rename(out)
    return out


def parse_fasm(path):
    feats = collections.defaultdict(dict)
    unknown = []
    for raw in Path(path).read_text().splitlines():
        m = re.search(r'unknown_bit\s*=\s*"([0-9a-fA-F]+)_(\d+)_(\d+)"', raw)
        if m:
            unknown.append((int(m.group(1), 16), int(m.group(2)), int(m.group(3))))
            continue
        line = re.sub(r"\{.*\}", "", raw.split("#", 1)[0]).strip()
        if not line:
            continue
        m = re.fullmatch(r"(\w+)\.([\w.]+?)(?:\[(\d+)(?::(\d+))?\])?(?:\s*=\s*(\d+)'([bhd])([0-9a-fA-F_]+))?", line)
        if not m:
            die(f"unparsable FASM line: {line}")
        tile, feat, hi, lo, _, base, digits = m.groups()
        val = 1 if digits is None else int(digits.replace("_", ""), {"b": 2, "h": 16, "d": 10}[base])
        if hi is None:
            if val != 1:
                die(f"FASM feature with value {val}: {line}")
            feats[tile][feat] = True
            continue
        hi = int(hi)
        lo = int(lo) if lo is not None else hi
        cur = feats[tile].setdefault(feat, set())
        if cur is True:
            die(f"FASM feature both plain and indexed: {line}")
        for i in range(hi - lo + 1):
            if (val >> i) & 1:
                cur.add(lo + i)
    return feats, unknown


class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        p = self.p
        root = a
        while p.get(root, root) != root:
            root = p[root]
        while p.get(a, a) != root:
            p[a], a = root, p[a]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def build_nodes(grid, spec):
    out = cache_dir("graph") / f"nodes_{sanitize(spec)}_m{CONFIG['margin']}.pkl"
    if out.exists():
        return pickle.loads(out.read_bytes())
    rtiles = region.region_tiles(grid, spec)
    xs = [grid[t]["grid_x"] for t in rtiles]
    ys = [grid[t]["grid_y"] for t in rtiles]
    m = CONFIG["margin"]
    x0, x1, y0, y1 = min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m
    at = {(t["grid_x"], t["grid_y"]): (n, t["type"]) for n, t in grid.items()
          if x0 <= t["grid_x"] <= x1 and y0 <= t["grid_y"] <= y1}
    by_type = collections.defaultdict(list)
    for xy, (n, ty) in at.items():
        by_type[ty].append((xy, n))
    tc = json.loads((DB / CONFIG["fabric"] / "tileconn.json").read_text())
    uf = UF()
    crossing = []
    for rule in tc:
        dx, dy = rule["grid_deltas"]
        ta, tb = rule["tile_types"]
        for (x, y), n in by_type.get(ta, []):
            other = at.get((x + dx, y + dy))
            if not other or other[1] != tb:
                continue
            ina, inb = n in rtiles, other[0] in rtiles
            for wa, wb in rule["wire_pairs"]:
                uf.union((n, wa), (other[0], wb))
                if ina != inb:
                    crossing.append((n, wa) if ina else (other[0], wb))
    node_of = {}
    members = collections.defaultdict(list)
    for t in rtiles:
        for w in tile_type(grid[t]["type"])["wires"]:
            r = uf.find((t, w))
            members[r].append((t, w))
    roots = sorted(members, key=lambda r: min(members[r]))
    rid = {r: i for i, r in enumerate(roots)}
    for r, ms in members.items():
        for tw in ms:
            node_of[tw] = rid[r]
    names = [None] * len(roots)
    wires = [None] * len(roots)
    for r, i in rid.items():
        ms = sorted(members[r], key=lambda tw: (not tw[0].startswith("INT"), tw))
        names[i] = "n_" + sanitize(f"{ms[0][0]}__{ms[0][1]}")
        wires[i] = ms
    leaves = [False] * len(roots)
    for tw in crossing:
        r = uf.find(tw)
        if r in rid:
            leaves[rid[r]] = True
    res = {"node_of": node_of, "names": names, "wires": wires, "leaves": leaves, "rtiles": sorted(rtiles)}
    out.write_bytes(pickle.dumps(res))
    return res


def coverage_key(rest):
    k = re.sub(r"^[A-D](?=(LUT|FF|5FF|FFMUX|5FFMUX|OUTMUX)\.)", "N", rest)
    k = re.sub(r"^CARRY4\.[A-D]CY0$", "CARRY4.NCY0", k)
    return re.sub(r"^(NFFMUX|NOUTMUX)\.[A-D](X|5Q)$", r"\1.N\2", k)


def classify_slice_feature(feat):
    for pat, kind in SLICE_FEATURES:
        m = re.fullmatch(pat, feat)
        if m:
            return kind, m.groupdict()
    return None, None


class Model:
    def __init__(self, grid, spec, fasm_path):
        self.grid = grid
        self.spec = spec
        self.g = build_nodes(grid, spec)
        self.rtiles = set(self.g["rtiles"])
        self.feats, unknown = parse_fasm(fasm_path)
        self.coverage = collections.Counter()
        self.check_unknown(unknown)
        self.slices = {}
        self.sites = {}
        self.port_pairs = []
        self.brams = {}
        self.dsps = {}
        self.site_pin_node = {}
        self.drv = collections.defaultdict(list)
        self.default1 = set()
        self.fanout = collections.defaultdict(list)
        self.fasm_pips = []
        self.load_tiles()

    def node(self, tile, wire):
        k = (tile, wire)
        if k not in self.g["node_of"]:
            die(f"wire {tile}/{wire} not in region node graph")
        return self.g["node_of"][k]

    def check_unknown(self, unknown):
        words = region.region_bits({t: self.grid[t] for t in self.rtiles})
        inside = [u for u in unknown if u[0] in words and u[1] in words[u[0]]]
        self.unknown_outside = len(unknown) - len(inside)
        if inside:
            die(f"{len(inside)} bits in region frames/words not decoded by prjxray-db, e.g. "
                + ", ".join(f"{f:08x}_{w}_{b}" for f, w, b in inside[:5]))

    def load_tiles(self):
        for t in sorted(self.rtiles):
            ty = self.grid[t]["type"]
            tt = tile_type(ty)
            feats = self.feats.get(t, {})
            if ty in CONFIG["int_types"]:
                self.load_int(t, ty, tt, feats)
            elif ty in CONFIG["clb_types"]:
                self.load_clb(t, ty, tt, feats)
            elif ty.startswith(CONFIG["interface_prefixes"]):
                self.load_pips(t, ty, tt, feats, "interface")
            elif ty in CONFIG["bram_types"]:
                site = {f: v for f, v in feats.items() if f.split(".")[0] not in tt["wire_set"]}
                self.load_pips(t, ty, tt, {f: v for f, v in feats.items() if f not in site}, "BRAM tile")
                self.load_bram(t, ty, tt, site)
            elif ty in CONFIG["dsp_types"]:
                site = {f: v for f, v in feats.items() if f.split(".")[0] not in tt["wire_set"]}
                self.load_pips(t, ty, tt, {f: v for f, v in feats.items() if f not in site}, "DSP tile")
                self.load_dsp(t, ty, tt, site)
            elif feats:
                die(f"region tile {t} of unsupported type {ty} has features {sorted(feats)[:5]}")
            for dst, src in tt["ppips"].get("always", []):
                self.add_drv(self.node(t, dst), ("always", self.node(t, src), f"{t}.{dst}.{src}"))
            for dst, src in tt["ppips"].get("default", []):
                if src != "VCC_WIRE":
                    die(f"default ppip {ty}.{dst}.{src} with a source other than VCC_WIRE")
                self.default1.add(self.node(t, dst))
            for w in tt["wires"]:
                if w in CONFIG["const_wires"]:
                    self.add_drv(self.node(t, w), ("const", CONFIG["const_wires"][w], f"{t}.{w}"))
        for n, ds in self.drv.items():
            for d in ds:
                if d[0] in ("pip", "always"):
                    self.fanout[d[1]].append(n)

    def add_drv(self, n, d):
        if d not in self.drv[n]:
            self.drv[n].append(d)

    def load_pips(self, t, ty, tt, feats, label):
        always = set(tt["ppips"].get("always", []))
        zero = zero_encoded(ty)
        dsts = collections.Counter(f.split(".")[0] for f in feats)
        for f, v in feats.items():
            if f in zero and dsts[f.split(".")[0]] > 1:
                self.coverage[f"{label} zero-bit default pip dropped (another pip drives the same wire)"] += 1
                continue
            parts = f.split(".")
            if len(parts) != 2 or v is not True:
                die(f"unsupported {label} feature {t}.{f}")
            dst, src = parts
            if (dst, src) in always:
                self.coverage[f"{label} always-on pip (FASM)"] += 1
                continue
            p = tt["pips"].get((src, dst))
            if p is None or p.get("is_pseudo") == "1":
                die(f"{label} feature {t}.{f} is not a configurable pip of {ty}")
            self.coverage[f"{label} pip"] += 1
            name = f"{t}.{dst}.{src}"
            self.fasm_pips.append(name)
            self.add_drv(self.node(t, dst), ("pip", self.node(t, src), name))

    def site_pins(self, key, t, s):
        pins = {p: d["wire"] for p, d in s["site_pins"].items()}
        dirs = site_type(s["type"])
        for p, w in pins.items():
            n = self.node(t, w)
            self.site_pin_node[(key, p)] = n
            if dirs.get(p) == "OUT":
                self.add_drv(n, ("cell", key, p))
        return pins

    def load_bram(self, t, ty, tt, feats):
        if not feats:
            return
        used = [h for h in ("RAMB18_Y0", "RAMB18_Y1") if feats.get(f"{h}.IN_USE") is True]
        if not used:
            for f, v in feats.items():
                zero_init = re.fullmatch(r"RAMB18_Y[01]\.INITP?_[0-9A-F]{2}", f) and not v
                if not (Bram.UNUSED_OK.fullmatch(f) or zero_init):
                    die(f"unused BRAM tile {t} has feature {f}")
                self.coverage["BRAM unused tile " + re.sub(r"RAMB18_Y[01]", "RAMB18_Yn", f)] += 1
            return
        if used != ["RAMB18_Y0", "RAMB18_Y1"]:
            die(f"{t}: BRAM halves in use {used}; only a whole RAMB36E1 is modelled ({sorted(feats)[:4]})")
        s = [x for x in tt["sites"] if x["type"] == "RAMBFIFO36E1"]
        if len(s) != 1:
            die(f"{t}: no RAMBFIFO36E1 site")
        key = f"{t}.RAMB36"
        b = Bram(self, key, t, feats)
        self.site_pins(key, t, s[0])
        self.brams[key] = b
        self.sites[key] = b

    def load_dsp(self, t, ty, tt, feats):
        per = collections.defaultdict(dict)
        for f, v in feats.items():
            m = re.fullmatch(r"DSP48\.DSP_([01])\.(\w+)", f)
            if not m:
                die(f"unknown DSP feature {t}.{f}")
            per[int(m.group(1))][m.group(2)] = v
        for k, fs in sorted(per.items()):
            s = [x for x in tt["sites"] if x["type"] == "DSP48E1" and x["y_coord"] == k]
            if len(s) != 1:
                die(f"{t}: no DSP48E1 site with y_coord {k}")
            key = f"{t}.DSP_{k}"
            d = Dsp(self, key, t, fs)
            self.site_pins(key, t, s[0])
            self.dsps[key] = d
            self.sites[key] = d

    def load_int(self, t, ty, tt, feats):
        for f, v in feats.items():
            parts = f.split(".")
            if len(parts) != 2 or v is not True:
                die(f"unsupported INT feature {t}.{f}")
            dst, src = parts
            p = tt["pips"].get((src, dst))
            kind = "INT pip DST.SRC"
            if p is None:
                p = tt["pips"].get((dst, src))
                if p is None or p.get("is_directional") != "0":
                    die(f"INT feature {t}.{f} is not a pip of {ty}")
                kind = "INT bidirectional pip DST.SRC"
            if p.get("is_pseudo") == "1":
                die(f"INT feature {t}.{f} is a pseudo pip (unsupported)")
            if p.get("is_directional") != "1":
                kind = "INT bidirectional pip DST.SRC"
            self.coverage[kind] += 1
            name = f"{t}.{dst}.{src}"
            self.fasm_pips.append(name)
            self.add_drv(self.node(t, dst), ("pip", self.node(t, src), name))

    def load_clb(self, t, ty, tt, feats):
        sites = {}
        for s in tt["sites"]:
            prefix = f"{s['type']}_X{s['x_coord']}"
            sites[prefix] = s
        per = collections.defaultdict(dict)
        for f, v in feats.items():
            pre, _, rest = f.partition(".")
            if pre not in sites:
                die(f"CLB feature {t}.{f}: unknown site prefix")
            kind, gd = classify_slice_feature(rest)
            if kind is None:
                die(f"unknown CLB feature {t}.{f}")
            if kind == "unsupported":
                die(f"unsupported CLB feature {t}.{f} (LUTRAM/SRL/latch are not modelled)")
            if kind == "lut_init":
                if v is True:
                    die(f"LUT INIT without index {t}.{f}")
            elif v is not True:
                die(f"indexed value on non-INIT feature {t}.{f}")
            val = gd.get("v")
            letter = gd.get("l")
            if kind in ("ffmux", "outmux") and val:
                if val in MUX_LEGAL and letter not in MUX_LEGAL[val]:
                    die(f"illegal mux source {t}.{f}")
                if re.fullmatch(r"[A-D](X|5Q)", val) and val[0] != letter:
                    die(f"illegal mux source {t}.{f}")
            self.coverage[coverage_key(rest)] += 1
            per[pre][rest] = v
        for pre, s in sites.items():
            key = f"{t}.{pre}"
            pins = {p: d["wire"] for p, d in s["site_pins"].items()}
            sl = Slice(self, key, t, s["type"], per.get(pre, {}), pins)
            self.slices[key] = sl
            self.sites[key] = sl
            self.site_pins(key, t, s)

    def resolve_driver(self, n):
        ds = self.drv.get(n, [])
        if len(ds) > 1 and all(d[0] == "always" for d in ds):
            ds = [d for d in ds if self.drv.get(d[1])] or ds
        if len(ds) > 1:
            die(f"node {self.g['names'][n]} has {len(ds)} drivers: {[d[2] if d[0] != 'cell' else d[1:] for d in ds]}")
        if ds:
            return ds[0]
        if n in self.default1:
            return ("const", "1'b1", "default VCC ppip")
        if self.g["leaves"][n]:
            return ("port", None, None)
        return ("undriven", None, None)

    def trace_back(self, n):
        seen = set()
        while n not in seen:
            seen.add(n)
            d = self.resolve_driver(n)
            if d[0] in ("pip", "always"):
                n = d[1]
                continue
            return n, d
        die("routing loop")

    def trace_fwd(self, n, outputs):
        seen, q, hits = {n}, collections.deque([n]), []
        while q:
            x = q.popleft()
            if x in outputs:
                hits.append(x)
            for y in self.fanout.get(x, []):
                if y not in seen:
                    seen.add(y)
                    q.append(y)
        return sorted(hits, key=lambda i: self.g["names"][i])


def lut_support(init, n):
    sup = []
    for i in range(n):
        b = 1 << i
        if any(((init >> k) & 1) != ((init >> (k ^ b)) & 1) for k in range(1 << n)):
            sup.append(i)
    return sup


class Slice:
    def __init__(self, model, key, tile, stype, feats, pins):
        self.m = model
        self.key = key
        self.tile = tile
        self.stype = stype
        self.f = feats
        self.pins = pins
        self.id = sanitize(key)
        self.memo = {}
        self.gen = None

    def init(self, letter):
        v = self.f.get(f"{letter}LUT.INIT", set())
        return sum(1 << i for i in v)

    def pin(self, p):
        return self.gen.net(self.m.site_pin_node[(self.key, p)])

    def one_of(self, prefix):
        vals = [k[len(prefix):] for k in self.f if k.startswith(prefix)]
        if len(vals) != 1:
            die(f"{self.key}: expected exactly one {prefix}* feature, found {vals}")
        return vals[0]

    def lut(self, letter, out):
        k = ("lut", letter, out)
        if k in self.memo:
            return self.memo[k]
        init = self.init(letter)
        n = 6 if out == 6 else 5
        if n == 5:
            init &= (1 << 32) - 1
        sup = lut_support(init, n)
        name = f"c_{self.id}_{letter}O{out}"
        self.memo[k] = name
        args = [self.pin(f"{letter}{i + 1}") if i in sup else "1'b0" for i in range(n)]
        conns = ", ".join(f".I{i}({a})" for i, a in enumerate(args))
        prim = "LUT6" if n == 6 else "LUT5"
        self.gen.cell(prim, f"{name}_i", f"{1 << n}'h{init:0{(1 << n) // 4}x}", f"{conns}, .O({name})", name)
        return name

    def f7(self, letter):
        k = ("f7", letter)
        if k in self.memo:
            return self.memo[k]
        name = f"c_{self.id}_F7{letter}"
        self.memo[k] = name
        lo, hi, sel = ("B", "A", "AX") if letter == "A" else ("D", "C", "CX")
        self.gen.cell("MUXF7", f"{name}_i", None,
                      f".I0({self.lut(lo, 6)}), .I1({self.lut(hi, 6)}), .S({self.pin(sel)}), .O({name})", name)
        return name

    def f8(self):
        k = ("f8",)
        if k in self.memo:
            return self.memo[k]
        name = f"c_{self.id}_F8"
        self.memo[k] = name
        self.gen.cell("MUXF8", f"{name}_i", None,
                      f".I0({self.f7('C')}), .I1({self.f7('A')}), .S({self.pin('BX')}), .O({name})", name)
        return name

    def carry(self):
        k = ("carry",)
        if k in self.memo:
            return self.memo[k]
        name = f"c_{self.id}_CY"
        self.memo[k] = name
        pre = self.one_of("PRECYINIT.")
        cyinit = {"C0": "1'b0", "C1": "1'b1", "AX": None, "CIN": None}[pre]
        if cyinit is None:
            cyinit = self.pin(pre)
        di = [self.lut(l, 5) if f"CARRY4.{l}CY0" in self.f else self.pin(f"{l}X") for l in LETTERS]
        s = [self.lut(l, 6) for l in LETTERS]
        self.gen.wire(f"{name}_CO", 4)
        self.gen.wire(f"{name}_O", 4)
        self.gen.cell("CARRY4", f"{name}_i", None,
                      f".CI(1'b0), .CYINIT({cyinit}), .DI({{{', '.join(reversed(di))}}}), "
                      f".S({{{', '.join(reversed(s))}}}), .CO({name}_CO), .O({name}_O)", None)
        return name

    def source(self, letter, v):
        i = LETTERS.index(letter)
        if v == "O6":
            return self.lut(letter, 6)
        if v in ("O5", "IN_A"):
            return self.lut(letter, 5)
        if v == "XOR":
            return f"{self.carry()}_O[{i}]"
        if v == "CY":
            return f"{self.carry()}_CO[{i}]"
        if v == "F7":
            return self.f7(letter)
        if v == "F8":
            return self.f8()
        if v == "IN_B":
            return self.pin(f"{letter}X")
        if re.fullmatch(r"[A-D]X", v):
            return self.pin(v)
        if re.fullmatch(r"[A-D]5Q", v):
            return self.ff(letter, True)
        die(f"{self.key}: no model for mux source {v}")

    def ff(self, letter, five):
        k = ("ff", letter, five)
        if k in self.memo:
            return self.memo[k]
        tag = f"{letter}5FF" if five else f"{letter}FF"
        name = f"c_{self.id}_{tag}"
        self.memo[k] = name
        d = self.source(letter, self.one_of(f"{tag}MUX."))
        clkinv = "CLKINV" in self.f
        if clkinv == ("NOCLKINV" in self.f):
            die(f"{self.key}: CLKINV/NOCLKINV not exactly one")
        sync = "FFSYNC" in self.f
        zrst = f"{tag}.ZRST" in self.f
        init = 0 if f"{tag}.ZINI" in self.f else 1
        prim, srpin = FF_PRIMS[(sync, zrst)]
        ce = self.pin("CE") if "CEUSEDMUX" in self.f else "1'b1"
        sr = self.pin("SR") if "SRUSEDMUX" in self.f else "1'b0"
        params = f"1'b{init}), .IS_C_INVERTED(1'b{int(clkinv)}"
        self.gen.cell(prim, f"{name}_i", params,
                      f".C({self.pin('CLK')}), .CE({ce}), .{srpin}({sr}), .D({d}), .Q({name})", name)
        return name

    def out(self, p):
        if p in LETTERS:
            return self.lut(p, 6)
        m = re.fullmatch(r"([A-D])(MUX|Q)", p)
        if m and m.group(2) == "MUX":
            return self.source(m.group(1), self.one_of(f"{m.group(1)}OUTMUX."))
        if m:
            return self.ff(m.group(1), False)
        if p == "COUT":
            return f"{self.carry()}_CO[3]"
        die(f"{self.key}: output pin {p} has no model")


def bits_of(v, width):
    if v is True:
        return 1
    if not v:
        return 0
    if max(v) >= width:
        die(f"bit {max(v)} beyond width {width}")
    return sum(1 << i for i in v)


def remap_bram36_init(y0, y1, n, width=256):
    out = {}
    for idx in range(n // 2):
        lo0, lo1 = y0.get(idx, 0), y1.get(idx, 0)
        for k, part in ((2 * idx, 0), (2 * idx + 1, 128)):
            v = 0
            for i in range(128):
                v |= ((lo0 >> (part + i)) & 1) << (2 * i)
                v |= ((lo1 >> (part + i)) & 1) << (2 * i + 1)
            out[k] = v
    return out


class Bram:
    KNOWN = re.compile(r"RAMB18_Y[01]\.(IN_USE|INITP?_[0-9A-F]{2}|ZINIT_[AB]|ZSRVAL_[AB]|DO[AB]_REG|READ_WIDTH_[AB]_\d+|"
                       r"WRITE_WIDTH_[AB]_\d+|WRITE_MODE_[AB]_(READ_FIRST|NO_CHANGE)|ZINV_\w+|RSTREG_PRIORITY_[AB]_\w+|"
                       r"RDADDR_COLLISION_HWCONFIG_\w+)|RAMB36\.(BRAM36_(READ|WRITE)_WIDTH_[AB]_1|RAM_EXTENSION_[AB]_NONE_OR_UPPER)|"
                       r"ZALMOST_(EMPTY|FULL)_OFFSET|CASCOUT_(ARD|BWR)_ACTIVE")
    UNUSED_OK = re.compile(r"CASCOUT_(ARD|BWR)_ACTIVE|RAMB18_Y[01]\.(RDADDR_COLLISION_HWCONFIG_DELAYED_WRITE|"
                           r"(READ|WRITE)_WIDTH_[AB]_1|RSTREG_PRIORITY_[AB]_RSTREG)|RAMB36\.RAM_EXTENSION_[AB]_NONE_OR_UPPER")
    PINS_LU = {"CLKARDCLK": ("CLKARDCLKL", "CLKARDCLKU"), "CLKBWRCLK": ("CLKBWRCLKL", "CLKBWRCLKU"),
               "ENARDEN": ("ENARDENL", "ENARDENU"), "ENBWREN": ("ENBWRENL", "ENBWRENU"),
               "REGCEAREGCE": ("REGCEAREGCEL", "REGCEAREGCEU"), "REGCEB": ("REGCEBL", "REGCEBU"),
               "RSTRAMARSTRAM": ("RSTRAMARSTRAMLRST", "RSTRAMARSTRAMU"), "RSTRAMB": ("RSTRAMBL", "RSTRAMBU"),
               "RSTREGARSTREG": ("RSTREGARSTREGL", "RSTREGARSTREGU"), "RSTREGB": ("RSTREGBL", "RSTREGBU")}
    BUSES = {"ADDRARDADDR": (16, "ADDRARDADDRL{}", "ADDRARDADDRU{}", 15), "ADDRBWRADDR": (16, "ADDRBWRADDRL{}", "ADDRBWRADDRU{}", 15),
             "WEA": (4, "WEAL{}", "WEAU{}", 4), "WEBWE": (8, "WEBWEL{}", "WEBWEU{}", 8),
             "DIADI": (32, "DIADI{}", None, 0), "DIBDI": (32, "DIBDI{}", None, 0),
             "DIPADIP": (4, "DIPADIP{}", None, 0), "DIPBDIP": (4, "DIPBDIP{}", None, 0)}
    OUTS = {"DOADO": 32, "DOBDO": 32, "DOPADOP": 4, "DOPBDOP": 4}

    def __init__(self, model, key, tile, feats):
        self.m = model
        self.key = key
        self.tile = tile
        self.f = feats
        self.id = sanitize(key)
        self.gen = None
        self.memo = {}
        for f in feats:
            if not self.KNOWN.fullmatch(f):
                die(f"BRAM feature {tile}.{f} is not modelled (FIFO, ECC, cascade and SDP are not)")
            self.m.coverage["BRAM " + re.sub(r"_[0-9A-F]{2}$", "_xx", f.split(".", 1)[-1])] += 1
        self.params = self.decode()

    def has(self, f):
        v = self.f.get(f)
        return v is True or (isinstance(v, set) and 0 in v)

    def width(self, kind, port):
        w = [int(m.group(1)) for f in self.f for m in [re.fullmatch(rf"RAMB18_Y0\.{kind}_WIDTH_{port}_(\d+)", f)] if m]
        if len(w) != 1:
            die(f"{self.key}: expected one RAMB18_Y0.{kind}_WIDTH_{port}_*, found {w}")
        if w[0] == 1:
            return 1 if self.has(f"RAMB36.BRAM36_{kind}_WIDTH_{port}_1") else 2
        return {2: 4, 4: 9, 9: 18, 18: 36}[w[0]]

    def decode(self):
        p = {}
        for half in ("RAMB18_Y0", "RAMB18_Y1"):
            for kind in ("READ", "WRITE"):
                for port in "AB":
                    w0 = [f for f in self.f if f.startswith(f"{half}.{kind}_WIDTH_{port}_")]
                    if half == "RAMB18_Y1" and sorted(x.split(".", 1)[1] for x in w0) != sorted(
                            x.split(".", 1)[1] for x in self.f if x.startswith(f"RAMB18_Y0.{kind}_WIDTH_{port}_")):
                        die(f"{self.key}: RAMB18_Y0/Y1 width features differ for {kind} {port}")
        p["RAM_MODE"] = '"TDP"'
        for kind in ("READ", "WRITE"):
            for port in "AB":
                p[f"{kind}_WIDTH_{port}"] = self.width(kind, port)
        for port in "AB":
            p[f"DO{port}_REG"] = int(self.has(f"RAMB18_Y0.DO{port}_REG"))
            if self.has(f"RAMB18_Y0.DO{port}_REG") != self.has(f"RAMB18_Y1.DO{port}_REG"):
                die(f"{self.key}: DO{port}_REG differs between halves")
            mode = "NO_CHANGE" if self.has(f"RAMB18_Y0.WRITE_MODE_{port}_NO_CHANGE") else \
                "READ_FIRST" if self.has(f"RAMB18_Y0.WRITE_MODE_{port}_READ_FIRST") else "WRITE_FIRST"
            p[f"WRITE_MODE_{port}"] = f'"{mode}"'
            for what in ("INIT", "SRVAL"):
                lo = bits_of(self.f.get(f"RAMB18_Y0.Z{what}_{port}"), 18) ^ 0x3FFFF
                hi = bits_of(self.f.get(f"RAMB18_Y1.Z{what}_{port}"), 18) ^ 0x3FFFF
                p[f"{what}_{port}"] = f"36'h{(hi << 18) | lo:09x}"
        for pin in ("CLKARDCLK", "CLKBWRCLK", "ENARDEN", "ENBWREN", "RSTRAMARSTRAM", "RSTRAMB", "RSTREGARSTREG", "RSTREGB"):
            inv = not self.has(f"RAMB18_Y0.ZINV_{pin}")
            if inv != (not self.has(f"RAMB18_Y1.ZINV_{pin}")):
                die(f"{self.key}: ZINV_{pin} differs between halves")
            p[f"IS_{pin}_INVERTED"] = f"1'b{int(inv)}"
        init = remap_bram36_init({i: bits_of(self.f.get(f"RAMB18_Y0.INIT_{i:02X}"), 256) for i in range(64)},
                                 {i: bits_of(self.f.get(f"RAMB18_Y1.INIT_{i:02X}"), 256) for i in range(64)}, 128)
        initp = remap_bram36_init({i: bits_of(self.f.get(f"RAMB18_Y0.INITP_{i:02X}"), 256) for i in range(8)},
                                  {i: bits_of(self.f.get(f"RAMB18_Y1.INITP_{i:02X}"), 256) for i in range(8)}, 16)
        self.init_words = init
        self.initp_words = initp
        full = sum(init[i] << (256 * i) for i in range(128))
        fullp = sum(initp[i] << (256 * i) for i in range(16))
        p["INIT"] = f"32768'h{full:08192x}"
        p["INITP"] = f"4096'h{fullp:01024x}"
        return p

    def words(self, port="A"):
        w = self.params[f"READ_WIDTH_{port}"]
        d, pb = {36: (32, 4), 18: (16, 2), 9: (8, 1)}.get(w, (w, 0))
        full = sum(self.init_words[i] << (256 * i) for i in range(128))
        fullp = sum(self.initp_words[i] << (256 * i) for i in range(16))
        n = 32768 // d
        return [((full >> (i * d)) & ((1 << d) - 1)) | ((((fullp >> (i * pb)) & ((1 << pb) - 1)) if pb else 0) << d)
                for i in range(n)], d + pb

    def pin(self, p):
        return self.gen.net(self.m.site_pin_node[(self.key, p)])

    def source(self, pin):
        return self.m.trace_back(self.m.site_pin_node[(self.key, pin)])

    def same_source(self, a, b):
        (sa, da), (sb, db) = self.source(a), self.source(b)
        if sa == sb or (da[0] == "const" and db[0] == "const" and da[1] == db[1]):
            return True
        if da[0] == "port" and db[0] == "port":
            self.m.port_pairs.append((self.key, a, b, sa, sb))
            return True
        return False

    def const_zero(self, pins):
        return all(d[0] == "const" and d[1] == "1'b0" for _, d in (self.source(x) for x in pins))

    def port_writes(self):
        for port, we in (("A", [f"WEAL{i}" for i in range(4)] + [f"WEAU{i}" for i in range(4)]),
                         ("B", [f"WEBWEL{i}" for i in range(8)] + [f"WEBWEU{i}" for i in range(8)])):
            if self.const_zero(we):
                if self.params[f"WRITE_WIDTH_{port}"] != 0:
                    self.m.coverage[f"BRAM port {port} write enables tied 0: WRITE_WIDTH_{port} "
                                    f"{self.params[f'WRITE_WIDTH_{port}']} -> 0"] += 1
                self.params[f"WRITE_WIDTH_{port}"] = 0
            elif self.params[f"WRITE_WIDTH_{port}"] != self.params[f"READ_WIDTH_{port}"]:
                die(f"{self.key}: port {port} writes with WRITE_WIDTH {self.params[f'WRITE_WIDTH_{port}']} != READ_WIDTH "
                    f"{self.params[f'READ_WIDTH_{port}']} (not modelled)")

    def instantiate(self):
        if "inst" in self.memo:
            return self.memo["inst"]
        name = f"c_{self.id}"
        self.memo["inst"] = name
        self.port_writes()
        conns = []
        for port, (lo, hi) in self.PINS_LU.items():
            if not self.same_source(lo, hi):
                die(f"{self.key}: {lo} and {hi} have different sources")
            conns.append(f".{port}({self.pin(lo)})")
        for port, (w, lo, hi, nhi) in self.BUSES.items():
            bits = []
            for i in range(w):
                if hi and i < nhi and not self.same_source(lo.format(i), hi.format(i)):
                    die(f"{self.key}: {lo.format(i)} and {hi.format(i)} have different sources")
                bits.append(self.pin(lo.format(i)))
            conns.append(f".{port}({{{', '.join(reversed(bits))}}})")
        for port, w in self.OUTS.items():
            self.gen.wire(f"{name}_{port}", w)
            conns.append(f".{port}({name}_{port})")
        self.gen.cell_params("R2V_RAMB36E1", f"{name}_i", self.params, ", ".join(conns))
        return name

    def out(self, p):
        m = re.fullmatch(r"(DOADO|DOBDO|DOPADOP|DOPBDOP)(\d+)", p)
        if not m:
            die(f"{self.key}: output pin {p} has no model")
        return f"{self.instantiate()}_{m.group(1)}[{m.group(2)}]"


class Dsp:
    BUSES = {"A": 30, "B": 18, "C": 48, "D": 25, "ACIN": 30, "BCIN": 18, "PCIN": 48, "ALUMODE": 4, "INMODE": 5, "OPMODE": 7,
             "CARRYINSEL": 3}
    BITS = ["CARRYCASCIN", "CARRYIN", "CEAD", "CEALUMODE", "CEC", "CECARRYIN", "CECTRL", "CED", "CEINMODE", "CEM",
            "CEP", "CLK", "MULTSIGNIN", "RSTA", "RSTALLCARRYIN", "RSTALUMODE", "RSTB", "RSTC", "RSTCTRL", "RSTD",
            "RSTINMODE", "RSTM", "RSTP"]
    CE2 = {"CEA1": "CEA1", "CEA2": "CEA2", "CEB1": "CEB1", "CEB2": "CEB2"}
    OUTS = {"P": 48, "ACOUT": 30, "BCOUT": 18, "PCOUT": 48, "CARRYOUT": 4}
    REGS = ["ADREG", "ALUMODEREG", "CARRYINREG", "CARRYINSELREG", "CREG", "DREG", "INMODEREG", "MREG", "OPMODEREG", "PREG"]
    KNOWN = re.compile(r"AREG_[02]|BREG_[02]|A_INPUT|B_INPUT|USE_DPORT|USE_SIMD_FOUR12|USE_SIMD_FOUR12_TWO24|PATTERN|MASK|"
                       r"AUTORESET_PATDET_RESET|AUTORESET_PATDET_RESET_NOT_MATCH|SEL_MASK_C|SEL_MASK_ROUNDING_MODE[12]|"
                       r"SEL_PATTERN_C|ZAREG_2_ACASCREG_1|ZBREG_2_BCASCREG_1|Z(" + "|".join(REGS) + r")|"
                       r"ZIS_(ALUMODE|INMODE|OPMODE|CLK|CARRYIN)_INVERTED")

    def __init__(self, model, key, tile, feats):
        self.m = model
        self.key = key
        self.tile = tile
        self.f = feats
        self.id = sanitize(key)
        self.gen = None
        self.memo = {}
        for f in feats:
            if not self.KNOWN.fullmatch(f):
                die(f"DSP feature {tile}.DSP48.{key[-5:]}.{f} is not modelled")
            self.m.coverage["DSP " + f] += 1
        self.params = self.decode()

    def has(self, f):
        v = self.f.get(f)
        return v is True or (isinstance(v, set) and 0 in v)

    def decode(self):
        p = {}
        for r in ("A", "B"):
            reg = 0 if self.has(f"{r}REG_0") else 2 if self.has(f"{r}REG_2") else 1
            if self.has(f"{r}REG_0") and self.has(f"{r}REG_2"):
                die(f"{self.key}: {r}REG_0 and {r}REG_2 both set")
            p[f"{r}REG"] = reg
            p[f"{r}CASCREG"] = (1 if not self.has(f"Z{r}REG_2_{r}CASCREG_1") else 2) if reg == 2 else reg
            p[f"{r}_INPUT"] = '"CASCADE"' if self.has(f"{r}_INPUT") else '"DIRECT"'
        p["USE_DPORT"] = '"TRUE"' if self.has("USE_DPORT") else '"FALSE"'
        p["USE_SIMD"] = '"FOUR12"' if self.has("USE_SIMD_FOUR12") else '"TWO24"' if self.has("USE_SIMD_FOUR12_TWO24") else '"ONE48"'
        if self.has("USE_SIMD_FOUR12") and not self.has("USE_SIMD_FOUR12_TWO24"):
            die(f"{self.key}: USE_SIMD_FOUR12 without USE_SIMD_FOUR12_TWO24")
        p["PATTERN"] = f"48'h{bits_of(self.f.get('PATTERN'), 48):012x}"
        p["MASK"] = f"48'h{bits_of(self.f.get('MASK'), 48):012x}"
        p["AUTORESET_PATDET"] = '"RESET_NOT_MATCH"' if self.has("AUTORESET_PATDET_RESET_NOT_MATCH") else \
            '"RESET_MATCH"' if self.has("AUTORESET_PATDET_RESET") else '"NO_RESET"'
        p["SEL_MASK"] = '"C"' if self.has("SEL_MASK_C") else '"ROUNDING_MODE1"' if self.has("SEL_MASK_ROUNDING_MODE1") else \
            '"ROUNDING_MODE2"' if self.has("SEL_MASK_ROUNDING_MODE2") else '"MASK"'
        p["SEL_PATTERN"] = '"C"' if self.has("SEL_PATTERN_C") else '"PATTERN"'
        for r in self.REGS:
            p[r] = 0 if self.has(f"Z{r}") else 1
        for bus, w in (("ALUMODE", 4), ("INMODE", 5), ("OPMODE", 7)):
            p[f"IS_{bus}_INVERTED"] = f"{w}'b{bits_of(self.f.get(f'ZIS_{bus}_INVERTED'), w) ^ ((1 << w) - 1):0{w}b}"
        for b in ("CLK", "CARRYIN"):
            p[f"IS_{b}_INVERTED"] = f"1'b{int(not self.has(f'ZIS_{b}_INVERTED'))}"
        return p

    def pin(self, p):
        return self.gen.net(self.m.site_pin_node[(self.key, p)])

    def instantiate(self):
        if "inst" in self.memo:
            return self.memo["inst"]
        name = f"c_{self.id}"
        self.memo["inst"] = name
        inv = {}
        for bus, w in (("ALUMODE", 4), ("INMODE", 5), ("OPMODE", 7)):
            v = int(self.params[f"IS_{bus}_INVERTED"].split("'b")[1], 2)
            inv.update({f"{bus}{i}": (v >> i) & 1 for i in range(w)})
        for b in ("CLK", "CARRYIN"):
            inv[b] = int(self.params[f"IS_{b}_INVERTED"][-1])
        self.m.coverage["DSP inverted site pins folded into the netlist"] += sum(inv.values())

        def src(pin):
            return f"~{self.pin(pin)}" if inv.get(pin) else self.pin(pin)
        conns = []
        for bus, w in self.BUSES.items():
            conns.append(f".{bus}({{{', '.join(src(f'{bus}{i}') for i in reversed(range(w)))}}})")
        for b in self.BITS:
            conns.append(f".{b}({src(b)})")
        for port, pin in self.CE2.items():
            conns.append(f".{port}({self.pin(pin)})")
        for port, w in self.OUTS.items():
            self.gen.wire(f"{name}_{port}", w)
            conns.append(f".{port}({name}_{port})")
        for port in ("CARRYCASCOUT", "MULTSIGNOUT", "OVERFLOW", "UNDERFLOW", "PATTERNDETECT", "PATTERNBDETECT"):
            self.gen.wire(f"{name}_{port}")
            conns.append(f".{port}({name}_{port})")
        self.gen.cell_params("DSP48E1", f"{name}_i", {k: v for k, v in self.params.items() if not k.startswith("IS_")},
                             ", ".join(conns))
        return name

    def out(self, p):
        m = re.fullmatch(r"(P|ACOUT|BCOUT|PCOUT|CARRYOUT)(\d+)", p)
        if m:
            return f"{self.instantiate()}_{m.group(1)}[{m.group(2)}]"
        if p in ("CARRYCASCOUT", "MULTSIGNOUT"):
            return f"{self.instantiate()}_{p}"
        die(f"{self.key}: output pin {p} has no model")


class Gen:
    def __init__(self, model):
        self.m = model
        self.seen = set()
        self.q = collections.deque()
        self.assigns = []
        self.cells = []
        self.wires = []
        self.inputs = set()
        self.undriven = set()
        self.prim_count = collections.Counter()
        for s in model.sites.values():
            s.gen = self
            s.memo = {}

    def name(self, n):
        return self.m.g["names"][n]

    def net(self, n):
        if n not in self.seen:
            self.seen.add(n)
            self.q.append(n)
        return self.name(n)

    def wire(self, name, width=1):
        self.wires.append(f"wire [{width - 1}:0] {name};" if width > 1 else f"wire {name};")

    def cell(self, prim, inst, init, conns, outwire):
        if outwire:
            self.wire(outwire)
        self.prim_count[prim] += 1
        par = f" #(.INIT({init}))" if init else ""
        self.cells.append(f"{prim}{par} {inst} ({conns});")

    def cell_params(self, prim, inst, params, conns):
        self.prim_count[prim] += 1
        par = ", ".join(f".{k}({v})" for k, v in params.items())
        self.cells.append(f"{prim} #({par}) {inst} ({conns});")

    def materialize(self):
        for key in sorted(self.m.brams) + sorted(self.m.dsps):
            self.m.sites[key].instantiate()
        for key in sorted(self.m.slices):
            sl = self.m.slices[key]
            for f in sorted(sl.f):
                m = re.fullmatch(r"([A-D])(LUT\.INIT|FFMUX\..*|5FFMUX\..*|OUTMUX\..*)", f)
                if not m:
                    continue
                l, what = m.groups()
                if what == "LUT.INIT":
                    sl.lut(l, 6)
                elif what.startswith("FFMUX"):
                    sl.ff(l, False)
                elif what.startswith("5FFMUX") and (f"{l}5FF.ZINI" in sl.f or f"{l}5FF.ZRST" in sl.f):
                    sl.ff(l, True)
                elif what.startswith("OUTMUX"):
                    sl.out(f"{l}MUX")

    def run(self, roots):
        for n in roots:
            self.net(n)
        self.materialize()
        while self.q:
            n = self.q.popleft()
            d = self.m.resolve_driver(n)
            nm = self.name(n)
            if d[0] in ("pip", "always"):
                self.assigns.append(f"assign {nm} = {self.net(d[1])};")
            elif d[0] == "const":
                self.assigns.append(f"assign {nm} = {d[1]};")
            elif d[0] == "cell":
                self.assigns.append(f"assign {nm} = {self.m.sites[d[1]].out(d[2])};")
            elif d[0] == "port":
                self.inputs.add(n)
            else:
                self.undriven.add(n)
                self.assigns.append(f"assign {nm} = 1'bx;")


def build_netlist(model, modname):
    outputs = set()
    for n, ds in model.drv.items():
        if model.g["leaves"][n] and any(d[0] == "pip" for d in ds):
            outputs.add(n)
    for key, sl in model.slices.items():
        n = model.site_pin_node[(key, "COUT")]
        carry_feats = any(re.fullmatch(r"([A-D](OUT|FF)MUX\.(XOR|CY)|CARRY4\..*|PRECYINIT\.(C1|AX|CIN))", f) for f in sl.f)
        if model.g["leaves"][n] and carry_feats:
            outputs.add(n)
    gen = Gen(model)
    gen.run(sorted(outputs))
    names = model.g["names"]
    ins = sorted(gen.inputs, key=lambda i: names[i])
    outs = sorted(outputs, key=lambda i: names[i])
    ports = [f"input wire {names[i]}" for i in ins] + [f"output wire {names[i]}" for i in outs]
    internal = sorted((n for n in gen.seen if n not in gen.inputs and n not in outputs), key=lambda i: names[i])
    lines = [f"module {modname} (", "    " + ",\n    ".join(ports), ");"]
    lines += [f"    wire {names[i]};" for i in internal]
    lines += ["    " + w for w in gen.wires]
    lines += ["    " + a for a in gen.assigns]
    lines += ["    " + c for c in gen.cells]
    lines.append("endmodule")
    used_pips = set()
    for n in gen.seen:
        d = model.resolve_driver(n)
        if d[0] == "pip":
            used_pips.add(d[2])
    info = {
        "region": model.spec,
        "inputs": [names[i] for i in ins],
        "outputs": [names[i] for i in outs],
        "nodes": len(gen.seen),
        "primitives": dict(gen.prim_count),
        "undriven_internal_nodes": sorted(names[i] for i in gen.undriven),
        "fasm_pips_in_region": len(model.fasm_pips),
        "fasm_pips_in_cone": len(used_pips),
        "fasm_pips_not_reached": sorted(set(model.fasm_pips) - used_pips),
        "fasm_features_by_kind": dict(sorted(model.coverage.items())),
        "unknown_bits_outside_region": model.unknown_outside,
    }
    return "\n".join(lines) + "\n", info, gen, set(outs), set(ins)


def parse_shell(path):
    pat = re.compile(r'BEL\s*=\s*"X(\d+)Y(\d+)/SLICE_X(\d)Y0\.([A-D])(6LUT|FF)"\s*\*\)\s*(\w+)\s*(?:#\(.*?\))?\s*(\w+)\s*\(')
    anchors = []
    for line in Path(path).read_text().splitlines():
        m = pat.search(line)
        if not m:
            continue
        gx, gy, si, letter, bel, prim, inst = m.groups()
        mi = re.fullmatch(r"ain_(\w+)_(\d+)", inst)
        mq = re.fullmatch(r"q_(\w+)_(\d+)", inst)
        if mi and prim == "LUT1" and bel == "6LUT":
            anchors.append(("in", mi.group(1), int(mi.group(2)), int(gx), int(gy), int(si), letter))
        elif mq and bel == "FF":
            anchors.append(("out", mq.group(1), int(mq.group(2)), int(gx), int(gy), int(si), letter))
    return anchors


def anchor_slice(model, gx, gy, si):
    tiles = [n for n, t in model.grid.items() if t["grid_x"] == gx and t["grid_y"] == gy]
    if len(tiles) != 1:
        die(f"generic tile X{gx}Y{gy} maps to {tiles}")
    t = tiles[0]
    if t not in model.rtiles:
        die(f"anchor tile {t} (X{gx}Y{gy}) is outside the region")
    sites = [s for s in tile_type(model.grid[t]["type"])["sites"] if s["x_coord"] == si]
    if len(sites) != 1:
        die(f"{t}: no site with x_coord {si}")
    return model.slices[f"{t}.{sites[0]['type']}_X{si}"]


def map_anchors(model, anchors, outputs, inputs):
    names = model.g["names"]
    din, dout, clocks = {}, {}, set()
    for kind, port, bit, gx, gy, si, letter in anchors:
        sl = anchor_slice(model, gx, gy, si)
        if kind == "in":
            sup = lut_support(sl.init(letter), 6)
            a6 = model.trace_back(model.site_pin_node[(sl.key, f"{letter}6")])[1]
            if len(sup) != 1 and a6[0] == "const" and a6[1] == "1'b1":
                sup = lut_support(sl.init(letter) >> 32, 5)
            if len(sup) != 1:
                die(f"input anchor ain_{port}_{bit} at {sl.key}.{letter}6LUT: INIT depends on {len(sup)} pins")
            n = model.site_pin_node[(sl.key, f"{letter}{sup[0] + 1}")]
            src, d = model.trace_back(n)
            if d[0] != "port" or src not in inputs:
                die(f"input anchor ain_{port}_{bit}: pin traces to {d[0]} {names[src]}, not an input port")
            din[(port, bit)] = names[src]
        else:
            n = model.site_pin_node[(sl.key, f"{letter}Q")]
            hits = model.trace_fwd(n, outputs)
            if not hits:
                die(f"output anchor q_{port}_{bit} at {sl.key}.{letter}Q reaches no output port")
            dout[(port, bit)] = names[hits[0]]
            src, d = model.trace_back(model.site_pin_node[(sl.key, "CLK")])
            if d[0] != "port":
                die(f"output anchor q_{port}_{bit}: CLK traces to {d[0]} {names[src]}")
            clocks.add(names[src])
    if len(set(din.values())) != len(din):
        die("two input anchors share one input port")
    if not clocks:
        die("no clock port found")
    return din, dout, sorted(clocks)


def parse_registered(path):
    regs = set()
    for line in Path(path).read_text().splitlines():
        m = re.search(r"\bFDRE\s+r_(\w+)_(\d+)\s*\(", line)
        if m:
            regs.add(m.group(1))
    return regs


def map_partpins(model, pins, outputs, inputs):
    names = model.g["names"]
    din, dout, unused = {}, {}, []
    for p in pins:
        n = model.g["node_of"].get((p["alias_tile"], p["alias_wire"]))
        if n is None:
            die(f"partition pin {p['wire']} ({p['alias_tile']}/{p['alias_wire']}) is not a node of the region")
        key = (p["port"], p["bit"])
        if p["dir"] == "in":
            if n in inputs:
                din[key] = names[n]
            else:
                unused.append(key)
        else:
            if n not in outputs:
                die(f"partition pin {p['wire']} of {p['port']}[{p['bit']}] is not a region output")
            dout[key] = names[n]
    clocks = set()
    for key, sl in model.slices.items():
        if any(re.match(r"[A-D]5?FFMUX\.", f) for f in sl.f):
            src, d = model.trace_back(model.site_pin_node[(key, "CLK")])
            if d[0] != "port":
                die(f"{key}: FF clock traces to {d[0]} {names[src]}")
            clocks.add(names[src])
    if len(set(din.values())) != len(din):
        die("two input partition pins share one region input")
    return din, dout, sorted(clocks), unused


def vectors(ports, sweep=0):
    rnd = random.Random(CONFIG["seed"])
    widths = dict(ports["inputs"])
    vs = [{"valid": 1, "funct": 0, "rs1": i, "rs2": 0} for i in range(sweep)]
    ew, ef = CONFIG["edge_words"], CONFIG["edge_functs"]
    for a in ew:
        for b in ew:
            for f in ef[:4]:
                vs.append({"valid": 1, "funct": f, "rs1": a, "rs2": b})
    for f in ef:
        vs.append({"valid": 0, "funct": f, "rs1": 0x12345678, "rs2": 0x0F0F0F0F})
    for _ in range(CONFIG["n_random"]):
        v = {p: rnd.getrandbits(w) for p, w in widths.items()}
        if rnd.random() < 0.3:
            v["rs2"] = rnd.choice([v["rs1"], (~v["rs1"]) & 0xFFFFFFFF, (v["rs1"] + 1) & 0xFFFFFFFF, rnd.choice(ew)])
        vs.append(v)
    return vs


def rtl_path(rm):
    return CONFIG["rtl_dir"] / f"rm_core_{rm}.v"


def rtl_clocked(rm):
    return re.search(r"module\s+rm_core\s*\(\s*input\s+wire\s+clk\b", rtl_path(rm).read_text()) is not None


def write_tb(path, modname, ports, din, dout, clk, vs, unused_inputs, clocked=False):
    ins, outs = ports["inputs"], ports["outputs"]
    total = sum(w for _, w in ins)
    L = ["`timescale 1ns/1ps", "module r2v_tb;", "    reg clk = 1'b0;"]
    for p, w in ins:
        L.append(f"    reg [{w - 1}:0] {p};")
    for p, w in outs:
        L.append(f"    wire [{w - 1}:0] {p}_ref, {p}_dut;")
        L.append(f"    reg [{w - 1}:0] {p}_pre;")
    L.append(f"    reg [{total - 1}:0] vec [0:{len(vs) - 1}];")
    L.append("    rm_core u_ref (" + (".clk(clk), " if clocked else "") + ", ".join(f".{p}({p})" for p, _ in ins) + ", "
             + ", ".join(f".{p}({p}_ref)" for p, _ in outs) + ");")
    conns = [f".{c}(clk)" for c in clk]
    for (p, b), n in sorted(din.items()):
        conns.append(f".{n}({p}[{b}])")
    for (p, b), n in sorted(dout.items()):
        conns.append(f".{n}({p}_dut[{b}])")
    for n in unused_inputs:
        conns.append(f".{n}(1'bx)")
    L.append(f"    {modname} dut (\n        " + ",\n        ".join(conns) + ");")
    L.append("    integer i, npass, nfail;")
    L.append("    initial begin")
    for i, v in enumerate(vs):
        word = 0
        for p, w in ins:
            word = (word << w) | v[p]
        L.append(f"        vec[{i}] = {total}'h{word:x};")
    cat_ref = "{" + ", ".join(f"{p}_ref" for p, _ in outs) + "}"
    cat_dut = "{" + ", ".join(f"{p}_dut" for p, _ in outs) + "}"
    warm = CONFIG["clocked_warmup"] if clocked else 0
    if clocked:
        cat_cmp = "{" + ", ".join(f"{p}_pre" for p, _ in outs) + "}"
        step = ["            #4 " + "; ".join(f"{p}_pre = {p}_ref" for p, _ in outs) + ";",
                "            #1 clk = 1'b1;"]
    else:
        cat_cmp = cat_ref
        step = ["            #5 clk = 1'b1;"]
    shown = ", ".join(f"{p}_dut, {p}_pre" if clocked else f"{p}_dut, {p}_ref" for p, _ in outs)
    L += [
        "        npass = 0; nfail = 0;",
        f"        for (i = 0; i < {len(vs)}; i = i + 1) begin",
        "            {" + ", ".join(p for p, _ in ins) + "} = vec[i];",
    ] + step + [
        "            #1;",
        f"            if (i < {warm}) ;",
        f"            else if ({cat_dut} === {cat_cmp}) npass = npass + 1;",
        "            else begin",
        "                nfail = nfail + 1;",
        "                if (nfail <= 5) $display(\"MISMATCH i=%0d "
        + " ".join(f"{p}=%h" for p, _ in ins) + " | " + " ".join(f"{p}: dut=%h ref=%h" for p, _ in outs) + "\", i, "
        + ", ".join(p for p, _ in ins) + ", " + shown + ");",
        "            end",
        "            #4 clk = 1'b0;",
        "        end",
        f"        $display(\"RESULT pass=%0d fail=%0d warmup=%0d\", npass, nfail, {warm});",
        "        $finish;",
        "    end",
        "endmodule",
    ]
    Path(path).write_text("\n".join(L) + "\n")


def write_formal(path, modname, ports, din, dout, clk, unused_inputs, clocked=False, comb=()):
    ins, outs = ports["inputs"], ports["outputs"]
    owidth = sum(w for _, w in outs)
    nfree = max(len(unused_inputs), 1)
    conns = [f".{c}(clk)" for c in clk]
    conns += [f".{n}({p}[{b}])" for (p, b), n in sorted(din.items())]
    conns += [f".{n}({p}_dut[{b}])" for (p, b), n in sorted(dout.items())]
    conns += [f".{n}(free[{i}])" for i, n in enumerate(unused_inputs)]
    cat_ref = "{" + ", ".join(f"{p}_ref" for p, _ in outs) + "}"
    cat_dut = "{" + ", ".join(f"{p}_dut" for p, _ in outs) + "}"
    L = ["module r2v_formal (input wire clk, "
         + ", ".join(f"input wire [{w - 1}:0] {p}" for p, w in ins)
         + f", input wire [{nfree - 1}:0] free, output wire ok);"]
    for p, w in outs:
        L.append(f"    wire [{w - 1}:0] {p}_ref, {p}_dut;")
    L.append("    rm_core u_ref (" + (".clk(clk), " if clocked else "") + ", ".join(f".{p}({p})" for p, _ in ins) + ", "
             + ", ".join(f".{p}({p}_ref)" for p, _ in outs) + ");")
    L.append(f"    {modname} dut (\n        " + ",\n        ".join(conns) + ");")
    warm = CONFIG["clocked_warmup"] if clocked else 1
    if comb:
        terms = []
        for p, w in outs:
            if p in comb:
                terms.append(f"({p}_dut == {p}_ref)")
                continue
            L.append(f"    reg [{w - 1}:0] q_{p} = {w}'d0;")
            L.append(f"    always @(posedge clk) q_{p} <= {p}_ref;")
            terms.append(f"({p}_dut == q_{p})")
        L += ["    reg [3:0] cycles = 4'd0;",
              f"    always @(posedge clk) if (cycles < {warm}) cycles <= cycles + 4'd1;",
              f"    assign ok = (cycles < {warm}) || ({' && '.join(terms)});",
              "endmodule"]
        Path(path).write_text("\n".join(L) + "\n")
        return
    L += [f"    reg [{owidth - 1}:0] q_ref = {owidth}'d0;",
          "    reg [3:0] cycles = 4'd0;",
          f"    always @(posedge clk) begin q_ref <= {cat_ref}; if (cycles < {warm}) cycles <= cycles + 4'd1; end",
          f"    assign ok = (cycles < {warm}) || ({cat_dut} == q_ref);",
          "endmodule"]
    Path(path).write_text("\n".join(L) + "\n")


def run_formal(workdir, formal, netlist, rm):
    rtl = rtl_path(rm)
    script = (f"read_verilog {CONFIG['cells_sim']}; read_verilog {CONFIG['bram_model']} {netlist} {rtl} {formal}; "
              "hierarchy -top r2v_formal; proc; flatten; opt_clean; "
              "sat -tempinduct -prove ok 1 -set-init-zero")
    log = workdir / "formal.log"
    r = subprocess.run([f"{CONFIG['tools']}/yosys", "-q", "-l", str(log), "-p", script],
                       capture_output=True, text=True)
    text = log.read_text() if log.exists() else r.stdout + r.stderr
    if r.returncode == 0 and "Induction step proven: SUCCESS!" in text:
        return "PROVED"
    if "FAIL" in text or "failed" in text:
        return "DISPROVED"
    die(f"yosys formal run inconclusive ({log})")


def corrupt_fasm(model, src, dst, anchors_bels, gen):
    cands = []
    for key, sl in sorted(model.slices.items()):
        for letter in LETTERS:
            if (key, letter) in anchors_bels or ("lut", letter, 6) not in sl.memo:
                continue
            init = sl.init(letter)
            sup = lut_support(init, 6)
            if sup:
                cands.append((key, letter, init, sup))
    if not cands:
        die("no non-anchor LUT in the cone to corrupt")
    key, letter, init, sup = cands[0]
    sl = model.slices[key]
    idx = 0
    for i in range(6):
        if i in sup:
            continue
        n = model.site_pin_node[(key, f"{letter}{i + 1}")]
        _, d = model.trace_back(n)
        if d[0] == "const" and d[1] == "1'b1":
            idx |= 1 << i
    tile, site = key.split(".", 1)
    feat = f"{site}.{letter}LUT.INIT"
    new = init ^ (1 << idx)
    out = []
    replaced = False
    for raw in Path(src).read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith(f"{tile}.{feat}[") or line == f"{tile}.{feat}":
            if not replaced:
                out.append(f"{tile}.{feat}[63:0] = 64'b{new:064b}")
                replaced = True
            continue
        out.append(raw)
    if not replaced:
        out.append(f"{tile}.{feat}[63:0] = 64'b{new:064b}")
    Path(dst).write_text("\n".join(out) + "\n")
    return f"{tile}.{feat} bit {idx} flipped (0x{init:016x} -> 0x{new:016x}, support pins {[f'{letter}{i + 1}' for i in sup]})"


def run_sim(workdir, tb, netlist, rm):
    env_bin = str(CONFIG["tools"])
    rtl = rtl_path(rm)
    if not rtl.exists():
        die(f"no RTL {rtl}")
    vvp = workdir / "sim.vvp"
    cmd = [f"{env_bin}/iverilog", "-g2012", "-o", str(vvp), "-s", "r2v_tb", str(tb), str(netlist), str(rtl),
           str(CONFIG["cells_sim"]), str(CONFIG["bram_model"])]
    r = subprocess.run(cmd, capture_output=True, text=True)
    (workdir / "iverilog.log").write_text(r.stdout + r.stderr)
    if r.returncode:
        die(f"iverilog failed ({workdir / 'iverilog.log'})")
    r = subprocess.run([f"{env_bin}/vvp", "-n", str(vvp)], capture_output=True, text=True)
    (workdir / "vvp.log").write_text(r.stdout + r.stderr)
    m = re.search(r"RESULT pass=(\d+) fail=(\d+) warmup=(\d+)", r.stdout)
    if "R2V-UNSUPPORTED" in r.stdout or not m:
        die(f"simulation did not finish or hit an unsupported primitive configuration ({workdir / 'vvp.log'})")
    mism = [l for l in r.stdout.splitlines() if l.startswith("MISMATCH")]
    return int(m.group(1)), int(m.group(2)), mism, int(m.group(3))


def resolve_input(path):
    p = Path(path)
    if p.suffix == ".bit":
        return bit_to_fasm(p)
    return p


def cmd_netlist(a):
    grid = region.load_grid()
    model = Model(grid, a.region, resolve_input(a.input))
    modname = a.module or f"region2v_{sanitize(a.tag or Path(a.input).stem)}"
    text, info, *_ = build_netlist(model, modname)
    out = Path(a.out)
    out.write_text(text)
    out.with_suffix(".json").write_text(json.dumps(info, indent=1) + "\n")
    print(f"wrote {out}: {len(info['inputs'])} inputs, {len(info['outputs'])} outputs, primitives {info['primitives']}")


def cmd_check(a):
    grid = region.load_grid()
    ports = json.loads(CONFIG["ports_json"].read_text())
    tag = sanitize(a.tag)
    work = cache_dir("check", tag + ("_corrupt" if a.corrupt else ""))
    fasm = resolve_input(a.input)
    model = Model(grid, a.region, fasm)
    pins = json.loads(Path(a.partpins).read_text())["pins"] if getattr(a, "partpins", None) else None
    anchors = [] if pins else parse_shell(a.shell)
    comb = set()
    if pins:
        regs = parse_registered(a.shell)
        comb = {p for p, _ in ports["outputs"] if p not in regs}
    anchor_bels = {(anchor_slice(model, gx, gy, si).key, letter) for kind, _, _, gx, gy, si, letter in anchors
                   if kind == "in"}
    for kind, _, _, gx, gy, si, letter in anchors:
        if kind == "out":
            anchor_bels.add((anchor_slice(model, gx, gy, si).key, letter))
    note = ""
    if a.corrupt:
        _, _, gen, _, _ = build_netlist(model, "tmp")
        bad = work / "corrupt.fasm"
        note = corrupt_fasm(model, fasm, bad, anchor_bels, gen)
        model = Model(grid, a.region, bad)
    modname = f"region2v_{tag}"
    text, info, gen, outs, ins = build_netlist(model, modname)
    netlist = work / "region.v"
    netlist.write_text(text)
    pins_unused = []
    if pins:
        din, dout, clk, pins_unused = map_partpins(model, pins, outs, ins)
    else:
        din, dout, clk = map_anchors(model, anchors, outs, ins)
    for key, a_pin, b_pin, sa, sb in model.port_pairs:
        na, nb = model.g["names"][sa], model.g["names"][sb]
        if not (na in clk and nb in clk):
            die(f"{key}: {a_pin} and {b_pin} come from different region inputs {na} and {nb}, not both clock ports")
    want_in = {(p, b) for p, w in ports["inputs"] for b in range(w)}
    want_out = {(p, b) for p, w in ports["outputs"] for b in range(w)}
    have_in = set(din) | set(pins_unused)
    if have_in != want_in or set(dout) != want_out:
        die(f"{'partition pins' if pins else 'anchors'} do not cover ports.json: missing in "
            f"{sorted(want_in - have_in)[:5]}, out {sorted(want_out - set(dout))[:5]}")
    names = model.g["names"]
    used = set(din.values()) | set(clk)
    unused = sorted(names[i] for i in ins if names[i] not in used)
    info.update({"fasm": str(fasm), "rm": a.rm, "clock_ports": clk, "anchor_inputs": len(din), "anchor_outputs": len(dout),
                 "unused_input_ports_driven_x": unused, "corruption": note})
    if pins:
        info.update({"partition_pins": a.partpins, "partpin_inputs_used": len(din),
                     "partpin_inputs_unused_by_this_module": [f"{p}[{b}]" for p, b in sorted(pins_unused)],
                     "combinational_outputs": sorted(comb)})
    (work / "region.json").write_text(json.dumps(info, indent=1) + "\n")
    vs = vectors(ports, a.sweep)
    tb = work / "tb.v"
    clocked = rtl_clocked(a.rm)
    info["rtl_clocked"] = clocked
    (work / "region.json").write_text(json.dumps(info, indent=1) + "\n")
    write_tb(tb, modname, ports, din, dout, clk, vs, unused, clocked)
    npass, nfail, mism, warm = run_sim(work, tb, netlist, a.rm)
    formal = "not run"
    if a.formal:
        fv = work / "formal.v"
        write_formal(fv, modname, ports, din, dout, clk, unused, clocked, comb)
        formal = run_formal(work, fv, netlist, a.rm)
    prims = " ".join(f"{k}={v}" for k, v in sorted(info["primitives"].items()))
    for key, b in sorted(model.brams.items()):
        prims += f" | {key} READ_WIDTH_A={b.params['READ_WIDTH_A']} DOA_REG={b.params['DOA_REG']}"
    for key, d in sorted(model.dsps.items()):
        prims += f" | {key} AREG={d.params['AREG']} BREG={d.params['BREG']} MREG={d.params['MREG']} PREG={d.params['PREG']}"
    ok = nfail == 0 and npass == len(vs) - warm and formal in ("PROVED", "not run")
    status = "PASS" if ok else "FAIL"
    print(f"{status} {a.tag} rm={a.rm}: sim pass={npass} fail={nfail} of {len(vs)} vectors"
          + (f" ({warm} warm-up cycles not compared)" if warm else "") + f" | formal {formal} "
          f"| ports in={len(ins)} out={len(outs)} "
          f"(unused inputs={len(unused)}) | {prims} | undriven={len(info['undriven_internal_nodes'])} "
          f"| pips in cone {info['fasm_pips_in_cone']}/{info['fasm_pips_in_region']}")
    if note:
        print(f"   corruption: {note}")
    for l in mism[:3]:
        print("   " + l)
    return status


def synth_bram_params(path):
    cells = []
    for m in json.loads(Path(path).read_text())["modules"].values():
        for name, c in m.get("cells", {}).items():
            if c["type"] == "RAMB36E1":
                cells.append((name, c["parameters"]))
    if len(cells) != 1:
        die(f"{path}: expected one RAMB36E1 cell, found {len(cells)}")
    return cells[0]


def compare_bits(want, have, width):
    if len(want) != width:
        die(f"synthesis value has {len(want)} bits, expected {width}")
    known = bad = 0
    for i, ch in enumerate(reversed(want)):
        if ch not in "01":
            continue
        known += 1
        bad += int(ch) != ((have >> i) & 1)
    return known, bad


def cmd_bram(a):
    grid = region.load_grid()
    model = Model(grid, a.region, resolve_input(a.input))
    if len(model.brams) != 1:
        die(f"expected one RAMB36 in the region, found {sorted(model.brams)}")
    key, b = next(iter(model.brams.items()))
    cell, params = synth_bram_params(a.synth_json)
    known = bad = 0
    bad_params = []
    for kind, n, words in (("INIT", 128, b.init_words), ("INITP", 16, b.initp_words)):
        for i in range(n):
            k, x = compare_bits(params.get(f"{kind}_{i:02X}", "0" * 256), words[i], 256)
            known += k
            bad += x
            if x:
                bad_params.append(f"{kind}_{i:02X}")
    work = cache_dir("bram", sanitize(a.tag))
    rep = {"tag": a.tag, "bram": key, "synth_json": a.synth_json, "synth_cell": cell, "read_width_a": b.params["READ_WIDTH_A"],
           "init_bits_compared": known, "init_bits_differ": bad, "params_differ": bad_params}
    (work / "bram.json").write_text(json.dumps(rep, indent=1) + "\n")
    ok = bad == 0 and known > 0
    print(f"{'PASS' if ok else 'FAIL'} {a.tag}: {key} INIT/INITP decoded from the bitstream vs {cell} in {Path(a.synth_json).name}: "
          f"{known - bad}/{known} defined bits equal ({bad} differ{', in ' + ' '.join(bad_params[:4]) if bad_params else ''})")
    return "PASS" if ok else "FAIL"


def main():
    ap = argparse.ArgumentParser(description="Region bits -> Verilog netlist (prjxray-db only), and an RTL equivalence sim")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("netlist", help="emit the region netlist")
    n.add_argument("input", help=".fasm or .bit (a full bitstream)")
    n.add_argument("region", help="e.g. SLICE_X12Y100:SLICE_X15Y149")
    n.add_argument("-o", "--out", required=True)
    n.add_argument("--tag")
    n.add_argument("--module")
    c = sub.add_parser("check", help="netlist + anchors from the shell + simulation against rm_core_<rm>.v")
    c.add_argument("input")
    c.add_argument("region")
    c.add_argument("--shell", required=True)
    c.add_argument("--partpins", help="partpins.py's .json: find the module's ports at these partition pins instead "
                                      "of through the shell's anchors (the shell then only names registered outputs)")
    c.add_argument("--rm", required=True)
    c.add_argument("--tag", required=True)
    c.add_argument("--corrupt", action="store_true", help="flip one INIT bit of a non-anchor LUT in a FASM copy")
    c.add_argument("--formal", action="store_true", help="also prove equivalence with yosys sat -tempinduct")
    c.add_argument("--sweep", type=int, default=0,
                   help="first apply funct=0, rs1=0..N-1 (an exhaustive read of an N-entry table), then the usual vectors")
    bm = sub.add_parser("bram", help="decode the region's RAMB36 INIT and compare it with the RTL memory")
    bm.add_argument("input")
    bm.add_argument("region")
    bm.add_argument("--synth-json", required=True, help="the RM's yosys JSON (rm_<rm>_synth.json) with one RAMB36E1")
    bm.add_argument("--tag", required=True)
    a = ap.parse_args()
    try:
        if a.cmd == "netlist":
            cmd_netlist(a)
        elif a.cmd == "bram":
            sys.exit(0 if cmd_bram(a) == "PASS" else 1)
        else:
            st = cmd_check(a)
            sys.exit(0 if st == "PASS" else 1)
    except R2VError as e:
        print(f"ERROR {getattr(a, 'tag', '') or ''}: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
