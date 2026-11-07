import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "toolchain" / "litex" / "ref"

CONFIG = {
    "xdc": ROOT / "designs" / "ddr3" / "arty_ddr3" / "digilent_arty.xdc",
    "mig_prj": REF / "vivado-boards" / "new" / "board_files" / "arty-a7-35" / "E.0" / "1.1" / "mig.prj",
    "master_xdc": REF / "digilent-xdc" / "Arty-A7-35-Master.xdc",
    "out": ROOT / "build" / "ddr3" / "pins_check.json",
    "litex_to_mig": [
        (r"ddram_a\[(\d+)\]", r"ddr3_addr[\1]"), (r"ddram_ba\[(\d+)\]", r"ddr3_ba[\1]"),
        (r"ddram_dq\[(\d+)\]", r"ddr3_dq[\1]"), (r"ddram_dm\[(\d+)\]", r"ddr3_dm[\1]"),
        (r"ddram_dqs_p\[(\d+)\]", r"ddr3_dqs_p[\1]"), (r"ddram_dqs_n\[(\d+)\]", r"ddr3_dqs_n[\1]"),
        (r"ddram_clk_p", "ddr3_ck_p[0]"), (r"ddram_clk_n", "ddr3_ck_n[0]"),
        (r"ddram_(ras_n|cas_n|we_n|reset_n)", r"ddr3_\1"), (r"ddram_(cs_n|cke|odt)", r"ddr3_\1[0]"),
    ],
    "litex_to_master": {"clk100": "CLK100MHZ", "cpu_reset_n": "ck_rst", "serial_tx": "uart_rxd_out",
                        "serial_rx": "uart_txd_in", "user_led0": "led[0]", "user_led1": "led[1]",
                        "user_led2": "led[2]", "user_led3": "led[3]", "eth_ref_clk": "eth_ref_clk"},
}


def xdc_ports(path):
    ports = {}
    for ln in path.read_text().splitlines():
        s = ln.lstrip("#")
        for m in re.finditer(r"(PACKAGE_PIN|LOC|IOSTANDARD|SLEW|IN_TERM)\s+(\S+)", s.split("[get_ports")[0]):
            p = re.search(r"get_ports\s*\{\s*([^}\s]+)\s*\}", s)
            if p:
                key = "LOC" if m.group(1) == "PACKAGE_PIN" else m.group(1)
                ports.setdefault(p.group(1), {})[key] = m.group(2)
    return ports


def main():
    ours = xdc_ports(CONFIG["xdc"])
    mig = {p.get("name"): {"LOC": p.get("PADName"), "IOSTANDARD": p.get("IOSTANDARD")}
           for p in ET.parse(CONFIG["mig_prj"]).getroot().iter("Pin") if p.get("IOSTANDARD")}
    master = xdc_ports(CONFIG["master_xdc"])
    rows, bad = [], 0
    for port, a in sorted(ours.items()):
        ref, src = None, None
        for pat, rep in CONFIG["litex_to_mig"]:
            if re.fullmatch(pat, port):
                ref, src = mig.get(re.sub(pat, rep, port)), "mig.prj " + re.sub(pat, rep, port)
                break
        if ref is None and port in CONFIG["litex_to_master"]:
            ref, src = master.get(CONFIG["litex_to_master"][port]), "master " + CONFIG["litex_to_master"][port]
        if ref is None:
            rows.append({"port": port, "ours": a, "ref": None, "ok": None})
            continue
        ok = ref["LOC"] == a.get("LOC") and ref.get("IOSTANDARD") == a.get("IOSTANDARD")
        bad += not ok
        rows.append({"port": port, "ours": a, "ref": ref, "src": src, "ok": ok})
    ddr_mig = {n for n in mig}
    covered = {r["src"].split(" ", 1)[1] for r in rows if r.get("src", "").startswith("mig.prj")}
    res = {"checked": sum(r["ok"] is not None for r in rows), "mismatch": bad,
           "unchecked": [r["port"] for r in rows if r["ok"] is None],
           "mig_pins": len(ddr_mig), "mig_pins_not_in_ours": sorted(ddr_mig - covered), "rows": rows,
           "sources": {k: str(CONFIG[k].relative_to(ROOT)) for k in ("xdc", "mig_prj", "master_xdc")}}
    CONFIG["out"].parent.mkdir(parents=True, exist_ok=True)
    CONFIG["out"].write_text(json.dumps(res, indent=1) + "\n")
    print(f"checked {res['checked']} ports, {bad} mismatches; MIG pins {len(ddr_mig)}, not in ours: "
          f"{res['mig_pins_not_in_ours']}; unchecked: {res['unchecked']}")
    for r in rows:
        if r["ok"] is False:
            print("MISMATCH", r)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
