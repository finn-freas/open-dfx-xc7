#!/usr/bin/env python3
"""Bambu vs Vitis HLS on equal terms (docs/hls.md).

Each tool's kernel RTL (<eval>/<tool>/<kernel>/rtl/*.v) is put in the same wrapper: every kernel input bit comes
from a shift register fed by one pin, every output bit is XORed into a second shift register that drives one pin.
All kernel ports are then register to register, and the design fits the pins of any package. The wrapper is
implemented with ofx (our flow) and with Vivado; the kernel's own resources come from yosys synth_xilinx of the
kernel alone (our flow) and from Vivado's hierarchical utilization of the kernel instance.

  hls_compare.py ours TOOL KERNEL...     wrap and build with `ofx build --run`, write <eval>/impl/TOOL_KERNEL/result.json
  hls_compare.py vivado-prep DIR         copy every wrapped design into DIR (for flow/hls_vivado.sh)
  hls_compare.py table                   collate the results into a markdown table
"""
import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "eval": Path(os.environ.get("HLS_EVAL", ROOT / "build" / "hls_eval")),
    "yosys": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "yosys",
    "ofx": ROOT / "bin" / "ofx",
    "board": "arty-a7-35t",
    "pins": {"clk": "E3", "sin": "A9", "sout": "H5"},
    "clock_ns": 10.0,
    "clock_names": ("clock", "ap_clk", "clk"),
    "kernel_synth": "synth_xilinx -flatten -abc9 -arch xc7 -noiopad -noclkbuf -top {top}",
    "tools": ("bambu", "vitis"),
    "kernels": ("fir", "matmul", "crc32", "hist", "dotprod"),
}


def rtl_files(tool, k):
    d = CONFIG["eval"] / tool / k / "rtl"
    return sorted(p for p in d.iterdir() if p.suffix in (".v", ".sv"))


def ports(files, top):
    js = CONFIG["eval"] / "tmp_ports.json"
    js.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(CONFIG["yosys"]), "-q", "-p",
           f"read_verilog -sv -lib {' '.join(str(f) for f in files)}; write_json {js}"]
    subprocess.run(cmd, check=True, cwd=files[0].parent)
    mod = json.loads(js.read_text())["modules"][top]
    js.unlink()
    return [(n, p["direction"], len(p["bits"])) for n, p in mod["ports"].items()]


def wrapper(top, plist):
    clk = [n for n, d, w in plist if d == "input" and n in CONFIG["clock_names"]]
    if len(clk) != 1:
        raise SystemExit(f"{top}: expected one clock port among {CONFIG['clock_names']}, got {clk}")
    ins = [(n, w) for n, d, w in plist if d == "input" and n != clk[0]]
    outs = [(n, w) for n, d, w in plist if d == "output"]
    if any(d == "inout" for _, d, _ in plist):
        raise SystemExit(f"{top}: inout ports are not supported by the wrapper")
    ni = max(1, sum(w for _, w in ins))
    no = max(1, sum(w for _, w in outs))
    conn = [f".{clk[0]}(clk)"]
    i = 0
    for n, w in ins:
        conn.append(f".{n}(isr[{i + w - 1}:{i}])")
        i += w
    o = 0
    for n, w in outs:
        conn.append(f".{n}(kout[{o + w - 1}:{o}])")
        o += w
    body = ",\n    ".join(conn)
    return f"""module hlsw_{top} (input wire clk, input wire sin, output wire sout);
  reg [{ni}:0] isr = 0;
  always @(posedge clk) isr <= {{isr[{ni - 1}:0], sin}};
  wire [{no - 1}:0] kout;
  reg [{no}:0] osr = 0;
  always @(posedge clk) osr <= {{osr[{no - 1}:0], 1'b0}} ^ {{1'b0, kout}};
  assign sout = osr[{no}];
`ifdef HLSW_KEEP
  (* keep_hierarchy = "yes" *)
`endif
  {top} u_k (
    {body}
  );
endmodule
""", {"in_bits": ni, "out_bits": no}


def xdc():
    p = CONFIG["pins"]
    lines = [f"set_property -dict {{PACKAGE_PIN {p[n]} IOSTANDARD LVCMOS33}} [get_ports {n}]" for n in ("clk", "sin", "sout")]
    lines.append(f"create_clock -name clk -period {CONFIG['clock_ns']:.3f} [get_ports clk]")
    return "\n".join(lines) + "\n"


def wrap(tool, k):
    files = rtl_files(tool, k)
    d = CONFIG["eval"] / "impl" / f"{tool}_{k}"
    (d / "src").mkdir(parents=True, exist_ok=True)
    (d / "constraints").mkdir(parents=True, exist_ok=True)
    for f in files:
        (d / "src" / f.name).write_bytes(f.read_bytes())
    for f in (CONFIG["eval"] / tool / k / "rtl").glob("*.dat"):
        (d / "src" / f.name).write_bytes(f.read_bytes())
    text, info = wrapper(k, ports(files, k))
    (d / "src" / f"hlsw_{k}.v").write_text(text)
    (d / "constraints" / "hlsw.xdc").write_text(xdc())
    srcs = [f"src/{f.name}" for f in files] + [f"src/hlsw_{k}.v"]
    (d / "ofx.toml").write_text(
        f'[project]\nname = "hlsw_{k}"\ntop = "hlsw_{k}"\nboard = "{CONFIG["board"]}"\n'
        f"sources = {json.dumps(srcs)}\nconstraints = [\"constraints/hlsw.xdc\"]\nseed = 1\n\n"
        f"[clocks]\nclk = {CONFIG['clock_ns']}\n")
    (d / "wrap.json").write_text(json.dumps(info) + "\n")
    return d, files, info


CELL_CLASSES = [
    ("LUT", r"^LUT[1-6]$"), ("FF", r"^FD[CPRSE]E?$"), ("DSP", r"^DSP48E1$"), ("RAMB36", r"^RAMB36E1$"),
    ("RAMB18", r"^RAMB18E1$"), ("LUTRAM", r"^RAM(32M|32X1[SD]|64M|64X1[SD]|128X1[SD]|256X1S)$"),
    ("SRL", r"^SRLC?(16E|32E)$"), ("CARRY4", r"^CARRY4$"), ("MUXF", r"^MUXF[78]$"),
]


def classify(counts):
    out = {c: 0 for c, _ in CELL_CLASSES}
    for cell, n in counts.items():
        for c, pat in CELL_CLASSES:
            if re.match(pat, cell):
                out[c] += n
    out["BRAM36"] = out["RAMB36"] + out["RAMB18"] / 2
    return out


def kernel_stat(files, top, out_dir):
    js = out_dir / "kernel_stat.json"
    ys = f"read_verilog -sv {' '.join(str(f) for f in files)}; {CONFIG['kernel_synth'].format(top=top)}; tee -o {js} stat -json"
    subprocess.run([str(CONFIG["yosys"]), "-q", "-l", str(out_dir / "kernel_synth.log"), "-p", ys], check=True,
                   cwd=files[0].parent, stdout=subprocess.DEVNULL)
    txt = js.read_text()
    data = json.loads(txt[txt.index("{"):])
    cells = data.get("design", {}).get("num_cells_by_type") or data["modules"][f"\\{top}"]["num_cells_by_type"]
    return classify(cells)


def nextpnr_results(impl):
    log = (impl / "nextpnr.log").read_text(errors="replace")
    fmax = re.findall(r"Max frequency for clock\s+'?([^':]+)'?:\s+([\d.]+) MHz", log)
    util = {}
    blk = log[log.rfind("Device utilisation"):] if "Device utilisation" in log else ""
    for m in re.finditer(r"^\S*\s*(\w+):\s+(\d+)/\s*(\d+)", blk, re.M):
        util.setdefault(m.group(1), int(m.group(2)))
    return {"fmax_mhz": float(fmax[-1][1]) if fmax else None, "nextpnr_util": util}


def cmd_ours(a):
    for k in a.kernels:
        d, files, info = wrap(a.tool, k)
        r = {"tool": a.tool, "kernel": k, **info}
        r["kernel_synth"] = kernel_stat(files, k, d)
        env = dict(os.environ)
        log = d / "ofx_build.log"
        with open(log, "w") as f:
            rc = subprocess.run([sys.executable, str(CONFIG["ofx"]), "build", "--run"], cwd=d, stdout=f,
                                stderr=subprocess.STDOUT, env=env).returncode
        r["ofx_rc"] = rc
        impl = d / "build" / "impl"
        if (impl / "nextpnr.log").exists():
            r.update(nextpnr_results(impl))
        r["bitstream"] = (impl / f"hlsw_{k}.bit").exists()
        (d / "result.json").write_text(json.dumps(r, indent=1) + "\n")
        print(json.dumps({x: r.get(x) for x in ("tool", "kernel", "ofx_rc", "fmax_mhz", "bitstream")}),
              json.dumps(r["kernel_synth"]), flush=True)


def cmd_bambu(a):
    sys.path.insert(0, str(ROOT))
    from ofx import hls
    for k in a.kernels:
        src = ROOT / "designs" / "hls" / k
        spec = {"top": k, "sources": [src / f"{k}.c"], "testbench": src / "tb.c", "include": [src],
                "clock_ns": CONFIG["clock_ns"], "device": hls.CONFIG["devices"]["artix7"], "args": a.args}
        out = CONFIG["eval"] / "bambu" / k
        (out / "rtl").mkdir(parents=True, exist_ok=True)
        rc = hls.run_bambu(spec, out / "work", hls.command(spec), out / "bambu.log")
        gen = out / "work" / f"{k}.v"
        if rc == 0 and gen.exists():
            (out / "rtl" / f"{k}.v").write_text(gen.read_text())
        src_rc = hls.run_bambu(spec, out / "sim", hls.command(spec, tb=spec["testbench"]), out / "sim.log")
        sim = (out / "sim.log").read_text(errors="replace")
        lat = {"rc": rc, "sim_rc": src_rc, "cycles": hls.cycles(sim)}
        (out / "latency.json").write_text(json.dumps(lat) + "\n")
        print(k, json.dumps(lat), flush=True)


def cmd_vivado_prep(a):
    dst = Path(a.dir)
    names = []
    for t in CONFIG["tools"]:
        for k in CONFIG["kernels"]:
            src = CONFIG["eval"] / "impl" / f"{t}_{k}"
            if not (src / "ofx.toml").exists():
                continue
            o = dst / f"{t}_{k}"
            o.mkdir(parents=True, exist_ok=True)
            for f in (src / "src").iterdir():
                (o / f.name).write_bytes(f.read_bytes())
            (o / "hlsw.xdc").write_bytes((src / "constraints" / "hlsw.xdc").read_bytes())
            (o / "top.txt").write_text(f"hlsw_{k} {k}\n")
            names.append(o.name)
    (dst / "designs.txt").write_text("\n".join(names) + "\n")
    print(" ".join(names))


def hier_util(rpt):
    """Rows of Vivado's report_utilization -hierarchical as {instance: {column: value}}."""
    if not rpt.exists():
        return {}
    head, rows = None, {}
    for line in rpt.read_text(errors="replace").splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if cols and cols[0] == "Instance":
            head = cols
            continue
        if head and len(cols) == len(head):
            rows[cols[0]] = dict(zip(head, cols))
    return rows


def cmd_vivado_collect(a):
    vd = CONFIG["eval"] / "vivado"
    res = {}
    for d in sorted(p for p in vd.iterdir() if p.is_dir()):
        st = (d / "status.txt").read_text().strip() if (d / "status.txt").exists() else "missing"
        r = {"status": st}
        m = re.search(r"wns\s+(-?[\d.]+)", (d / "result.txt").read_text()) if (d / "result.txt").exists() else None
        if m:
            wns = float(m.group(1))
            r["wns_ns"] = wns
            r["fmax_mhz"] = round(1000.0 / (CONFIG["clock_ns"] - wns), 1)
        for tag, f in (("impl", "util_hier.rpt"), ("synth", "util_hier_synth.rpt")):
            rows = hier_util(d / f)
            k = next((v for n, v in rows.items() if n.strip() == "u_k"), None)
            if k:
                r[f"kernel_{tag}"] = {"LUT": int(k.get("Total LUTs", 0)), "LUTRAM": int(k.get("LUTRAMs", 0)),
                                      "SRL": int(k.get("SRLs", 0)), "FF": int(k.get("FFs", 0)),
                                      "BRAM36": float(k.get("RAMB36", 0)) + float(k.get("RAMB18", 0)) / 2,
                                      "DSP": int(k.get("DSP Blocks", 0))}
        kc = d / "kcells.txt"
        if kc.exists():
            cells = {}
            for line in kc.read_text().splitlines():
                if line.strip():
                    n, c = line.split()
                    cells[n] = int(c)
            r["kernel_cells"] = classify(cells)
        res[d.name] = r
    (vd / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))


def bambu_latency(k):
    d = CONFIG["eval"] / "bambu" / k
    f = d / "latency.json"
    return json.loads(f.read_text()) if f.exists() else {}


def vitis_latency(k):
    d = CONFIG["eval"] / "vitis" / k
    out = {}
    x = d / f"{k}_csynth.xml"
    if x.exists():
        r = ET.parse(x).getroot()
        pe = r.find("PerformanceEstimates/SummaryOfOverallLatency")
        if pe is not None:
            out["csynth_min"] = pe.findtext("Best-caseLatency")
            out["csynth_max"] = pe.findtext("Worst-caseLatency")
            out["interval_max"] = pe.findtext("Interval-max")
        est = r.findtext("PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod")
        out["est_clk_ns"] = est
    c = d / f"{k}_cosim.rpt"
    if c.exists():
        m = re.search(r"\|\s*Verilog\|\s*(\w+)\|\s*(\d+)\|\s*(\d+)\|\s*(\d+)\|", c.read_text())
        if m:
            out["cosim_status"] = m.group(1)
            out["cosim_min"], out["cosim_avg"], out["cosim_max"] = m.group(2), m.group(3), m.group(4)
    return out


def load_json(p):
    return json.loads(p.read_text()) if p.exists() else {}


def cmd_table(a):
    viv = load_json(CONFIG["eval"] / "vivado" / "results.json")
    rows = []
    for k in CONFIG["kernels"]:
        for t in CONFIG["tools"]:
            r = load_json(CONFIG["eval"] / "impl" / f"{t}_{k}" / "result.json")
            if not r:
                continue
            lat = bambu_latency(k) if t == "bambu" else vitis_latency(k)
            ks = r.get("kernel_synth", {})
            v = viv.get(f"{t}_{k}", {})
            xt = CONFIG["eval"] / "xtime" / "out" / f"{t}_{k}_placed" / "timing.rpt"
            xf = None
            if xt.exists():
                m = re.search(r"WNS\(ns\).*\n.*\n\s*(-?[\d.]+)", xt.read_text())
                if m:
                    xf = round(1000.0 / (CONFIG["clock_ns"] - float(m.group(1))), 1)
            rows.append({"kernel": k, "tool": t, "lat": lat, "ks": ks, "fmax": r.get("fmax_mhz"), "viv": v,
                         "bit": r.get("bitstream"), "xtime_fmax": xf})
    (CONFIG["eval"] / "table.json").write_text(json.dumps(rows, indent=1) + "\n")
    res = lambda d: (f"{d.get('LUT', '-')} / {d.get('FF', '-')} / {d.get('DSP', '-')} / {d.get('BRAM36', '-'):g}"
                     if d else "-")
    print("| kernel | tool | latency (cycles) | ofx (yosys) LUT / FF / DSP / BRAM36 | Fmax ofx, nextpnr timer | "
          "Fmax ofx placement, Vivado timer | Vivado LUT / FF / DSP / BRAM36 | Fmax Vivado |")
    print("|---|---|---|---|---|---|---|---|")
    for x in rows:
        lat = x["lat"]
        if x["tool"] == "vitis":
            ls = f"{lat.get('cosim_max', '?')} (csynth {lat.get('csynth_max', '?')})"
        else:
            ls = f"{lat.get('cycles', '?')}" + ("" if lat.get("sim_rc") == 0 else " (sim FAIL)")
        print(f"| {x['kernel']} | {'Bambu' if x['tool'] == 'bambu' else 'Vitis HLS'} | {ls} | {res(x['ks'])} | "
              f"{x['fmax'] if x['fmax'] else '-'} | {x['xtime_fmax'] or '-'} | {res(x['viv'].get('kernel_cells') or x['viv'].get('kernel_impl', {}))} | "
              f"{x['viv'].get('fmax_mhz', '-')} |")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("ours")
    o.add_argument("tool", choices=CONFIG["tools"])
    o.add_argument("kernels", nargs="+")
    o.set_defaults(fn=cmd_ours)
    b = sub.add_parser("bambu")
    b.add_argument("kernels", nargs="+")
    b.add_argument("--args", nargs="*", default=[])
    b.set_defaults(fn=cmd_bambu)
    v = sub.add_parser("vivado-prep")
    v.add_argument("dir")
    v.set_defaults(fn=cmd_vivado_prep)
    sub.add_parser("vivado-collect").set_defaults(fn=cmd_vivado_collect)
    t = sub.add_parser("table")
    t.set_defaults(fn=cmd_table)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
