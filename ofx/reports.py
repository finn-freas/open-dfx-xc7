import json
import re
from pathlib import Path

CONFIG = {
    "fmax_re": r"Max frequency for clock '([^']+)': ([\d.]+) MHz \((PASS|FAIL) at ([\d.]+) MHz\)",
    "util_re": r"Info:\s+([A-Za-z0-9_]+):\s+(\d+)/\s*(\d+)\s+(\d+)%",
    "keep_zero": ("SLICE_LUTX", "SLICE_FFX", "CARRY4", "RAMB36E1", "RAMB18E1", "DSP48E1", "BUFGCTRL"),
}


def nextpnr_log(d):
    f = Path(d) / "nextpnr.log"
    return f.read_text(errors="replace") if f.exists() else None


def timing(d):
    text = nextpnr_log(d)
    if text is None:
        return None
    clocks = {}
    for clk, f, st, tgt in re.findall(CONFIG["fmax_re"], text):
        clocks[clk] = {"fmax_mhz": float(f), "status": st, "target_mhz": float(tgt)}
    return clocks


def utilization(d):
    text = nextpnr_log(d)
    if text is None or "Device utilisation:" not in text:
        return None
    block = text.rsplit("Device utilisation:", 1)[1]
    out = {}
    for line in block.splitlines()[1:]:
        m = re.search(CONFIG["util_re"], line)
        if not m:
            if out:
                break
            continue
        name, used, total, pct = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        if used or name in CONFIG["keep_zero"]:
            out[name] = {"used": used, "total": total, "pct": pct}
    return out


def build_dirs(root):
    root = Path(root)
    if (root / "nextpnr.log").exists():
        return [root]
    return sorted(p.parent for p in root.glob("*/nextpnr.log"))


def print_timing(dirs):
    bad = 0
    for d in dirs:
        t = timing(d)
        if t is None:
            print(f"{d}: no nextpnr.log (not built yet)")
            continue
        if not t:
            print(f"{d}: no clock constraints reported")
        for clk, v in t.items():
            bad += v["status"] != "PASS"
            print(f"{d.name:24s} {clk:28s} Fmax {v['fmax_mhz']:8.2f} MHz  target {v['target_mhz']:7.2f} MHz  "
                  f"{v['status']}  ({d / 'nextpnr.log'})")
    return bad


def partition_utilization(d, insts):
    """Cells of each reconfigurable partition instance in a build's routed json, by cell type (the counterpart of
    Vivado's report_utilization -pblocks)."""
    f = next(iter(sorted(Path(d).glob("*_routed.json"))), None)
    if f is None or not insts:
        return None
    m = json.loads(f.read_text())
    top = next(v for v in m["modules"].values() if v.get("attributes", {}).get("top"))
    out = {i: {} for i in insts}
    for name, c in top["cells"].items():
        for i in insts:
            if name.startswith(i + "."):
                out[i][c["type"]] = out[i].get(c["type"], 0) + 1
    return out


def print_report(dirs, insts=()):
    for d in dirs:
        u = utilization(d)
        print(f"== {d}")
        if u is None:
            print("   no utilisation in nextpnr.log (not built yet)")
            continue
        for name, v in u.items():
            print(f"   {name:22s} {v['used']:7d} / {v['total']:7d}  {v['pct']:3d}%")
        for clk, v in (timing(d) or {}).items():
            print(f"   clock {clk}: {v['fmax_mhz']:.2f} MHz ({v['status']} at {v['target_mhz']:.2f} MHz)")
        for inst, cells in (partition_utilization(d, insts) or {}).items():
            print(f"   partition {inst}: " + (", ".join(f"{t} {k}" for t, k in sorted(cells.items())) or "no cells"))
        bit = next(iter(sorted(d.glob("*.bit"))), None)
        if bit:
            print(f"   bitstream {bit} ({bit.stat().st_size} bytes)")


def pr_check_summary(checks):
    out = []
    for f in sorted(Path(checks).glob("pr_check_*.json")):
        if f.name == "pr_check_multi.json":
            continue
        r = json.loads(f.read_text())
        ok = not r.get("outside") and not r.get("foreign_words")
        out.append((f, ok, r.get("differing"), len(r.get("inside", [])), len(r.get("outside", []))))
    return out
