# DRAFT (not posted): nextpnr-xilinx primitive gaps against Vivado (FIFO, DIFF_TERM, IO buffer parameters, BUFH, MMCM/PLL defaults, ICAP/DNA enables)

Status: **compiled and tested offline 2026-11-06 against Vivado 2025.2 bitstreams of the same RTL; no hardware test.**
Nothing pushed or posted. The install series (install/patches/nextpnr) is unchanged.

Seven patches, in this order on top of the `ofx` series (0001-0011, tree a9c8095a), against openXC7/nextpnr ce3f7c18:

| patch | files | size | gap |
|---|---|---|---|
| nextpnr-io-buffer-params.patch | pack_io.cc | +21 | G10 IOBUF DRIVE ignored (also SLEW, IOSTANDARD, DIFF_TERM parameters) |
| nextpnr-mmcm-base-ties.patch | pins.cc | +19 | MMCME2_BASE/PLLE2_BASE ZINV bits, CLKIN2 route |
| nextpnr-bufh-region.patch | pack.cc, pack_clocking.cc | +4/-3 | G7 BUFH/BUFHCE |
| nextpnr-diff-term.patch | fasm.cc | +24/-2 | G2 DIFF_TERM silently ignored |
| nextpnr-cfg-in-use.patch | fasm.cc | +23 | G11 ICAPE2/DNA_PORT enable bits |
| nextpnr-clkout-unused.patch | fasm.cc | +16 | G13 unused MMCM/PLL CLKOUT counters |
| nextpnr-fifo.patch | pack.cc, pack.h, xilinx.cc, fasm.cc | +194/-7 | G5 FIFO18E1/FIFO36E1 |

diff-term, cfg-in-use and fifo write features that prjxray-db a8b09269 does not have; they need the three
segbits drafts of docs/drafts/prjxray-db-prim-segbits.md. Without them fasm2frames stops with FasmLookupError on the
first such line, so a design that uses DIFF_TERM, a FIFO, an ICAPE2 or a DNA_PORT needs the new database. With the
stock database every other design is unaffected.

The seven patches applied in order to the `ofx` tree give build/src/nextpnr-ofx-prim file for file
(`DRY_RUN=0 bash toolchain/buildenv/check_prim_series.sh`, 2026-11-06: "tree identical"). Build (variant `ofx-prim`, `--version`
`ce3f7c18-ofx-prim`, log build/nextpnr-build/ofx-prim.build.log; one compiler warning, the pre-existing
`xilinx.cc` `-Wsign-compare`):

```
DRY_RUN=0 JOBS=4 VARIANT=ofx-prim PATCHES="nextpnr-pblock-xdc.patch nextpnr-router-region.patch nextpnr-pblock-replay.patch \
  nextpnr-pblock-routethru.patch nextpnr-partition-pins.patch nextpnr-pblock-lutff.patch nextpnr-carry-replay-order.patch \
  nextpnr-partition-pins-route.patch nextpnr-dsp-mask-areg.patch nextpnr-iserdes-const-pins.patch nextpnr-muxf7-mixed-loads.patch \
  nextpnr-io-buffer-params.patch nextpnr-mmcm-base-ties.patch nextpnr-bufh-region.patch nextpnr-diff-term.patch \
  nextpnr-cfg-in-use.patch nextpnr-clkout-unused.patch nextpnr-fifo.patch" bash toolchain/buildenv/build_nextpnr_variant.sh
python3 flow/prim_db.py --run        # build/prjxray-db-prim: the toolchain db plus the three segbits drafts
python3 flow/prim_eval.py <designs> --run
```

## Evaluation
- `flow/prim_eval.py` (new; CONFIG block, dry run by default): per design the toolchain build (build/gap/<d>/oxc7,
  yosys + stock nextpnr), then `ofx` and `ofx-prim` from the same yosys JSON, nextpnr through ofx/npwait.sh, one at a
  time, fasm2frames/xc7frames2bit with build/prjxray-db-prim. Both bitstreams and Vivado's are decoded with
  `flow/bit2fasm.py --db-root build/prjxray-db-prim/artix7` and compared with gap_report's rules (CLB and INT/clock-row
  tiles excluded; "by type" drops coordinates). Results build/gap/prim_eval_ofx-prim.json, logs
  build/gap/<d>/{ofx,ofx-prim}/nextpnr.log.
- Designs: the gap designs plus 20 new ones from `flow/prim_designs.py`; Vivado batch `prim` (vivado/run_gap.ps1).
- Vivado pin maps of placed FIFOs (`vivado/prim_pinmap.tcl`: get_bel_pins / get_site_pins / net per cell pin):
  C:\Users\finnf\open-dfx-xc7-vivado\build\prim_pinmap\<d>.pinmap.txt.

## io-buffer-params (G10)
- Cause: pack_io copied only the top-level port's attributes (XDC) to the PAD cell; fasm.cc reads DRIVE, SLEW,
  IOSTANDARD from there. An IOBUF/OBUF/IBUFDS parameter was dropped. iobuf (`IOBUF #(.DRIVE(8))`) got the default
  12 mA pattern `LVCMOS33_LVTTL.DRIVE.I12_I16` where Vivado writes `I12_I8`.
- Fix: before the buffers are decomposed, IOSTANDARD (unless "DEFAULT"), DRIVE, SLEW and DIFF_TERM parameters of the
  IO buffer are copied to each of its pads when the port has no such XDC property. DIFF_TERM is compared by name so
  no IdString is interned.
- Precedence: drv_xdc_over (OBUF DRIVE 4 SLEW SLOW in RTL, XDC DRIVE 16 SLEW FAST): Vivado uses the XDC values; ofx
  already matched and ofx-prim gives the same .frames.

## mmcm-base-ties
- Cause: MMCME2_BASE/PLLE2_BASE are renamed to *_ADV in prepare_clocking, after the first pack_constants. In that
  pass RST/PWRDWN tied to 0 were not invertible pins of a *_BASE cell, so they went to GND without inversion, and
  the MMCME2_ADV has no tied_pins entry, so PSEN/PSINCDEC/CLKIN2/DRP/PS ports of an MMCME2_BASE were left floating.
  Vivado writes `ZINV_RST/PWRDWN/PSEN/PSINCDEC` for an MMCME2_BASE and routes CLKIN2 from `CLK_IN2_INT`.
- Which is right: both flows already agree on MMCME2_ADV and PLLE2_ADV with the same constant ties (gap designs), and
  nextpnr's comment records the PLL case as working on hardware. The BASE case was the odd one out. After the fix
  the BASE cells are packed exactly as an ADV with those ties. Still not checked on silicon here.
- Fix: invertible_pins gains RST/PWRDWN of MMCME2_BASE and PLLE2_BASE; tied_pins gains the MMCME2_ADV inputs that an
  MMCME2_BASE lacks (CLKIN2 0, CLKINSEL 1, DADDR/DI/DCLK/DEN/DWE/PSCLK/PSEN/PSINCDEC 0), like PLLE2_ADV already has.
  An MMCME2_ADV whose RTL leaves those inputs open now gets them tied too.

## clkout-unused (G13 part)
- Vivado writes `CLKOUTn_CLKOUT1_HIGH_TIME[0]`, `LOW_TIME[0]` and `NO_COUNT` (FRACTIONAL_NO_COUNT on CLKOUT5/6) for every
  output that is unconnected and has no DIVIDE parameter (mmcme2_adv, mmcme2_base: CLKOUT2..6; plle2_adv: CLKOUT2..5);
  nextpnr wrote nothing. The patch writes that. An unconnected output with a DIVIDE parameter keeps the old
  behaviour (not measured).

## bufh-region (G7)
- Cause, in two parts: the BUFHCE's loads were not kept in its clock region (bufh: `Failed to route arc 0.0 of net
  'g1' ... to X56Y107/SLICE_X0Y0.CLKINV_OUT`), and a BUFHCE output was not on the dedicated-route list of
  route_clocks, so router2 failed even on loads inside the region (`... X56Y102 ...`, build/gap/prim_eval_run1.log).
- Fix: BUFHCE_BUFHCE joins BUFIO/BUFR in the post-packing pass that constrains a regional buffer's sinks to the
  region the clock reaches (the existing graph walk), and its output net is routed by route_clocks.
- Ablation: with only the route_clocks part the load lands at Y107 again and the same arc fails
  (build/gap/bufh/ablate/nextpnr_no_region.log).

## diff-term (G2)
- Cause: fasm.cc never wrote DIFF_TERM, and prjxray-db has no feature for it.
- Fix: on an HR-bank LVDS_25 input-only P half with DIFF_TERM TRUE (parameter or XDC), write
  `IOB_Y0.LVDS_25.IN_ONLY_DIFF_TERM` instead of the IN_ONLY key (see the segbits draft for why one key). DIFF_TERM
  on any other standard or bank is an error instead of being dropped. A bidirectional LVDS_25 pair writes nothing
  extra: Vivado's IOBUFDS bitstream is the same with and without DIFF_TERM.

## cfg-in-use (G11)
- Write `CFG_CENTER_MID.ICAP.IN_USE` for an ICAPE2 on ICAP_X0Y0 (a warning and nothing for the second site) and
  `CFG_CENTER_MID.DNA_PORT.IN_USE` when a DNA_PORT is placed.

## fifo (G5)
- Cause: no packer rule, so the FIFO18E1 cell never matched its bel ("no BELs remaining"); the chipdb generator also
  skips the FIFO36E1 site variant ("unsupported atm", gen/xilinx_gen.py), so there is no FIFO36E1 bel.
- Fix, without touching the chipdb (it stays byte-identical to the nightly's):
  - FIFO18E1 -> the FIFO18E1 bel of the lower RAMB18 site; FIFO36E1 -> the primary RAMBFIFO36E1 bel, its pins named
    after the RAMBFIFO36E1 site pins the FIFO36E1 variant reaches (from nextpnr-xilinx-meta's site_type JSON).
  - Pin map from Vivado: DI[0] on DIBDI0 (write port B) except in FIFO18_36/FIFO36_72, where the low half of DI is
    on port A; DIP likewise; DO direct. RDCLK/WRCLK/RSTREG/REGCE go to both halves of a FIFO36E1, RDEN/WREN/RST to the
    lower half only. RDRCLK (output register clock) gets RDCLK when DO_REG=1.
  - fasm: FIFO_MODE, IN_USE, the RAM widths of the half (READ_WIDTH_A/WRITE_WIDTH_B, or the SDP 36 set), DOA/DOB_REG =
    DO_REG, NO_CHANGE, ZINV bits of the RAM pins the FIFO pins sit on, EN_SYN, FIRST_WORD_FALL_THROUGH,
    FIFO_PORT_WIDTH_<n>, and the offsets as Vivado stores them: ALMOST_FULL_OFFSET + 1 when EN_SYN is FALSE,
    ALMOST_EMPTY_OFFSET - 1 with FIRST_WORD_FALL_THROUGH (fifo18e1_async, f18_async_o, f18_w9_fwft, f36_w9_async).
  - Refused with an error: EN_ECC_READ/WRITE, a non-zero INIT or SRVAL, FIFO36E1 DATA_WIDTH 4 (not measured).
- A first version put DI[0] on DIBDI0 in every mode. The decoded-feature comparison could not see that (it is a swap
  of fabric routes, and INT tiles are excluded); a per-pin comparison of the routed nets with Vivado's pin map found
  it: now 0 mismatches over 18/36/36/72 data pins of fifo18e1/fifo36e1/f18_w36/f36_w72 (each pin carries the same LFSR
  bit as in Vivado's netlist).

## xadc (G6, separate: nextpnr-xadc.patch, +52/-2, pack_io.cc, pack.h, fasm.cc; variant `ofx-prim-xadc`)
- Cause: the chipdb has no XADC bel. The generator takes a site's bels from nextpnr-xilinx-meta
  (`site_type_<type>.json`, gen/xilinx_device.py `get_site_type_data`), and the meta repo (8a3f5a09) has no
  `site_type_XADC.json`, so the MONITOR_BOT XADC site is imported empty. prjxray-db also has no bits for the MONITOR tile.
- Fix: docs/drafts/nextpnr-xilinx-meta-site_type_XADC.json (flat: one XADC_XADC bel whose pins are the 220 site pins
  of prjxray-db's tile_type_MONITOR_BOT.json; `cap` = input, `res` = output), a regenerated chipdb, the INIT segbits
  draft, and docs/drafts/prjxray-db-monitor-bot.ppips (the tile's 117 pips as pseudo-pips: fasm2frames rejected the
  site-pin pips without it; Vivado's XADC bitstreams have no MONITOR_BOT bits except INIT). nextpnr: XADC -> XADC_XADC
  (the rule is only made when the design has an XADC, so no IdString is interned otherwise), preplaced on its single
  site; a 0 tie on DCLK/CONVSTCLK goes back to GND (no site inverter in the flat site); INIT_40..INIT_5F written.
- Not done: the 3 INT_L/HCLK_L bits Vivado sets with an XADC; analog inputs; the site inverters.

## Results
See docs/gap-vivado.md "Primitive gap fixes (ofx-prim)" for the per-design table and the no-op check.

## Not known / not done
- Hardware behaviour of every change.
- The XDC reader of the `ofx` series stores any `set_property` on a port, so `set_property DIFF_TERM TRUE` works in
  `ofx-prim` (dt_xdc). The nextpnr-xdc2-constraints draft warns DIFF_TERM as "NOT applied"; combined with diff-term that
  warning would be wrong and needs dropping. With the base reader `set_property DIFF_TERM TRUE [get_ports {a b}]`
  (a braced list) crashes on `xdc.cc:57` `str.back() == '}'` (seen in the first dt_xdc; the XDC table of
  docs/open-vivado-roadmap.md lists that crash as fixed by the xdc draft); dt_xdc now uses one port per line.
- FIFO timing was not examined; nextpnr's log of f36_w72 never names u_fifo (0 matches), so its pins are probably
  untimed, as gap G9 found for ICAPE2. Not checked in the chipdb.
