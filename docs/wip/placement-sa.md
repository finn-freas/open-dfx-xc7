# WIP: timing-driven SA refinement after legalisation (VPR style) -- state file

Owner: the SA-refinement agent. Started 2026-11-08 13:30. Separate from the global-placer agent's work
(docs/wip/placement-global.md: critical-connection pull in the global placer, LUT->FF pairing).

## What it is
nextpnr option `-o sa-refine[=key=value:...]` (xilinx uarch, new file himbaechel/uarch/xilinx/sa_refine.cc, called in
`postPlace()` right after the `dpl` detailed placer). Off unless asked for. Runs after the static placer, its
legalisation and its placer1 refinement (which runs at temperature ~0 for ~14 iterations, i.e. greedy, with
nextpnr's uncalibrated predictDelay and the ICAP-flattened criticality: on rv_soc its timing cost is 14-23 against a
wirelength of ~26000, so it is wirelength-only in practice).
- Moves inside a window that shrinks with the acceptance rate (VPR rlim, floor `rmin`):
  one unclustered LUT/FF (move to a free bel or swap with another), a small LUT/FF cluster (the packer's LUT and the
  FFs it drives) to a free legal position, or the whole content of a slice swapped with another slice (or moved to an
  empty one) when every cluster in it lies inside the slice (keeps packing; carries and F7/F8 muxes included,
  LUTRAM/SRL slices excluded: moving them crashed the global-clock router, `slicemask` bit 4).
  With probability `pcent` the window is centred on the criticality-weighted centroid of the unit's connections
  (VPR's weighted-centroid move), with `pcrit` the unit is drawn from the critical cells.
- Cost (VPR): (1 - lambda) dWL/WL + lambda dT/T, WL = bounding-box HPWL (nets <= 256 users),
  T = sum over arcs of crit^e * delay(arc).
- delay(arc): the Vivado-fitted model of flow/xroute_predict.py (Finding 13): dedicated in-slice connection 0, routed
  in-slice 665 ps to a LUT input / 866 ps to another pin, another slice of the tile 682 ps, else
  489 + 1.391 * delay matrix (the fit for the cell-calibrated chipdb, whose routing equals the stub chipdb's).
- Criticality: a full TimingAnalyser run on the same arc model (set_route_delay on every non-clock arc) at every
  temperature, against the slack at quantile `quant` of the port slacks (crit_quantile, so the ICAPE2 path does not
  flatten it). Between analyses the timing cost is updated incrementally per moved arc (VPR's scheme).
- Start temperature: chosen so that the uphill moves of a 2000-move sample are accepted with mean probability `t0`
  (low: refine, do not melt). Cooling: VPR's acceptance-rate schedule; stop at 1e-3 of T0 or 5 flat temperatures,
  then `greedy` (2) zero-temperature passes.

## Status
- 2026-11-08 13:35-14:00: worktree build/src/nextpnr-sa (base commit 5a1218ef = place_v17 source snapshot, built as
  build/nextpnr-build/sa); sa_refine.cc written; first version frozen as build/nextpnr-build/sa_v1 (worktree commit
  ade3dfea), draft docs/drafts/nextpnr-placer-sa-refine.patch.
- **No-op:** sa_v1 without the option (`sa_off_tu_stub`, target util 1.0) gives `.frames` identical to place_v17
  (`pl17_tuonly_stub`) and place_v15 (`pl15_tuonly_stub`) on rv_soc seeds 1-3 (`place_bench_sa.py --noop`).
- Bugs found on the way: (1) slice moves picked up bels with z >= 128 (not slice bels) -> fixed; (2) moving LUTRAM
  slices crashed the global-clock router (relptr assertion) -> LUTRAM/SRL slices excluded (slicemask default 3).
- Tuning on rv_soc s1 (tu 1.0 placement), nextpnr side, **"model slack" = my TimingAnalyser run on the Vivado-fitted arc
  model with the stub chipdb's cell delays** (not Vivado's timer, not nextpnr's routed timer):
  - a hot start (t0 = 30 % of mean uphill cost) melts the placement (HPWL 16130 -> 45642 -> 17409 at the end);
  - t0 = 5 % uphill acceptance, quantile 0.02, exponent 4: the weighted sum falls but the worst slack gets worse
    (-4.44 -> -5.33 ns): with crit = 1 for the whole 2 % tail the worst path is not singled out;
  - quantile 0.002 (or 0 = worst path), exponent 8: worst -4.44 -> -3.99, 0.5 % quantile -4.18 -> -3.69 ns;
  - + window floor 3 and centroid probability 0.6 (`sa1`): worst -3.85, HPWL 16130 -> 16145, 4.4 s;
  - greedy (t0 = 1e-6) with the same moves: worst -3.95; inner 12: -3.94. The annealing temperature matters little;
    the gain comes from the cost (fitted delays, sharp criticality) and the move set.
- sa_v1 (`sa1` = t0=0.01:quant=0.002:exp=8:rmin=3:pcent=0.6), model slack worst before -> after, seeds 1-3:
  rv_soc tu 1.0: -4.44 -> -3.85, -4.77 -> -4.55, -5.07 -> -4.14; rv_soc base: -5.06 -> -3.92, -4.62 -> -4.15,
  -5.40 -> -4.92; rv_mul tu: -4.96 -> -4.00, -5.55 -> -4.97, -5.56 -> -4.76; bram tu s1: -2.08 -> -2.08 (bram's paths are
  multi-slice carry chains next to the RAMs, which sa_v1 cannot move). 4-6 s per run.
- **Measurement (coordinator, 14:00): Vivado-time with flow/exact_src.py** (the exact nextpnr implementation imported,
  Vivado only routes; the "placed" mode is 7-21 % optimistic). flow/sa_xqueue.sh: exact export + vivado/build_rte.tcl,
  slot 2 only, results build/exact_sa; names already being timed by another agent in build/exact are skipped and read
  from there (flow/sa_summary.py). Queue: base / tu / sa1_tu / sa1 x rv_soc, bram, rv_big, rv_mul(dq) x seeds 1-3.
- v2 in progress: carry-chain block moves (a CARRY4-rooted cluster with all its slices, shifted as one block, only
  when nextpnr's cluster placement equals the shift). bram s1: worst -2.08 -> -2.01 (13 of 4803 chain moves kept);
  rv_soc s1 -3.80.
- sa_v2 frozen (build/nextpnr-build/sa_v2, worktree commit "sa_v2"), runs `sa2_tu_*` seeds 1-3, model slack worst:
  rv_soc -4.44 -> -3.80, -4.77 -> -4.17, -5.07 -> -4.39; bram -2.08 -> -2.01, -2.18 -> -2.12, -2.59 -> -2.58;
  rv_big -6.19 -> -5.87, -6.67 -> -6.08, -6.32 -> -6.09; rv_mul -4.96 -> -4.36, -5.55 -> -4.93, -5.56 -> -4.24.
  Chain moves are rarely kept (11-83 of 3000-7000 tried): a shifted chain must land on slices whose own clusters fit.
- Model check against Vivado (exact import, Vivado timer): base rv_soc s1-3 Vivado 101.39 / 103.35 / 100.22 MHz;
  the model on the same placements (the "before" of the sa1_stub runs) -5.06 / -4.62 / -5.40 ns = 99.4 / 103.9 /
  96.2 MHz. Same order and level, so the model is usable as a proxy; the SA's model gain on those seeds is to
  112.2 / 109.7 / 101.8 MHz.
- Vivado slot 2: from 14:05 to 14:30 another agent ran the exact-import baselines (pl14_off_stub) on both slots; my
  worker polls lock2 every second. Queue reordered (sa1_tu, tu, sa2_tu, sa1, base).
- sa_v3 (frozen build/nextpnr-build/sa_v3, worktree commit "sa_v3"): + block RAM / DSP moves (an unclustered RAMB36/
  RAMB18/DSP48 to another site of its type within 12 tiles of itself or of its weighted centroid, or a swap; 5 % of the
  moves). Model slack worst before -> after (s1/s2/s3): rv_big tu -6.19/-6.67/-6.32 -> -5.55/-6.12/-6.06 (sa_v2 -5.87/
  -6.08/-6.09), rv_big base -6.61/-7.01/-6.50 -> -5.84/-5.67/-5.66; HPWL -6..-13 %. bram stays flat on the worst path.
  8-18 s per run. Queue: sa3_tu and sa3 (on the base placement) replace sa2_tu.
- **Is the SA fooling itself with its model?** No: flow/sa_arcmodel.py compares the arc model with Vivado's routed net
  delay (net_delays.txt) on the 50 worst non-ICAP Vivado paths of a run. Per arc, Vivado - model mean / mean abs:
  base rv_soc s1 -37 / 282 ps, s2 -12 / 152; sa1_tu rv_soc s1 -32 / 203, s2 +21 / 131; sa1_tu rv_mul s1 -13 / 207 ps;
  per path the net sum agrees within 2-4 %. The refined placements are no more mis-modelled than the base ones.
- Logic delay (flow/sa_logicfit.py scratch fit, rv_soc FF-to-FF worst paths, Vivado timer): logic = 1.19 + 0.154/LUT +
  0.227/CARRY4 ns. Per LUT this is close to the stub chipdb's 0.10-0.125 ns, so the model's path ranking is not far
  off on LUT depth; the fixed part (FF clock-to-out 0.456 vs 0.35, LUTRAM reads) is where it is optimistic.
- Exact-import Vivado, first SA rows (Vivado timer): sa1 on the tu 1.0 placement, seeds 1-3: rv_soc 107.11 / 100.44 /
  99.18 (base 101.39 / 103.35 / 100.22), bram 145.37 / 144.68 / 141.51 (base 139.12 / 145.90 / 144.36), rv_big 88.14 /
  83.96 / 82.03 (base 88.75 / 85.91 / 90.88), rv_mul 101.43 / 102.27 / 103.04. The tu-only rows (the right baseline for
  sa*_tu) are queued.
- Model endpoint dump (`-o sa-refine=...:dump=FILE`, no effect on placement; re-runs reproduce the sa3 runs line for
  line) + flow/sa_endpoints.py: model endpoint setup slack against Vivado's on the 200 worst non-ICAP endpoints of the
  same placement. Base rv_soc s1/s2/s3: Vivado - model +0.12 / -0.14 / +0.09 ns (sd 0.34 / 0.67 / 0.54), Pearson r
  0.95 / 0.77 / 0.88, the model's 50 worst endpoints all among Vivado's 200 worst. On the base placement the SA's
  timer ranks endpoints the way Vivado does. The same check on the SA placements decides whether the SA overfits.
- A Vivado worst path on sa1_tu rv_soc s3 (10.08 ns): RAMB36 CLKARDCLK->DOADO 2.454 ns, a 1.46 ns net to the first LUT,
  6 LUT levels, 6.27 ns of net. sa_v1 cannot move block RAMs; sa_v3 can.
- A second Vivado worker on slot 1 was refused by the permission system; the queue stays on slot 2 (about 4.5 min a run).

## Milestone 16:10 -- rv_soc, Vivado timer, exact import (nextpnr's LUT pin locks kept: lockpins.txt), seeds 1-3
| variant | Vivado Fmax per seed | mean | net ns | logic ns | cells/path | hops | hops/step | net ps/step | HPWL (grid) | slices | nextpnr s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base (pl14_off_stub) | 101.39 / 103.35 / 100.22 | 101.65 | 5.72 | 2.64 | 8.2 | 50.9 | 7.18 | 798 | 17267 | 492 | 42 |
| tu 1.0 (pl15_tuonly_stub) | 105.03 / 96.07 / 99.50 | 100.20 | 5.68 | 2.61 | 8.2 | 45.7 | 6.38 | 791 | 15743 | 473 | 28 |
| tu + sa_v1 | 107.11 / 100.44 / 99.18 | 102.24 | 5.45 | 2.58 | 8.1 | 39.6 | 5.57 | 767 | 15787 | 445 | 42 |
| tu + sa_v3 | **110.08 / 105.00 / 103.21** | **106.10** | 5.07 | 2.77 | 8.1 | 33.6 | 4.76 | 714 | 15386 | 438 | 50 |
(path columns: 100 worst non-ICAP Vivado paths; hops in prjxray grid units; HPWL from nextpnr's routed JSON.)
- sa_v3 beats tu on every seed (+4.8 / +9.3 / +3.7 %, mean +5.9 %) and base by +4.4 %. Hops per step 6.38 -> 4.76
  (Vivado's own placement: 5.3), net per step 791 -> 714 ps (Vivado's own: 498), HPWL -2 %, slices 473 -> 438.
- Model check on the SA placements: Vivado - model endpoint slack -0.15 / -0.15 / -0.19 ns (r 0.87 / 0.80 / 0.87) against
  +0.09 / -0.39 / +0.03 (r 0.84 / 0.87 / 0.95) on the tu placements: the SA's result is ~0.2 ns more optimistic in the
  model than in Vivado (it optimises against model error, as any optimiser does), but the ranking holds.
- The remaining per-step gap to Vivado's own placement (714 vs 498 ps at fewer hops) is no longer distance: Vivado's
  own run has 6.3 cells per path against our 8.1 (opt_design netlist) and picks LUT pins by timing (coordinator,
  16:05: timing-driven pin assignment alone +17 % on rv_soc, being implemented by the packing/router agent; this
  study keeps nextpnr's own locked pins so the two stack).
- 16:20: slot 2 handed back to the global placer (coordinator); flow/sa_xqueue.sh now runs as `worker 1` on slot 1,
  polling every 10 s so the packing agent keeps priority. From 16:21 to 17:00 it did not win the slot once.
- Parameter sweep (sa_v3 + dump binary, model worst slack after SA, rv_soc tu s1/s2/s3, seed mean): sa1 -4.16 ns;
  exp 12 -3.95; quant 0.0005 -4.05; inner 10 + rmin 4 -4.22 (2x time); lambda 0.85 -4.04; pslice/pcrit 0.5 -4.05.
  All within 0.2 ns, which is inside the seed spread. The stage is at a plateau: about 0.6-0.8 ns of model slack on
  rv_soc. The next step is not tuning but moves the stage cannot make yet (LUTRAM slices, two-chain swaps).
- Other agents exact-time the tu baselines into build/exact (rv_mul pl15_tuonly_dq s1 seen 16:40); the queue skips
  those and flow/sa_summary.py reads them from there. Queue order now: sa3_tu (bram, rv_big, rv_mul), rv_soc s4-5,
  the remaining tu rows, then sa3 on the base placement.
- **LUTRAM crash explained (a latent nextpnr validity hole):** xc7_logic_tile_valid() (xilinx_place.cc) checks
  SLICEM-only LUTs (LUTRAM, SRL) per *tile type*: in a CLBLL tile it rejects them, but in a CLBLM tile it accepts one in
  either slice, although only slice 0 of a CLBLM is a SLICEM. Slice moves put a LUTRAM into the SLICEL half of a
  CLBLM, isBelLocationValid() said yes, and the global-clock router later hit a relptr assertion. The placers so far
  never produced that placement, so nobody saw it. sa_refine.cc now refuses such a target itself (worktree, after
  sa_v3). With that guard LUTRAM slices move without a crash (rv_soc tu s1-3, slicemask=7), but the model gain is no
  larger (worst -4.06 / -4.60 / -4.30 against -3.76 / -4.37 / -4.36 without), so the default stays 3. The proper fix
  belongs in xc7_logic_tile_valid (check the slice, not only the tile type), as a separate small patch.
- rv_big s1 (Vivado timer): tu 89.40, tu + sa_v3 87.67 MHz (-1.9 %). The model ranks rv_big's endpoints worse than
  rv_soc's (r 0.62 / 0.70; only 1-6 of the model's 50 worst endpoints among Vivado's 200 worst), and the Vivado worst
  path after SA is an 11-level carry path into an FDSE S pin (model -5.27 there, Vivado -6.51).
- Per arc kind on the 100 worst Vivado paths (Vivado - model, ps; "inter" includes CO->CI carry hops, which the
  script prices by the matrix but the SA prices 0, so ignore it on carry-heavy designs): same-tile arcs +74 (tu) ->
  +266 (sa3) on rv_big, +111 -> +174 on rv_soc s1; same-slice LUT inputs -157 -> +332 on rv_big. **The SA pulls
  connections into tiles and slices where the model's 665 / 682 ps constants are optimistic** -- it exploits the
  constants. sa_v4 (frozen build/nextpnr-build/sa_v4) makes them keys; `sa4` = sa1 + site=750:tile=850, nextpnr done
  for all four designs, queued for Vivado after the sa3_tu rows.

## State at 18:15 (stopped: no Vivado slot 17:11-18:15)
All numbers: Vivado timer, exact import (flow/exact_src.py; Vivado only routes, nextpnr's LUT pin locks kept),
5 ns, seeds 1-3 unless marked; tu baselines partly timed by other agents (build/exact). flow/sa_summary.py:

| design | base | tu 1.0 | tu + sa_v1 | tu + sa_v3 | sa_v3 vs tu |
|---|---|---|---|---|---|
| rv_soc | 101.65 (101.39 / 103.35 / 100.22) | 100.20 (105.03 / 96.07 / 99.50) | 102.24 | **106.10 (110.08 / 105.00 / 103.21)** | +5.9 %, 3/3 seeds up |
| rv_mul (dspq) | 97.69 | 99.04 (99.97 / 95.10 / 102.05) | **102.21 (101.43 / 102.26 / 102.95)** | not timed | sa_v1: +3.2 %, 3/3 up |
| bram | 143.13 | 143.68 (144.47 / 144.74 / 141.82) | 143.85 | 146.91 (s1 only; tu s1 144.47) | s1 +1.7 % |
| rv_big | 88.51 | 85.43 (89.01 / 82.45 / 84.84) | 84.71 | 86.90 (s1 only; tu s1 89.01) | s1 -2.4 % |

Critical-path geometry (100 worst non-ICAP Vivado paths; tu -> tu + sa_v3): rv_soc hops/step 6.38 -> 4.76 (Vivado's own
placement 5.3), net/step 791 -> 714 ps; rv_big 4.94 -> 4.01, 675 -> 643 ps; bram 2.10 -> 1.87, 265 -> 253 ps.
HPWL (grid units, routed JSON) rv_soc 15743 -> 15386, rv_big 24034 -> 21934, bram 22850 -> 21843. nextpnr time +14-23 s.

Reading:
- The SA stage shortens the critical connections on every design: hops per step reach or beat Vivado's own placement.
  Where the model's critical paths are Vivado's (rv_soc, rv_mul: endpoint r 0.80-0.95, the model's 50 worst endpoints
  all in Vivado's 200 worst) that becomes Fmax: rv_soc +5.9 % over tu and +4.4 % over base, rv_mul +3.2 % (sa_v1).
- Where it is not (rv_big: r 0.62-0.70, 1-6 of 50), shorter hops do not give Fmax: rv_big s1 -2.4 %. bram is flat to
  +1.7 % (its paths are carry chains at fixed RAM pins; few moves apply).
- Net delay per step stays ~714 ps against Vivado's 498 at fewer hops: distance is no longer the gap on rv_soc. What
  remains is per-connection delay (local arcs the model prices too low and the SA crowds -- tile +110..+270 ps,
  same-slice LUT input up to +330 ps on rv_big), LUT pin choice (+17 % on its own, packing agent) and path depth
  (8.1 cells against 6.3 in Vivado's opt_design netlist).
- The SA exploits model error: Vivado - model endpoint slack moves by about -0.2 ns from tu to SA placements.
  sa_v4 (local constants 750 / 850 ps) is built and run in nextpnr for all four designs but not Vivado-timed.

Open / to resume (queue build/sa/xq/names.txt, `echo 0 > build/sa/xq/next; setsid nohup flow/sa_xqueue.sh worker 1
>> build/sa/xq/worker.log 2>&1 &`, slot 1 only; finished names are skipped):
1. sa3_tu rv_mul s1-3, bram s2-3, rv_big s2-3 (decide rv_mul/bram/rv_big with 3 seeds);
2. sa4_tu (site=750:tile=850) rv_big / rv_soc s1-3: does pricing local arcs honestly stop the rv_big loss;
3. rv_soc seeds 4-5 (sa3_tu, sa_off_tu); sa3 on the base placement (all designs).
4. Not a default candidate yet: a win on rv_soc/rv_mul, a loss on rv_big s1, 1 seed on bram.

## Slot-1 window 19:45-21:15 (coordinator): sa_v4 = sa_v3 + honest local pricing (site=750:tile=850)
Vivado timer, exact import, nextpnr's locked pins, seeds 1-3 (got the slot 20:07-20:12 and 20:53-21:19; the last run
started 21:14:46 and ended 21:19, then the worker exited at the window end and released the slot):

| design | base | tu 1.0 | tu + sa_v3 | **tu + sa_v4** | sa_v4 vs tu | vs base |
|---|---|---|---|---|---|---|
| rv_soc | 101.65 | 100.20 (105.03 / 96.07 / 99.50) | 106.10 | **106.17 (111.97 / 103.36 / 103.18)** | +6.0 %, 3/3 seeds up | +4.4 % |
| rv_big | 88.51 | 85.43 (89.01 / 82.45 / 84.84) | 86.90 (s1) | **89.76 (90.32 / 92.50 / 86.46)** | +5.1 %, 3/3 seeds up | +1.4 % |

- **Honest local pricing removes the rv_big loss**: s1 86.90 (sa_v3) -> 90.32 (sa_v4); rv_soc unchanged (106.10 vs 106.17).
- rv_big critical paths, tu -> sa_v4: hops/step 4.94 -> 3.51, net/step 675 -> 602 ps, HPWL 24034 -> 21829, slices 666 -> 632.
- Model vs Vivado on sa_v4: rv_big endpoint r 0.83 / 0.85 / 0.71 (sa_v3 s1 0.70), Vivado - model +0.22..+0.38 ns
  (the model is now pessimistic there, not optimistic); rv_soc r 0.90 / 0.88 / 0.83, offset +0.09 / -0.10 / -0.05.
  Same-tile arcs are still +222 / +282 ps under Vivado on rv_big / rv_soc s1 (n 11 / 60): a tile constant nearer 950
  may be the next step.
- Recommended setting so far: `-o sa-refine=t0=0.01:quant=0.002:exp=8:rmin=3:pcent=0.6:site=750:tile=850` on top of
  `--placer-static-target-util 1.0` (build sa_v4). Still to time (queue build/sa/xq): sa4 on bram and rv_mul (sa_v1
  already gave rv_mul +3.2 %, bram sa_v3 s1 +1.7 %), more seeds, and sa4 on the base placement.

## Wind-down 22:00 (user request) -- stopped, nothing running
- Slot 3 (vivado.lock3) run: bram tu + sa_v4 s1 = 145.75 MHz (tu s1 144.47, sa_v3 s1 146.91), Vivado timer, exact import.
  The worker was waiting for the slot (no Vivado of mine running) and was stopped; no lock of mine is held.
- Built but not Vivado-timed: sa5 = sa_v4 binary with tile=950 (rv_big, rv_soc s1-3; model worst slack rv_big -5.67 /
  -5.91 / -6.04, rv_soc -4.23 / -4.58 / -4.22 ns); sa4 on bram s2-3 and rv_mul s1-3 (nextpnr runs exist).
- Resume (queue build/sa/xq/names.txt keeps every name; finished ones are skipped):
  `cd ~/open-dfx-xc7; rm -f build/sa/xq/STOP; echo 0 > build/sa/xq/next; setsid nohup flow/sa_xqueue.sh worker 3 >> build/sa/xq/worker.log 2>&1 < /dev/null &`
  (worker 3 = slot 3, >= 5000 MB free; worker 1 = slot 1, polite 10 s polling; in a granted slot-1 window add
  `SA_FAST=1 SA_HOLD=1 SA_UNTIL=HH:MM`). Next names: bram sa4_tu s2-3, rv_mul sa4_tu_dq s1-3, rv_big/rv_soc sa5_tu s1-3,
  then rv_soc s4-5, sa3 on the base placement.
- Table: `python3 flow/sa_summary.py --designs rv_soc bram rv_big rv_mul --variants pl14_off_stub pl13_off_dq pl15_tuonly_stub pl15_tuonly_dq sa3_tu_stub sa4_tu_stub sa4_tu_dq sa5_tu_stub`.
