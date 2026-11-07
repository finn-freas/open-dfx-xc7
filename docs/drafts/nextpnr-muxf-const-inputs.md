# nextpnr-muxf-const-inputs (draft, not posted)

Base: openXC7/nextpnr ce3f7c18 + the `qordsp` stack (qorfix drafts, nextpnr-dsp-cascade-place,
nextpnr-cell-timing-cal). +11/-1 in himbaechel/uarch/xilinx/pack.cc. Not an option: it only changes trees that
could not be placed before. nextpnr build `qorarea` (build/nextpnr-build/qorarea), together with nextpnr-area-pack.

## Problem
`synth_xilinx -widemux 5` makes MUXF7/MUXF8 trees (pmux2shiftx + muxcover). On rv_soc, rv_mul and rv_big every
nextpnr build failed with `Unable to find legal placement for cell '...fpga_hard_mux.genblk3.genblk1.mux8' of
type 'SELMUX2_1'` (build/qor/oxc7/fix_tmg_wm5/rv_soc_p5/s1/nextpnr.log), also with the G8 MUXF7 fix
(nextpnr-muxf7-mixed-loads).

Cause, from the netlist and the code: 8 of the 32 MUXF8 in rv_soc have a constant data input
(`I0 = 1'b0`; the MUXF7 below has `I1 = 1'b0`). `legalise_muxf_tree` gives such an input a feed-through MUXF7
(`feed_through_muxf`) but does not legalise that new MUXF7, so its own data input stays the constant net.
`constrain_muxf_tree` then walks into the constant's driver -- the PSEUDO_GND cell -- and constrains it into the
mux tree at a LUT position. That cluster has no legal placement, so the placer gives up on the root.

## Change
When the input of a MUXF8 (MUXF9) is not driven by a LUT, the feed-through mux created for it is legalised like
any other tree node, so its data input gets a feed-through LUT. Inputs driven by a LUT take the old path, so the
change does nothing on trees that placed before.

## Evidence (docs/qor-vivado.md Finding 12)
- With the fix, `-widemux 5` builds place and route with the static placer (`area_wm5_ref`, seed 1, nextpnr timer):
  rv_soc 135.39, rv_mul 101.61, rv_big 104.10 MHz (build/qor/oxc7/area_wm5_ref/<d>_p5/s1/nextpnr.log).
- Control, the same netlist and placer on the `qordsp` build without the fix: stays in "Strict legalising 1177
  cells" and was stopped after 1200 s (build/qor/oxc7/dcp_wm5/rv_soc_p5/s1/nextpnr.log).
- No change without widemux: `area_ref` `.frames` identical to `dcp_static`/`fix_static` on the six benchmarks.
- The fix does not make `-widemux` usable: the yosys `-widemux 5` netlist itself fails the rv_soc firmware test in
  netlist simulation (before nextpnr is involved) and in the fasm2bels simulation of its bitstream, and a formal
  check of the yosys netlists leaves `reg_pc`/`reg_next_pc` unproven. Widemux stays off for that reason. The
  bitstream-level correctness of the feed-through trees this fix creates is therefore not shown separately.
