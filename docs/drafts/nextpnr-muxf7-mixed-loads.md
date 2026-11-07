# DRAFT (not posted): MUXF7 whose output also feeds fabric breaks its MUXF8 tree in nextpnr-xilinx

Status: **compiled and tested offline 2026-11-05; muxf7f8 now builds; slice structure agrees with Vivado's (F7 and F8 in one slice, F7 outputs leave the slice); not bit-identical in CLB tiles (different placement); no hardware test.** Nothing pushed or posted.

Patch: docs/drafts/nextpnr-muxf7-mixed-loads.patch, against openXC7/nextpnr ce3f7c18, himbaechel/uarch/xilinx/pack.cc `XilinxPacker::pack_muxfs()` only (+16/-6).
- Worktree build/src/nextpnr-muxf7, build build/nextpnr-build/muxf7 (`ce3f7c18-muxf7`), log build/nextpnr-build/muxf7.build.log. Also in build/nextpnr-build/gapfix.

## Problem
pack_muxfs makes a MUXF7 a tree root unless its output has exactly one user, a MUXF8 data input. In designs/gap/muxf7f8 both MUXF7 outputs also go to fabric, so both became roots. legalise_muxf_tree then put a feed-through MUXF7 (S=GND) plus a feed-through LUT in front of each MUXF8 input: 5 SELMUX2_1 cells instead of 3 (build/gap/muxf7f8/oxc7/nextpnr.log line 55), and the placer gave up: `Unable to find legal placement for cell 'u_m8' of type 'SELMUX2_1' after 10001 attempts`.

The slice can do this directly: the F7AMUX/F7BMUX output also drives the AMUX/CMUX output and the A/C flip-flop mux. The slice validity check in xilinx_place.cc already accounts for an F7 output with more than one user (it claims that position's output mux).

## Change
A MUXF7 (MUXF8) stays in its parent's tree when exactly one of its users is a data input (I0/I1) of an unconstrained MUXF8 (MUXF9); other users of other cell types are allowed. A MUXF8 user on S, a constrained parent, or two parent muxes still make it a root, as before.

## Evidence (run 2026-11-05)
Command: `python3 flow/gap_patch_eval.py muxf7 muxf7f8 muxf8_only ram64m ram128x1d ram64x1d ram32m lutram_infer srl lut_ff carry4 qor_blinky qor_rv_soc qor_rv_mul --run`. Results build/gap/patch_eval_muxf7.json, log build/gap/patch_eval_muxf7.log.

- muxf7f8: stock FAIL (as above); patched: placed, routed, bitstream written (build/gap/muxf7f8/muxf7/nextpnr.log: `Created 3 SELMUX2_1 cells`). Vivado utilisation for the same RTL: 2 F7 Muxes, 1 F8 Mux (build/gap/muxf7f8/viv/util.rpt).
- Decoded non-CLB/non-INT features against Vivado: 0 / 0 (by type and exact).
- CLB-level comparison (the gap diff excludes CLB tiles, so this was checked separately on the decoded FASM; F7/F8-related slice features):

| flow | slice | F7/F8 features |
|---|---|---|
| Vivado (build/gap/muxf7f8/viv/muxf7f8.viv.fasm) | CLBLM_R_X41Y49.SLICEL_X1 | AOUTMUX.F7, COUTMUX.F7, BFFMUX.F8 |
| openXC7 patched (build/gap/muxf7f8/muxf7/muxf7f8.dec.fasm) | CLBLM_R_X41Y51.SLICEM_X0 | AOUTMUX.F7, CFFMUX.F7, BOUTMUX.F8 |

Both put both F7s and the F8 in one slice and take both F7 outputs out of that slice while they also feed the F8. They differ in which output is registered in the same slice (Vivado registers the F8 output in BFF; openXC7 registers the second F7 output in CFF). That is a placement choice, not a different structure. No simulation of the openXC7 bitstream was done for this design.

## Regression
FASM and .frames identical to stock for muxf8_only, ram64m, ram128x1d, ram64x1d, ram32m, lutram_infer, srl, lut_ff, carry4, qor_blinky, qor_rv_soc, qor_rv_mul (the DRAM designs use MUXF7/F8 trees built by pack_dram, which runs after pack_muxfs).

## Not known
- Hardware behaviour (no board).
- Only one mixed-load design was tested. A MUXF7 with fabric loads whose position's output mux is also needed by a 5LUT output or CARRY4 output in the same slice is left to the existing validity check; not tested.
