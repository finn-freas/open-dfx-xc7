# nextpnr-placer-sa-refine (draft, not posted)

Base: the place_v17 source (build/src/nextpnr-place at 2026-11-08 13:24 = openXC7/nextpnr ce3f7c18 + the stack in
docs/drafts/nextpnr-placer-density.md, with `--placer-static-driver-crit-fanout`); worktree build/src/nextpnr-sa,
commit 5a1218ef = that snapshot. The patch applies with `git apply` on it. Build build/nextpnr-build/sa (cmake flags of
docs/buildenv.md, ninja -j2); frozen binaries sa_v1 (ade3dfea), sa_v2 (+ carry-chain moves), sa_v3 (+ RAM/DSP moves), sa_v4 (+ site/tile keys, LUTRAM guard, endpoint dump);
the current tree adds only the endpoint dump (no placement change, checked on rv_soc s1-3).

## -o sa-refine[=key=value:...]
Timing-driven simulated-annealing refinement after legalisation, VPR style. New file
himbaechel/uarch/xilinx/sa_refine.cc, called from XilinxImpl::postPlace() after the `dpl` detailed placer, before
fixup_placement. Off unless given; skipped under -o preplaced/prerouted.
- Moves (window shrinking with the acceptance rate, VPR rlim, floor rmin): single unclustered LUT/FF move or swap;
  small LUT/FF cluster to a free legal position; whole-slice swap/shift (clusters inside the slice; carries and F7/F8
  muxes allowed, LUTRAM/SRL slices not: they crashed the global-clock router); carry-chain block shift (all slices of
  a CARRY4-rooted cluster, accepted only when getClusterPlacement equals the shift); block RAM / DSP to another site
  of its type within 12 tiles or a swap. Weighted-centroid targets (pcent), critical-cell selection (pcrit).
- Cost (1 - lambda) dWL/WL + lambda * dT/T, T = sum crit^exp * delay(arc), incremental per move.
- delay(arc): Vivado-fitted model (flow/xroute_predict.py): dedicated in-slice 0, routed in-slice 665 ps (LUT input)
  / 866 (other), same tile 682, else alpha + beta * delay matrix (489 + 1.391 for the stub/cell chipdb).
- Criticality: TimingAnalyser on the same arc model (set_route_delay), redone every temperature, against the slack
  at quantile `quant` (crit_quantile; 0.002 in the measured setting).
- Start temperature: uphill acceptance t0 over a 2000-move sample. VPR cooling; 2 greedy passes at the end.
- Keys (default): lambda 0.7, exp 4, t0 0.05, rlim 8, rmin 1, inner 4, quant 0.02, alpha 489, beta 1.391, pcrit 0.3,
  pcent 0.3, pslice 0.3, pchain 0.5, phard 0.05, hardwin 12, temps 300, time 900, critmin 0.5, greedy 2, kinds 31
  (1 single, 2 cluster, 4 slice, 8 chain, 16 RAM/DSP), slicemask 3, dump=FILE (model endpoint slacks).
  Measured settings: `sa1` = t0=0.01:quant=0.002:exp=8:rmin=3:pcent=0.6; `sa4` = sa1 + site=750:tile=850 (sa_v4
  adds the site/siteother/tile keys; the 665/682 ps defaults let the SA crowd local arcs that Vivado routes slower).

## No-op
Option absent: returns at once. sa_v1 with tu 1.0 and no option: `.frames` identical to place_v17 and place_v15 on
rv_soc seeds 1-3 (flow/place_bench_sa.py --noop).

## Results
docs/wip/placement-sa.md (Vivado timer, exact import via flow/exact_src.py + flow/sa_xqueue.sh).
