import argparse
import json
import shutil
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "prjxray_db": "toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7",
    "meta_src": "build/chipdb/meta",
    "meta_out": "build/chipdb-prim/meta",
    "draft": "docs/drafts/nextpnr-xilinx-meta-site_type_XADC.json",
    "dry_run": True,
}

ROOT = CONFIG["root"]


def site_type():
    tt = json.loads((ROOT / CONFIG["prjxray_db"] / "tile_type_MONITOR_BOT.json").read_text())
    site = next(s for s in tt["sites"] if s["type"] == "XADC")
    bel_pins, pins = {}, {}
    for name, p in sorted(site["site_pins"].items()):
        direction = "INPUT" if "cap" in p else "OUTPUT"
        bel_pins[name] = {"dir": direction, "wire": name}
        pins[name] = {"primary": name, "wire": name, "dir": direction}
    bels = {"XADC": {"type": "XADC_XADC", "class": "BEL", "pins": bel_pins}}
    return {"XADC": {"bels": bels, "pips": [], "pins": pins}}


def main():
    ap = argparse.ArgumentParser(description="flat XADC site type for nextpnr-xilinx-meta, from prjxray-db's MONITOR_BOT site pins; and a meta copy with it")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    st = site_type()
    n = len(st["XADC"]["pins"])
    print(f"XADC: {n} site pins, one bel, no site pips")
    if dry:
        print(f"[dry] would write {CONFIG['draft']} and copy {CONFIG['meta_src']} to {CONFIG['meta_out']}")
        return
    (ROOT / CONFIG["draft"]).write_text(json.dumps(st, indent=2) + "\n")
    dst = ROOT / CONFIG["meta_out"]
    if not dst.exists():
        shutil.copytree(ROOT / CONFIG["meta_src"], dst, symlinks=True)
    shutil.copy(ROOT / CONFIG["draft"], dst / "artix7" / "site_type_XADC.json")
    print(f"wrote {CONFIG['draft']} and {dst / 'artix7' / 'site_type_XADC.json'}")


if __name__ == "__main__":
    main()
