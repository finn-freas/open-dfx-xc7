# WIP: global placement + delay calibration (Finding 13) -- state file

Owner: the route-timing/placement agent. Updated 2026-11-06 evening.

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
