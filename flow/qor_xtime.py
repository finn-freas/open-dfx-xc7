import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qor_bench
from build_openxc7 import tool

ROOT = qor_bench.ROOT

CONFIG = {
    "out": ROOT / "build" / "qor" / "xtime",
    "vivado_out": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build"),
    "vivado_tag": "qor_xtime",
    "dry_run": True,
    "skip_types": {"PAD", "IOB33_INBUF_EN", "IOB33_OUTBUF", "IOB33M_INBUF_EN", "IOB33M_OUTBUF", "IOB33S_INBUF_EN",
                   "IOB33S_OUTBUF", "PSEUDO_GND", "PSEUDO_VCC", "BUFGCTRL", "ICAP_ICAP"},
    "carry_suffix": "$split$muxcy0$PACKED_CARRY4$",
}


def name_of(design, period, vname, mode):
    return f"{design}_{qor_bench.ptag(period)}_{vname}_{mode}"


def write_netlist(syn_json, edf, dry):
    if edf.exists():
        return
    cmd = [tool("yosys"), "-q", "-p", f"read_json {syn_json}; delete t:$scopeinfo; write_edif -pvector bra {edf}"]
    print(f"[{'dry' if dry else 'run'}] edif {edf.relative_to(ROOT)}")
    if not dry:
        subprocess.run(cmd, check=True)


CARRY_SPLIT = re.compile(r"\$split\$muxcy\d+\$PACKED_CARRY4\$$")


def placement(routed, netlist_cells=None):
    """nextpnr placement as (cell, BEL) rows for Vivado's place_cell. A CARRY4 loses nextpnr's packing suffix
    ($split$muxcy<N>$PACKED_CARRY4$, any N; flow/qor_suite.py placement_rows); when nextpnr split one netlist CARRY4
    over two sites, the part holding bit 0 (muxcy0) is kept and Vivado places the rest. With netlist_cells, cells
    absent from the synthesized netlist (nextpnr-only feed-through LUTs, duplicates) are skipped too."""
    j = json.loads(Path(routed).read_text())
    m = j["modules"][next(iter(j["modules"]))]
    rows, skipped, seen = [], 0, {}
    for name, c in m["cells"].items():
        bel = c["attributes"].get("NEXTPNR_BEL")
        if not bel or c["type"] in CONFIG["skip_types"] or "/" in name:
            skipped += 1
            continue
        n = CARRY_SPLIT.sub("", name) if c["type"] == "CARRY4" else name
        if netlist_cells is not None and n not in netlist_cells:
            skipped += 1
            continue
        if n in seen:
            skipped += 1
            if "$muxcy0$" in name:
                rows[seen[n]] = (n, bel)
            continue
        seen[n] = len(rows)
        rows.append((n, bel))
    return rows, skipped


def tcl_quote(s):
    return "{" + s + "}"


def crit_paths(report):
    r = json.loads(Path(report).read_text())
    out = []
    for cp in r.get("critical_paths", []):
        segs = cp.get("path", [])
        if not segs:
            continue
        body = [s for s in segs if s.get("type") != "clk-skew"]
        src, dst = body[0].get("from", {}), body[-1].get("to", {})
        out.append((cp.get("from"), cp.get("to"), (src.get("cell"), src.get("port")), (dst.get("cell"), dst.get("port")),
                    sum(s.get("delay", 0) for s in segs)))
    return out


def prep(design, period, vname, seed, dry):
    period_dir = qor_bench.CONFIG["out"] / "src" / f"{design}_{qor_bench.ptag(period)}"
    run = qor_bench.CONFIG["out"] / "oxc7" / vname / f"{design}_{qor_bench.ptag(period)}" / f"s{seed}"
    st = json.loads((run / "status.json").read_text())
    syn_json = Path(st["cmd"][st["cmd"].index("--json") + 1])
    top = qor_bench.CONFIG["designs"][design]["top"]
    made = []
    for mode in ("free", "placed"):
        d = CONFIG["out"] / "src" / name_of(design, period, vname, mode)
        if not dry:
            d.mkdir(parents=True, exist_ok=True)
        write_netlist(syn_json, d / "netlist.edf", dry)
        if dry:
            made.append(d.name)
            continue
        (d / "top.txt").write_text(top + "\n")
        (d / "mode.txt").write_text(mode + "\n")
        (d / "constraints.xdc").write_text((period_dir / "constraints.xdc").read_text())
        paths = crit_paths(run / "report.json")
        (d / "paths.txt").write_text("".join(f"{tcl_quote(a[0])} {a[1]} {tcl_quote(b[0])} {b[1]} {dly:.3f}\n"
                                             for _, _, a, b, dly in paths))
        if mode == "placed":
            rows, skipped = placement(run / f"{top}_routed.json")
            (d / "place.txt").write_text("".join(f"{tcl_quote(n)} {b}\n" for n, b in rows))
            (d / "place_info.json").write_text(json.dumps({"rows": len(rows), "skipped": skipped, "from": str(run)}) + "\n")
        made.append(d.name)
    return made


def main():
    ap = argparse.ArgumentParser(description="Vivado timing of openXC7 results: the yosys netlist placed and routed by "
                                             "Vivado (free), and the same netlist with nextpnr's placement (placed)")
    ap.add_argument("--designs", nargs="+", default=["rv_soc", "rv_mul", "bram"])
    ap.add_argument("--periods", nargs="+", type=float, default=[5])
    ap.add_argument("--variant", default="tmg")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    names = []
    for d in a.designs:
        for p in a.periods:
            names += prep(d, p, a.variant, a.seed, dry)
    print("names: " + " ".join(names))


if __name__ == "__main__":
    main()
