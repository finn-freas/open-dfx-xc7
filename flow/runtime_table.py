import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "runs": ROOT / "build" / "runtime",
    "vivado": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/runtime"),
    "designs": ["blinky", "rv_soc", "litex_ddr3", "mc12_a100"],
    "main_clock": {"blinky": None, "rv_soc": "u_bridge.clk", "litex_ddr3": "sys_clk", "mc12_a100": "g_core[0].u_core.clk"},
    "rows": [
        ("synthesis", "yosys", "read+synth"),
        ("P&R start: chipdb, netlist, pack", "pnr_setup", "opt"),
        ("placement (incl. delay matrix)", "place", "place"),
        ("routing (incl. final timing, FASM)", "route", "route"),
        ("bitstream (fasm2frames + xc7frames2bit)", "bitstream", "bitstream"),
        ("flow overhead (Python / Vivado start+exit)", "overhead", "overhead"),
        ("total", "total", "process_wall"),
    ],
}


def open_vals(d):
    ph = d.get("nextpnr_phases", {})
    st = d["stages"]
    proc = d.get("nextpnr_proc", {})
    wait = max(0.0, st.get("nextpnr", 0) - proc.get("wall", 0))
    v = {
        "yosys": st.get("yosys"),
        "pnr_setup": (ph.get("startup+chipdb+json") or 0) + (ph.get("pack") or 0),
        "place": ph.get("place"),
        "route": (ph.get("route") or 0) + (ph.get("post-route timing+fasm") or 0),
        "bitstream": st.get("fasm2frames", 0) + st.get("xc7frames2bit", 0),
        "total": d["wall"] - wait,
        "pnr_cpu": proc.get("user", 0) + proc.get("sys", 0),
        "load": d["load_before"]["load1"],
        "fmax": ph.get("fmax", {}),
    }
    v["overhead"] = v["total"] - sum(v[k] or 0 for k in ("yosys", "pnr_setup", "place", "route", "bitstream"))
    return v


def vivado_vals(f):
    t = {}
    for ln in Path(f).read_text().splitlines():
        k, _, val = ln.partition(" ")
        try:
            t[k] = float(val.replace(",", ""))
        except ValueError:
            pass
    if "read" in t and "synth" in t:
        t["read+synth"] = t["read"] + t["synth"]
    steps = sum(t.get(k, 0) for k in ("read", "synth", "opt", "place", "route", "bitstream"))
    if "process_wall" in t:
        t["overhead"] = t["process_wall"] - steps
    return t


def cell(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    if not xs:
        return "-"
    m = statistics.median(xs)
    if len(xs) == 1:
        return f"{m:.1f} (n=1)"
    return f"{m:.1f} ({min(xs):.1f}-{max(xs):.1f}, n={len(xs)})"


def runs(variant, design):
    out = []
    for p in sorted((CONFIG["runs"] / variant / design).glob("r*/runtime.json")):
        d = json.loads(p.read_text())
        if d["rc"] == 0 and "nextpnr_proc" in d:
            out.append(open_vals(d))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default="base")
    ap.add_argument("--after", default="dmc")
    ap.add_argument("--extra", nargs="*", default=["exitbb", "pr_t4", "static"])
    a = ap.parse_args()
    for design in CONFIG["designs"]:
        b, f = runs(a.before, design), runs(a.after, design)
        vv = []
        for p in sorted((CONFIG["vivado"] / design).glob("r*/times.txt")):
            v = vivado_vals(p)
            rep = p.parent.name
            log = CONFIG["runs"] / f"vivado_{rep}.log"
            if log.exists():
                for ln in log.read_text().splitlines():
                    w = ln.split()
                    if len(w) > 5 and w[0] == design and w[1] == rep and w[2] == "start":
                        v["load1"] = float(w[5])
            if "process_wall" in v:
                vv.append(v)
        print(f"\n### {design}\n")
        print(f"| stage | open flow, before ({a.before}) | open flow, after ({a.after}) | Vivado 2025.2 | Vivado step |")
        print("|---|---|---|---|---|")
        for label, k, vk in CONFIG["rows"]:
            print(f"| {label} | {cell([r[k] for r in b])} | {cell([r[k] for r in f])} | {cell([v.get(vk) for v in vv])} | {vk} |")
        print(f"| nextpnr CPU (user+sys) | {cell([r['pnr_cpu'] for r in b])} | {cell([r['pnr_cpu'] for r in f])} | | |")
        print(f"| load average at start | {cell([r['load'] for r in b])} | {cell([r['load'] for r in f])} | {cell([v.get('load1') for v in vv])} | |")
        clk = CONFIG["main_clock"][design]
        if clk:
            print(f"| Fmax {clk}, MHz (nextpnr timer) | {cell([r['fmax'].get(clk) for r in b])} | {cell([r['fmax'].get(clk) for r in f])} | | |")
        ex = [(e, runs(e, design)) for e in a.extra]
        ex = [(e, r) for e, r in ex if r]
        if ex:
            print(f"\nOpt-in trade-offs, {design}:\n")
            print("| variant | placement | routing | total | nextpnr CPU | Fmax (nextpnr timer) | load |")
            print("|---|---|---|---|---|---|---|")
            for e, rr in ex:
                fm = cell([r["fmax"].get(clk) for r in rr]) if clk else "-"
                print(f"| {e} | {cell([r['place'] for r in rr])} | {cell([r['route'] for r in rr])} | {cell([r['total'] for r in rr])} | "
                      f"{cell([r['pnr_cpu'] for r in rr])} | {fm} | {cell([r['load'] for r in rr])} |")


if __name__ == "__main__":
    main()
