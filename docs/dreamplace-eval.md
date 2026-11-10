# DREAMPlaceFPGA as an external global placer: evaluation (2026-11-08)

Question: how much would a state-of-the-art open FPGA placer gain on our designs, judged by Vivado's timer?
Recommendation of docs/wip/placement-global.md: try DREAMPlaceFPGA as an external oracle before any port.

## Short answer
**On our designs, DREAMPlaceFPGA gains nothing measurable, judged by Vivado's timer.**
- All numbers below come from Vivado routing and timing the exact nextpnr implementation.
- They are the mean of seeds 1-2. Both sides use the same seeds; seed 3 of the DREAMPlace variants could not get a
  Vivado slot, see Status.

| design | ours (pl14_off_stub) | cold | warm | timing-driven cold | timing-driven warm |
|---|---|---|---|---|---|
| rv_soc | 102.37 | 95.53 (-6.7 %) | 99.59 (-2.7 %) | 92.20 (-9.9 %) | 100.28 (-2.0 %) |
| bram | 142.51 | 122.89 (-13.8 %) | 127.33 (-10.7 %) | 121.37 (-14.8 %) | 130.97 (-8.1 %) |
| rv_big | 87.33 | 84.34 (-3.4 %) | 88.97 (+1.9 %) | 81.59 (-6.6 %) | 88.04 (+0.8 %) |

- **Every cold import is worse:** -3 to -15 %. "Cold" means nextpnr legalises DREAMPlace's global placement directly.
- **Warm import is within the seed spread on the CPUs** (-2.7 % to +1.9 %) **and clearly worse on bram** (-8 to
  -11 %). "Warm" means nextpnr's own spreading starts from DREAMPlace's global placement.
- **Timing-driven mode** (FCCM'24, with our 7-series delay table) is no better than wirelength-driven.
- **Vivado placing the same netlist itself** reaches rv_soc 136.02 (148.81 MHz excluding ICAP), bram 164.07 and
  rv_big 110.89 MHz. None of the variants closes any of that gap.
- **What DREAMPlaceFPGA does show:**
  - Its global placement has 21-30 % less wirelength than ours on the two CPUs.
  - It has Vivado's flat shape (rv_soc sd_y 5.0, Vivado 5.5, ours 16.4).
  - That does not survive nextpnr's 7-series legalisation. DREAMPlaceFPGA's own legaliser cannot do 7-series.

**Recommendation: drop it as a placer. Do not port it.** Keep the GP-exchange draft as a research oracle. The lever it
points at is a packing-aware legaliser in nextpnr. Details under Recommendation.

**Status:**
- Seed 3 of the four DREAMPlace variants (12 Vivado runs) was not timed. Their exact sources are exported in
  C:\Users\finnf\open-dfx-xc7-vivado\designs\exact\.
- To finish:
  1. Run `setsid nohup flow/dpf_vivado.sh --run <names>`. The names are line 1 of build/dpf/logs/viv_q3.log; finished
     ones are skipped.
  2. Then run `python3 flow/dpf_mkdoc.py`.

## What was run
- **Placer:** DREAMPlaceFPGA, official repo github.com/rachelselinar/DREAMPlaceFPGA, commit 00449431
  (2025-04-30), BSD-3. Built in toolchain/dreamplacefpga (gitignored), **CPU only**:
  - The laptop GPU (RTX 5060, sm_120) needs CUDA >= 12.8, and upstream supports CUDA < 12 and PyTorch < 2.0 only.
  - The designs have 2-4k cells, so the CPU is enough: 70-130 s per global placement on 4 threads.
- **Environment:** conda-forge only. micromamba from conda-forge; python 3.8, pytorch 1.8.0 cpu, gxx 9, boost 1.85,
  cmake 3.29. Scripts: docs/drafts/dreamplacefpga/{env_create.sh,build.sh}.
  Sharded repodata failed with TLS resets, so flat repodata is used (`use_sharded_repodata: false`).
- **Local fixes to DREAMPlaceFPGA** (docs/drafts/dreamplacefpga/dreamplacefpga-local.patch):
  1. Upstream ships no CMakeLists for `ops/timing`, so `timer_cpp` is never built. BasicPlace imports it, so every run
     fails at import.
  2. `create_loc2site_map` is UltraScale-only and raises IndexError on any other site map. It is now wrapped; it is
     used only by the Interchange/Tcl writers.
  3. Timing graph levelisation: `max_level` can be below a vertex's level, giving KeyError. It is now raised to the
     real maximum.
  - Self-test: ISPD'16 FPGA-example1 global placement converges on the CPU (overflow < 0.1 at iteration 1522).
- **No 7-series architecture exists** in DREAMPlaceFPGA. It has ISPD'16 simplified UltraScale (Bookshelf) and
  UltraScale+ (Interchange) only.
  - Its packer-legaliser hard-codes the UltraScale CLB: `SLICE_CAPACITY = 16`, CARRY8, 2 CK/SR and 4 CE per CLB.
  - It has no carry chains, LUTRAM, SRL or F7/F8 muxes at all. The ISPD'16 benchmarks contain none.
  - So its legaliser and detailed placer cannot produce a legal Artix-7 placement. Only its **global placement** is
    evaluated here. nextpnr legalises, refines and routes.

## Bridge (all in the repo)
- **nextpnr draft** docs/drafts/nextpnr-placer-gp-exchange.patch (worktree build/src/nextpnr-dpf = nextpnr-place state
  of 2026-11-08 13:24 plus this change; build build/nextpnr-build/dpf):
  - `--placer-static-gp-dump FILE`: the static placer's own problem in its placer grid (45 x 154 on xc7a50t): per-group
    bel areas, every placer cell / macro chunk with nextpnr's area, and nets with port, type and netlist cell per pin.
    Global-clock and constant nets are excluded, as in nextpnr's GP.
  - `--placer-static-gp-import FILE` ("cold"): take the cell positions instead of the Nesterov spreading. Then run
    nextpnr's usual strict legalisation (block RAMs first, then logic) and placer1 refinement. Macro chunks are
    re-assembled around the mean anchor of their imported positions.
  - `--placer-static-gp-import-warm` ("warm"): start nextpnr's own spreading from the imported positions.
  - No-op: without the options, the dpf binary gives `.frames` identical to pl14_off_stub on rv_soc seeds 1-3.
- **flow/dpf_bridge.py**: dump -> ISPD'16 Bookshelf, and DREAMPlace .gp.pl -> import file. Artix-7 model:
  - One Bookshelf SLICE site (16 LUT / 16 FF) per CLB tile: 2 slices x 4 LUT6 x 8 FF, which is the ISPD SLICE's
    capacity.
  - BRAM/DSP columns at their x position.
  - DREAMPlaceFPGA assumes UltraScale-like full-height columns: its region boxes are whole columns, RAM sites sit every
    5 rows and DSP every 2.5. So each column gets its bel type over the full height. nextpnr legalises onto the real
    bels.
  - One node per packed netlist cell:
    - LUT<k> with I0..I5/O; LUTRAM as LUT6;
    - FDRE with D/Q/C/CE/R, so DREAMPlace's control-set area adjustment sees them;
    - CARRY4 as LUT6, F7/F8 mux as LUT3;
    - members of a nextpnr macro chunk chained by 2-pin nets.
- **flow/dpf_bench.py** runs dump -> DREAMPlace -> import -> nextpnr (through ofx/npwait.sh, OFX_MAX_NEXTPNR=3)
  -> `--xprep` (flow/exact_src.py). Vivado: flow/rte_dump_vivado.sh, slot 1, results in
  C:\Users\finnf\open-dfx-xc7-vivado\build\exact.
- **flow/dpf_summary.py** builds the table below.
- **Timing:** the exact import (flow/exact_src.py). Vivado imposes the whole nextpnr implementation's placement
  (LUTRAM sub-cells, nextpnr-made cells and LUT pins included) and only routes. The older "placed" mode is optimistic.

### Pitfalls found on the way (they cost most of the first hours)
- DSP site past the top of the grid: heap corruption in the Bookshelf parser. Fixed in the export.
- Partial columns: DREAMPlace computes filler area from full columns, so fillers exceed the real capacity and LUT
  overflow can never reach the target. Fixed by the regular-column model.
- **Nodes with identical connectivity stay stacked.** First version: a cell of area A became round(A/0.125) LUT nodes
  on one star net. They get identical gradients forever: LUT overflow stuck at 0.35, HPWL diverged (-INF). Each
  netlist cell is now its own node, which fixed it.
- DREAMPlaceFPGA ignores `target_density`: the per-region targets are hard-coded in PlaceDB.py.
- With `deterministic_flag=1` its result does not depend on `random_seed`. Seeds 1-3 below therefore share one
  DREAMPlace GP per design, and differ only in nextpnr's legalisation and refinement.

## Results
Vivado columns: Vivado timer, exact import, Vivado routes, 5 ns constraint, Fmax = 1000 / (5 - WNS). The mean is over the seeds present. nextpnr column: nextpnr timer. HPWL/wires: nextpnr. `python3 flow/dpf_summary.py --variants pl14_off_stub pl_dpf_wl pl_dpf_warm pl_dpf_td pl_dpf_td_warm` regenerates it.

| design | placer | Vivado Fmax per seed (Vivado timer, exact import) | mean | mean excl. ICAP | nextpnr Fmax mean (nextpnr timer) | HPWL after legalisation (nextpnr metric) | routed wires | GP s (DREAMPlace, CPU) | nextpnr s |
|---|---|---|---|---|---|---|---|---|---|
| rv_soc | pl14_off_stub | 101.39 / 103.35 / 100.22 | 101.65 | 101.65 | 135.37 | 17363 | 43257 | - | 42 |
| rv_soc | pl_dpf_wl | 99.36 / 91.69 / - | 95.53 | 95.53 | 132.61 | 24322 | 45839 | 106 | 15 |
| rv_soc | pl_dpf_warm | 100.67 / 98.50 / - | 99.59 | 99.59 | 136.58 | 17707 | 43472 | 106 | 20 |
| rv_soc | pl_dpf_td | 89.91 / 94.49 / - | 92.20 | 92.20 | 130.62 | 25017 | 45695 | 103 | 16 |
| rv_soc | pl_dpf_td_warm | 103.43 / 97.13 / - | 100.28 | 100.28 | 136.05 | 18486 | 43346 | 103 | 23 |
| rv_soc | Vivado places the same netlist (vref, 1 run) | 136.02 | 136.02 | 148.81 | - | - | - | - | - |
| bram | pl14_off_stub | 139.12 / 145.90 / 144.36 | 143.13 | 143.13 | 149.45 | 22485 | 46462 | - | 27 |
| bram | pl_dpf_wl | 123.35 / 122.44 / - | 122.89 | 122.89 | 125.22 | 52918 | 51361 | 73 | 17 |
| bram | pl_dpf_warm | 126.47 / 128.19 / - | 127.33 | 127.33 | 136.80 | 40045 | 49632 | 73 | 25 |
| bram | pl_dpf_td | 120.12 / 122.62 / - | 121.37 | 121.37 | 130.21 | 52851 | 51292 | 81 | 19 |
| bram | pl_dpf_td_warm | 129.80 / 132.14 / - | 130.97 | 130.97 | 137.56 | 39975 | 49823 | 81 | 23 |
| bram | Vivado places the same netlist (vref, 1 run) | 164.07 | 164.07 | 164.07 | - | - | - | - | - |
| rv_big | pl14_off_stub | 88.75 / 85.91 / 90.88 | 88.51 | 88.51 | 103.64 | 25539 | 72899 | - | 33 |
| rv_big | pl_dpf_wl | 83.75 / 84.93 / - | 84.34 | 84.34 | 101.66 | 36869 | 75395 | 126 | 20 |
| rv_big | pl_dpf_warm | 85.11 / 92.84 / - | 88.97 | 88.97 | 101.41 | 29219 | 74321 | 126 | 25 |
| rv_big | pl_dpf_td | 82.91 / 80.26 / - | 81.59 | 81.59 | 100.38 | 38001 | 75492 | 145 | 20 |
| rv_big | pl_dpf_td_warm | 84.43 / 91.65 / - | 88.04 | 88.04 | 102.75 | 29433 | 73025 | 145 | 27 |
| rv_big | Vivado places the same netlist (vref, 1 run) | 110.89 | 110.89 | 110.89 | - | - | - | - | - |

Variants, all through nextpnr's legaliser, placer1 refinement and router, on the stub chipdb:
- `pl14_off_stub`: our static placer, the default options, with the same packer, legaliser and router.
- `pl_dpf_wl` ("cold"): DREAMPlaceFPGA wirelength- and routability-driven GP with the ISPD'16 defaults, then
  nextpnr legalises it directly.
- `pl_dpf_warm`: the same GP as the start of nextpnr's own spreading.
- `pl_dpf_td`, `pl_dpf_td_warm`: DREAMPlaceFPGA's timing-driven GP (FCCM'24), with a 7-series delay model:
  - net delay: our static-delay fit, 786 + 63/29 ps per row and 37/7 ps per column;
  - logic delays approximate: LUT 124, FF 456, RAMB36 2454 ps;
  - constraint 5000 ps.

### Global placement alone, one metric
flow/dpf_gpcmp.py measures HPWL on the gp-dump nets in placer grid units. "Ours" is nextpnr's static GP just before
logic legalisation (`--placer-static-gp-out`), seed 1. Neither side is legal at that point.

| design | ours: HPWL / sd_x / sd_y | DREAMPlaceFPGA wl: HPWL / sd_x / sd_y | DREAMPlaceFPGA td: HPWL |
|---|---|---|---|
| rv_soc | 11829 / 3.2 / 16.4 | 8261 / 5.8 / 5.0 (-30 %) | 8726 |
| bram | 15470 / 9.1 / 14.2 | 40343 / 7.9 / 26.8 (+161 %) | 40340 |
| rv_big | 15370 / 5.6 / 10.4 | 12188 / 6.4 / 5.8 (-21 %) | 13198 |

- **On the two CPUs, DREAMPlaceFPGA's GP is clearly better in wirelength.**
  - It also has the flat, compact shape of Vivado's placement: sd_y 5.0 on rv_soc, against Vivado's 5.5 and our 16.4
    (Finding 13 / place_diag).
  - With nextpnr's x weight of 2 the gain shrinks to -14 % and -4 %.
  - Part of the gain is density: DREAMPlace stops at overflow 0.1 at target density 1.0, while our GP spreads to
    0.7.
- **bram is the opposite.** DREAMPlace's RAM handling spreads the 24 RAMB36 over Y2..Y29 of three columns, and the
  logic follows. Ours packs them into Y8..Y22 of two columns.
  - The RAMs are legalised mid-GP by its DSP/RAM legaliser while their overflow is still high.
  - On UltraScale ISPD designs this is probably harmless. Here it costs 2.6x the wirelength.

### Why the CPU wirelength gain does not turn into Fmax
- **Cold import:** nextpnr's strict legalisation adds +40-50 % HPWL to the dense DREAMPlace GP (rv_soc 16889 ->
  24323 in nextpnr's metric). On our own GP it adds +17 % (rv_soc s1, 15301 -> 17946).
  - nextpnr has to pack 7-series slices: carry chains in one column, one CE/SR per slice, LUT/FF pairing, LUTRAM in
    SLICEM. It does that out of a solution that ignores all of them.
  - DREAMPlaceFPGA's own packer-legaliser is built for exactly this step, but it models the UltraScale CLB and has no carry or
    LUTRAM support.
- **Warm import:** nextpnr re-spreads to its own density, so the result looks like our own placement.
  - HPWL is within 2 % on rv_soc and +14 % on rv_big.
  - Vivado-timed Fmax is within the seed spread on the CPUs (see the table).
- **Timing-driven GP:** gives nothing measurable on top. Its delay model is ours, so it cannot know more than our
  placer's timing term does.

### Runtime
- DREAMPlaceFPGA's GP takes 73-145 s on 4 CPU threads, plus about 1 s for the bridge.
- nextpnr's whole static placement takes a few seconds; its total pnr time is 15-42 s including routing.
- On these 2-4k-cell designs an external GPU/CPU placer costs runtime instead of saving it. Its speed advantage is
  for 100k+ cell designs.

## Recommendation
- **Adopt as an external option: no.**
  - It is not better on Vivado's timer.
  - It costs 70-145 s of CPU per placement against a few seconds for our global placer.
  - It drags a PyTorch-1.8 / Python-3.8 / CUDA<12 stack (no GPU support for current cards) into the toolchain.
  - It still needs nextpnr to legalise.
- **Port DREAMPlaceFPGA: no.**
  - Our placer_static.cc is already the same family: ePlace/elfPlace-style electrostatics with Nesterov.
  - The parts that would matter for 7-series are its packer-legaliser and detailed placer. Those would have to be
    rewritten anyway: slice = 4 LUT6 + 8 FF, one CE/SR per slice, CARRY4 columns, LUTRAM/SRL in SLICEM, F7/F8.
  - That is about 3-5 weeks for a 7-series DL (direct legalisation) in DREAMPlaceFPGA's C++/CUDA, before any
    evidence that it beats nextpnr's.
- **Drop it as a placer, keep the bridge as a measurement tool** (docs/drafts/nextpnr-placer-gp-exchange.patch,
  flow/dpf_*.py). It is opt-in and no-op when off: `.frames` identical on rv_soc seeds 1-3.
  - `--placer-static-gp-dump` / `--placer-static-gp-import[-warm]` / `--placer-static-gp-out` let any external
    global placer be tried against nextpnr's legaliser in under a day.
  - flow/dpf_gpcmp.py compares global placements in one metric.
- **What this says about our own placer:**
  1. **The global placement is not the main loss on the CPUs, the legalisation/packing step is.**
     - A GP with 21-30 % less wirelength and Vivado's flat shape gives no Fmax after nextpnr's strict legaliser.
     - The cold import loses 40-50 % HPWL in legalisation, against +17 % for our own GP (rv_soc s1).
     - Next lever: a packing-aware legaliser, elfPlace/DREAMPlaceFPGA-style direct legalisation (DL) for 7-series
       slices. It would cluster LUT/FF/carry by GP position and control set before site assignment, instead of
       nextpnr's greedy cell-by-cell strict legalisation. Effort about 2-3 weeks in xilinx_place.cc / placer_static.cc.
     - This fits Finding 15's packing work (dp4, carry-di-bypass).
  2. **Do not let block RAMs spread vertically.** bram shows what scattered RAMs cost (-11 %).
     Our `static-ram-assign` draft goes the other way and is the right direction.
  3. **The flat shape alone does not explain the Vivado gap.** rv_soc warm and td_warm have Vivado-like shape in GP,
     but the final Fmax stays about 100 MHz against Vivado's 136/149. This agrees with Finding 15/17: the remaining
     gap is in the detailed packing/legalisation and the delay model, not the global shape.
- **Effort spent:** about 1 working day, including the environment, two upstream fixes, the bridge, 45 nextpnr runs
  and 36 Vivado runs.
  - About half of the Vivado time was waiting for slots: other queues held slot 1 back to back, and the coordinator's
    priority windows applied.
