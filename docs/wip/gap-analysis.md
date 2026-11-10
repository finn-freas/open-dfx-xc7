# Where the Fmax gap to Vivado sits (2026-11-09 night)

Vivado timer, exact import of cb_all2 (= ua_dxy) s1 against Vivado placing the same netlist itself (vref:
place_design + route_design, no phys_opt). Scripts: build/exact/gap_paths.py, gap_match.py, gap_ram.py, fo_share.py.

## Like-for-like references (Fmax excl. ICAPE2, MHz)
| design | Vivado places | ours cb_all2 (6-seed mean) | ours / Vivado |
|---|---|---|---|
| rv_soc | 148.8 | 116.2 | 78 % |
| bram | 164.1 | 147.6 | 90 % |
| rv_big | 110.9 | 98.0 | 88 % |
| rv_mul | 159.2 | ~118 | ~74 % |
With the syn2 netlist Vivado reaches rv_soc 163.3, bram 162.5.

## Same paths, different routing delay
Our worst 50 start->end pairs, looked up in Vivado's 200 worst:
- rv_soc: 35 of 50 are not even in Vivado's 200 worst (slack there > -0.48 ns). On the 15 shared pairs logic delay is
  identical (3.20 vs 3.20 ns) and route delay is 4.38 vs 2.48 ns.
- rv_mul: 44 of 50 not in Vivado's 200 worst; shared pairs route 3.75 vs 2.79 ns, logic 3.32 vs 3.05 ns.
So the gap is route delay on the critical paths (~1-2 ns), not logic depth or LUT pin choice.

## Which paths
Two start points dominate our worst paths on both CPUs:
1. Block-RAM outputs (ram.0.1 / ram.0.0, DOADO): RAM -> first LUT 0.91-0.96 ns in ours vs 0.64-0.75 in Vivado, then
   4-6 slice hops of 0.4-1.0 ns each spread over ~8 columns (ours) vs 0.2-0.7 ns within ~5 columns (Vivado).
2. A CPU register with fanout 29 (pcpi_rs1, slice$10967) feeding ALU/compare carry chains: 0.98 ns first hop, chain
   source FF 16 rows from its carry chain on rv_mul (Vivado: ~6 rows).
On rv_soc 28 % of route delay on the worst paths is on nets with fanout >= 16 (fo_share.py).

## Levers, measured or running
- Driver replication (point 2): Vivado's replication on our placements +7.9 % rv_soc, +2.1 % bram (t 3.0); 0 % on
  Vivado's own. Our own pass is being built (docs/drafts/nextpnr-replicate.*, pending).
- Compactness of RAM-fed logic (point 1): detailed-placement timing share (cb2_lam25, running), ring legaliser
  (cb2_ring / cb2_ring20, running).

## Correction (2026-11-10 ~01:00): the "replication" gain was not replication
Results, % vs cb_all2 on the same seed, Vivado timer: cb2po (fixed_po) rv_soc +7.9, bram +2.1, rv_big +6.0 (t 3.4);
our replication pass cb2_repl -0.2 % (12 runs); cb2_syn2 +5.3 % (rv_soc +16.3, rv_mul +9.0, rv_big -4.7);
cb2_ring +0.7, cb2_ring20 -0.4, cb2_lam25 +0.7, cb2_hx25 +0.6 (all neutral).
But Vivado's phys_opt in fixed_po changed nothing ("Optimized 0 net ... Created 0 new cell" in every pass, rv_soc
s1), yet WNS went -3.677 -> -3.086 ns. fixed_po differs from the normal exact import in two more ways: cells are
unfixed after placement, and route_design runs without -preserve (the normal import uses -preserve; vref does not).
Isolation running (build/exact/iso_run.log): fixed_rt = route_design without -preserve; fixed_unfix = + unfixed cells.
If -preserve alone costs ~5 %, the exact import has understated every placement by that much (ours vs vref is then
not like for like).
**Result:** fixed_rt and fixed_unfix are exactly 0.0 % on all 12 runs each: the measurement was right (rv_soc 75 %,
bram 90 %, rv_big 88 %, rv_mul 74 % of Vivado). The +5.0 % (t 4.2, 12 runs) IS phys_opt; the earlier grep only saw
place_design's empty passes. Vivado's critical-cell optimisation does a few targeted things per run
(scratchpad po_actions.py over the cb2po logs): replicates the CPU operand registers pcpi_rs1[0/1] / pcpi_rs2[0/1]
(fanout ~29) 1-3x and replaces the driver of 1-3 LUT nets on the critical path (rv_soc s1: 3 actions, +0.626 ns);
rv_big s3 / rv_mul s1 replicate 15-27 pcpi_rs2 / multiplier-input bits. Our pass (cb2_repl, 10-31 broad copies)
gives -0.2 %: it does not hit these. Revision to a critical-cell mode is with the replication agent.

## Carry DI inputs were untimed (2026-11-10)
Found by the replication agent, confirmed: the chipdb generator (gen/xilinx_gen.py) imports the SDF cell
("CARRY4", "SLICEM") only, but prjxray's slicem.sdf keeps the DI -> O/CO arcs under CARRY4_AX/BX/CX/DX (e.g. DI0 -> CO3
0.444-0.550 ns). So every carry DI input (368 arcs on rv_soc s1) is unconstrained for the placer, sa-refine, the
router and nextpnr's reported Fmax; Vivado's worst rv_soc s1 path goes through one (LUT1 -> carry DI0 -> CO3).
Test chipdb with the four extra imports: build/chipdb-rcal-a6pd-cdi (generator copy build/carrydi/, script
scratchpad cdi_gen.sh). Variants cb2_cdi (cb_all2 on it) and cb2_cdirepl (critical-cell replication on it):
seeds 1-3 x 4 designs, Vivado timing via build/exact/cdi_run.log. If it helps, this becomes a release chipdb patch
(generator change; changes every design with carries).
Replication v2 (cc=1, docs/drafts/nextpnr-replicate.md): makes Vivado's copies on rv_soc (pcpi_rs1[1] + its D LUT,
LUTs 3473/1207, pcpi_rs2[0/1]); Vivado timing via build/exact/repl2_viv.log.

Results, % vs cb_all2 same seed (Vivado timer, 3 seeds x 4 designs):
| variant | rv_soc | bram | rv_big | rv_mul | mean (t) |
|---|---|---|---|---|---|
| cb2_repl2 (critical-cell replication) | +5.1 (all 3 seeds +4.3/+6.3/+4.9) | +0.5 | -3.7 | -1.1 | +0.2 (0.2) |
| cb2_cdi (carry DI arcs in the chipdb) | +1.1 | +1.5 | +0.2 | -3.9 | -0.3 (-0.1) |
| cb2_cdirepl (both) | +4.1 | -0.3 | -0.0 | -2.4 | +0.4 (0.2) |
Share of Vivado (vref): cb_all2 75/90/88/74 %, cb2_cdirepl 79/89/87/72 %.
- Replication is a consistent rv_soc win but not a general one (the model mis-ranks the multiplier designs' nets).
- Correct carry DI timing is QoR-neutral (again: a more accurate timer alone does not improve placement), but it is a
  correctness fix for nextpnr's reports and the router; worth a release chipdb patch on its own.
Next: global-placer timing weight sweep (cb2_tw10/tw20/ce1/tw20ce4), build/exact/tw_run.log.

## Global-placer timing weight (2026-11-10)
Arc weight 1 + W * crit^E (default W 5, E 2). % vs cb_all2 same seed, Vivado timer, 3 seeds x 4 designs:
| variant | rv_soc | bram | rv_big | rv_mul | mean (t) |
|---|---|---|---|---|---|
| cb2_tw10 (W 10) | +3.9 | +0.9 | +0.8 | -11.8 | -1.5 (-0.6) |
| cb2_tw20 (W 20) | +3.0 | -0.6 | -2.5 | -8.8 | -2.2 (-1.0) |
| cb2_ce1 (E 1) | +1.9 | +1.1 | +0.2 | -3.1 | +0.0 |
| cb2_tw20ce4 (W 20, E 4) | +4.7 | +0.1 | +0.8 | -4.4 | +0.3 (0.2) |
None adopted. Same split as replication: rv_soc gains, rv_mul loses.

Why rv_mul loses (scratchpad optim.py, arcs.py / arcs2.py over paths_setup.rpt):
- The placer's own post-placement estimate cannot see it: rv_mul ua_dxy est 129.2 MHz -> Vivado 117.8 (-8.6 %);
  tw10 est 129.2 -> Vivado 103.8 (-19.7 %); tw20 -17.7 %, tw20ce4 -16.2 %. The stronger pull finds placements the
  model scores equal but Vivado does not (rv_soc: -13.5 % for ua_dxy, -9 to -12 % for the tw variants).
- What it does: on rv_mul the slice->slice arcs of high-fanout nets (fo >= 16) on Vivado's 20 worst paths grow from
  dy 3.2 rows / 0.73 ns (ua_dxy) to dy 13.7 rows / 1.40 ns, 48 % of them >= 10 rows (tw10); tw20ce4 dy 9.6 / 1.08 ns.
  Vivado's own placement: dy 2.7. The shared driver (pcpi_rs1/rs2, fo ~28) is pulled between distant sink groups.
- Replication removes exactly that arc class (cb2_repl2 rv_mul fo >= 16: dy 1.9 rows, 0.64 ns), but on its own the
  RAM-output paths then become worst. Combined (build/exact/twr_run.log, % vs cb_all2 same seed, 3 seeds):
| variant | rv_soc | bram | rv_big | rv_mul | mean (t) | share of Vivado |
|---|---|---|---|---|---|---|
| cb2_twrepl (tw20ce4 + replication) | +6.7 | +1.2 | +1.0 | -4.0 | +1.2 (0.6) | 80/91/88/71 % |
| cb2_twcdirepl (+ carry-DI chipdb) | +7.8 | +0.2 | -0.8 | -1.5 | +1.4 (0.5) | 81/90/86/73 % |
  Better than either part alone and rv_soc is consistent, but rv_mul still loses and the mean is within noise:
  not a default.

## Which of our own numbers predict Vivado's (scratchpad est_corr2.py, bestk.py)
Same chipdb (ua_dxy + cb2_* without cdi), 42 placements per design, Spearman against Vivado Fmax:
post-placement estimate rv_soc +0.31, bram -0.12, rv_big +0.21, rv_mul -0.33; nextpnr's own routed Fmax +0.54,
+0.22, +0.17, +0.28. The placement estimate is no guide; the routed one is a weak one.
Picking the best of k seeds by nextpnr's routed Fmax, cb_all2 6 seeds, averaged over every k-subset (Vivado timer):
| k | rv_soc | bram | rv_big | rv_mul | mean | oracle mean |
|---|---|---|---|---|---|---|
| 2 | +1.7 | +0.1 | +4.0 | +0.6 | +1.6 | +2.9 |
| 3 | +2.5 | +0.7 | +5.6 | +2.6 | +2.8 | +4.2 |
| 4 | +2.7 | +1.3 | +6.3 | +4.4 | +3.7 | +4.9 |
Implemented: `seeds = N` in ofx.toml / build_openxc7.py --seeds (docs/ofx.md); runs in parallel, keeps the best
routed Fmax; axi_xbar check: kept seed's frames identical to a plain --seed build. Default stays 1 (CPU x N).
Variants as a strategy portfolio instead (same seed, pick by routed Fmax, 12 design-seeds, scratchpad portfolio.py):
{cb_all2, repl2} +1.8 % (rv_soc +5.1: the pick keeps replication where it helps and drops it on rv_mul);
{cb_all2, tw20ce4, repl2} +2.2 %; all 8 variants +3.6 % (oracle +5.7). No better than seeds at equal cost.

## Fanout-aware arc delay (2026-11-10, running)
Vivado's routed delay grows with the net's sink count (replication's fit: +102 ps per doubling of sinks); the static
placer's and sa-refine's arc estimates use distance only, so high-fanout critical arcs look cheap to the placer.
New opt-in `-o arc-fanout=K` (static placer timing update) and sa-refine key `fo=K`: + K * log2(sinks / 2) ps on
inter-tile arcs of nets with > 2 sinks. Worktree build/src/nextpnr-afo (= nextpnr-repl tree + 17 lines), binary
build/nextpnr-build/afo. No-op: without the option rv_soc s1 FASM identical to cb_all2 (only the version line).
Variants cb2_afo100 / cb2_afo200, seeds 1-3 x 4 designs, build/exact/afo_run.log.
| variant | rv_soc | bram | rv_big | rv_mul | mean (t) | share of Vivado |
|---|---|---|---|---|---|---|
| cb2_afo100 (K 100) | +5.7 | +1.4 | -1.4 | -5.8 | -0.0 (0.0) | 80/91/86/70 % |
| cb2_afo200 (K 200) | +0.4 | -2.9 | +1.1 | -14.0 | -3.9 (-1.5) | 76/87/88/63 % |
Not adopted. Third lever in a row with the same signature: anything that raises the timing pull helps rv_soc and
costs rv_mul. On rv_mul every losing placement has the same worst path (pcpi_rs1 FF -> LUT2 -> carry chain xr_92
S1->O2 -> 2 LUT1 -> carry chain xr_758/771/765 DI0->O3 -> LUT3 -> LUT4 -> FF S) spread as a zig-zag over rows
(afo200 s1: Y4 -> Y8 -> Y16 -> Y19-21 -> Y3 -> Y1; ua_dxy s1 Y31 -> Y15 -> Y16-18 -> Y24-25); Vivado keeps it in
Y31-37 of two columns. The two carry chains are rigid macros: sa-refine keeps 50 of 8014 chain moves on rv_mul,
so their relative position is fixed by global placement + legalisation. Next lever: place / move chains with the
logic between them (chain-to-chain alignment), not more timing weight.

Chain moves in sa-refine (nextpnr-only probes on s1, scratchpad chain_probe.py, build/chain_probe*/):
- More chain effort (pchain 0.9, rmin 6, inner 8): chain moves kept stay at 50-77 of 8-28 k attempts; model slack
  no better; nextpnr routed Fmax rv_mul 102.1 -> 85.6-98.6.
- A chain move was refused whenever its target overlapped its own slices, i.e. every small nudge along its own
  column. New opt-in key sa-refine `chainovl=1` (worktree nextpnr-afo, uncommitted): the slices entered hand their
  contents to the slices left. No-op FASM identical without it. Attempts rise (rv_mul 8014 -> 11899) but kept moves
  do not (50 -> 50) and the model slack is worse (rv_mul -4.655 -> -4.952, rv_soc -4.631 -> -4.830): at the
  near-greedy temperature a whole-chain shift disturbs too many other arcs to pay off. Dropped; chain alignment has
  to come from global placement (chain-aware spreading / legalisation), which is the next real project.

## Carry chains in global placement and legalisation (2026-11-10)
What the static placer does with a chain today (common/place/placer_static.cc): each cluster is split into chunks by
(dx, dy, cell group); every chunk is its own movable cell with its own wirelength/density gradient. Rigidity comes only
from update_chains, which after every step pulls each chunk a fraction alpha = 1.0005^iter - 1 toward its rigid
position around the cluster's area-weighted centroid (rv_mul runs ~480 iterations, so alpha ends at ~0.27). The
legaliser takes clusters largest-first and places a chain by its ROOT chunk's solver position only: random tiles in a
growing square, first legal root site wins, no cost. Nets touching a chain get no special weight.

Measured first (new opt-in `-o chain-log`, nextpnr-only, rv_mul / rv_soc s1-3): the solver keeps chains nearly rigid
(chunk distance from the rigid fit mean 0.6-1.1 placer tiles, max 2-4.5) and legalisation moves them little (root
displacement mean dx 0.4 dy 0.8, max 5-6, 0-2 chains of 31-39 moved > 4 tiles). So neither stretching nor the random
legaliser explains the rv_mul layout: the chains sit where the global placer's net forces put them.

Prototyped in worktree build/src/nextpnr-afo (uncommitted, next to arc-fanout / chainovl; all opt-in):
- `-o chain-legal=R[,TW[,DISP]]`: chain roots legalised by cost over every free root site within R tiles: sum over the
  members' external arcs of (1 + TW crit^2) x predicted delay to the neighbours' solver (or already legal) positions.
- `-o chain-net-w=K`: wirelength/timing weight x K for every net touching a chain cell (global placer).
- `-o chain-snap`: snap chains to their rigid centroid fit before legalisation. `-o chain-rigid=A`: alpha floor A.
No-op: without the options (and with chain-log only) FASM identical to cb_all2 for rv_mul s1-3 and rv_soc s1-3.
nextpnr-only probe (routed Fmax, mean of rv_mul + rv_soc s1-3): base 98.0, cl8 98.0, cnw2 97.8, snap 99.1, rig05 98.1;
chain-rigid=1 91-94 and chain-net-w=4 95 dropped. Chain-to-chain links (chain output -> <= 2 LUTs -> other chain,
13 on rv_mul, scratchpad chain_geo.py) do get shorter: far (> 6 sites) 23 % -> 0-8 % with cnw2 / cl4 / cl8.

Vivado timer, % vs cb_all2 same seed, seeds 1-3 x 4 designs (build/exact/ch1_run.log, ch2_run.log):
| variant | rv_soc | bram | rv_big | rv_mul | mean (t) | share of Vivado |
|---|---|---|---|---|---|---|
| cb2_chcl8 (chain-legal=8) | +2.3 | +0.1 | -1.3 | -2.9 | -0.5 (-0.2) | 77/90/86/72 % |
| cb2_chcnw2 (chain-net-w=2) | +2.4 | -0.1 | +3.5 | -5.5 | +0.1 (0.0) | 77/90/91/70 % |
| cb2_chsnap (chain-snap) | -3.3 | +2.0 | +2.1 | -3.2 | -0.6 (-0.5) | 73/91/90/72 % |
| cb2_chrig05 (chain-rigid=0.5) | -0.2 | -0.4 | +1.0 | -3.1 | -0.7 (-0.3) | 75/89/88/72 % |
None adopted: all within noise, and every one loses on rv_mul (cnw2 s1 -14.6 %).

rv_mul worst path, all 15 placements (ua_dxy + 4 variants x 3 seeds): 13 are still the pcpi_rs1/rs2 -> chain ->
chain -> LUT3/LUT4 -> FF S path (the other 2: RAM-output paths), and in 11 of the 13 its two chains are already close
(chain1 -> LUT1 -> chain2 within 0-4 columns and 0-7 rows, e.g. cnw2 s1 X56Y13 -> X58Y15-17; Vivado X43Y31 ->
X43Y34-36; exceptions cnw2 s3 10 rows, rig05 s2 15 columns). The long hops are at both ends: the operand FF (fo 27-28)
-> chain1 S LUT (2-18 rows, up to 14 columns) and chain2 O3 -> LUT3 / LUT4 / FF (up to 12 rows or 14 columns). Pulling chains toward their logic (cnw2) just moves the long hop: cnw2 s1 compacts the
chains and sends LUT3 13 columns away. Conclusion: chain-to-chain alignment is not rv_mul's problem; the problem is the
shared operand registers (pulled between ~28 sink groups) and the sink-side cone, i.e. the replication / critical-cell
territory (Vivado's phys_opt replicates exactly pcpi_rs1/rs2), not chain handling in the global placer.
