# WIP: Vivado-calibrated arc delay table (`-o dtab`) -- state file

Owner: the delay-table agent (resumed 2026-11-10 after the hard stop). Lever 1 of
docs/wip/placement-research-2026-11.txt. Updated at every milestone; the resume commands are at the end.

## What it is
An arc delay table fitted on Vivado's routed net delays, used instead of the linear `static-delay=816,40,40,18,18`
estimate by the static global placer's timing update and by sa-refine. All opt-in:
- `-o dtab=FILE` loads the table; `-o static-delay=dtab` (global placer timing update); sa-refine key `dtab=1`;
  `-o dtab-fo=K` scales the fanout term (0 = off); `-o dtab-predict` (predictDelay); `-o dtab-eval` (logs the worst
  setup slack of the final placement under each arc model, no effect on the result).
- Model between tiles: `G[|dix|][|diy|] + src[pin class] + dst[pin class] + crossings + fo[log2 sinks]`; dix = distance
  in INT columns, diy = rows without HCLK/BRKH rows; crossings = a cost per BRAM / DSP / clock / break column and per
  HCLK / BRKH row passed. Inside a tile: dedicated in-slice path `direct`, routed same slice `site[src][dst]`, other
  slice `tile[src][dst]`.
- The table only feeds the timing analysis that sets criticalities (arc weights 1 + W crit^E); the placer's gradient
  is still wirelength, so the table needs no smoothing for this use.

## Where things are
- nextpnr source: worktree `build/src/nextpnr-dtab` (base e0a13c17 = the replication tree), UNCOMMITTED edits in
  common/place/placer_static.{cc,h} (`predict_arc` hook), himbaechel/uarch/xilinx/{xilinx.cc,xilinx.h,sa_refine.cc,
  CMakeLists.txt} and the new himbaechel/uarch/xilinx/dtab.cc. Binary `build/nextpnr-build/dtab/nextpnr-himbaechel`.
- Scripts: `flow/dtab/` (rescued from the killed agent's scratchpad, paths made relative):
  build_ds.py (dataset), fit.py (fit + table file), dtab.py (Python twin of the C++ lookup), dl.py (geometry, pin
  classes, the old models), measure.py (per-arc error by class), pathlev.py (path level), eval_run.py + corr.py
  (placer-side slack under each model vs Vivado), noop.py, lodo.sh (leave-one-design-out), dt_run.sh + dt_viv.sh (bench).
- Data: `build/dtab/` (not in git): arcs/ (624 runs), t_mean.txt, t_crit.txt, t_fo.txt (= t_fo_v1.txt, the table the
  bench variants use), fit_*.log, m_test.md, path_s3.md, noop/, eval/.
- Bench variants (flow/place_bench.py, uncommitted hunk next to the replication agent's `split` hunk): `cb2_dt`
  (table + fanout term), `cb2_dtnf` (dtab-fo=0), `cb2_dt_tw10`, `cb2_dt_tw20`, `cb2_dt_tw20ce4` (the timing weights
  that failed with the linear model), each with a `_dq` twin for rv_mul. Control = `ua_dxy` (= cb_all2).

## What the killed agent had finished (reconstructed 2026-11-10)
1. **Dataset, no new Vivado runs.** There were no dedicated probe nets: build_ds.py takes every routed sink pin of the
   exact imports already timed by Vivado (C:\Users\finnf\open-dfx-xc7-vivado\build\exact\<run>\net_delays.txt, SLOW_MAX
   net delay) with driver/sink cell type, BEL, tile position, sink count and the rank of the worst Vivado path it is on.
   624 runs (4 designs x ~45 placement variants x seeds, plus Vivado's own placements `vref`), ~3.9 M arcs.
2. **Fit** (fit.py): train = seeds 1,2,4,5,6 (440 runs, 2.46 M arcs between tiles); alternating least squares on
   bin means, G shrunk toward the additive X[dix] + Y[diy] with weight 30. Training rms: t_mean 179.6 ps,
   t_crit (arcs on Vivado's 50 worst paths weighted x20) 182.7 ps, t_fo (per-log2-fanout term) 198.4 ps on the finer
   bins. Fitted terms (t_fo): one INT column ~+52..70 ps, one row ~+53 ps, BRAM column +76 ps, HCLK row +39 ps,
   fanout +35 / +111 / +231 / +352 / +459 / +633 / +753 ps for 2-3 / 4-7 / ... / 128+ sinks, direct in-slice 52 ps.
3. **Held-out test** (seed 3 of every variant + vref, 184 runs, 1.48 M arcs; m_test.md, path_s3.md) -- see the
   accuracy section.
4. **nextpnr integration** built; **no-op verified**: the dtab binary without the options, and with
   `-o dtab=... -o dtab-eval` only, gives FASM identical to ua_dxy (cb_all2) on rv_soc s1 and rv_mul s1 (only the
   version comment differs; re-checked 2026-11-10 with build/dtab/s_noop.sh). So the existing ua_dxy exact-import
   results are the control "same binary, table off".
5. Started, nothing finished: `-o dtab-eval` re-runs of old placements (6 logs, rv_soc only), and the first bench
   run (cb2_dt rv_soc s1 was in the router when killed). **No Vivado-timed result of any dtab variant existed.**

## Table accuracy (Vivado's routed net delay, SLOW_MAX; error = model - Vivado)
Held-out seed 3 + vref, 184 runs. Cell = mean error / mean |error| ps / Pearson r.

| arc class | n | Vivado mean ps | static 816,40,40,18,18 | sa-refine 313+1.235*matrix | table (t_mean) | table + fanout (t_fo) |
|---|---|---|---|---|---|---|
| all | 1476771 | 986 | +66 / 403 / 0.75 | -20 / 261 / 0.84 | +1 / 230 / 0.88 | +1 / 214 / 0.90 |
| between tiles | 1034783 | 1307 | -140 / 332 / 0.70 | -31 / 331 / 0.72 | +1 / 298 / 0.77 | +2 / 277 / 0.81 |
| CLB->CLB distance 17-32 | 165400 | 1883 | -442 / 544 / 0.39 | -318 / 491 / 0.40 | -28 / 443 / 0.46 | -24 / 384 / 0.63 |
| CLB->CLB distance 33+ | 39214 | 2449 | -333 / 587 / 0.22 | -371 / 568 / 0.23 | +22 / 512 / 0.36 | +4 / 456 / 0.52 |
| crosses BRAM/DSP column | 399787 | 1549 | -239 / 397 / 0.67 | -126 / 379 / 0.67 | +3 / 339 / 0.76 | +2 / 310 / 0.80 |
| crosses HCLK row | 195733 | 1800 | -276 / 467 / 0.63 | -198 / 450 / 0.64 | -6 / 410 / 0.72 | -3 / 367 / 0.78 |
| fanout >= 16 | 395221 | 1637 | -340 / 488 / 0.64 | -234 / 453 / 0.66 | -135 / 384 / 0.75 | +4 / 375 / 0.77 |
| same slice, direct | 291063 | 52 | +764 / 766 | -52 / 52 | 0 / 34 | 0 / 34 |
| on Vivado's 50 worst paths | 7973 | 960 | +72 / 212 / 0.69 | +155 / 243 / 0.69 | +133 / 244 / 0.69 | +65 / 219 / 0.71 |

(full table: build/dtab/m_test.md.) Reading:
- The table removes the bias the linear model has on long, column-crossing and high-fanout arcs (-240..-440 ps ->
  within 30 ps) and cuts the mean |error| between tiles by 17 % (332 -> 277 ps); r 0.70 -> 0.81.
- **On the arcs that matter (Vivado's 50 worst paths) it is no better than the linear model** (219 vs 212 ps mean
  |error|, r 0.71 vs 0.69) and it is pessimistic by +65 ps per arc: Vivado's router gives critical arcs better routes
  than the average arc of the same geometry, and no geometry-only table can know which arcs those are.
- Path level (Vivado's 50 worst paths of each seed-3 run, 9000 paths, path_s3.md), path delay error mean / mean |.|:
  static +18.5 / 18.9 % (it charges 816 ps for every dedicated in-slice hop), sa-refine's model +8.9 / 12.5 %,
  table + fanout +5.6 / 9.7 %; by design, table + fanout: bram -3.8 / 4.4 %, rv_big +1.1 / 6.7 %,
  rv_mul +11.9 / 13.7 %, rv_soc +13.5 / 14.0 %.

### Leave-one-design-out (2026-11-10, flow/dtab/lodo.sh)
Table + fanout fitted on the other three designs (seeds 1,2,4,5,6), tested on every arc of the held-out design's
control placements (ua_dxy seeds 1-6). Mean error / mean |error| ps / r; "in-sample" = t_fo (design seen in training).

| held-out design | class | n | static | sa-refine model | table, design held out | table in-sample |
|---|---|---|---|---|---|---|
| rv_soc | between tiles | 29770 | -195 / 345 / 0.67 | -8 / 317 / 0.70 | +15 / 264 / 0.76 | +19 / 262 / 0.77 |
| rv_soc | CLB->CLB d 17-32 | 4901 | -645 / 671 / 0.35 | -340 / 487 / 0.38 | -20 / 355 / 0.62 | -11 / 354 / 0.62 |
| rv_soc | fanout >= 16 | 11850 | -423 / 504 / 0.64 | -208 / 400 / 0.70 | +33 / 342 / 0.72 | +35 / 339 / 0.73 |
| rv_big | between tiles | 42085 | -202 / 365 / 0.71 | -28 / 340 / 0.73 | -3 / 278 / 0.81 | +10 / 275 / 0.81 |
| rv_big | CLB->CLB d 33+ | 662 | -853 / 945 / 0.26 | -572 / 724 / 0.19 | -91 / 497 / 0.47 | -52 / 475 / 0.53 |
| rv_mul | between tiles | 40128 | -172 / 328 / 0.71 | +2 / 309 / 0.75 | +47 / 269 / 0.80 | +40 / 265 / 0.81 |
| rv_mul | fanout >= 16 | 16071 | -376 / 466 / 0.72 | -184 / 385 / 0.77 | +81 / 348 / 0.78 | +65 / 339 / 0.79 |
| bram | between tiles | 22044 | -112 / 320 / 0.76 | +51 / 316 / 0.76 | +55 / 327 / 0.82 | +55 / 269 / 0.85 |
| bram | crosses HCLK row | 4280 | -89 / 411 / 0.61 | -17 / 405 / 0.61 | +331 / 491 / 0.71 | +139 / 366 / 0.79 |
| bram | CLB->CLB d 33+ | 1479 | -47 / 351 / 0.39 | -114 / 338 / 0.34 | +409 / 513 / 0.46 | +80 / 301 / 0.56 |
| bram | fanout >= 16 | 4598 | -263 / 565 / 0.56 | -22 / 522 / 0.52 | +282 / 507 / 0.73 | +146 / 448 / 0.79 |

- The three CPU designs generalise to each other (held-out = in-sample within 5 ps): there the table is a real
  model of the device, 20-25 % lower mean |error| between tiles than the linear model and no bias on long arcs.
- **bram does not transfer**: a table that never saw bram is +330..+410 ps pessimistic on its long / HCLK-crossing /
  high-fanout arcs and no better than the linear model overall (327 vs 320 ps). Long arcs in the congested CPU
  placements are slower than long arcs in bram's regular RAM-column layout; (dx, dy, fanout) does not carry that.
  So the table is partly a model of these placements, not only of the device: congestion is the missing feature.
- Path level, held-out design, Vivado's 50 worst paths of its seed-3 runs (path delay error mean / mean |.|):
  rv_soc +13.1 / 13.7 % (in-sample +13.5 / 14.0), rv_mul +12.3 / 14.0 (+11.9 / 13.7), rv_big +0.8 / 6.5 (+1.1 / 6.7),
  bram -6.4 / 6.9 (-3.8 / 4.4). Files build/dtab/lodo_*.md, lodo_path_*.md.

### Critical-arc-weighted fit (t_fo_c200.txt: arcs on Vivado's 50 worst paths weighted x200)
All held-out arcs: unchanged (mean |error| 226 vs 214 ps for t_fo; between tiles 284 vs 277). Path level (same 9000
paths): mean |path error| 9.7 % -> 8.1 % (bram 2.4, rv_big 5.6, rv_mul 12.2, rv_soc 12.3 %), still +11..12 % pessimistic
on rv_soc / rv_mul. x5000 gives 7.6 % but a ragged, non-monotone table (X[dix] 623 .. 4460 ps), rejected.
Whatever the weighting, a geometry table over-predicts the CPU designs' critical paths by ~11 %: Vivado's router
gives those arcs the fast wires. Bench variant `cb2_dtc` uses t_fo_c200.

## Bench (exact import, Vivado timer) -- RUNNING
Yardstick: Vivado 2025.2 timer (`wns_noicap` of slack.txt, Fmax = 1000 / (5 - WNS) MHz) on the exact import of our
placement (flow/exact_src.py + vivado/build_rte.tcl "fixed" mode, Vivado only routes), same seed against `ua_dxy`.
Results table: filled in below when runs finish (`python3 flow/dtab/dt_table.py`).

## Log
- 2026-11-10 11:50 resumed. Scripts rescued to flow/dtab/. No-op re-checked. Started the bench: producer
  flow/dtab/dt_run.sh (V = cb2_dt cb2_dtnf cb2_dt_tw10 cb2_dt_tw20ce4 cb2_dt_tw20, seeds 1-3, 4 designs, nextpnr one at a
  time) + 2 Vivado workers flow/dtab/dt_viv.sh (each run takes a vivado_slot.sh lock). Leave-one-design-out fits
  started (flow/dtab/lodo.sh).

## Resume commands
```
cd ~/open-dfx-xc7
# state: what is running, queue, results so far
ps -eo pid,etime,args | grep -E "[d]t_run|[d]t_viv|nextpnr-build/[d]tab"; cat build/dtab/q_dt.txt; tail build/dtab/dt_run.log
# (re)start the bench; finished runs are skipped (slack.txt present), a stale claim of a killed Vivado run must go first:
#   rmdir build/exact/claims/<name>  for names without C:\...\build\exact\<name>\status.txt
V="cb2_dt cb2_dtnf cb2_dt_tw10 cb2_dt_tw20ce4 cb2_dt_tw20" TAG=dt SEEDS="1 2 3" setsid nohup bash flow/dtab/dt_run.sh > build/dtab/dt_run.log 2>&1 &
TAG=dt setsid nohup bash flow/dtab/dt_viv.sh 1 > build/dtab/dt_viv_1.out 2>&1 &
TAG=dt setsid nohup bash flow/dtab/dt_viv.sh 2 > build/dtab/dt_viv_2.out 2>&1 &
# stop everything of this workstream: touch build/dtab/STOP (loops leave after the current run)
# rebuild the binary: see "Build" below; refit: python3 flow/dtab/fit.py build/dtab/t_fo.txt --fo
```
Build: `cmake -S build/src/nextpnr-dtab -B build/nextpnr-build/dtab -G Ninja -DARCH=himbaechel -DHIMBAECHEL_UARCH=xilinx
-DCMAKE_BUILD_TYPE=Release ...` (same flags as the other worktrees; toolchain/buildenv/env/bin on PATH), then
`ninja -C build/nextpnr-build/dtab nextpnr-himbaechel`.
