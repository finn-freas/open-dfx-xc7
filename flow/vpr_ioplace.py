"""VPR --fix_clusters file for the I/O pads of a flow/vpr_export.py netlist: the cluster holding pad "clk" (input) or
"out:led[0]" (output) goes to the x y z F4PGA's pinmap.csv gives for its XDC PACKAGE_PIN.
usage: vpr_ioplace.py VPRDIR > io.place"""
import csv
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINMAP = ROOT / "toolchain" / "vtr" / "arch" / "share" / "f4pga" / "arch" / "xc7a50t_test" / "xc7a35tcsg324-1" / "pinmap.csv"

d = Path(sys.argv[1])
pins = json.loads((d / "export.json").read_text())["pins"]
pm = {r["name"]: r for r in csv.DictReader(open(PINMAP))}
owner = {}
for cl in ET.parse(d / "design.net").getroot().findall("block"):
    if not cl.get("instance", "").startswith("BLK-TL-IOPAD"):
        continue
    for b in cl.iter("block"):
        owner.setdefault(b.get("name"), cl.get("name"))
for port, pin in pins.items():
    r = pm[pin]
    for n in (port, "out:" + port):
        if n in owner:
            print(f"{owner[n]} {r['x']} {r['y']} {r['z']}")
