import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "yosys": ROOT / "toolchain/oss-cad-suite/bin/yosys",
    "plugin": ROOT / "build/yosys-plugin/clkbufmap_gapfix.so",
    "min_bits": 1025,
    "out": ROOT / "build/qor/synx/blockrule",
    "dry_run": True,
}


def run(cmd, log):
    with open(log, "w") as f:
        return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT).returncode


def mems(dump):
    res, cur, style = [], None, False
    for ln in dump.splitlines():
        if re.match(r"\s*attribute \\ram_style", ln):
            style = True
            continue
        m = re.match(r"\s*cell \$mem_v2 (\S+)(?:\s+#\s+(\S+))?", ln)
        if m:
            cur = {"cell": (m.group(2) or m.group(1)).lstrip("\\"), "has_style": style}
            style = False
            res.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"\s*parameter \\(MEMID|SIZE|WIDTH|RD_CLK_ENABLE|RD_PORTS) (.*)", ln)
        if m:
            cur[m.group(1)] = m.group(2).strip()
    return res


def main():
    ap = argparse.ArgumentParser(description="synth_xilinx with a Vivado-like block-RAM rule for synchronous memories")
    ap.add_argument("src_dir")
    ap.add_argument("--min-bits", type=int, default=CONFIG["min_bits"])
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    src = ROOT / a.src_dir
    top = (src / "top.txt").read_text().split()[0]
    rtl = [src / f"{top}.v", *sorted(p for p in src.glob("*.v") if p.name != f"{top}.v")]
    out = CONFIG["out"] / src.name
    sx = f"synth_xilinx -flatten -abc9 -arch xc7 -top {top}"
    if CONFIG["dry_run"] and not a.run:
        print(f"[dry] {src} -> {out}, min_bits {a.min_bits}")
        return
    out.mkdir(parents=True, exist_ok=True)
    il = out / "pre_mem.il"
    ys1 = f"read_verilog -sv {' '.join(map(str, rtl))}; {sx} -run :map_memory; select -module {top}; write_rtlil -selected {il}; select -clear; tee -q -o {out / 'mems.txt'} dump t:$mem_v2"
    assert run([str(CONFIG["yosys"]), "-m", str(CONFIG["plugin"]), "-p", ys1], out / "pass1.log") == 0
    chosen = []
    for m in mems((out / "mems.txt").read_text()):
        bits = int(m["SIZE"]) * int(m["WIDTH"])
        rd_sync = m.get("RD_CLK_ENABLE", "")
        sync = rd_sync and set(rd_sync.split("'")[-1]) == {"1"}
        if sync and bits >= a.min_bits and not m.get("has_style"):
            chosen.append((m["cell"], m["MEMID"], bits))
    sel = " ".join(f"{top}/{c}" for c, _, _ in chosen)
    setattr_cmd = f"setattr -set ram_style \"block\" {sel}; " if chosen else ""
    rd = f"read_verilog -sv {' '.join(map(str, rtl))}"
    litex = any(k in src.parts for k in ("ddr3", "eth"))
    tail = (f"{sx} -run map_memory:finalize; clkbufmap_gapfix -buf BUFG O:I; clean; {sx} -run check:" if litex
            else f"{sx} -run map_memory:")
    ys2 = (f"{rd}; {sx} -run :map_memory; {setattr_cmd}{tail}; tee -q -o {out / 'stat.txt'} stat -tech xilinx; "
           f"write_json {out / (top + '.json')}")
    assert run([str(CONFIG["yosys"]), "-m", str(CONFIG["plugin"]), "-p", ys2], out / "pass2.log") == 0
    (out / "chosen.txt").write_text("".join(f"{mid} {bits}\n" for _, mid, bits in chosen))
    print("block:", ", ".join(f"{mid} ({bits} bits)" for _, mid, bits in chosen))


if __name__ == "__main__":
    main()
