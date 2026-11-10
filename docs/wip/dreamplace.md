# WIP: DREAMPlaceFPGA as an external global placer (state file)

Owner: the DREAMPlace-eval agent. Started 2026-11-08 13:30.

## Goal
Measure what a state-of-the-art open FPGA placer (DREAMPlaceFPGA, BSD-3, github.com/rachelselinar/DREAMPlaceFPGA,
commit 00449431, 2025-04-30) gains on rv_soc / bram / rv_big, 3 seeds, Vivado's timer, against our static placer
and Vivado's own placement. Result goes to docs/dreamplace-eval.md.

## Findings so far
- No 7-series architecture exists in DREAMPlaceFPGA. It supports the ISPD'16 simplified UltraScale (Bookshelf) and
  UltraScale+ through the Interchange Format. Its packer-legalizer hard-codes the UltraScale slice
  (`SLICE_CAPACITY = 16`, CARRY8, 2 CK/SR + 4 CE per CLB) and has no carry-chain, LUTRAM, SRL or MUXF7/F8 support
  (the ISPD'16 benchmarks contain none). So its legalizer and detailed placer cannot produce a legal Artix-7 placement
  without a port of those stages.
- Dependencies pinned upstream: Python 3.5-3.7 (3.8 works per issues), PyTorch 1.6-1.8 (2.x incompatible), CUDA < 12.
  The laptop GPU is an RTX 5060 (sm_120, needs CUDA >= 12.8), so the build is CPU-only. Designs are 2-6k cells; CPU is
  enough.

## Approach (GP exchange)
- nextpnr draft (worktree build/src/nextpnr-dpf = nextpnr-place state of 13:24 + this change, build
  build/nextpnr-build/dpf): `--placer-static-gp-dump FILE` writes the static placer's own problem (placer grid,
  per-group bel areas, cells/macro chunks with nextpnr's areas, nets without global/constant nets);
  `--placer-static-gp-import FILE` takes the cell positions instead of the Nesterov spreading, then runs nextpnr's
  usual strict legalisation (IP first, then logic) and placer1 refinement. Macro chunks are put back around the mean
  anchor of their imported positions.
- flow/dpf_bridge.py: dump -> Bookshelf (one SLICE site per CLB tile = 8 LUT6 / 16 FF, as the ISPD SLICE;
  BRAM per RAMB36 bel; DSP per DSP48E1 bel; IO per fixed-cell location), and DREAMPlace .gp.pl -> import file.
- So the comparison isolates global placement: same packer, legaliser, refiner, router; Vivado routes and times the
  final placement (place_bench xprep -> vivado/build_xtime.tcl).

## Log
- 13:30 cloned to toolchain/dreamplacefpga/src; conda-forge env via micromamba (toolchain/dreamplacefpga/env).
- 13:55 nextpnr build dpf done (no-op: `pl_dpf_off` = dpf binary without the options, rv_soc s1 `.frames` IDENTICAL
  to pl14_off_stub). gp-dump of rv_soc/bram/rv_big in build/dpf/dump/<d>/gp.dump (placer grid 45 x 154).
- 14:00 conda-forge env (micromamba from conda-forge; sharded repodata failed with TLS resets, flat repodata works):
  python 3.8, pytorch 1.8.0 cpu, gxx 9, boost 1.85, cmake 3.29. DREAMPlaceFPGA built CPU-only into
  toolchain/dreamplacefpga/install. Two local fixes (docs/drafts/dreamplacefpga/, toolchain/.../patches/):
  upstream has no CMakeLists for ops/timing (timer_cpp is never built, so BasicPlace's import fails), and
  create_loc2site_map is UltraScale-only (IndexError on other site maps) -> wrapped.
  Self-test: ISPD'16 FPGA-example1 GP converges (overflow < 0.1 at iter 1522, CPU, 4 threads).
- Export fixes found on rv_soc: (1) DSP site past the grid top corrupted the heap; (2) DREAMPlaceFPGA assumes full-height
  columns (region boxes, RAM every 5 rows, DSP every 2.5): the model is now regular columns; (3) **nodes with identical
  connectivity stay stacked** (a cell split into k nodes on one star net: identical gradients) -> LUT overflow stuck at
  0.35 and HPWL diverged. Now the cell's nets are spread round-robin over its nodes, chained by 2-pin nets:
  GP converges (rv_soc: iter ~600-1550, 35-95 s CPU).
- First end-to-end rv_soc s1 (pl_dpf_wl): DREAMPlace GP HPWL in nextpnr's metric 14722 (our static GP before its
  legalisation ~15300), but nextpnr's strict legalisation adds +9418 (ours +2645) -> 24266 vs 17946 after legalise.
  nextpnr timer 131.67 MHz (ICAP-bound design; ours 134.19). DREAMPlace packs at target density 1.0 on nominal areas;
  nextpnr's own GP spreads to 0.7 with FF area 1.4x. Sweeping target_density / routability on rv_soc s1 (HPWL proxy).
- Vivado timing switched to flow/exact_src.py (coordinator, 4f4c0f9): exact import, Vivado only routes. Baselines
  pl14_off_stub x 3 designs x 3 seeds exported and queued (build/dpf/logs/viv_base.log, results build/exact).
- 15:00 bridge v2: one Bookshelf node per packed netlist cell (LUT<k> with I0..I5/O, FDRE with D/Q/C/CE/R, CARRY4 as
  LUT6), macro chunk members chained; dump carries port/type/cell per pin. nextpnr `--placer-static-gp-import-warm`
  (draft): start nextpnr's own spreading from the imported positions instead of legalising them directly.
  rv_soc s1, nextpnr metric: cold import 17017 GP -> 24023 after legalise; warm 17698 (ours 17946).
  DREAMPlaceFPGA ignores `target_density` (fixed per-region targets in PlaceDB.py) and its result does not depend on
  random_seed with deterministic_flag=1: seeds 1-3 differ only in nextpnr's legalisation/refinement.
- No-op re-checked on the final dpf binary: rv_soc s1-3 `.frames` IDENTICAL to pl14_off_stub.
- Batch build/dpf/run_all.sh (log build/dpf/logs/run_all.log): pl_dpf_wl, pl_dpf_warm x 3 designs x 3 seeds.
- Timing-driven DREAMPlaceFPGA: works after a one-line levelization fix (timing_graph.py max_level) and driverless
  chain nets (else igraph finds cycles); 7-series model build/dpf/timing7 (net delay = the static-delay fit
  786,63,29,37,7 ps; logic delays approximate: LUT 124, FF 456, RAMB36 2454 ps).
- Vivado references: exact pl14_off_stub (9 runs) done; vref (Vivado places the same exported netlist) queued.
- 15:30 all DREAMPlace runs done (wl, warm, td, td_warm x 3 x 3; nextpnr side in `python3 flow/dpf_summary.py
  --variants pl14_off_stub pl_dpf_wl pl_dpf_warm pl_dpf_td pl_dpf_td_warm`). Nextpnr timer / HPWL: no variant beats
  our static placer except rv_soc warm (+0.9 % nextpnr timer, noise level); bram cold HPWL 2.4x ours (DREAMPlace
  spreads the 24 RAMB36 over Y2..Y29 of three columns, ours packs them in Y8..Y22 of two).
- Vivado: slot 1 was taken back to back by other queues 15:17-16:03. 16:06 I replaced my three rte_dump_vivado.sh
  queues by flow/dpf_vivado.sh (vivado_acquire / vivado_release, as instructed). **Incident:** the kill reached the
  queue that was running rv_soc_p5_pl_dpf_wl_s1_exact in its last seconds; its EXIT trap released vivado.lock about
  5 s before that Vivado exited (it completed normally: rc 0, status 16:06:25), and another agent's run took slot 1
  at 16:06:21. No run was cut; the result is valid. Queue: build/dpf/logs/viv_q.log (37 names).
- Vivado references (Vivado timer): exact pl14_off_stub rv_soc 101.65 / bram 143.13 / rv_big 88.51 MHz (3 seeds);
  Vivado placing the same exported netlist itself (vref, no opt_design): rv_soc 136.02 (148.81 excl. ICAP),
  bram 164.07.
- 17:30 Vivado (exact import, Vivado timer), seed 1, MHz: rv_soc ours 101.39 / wl 99.36 / warm 100.67 / td_warm 103.43;
  bram ours 139.12 / wl 123.35 / warm 126.47 / td_warm 129.80; rv_big ours 88.75 / wl 83.75 / warm 85.11 /
  td_warm 84.43. Vivado placing the same netlist: rv_soc 136.02 (148.81 excl. ICAP), bram 164.07, rv_big 110.89.
  Seeds 2-3 running (queue build/dpf/logs/viv_q3.log, seed-major order).
- 18:13 Vivado paused for the coordinator (slot 1 reserved for the LUT-pin queue until ~19:45): the 15 pending sources
  were moved to C:\Users\finnf\open-dfx-xc7-vivado\designs\exact_paused_dpf\, so the runner skipped them and exited
  cleanly after rv_big td_warm s2. Resume: move them back to designs\exact\ and
  `setsid nohup flow/dpf_vivado.sh --run <names in build/dpf/logs/viv_q3.log line 1>`.
  Seeds 1-2 done for wl / warm / td_warm, seed 1 for td.
- 18:20 coordinator: after 19:45 slot 1 belongs to the SA agent until ~21:00; use slot 2, alternating with the
  global placer's place_vqueue (take it only when no place_vivado.sh runs, or one run after each of its runs).
  flow/dpf_vivado.sh now does exactly that (flag build/dpf/logs/last_dpf_run vs place_xtime2 status.txt).
  build/dpf/resume_viv.sh (started 18:14) waits until 19:46, moves the paused sources back, and execs the runner
  (log build/dpf/logs/viv_q4.log).
- 18:45 one-metric GP comparison (flow/dpf_gpcmp.py on the gp-dump nets; ours = nextpnr's static GP just before
  logic legalisation, new debug option `--placer-static-gp-out FILE`; seed 1; placer grid units):
  rv_soc ours HPWL 11829 sd_x/sd_y 3.2/16.4, DREAMPlace 8261 5.8/5.0 (-30 %, Vivado-like flat shape);
  rv_big ours 15370 5.6/10.4, DREAMPlace 12188 6.4/5.8 (-21 %); bram ours 15470, DREAMPlace 40343 (2.6x: RAMB36
  scattered over Y2..Y29). With nextpnr's x weight 2 the rv_soc/rv_big gain shrinks to -14 % / -4 %.
  So DREAMPlace's GP is better in wirelength on the CPUs, and the gain is lost in legalisation (cold: +40-50 % HPWL)
  or does not show up in Vivado's timing (warm). No-op re-checked on this binary: rv_soc s1-3 frames IDENTICAL.
- 21:40 STOP. Result in docs/dreamplace-eval.md (regenerate: python3 flow/dpf_mkdoc.py). Seeds 1-2 Vivado-timed for
  all four DREAMPlace variants, 3 seeds for ours. Seed 3 of the DREAMPlace variants (12 runs) is exported but not
  timed: after 19:45 the alternation on slot 2 gave about one run per 25 min, and slot 1 was held by other queues.
  My runner was stopped while idle (no lock held). No processes of mine are left.
  Recommendation: drop as a placer, no port. Keep the GP-exchange draft as an oracle; next lever = a packing-aware
  (DL-style) 7-series legaliser in nextpnr.
