import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
from build_openxc7 import tool

ROOT = qor_bench.ROOT

CONFIG = {
    "out": ROOT / "build" / "xroute",
    "vivado_out": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "vivado_tag": "xroute",
    "dry_run": True,
    "npwait": ROOT / "ofx" / "npwait.sh",
    "tilegrid": ROOT / "toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7/xc7a50t/tilegrid.json",
    "designs": {
        "blinky": ("cal_static", 1),
        "rv_soc": ("cal_static", 1),
        "bram": ("cal_static", 1),
        "rv_mul": ("dspq_cal", 1),
        "rv_big": ("dspq_cal", 1),
        "fir": ("dspq_cal", 1),
        "eth": ("pl_base", 1, 10, "digilent_arty", "designs/eth/arty_eth/digilent_arty.xdc"),
    },
    "base_override": {
        "eth": {"bin": ROOT / "build/nextpnr-build/qorperm/nextpnr-himbaechel",
                "chipdb": ROOT / "build/chipdb-cal/on/chipdb-xc7a50t.bin"},
    },
    "period": 5,
    "timers": {
        "cal": {},
        "perm_off": {"bin": ROOT / "build/nextpnr-build/qorperm/nextpnr-himbaechel"},
        "perm": {"bin": ROOT / "build/nextpnr-build/qorperm/nextpnr-himbaechel", "args": ["-o", "lut-perm-timing"]},
        "rcal": {"bin": ROOT / "build/nextpnr-build/qorperm/nextpnr-himbaechel", "args": ["-o", "lut-perm-timing"],
                 "chipdb": ROOT / "build/chipdb-rcal/on/chipdb-xc7a50t.bin"},
    },
    "export_timers": {"cal", "rcal"},
    "skip_types": {"PAD", "PSEUDO_VCC", "PSEUDO_GND"},
    "io_types": {"IOB33_INBUF_EN", "IOB33_OUTBUF", "IOB33M_INBUF_EN", "IOB33M_OUTBUF", "IOB33S_INBUF_EN", "IOB33S_OUTBUF"},
    "carry_re": r"^(.*)\$split\$muxcy(\d+)\$PACKED_CARRY4\$$",
    "intcell_suffixes": ("$intcell$IBUF", "$intcell$OBUF"),
    "lut_types": {"LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6"},
    "lutram_macros": {"RAM32M": {"6": "RAM{l}_D1", "5": "RAM{l}"}},
    "bufg_ports": {"BUFG": {"I0": "I", "O": "O"}},
    "new_prefix": "xr_",
    "lutram_types": {"RAMD32", "RAMS32", "RAMD64E", "RAMS64E"},
    "lutram_mode": "macro",
    "param_map": {"RAMD32": {"INIT": "INIT", "IS_WCLK_INVERTED": "IS_CLK_INVERTED"}},
}


def dinfo(design):
    v = CONFIG["designs"][design]
    if len(v) == 2:
        return {"variant": v[0], "seed": v[1], "period": CONFIG["period"], "top": qor_bench.CONFIG["designs"][design]["top"],
                "xdc": qor_bench.CONFIG["out"] / "src" / f"{design}_{qor_bench.ptag(CONFIG['period'])}" / "constraints.xdc"}
    return {"variant": v[0], "seed": v[1], "period": v[2], "top": v[3], "xdc": ROOT / v[4]}


def name_of(design, chipdb="cal"):
    i = dinfo(design)
    tag = "" if chipdb == "cal" else f"_{chipdb}"
    return f"{design}_{qor_bench.ptag(i['period'])}_{i['variant']}_s{i['seed']}{tag}"


def src_run(design):
    i = dinfo(design)
    return qor_bench.CONFIG["out"] / "oxc7" / i["variant"] / f"{design}_{qor_bench.ptag(i['period'])}" / f"s{i['seed']}"


def say(dry, msg):
    print(f"[{'dry' if dry else 'run'}] {msg}")


def rerun_nextpnr(design, chipdb, dry):
    tm = dict(CONFIG["base_override"].get(design, {}))
    tm.update(CONFIG["timers"][chipdb])
    tm["chipdb"] = CONFIG["timers"][chipdb].get("chipdb") or CONFIG["base_override"].get(design, {}).get("chipdb")
    run = src_run(design)
    st = json.loads((run / "status.json").read_text())
    out = CONFIG["out"] / "npr" / name_of(design, chipdb)
    if (out / "done.json").exists():
        return out
    cmd = list(st["cmd"])
    rep = {"--write": str(out / "routed.json"), "--report": str(out / "report.json")}
    new = [cmd[0]]
    i = 1
    while i < len(cmd):
        a = cmd[i]
        if a in rep:
            new += [a, rep[a]]
            i += 2
            continue
        if a == "-o" and cmd[i + 1].startswith("fasm="):
            new += ["-o", f"fasm={out / 'npr.fasm'}"]
            i += 2
            continue
        if a == "--chipdb" and tm.get("chipdb"):
            new += [a, str(tm["chipdb"])]
            i += 2
            continue
        new.append(a)
        i += 1
    if tm.get("bin"):
        new[0] = str(tm["bin"])
    new += list(tm.get("args", [])) + ["--sdf", str(out / "npr.sdf")]
    say(dry, f"nextpnr --sdf {out.relative_to(ROOT)}")
    if dry:
        return out
    out.mkdir(parents=True, exist_ok=True)
    env = dict(__import__("os").environ, OFX_NEXTPNR_BIN=new[0])
    with open(out / "nextpnr.log", "w") as lf:
        rc = subprocess.run([str(CONFIG["npwait"])] + new[1:], stdout=lf, stderr=subprocess.STDOUT, env=env).returncode
    if rc:
        raise SystemExit(f"nextpnr failed rc={rc}: {out / 'nextpnr.log'}")
    top = dinfo(design)["top"]
    same = fasm_body(out / "npr.fasm") == fasm_body(run / f"{top}.fasm")
    (out / "done.json").write_text(json.dumps({"cmd": new, "fasm_identical_to_source": same, "source": str(run),
                                               "chipdb": chipdb}, indent=1) + "\n")
    return out


def fasm_body(path):
    return sorted(ln for ln in Path(path).read_text().splitlines() if not ln.startswith("#"))


def mod_of(j):
    return j["modules"][next(iter(j["modules"]))]


class Netlist:
    def __init__(self, syn_json, routed_json, top):
        self.y = json.loads(Path(syn_json).read_text())
        self.ym = self.y["modules"][top]
        self.n = mod_of(json.loads(Path(routed_json).read_text()))
        self.ycells = self.ym["cells"]
        self.ncells = self.n["cells"]
        self.nbit_name = {}
        for nm, net in self.n["netnames"].items():
            for b in net["bits"]:
                self.nbit_name.setdefault(b, nm)
        self.ybit_by_name = {}
        for nm, net in self.ym["netnames"].items():
            bits = net["bits"]
            off = net.get("offset", 0)
            if len(bits) == 1:
                self.ybit_by_name.setdefault(nm, bits[0])
            for i, b in enumerate(bits):
                self.ybit_by_name.setdefault(f"{nm}[{i + off}]", b)
        self.next_bit = 1 + max([b for c in self.ycells.values() for v in c["connections"].values() for b in v
                                 if isinstance(b, int)] + [b for v in self.ym["netnames"].values() for b in v["bits"]
                                                           if isinstance(b, int)])
        self.first_new = self.next_bit
        self.map_cells()
        self.find_drivers()

    def orig(self, nname, c):
        if nname in self.ycells:
            return nname, "cell"
        m = re.match(CONFIG["carry_re"], nname)
        if c["type"] == "CARRY4" and m and m.group(1) in self.ycells:
            return None, "new"
        for s in CONFIG["intcell_suffixes"]:
            if nname.endswith(s) and nname[:-len(s)] in self.ycells:
                return nname[:-len(s)], "cell"
        if "/" in nname and nname.rsplit("/", 1)[0] in self.ycells:
            if CONFIG["lutram_mode"] == "prims" and self.ycells[nname.rsplit("/", 1)[0]]["type"] in CONFIG["lutram_macros"]:
                return None, "new"
            return nname.rsplit("/", 1)[0], "macro"
        return None, "new"

    def map_cells(self):
        self.split_carry = {m.group(1) for n, c in self.ncells.items() if c["type"] == "CARRY4"
                            for m in [re.match(CONFIG["carry_re"], n)] if m and m.group(1) in self.ycells}
        self.split_carry |= {n.rsplit("/", 1)[0] for n in self.ncells if "/" in n and n.rsplit("/", 1)[0] in self.ycells
                             and CONFIG["lutram_mode"] == "prims"
                             and self.ycells[n.rsplit("/", 1)[0]]["type"] in CONFIG["lutram_macros"]}
        self.ydriver = {}
        for yc, c in self.ycells.items():
            for p, bits in c["connections"].items():
                if c.get("port_directions", {}).get(p) == "output":
                    for b in bits:
                        self.ydriver[b] = yc
        self.cmap = {}
        self.vname = {}
        k = 0
        for nname, c in self.ncells.items():
            if c["type"] in CONFIG["skip_types"]:
                self.cmap[nname] = (None, "skip")
                continue
            yc, kind = self.orig(nname, c)
            if kind == "new" and c["type"] in CONFIG["io_types"]:
                self.cmap[nname] = (None, "skip")
                self.io_kept = getattr(self, "io_kept", 0) + 1
                continue
            if kind == "new":
                yc = f"{CONFIG['new_prefix']}{k}"
                k += 1
            elif kind == "cell" and c["attributes"].get("X_ORIG_TYPE") in CONFIG["lut_types"] and                     self.ycells[yc]["type"] != c["attributes"]["X_ORIG_TYPE"]:
                kind = "retyped"
            self.cmap[nname] = (yc, kind)
            self.vname[nname] = yc

    def oport(self, nname, port):
        c = self.ncells[nname]
        yc, kind = self.cmap[nname]
        if kind == "cell" and self.ycells[yc]["type"] in CONFIG["bufg_ports"]:
            return CONFIG["bufg_ports"][self.ycells[yc]["type"]].get(port)
        v = c["attributes"].get(f"X_ORIG_PORT_{port}")
        if v is None:
            return None
        return v.split()[0]

    @staticmethod
    def split_port(op):
        m = re.match(r"^(.*)\[(\d+)\]$", op)
        return (m.group(1), int(m.group(2))) if m else (op, 0)

    def ybit(self, yc, op):
        base, i = self.split_port(op)
        conn = self.ycells[yc]["connections"].get(base)
        if conn is None or i >= len(conn):
            return None
        return conn[i]

    def find_drivers(self):
        self.driver = {}
        self.users = defaultdict(list)
        for nname, c in self.ncells.items():
            for p, bits in c["connections"].items():
                if not bits:
                    continue
                if c["port_directions"].get(p) == "output":
                    self.driver[bits[0]] = (nname, p)
                else:
                    self.users[bits[0]].append((nname, p))
        self.canon = {}
        self.stats = Counter()
        for b in set(self.driver) | set(self.users):
            self.canon[b] = self.canon_of(b)

    def canon_of(self, b):
        d = self.driver.get(b)
        if d is None:
            self.stats["undriven"] += 1
            return self.ybit_by_name.get(self.nbit_name.get(b), "x")
        nname, p = d
        t = self.ncells[nname]["type"]
        if t == "PSEUDO_GND":
            return "0"
        if t == "PSEUDO_VCC":
            return "1"
        yc, kind = self.cmap[nname]
        if kind in ("cell", "retyped"):
            op = self.oport(nname, p)
            yb = self.ybit(yc, op) if op else None
            if yb is not None:
                return yb
        if kind == "macro":
            yb = self.ybit_by_name.get(self.nbit_name.get(b))
            if yb is not None:
                return yb
            self.stats["macro_out_unnamed"] += 1
        if kind == "new":
            yb = self.ybit_by_name.get(self.nbit_name.get(b))
            if yb is not None and self.ydriver.get(yb) in self.split_carry:
                self.stats["carry_out_named"] += 1
                return yb
            nb = self.next_bit
            self.next_bit += 1
            return nb
        if kind == "skip":
            yb = self.ybit_by_name.get(self.nbit_name.get(b))
            if yb is not None:
                return yb
        self.stats["driver_unmapped"] += 1
        nb = self.next_bit
        self.next_bit += 1
        return nb

    def rewire(self):
        changes = []
        for nname, c in self.ncells.items():
            yc, kind = self.cmap[nname]
            if kind != "cell":
                continue
            for p, bits in c["connections"].items():
                if not bits or c["port_directions"].get(p) == "output":
                    continue
                op = self.oport(nname, p)
                if not op:
                    self.stats["in_port_unmapped"] += 1
                    continue
                yb = self.ybit(yc, op)
                want = self.canon[bits[0]]
                if (yb in ("0", "1") or yb is None) and want in ("0", "1"):
                    self.stats["pin_const_kept"] += 1
                    continue
                if yb == want:
                    self.stats["pin_same"] += 1
                    continue
                kind2 = "to_new" if isinstance(want, int) and want >= self.first_new else "to_existing"
                self.stats[f"pin_rewire_{kind2}"] += 1
                changes.append((yc, op, yb, want, kind2))
        return changes

    def build(self):
        changes = self.rewire()
        cells = {k: v for k, v in json.loads(json.dumps(self.ycells)).items() if k not in self.split_carry}
        for yc, op, old, want, _ in changes:
            base, i = self.split_port(op)
            conn = cells[yc]["connections"].setdefault(base, [])
            if i >= len(conn):
                self.stats["port_added"] += 1
                conn.extend(["x"] * (i + 1 - len(conn)))
            cells[yc]["connections"][base][i] = want
        for nname, c in self.ncells.items():
            yc, kind = self.cmap[nname]
            if kind not in ("new", "retyped"):
                continue
            t = c["attributes"].get("X_ORIG_TYPE")
            conns, dirs = {}, {}
            for p, bits in c["connections"].items():
                op = self.oport(nname, p)
                if not op or not bits:
                    continue
                conns[op] = [self.canon[bits[0]]]
                dirs[op] = c["port_directions"][p]
            params = {}
            if t in CONFIG["lut_types"]:
                k = int(t[3:])
                init = c["parameters"].get("INIT", "0")
                params["INIT"] = init[-(1 << k):].rjust(1 << k, "0")
            else:
                pm_ = CONFIG["param_map"].get(t)
                params = dict(c["parameters"]) if pm_ is None else                     {pm_[k]: v for k, v in c["parameters"].items() if k in pm_}
            cells[yc] = {"hide_name": 0, "type": t, "parameters": params, "attributes": {}, "port_directions": dirs,
                         "connections": conns}
            self.stats[f"{kind}_{t}"] += 1
        mod = dict(self.ym)
        mod["cells"] = cells
        return mod, changes

    def vpin(self, nname, p):
        yc, kind = self.cmap[nname]
        if kind not in ("cell", "new", "retyped"):
            return None
        op = self.oport(nname, p)
        return f"{yc}/{op}" if op else None


def lock_pins(c):
    pairs = []
    for k, v in c["attributes"].items():
        m = re.match(r"^X_ORIG_PORT_(A[1-6])$", k)
        if m and re.match(r"^I[0-5]$", v):
            pairs.append(f"{v}:{m.group(1)}")
    return sorted(pairs)


def tile_names():
    tg = json.loads(CONFIG["tilegrid"].read_text())
    return {(v["grid_x"], v["grid_y"]): k for k, v in tg.items()}


def net_pips(routing, tiles):
    t = routing.split(";")
    pips = []
    for i in range(0, len(t) - 2, 3):
        p = t[i + 1]
        if not p:
            continue
        xy, dst, src = p.split("/")
        if "." in dst or "." in src:
            continue
        x, y = map(int, re.match(r"X(\d+)Y(\d+)", xy).groups())
        pips.append(f"{tiles[(x, y)]}/{src}/{dst}")
    return pips


def export(design, npr, dry, chipdb="cal"):
    name = name_of(design, chipdb)
    d = CONFIG["out"] / "src" / name
    if (d / "export.json").exists():
        return d
    say(dry, f"export {d.relative_to(ROOT)}")
    if dry:
        return d
    run = src_run(design)
    st = json.loads((run / "status.json").read_text())
    syn_json = Path(st["cmd"][st["cmd"].index("--json") + 1])
    top = dinfo(design)["top"]
    nl = Netlist(syn_json, npr / "routed.json", top)
    mod, changes = nl.build()
    d.mkdir(parents=True, exist_ok=True)
    yj = dict(nl.y)
    yj["modules"] = {top: mod}
    (d / "netlist.json").write_text(json.dumps(yj))
    subprocess.run([tool("yosys"), "-q", "-p", f"read_json {d / 'netlist.json'}; delete t:$scopeinfo; "
                    f"write_edif -pvector bra {d / 'netlist.edf'}"], check=True)
    (d / "top.txt").write_text(top + "\n")
    (d / "constraints.xdc").write_text(Path(dinfo(design)["xdc"]).read_text())
    place, macros, lpins = [], defaultdict(list), []
    for nname, c in nl.ncells.items():
        yc, kind = nl.cmap[nname]
        bel = c["attributes"].get("NEXTPNR_BEL")
        if kind == "skip" or not bel or c["type"] in CONFIG["io_types"]:
            continue
        site, b = bel.split("/")
        if kind == "macro":
            mt = nl.ycells[yc]["type"]
            rule = CONFIG["lutram_macros"].get(mt)
            m = re.match(r"^([A-D])([56])LUT$", b)
            if rule and m:
                macros[yc].append((rule[m.group(2)].format(l=m.group(1)), bel))
            continue
        if c["type"] == "BUFGCTRL":
            place.append((yc, site))
            continue
        place.append((yc, bel))
        if c["attributes"].get("X_ORIG_TYPE") in CONFIG["lut_types"]:
            lp = lock_pins(c)
            if lp:
                lpins.append((yc, lp))
    tiles = tile_names()
    routes, const = [], []
    for nm, net in nl.n["netnames"].items():
        r = net["attributes"].get("ROUTING")
        if not r or not net["bits"]:
            continue
        pips = net_pips(r, tiles)
        if not pips:
            continue
        b = net["bits"][0]
        canon = nl.canon.get(b)
        if canon in ("0", "1"):
            const.append((canon, nm, pips))
            continue
        ident = None
        for u, p in nl.users.get(b, []):
            if nl.cmap[u][1] in ("cell", "new", "retyped"):
                ident = nl.vpin(u, p)
                if ident:
                    break
        if ident is None and b in nl.driver:
            ident = nl.vpin(*nl.driver[b])
        routes.append((ident or "-", nm, pips))
    ram = {nl.vname[n] for n, c in nl.ncells.items() if c["attributes"].get("X_ORIG_TYPE") in CONFIG["lutram_types"]}
    place.sort(key=lambda cb: (cb[0] not in ram, not re.search(r"/D[56]LUT$", cb[1])))
    (d / "place.txt").write_text("".join(f"{{{c}}} {b}\n" for c, b in place))
    (d / "macros.txt").write_text("".join(f"{{{m}}} " + " ".join(f"{{{s}}} {b}" for s, b in v) + "\n"
                                          for m, v in macros.items()))
    (d / "lockpins.txt").write_text("".join(f"{{{c}}} {{{' '.join(lp)}}}\n" for c, lp in lpins))
    (d / "routes.txt").write_text("".join(f"{{{i}}} {{{nm}}} {' '.join(p)}\n" for i, nm, p in routes))
    (d / "const_routes.txt").write_text("".join(f"{v} {{{nm}}} {' '.join(p)}\n" for v, nm, p in const))
    (d / "names.json").write_text(json.dumps(nl.vname))
    sub_of = {bel: s for v in macros.values() for s, bel in v}
    pinmap = {}
    for nname, c in nl.ncells.items():
        yc, kind = nl.cmap[nname]
        if kind == "skip":
            continue
        vc = yc
        if kind == "macro":
            s = sub_of.get(c["attributes"].get("NEXTPNR_BEL"))
            if not s:
                continue
            vc = f"{yc}/{s}"
        for p in c["connections"]:
            op = nl.oport(nname, p)
            if op:
                pinmap.setdefault(f"{vc}/{op}", [nname, p])
    (d / "pinmap.json").write_text(json.dumps(pinmap))
    info = {"stats": dict(nl.stats), "place": len(place), "macros": len(macros), "lockpins": len(lpins),
            "routes": len(routes), "routes_unidentified": sum(1 for i, _, _ in routes if i == "-"),
            "const_nets": len(const), "pips": sum(len(p) for _, _, p in routes),
            "rewires_to_existing": [(a, b, str(c), str(e)) for a, b, c, e, k in changes if k == "to_existing"][:50],
            "from": str(run), "npr": str(npr)}
    (d / "export.json").write_text(json.dumps(info, indent=1) + "\n")
    return d


def main():
    ap = argparse.ArgumentParser(description="Time nextpnr's complete implementation (placement and routing) in Vivado: "
                                             "export the netlist as nextpnr implemented it, every cell's BEL, LUT pin "
                                             "mapping and every net's pips; compare per arc and per path")
    ap.add_argument("--designs", nargs="+", default=list(CONFIG["designs"]))
    ap.add_argument("--chipdb", default="cal")
    ap.add_argument("--prep", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    names = []
    for d in a.designs:
        if a.prep:
            npr = rerun_nextpnr(d, a.chipdb, dry)
            if a.chipdb in CONFIG["export_timers"]:
                export(d, npr, dry, a.chipdb)
        names.append(name_of(d, a.chipdb))
    print("names: " + " ".join(names))


if __name__ == "__main__":
    main()
