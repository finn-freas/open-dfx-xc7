import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_xtime

ROOT = qor_xtime.ROOT

CONFIG = {
    "designs_dir": ROOT / "designs" / "xdc",
    "builds": ROOT / "build" / "xdc",
    "out": ROOT / "build" / "xdc_xtime",
    "vivado_out": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/xdc_xtime"),
    "vivado_ref": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/xdc"),
    "designs": ["x_iodly", "x_iodly_minmax", "x_iodly_fall", "x_mcp_from", "x_mcp_thru", "x_maxdly_cells", "x_maxdly_dp"],
    "variant": "xdc3",
    "dry_run": True,
    "npr_line": re.compile(r"Max (?:frequency|delay) for (.+?): .*?slack (-?[\d.]+) ns"),
    "rpt_slack": re.compile(r"^Slack \([A-Z]+\)\s*:\s*(-?[\d.]+)ns", re.M),
    "rpt_datapath": re.compile(r"Data Path Delay:\s*(-?[\d.]+)ns"),
    "npr_fmax": re.compile(r"Max frequency for clock '([^']+)': ([\d.]+) MHz \((?:PASS|FAIL) at ([\d.]+) MHz\)"),
}


def name_of(design, variant):
    return f"{design}_{variant}"


def register_names(module):
    bit_name = {}
    for n, nn in module["netnames"].items():
        if nn.get("hide_name"):
            continue
        bits, off = nn["bits"], nn.get("offset", 0)
        for i, b in enumerate(bits):
            bit_name.setdefault(b, f"{n}_reg[{i + off}]" if len(bits) > 1 else f"{n}_reg")
    names = {}
    for n, c in module["cells"].items():
        if c["type"].startswith("FD") and "Q" in c["connections"]:
            v = bit_name.get(c["connections"]["Q"][0])
            if v and v not in names.values():
                names[n] = v
    return names


def renamed_json(syn_json, out):
    j = json.loads(Path(syn_json).read_text())
    m = j["modules"][next(n for n, mod in j["modules"].items() if mod.get("attributes", {}).get("top"))]
    names = register_names(m)
    m["cells"] = {names.get(n, n): c for n, c in m["cells"].items()}
    Path(out).write_text(json.dumps(j))
    return names


def prep(design, variant, dry):
    run = CONFIG["builds"] / design / variant
    d = CONFIG["out"] / "src" / name_of(design, variant)
    print(f"[{'dry' if dry else 'run'}] {d.relative_to(ROOT)} from {run.relative_to(ROOT)}")
    if dry:
        return d.name
    d.mkdir(parents=True, exist_ok=True)
    names = renamed_json(run / f"{design}.json", d / "renamed.json")
    qor_xtime.write_netlist(d / "renamed.json", d / "netlist.edf", dry)
    (d / "top.txt").write_text(design + "\n")
    (d / "mode.txt").write_text("placed\n")
    (d / "constraints.xdc").write_text(next((CONFIG["designs_dir"] / design).glob("*.xdc")).read_text())
    rows, skipped = qor_xtime.placement(run / f"{design}_routed.json")
    rows = [(names.get(n, n), b) for n, b in rows]
    (d / "place.txt").write_text("".join(f"{qor_xtime.tcl_quote(n)} {b}\n" for n, b in rows))
    (d / "place_info.json").write_text(json.dumps({"rows": len(rows), "skipped": skipped, "from": str(run)}) + "\n")
    return d.name


def npr_slacks(log):
    lines = Path(log).read_text(errors="replace").splitlines()
    tail = lines[max(i for i, ln in enumerate(lines) if "Slack histogram" in ln or "Program finished" in ln) - 40:]
    out = {}
    for ln in tail:
        m = CONFIG["npr_line"].search(ln)
        if m:
            out[m.group(1)] = float(m.group(2))
        m = CONFIG["npr_fmax"].search(ln)
        if m:
            out[f"clock {m.group(1)}"] = round(1000 / float(m.group(3)) - 1000 / float(m.group(2)), 3)
    return out


def collect(design, variant):
    viv = CONFIG["vivado_out"] / name_of(design, variant)
    rec = {"design": design, "variant": variant}
    st = viv / "status.txt"
    rec["vivado_status"] = st.read_text().split("\n")[0] if st.exists() else None
    for key, path in (("vivado_on_ours", viv / "pairs.txt"), ("vivado_own", CONFIG["vivado_ref"] / design / "pairs.txt")):
        rec[key] = path.read_text().splitlines() if path.exists() else None
    corners = {}
    for rpt in sorted(viv.glob("*_slow.rpt")) + sorted(viv.glob("*_fast.rpt")):
        m = CONFIG["rpt_slack"].search(rpt.read_text(errors="replace"))
        d = CONFIG["rpt_datapath"].search(rpt.read_text(errors="replace"))
        if m:
            corners[rpt.stem] = {"slack": float(m.group(1)), "datapath": float(d.group(1)) if d else None}
    rec["vivado_on_ours_corners"] = corners
    miss = viv / "place_missed.txt"
    rec["place_missed"] = miss.read_text().splitlines()[:5] if miss.exists() else None
    rec["nextpnr"] = npr_slacks(CONFIG["builds"] / design / variant / "nextpnr.log")
    return rec


def main():
    ap = argparse.ArgumentParser(description="Vivado timing of nextpnr's placement of the XDC test designs, with the "
                                             "same XDC (vivado/build_xdctime.tcl)")
    ap.add_argument("designs", nargs="*")
    ap.add_argument("--variant", default=CONFIG["variant"])
    ap.add_argument("--collect", action="store_true", help="compare Vivado's slacks with nextpnr's")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    designs = a.designs or CONFIG["designs"]
    if a.collect:
        print(json.dumps([collect(d, a.variant) for d in designs], indent=2))
        return
    names = [prep(d, a.variant, dry) for d in designs]
    print("names: " + ",".join(names))


if __name__ == "__main__":
    main()
