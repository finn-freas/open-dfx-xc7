import re
import sys
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "base_v": "examples/gtp_b3/src/gtp_b3.v",
    "base_xdc": "examples/gtp_b3/constraints/gtp_b3.xdc",
    "specimens": {
        "fz_gref_base": {"g0": True, "g1": True, "inv0": "1'b0", "inv1": "1'b0"},
        "fz_gref_inv0": {"g0": True, "g1": True, "inv0": "1'b1", "inv1": "1'b0"},
        "fz_gref_inv1": {"g0": True, "g1": True, "inv0": "1'b0", "inv1": "1'b1"},
        "fz_gref_g0": {"g0": True, "g1": False, "inv0": "1'b0", "inv1": "1'b0"},
        "fz_gref_g1": {"g0": False, "g1": True, "inv0": "1'b0", "inv1": "1'b0"},
    },
}


def specimen(src, name, s):
    v = src.replace("module gtp_b3", "module " + name)
    v = v.replace(".IS_GTGREFCLK0_INVERTED(1'b0)", f".IS_GTGREFCLK0_INVERTED({s['inv0']})")
    v = v.replace(".IS_GTGREFCLK1_INVERTED(1'b0)", f".IS_GTGREFCLK1_INVERTED({s['inv1']})")
    pins = []
    if s["g0"]:
        pins.append(".GTGREFCLK0(gclk)")
    if s["g1"]:
        pins.append(".GTGREFCLK1(gclk)")
    v = v.replace(".GTREFCLK0(refclk),", ".GTREFCLK0(refclk), " + " ".join(p + "," for p in pins))
    v = v.replace("    IBUFDS_GTE2 u_refbuf", "    wire gclk;\n    BUFG u_gbuf (.I(clk), .O(gclk));\n    IBUFDS_GTE2 u_refbuf")
    assert v.count("u_gbuf") == 1 and (not pins or "GTGREFCLK" in v)
    return v


def main():
    out = Path(sys.argv[1])
    src = (CONFIG["root"] / CONFIG["base_v"]).read_text()
    xdc = (CONFIG["root"] / CONFIG["base_xdc"]).read_text()
    for name, s in CONFIG["specimens"].items():
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.v").write_text(specimen(src, name, s))
        (d / f"{name}.xdc").write_text(xdc)
        print(name)


if __name__ == "__main__":
    main()
