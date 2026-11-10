# WIP: VPR as placement engine (2026-11-08)

Goal: does VPR's timing-driven annealer (F4PGA's xc7 placer) place our netlists closer to Vivado than nextpnr's
static placer? Result goes to docs/vpr-eval.md.

## Setup (done)
- VTR `verilog-to-routing/vtr-verilog-to-routing` @ 25e723a24 (v8.0.0-5699, the `vtr-optimized` version F4PGA's
  f4pga-examples xc7/environment.yml pins). Clone toolchain/vtr/vtr-verilog-to-routing (blob:none), build
  `make -j2 vpr` with toolchain/buildenv (gcc 14.4, cmake `-DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DWITH_ABC=OFF
  -DVPR_USE_EZGL=off -DWITH_ODIN=OFF`, `CPATH=$BUILDENV_PREFIX/include` for zlib.h). Not committed (external).
- F4PGA arch packages from F4PGA's official GCS bucket (f4pga-examples docs/getting.rst, timestamp 20220920-124259,
  hash 007d1c1): symbiflow-arch-defs-install-xc7 (techmaps) and -xc7a50t_test (arch.timing.xml, 2.75 GB rr graph,
  lookahead, place delay, grid map, pinmaps). sha256 install-xc7 8d8ba213...; toolchain/vtr/dl. VPR warns the arch
  was made for VPR c012f19d3 (F4PGA's own build); it loads and runs.
- chipsalliance/f4pga @ 0723f9ca (fix_xc7_carry.py, the xc7 VPR option set), chipsalliance/f4pga-examples (pins).

## Flow
flow/vpr_export.py (our yosys JSON -> F4PGA techmaps only, no re-synthesis -> eblif), flow/vpr_run.sh (pack once,
place per seed, I/O fixed by flow/vpr_ioplace.py), flow/vpr_import.py (VPR clusters -> sites via vpr_grid_map.csv,
pb path -> bel), flow/vpr_bench.py (nextpnr rte-run binary `-o place-import`, then place_bench.xprep), flow/vpr_vivado.sh
(Vivado slot 1, build_xtime.tcl placed mode, dumps).

Caveats known so far:
- No DSP48E1 / ICAPE2 model in F4PGA's xc7 arch: dropped from VPR's copy (rv_big 4 DSPs, rv_soc ICAPE2); nextpnr
  places them and the logic that only fed them.
- F4PGA's carry fixup adds LUTs when a CARRY4 bit uses both O and CO (VPR-only cells, not imported).
- Distributed RAM (RAM32M), I/O, BUFG are left to nextpnr.
- rv_soc first pack: 339 SLICEL + 14 SLICEM clusters (nextpnr base 492 slices, Vivado 398).

## Status (16:55): DONE, docs/vpr-eval.md final (default + inner_num 5, exact)

## Status (16:05)
- Done: docs/vpr-eval.md with exact Vivado numbers for default VPR (vpr_imp): rv_soc 104.80 vs base 101.65,
  bram 134.66 vs 143.13, rv_big 87.43 vs 88.51 MHz. Recommendation: drop.
- Running: `--inner_num 5` variant (vpr_imp_hi), exact Vivado queue build/vpr/viv_exact_hi.log (runner
  rte_dump_vivado.sh, slot 1). Add its row to vpr-eval.md when it lands.
- Ignore build/place_xtime-style placed-mode results from flow/vpr_vivado.sh (runner 1220349, optimistic mode).

## Status (15:00)
- VPR packs + places all 3 designs x 3 seeds (default F4PGA options: inner_num 0.5, anneal 3-9 s; `hi` tag:
  `--inner_num 5`, 27-78 s). Every VPR run loads the 2.75 GB rr graph (~17 s, 3.4 GB RSS).
- Pure VPR HPWL on the cells it places, against the base's positions of the same cells (same nets, tile grid):
  rv_soc +5..+17 %, bram -14..+20 %, rv_big +26..+34 % (worse, except bram s2).
- nextpnr import is lossy: nextpnr's LUT->FF / carry clusters and bel rules differ from VPR's packing; only ~47-49 %
  of VPR's cells end on VPR's bel (cluster not placeable ~180-240, members moved ~300-600), ~1100-1700 cells left to
  nextpnr's static placer. HPWL of the hybrid: rv_soc 25.2k vs base 17.6k, rv_big 37.6k vs 25.5k, bram 24.1k vs 24.0k.
  An in-slice re-pick to nextpnr's conventions (flow/vpr_import.py nextpnr_conventions) moved it 47 -> 49 % only.
- Measurement switched to flow/exact_src.py (coordinator, 4f4c0f9): base exact (Vivado timer) rv_soc 101.65,
  bram 143.13 (placed mode had 112.56 / 155.87).
- Running: Vivado exact of the hybrid (vpr_imp, 9 runs); Vivado placed mode of VPR's raw placement without nextpnr
  (flow/vpr_xsrc.py, default + hi, 18 runs) to compare with the base's placed-mode numbers.
