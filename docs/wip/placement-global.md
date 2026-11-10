# WIP: global placement + delay calibration (Finding 13) -- state file

Owner: the route-timing/placement agent. Updated 2026-11-06 evening.



## Session 2026-11-08 (global placer: density, RAM columns, combination) -- stopped 09:15, no valid Vivado result yet
**Placement-extraction bug (from the benchmark agent, fixed in efcb64f):** `qor_xtime.placement()` stripped only the
`$split$muxcy0$PACKED_CARRY4$` suffix, so CARRY4 parts with muxcy<N>, N>0, were never imposed, and nextpnr-only cells
were passed to place_cell. It now uses qor_suite's `placement_rows` logic (any N; keep the muxcy0 part of a split
CARRY4; with the netlist's cell names, skip cells absent from the netlist). place_bench passes the netlist cells.
rv_soc anchored s1: place.txt 2503 rows (1933 taken by Vivado, 610 refused) -> 1966 rows, all netlist cells.
- **Every Vivado-timed "our placement" number before efcb64f is biased** (Vivado placed the carries itself), the
  baselines included: pl_base 116.81 / 155.87 / 104.95, all pl5-pl11 rows, Findings 13/15/16 rows that used
  qor_xtime.placement. Do not draw conclusions from them until re-timed.
- Re-timed results go to C:\Users\finnf\open-dfx-xc7-vivado\build\place_xtime2 (place_bench `vivado_tag`), the old
  ones stay in place_xtime for comparison.
- Old-extraction numbers from this morning, for the record only (biased): anchored stub rv_soc s1 110.11, s3 117.67;
  bram s1 153.68 MHz (Vivado timer). place_diag on rv_soc s1: footprint sd_x/sd_y 12.1/8.3 (Vivado 10.6/5.5,
  old fix_static 8.4/16.9), but the 100 worst Vivado paths still take 65.7 hops (bbox 37.4): the anchored start fixes
  the shape, not the stretched critical paths (they zigzag 16-25 grid units in x between successive LUTs).

New tooling (committed 330b4a0, efcb64f):
- flow/place_vivado.sh: Vivado-time `build/qor/place/xsrc/<name>` with vivado/build_xtime.tcl, one name per Vivado
  slot (vivado_slot.sh locks, 5 s polling like flow/dpl_vivado.sh).
- vivado/build_xtime.tcl: a source with `dump.flag` also writes cells.txt and the 1000 worst paths (paths.txt) after
  Vivado's route, in place_dump.tcl's format. Without the flag nothing changes.
- flow/place_vqueue.sh: two-worker Vivado queue: `add NAME...`, `worker ID`; workers exit when
  build/qor/place/gp/vq/STOP exists.
- flow/place_diag.py `--ours NAME`: the diagnosis on any dumped run (default output byte-identical to before).
  Cross metrics need the same yosys netlist as the Vivado reference dump; the self metrics are always valid.
- flow/place_shape.py: footprint from nextpnr's routed JSON (sd_x/sd_y, slices, RAM sites, HPWL), no Vivado.
- flow/place_summary.py: one row per design x variant: Vivado Fmax per seed, nextpnr Fmax, HPWL, slices, sd,
  worst-100 hops, nextpnr seconds.

nextpnr draft docs/drafts/nextpnr-placer-density.{patch,md} (worktree build/src/nextpnr-place; builds place_v12/13/14;
v13 adds the packing-dpl draft to this worktree so carry-di-bypass combines with the placer options):
- `-o static-group-util=COMB,FF,RAM,DSP`: target utilisation per cell group (change 3, target density).
- `-o static-ram-assign`: block RAMs legalised by a global cheapest-first assignment on timing-weighted predicted delay
  to their neighbours (step 4). bram s1: RAMs in 3 columns (11 / 7 / 6) as Vivado (6 / 11 / 7), against 2 columns of 12.
- No-op: options off -> `.frames` identical to place_v11 on rv_soc and bram, seeds 1-3 (v12, v13, v14, anchoring on),
  and place_v14 with no options identical to the `ref` binary (pl_base) on rv_soc and bram, seeds 1-3.

nextpnr side, seeds 1-3, stub chipdb (nextpnr timer for Fmax; rv_soc and rv_mul are ICAP-limited at ~131-138 MHz
there, so only shape/area columns say anything):

| design | variant | nextpnr Fmax mean | sd_x / sd_y | slices | HPWL after legalisation |
|---|---|---|---|---|---|
| rv_soc | pl_base (= pl14_off_stub) | 135.37 | 9.2 / 13.2 | 492 | 17363 |
| rv_soc | anchored (pl11_anc20ipw_stub) | 135.84 | 13.2 / 7.1 | 483 | 18305 |
| rv_soc | anchored + target util 0.9 | 135.82 | 15.1 / 5.7 | 466 | 16301 |
| rv_soc | anchored + target util 1.0 | 135.79 | 15.8 / 5.3 | 458 | 15403 |
| bram | pl_base | 149.45 | 16.4 / 18.2 | 323 | 22485 |
| bram | anchored | 149.71 | 25.1 / 18.1 | 337 | 23344 |
| bram | anchored + tu 0.9 | 149.44 | 24.4 / 16.4 | 335 | 22117 |
| bram | anchored + tu 1.0 | 150.63 | 20.0 / 15.5 | 331 | 22029 |
| bram | anchored + RAM group util 1.0 (gur) | 152.08 | 20.9 / 18.0 | 331 | 22431 |
| bram | anchored + tu 1.0 + carry-di-bypass | 131.96 | 7.0 / 13.9 | 275 | 20303 |

- Target utilisation 1.0 (elfPlace's setting) gives the flattest, smallest footprint: rv_soc HPWL -11 % against
  pl_base, slices 458 vs 492, sd_y 5.3 (Vivado 5.5). Vivado timing of it is pending (re-time).
- Further finished nextpnr runs (seeds 1-3, sources prepared and queued): pl14_anc20ipw_ra_stub, pl14_anc20ipw_gur_ra_stub,
  pl14_anc20ipw_tu10_ra_stub (rv_soc, bram, rv_big), pl13_anc20ipw_tu10_cdb_stub (rv_soc, bram, rv_big),
  pl13_off_dq and pl13_anc20ipw_tu10_cdb_dq (rv_mul; the dspq netlist as in Finding 16), pl11_anc20ipw_stub rv_big,
  pl14_off_stub rv_big.

Next lever (09:20-09:40): **criticality against a slack quantile** (`--placer-static-crit-quantile Q`, place_v15,
draft nextpnr-placer-density). Why: nextpnr's criticality is 1 - (slack - worst) / -worst, and on rv_soc the worst
path is the ICAPE2 one (5.2 ns clock-to-out under hardblock-timing), so the logic paths Vivado finds critical get a
low criticality and a net weight near 1 in the global placer. With Q the static placer's analyser measures against
the slack at quantile Q of the port slacks. No-op: options off -> frames identical to place_v11 (rv_soc s1-3).
nextpnr side, seeds 1-3 (anchored + ip-wait + target util 1.0 = "tu10"):

| design | variant | nextpnr Fmax mean (nextpnr timer) | sd_x / sd_y | slices | HPWL after legalisation |
|---|---|---|---|---|---|
| rv_soc | base | 135.37 | 9.2 / 13.2 | 492 | 17363 |
| rv_soc | tu10 + cq 0.02 | 138.01 | 10.1 / 7.9 | 438 | 16932 |
| rv_soc | tu10 + cq 0.02 + carry-di-bypass | 135.08 | 10.2 / 6.7 | 388 (Vivado 398) | 17349 |
| bram | base | 149.45 | 16.4 / 18.2 | 323 | 22485 |
| bram | tu10 + cq 0.02 | 153.73 | 23.9 / 15.2 | 321 | 20953 |
| bram | tu10 + cq 0.02 + RAM assign | 144.22 | 28.3 / 18.2 | 341 | 23328 |
| bram | tu10 + cq 0.02 + carry-di-bypass | 134.69 | 7.1 / 14.4 | 287 | 20080 |
| rv_big | base | 103.64 | 14.6 / 9.8 | 748 | 25539 |
| rv_big | tu10 + cq 0.02 | 102.48 | 13.0 / 9.9 | 668 | 23218 |
| rv_big | tu10 + cq 0.02 + carry-di-bypass | 105.09 | 10.5 / 9.2 | 605 | 21769 |
| rv_mul (dspq) | base (pl13_off_dq) | 136.22 | 12.4 / 12.2 | 633 | 26733 |
| rv_mul (dspq) | tu10 + cq 0.02 | 134.90 | 15.5 / 8.7 | 651 | 21055 |

- cq 0.05 was no better than 0.02 in nextpnr's timer (rv_soc 138.12, bram 145.69, rv_big 100.89).
- The combination is the most compact we have (rv_soc 388 slices against Vivado's 398; HPWL -9 % rv_big, -21 % rv_mul).
  Whether it moves Fmax is for Vivado's timer: queued right after the baselines (tu10_cq02, then + cdb, rv_mul dq).
- Vivado: from 08:59 to 10:07 my workers won no slot (QoR suite, rte and rte_arcs runs took both slots back to back). The queue workers (flow/place_vqueue.sh worker 1, 2; logs build/qor/place/gp/vq3_w*.log) keep running; stop them with touch build/qor/place/gp/vq/STOP.

Path-based refinement, first try (10:15, place_v16): the dpl detailed placer (packing-dpl draft) had the same
flattening, so it saw 25 candidate cells on rv_soc. A 6th `-o dpl` field now sets the criticality quantile
(`dpl=2,3,0.8,4,0,0.02`). rv_soc s1 then gets 53-54 candidates and 24/13/10 moves. nextpnr timer, 3 seeds:
rv_soc 136.65 (138.01 without), bram 150.72 (153.73), rv_big 102.87 (102.48); with carry-di-bypass bram goes
134.69 -> 141.40. Not yet Vivado-timed. No-op: v16 without the field = v15 (rv_soc s1-3 frames identical).

Vivado queue from 10:08: slot 2 (vivado.lock2) is reserved for this queue. Worker 2 waits on it only (VIV_SLOT=2),
worker 1 takes either. Order: stub baselines (pl14_off_stub rv_soc/bram/rv_big, rv_mul pl13_off_dq), then
pl15_tu10_cq02_stub, rv_mul pl15_tu10_cq02_dq, pl15_tu10_cq02_cdb_stub, anchored, then the rest.
First re-timed result (fixed extraction, Vivado timer): stub base rv_soc s2 112.56 MHz (the biased old number for
the same placement was 117.45).

To resume:
1. `rm build/qor/place/gp/vq/STOP`, then `setsid nohup flow/place_vqueue.sh worker 1` (and 2). The queue
   (build/qor/place/gp/vq/names.txt, 51+ names, re-prepared with the fixed extraction, dump.flag set) starts with the
   baselines: pl14_off_stub (= stub base) rv_soc/bram/rv_mul(pl13_off_dq)/rv_big, then anchored, tu10+ra,
   tu10+cdb, tu10, ra. `next` was reset; names whose place_xtime2/<name>/status.txt exists are skipped.
2. Table: `python3 flow/place_summary.py --designs rv_soc bram rv_big --variants pl14_off_stub pl11_anc20ipw_stub ...`
   (rv_mul: pl13_off_dq, pl13_anc20ipw_tu10_cdb_dq).
3. No Vivado slot was won 08:59-09:15 (QoR suite, router and dpl agents held both slots).

## Change 1 tried: anchored initial placement (2026-11-07 10:40, build place_v11)
- New opt-in option `--placer-static-anchor-init N`, in common/place/placer_static.cc, `anchor_initial`.
  - Before spreading, it runs N Jacobi star-model relaxations. Each movable cell moves halfway to the mean position of the cells it shares a net with (fanout <= 16). Fixed cells are included: IO and the ICAP.
  - So the start reflects where the fixed blocks are, instead of a Gaussian blob at the device centre.
- No-op with the option off: `.frames` identical to place_v4, rv_soc, 3 seeds.

rv_soc, 3 seeds, route-calibrated chipdb (nextpnr timer for Fmax):

| variant | nextpnr Fmax (seeds) | sd_x / sd_y | slices | RAMB36 sites (s1) |
|---|---|---|---|---|
| off | 103.48 / 99.99 / 93.93 | 10.0 / 15.4 | 495 | X1Y15, X1Y16 |
| `anchor-init 20` | 100.85 / 87.15 / 95.47 | 9.8 / 9.9 | 502 | - |
| `anchor-init 20` + `ip-wait 0.5` | 95.69 / 90.04 / 98.84 | 13.5 / 6.3 | 479 | X1Y3, X1Y7 (next to the ICAP, as Vivado's X0/X1 Y4) |
| Vivado's own placement | 157.63 (Vivado timer) | 10.6 / 5.5 | 398 | X0Y4, X1Y4 |

- The shape is now Vivado-like: sd_y 6.3 against Vivado's 5.5 and our 15.4 before, with the RAMs at the ICAP.
- nextpnr's own Fmax is within the seed spread, about 4 % lower in the mean.
- **Vivado timer, 3 seeds, rv_soc** (Vivado routes our placement):
  - `anchor-init 20`: 117.37 / 119.03 / 109.46, mean 115.29 MHz.
  - `anchor-init 20` + `ip-wait 0.5`: 119.13 / 113.74 / 124.80, mean **119.22 MHz**.
  - Stub baseline 116.81; route-calibrated plp_rcal 117.18.
  - That is +2.1 % with a Vivado-like shape. It is still inside the seed spread (111-126), so it is not yet a proven win.
- **bram and rv_big, `anchor-init 20` + `ip-wait 0.5`, Vivado timer, 3 seeds** (11:00-11:08):

  | design | stub baseline pl_base | rcal chipdb, no anchoring (plp_rcal) | anchored + ip-wait (rcal) |
  |---|---|---|---|
  | rv_soc | 116.81 | 117.18 | 119.22 (+1.7 % vs rcal) |
  | bram | 155.87 | 149.35 | 151.44 (155.11 / 152.37 / 146.84; +1.4 %) |
  | rv_big | 104.95 | 93.82 (seeds 1-3) | 101.41 (105.70 / 92.77 / 105.75; +8.1 %) |

  - Against the same route-calibrated chipdb, anchoring helps all three designs: +1.4 % to +8.1 %.
  - Against the stub-chipdb baseline it is +2.1 % on rv_soc, -2.8 % on bram and -3.4 % on rv_big.
  - The shape gain is clear on rv_soc only. bram and rv_big have 24 and 16 RAMB36, spread over RAM columns, and their sd_y stays 10-18 (plp_rcal 8-20).
  - nextpnr timer: bram 131.53 / 129.42 / 116.46, rv_big 91.37 / 89.44 / 86.39 MHz.
- **Stub chipdb, anchored + ip-wait** (variant `pl11_anc20ipw_stub`), nextpnr timer only:
  - rv_soc 137.93 / 138.18 / 131.41 MHz (pl_base: 134.19 / 134.19 / 137.72).
  - bram 149.50 / 146.28 / 153.35 MHz (pl_base: 150.99 / 150.53 / 146.82).
  - The run went past the 11:30 stop: the machine was paused, and bram s1 shows 26741 s of wall time. So it is not Vivado-timed.
  - xsrc is ready: `{rv_soc,bram}_p5_pl11_anc20ipw_stub_s{1,2,3}_placed`.
- Next session:
  1. Vivado-time pl11_anc20ipw_stub (sources ready). Anchored start with the stub chipdb, which isolates the anchoring effect from the cell-chipdb loss. Also on eth and rv_mul.
  2. Add target density (change 3) on top, since the cells per bin are still lower than Vivado's.
  3. Combine it with Finding 15's `-o carry-di-bypass`.
  4. Measure top-100 path hops with flow/place_diag.py once a Vivado placement dump of the new variant exists. vivado/place_dump.tcl in "placed" mode gives one.

## Change 2 tried: y-weighted wirelength (2026-11-07 10:30, build place_v10)
- The finding: `-o static-hpwl-x/-y` (hpwl_scale_*) never reached the global placer's gradient. It only feeds the HPWL log and placer1 refinement. That is why the earlier `hx1` runs barely moved the global shape.
- New opt-in option `-o static-grad-y=F` scales the y component of the global wirelength gradient. `-o static-hpwl-y=N` was also added, for the placer1 cost.
- No-op with the options off: `.frames` identical to place_v4, rv_soc, 3 seeds.

rv_soc, 3 seeds, route-calibrated chipdb, nextpnr timer:

| variant | Fmax MHz (seeds) | sd_x / sd_y | slices | HPWL after legalisation (mean) |
|---|---|---|---|---|
| off (baseline) | 103.48 / 99.99 / 93.93 | 10.0 / 15.4 | 495 | 17142 |
| `static-grad-y=2` | 84.75 / 97.44 / 89.85 | 10.9 / 17.6 | 483 | 20532 |
| `static-grad-y=2`, `static-hpwl-x=1`, `static-hpwl-y=2` | 86.24 / 83.77 / 89.12 | 10.9 / 17.6 | 480 | - |
| `static-grad-y=0.5` | 91.30 / 88.72 / 90.34 | 7.7 / 13.9 | 511 | 17508 |

- The y weight does not flatten the placement. Weight 2 makes it taller, 0.5 makes it slightly flatter, and every setting costs Fmax.
- So the tall shape is not set by the wirelength balance. It comes from the density equilibrium around the fixed blocks and the early RAM legalisation.
- That points to change 1 (anchored initial placement and RAM co-placement) and change 3 (target density) as the real levers.
- Not Vivado-timed: nextpnr's calibrated timer already shows a loss, and no slot was free.
- sd_x / sd_y come from flow/place_sdy.py (slice positions in nextpnr's routed JSON, prjxray grid units).

## DIAGNOSIS for the global-placer rewrite (2026-11-07, rv_soc; no new Vivado runs)
Data:
- Vivado's own placement: C:\Users\finnf\open-dfx-xc7-vivado\build\place_dump\rv_soc_p5_fix_static_free.
- Ours: nextpnr fix_static imposed, `..._placed`.
- Script: flow/place_diag.py; output build/qor/place/diag/rv_soc.json; prjxray grid units, where one CLB column is 2 in x.

What Vivado does that we don't:
1. **Vivado builds around the fixed hard block.**
   - The ICAP is fixed at ICAP_X0Y1, in the bottom clock region.
   - Vivado places the two RAMB36 at X0Y4/X1Y4, next to it, and the CPU logic and the register-file LUTRAMs in SLICE rows Y19-33 around them.
   - We put the RAMB36 at X1Y15/16, mid-device, and the logic and LUTRAMs at rows Y36-89, away from the ICAP.
   - Our static placer starts from the device centre and legalises the RAMs early, so the fixed ICAP barely pulls anything.
2. **Vivado's footprint is flat and wide; ours is tall.**

   | | x range | y range | sd x / y | 4x4 bins used | cells per used bin |
   |---|---|---|---|---|---|
   | Vivado | 23-84 | 117-140 (24 rows) | 10.6 / 5.5 | 55 | 37.8 |
   | ours | 33-90 | 58-124 (66 rows) | 8.4 / 16.9 | 82 | 25.3 (density 33 % lower) |

   Our wirelength weights x twice as much as y (`hpwl_scale_x = 2`). The Vivado-fitted delay says the opposite: 63 ps per y unit against 37 ps per x unit up to the knees (`static-delay` fit). So the placer is pushed to spread vertically, which is the expensive direction.
3. **We stretch our own critical paths.** The 100 worst paths are summed over Manhattan hops along the path:

   | paths | in our placement | in Vivado's placement |
   |---|---|---|
   | our 100 worst | 65.7 hops (bbox 44.1) | 20.0 hops (bbox 16.4) |
   | Vivado's 100 worst | 30.4 hops | 28.2 hops |

   - Our placer spreads exactly the paths that then become critical. They run between the ICAP/RAM endpoints and logic placed far away.
   - The timing weights (1 + 5·crit²), driver->sink arcs (pl8) and preconditioning (pl9) did not fix it, because the anchoring and aspect ratio are wrong before timing matters.
4. **Carry chains are not the problem.** Ours are more often contiguous columns (18 of 23 chains) than Vivado's (11 of 23).
5. Not measured: per-module bounding boxes, because the yosys netlist is flattened and the dump's cell names don't carry hierarchy. Datapath bit order was not measured either, because the dump's EDIF names did not map to the yosys JSON in the time left.

Concrete algorithm changes, in order:
1. **Anchored initial placement.**
   - Before Nesterov, run a quadratic or star-model solve with all fixed cells (IO, ICAP, and BRAM/DSP when pre-placed) as anchors, instead of starting from the centre.
   - Co-place the RAMB/DSP with their logic: keep `ip-wait`-style late legalisation, but pull the RAMs toward the fixed anchors.
   - Effort: 1-2 days in placer_static.cc. Measure the hops of the 100 worst paths, sd_y, and Vivado-timed Fmax on rv_soc, bram and rv_big.
2. **Anisotropic wirelength matching the delay.**
   - `-o static-hpwl-x=1` already exists. Add a y weight, for example `-o static-hpwl-y=2`, so the wirelength gradient follows the 63:37 delay ratio and the footprint gets flat and dense like Vivado's.
   - Effort: under 1 day. The earlier hx1 tests only removed the x penalty; they never added a y penalty.
3. **Target density instead of spreading to the overlap stop.**
   - Vivado packs 38 cells per 4x4 bin against our 25. Use a per-group target density so the electrostatic equilibrium is compact (elfPlace-style target density per resource), not just "overlap < 0.1".
   - Effort: about 2 days.

Port of an electrostatic placer:
- placer_static.cc already is one: ePlace/RePlAce-style FFT electrostatics with Nesterov. A full port of elfPlace or DREAMPlace-FPGA is therefore not the next step. Their gains come from items like those above, plus multi-resource fields, augmented-Lagrangian density and area adjustment.
- Cheaper first: run DREAMPlaceFPGA (BSD-3, Python/C++/CUDA) as an external oracle through a placement exchange (bookshelf-style netlist export, positions imported as `-o preplaced`). That costs about 1 week. Vivado-time its placement to bound the achievable gain before porting anything.
- A full in-tree port: about 3-4 weeks for multi-field density, ALM, preconditioner, area adjustment and clock-region handling, plus validation.

## Resume 2026-11-07 09:36-11:05
- pl8 (timing-arc term) timed by Vivado, 3 seeds: rv_soc 109.11, bram 154.20, rv_big 94.95 MHz. Static-delay alone gives 115.02 / 150.42 / 99.44; the stub baseline is 116.81 / 155.87 / 104.95. Not a win.
- pl9 (weighted preconditioner), Vivado timer, 3 seeds: rv_soc 116.83, bram 146.80, rv_big 90.57 MHz. rv_big HPWL is -13 %, but it is still not a win.
- Packing that follows global placement (coordinating with Finding 15's carry-di-bypass) was not started: no time left.
  - Finding 15's mixes show global placement costs about 10 MHz on rv_soc (Vivado's packing at our positions 137.9 vs 148.35 at its own), so global placement remains the lever.
  - Next idea there: re-pack after global placement, e.g. elfPlace-style area adjustment (survey item 5), on top of `-o carry-di-bypass`.

## STATE AT WRAP-UP (2026-11-07 ~01:50)
- Round-2 Vivado results are in docs/qor-vivado.md Finding 13 ("Placement round 2").
- Still running when I stopped: two of my Vivado runs, left to finish on their own.
  - chunk_03 (rv_big plp_cal/plp_rcal s1-3) holds vivado.lock2; chunk_04 (rv_soc pl6_sd/sdpc) holds vivado.lock.
  - Their worker3.sh processes release the locks when the runs end and take no further chunks (the claims are set).
- Not yet run in Vivado:
  - chunk_20 (pl8_sdarc2 x rv_soc/bram/rv_big): the timing-arc term;
  - chunk_21 (pl9_sdwp x 3): the weighted preconditioner.
  - Their xsrc is ready. Names: `<d>_p5_pl8_sdarc2_rcal_s{1,2,3}_placed` and `<d>_p5_pl9_sdwp_rcal_s{1,2,3}_placed`.
- Next:
  1. Vivado-time pl8 and pl9.
  2. Find out why the cell-calibrated chipdb lowers Vivado-timed Fmax (bram -5.5 %, rv_big -12 %).
  3. Survey items 3-5 (timing schedule, carry alignment, clustering area).
  4. Move to flow/qor_suite.py.
  5. The static-for-all-sizes default, which belongs to the release agent.

## Placer literature survey (2026-11-06, papers and their open code only)
Ranked by expected Fmax gain under Vivado's timer against effort, for the global placer (placer_static.cc already
does electrostatic FFT density with Nesterov):
1. Driver->sink timing-arc wirelength term, w = crit^8-9 on critical arcs.
   - Source: DREAMPlaceFPGA timing-driven, FCCM 2024. Code BSD-3 (github.com/rachelselinar/DREAMPlaceFPGA).
   - Implemented as `--placer-static-arc-ratio` (place_v8).
   - First runs are negative on rv_soc in nextpnr's timer; Vivado timing is queued.
2. Preconditioner that includes net and timing weights, plus a guard on the density/wirelength gradient ratio.
   - Sources: Mai/Wang/Lin TCAD 2024 (OpenPARF, BSD-3); elfPlace ICCAD 2019.
   - Mai et al. report the preconditioner alone gave a 49.7 % WNS gain in their ablation.
3. Timing-update schedule: start once the overflow is below 0.15, update every 5 iterations, at most 20 updates;
   scale the term to the wirelength gradient (DREAMPlaceFPGA parameters).
4. Per-iteration carry-chain column alignment (Mai et al.: 46.8 % WNS gain in their ablation).
5. Area adjustment for clustering compatibility (elfPlace Eq. 32-34): LUT input pins, FF control sets. This targets
   the 398 vs 501 slice gap.
6. Routability and pin-density inflation (elfPlace).
7. Augmented-Lagrangian density weight (elfPlace), instead of the fixed x1.025 per iteration.

- UTPlaceF, RippleFPGA and GPlace are binaries only, or have no code.
- AMF-Placer 2.0 (Apache-2.0) reports critical path delay within 0.6-2.2 % of Vivado.
- Detailed placement is the packing/detailed-placement agent's.

## Heap vs static default (ofx/defaults.py `static_max_cells` = 3000; question from the runtime agent)
Evidence so far:

| design | static placer | HeAP |
|---|---|---|
| mc12_a100 (30k LUT) | 173 s place, routes with 0 overuse, 124 MHz (nextpnr timer) | 921 s HeAP + 267 s SA, router diverges (docs/runtime.md) |
| DDR SoC, Vivado WNS | -1.96 / -1.87 ns (2 seeds) | -1.584 ns (1 seed) |
| DDR SoC, nextpnr pnr time | 61-79 s | 80 s |
| eth SoC, Vivado WNS | -5.15 / -4.28 / -4.30 ns | -4.730 ns (1 seed) |
| eth SoC, nextpnr pnr time | 82-89 s | 208 s |

- **Result (Vivado timer, 3 seeds, nextpnr build place_ref, stub chipdb):**

  | design | static placer, Vivado Fmax mean (min-max) | HeAP, Vivado Fmax mean (min-max) |
  |---|---|---|
  | DDR | 83.92 (83.63-84.22), 2 seeds; on s3 Vivado could not place around the imposed cells | 84.46 (81.99-86.75) |
  | eth | 68.64 (65.99-70.03) | 67.39 (66.23-69.06) |

  Static costs no Fmax beyond seed noise, and it is better on every other measure (`place_bench --metrics`):

  | design | placer1 wirelength, static vs HeAP | routed wires | router iteration-1 overuse | router iterations | nextpnr s |
  |---|---|---|---|---|---|
  | DDR | 136654 vs 160257 | 222016 vs 229656 | 10013 vs 11907 | 11.7 vs 19.0 | 71 vs 105 |
  | eth | 152990 vs 213697 | 284522 vs 298662 | 10974 vs 15270 | 14.0 vs 26.3 | 85 vs 193 |

  On mc12_a100, HeAP does not route at all. **Recommendation:** static for every size, i.e. remove `static_max_cells`. That is for the release agent's noop/regression process.
- (was:) Running now: HeAP for 3 seeds on DDR and eth (`plh_base`, run9.log), to be timed by Vivado against `pl_base`.
- Leaning: static for all sizes (remove the 3000-cell threshold), unless DDR's heap advantage survives 3 seeds. The decision is the release agent's: defaults go through the noop/regression process.

## Done (verified)
- Route-delay calibration re-verified (build/xroute/verify/r3):
  - draft patches apply;
  - chipdb without `--route-timing` is byte-identical to chipdb-cal/on, and with the JSON to chipdb-rcal/on;
  - the lut-perm-timing no-op holds (FASM sorted, SDF, report);
  - strict and loose refits reproduce the numbers.
- Placer delay models measured against Vivado (flow/xroute_predict.py, build/xroute/predict/):
  - static placer formula -433 ps mean on the test designs; predictDelay -731 / -538 ps (cal / rcal chipdb);
  - fitted models bring both to about -30 ps mean.
- Key fact: the static (global) placer ignores the chipdb (fixed formula), so the rcal chipdb never changed the
  global placement: HPWL after legalisation is identical.
- Drafts docs/drafts/nextpnr-placer-delay-cal.{patch,md}: `-o static-delay`, `-o predict-cal`,
  `--placer-static-timing-every`. Builds place_v5 and place_v6. The v5 no-op holds: frames identical on 9 runs.
- place_bench `--metrics` (HPWL, placer1 wirelength, routed wires, router iteration-1 overuse, runtime).

## Committed
- 15b24fc: xroute_predict, the placer-delay-cal draft, the hold draft, place_bench `--metrics`.
- 56dfe69: Finding 13 and the roadmap rows.

## nextpnr timer only so far (rcal chipdb, rv_soc, 3 seeds)
Runtimes are inflated: machine load is about 19.

| variant | mean MHz |
|---|---|
| plp_rcal | 99.13 |
| pl6_sd | 97.34 |
| pl6_sdpc | 95.37 |
| pl6_te2 | 99.46 |

- No gain in nextpnr's timer.
- HPWL after legalisation: 17142 (plp_rcal) vs 17514 (sd).
- Only Vivado's timer can decide these.

## STOPPED 21:40: Vivado never became free (another agent's run held it from 20:09 on), so no Vivado-timed placement result of round 2 exists yet
To resume: run the three batches below under the lock rule. The xsrc for every name is prepared and fresh.
- Batch 1: `<d>_p5_{plp_cal,plp_rcal}_s{1,2,3}_placed` for d in rv_soc, bram, rv_big, and `eth_p10_{plp_cal,plp_rcal}_s{1,2,3}_placed`.
- Batch 3: `<d>_p5_{pl6_sd_rcal,pl6_sdpc_rcal}_s{1,2,3}_placed` for the same three designs, and `rv_mul_p5_pl6_sd_dqrcal_s{1,2,3}_placed`.
- Batch 2: `<d>_p5_{pl5_pc_rcal,pl5_pc_cal}_s*`, `rv_mul_p5_{plp_dqcal,plp_dqrcal,pl5_pc_dqrcal}_s*`, `eth_p10_pl5_pc_rcal_s*`.
- Also ready: `<d>_p5_plp_rcal_s{4..8}_placed` (run5) for a seed-selection study. It asks whether the rcal nextpnr timer, now calibrated, picks the best seed under Vivado's timer.
- Runner: `vivado/run_qor.ps1 -Tag place_xtime -Script build_xtime.tcl -SrcRel build\qor\place\xsrc -Names <comma list> -Run`.

## Vivado queue (planned 21:30)
- The locked chain runs batch 1+3, then batch 2.
- Batch 1+3: plp_cal/plp_rcal x rv_soc/bram/rv_big/eth, then pl6_sd/pl6_sdpc x rv_soc/bram/rv_big and rv_mul pl6_sd_dq.
- Batch 2: pl5_pc_*, rv_mul plp_dq*, eth pl5.
- Name lists: the scratchpad names1/2/3.txt; they can be rebuilt from `place_bench.py` variant names, `<design>_p5_<variant>_s<seed>_placed`.
- Results land in C:\Users\finnf\open-dfx-xc7-vivado\build\place_xtime.
- Table: `python3 flow/place_bench.py --report --designs ... --variants ...`.

## Running / queued
- Vivado (locked queue, scratchpad vivq.sh): place_xtime batch 1 (plp_cal/plp_rcal x rv_soc/bram/rv_big/eth,
  3 seeds) and batch 2 (pl5_pc_*, rv_mul dq cal/rcal/pc, eth pl5).
  - None had run by 21:00: another agent's Vivado held the machine.
- nextpnr:
  - run6 (place_v6 variants pl6_* on rv_soc/bram/rv_big, rv_mul pl6_sd_dqrcal), log build/qor/place/r13/run6.log;
  - run5 (plp_rcal seeds 4-8, for a seed-selection study), log build/qor/place/r13/run5.log.

## Next
1. When Vivado frees up: report Vivado-timer Fmax (seed means) for plp_cal vs plp_rcal vs pl5_pc vs pl6_sd*,
   with HPWL, routed wires and runtime (`--metrics`).
2. xprep the pl6 runs and Vivado-time them.
3. Write Finding 13 in docs/qor-vivado.md:
   - the draft text is in build/xroute/finding12.md (the old name); use the r3 strict tables;
   - the end-to-end rcal numbers, the placer model section, and placement round 2.
4. Update the roadmap rows "Placement and routing" and "Setup/hold, worst path, Fmax", and add a "Hold fixing" row.

## Handed over
- Hold repair went to the router agent (message sent):
  - docs/drafts/nextpnr-hold-fix-upstream.patch, flow/hold_bench.py, worktree build/src/nextpnr-hold, build
    build/nextpnr-build/hold;
  - the Vivado xroute runs for bufr are queued (names bufr_p10_hold_{rel,up}_s1).

## Uncommitted paths of mine
- flow/place_bench.py (variants, `--metrics`, npwait 3), flow/xroute_predict.py, flow/hold_bench.py.
- docs/drafts/nextpnr-placer-delay-cal.*, docs/drafts/nextpnr-hold-fix-upstream.patch.
