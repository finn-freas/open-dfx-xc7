# nextpnr-dsp-cascade-place (draft, not posted)

Base: openXC7/nextpnr ce3f7c18 + the `qorfix` stack (nextpnr-dsp-mask-areg, nextpnr-iserdes-const-pins,
nextpnr-muxf7-mixed-loads, nextpnr-hardblock-timing). Applies with `git apply` on that stack (checked
2026-11-06 in a scratch worktree). +36/-7 in xilinx.cc, xilinx.h, xilinx_place.cc. Opt-in: `-o dsp-cascade-place`.

## Problem
A 32-tap systolic FIR (designs/qor/qor_fir, 32 DSP48E1 in a PCOUT -> PCIN chain, which yosys splits into
chains of 20 and 12) did not place: heap placer `Unable to find legal placement for cell '$qor_fir.v:37$mul$16'
of type 'DSP48E1_DSP48E1'` (build/qor/oxc7/base/fir_p5/s1/nextpnr.log); the static placer hung in strict
legalisation (build/qor/oxc7/dspq/fir_p5/s1/nextpnr.log, stopped).

Cause, from the code: `pack_dsp_xc7.cc` `walk_dsp` gives every cascaded DSP a fixed relative position: the upper
DSP of the same tile, then the lower DSP of the tile 5 rows up. BaseArch's `getClusterPlacement` uses these
offsets as they are. In xc7a50t each DSP column has 30 DSP tiles in 6 clock regions of 5 tiles (10 DSPs); the
step between tiles is 5 rows, but 6 across the HCLK rows and the BRKH row (prjxray-db
artix7/xc7a50t/tilegrid.json: steps {5: 24, 6: 5} in both DSP columns). tileconn.json shows the cascade wires
do cross those rows (DSP_L -> HCLK_DSP_L at grid delta -5, HCLK_DSP_L -> DSP_L at +1; BRKH_DSP_L likewise).
So any chain longer than 10 DSPs, which must cross a region boundary, had no legal position at all.

## Change
- The RAMB36 cascade already does this for BRAM (upstream `bram_cascade_next`): the next block is found along the
  chipdb wires. The patch makes that walk generic (`cascade_next(bel, out_pin, in_pin, bel_type)`) and adds
  `dsp_cascade_next` (PCOUT0 -> PCIN0 of a DSP48E1 bel).
- `getClusterPlacement` / `getClusterOffset` use it for a DSP48E1 cluster when `-o dsp-cascade-place` is given; the
  root keeps its absolute z (lower DSP), as BaseArch did.
- Off by default: without the option the binary takes the old path.

## Evidence (all 5 ns constraint, nextpnr timer unless said otherwise)
- No-op: without the option, `.frames` identical to the `qorfix` binary for rv_mul, rv_big, bram, rv_soc
  (build/qor/oxc7/dcp_noopt vs fix_static, `cmp`).
- FIR places and routes, bitstream written: heap placer 234.41 MHz (build/qor/oxc7/dcp_heap/fir_p5/s1), static
  placer 209.69 MHz (dcp_static). The 20-chain sits on DSP48_X0Y0..Y19 and the 12-chain on DSP48_X1Y18..Y29, both
  across a clock-region boundary.
- Vivado accepts every nextpnr DSP site of the static placement (1645 cells placed, 2 not) and times it at
  203.05 MHz (Vivado timer; C:\Users\finnf\open-dfx-xc7-vivado\build\qor_xtime\fir_p5_dcp_static_placed). Vivado's
  own result on the same RTL: 203.09 MHz. Option on, `.frames` identical to the qorfix build for blinky, rv_soc,
  bram, rv_mul and rv_big (no chain longer than 2). docs/qor-vivado.md Finding 9.

## Open
- `walk_dsp` still sets constr_y to the 5-row estimate; only the final placement follows the chipdb.
- yosys `xilinx_dsp` splits chains at 20 (MAX_DSP_CASCADE); a chain longer than a DSP column is not split here.
