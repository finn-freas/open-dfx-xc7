"""Run `ofx debug capture` in the LiteX venv (the LiteScope driver and litex.tools need migen/litex)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ofx import debug


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("meta", help="debug.json written by `ofx debug insert`")
    ap.add_argument("--via", choices=["sim", "jtag", "uart"], default="sim")
    ap.add_argument("--trigger", action="append", default=[], help="probe=value (0x.., 0b.. with x for don't care)")
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--length", type=int)
    ap.add_argument("--vcd", required=True)
    ap.add_argument("--simdir", default=None)
    ap.add_argument("--set", action="append", default=[], help="sim: top input=value")
    ap.add_argument("--server", default="localhost:1234")
    ap.add_argument("--uart")
    ap.add_argument("--json")
    a = ap.parse_args()
    meta = json.loads(Path(a.meta).read_text())
    trig = []
    for t in a.trigger:
        k, v = t.split("=", 1)
        trig.append({k.replace(".", "_"): v})
    stim = {k: int(v, 0) for k, v in (s.split("=", 1) for s in a.set)}
    host, port = a.server.split(":")
    simdir = Path(a.simdir) if a.simdir else Path(a.meta).parent / "sim"
    res = debug.capture(meta, a.via, trig, a.offset, a.length, Path(a.vcd), simdir, stim, (host, int(port)), a.uart)
    print(json.dumps(res, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n")
    if a.via == "sim" and not res.get("check", {}).get("pass"):
        sys.exit("capture does not match the simulated probe trace")


if __name__ == "__main__":
    main()
