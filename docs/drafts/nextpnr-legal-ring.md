# nextpnr-legal-ring (draft, not posted)

Base: the combo stack (docs/drafts/nextpnr-combo-stack.patch on release 0001-0032). Worktree build/src/nextpnr-legal,
build build/nextpnr-build/legal (legal_build.sh). One file pair: common/place/placer_static.{cc,h} plus
common/kernel/command.cc. Off by default.

## --placer-static-legal-ring N [--placer-static-legal-ring-clusters] [--placer-static-legal-wy F] [--placer-static-legal-wn F]
The static placer's strict legaliser picks random tiles in a growing radius and takes the first legal bel (clusters)
or the best of a few by input wirelength (single cells). It costs 9-27 % HPWL over the global placement here, and
40-50 % on DREAMPlaceFPGA's denser placements (docs/dreamplace-eval.md). With the option, each cell (and, with
-clusters, each cluster root with its whole cluster on free bels and every touched tile legal) goes to the cheapest
bel in rings of Chebyshev radius 0..N around its solver position: cost = displacement (a vertical step weighs wy) +
wn x the mean distance to its already-placed net neighbours (fanout <= 16); a ring stops the search once it cannot
beat the best. Cells it cannot place within N fall back to the random search.

## No-op
Options off: `.frames` identical to the combo binary (rv_soc, route-calibrated chipdb, s1-3) and to the previous legal
build (rv_soc, bram s1-3).

## Results (nextpnr side only; not Vivado-timed)
flow/legal_cost.py, logic legalisation step, mean of seeds 1-3, stub chipdb, target util 1.0 ("tu") or tu10:

| design | tu: old | tu: ring 8 + clusters | tu10: old | tu10: ring 8 + clusters |
|---|---|---|---|---|
| rv_soc | +18.4 % | +13.5 % | +25.7 % | +17.8 % |
| bram | +9.4 % | +8.3 % | +9.2 % | +6.2 % |
| rv_big | +26.8 % | +17.7 % | +23.0 % | +14.9 % |

Single cells only (no -clusters) gave rv_soc +16.3 %, rv_big +22.7 %. wy = 2 is no better than 1.
