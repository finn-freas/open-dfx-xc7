# nextpnr-placer-density (draft, not posted)

Base: the worktree build/src/nextpnr-place as of 2026-11-08 morning = openXC7/nextpnr ce3f7c18 + install/patches/nextpnr
0001-0011 + hardblock-timing + nextpnr-placer-tuning + nextpnr-placer-delay-cal (which carries the anchored start,
`--placer-static-anchor-init`) + nextpnr-packing-dpl (`-o carry-di-bypass`, `-o dpl`). Applies with `git apply` on
that stack. 6 files: common/place/placer_static.{cc,h}, common/kernel/timing.{cc,h}, common/kernel/command.cc,
himbaechel/uarch/xilinx/xilinx.cc. Builds build/nextpnr-build/place_v12 (group utilisation, before its option was
registered), place_v13 (+ packing-dpl), place_v14 (+ RAM assignment), place_v15 (+ criticality quantile), place_v16 (+ a 6th  field: the detailed placer's criticality quantile). Every option is off by default.

## -o static-group-util=COMB,FF,RAM,DSP (target density per cell group)
The static placer fills each cell group with spacers up to one target utilisation (`--placer-static-target-util`,
default 0.7), so at the electrostatic equilibrium the cells sit at about 70 % of a bin's capacity, and the block
RAMs, at 70 % of the RAM columns' capacity, which for a design using half the RAM sites stretches them over most of
the column height. This option sets the target per group (elfPlace-style per-resource target density); a value < 0
keeps the global one. `--placer-static-target-util 1.0` (already in the tuning draft) is the same for all groups.

## -o static-ram-assign (block RAM column and row next to their logic)
At the block-RAM legalisation step, the unclustered RAMB18/RAMB36 cells are assigned to sites by a global greedy
assignment instead of the nearest-free-site legaliser: for every RAM and every site of its type, the cost is the sum
over its arcs (nets of fanout <= 64, global buffers excluded) of the static placer's predicted delay to the
neighbour's solver position, weighted 1 + timingweight * crit^critexp like the wirelength; all (RAM, site) pairs are
taken cheapest first. With the y-heavy delay model the RAMs spread over more columns instead of stacking one
column (bram: 3 RAM columns as Vivado uses, against 2 before).

## --placer-static-crit-quantile Q (criticality against the slack quantile, not the worst path)
nextpnr's criticality is 1 - (slack - worst) / -worst. On rv_soc the worst path is the ICAPE2 one (5.2 ns
clock-to-out with hardblock-timing), so every logic path gets a low criticality and the global placer's net weight
1 + 5 crit^2 stays near 1 on exactly the paths Vivado finds critical (place_diag: the 100 worst Vivado paths take
65.7 hops). With Q > 0 the static placer's timing analyser (TimingAnalyser::crit_quantile, only the static placer's
instance) measures criticality against the slack at quantile Q of the domain pair's port slacks: ports below it get 1.

## --placer-static-driver-crit-fanout N
The static placer gives a net driver its users' worst criticality only for nets of fanout < 5, so the driver of a
critical clock-enable or reset net (Finding 17: 34-45 of the 100 worst paths end at CE, 15-21 at R) is weighted as
uncritical. N raises that limit (default 5 = unchanged). place_v17; options off: frames identical to place_v15
(rv_soc s1-3, target util 1.0 on).

## No-op
With the options off, `.frames` are identical to place_v11 (rv_soc and bram, seeds 1-3, anchored start on:
`pl11_anc20ipw_stub` vs `pl12_/pl13_/pl14_anc20ipw_stub`; `flow/place_bench.py --noop`).

place_v15 (options off, anchoring on): identical to place_v11 on rv_soc seeds 1-3.

## Results
docs/wip/placement-global.md ("Session 2026-11-08"), Vivado's timer.
