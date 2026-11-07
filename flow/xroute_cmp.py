import argparse
import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xroute

ROOT = xroute.ROOT

CONFIG = {
    "src": xroute.CONFIG["out"] / "src",
    "npr": xroute.CONFIG["out"] / "npr",
    "vivado": xroute.CONFIG["vivado_out"] / xroute.CONFIG["vivado_tag"],
    "out": xroute.CONFIG["out"] / "cmp",
    "bit2fasm": ROOT / "flow" / "bit2fasm.py",
    "tabbypy": ROOT / "toolchain/openxc7/libexec/tabbypy3",
    "const_net_re": r"^(GND|VCC)(_\w+)?$|^<const[01]>$",
    "dry_run": True,
    "strict_unfixed": True,
    "wire_classes": [
        ("clock", r"^(GCLK|HCLK|CLK_|GFAN|CLK\d|CLK_L\d|BUFH|HROW|CMT|CCIO|LIOI_I2GCLK|RIOI_I2GCLK|IOI_I2GCLK)"),
        ("long", r"^(LH\d+|LV\d+|LV_L\d+|LVB\d+|LVB_L\d+)$"),
        ("hex", r"^[NSEW]{2}6(BEG|A|B|C|D|E|END|MID)"),
        ("double", r"^[NSEW]{2}2(BEG|A|END|MID)"),
        ("single", r"^[NSEW][NSEWLR]1(BEG|END)"),
        ("bounce", r"^(FAN_ALT|FAN_BOUNCE|BYP_ALT|BYP_BOUNCE|BYP_BOUNCE_N|FAN_BOUNCE_S|GND_WIRE|VCC_WIRE)"),
        ("imux", r"^(IMUX|BYP\d|BYP_L\d|FAN\d|FAN_L\d|CTRL|CLK_L|IMUX_L)"),
        ("out", r"^(LOGIC_OUTS)"),
    ],
    "vivado_cell": {
        "LUT": r"^LUT[1-6]$",
        "FF": r"^FD[RSCP]E$",
        "CARRY4": r"^CARRY4$",
        "MUXF": r"^MUXF[78]$",
        "BRAM": r"^RAMB(18|36)E1$",
        "DSP": r"^DSP48E1$",
        "LUTRAM": r"^RAM[DS](32|64)",
        "SRL": r"^SRL",
        "IO": r"^(IBUF|OBUF)",
        "BUFG": r"^BUFG",
        "ICAP": r"^ICAPE2$",
    },
}


def unesc(s):
    return re.sub(r"\\(.)", r"\1", s)


def tmax(t):
    return float(t.strip("()").split(":")[-1])


def tmin(t):
    return float(t.strip("()").split(":")[0])


def mm(a, b):
    return (min(tmin(a), tmin(b)), max(tmax(a), tmax(b)))


def parse_sdf(path):
    inter, iopath, setup, hold = {}, {}, {}, {}
    inst = None
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        m = re.match(r"^\(INTERCONNECT (\S+) (\S+) (\([^)]*\)) (\([^)]*\))\)$", s)
        if m:
            a, b = unesc(m.group(1)), unesc(m.group(2))
            ai, ap = a.rsplit("/", 1)
            bi, bp = b.rsplit("/", 1)
            inter[(ai, ap, bi, bp)] = mm(m.group(3), m.group(4))
            continue
        m = re.match(r"^\(INSTANCE (.*)\)$", s)
        if m:
            inst = unesc(m.group(1))
            continue
        m = re.match(r"^\(IOPATH (\S+) (\S+) (\([^)]*\)) (\([^)]*\))\)$", s)
        if m:
            iopath[(inst, m.group(1), m.group(2))] = mm(m.group(3), m.group(4))
            continue
        m = re.match(r"^\(SETUPHOLD \((pos|neg)edge (\S+)\) \((pos|neg)edge (\S+)\) (\([^)]*\)) (\([^)]*\))\)$", s)
        if m:
            k = (inst, m.group(2), m.group(4))
            setup[k] = max(setup.get(k, -1e9), tmax(m.group(5)))
            hold[k] = max(hold.get(k, -1e9), tmin(m.group(6)))
    return {"inter": inter, "iopath": iopath, "setup": setup, "hold": hold}


def wire_class(node):
    w = node.split("/")[-1]
    for name, pat in CONFIG["wire_classes"]:
        if re.match(pat, w):
            return name
    return "other"


def cell_class(ref):
    for k, pat in CONFIG["vivado_cell"].items():
        if re.match(pat, ref):
            return k
    return "other"


def stat(errs):
    if not errs:
        return None
    a = [abs(e) for e in errs]
    return {"n": len(errs), "mean": statistics.mean(errs), "median": statistics.median(errs), "mae": statistics.mean(a),
            "p90abs": sorted(a)[int(0.9 * (len(a) - 1))], "min": min(errs), "max": max(errs)}


def vname(s):
    return s.replace("\\\\", "\\")


def parse_paths(path):
    text = Path(path).read_text(errors="replace").splitlines()
    paths, cur, sec, pend = [], None, 0, None
    num = r"(-?\d+\.\d+)"
    for raw in text:
        line = raw.rstrip()
        m = re.match(r"^Slack(?: \((MET|VIOLATED)\))?\s*:\s*" + num + "ns", line)
        if m:
            cur = {"slack": float(m.group(2)), "arcs": [], "sec": 0}
            paths.append(cur)
            sec, pend, last_pin, last_out = 0, None, None, None
            continue
        if cur is None:
            continue
        for key, pat in (("requirement", r"^\s+Requirement:\s+" + num), ("datapath", r"^\s+Data Path Delay:\s+" + num),
                         ("skew", r"^\s+Clock Path Skew:\s+" + num), ("uncertainty", r"^\s+Clock Uncertainty:\s+" + num)):
            m = re.match(pat, line)
            if m:
                cur[key] = float(m.group(1))
        m = re.match(r"^\s+Source:\s+(\S+)", line)
        if m:
            cur["source"] = vname(m.group(1))
        m = re.match(r"^\s+Destination:\s+(\S+)", line)
        if m:
            cur["dest"] = vname(m.group(1))
        if re.match(r"^\s+-{20,}", line):
            sec += 1
            continue
        if sec == 0:
            continue
        if pend is not None:
            line = pend + " " + line.strip()
            pend = None
        m = re.search(r"(\w+) \(((?:Prop|Setup|Hold)_\S+)\)\s*$", line)
        if m:
            pend = line
            continue
        m = re.search(r"(\w+) \(((?:Prop|Setup|Hold)_\S+)\)\s+" + num + r"\s+" + num + r"\s*[rf]?\s*(\S*)$", line)
        if m:
            ref, kind, incr, pin = m.group(1), m.group(2), float(m.group(3)), vname(m.group(5))
            if kind.startswith("Prop"):
                if sec == 2:
                    cur["arcs"].append(("cell", last_pin, pin, incr, ref, kind))
                last_out = pin
                last_pin = pin
            elif sec == 3:
                cur["check"] = (ref, kind, -incr if kind.startswith("Setup") else incr, pin)
            continue
        m = re.search(r"net \(fo=\d+, routed\)\s+" + num + r"\s+" + num + r"\s+(\S+)$", line)
        if m:
            cur.setdefault("_nets", []).append(float(m.group(1)))
            cur["_net_pending"] = (float(m.group(1)), vname(m.group(3)), sec)
            continue
        if re.search(r"net \(fo=\d+, (?!routed\))\w+\)", line) and sec == 2:
            cur["estimated_nets"] = cur.get("estimated_nets", 0) + 1
            continue
        m = re.search(r"\s[rf]\s+(\S+/\S+)$", line)
        if m and not re.search(num + r"\s+" + num, line):
            pin = vname(m.group(1))
            np_ = cur.pop("_net_pending", None)
            if np_ and np_[2] == 2 == sec:
                cur["arcs"].append(("net", last_out, pin, np_[0], np_[1], ""))
            if sec == 1:
                cur["start_pin"] = pin
            if sec == 2:
                cur["end_pin"] = pin
            last_pin = pin
            continue
        m = re.match(r"^\s+clock pessimism\s+" + num, line)
        if m and sec == 3:
            cur["cpr"] = float(m.group(1))
    for p in paths:
        p.pop("_nets", None)
        p.pop("_net_pending", None)
        p.pop("sec", None)
    return paths


PIP_RE = r"^(?P<tile>[A-Z0-9_]+_X\d+Y\d+)/(?P<type>[A-Z0-9_]+)\.(?P<src>[A-Za-z0-9_]+)(?P<dir><<->>|->>|->)(?P<dst>[A-Za-z0-9_]+)$"


def npr_pips(src):
    out, const = set(), set()
    for f, tgt in (("routes.txt", out), ("const_routes.txt", const)):
        for ln in (src / f).read_text().splitlines():
            for p in ln.split()[2:]:
                if p.count("/") == 2 and not p.startswith("{"):
                    tgt.add(p)
    return out, const


def viv_pips(path):
    by_net = defaultdict(set)
    for ln in Path(path).read_text(errors="replace").splitlines():
        net, _, pip = ln.partition("\t")
        m = re.match(PIP_RE, pip)
        if m:
            by_net[net].add((f"{m['tile']}/{m['src']}/{m['dst']}", m["dir"] == "<<->>", f"{m['tile']}/{m['dst']}/{m['src']}"))
    return by_net


def identity(name):
    src, viv = CONFIG["src"] / name, CONFIG["vivado"] / name
    nset, nconst = npr_pips(src)
    vb = viv_pips(viv / "vpips.txt")
    vset, vconst = set(), set()
    for net, ps in vb.items():
        tgt = vconst if re.match(CONFIG["const_net_re"], net) else vset
        for fwd, bidi, rev in ps:
            tgt.add(rev if bidi and rev in nset | nconst else fwd)
    res = {"npr_pips": len(nset), "viv_pips": len(vset), "only_npr": sorted(nset - vset)[:20],
           "only_viv": sorted(vset - nset)[:20], "n_only_npr": len(nset - vset), "n_only_viv": len(vset - nset),
           "npr_const_pips": len(nconst), "viv_const_pips": len(vconst), "const_common": len(nconst & vconst)}
    log = (viv / "route_log.txt").read_text(errors="replace").splitlines() if (viv / "route_log.txt").exists() else []
    res["route_log_tail"] = log[-1] if log else None
    res["route_log_errors"] = Counter(ln.split()[0] for ln in log[:-1] if ln.split() and ln.split()[0].startswith(("err_", "status_", "nonet", "badpips", "roots")))
    return res


def fasm_identity(name, dry):
    viv = CONFIG["vivado"] / name
    top = (CONFIG["src"] / name / "top.txt").read_text().strip()
    bit, vf = viv / f"{top}.bit", CONFIG["out"] / name / "vivado.fasm"
    done = json.loads((CONFIG["npr"] / name / "done.json").read_text())
    if not done.get("fasm_identical_to_source"):
        return None
    nbit = Path(done["source"]) / f"{top}.bit"
    nfasm = CONFIG["out"] / name / "nextpnr_bit.fasm"
    if not bit.exists():
        return None
    for b, f in ((bit, vf), (nbit, nfasm)):
        if f.exists():
            continue
        print(f"[{'dry' if dry else 'run'}] bit2fasm {b} -> {f}")
        if dry:
            return None
        f.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(CONFIG["tabbypy"]), str(CONFIG["bit2fasm"]), str(b), str(f)], check=True, cwd=ROOT,
                       stdout=subprocess.DEVNULL)
    def feats(p):
        out = set()
        for ln in Path(p).read_text().splitlines():
            ln = ln.split("#")[0].strip()
            if not ln:
                continue
            m = re.match(r"^(\S+?)(\[(\d+):(\d+)\])?\s*=\s*\d+'b([01]+)$", ln)
            if m and m.group(2):
                hi, lo, bits = int(m.group(3)), int(m.group(4)), m.group(5)
                for k, b in enumerate(reversed(bits)):
                    if b == "1":
                        out.add(f"{m.group(1)}[{lo + k}]")
                continue
            out.add(ln)
        return out
    nf = feats(nfasm)
    vfe = feats(vf)
    nconst = set()
    for ln in (CONFIG["src"] / name / "const_routes.txt").read_text().splitlines():
        for p in ln.split()[2:]:
            if p.count("/") == 2:
                t, src_, dst = p.split("/")
                nconst.add(f"{t}.{dst}.{src_}")
    vconst = set()
    for net, ps in viv_pips(viv / "vpips.txt").items():
        if re.match(CONFIG["const_net_re"], net):
            for fwd, bidi, rev in ps:
                for q in ((fwd, rev) if bidi else (fwd,)):
                    t, src_, dst = q.split("/")
                    vconst.add(f"{t}.{dst}.{src_}")
    def kind(f):
        if f in nconst or f in vconst:
            return "constant-net pip"
        if ".PRECYINIT." in f:
            return "carry CYINIT constant (AX routed GND vs C0)"
        if "REBUF" in f or "_USED" in f:
            return "clock buffer enable / used bits"
        if re.match(r"^[LR]IOB33_", f):
            return "IOB config"
        return "other"
    only_n, only_v = nf - vfe, vfe - nf
    return {"npr_features": len(nf), "viv_features": len(vfe), "common": len(nf & vfe), "n_only_npr": len(only_n),
            "n_only_viv": len(only_v), "only_npr_kinds": dict(Counter(kind(f) for f in only_n)),
            "only_viv_kinds": dict(Counter(kind(f) for f in only_v)),
            "other_npr": sorted(f for f in only_n if kind(f) == "other")[:40],
            "other_viv": sorted(f for f in only_v if kind(f) == "other")[:40]}


def xroute_npr_name(name):
    return name


def arc_nodes(viv):
    parent = defaultdict(dict)
    for ln in (viv / "edges.txt").read_text(errors="replace").splitlines():
        p = ln.split("\t")
        if len(p) >= 3:
            parent[p[0]][p[2]] = (p[1], p[3] if len(p) > 3 else None)
    out, pips = {}, {}
    for ln in (viv / "sinks.txt").read_text(errors="replace").splitlines():
        p = ln.split("\t")
        if len(p) < 5:
            continue
        net, drv, pin, nodes = p[0], p[1], p[2], p[4].split()
        if not nodes:
            out[pin] = []
            pips[pin] = []
            continue
        n, path, pl, par = nodes[0], [], [], parent.get(net, {})
        guard = 0
        while n in par and guard < 500:
            path.append(n)
            pl.append(par[n][1])
            n = par[n][0]
            guard += 1
        out[pin] = path
        pips[pin] = pl
    arc_nodes.pips = pips
    return out


def class_counts(path):
    return Counter(wire_class(n) for n in path)


def top_class(cc):
    for k in ("clock", "long", "hex", "double", "single", "bounce"):
        if cc.get(k):
            return k
    return "local" if cc else "intrasite"


def unfixed_nets(viv):
    out = set()
    f = viv / "route_log.txt"
    if not f.exists():
        return out
    for ln in f.read_text(errors="replace").splitlines():
        p = ln.split()
        if len(p) >= 2 and p[0] in ("status_rel", "err_rel", "nonet"):
            out.add(p[1])
    want = defaultdict(set)
    ef = viv / "edges.txt"
    if ef.exists():
        for ln in ef.read_text(errors="replace").splitlines():
            q = ln.split("	")
            if len(q) > 3 and q[0] in out:
                want[q[0]].add(q[3])
    if not want:
        return out
    got = viv_pips(viv / "vpips.txt")
    same = set()
    for n in out:
        g = {fwd for fwd, bidi, rev in got.get(n, set())} | {rev for fwd, bidi, rev in got.get(n, set()) if bidi}
        if want.get(n) and want[n] <= g and len({fwd for fwd, _, _ in got.get(n, set())}) == len(want[n]):
            same.add(n)
    unfixed_nets.same = len(same)
    return out if CONFIG["strict_unfixed"] else out - same


def npr_dir(name, timer):
    return CONFIG["npr"] / (name if timer == "cal" else f"{name}_{timer}")


def compare(name, kind="setup", timer="cal", add=None, classify=None):
    src, viv = CONFIG["src"] / name, CONFIG["vivado"] / name
    pm = {k: tuple(v) for k, v in json.loads((src / "pinmap.json").read_text()).items()}
    sdf = parse_sdf(npr_dir(name, timer) / "npr.sdf")
    use = 1 if kind == "setup" else 0
    clk_in = {}
    for (a, ap, b, bp), v in sdf["inter"].items():
        clk_in[(b, bp)] = v
    routes = arc_nodes(viv)
    by_to = defaultdict(list)
    for (inst, a, b), v in sdf["iopath"].items():
        by_to[(inst, b)].append((a, v))
    paths = parse_paths(viv / f"paths_{kind}.rpt")
    bad = unfixed_nets(viv)
    cells, nets, prow, miss = {}, {}, [], Counter()
    for p in paths:
        ok, nsum, vsum = True, 0.0, 0.0
        if any(t == "net" and r in bad for t, _, _, _, r, _ in p["arcs"]):
            miss["path_on_unfixed_net"] += 1
            continue
        if p.get("estimated_nets"):
            miss["path_on_unrouted_net"] += 1
            continue
        for typ, a, b, d, ref, k in p["arcs"]:
            na, nb = pm.get(a), pm.get(b)
            if not na or not nb:
                miss[f"{typ}_pin"] += 1
                ok = False
                continue
            if typ == "cell":
                v = sdf["iopath"].get((na[0], na[1], nb[1]))
                if v is None and na[0] == nb[0]:
                    base = re.sub(r"[LU]$", "", na[1])
                    alt = [vv for a2, vv in by_to.get((na[0], nb[1]), []) if re.sub(r"[LU]$", "", a2) == base]
                    v = alt[0] if alt else None
                if v is None or na[0] != nb[0]:
                    miss["cell_arc"] += 1
                    ok = False
                    continue
                key = (a, b)
                cells.setdefault(key, {"ref": ref, "cls": cell_class(ref), "viv": d, "npr": v[use], "arc": k,
                                       "npr_cell": na[0], "npr_from": na[1], "npr_to": nb[1]})
                cells[key]["viv"] = max(cells[key]["viv"], d) if kind == "setup" else min(cells[key]["viv"], d)
            else:
                v = sdf["inter"].get((na[0], na[1], nb[0], nb[1]))
                if v is None:
                    miss["net_arc"] += 1
                    ok = False
                    continue
                if add and kind == "setup":
                    extra = sum(add.get(classify(q), 0.0) for q in arc_nodes.pips.get(b, []) if q) * 1000.0
                    v = (v[0], v[1] + extra)
                cc = class_counts(routes.get(b, []))
                key = (a, b)
                nets.setdefault(key, {"viv": d, "npr": v[use], "cls": top_class(cc), "counts": dict(cc), "net": ref})
                nets[key]["viv"] = max(nets[key]["viv"], d) if kind == "setup" else min(nets[key]["viv"], d)
            nsum += v[use]
            vsum += d
        if not ok or "check" not in p or not p.get("start_pin") or not p.get("end_pin"):
            continue
        sp, ep = pm.get(p["start_pin"]), pm.get(p["end_pin"])
        ck_end = None
        ck_cell = ep[0] if ep else None
        chk = None
        if ep:
            for (inst, port, clk), sv in (sdf["setup"] if kind == "setup" else sdf["hold"]).items():
                if inst == ep[0] and port == ep[1]:
                    chk, ck_end = sv, clk
                    break
        if chk is None or not sp:
            miss["check"] += 1
            continue
        cl = clk_in.get((sp[0], sp[1]), (0.0, 0.0))[use]
        cc_ = clk_in.get((ep[0], ck_end), (0.0, 0.0))[use]
        vt = p["requirement"] - p["slack"] - p.get("uncertainty", 0.0) if kind == "setup" else p["slack"] + p.get("uncertainty", 0.0)
        if kind == "setup":
            nt = (nsum + chk + cl - cc_) / 1000.0
        else:
            nt = (nsum - chk + cl - cc_) / 1000.0
        prow.append({"start": p["start_pin"], "end": p["end_pin"], "viv_T": vt, "npr_T": nt, "viv_data": p.get("datapath"),
                     "npr_data": nsum / 1000.0, "viv_check": p["check"][2], "npr_check": chk / 1000.0,
                     "viv_skew": p.get("skew"), "npr_skew": (cc_ - cl) / 1000.0, "check_kind": p["check"][1],
                     "levels": sum(1 for a in p["arcs"] if a[0] == "cell") - 1})
    for d in list(cells.values()) + list(nets.values()):
        d["npr"] = d["npr"] / 1000.0
    return {"paths": prow, "cells": cells, "nets": nets, "miss": dict(miss), "n_paths": len(paths)}


def tables(res):
    out = {}
    cells = defaultdict(list)
    for d in res["cells"].values():
        k = d["cls"]
        if k == "FF":
            k = "FF clk->Q"
        cells[k].append(d["npr"] - d["viv"])
    out["cell"] = {k: stat(v) for k, v in cells.items()}
    nets = defaultdict(list)
    for d in res["nets"].values():
        nets[d["cls"]].append(d["npr"] - d["viv"])
    out["net"] = {k: stat(v) for k, v in nets.items()}
    chk = defaultdict(list)
    for p in res["paths"]:
        chk[p["check_kind"].split("_")[0] + "_" + p["check_kind"].split("_")[1]].append(p["npr_check"] - p["viv_check"])
    out["check"] = {k: stat(v) for k, v in chk.items()}
    out["path"] = stat([p["npr_T"] - p["viv_T"] for p in res["paths"]])
    out["path_rel"] = stat([(p["npr_T"] - p["viv_T"]) / p["viv_T"] for p in res["paths"] if p["viv_T"] > 0.2])
    out["skew"] = stat([p["npr_skew"] - (p["viv_skew"] or 0) for p in res["paths"]])
    return out


def all_net_arcs(name, timer="cal"):
    src, viv = CONFIG["src"] / name, CONFIG["vivado"] / name
    pm = {k: tuple(v) for k, v in json.loads((src / "pinmap.json").read_text()).items()}
    sdf = parse_sdf(npr_dir(name, timer) / "npr.sdf")
    by_sink = {(b, bp): v for (a, ap, b, bp), v in sdf["inter"].items()}
    routes = arc_nodes(viv)
    bad = unfixed_nets(viv)
    rows, miss = [], Counter()
    for ln in (viv / "net_delays.txt").read_text(errors="replace").splitlines():
        p = ln.split("\t")
        if len(p) < 5 or p[1] == "ERR" or not p[3]:
            continue
        net, to, smax, fmin = p[0], p[2], float(p[3]) / 1000.0, float(p[4]) / 1000.0
        if re.match(CONFIG["const_net_re"], net):
            continue
        if len(p) > 6 and p[6] == "1":
            miss["estimated"] += 1
            continue
        if net in bad:
            miss["unfixed_net"] += 1
            continue
        np_ = pm.get(to)
        if not np_:
            miss["pin"] += 1
            continue
        v = by_sink.get(np_)
        if v is None:
            miss["arc"] += 1
            continue
        path = routes.get(to)
        if path is None:
            miss["route"] += 1
            continue
        cc = class_counts(path)
        rows.append({"net": net, "to": to, "viv": smax, "viv_min": fmin, "npr": v[1] / 1000.0, "npr_min": v[0] / 1000.0,
                     "counts": dict(cc), "cls": top_class(cc), "nodes": path, "pips": arc_nodes.pips.get(to, []),
                     "npr_cell": np_[0], "npr_port": np_[1]})
    return rows, dict(miss)


def lstsq(X, y, ridge=1e-6):
    k = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) + (ridge if i == j else 0.0) for j in range(k)] for i in range(k)]
    b = [sum(r[i] * t for r, t in zip(X, y)) for i in range(k)]
    for c in range(k):
        piv = max(range(c, k), key=lambda r: abs(A[r][c]))
        A[c], A[piv], b[c], b[piv] = A[piv], A[c], b[piv], b[c]
        if abs(A[c][c]) < 1e-12:
            continue
        for r in range(k):
            if r != c:
                f = A[r][c] / A[c][c]
                A[r] = [x - f * y_ for x, y_ in zip(A[r], A[c])]
                b[r] -= f * b[c]
    return [b[i] / A[i][i] if abs(A[i][i]) > 1e-12 else 0.0 for i in range(k)]


def fmt(s, unit=1000.0):
    if not s:
        return "-"
    return f"{s['n']} / {s['mean'] * unit:+.0f} / {s['mae'] * unit:.0f} / {s['p90abs'] * unit:.0f}"


def report(names, dry, timer="cal"):
    out = {}
    for n in names:
        viv = CONFIG["vivado"] / n
        if not (viv / "status.txt").exists():
            print(f"[skip] {n}: no Vivado result")
            continue
        d = CONFIG["out"] / (n if timer == "cal" else f"{n}_{timer}")
        d.mkdir(parents=True, exist_ok=True)
        r = {"identity": identity(n), "fasm": fasm_identity(n, dry)}
        for k in ("setup", "hold"):
            c = compare(n, k, timer)
            r[k] = {"tables": tables(c), "miss": c["miss"], "n_paths_vivado": c["n_paths"], "n_paths": len(c["paths"])}
            (d / f"paths_{k}.json").write_text(json.dumps(c["paths"], indent=0))
        rows, miss = all_net_arcs(n, timer)
        g = defaultdict(list)
        for a in rows:
            g[a["cls"]].append(a["npr"] - a["viv"])
        r["net_arcs"] = {"miss": miss, "by_class": {k: stat(v) for k, v in g.items()}, "n": len(rows)}
        (d / "net_arcs.json").write_text(json.dumps(rows))
        (d / "summary.json").write_text(json.dumps(r, indent=1, default=str))
        out[n] = r
    return out


def main():
    ap = argparse.ArgumentParser(description="Compare nextpnr's timer (SDF) with Vivado's on nextpnr's identical "
                                             "implementation (vivado/build_xroute.tcl results)")
    ap.add_argument("names", nargs="+")
    ap.add_argument("--timer", default="cal")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    res = report(a.names, dry, a.timer)
    for n, r in res.items():
        i, f = r["identity"], r["fasm"] or {}
        print(f"{n}: pips npr {i['npr_pips']} viv {i['viv_pips']} only_npr {i['n_only_npr']} only_viv {i['n_only_viv']}; "
              f"fasm common {f.get('common')} only_npr {f.get('n_only_npr')} only_viv {f.get('n_only_viv')}; "
              f"{i['route_log_tail']}")
        for k in ("setup", "hold"):
            t = r[k]["tables"]
            print(f"  {k} paths {r[k]['n_paths']}/{r[k]['n_paths_vivado']} path err (n/mean/mae/p90 ps) {fmt(t['path'])}")
            for c, s in sorted(t["cell"].items()):
                print(f"    cell {c}: {fmt(s)}")
            for c, s in sorted(t["check"].items()):
                print(f"    check {c}: {fmt(s)}")
        for c, s in sorted(r["net_arcs"]["by_class"].items()):
            print(f"    net {c}: {fmt(s)}")



def vivado_wns(name):
    t = (CONFIG["vivado"] / name / "timing.rpt").read_text(errors="replace").splitlines()
    i = [k for k, ln in enumerate(t) if ln.strip().startswith("WNS(ns)")][0]
    v = t[i + 2].split()
    return float(v[0]), float(v[4])


def claim(name, timer="cal"):
    r = json.loads((npr_dir(name, timer) / "report.json").read_text())
    return min(v["achieved"] for v in r["fmax"].values())


def md_table(names, timer, period_of):
    out = ["| design | nets fixed by ROUTE / routed nets | pips only nextpnr / only Vivado (of nextpnr's) | "
           "nextpnr claim MHz (nextpnr timer) | identical implementation MHz (Vivado timer) | claim error | Vivado MHz, worst fully routed path (paths with an unrouted net / reported) | claim error vs that |", "|---|---|---|---|---|---|---|---|"]
    comp = defaultdict(lambda: defaultdict(list))
    for n in names:
        s = json.loads((CONFIG["out"] / (n if timer == "cal" else f"{n}_{timer}") / "summary.json").read_text())
        i = s["identity"]
        ok = re.search(r"ok (\d+)", i["route_log_tail"] or "")
        routes = len((CONFIG["src"] / n / "routes.txt").read_text().splitlines())
        wns, whs = vivado_wns(n)
        viv = 1000.0 / (period_of(n) - wns)
        c = claim(n, timer)
        ps = parse_paths(CONFIG["vivado"] / n / "paths_setup.rpt")
        nest = sum(1 for q in ps if q.get("estimated_nets"))
        vr = 1000.0 / (period_of(n) - min(q["slack"] for q in ps if not q.get("estimated_nets")))
        out.append(f"| {n} | {ok.group(1) if ok else '-'} / {routes} | {i['n_only_npr']} / {i['n_only_viv']} "
                   f"(of {i['npr_pips']}) | {c:.2f} | {viv:.2f} (WNS {wns:+.3f}, WHS {whs:+.3f}) | "
                   f"{100 * (c - viv) / viv:+.1f} % | {vr:.2f} ({nest} / {len(ps)}) | {100 * (c - vr) / vr:+.1f} % |")
        d = CONFIG["out"] / (n if timer == "cal" else f"{n}_{timer}")
        for kind in ("setup", "hold"):
            for k, v in s[kind]["tables"]["cell"].items():
                if v:
                    comp[f"cell {k} ({kind})"][n] = v
            for k, v in s[kind]["tables"]["check"].items():
                if v:
                    comp[f"{k}"][n] = v
            comp[f"path T ({kind})"][n] = s[kind]["tables"]["path"]
        for k, v in s["net_arcs"]["by_class"].items():
            if v:
                comp[f"net {k} (slow max)"][n] = v
    out += ["", "| component | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for k in sorted(comp):
        out.append(f"| {k} | " + " | ".join(fmt(comp[k].get(n)) for n in names) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    main()
