# nextpnr-cell-timing-cal (draft, not posted)

Base: openXC7/nextpnr ce3f7c18 (applies there and on the qorfix stack; checked with `git apply --check`).
+30/-5 in himbaechel/uarch/xilinx/gen/xilinx_gen.py. Opt-in: chipdb generator option `--cell-timing FILE`.

## Problem
For artix7 the generator writes stub cell timings: LUT 0.100-0.125 ns (O6) / 0.120-0.150 (O5) on every pin, FF
clk->Q 0.30-0.35, D/CE/SR setup 0.10 ns. Vivado's slow-corner arcs on xc7a35t-1 are larger (FF clk->Q 0.456 ns),
so nextpnr's Fmax is optimistic and its timing-driven placement weighs paths wrongly. prjxray-db's CLBLL_L.sdf has
the same stub-like values (LUT6 0.124 on every pin, FF CLK->Q 0.303/0.340), so it is not a better source.

## Change
`--cell-timing FILE` (JSON, ps, `[fast, slow]` pairs) replaces the LUT A1..A6 -> O6/O5 arcs, FF CK->Q, D setup,
CE setup, and adds a site-pip timing class `SLICE_FF_BYPASS` on the AX..DX input of the [A-D](5)FFMUX (the
bypass path into an FF, slower than LUT -> FF in Vivado). Hold values are left alone (they drive hold fixing).
Without the option the output is unchanged.

The JSON for xc7a35t-1 is measured, not hand-written: vivado/build_arcs.tcl dumps Vivado's `get_timing_arcs` of
up to 400 cells per type from three placed and routed designs, and flow/vivado_cell_timing.py reduces them
(build/chipdb-cal/cell_timing_xc7a35t_1.{json,txt}):
- FF CK->Q 0.456 ns (median of 1231; range 0.419-0.518); D setup from the slice's own LUT -0.075 ns (clamped to
  1 ps), via AX..DX 0.215 ns (the 0.290 ns difference goes on SLICE_FF_BYPASS); CE setup 0.169 ns.
- LUT: Vivado's arc is either about 0.12-0.15 or 0.29-0.35 ns, and within one LUT typically one input is fast.
  This is not explained by the physical pin, unateness, SLICEL/SLICEM, LUT pairing, output pin or out-of-slice
  loads (checked); it seems route-dependent, so the mean is used: O6 0.200 ns, O5 0.228 ns.

## Evidence
- No-op: chipdb generated without the option is byte-identical to the nightly's chipdb-xc7a50t.bin
  (build/chipdb-cal/off, `cmp`).
- nextpnr's Fmax claim against Vivado's timer on the identical placement (Vivado re-routes), 6 designs at 5 ns:
  mean absolute error 9.6 % with the stub chipdb, 6.3 % with the calibrated one (docs/qor-vivado.md Finding 10).

## Open
- Identical routes were not imposed on Vivado (would need FIXED_ROUTE from nextpnr's pips).
- Routing delays (node RC from prjxray) are not calibrated; CARRY4, MUXF7 and BRAM keep their SDF values.
- One speed grade and corner (xc7a35t-1, slow max); the JSON is per part.
