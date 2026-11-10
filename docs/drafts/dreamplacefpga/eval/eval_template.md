# DREAMPlaceFPGA as an external global placer: evaluation (2026-11-08)

Question: how much would a state-of-the-art open FPGA placer gain on our designs, judged by Vivado's timer?
Recommendation of docs/wip/placement-global.md: try DREAMPlaceFPGA as an external oracle before any port.

## Short answer
@@RESULT@@

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
@@TABLE@@

@@ANALYSIS@@

## Recommendation
@@RECO@@
