# nextpnr-area-pack (draft, not posted)

Base: openXC7/nextpnr ce3f7c18 + the `qordsp` stack + nextpnr-muxf-const-inputs. Checked with `git apply` on a
scratch worktree of that stack (2026-11-06; the result is byte-identical to build/src/nextpnr-qorarea). +161/-8 in
himbaechel/uarch/xilinx/{pack_carry.cc, pack.cc, pack.h, xilinx.cc, xilinx.h}. nextpnr build `qorarea`
(build/nextpnr-build/qorarea; logs qorarea.build*.log, the only warning is the pre-existing xilinx.cc
sign-compare). Two options, both off by default: `-o carry-di-bypass` and `-o lut-pair[=N]`.

## Problem (docs/qor-vivado.md Finding 11)
Counted on the routed designs (flow/qor_area.py), nextpnr used more LUT sites than Vivado on the same yosys
netlist, for two reasons that are in the packer, not in yosys:
1. **Carry DI feed-throughs.** `pack_carries` drives every CARRY4 DI input that is not the only load of a LUT
   through a new LUT1 on the 5LUT of that position. On rv_soc that is 366 LUT1 (plus 145 for S inputs), i.e. 519
   of 1748 LUT bels are nextpnr-made. The slice has a direct path: the CY0 mux of each position selects O5 or the
   AX..DX bypass pin (`CARRY4.[A-D]CY0` set = O5; the FASM writer already writes the bypass leg as "no bit").
   Vivado uses the bypass for DI that comes from outside the slice.
2. **No LUT combining.** Vivado's synthesis pairs LUTs that share inputs into one LUT6 site (O6 + O5; rv_soc:
   115 dual-output sites). nextpnr only gets a pair when the placer happens to put two compatible LUTs in one
   site (65 on rv_soc), and Vivado itself, given the yosys netlist, makes only 41.

## Change
- `-o carry-di-bypass` (pack_carry.cc): a DI that no LUT of its own position drives stays connected to its net
  and is routed in through the bypass pin. The tags (`assign_cell_tags`) record it as that position's X-pin use,
  so the existing slice legality check (`x_net`) keeps the pin free of another bypass user (flip-flop D, F7/F8
  select, LUTRAM DI). Bit 0 of a chain root keeps the feed-through when CYINIT is connected (it may need AX).
  With the 5LUT free, an S input may also come from a single-load LUT6, and a DI LUT is only kept on the 5LUT when
  S and DI fit in five inputs together; otherwise DI takes the bypass.
- `-o lut-pair[=N]` (pack.cc `pair_luts`, before `pack_lutffs`): two free logic LUTs (not memory/SRL, not in a
  cluster, at most 5 inputs each) that share at least N inputs (default 2) and use at most 5 distinct inputs are
  put into one site as a 2-cell cluster (6LUT + 5LUT, as `constrain_lut6_2_pairs` does for LUT6_2 halves). Greedy,
  in cell order, each LUT takes the partner with the most shared inputs; the LUT that alone drives a flip-flop
  stays on O6 so `pack_lutffs` can still attach its FF.
- With either option a LUT whose only load is a CARRY4 in another cluster no longer counts as
  `only_drives_carry` (that flag assumed the load is the carry of its own site); without it the slice output
  mux of a paired O5 was not counted, and rv_mul failed to route (`Failed to route arc ... C5FF_Q`).

## Evidence
See docs/qor-vivado.md Finding 11: no-op without the options (`.frames` identical to the qordsp build), area and
Fmax before/after on blinky, rv_soc, rv_mul, rv_big, bram, fir, arty_ddr3 and arty_eth, and the bitstream-level
simulation (fasm2bels netlist of the bitstream running the rv_soc firmware test, flow/bit2netlist.sh).

## Open
- The pairing is greedy and placement-blind; it does not use the critical path. On bram it costs nextpnr Fmax
  (Finding 11), so it is not a candidate default as is.
- Feed-throughs for S inputs that come straight from a flip-flop (counters) are still LUT1s; Vivado also routes
  them through the LUT but does not count route-throughs as LUTs.
