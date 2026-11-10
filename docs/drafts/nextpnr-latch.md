# nextpnr-latch (+ nextpnr-timing-log-xclock) (drafts, not posted)

Base: the ofx 0.1 nextpnr series + 0028 (partition-pins-ce-sr) + gt-unisim-defaults; build/src/nextpnr-fixes.

## Problem
yosys maps latches to LDCE/LDPE. nextpnr-xilinx had the latch infrastructure (X_FF_AS_LATCH in the control-set,
placer and FASM checks, a LATCH bit in the writer) but no pack rule, so a design with a latch stopped with
"no BELs remaining to implement cell type 'LDCE'" (QoR suite raygentop: 1356 LDCE + 12 LDPE). Vivado builds it.

## Change (nextpnr-latch.patch)
- pack.cc: LDCE/LDPE -> SLICE_FFX; G->CK, GE->CE, CLR/PRE->SR; IS_G_INVERTED->IS_C_INVERTED; X_FF_AS_LATCH.
- fasm.cc: LDCE = ZRST, LDPE = no ZRST (INIT default 1), LATCH set, FFSYNC clear; the slice clock inverter has the
  opposite sense for a latch (CLKINV for a gate that is not inverted; prjxray fasm2bels decodes
  IS_G_INVERTED = !CLKINV).
- Only netlists with LDCE/LDPE can change.

## nextpnr-timing-log-xclock.patch
log_fmax took min() of both clocks' constraints for a related clock pair when neither had an Fmax entry and threw
std::out_of_range (dict::at) after routing. raygentop (each latch gate net is its own clock) hit it. Such a pair is
skipped. Without the crash this code path is unchanged.

## Evidence (2026-11-08)
- raygentop (QoR suite netlist, 125 MHz target): places, routes (158.45 MHz on nextpnr's timer), FASM with 541
  LATCH slices, fasm2frames OK (~/ofx-test/fixes/raygentop2). Before: no BEL for LDCE; with the latch patch alone:
  crash in log_fmax.
- designs/gap/latch_{ldce,ldce_ginv,ldpe,ldpe_ginv}: build; per slice LATCH, ZRST/ZINI and CLKINV/NOCLKINV as in
  prjxray's decoder. Vivado reference bitstreams of the same four designs: see docs/wip/fixes.md (queued for the
  Vivado slot).
- No-op: `install/noop_check.py --candidate <binary with latch + gt-unisim-defaults + timing-log>` on blinky,
  rv_soc, rv_ppt: 5/12 identical, 7 differ only by the ICAP line (as for the 0.1 binary), 0 otherwise.

## Limits
nextpnr times a latch like a flipflop on its gate (no time borrowing, every gate net is its own clock).
