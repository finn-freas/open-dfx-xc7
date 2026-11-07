# nextpnr-ologic-iob-sdr (draft, not posted)

Base: openXC7/nextpnr e62fafd1 + nextpnr-xdc-timing + nextpnr-xdc2-constraints + nextpnr-timing-report (the `timrep`
variant). Worktree build/src/nextpnr-xdc3, build build/nextpnr-build/xdc3 (variant `xdc3`). +2/-1 in
himbaechel/uarch/xilinx/fasm.cc.

## Problem
With IOB TRUE, nextpnr-xdc2-constraints moves a register that only drives an output buffer into the OLOGIC output
flip-flop, as an ODDR in SAME_EDGE mode with D1 = D2. The FASM writer wrote every OUTFF as `OSERDES.DATA_RATE_OQ.DDR`.
Vivado writes `OSERDES.DATA_RATE_OQ.SDR` for a register in the OUTFF. The logic value is the same (D1 = D2), but the
configuration is not Vivado's: x_io_oiob had 119 of 123 decoded ILOGIC/OLOGIC lines identical to Vivado's, the 4
others were these bits.

## Change
The packer already marks a register moved into the I/O logic with the attribute `X_IOB_SDR` (the IFF uses it for
ZSRVAL_Q1). The OUTFF branch of the FASM writer now reads it: `DATA_RATE_OQ.SDR` for such a register,
`DATA_RATE_OQ.DDR` for an ODDR as before. Nothing else changes: placement, routing and timing do not read the
attribute.

## Evidence (offline, re-verified 2026-11-06 after the WIP checkpoint 791d27d)
- Patch check: the four patches (nextpnr-xdc-timing, nextpnr-xdc2-constraints, nextpnr-timing-report, this one) apply in
  order to a fresh e62fafd1 export and give the xdc3 worktree's files byte for byte (0 files differ). The xdc3 binary
  is newer than every source file of the worktree.
- Decoded ILOGIC/OLOGIC lines (`flow/bit2fasm.py`, filter of `build/xdc2_scratch/iobcmp.sh`) against Vivado 2025.2's
  bitstream of the same RTL and XDC (`build/xdc/<d>/{vivado.fasm,xdc3/decoded.fasm}`):
  - x_io_oiob: 123 of 123 identical (xdc2: 119).
  - x_io_onoiob: 95 of 95; x_io_iob 105 of 109 and x_io_iiob 115 of 123, as with xdc2. The other lines are the IOI
    clock leaf track (`IOI_LEAF_GCLK0` here, `GCLK5` in Vivado), a clock-routing choice, not a packing bit.
- FASM xdc2 -> xdc3 on all 54 XDC test designs that build (`flow/xdc_audit.py --variant xdc3 --run`; x_loc,
  x_clk_noncc, x_clk_nside stop at the clock DRC as intended): x_io_oiob differs in exactly the 4
  `OSERDES.DATA_RATE_OQ` lines; the other 53 differ only in the version comment, and their frames are identical.
- No-op (`flow/xdc_noop.py --new xdc3 --run`, `build/xdc_noop/noop.json`): blinky and rv_soc 0 frames against the router
  variant; rv_pr native, 7 statics, 0 frames in 7/7 against `build/patched/rv_pr_native/router`.
