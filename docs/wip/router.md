# WIP: router workstream (router2, Vivado-timed routing share) + hold repair

State 2026-11-06 ~21:50. Owner: router agent. Hold repair handed over (second priority).

## Done
- Harness `flow/route_xtime.py` + `vivado/build_rte.tcl` (committed). Stages vref/own/import/npr/export/vivado/report.
  - vref: Vivado places+routes the yosys netlist (no opt_design) -> cells.txt + slack.txt (WNS with/without ICAPE2).
  - import: Vivado cells mapped onto nextpnr's packed names -> `-o place-import=FILE`.
  - export: flow/xroute.py export; `<name>` = nextpnr pips imposed, `<name>_vr` = same placement, Vivado routes.
- nextpnr worktree build/src/nextpnr-rte (release tree 961ea46e), build build/nextpnr-build/rte
  (build/nextpnr-build/rte_build.sh). UNCOMMITTED source changes there (to become docs/drafts/nextpnr-router-timing.patch):
  - `-o place-import=FILE` (xilinx.cc apply_place_import)
  - `--router2-opt KEY=VALUE` (command.cc) and router2 settings critExp, critFloor, critEstWeight/Thresh,
    critRipupIters/Thresh/ResetCong/KeepBest (router2.cc/.h). Keep-best snapshot is in source, NOT yet built.
- Hold: docs/drafts/nextpnr-hold-fix-upstream.{patch,md} + flow/hold_bench.py committed (a623b07).
  x_iodly_minmax (nextpnr timer, hold binary): hold-fix + upstream repairs input hold (3 detours + 2 buffers, 0 left),
  route-min-scale 0.39 needs 4 detours + 18 buffers; Fmax 72.34 unchanged (build/rte/iodly/).

## Screening so far (nextpnr timer, NOT Vivado)
- cal chipdb timer is 0.3-0.6 ns/arc optimistic (Finding 13 draft), so screening uses the rcal chipdb.
- rv_soc rcal, own placement, mean of seeds 1-3: base 99.13, crr3 (no keep-best) 101.84, ew1 100.45, cexp8 96.33 MHz.
- crr3 (rip-up rounds with congestion reset) crashed on a partial-net rip-up (assert in route_arc); fixed by ripping
  the whole net.

## Blocked
- Vivado: another agent's vivado.exe (pid 26308) holds /mnt/c/Users/finnf/vivado.lock since before 20:40.
  Queued: vref runs (python flow/route_xtime.py vref --run, pid 100350, waits for lock); then bufr hold runs
  (designs/rte/bufr_p10_hold_{rel,up,msfix}_s1, mode fixed).

## Next
1. After vref: `import --run`, `npr --variants vimp --run`, `export --variants own vimp --run`, `vivado`, `report`.
2. Rebuild rte with keep-best; screen crr3 variants with rcal; take best + rcal to Vivado.
3. Write Finding (routing share, each change: Vivado timer mean over seeds, runtime).

## Update ~22:35
- Vivado vref (Vivado places+routes the yosys netlist, no opt_design; Vivado timer, excl. ICAPE2):
  rv_soc 173.2, rv_mul 157.9, rv_big 166.7, bram 172.3 MHz (WNS_noicap -0.774/-1.363/-0.999/-0.805 ns at 5 ns);
  place+route 82/76/99/93 s. /mnt/c/Users/finnf/open-dfx-xc7-vivado/build/rte/<d>_vref/.
- place-import works (option registered); rv_soc binds 1908 cells, ~35-85 carry clusters per design cannot sit at
  Vivado's root (nextpnr re-chunks chains / duplicates S LUTs) and go to the placer.
- nextpnr timer with rcal chipdb, nextpnr router on Vivado's placement (vimp, seed 1): rv_soc 103.92, rv_mul 102.16,
  rv_big 104.13, bram 131.87 MHz; on its own placement (own, mean s1-3) 99.13 / 87.15 / 90.40 / 125.40.
  To be confirmed by Vivado's timer (queued: <d>_vimp_cal_s1 / _vr, <d>_own_cal_s1 / _vr, rcal --no-vr).
- Router options, rcal, own placement, paired mean of seeds 1-3 (nextpnr timer): sd1crk3 (critSeedDelay=1 +
  critRipupIters=3 keep-best) +4.0/+5.7/+2.1/+4.3 % (rv_soc/rv_mul/rv_big/bram), router time not higher;
  crk3 +3.4/+1.9/+2.1/+1.8; sd1 -0.1/+5.0/+2.0/+3.5; cexp8 and ew1 within noise.
- Run binary: build/nextpnr-build/rte-run (copy; never rebuild in place while runs are queued).

## State at the 01:40 stop (2026-11-07)
- Committed: Finding 16 in docs/qor-vivado.md (nextpnr rcal timer numbers; Vivado reference placements), draft
  docs/drafts/nextpnr-router-timing.{patch,md} (no-op verified on 4 designs), hold draft md with x_iodly_minmax.
- NOT measured: every Vivado-timed router number. Exported and ready (C:\Users\finnf\open-dfx-xc7-vivado\designs\rte\):
  <d>_vimp_cal_s1 (+_vr), <d>_own_cal_s1 (+_vr), <d>_vimp_rcal_s1, <d>_vimp_sd1crk3_rcal_s1, <d>_own_rcal_s{1,2,3},
  <d>_own_sd1crk3_rcal_s{1,2,3}, bufr_p10_hold_{rel,up,msfix}_s1. My runs waited for a slot 22:02-01:15 without one.
- Resume: `python3 flow/route_xtime.py vivado --variants vimp --chipdb cal --run` (pairs), then
  `vivado --variants vimp vimp_sd1crk3 --chipdb rcal --no-vr --run`, `vivado --variants own own_sd1crk3 --chipdb rcal
  --seeds 1 2 3 --no-vr --run`, `vivado --variants own --chipdb cal --run`, `vivado --names bufr_p10_hold_*_s1 --run`;
  then `report`, `python3 flow/route_cmp.py <name>...` for per-path routing deltas, and fill Finding 16.
- Next router ideas: load/fanout-aware cost for critical arcs; packer mode keeping yosys CARRY4 boundaries so the
  Vivado import is exact.

## State at the 11:30 stop (2026-11-07)
- Vivado-timed check of `critSeedDelay=1` + `critRipupIters=3` against the base (rcal, own placement, same placement
  per seed) is in Finding 16: rv_soc -0.0 %, rv_mul +4.0 %, rv_big +0.5 %, bram +3.1 % (paired, 3 seeds); rv_mul and bram never
  worse, the CPUs mixed. Options stay opt-in/off until more seeds.
- Lesson: nextpnr's rcal timer is right on average (-8.4..+7.7 % per run vs Vivado) but cannot rank router changes of
  a few percent; judge router work with Vivado's timer.
- Still exported, not run: <d>_vimp_cal_s1 (+_vr), <d>_own_cal_s1 (+_vr) (router share on identical placement);
  single-option runs rv_{soc,big}_own_{sd1,crk3}_rcal_s1; bufr_p10_hold_*_s1.
- flow/route_xtime.py now kills a cmd.exe that outlives its Vivado run (one held slot 2 for 34 min on 2026-11-07).
- Next: router-share pairs in Vivado; a load/fanout-aware critical-arc cost validated by Vivado; exact import
  (packer mode keeping yosys CARRY4 boundaries).
- Single-option runs (Vivado timer, excl. ICAPE2, seed 1, same placement as the base s1): rv_big critSeedDelay=1
  76.69 MHz (WNS_noicap -8.040), rv_big critRipupIters=3 83.04 (-7.042) against base 83.29; rv_soc critSeedDelay=1
  98.18 (-5.185) against base 101.40. rv_soc critRipupIters=3 was cut off at the final stop (the machine slept
  ~11:15-18:30 and the run restarted after the deadline); rerun it.
- All my jobs are stopped; no Vivado slot held.

## State 2026-11-08 morning
- rv_soc `critRipupIters=3` s1 (the run cut off at the last stop) did finish on 2026-11-07 18:37: Vivado timer 101.40 MHz (WNS_noicap -4.862), identical to the base s1. nextpnr's keep-best restored the first legal routing (all 3 rip-up rounds worse on its own timer), so routes.txt is byte-identical to the base. Single-option table for rv_soc: crk3 s1 0.0 %.
- New harness: vivado/build_rte.tcl dumps every routed net's pips as node pairs plus driver/load pin nodes when RTE_ROUTE_DUMP=1 (routes_dump.txt, ~35 s); flow/rte_dump_vivado.sh runs it (results C:\Users\finnf\open-dfx-xc7-vivado\build\rte_arcs\); flow/route_arcs.py compares, arc by arc on the identical placement, nextpnr's pips (NAME) against Vivado's own routing (NAME_vr), both Vivado-timed: wire classes, hops, travel vs Manhattan, branching, LUT route-throughs.
- rv_soc own_rcal s1, Vivado routing the identical placement: WNS_noicap -4.664 (103.48 MHz) vs nextpnr's routes -4.862 (101.40): the router share on this seed is only +2.0 % (Vivado timer), not 15-20 %.
- Per-arc (Vivado timer, 357 arcs on the 200 worst paths of either run): nextpnr's routes are 55.6 ns slower in sum (1182 vs 1026 ps per arc). 45 arcs that pass **through an unused LUT** (IMUX -> LUT pin -> LUT -> LOGIC_OUTS, chipdb pip class LUT_ROUTETHRU with timing SITE_NULL, i.e. free in nextpnr's model) carry 41.8 ns of it (930 ps per arc); Vivado's routing uses no route-through at all. Arcs of the same shape are equal (-13 ps). Over all 7057 arcs nextpnr is on average 121 ps faster (Vivado spends delay on non-critical arcs).
- Draft change (opt-in, rte tree, binary build/nextpnr-build/rte-nrt): `-o no-lut-routethru` makes LUT_ROUTETHRU pips unavailable to the router (set in preRoute, so placement is unchanged). Variants own_nrt / own_nrt0 (no-op) in route_xtime.py; nextpnr runs started (build/rte/nrt_npr.log).
- Router share on the identical placement, seed 1 (Vivado timer, excl. ICAPE2; nextpnr's pips imposed vs Vivado routing the same placement; build/rte_arcs): rv_soc 101.40 vs 103.48 (+2.0 %), bram 135.45 vs 140.21 (+3.5 %), rv_big 83.29 vs 93.04 (+11.7 %); rv_mul's Vivado-routed run failed to launch (WSL interop "accept4 failed"), requeued. Seeds 2-3 queued (build/rte/arcs_chain2.sh, log arcs_viv2.log).
- Worst nextpnr path, arc by arc against Vivado's routes: rv_big +1.52 ns on the path, of which one LUT route-through arc +643 ps, one arc using LV18 + two hexes for a short hop +629 ps, a detour +228 ps; rv_soc +0.19 ns (one detour); bram +0.43 ns (BRAM DI arc over LV18/LH12/LV18/LH12 long lines). bram's 200-path set has no route-through; there the long lines are the candidate.
- No-op: `-o no-lut-routethru` off (rte-nrt binary, variant own_nrt0) gives FASM identical to the base on rv_soc, rv_mul, rv_big and bram (s1). nextpnr side (rcal timer, not trusted for ranking) own_nrt vs base s1-3: rv_soc 99.99/101.90/95.80 vs 103.48/99.99/93.93; rv_mul 87.37/90.88/86.93 vs 86.63/90.40/84.42; rv_big 90.74/94.75/90.07 vs 87.80/93.25/90.16; bram 128.53/131.30/116.37 vs 128.53/125.16/122.52; router2 time lower on 10 of 12. Vivado timing queued (build/rte/nrt_viv.log).
- 12:05 no-lut-routethru under Vivado's timer, 3 seeds x 4 designs (Finding 16): rv_soc +2.0 %, rv_mul +1.8 %, rv_big +2.4 %, bram -1.0 % paired; mean +1.3 %; router2 time lower on 9/12. Opt-in, not a default yet.
- Runner notes: Vivado slot 2 is the global placer's; my runners take slot 1 only (rte_dump_vivado.sh polls vivado.lock every 3 s; RTE_OUT/RTE_ROUTE_DUMP=0 reuse it for plain build/rte runs). Careful: a bash script's LAST command is exec'd, so killing a chain script whose last line is a runner kills the runner (its lock then has to be released by hand).
- Queued: router share seeds 2-3 (build/rte/arcs_chain3.sh -> arcs_viv2.log): rv_soc s2 _vr done, rest pending.
- 12:30 router share seeds 2-3 done (Finding 16): 3-seed mean +4.9 % over 12 runs (Vivado routes vs nextpnr routes on the same placement).
- 17:40 LUT pins (top priority): nextpnr already permutes LUT pins in router2 (LUT_PERMUTATION pseudo-pips, fixup_routing), but never onto A6 for <6-input LUTs, and its pin choice ignores that Vivado-timed routes into A1/A2 are ~350 ps slower than into A5/A6 (rv_soc dp0 s1, nextpnr's own pin choice timed by Vivado: mean arc net delay A1 1.27-1.44, A2 1.32-1.35, A3/A4 1.16-1.21, A5 0.99-1.01, A6 0.94 ns). Drafts:
  - A: chipdb variant with A6 permutation pips (build/chipdb-rcal-a6, gen env OFX_LUT_A6_PERM=1; docs/drafts/nextpnr-lut-a6-perm-gen.patch) + `-o lut-a6-perm` (docs/drafts/nextpnr-lut-a6-perm.patch, binary build/nextpnr-build/lpa): the pips are usable only with the option and only for a LUT alone on the 6LUT (empty 5LUT, no A6 net, not memory/SRL).
  - B: chipdb variant build/chipdb-rcal-a6pd that also times the permutation pip by physical pin (OFX_LUT_PIN_DELAY=350,330,190,160,0,0 ps), so router and timer prefer A5/A6 for critical arcs.
  - No-op: lpa binary + A6 chipdb without the option gives FASM identical to dp0 (dpl0 binary, rcal chipdb) on rv_soc, bram, rv_mul, rv_big s1. With the option rv_soc puts 133 LUTs' inputs on A6 (A+B: 184), bram 66 (116).
  - Variants lp0/lpA/lpB/lpAB in flow/lpa_bench.py; exact-import Vivado queue build/exact/lpa_viv.sh (starts 17:55 after the SA yield); decode + firmware sim of lpA/lpAB rv_soc s1 running (build/exact/check_lp*.log).
- 19:00 s1 under Vivado's timer (exact import, pins locked, Fmax excl. ICAP; base = dp0, FASM identical to lp0): rv_soc 103.48 -> lpA 109.94 / lpB 109.02 / lpAB 112.93; bram 140.21 -> 142.47 / 143.76 / 143.76; rv_mul 87.05 -> 87.65 / 94.08 / 94.08; rv_big 92.61 -> 95.76 / 98.03 / 96.74 (means lpA +3.0, lpB +5.5, lpAB +6.1 %). lpA and lpAB rv_soc s1 decode + firmware sim 11/11. s2/s3 queued (build/exact/lpa_viv2.sh).
- `-o lut6-first` (same draft patch, binary build/nextpnr-build/lpb): after placement a LUT alone on a 5LUT moves to its 6LUT and a lone x5FF flip-flop to its xFF where the tile stays legal (clustered/locked cells stay). rv_soc s1: 135 LUTs and 78 FFs moved, 0 refused. Off = FASM identical to dp0 (rv_soc, bram s1). Variants lpX (alone, rcal chipdb) and lpXAB (with A6 + pin delays) queued (build/exact/lpx_viv.sh).
- 21:00 exact-import Vivado table (Fmax excl. ICAP, % vs dp0 = option-off FASM), s1: rv_soc lpA +6.2 / lpB +5.4 / lpAB +9.1 / lpX (lut6-first) +9.7 / lpXAB (lut6-first + A6 + pin delays) +17.3 (121.4 MHz); bram +1.6 / +2.5 / +2.5 / +2.2 / +3.4; rv_mul +0.7 / +8.1 / +8.1 / +1.7 / +12.1; rv_big +3.4 / +5.9 / +4.5 / +1.7 / pending. s2: lpA rv_soc +7.0, bram +0.2, rv_mul -0.1, rv_big +7.3; lpAB +5.1 / +4.1 / +7.7 / +0.0. lpX and lpXAB rv_soc s1 decode + firmware sim 11/11. Remaining s2/s3 queued after the SA slot window (build/exact/resume2.sh, 21:15).
- The A6 chipdb variants need the patched binary (docs/drafts/nextpnr-lut-a6-perm.md): an unpatched binary routes through the A6 pips and fails in FASM.

## State at the wind-down (2026-11-08 ~22:05)
Vivado timer, exact import (flow/exact_src.py), nextpnr's LUT pins locked, Fmax excl. ICAPE2, % against dp0 (= option-off FASM of every variant):
| run | base | lpA | lpB | lpAB | lpX | lpXAB | lpX2AB |
|---|---|---|---|---|---|---|---|
| rv_soc s1 | 103.48 | +6.2 | +5.4 | +9.1 | +9.7 | +17.3 | +17.2 |
| bram s1 | 140.21 | +1.6 | +2.5 | +2.5 | +2.2 | +3.4 | +2.2 |
| rv_mul s1 | 87.05 | +0.7 | +8.1 | +8.1 | +1.7 | +12.1 | +18.6 |
| rv_big s1 | 92.61 | +3.4 | +5.9 | +4.5 | +1.7 | +11.0 | +6.6 |
| rv_soc s2 | 98.87 | +7.0 | - | +5.1 | - | +14.1 | - |
| bram s2 | 137.14 | +0.2 | - | +4.1 | - | +2.5 | - |
| rv_mul s2 | 90.20 | -0.1 | - | +7.7 | - | - | - |
| rv_big s2 | 87.26 | +7.3 | - | +0.0 | - | - | - |
lpA = A6 permutation (chipdb-rcal-a6 + -o lut-a6-perm), lpB = per-pin permutation delays (chipdb-rcal-a6pd), lpX = -o lut6-first (rcal chipdb), lpXAB = lut6-first + A6 + pin delays, lpX2AB = lut6-first=2 (also splits LUT pairs) + A6 + pin delays. Binaries build/nextpnr-build/lpa (A, B), lpb (X, XAB), lpc (X2AB). Bitstreams of lpA, lpAB, lpX, lpXAB, lpX2AB rv_soc s1 decode and pass the firmware bench 11/11. Worst-100-path LUT inputs on A5+A6: rv_soc 23 -> 30 %, rv_mul 32 -> 55 % (dp0 -> lpXAB s1).
Pending (nextpnr runs done, exact sources exported, held in C:\Users\finnf\open-dfx-xc7-vivado\designs\exact_hold): all s3, the rest of s2, lpX2AB s2/s3 (nextpnr not yet run: `python3 flow/lpa_bench.py --variants lpX2AB --seeds 2 3 --run`, then `python3 flow/exact_src.py <d> lpX2AB <s> --run`).
Resume: `mv /mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact_hold/* /mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact/` then `SRC=/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact RTE_OUT=/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact RTE_ROUTE_DUMP=0 flow/rte_dump_vivado.sh --run <names>` (slot 1 only); table: the script in this file's history (wns_noicap of build/exact/<name>/slack.txt against <d>_p5_dp0_s<n>_exact).
Next: rebase the drafts onto 0032, make lpXAB the default candidate once s2/s3 confirm, pair splitting by criticality (critical LUTs off 5LUT pairs).

## s1-s3 complete (2026-11-09)
Held runs finished (build/exact/ua_run2.sh). % Fmax against dp0 on the same seed, Vivado timer, exact import:
| variant | rv_soc | bram | rv_mul | rv_big | mean | runs > base |
|---|---|---|---|---|---|---|
| lpA | +6.2 +7.0 -2.8 | +1.6 +0.2 +1.1 | +0.7 -0.1 +5.8 | +3.4 +7.3 -0.1 | +2.5 (12) | 9/12 |
| lpB | +5.4 +3.9 +9.1 | +2.5 +4.1 +0.3 | +8.1 +5.9 +7.8 | +5.9 +3.0 +0.5 | +4.7 (12) | 12/12 |
| lpAB | +9.1 +5.1 +7.7 | +2.5 +4.1 +0.2 | +8.1 +7.7 +7.2 | +4.5 +0.0 +3.8 | +5.0 (12) | 11/12 |
| lpX | +9.7 +9.5 +1.0 | +2.2 +2.5 +0.2 | +1.7 +0.0 +6.3 | +1.7 -1.1 -1.0 | +2.7 (12) | 10/12 |
| lpXAB | +17.3 +14.1 +14.2 | +3.4 +2.5 +0.1 | +12.1 +4.9 +6.8 | +11.0 +1.7 +4.3 | +7.7 (12) | 12/12 |
lpXAB confirmed (12/12 runs better, +7.7 % mean); it is already part of cb_all. Per-pin delays alone (lpB) are 12/12
too, matching the equal-pin-cost test in docs/wip/user-assumptions.md (-3.9 % when the delays are made equal).
lpX2AB s2/s3 never ran (s1 only: +17.2 / +2.2 / +18.6 / +6.6).
