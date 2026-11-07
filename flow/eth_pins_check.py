import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ddr_pins_check as dp

ROOT = dp.ROOT

CONFIG = {
    "xdcs": [ROOT / "designs" / "eth" / n / "digilent_arty.xdc" for n in ("arty_eth", "arty_scope")],
    "master_xdc": dp.CONFIG["master_xdc"],
    "out": ROOT / "build" / "eth" / "pins_check.json",
    "litex_to_master": [
        (r"eth_clocks_tx", "eth_tx_clk"), (r"eth_clocks_rx", "eth_rx_clk"), (r"eth_rst_n", "eth_rstn"),
        (r"eth_(mdio|mdc|rx_dv|col|crs|tx_en|ref_clk)", r"eth_\1"), (r"eth_rx_er", "eth_rxerr"),
        (r"eth_rx_data\[(\d)\]", r"eth_rxd[\1]"), (r"eth_tx_data\[(\d)\]", r"eth_txd[\1]"),
        (r"clk100", "CLK100MHZ"), (r"cpu_reset_n", "ck_rst"), (r"serial_tx", "uart_rxd_out"),
        (r"serial_rx", "uart_txd_in"), (r"user_led(\d)", r"led[\1]"),
    ],
}


def check(xdc, master):
    rows, bad = [], 0
    for port, a in sorted(dp.xdc_ports(xdc).items()):
        ref_name = next((re.sub(p, r, port) for p, r in CONFIG["litex_to_master"] if re.fullmatch(p, port)), None)
        ref = master.get(ref_name) if ref_name else None
        ok = None if ref is None else (ref["LOC"] == a.get("LOC") and ref.get("IOSTANDARD") == a.get("IOSTANDARD"))
        bad += ok is False
        rows.append({"port": port, "ours": a, "master": ref_name, "ref": ref, "ok": ok})
    return rows, bad


def main():
    master = dp.xdc_ports(CONFIG["master_xdc"])
    eth_master = sorted(k for k in master if k.startswith("eth_"))
    res, rc = {"master_xdc": str(CONFIG["master_xdc"].relative_to(ROOT)), "master_eth_ports": eth_master}, 0
    for xdc in CONFIG["xdcs"]:
        rows, bad = check(xdc, master)
        covered = {r["master"] for r in rows if r["ok"] is not None}
        rec = {"checked": sum(r["ok"] is not None for r in rows), "mismatch": bad,
               "unchecked": [r["port"] for r in rows if r["ok"] is None],
               "master_eth_not_in_ours": sorted(set(eth_master) - covered), "rows": rows}
        res[str(xdc.relative_to(ROOT))] = rec
        rc |= bool(bad)
        print(f"{xdc.relative_to(ROOT)}: checked {rec['checked']} ports, {bad} mismatches; master eth ports not used: "
              f"{rec['master_eth_not_in_ours']}; unchecked: {rec['unchecked']}")
        for r in rows:
            if r["ok"] is False:
                print("MISMATCH", r)
    CONFIG["out"].parent.mkdir(parents=True, exist_ok=True)
    CONFIG["out"].write_text(json.dumps(res, indent=1) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())
