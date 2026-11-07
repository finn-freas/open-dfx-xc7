# openXC7 vs Vivado: measured gap analysis (xc7a35tcsg324-1)

Date: 2026-11-05. No hardware was used. Every number below comes from a run in build/gap/; the source file is named next to it. Effort figures are **estimates**, not measurements.

## Setup
- openXC7: Yosys 0.70+186 (oss-cad-suite 20261021), nextpnr-xilinx ce3f7c18, prjxray a5589d51, prjxray-db a8b09269 (toolchain/openxc7-BUILD-INFO.json; also build/gap/<design>/oxc7/status.json "versions").
- Vivado v2025.2, SW Build 6299465 (build/gap/vivado_gap/version.txt). It is a reference only.
- Part xc7a35tcsg324-1. The openXC7 chipdb is xc7a50t.
- Scripts (all new; CONFIG block at the top; long builds default to DRY_RUN):
  - flow/gap_designs.py: writes one tiny design per primitive into designs/gap/<name>/. Each design has a 64-bit LFSR stimulus folded onto 4 LEDs. `--qor` also copies the QoR designs.
  - flow/gap_build.py: openXC7 synth → pnr → fasm2frames → xc7frames2bit into build/gap/<name>/oxc7/. It records per-stage status, seconds and first error line in status.json. It uses the same commands as flow/build_openxc7.py, whose tool/DB helpers it imports.
  - vivado/build_gap.tcl + vivado/run_gap.ps1: one Vivado session per batch, non-project flow. Per design it writes times.txt, status.txt, util/timing/drc reports, worst_paths.txt and the .bit. Logs are in build/gap/vivado_<tag>/vivado.log.
  - flow/gap_report.py: ingests the Vivado outputs into build/gap/<name>/viv/ and decodes the Vivado .bit with flow/bit2fasm.py --verbose.
    - It counts unknown bits and maps them to tile and tile-relative segbit through tilegrid.json.
    - It also decodes the openXC7 .bit with the same decoder and diffs the two (CLB and INT/routing tiles excluded).
    - It writes build/gap/<name>/report.json and fasm_diff.json.
  - flow/gap_xadc_segbits.py: derives the XADC INIT bit map (see drafts).
- **gapfix build (added 2026-11-05):** nextpnr ce3f7c18 + the three nextpnr drafts G1, G3, G8 (build/nextpnr-build/gapfix, worktree build/src/nextpnr-gapfix), and yosys with the G4 clkbufmap draft loaded as a plugin (build/yosys-plugin/clkbufmap_gapfix.so; yosys itself could not be rebuilt, see docs/drafts/yosys-clkbufmap-keep-buffer-inputs.md). Same chipdb, prjxray-db, fasm2frames and decoder as before. Outputs: build/gap/<design>/gapfix/, per design build/gap/<design>/report_gapfix.json and fasm_diff_gapfix.json, summaries build/gap/summary_<tag>_gapfix.json, table build/gap/before_after.md (flow/gap_before_after.py). Run script: build/gap/gapfix_run.sh.
- Vivado batches: gap (first 44 designs), gap2 (variants, XADC fuzz), gap3 (QoR, fixes), gap4 (5 ns QoR, idelay_loc), gap5 (QoR with path dump). Vivado jobs ran one at a time.
  - The lut_ff Vivado log was overwritten by the gap batch; its reports and bit are kept.
- Diff column: decoded features present in only one flow, excluding CLB and INT/interface/clock-row tiles. "exact" compares tile names; "by type" strips tile coordinates and RAMB18_Y0/Y1 and DSP_0/1 site indices.
  - Every Vivado build also sets 8 features on the PUDC_B/EMCCLK IOB pair (LIOB33_X0Y43: PULLUP/IN on IOB_Y0, PULLDOWN on IOB_Y1, SLEW.FAST) that openXC7 never sets. They are excluded from the diff column and listed under gap G13.

## Device facts (Vivado, build/gap/vivado_gap/device_sites.txt)
- ODELAYE2 sites: 0. IDELAYE2: 250. IDELAYCTRL: 5. MMCME2_ADV: 5. PLLE2_ADV: 5. XADC: 1. DSP48E1: 120. RAMB18E1: 75.
- GTPE2_CHANNEL: 4 sites, GTPE2_COMMON: 1, IBUFDS_GTE2: 2 exist in Vivado's model of xc7a35tcsg324-1.
- prjxray-db package_pins.csv for this package lists 0 MGT pins. **GTP was not tested** (no bonded reference clock or serial pins in the package data).

## Primitive table
Columns synth/pnr/fasm/bitstream = openXC7 stage results (first failing stage marked). Logs: build/gap/<design>/oxc7/{yosys,nextpnr,fasm2frames,xc7frames2bit}.log, build/gap/<design>/viv/*.rpt. Combined source: build/gap/primitive_table.md.

| design | synth | pnr | fasm | bitstream | Vivado | Vivado unknown bits | diff viv-only / oxc7-only exact (by type) | after: gapfix build, diff exact (by type) |
|---|---|---|---|---|---|---|---|---|
| lut_ff (LUT6, FDRE/FDSE/FDCE/FDPE) | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| carry4 (CARRY4 + adder) | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| muxf7f8 (F7 outputs also used in fabric) | ok | **FAIL** | - | - | ok | 0 | - | ok, 0 / 0 (0 / 0) |
| muxf8_only | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| srl (SRL16E, SRLC32E cascade) | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| ram32m | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| ram64m | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| ram64x1d | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| ram128x1d | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| lutram_infer | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| ramb18e1 (TDP 18/9) | ok | ok | ok | ok | ok | 0 | 322 / 452 (26 / 23) | ok, 322 / 452 (26 / 23) |
| ramb36e1 (TDP 36) | ok | ok | ok | ok | ok | 0 | 486 / 564 (2 / 36) | ok, 486 / 564 (2 / 36) |
| ramb36_cascade (2x RAMB36 64Kx1) | ok | ok | ok | ok | ok | 0 | 546 / 627 (4 / 36) | ok, 546 / 627 (4 / 36) |
| ramb36_ecc (WEBWE active, ECCPARITY used) | ok | ok | ok | ok | **FAIL** (DRC REQP-195, REQP-1886) | - | - | ok |
| ramb36_ecc2 (WEBWE=VCC, no ECCPARITY) | ok | ok | ok | ok | ok | 0 | 272 / 422 (4 / 42) | ok, 272 / 422 (4 / 42) |
| bram_infer | ok | ok | ok | ok | ok | 0 | 269 / 350 (2 / 40) | ok, 269 / 350 (2 / 40) |
| fifo18e1 | ok | **FAIL** | - | - | ok | 2 (BRAM_L) | - | **FAIL** (pnr) |
| fifo18e1_async | ok | **FAIL** | - | - | ok | 2 (BRAM_L) | - | **FAIL** (pnr) |
| fifo36e1 | ok | **FAIL** | - | - | ok | 2 (BRAM_L) | - | **FAIL** (pnr) |
| dsp48e1 | ok | ok | ok | ok | ok | 0 | 104 / 102 (2 / 0) | ok, 104 / 104 (0 / 0) |
| dsp_cascade (ACOUT/PCOUT) | ok | ok | ok | ok | ok | 0 | 206 / 202 (2 / 0) | ok, 206 / 206 (0 / 0) |
| dsp_patdet | ok | ok | ok | ok | ok | 0 | 95 / 91 (4 / 0) | ok, 95 / 95 (0 / 0) |
| dsp_infer | ok | ok | ok | ok | ok | 0 | 109 / 107 (2 / 0) | ok, 109 / 109 (0 / 0) |
| mmcme2_adv | ok | ok | ok | ok | ok | 0 | 73 / 58 (15 / 0) | ok, 73 / 58 (15 / 0) |
| mmcme2_base | ok | ok | ok | ok | ok | 0 | 65 / 46 (20 / 1) | ok, 65 / 46 (20 / 1) |
| plle2_adv | ok | ok | ok | ok | ok | 0 | 72 / 60 (12 / 0) | ok, 72 / 60 (12 / 0) |
| bufg | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| bufgctrl (BUFGCTRL, BUFGCE) | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| bufh (BUFH, BUFHCE) | ok | **FAIL** | - | - | ok | 0 | - | **FAIL** (pnr) |
| bufr (pin also clocks fabric) | ok | **FAIL** | - | - | ok | 0 | - | ok, 0 / 0 (0 / 0) |
| bufr_pin (dedicated pin) | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| bufio_iddr (pin also clocks fabric) | ok | **FAIL** | - | - | ok | 0 | - | ok, 0 / 4 (0 / 4) |
| bufio_pin (dedicated pin) | ok | ok | ok | ok | ok | 0 | 0 / 4 (0 / 4) | ok, 0 / 4 (0 / 4) |
| idelay (IDELAYCTRL + IDELAYE2, IODELAY_GROUP) | ok | ok | ok | ok | **FAIL** (Place 30-578) | - | - | ok |
| idelay_nogrp | ok | ok | ok | ok | **FAIL** (Place 30-578) | - | - | ok (frames identical to before) |
| idelay_loc (IDELAYCTRL LOC'd) | ok | ok | ok | ok | ok | 0 | 1 / 1 (1 / 0) | ok, 1 / 1 (1 / 0) |
| odelay | ok | **FAIL** (no ODELAY in HR banks) | - | - | **FAIL** (UTLZ-1: 0 ODELAYE2 sites) | - | - | **FAIL** (pnr) |
| iserdes (BUFIO/BUFR from shared pin, all pins tied) | ok | **FAIL** | - | - | ok | 0 | - | ok, 0 / 1 (0 / 1) |
| iserdes_pin | ok | **FAIL** | - | - | ok | 0 | - | ok, 0 / 1 (0 / 1) |
| iserdes_noshift | ok | **FAIL** | - | - | ok | 0 | - | ok, 0 / 1 (0 / 1) |
| iserdes_min (unused pins left open) | ok | ok | ok | ok | ok | 0 | 0 / 1 (0 / 1) | ok, 0 / 1 (0 / 1) |
| oserdes (BUFIO/BUFR from shared pin) | ok | **FAIL** | - | - | ok | 0 | - | ok, 7 / 2 (7 / 2) |
| oserdes_pin | ok | ok | ok | ok | ok | 0 | 7 / 2 (7 / 2) | ok, 7 / 2 (7 / 2) |
| iddr_oddr | ok | ok | ok | ok | ok | 0 | 4 / 10 (4 / 10) | ok, 4 / 10 (4 / 10) |
| diff_lvds (IBUFDS DIFF_TERM TRUE + OBUFDS, LVDS_25) | ok | ok | ok | ok | ok | 6 (LIOB33_X0Y91) | 0 / 1 (0 / 1) | ok, 0 / 1 (0 / 1) |
| diff_lvds_noterm | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| diff_tmds (OBUFDS TMDS_33) | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| iobufds (LVDS_25) | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| iobuf (LVCMOS33 DRIVE 8) | ok | ok | ok | ok | ok | 0 | 1 / 1 (1 / 1) | ok, 1 / 1 (1 / 1) |
| startupe2 | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| icape2 | ok | ok | ok | ok | ok | 3 (CFG_CENTER_MID) | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| frame_ecce2 | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| xadc | ok | **FAIL** | - | - | ok | 8 (MONITOR_BOT 5, INT_L 2, HCLK_L 1) | - | **FAIL** (pnr) |
| dna_port | ok | ok | ok | ok | ok | 3 (CFG_CENTER_MID) | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| usr_accesse2 | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| bscane2 | ok | ok | ok | ok | ok | 0 | 0 / 0 (0 / 0) | ok, 0 / 0 (0 / 0) |
| GTPE2 | not tested (see Device facts) | | | | | | | |

XADC fuzz builds xadc_fz_{none,all,0..8} (Vivado only): 3 / 515 / 259 unknown bits each (build/gap/report_gap2.md).

After column (gapfix): result of the same RTL and XDC through the gapfix build, compared with the same Vivado bitstream (build/gap/<design>/report_gapfix.json). Of 61 designs built both ways, 40 give .frames byte-identical to before; 8 differ on purpose (bufg, bufgctrl, the four dsp_*, qor_rv_mul, qor_rv_mul_t5); 7 build now and did not before (muxf7f8, bufr, bufio_iddr, oserdes, iserdes, iserdes_pin, iserdes_noshift); 6 still fail (bufh, fifo18e1, fifo18e1_async, fifo36e1, odelay, xadc) with the same first error as before. The gapfix yosys JSON equals the old one in 54 designs once the auto-generated `$auto$clkbufmap...cc:<line>` cell names are ignored; the 7 others are the designs with a clock buffer on a pin that also clocks fabric.

First error text per failing openXC7 stage (build/gap/<design>/oxc7/nextpnr.log):
- muxf7f8: `Unable to find legal placement for cell 'u_m8' of type 'SELMUX2_1' after 10001 attempts`
- fifo18e1, fifo18e1_async: `Unable to place cell 'u_fifo', no BELs remaining to implement cell type 'FIFO18E1'`; fifo36e1: same for 'FIFO36E1'
- bufh: `Failed to route arc 0.0 of net 'g1', from X60Y78/BUFHCE_X0Y0.O to X56Y107/SLICE_X0Y0.CLKINV_OUT` (load placed outside the BUFH's clock region)
- bufr: `Failed to route arc 4.0 of net ... from X60Y103/BUFGCTRL_X0Y0.O to X113Y130/BUFR_X0Y1.I`
- bufio_iddr: `... from X60Y103/BUFGCTRL_X0Y0.O to X113Y78/BUFIO_X0Y0.I`; oserdes: same shape to BUFIO_X0Y2.I
  - yosys.log: `Inserting BUFG on ...` (CLKBUFMAP). The BUFG sits in front of the BUFIO/BUFR.
- odelay: `BEL X114Y82/IOB_X0Y1.IOB33.OUTBUF~IOB33 is located on a high range bank. High range banks do not have ODELAY`
- iserdes: `Failed to route arc 0.0 of net '$PACKER_VCC_NET', from X0Y0/VCC to X113Y75/ILOGIC_X0Y0.OCLKBINV_OUT`; iserdes_pin: `... '$PACKER_GND_NET' ... ILOGIC_X0Y0.SHIFTIN2`; iserdes_noshift: `... ILOGIC_X0Y0.DDLY`
- xadc: `Unable to place cell 'u_xadc', no BELs remaining to implement cell type 'XADC'`

Vivado failures (build/gap/<design>/viv/status.txt, build/gap/vivado_<tag>/vivado.log):
- ramb36_ecc: DRC REQP-195 (ECCPARITY used with EN_ECC_READ and EN_ECC_WRITE) and REQP-1886 (WEBWE must be VCC with EN_ECC_WRITE). openXC7 built the same RTL without complaint.
- idelay, idelay_nogrp: `[Place 30-578] Found un-associated IO delay instances`. The cause was not found; with `LOC IDELAYCTRL_X1Y1` (idelay_loc) it builds. Vivado also gives a critical warning that REFCLK is 100 MHz while REFCLK_FREQUENCY=200 (the test design's choice).

Notable bit differences in designs that build in both (build/gap/<design>/fasm_diff.json):
- DSP48E1 (all four): Vivado sets AREG_1/BREG_1; openXC7 does not. dsp_patdet: Vivado sets MASK[46], MASK[47] (mask 48'hffff_ffff_0000); openXC7 truncates MASK to 46 bits.
- diff_lvds: 6 Vivado-only bits that prjxray-db cannot decode. They go away with DIFF_TERM FALSE (diff_lvds_noterm: 0 unknown, 0 diff). openXC7 never writes DIFF_TERM.
- iobuf: Vivado DRIVE.I12_I8 vs openXC7 DRIVE.I12_I16 for an IOBUF instantiated with DRIVE(8). nextpnr fasm.cc reads DRIVE only from the pad attribute (XDC), not from the buffer's parameter.
- mmcme2_base: Vivado sets MMCME2_ADV.ZINV_RST/PWRDWN/PSEN/PSINCDEC; openXC7 does not for MMCME2_BASE, but does for MMCME2_ADV with the same ties (mmcme2_adv diff has no ZINV entries).
  - nextpnr's comments say this bit's polarity was fixed after a hardware observation. **Which build is correct on silicon is unverified.**
- mmcme2_adv/base, plle2_adv: Vivado writes HIGH_TIME/LOW_TIME/NO_COUNT for unused CLKOUT2..6; openXC7 leaves them 0 (unused outputs).
- oserdes_pin: openXC7 writes OSERDES.DATA_RATE_TQ.BUF where the RTL says DATA_RATE_TQ "SDR" and Vivado writes SDR. Vivado also sets IS_D5..D8_INVERTED and TDDR.SRUSED.
- iddr_oddr, bufio_pin: openXC7 sets ILOGIC IFF.ZSRVAL_Q1..Q4 and OLOGIC ODDR.SRUSED/ZSRVAL_OQ where Vivado does not.
- iserdes_min: openXC7 sets IFF.ZINV_OCLK, Vivado does not (OCLK unused).
- idelay_loc: Vivado IDELAY_Y0.IS_DATAIN_INVERTED vs openXC7 ILOGIC_Y0.ZINV_D.
- BRAM designs: openXC7 sets CASCOUT_ARD/BWR_ACTIVE and BRAM_ADDR*->CASCIN* pips on non-cascaded BRAMs. Vivado writes ZALMOST_*_OFFSET defaults in RAM mode.

## Primitive gap fixes (`ofx-prim`, 2026-11-06)
Drafts: docs/drafts/nextpnr-prim-gaps.md (seven nextpnr patches on the `ofx` series, variant `ofx-prim`),
docs/drafts/nextpnr-xadc.patch (variant `ofx-prim-xadc`, needs a regenerated chipdb), docs/drafts/prjxray-db-prim-segbits.md
(DIFF_TERM, FIFO width code, ICAP/DNA_PORT enables), docs/drafts/prjxray-db-xadc-init.segbits and
docs/drafts/prjxray-db-monitor-bot.ppips. Not on hardware. Not in install/patches.

- Run: `python3 flow/prim_eval.py <designs> --run` (log build/gap/prim_eval_all.log, results
  build/gap/prim_eval_ofx-prim.json, table build/gap/prim_table.md from flow/prim_table.py). `ofx` and `ofx-prim` get
  the same yosys JSON (build/gap/<d>/oxc7), nextpnr ce3f7c18-ofx / ce3f7c18-ofx-prim with the nightly chipdb, seed 1;
  fasm2frames and every decode use build/prjxray-db-prim (the toolchain's prjxray-db plus the three segbits drafts,
  `flow/prim_db.py --run`). The Vivado column is decoded with the same database, so a bit the drafts explain is no
  longer "unknown".
- New designs: 20 from flow/prim_designs.py, Vivado batch `prim` (C:\Users\finnf\open-dfx-xc7-vivado\build\prim\).
  Two Vivado jobs overlapped once: this batch and another agent's started in the same second (05:06:40).
- Diff columns as above (CLB, INT, clock-row tiles excluded); "exact" also differs when nextpnr picks another site
  than Vivado (BRAM tile, CMT), "by type" does not.

| design | Vivado tag | Vivado unknown bits (draft db) | ofx | ofx vs Vivado exact (by type) | ofx-prim | ofx-prim vs Vivado exact (by type) | .frames ofx-prim = ofx |
|---|---|---|---|---|---|---|---|
| bram_infer | gap | 0 | ok | 269 / 350 (2 / 40) | ok | 269 / 350 (2 / 40) | yes |
| bscane2 | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| bufg | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| bufgctrl | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| bufh | gap | 0 | **FAIL** (pnr) | - | ok | 0 / 0 (0 / 0) | - |
| bufio_iddr | gap | 0 | **FAIL** (pnr) | - | **FAIL** (pnr) | - | - |
| bufio_pin | gap2 | 0 | ok | 0 / 4 (0 / 4) | ok | 0 / 4 (0 / 4) | yes |
| bufr | gap | 0 | **FAIL** (pnr) | - | **FAIL** (pnr) | - | - |
| bufr_pin | gap2 | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| carry4 | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| diff_lvds | gap | 0 | ok | 1 / 1 (1 / 1) | ok | 0 / 0 (0 / 0) | no |
| diff_lvds_noterm | gap2 | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| diff_tmds | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| dna_port | gap | 0 | ok | 1 / 0 (1 / 0) | ok | 0 / 0 (0 / 0) | no |
| dna_port2 | prim | 0 | ok | 1 / 0 (1 / 0) | ok | 0 / 0 (0 / 0) | no |
| drv_obuf | prim | 0 | ok | 3 / 3 (3 / 0) | ok | 0 / 0 (0 / 0) | no |
| drv_xdc_over | prim | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| dsp48e1 | gap | 0 | ok | 104 / 104 (0 / 0) | ok | 104 / 104 (0 / 0) | yes |
| dsp_cascade | gap | 0 | ok | 206 / 206 (0 / 0) | ok | 206 / 206 (0 / 0) | yes |
| dsp_infer | gap | 0 | ok | 109 / 109 (0 / 0) | ok | 109 / 109 (0 / 0) | yes |
| dsp_patdet | gap | 0 | ok | 95 / 95 (0 / 0) | ok | 95 / 95 (0 / 0) | yes |
| dt_a | prim | 0 | ok | 7 / 7 (2 / 1) | ok | 0 / 0 (0 / 0) | no |
| dt_a_none | prim | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| dt_b | prim | 0 | ok | 7 / 7 (2 / 1) | ok | 0 / 0 (0 / 0) | no |
| dt_xdc | prim | 0 | ok | 2 / 2 (2 / 1) | ok | 0 / 0 (0 / 0) | no |
| f18_async_o | prim | 0 | **FAIL** (pnr) | - | ok | 182 / 182 (0 / 0) | - |
| f18_w36 | prim | 0 | **FAIL** (pnr) | - | ok | 0 / 0 (0 / 0) | - |
| f18_w4 | prim | 0 | **FAIL** (pnr) | - | ok | 183 / 183 (0 / 0) | - |
| f18_w9_fwft | prim | 0 | **FAIL** (pnr) | - | ok | 184 / 184 (0 / 0) | - |
| f36_w18 | prim | 0 | **FAIL** (pnr) | - | ok | 262 / 262 (0 / 0) | - |
| f36_w72 | prim | 0 | **FAIL** (pnr) | - | ok | 262 / 262 (0 / 0) | - |
| f36_w9_async | prim | 0 | **FAIL** (pnr) | - | ok | 0 / 0 (0 / 0) | - |
| fifo18e1 | gap | 0 | **FAIL** (pnr) | - | ok | 183 / 183 (0 / 0) | - |
| fifo18e1_async | gap2 | 0 | **FAIL** (pnr) | - | ok | 184 / 184 (0 / 0) | - |
| fifo36e1 | gap | 0 | **FAIL** (pnr) | - | ok | 0 / 0 (0 / 0) | - |
| frame_ecce2 | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| icap_dna | prim | 0 | ok | 2 / 0 (2 / 0) | ok | 0 / 0 (0 / 0) | no |
| icape2 | gap | 0 | ok | 1 / 0 (1 / 0) | ok | 0 / 0 (0 / 0) | no |
| icape2_x16 | prim | 0 | ok | 1 / 0 (1 / 0) | ok | 0 / 0 (0 / 0) | no |
| icape2_x8 | prim | 0 | ok | 1 / 0 (1 / 0) | ok | 0 / 0 (0 / 0) | no |
| iddr_oddr | gap | 0 | ok | 4 / 10 (4 / 10) | ok | 4 / 10 (4 / 10) | yes |
| idelay | - | - | ok | - | ok | - | yes |
| idelay_loc | gap4 | 0 | ok | 1 / 1 (1 / 0) | ok | 1 / 1 (1 / 0) | yes |
| idelay_nogrp | - | - | ok | - | ok | - | yes |
| iobuf | gap | 0 | ok | 1 / 1 (1 / 1) | ok | 0 / 0 (0 / 0) | no |
| iobufds | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| iserdes | gap | 0 | **FAIL** (pnr) | - | **FAIL** (pnr) | - | - |
| iserdes_min | gap2 | 0 | ok | 0 / 1 (0 / 1) | ok | 0 / 1 (0 / 1) | yes |
| iserdes_noshift | gap2 | 0 | ok | 0 / 1 (0 / 1) | ok | 0 / 1 (0 / 1) | yes |
| iserdes_pin | gap2 | 0 | ok | 0 / 1 (0 / 1) | ok | 0 / 1 (0 / 1) | yes |
| lut_ff | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| lutram_infer | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| mmcme2_adv | gap | 0 | ok | 73 / 58 (15 / 0) | ok | 73 / 73 (0 / 0) | no |
| mmcme2_base | gap | 0 | ok | 65 / 46 (20 / 1) | ok | 65 / 65 (0 / 0) | no |
| mmcme2_base_rst | prim | 0 | ok | 64 / 46 (19 / 1) | ok | 64 / 64 (0 / 0) | no |
| muxf7f8 | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| muxf8_only | gap2 | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| odelay | - | - | **FAIL** (pnr) | - | **FAIL** (pnr) | - | - |
| oserdes | gap | 0 | **FAIL** (pnr) | - | **FAIL** (pnr) | - | - |
| oserdes_pin | gap2 | 0 | ok | 7 / 2 (7 / 2) | ok | 7 / 2 (7 / 2) | yes |
| plle2_adv | gap | 0 | ok | 72 / 60 (12 / 0) | ok | 72 / 72 (0 / 0) | no |
| plle2_base | prim | 0 | ok | 70 / 56 (14 / 0) | ok | 70 / 70 (0 / 0) | no |
| ram128x1d | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| ram32m | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| ram64m | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| ram64x1d | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| ramb18e1 | gap | 0 | ok | 322 / 452 (26 / 23) | ok | 322 / 452 (26 / 23) | yes |
| ramb36_cascade | gap | 0 | ok | 546 / 627 (4 / 36) | ok | 546 / 627 (4 / 36) | yes |
| ramb36_ecc | - | - | ok | - | ok | - | yes |
| ramb36_ecc2 | gap3 | 0 | ok | 272 / 422 (4 / 42) | ok | 272 / 422 (4 / 42) | yes |
| ramb36e1 | gap | 0 | ok | 486 / 564 (2 / 36) | ok | 486 / 564 (2 / 36) | yes |
| srl | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| startupe2 | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| usr_accesse2 | gap | 0 | ok | 0 / 0 (0 / 0) | ok | 0 / 0 (0 / 0) | yes |
| xadc | gap | 8 | **FAIL** (pnr) | - | **FAIL** (pnr) | - | - |
| xadc_idle | prim | 7 | **FAIL** (pnr) | - | **FAIL** (pnr) | - | - |

Result over 76 gap designs:
- 41 give `.frames` byte-identical to `ofx`. These include every design that uses none of the changed features.
- 17 differ, each only where it uses a changed feature: DIFF_TERM (diff_lvds, dt_a, dt_b, dt_xdc), an IO buffer
  parameter (iobuf, drv_obuf), ICAPE2/DNA_PORT (icape2, icape2_x8, icape2_x16, dna_port, dna_port2, icap_dna), MMCM/PLL
  (mmcme2_adv, mmcme2_base, mmcme2_base_rst, plle2_adv, plle2_base). All 17 are 0 / 0 by type against Vivado.
- 11 build now and did not with `ofx`: bufh and the 10 FIFO designs, all 0 / 0 by type.
- 7 fail with both, at the same stage as before: bufio_iddr, bufr, iserdes, oserdes (they need the yosys clkbufmap draft,
  which this run does not load), odelay (not a gap), xadc and xadc_idle (no XADC bel; see the XADC variant below).

FIFO data pins: the feature diff cannot see a swap of fabric routes onto the data pins (INT tiles are excluded).
A per-pin check compares the routed net on each DIADI/DIBDI/DIPADIP/DIPBDIP bel pin with the net on the same site pin in
Vivado's placed netlist (vivado/prim_pinmap.tcl): 0 mismatches over 18 (fifo18e1), 36 (fifo36e1), 36 (f18_w36) and
72 (f36_w72) pins. A first version of the patch failed this check for the two full-width modes (fixed before the run
above).

XADC (variant `ofx-prim-xadc` = `ofx-prim` + docs/drafts/nextpnr-xadc.patch, chipdb build/chipdb-prim/chipdb-xc7a50t.bin
from `toolchain/buildenv/gen_chipdb.sh` with the nextpnr-xilinx-meta copy build/chipdb-prim/meta plus
docs/drafts/nextpnr-xilinx-meta-site_type_XADC.json, written by flow/prim_xadc_meta.py from prjxray-db's MONITOR_BOT site
pins; 51 s, 1.8 GB peak, build/chipdb-prim/gen.log). Database build/prjxray-db-prim-xadc (also the INIT segbits and the
MONITOR_BOT pseudo-pips). Results build/gap/prim_eval_ofx-prim-xadc.json, log build/gap/prim_eval_xadc.log:

| design | ofx-prim-xadc | vs Vivado exact (by type) | Vivado bits left unknown |
|---|---|---|---|
| xadc | ok | 0 / 0 (0 / 0) | 3: INT_L_X18Y79 26_00 27_40, HCLK_L_X49Y78 25_13 |
| xadc_idle (DCLK, DEN, DADDR tied 0) | ok | 0 / 0 (0 / 0) | 2: INT_L_X18Y79 26_00, HCLK_L_X49Y78 25_13 |
| xadc_fz_none, xadc_fz_all, xadc_fz_0, xadc_fz_5 | ok | 0 / 0 (0 / 0) each | 3 each (same) |
| lut_ff | ok, `.frames` identical to ofx | 0 / 0 | 0 |

- The XADC FASM matches Vivado's on all 512 INIT bits (xadc_fz_all). The three base bits are in INT_L/HCLK_L tiles; the
  openXC7 bitstream does not have them. 27_40 depends on DCLK being clocked (gone in xadc_idle). Their meaning is
  unknown; prjxray-db does not decode them.
- The new chipdb on other designs: blinky and rv_soc FASM identical to `ofx-prim` (build/ofx_prim_xadc_noop/); rv_ppa
  was not rerun with it.
- The XADC site in the meta file is flat (one bel, no site inverters), so IS_DCLK_INVERTED / IS_CONVSTCLK_INVERTED are
  refused; a 0 tie on those pins is routed as GND. VP/VN and VAUX analog inputs were not connected in any test.

No-op check of `ofx-prim` (install/noop_check.py through flow/prim_noop.py, same inputs as the `ofx` no-op of
docs/install.md; summary build/ofx_prim_noop/summary_blinky_rv_soc_rv_ppa.json, FASM check
build/ofx_prim_noop/fasm_check.json by flow/prim_noop_fasm.py):

| design | builds | result |
|---|---|---|
| blinky (stock reference) | 1 | `.frames` identical |
| rv_soc (stock reference) | 1 | FASM identical except one added line, `CFG_CENTER_MID_X46Y32.ICAP.IN_USE` (rv_soc has an ICAPE2); with the draft db the `.frames` differ from the reference in exactly 3 bits |
| rv_ppa / partpin2 | 10 | 4 module-proxy builds (xor_p, andn_p, add_p, rot_p) `.frames` identical; the 6 builds that contain the ICAPE2 (greybuf_p, grey_s, xor_n, andn_n, add_n, rot_n) differ only by that line, 3 bits each |

With the stock prjxray-db the 7 ICAPE2 builds stop in fasm2frames (`FasmLookupError ... ICAP.IN_USE`): the
cfg-in-use patch needs the database draft.

## QoR
Same RTL, same XDC. Logs: build/gap/<design>/oxc7/{yosys,nextpnr}.log and status.json; build/gap/<design>/viv/{util,timing}.rpt, times.txt, worst_paths.txt.
- qor_rv_soc: rv_soc with rm_slot replaced by a registered XOR core.
- qor_rv_mul: the same with picorv32 ENABLE_FAST_MUL=1, ENABLE_DIV=1.
- _t5: the same RTL with a 5 ns clock. nextpnr gets --freq 200 --timing-allow-fail; nextpnr then exits non-zero, but FASM and bitstream are written.

| design | flow | logic LUTs | LUT as memory | FF | CARRY4 | BRAM (RAMB36) | DSP | Fmax MHz | runtime s |
|---|---|---|---|---|---|---|---|---|---|
| blinky | openXC7 | 0 (yosys) / 56 LUT bels (nextpnr, all LUT1 carry feed-throughs) | 0 | 28 | 7 | 0 | 0 | 372.58 (nextpnr) | 9.0 / 12.5 |
| blinky | Vivado | 1 | 0 | 28 | 7 | 0 | 0 | 393.86 (WNS 7.461 @10 ns) | 84.3 |
| rv_soc @10 ns | openXC7 | 1054 (yosys) / 1747 LUT bels | 14 RAM32M | 764 | 100 (yosys 92) | 2 | 0 | 159.26 | 65.8 / 109.2 |
| rv_soc @10 ns | Vivado | 935 | 50 | 771 | 63 | 2 | 0 | 134.72 overall; 138.05 excluding ICAP paths | 101.7 / 115.8 |
| rv_soc @5 ns | openXC7 | same netlist | | | | | | 159.26 | 114.9 |
| rv_soc @5 ns | Vivado | 991 | 50 | 771 | 63 | 2 | 0 | 135.83 overall; 171.0 excluding ICAP | 279.2 / 208.5 |
| rv_mul @10 ns | openXC7 | 1402 / 2448 LUT bels | 14 RAM32M | 1073 | 159 (yosys 148) | 2 | 4 | 140.69 | 76.7 / 93.9 |
| rv_mul @10 ns | Vivado | 1378 | 50 | 1018 | 123 | 2 | 4 | 127.60 overall; 136.31 excluding ICAP | 115.1 / 150.6 |
| rv_mul @5 ns | openXC7 | same netlist | | | | | | 140.69 | 118.7 |
| rv_mul @5 ns | Vivado | 1433 | 50 | 1065 | 123 | 2 | 4 | 135.78 overall; 172.35 excluding ICAP | 218.9 / 176.7 |

How to read this:
- Runtime is the sum of the tool stages: openXC7 = yosys + nextpnr + fasm2frames + xc7frames2bit; Vivado = synth + opt + place + route + write_bitstream from times.txt (Vivado start-up and reports excluded).
- Two numbers are two runs. The machine was shared: other workers' gcc builds and Python jobs ran at load average 5–8 during the second openXC7 run (`uptime` in that run). Vivado ran from Windows at the same time as WSL jobs. **Runtime is only indicative.**
- "openXC7 Fmax" is nextpnr's own timing model. "Vivado Fmax" is 1000 / (period − WNS) from Vivado's signoff timer. They are **not the same model**; no cross-timing of one flow's result in the other tool's timer was done.
- Vivado's worst path in every rv design is FF → ICAPE2 (setup at u_icap/RDWRB, worst_paths.txt). nextpnr's critical-path reports never name u_icap (0 matches in nextpnr.log). So nextpnr appears not to time ICAPE2 pins at all; this is inferred from the logs, not checked in the chipdb.
- "Excluding ICAP" takes the worst slack over the 2000 worst unique-pin paths whose start and end are not u_icap pins.
- At 10 ns Vivado stops optimising once the constraint is met, so its 10 ns Fmax understates it. The 5 ns runs are the fairer comparison: Vivado 171.0 / 172.35 MHz (non-ICAP) vs nextpnr-reported 159.26 / 140.69 MHz.
- nextpnr's post-route Fmax was identical at --freq 100 and --freq 200 for both rv designs.
- gapfix build: nextpnr Fmax and LUT bel counts are unchanged for all five QoR builds (qor_blinky 372.58, qor_rv_soc(_t5) 159.26, qor_rv_mul(_t5) 140.69 MHz; build/gap/qor_*/report_gapfix.json). qor_blinky and qor_rv_soc(_t5) .frames are byte-identical to before; qor_rv_mul(_t5) differ only in DSP FASM lines (G1).
- LUT counts: Vivado "Slice LUTs" excludes route-through LUTs. nextpnr's SLICE_LUTX includes them (blinky: 56 LUT1 feed-throughs for 7 CARRY4, against Vivado's 1 LUT). Compare yosys logic LUTs with Vivado "LUT as Logic": +12.7 % (rv_soc, 1054 vs 935) and +1.7 % (rv_mul, 1402 vs 1378). CARRY4: +59 % / +29 %.

## Gaps, prioritised
Effort is an **estimate** (person-days for someone who knows the code base); none of it was measured.

| # | gap | evidence | kind | effort (estimate) | draft |
|---|---|---|---|---|---|
| G1 | DSP48E1 MASK[47:46] dropped; AREG/BREG=1 bits not written | dsp_* fasm_diff.json | silent bitstream difference (MASK: wrong pattern-detect when those bits are set) | 0.5 d + HW check | docs/drafts/nextpnr-dsp-mask-areg.{md,patch}. **Compiled and tested: all four dsp_* designs 0 / 0 by type against Vivado; only DSP FASM lines change** |
| G2 | DIFF_TERM ignored; prjxray-db has no feature for it | diff_lvds 6 unknown bits vs diff_lvds_noterm 0 | silent: no input termination | done (draft) | docs/drafts/nextpnr-prim-gaps.md (diff-term) + prjxray-db-prim-segbits.md. **After: diff_lvds, dt_a, dt_b, dt_xdc 0 / 0 exact; 17 LIOB33/RIOB33 pairs, 0 collisions; refused (error) for standards/banks not measured** |
| G3 | ISERDESE2 constant ties on cascade/feedback/OCLK/CLKDIVP pins unroutable | iserdes, iserdes_pin, iserdes_noshift vs iserdes_min | build fails | 0.5 d | docs/drafts/nextpnr-iserdes-const-pins.{md,patch}. **Compiled and tested (CLKDIVP added after the first run): iserdes_pin, iserdes_noshift build; 0 / 1 by type (the pre-existing ZINV_OCLK)** |
| G4 | yosys CLKBUFMAP puts a BUFG in front of BUFIO/BUFR when the pin also clocks fabric | bufr, bufio_iddr, oserdes vs bufr_pin, bufio_pin, oserdes_pin | build fails (workaround: dedicated pin or explicit IBUF/BUFG split) | 1 d (yosys clkbufmap: skip clock-buffer inputs) | docs/drafts/yosys-clkbufmap-keep-buffer-inputs.{md,patch}. **Tested as a plugin (yosys not rebuilt): bufr 0 / 0, bufio_iddr and oserdes build with the same residuals as their _pin variants; bufg/bufgctrl clock structure now matches Vivado's (all BUFGs from one HROW input)** |
| G5 | FIFO18E1/FIFO36E1 not supported by nextpnr | fifo* | build fails | done (draft) | nextpnr-prim-gaps.md (fifo) + prjxray-db-prim-segbits.md (width code: the "2 undocumented bits" are 3). **After: 10 FIFO designs build, 0 / 0 by type; data pins checked against Vivado's netlist** |
| G6 | XADC not supported by nextpnr; prjxray-db has no MONITOR segbits | xadc, xadc_fz_* | build fails | partly done (draft): the chipdb has no XADC site because nextpnr-xilinx-meta has no site_type_XADC.json | nextpnr-xadc.patch + site_type_XADC.json + prjxray-db-xadc-init.segbits + prjxray-db-monitor-bot.ppips. **After (variant ofx-prim-xadc, new chipdb): 6 XADC designs build, 0 / 0 exact; 3 INT_L/HCLK_L bits Vivado sets are still unknown and not written** |
| G7 | BUFH/BUFHCE loads not kept in the BUFH clock region | bufh | build fails | done (draft) | nextpnr-prim-gaps.md (bufh-region). **After: bufh 0 / 0 exact; region and dedicated routing both needed (ablation)** |
| G8 | MUXF7 whose output also feeds fabric, under a MUXF8 | muxf7f8 vs muxf8_only | build fails | 1–3 d (packer/validity) | docs/drafts/nextpnr-muxf7-mixed-loads.{md,patch}. **Compiled and tested: muxf7f8 builds, 0 / 0 outside CLB; in the CLB the F7/F8 slice structure agrees with Vivado, placement differs (not bit-identical)** |
| G9 | Timing: ICAPE2 pins untimed in nextpnr; Fmax gap on rv designs (nextpnr-reported 159/141 vs Vivado 171/172 MHz non-ICAP at 5 ns; different timers) | QoR table | QoR / signoff | large, open-ended | none |
| G10 | IOBUF/OBUF instance DRIVE parameter ignored (only XDC pad attribute read) | iobuf | silent drive-strength difference | done (draft) | nextpnr-prim-gaps.md (io-buffer-params; also SLEW/IOSTANDARD/DIFF_TERM). **After: iobuf, drv_obuf 0 / 0 exact; XDC still wins, as in Vivado (drv_xdc_over)** |
| G11 | DNA_PORT and ICAPE2 CFG_CENTER_MID bits never written by openXC7 | dna_port, icape2 (3 bits each) | unknown effect on silicon | done (draft) | nextpnr-prim-gaps.md (cfg-in-use) + prjxray-db-prim-segbits.md. **After: 6 designs 0 / 0; ICAP bits independent of ICAP_WIDTH. Effect on silicon still unknown** |
| G12 | No DRC: openXC7 accepts what Vivado rejects (ECC with active WEBWE and used ECCPARITY) | ramb36_ecc | silent misuse | per rule, small; overall large | none |
| G13 | Smaller defaults that differ: MMCME2_BASE ZINV_* vs ADV and unused CLKOUT counters (**done, draft: mmcm-base-ties, clkout-unused; MMCM/PLL designs 0 / 0 by type**); OSERDES DATA_RATE_TQ; ILOGIC/OLOGIC SR defaults; BRAM CASCOUT_*_ACTIVE; PUDC_B/EMCCLK IOB config | see bit differences above | probably benign, **unverified** | 1–2 d to align, HW needed to judge | none |
| — | ODELAYE2: not present on HR-only Artix-7. Both tools refuse it. | odelay | not a gap | — | — |
| — | GTPE2 | not tested | — | — | — |

## Not verified / open
- Nothing here ran on silicon. Whether the AREG_1/BREG_1, CFG_CENTER_MID, MMCM ZINV and default-value differences change behaviour is unknown.
- The DIFF_TERM bits were measured on 17 LIOB33/RIOB33 pairs, LVDS_25 only (docs/drafts/prjxray-db-prim-segbits.md).
- The `ofx-prim` changes (FIFO, DIFF_TERM, IO buffer parameters, BUFH, MMCM/PLL ties and counters, ICAP/DNA enables, XADC) match Vivado's decoded bitstreams; none ran on silicon.
- The three nextpnr drafts (G1, G3, G8) are compiled (build/nextpnr-build/{dsp,iserdes,muxf7,gapfix}) and tested against the gap designs; see the "after" column and docs/drafts/*.md. Regression: blinky and rv_soc (designs/, same JSON as build/openxc7/<d>/xc7a35tcsg324-1_s1) give FASM (ignoring the version comment line) and .frames identical to stock with each of dsp, iserdes, muxf7 and gapfix (build/gapfix_regress/result.txt).
- The yosys draft (G4) was tested only as a plugin built from the patched source against the oss-cad-suite yosys; a rebuilt yosys binary was not tested (no flex/bison; conda-forge download failed).
- The Vivado 30-578 IDELAY failure without LOC was not explained.
- The XADC "base" bits in INT_L_X18Y79 (26_00, 27_40) and HCLK_L_X49Y78 (25_13) are not explained. INT tile bits that prjxray-db does not decode are unexpected.
