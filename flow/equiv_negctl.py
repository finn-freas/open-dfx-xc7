"""Negative control for the sequential equivalence check (flow/synth_timing_equiv.py check_seq): flip one bit of one
LUT INIT in the gate netlist and expect the miter + ABC dprove to fail.  usage: equiv_negctl.py GOLD.json GATE.json OUT [K]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth_timing_equiv as e

gold, gate, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
k = int(sys.argv[4]) if len(sys.argv) > 4 else 0
out.mkdir(parents=True, exist_ok=True)
j = json.loads(gate.read_text())
m = next(v for v in j["modules"].values() if v.get("attributes", {}).get("top"))
luts = sorted(n for n, c in m["cells"].items() if c["type"] in ("LUT4", "LUT5", "LUT6"))
victim = luts[k % len(luts)]
init = m["cells"][victim]["parameters"]["INIT"]
m["cells"][victim]["parameters"]["INIT"] = init[:-1] + ("1" if init[-1] == "0" else "0")
neg = out / "gate_neg.json"
neg.write_text(json.dumps(j))
g = e.prep_side(gold, "gold", out)
h = e.prep_side(neg, "gate", out)
print(victim, e.check_seq(out, g, h))
