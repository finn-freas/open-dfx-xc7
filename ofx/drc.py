import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from . import design as D

CONFIG = {
    "speed_grade": "-1",
    "vco": {"MMCME2_ADV": (600.0, 1200.0), "PLLE2_ADV": (800.0, 1600.0)},
    "clkin": {"MMCME2_ADV": (10.0, 800.0), "PLLE2_ADV": (19.0, 800.0)},
    "default_iostandard": "LVCMOS18",
    "pfd": {"MMCME2_ADV": (10.0, 450.0), "PLLE2_ADV": (19.0, 450.0)},
    "pll_alias": {"MMCME2_BASE": "MMCME2_ADV", "MMCME2_ADV": "MMCME2_ADV", "PLLE2_BASE": "PLLE2_ADV",
                  "PLLE2_ADV": "PLLE2_ADV"},
    "comb_types": ("LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6", "LUT6_2", "MUXF7", "MUXF8", "CARRY4", "INV", "BUF"),
    "lut_types": ("LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6", "LUT6_2", "INV"),
    "async_ff": {"FDCE": "CLR", "FDPE": "PRE", "FDCE_1": "CLR", "FDPE_1": "PRE"},
    "clock_pins": {
        "FDRE": ("C",), "FDSE": ("C",), "FDCE": ("C",), "FDPE": ("C",), "FDRE_1": ("C",), "FDCE_1": ("C",),
        "FDPE_1": ("C",), "FDSE_1": ("C",), "LDCE": ("G",), "LDPE": ("G",),
        "SRL16E": ("CLK",), "SRLC32E": ("CLK",), "SRLC16E": ("CLK",),
        "RAMB18E1": ("CLKARDCLK", "CLKBWRCLK", "REGCLKARDRCLK", "REGCLKB"),
        "RAMB36E1": ("CLKARDCLK", "CLKBWRCLK", "REGCLKARDRCLK", "REGCLKB"),
        "FIFO18E1": ("RDCLK", "WRCLK"), "FIFO36E1": ("RDCLK", "WRCLK"), "DSP48E1": ("CLK",),
        "IDDR": ("C",), "ODDR": ("C",), "IDDR_2CLK": ("C", "CB"), "ISERDESE2": ("CLK", "CLKB", "CLKDIV", "OCLK"),
        "OSERDESE2": ("CLK", "CLKDIV"), "IDELAYE2": ("C",), "ODELAYE2": ("C",),
        "RAM32X1D": ("WCLK",), "RAM64X1D": ("WCLK",), "RAM128X1D": ("WCLK",), "RAM32M": ("WCLK",), "RAM64M": ("WCLK",),
        "RAM32X1S": ("WCLK",), "RAM64X1S": ("WCLK",), "RAM128X1S": ("WCLK",), "RAM256X1S": ("WCLK",),
    },
    "ram_ctrl_pins": ("ENARDEN", "ENBWREN", "RSTRAMARSTRAM", "RSTRAMB", "RSTREGARSTREG", "RSTREGB", "REGCEAREGCE",
                      "REGCEB"),
    "clock_bufs": ("BUFG", "BUFGCTRL", "BUFGCE", "BUFGMUX", "BUFH", "BUFHCE", "BUFR", "BUFIO"),
    "ibuf_types": ("IBUF", "IBUFG", "IBUF_IBUFDISABLE", "IBUF_INTERMDISABLE", "IBUFDS", "IBUFGDS", "IBUFDS_DIFF_OUT"),
    "diff_re": re.compile(r"(IBUFDS|IBUFGDS|OBUFDS|OBUFTDS|IOBUFDS)"),
    "diff_pt_re": re.compile(r"^IOB(33|18)[MS]_"),
    "capacity": {
        "xc7a35t": {"Slice LUTs": 20800, "Slice Registers": 41600, "RAMB18": 100, "DSPs": 90, "BUFG": 32,
                    "MMCME2_ADV": 5, "PLLE2_ADV": 5, "BUFR": 20, "BUFIO": 20, "IDELAYCTRL": 5, "Bonded IOB": 210},
        "xc7a50t": {"Slice LUTs": 32600, "Slice Registers": 65200, "RAMB18": 150, "DSPs": 120, "BUFG": 32,
                    "MMCME2_ADV": 5, "PLLE2_ADV": 5, "BUFR": 20, "BUFIO": 20, "IDELAYCTRL": 5, "Bonded IOB": 210},
        "xc7a100t": {"Slice LUTs": 63400, "Slice Registers": 126800, "RAMB18": 270, "DSPs": 240, "BUFG": 32,
                     "MMCME2_ADV": 6, "PLLE2_ADV": 6, "BUFR": 24, "BUFIO": 24, "IDELAYCTRL": 6, "Bonded IOB": 210},
    },
    "util_types": {
        "Slice LUTs": ("LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6", "INV", "LUT6_2"),
        "Slice Registers": ("FDRE", "FDSE", "FDCE", "FDPE", "FDRE_1", "FDSE_1", "FDCE_1", "FDPE_1", "LDCE", "LDPE"),
        "RAMB18": ("RAMB18E1", "RAMB36E1", "FIFO18E1", "FIFO36E1"),
        "DSPs": ("DSP48E1",),
        "BUFG": ("BUFG", "BUFGCTRL", "BUFGCE", "BUFGMUX", "BUFGCE_1", "BUFGMUX_1", "BUFGMUX_CTRL"),
        "MMCME2_ADV": ("MMCME2_ADV", "MMCME2_BASE"),
        "PLLE2_ADV": ("PLLE2_ADV", "PLLE2_BASE"),
        "BUFR": ("BUFR",), "BUFIO": ("BUFIO",), "IDELAYCTRL": ("IDELAYCTRL",),
    },
    "util_weight": {"RAMB36E1": 2, "FIFO36E1": 2},
    "clock_region_rows": 50,
    "pblock_slice_res": {
        "LUT": (("LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6", "LUT6_2", "INV"), 4),
        "Register": (("FDRE", "FDSE", "FDCE", "FDPE", "LDCE", "LDPE"), 8),
        "CARRY4": (("CARRY4",), 1), "MUXF7": (("MUXF7",), 2), "MUXF8": (("MUXF8",), 1),
    },
    "tall_rows": 5,
    "io_placer_errors": ("BIVC-1", "BIVRU-1"),
    "rules": {
        "BIVC-1": ("Error", "Bank IO standard Vcc"),
        "BUFC-1": ("Warning", "Input Buffer Connections"),
        "CFGBVS-1": ("Warning", "Missing CFGBVS and CONFIG_VOLTAGE Design Properties"),
        "DPIP-1": ("Warning", "Input pipelining"),
        "DPOP-1": ("Warning", "PREG Output pipelining"),
        "DPOP-2": ("Warning", "MREG Output pipelining"),
        "LUTLP-1": ("Critical Warning", "Combinatorial Loop Alert"),
        "LVDS-1": ("Warning", "Bidirection LVDS IOs"),
        "MDRV-1": ("Error", "Multiple Driver Nets"),
        "NSTD-1": ("Critical Warning", "Unspecified I/O Standard"),
        "PDRC-153": ("Warning", "Gated clock check"),
        "PLHOLDVIO-2": ("Warning", "Non-Optimal connections which could lead to hold violations"),
        "PLIO-3": ("Warning", "Placement Constraints Check for IO constraints"),
        "PLIO-8": ("Warning", "Placement Constraints Check for IO constraints"),
        "REQP-88": ("Warning", "enum_IDELAY_TYPE_FIXED_connects_CNTVALUEIN_ACTIVE"),
        "REQP-181": ("Advisory", "writefirst"),
        "REQP-195": ("Error", "enum_RAMB36_EN_ECC_READ_TRUE_EN_ECC_WRITE_TRUE_connects_ECCPARITY"),
        "REQP-1839": ("Warning", "RAMB36 async control check"),
        "REQP-1840": ("Warning", "RAMB18 async control check"),
        "REQP-1886": ("Critical Warning", "RAMB36 ECC WEBWE must be VCC"),
        "RTSTAT-1": ("Critical Warning", "Unrouted nets"),
        "RTSTAT-12": ("Error", "No Routing"),
        "BIVRU-1": ("Error", "Bank IO standard Vref utilization"),
        "OFX-RAMBWIDTH-1": ("Warning", "Illegal RAMB READ/WRITE_WIDTH for the RAM_MODE (ofx-only)"),
        "PDRC-29": ("Error", "MMCM_adv_ClkFrequency_clkin1"),
        "PDRC-34": ("Error", "MMCM_adv_ClkFrequency_div_no_dclk"),
        "PDRC-38": ("Error", "PLL_adv_ClkFrequency_clkin1"),
        "PDRC-43": ("Error", "PLL_adv_ClkFrequency_div_no_dclk"),
        "AVAL-46": ("Critical Warning", "v7v8_mmcm_fvco_rule1"),
        "HDPR-30": ("Error", "Missing PBLOCK On Reconfigurable Cell"),
        "Place 30-8517": ("Warning", "Pblock ranges must include all sites of a tile"),
        "OFX-PFD-1": ("Warning", "MMCM/PLL phase-frequency-detector input out of range (ofx-only)"),
        "OFX-CLKFB-1": ("Warning", "MMCM/PLL feedback input unconnected (ofx-only)"),
        "PLIDC-1": ("Error", "IDELAYCTRL missing from group with assigned IODELAYs"),
        "PLIDC-10": ("Error", "IDELAYCTRL missing for IODELAYs"),
        "CFGBVS-4": ("Critical Warning", "CFGBVS and CONFIG_VOLTAGE Design Properties"),
        "PLCK-87": ("Error", "Clock Placer Checks"),
        "HDPR-1": ("Error", "Cells must have a Pblock defined"),
        "HDPR-10": ("Error", "RESET_AFTER_RECONFIG Reconfigurable Pblocks must be frame aligned"),
        "HDPR-26": ("Warning", "Improper Pblock column boundary"),
        "HDPR-45": ("Critical Warning", "Reconfig Pblock should range all grid types covered by the Pblock rectangles"),
        "IOSTDTYPE-1": ("Critical Warning", "IOStandard Type"),
        "UCIO-1": ("Critical Warning", "Unconstrained Logical Port"),
        "Place 30-574": ("Error", "Poor placement for routing between an IO pin and BUFG"),
        "Place 30-578": ("Error", "Un-associated IO delay instances (no IDELAYCTRL)"),
        "PLCK-12": ("Warning", "Clock Placer Checks"),
        "PLIO-9": ("Error", "Placement Constraints Check for IO constraints"),
        "UTLZ-1": ("Error", "Resource utilization"),
    },
}

IOSTD = {}


def _std(names, vcco, kind="se", vref=False, dci=False, hp_only=False):
    for n in names.split():
        IOSTD[n] = {"vcco": vcco, "kind": kind, "vref": vref, "dci": dci, "hp_only": hp_only or dci}


_std("LVTTL LVCMOS33 PCI33_3", 3.3)
_std("LVCMOS25", 2.5)
_std("LVCMOS18", 1.8)
_std("LVCMOS15", 1.5)
_std("LVCMOS12", 1.2)
_std("MOBILE_DDR", 1.8)
_std("SSTL18_I SSTL18_II HSTL_I_18 HSTL_II_18", 1.8, vref=True)
_std("SSTL15 SSTL15_R HSTL_I HSTL_II", 1.5, vref=True)
_std("SSTL135 SSTL135_R", 1.35, vref=True)
_std("HSUL_12", 1.2, vref=True)
_std("LVDS_25 MINI_LVDS_25 PPDS_25 RSDS_25 BLVDS_25", 2.5, kind="diff")
_std("TMDS_33", 3.3, kind="diff")
_std("DIFF_SSTL18_I DIFF_SSTL18_II DIFF_HSTL_I_18 DIFF_HSTL_II_18 DIFF_MOBILE_DDR", 1.8, kind="diff")
_std("DIFF_SSTL15 DIFF_SSTL15_R DIFF_HSTL_I DIFF_HSTL_II", 1.5, kind="diff")
_std("DIFF_SSTL135 DIFF_SSTL135_R", 1.35, kind="diff")
_std("DIFF_HSUL_12", 1.2, kind="diff")
_std("LVDS", 1.8, kind="diff", hp_only=True)
_std("LVDCI_18 LVDCI_DV2_18 HSLVDCI_18 SSTL18_I_DCI SSTL18_II_DCI SSTL18_II_T_DCI HSTL_I_DCI_18 HSTL_II_DCI_18 "
     "HSTL_II_T_DCI_18", 1.8, dci=True)
_std("LVDCI_15 LVDCI_DV2_15 HSLVDCI_15 SSTL15_DCI SSTL15_T_DCI HSTL_I_DCI HSTL_II_DCI HSTL_II_T_DCI", 1.5, dci=True)
_std("SSTL135_DCI SSTL135_T_DCI", 1.35, dci=True)
_std("SSTL12_DCI SSTL12_T_DCI HSUL_12_DCI", 1.2, dci=True)


class Report:
    def __init__(self):
        self.v = []

    def add(self, rule, msg, objs=()):
        sev, desc = CONFIG["rules"].get(rule, ("Warning", rule))
        self.v.append({"rule": rule, "severity": sev, "description": desc, "message": msg, "objects": list(objs)})

    def counts(self):
        c = defaultdict(int)
        for x in self.v:
            c[x["rule"]] += 1
        return dict(c)


def io_ports(net, xdc, pins, sites):
    pads = {n: c for n, c in net.cells.items() if c["ptype"] == "PAD" or c["type"] == "PAD"}
    pad_by_port = {}
    for n, c in pads.items():
        bits = [b for v in c["conns"].values() for b in v.values()]
        for p, (b, _) in net.port_bits.items():
            if b in bits:
                pad_by_port[p] = n
    out = {}
    hr_only = not any("18" in r["tile"].split("_")[0] for r in pins.values())
    for p, (b, d) in net.port_bits.items():
        props = dict(xdc.port_props(p))
        pc = pads.get(pad_by_port.get(p))
        a = pc["attrs"] if pc else {}
        for k in ("IOSTANDARD", "PACKAGE_PIN", "LOC", "DIFF_TERM", "IOB", "INTERNAL_VREF"):
            if k in a and k not in props:
                props[k] = D.as_str(a[k])
        std = IOSTD.get((props.get("IOSTANDARD") or "").upper())
        if std and std["hp_only"] and hr_only:
            props.pop("IOSTANDARD", None)
        loc = props.get("PACKAGE_PIN") or props.get("LOC")
        role = diff_role(net, b)
        if loc and role and pins.get(loc):
            m = re.search(r"_L\d+([PN])_", pins[loc]["function"])
            if m and m.group(1) != role:
                for k in ("PACKAGE_PIN", "LOC", "IOSTANDARD"):
                    props.pop(k, None)
                loc = None
        site = None
        if pc and pc.get("bel"):
            site = pc["bel"].split("/")[0]
        rec = pins.get(loc) if loc else (sites.get(site) if site else None)
        conn = set()
        for cell, _, _ in net.sinks.get(b, []) + net.drivers.get(b, []):
            if cell != "<port>":
                conn.add(cell)
        diff = any(CONFIG["diff_re"].search(net.cells[c]["type"]) or CONFIG["diff_pt_re"].match(net.cells[c]["ptype"]) or
                   (not net.routed and CONFIG["diff_re"].search(c)) for c in conn)
        out[p] = {"bit": b, "dir": d, "props": props, "loc": loc, "pin": rec, "pad": pad_by_port.get(p), "diff": diff,
                  "cells": conn}
    return out


def diff_role(net, b):
    for c, port, _ in net.sinks.get(b, []) + net.drivers.get(b, []):
        if c != "<port>" and CONFIG["diff_re"].search(net.cells[c]["type"]):
            if port in ("O", "I", "IO"):
                return "P"
            if port in ("OB", "IB", "IOB"):
                return "N"
    return None


def vcco_need(io):
    std = io["props"].get("IOSTANDARD")
    if not std or std.upper() == "DEFAULT":
        std = CONFIG["default_iostandard"]
    s = IOSTD.get((std or "").upper())
    if not s:
        return None
    if io["dir"] in ("output", "inout"):
        return s["vcco"]
    if s["vref"] or (s["kind"] == "diff" and str(io["props"].get("DIFF_TERM", "")).upper() not in ("TRUE", "1")):
        return None
    return s["vcco"]


def std_of(io):
    s = io["props"].get("IOSTANDARD")
    return s if s and s.upper() != "DEFAULT" else CONFIG["default_iostandard"]


def check_io(net, xdc, pins, sites, rep):
    ios = io_ports(net, xdc, pins, sites)
    n = len(ios)
    noloc = [p for p, io in ios.items() if not io["loc"]]
    nostd = [p for p, io in ios.items() if not io["props"].get("IOSTANDARD") or io["props"]["IOSTANDARD"].upper() == "DEFAULT"]
    if nostd:
        rep.add("NSTD-1", f"{len(nostd)} out of {n} logical ports use I/O standard (IOSTANDARD) value 'DEFAULT', instead "
                          f"of a user assigned specific value. Problem ports: {', '.join(sorted(nostd))}.", nostd)
    if noloc:
        rep.add("UCIO-1", f"{len(noloc)} out of {n} logical ports have no user assigned specific location constraint "
                          f"(LOC). Problem ports: {', '.join(sorted(noloc))}.", noloc)
    buses = defaultdict(list)
    for p, io in ios.items():
        base, idx = D.bus(p)
        if idx is not None:
            buses[base].append((idx, p, bool(io["loc"])))
    for base, bits in sorted(buses.items()):
        locked = [b for b in bits if b[2]]
        if locked and len(locked) < len(bits):
            lo, hi = min(b[0] for b in bits), max(b[0] for b in bits)
            free = [b[1] for b in sorted(bits) if not b[2]]
            rep.add("PLIO-3", f"Partially locked IO Bus is found. Following components of the IO Bus {base}[{hi}:{lo}] "
                              f"are not locked:  {' '.join(free)}", free)
    banks = defaultdict(list)
    for p, io in ios.items():
        if io["pin"]:
            banks[io["pin"]["bank"]].append(p)
    for bank, ports in sorted(banks.items(), key=lambda x: str(x[0])):
        need = {}
        for p in sorted(ports):
            v = vcco_need(ios[p])
            if v is not None:
                need.setdefault(v, p)
        if len(need) > 1:
            (v1, p1), (v2, p2) = sorted(need.items(), reverse=True)[:2]
            rep.add("BIVC-1", f"Bank IO standard Vcc: Conflicting Vcc voltages in bank {bank}. For example, the following "
                              f"two ports in this bank have conflicting VCCOs:  {p2} ({std_of(ios[p2])}, "
                              f"requiring VCCO={v2:.3f}) and {p1} ({std_of(ios[p1])}, requiring "
                              f"VCCO={v1:.3f})", [p1, p2])
        vref_in = [p for p in ports if ios[p]["dir"] in ("input", "inout") and
                   (IOSTD.get((ios[p]["props"].get("IOSTANDARD") or "").upper()) or {}).get("vref")]
        internal = xdc.banks.get(bank, {}).get("INTERNAL_VREF")
        if vref_in and not internal:
            on_vref = [p for p in ports if "VREF" in ios[p]["pin"]["function"]]
            if on_vref:
                rep.add("BIVRU-1", f"Bank {bank} needs an external VREF for {', '.join(sorted(vref_in))}, but its VREF "
                                  f"pin(s) are used by {', '.join(sorted(on_vref))}; set INTERNAL_VREF on the bank or "
                                  f"move the ports.", on_vref)
    for p, io in sorted(ios.items()):
        s = IOSTD.get((io["props"].get("IOSTANDARD") or "").upper())
        if s and io["pad"] is not None or (s and not net.routed):
            if s["kind"] == "diff" and not io["diff"]:
                rep.add("IOSTDTYPE-1", f"I/O port {p} is Single-Ended but has an IOStandard of "
                                       f"{io['props']['IOSTANDARD']} which can only support Differential", [p])
    lvds_bidir = sorted(p for p, io in ios.items() if io["dir"] == "inout" and io["diff"] and
                        (io["props"].get("IOSTANDARD") or "").upper() == "LVDS_25")
    if lvds_bidir:
        rep.add("LVDS-1", "The following port(s) use the LVDS_25 I/O standard and have bi-directional differential "
                          f"usage. {', '.join(lvds_bidir)}.", lvds_bidir)
    for p, io in sorted(ios.items()):
        if str(io["props"].get("IOB", "")).upper() == "TRUE":
            site = "OLOGIC" if io["dir"] == "output" else "ILOGIC"
            packed = any(site in (net.cells[c].get("bel") or "") for c in reachable_ffs(net, io))
            if not packed:
                rep.add("PLIO-8", f"Terminal {p} has IOB constraint set to TRUE, but it is either not connected to a "
                                  "FLOP element or the connected FLOP element could not be brought into the I/O.", [p])
    return ios


def pins_tile(io):
    return io["pin"]["tile"] if io["pin"] else "33"


def reachable_ffs(net, io):
    out = set()
    for c in io["cells"]:
        for port, bits in net.cells[c]["conns"].items():
            for b in bits.values():
                for cc, _, _ in net.sinks.get(b, []) + net.drivers.get(b, []):
                    if cc != "<port>" and net.cells[cc]["type"].startswith(("FD", "IDDR", "ODDR")):
                        out.add(cc)
    return out


def check_cfg(xdc, ios, rep):
    d = {k.upper(): str(v).upper() for k, v in xdc.design.items()}
    if "CFGBVS" not in d and "CONFIG_VOLTAGE" not in d:
        rep.add("CFGBVS-1", "Neither the CFGBVS nor CONFIG_VOLTAGE voltage property is set in the current_design.")
        return
    cv = D.as_float(d.get("CONFIG_VOLTAGE"), 0.0)
    bvs = d.get("CFGBVS")
    if bvs and cv:
        if (bvs == "VCCO" and cv < 2.5) or (bvs == "GND" and cv > 1.8):
            want = "GND" if cv < 2.5 else "VCCO"
            rep.add("CFGBVS-4", f"When CONFIG_VOLTAGE is set to {d['CONFIG_VOLTAGE']}, CFGBVS property of current_design "
                                f"should be set to {want}.")


def driver_cell(net, b):
    c, port, idx = net.driver(b)
    return c, port


def check_logic(net, rep):
    clkpins = CONFIG["clock_pins"]
    comb = set(CONFIG["comb_types"])
    adj = defaultdict(set)
    for name, c in net.cells.items():
        if c["type"] not in comb:
            continue
        for port, bits in c["conns"].items():
            for b in bits.values():
                if not isinstance(b, int):
                    continue
                if any(d[0] == name for d in net.drivers.get(b, [])):
                    for s, sp, _ in net.sinks.get(b, []):
                        if s != "<port>" and net.cells[s]["type"] in comb:
                            adj[name].add(s)
    for scc in sccs(adj):
        if len(scc) > 1 or (scc and scc[0] in adj.get(scc[0], ())):
            rep.add("LUTLP-1", f"{len(scc)} LUT cells form a combinatorial loop. This can create a race condition. "
                               f"Cells: {', '.join(sorted(scc))}", sorted(scc))
    for b, ds in net.drivers.items():
        real = [d for d in ds if d[0] != "<port>" and net.cells[d[0]]["ptype"] not in ("PAD",) and
                not net.cells[d[0]]["ptype"].startswith("PSEUDO")]
        if len(real) > 1 and not any(d[0] == "<port>" for d in ds):
            rep.add("MDRV-1", f"Net {net.name(b)} has multiple drivers: "
                              f"{', '.join(f'{c}/{p}' for c, p, _ in real)}.", [net.name(b)])
    for b in list(net.sinks):
        sinks = clock_sinks(net, b, clkpins)
        if not sinks:
            continue
        c, port = driver_cell(net, b)
        if c and c != "<port>" and net.cells[c]["type"] in CONFIG["lut_types"]:
            rep.add("PDRC-153", f"Net {net.name(b)} is a gated clock net sourced by a combinational pin {c}/{port}, "
                                f"cell {c}.", [net.name(b)])
            direct = [s for s in net.sinks.get(b, []) if s[0] != "<port>" and s[1] in clkpins.get(net.cells[s[0]]["type"], ())]
            if direct:
                rep.add("PLHOLDVIO-2", f"A LUT {c} is driving clock pin of {len(direct)} cells. This could lead to large "
                                       f"hold time violations.", [c])


def clock_sinks(net, b, clkpins, depth=0):
    out = []
    for s, sp, _ in net.sinks.get(b, []):
        if s == "<port>":
            continue
        t = net.cells[s]["type"]
        if sp in clkpins.get(t, ()):
            out.append((s, sp))
        elif t in CONFIG["clock_bufs"] and sp in ("I", "I0", "I1") and depth < 3:
            for ob in net.pins(s, "O").values():
                out += clock_sinks(net, ob, clkpins, depth + 1)
    return out


def sccs(adj):
    index, low, on, stack, out = {}, {}, set(), [], []
    counter = [0]
    nodes = set(adj) | {v for vs in adj.values() for v in vs}
    for root in sorted(nodes):
        if root in index:
            continue
        work = [(root, iter(sorted(adj.get(root, ()))))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on.add(root)
        while work:
            v, it = work[-1]
            nxt = next(it, None)
            if nxt is not None:
                if nxt not in index:
                    index[nxt] = low[nxt] = counter[0]
                    counter[0] += 1
                    stack.append(nxt)
                    on.add(nxt)
                    work.append((nxt, iter(sorted(adj.get(nxt, ())))))
                elif nxt in on:
                    low[v] = min(low[v], index[nxt])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                out.append(comp)
    return out


def check_ram_dsp(net, rep):
    for r in net.of_type("RAMB18E1", "RAMB36E1"):
        t = net.cells[r]["type"]
        rule = "REQP-1840" if t == "RAMB18E1" else "REQP-1839"
        for pin in CONFIG["ram_ctrl_pins"]:
            for b in net.pins(r, pin).values():
                c, _ = driver_cell(net, b)
                if c and c != "<port>":
                    ct = net.cells[c]["type"]
                    ap = CONFIG["async_ff"].get(ct)
                    if ap and not all(net.is_const(x) for x in net.pins(c, ap).values()):
                        rep.add(rule, f"The {t} {r} has an input control pin {r}/{pin} (net: {net.name(b)}) which is "
                                      f"driven by a register ({c}) that has an active asychronous set or reset.", [r])
        mode = D.as_str(net.param(r, "RAM_MODE", "TDP")).upper()
        wfa = D.as_str(net.param(r, "WRITE_MODE_A", "WRITE_FIRST")).upper()
        wfb = D.as_str(net.param(r, "WRITE_MODE_B", "WRITE_FIRST")).upper()
        ca, cb = net.pin(r, "CLKARDCLK"), net.pin(r, "CLKBWRCLK")
        if mode == "SDP" and "WRITE_FIRST" in (wfa, wfb) and ca == cb:
            rep.add("REQP-181", f"Synchronous clocking is detected for BRAM ({r}) in SDP mode with WRITE_FIRST "
                                "write-mode.", [r])
        if t == "RAMB36E1":
            er = D.as_str(net.param(r, "EN_ECC_READ", "FALSE")).upper() in ("TRUE", "1")
            ew = D.as_str(net.param(r, "EN_ECC_WRITE", "FALSE")).upper() in ("TRUE", "1")
            par = [b for b in net.pins(r, "ECCPARITY").values() if net.sinks.get(b)]
            if er and ew and par:
                rep.add("REQP-195", f"{r}: Built-in Error Correction mode is used. The software does not support "
                                    "concurrent use of the ECCPARITY bus when both EN_ECC_READ and EN_ECC_WRITE are TRUE.",
                        [r])
            if ew and not all(vcc(net, b) for b in net.pins(r, "WEBWE").values()):
                rep.add("REQP-1886", f"The RAMB36E1 cell {r} has EN_ECC_WRITE set to TRUE. The byte-write enable "
                                     "WEBWE[7:0] pins must be connected to VCC.", [r])
        check_ram_widths(net, r, t, mode, rep)
    for d in net.of_type("DSP48E1"):
        mult = D.as_str(net.param(d, "USE_MULT", "MULTIPLY")).upper()
        if mult == "NONE":
            continue
        for port, reg in (("A", "AREG"), ("B", "BREG")):
            if D.as_int(net.param(d, reg, 1), 1) == 0:
                bits = net.pins(d, port)
                if any(not net.is_const(b) for b in bits.values()):
                    rep.add("DPIP-1", f"DSP {d} input {d}/{port}[{max(bits) if bits else 0}:0] is not pipelined.", [d])
        if D.as_int(net.param(d, "PREG", 1), 1) == 0:
            rep.add("DPOP-1", f"DSP {d} output {d}/P[47:0] is not pipelined (PREG=0).", [d])
        if D.as_int(net.param(d, "MREG", 1), 1) == 0:
            rep.add("DPOP-2", f"DSP {d} multiplier stage {d}/P[47:0] is not pipelined (MREG=0).", [d])
    for c in net.of_type("IDELAYE2"):
        typ = D.as_str(net.param(c, "IDELAY_TYPE", "FIXED")).upper()
        if typ not in ("VAR_LOAD", "VAR_LOAD_PIPE") and any(not net.is_const(b) for b in net.pins(c, "CNTVALUEIN").values()):
            rep.add("REQP-88", f"{c}: With IDELAY_TYPE not VAR_LOAD or VAR_LOAD_PIPE any signals on input pins "
                               "CNTVALUEIN 0 thru 4 are not used and will be ignored.", [c])


def vcc(net, b):
    if not isinstance(b, int):
        return str(b) == "1"
    return any(c != "<port>" and net.cells[c]["ptype"] in ("PSEUDO_VCC", "VCC") for c, _, _ in net.drivers.get(b, []))


def check_ram_widths(net, r, t, mode, rep):
    ok = {"RAMB18E1": {"TDP": (0, 1, 2, 4, 9, 18), "SDP": (0, 1, 2, 4, 9, 18, 36)},
          "RAMB36E1": {"TDP": (0, 1, 2, 4, 9, 18, 36), "SDP": (0, 1, 2, 4, 9, 18, 36, 72)}}[t].get(mode)
    if not ok:
        return
    for k in ("READ_WIDTH_A", "READ_WIDTH_B", "WRITE_WIDTH_A", "WRITE_WIDTH_B"):
        w = D.as_int(net.param(r, k, 0), 0)
        if w not in ok:
            rep.add("OFX-RAMBWIDTH-1", f"{r}: {k}={w} is not a legal width for {t} in {mode} mode (legal: "
                                   f"{', '.join(map(str, ok))}).", [r])


def port_period(net, xdc, b, depth=0):
    c, port = driver_cell(net, b)
    if c == "<port>":
        return xdc.clock_period(port)
    if c is None or depth > 4:
        return None
    t = net.cells[c]["type"]
    if t in CONFIG["ibuf_types"] or t in CONFIG["clock_bufs"] or net.cells[c]["ptype"].startswith("IOB"):
        for p in ("I", "I0", "PAD"):
            for ib in net.pins(c, p).values():
                v = port_period(net, xdc, ib, depth + 1)
                if v:
                    return v
        for p, (pb, d) in net.port_bits.items():
            if any(pb in bits.values() for bits in net.cells[c]["conns"].values()):
                return xdc.clock_period(p)
    return None


def check_clocking(net, xdc, ios, rep):
    cdr_false = xdc.net_prop("CLOCK_DEDICATED_ROUTE")
    for p, io in sorted(ios.items()):
        if io["dir"] != "input" or not io["pin"]:
            continue
        fn = io["pin"]["function"]
        cc = re.search(r"_(MRCC|SRCC)_", fn)
        nside = cc and re.search(r"_L\d+N_", fn) and not io["diff"]
        if cc and not nside:
            continue
        feeds = []
        for c in io["cells"]:
            for ob in [b for port, bits in net.cells[c]["conns"].items() for b in bits.values()
                       if any(d[0] == c for d in net.drivers.get(b, []))]:
                for s, sp, _ in net.sinks.get(ob, []):
                    if s != "<port>" and net.cells[s]["type"] in ("BUFG", "BUFGCTRL", "BUFGCE", "BUFGMUX", "MMCME2_ADV",
                                                                     "MMCME2_BASE", "PLLE2_ADV", "PLLE2_BASE"):
                        feeds.append((s, ob))
        if not feeds:
            continue
        relaxed = any(str(v).upper() == "FALSE" and any(re.fullmatch(D.glob_re(pat), f"{p}_IBUF", re.I) or
                      re.fullmatch(D.glob_re(pat), net.name(feeds[0][1]), re.I) for pat in pats)
                      for pats, v, _ in cdr_false)
        s, ob = feeds[0]
        if nside:
            rep.add("PLIO-9", f"Placement Constraints Check for IO constraints: The following clock source has been "
                              f"LOCed to a N-Type CCIO : {p}. For a single-ended input in a CCIO pair, only the P-side "
                              "can be used to drive a clock buffer.", [p])
            continue
        msg = (f"Sub-optimal placement for a clock-capable IO pin and BUFG pair. The clock port {p} is on pin "
               f"{io['loc'] or io['pin']['pin']} ({fn}), which is not clock capable, and drives {s} "
               f"({net.cells[s]['type']}).")
        if relaxed:
            rep.add("Place 30-574", msg + " CLOCK_DEDICATED_ROUTE is FALSE.", [p])
            rep.v[-1]["severity"] = "Warning"
            rep.add("PLCK-12", msg + " CLOCK_DEDICATED_ROUTE is FALSE, so this is only a warning; the clock uses "
                                     "general routing to reach the global buffer.", [p])
        else:
            rep.add("Place 30-574", msg, [p])
            rep.add("PLCK-12", "Poor placement for routing between an IO pin and BUFG. " + msg, [p])
            rep.v[-1]["severity"] = "Error"
    for c in net.of_type("MMCME2_ADV", "MMCME2_BASE", "PLLE2_ADV", "PLLE2_BASE"):
        kind = CONFIG["pll_alias"][net.cells[c]["type"]]
        mmcm = kind == "MMCME2_ADV"
        per = D.as_float(net.param(c, "CLKIN1_PERIOD", 0.0), 0.0)
        if not per:
            per = port_period(net, xdc, net.pin(c, "CLKIN1")) or 0.0
        if not per:
            continue
        mult = D.as_float(net.param(c, "CLKFBOUT_MULT_F" if mmcm else "CLKFBOUT_MULT", 5.0), 5.0)
        div = D.as_float(net.param(c, "DIVCLK_DIVIDE", 1), 1.0) or 1.0
        fin = 1000.0 / per
        pfd = fin / div
        vco = pfd * mult
        lo, hi = CONFIG["vco"][kind]
        plo, phi = CONFIG["pfd"][kind]
        if not lo <= vco <= hi:
            rep.add("PDRC-34" if mmcm else "PDRC-43",
                    f"The computed value {vco:.3f} MHz (CLKIN1_PERIOD) for the VCO operating frequency of the {kind} cell "
                    f"{c} falls outside the operating range of the {'MMCM' if mmcm else 'PLL'} VCO frequency for this "
                    f"device ({lo:.3f} - {hi:.3f} MHz). CLKFBOUT_MULT {mult:g}, DIVCLK_DIVIDE {div:g}.", [c])
            if mmcm:
                rep.add("AVAL-46", f"The current computed target frequency, FVCO, is out of range for cell {c}. The computed "
                                   f"FVCO is {vco:.3f} MHz. The valid FVCO range for speed grade {CONFIG['speed_grade']} "
                                   f"is {lo:.0f}MHz to {hi:.0f}MHz.", [c])
        flo, fhi = CONFIG["clkin"][kind]
        if not flo <= fin <= fhi:
            rep.add("PDRC-29" if mmcm else "PDRC-38",
                    f"The {kind} cell {c} has a CLKIN1 frequency of {fin:.3f} MHz; the legal range is {flo:.3f} - "
                    f"{fhi:.3f} MHz.", [c])
        if not plo <= pfd <= phi:
            rep.add("OFX-PFD-1", f"The {kind} cell {c} has a phase frequency detector input of {pfd:.3f} MHz; the legal "
                                 f"range is {plo:.3f} - {phi:.3f} MHz.", [c])
        fb = net.pin(c, "CLKFBIN")
        if fb is None or net.is_const(fb):
            rep.add("OFX-CLKFB-1", f"The {kind} cell {c} has its CLKFBIN pin unconnected or tied to a constant; the "
                                   "MMCM/PLL can never lock.", [c])


def check_buffers(net, rep):
    inout = {b for p, (b, d) in net.port_bits.items() if d == "inout"}
    for name, c in net.cells.items():
        t, pt = c["type"], c["ptype"]
        if not ("INBUF" in pt or (not net.routed and t in CONFIG["ibuf_types"] + ("IOBUF", "IOBUFDS"))):
            continue
        if not any(b in inout for v in c["conns"].values() for b in v.values()):
            continue
        outs = [b for port in ("OUT", "O") for b in c["conns"].get(port, {}).values()]
        if not any(net.sinks.get(b) for b in outs):
            rep.add("BUFC-1", f"Input buffer {name} has no loads. It is recommended to have an input buffer drive an "
                              "internal load.", [name])


_SYNTH_ATTRS = {}


def synth_attrs(net):
    """nextpnr drops IODELAY_GROUP from duplicated IDELAYCTRLs (u_ctrl$intcell$CTRL_DUP_0); read the attributes from
    the synthesized netlist next to the routed one (<top>.json) when there is one"""
    key = str(net.path)
    if key not in _SYNTH_ATTRS:
        out = {}
        if net.routed:
            cand = net.path.with_name(net.path.name.replace("_routed.json", ".json"))
            if cand.exists() and cand != net.path:
                try:
                    j = json.loads(cand.read_text())
                    for m in j.get("modules", {}).values():
                        for n, c in m.get("cells", {}).items():
                            if c.get("attributes"):
                                out[n] = c["attributes"]
                except (ValueError, OSError):
                    out = {}
        _SYNTH_ATTRS[key] = out
    return _SYNTH_ATTRS[key]


def cell_group(net, c):
    a = net.cells[c]["attrs"]
    g = D.as_str(a.get("IODELAY_GROUP", ""))
    if not g:
        g = D.as_str(synth_attrs(net).get(c.split("$intcell$")[0], {}).get("IODELAY_GROUP", ""))
    return g


def check_iodelay(net, rep):
    """Vivado 2025.2: no IDELAYCTRL at all -> PLIDC-10; an IODELAY_GROUP with delays but no IDELAYCTRL -> PLIDC-1
    (both Errors at opt/place DRC, drc_idelay_noctrl). Place 30-578 (placer cannot associate a controller) is kept
    for an IDELAY whose group differs from every controller's group."""
    ctrls = net.of_type("IDELAYCTRL")
    dlys = net.of_type("IDELAYE2", "ODELAYE2")
    if not dlys:
        return
    if not ctrls:
        rep.add("PLIDC-10", f"IDELAYCTRL missing for IODELAYs: There are {len(dlys)} IDELAY/ODELAY/IODELAY cells in the "
                            "design which requires IDelayCtrl, but there is no IDelayCtrl cell", sorted(dlys))
    cgroups = {cell_group(net, c) for c in ctrls}
    dgroups = defaultdict(list)
    for c in dlys:
        dgroups[cell_group(net, c)].append(c)
    for g, cs in sorted(dgroups.items()):
        if g and g not in cgroups:
            rep.add("PLIDC-1", f"IDELAYCTRL missing from group with assigned IODELAYs: IODELAY cells have been found to be "
                               f"associated with IODELAY_GROUP '{g}', but there is no IDELAYCTRL associated with this "
                               "IODELAY_GROUP.", sorted(cs))
        elif ctrls and g and g not in cgroups:
            rep.add("Place 30-578", "Found un-associated IO delay instances in the design. The list of IO delay instances "
                                    f"without an associated IdelayCtrl is as follows: {', '.join(sorted(cs))}", sorted(cs))


def device_caps(part):
    for k, v in CONFIG["capacity"].items():
        if part.startswith(k):
            return v
    return None


def util_counts(net):
    cnt = defaultdict(int)
    for name, c in net.cells.items():
        t = c["type"]
        for res, types in CONFIG["util_types"].items():
            if t in types:
                cnt[res] += CONFIG["util_weight"].get(t, 1)
    if net.routed:
        cnt["Bonded IOB"] = sum(1 for c in net.cells.values() if c["type"] == "PAD")
    else:
        cnt["Bonded IOB"] = len(net.port_bits)
    return cnt


def check_util(net, pins, rep, part=None):
    hp = any("18" in r["tile"].split("_")[0] for r in pins.values())
    n = len(net.of_type("ODELAYE2"))
    if n and not hp:
        rep.add("UTLZ-1", f"Resource utilization: ODELAYE2 over-utilized in Top Level Design (This design requires {n} "
                          "ODELAYE2 cells but the device has only HR banks, which have no ODELAYE2 sites).", [])
    caps = device_caps(part or D.CONFIG["default_part"])
    if not caps:
        return
    cnt = util_counts(net)
    for res, have in caps.items():
        need = cnt.get(res, 0)
        if need > have:
            rep.add("UTLZ-1", f"Resource utilization: {res} over-utilized in Top Level Design (This design requires more "
                              f"{res} cells than are available in the target device. This design requires {need} of such "
                              f"cell types but only {have} compatible sites are available in the target device.)", [])


def check_routing(net, rep):
    if not net.routed:
        rep.add("RTSTAT-1", "The design is not placed and routed (a synthesized netlist was given).", [])
        return
    bad = []
    for b, ss in net.sinks.items():
        if not ss or not net.drivers.get(b):
            continue
        if not any(s[0] != "<port>" for s in ss):
            continue
        if all(d[0] == "<port>" or net.cells[d[0]]["ptype"] == "PAD" for d in net.drivers[b]):
            continue
        if not str(net.netattr.get(b, {}).get("ROUTING", "")).strip():
            bad.append(net.name(b))
    routed_any = any(str(a.get("ROUTING", "")).strip() for a in net.netattr.values())
    if bad and not routed_any:
        rep.add("RTSTAT-12", "No Routing: The design is completely unrouted. Please run tcl command route_design.", [])
        return
    if bad:
        rep.add("RTSTAT-1", f"{len(bad)} net(s) are not routed. The problem bus(es) and/or net(s) are "
                            f"{', '.join(sorted(bad)[:20])}.", bad)


PB_RE = {
    "rp": re.compile(r"set_property\s+HD\.RECONFIGURABLE\s+(\S+)\s+\[get_cells\s+\{?([^\]\}]+?)\}?\s*\]", re.I),
    "create": re.compile(r"create_pblock\s+(\S+)"),
    "add": re.compile(r"add_cells_to_pblock\s+\[get_pblocks\s+(\S+?)\]\s+\[get_cells\s+\{?([^\]\}]+?)\}?\s*\]"),
    "resize": re.compile(r"resize_pblock\s+\[get_pblocks\s+(\S+?)\]\s+-add\s+\{?([^}\n]+)\}?"),
    "prop": re.compile(r"set_property\s+(RESET_AFTER_RECONFIG|SNAPPING_MODE|CONTAIN_ROUTING|EXCLUDE_PLACEMENT)\s+(\S+)\s+"
                       r"\[get_pblocks\s+(\S+?)\]", re.I),
    "range": re.compile(r"^SLICE_X(\d+)Y(\d+):SLICE_X(\d+)Y(\d+)$"),
}


def dfx_constraints(xdc_paths):
    rps, pbs = {}, {}
    for p in [x for x in (xdc_paths or []) if x]:
        t = Path(p).read_text(errors="replace")
        t = re.sub(r"\\\n", " ", t)
        for line in t.splitlines():
            line = line.split("#")[0]
            m = PB_RE["rp"].search(line)
            if m and m.group(1).strip("{}").upper() in ("TRUE", "1"):
                rps[m.group(2).strip()] = None
            m = PB_RE["create"].search(line)
            if m:
                pbs.setdefault(m.group(1), {"cells": [], "ranges": [], "props": {}})
            m = PB_RE["add"].search(line)
            if m:
                pbs.setdefault(m.group(1), {"cells": [], "ranges": [], "props": {}})["cells"].append(m.group(2).strip())
            m = PB_RE["resize"].search(line)
            if m:
                pbs.setdefault(m.group(1), {"cells": [], "ranges": [], "props": {}})["ranges"] += m.group(2).split()
            m = PB_RE["prop"].search(line)
            if m:
                pbs.setdefault(m.group(3), {"cells": [], "ranges": [], "props": {}})["props"][m.group(1).upper()] = \
                    m.group(2).strip("{}").upper()
    for name, pb in pbs.items():
        for c in pb["cells"]:
            if c in rps:
                rps[c] = name
    return rps, pbs


def slice_box(pb):
    out = []
    for r in pb["ranges"]:
        m = PB_RE["range"].match(r)
        if m:
            x0, y0, x1, y1 = map(int, m.groups())
            out.append((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
    return out


_REGION = {}


def region_mod():
    """flow/region.py owns the tile-grid / INT-pair logic used by the region DRC; reuse it here"""
    if "m" not in _REGION:
        from . import ROOT
        sys.path.insert(0, str(ROOT / "flow"))
        try:
            import region as m
            _REGION["m"] = m
            _REGION["grid"] = m.load_grid()
        except Exception as e:
            _REGION["m"] = None
            _REGION["err"] = str(e)
    return _REGION["m"]


def check_dfx_grid(pbn, rp, pb, snap, rep):
    m = region_mod()
    if m is None:
        return
    grid = _REGION["grid"]
    spec = ",".join(r for r in pb["ranges"] if re.match(r"^(SLICE|RAMB36|RAMB18|DSP48)_X\d+Y\d+(:\S+)?$", r))
    if not spec:
        return
    tiles = m.region_tiles(grid, spec)
    sl = [t for t in tiles.values() if t["type"].startswith("CLB")]
    if sl:
        gx0, gx1 = min(t["grid_x"] for t in sl), max(t["grid_x"] for t in sl)
        gy0, gy1 = min(t["grid_y"] for t in sl), max(t["grid_y"] for t in sl)
        have = {r.split("_")[0] for r in pb["ranges"]}
        need = []
        for t in grid.values():
            if gx0 <= t["grid_x"] <= gx1 and gy0 <= t["grid_y"] <= gy1 + CONFIG["tall_rows"] - 1:
                if t["type"].startswith("BRAM_") and t["type"] in ("BRAM_L", "BRAM_R"):
                    need += [x for x in ("RAMB18", "RAMB36") if x not in have]
                elif t["type"] in ("DSP_L", "DSP_R"):
                    need += [x for x in ("DSP48",) if x not in have]
        need = sorted(set(need))
        if need:
            rep.add("HDPR-45", f"The Pblock for Reconfigurable cell '{rp}' spans site types that are not included in the "
                               f"Pblock range. To ensure routability, it is strongly recommended that the following "
                               f"ranged sites to be included in the Pblock: {', '.join(need)}", [pbn])
    if not snap:
        edges = set()
        for a, b in m.pair_violations(grid, spec):
            side = "left" if a.startswith("INT_R") else "right"
            edges.add((side, int(re.search(r"_X(\d+)Y", a).group(1))))
        for side, x in sorted(edges):
            rep.add("HDPR-26", f"The Reconfigurable Pblock '{pbn}' has a '{side}' edge that terminates on an improper "
                               f"column boundary (INT tile column X{x}: its INT_L/INT_R partner is outside the Pblock).",
                    [pbn])


def rp_cells(net, rp):
    pre = (rp + ".", rp + "/")
    return [n for n in net.cells if n.startswith(pre)]


def rp_types(net, rp):
    """cell types inside the RP: flattened names (routed: u_rp.*) or, in a hierarchical synthesized netlist where
    u_rp is still an instance of the RM module (keep_hierarchy), that module's cells"""
    cells = rp_cells(net, rp)
    if cells:
        return [net.cells[c]["type"] for c in cells]
    try:
        mods = json.loads(net.path.read_text())["modules"]
    except (ValueError, OSError, KeyError):
        return []
    inst = None
    for m in mods.values():
        c = m.get("cells", {}).get(rp)
        if c and c["type"] in mods:
            inst = c["type"]
    if inst:
        out, todo = [], [inst]
        while todo:
            m = mods.get(todo.pop())
            for c in (m or {}).get("cells", {}).values():
                (todo if c["type"] in mods else out).append(c["type"])
        return out
    return []


def check_dfx(net, xdc_paths, rep):
    rps, pbs = dfx_constraints(xdc_paths)
    rows = CONFIG["clock_region_rows"]
    for rp, pbn in sorted(rps.items()):
        if pbn is None:
            rep.add("HDPR-30", f"Missing PBLOCK On Reconfigurable Cell: HD.RECONFIGURABLE cell '{rp}' must have PBLOCK "
                               "assigned to itself or its descendant cells.", [rp])
            for c in rp_cells(net, rp) or [rp]:
                rep.add("HDPR-1", f"HD.RECONFIGURABLE primitive cell '{c}' does not have a Pblock defined. Please first "
                                  f"define a Pblock for the HD.RECONFIGURABLE cell '{rp}' and define the range(s) for "
                                  "each primitive type.", [c])
            continue
        pb = pbs[pbn]
        boxes = slice_box(pb)
        if any(b[0] % 2 or b[2] % 2 == 0 for b in boxes):
            rep.add("Place 30-8517", f"Pblock ranges must include all sites of a tile. The ranges of pblock {pbn} "
                                     f"({' '.join(pb['ranges'])}) split a CLB tile and are widened to tile boundaries.",
                    [pbn])
        snap = pb["props"].get("SNAPPING_MODE") in ("ON", "ROUTING", "TRUE")
        if pb["props"].get("RESET_AFTER_RECONFIG") in ("TRUE", "1") and not snap:
            bad = [b for b in boxes if b[1] % rows or (b[3] + 1) % rows]
            if bad:
                rep.add("HDPR-10", f"Reconfigurable cell '{rp}' has RESET_AFTER_RECONFIG=TRUE on its Pblock '{pbn}' "
                                   f"but the ranges ({' '.join(pb['ranges'])}) are not aligned to the reconfigurable "
                                   f"frame boundary (clock-region rows of {rows} slices).", [pbn])
        check_dfx_grid(pbn, rp, pb, snap, rep)
        cells = rp_cells(net, rp)
        nsl = sum((b[2] - b[0] + 1) * (b[3] - b[1] + 1) for b in boxes)
        if not boxes:
            continue
        need = defaultdict(int)
        for t in rp_types(net, rp):
            for res, (types, _) in CONFIG["pblock_slice_res"].items():
                if t in types:
                    need[res] += 1
        for res, (types, per) in CONFIG["pblock_slice_res"].items():
            if need[res] > per * nsl:
                rep.add("UTLZ-1", f"{res} over-utilized in Pblock {pbn} (This design requires more {res} cells than are "
                                  f"available in Pblock '{pbn}'. This design requires {need[res]} of such cell types but "
                                  f"only {per * nsl} compatible sites are available in Pblock '{pbn}'.)", [pbn])


def run_checks(netlist_path, xdc_paths, part=None):
    net = D.Netlist(netlist_path)
    xdc = D.Xdc(xdc_paths)
    pins, sites = D.package_pins(part or D.CONFIG["default_part"])
    rep = Report()
    ios = check_io(net, xdc, pins, sites, rep)
    check_cfg(xdc, ios, rep)
    check_logic(net, rep)
    check_ram_dsp(net, rep)
    check_clocking(net, xdc, ios, rep)
    check_buffers(net, rep)
    check_iodelay(net, rep)
    check_util(net, pins, rep, part)
    check_routing(net, rep)
    check_dfx(net, xdc_paths, rep)
    if any(v["rule"] in CONFIG["io_placer_errors"] for v in rep.v):
        rep.add("PLCK-87", "IO/clock placer failed to collectively place all IOs and clock instances (a bank-level IO "
                           "rule above fails).")
    return rep, net


def format_report(rep, title):
    rows = defaultdict(list)
    for v in rep.v:
        rows[(v["rule"], v["severity"], v["description"])].append(v)
    out = [f"Report DRC (ofx) : {title}", f"Checks found: {len(rep.v)}"]
    w = max([len(r[0]) for r in rows] + [4])
    out.append(f"+-{'-' * w}-+------------------+------------------------------------------------------------+--------+")
    out.append(f"| {'Rule':{w}} | Severity         | Description                                                | Checks |")
    out.append(f"+-{'-' * w}-+------------------+------------------------------------------------------------+--------+")
    for (r, s, d), vs in sorted(rows.items()):
        out.append(f"| {r:{w}} | {s:16} | {d[:58]:58} | {len(vs):6} |")
    out.append(f"+-{'-' * w}-+------------------+------------------------------------------------------------+--------+")
    out.append("")
    for (r, s, d), vs in sorted(rows.items()):
        for k, v in enumerate(vs, 1):
            out += [f"{r}#{k} {s}", d, v["message"], ""]
    return "\n".join(out)


def errors(rep):
    return [v for v in rep.v if v["severity"] in ("Error",)]


def main(build, xdc=None, part=None, json_out=None, quiet=False):
    np = D.find_netlist(build)
    if np is None:
        sys.exit(f"ofx drc: no netlist in {build}")
    rep, net = run_checks(np, xdc, part or D.part_of(build))
    if not quiet:
        print(format_report(rep, str(np)))
    if json_out:
        Path(json_out).write_text(json.dumps({"netlist": str(np), "routed": net.routed, "violations": rep.v,
                                              "counts": rep.counts()}, indent=1) + "\n")
    return rep
