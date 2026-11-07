# `ofx drc`: a report_drc-style rule deck, checked against Vivado

`ofx drc` reads the routed netlist from nextpnr, or the synthesized one when nothing routed, together with the XDC files and the part's package pins and tile grid. It prints a report in the same layout as Vivado's `report_drc`: a rule table, then one entry per violation. It exits 1 when an Error-severity rule fires (`--no-fail` overrides that).

```
bin/ofx drc                                   # the project's build
bin/ofx drc --build build/drc/drc_vref --xdc designs/drc/drc_vref/drc_vref.xdc --json out.json
```

Every rule ID that `ofx drc` reports is Vivado's own ID, and its severity matches Vivado 2025.2's `get_drc_checks` catalogue. A rule that has no Vivado counterpart is named `OFX-*` and is not counted in the comparison. Vivado 2025.2 lists 7026 checks (`get_drc_checks`, xc7a35t). ofx implements 46 of them: the ones that matter for real designs and that Vivado reports on the designs here.

## Rules

| Area | Rules (Vivado IDs) | What ofx checks |
|---|---|---|
| IO standards and banks | BIVC-1, BIVRU-1, NSTD-1, UCIO-1, IOSTDTYPE-1, LVDS-1, PLIO-3, PLIO-8, PLCK-87 | VCCO conflicts per bank, taken from the IOSTANDARD table. A missing or DEFAULT standard counts as LVCMOS18, which is what Vivado does (drc_nstd). Inputs with a VREF standard, and differential inputs without DIFF_TERM, are exempt. A bank that needs an external VREF while its VREF pin is used, without INTERNAL_VREF, is BIVRU-1. Two XDC rejections are modelled the way Vivado applies them: a standard the part lacks (for example LVDCI_15 on an HR-only Artix-7) is dropped, and a P or N port placed on the wrong pin of a pair loses its LOC and IOSTANDARD. PLCK-87 follows any bank-level IO Error |
| Configuration | CFGBVS-1, CFGBVS-4 | Missing CFGBVS/CONFIG_VOLTAGE; CFGBVS VCCO with 1.5/1.8 V (or GND with 2.5/3.3 V) |
| Clocking | PLIO-9, Place 30-574, PLCK-12, PDRC-153, PLHOLDVIO-2, PDRC-29/34 (MMCM), PDRC-38/43 (PLL), AVAL-46 | A clock input on a pin that is not clock-capable, or on the N side of a CC pair, and whether CLOCK_DEDICATED_ROUTE FALSE turns the Error into a Warning. Gated clocks (LUT-driven clock nets), and LUTs driving clock pins directly. MMCM/PLL CLKIN1 and VCO ranges (speed grade -1) |
| BRAM / DSP | REQP-1839, REQP-1840, REQP-181, REQP-195, REQP-1886, DPIP-1, DPOP-1, DPOP-2 | RAMB control pins driven by async set/reset registers; SDP WRITE_FIRST on one clock; ECC parity and WEBWE rules; DSP A/B input, M and P pipelining |
| IO delay | PLIDC-1, PLIDC-10, Place 30-578, REQP-88 | No IDELAYCTRL at all; an IODELAY_GROUP without a controller (the group is read from the synthesized netlist when nextpnr dropped it); CNTVALUEIN driven while IDELAY_TYPE ignores it |
| Logic | LUTLP-1, MDRV-1, BUFC-1 | Combinational loops (Tarjan SCC on LUT/MUX/CARRY), multiple drivers, an input buffer with no load |
| Utilization | UTLZ-1 | Device capacity per resource (BUFG, MMCM, PLL, DSP, RAMB, IDELAYCTRL, BUFR/BUFIO, IOB, LUT, FF; xc7a35t/50t/100t), and per Pblock (LUT, FF, CARRY4, MUXF7/8 against 4/8/1/2/1 per SLICE) |
| Routing | RTSTAT-1, RTSTAT-12 | Partly unrouted nets, or a completely unrouted design |
| DFX | HDPR-1, HDPR-30, HDPR-10, HDPR-26, HDPR-45, Place 30-8517 | An RP (HD.RECONFIGURABLE) without a Pblock. RESET_AFTER_RECONFIG Pblocks that are not frame-aligned. Pblock edges that split an INT_L/INT_R pair when SNAPPING_MODE is off (same tile-grid code as `flow/region.py --drc`). Pblocks that span BRAM/DSP columns without RAMB/DSP ranges. Ranges that split a CLB tile |
| ofx-only | OFX-CLKFB-1, OFX-PFD-1, OFX-RAMBWIDTH-1 | MMCM/PLL feedback unconnected, PFD out of range, an illegal RAMB width for the RAM_MODE. Vivado 2025.2 is silent on drc_mmcm_nofb and drc_ramb_width |

## Comparison with Vivado

`flow/drc_compare.py` runs `ofx drc` on every open build that has a Vivado reference run of the same RTL and XDC. The references are Vivado 2025.2, xc7a35tcsg324-1, `vivado/build_drcpow.tcl`: report_drc after opt, after place (or after a failed place), and after route. Rule IDs are also read from the Vivado log, so DRCs that stop opt, place or bitgen are counted too. Placer messages that only repeat a DRC are not scored: Place 30-568 repeats PLHOLDVIO-2, Place 30-87 repeats PLIO-3, and Place 30-2953 is a note.

The designs:
- `test`: the deliberately broken designs in `flow/drc_designs.py`, one or two per rule, plus a clean `drc_ok`.
- `gap`: primitive test designs.
- `xdc`: XDC coverage designs.
- `power`: the power calibration designs.
- `qor`: QoR designs.
- `ddr3`/`eth`: LiteX SoCs.

A (design, rule) pair counts as "both" when both tools report the rule on that design. "Vivado only" and "ofx only" are disagreements.

<!-- drc-results (generated from build/; rerun after new Vivado data) -->
**198 designs with a Vivado report_drc and an open netlist; 42 rules seen; (design, rule) pairs: 204 flagged by both, 11 Vivado only, 6 ofx only; 35/42 rules with no disagreement**

Per rule (all sets):

| Rule | Vivado severity | ofx severity | both flag | Vivado only | ofx only | same count | where they differ |
|---|---|---|---|---|---|---|---|
| AVAL-46 | Critical Warning | Critical Warning | 2 | 0 | 0 | 2/2 |  |
| BIVC-1 | Error | Error | 5 | 0 | 0 | 5/5 |  |
| BIVRU-1 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| BUFC-1 | Warning | Warning | 2 | 0 | 0 | 2/2 |  |
| CFGBVS-1 | Warning | Warning | 138 | 0 | 0 | 138/138 |  |
| CFGBVS-4 | Critical Warning | Critical Warning | 1 | 0 | 0 | 1/1 |  |
| DPIP-1 | Warning | Warning | 3 | 0 | 0 | 0/3 |  |
| DPOP-1 | Warning | Warning | 1 | 0 | 6 | 1/1 | +arty_ddr3, +arty_eth, +pw_dsp32, +pw_dsp32_p5, +pw_dsp64, +pw_dsp8 |
| DPOP-2 | Warning | Warning | 1 | 2 | 0 | 1/1 | arty_ddr3, arty_eth |
| HDPR-1 | Error | Error | 1 | 0 | 0 | 0/1 |  |
| HDPR-10 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| HDPR-26 | Warning | Warning | 2 | 0 | 0 | 2/2 |  |
| HDPR-30 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| HDPR-45 | Critical Warning | Critical Warning | 2 | 0 | 0 | 2/2 |  |
| IOSTDTYPE-1 | Critical Warning | Critical Warning | 1 | 0 | 0 | 1/1 |  |
| LUTLP-1 | Critical Warning | Critical Warning | 1 | 0 | 0 | 1/1 |  |
| LVDS-1 | Warning | Warning | 2 | 0 | 0 | 2/2 |  |
| MDRV-1 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| NSTD-1 | Critical Warning | Critical Warning | 3 | 0 | 0 | 3/3 |  |
| PDRC-153 | Warning | Warning | 1 | 2 | 0 | 1/1 | arty_ddr3, arty_eth |
| PDRC-34 | Error | Error | 2 | 0 | 0 | 2/2 |  |
| PDRC-43 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| PLCK-12 | Error/Warning | Error/Warning | 3 | 0 | 0 | 3/3 |  |
| PLCK-87 | Error | Error | 6 | 0 | 0 | 6/6 |  |
| PLHOLDVIO-2 | Warning | - | 0 | 3 | 0 | 0/0 | arty_ddr3, arty_eth, drc_gated |
| PLIDC-1 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| PLIDC-10 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| PLIO-3 | Warning | Warning | 1 | 0 | 0 | 1/1 |  |
| PLIO-8 | Warning | Warning | 1 | 0 | 0 | 1/1 |  |
| PLIO-9 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| Place 30-574 | Error/Warning | Error/Warning | 4 | 0 | 0 | 4/4 |  |
| Place 30-578 | Error | - | 0 | 2 | 0 | 0/0 | idelay, idelay_nogrp |
| Place 30-8517 | Warning | Warning | 1 | 0 | 0 | 1/1 |  |
| REQP-181 | Advisory | Advisory | 2 | 0 | 0 | 2/2 |  |
| REQP-1839 | Warning | Warning | 1 | 0 | 0 | 1/1 |  |
| REQP-1840 | Warning | Warning | 1 | 1 | 0 | 1/1 | arty_ddr3 |
| REQP-1886 | Critical Warning | Critical Warning | 1 | 0 | 0 | 1/1 |  |
| REQP-195 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| REQP-88 | Warning | Warning | 1 | 0 | 0 | 1/1 |  |
| RTSTAT-12 | Error | Error | 1 | 0 | 0 | 1/1 |  |
| UCIO-1 | Critical Warning | Critical Warning | 2 | 0 | 0 | 2/2 |  |
| UTLZ-1 | Error | Error | 2 | 1 | 0 | 2/2 | drc_dfx_small |

The deliberately broken test designs (`designs/drc`, both tools on the same RTL and XDC):

| Design | set | Vivado | ofx | open netlist |
|---|---|---|---|---|
| drc_bivc | test | BIVC-1x1 PLCK-87x1 | BIVC-1x1 PLCK-87x1 | routed |
| drc_bivc_in | test | BIVC-1x1 PLCK-87x1 | BIVC-1x1 PLCK-87x1 | routed |
| drc_bufg_over | test | UTLZ-1x1 | UTLZ-1x1 | synth only |
| drc_cfgbvs | test | CFGBVS-1x1 | CFGBVS-1x1 | routed |
| drc_cfgbvs_gnd | test |  |  | routed |
| drc_cfgbvs_v18 | test | CFGBVS-4x1 | CFGBVS-4x1 | routed |
| drc_dci | test | BIVC-1x1 NSTD-1x1 PLCK-87x1 | BIVC-1x1 NSTD-1x1 PLCK-87x1 | routed |
| drc_dfx_nopb | test | HDPR-1x22 HDPR-30x1 | HDPR-1x34 HDPR-30x1 | routed |
| drc_dfx_ok | test | HDPR-45x1 | HDPR-45x1 | routed |
| drc_dfx_rar | test | HDPR-10x1 HDPR-26x2 HDPR-45x1 | HDPR-10x1 HDPR-26x2 HDPR-45x1 | routed |
| drc_dfx_small | test | HDPR-26x1 Place 30-8517x1 UTLZ-1x1 | HDPR-26x1 Place 30-8517x1 | synth only |
| drc_diff_npin | test | NSTD-1x1 UCIO-1x1 | NSTD-1x1 UCIO-1x1 | synth only |
| drc_dsp_nopipe | test | DPIP-1x2 DPOP-1x1 DPOP-2x1 | DPIP-1x1 DPOP-1x1 DPOP-2x1 | routed |
| drc_ffclk | test |  |  | routed |
| drc_gated | test | PDRC-153x1 PLHOLDVIO-2x1 | PDRC-153x1 | routed |
| drc_idelay_noctrl | test | PLIDC-1x1 PLIDC-10x1 | PLIDC-1x1 PLIDC-10x1 | routed |
| drc_iobuf_noload | test | BUFC-1x1 | BUFC-1x1 | routed |
| drc_iostdtype | test | IOSTDTYPE-1x1 | IOSTDTYPE-1x1 | routed |
| drc_lutlp | test | LUTLP-1x1 | LUTLP-1x1 | synth only |
| drc_lvds_vcco | test | BIVC-1x1 PLCK-87x1 | BIVC-1x1 PLCK-87x1 | routed |
| drc_mdrv | test | MDRV-1x1 | MDRV-1x1 | synth only |
| drc_mmcm_nofb | test |  |  | routed |
| drc_mmcm_vco | test | AVAL-46x1 PDRC-34x1 | AVAL-46x1 PDRC-34x1 | synth only |
| drc_mmcm_vcolow | test | AVAL-46x1 PDRC-34x1 | AVAL-46x1 PDRC-34x1 | routed |
| drc_noncc | test | PLCK-12x1 Place 30-574x1 | PLCK-12x1 Place 30-574x1 | synth only |
| drc_noncc_cdr | test | PLCK-12x1 Place 30-574x1 | PLCK-12x1 Place 30-574x1 | synth only |
| drc_nstd | test | BIVC-1x1 NSTD-1x1 PLCK-87x1 | BIVC-1x1 NSTD-1x1 PLCK-87x1 | synth only |
| drc_ok | test |  |  | routed |
| drc_pll_vco | test | PDRC-43x1 | PDRC-43x1 | routed |
| drc_ramb36_async | test | REQP-1839x1 | REQP-1839x1 | routed |
| drc_ramb_async | test | REQP-1840x1 | REQP-1840x1 | routed |
| drc_ramb_width | test |  |  | routed |
| drc_ucio | test | PLIO-3x1 UCIO-1x1 | PLIO-3x1 UCIO-1x1 | synth only |
| drc_unrouted | test | RTSTAT-12x1 | RTSTAT-12x1 | routed |
| drc_vref | test | BIVRU-1x1 PLCK-87x1 | BIVRU-1x1 PLCK-87x1 | routed |
| drc_vref_int | test |  |  | routed |
<!-- /drc-results -->

### Why the remaining disagreements happen

Every remaining disagreement was looked at. Most come from the two flows building different netlists from the same RTL, not from the rule logic:
- **DPOP-1 / DPOP-2 (arty_ddr3, arty_eth, pw_dsp*).** In pw_dsp*, yosys keeps the accumulator `p <= p + m` in fabric (PREG=0, so ofx reports DPOP-1) while Vivado folds it into PREG (see docs/power.md). In VexRiscv's multiplier, Vivado packs the product register into PREG (MREG=0, so Vivado reports DPOP-2), while yosys leaves PREG=0 (so ofx reports DPOP-1). Each tool is right about its own netlist. drc_dsp_nopipe, where the DSP is instantiated, agrees on both rules.
- **DPIP-1 count on drc_dsp_nopipe (Vivado 2, ofx 1).** The open flow packs the external `b` register into BREG (BREG=2 in the routed netlist), so only A is unpipelined.
- **PDRC-153 / PLHOLDVIO-2 (arty_ddr3, arty_eth, drc_gated).** Vivado's netlist has a LUT (`clk100_inst`) driving FDCE clock pins directly. The yosys flow puts a BUFG (`clkbufmap`) after the gating LUT. ofx still reports PDRC-153 on drc_gated, but no LUT drives a clock pin directly in the open netlist, so it reports no PLHOLDVIO-2.
- **REQP-1840 (arty_ddr3).** The flagged net, `tag_mem_reg_ENBWREN_cooolgate_en_sig_5`, is created by Vivado's BRAM power optimisation in opt_design ("cooolgate"). It does not exist in the open netlist.
- **Place 30-578 (gap idelay, idelay_nogrp).** Vivado's placer could not associate a controller in two designs. Both use IDELAYCTRL REFCLK = the 100 MHz board clock with no LOC; the same design with a LOC'd IDELAYCTRL (idelay_loc) passes. The grouping rules (PLIDC-1/-10) agree. The cause of this placer error is not modelled yet. `drc_idelay_ref200(g)` (200 MHz REFCLK from an MMCM, with and without a group) separate the REFCLK source from grouping; see the IDELAY note below.
- **UTLZ-1 per Pblock (drc_dfx_small).** The rule exists in ofx and fires on a routed or flattened netlist. On drc_dfx_small, nextpnr itself refuses the 1-SLICE Pblock ("Unable to find legal placement for ... CARRY4"), so ofx only has yosys's hierarchical JSON, and there the RM module is not resolved.
- **Counts.** HDPR-1 is reported per primitive cell, so the yosys netlist gives 34 against Vivado's 22. UTLZ-1 for BUFG: ofx counts 34 (33 instantiated plus the clock input's BUFG) against Vivado's 33. The rule fires either way.

Things ofx reports that Vivado 2025.2 does not are kept under `OFX-` IDs and not scored:
- MMCM feedback unconnected (drc_mmcm_nofb: Vivado is silent; the MMCM can never lock);
- PFD range;
- RAMB18 TDP READ_WIDTH=36 (drc_ramb_width: Vivado is silent).

## Files

- `ofx/drc.py`: the deck, plus `ofx drc` (`ofx/cli.py`).
- `flow/drc_designs.py`: writes the test designs into `designs/drc/`.
- `flow/drc_compare.py`: the comparison. It writes `build/drc/compare.{json,md}`.
- `vivado/build_drcpow.tcl` and `vivado/run_drcpow.ps1`: the Vivado reference runs. They do DRC and power in one pass and take the machine-wide Vivado lock through the caller.
