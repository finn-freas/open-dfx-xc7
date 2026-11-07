import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "open": "build/xdc",
    "vivado": Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/xdc"),
    "variants": ("base", "xdc", "xdc2"),
    "io_feature": re.compile(r"^[LR]IOB33\S*\.IOB_Y\d\.\S+|^[LR]IOI3\S*\.(?:OLOGIC|ILOGIC)_Y\d\.\S*(?:FF|OQUSED|ZINV_D|IFF)\S*"),
    "wns": re.compile(r"^\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)"),
    "package_pins": "toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7/xc7a35tcsg324-1/package_pins.csv",
    "tabbypy": "toolchain/openxc7/libexec/tabbypy3",
    "dry_run": True,
}

ROOT = CONFIG["root"]


def vivado(name):
    d = CONFIG["vivado"] / name
    rec = {"dir": str(d)}
    st = d / "status.txt"
    if not st.exists():
        return rec
    rec["status"] = st.read_text().strip().splitlines()[0]
    tr = d / "timing.rpt"
    if tr.exists():
        lines = tr.read_text(errors="replace").splitlines()
        for i, ln in enumerate(lines):
            if "WNS(ns)" in ln and "TNS(ns)" in ln:
                for nxt in lines[i + 1:i + 4]:
                    m = CONFIG["wns"].match(nxt)
                    if m:
                        rec["wns"], rec["whs"] = float(m.group(1)), float(m.group(5))
                        rec["failing_setup_endpoints"] = int(m.group(3))
                        break
                break
    pf = d / "pairs.txt"
    if pf.exists():
        rec["pairs"] = pf.read_text().strip().splitlines()
    sc = d / "synth_cells.txt"
    if sc.exists():
        kinds = {}
        for ln in sc.read_text().splitlines():
            kinds[ln.split()[0]] = kinds.get(ln.split()[0], 0) + 1
        rec["synth_cells"] = kinds
    return rec


def decode(bit, out):
    if out.exists() or not bit.exists():
        return out if out.exists() else None
    subprocess.run([str(ROOT / CONFIG["tabbypy"]), str(ROOT / "flow" / "bit2fasm.py"), str(bit), str(out)], cwd=ROOT,
                   capture_output=True)
    return out if out.exists() else None


def io_features(fasm):
    if fasm is None:
        return None
    return sorted(ln.strip() for ln in fasm.read_text().splitlines() if CONFIG["io_feature"].match(ln.strip()))


def port_sites(name):
    pins = {}
    for ln in (ROOT / "designs" / "xdc" / name / f"{name}.xdc").read_text().split("\n"):
        m = re.search(r"PACKAGE_PIN\s+(\w+).*\[get_ports\s+(\{[^}]+\}|[^\s\]]+)\]", ln)
        if m:
            pins[m.group(2).strip("{}").strip()] = m.group(1)
    csv = ROOT / CONFIG["package_pins"]
    rows = {r.split(",")[0]: r.split(",") for r in csv.read_text().splitlines()[1:]}
    sites = {}
    for port, pin in pins.items():
        _, _, site, tile, _ = rows[pin][:5]
        sy, ty = int(site.split("Y")[-1]), int(tile.split("Y")[-1])
        iob = (0 if ty % 50 == 0 else 1) if "SING" in tile else 1 - (sy - ty)
        sites[port] = (tile, f"IOB_Y{iob}")
    return sites


def port_features(name, fasm):
    if fasm is None:
        return None
    lines = fasm.read_text().splitlines()
    out = {}
    for port, (tile, iob) in port_sites(name).items():
        pre = f"{tile}.{iob}."
        out[port] = sorted(ln.strip()[len(pre):] for ln in lines if ln.strip().startswith(pre))
    return out


def main():
    ap = argparse.ArgumentParser(description="XDC coverage: open-flow logs and FASM next to Vivado's reports")
    ap.add_argument("designs", nargs="*")
    ap.add_argument("--fasm", action="store_true", help="also decode the bitstreams and compare I/O features")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    summary = json.loads((ROOT / CONFIG["open"] / "summary.json").read_text())
    names = a.designs or sorted(summary)
    out = {}
    for n in names:
        rec = {"open": summary.get(n, {}), "vivado": vivado(n)}
        if a.fasm and not dry:
            vb = CONFIG["vivado"] / n / f"{n}.bit"
            vf = decode(vb, ROOT / CONFIG["open"] / n / "vivado.fasm")
            rec["io"] = {"vivado": io_features(vf)}
            rec["ports"] = {"vivado": port_features(n, vf)}
            for v in CONFIG["variants"]:
                ob = ROOT / CONFIG["open"] / n / v / f"{n}.bit"
                of = decode(ob, ROOT / CONFIG["open"] / n / v / "decoded.fasm")
                rec["io"][v] = io_features(of)
                rec["ports"][v] = port_features(n, of)
        out[n] = rec
        print(n, json.dumps({"vivado": {k: rec["vivado"].get(k) for k in ("status", "wns", "failing_setup_endpoints")},
                             **{v: rec["open"].get(v, {}).get("fmax") for v in CONFIG["variants"]}}))
    if not dry:
        (ROOT / CONFIG["open"] / "compare.json").write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
