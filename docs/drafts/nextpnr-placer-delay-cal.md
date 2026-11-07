# nextpnr-placer-delay-cal (draft, not posted)

Base: the nextpnr-placer-tuning stack (worktree build/src/nextpnr-place = ofx series + hardblock-timing +
nextpnr-placer-tuning). Builds: `place_v5` (predict-cal only), `place_v6` (all three options; logs
build/nextpnr-build/place_v5.build.log, place_v6.build.log). 5 files. Every option is off by default.

## Problem
nextpnr has two placement delay models, and neither was fitted to the fabric:
- The static (global) placer uses its own formula in xilinx.cc `configurePlacerStatic`:
  500 + 48*min(dy,6) + 24*max(dy-6,0) + 24*min(dx,12) + 12*max(dx-12,0) ps.
  It does not read the chipdb, so a recalibrated chipdb (nextpnr-route-timing-cal) leaves the global placement
  unchanged: the HPWL after legalisation is identical with the cell- and route-calibrated chipdbs
  (build/qor/place/metrics_*.md).
- placer1 refinement and pre-route timing use `XilinxImpl::predictDelay` (the delay matrix measured on the chipdb).

The reference is Vivado's routed delay on the same arc, on the identical implementations of docs/qor-vivado.md
Finding 13 (nextpnr's placement and routes imposed on Vivado pip for pip). Results from flow/xroute_predict.py,
build/xroute/predict/; "test" means rv_mul and rv_big, which were not used for the fit. Against that reference,
both models are low:
- The static formula is -433 ps mean (mean absolute 447) on the test designs.
- predictDelay is -731 ps with the cell-calibrated chipdb and -538 ps with the route-calibrated one. It predicts a
  same-slice LUT input at 0 ps, where Vivado measures 0.67 ns, and another slice of the same tile at 150 ps, where
  Vivado measures 0.68 ns.

## Change
- `-o static-delay=C,Y1,Y2,X1,X2` (ps): the static placer's estimate C + Y1*min(dy,6) + Y2*max(dy-6,0) +
  X1*min(dx,12) + X2*max(dx-12,0).
  - Fitted values (least squares on blinky, rv_soc and bram arcs): `786,63,29,37,7`.
  - Test error: -433 -> -28 ps mean, 447 -> 269 ps mean absolute.
- `-o predict-cal=SITE,TILE,ALPHA,BETA`: predictDelay returns SITE for a LUT input fed from the same slice, TILE
  for another slice of the same tile (FF2 sources keep at least their 700 ps), and ALPHA + BETA * matrix between
  tiles.
  - Fitted values: `665,682,313,1.235` for the route-calibrated chipdb, `665,682,489,1.391` for the
    cell-calibrated one.
  - Test error: -538 -> -33 ps mean, 542 -> 259 ps mean absolute.
- `-o static-delay=matrix`: the static placer uses the chipdb's delay matrix, the same estimate as
  predictDelay (scaled by `-o predict-cal` when that is given), so a recalibrated chipdb reaches the global
  placer as well. Same tile = TILE (or 150 ps). Build `place_v7`.
- `--placer-static-timing-every N`: the static placer re-runs timing analysis every N spreading iterations
  (default 10).
- `--placer-static-arc-ratio R` / `--placer-static-arc-exp E` (build `place_v8`): a timing-arc term in the static
  placer.
  - It follows the timing-driven DREAMPlaceFPGA (Xiong, Rajarathnam, Pan, FCCM 2024; code BSD-3,
    github.com/rachelselinar/DREAMPlaceFPGA). The idea is used here; no code was copied.
  - Every driver -> sink arc with criticality >= 0.5 adds a smoothed |x_d - x_s| + |y_d - y_s| term with weight
    crit^E (E = 8).
  - The term is scaled each iteration to r times the net wirelength gradient. r ramps 0.1, 0.2, ... per timing
    update, up to R.
  - The term switches on once the logic overlap is below 0.3.
  - First runs (nextpnr timer, seed 1): rv_soc 98.2 -> 82.4 MHz with R = 0.2, and 71.8 with R = 0.5 or 1.0.
    bram 133.1 -> 132.0, rv_big 78.3 -> 84.5. Vivado timing of 3 seeds is queued.
- `--placer-static-weighted-precond` (build `place_v9`): the static placer's preconditioner uses the cell's summed
  timing net weights (1 + W*crit^E per port) instead of its pin count. This is the idea of Mai, Wang, Lin, TCAD 2024
  (OpenPARF, BSD-3); no code was copied.
  - Seed 1 HPWL after legalisation, with `static-delay`: rv_big 25980 -> 22470, rv_soc 17514 -> 18422,
    bram 21894 -> 21615.
- No-op with each new option off: `.frames` identical to place_v4 on rv_soc, 3 seeds each, for place_v6, place_v7,
  place_v8 and place_v9 (build/qor/place/r13/run6b.log, run8.log, run10.log).

## Evidence
- No-op with the options off: `.frames` identical, place_v5 vs place_v4, on rv_soc, bram and rv_big, 3 seeds each
  (build/qor/place/r13/run4b.log).
- rv_mul (`-pipeline` netlist) with the options off gives the same Fmax per seed on place_v5 as on the qorperm
  stack.
- place_v6 no-op: build/qor/place/r13/run6.log.
- Vivado-timed results: docs/qor-vivado.md Finding 13 ("Placement round 2").
