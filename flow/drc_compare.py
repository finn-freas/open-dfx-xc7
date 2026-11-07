import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ofx import drc

CONFIG = {
    "viv": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "viv_order": ("drcpow", "drcpow_b2", "drcpow_b1", "drcpow2", "gap5", "gap4", "gap3", "prim", "gap2", "gap", "xdc2", "xdc", "ddr3", "eth"),
    "out": ROOT / "build" / "drc" / "compare.json",
    "md": ROOT / "build" / "drc" / "compare.md",
    "rule_row": re.compile(r"^\|\s*([A-Z0-9]+-\d+)\s*\|\s*([A-Za-z ]+?)\s*\|\s*(.*?)\s*\|\s*(\d+)\s*\|", re.M),
    "log_id": re.compile(r"^(ERROR|CRITICAL WARNING|WARNING): \[(Place 30-\d+|DRC [A-Z0-9]+-\d+)\]\s*(.*)$", re.M),
    "skip_rules": ("Place 30-99", "Place 30-2953", "Place 30-568", "Place 30-87"),
    "fallback_ignore": ("RTSTAT-1",),
    "ofx_only_prefix": "OFX-",
    "sets_md": ("test", "gap", "xdc", "ddr3", "eth", "qor"),
}


def sets():
    out = []
    for d in sorted((ROOT / "designs" / "drc").iterdir()):
        n = d.name
        out.append(("test", n, ROOT / "build" / "drc" / n, [d / f"{n}.xdc"]))
    pw = ROOT / "designs" / "power"
    for d in sorted(pw.iterdir()) if pw.exists() else ():
        out.append(("power", d.name, ROOT / "build" / "power" / "open" / d.name, [d / f"{d.name}.xdc"]))
    for d in sorted((ROOT / "designs" / "gap").iterdir()):
        n = d.name
        out.append(("gap", n, ROOT / "build" / "gap" / n / "ofx", sorted(d.glob("*.xdc"))))
    for d in sorted((ROOT / "designs" / "xdc").iterdir()):
        n = d.name
        out.append(("xdc", n, ROOT / "build" / "xdc" / n / "xdc2", sorted(d.glob("*.xdc"))))
    for kind, n, b in (("ddr3", "arty_ddr3", "build/ddr3/arty_ddr3/gapfix"), ("eth", "arty_eth", "build/eth/arty_eth/gapfix")):
        out.append((kind, n, ROOT / b, sorted((ROOT / "designs" / kind / n).glob("*.xdc"))))
    for d in sorted((ROOT / "build" / "qor" / "src").iterdir()):
        out.append(("qor", d.name, ROOT / "build" / "qor" / "oxc7" / "base" / d.name / "s1", sorted(d.glob("*.xdc"))))
    return out


def viv_dir(kind, name):
    for tag in CONFIG["viv_order"]:
        sub = CONFIG["viv"] / tag
        for cand in (sub / name, sub / name / name):
            if (cand / "status.txt").exists() or (cand / "drc.rpt").exists():
                return cand
    return None


def log_section(d, name):
    log = d.parent / "vivado.log"
    if not log.exists():
        return ""
    t = log.read_text(errors="replace")
    m = re.search(rf"(?:DRCPOW|XDC|GAP)_BEGIN {re.escape(name)}\n(.*?)(?=(?:DRCPOW|XDC|GAP)_BEGIN |\Z)", t, re.S)
    return m.group(1) if m else ""


def vivado_rules(d, name):
    rules = {}
    rpt = None
    for f in ("drc.rpt", "drc_place_fail.rpt", "drc_opt.rpt"):
        if (d / f).exists():
            rpt = d / f
            break
    if rpt:
        for rule, sev, desc, n in CONFIG["rule_row"].findall(rpt.read_text(errors="replace")):
            rules[rule] = {"severity": sev, "count": int(n), "description": desc, "src": rpt.name}
    sec = log_section(d, name)
    for sev, rid, msg in CONFIG["log_id"].findall(sec):
        rid = rid.replace("DRC ", "")
        if rid not in rules and rid not in CONFIG["skip_rules"]:
            sv = {"ERROR": "Error", "CRITICAL WARNING": "Critical Warning", "WARNING": "Warning"}[sev]
            rules[rid] = {"severity": sv, "count": 1, "description": msg[:120], "src": "vivado.log"}
    st = (d / "status.txt").read_text(errors="replace") if (d / "status.txt").exists() else ""
    return rules, rpt.name if rpt else None, st


def ofx_rules(build, xdcs):
    from ofx import design as D
    np = D.find_netlist(build) if build.exists() else None
    if np is None:
        return None, None
    rep, net = drc.run_checks(np, [str(x) for x in xdcs])
    out = defaultdict(lambda: {"count": 0})
    for v in rep.v:
        if v["rule"].startswith(CONFIG["ofx_only_prefix"]):
            continue
        out[v["rule"]]["count"] += 1
        out[v["rule"]]["severity"] = v["severity"]
    return dict(out), net.routed


def compare(kinds):
    rows = []
    for kind, name, build, xdcs in sets():
        if kinds and kind not in kinds:
            continue
        vd = viv_dir(kind, name)
        if vd is None:
            continue
        vr, src, st = vivado_rules(vd, name)
        o, routed = ofx_rules(build, xdcs)
        if o is None:
            rows.append({"kind": kind, "name": name, "vivado": vr, "ofx": None, "vivado_src": src})
            continue
        if not routed:
            for r in CONFIG["fallback_ignore"]:
                o.pop(r, None)
        rows.append({"kind": kind, "name": name, "vivado": vr, "ofx": o, "routed": routed, "vivado_src": src,
                     "vivado_dir": str(vd), "status": st.strip()})
    return rows


def per_rule(rows):
    agg = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0, "count_eq": 0, "designs_fn": [], "designs_fp": [],
                               "sev_viv": set(), "sev_ofx": set()})
    for r in rows:
        if r["ofx"] is None:
            continue
        for rule in set(r["vivado"]) | set(r["ofx"]):
            a = agg[rule]
            v, o = r["vivado"].get(rule), r["ofx"].get(rule)
            if not v and r["vivado_src"] is None:
                continue
            if v:
                a["sev_viv"].add(v["severity"])
            if o:
                a["sev_ofx"].add(o["severity"])
            if v and o:
                a["tp"] += 1
                a["count_eq"] += int(v["count"] == o["count"])
            elif v:
                a["fn"] += 1
                a["designs_fn"].append(r["name"])
            else:
                a["fp"] += 1
                a["designs_fp"].append(r["name"])
    return {k: {**v, "sev_viv": sorted(v["sev_viv"]), "sev_ofx": sorted(v["sev_ofx"])} for k, v in agg.items()}


def totals(agg):
    tp = sum(a["tp"] for a in agg.values())
    fn = sum(a["fn"] for a in agg.values())
    fp = sum(a["fp"] for a in agg.values())
    return tp, fn, fp


def markdown(rows, agg):
    tp, fn, fp = totals(agg)
    nrow = sum(1 for r in rows if r["ofx"] is not None)
    rules_ok = sum(1 for a in agg.values() if a["fn"] == 0 and a["fp"] == 0)
    out = [f"{nrow} designs with a Vivado report_drc and an open netlist; {len(agg)} rules seen; "
           f"(design, rule) pairs: {tp} flagged by both, {fn} Vivado only, {fp} ofx only; "
           f"{rules_ok}/{len(agg)} rules with no disagreement", "",
           "| Rule | Vivado severity | ofx severity | both flag | Vivado only | ofx only | same count | where they differ |",
           "|---|---|---|---|---|---|---|---|"]
    for rule, a in sorted(agg.items()):
        diff = ", ".join(sorted(set(a["designs_fn"]))[:6] + [f"+{x}" for x in sorted(set(a["designs_fp"]))[:6]])
        out.append(f"| {rule} | {'/'.join(a['sev_viv']) or '-'} | {'/'.join(a['sev_ofx']) or '-'} | {a['tp']} | {a['fn']} | "
                   f"{a['fp']} | {a['count_eq']}/{a['tp']} | {diff} |")
    out += ["", "| Design | set | Vivado | ofx | open netlist |", "|---|---|---|---|---|"]
    for r in rows:
        v = " ".join(f"{k}x{x['count']}" for k, x in sorted(r["vivado"].items()))
        o = "(no open build)" if r["ofx"] is None else " ".join(f"{k}x{x['count']}" for k, x in sorted(r["ofx"].items()))
        out.append(f"| {r['name']} | {r['kind']} | {v} | {o} | {'routed' if r.get('routed') else 'synth only'} |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="run ofx drc on the open builds and compare with Vivado report_drc")
    ap.add_argument("--kinds", nargs="*", help="test gap xdc ddr3 eth qor (default all)")
    ap.add_argument("--show", action="store_true", help="print the per-design table")
    a = ap.parse_args()
    rows = compare(a.kinds)
    agg = per_rule(rows)
    CONFIG["out"].parent.mkdir(parents=True, exist_ok=True)
    CONFIG["out"].write_text(json.dumps({"rows": rows, "rules": agg}, indent=1, default=list) + "\n")
    md = markdown(rows, agg)
    CONFIG["md"].write_text(md)
    print(md if a.show else md.split("\n\n")[0])
    print(f"{len(rows)} designs; {CONFIG['out']}")


if __name__ == "__main__":
    main()
