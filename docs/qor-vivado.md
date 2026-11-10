# openXC7 vs Vivado: QoR benchmark, timer honesty, and what was closed (xc7a35tcsg324-1)

Date: 2026-11-05. No hardware was used. Every number comes from a run whose log is named next to it. "nextpnr" numbers are nextpnr's own timer, "Vivado" numbers are Vivado 2025.2's signoff timer; the two are never mixed in one cell without saying so.

## Setup
- Harness: `flow/qor_bench.py` (CONFIG block, DRY_RUN default, `--run` to build). Per design and clock period it writes `build/qor/src/<design>_p<ns>/` (RTL copy, `constraints.xdc` with the period substituted, `top.txt`). yosys results are cached by a hash of binary, script and RTL in `build/qor/synth/<design>/<key>/` (`meta.json`, `yosys.log`, `stat.txt`); nextpnr runs go to `build/qor/oxc7/<variant>/<design>_p<ns>/s<seed>/` (`status.json` with the command, key, seconds and parsed result; `nextpnr.log`, `report.json`, fasm/frames/bit). A run is reused only if its key (binary, size, arguments, synth key) matches.
- Vivado side: `vivado/run_qor.ps1 -Run` (refuses to start if a `vivado` process exists) runs the unchanged `vivado/build_gap.tcl` flow (synth, opt, place, route, bitstream; default directives) on `build/qor/src/*`. Outputs: `C:\Users\finnf\open-dfx-xc7-vivado\build\qor\<design>_p<ns>\` (times.txt, util.rpt, timing.rpt, worst_paths.txt), log `...\build\qor\vivado_20261105_221301.log`.
- Report: `python3 flow/qor_bench.py --report --variants <v...> [--doc-tag T]` builds the table (`build/qor/table_<variants>.md`) from the cache only.
- Designs (only RTL in the repo or written here):
  - blinky (`designs/gap/qor_blinky`), rv_soc and rv_mul (`designs/gap/qor_rv_soc`, `qor_rv_mul`, as in docs/gap-vivado.md; both contain an ICAPE2).
  - rv_big (`designs/qor/qor_rv_big`, new): rv_mul (FAST_MUL + DIV) with 64 KB RAM (16 RAMB36) and the ICAPE2 replaced by a register, so it has no ICAP paths.
  - fir (`designs/qor/qor_fir`, new): 32-tap systolic FIR, 16x16 multiplies, run-time loadable coefficients, 32 DSP48E1.
  - bram (`designs/qor/qor_bram`, new): one 16K x 32 memory plus 8 chained 1K x 36 banks with 36-bit three-operand adders between them (24 RAMB36).
- Periods 10, 7, 5 ns. nextpnr always gets `--freq 1000/period` and `--timing-allow-fail` (the flag only changes the exit code and the log level of the final check: common/kernel/timing_log.cc).
- Tool versions: as in docs/gap-vivado.md (Yosys 0.70+186, nightly nextpnr ce3f7c18, prjxray-db a8b09269, Vivado v2025.2). Variant binaries are listed under "nextpnr builds" below.
- Machine shared with two other agents (one Vivado, one nextpnr) for the whole session. **Runtimes are indicative only.** openXC7 runtime = yosys + nextpnr + fasm2frames + xc7frames2bit; Vivado runtime = synth + opt + place + route + write_bitstream from times.txt.

## Finding 1: nextpnr's timer did not see BRAM36, DSP or ICAP paths (fixed, opt-in)
Read from the code (build/src/nextpnr-stock):
- himbaechel/arch.cc `get_port_timing_class_default`: a cell with `timing_index == -1` is TMG_IGNORE. The chipdb generator (`himbaechel/uarch/xilinx/gen/xilinx_gen.py`) makes cell timing only for SLICE_LUTX, SLICE_FFX, SELMUX2_1, CARRY4 and the RAMB18E1/RAMB36E1 variants. **DSP48E1 and ICAPE2 have none**, so no path into or out of a DSP or the ICAP was timed.
- The RAMB36E1 variants name the read-data clock-to-out, the address and the data-in setup arcs against `CLKARDCLK`/`CLKBWRCLK`, but a packed RAMB36E1 cell only has `CLKARDCLKL/U` and `CLKBWRCLKL/U` (checked in build/qor/oxc7/base/bram_p10/s1/qor_bram_routed.json). `TimingAnalyser::get_cell_delays` (common/kernel/timing.cc:128) skips an arc whose clock port the cell lacks. **So every RAMB36 read path and address/data setup was untimed too**; only WE/EN/RST setups were checked. RAMB18E1 is not affected (its ports have no L/U suffix).
- Timing data exists: prjxray-db `artix7/timings/DSP_L.sdf` (168 conditional CELLTYPEs) and `CFG_CENTER_MID.sdf` (ICAP: setup RDWRB 5.587::6.427, CSIB 3.390::3.900, I 2.237::2.574, CLK->O 3.616::5.200 ns). Vivado's own report uses the same ICAP number: `Setup_icape2_CLK_RDWRB -6.427` (C:\Users\finnf\open-dfx-xc7-vivado\build\qor\rv_soc_p5\timing.rpt).
- Fix: docs/drafts/nextpnr-hardblock-timing.patch (`-o hardblock-timing`, **off by default**). `gen/hardblock_timing.py` turns the two SDF files into `hardblock_timing.inc` (718 arcs). `hardblock_timing.cc` overrides `getCellDelay` / `getPortTimingClass` / `getPortClockingInfo`: a DSP48E1 gets the union of all SDF rows whose parameter condition it meets (AREG, MREG, PREG, USE_MULT, A_INPUT, ... with UG479 defaults), ICAPE2 gets its arcs, and a RAMB36 arc whose clock is missing is moved to the L half (U for a port ending in U). The chipdb is not changed.
- Reproducibility: without the option the patched binary gives FASM identical (version line excluded) to the nightly on bram_p10 and rv_soc_p10 (build/qor/oxc7/qor_noopt vs base).
- Effect on nextpnr's own Fmax at 10 ns (build/qor/oxc7/{base,tmg}/<d>_p10/s1/nextpnr.log). This is the timer becoming honest, not the design getting slower:

| design | nextpnr before (blind) | nextpnr with hardblock-timing | path that appears |
|---|---|---|---|
| rv_soc | 140.90 | 134.07 | FF -> u_icap.RDWRB, setup 6.43 ns |
| rv_mul | 149.43 | 90.57 | FF -> DSP A->PCOUT (4.03) -> PCIN->P (1.52) -> carry chain -> FF |
| rv_big | 112.85 | 93.06 | same DSP path |
| bram | 238.78 | 112.11 | RAMB36 DOBDO (clk->q 2.45) -> 2.94 ns route -> adder -> FF |
| blinky | 372.58 | 372.58 | unchanged (no hard blocks) |

- On rv_soc the honest nextpnr number (134.07, ICAP-limited) now matches Vivado's overall Fmax on the same RTL (134.72 at 10 ns, 135.83 at 5 ns). The 159.26 in docs/gap-vivado.md was nextpnr not timing the ICAP; the 140.90 here differs from 159.26 only by the source path baked into yosys cell names (see Finding 4).

## Finding 2: why nextpnr gives the same Fmax at 5 ns as at 10 ns
From the code, not inferred:
- common/kernel/timing.cc:664 "all required times are normalised": endpoints get required time 0, and `compute_slack` gives setup_slack = -(arrival - required), i.e. minus the path delay, with no period in it.
- `compute_criticality` (timing.cc:832): crit = 1 - (slack - worst)/(-worst) = path delay / worst path delay. Criticality is relative to the worst path, so it is identical for any period.
- The heap placer, `timing_opt` and router2's net ordering and cost all use this criticality. The period only enters the final pass/fail check, multicycle handling, and router2's `--tmg-ripup` (`arc_failed_slack`).
- Consequence, measured: for base and hardblock-timing, the FASM at 7 and 5 ns is byte-identical (version line excluded) to the one at 10 ns for blinky, rv_soc, rv_mul, rv_big and bram (20 comparisons, build/qor/oxc7/{base,tmg}/<d>_p{10,7,5}/s1). The clock constraint changes nothing but the PASS/FAIL line.
- `--tmg-ripup` is the one place the period matters, and at 5 ns every path fails, so it rips up until its 1500-iteration cap: rv_soc 1021 s for 136.54 MHz (vs 20 s, 134.07), rv_mul 613 s for 94.39, bram 48 s for 120.21, rv_big 42 s for 97.74 (build/qor/oxc7/tmg_ripup/*/s1/nextpnr.log). Not usable as an effort knob.
- What does make the constraint drive effort here is a flow-level loop: `qor_bench.py` variant key `until_met` (variant `tmg_auto`) runs seeds until the nextpnr Fmax reaches the target. Opt-in.

## Finding 3: timers on equal terms (Vivado's timer on openXC7's netlist and placement)
`flow/qor_xtime.py` writes the yosys netlist of a build as EDIF (`$scopeinfo` cells removed) twice: "free" (Vivado opt/place/route of the yosys netlist) and "placed" (nextpnr's placement imposed with `place_cell` and fixed, then Vivado place/route; nextpnr-made LUT feed-throughs and the DRAM sub-cells are left to Vivado). `vivado/build_xtime.tcl` also times nextpnr's critical start/end pair in Vivado. Outputs C:\Users\finnf\open-dfx-xc7-vivado\build\qor_xtime\<name>\, log `vivado_20261105_230036.log` and later. Source builds: build/qor/oxc7/tmg/<d>_p5/s1. All at 5 ns.

| design | Vivado, own synth (Vivado timer) | Vivado P&R of the yosys netlist (Vivado timer) | nextpnr placement, Vivado routing (Vivado timer) | nextpnr's claim for its own result (nextpnr timer) | cells placed from nextpnr |
|---|---|---|---|---|---|
| blinky | 393.86 | 350.88 | 346.50 | 372.58 | 36 (rest are nextpnr LUT1 feed-throughs) |
| rv_soc | 135.83 (171.00 excl. ICAP) | 136.02 (157.63 excl. ICAP) | 106.99 (same excl. ICAP) | 134.07 (ICAP path) | 1926 |
| rv_mul | 135.78 (172.35 excl. ICAP) | 111.27 | 80.52 | 90.57 | 2694 |
| rv_big | 178.73 | 111.07 | 92.27 | 93.06 | 2782 |
| bram | 173.73 | 170.88 | 121.64 | 112.11 | 1481 |

With the static placer (Finding 7; source builds build/qor/oxc7/fix_static/<d>_p5/s1, Vivado runs `*_fix_static_placed`, logs vivado_20261106_*.log):

| design | nextpnr placement (heap), Vivado routing + timer | nextpnr placement (static), Vivado routing + timer | nextpnr's claim (static) |
|---|---|---|---|
| blinky | 346.50 | 358.29 | 375.94 |
| rv_soc | 106.99 | 121.36 | 134.19 (ICAP path) |
| rv_mul | 80.52 | 93.15 | 104.90 |
| rv_big | 92.27 | 106.25 | 102.33 |
| bram | 121.64 | 155.09 | 150.99 |

Same start/end pair as nextpnr's critical path (path delay incl. setup; nextpnr timer vs Vivado timer):

| design, path | nextpnr | Vivado, nextpnr placement | Vivado, own placement of the same netlist |
|---|---|---|---|
| blinky counter carry chain | 2.684 | 2.770 | 2.539 |
| rv_soc FF -> ICAP RDWRB | 7.459 | 7.877 | 7.352 |
| rv_mul FF -> DSP -> carry -> FF | 11.041 | 12.316 | 8.987 |
| rv_big same | 10.746 | 10.452 | 9.003 |
| bram RAMB36 -> adder -> FF | 8.920 | 7.964 | 5.780 |

How to read this:
- "Vivado P&R of the yosys netlist" against "Vivado, own synth" isolates **synthesis**, timed by one timer: yosys costs 8 % on rv_soc (non-ICAP), 35-38 % on rv_mul/rv_big (DSP mapping, Finding 5), 2 % on bram, 11 % on blinky.
- "nextpnr placement, Vivado routing" against "Vivado P&R of the yosys netlist" isolates **placement**, again one timer and one router: 1 % (blinky), 17-32 % (the rest).
- nextpnr's claim against Vivado's timing of the same placement mixes the timer with the router (Vivado reroutes). On blinky (+7.5 %) and rv_mul (+12.5 %) nextpnr is optimistic; on bram it is pessimistic (Vivado's router does better on nextpnr's placement, 112 -> 122). On single paths nextpnr is 0.09-1.3 ns optimistic where the route is comparable.
- The cell models differ: nextpnr's artix7 stubs give LUT 0.10-0.125 ns for every pin and FF clk->Q 0.30-0.35 ns (gen/xilinx_gen.py:644-662); Vivado reports FDRE C->Q 0.456 and LUT 0.117-0.348 depending on the pin (C:\...\qor_xtime\rv_soc_p5_tmg_placed\paths.rpt). prjxray-db's slicel.sdf also has 0.124 for every LUT pin, so the per-pin difference is not in the database nextpnr has. **nextpnr's numbers in this document are therefore not a Vivado-equivalent signoff.** Fixed routing (FIXED_ROUTE from the nextpnr routes) was not done, so a timer-only comparison on identical routes is still open.

## Finding 4: seed and name noise is larger than most option effects
- rv_soc through the identical flow gives 159.26 (designs/gap) or 140.90 (build/qor) nextpnr MHz; the only difference is the directory in the yosys cell names (e.g. `$flatten\u_cpu.\genblk1.pcpi_mul.$/home/finnf/.../picorv32.v:2371$mul$774`), which changes hash order in nextpnr. yosys LUTs 1054 vs 1057.
- Seeds 1-3 with hardblock-timing at 5 ns: rv_mul 90.57 / 97.89 / 104.44, bram 112.11 / 117.90 / 124.49, rv_big 93.06 / 95.21 / 93.49, rv_soc 134.07 / 134.73 / 132.12 (build/qor/oxc7/tmg_s3).
- So single-seed differences below ~10 % mean nothing; options are judged on several designs and on best-of-N.

<!-- qor_bench:experiments:begin -->
Experiments at 5 ns, nextpnr Fmax in MHz (nextpnr timer; all but `base` with hardblock-timing), nextpnr seconds summed over seeds. Source: build/qor/oxc7/<variant>/<design>_p5/s<seed>/status.json.

| variant | what | rv_soc | rv_mul | rv_big | bram |
|---|---|---|---|---|---|
| base | nightly nextpnr, blind timer (reference only) | 140.90 (31 s) | 149.43 (35 s) | 112.85 (19 s) | 238.78 (21 s) |
| tmg | hardblock-timing (honest timer), heap placer, seed 1 | 134.07 (20 s) | 90.57 (20 s) | 93.06 (19 s) | 112.11 (13 s) |
| tmg_s3 | same, seeds 1-3 | best 134.73 / median 134.07 / worst 132.12 (54 s) | best 104.44 / median 97.89 / worst 90.57 (63 s) | best 95.21 / median 93.49 / worst 93.06 (54 s) | best 124.49 / median 117.90 / worst 112.11 (33 s) |
| fix_tmg_s8 | gapfix + hardblock-timing, seeds 1-8 | best 140.10 / median 132.06 / worst 123.84 (107 s) | best 104.44 / median 100.80 / worst 90.57 (166 s) | best 100.97 / median 96.22 / worst 93.06 (151 s) | best 124.49 / median 117.42 / worst 112.11 (98 s) |
| tmg_critexp4 | --placer-heap-critexp 4 | 137.59 (21 s) | 101.65 (21 s) | 98.48 (17 s) | 100.52 (12 s) |
| fix_tmg_ce4_s8 | --placer-heap-critexp 4, seeds 1-8 | best 137.59 / median 135.76 / worst 130.11 (118 s) | best 101.65 / median 95.63 / worst 89.02 (168 s) | best 99.99 / median 98.04 / worst 92.38 (158 s) | best 123.52 / median 118.24 / worst 100.52 (107 s) |
| tmg_tw20 | --placer-heap-timingweight 20 | 126.94 (14 s) | 96.99 (22 s) | 96.46 (18 s) | 118.20 (13 s) |
| tmg_tw40 | --placer-heap-timingweight 40 | 121.33 (16 s) | 104.19 (21 s) | 93.74 (18 s) | 112.65 (12 s) |
| tmg_topt | -o timing-opt=4,30 | 134.07 (20 s) | 88.79 (18 s) | 92.54 (18 s) | 113.49 (12 s) |
| tmg_altw | --router2-alt-weights | 134.07 (20 s) | 92.11 (15 s) | 94.13 (18 s) | 117.52 (12 s) |
| tmg_slack | --router2-slack-order | 134.07 (21 s) | 92.27 (16 s) | 92.54 (18 s) | 118.92 (12 s) |
| tmg_bbbudget | --router2-bb-budget | 134.07 (13 s) | 91.79 (18 s) | 92.54 (17 s) | 111.84 (12 s) |
| tmg_ripup | --tmg-ripup | 136.54 (1021 s) | 94.39 (613 s) | 97.74 (42 s) | 120.21 (48 s) |
| tmg_parref | --parallel-refine | 134.07 (16 s) | 88.53 (17 s) | 92.64 (19 s) | 114.80 (16 s) |
| fix_tmg_ctforce | -o clock-tree=force | 130.33 (11 s) | 90.78 (17 s) | 93.62 (21 s) | 114.00 (16 s) |
| fix_tmg_dmoff | -o delay-matrix=off | 128.11 (11 s) | 96.19 (24 s) | 97.68 (17 s) | 118.02 (8 s) |
| fix_tmg_bramforce | -o bram-place=force | 134.07 (19 s) | 90.57 (17 s) | 95.70 (27 s) | 151.24 (13 s) |
| fix_heap_bf_s8 | -o bram-place=force, seeds 1-8 | best 140.10 / median 132.06 / worst 123.84 (140 s) | best 104.44 / median 100.80 / worst 90.57 (250 s) | best 99.74 / median 97.43 / worst 93.68 (253 s) | best 151.24 / median 148.08 / worst 139.53 (109 s) |
| tmg_sa | --placer sa | 134.72 (72 s) | 104.77 (124 s) | 98.42 (121 s) | 140.81 (83 s) |
| tmg_static | --placer static | 134.19 (23 s) | 104.90 (21 s) | 102.33 (20 s) | 150.99 (15 s) |
| fix_static | gapfix + hardblock-timing + --placer static | 134.19 (27 s) | 104.90 (21 s) | 102.33 (30 s) | 150.99 (19 s) |
| fix_static_bf | --placer static -o bram-place=force | 134.19 (34 s) | 104.90 (26 s) | 96.06 (35 s) | 143.78 (22 s) |
| fix_static_s8 | --placer static, seeds 1-8 | best 138.29 / median 135.29 / worst 134.19 (225 s) | best 107.08 / median 102.49 / worst 100.57 (222 s) | best 106.36 / median 104.24 / worst 102.24 (200 s) | best 155.45 / median 150.76 / worst 135.06 (154 s) |
| tmg_dff | yosys -dff | 132.63 (12 s) | 97.41 (27 s) | 91.87 (25 s) | 114.74 (14 s) |
| fix_tmg_wm5 | yosys -widemux 5 (gapfix nextpnr) | fail (ERROR: Unable to find legal placement fo) | fail (ERROR: Unable to find legal placement fo) | fail (ERROR: Unable to find legal placement fo) | 125.88 (11 s) |
| fix_tmg_noicap | ICAP setup as 2-cycle (nextpnr's non-ICAP Fmax) | 140.39 (20 s) | 96.96 (31 s) | not run | not run |
| fix_tmg_noicap_s8 | same, seeds 1-8 | best 143.62 / median 134.08 / worst 125.52 (135 s) | best 106.51 / median 97.50 / worst 91.63 (177 s) | not run | not run |
| fix_static_noicap | --placer static, ICAP 2-cycle | 145.62 (28 s) | 103.96 (34 s) | not run | not run |
| fix_static_noicap_s8 | --placer static, ICAP 2-cycle, seeds 1-8 | best 145.62 / median 141.98 / worst 140.45 (230 s) | best 107.16 / median 104.13 / worst 102.19 (262 s) | not run | not run |
<!-- qor_bench:experiments:end -->

## Finding 7: placement is the largest P&R lever; `--placer static` is clearly better
- Option screen at 5 ns (table above): with the honest timer, router options (alt weights, slack order, bb budget, timing-opt) and heap weights move results by less than the seed spread; `--tmg-ripup` is slow and small; `-o clock-tree=force` and `-o delay-matrix=off` are not better.
- `--placer static` (upstream electrostatic placer, configured in xilinx.cc `configurePlacerStatic`) is better on every design at about the same runtime: seed 1 rv_mul 104.90 vs 90.57, rv_big 102.33 vs 93.06, bram 150.99 vs 112.11, rv_soc 134.19 vs 134.07 (ICAP-bound); with ICAP as 2-cycle rv_soc 145.62 vs 140.39. Over 8 seeds its worst result is at or above the heap placer's median on rv_soc, rv_big and bram and 0.2 MHz below it on rv_mul, and its spread is smaller.
- `-o bram-place=force` (off by default because no clock delays are measured for xc7a50t) gives bram 151.24 with the heap placer, the same gain as the static placer on that design; it does little for the others (best of 8 with heap: bram 151.24, rv_big 99.74). Combined with the static placer it is worse (bram 143.78, rv_big 96.06), so the two are alternatives.
- `--placer sa` is good too (bram 140.81, rv_mul 104.77) but 4-6x slower.
- **Independent check with Vivado's timer** (Finding 3, second table): the static placements, routed and timed by Vivado, are 3-34 % faster than the heap placements (blinky 346.5 -> 358.3, rv_soc 107.0 -> 121.4, rv_mul 80.5 -> 93.2, rv_big 92.3 -> 106.3, bram 121.6 -> 155.1). So the improvement is real and not an artefact of nextpnr's timer.
- Best-of-N seeds (`seeds` in a variant) and "run seeds until the constraint is met" (`until_met`, variant `fix_static_auto`) make the clock constraint drive effort: at 10 ns every design meets with one run; at 7 and 5 ns 8 runs are made and the best kept (e.g. rv_mul 107.08, rv_big 106.36, bram 155.45, rv_soc 138.29 ICAP-bound).
- None of this is a default change: `qor_bench.py` variants select it; build_openxc7.py already passes `--nextpnr-arg`.

## Finding 5: synthesis gaps (yosys)
- rv_mul/rv_big: yosys maps picorv32's 33x33 `rd <= rs1 * rs2` to 4 DSP48E1 with AREG/BREG but MREG=0, PREG=0, and sums the partial products partly over PCIN and partly in a fabric carry chain. The critical path is FF -> A->PCOUT 4.03 ns -> PCIN->P 1.52 ns -> carry chain -> FF (build/qor/oxc7/tmg/rv_big_p5/s1/nextpnr.log). Vivado on the yosys netlist reaches only 111 MHz; Vivado on its own netlist 172-179 MHz. This is the largest single gap, and it is in yosys (`xilinx_dsp` cannot pack a register that sits after the fabric adder; no DSP register retiming).
- fir: Vivado packs the x delay line into the DSP input/cascade registers (598 FF); yosys keeps 1589 FF (1241 with `-dff`, which merges registers equal to LFSR bits).
- bram: 854 yosys LUTs vs 549-799 Vivado (three-operand 36-bit adders via maccmap), 98 vs 80 CARRY4; but Vivado on the yosys netlist still reaches 170.9 MHz, so for timing the bram gap is placement, not synthesis.
- Options (build/qor/synth/*/*/meta.json, LUT/FF counts from `stat -tech xilinx`):

| design | default LUT/FF/CARRY4 | -dff | -widemux 5 (LUT + MUXF7) | abc9.D = 0.25/0.40 x period (5 and 10 ns) |
|---|---|---|---|---|
| rv_soc | 1057 / 764 / 92 | 1027 / 735 / 86 | 1072 + 56 / 764 / 92 | 1057-1068, no change |
| rv_mul | 1397 / 1073 / 148 | 1400 / 1044 / 142 | 1345 + 56 / 1040 / 132 | 1397, no change |
| rv_big | 1448 / 1108 / 148 | 1442 / 1079 / 142 | 1397 + 56 / 1075 / 132 | 1448, no change |
| bram | 854 / 494 / 98 | 854 / 491 / 95 | 854 | 854 |
| fir | 22 / 1589 / 0 | 22 / 1241 / 0 | 22 | 20-22 |
| Vivado (5 ns) | rv_soc 991+50 mem / 771 / 63; rv_mul 1433+50 / 1065 / 123; rv_big 1504+50 / 1159 / 123; bram 799+1 / 509 / 80; fir 18+2 / 598 / 0 | | | |

- A delay target derived from the clock (`scratchpad -set abc9.D`) does not change the mapping here: abc9 maps for best delay first and its area recovery does not move these designs. `-retime` does not exist in this yosys (`synth_xilinx -h`). `-noflatten` is not comparable (stat counts differ by hierarchy) and was not pursued. `-widemux 5` needs the MUXF7 fix (G8, gapfix): with the stock nextpnr rv_soc/rv_mul/rv_big fail to place (`Unable to find legal placement ... SELMUX2_1`, build/qor/oxc7/tmg_wm5/*/s1/nextpnr.log).

## Finding 6: DFX keep-out cost (rv_pr, region SLICE_X12Y100:SLICE_X15Y149)
Re-run of the first native build (xor_a: build/patched/rv_pr_native/router/cfg_xor_linked.json and pblock.xdc, unchanged) into build/qor/dfx/ with `--sdf`; FASM identical to build/patched/rv_pr_native/router/xor_a (version line excluded).
- Placement is identical with and without keep-out (2772 cells, 0 differ): the cost is routing only. nextpnr: keep-out 141.16, no keep-out 152.09 MHz.
- Per-arc routed delay from the SDF (`flow/dfx_keepout_cost.py build/qor/dfx/keep_sdf build/qor/dfx/nokeep_sdf`, out build/qor/dfx/keep_vs_nokeep.json): arcs that cross the region are on average not slower (0.930 vs 0.943 ns, 1090 arcs); arcs near it (within 4 slices) +18 ps on average (2131 arcs). Total static pips 35325 vs 34473 (+2.5 %). So it is **not** a global detour or congestion problem.
- The loss sits in a few critical arcs that run along the region's east edge: on the critical path, `...aiger$o1299.A[4]` (slice x 17->19, y 144->125) 1.556 vs 0.888 ns and `...reintegrate$72...A[2]` 1.355 vs 0.854 ns. Without keep-out those arcs use the region's INT columns.
- Router patch (ours, on top of router-region): docs/drafts/nextpnr-router-keepout-crit.patch, `--router2-region-keep-out-crit C`. Arcs that keep-out would hold out but whose criticality is >= C in router2's first timing analysis may cross the region; decided once so the rule does not change between iterations. Without the option the binary reproduces the keep-out build exactly (rk_off FASM identical to keep).

| build | nextpnr Fmax | static pips / nets in region | exempt arcs | log |
|---|---|---|---|---|
| keep-out (current default) | 141.16 | 0 / 0 | - | build/qor/dfx/keep/nextpnr.log |
| crit >= 0.90 | 149.34 | 55 / 20 | 129 | build/qor/dfx/rk_c90/nextpnr.log |
| crit >= 0.75 | 147.91 | 176 / 63 | 509 | build/qor/dfx/rk_c75/nextpnr.log |
| crit >= 0.50 | 153.59 | 485 / 206 | 2806 | build/qor/dfx/rk_c50/nextpnr.log |
| no keep-out | 152.09 | 958 / 402 | all | build/qor/dfx/nokeep/nextpnr.log |

(single seed each; 147.91 < 149.34 is within the seed noise of Finding 4.)
- Full native flow with crit 0.90 (`flow/build_pr_native.py --variant rkcrit90 --rms xor andn add rot popc minmax --timing-allow-fail popc minmax --out build/qor/dfx/native`, log build/qor/dfx/native_rkcrit90.out): every RM routes, including rot; Fmax xor/andn/add 149.34, rot 147.95, minmax 146.31, popc 101.93 MHz (keep-out flow: 141.16 and popc 99.45). 15/15 pr_check pairs "STATIC IDENTICAL OUTSIDE REGION" (build/qor/dfx/native/rkcrit90/checks/). 55 static pips in the region in every build; they are replayed with the static routing, so each RM routes around them.
- Not done for rkcrit90: native_check.sh (region2v simulation, SAT proof, partial/byteman checks), rv_m, rv_b, rv_c, rv2. The 55 static pips make the RM's routing resources slightly smaller; a denser RM than rot could fail where keep-out would not.
- Vivado's DFX timing for the same design was not re-measured here.
- build_pr_native.py: one new variant entry `rkcrit90`; dry runs of all six designs are byte-identical before and after (md5 2844fc30...).

## Finding 8 (2026-11-06): wide multipliers, DSP pipeline registers (yosys draft, closes most of the rv_mul/rv_big synthesis gap)
What yosys did, read from build/qor/dsp/explore (`debug xilinx_dsp` on picorv32_pcpi_fast_mul alone, log m2.log):
- mul2dsp splits the 33x33 signed multiply into 2 A slices x 2 B slices; each A slice becomes a PCIN pair (`sliceB[0]` -> `sliceB_last`, `(PCIN >> 17) + M`), and the two pairs are added in fabric (12 CARRY4).
- Two DSPs got no A/B input register: `opt_dff` gives the operand's sign bit (`rs1[32]`, `rs2[32]`, reset when the operand is unsigned) its own `$sdffce`, so the upper slice's A/B bits come from two register cells and `in_dffe` (one cell only) fails.
- `rd` is after the fabric adder, so it is never PREG: FF -> A->PCOUT -> PCIN->P -> CARRY4 -> FF.
- How Vivado does it (C:\Users\finnf\open-dfx-xc7-vivado\build\qor\rv_big_p5\worst_paths.txt): input registers in the DSPs (a path ends at `rd0/B[16]`), `rd` moved back onto the DSP outputs, with registers named `*_psdsp` in the fabric for the low bits of the first DSP of each pair; the fabric adder then sits after the register.
- FIR: the x delay line (two registers per tap) stayed in fabric because the A cascade matcher only looks through one register ("TODO: Check for two levels of flops"); 1589 FF against Vivado's 598.

Change: docs/drafts/yosys-xilinx-dsp-pipeline.patch (`xilinx_dsp -pipeline`, `synth_xilinx -dsp_pipeline`; off by default): merge split input registers (moving a reset that not all bits share into D), A/B cascade through two registers (ACASCREG/BCASCREG=2), and move a reset-free, x-init register after a fabric `$add` tree of DSP P outputs back onto those outputs, packed into PREG where PCOUT is unused. Tested two ways: as a plugin of the same sources (toolchain/buildenv/build_yosys_dsp_plugin.sh, qor_bench variants `dspq_off`/`dspq`), and as a full in-tree build (toolchain/buildenv/build_yosys_full.sh, bison/flex now installed from conda-forge into toolchain/buildenv/env-bisonflex; log build/yosys-build/yosys-dspqor.build2.log): `synth_xilinx -dsp_pipeline` gives the same cell types and DSP register settings as the plugin on rv_mul, rv_big, fir, rv_soc, and without the option the same as the oss-cad-suite yosys (build/qor/dsp/yfull).
- No-op: without `-pipeline` the yosys JSON is byte-identical for fir, rv_soc, bram, blinky; on rv_mul/rv_big two `$auto$xilinx_dsp_cascade_pm.h:<line>` cell names differ (generated-header line numbers), and the `.frames` are identical to `fix_static` (build/qor/oxc7/dspq_off vs fix_static).
- Equivalence: random simulation (iverilog + yosys cells_sim.v) of the multiplier alone, off vs on: 59503 MUL/MULH/MULHSU/MULHU results compared, 0 mismatches (build/qor/dsp/sim/fm_off_vs_on.log); FIR whole design, 200000 cycles with random coefficient loads: 0 mismatches (build/qor/dsp/sim/fir/result.log). rv_big whole design 100000 cycles: 0 mismatches, but the firmware has no MUL instruction and the LEDs did not change, so this only shows the rest of the SoC is unchanged (build/qor/dsp/sim/rv_big/result.log).
- Mapping: picorv32 multiplier all 4 DSPs AREG=BREG=1, the 2 pair ends PREG=1, 34 bits in fabric registers. Cells (`stat -tech xilinx`): rv_mul LUT 1397 -> 1422, FF 1073 -> 1011; rv_big LUT 1448 -> 1463, FF 1108 -> 1046; fir FF 1589 -> 597 (Vivado 598).

| design (5 ns) | Vivado, own synth (Vivado timer) | Vivado P&R of the yosys netlist, before -> with -pipeline (Vivado timer) | nextpnr static placer seed 1, before -> after (nextpnr timer) | best of 8 seeds, before -> after (nextpnr timer) |
|---|---|---|---|---|
| rv_mul | 135.78 (172.35 excl. ICAP) | 111.27 -> 135.94 (159.01 excl. ICAP) | 104.90 -> 137.84 | 107.08 -> 140.13 (median 134.78) |
| rv_big | 178.73 | 111.07 -> 156.59 | 102.33 -> 125.69 | 106.36 -> 143.12 (median 128.07) |
| fir | 203.09 | 215.75 -> 205.68 | did not place -> 198.65 (with Finding 9) | - -> 209.69 (median 199.24) |

Sources: Vivado C:\Users\finnf\open-dfx-xc7-vivado\build\qor_xtime\<d>_p5_{tmg,dspq,dcp_static,dspq_dcp}_free (log vivado_20261106_031601.log and the next ones); nextpnr build/qor/oxc7/{fix_static,dspq,dspq_s8,dspq_dcp_s8}/<d>_p5/s*/nextpnr.log.
- rv_big's worst Vivado path on the new netlist is a RAMB36 read -> FF path (-1.386 ns at 5 ns); the multiplier's worst path (DSP -> PCIN) has -0.670 ns, i.e. about 177 MHz, against 178.73 for Vivado's own design. rv_mul with ICAP is limited by the ICAP setup like Vivado's own build (135.94 vs 135.78).
- On the FIR the pipelined netlist is slower in Vivado's P&R than the default one (205.68 vs 215.75) although it has Vivado's register count; not investigated.

## Finding 9 (2026-11-06): DSP cascade placement (nextpnr draft; the FIR places)
- Why it failed, from the code: `pack_dsp_xc7.cc` gives each cascaded DSP a fixed offset (upper DSP of the tile, then the lower DSP 5 rows up) and BaseArch places clusters by these offsets. In xc7a50t the DSP tile step is 5 rows but 6 across the HCLK and BRKH rows (prjxray-db tilegrid.json, both DSP columns: steps {5: 24, 6: 5}), and tileconn.json shows the cascade wires cross those rows. So every chain longer than 10 DSPs (one clock region) had no legal position. yosys cuts the FIR's 32-chain into 20 + 12.
- Fix: docs/drafts/nextpnr-dsp-cascade-place.patch, `-o dsp-cascade-place` (off by default), on the qorfix stack; nextpnr build `qordsp` (build/nextpnr-build/qordsp, log qordsp.build3.log; the only warning is the pre-existing xilinx.cc sign-compare). The next DSP is found along the chipdb's PCOUT0 -> PCIN0 wires, as upstream already does for RAMB36 cascades.
- No-op: option off, `.frames` identical to `qorfix` on rv_mul, rv_big, bram, rv_soc (build/qor/oxc7/dcp_noopt vs fix_static); option on, identical on blinky, rv_soc, bram (dcp_static vs fix_static) and rv_mul, rv_big (dspq_dcp vs dspq), which have no long chain.
- FIR (default yosys netlist): heap placer 234.41 MHz, static placer 209.69 MHz (nextpnr timer; build/qor/oxc7/dcp_{heap,static}/fir_p5/s1). The 20-chain sits on DSP48_X0Y0..Y19 and the 12-chain on DSP48_X1Y18..Y29, both across a clock-region boundary. Vivado accepts every DSP site (1645 cells placed, 2 not) and times that placement at 203.05 MHz (Vivado timer, `fir_p5_dcp_static_placed`); Vivado's own FIR: 203.09.

## Finding 10 (2026-11-06): delay model calibrated against Vivado (nextpnr chipdb draft)
Where the numbers come from: `gen/xilinx_gen.py` writes stub LUT (0.10-0.125 ns), FF (clk->Q 0.30-0.35, setup 0.10) values for artix7; prjxray-db's CLBLL_L.sdf has the same kind of numbers (LUT6 0.100-0.124 for every pin, FF_INIT CLK->Q 0.244-0.303, REG_INIT_FF 0.274-0.340), so the SDF is not closer to Vivado. Vivado was used as the oracle instead: vivado/build_arcs.tcl places a netlist as nextpnr did, routes it and dumps `get_timing_arcs` (slow max / fast min) of up to 400 cells per type with the physical bel pin, whether a load or driver is outside the slice, the arc SENSE, site type, exit pin and LUT pairing (C:\Users\finnf\open-dfx-xc7-vivado\build\qor_arcs3, qor_arcs4; 3 designs, 38458 arcs).
- FF: clock-to-Q median 0.456 ns (0.419-0.518); D setup -0.075 ns when D comes from the slice's own LUT and 0.215 ns through the AX..DX bypass; CE setup 0.169 ns.
- LUT: an arc is either about 0.12-0.15 ns or about 0.29-0.35 ns, and within one LUT6 typically one input is fast and the others slow. This is not explained by the physical pin, the function's unateness (SENSE), SLICEL vs SLICEM, a used 5LUT/6LUT pair, the output pin, or loads outside the slice (all checked, flow/vivado_cell_timing.py output, build/chipdb-cal/cell_timing_xc7a35t_1.txt); it probably depends on the input's routing, which nextpnr's per-pin cell arcs cannot express. The calibration therefore uses the mean: O6 0.200 ns, O5 0.228 ns (median 0.124/0.153).
- Change: docs/drafts/nextpnr-cell-timing-cal.patch, chipdb generator option `--cell-timing FILE` (LUT arcs, FF clk->Q, D/CE setup, and a `SLICE_FF_BYPASS` site-pip class of 0.290 ns on the AX..DX -> FF mux). The file is made by flow/vivado_cell_timing.py; the chipdb by `GEN_ARGS="--cell-timing ..." toolchain/buildenv/gen_chipdb.sh` (build/chipdb-cal/on, 50 s). Without the option the generated chipdb is byte-identical to the nightly's (build/chipdb-cal/off, `cmp`). Hold values are not changed (they drive hold fixing).
- Validation, on identical placements only (Vivado re-routes; the routes were not imposed): nextpnr's claim against Vivado's timer on nextpnr's placement, all 5 ns, static placer, seed 1 (nextpnr build/qor/oxc7/<variant>/<d>_p5/s1; Vivado C:\...\qor_xtime\<d>_p5_<variant>_placed, log vivado_20261106_040347.log):

| design | stub chipdb: nextpnr claim / Vivado on that placement | error | calibrated chipdb: nextpnr claim / Vivado on that placement | error |
|---|---|---|---|---|
| blinky | 375.94 / 358.29 | +4.9 % | 364.70 / 358.29 | +1.8 % |
| rv_soc | 134.19 / 121.36 | +10.6 % | 133.08 / 125.03 | +6.4 % |
| bram | 150.99 / 155.09 | -2.6 % | 142.07 / 149.88 | -5.2 % |
| rv_mul (-pipeline netlist) | 137.84 / 112.69 | +22.3 % | 132.96 / 121.82 | +9.1 % |
| rv_big (-pipeline netlist) | 125.69 / 109.09 | +15.2 % | 124.18 / 110.95 | +11.9 % |
| fir (-pipeline netlist) | 198.65 / 203.17 | -2.2 % | 214.73 / 208.03 | +3.2 % |

- Mean absolute error 9.6 % -> 6.3 %; nextpnr is still optimistic on the CPU designs. What is left was not separated further: Vivado routes the placement itself and places 500-1250 cells nextpnr made (LUT feed-throughs, LUTRAM sub-cells), and nextpnr's report gives only one critical path per clock, so a per-path cell/net split against Vivado was not possible here. A comparison on identical routes needs FIXED_ROUTE from nextpnr's pips and was not done.
- Vivado's timing of the placements made with the calibrated model (single seed, so within the noise of Finding 4): rv_soc 121.36 -> 125.03, rv_mul 112.69 -> 121.82, rv_big 109.09 -> 110.95, fir 203.17 -> 208.03, bram 155.09 -> 149.88, blinky 358.29 -> 358.29.
- The table at the end of this file (`qor_bench:dsp`) has every nextpnr run of Findings 8-10.

## Finding 11 (2026-11-06): placement algorithms against Vivado's placement (nextpnr draft; no option closes the gap)
Method: every Vivado number below is Vivado's timer on nextpnr's placement with Vivado routing (vivado/build_xtime.tcl, the Finding 3 method; "Vivado timer"); "nextpnr timer" is nextpnr's own Fmax. 3 seeds per variant, given per seed and as mean (min-max). Harness: flow/place_bench.py (CONFIG block, dry run by default; `--run`, `--xprep`, `--report`, `--noop`). nextpnr runs: build/qor/oxc7/<variant>/<design>_p<ns>/s<seed>/ (nextpnr.log, status.json). Vivado runs: C:\Users\finnf\open-dfx-xc7-vivado\build\place_xtime\<design>_p<ns>_<variant>_s<seed>_placed\ (timing.rpt, worst_paths.txt; logs vivado_*.log in the same directory). qor designs at 5 ns; the LiteX DDR3 SoC (`ddr`, netlist build/ddr3/arty_ddr3/gapfix) and the LiteEth SoC (`eth`, netlist build/eth/arty_eth/gapfix) at 100 MHz sys_clk (Vivado clock `main_crg_clkout0`). Every variant uses the static placer and `-o hardblock-timing`.

### What Vivado does differently (idea 4)
vivado/place_dump.tcl places and routes the yosys netlist itself ("free"), and also with nextpnr's placement imposed, and dumps every cell's site and the cells of the 1000 worst paths. flow/place_compare.py compares them on the prjxray tile grid (grid units; one CLB column is 2 in x). Source placement: build/qor/oxc7/fix_static/<d>_p5/s1. Outputs: C:\Users\finnf\open-dfx-xc7-vivado\build\place_dump\<d>_p5_fix_static_{free,placed}\ and build/qor/place/compare/<d>_p5_fix_static_placed.json.

| | rv_soc Vivado | rv_soc nextpnr | bram Vivado | bram nextpnr |
|---|---|---|---|---|
| slices used | 398 | 501 | 290 | 333 |
| LUTs / FFs per used slice | 3.56 / 2.42 | 3.00 / 2.02 | 3.58 / 3.15 | 3.30 / 2.78 |
| logic spread, sd of x / y (grid units) | 10.6 / 5.5 | 8.4 / 16.9 | 26.1 / 7.6 | 21.7 / 14.1 |
| own 200 worst paths: summed hop distance, mean | 29.8 | 56.6 | 13.8 | 18.4 |
| the same paths' cells in the other tool's placement | 34.1 (in nextpnr's) | 26.8 (in Vivado's) | 15.7 | 12.9 |
| own 200 worst paths: mean net delay, ns (Vivado timer) | 2.99 | 4.51 | 1.45 | 2.01 |
| RAMB36 sites | X0Y4, X1Y4 | X1Y15, X1Y16 | 3 columns (X0-X2), Y2-Y12 | 2 columns (X0-X1), Y8-Y22 |

- nextpnr's placement is less dense and tall. The cells on its own critical paths are twice as far apart as the same cells are in Vivado's placement, while Vivado's critical paths get only a little longer in nextpnr's placement (34 vs 30). So the loss is that nextpnr spreads exactly the paths it should keep tight.
- Vivado's in-placer physical synthesis did only LUT combining on rv_soc (32 LUTs; no replication, no fanout optimisation; C:\Users\finnf\open-dfx-xc7-vivado\build\place_dump\vivado_20261106_035645.log). So the rv_soc gap is placement, not netlist changes.
- The static placer legalises the block RAMs once their own overlap drops below 0.15. On rv_soc that happens at about iteration 7, while the logic overlap is still 96 % (build/qor/oxc7/pl_base/rv_soc_p5/s1/nextpnr.log, "Strict legalising 20 cells"). The logic then spreads along the fixed BRAM column.
- Spreading takes rv_soc's HPWL from about 4850 to about 15300 before legalisation; legalisation adds another 17 % (17946); the placer1 refinement then recovers 8 % of its own wirelength metric (same log).

### Changes (docs/drafts/nextpnr-placer-tuning.patch, all opt-in)
- `--tmg-crit-target F` / `--tmg-crit-floor C`: period-aware criticality, from the slack against F times the clock period; failing endpoints map to [C, 1].
- Static placer: `--placer-static-timingweight`, `--placer-static-critexp`, `--placer-static-target-util`, `--placer-static-ip-wait L` (legalise BRAM/DSP only once the logic overlap is below L), and `--placer-static-overlap-stop S` (legalise the logic at overlap S instead of 0.1).
- Refinement: `--placer1-critexp`, `--placer1-timing-tradeoff`.
- xilinx: `-o static-hpwl-x=N`, `-o static-ff-area=A`.

Binaries: build/nextpnr-build/place_ref is ofx + hardblock-timing, the baseline `pl_base`. place_v1 to place_v4 are successive versions of the draft; v4 is the patch.

Variant names:
- `ct10`: `--tmg-crit-target 1.0`
- `ipw5`: `--placer-static-ip-wait 0.5`
- `ff1`: `-o static-ff-area=1.0`
- `hx1`: `-o static-hpwl-x=1`
- `os25` / `os40`: `--placer-static-overlap-stop 0.25` / `0.4`
- `_cal`: calibrated chipdb build/chipdb-cal/on (Finding 10)
- `_dq`: yosys `-pipeline` netlist (Finding 8)

No-op (options off):
- `.frames` identical to `pl_base` for blinky, rv_soc, bram and rv_big, seeds 1-3, with v1 and with v4 (build/qor/place/run1.log, run9.log).
- DDR fasm identical, seeds 1-3 (v1).
- rv_ppa: 10/10 builds identical to the partpin2 reference with v4 (install/noop_check.py with candidate place_v4: build/qor/place/noop_rvppa/summary_rv_ppa.json).

### Results
Vivado timer and nextpnr timer per design, variant and seed (`--report` output):

| design | period | variant | nextpnr Fmax per seed (nextpnr timer) | mean (min-max) | Vivado Fmax on nextpnr placement per seed (Vivado timer) | mean (min-max) | Vivado WNS per seed |
|---|---|---|---|---|---|---|---|
| rv_soc | 5 | pl_base | 134.19 / 134.19 / 137.72 | 135.37 (134.19-137.72) | 121.36 / 117.45 / 111.62 | 116.81 (111.62-121.36) | -3.24 / -3.51 / -3.96 |
| rv_soc | 5 | pl_ct10 | 133.82 / 134.95 / 132.87 | 133.88 (132.87-134.95) | 124.95 / 117.08 / 111.20 | 117.74 (111.20-124.95) | -3.00 / -3.54 / -3.99 |
| rv_soc | 5 | pl3_ipw5 | 135.56 / 129.48 / 135.26 | 133.43 (129.48-135.56) | 124.89 / 118.54 / 115.33 | 119.59 (115.33-124.89) | -3.01 / -3.44 / -3.67 |
| rv_soc | 5 | pl3_ipw5_ff1 | 135.56 / 135.57 / 138.29 | 136.47 (135.56-138.29) | 127.53 / 117.98 / 116.33 | 120.61 (116.33-127.53) | -2.84 / -3.48 / -3.60 |
| rv_soc | 5 | pl4_os25 | 137.72 / 138.29 / 129.90 | 135.31 (129.90-138.29) | 116.65 / 118.39 / 110.50 | 115.18 (110.50-118.39) | -3.57 / -3.45 / -4.05 |
| rv_soc | 5 | pl4_os40 | 138.29 / 138.29 / 135.78 | 137.45 (135.78-138.29) | 114.27 / 120.12 / 119.26 | 117.88 (114.27-120.12) | -3.75 / -3.33 / -3.38 |
| rv_soc | 5 | pl3_off_cal | 133.08 / 133.42 / 133.51 | 133.34 (133.08-133.51) | 125.03 / 110.91 / 117.58 | 117.84 (110.91-125.03) | -3.00 / -4.02 / -3.50 |
| rv_soc | 5 | pl3_ipw5_cal | 138.54 / 131.56 / 133.32 | 134.47 (131.56-138.54) | 120.80 / 116.52 / 113.17 | 116.83 (113.17-120.80) | -3.28 / -3.58 / -3.84 |
| bram | 5 | pl_base | 150.99 / 150.53 / 146.82 | 149.45 (146.82-150.99) | 155.09 / 155.40 / 157.13 | 155.87 (155.09-157.13) | -1.45 / -1.44 / -1.36 |
| bram | 5 | pl_ct10 | 149.37 / 147.19 / 150.22 | 148.92 (147.19-150.22) | 150.60 / 147.43 / 154.27 | 150.77 (147.43-154.27) | -1.64 / -1.78 / -1.48 |
| bram | 5 | pl3_ipw5 | 145.01 / 151.42 / 140.83 | 145.75 (140.83-151.42) | 157.95 / 157.68 / 151.13 | 155.59 (151.13-157.95) | -1.33 / -1.34 / -1.62 |
| bram | 5 | pl3_ipw5_ff1 | 155.35 / 157.08 / 149.70 | 154.05 (149.70-157.08) | 155.93 / 155.96 / 153.26 | 155.05 (153.26-155.96) | -1.41 / -1.41 / -1.52 |
| bram | 5 | pl3_off_cal | 142.07 / 142.09 / 144.55 | 142.90 (142.07-144.55) | 149.88 / - / - | 149.88 | -1.67 / - / - |
| rv_big | 5 | pl_base | 102.33 / 102.24 / 106.36 | 103.64 (102.24-106.36) | 106.25 / 99.66 / 108.94 | 104.95 (99.66-108.94) | -4.41 / -5.03 / -4.18 |
| rv_big | 5 | pl_ct10 | 102.84 / 98.61 / 94.21 | 98.55 (94.21-102.84) | 97.05 / 95.76 / 98.66 | 97.16 (95.76-98.66) | -5.30 / -5.44 / -5.14 |
| ddr | 10 | pl_base | 110.89 / 105.33 / 106.28 | 107.50 (105.33-110.89) | 83.63 / 84.22 / - | 83.92 (83.63-84.22) | -1.96 / -1.87 / - |
| ddr | 10 | pl3_ipw5_hx1 | 115.31 / 112.89 / 116.58 | 114.93 (112.89-116.58) | 83.77 / - / - | 83.77 | -1.94 / - / - |
| eth | 10 | pl_base | 101.93 / 95.62 / 93.68 | 97.08 (93.68-101.93) | 65.99 / 70.03 / 69.91 | 68.64 (65.99-70.03) | -5.15 / -4.28 / -4.30 |
| eth | 10 | pl3_ipw5_hx1 | 102.23 / 87.67 / 91.17 | 93.69 (87.67-102.23) | 66.68 / 69.91 / - | 68.30 (66.68-69.91) | -5.00 / -4.30 / - |
| eth | 10 | pl3_off_cal | 82.07 / 82.47 / 91.60 | 85.38 (82.07-91.60) | 66.30 / - / - | 66.30 | -5.08 / - / - |
| eth | 10 | pl3_ipw5_hx1_cal | 82.21 / 82.07 / 87.28 | 83.85 (82.07-87.28) | 64.82 / - / - | 64.82 | -5.43 / - / - |

Screened with nextpnr's timer only (mean of 3 seeds, MHz). Base: rv_soc 135.37, bram 149.45, rv_big 103.64, ddr 107.50, eth 97.08.
- The `_dq` rows compare with `pl3_off_dq`, and the `_dqcal` rows with `pl3_off_dqcal`.
- For `_cal` the base is `pl3_off_cal` (ddr 100.94, eth 85.38).
- rv_soc is ICAP-limited in nextpnr's timer (134-138 MHz on every variant), so its column says nothing about placement.
- ct10 on the DDR SoC: 103.73 (94.93-108.41).

| variant | rv_soc | bram | rv_big | rv_mul | ddr | eth |
|---|---|---|---|---|---|---|
| pl_sw20 | 135.13 (134.19-135.63) | 150.02 (148.30-151.81) | 97.87 (92.09-105.42) | - | - | - |
| pl_r1t8 | 136.27 (135.26-138.29) | 151.59 (150.76-152.35) | 103.38 (102.57-104.08) | - | - | - |
| pl_topt | 135.37 (134.19-137.72) | 149.20 (147.45-152.35) | 103.05 (100.50-106.41) | - | - | - |
| pl3_ipw5_tu5 | 136.38 (135.56-136.80) | 151.45 (147.25-154.32) | 102.32 (101.49-102.83) | - | - | - |
| pl3_ipw5_tu9 | 134.91 (134.19-135.26) | 152.79 (149.84-154.97) | 101.37 (100.14-103.26) | - | 112.23 (110.23-113.92) | - |
| pl3_ipw5_hxff | 132.42 (129.87-135.56) | 152.18 (150.11-154.89) | 102.07 (99.77-103.36) | - | 109.68 (103.48-115.78) | 96.46 (94.15-97.90) |
| pl4_os25 | 135.31 (129.90-138.29) | 146.95 (140.35-153.28) | 103.61 (98.92-106.16) | - | 112.73 (106.32-117.23) | 94.61 (88.66-98.50) |
| pl3_off_dq | - | - | 133.09 (125.69-143.12) | 136.21 (133.14-137.84) | - | - |
| pl3_ipw5_dq | - | - | 135.71 (130.45-143.12) | 136.21 (133.14-137.84) | - | - |
| pl3_ipw5_hx1_dq | - | - | 134.42 (129.22-138.93) | 136.73 (134.79-137.72) | - | - |
| pl3_ipw5_hxff_dq | - | - | 133.84 (125.99-142.94) | 136.36 (133.42-137.93) | - | - |
| pl3_off_dqcal | - | - | 122.46 (119.43-124.18) | 130.05 (123.81-133.37) | - | - |
| pl3_ipw5_dqcal | - | - | 124.22 (119.43-129.07) | 130.05 (123.81-133.37) | - | - |
| pl3_ipw5_hx1_cal | - | - | - | - | 98.82 (96.47-100.79) | 83.85 (82.07-87.28) |

### What helped and what did not
- **Period-aware criticality (`ct10`) does not help** under Vivado's timer:
  - rv_soc 117.74 vs 116.81 (noise);
  - bram 150.77 vs 155.87 and rv_big 97.16 vs 104.95, worse on every seed;
  - DDR SoC: nextpnr's own Fmax drops too (103.73 vs 107.50).

  At 5 ns every design fails by 1-5 ns, so most paths saturate near the floor and the placer loses its focus on the worst ones. Not a default candidate.
- **BRAM-wait (`ipw5`) changes the shape as intended:** rv_soc y-sd is 7.1-7.3 instead of 10.9-18.0, close to Vivado's 5.5.
  - Stub chipdb: rv_soc +2.4 % (119.59 vs 116.81, better on all 3 seeds), +3.3 % with `ff1` (120.61).
  - Calibrated chipdb: the gain disappears (116.83 vs 117.84).
  - bram is unchanged (155.59 vs 155.87).
  - No-op on rv_mul (`-pipeline` netlist), rv_big (default netlist) and the DDR SoC: frames/fasm identical on all 3 seeds, because their RAM/DSP groups converge after the logic anyway. rv_big with the `-pipeline` netlist differs on 1 of 3 seeds. Not run alone on eth.
- **Denser stopping (`os25`/`os40`) packs like Vivado** (rv_soc 377-422 slices vs 479-513). But the legaliser then moves cells further (HPWL after legalisation 18050/17959 vs 17946), and Vivado times it no better (115.18 / 117.88 vs 116.81).
- **`hx1` raises nextpnr's own Fmax on the DDR SoC** on all 3 seeds (114.93 vs 107.50), but not Vivado's timing of it: seed 1 WNS -1.94 vs -1.96. On seed 2 Vivado could not place the remaining cells around the imposed placement ("Placer could not place all instances"). eth is unchanged (68.30 vs 68.64). With the calibrated chipdb, eth seed 1 is 64.82 (hx1) vs 66.30 (off).
- Static timing weight 20, placer1 trade-off 0.8, `-o timing-opt=3,10` and target util 0.5/0.9 stay within seed noise in nextpnr's timer. They were not taken to Vivado.
- **Why the knobs cannot close the gap, measured on eth** (pl_base s1):
  - nextpnr's critical path is the same 12-level path Vivado reports (FF -> LUTs -> LUTRAM `storage_9` ADDR -> FF).
  - nextpnr: 9.81 ns (2.08 logic, 7.74 routing; build/qor/oxc7/pl_base/eth_p10/s1/nextpnr.log).
  - Vivado on the same placement: 14.51 ns (3.27 logic, 11.24 routing; C:\Users\finnf\open-dfx-xc7-vivado\build\place_xtime\eth_p10_pl_base_s1_placed\paths.rpt).
  - So nextpnr's interconnect estimate is about 30 % below Vivado's on this path (Vivado re-routes, so the routes are not identical). The placer minimises a cost in which long hops look cheap.
  - The cell-timing calibration (Finding 10) does not cover routing delays.
  - Overall on eth, nextpnr claims 97.08 MHz (mean) where Vivado measures 68.64.
- **Static vs heap placer on the SoCs:**
  - DDR, static placer: WNS -1.96 / -1.87 (seeds 1, 2), against -1.584 for the heap placement of docs/ddr3-litedram.md.
  - eth, static placer: -5.15 / -4.28 / -4.30, against -4.730 heap (docs/ethernet-debug.md).
  - So on the two real SoCs the static placer is not better than the heap placer under Vivado's timer, unlike on the qor designs (Finding 7).

### Remaining gap (Vivado timer)
| design | best measured nextpnr placement | Vivado placing the same netlist |
|---|---|---|
| rv_soc | 120.61 MHz (best variant mean) | 157.63 MHz, excl. ICAP (Finding 3) |
| bram | 155.87 MHz | 170.88 MHz |
| DDR | WNS -1.87 to -1.96 ns | +0.418 ns |
| eth | WNS -4.28 to -5.15 ns | -0.121 ns |

## Finding 12 (2026-11-06): area against Vivado -- where the extra cells come from, and three drafts
Method:
- flow/qor_area.py counts the post-route area from nextpnr's routed JSON with Vivado's rule: a LUT6 site counts once, whether one or both of its LUTs are used. LUTs that nextpnr made (route-throughs, carry feed-throughs, duplicates) are found by comparing with the yosys netlist. Sites that hold only such LUTs are listed separately, because Vivado does not count route-throughs: on blinky Vivado reports 1 LUT for a 28-bit counter with 7 CARRY4, while nextpnr uses 28 sites, 27 of them route-throughs only.
- Vivado numbers come from util.rpt ("Slice LUTs", "using O5 and O6", the Primitives table):
  - Vivado's own build: C:\Users\finnf\open-dfx-xc7-vivado\build\qor\<d>_p5, ddr3\arty_ddr3, eth\arty_eth.
  - Vivado's P&R of the yosys netlist: qor_xtime\<d>_p5_tmg_free, ddr3_xtime\arty_ddr3_gapfix_free, eth_xtime\arty_eth_gapfix_free.
- 5 ns builds (LiteX: 100 MHz). Area at seed 1. Output: build/qor/area/area_*.{json,md} and build/qor/area/litex/<d>/<variant>/area.json.
- Correction: qor_bench's yosys LUT count left out INV cells. nextpnr turns them into LUT1s, and Vivado counts LUT1s. rv_soc has 1057 LUTs + 50 INV = 1107. So the "+7 % LUTs on rv_soc" in Finding 5 and in the summary compared 1057 yosys cells with Vivado's LUT *sites* (991 logic / 1041 total). On cells the two are equal.

Before (`area_ref`: nextpnr build `qorarea` with no new option; its `.frames` are identical to `dcp_static`/`fix_static`):

| design | Vivado own: LUT sites (LUT cells, O5+O6 sites) | Vivado P&R of the yosys netlist | nextpnr: LUT sites (O5+O6 logic pairs) + sites with only nextpnr-made LUTs; LUT bels | FF (Vivado own / yosys in Vivado / nextpnr) | CARRY4 (same order) | LUTRAM sites (own / yosys) | control sets (same order) |
|---|---|---|---|---|---|---|---|
| blinky | 1 (1, 0) | 1 (1, 0) | 1 (0) + 27; 56 | 28 / 28 / 28 | 7 / 7 / 7 | 0 / 0 | 1 / 1 / 1 |
| rv_soc | 1041 (1106, 115) | 1122 (1107, 41) | 1098 (65) + 161; 1748 | 771 / 768 / 764 | 63 / 92 / 100 | 50 / 56 | 40 / 62 / 64 |
| rv_mul | 1483 (1597, 164) | 1582 (1575, 49) | 1567 (64) + 164; 2443 | 1065 / 1077 / 1073 | 123 / 148 / 159 | 50 / 56 | 46 / 71 / 74 |
| rv_big | 1554 (1694, 190) | 1630 (1626, 52) | 1608 (74) + 164; 2494 | 1159 / 1116 / 1108 | 123 / 148 / 159 | 50 / 56 | 47 / 71 / 74 |
| bram | 800 (945, 146) | 754 (869, 116) | 733 (137) + 108; 1370 | 509 / 494 / 494 | 80 / 98 / 98 | 1 / 1 | 1 / 1 / 1 |
| fir | 20 (18, 0) | - | 25 (0) + 0; 25 | 598 / - / 1589 | 0 / - / 0 | 2 / 2 | 2 / - / 2 |
| arty_ddr3 | 4340 (5134, 936) | 4821 (5456, 955) | 5153 (620) + 433; 7368 | 3677 / 3738 / 3741 | 178 / 255 / 266 | 142 / 320 | - |
| arty_eth | 5432 (5853, 933) | 5965 (6284, 955) | 6389 (533) + 1193; 10754 | 5264 / 5352 / 5358 | 446 / 517 / 532 | 512 / 636 | - |

Where the extra cells come from:
1. **LUT cells: not the gap.** yosys and Vivado produce about the same number of LUT cells:
   - rv_soc 1107 vs 1106, rv_mul 1575 vs 1597, rv_big 1626 vs 1694, bram 869 vs 945;
   - LiteX: +6 % (arty_ddr3 5454 vs 5134) and +7 % (arty_eth 6284 vs 5853).
   abc9's LUT mapping does not lose area on these designs.
2. **LUT combining (dual-output sites).** Vivado's synthesis pairs LUTs into O6+O5 sites: 115 on rv_soc, 164 on rv_mul, 190 on rv_big, 936 on arty_ddr3, 933 on arty_eth. Given the yosys netlist, Vivado's own placer makes only 41-52 such pairs on the CPUs, and nextpnr 64-74. This is most of the LUT-site gap on the CPUs.
3. **nextpnr-made LUTs.** On rv_soc, 519 of the 1748 LUT bels are LUT1s that nextpnr inserted: 366 for CARRY4 DI inputs, 145 for S inputs and 8 constant-zero feeds for carry-outs. 161 sites hold nothing else. On arty_eth 1193 sites are like that.
4. **CARRY4.** yosys uses 29 more than Vivado on rv_soc, 25 more on rv_mul/rv_big, 77 more on arty_ddr3 and 71 more on arty_eth. nextpnr adds 8-15 more.
   - `share` runs without `-aggressive`, and plain `share` never merges `$alu` cells. picorv32's `alu_add_sub` (add and subtract of the same operands) and five other 32-bit additions each get their own chain: 7 x 8 = 56 of rv_soc's 92 CARRY4.
   - Every adder or comparator of 3 bits or more uses CARRY4. rv_soc has 11 adders of 3-8 bits, which take 18 CARRY4.
   - nextpnr adds a carry stage (a zero-fed LUT plus XORCY) when the carry-out and the sum of the same bit are both used: 8 on rv_soc and 11 on rv_mul. One slice output cannot carry both signals.
   - bram: 7 three-operand 36-bit additions go through maccmap into one carry chain each (63 CARRY4). Vivado uses 80 CARRY4 in total against yosys's 98. Not addressed.
5. **LUTRAM.** The CPUs use 56 sites against Vivado's 50. arty_ddr3 uses 320 against 142: yosys maps a 256-deep, 44-bit memory to 44 RAM256X1S (176 sites), while Vivado puts it in block RAM (Vivado 25 RAMB18 + 11 RAMB36, yosys 37 + 3). Not addressed.
6. **FF.** Within 2 % everywhere (rv_soc 764 vs 771, rv_big 1108 vs 1159, arty_ddr3 3741 vs 3677), except the FIR: 1589 vs 598, which the DSP pipeline draft fixes (Finding 8). No loss from constant or duplicate flip-flops was seen.
7. **Control sets.** 62-74 against Vivado's 40-47 (opt_dff makes more enable/reset variants). At these utilisations this does not cost LUT sites. Not addressed.

Changes (opt-in drafts):
- docs/drafts/nextpnr-area-pack.{patch,md}:
  - `-o carry-di-bypass`: carry DI enters through the AX..DX bypass pin instead of a feed-through LUT1.
  - `-o lut-pair`: two LUTs that share at least 2 inputs and together use at most 5 are put into one O6/O5 site.
- docs/drafts/yosys-xilinx-area-opts.{patch,md}:
  - `synth_xilinx -share_aggressive`: `share -aggressive`.
  - `-carry_minwidth N`: adders and comparators narrower than N bits use LUTs.
  - The 5-bit threshold comes from a sweep on rv_soc (build/qor/area/yexp/*.stat): N = 4/5/6/7/9 gives 91/88/80/78/74 CARRY4 for 1108/1109/1123/1135/1150 LUT cells (default: 92 for 1107). N = 5 saves 4 CARRY4 for 2 LUT cells; larger N costs about 2-6 LUT cells per CARRY4 saved.
- docs/drafts/nextpnr-muxf-const-inputs.{patch,md}: the `-widemux` placement failure (below).
- Builds: nextpnr `qorarea` (build/nextpnr-build/qorarea) and yosys build/yosys-build/yosys-area/yosys.
- qor_bench variants:
  - `area_ref`: no option.
  - `area_pnr`: carry-di-bypass + lut-pair.
  - `area_all`: area_pnr + yosys `-share_aggressive -carry_minwidth 5`.
  - single options: `area_di`, `area_pair`, `area_share`, `area_cmw`.
  - `area_ysref`: the new yosys binary with no option.
- LiteX: flow/qor_area_litex.py (log build/qor/area/run_litex.log).
- No-op checks:
  - `area_ref` `.frames` are identical to `dcp_static` (blinky, rv_soc, bram, fir) and to `fix_static` (rv_mul, rv_big).
  - `area_ysref` (new yosys, no option) `.frames` are identical on all six designs.

After, 5 ns. Area at seed 1. Fmax is the nextpnr timer, best / median / worst of seeds 1-4 (build/qor/oxc7/area_{ref,pnr,all}/<d>_p5/s{1..4}; logs build/qor/area/run_final_main.log):

| design | variant | LUT sites, Vivado rule (O5+O6 pairs) | + sites with only nextpnr LUTs | LUT bels | CARRY4 | FF | Fmax MHz (nextpnr timer) |
|---|---|---|---|---|---|---|---|
| blinky | Vivado own | 1 | - | - | 7 | 28 | 393.86 (Vivado timer) |
| blinky | area_ref | 1 | 27 | 56 | 7 | 28 | 376.93 / 375.94 / 372.58 |
| blinky | area_pnr = area_all | 1 | 27 | 29 | 7 | 28 | 372.58 / 372.58 / 354.36 |
| rv_soc | Vivado own | 1041 (115) | - | - | 63 | 771 | 135.83 (Vivado timer) |
| rv_soc | area_ref | 1098 (65) | 161 | 1748 | 100 | 764 | 137.72 / 135.96 / 134.19 |
| rv_soc | area_pnr | 1059 (104) | 122 | 1377 | 100 | 764 | 137.72 / 134.87 / 134.19 |
| rv_soc | area_all | 1078 (139) | 71 | 1361 | 64 | 764 | 135.26 / 132.09 / 124.01 |
| rv_mul | Vivado own | 1483 (164) | - | - | 123 | 1065 | 135.78 (Vivado timer) |
| rv_mul | area_ref | 1567 (64) | 164 | 2443 | 159 | 1073 | 104.90 / 101.61 / 100.57 |
| rv_mul | area_pnr | 1469 (162) | 122 | 1858 | 159 | 1073 | 104.77 / 98.35 / 87.62 |
| rv_mul | area_all | 1442 (218) | 74 | 1814 | 98 | 1073 | 102.99 / 98.20 / 84.59 |
| rv_big | Vivado own | 1554 (190) | - | - | 123 | 1159 | 178.73 (Vivado timer) |
| rv_big | area_ref | 1608 (74) | 164 | 2494 | 159 | 1108 | 106.36 / 103.63 / 102.24 |
| rv_big | area_pnr | 1535 (147) | 130 | 1909 | 159 | 1108 | 103.95 / 101.18 / 98.71 |
| rv_big | area_all | 1478 (218) | 72 | 1849 | 98 | 1108 | 102.39 / 100.42 / 99.43 |
| bram | Vivado own | 800 (146) | - | - | 80 | 509 | 173.73 (Vivado timer) |
| bram | area_ref | 733 (137) | 108 | 1370 | 98 | 494 | 150.99 / 148.68 / 136.86 |
| bram | area_pnr | 645 (225) | 93 | 995 | 98 | 494 | 164.66 / 152.87 / 142.78 |
| bram | area_all | 626 (244) | 98 | 995 | 98 | 494 | 161.81 / 159.60 / 157.55 |
| fir | all three | 25 (0) | 0 | 25 | 0 | 1589 | 218.15 / 201.84 / 179.86 (identical `.frames`) |

LiteX SoCs, 100 MHz, one seed (sys_clk, nextpnr timer). Build logs build/qor/area/litex/<d>/<variant>/{yosys.log(.gz),nextpnr.log}:

| design | variant | LUT sites (pairs) | + nextpnr-only sites | LUT bels | CARRY4 | FF | LUTRAM sites | sys_clk MHz | yosys s |
|---|---|---|---|---|---|---|---|---|---|
| arty_ddr3 | Vivado own | 4340 (936) | - | - | 178 | 3677 | 142 | - | - |
| arty_ddr3 | area_ref | 5153 (620) | 433 | 7368 | 266 | 3741 | 320 | 110.89 | 30 |
| arty_ddr3 | area_pnr | 4850 (923) | 387 | 6482 | 266 | 3741 | 320 | 107.02 | 31 |
| arty_ddr3 | area_all | 4931 (1042) | 124 | 6297 | 163 | 3741 | 320 | 100.20 | 55 |
| arty_eth | Vivado own | 5432 (933) | - | - | 446 | 5264 | 512 | - | - |
| arty_eth | area_ref | 6389 (533) | 1193 | 10754 | 532 | 5358 | 636 | 101.93 | 43 |
| arty_eth | area_pnr | 6137 (785) | 1087 | 8817 | 532 | 5358 | 636 | 94.63 | 52 |
| arty_eth | area_all | 6200 (906) | 899 | 8735 | 472 | 5359 | 636 | 89.09 | 693 |

The single options, seed 1 (Fmax nextpnr timer; `area_share` and `area_cmw` also carry the two nextpnr options):

| design | area_di: sites + only-nextpnr / Fmax | area_pair | area_share (CARRY4) | area_cmw (CARRY4) |
|---|---|---|---|---|
| rv_soc | 1095 + 123 / 134.19 | 1066 + 161 / 138.29 | 1069 + 75 (67) / 127.18 | 1055 + 112 (94) / 137.72 |
| rv_mul | 1478 + 124 / 99.53 | 1526 + 164 / 106.86 | 1464 + 70 (101) / 91.52 | 1503 + 115 (153) / 97.58 |
| rv_big | 1598 + 125 / 97.74 | 1561 + 164 / 97.85 | 1514 + 79 (101) / 100.53 | 1537 + 112 (153) / 97.76 |
| bram | 645 + 105 / 158.53 | 695 + 108 / 138.64 | 626 + 98 (98) / 161.60 | 645 + 93 (98) / 142.78 |

What this means:
- **nextpnr options (`area_pnr`).** LUT sites by Vivado's rule go down 3.6 % (rv_soc), 6.3 % (rv_mul), 4.5 % (rv_big), 12 % (bram) and 5.9 % (arty_ddr3). LUT bels go down 21-27 % (12-18 % on the LiteX SoCs). The O5+O6 pairs come close to Vivado's (rv_soc 104 vs 115, rv_mul 162 vs 164).
  - Median Fmax (nextpnr timer, 4 seeds): -0.8 % rv_soc (ICAP-bound), -3.2 % rv_mul, -2.4 % rv_big, +2.8 % bram.
  - The worst seed on rv_mul drops from 100.57 to 87.62.
  - On the LiteX SoCs, one seed: -3.5 % (arty_ddr3) and -7.2 % (arty_eth).
- **yosys options on top (`area_all`).** CARRY4 at Vivado's level or below: rv_soc 64 vs 63, rv_mul/rv_big 98 vs 123, arty_ddr3 163 vs 178, arty_eth 472 vs 446.
  - Cost: 1-5 % more LUT cells (rv_soc 1161 vs 1107, arty_ddr3 5654 vs 5454), and on arty_eth 693 s of yosys time instead of 43 s (`share -aggressive`).
  - On rv_mul and rv_big the result is now below Vivado's LUT sites (1442 vs 1483, 1478 vs 1554).
  - Fmax: rv_soc median -2.8 %, and LiteX one seed -9.6 % (arty_ddr3) and -12.6 % (arty_eth). That is larger than the seed noise of Finding 4 on the SoCs.
  - So `area_all` trades Fmax for area and is not a default.
- **lut-pair alone costs Fmax on bram** (138.64 vs 150.99 at seed 1). It places related LUTs together whether or not they are on the critical path.
- Vivado's timer was not run on the new placements: Vivado was in use by other agents for the whole session.

Equivalence:
- **yosys, formal.** flow/qor_area_equiv.sh: `equiv_make`, `equiv_struct`, `equiv_simple -seq 8`, `equiv_induct -seq 8`. Block RAM, LUTRAM, SRL and ICAPE2 are cut with `expose -evert`; CARRY4, DSP48E1 and MUXF7/8 are mapped to their cells_sim models. Logs: build/qor/area/equiv/*.equiv.log.
  - `-carry_minwidth 5` is proven on blinky, rv_soc (1175 `$equiv` cells; CARRY4 92 -> 88) and bram. On rv_mul and rv_big the check with the DSP48E1 models had not finished after 30 minutes when this was written (build/qor/area/equiv/rv_mul_cmw.equiv.log); they are covered by the simulation below.
  - `-share_aggressive` is proven on blinky and bram.
  - FIR: the old and new netlists are textually identical for both options (no carry chain, nothing to share).
  - On rv_soc, rv_mul and rv_big `-share_aggressive` is **not** proven by induction. 101 of 1246 cells stay open on rv_soc: `reg_op1`, `cpuregs_wrdata` and `reg_sh`, i.e. the merged adders' results. Induction starts from arbitrary states, where the sharing conditions may not hold.
- **yosys, simulation.** flow/qor_area_sim.sh runs the default netlist and the `-share_aggressive -carry_minwidth 5` netlist in lockstep in the rv_soc firmware test (designs/rv_soc/tb/b2n_tb_rv_soc.v: 11 operand pairs sent over the UART, through the CPU, and back).
  - rv_soc, rv_mul, rv_big: 157836 cycles each, 0 cycles where tx/led differ, 11/11 results correct, 132 tx edges (build/qor/area/sim/<d>/sim.log).
  - Negative control: one LUT6 INIT bit flipped in the rv_soc gate netlist gives 400 mismatching cycles (build/qor/area/sim/rv_soc_neg/sim.log).
  - Limit: the firmware runs no MUL/DIV, so the merged adders of rv_mul/rv_big's divider are not exercised.
- **nextpnr, bitstream.** The bitstream is decoded by fasm2bels into a netlist, which runs the same firmware test (flow/bit2netlist.sh; qor_rv_soc/rv_mul/rv_big entries added).
  - rv_soc `area_pnr` and `area_all`, final build: 11/11 PASS. The earlier `qorarea` build also passed for `area_di`, `area_pair` and `area_pnr` (build/qor/area/b2n_round1).
  - Negative control: `area_all` checked as the `andn` module fails 6 vectors, as required (build/qor/area/b2n_*.log).
  - fasm2bels cannot decode DSP tiles (`KeyError: 'DSP_L'`), so the rv_mul/rv_big bitstreams were not simulated.

`-widemux`:
- **Placement failure: root cause and fix.** Finding 5's `Unable to find legal placement ... mux8` came from MUXF8s with a constant data input. The feed-through MUXF7 created for such an input was not legalised, so the PSEUDO_GND cell ended up inside the mux cluster. Fixed in docs/drafts/nextpnr-muxf-const-inputs.
  - With the fix, `-widemux 5` places and routes on rv_soc, rv_mul and rv_big: 135.39 / 101.61 / 104.10 MHz, nextpnr timer, seed 1, `area_wm5_ref`. Control: the `qordsp` build without the fix, same static placer, stays in "Strict legalising 1177 cells" and was stopped after 1200 s (build/qor/oxc7/dcp_wm5/rv_soc_p5/s1/nextpnr.log); with the heap placer it errors out (Finding 5).
- **Widemux stays off for correctness.** The `-widemux 5` netlist does not behave like the default one:
  - Lockstep simulation on rv_soc: tx differs from cycle 130 on, in 126516 of 157836 cycles (build/qor/area/sim_wm5/rv_soc/sim.log).
  - The bitstreams of `area_wm5` and `area_wm5_ref` fail the firmware test: tx idles low at boot, and all 11 results are wrong (`fails=12`, build/qor/area/b2n_rv_soc_area_wm5{,_ref}.log).
  - The formal check leaves exactly `reg_pc`/`reg_next_pc[31:2]` unproven (build/qor/area/equiv/rv_soc_wm5.equiv.log).
  - Root cause not established (a `full_case`/x-semantics difference or a yosys bug).
- Its area effect, for the record: rv_mul/rv_big -7 % LUT cells (1460 vs 1575) and -3 % FF; rv_soc +16 LUT cells.

Remaining gap, `area_all` against Vivado's own build:

| design | LUT sites | CARRY4 | FF | LUTRAM sites |
|---|---|---|---|---|
| rv_soc | 1078 vs 1041 (+3.6 %) | 64 vs 63 | 764 vs 771 | 56 vs 50 |
| rv_mul | 1442 vs 1483 (-2.8 %) | 98 vs 123 | 1073 vs 1065 | 56 vs 50 |
| rv_big | 1478 vs 1554 (-4.9 %) | 98 vs 123 | 1108 vs 1159 | 56 vs 50 |
| bram | 626 vs 800 (-22 %) | 98 vs 80 | 494 vs 509 | 1 vs 1 |
| fir | 25 vs 20 | 0 vs 0 | 1589 vs 598 (597 with `-dsp_pipeline`) | 2 vs 2 |
| arty_ddr3 | 4931 vs 4340 (+13.6 %) | 163 vs 178 | 3741 vs 3677 | 320 vs 142 |
| arty_eth | 6200 vs 5432 (+14.1 %) | 472 vs 446 | 5359 vs 5264 | 636 vs 512 |

- nextpnr still uses sites that hold only its own LUTs: 71-98 on the small designs, 124 on arty_ddr3 and 899 on arty_eth. Most of them are S feed-throughs from counter flip-flops. Vivado does the same routing but does not count it.
- Open: LiteX LUTRAM (memory mapping cost), bram's three-operand adders, control sets, the Fmax cost of the pairing, and a Vivado-timer check of the new placements.

## Finding 13 (2026-11-06): nextpnr's implementation timed by Vivado pip for pip; routing and placer delay models calibrated (nextpnr drafts)
Method (flow/xroute.py, vivado/build_xroute.tcl, flow/xroute_cmp.py, flow/xroute_fit.py, flow/xroute_predict.py; CONFIG blocks, dry run by default):
- nextpnr is re-run with the source build's exact command plus `--sdf`, in build/xroute/npr/<name>/. done.json there records that the FASM (sorted lines) is identical to the source build's.
- Netlist: the yosys netlist, rewired to nextpnr's connectivity:
  - the cells nextpnr adds (LUT1 feed-throughs to CARRY4 S/DI, constant LUTs, duplicated LUTs);
  - INV/BUF turned into LUT1;
  - every CARRY4 rebuilt from nextpnr's physical cells.
  Every original pin is checked against nextpnr's net.
- Placement: every cell is `place_cell`ed at nextpnr's BEL and fixed. LUT pins get LOCK_PINS from `X_ORIG_PORT`. RAM32M macros take `LOC`.
- Routing:
  - nextpnr's tile pips are translated to Vivado nodes and set as `ROUTE` (absolute node names), then `IS_ROUTE_FIXED`;
  - `route_design -preserve` completes only what could not be set;
  - then report_timing (5000 setup and 5000 hold paths), `get_net_delays` for every arc, and `get_pips` per net.
- Identity is checked twice: Vivado's pips per net against nextpnr's, and both bitstreams decoded with bit2fasm.
- nextpnr's side is its SDF (slow max), mapped pin by pin to Vivado's report. Re-adding the SDF arcs reproduces nextpnr's own critical path exactly.
- Paths through a net whose Vivado pips differ from nextpnr's are excluded ("strict").
- Source builds: build/qor/oxc7/cal_static/{blinky,bram,rv_soc}_p5/s1 and dspq_cal/{rv_mul,rv_big}_p5/s1 (Finding 10 chipdb, static placer, 5 ns).
- Vivado outputs: C:\Users\finnf\open-dfx-xc7-vivado\build\xroute\<name>\.
- Tables: build/xroute/verify/r3/table_{cal,perm,cal_rcal}_strict.md. They were re-generated on 2026-11-06 from the stored Vivado outputs, and they equal the earlier tables in build/xroute/cmp.

### Identity
| design | nets whose Vivado pips differ / routed nets | pips only nextpnr / only Vivado (of nextpnr's) |
|---|---|---|
| blinky | 0 / 37 | 0 / 0 (of 191) |
| rv_soc | 0 / 1734 | 0 / 0 (of 24406) |
| rv_mul | 1 / 2601 | 25 / 24 (of 34875) |
| rv_big | 2 / 2610 | 6 / 6 (of 38003) |
| bram | 104 / 1458 | 300 / 364 (of 22922): nextpnr leaves a LUT O6 through the AMUX pin where Vivado's site router uses the A pin |
| fir | not imposed: Vivado refuses a 5LUT route-through next to an SRL in the same SLICEM | |

Decoded bitstreams (bit2fasm), nextpnr's against Vivado's:
- blinky: 1327 features in common; nextpnr-only 20 (constant-net pips, clock buffer bits, 1 CYINIT), Vivado-only 9 (unused-IOB settings, 1 CYINIT).
- rv_mul: 77653 in common; rv_big: 85355 in common. The differences are constant-net routing and LUT INIT bits.

### nextpnr's post-route SDF used predicted delays for permuted LUT inputs (fixed, opt-in)
- The bug: `fixup_routing` moves a permuted LUT input's port but leaves the route ending on the old pin, so the SDF printed `predictArcDelay` (0 ps inside a site) for 30-65 % of LUT input arcs.
- The fix: docs/drafts/nextpnr-lut-perm-timing.patch (`-o lut-perm-timing`, build `qorperm`) rebinds the last hop.
- Unchanged by it: nextpnr's printed Fmax and `--report` (computed before fixup).
- No-op, re-verified 2026-11-06 on blinky, rv_soc and bram (build/xroute/verify/r3/perm/result2.txt):
  - option off: FASM, SDF and report identical to `qordsp`;
  - option on: FASM identical as sorted lines, every permuted hop rebound (51 / 3502 / 2311).

### Per-component error, nextpnr minus Vivado on the identical implementation
Full table: build/xroute/verify/r3/table_perm_strict.md (arcs / mean / mean abs / p90 abs, ps). nextpnr timer = SDF with `-o lut-perm-timing`; Vivado timer for Vivado.
- Cells are close:
  - LUT -50 to +21 ps mean (+76 on blinky's one arc);
  - FF clock-to-Q -16 to +10;
  - CARRY4 -32 to -3;
  - RAMB36/DSP48E1/ICAPE2 arcs 0 (they come from prjxray's SDF).
- Setup checks:
  - FF setup +46 to +103 ps (blinky, bram), -36 to -132 ps (CPUs);
  - RAMB36 setup -69 to -166 ps;
  - LUTRAM (RAMD32) setup +341 to +400 ps (pessimistic).
- Routing is the error. Every class is 0.3-0.7 ns too fast per arc in nextpnr: single -380 to -505, double -421 to -484, hex -476 to -593, long -452 to -712, bounce -372 to -415 (blinky's single arc +109), local (LOGIC_OUTS -> IMUX only) -277 to -343 ps mean. The clock net's insertion delay is 0.46-0.78 ns low; it cancels in the skew.
- Hold:
  - nextpnr has no fast corner for routing (`getPipDelay` is one value), so its hold slack is 0.5-1.3 ns per path larger than Vivado's (path T hold: bram +1254, rv_soc +588, rv_mul +521, rv_big +713 ps mean);
  - RAMB36 hold is 0.50-0.65 ns low, DSP48E1 hold 0.74-0.79 ns low;
  - Vivado finds real hold violations on two of these implementations: bram WHS -0.094 ns, rv_soc -0.135 ns.
- On identical routes, nextpnr's Fmax claim is optimistic against Vivado's timer:

| design | nextpnr claim MHz (nextpnr timer) | identical implementation MHz (Vivado timer) | claim error | Vivado MHz, worst fully routed path | claim error vs that |
|---|---|---|---|---|---|
| blinky | 364.70 | 361.93 | +0.8 % | 361.93 | +0.8 % |
| bram | 142.07 | 131.30 | +8.2 % | 131.30 | +8.2 % |
| rv_soc | 133.08 | 97.03 | +37.2 % | 97.03 | +37.2 % |
| rv_mul | 132.96 | 89.33 | +48.8 % | 105.15 | +26.4 % |
| rv_big | 124.18 | 91.56 | +35.6 % | 99.11 | +25.3 % |

Finding 10's smaller errors (6.3 % mean) came from Vivado re-routing nextpnr's placement with its own, better router.

### Routing-delay calibration (docs/drafts/nextpnr-route-timing-cal, opt-in chipdb)
Fit (flow/xroute_fit.py):
- least squares of the per-arc error against the number of pips of each wire class on the arc (class = regex on the pip's destination wire);
- fitted on blinky, rv_soc and bram only;
- one additive slow-corner delay per class goes into the chipdb (`--route-timing`, build/chipdb-rcal/route_timing_xc7a35t_1.json, chipdb build/chipdb-rcal/on).

Fitted adds (ps): IMUX +413, FAN/CTRL +280, BYP +98, single +22, double +30, quad +26, hex +26, long +30, bounce +5, BRAM inputs -44, hard-block outputs -10, CLB site outputs -56. Most of the missing delay is a fixed cost at the interconnect input mux, not in the wires.

Re-verified 2026-11-06 (build/xroute/verify/r3):
- the two drafts apply on a fresh nextpnr-stock export;
- the generator equals the rcal worktree's;
- chipdb without the option is byte-identical to build/chipdb-cal/on, and with the JSON to build/chipdb-rcal/on;
- a refit on the current data moves no class by more than 55 ps (ctrl 280 -> 225, loose set) and the test mean by 6 ps.

Per-arc net delay error, nextpnr minus Vivado (slow max), offline (SDF arcs plus the per-class additions; build/xroute/fit/eval.json):

| arcs | before: mean / mean abs / p90 abs (ps) | after |
|---|---|---|
| fitted designs (blinky, rv_soc, bram), 10017 arcs | -478 / 481 / 757 | -5 / 154 / 307 |
| not fitted (rv_mul, rv_big), 13885 arcs | -517 / 520 / 828 | -49 / 166 / 329 |

Per setup path, same implementation, offline (strict: paths without a Vivado-unrouted net; build/xroute/verify/rep/eval_strict.log), mean error:

| design | before (ps) | after (ps) |
|---|---|---|
| blinky | -163 | +108 |
| bram | -507 | +77 |
| rv_soc | -897 | +173 |
| rv_mul | -688 | +35 |
| rv_big | -552 | +6 |

An earlier "0.6-0.7 ns residual" on the CPUs counted paths through nets that Vivado had left unrouted; it was a measurement artifact.

End to end: nextpnr re-run with the calibrated chipdb (`rcal`, build `qorperm`, `-o lut-perm-timing`) makes a new implementation, which is again imposed on Vivado pip for pip (build/xroute/verify/r3/table_cal_rcal_strict.md):

| design | nextpnr claim, cal chipdb | Vivado on that implementation (worst fully routed path) | error | nextpnr claim, rcal chipdb | Vivado on that implementation | error |
|---|---|---|---|---|---|---|
| rv_mul (not fitted) | 132.96 | 105.15 | +26.4 % | 86.63 | 94.61 | -8.4 % |
| rv_big (not fitted) | 124.18 | 99.11 | +25.3 % | 87.80 | 83.29 | +5.4 % |

- MHz. nextpnr timer for the claims, Vivado timer for the rest.
- rv_big_rcal: Vivado's router left 3 pins unrouted after the fixed routes were set.
- So the claim error drops from +25 % to within 9 %, both signs, on designs not used in the fit.

Clock leaf and carry chain (JSON v2, docs/drafts/nextpnr-route-timing-cal.md):
- Every clock-tree arc from the BUFG to an FF clock pin is 0.77-0.78 ns short in nextpnr: rv_soc mean 0.896 ns in nextpnr against 1.675 ns in Vivado's timer, on 879 arcs. A `clock_leaf` class of +775 ps puts blinky's clock pins at 1.671 ns; Vivado measures 1.645. Fmax is unchanged, because the add cancels in the skew.
- CARRY4 cell arcs already agree with Vivado: CIN -> O/CO within 5 ps, S -> O/CO within 19-43 ps.
- The COUT -> CIN hop is corrected by the existing CLB-output class.
- So the long-carry-path optimism is in routing and the clock leaf, not in the carry cells.

### Placer delay model (docs/drafts/nextpnr-placer-delay-cal, opt-in)
The placer sees routing delay through two models that are not the router's:
- **Global placer.** The static placer uses a fixed formula in xilinx.cc: 500 + 48*min(dy,6) + 24*max(dy-6,0) + 24*min(dx,12) + 12*max(dx-12,0) ps. It never reads the chipdb, so the route-calibrated chipdb does not change the global placement: HPWL after legalisation is identical with both chipdbs on rv_soc, bram and rv_big (build/qor/place/metrics_plp_cal_plp_rcal_pl5_pc_rcal.md).
- **Refinement and pre-route timing.** placer1 and the pre-route timer use `predictDelay`, which reads a delay matrix measured on the chipdb.

flow/xroute_predict.py recomputes both for every routed arc of the identical implementations above and compares them with Vivado's routed delay of that arc. Fits are least squares on blinky, rv_soc and bram; test = rv_mul and rv_big; outputs in build/xroute/predict/.

| model | test arcs: mean / mean abs / p90 abs (ps) |
|---|---|
| static placer formula (current) | -433 / 447 / 888 |
| static placer, fitted `-o static-delay=786,63,29,37,7` | -28 / 269 / 534 |
| predictDelay, cell-calibrated chipdb (current) | -731 / 732 / 1206 |
| predictDelay, route-calibrated chipdb (current) | -538 / 542 / 985 |
| predictDelay, fitted `-o predict-cal=665,682,313,1.235` (rcal chipdb) | -33 / 259 / 527 |

- A LUT input fed from the same slice: predictDelay says 0 ps, Vivado 0.67 ns mean. Another slice of the same tile: 150 ps vs 0.68 ns.
- Between tiles, Vivado's routed delay grows about 1.2-1.4 times as fast with distance as the delay matrix, which is the cheapest route through the routing graph.
- The static formula's distance slopes are of the right size, but its constant is about 0.3 ns low.

### Placement round 2
Variants (flow/place_bench.py; 3 seeds; static placer; route-calibrated chipdb `rcal` unless named):
- `plp_cal` / `plp_rcal`: build `qorperm` with the cell- / route-calibrated chipdb;
- `pl5_pc_*`: `-o predict-cal`;
- `pl6_sd_*`: `-o static-delay=786,63,29,37,7`; `pl6_sdpc_*`: both;
- `pl6_te2_*`: `--placer-static-timing-every 2`.

No-op with the options off, `.frames` identical:
- place_v5 vs place_v4 on rv_soc, bram and rv_big, 3 seeds each (build/qor/place/r13/run4b.log);
- place_v6 vs place_v4 on rv_soc, 3 seeds (run6b.log).

nextpnr timer, route-calibrated chipdb, 3 seeds, mean (min-max) MHz:

| design | plp_rcal | pl5_pc_rcal | pl6_sd_rcal | pl6_sdpc_rcal |
|---|---|---|---|---|
| rv_soc | 99.13 (93.93-103.48) | 95.70 (90.09-102.49) | 97.34 (93.99-99.80) | 95.37 (87.40-99.92) |
| bram | 125.40 (122.52-128.53) | 121.94 (110.95-128.63) | 128.07 (121.80-133.05) | 125.32 (119.08-129.48) |
| rv_big | 87.08 (86.10-88.58) | 90.14 (88.72-90.88) | 83.41 (78.30-87.40) | 83.94 (82.43-86.07) |
| rv_mul (`-pipeline`, `_dq`) | 87.15 (84.42-90.40) | 92.90 (90.69-94.52) | 91.76 (87.36-98.50) | - |

Placement quality besides Fmax, seed means (`place_bench.py --metrics`, build/qor/place/metrics_*.md):

| design | variant | HPWL after legalisation | routed wires | overused wires, router iteration 1 | router iterations |
|---|---|---|---|---|---|
| rv_soc | plp_rcal | 17142 | 43024 | 1798 | 9.3 |
| rv_soc | pl6_sd_rcal | 17514 | 43061 | 1760 | 12.7 |
| bram | plp_rcal | 21741 | 46319 | 1265 | 15.3 |
| bram | pl6_sd_rcal | 21894 | 46422 | 1359 | 14.7 |
| rv_big | plp_rcal | 25725 | 72728 | 2413 | 18.7 |
| rv_big | pl6_sd_rcal | 25980 | 72356 | 2426 | 11.0 |

- In nextpnr's own (now calibrated) timer, none of the delay-model options gains consistently: rv_mul +5 to +7 %, rv_big -4 %, rv_soc -2 to -4 %, within the seed spread.
- The fitted global-placer model (`static-delay`) costs 1-2 % HPWL.
- Wall times are not reported. The machine ran at load 15-20 (8 agents), so the nextpnr seconds in status.json are not comparable between runs.

**Vivado timer on nextpnr's placement** (Vivado routes; mean of 3 seeds in MHz; `place_bench.py --report`; runs in open-dfx-xc7-vivado/build/place_xtime on C:):

| variant | rv_soc | bram | rv_big |
|---|---|---|---|
| pl_base: stub chipdb, Finding 11 | 116.81 | 155.87 | 104.95 |
| plp_cal: cell-calibrated chipdb | 117.84 | 147.28 | 92.20 |
| plp_rcal: route-calibrated chipdb | 117.18 | 149.35 | 94.57 (seeds 4-8) |
| pl5_pc_rcal: predict-cal | 116.00 | 149.69 | 90.84 |
| pl6_sd_rcal: static-delay | 115.02 | 150.42 | 99.44 |
| pl6_sdpc_rcal: static-delay + predict-cal | 119.18 (2 seeds) | 152.65 | 96.56 |
| pl7_mxpc_rcal: delay matrix + predict-cal for the global placer | 116.66 | 153.95 | 96.73 |
| pl6_sdce4_rcal: static-delay, critexp 4 | 112.80 | 153.02 | 96.94 |
| pl8_sdarc2_rcal: static-delay + timing-arc term, ratio 0.2 (DREAMPlaceFPGA-TD idea) | 109.11 | 154.20 | 94.95 |
| pl9_sdwp_rcal: static-delay + weighted preconditioner (Mai et al. idea) | 116.83 | 146.80 | 90.57 |

- The cell-calibrated chipdb makes the placements worse in Vivado's eyes: bram -5.5 %, rv_big -12 % against the stub chipdb.
- Feeding calibrated delays to the global placer wins back part of that loss: bram 147-149 -> 150-154, rv_big 92-95 -> 97-99.
- No variant beats the stub chipdb's placement, and rv_soc stays within its seed spread (107-126).
- The gap to Vivado placing the same netlist is unchanged: rv_soc 157.63, bram 170.88 MHz (Finding 11).
- The timing-arc term (pl8) costs rv_soc 6 % and rv_big 4.5 % against static-delay alone; bram is +2.5 %. It is not a win.
- The weighted preconditioner (pl9) cuts rv_big's HPWL after legalisation by 13 % (25539 -> 22198 against the stub baseline; routed wires -2 %). Its Vivado-timed Fmax is no better: rv_soc equal to the baseline, bram -5.8 %, rv_big -13.7 %. Shorter total wirelength did not mean shorter critical paths, so it is not a win.
- Conclusion of round 2: none of the five global-placement changes (delay calibration of the global placer, predict-cal, timing-arc term, weighted preconditioner, critexp) beats the stub-chipdb placement under Vivado's timer on more than one design. Finding 15's mixes show global placement still loses about 10 MHz on rv_soc, so the cause lies in how the global placer spreads and orders cells, not in the delay values it uses.

Other results:
- eth SoC, 3 seeds: plp_rcal 68.95, pl5_pc_rcal 70.08, pl_base 68.64 MHz.
- rv_mul (`-pipeline` netlist): plp_dqcal 109.64, pl5_pc_dqrcal 107.86 MHz.
- Static vs HeAP placer, Vivado timer, 3 seeds:
  - DDR: static 83.92 (2 seeds), HeAP 84.46.
  - eth: static 68.64, HeAP 67.39.
  - So Fmax is equal within the seeds, but static needs 1.5-2.3x less nextpnr time and far fewer router iterations (docs/wip/placement-global.md).
- Router gap: with the rcal chipdb, nextpnr's claim (calibrated timer on its own routes) is 99 / 125 / 57 MHz on rv_soc / bram / eth. Vivado's timer, with Vivado routing the same placements, gives 117 / 149 / 69. So nextpnr's routing costs about 15-20 % on its own.

The nextpnr timer alone cannot rank these: with the rcal chipdb its claims moved from 133 to 99 MHz (rv_soc) without any placement change. The Vivado timings of all variants (sources in build/qor/place/xsrc) were queued but had not run when this was written: Vivado was held by other work. Results go here and in docs/wip/placement-global.md.


### Open
- fir cannot be imposed: it needs a LUT route-through next to an SRL, which Vivado treats as illegal.
- bram's 104 nets leave through the OUTMUX; ROUTE alone cannot express that.
- nextpnr has no fast-corner routing delay, so hold is not calibrated. The fast-corner timer is now the XDC agent's work.
- One part and corner: xc7a35t-1, slow max.

## Finding 14 (2026-11-06): timing-driven synthesis, retiming, FSM extraction, resource sharing, and the LiteX LUTRAM gap
Question: how much does yosys's netlist cost against Vivado's own synthesis, which yosys options or fixes close it, and why does the LiteX DDR3 SoC use 320 LUTRAM sites against Vivado's 142? Everything below is opt-in; the default flow is unchanged.

Method:
- Netlist variants: flow/synth_timing.py (CONFIG block, dry run by default, cached by a hash of binary, script and RTL in build/qor/synx/synth/<design>/<key>/ with meta.json, yosys.log, stat.txt).
  - `ys`: default `synth_xilinx -flatten -abc9`. `ys_dspq`: with the DSP pipeline draft (Finding 8).
  - `t_dff` / `d_dff`: `abc9 -dff` on `ys` / `ys_dspq`.
  - `t_retime_full` / `d_retime_full`: before LUT mapping, every flip-flop without keep/ASYNC_REG/DONT_TOUCH is legalised to a plain DFF and passed through `abc -dff`, whose script contains ABC's `dretime`; then the normal abc9 LUT mapping. This is the only retiming this yosys has (`synth_xilinx -retime` does not exist).
  - `t_cal`: abc9 with a flat 7-series LUT model, 200 ps on every input (Finding 10's mean Vivado O6 arc), and 450 ps wire delay per level (`-W 450`; Vivado's mean net delay per logic level on the 100 worst rv_soc/rv_big paths is 0.48-0.82 ns). yosys's built-in model has LUT6 inputs at 642/631/472/407/238/127 ps and `-W 300`. `t_cal_dff` = both.
  - `m_keepmem`: the new yosys draft (LUTRAM section below).
- Vivado as the referee for synthesis only: flow/qor_synx.py writes each yosys netlist as EDIF. vivado/build_synx.tcl links it, or runs `synth_design` on the RTL for the `viv*` rows. It then runs the same `opt_design`, `place_design -directive Default` and `route_design`, and dumps 1000 setup paths. Outputs are in C:\Users\finnf\open-dfx-xc7-vivado\build\qor_synx\<design>_<variant>\.
  - Placement and routing are Vivado's in every row; only the netlist differs.
  - Fmax is from Vivado's timer, on the main clock, with ICAP paths excluded (as in Finding 3).
  - `viv_*` rows pass `synth_design` options through synth_opts.txt: `-retiming`, `-fsm_extraction off`, `-resource_sharing off`.
- Area uses Vivado's post-route "Slice LUTs" from the same P&R, and nextpnr's post-route LUT sites counted by the same rule (flow/qor_area.py, Finding 12).
- Checks:
  - Every yosys variant with numbers below was simulated in lockstep against the default netlist under the rv_soc firmware test (flow/synth_timing_equiv.py -> flow/qor_area_sim.sh). The test runs 157836 cycles and 11 operand vectors through the CPU, compares tx/led every cycle, and checks the answers.
  - The LUTRAM fix has its own testbench.
- Synthesis runtime is yosys wall time from meta.json on a machine shared by 8 agents, so it is indicative only.

Vivado P&R of each netlist, Default directive, one run per row (flow/qor_synx_table.py, build/qor/synx/finding14_table.json; Vivado log C:\Users\finnf\open-dfx-xc7-vivado\build\qor_synx\vivado_20261106_215945.log, rv_soc_viv/ys and rv_big_viv from vivado_20261106_134010.log). Fmax is Vivado's timer. Area is Vivado's post-route utilisation. Synthesis time is Vivado `synth_design` or yosys wall time:

| netlist | Fmax MHz excl. ICAP (Vivado timer) | worst path: levels (LUT, CARRY4) | post-route LUT sites | LUTRAM | FF | CARRY4 | synthesis s |
|---|---|---|---|---|---|---|---|
| rv_soc Vivado synth_design | 171.00 | 3 (3, 0) | 1041 | 50 | 771 | 63 | 52.4 |
| rv_soc Vivado -retiming | 179.50 | 2 (2, 0) | 1032 | 50 | 844 | 63 | 61.0 |
| rv_soc yosys `ys` | 157.63 | 6 (6, 0) | 1122 | 56 | 768 | 92 | 7.5 |
| rv_soc `t_dff` | 162.63 | 8 (4, 4) | 1090 | 56 | 739 | 86 | 12.9 |
| rv_soc `t_retime_full` | 160.41 | 6 (6, 0) | 1206 | 56 | 716 | 86 | 10.3 |
| rv_soc `t_cal` | 164.20 | 8 (4, 4) | 1141 | 56 | 768 | 92 | 8.9 |
| rv_soc `t_cal_dff` | 165.84 | 8 (4, 4) | 1126 | 56 | 739 | 83 | 13.2 |
| rv_big Vivado synth_design | 177.68 | 8 (4, 4) | 1554 | 50 | 1159 | 123 | 188.3 |
| rv_big Vivado -retiming | 177.68 | 8 (4, 4) | 1554 | 50 | 1159 | 123 | 66.9 |
| rv_big yosys `ys` | 111.07 | 11 (1, 8) | 1630 | 56 | 1116 | 148 | 19.4 |
| rv_big `ys_dspq` | 156.59 | 5 (5, 0) | 1644 | 56 | 1066 | 148 | 23.3 |
| rv_big `d_dff` | 168.52 | 4 (4, 0) | 1588 | 56 | 1023 | 142 | 48.3 |
| rv_big `d_retime_full` | 162.39 | 5 (5, 0) | 1780 | 56 | 1001 | 142 | 31.4 |

Vivado synthesis options, synth only (post-synthesis "Slice LUTs" / CARRY4 / FF against the default `synth_design` of the same design):
- rv_soc: default 1009 / 63 / 771. `-resource_sharing off` gives 1040 / 71 / 767. `-fsm_extraction off` gives 1026 / 63 / 767.
- rv_big: default 1560 / 123 / 1159. `-resource_sharing off` gives 1594 / 131 / 1094. `-fsm_extraction off` gives 1579 / 123 / 1097.

What this says (one run per row; the spread over three place directives on the same netlist was 157.6-165.9 MHz for rv_soc `ys`, so differences under about 5 % are within placement noise):
- Retiming:
  - Vivado's `-retiming` lifts rv_soc from 171.0 to 179.5 MHz: 37 backward moves, +73 FF, the worst path down to 2 LUT levels.
  - On rv_big Vivado reports 74 backward moves, but its post-route numbers are identical to the default run (not investigated).
  - yosys's only retiming (`t_retime_full`, ABC `dretime`) gives +1.8 % on rv_soc and +3.7 % on rv_big over the matching baseline (162.39 vs `ys_dspq` 156.59). It costs +84 / +136 LUT sites.
  - `abc9 -dff` does better at no area cost: rv_soc +3.2 % (162.63) at -32 LUT sites. rv_big on top of the DSP draft: 156.59 -> 168.52 MHz (+7.6 %) at -56 LUT sites, which brings rv_big to 5.2 % under Vivado's own netlist (from 37.5 % under with plain `ys`).
- Timing-driven LUT mapping: the flat calibrated abc9 model (`t_cal`) helps under Vivado's timer, rv_soc 157.63 -> 164.20 (+4.2 %), although nextpnr's own timer ranked it worse (133.42 vs 143.82, Finding 14 nextpnr json).
  - Combined `t_cal_dff`: 165.84 MHz (+5.2 %), 1126 LUT sites (+4), 739 FF. rv_soc goes from 7.8 % to 3.0 % under Vivado's netlist.
  - Both stay at 8 logic levels on the worst path, against Vivado's 3. That path is BRAM -> logic (see the abc9 arrival note below).
- Resource sharing and FSM extraction in Vivado are worth 1-3 % LUTs on these CPUs. Turning sharing off adds 8 CARRY4, the same direction as yosys's missing `share -aggressive` (Finding 12).
- Synthesis time: yosys 7.5-48 s against Vivado 52-188 s on these designs. `-dff` roughly doubles yosys's time on rv_big (23 -> 48 s with the DSP draft) and on rv_mul. On arty_ddr3 it takes 195 s against 33 s.

LiteX LUTRAM gap (arty_ddr3, 320 vs 142 LUTRAM sites): root cause and fix.
- 176 of the 320 sites are one memory: the L2 cache tag memory `tag_mem`, 512 x 22, single port, synchronous write-first read (`if (we) tag_mem_dat0 <= dw; else tag_mem_dat0 <= tag_mem[adr];`). Two bits of the written tag are constant 0 in this SoC.
- During `synth_xilinx`'s `prepare` step, `opt` (opt_dff) turns those two bits of the read register into a `$sdff` with sync reset `we`. The register is now split into two FF cells.
- `memory_dff` runs later (in `coarse`) and logs "no output FF found" for tag_mem. The read port stays asynchronous, block RAM cannot implement that, and memory_libmap picks 44 RAM256X1S (176 LUT sites) plus a fabric register. Vivado uses one RAMB18 for it.
- Reproduced in 11 lines (build/qor/synx/lutram/tm2.v): 44 RAM256X1S. The same memory without the constant bits (tm.v) gives 1 RAMB18E1.
- Fix, docs/drafts/yosys-opt-dff-keep-memrd-regs.{patch,md} (+26 lines in passes/opt/dff), built as build/yosys-build/yosys-synx/yosys:
  - Opt-in with `scratchpad -set opt_dff.keep_memrd_regs 1`.
  - opt_dff then does not infer a sync reset on part of a register whose D comes from a `$memrd` data port. A reset over the whole register is still inferred.
- Scripted alternatives tried first, rejected:
  - `memory_dff` before the full `opt` (`m_memdff`): on rv_soc it merges the address register of the boot RAM instead of its output register, +58 FF and +54 LUT cells.
  - `opt -nosdff` until `memory -nomap` (`m_nosdff`): fixes tag_mem but adds 210 LUT cells on arty_ddr3, because sync-reset inference moves for every register.
  - The manual `prepare` script itself (`t_prep`) gives a byte-identical netlist to `synth_xilinx` on rv_soc (build/qor/synx/noop.json).
- No-op check: with the option off, the same binary gives byte-identical netlists to the option-on run on rv_soc, rv_mul, rv_big, bram and fir; only arty_ddr3 changes.
  - The rebuilt binary has the same cell counts as oss-cad-suite's yosys on all six designs. Auto-generated names differ, because NEW_ID contains the source path.
- Effect on arty_ddr3 (yosys stat): 44 RAM256X1S -> 0, RAMB18E1 37 -> 38, LUT cells 5141 -> 5197 (+56), FF 3741 -> 3738, MUXF7/8 3 -> 8. Synthesis 36.3 s -> 37.7 s.
  - The +56 LUTs come from yosys putting the RAM in SDP x36 READ_FIRST mode and emulating write-first in fabric: tm2 gets 21 FDRE + 22 LUT3 next to the RAMB18E1. Vivado uses the RAMB18's own WRITE_FIRST mode.
- nextpnr post-route, by Vivado's LUT-site rule (flow/qor_area_litex.py variants `area_keepmem`, `area_pnr_keepmem`; seed 1; build/qor/area/litex/arty_ddr3/<variant>/):

| arty_ddr3 | LUT sites (O5+O6 pairs) | + sites with only nextpnr LUTs | LUTRAM sites | FF | sys_clk MHz (nextpnr timer, seed 1) |
|---|---|---|---|---|---|
| Vivado own | 4340 (936) | - | 142 | 3677 | - |
| area_ref (Finding 12) | 5153 (620) | 433 | 320 | 3741 | 110.89 |
| area_keepmem | 5040 (613) | 435 | 144 | 3738 | 97.20 |
| area_pnr (Finding 12) | 4850 (923) | 387 | 320 | 3741 | 107.02 |
| area_pnr_keepmem | 4682 (971) | 406 | 144 | 3738 | 102.33 |

  - LUTRAM is now at Vivado's level (144 vs 142). With the nextpnr area options, LUT sites go from +11.8 % to +7.9 % over Vivado.
  - Seeds 2 and 3 (flow/qor_synx_seeds.py, seed set in gap_build.CONFIG, build/qor/area/litex_seeds/s<seed>/, log build/qor/synx/logs/seeds.log):
    - area_ref: LUT sites 5188 / 5176, sys_clk 105.33 / 106.28 MHz.
    - area_keepmem: LUT sites 5028 / 5001, sys_clk 104.69 / 88.98 MHz.
    - Over 3 seeds: LUT sites -2.6 % (median 5176 -> 5028), and nextpnr-timer sys_clk median 106.28 -> 97.20 MHz (-8.5 %). The best seeds are 110.89 vs 104.69.
  - So the fix trades nextpnr Fmax for area. The critical sys_clk path now starts at the tag RAM's clock-to-out: `tag_mem.0.0.DOADO7`, clk-to-q 2.45 ns in nextpnr's model, against a 0.35 ns flip-flop before. The tag compare is behind it.
  - Vivado faces the same block RAM. Vivado P&R of the same netlists (flow/ddr_xtime.py `--variant keepmem --modes free`; C:\Users\finnf\open-dfx-xc7-vivado\build\ddr3_xtime\arty_ddr3_keepmem_free against arty_ddr3_gapfix_free; Vivado's timer at 100 MHz):
    - WNS +0.418 -> +0.334 ns, about 104.4 -> 103.5 MHz.
    - LUT sites 4821 -> 4664 (-3.3 %), LUTRAM 320 -> 144, Block RAM tiles 21.5 -> 22, FF 3738 -> 3767.
    - So under Vivado's placer and timer the area gain costs under 1 % Fmax. The -8.5 % above is how nextpnr handles the RAM clock-to-out path.
  - The qor_synx flow (vivado/build_synx.tcl) failed placement on the arty_ddr3 keepmem netlist ("un-associated IO delay instances"; the default netlist was not tried in that flow). The cause was not checked; that flow reloads opt.dcp before place_design. So ddr_xtime was used here.
  - The write-first emulation adds a LUT level after the RAM. Using TDP WRITE_FIRST would remove it (not done).
- Function: flow/qor_memdff_sim.sh simulates RTL, stock netlist and patched netlist of tm.v and tm2.v in lockstep: 512 writes to fill the memory, then 200000 random cycles.
  - Result: 0 mismatches (build/qor/synx/lutram/sim/*.sim.log).
  - yosys's cells_sim RAMB18E1 returns X in SDP x36 mode, so the script carries a minimal model of exactly that mode, which stops the run if any other mode is used.
  - Negative control: one LUT3 INIT of the patched tm2 netlist set to 0 gives 100422 mismatching cycles.
  - No gate-level testbench exists for the whole SoC; the change is confined to tag_mem (one "Keeping" log line per opt run, and the other 5 designs are unchanged).
- arty_eth (636 vs 512 LUTRAM): the draft changes nothing. Its LUTRAM is 147 RAM32M + 8 RAM64M from FIFOs, a different gap that is still open.

FSM extraction against Vivado:
- arty_ddr3: yosys extracts no FSM. 15 state registers (the 8 bank machines, refresher, multiplexer, wishbone2csr, litedramwishbone2native, fullmemorywe, choose_req/cmd grant) are rejected only because "Register has an initialization value"; LiteX gives every register one.
  - Vivado extracts 4 of them (log C:\Users\finnf\open-dfx-xc7-vivado\build\ddr3\vivado.log): refresher, multiplexer and litedramwishbone2native kept 'sequential' (binary, as in the RTL), wishbone2csr 'one-hot'.
  - So for 3 of the 4 Vivado keeps the same encoding yosys leaves in place. FSM encoding is not where the LiteX area gap is.
- rv_soc/rv_big: yosys recodes picorv32's `cpu_state` (already one-hot in the RTL) and `mem_wordsize` to one-hot. Vivado extracts `mem_state` (sequential) and the bridge `state` (one-hot).
  - `t_nofsm` (`fsm_encoding none` on every wire): rv_soc 1057 -> 1054 LUT cells, rv_big 1448 -> 1446, arty_ddr3 5141 -> 5136.
  - nextpnr-timer Fmax over 3 seeds (build/qor/synx/nextpnr_ys_t_cal_..._s_share.json): rv_soc 143.82 -> 142.49, rv_big 103.64 -> 104.12, within the seed noise of Finding 4.
- Vivado `-fsm_extraction off`: the synth-only rows of the Vivado table above.

Resource sharing:
- yosys `share -aggressive` (Finding 12's `-share_aggressive`): CARRY4 rv_soc 92 -> 64, rv_big 148 -> 96, but LUT cells +7 % / +10 %, and depth goes up (max LUT levels 7 -> 8, rv_soc).
  - nextpnr-timer Fmax over 3 seeds: rv_soc 143.82 -> 124.84 (-13 %), rv_big 103.64 -> 103.17.
  - Synthesis: rv_soc 9.2 s -> 33.3 s, arty_ddr3 32.8 s -> 77.0 s.
- Vivado `-resource_sharing off` against the default (auto): the synth-only rows of the Vivado table above.

abc9 and timing-driven LUT mapping:
- A delay target (`abc9.D`, Finding 5) changes nothing. A `&dch` x2 script on the flat model (`t_cal_dch2`) gives rv_soc 133.05 vs `t_cal` 133.42 MHz, and rv_big 103.78 vs 104.13 (nextpnr timer, mean of 3 seeds, build/qor/synx/nextpnr_ys_t_cal_..._s_share.json).
- yosys's BRAM clock-to-out never reaches ABC.
  - RAMB36E1's `(posedge CLKARDCLK => DOADO) = 2454` arc is conditional on `&DOA_REG`; the 882 ps arc is on `|DOA_REG`. With DOA_REG = 0 neither condition holds. The intent was presumably `!DOA_REG` for the 2454 ps arc.
  - But the cause is deeper. With the RAMB18E1/RAMB36E1 models overridden so that the arc is 0, 2454 or 5000 ps, or conditioned on `!DOx_REG`, abc9's input.xaig is byte-identical, ABC reports the same mapped delay (`Del = 1548`), and the rv_soc netlist is byte-identical (build/qor/synx/arrival/).
  - So abc9 maps BRAM-fed logic as if the RAM output arrived at time 0.
  - On rv_soc the critical paths under Vivado's timer are exactly those: boot RAM -> picorv32 `reg_out`. Vivado's own netlist has 3 LUT levels there (Default: 171.0 MHz). Yosys's has 6 LUT levels (157.6 MHz), on the same Vivado P&R.
  - The XAIG's `i` section carries no arrival value at all: no float 2454 or 882 (RAM), nor 303 (FDRE clock-to-out), in input.xaig.
  - Keying write_xaiger's arrival map by the sigmapped bit, as the primary inputs are looked up, changed nothing (tried in build/src/yosys-synx, reverted).
  - Found in round 2 below: abc9's default writer (`write_xaiger2`) emits no arrival times at all; `abc9.xaiger=1` restores them.
- abc9 with the flat calibrated model (`t_cal`): see the Vivado table above.

Retiming:
- yosys has no register retiming except ABC's `dretime` through `abc -dff` (`t_retime_full`) and `abc9 -dff`, which only lets ABC merge/sweep flip-flops (`t_dff`). The Vivado table above compares both with Vivado's `synth_design -retiming`.
- arty_ddr3: `t_retime_full` moves no flip-flop (3741 before and after). A likely reason, not verified: LiteX gives every register an init value.

DSP accumulators (pw_dsp power designs, open flow 6.8-7.8x Vivado's LUTs, build/power/fit.md):
- pw_dsp8 with stock yosys: 4 DSP48E1, 96 CARRY4, 548 FDRE, 620 LUTs. All eight 48-bit accumulators `p[i] <= p[i] + m[i]` are in fabric.
- Root cause: MACs i and i+1 have identical inputs (`a[i] = s[i/2]`, `b[i] = s[i/2+1]`). opt_merge merges their multipliers, so each multiplier output then feeds two accumulators. xilinx_dsp packs the A/B/M registers ("ffA2 ffB2 ffM") but no post-adder for a multiplier with two users.
- With the pairs made distinct (`a[i] = s[i/2][24:0] ^ i`, build/qor/synx/dspacc/pw_dsp8u.v), the same yosys packs every accumulator: 8 DSP48E1 with "postadder ... ffP", 0 CARRY4, 164 FDRE, 313 LUTs. The init value on `p` does not matter (pw_dsp8n.v, same result).
- So yosys's accumulator packing works. These designs hit a pass-order interaction: merging duplicate multipliers before DSP packing.
- Not changed here. A fix would let xilinx_dsp duplicate a multiplier that feeds several post-adders, or run opt_merge on `$mul` only after DSP packing.

Checks (all PASS, 157836 cycles, 0 tx/led mismatches, 11/11 vectors; build/qor/synx/equiv/<design>/<variant>_<key>/sim/<design>/sim.log):
- rv_soc: `t_dff`, `t_retime_full`, `t_cal`, `t_cal_dff`, `m_nosdff`.
- rv_big: `t_dff`, `t_retime_full`, `d_dff`, `d_retime_full`, `m_nosdff`. rv_mul: `m_nosdff`.
- `t_cal` is also proven with `equiv_struct`/`equiv_induct` on rv_soc (870 `$equiv` cells, 0 unproven). The `-dff` and retiming variants move registers, so the structural check does not apply to them.
- The earlier lockstep negative control (Finding 12: one flipped LUT INIT gives 400 mismatching cycles) shows the bench detects a single wrong LUT.


### Finding 14, round 2 (2026-11-06 night): BRAM arrival found, DSP accumulators, arty_eth LUTRAM

**abc9 and the block RAM clock-to-out: root cause.**
- abc9 writes the netlist it hands to ABC with `write_xaiger2`, unless `-dff` is given. The code is passes/techmap/abc9.cc: `xaiger = design->scratchpad_get_int("abc9.xaiger", 2)`, and `-dff` forces 1.
- write_xaiger2 writes no arrival-time section. So every blackbox output reaches ABC at time 0: block RAM, DSP, LUTRAM, and the flip-flop clock-to-out.
- This is why the round-1 model overrides had no effect.
- The older `write_xaiger` (`scratchpad -set abc9.xaiger 1`, an existing option, so no code change) does write them. On rv_soc, ABC's mapped delay goes from 3440 ps (RAMB36 arc set to 0) to 4335 ps (the real arc), and the netlist changes.
- It also means the `-dff` variants of round 1 (`t_dff`, `t_cal_dff`, `d_dff`) already had the arrival times, because `-dff` selects the old writer. `x1_cal_dff` gives the same cell counts as `t_cal_dff`.
- Vivado P&R and timer, Default directive, one run each:

| netlist | Fmax MHz (Vivado timer) | post-route LUT sites | FF | CARRY4 | yosys s |
|---|---|---|---|---|---|
| rv_soc Vivado synth_design | 171.00 | 1041 | 771 | 63 | 52.4 (Vivado) |
| rv_soc Vivado -retiming | 179.50 | 1032 | 844 | 63 | 61.0 (Vivado) |
| rv_soc `ys` | 157.63 | 1122 | 768 | 92 | 7.5 |
| rv_soc `x1` (abc9.xaiger 1) | 162.44 | 1194 | 768 | 90 | 11.5 |
| rv_soc `x1_cal` (+ flat calibrated LUT model) | 176.77 | 1188 | 768 | 87 | 10.5 |
| rv_big Vivado synth_design | 177.68 | 1554 | 1159 | 123 | 188.3 (Vivado) |
| rv_big `ys_dspq` | 156.59 | 1644 | 1066 | 148 | 23.3 |
| rv_big `dx1` | 162.65 | 1618 | 1068 | 146 | 27.8 |
| rv_big `dx1_cal` | 169.15 | 1674 | 1058 | 143 | 43.0 |

- On rv_soc, `x1_cal` is 3.4 % above Vivado's own netlist on Vivado's P&R, and 1.5 % below Vivado with `-retiming`. It costs 66 more LUT sites than plain yosys (147 more than Vivado).
- rv_big `dx1_cal` is 4.8 % under Vivado.
- These are single runs: the spread over place directives on one netlist was up to 5 % (round 1). A run with the Explore and ExtraTimingOpt directives on `x1_cal` / `dx1_cal` is queued; see docs/wip/synthesis.md.
- With nextpnr (the open flow's placer), nextpnr timer, mean of seeds 1-3. Same build and options as round 1; build/qor/synx/logs/np_x1.log, build/qor/oxc7/synx_<variant>_noicap/:
  - rv_soc: `ys` 143.82, `x1` 143.99, `x1_cal` 147.11 MHz (+2.3 %).
  - rv_big: `ys_dspq` 133.09, `dx1` 148.24 (+11.4 %), `dx1_cal` 131.68 MHz.
  - LiteX SoCs, `abc9.xaiger 1` alone, nextpnr, seed 1 (flow/qor_area_litex.py variant `area_x1`; build/qor/area/litex/<d>/area_x1/):
    - arty_ddr3: system clock 106.2 MHz, against 110.89 for area_ref seed 1, and 105.33 / 106.28 for seeds 2 and 3. Same LUT sites (5160 vs 5153).
    - arty_eth: system clock 93.1 vs 101.9 (one seed each).
    - The system clock is reported under a different net name in these runs (`main_crg_clkout_buf0` / `etherbone_clk` instead of `sys_clk`).
    - So no LiteX gain is shown, and arty_eth may lose; more seeds and a Vivado-timer run are needed.
  - So the arrival times help the CPU designs under both placers. The calibrated LUT model helps rv_soc under both, but rv_big only under Vivado's placer. There is no single best preset yet.
- Lockstep firmware simulation PASS for `x1`, `x1_cal`, `dx1`, `dx1_cal` (157836 cycles, 0 mismatches).

**DSP accumulators (pw_dsp).**
- Opt-in prepare variant `k_mul` in flow/synth_timing.py: `$mul` cells carry `keep` during `prepare`'s opt, and the attribute is removed before `map_dsp`. So identical multipliers are no longer merged before xilinx_dsp has packed each one with its accumulator.
- No-op: byte-identical netlists on rv_soc, rv_mul, rv_big, bram and fir.
- Effect (flow/qor_pwdsp_kmul.sh, yosys stat; synthesis time unchanged within noise):

| design | DSP48E1 | CARRY4 | FF | LUT |
|---|---|---|---|---|
| pw_dsp8 | 4 -> 8 | 96 -> 0 | 548 -> 164 | 620 -> 305 |
| pw_dsp32, pw_dsp32_p5 | 16 -> 32 | 384 -> 0 | 2084 -> 548 | 2352 -> 1047 |
| pw_dsp64 | 32 -> 64 | 768 -> 0 | 4132 -> 1060 | 4665 -> 2030 |

- The check uses a pw_dsp8 copy whose output xors one accumulator of each identical pair; the original output is constant 0. RTL, stock and `k_mul` netlists in lockstep for 20000 cycles: 0 mismatches, with 18747 output changes. Negative control: one LUT2 INIT changed gives 18749 mismatches.

**arty_eth LUTRAM (636 vs 512 sites): cause and an opt-in rule.**
- Vivado's own synthesis puts three synchronous FIFO memories into block RAM: `storage_12` 16x70 (RAMB36), `mem_2` 128x12 (RAMB18) and `mem_3` 32x42 (RAMB36). Source: the "Block RAM: Final Mapping Report" in C:\Users\finnf\open-dfx-xc7-vivado\build\eth\vivado.log.
- yosys's memory_libmap cost model keeps them in LUTRAM: 12 RAM32M, 7 RAM32M and 8 RAM64M, about 108 LUT sites.
- Raising the LUTRAM cost in the libmap file is not selective: it also moves the depth-2 memories to flip-flops.
- flow/synth_blockrule.py (opt-in, two yosys passes): `ram_style = "block"` for memories whose read ports are all synchronous, that hold more than 1024 bits, and that have no ram_style of their own.
  - The threshold is fitted to these designs: rv_soc's register file is exactly 1024 bits, and Vivado keeps it in LUTRAM.
  - arty_eth: RAM32M 147 -> 133, RAM64M 8 -> 0 (620 -> 532 LUTRAM sites at 4 per primitive; Vivado 504 + 8 SRL), RAMB18 12 -> 13, RAMB36 27 -> 29.
  - No-op: arty_ddr3 is identical to the default netlist, and rv_soc with the rule equals rv_soc without it.
- flow/qor_blockrule_sim.sh: RTL, LUTRAM netlist and block-RAM netlist of the three FIFO shapes, with Xilinx's unisim RAMB18E1/RAMB36E1 models from the local Vivado install. 100000 random cycles each, 0 mismatches.
  - The first 16 cycles have no writes, because glbl holds GSR for 100 ns and the model ignores writes then. The first 64 cycles are not compared.
  - Negative control: WRITE_MODE_A set to WRITE_FIRST gives 62422 mismatches.
- yosys uses 2 RAMB36 for the 16x70 FIFO (two read ports) where Vivado uses 1.
- nextpnr post-route, seed 1, LUT sites by Vivado's rule (flow/qor_area_litex.py variants `area_blockrule` / `area_pnr_blockrule`, netlist from build/gap/arty_eth/blockrule/):
  - LUTRAM 636 -> 548 sites (Vivado 512).
  - LUT sites 6389 -> 6315 (area_ref) and 6137 -> 6104 (with the nextpnr area options).
  - sys_clk, nextpnr timer: 101.93 -> 89.92 and 94.63 -> 89.43 MHz.
  - Single seed, but the same direction as the arty_ddr3 LUTRAM fix: nextpnr pays for the RAM clock-to-out paths that Vivado absorbs.
- Vivado P&R of the arty_eth netlist with the rule: queued (docs/wip/synthesis.md).

## Finding 15 (2026-11-07): packing and detailed placement against Vivado's placement (nextpnr draft `nextpnr-packing-dpl`)
Method:
- nextpnr: own tree build/src/nextpnr-dpl = ce3f7c18 + install/patches/nextpnr (TREE 961ea46e); builds build/nextpnr-build/dpl0 (base), dpl1 (+ `-o carry-di-bypass`), dpl2 (+ `-o dpl`). Every run: `--placer static -o hardblock-timing`, route-calibrated chipdb build/chipdb-rcal/on (Finding 13), 5 ns for the qor designs, 100 MHz sys_clk for eth. Variants dp0 (base), dp1 (carry-di-bypass), dp2dp (carry-di-bypass + dpl). Harness flow/dpl_bench.py (nextpnr through ofx/npwait.sh); runs in build/qor/oxc7/<variant>/<design>_p<ns>/s<seed>/.
- Vivado's timer: vivado/dpl_dump.tcl places the yosys netlist itself ("free", opt + place + route) or imposes our placement fixed and places only what nextpnr made itself ("placed", the Finding 3 method), routes, and dumps cells, the 1000 worst paths as pin lists, utilisation, congestion, routed PIP count and step times. Runner flow/dpl_vivado.sh / flow/dpl_queue.sh (one invocation per design under vivado/vivado_slot.sh). Output C:\Users\finnf\open-dfx-xc7-vivado\build\dpl_xtime\<name>\.
- Metrics: flow/dpl_metrics.py on a dump plus the yosys netlist (slices, LUT/FF per slice, LUT-FF pairs on the direct D path, carry S-LUT in the carry's slice, HPWL in prjxray grid units, FF slice x control-set pairs, critical-path hops); one row per dump with flow/dpl_summary.py.
- Mixed placements: flow/dpl_mix.py takes one placement's slices (which cells share a slice, on which bels) to the mean position the same cells have in the other placement and legalises them slice by slice (carry chains as one column piece; RAMB/DSP from the global source). `vpack_nglob` = Vivado's packing at our positions, `npack_vglob` = ours at Vivado's, `vpack_vglob` = Vivado's own through the same legaliser (control).

### Diagnosis (Vivado timer, seed 1)
| | rv_soc Vivado | rv_soc ours (dp0) | bram Vivado | bram ours (dp0) | rv_mul Vivado |
|---|---|---|---|---|---|
| Fmax, MHz (Vivado timer; rv_soc excl. ICAP) | 157.63 | 126.17 | 170.88 | 150.13 | 111.27 |
| slices (Vivado count) | 398 | 497 | 290 | 369 | 551 |
| LUTs / FFs per used slice | 3.56 / 2.42 | 3.00 / 1.98 | 3.58 / 3.15 | 3.06 / 2.56 | 3.54 / 2.52 |
| LUT->FF pairs on the direct D path | 83.0 % | 98.6 % | 73.7 % | 87.7 % | 86.3 % |
| carry S LUT in the carry's slice | 100 % | 65.6 % | 92.0 % | 81.6 % | 100 % |
| HPWL, all signal nets (grid units) | 17141 | 19875 | 21092 | 22327 | 22151 |
| routed signal PIPs (Vivado router) | 39688 | 43670 | 20771 | 22428 | 46691 |
| FF slice x control-set pairs (minimum) | 319 (130) | 388 (130) | 157 (62) | 193 (62) | 432 |
| worst 200 paths: mean hops / net delay ns | 29.7 / 2.99 | 36.4 / 3.74 | 13.8 / 1.45 | 22.7 / 2.09 | 28.4 / 2.85 |

- LUT-FF pairing is **not** the gap: nextpnr pairs more often than Vivado (98.6 vs 83.0 %, 87.7 vs 73.7 %). Carry chains are aligned in both (0 broken links). F7/F8 use is equal (same netlist). DSP/BRAM to logic distance is not worse in ours (rv_soc 9.3 vs 24.5 grid units; bram 17.2 vs 18.1).
- What differs: 25-27 % more slices (fewer LUTs and FFs per slice), 6-16 % more HPWL and 8-10 % more routed PIPs, 20-23 % more FF slice/control-set pairs, and the critical paths have 23-64 % more hops with 25-44 % more net delay.
- One packing cause found in the code (pack_carry.cc): every CARRY4 DI input without a single-load LUT gets a feed-through LUT on the position's 5LUT (rv_soc 366 of 368, bram 357/392, rv_big 590/592), and only LUT1-LUT5 may be the S LUT. The S LUT and the DI feed-through share the 5 inputs of one LUT6 site, so S LUTs with 5 inputs or a LUT6 get a feed-through too and sit elsewhere (S feed-throughs: rv_soc 145 of 376, bram 125/392, rv_big 144/603). Vivado feeds DI from the X pin (AX..DX -> xCY0 mux) and keeps the S LUT in the carry slice (100 % on rv_soc and rv_mul). In the imposed placement this shows as 65.6 % / 81.6 % S-LUT co-location.

### Fix 1: `-o carry-di-bypass` (packing)
DI comes in through the X pin unless it is constant or DI0 of a chain head whose CYINIT already uses AX; the X-pin use goes into the cell tags (`x_sigs`), so slice validity keeps a flip-flop bypass or MUXF7/F8 select off it; S may then be a LUT6. Routing and FASM needed no change (the chipdb has the AX -> ACY0 site pip; AX is the FASM default). nextpnr side, mean of seeds 1-3 (nextpnr timer for Fmax):

| design | LUT cells dp0 -> dp1 | slices dp0 -> dp1 | nextpnr PIPs dp0 -> dp1 | nextpnr Fmax dp0 -> dp1 -> dp2dp | nextpnr s dp0 / dp1 / dp2dp |
|---|---|---|---|---|---|
| rv_soc | 1748 -> 1538 (-12 %) | 495 -> 449 (-9 %) | 28980 -> 29425 | 99.1 -> 92.1 -> 93.2 | 79 / 63 / 53 |
| rv_mul | 2443 -> 2147 (-12 %) | 683 -> 639 (-6 %) | 40464 -> 40517 | 90.3 -> 86.9 -> 89.9 | 47 / 67 / 53 |
| rv_big | 2494 -> 2198 (-12 %) | 744 -> 677 (-9 %) | 49107 -> 49150 | 87.1 -> 84.0 -> 87.2 | 48 / 40 / 33 |
| bram | 1370 -> 1090 (-20 %) | 341 -> 287 (-16 %; Vivado 290) | 32540 -> 32488 | 125.4 -> 130.4 -> 134.8 | 27 / 25 / 27 |
| eth (LiteX) | 10754 -> 10089 (-6 %) | 2868 -> 2796 (-3 %) | 190569 -> 192588 | 57.0 -> 60.2 -> 60.6 | 121 / 108 / 114 |

- bram now uses as many slices as Vivado (287 vs 290). On the CPUs nextpnr's own timer drops 3-7 % with dp1 alone; the critical paths there are 9-level LUT chains without a carry (e.g. rv_mul s1, identical cell sequence, 10.77 vs 11.39 ns, all in the routing), i.e. a different placement of the same path, not a slower carry. Vivado-timed numbers: see "Vivado-timed comparison" below.

### Fix 2: `-o dpl[=R,P,C,E]` (timing-driven detailed placement)
After placer1 refinement (XilinxImpl::postPlace, before fixup_placement): each unclustered LUT/FF with an arc of criticality >= C (0.8) is offered every compatible bel within R (2) tiles of the criticality-weighted centre of its connections, as a move or a swap with an unclustered cell of the same type; kept when both tiles stay legal (isBelLocationValid) and the crit^E-weighted (E = 4) predicted delay of both cells' arcs drops. Arc model: LUT input 665/682 ps from its own slice/tile, LUT -> FF of its own position 0, between tiles 313 + 1.235 x delay matrix (the fit of docs/drafts/nextpnr-placer-delay-cal.md). P = 3 passes with timing re-analysed between them. rv_soc s1: 25 candidate cells, 28 + 9 + 8 moves; a wider setting (`dpl=3,4,0.5,3`, variant dp2w) moves 136-262 cells per pass but is not better in nextpnr's timer (rv_soc 93.1, rv_mul 86.6, rv_big 88.4, bram 131.4, mean of 3 seeds). Runtime: the pass was not timed on its own; total nextpnr time with it is within the run-to-run spread (table above; the machine is shared).
- nextpnr timer, mean of 3 seeds, dp1 -> dp2dp: rv_soc +1.2 %, rv_mul +3.5 %, rv_big +3.8 %, bram +3.4 %, eth +0.7 %.

### Correctness
- No-op: with the options off, dpl1 and dpl2 give FASM identical to dpl0 (rv_soc, bram, seed 1; `dpl_bench.py --noop`); with carry-di-bypass on the FASM differs (positive control).
- All 30 dp1 and dp2dp FASMs (5 designs x 3 seeds) assemble with fasm2frames (prjxray-db with the ICAP/DNA bits of install/patches).
- rv_soc dp1 s1 and dp2dp s1: bitstream decoded back to a netlist (fasm2bels) passes the firmware test bench 11/11 vectors (flow/dpl_check.sh -> flow/bit2netlist.sh). rv_mul/rv_big cannot be decoded (fasm2bels has no DSP_L tile; the same on dp0).

### Vivado-timed comparison and mixed placements
Seed 1 unless stated, Vivado routing and timer on each placement (flow/dpl_summary.py; rv_soc Fmax excludes the ICAP endpoint; HPWL in grid units, PIPs = Vivado's routed signal PIPs):

| placement | rv_soc Fmax | slices | HPWL | PIPs | bram Fmax | slices | HPWL | PIPs |
|---|---|---|---|---|---|---|---|---|
| Vivado places the yosys netlist (opt + place + route) | 157.63 | 398 | 17141 | 39688 | 170.88 | 290 | 21092 | 20771 |
| Vivado's slices at Vivado's positions through dpl_mix's legaliser (`vpack_vglob`, control) | 148.35 | 400 | 19249 | - | queued | | | |
| Vivado's slices at our dp0 positions (`vpack_nglob`) | 137.91 | 399 | 21475 | - | 145.82 | 299 | 30903 | - |
| our dp0 slices at Vivado's positions (`npack_vglob`) | 114.90 | 497 | 23061 | - | 147.58 | 369 | 25412 | 22517 |
| ours, dp0 (base) | 126.17 | 497 | 19875 | 43670 | 150.13 | 369 | 22327 | 22428 |
| ours, dp1 (carry-di-bypass) | 106.35 | 480 | 19266 | 43352 | 157.18 | 269 | 21079 | 22363 |
| ours, dp2dp (carry-di-bypass + dpl) | 109.45 | 481 | 19317 | 43978 | 155.35 | 267 | 21200 | 21942 |

rv_mul, seed 1: Vivado 111.27 MHz (551 slices), ours dp0 94.70 (716 slices).

Reading the mixes (rv_soc):
- The control loses 9.3 MHz against Vivado's own run (148.35 vs 157.63): imposing a placement without opt_design, the ~270 cells `place_cell` cannot take (LUTRAM macros, nextpnr-made cells) and the slice-level legaliser cost that much. Against the control, Vivado's packing at our global positions loses 10.4 MHz (137.91), and our own placement loses another 11.7 MHz (126.17). So on rv_soc **global placement and packing/detailed placement each account for about half** of the gap that is not imposition overhead.
- Our slices at Vivado's positions are worse than either (114.90; legaliser displacement 2.87 vs 1.49 grid units): our slices group cells that Vivado's placement keeps apart, so our packing is tied to our global placement and cannot be judged apart from it.
- bram: both mixes are worse than our own placement (Vivado's slices at our positions 145.82, ours at Vivado's 147.58, against 150.13), so on bram neither packing alone nor global placement alone explains the gap; the bram legaliser control was still queued at the stop.

The fixes under Vivado's timer, seeds 1-3 (Fmax per seed; mean; slices, HPWL and Vivado-routed PIPs are seed means):

| design | variant | Fmax per seed, MHz (Vivado timer) | mean | slices | HPWL | PIPs | Vivado route s |
|---|---|---|---|---|---|---|---|
| rv_soc (excl. ICAP) | Vivado's own placement | 157.63 (s1) | - | 398 | 17141 | 39688 | 34.6 |
| rv_soc | dp0 | 126.17 / 109.45 / 115.92 | 117.18 | 503 | 20004 | 43420 | 26.5 |
| rv_soc | dp1 | 106.35 / 114.77 / 115.92 | 112.35 | 462 | 19548 | 42900 | 24.2 |
| bram | Vivado's own placement | 170.88 (s1) | - | 290 | 21092 | 20771 | 39.6 |
| bram | dp0 | 150.13 / 147.28 / 150.63 | 149.35 | 341 | 22833 | 22228 | 39.6 |
| bram | dp1 | 157.18 / 154.44 / 145.71 | 152.44 | 287 | 21909 | 22041 | 39.4 |
| rv_mul | Vivado's own placement | 111.27 (s1) | - | 551 | 22151 | 46691 | 33.6 |
| rv_mul | dp0 | 94.70 / 107.98 / 103.64 | 102.11 | 710 | 23204 | 52116 | 26.3 |
| rv_mul | dp1 | 107.42 / 89.31 / 94.44 | 97.06 | 661 | 21419 | 50368 | 23.6 |

- carry-di-bypass is an **area and wirelength** gain on all three (slices -7 to -16 %, bram now 287 against Vivado's 290; HPWL -2 to -8 %; routed PIPs -1 to -3 %; Vivado's routing time equal or lower), and **Fmax-neutral within the seed spread** (mean -4.1 % rv_soc, +2.1 % bram, -4.9 % rv_mul, while single seeds move by up to 18 %). It does not close the Fmax gap.
- dpl (dp2dp), seed 1: rv_soc 109.45 (dp1 106.35), bram 155.35 (dp1 157.18); more seeds were still queued at the stop.
- The rv_soc seed-1 worst path (FF -> LUT2 -> 4 CARRY4 -> 2 LUT4 -> FDSE S) has the same cells in dp0 and dp1; in dp1 they are spread over SLICE_X30-45 / Y42-68 instead of X34-45 / Y69-82: a different global placement of the same path, not a slower carry.
- In the imposed placement an S LUT that nextpnr duplicated (`$S_DUP`, 9-11 per design in dp0 and dp1) is not in the yosys netlist, so Vivado drives that S input from the original LUT through a route-through; this penalises both variants alike.

### Round 2 (2026-11-07 morning): cluster moves that follow the global placement (`-o dpl=...,1`)
Change (docs/drafts/nextpnr-packing-dpl.patch, detail_place.cc): a 5th `dpl` field makes the detailed pass also move small LUT/FF clusters (a LUT and up to three flip-flops the packer tied to it) as one piece, to a free position near the criticality-weighted centre of the cluster's connections where `getClusterPlacement` is legal and both tiles stay valid; kept when the weighted predicted delay drops. With criticality floor 0 every unclustered cell and every such cluster is a candidate, so the slices are rebuilt around the global placement after legalisation. Without the 5th field the pass is unchanged; with no `dpl` at all the FASM is identical to the base (rebuilt dpl2, rv_soc and bram s1). Variant dp4 = carry-di-bypass + `dpl=2,2,0,1,1`. rv_soc s1: 1090 candidates, 725 + 356 moves; rv_soc dp4 s1 bitstream decodes and passes the firmware bench 11/11.

Vivado's timer, seeds 1-3 (means; Fmax per seed in brackets):

| design | variant | Fmax MHz | slices | HPWL | PIPs | Vivado route s | nextpnr s |
|---|---|---|---|---|---|---|---|
| rv_soc | dp1 | 112.35 | 462 | 19548 | 42900 | 24.2 | 63 |
| rv_soc | dp4 | 106.47 (106.37 / 106.37 / 106.66) | 440 | 19963 | 42402 | 22.8 | 31 |
| bram | dp1 | 152.44 | 287 | 21909 | 22041 | 39.4 | 25 |
| bram | dp4 | 146.26 (141.98 / 148.50 / 148.30) | 281 | 23852 | 22170 | 43.2 | 19 |
| rv_mul | dp1 | 97.06 | 661 | 21419 | 50368 | 23.6 | 67 |
| rv_mul | dp4 | 100.06 (106.86 / 93.74 / 99.58) | 609 | 21582 | 50168 | 25.0 | 33 |

- Area goes down again (slices -2 to -8 % against dp1; rv_mul 609 against Vivado's 551, rv_soc 440 against 398, bram 281 against 290), routed PIPs are equal or lower, but Fmax is not better: -5 % rv_soc, -4 % bram, +3 % rv_mul, all inside the seed spread except that rv_soc dp4 is consistently near 106.4 on all three seeds.
- So rebuilding the slices around the global placement with the current arc model does not move Vivado-timed Fmax. The model (the predict-cal fit) is what the moves optimise; with the global placement itself fixed, the critical paths keep their hop count (rv_soc worst-200 mean net delay 4.30 ns dp4 vs 4.17 dp1). This points the remaining gap back at global placement and at the delay model, not at slice composition.

### Round 3 (2026-11-08): re-timed with the fixed placement export, and carry-di-bypass as a default
The "placed" sources above came from qor_xtime.placement(), which stripped only the muxcy0 carry suffix, so part of every placement (rv_soc and rv_mul about 8-10 % of the cells, bram 1 %) was left to Vivado's placer. Fixed in efcb64f; all dp0/dp1 sources were re-prepared and re-timed into C:\Users\finnf\open-dfx-xc7-vivado\build\dpl_xtime2\ (flow/dpl_vivado.sh, flow/dpl_summary.py default to it). The earlier tables in this Finding (rounds 1-2, mixes, dp2dp, dp4) are from the old export and carry that bias.

Vivado's timer, same nextpnr run per seed (Fmax per seed; slices = Vivado's count of the imposed placement):

| design | dp0 (base) Fmax s1 / s2 / s3, mean | dp1 (carry-di-bypass) s1 / s2 / s3, mean | paired | slices dp0 -> dp1 (Vivado's own) |
|---|---|---|---|---|
| rv_soc (incl. ICAP) | 116.40 / 109.59 / 114.80, 113.60 | 120.39 / 113.66 / 115.01, 116.35 | +2.4 % | 499 -> 462 (398) |
| bram | 150.13 / 147.28 / 150.63, 149.35 | 157.18 / 154.44 / 145.71, 152.44 | +2.1 % | 341 -> 287 (290) |
| rv_mul | 98.53 / 102.00 / 99.56, 100.03 | 101.94 / 95.08 / 96.25, 97.76 | -2.2 % | 688 -> 646 (551) |
| rv_big | 100.55 / 98.88 / 93.10, 97.51 | 106.16 / 99.91 / 99.89, 101.99 | +4.6 % | 752 -> 687 (-) |
| eth (LiteX, 100 MHz) | 66.66 / 70.02 / 70.28, 68.99 | 67.02 / 74.43 / 65.46, 68.97 | 0.0 % | 3026 -> 2956 (-) |

- Mean over the four qor designs +1.7 % Fmax, eth 0.0 % (3 of 5 positive; rv_mul -2.2 % with single seeds from -6.8 to +3.5 %, inside its spread), slices -6 to -16 % (bram at Vivado's level, the CPUs still 12-17 % above it), Vivado routed PIPs equal or lower, Vivado route time equal.
- Safety checks for a default: (1) no-op on a design without carries: fir (no CARRY4 instance), dpl1 binary, `-o dsp-cascade-place`, seed 1: FASM identical with and without the option (build/qor/dpl/noop_fir); (2) off = base: dpl1/dpl2 without the option give FASM identical to dpl0 (rv_soc, bram); (3) rv_soc dp1 seeds 1, 2 and 3: bitstream decoded back to a netlist (fasm2bels) passes the firmware bench 11/11 each; all 15 dp1 FASMs assemble. rv_mul/rv_big cannot be decoded (no DSP_L in fasm2bels).
- **Superseded (2026-11-08 evening): the proposal is withdrawn.** The "placed" mode used above imposes only cells of the yosys netlist: it drops nextpnr's own cells (rv_soc dp0: 519 feed-through LUT1s, 100 split CARRY4s), leaves the LUTRAM register file (126 cells), 6 re-chunked CARRY4s and 32 refused cells to Vivado's placer, and lets Vivado re-assign LUT pins. flow/exact_src.py imports nextpnr's placement exactly (xroute netlist, LUTRAM macros, LUT pin locks; rv_soc dp0 s1: 2615 placed, 2 refused), and Vivado's timer then gives (Fmax excl. ICAP, dp0 -> dp1): rv_soc 103.48 -> 99.72 / 98.87 -> 97.22 / 100.45 -> 94.97 (-3.6 %, 3 of 3 seeds worse), bram 140.21 -> 142.01 / 137.14 -> 144.86 / 140.00 -> 135.65 (+1.3 %), rv_mul 87.05 -> 93.76 / 90.20 -> 85.86 / 90.28 -> 86.76 (-0.3 %), rv_big 92.61 -> 92.03 / 87.26 -> 88.17 / 88.98 -> 85.06 (-1.3 %); mean -1.0 %. Placed mode is optimistic by 7-21 % on seed 1 (rv_soc dp0 116.40 vs exact 103.48, dp1 120.39 vs 99.72, bram dp0 150.13 vs 140.21). carry-di-bypass stays opt-in (release patch 0031; ofx `carry_di_bypass = false`).
- **Proposal: make `-o carry-di-bypass` the default** (keep an `-o no-carry-di-bypass` escape): it is an area gain everywhere, Fmax-neutral to slightly positive under Vivado's timer on 12 paired runs, a no-op without carries, and functionally verified on rv_soc. eth (LiteX) is re-timed too: Fmax-neutral (0.0 %, slices -2 %). Still missing: a gate-level simulation of one DSP design (fasm2bels has no DSP_L).
- dp2dp (carry-di-bypass + dpl) re-timed the same way, seeds 1-3: rv_soc 117.73 / 118.19 / 111.00 (mean 115.64; dp1 116.35), bram 155.35 / 153.99 / 150.22 (153.19; dp1 152.44), rv_mul 100.25 / 95.08 / 96.34 (97.22; dp1 97.76). The detailed placer adds nothing measurable on top of carry-di-bypass.
- Side finding: fir with the static placer and without `-o dsp-cascade-place` spins in "Strict legalising 19 cells" (stopped after 17 min, dpl0 binary); pre-existing, unrelated to the option.

### What is open
- Vivado-timed dp2dp seeds 2-3, rv_big and eth, and the bram/rv_mul mix controls (queue order in build/qor/dpl/queue/names.txt; restart with `NAMES_FILE=... flow/dpl_queue.sh 1`).
- The QoR suite (flow/qor_suite.py quick mode) was not run on these variants.
- The detailed placer's arc model and candidate set are first guesses; under Vivado's timer it has not yet shown a gain (seed 1: rv_soc +3.1 MHz, bram -1.8 MHz against dp1).
- Two runs of this study briefly shared one Vivado slot (two workers' `mkdir` of the lock directory on /mnt/c both succeeded at the same second); the queue now runs one worker and serialises its acquisition.

## Finding 16 (2026-11-07): the router's share of the gap, and timing-driven router2 options (nextpnr draft `nextpnr-router-timing`)
Method (flow/route_xtime.py, vivado/build_rte.tcl, flow/route_cmp.py; CONFIG blocks, dry run by default):
- `vref`: Vivado 2025.2 places and routes the yosys netlist of the Finding 13 source builds (rv_soc, bram: `cal_static`; rv_mul, rv_big: `dspq_cal`, the `-pipeline` netlist) with default directives and **no opt_design**, so the netlist stays the one nextpnr reads. It dumps every primitive's LOC/BEL. Outputs C:\Users\finnf\open-dfx-xc7-vivado\build\rte\<d>_vref\ (slack.txt, timing.rpt, cells.txt, times.txt).
- `import`: Vivado's sites and BELs are mapped onto nextpnr's packed cell names (CARRY4 by the yosys cell of its first MUXCY, LUTRAM sub-cells by the macro's site and nextpnr's letter) and given to nextpnr as `-o place-import=FILE` (new, in the draft): cells are bound locked where the bel is free and the tile stays legal, carry chains as a whole at their root or not at all; the placer places the rest (nextpnr-made feed-through and duplicated LUTs, chains nextpnr cut differently). build/rte/import/<d>.place; per-run counts in build/rte/npr/<d>_vimp_*/nextpnr.log ("place-import:").
- `own`: the same nextpnr command as the source build (static placer, `-o hardblock-timing`, `-o dsp-cascade-place`, 5 ns), its own placement. Both chipdbs: `cal` (Finding 10 cell timing) and `rcal` (Finding 13 route calibration, timer within -8.4 / +5.4 % of Vivado on identical implementations).
- `export` / `vivado`: flow/xroute.py's export of a nextpnr run; Vivado imposes netlist, placement, LUT pins and every pip (`<name>`), or the identical placement with Vivado routing (`<name>_vr`). Each run writes WNS with and without ICAPE2 endpoints and startpoints (slack.txt) and the 200 worst non-ICAP paths with their pins plus every arc's slow-max delay, which flow/route_cmp.py compares path by path.
- All Fmax below exclude the ICAPE2 path (rv_soc and rv_mul contain one; it limits both tools to about 135 MHz and hides routing). Vivado Fmax = 1000 / (5 - WNS_noicap).

### Reference: Vivado on its own placement (Vivado timer, excl. ICAPE2)
| design | Vivado place+route of the yosys netlist, no opt_design | place / route s |
|---|---|---|
| rv_soc | 173.2 MHz (WNS_noicap -0.774) | 48 / 33 |
| rv_mul | 157.9 (-1.363) | 45 / 31 |
| rv_big | 166.7 (-0.999) | 63 / 36 |
| bram | 172.3 (-0.805) | 49 / 44 |

### nextpnr's router on Vivado's placement
nextpnr timer with the rcal chipdb (seed 1; `vimp`), against nextpnr on its own placement (`own`, mean of seeds 1-3, same timer):

| design | nextpnr route of Vivado's placement (rcal timer) | nextpnr on its own placement (rcal timer, mean s1-3) | Vivado on its own placement (Vivado timer) |
|---|---|---|---|
| rv_soc | 103.92 | 99.13 | 173.2 |
| rv_mul | 102.16 | 87.15 | 157.9 |
| rv_big | 104.13 | 90.40 | 166.7 |
| bram | 131.87 | 125.40 | 172.3 |

- Import fidelity: 1908 (rv_soc), 2387 (rv_mul), 2758 (rv_big) and 1517 (bram) cells bound at Vivado's bel; 35 / 76 / 85 / 9 carry chains could not sit at Vivado's root (nextpnr cuts chains where an intermediate CO is used and duplicates S-driving LUTs, so the chain or one of its LUTs collides with a Vivado cell) and were placed by nextpnr's placer, as were nextpnr's own feed-through LUTs. The placement is therefore Vivado's for most cells but not all.
- **Routing share (nextpnr timer, not yet Vivado's):** on (mostly) Vivado's placement nextpnr's router reaches 103.9 / 102.2 / 104.1 / 131.9 MHz where Vivado's router reaches 173.2 / 157.9 / 166.7 / 172.3 MHz (Vivado timer) on the exact placement. Read naively that is a 25-40 % routing loss, but it mixes two timers (nextpnr rcal vs Vivado, rcal was -8.4 / +5.4 % from Vivado on identical CPU implementations in Finding 13) and the import's displaced chains. The identical-placement Vivado runs that separate router from import (`<d>_vimp_cal_s1` with nextpnr's pips, `<d>_vimp_cal_s1_vr` with Vivado's) are exported (C:\Users\finnf\open-dfx-xc7-vivado\designs\rte\) and queued, but no Vivado slot was free between 22:00 and 01:30, so they did not run. Placement explains the rest of the gap: nextpnr on its own placement is a further 2-15 % below nextpnr on Vivado's (rcal timer).

### Router options (draft; nextpnr timer with rcal chipdb, own placement, paired mean of seeds 1-3)
Each variant is compared seed by seed with the same seed's base run (same placement: the router runs after placement and the placer does not see these options). Router2 seconds are means over the seeds on a shared, loaded machine (indicative).

| variant (`--router2-opt`) | rv_soc | rv_mul | rv_big | bram | router2 s (base: 24.9 / 22.0 / 17.6 / 9.9) |
|---|---|---|---|---|---|
| base | 99.13 | 87.15 | 90.40 | 125.40 | |
| `critSeedDelay=1` + `critRipupIters=3` (keep-best) | 102.99 (+4.0 %) | 92.05 (+5.7 %) | 92.27 (+2.1 %) | 130.72 (+4.3 %) | 21.6 / 14.8 / 10.8 / 8.2 |
| `critSeedDelay=2` + `critRipupIters=3` | 103.92 (+4.9 %) | 91.32 (+4.8 %) | 93.05 (+2.9 %) | 129.62 (+3.4 %) | 20.7 / 21.2 / 12.8 / 10.6 |
| `critSeedDelay=1` + `critRipupIters=5` | 103.11 (+4.1 %) | 92.05 (+5.7 %) | 92.27 (+2.1 %) | 131.32 (+4.8 %) | 22.5 / 19.5 / 17.6 / 10.9 |
| `critSeedDelay=1` only | 98.84 (-0.1 %) | 91.46 (+5.0 %) | 92.21 (+2.0 %) | 129.72 (+3.5 %) | 20.0 / 15.5 / 8.6 / 7.7 |
| `critRipupIters=3` (keep-best) | 102.38 (+3.4 %) | 88.79 (+1.9 %) | 92.28 (+2.1 %) | 127.72 (+1.8 %) | 21.7 / 17.5 / 11.9 / 7.6 |
| `critRipupIters=3`, no keep-best (first version) | 101.84 (+2.9 %) | 88.56 (+1.6 %) | 92.28 (+2.1 %) | 127.67 (+1.8 %) | 25.8 / 25.5 / 14.3 / 8.8 |
| `critRipupIters=3 critRipupResetCong=0` | 101.28 (+2.3 %) | 88.87 (+2.0 %) | 92.31 (+2.1 %) | 128.65 (+2.6 %) | 19.8 / 14.3 / 10.7 / 7.9 |
| `critExp=8 critFloor=0.01` | 96.33 (-2.8 %) | 88.91 (+2.0 %) | 90.63 (+0.3 %) | 128.31 (+2.3 %) | |
| `critEstWeight=1.0` (A* weight 1 for critical arcs) | 100.45 (+1.4 %) | 87.31 (+0.2 %) | 89.68 (-0.8 %) | 126.53 (+0.9 %) | |

On Vivado's placement (seed 1, rcal timer): `critSeedDelay=1` + `critRipupIters=3` 110.94 / 103.16 / 107.98 / 135.35 against 103.92 / 102.16 / 104.13 / 131.87 (+6.8 / +1.0 / +3.7 / +2.6 %).

- What the two options fix: (1) router2 seeds an arc's forward search with every wire of the net's existing tree near the sink at cost 0, so a critical arc branches off whatever tree is there, whatever that tree's delay from the source; `critSeedDelay` charges a seed its routed delay from the source times the arc's criticality. (2) router2 stops as soon as routing is legal, with criticalities from the pre-route estimate; `critRipupIters` re-routes the critical nets with the routed criticalities and keeps the best legal routing. Neither costs router time on these designs (router2 seconds equal or lower; the machine was shared, so only large changes would show). Vivado's timer does not confirm the gain (next section).
- Rip-up of only the critical arcs of a net (instead of the whole net) tripped router2's tree reconstruction (`cursor_bwd == src_wire_idx`, router2.cc) on rv_big and bram; the draft rips the whole net, as `--tmg-ripup` does.
- Not worth keeping: a steeper criticality curve (`critExp=8`), a lower A* weight for critical arcs (`critEstWeight=1`): within seed noise or worse.
- The calibrated routing delays in the router (`rcal` chipdb) are the larger lever by the global-placement agent's measurement (same nextpnr placement, 3 seeds, Vivado routes vs nextpnr routes, Finding 15 work): nextpnr's routes are 15-20 % slower than Vivado's (rv_soc 99.1 vs 117.2 MHz, bram 125.4 vs 149.4, eth 57.1 vs 69.0). The same comparison in this harness (`<d>_own_cal_s1` and `_vr`, and the rcal runs with `--no-vr`) is exported and queued, not run.

### Vivado's timer on the router options (same placement per seed; 2026-11-07)
`critSeedDelay=1` + `critRipupIters=3` against the base router, rcal chipdb, own placement: per seed the two runs share the placement (the options act after placement), and each implementation is imposed on Vivado pip for pip (`<d>_own_rcal_s<n>`, `<d>_own_sd1crk3_rcal_s<n>`, C:\Users\finnf\open-dfx-xc7-vivado\build\rte\). Vivado timer, Fmax excluding ICAPE2; nextpnr's own claim (rcal timer) in brackets. 85-234 nets per run could not take their ROUTE property whole and were completed by `route_design -preserve` (route_log.txt "partial"); the counts are within a few nets of each other in each pair.

| design | per seed: base -> options (Vivado timer) | mean base | mean options | paired mean |
|---|---|---|---|---|
| rv_soc | s1: 101.40 -> 96.57 (-4.8 %; nextpnr 103.48 -> 106.92)<br>s2: 92.83 -> 98.83 (+6.5 %; nextpnr 99.99 -> 101.57)<br>s3: 97.85 -> 96.08 (-1.8 %; nextpnr 93.93 -> 100.47) | 97.36 | 97.16 | -0.0 % (n=3) |
| rv_mul | s1: 94.61 -> 97.25 (+2.8 %; nextpnr 86.63 -> 90.16)<br>s2: 94.70 -> 95.29 (+0.6 %; nextpnr 90.40 -> 94.71)<br>s3: 85.09 -> 92.38 (+8.6 %; nextpnr 84.42 -> 91.29) | 91.47 | 94.97 | +4.0 % (n=3) |
| rv_big | s1: 83.29 -> 76.69 (-7.9 %; nextpnr 87.80 -> 91.37)<br>s2: 91.18 -> 93.08 (+2.1 %; nextpnr 93.25 -> 95.41)<br>s3: 90.98 -> 97.65 (+7.3 %; nextpnr 90.16 -> 90.04) | 88.49 | 89.14 | +0.5 % (n=3) |
| bram | s1: 135.45 -> 135.45 (+0.0 %; nextpnr 128.53 -> 131.96)<br>s2: 132.54 -> 136.00 (+2.6 %; nextpnr 125.16 -> 131.16)<br>s3: 127.02 -> 135.67 (+6.8 %; nextpnr 122.52 -> 129.03) | 131.67 | 135.70 | +3.1 % (n=3) |

- **Under Vivado's timer the gain is smaller and not consistent.** nextpnr's rcal timer predicted +2 to +6 % for these options; Vivado measures rv_soc -0.0 % (n=3), rv_mul +4.0 % (n=3), rv_big +0.5 % (n=3), bram +3.1 % (n=3). The per-seed changes go both ways (rv_soc -4.8 / +6.5 / -1.8 %, rv_big -7.9 / +2.1 / +7.3 %) and are smaller than the seed-to-seed spread of the base itself (rv_soc 92.8-101.4, rv_big 83.3-91.2 MHz). rv_mul (+2.8 / +0.6 / +8.6 %) and bram (+0.0 / +2.6 / +6.8 %) are not worse on any seed, so the options may help the DSP and BRAM designs; three seeds are not enough to tell that from noise. Mean over the four designs +1.9 %.
- Why: the router options trade routes by nextpnr's delay model, and the rcal model is right on average (base runs: nextpnr claim vs Vivado within -8.4 to +7.7 %, e.g. rv_soc 103.48 / 101.40, rv_mul 86.63 / 94.61, bram 128.53 / 135.45) but not per route; a 4 % change predicted by that model is inside its error. One worst path checked net by net (rv_soc s1, flow/route_cmp.py-style per-pin delays): the same 9-level path, two of its nets 120 and 334 ps slower in Vivado's timing after the options moved them.
- The base runs reproduce earlier Vivado numbers exactly where the implementation is the same (rv_mul s1 94.61 and rv_big s1 83.29 MHz, as Finding 13's rcal runs), so the harness is consistent.
- Conclusion: keep the options opt-in and off for now; they cost no router time, and Vivado shows no loss on average (+1.9 %) but no clear gain either (rv_soc -0.0 %, rv_big +0.5 %). A router change has to be judged by Vivado's timer (or a model that is right per route), not by nextpnr's.

### Router share on the identical placement, and where nextpnr's routes lose (2026-11-08)
**Correction (2026-11-08 evening): the `_vr` runs below keep nextpnr's LUT input pins locked (lockpins.txt), so the "router share" in this section excludes pin assignment.** With the same placement and Vivado free to re-assign LUT pins (place_design "Re-assign LUT pins", source `rv_soc_p5_dp0_s1_exact_nolock`, flow/exact_src.py with an empty lockpins.txt), rv_soc s1 reaches 119.6 MHz (WNS -3.359) against 103.48 with our pins and 101.40 with our pins and routes: **routing plus pin choice is worth +17-18 % on rv_soc s1**, back in the 15-20 % range. Per-LUT-arc dumps (vivado/build_rte.tcl RTE_LUT_ARCS=1, both runs): Vivado's intrinsic LUT delay (0.124 vs ~0.355 ns) is the same arc by arc in both runs, i.e. not pin-dependent; the gain is net delay. Vivado puts 170 LUTs with 5 or fewer inputs on A6 (nextpnr's chipdb only permutes A1-A5; A6 is reserved for a sixth input), and those 263 arcs get 442 ps shorter on average; on the 200 worst paths 18 arcs moved to A6 save 7.3 ns and 113 arcs moved among A1-A5 save 226 ps each, unchanged pins 0. Worst-100 paths: net 5.54 -> 4.82 ns, logic 2.49 -> 2.08 ns (a different path set). Follow-up: A6 permutation and criticality-aware pin choice in router2 (docs/wip/router.md).

Method: the `<d>_own_rcal_s<n>` exports (nextpnr placement imposed exactly by flow/xroute.py; this harness does not use qor_xtime.placement, so the 2026-11-08 cell-miss bug of the place_xtime runs does not apply) are timed twice by Vivado: with nextpnr's pips imposed and with Vivado routing the same placement (`_vr`). vivado/build_rte.tcl with RTE_ROUTE_DUMP=1 (flow/rte_dump_vivado.sh, C:\Users\finnf\open-dfx-xc7-vivado\build\rte_arcs\) also dumps every routed net as node pairs, and flow/route_arcs.py compares the two routings arc by arc (Vivado slow-max arc delays).

| design (seed 1) | nextpnr's routes (Vivado timer) | Vivado's routes, same placement (Vivado timer) | router share |
|---|---|---|---|
| rv_soc | 101.40 MHz (WNS_noicap -4.862) | 103.48 (-4.664) | +2.0 % |
| rv_mul | 94.61 (-5.570) | 100.22 (-4.978) | +5.9 % |
| rv_big | 83.29 (-7.006) | 93.04 (-5.748) | +11.7 % |
| bram | 135.45 (-2.383) | 140.21 (-2.132) | +3.5 % |

- Seeds 2-3 (same method, Vivado timer, nextpnr's routes -> Vivado's routes on the same placement): rv_soc 92.83 -> 98.87 (+6.5 %), 97.85 -> 100.45 (+2.7 %); rv_mul 94.70 -> 96.29 (+1.7 %), 85.09 -> 92.48 (+8.7 %); rv_big 91.18 -> 92.34 (+1.3 %), 90.98 -> 91.94 (+1.0 %); bram 132.54 -> 137.14 (+3.5 %), 127.02 -> 140.00 (+10.2 %). Mean over 3 seeds: rv_soc +3.7 %, rv_mul +5.4 %, rv_big +4.7 %, bram +5.7 %; **all 12 runs +4.9 %**.
- On the exact placement the router costs 2-12 % (seed 1 mean +5.8 %, 3-seed mean +4.9 %), not the 15-20 % estimated earlier from place_xtime imports (those left part of the cells to Vivado's placer, see the qor_xtime fix efcb64f).
- Where the delay goes (arcs on the 200 worst paths of either routing, Vivado timer): arcs of the same shape cost the same (rv_soc -13 ps, bram +4, rv_big -18, rv_mul -9 ps per arc). The losses are in arcs that pass **through an unused LUT** (IMUX -> LUT input -> LUT -> LOGIC_OUTS): rv_soc 45 such arcs carry 41.8 of the 55.6 ns total excess, rv_mul 29 arcs 13.5 ns (more than its 11.3 ns total excess); rv_big 1 arc (on its worst path, +643 ps), bram none. Vivado's own routing uses no LUT route-through on any of the four. The chipdb times these pseudo-pips as SITE_NULL (free; the rcal class adds -56 ps), so the router sees a shortcut where Vivado's timer charges a LUT delay and a new exit (a class fit over 50277 Vivado-timed arcs gives about +2.1 ns per route-through arc, rms 354 ps; indicative only).
- Second, smaller pattern: long lines (LV18/LH12) and hexes for short hops on rv_big and bram (rv_big worst path +629 ps on one such arc; bram's worst arc +413 ps over LV18/LH12/LV18/LH12). Load: per-branch cost in the fit is about 6 ps, fanout about 1 ps per load, so a load-aware router cost has little to gain under Vivado's timer.
- Draft change: `-o no-lut-routethru` (docs/drafts/nextpnr-router-timing.patch, binary build/nextpnr-build/rte-nrt): LUT_ROUTETHRU pips unavailable to the router; read in preRoute, so the placement per seed is unchanged and runs pair with the base. Off: FASM identical to the base on rv_soc, rv_mul, rv_big, bram (s1).

Vivado's timer on `-o no-lut-routethru` (rcal chipdb, own placement, same placement per seed as the base, nextpnr's pips imposed; Fmax excl. ICAPE2; TNS_noicap in ns; router2 seconds from nextpnr's log on a shared machine):

| design | per seed: base -> no-lut-routethru (Vivado timer) | mean base -> option | paired mean |
|---|---|---|---|
| rv_soc | s1 101.40 -> 98.85 (-2.5 %), s2 92.83 -> 95.83 (+3.2 %), s3 97.85 -> 102.97 (+5.2 %) | 97.36 -> 99.22 | +2.0 % |
| rv_mul | s1 94.61 -> 92.59 (-2.1 %), s2 94.70 -> 97.48 (+2.9 %), s3 85.09 -> 88.89 (+4.5 %) | 91.47 -> 92.99 | +1.8 % |
| rv_big | s1 83.29 -> 88.59 (+6.4 %), s2 91.18 -> 90.11 (-1.2 %), s3 90.98 -> 92.90 (+2.1 %) | 88.49 -> 90.53 | +2.4 % |
| bram | s1 135.45 -> 133.62 (-1.3 %), s2 132.54 -> 136.97 (+3.3 %), s3 127.02 -> 120.53 (-5.1 %) | 131.67 -> 130.37 | -1.0 % |

- The three CPUs (which use route-throughs on their critical arcs) gain +1.8 to +2.4 % (n=3 each, 2 of 3 seeds positive on each); bram (no route-through among its critical arcs) moves -1.0 %, i.e. noise. Mean over the four designs +1.3 %, about the same as `critSeedDelay=1` + `critRipupIters=3` (+1.9 %) and, like it, inside the seed spread of single runs. TNS_noicap moves both ways (rv_soc s1 -1546 -> -1402, rv_mul s2 -2612 -> -2334, rv_big s3 -2536 -> -2578). router2 time is lower on 9 of 12 runs (e.g. rv_soc 25.1 -> 13.9 s, rv_mul 19.2 -> 12.1 s): the route-throughs were negotiated detours.
- Why the gain is smaller than the 75 % share of the excess suggests: the route-through arcs sit mostly on high-fanout control nets (FF R/CE pins) of the 200 worst paths, not on the single worst path; once they are gone, the worst path is decided by the remaining per-arc routing noise (the same 9-level path moves by +-250 ps per arc between runs). The remaining router share (2-12 % on seed 1) is spread over many arcs by a few hundred ps each.
- Decision: keep it opt-in (no-op off, verified); a candidate default for the CPU designs once a few more seeds and the LiteX designs confirm it. It costs no runtime.

### No-op and cost
- Without the options the draft binary gives FASM identical (sorted, comments dropped) to the release binary on rv_soc, rv_mul, rv_big and bram (build/rte/noop/).
- Runtime: see the router2 column; the Vivado reference spends 31-44 s routing these designs, nextpnr's router2 8-33 s.

### Open
- The identical-placement router-share runs (`<d>_vimp_cal_s1` and `_vr`, `<d>_own_cal_s1` and `_vr`) are exported but not run; the Vivado time went to the option check above.
- Import fidelity: carry chains nextpnr cuts differently and its duplicated S LUTs keep 9-85 chains per design off Vivado's sites; a packer mode that keeps yosys' CARRY4 boundaries would make the import exact.
- High-fanout and load-dependent delays (Vivado's RC model) are not in nextpnr's router cost; Finding 13 left 0.6-0.7 ns of per-path optimism on the CPUs unexplained, which a load-aware cost for critical arcs might address.
- Defaults: the options stay opt-in and off (no Vivado-confirmed gain, previous section).

## nextpnr builds (build/nextpnr-build/, all ce3f7c18 + drafts, cmake flags of docs/buildenv.md, -j4)
- `qor`: + nextpnr-hardblock-timing.patch (worktree build/src/nextpnr-qor). Log build/nextpnr-build/qor.build.log.
- `qorfix`: + G1/G3/G8 gapfix drafts + hardblock-timing (build/src/nextpnr-qorfix).
- `rkcrit`: router-region branch (e62fafd1) + nextpnr-router-keepout-crit.patch (build/src/nextpnr-rkcrit).
- `qordsp`: `qorfix` + nextpnr-dsp-cascade-place.patch; its gen/xilinx_gen.py also carries nextpnr-cell-timing-cal.patch (build/src/nextpnr-qordsp, log build/nextpnr-build/qordsp.build3.log).
- yosys: build/src/yosys-dspqor = 3718f7f13 + yosys-xilinx-dsp-pipeline.patch; plugin build/yosys-plugin/xilinx_dsp_qor, full build build/yosys-build/yosys-dspqor/yosys.
- `place_ref`: `ofx` series (install/patches/nextpnr) + nextpnr-hardblock-timing.patch (worktree build/src/nextpnr-place, changes staged, not committed). `place_v1`..`place_v4`: the same + nextpnr-placer-tuning.patch at successive stages (v4 = the draft). Log build/nextpnr-build/place.build.log. The only warning is the pre-existing xilinx.cc sign-compare.
- `qorarea` (Finding 12): `qordsp` + nextpnr-muxf-const-inputs.patch + nextpnr-area-pack.patch (build/src/nextpnr-qorarea, logs build/nextpnr-build/qorarea.build*.log). yosys: build/src/yosys-area = 3718f7f13 + yosys-xilinx-area-opts.patch, full build build/yosys-build/yosys-area/yosys (log build/yosys-build/yosys-area.build.log).
- Each prints only the pre-existing xilinx.cc sign-compare warning.

<!-- qor_bench:main:begin -->

**blinky @ 10 ns (100.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 393.86 (Vivado) | 393.86 | 1 + 0 mem | 28 | 7 | 0.0 | 0 | 86.30 |
| openXC7 base | 372.58 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 7.40 |
| openXC7 tmg | 372.58 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 9.10 |
| openXC7 fix_static | 375.94 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 8.70 |
| openXC7 fix_static_auto | 375.94 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 8.50 |

**blinky @ 7 ns (142.9 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 393.86 (Vivado) | 393.86 | 1 + 0 mem | 28 | 7 | 0.0 | 0 | 73.40 |
| openXC7 base | 372.58 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 7.30 |
| openXC7 tmg | 372.58 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 8.90 |
| openXC7 fix_static | 375.94 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 9.00 |
| openXC7 fix_static_auto | 375.94 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 8.20 |

**blinky @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 393.86 (Vivado) | 393.86 | 1 + 0 mem | 28 | 7 | 0.0 | 0 | 79.80 |
| openXC7 base | 372.58 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 7.50 |
| openXC7 tmg | 372.58 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 8.90 |
| openXC7 fix_static | 375.94 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 16.50 |
| openXC7 fix_static_auto | 375.94 (nextpnr) | - | 0 / 56 | 28 | 7 | 0.00 | 0 | 8.20 |

**rv_soc @ 10 ns (100.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 134.72 (Vivado) | 138.05 | 935 + 50 mem | 771 | 63 | 2.0 | 0 | 95.50 |
| openXC7 base | 140.90 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 38.00 |
| openXC7 tmg | 134.07 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 28.70 |
| openXC7 fix_static | 134.19 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 36.00 |
| openXC7 fix_static_auto | 134.19 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 36.30 |

**rv_soc @ 7 ns (142.9 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 135.78 (Vivado) | 152.25 | 940 + 50 mem | 771 | 63 | 2.0 | 0 | 110.10 |
| openXC7 base | 140.90 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 49.80 |
| openXC7 tmg | 134.07 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 32.30 |
| openXC7 fix_static | 134.19 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 37.70 |
| openXC7 fix_static_auto (best of 8, seed 6; median 135.29, worst 134.19) | 138.29 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 240.00 |

**rv_soc @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 135.83 (Vivado) | 171.00 | 991 + 50 mem | 771 | 63 | 2.0 | 0 | 204.80 |
| openXC7 base | 140.90 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 41.00 |
| openXC7 tmg | 134.07 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 30.00 |
| openXC7 fix_static | 134.19 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 37.10 |
| openXC7 fix_static_auto (best of 8, seed 6; median 135.29, worst 134.19) | 138.29 (nextpnr) | - | 1057 / 1748 | 764 | 92 | 2.00 | 0 | 273.60 |

**rv_mul @ 10 ns (100.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 127.60 (Vivado) | 136.31 | 1378 + 50 mem | 1018 | 123 | 2.0 | 4 | 148.70 |
| openXC7 base | 149.43 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 47.00 |
| openXC7 tmg | 90.57 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 32.40 |
| openXC7 fix_static | 104.90 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 35.90 |
| openXC7 fix_static_auto | 104.90 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 37.90 |

**rv_mul @ 7 ns (142.9 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 135.78 (Vivado) | 145.41 | 1386 + 50 mem | 1018 | 123 | 2.0 | 4 | 233.20 |
| openXC7 base | 149.43 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 46.40 |
| openXC7 tmg | 90.57 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 31.50 |
| openXC7 fix_static | 104.90 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 33.60 |
| openXC7 fix_static_auto (best of 8, seed 5; median 102.49, worst 100.57) | 107.08 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 269.90 |

**rv_mul @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 135.78 (Vivado) | 172.35 | 1433 + 50 mem | 1065 | 123 | 2.0 | 4 | 215.90 |
| openXC7 base | 149.43 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 45.60 |
| openXC7 tmg | 90.57 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 31.90 |
| openXC7 fix_static | 104.90 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 32.40 |
| openXC7 fix_static_auto (best of 8, seed 5; median 102.49, worst 100.57) | 107.08 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 281.10 |

**rv_big @ 10 ns (100.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 137.42 (Vivado) | 137.42 | 1457 + 50 mem | 1098 | 123 | 16.0 | 4 | 143.80 |
| openXC7 base | 112.85 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 43.60 |
| openXC7 tmg | 93.06 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 44.00 |
| openXC7 fix_static | 102.33 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 45.10 |
| openXC7 fix_static_auto | 102.33 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 48.60 |

**rv_big @ 7 ns (142.9 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 153.21 (Vivado) | 153.21 | 1461 + 50 mem | 1098 | 123 | 16.0 | 4 | 173.10 |
| openXC7 base | 112.85 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 43.10 |
| openXC7 tmg | 93.06 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 41.80 |
| openXC7 fix_static | 102.33 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 47.40 |
| openXC7 fix_static_auto (best of 8, seed 3; median 104.24, worst 102.24) | 106.36 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 249.90 |

**rv_big @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 178.73 (Vivado) | 178.73 | 1504 + 50 mem | 1159 | 123 | 16.0 | 4 | 202.60 |
| openXC7 base | 112.85 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 41.00 |
| openXC7 tmg | 93.06 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 40.90 |
| openXC7 fix_static | 102.33 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 53.10 |
| openXC7 fix_static_auto (best of 8, seed 3; median 104.24, worst 102.24) | 106.36 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 259.00 |

**fir @ 10 ns (100.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 100.99 (Vivado) | 100.99 | 18 + 2 mem | 598 | - | 0.0 | 32 | 92.50 |

**fir @ 7 ns (142.9 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 144.15 (Vivado) | 144.15 | 18 + 2 mem | 598 | - | 0.0 | 32 | 115.30 |

**fir @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 203.09 (Vivado) | 203.09 | 18 + 2 mem | 598 | - | 0.0 | 32 | 95.50 |

**bram @ 10 ns (100.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 143.29 (Vivado) | 143.29 | 549 + 1 mem | 509 | 80 | 24.0 | 0 | 93.80 |
| openXC7 base | 238.78 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 26.20 |
| openXC7 tmg | 112.11 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 20.60 |
| openXC7 fix_static | 150.99 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 26.90 |
| openXC7 fix_static_auto | 150.99 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 28.10 |

**bram @ 7 ns (142.9 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 153.47 (Vivado) | 153.47 | 564 + 1 mem | 509 | 80 | 24.0 | 0 | 103.80 |
| openXC7 base | 238.78 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 35.90 |
| openXC7 tmg | 112.11 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 20.10 |
| openXC7 fix_static | 150.99 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 26.90 |
| openXC7 fix_static_auto | 150.99 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 28.40 |

**bram @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 173.73 (Vivado) | 173.73 | 799 + 1 mem | 509 | 80 | 24.0 | 0 | 190.80 |
| openXC7 base | 238.78 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 29.60 |
| openXC7 tmg | 112.11 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 21.10 |
| openXC7 fix_static | 150.99 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 27.20 |
| openXC7 fix_static_auto (best of 8, seed 8; median 150.76, worst 135.06) | 155.45 (nextpnr) | - | 854 / 1370 | 494 | 98 | 24.00 | 0 | 181.30 |
<!-- qor_bench:main:end -->

## Finding 17 (2026-11-08): global placement -- target density, criticality against a slack quantile, re-timed baselines (nextpnr draft `nextpnr-placer-density`)
Method:
- nextpnr: worktree build/src/nextpnr-place, builds place_v12-v16 (docs/drafts/nextpnr-placer-density.{patch,md}; every
  option off by default, `.frames` identical to place_v11 / the `ref` binary with them off). Stub chipdb, `--placer static
  -o hardblock-timing`, 5 ns, seeds 1-3. rv_mul uses the `-pipeline` (dspq) netlist as in Finding 16.
- Vivado's timer: our placement imposed (vivado/build_xtime.tcl, "placed" mode), Vivado places what it cannot take and routes.
  flow/place_vivado.sh + flow/place_vqueue.sh; output C:\Users\finnf\open-dfx-xc7-vivado\build\place_xtime2. Each run
  also dumps cells and the 1000 worst paths; "hops" = mean Manhattan grid hops along the 100 worst Vivado paths in that
  placement (flow/place_diag.py metric). Table: flow/place_summary.py.
- **Corrected extraction.** Until 2026-11-08 `qor_xtime.placement()` imposed only the `muxcy0` part of nextpnr's
  CARRY4 names, so the other carry chunks were left to Vivado, and nextpnr-only cells (carry DI feed-through LUTs) were
  sent to place_cell. It now uses flow/qor_suite.py's rule (efcb64f). Every earlier Vivado-timed "our placement" number
  of Findings 13/15/16 and docs/wip/placement-global.md that went through it is biased. Corrected stub baseline:
  rv_soc 112.56 (was 116.81), bram 155.87 (unchanged: bram's carries were never split, identical placement and
  result), rv_big 102.32 (was 104.95). With the fix about 60 of 1966 rv_soc rows still fail in place_cell (FFs on a bel
  next to an imposed carry: COUTMUX contention or bel occupied), against 582 of 2503 refused before.

Changes measured:
- `tu10`: anchored start (`--placer-static-anchor-init 20 --placer-static-ip-wait 0.5`, Finding 13 round 3) plus target
  utilisation 1.0 (`--placer-static-target-util 1.0`): spacers fill the device, so the cells sit at full density
  (elfPlace's target density) instead of 70 %.
- `cq02`: `--placer-static-crit-quantile 0.02` (new). nextpnr's criticality is 1 - (slack - worst) / -worst; on rv_soc and
  rv_mul the worst path is the ICAPE2 path (5.2 ns clock-to-out under hardblock-timing), so every logic path gets a low
  criticality and the global placer's net weight 1 + 5 crit^2 stays near 1 on the paths Vivado finds critical. With the
  option the static placer's analyser measures against the slack at the 2 % quantile of the port slacks.
- `cdb`: `-o carry-di-bypass` (Finding 15).

Vivado timer, Fmax per seed and mean, MHz; HPWL after legalisation and slices from nextpnr; hops on Vivado's 100 worst
paths; nextpnr seconds (shared machine):

| design | variant | Vivado Fmax per seed | mean | vs base | HPWL | slices | sd_x / sd_y | worst-100 hops | nextpnr s |
|---|---|---|---|---|---|---|---|---|---|
| rv_soc | base (stub, corrected) | 115.34 / 112.56 / 109.77 | 112.56 | | 17363 | 492 | 9.2 / 13.2 | 49.5 | 42 |
| rv_soc | tu10 + cq02 | 115.79 / 107.50 / 104.72 | 109.34 | -2.9 % | 16932 | 438 | 10.1 / 7.9 | 42.3 | 32 |
| rv_soc | tu10 + cq02 + cdb | 126.94 / 116.66 / 117.74 | **120.45** | **+7.0 %** | 17349 | 388 (Vivado 398) | 10.2 / 6.7 | 37.5 | 34 |
| bram | base | 155.09 / 155.40 / 157.13 | 155.87 | | 22485 | 323 | 16.4 / 18.2 | 19.1 | 27 |
| bram | tu10 + cq02 | 154.30 / 158.98 / 153.14 | 155.47 | -0.3 % | 20953 | 321 | 23.9 / 15.2 | 21.5 | 25 |
| bram | tu10 + cq02 + cdb | 144.26 / 148.63 / 151.86 | 148.25 | -4.9 % | 20080 | 287 (Vivado 290) | 7.1 / 14.4 | 23.0 | 25 |
| rv_big | base | 106.02 / 92.17 / 108.78 | 102.32 | | 25539 | 748 | 14.6 / 9.8 | 38.7 | 33 |
| rv_big | tu10 + cq02 | 104.23 / 95.37 / 97.78 | 99.13 | -3.1 % | 23218 | 668 | 13.0 / 9.9 | 33.8 | 32 |
| rv_big | tu10 + cq02 + cdb | 93.64 / 93.97 / 102.69 | 96.77 | -5.4 % | 21769 | 605 | 10.5 / 9.2 | 40.2 | 31 |
| rv_mul | base (dspq) | 112.54 / 105.90 / 100.12 | 106.19 | | 26733 | 633 | 12.4 / 12.2 | 65.3 | 39 |
| rv_mul | tu10 + cq02 (dspq) | 115.33 / 118.84 / 115.55 | **116.57** | **+9.8 %** | 21055 | 651 | 15.5 / 8.7 | 43.0 | 43 |

Reading:
- **The two ICAP designs gain, the others do not** (but see the ablations below: on rv_mul the target density, not cq02, carries the gain). rv_mul +9.8 % with every seed above the base's best seed, worst-path
  hops 65.3 -> 43.0 and HPWL -21 %; rv_soc +7.0 % with carry-di-bypass (two of three seeds above the base's best),
  hops 49.5 -> 37.5. That is where the criticality fix applies (the ICAPE2 path is their worst path). bram and rv_big
  have no ICAP; there the target density alone shortens HPWL (-7 / -9 %) and slices (rv_big -11 %) but Fmax is
  -0.3 % / -3.1 %, inside or near the seed spread (rv_big base 92-109).
- carry-di-bypass helps rv_soc (+10 % over tu10 + cq02) and costs bram and rv_big (-5 %, -2 %), the same mixed sign as
  Finding 15 had; area always drops (rv_soc 388 slices against Vivado's 398, bram 287 against 290).
- The worst-path hops fall where Fmax rises, but not one for one: rv_soc tu10 + cq02 shortens them (49.5 -> 42.3) and is
  still -2.9 %; on bram they grow a little (19.1 -> 21.5). Hops are a symptom, not the whole cause.
- The gap to Vivado placing these designs itself stays large: Finding 16 measured Vivado on its own placement (no opt_design, Vivado timer, ICAP excluded) at rv_soc 173.2, rv_mul 157.9, rv_big 166.7, bram 172.3 MHz. Those builds used the cal netlists of Finding 13, not exactly this run's netlist, so read it as the order of the gap (rv_soc 120 vs 173, rv_mul 117 vs 158), not a ratio. In these runs the ICAPE2 is not Vivado's worst path (Fmax with and without it are equal).
- Not separated yet: on rv_mul, how much comes from tu10 and how much from cq02 (runs pl15_tu10_dq, pl15_cq02_dq queued),
  and cq02 alone on the stub designs (pl15_cq02_stub). Queued too: the path-based refinement `-o dpl=2,3,0.8,4,0,0.02`
  (the detailed placer with the same quantile; it saw only 25 critical cells on rv_soc before, 53 with it).

Path-based refinement (`-o dpl=2,3,0.8,4,0,0.02`, the detailed placer with the same criticality quantile, place_v16),
Vivado timer, mean of seeds: rv_soc 108.68 (tu10 + cq02: 109.34), with cdb 118.18 (120.45); bram 154.98 (155.47),
with cdb 148.08 (148.25); rv_big 99.80 on 2 seeds (99.13). No gain: dropped.

What else differs from Vivado's own placement (flow/place_paths.py on the dumps, 100 worst paths, Vivado timer; Vivado's
"free" dump runs opt_design, ours do not):

| dump | worst slack ns | datapath ns | logic ns | net ns | levels (LUT / CARRY4) | hops | net ps per step | steps in one slice | LUT->FF in one slice |
|---|---|---|---|---|---|---|---|---|---|
| rv_soc, Vivado's own (fix_static_free) | -2.352 | 5.77 | 3.10 | 2.66 | 6.3 (4.2 / 0.2) | 28.2 | 498 | 23 % | 54 % |
| rv_soc, base s1 | -3.670 | 7.26 | 2.65 | 4.61 | 7.8 (5.6 / 0.2) | 52.2 | 679 | 21 % | 41 % |
| rv_soc, base s2 | -3.884 | 7.01 | 2.80 | 4.21 | 7.6 (4.5 / 1.1) | 38.7 | 639 | 23 % | 45 % |
| rv_soc, tu10 + cq02 + cdb s1 | -2.878 | 6.87 | 2.89 | 3.98 | 7.2 (4.6 / 0.6) | 32.1 | 640 | 29 % | 45 % |
| rv_soc, tu10 + cq02 + cdb s2 | -3.572 | 7.11 | 2.48 | 4.62 | 7.5 (5.3 / 0.2) | 43.1 | 710 | 23 % | 43 % |
| bram, Vivado's own | -0.852 | 5.47 | 4.05 | 1.42 | 10.7 (1.0 / 7.7) | 13.8 | 147 | 18 % | - |
| bram, base s1 | -1.448 | 5.97 | 3.96 | 2.00 | 9.5 (1.0 / 6.5) | 20.9 | 237 | 11 % | - |
| bram, tu10 + cq02 s1 | -1.481 | 6.01 | 3.99 | 2.03 | 9.9 (1.3 / 6.6) | 18.4 | 227 | 15 % | - |

- The gap is in the nets, not the cells: logic delay per path is equal or lower in ours (rv_soc 2.5-2.9 vs 3.10 ns),
  net delay is 1.5-2 ns higher (4.0-4.6 vs 2.66 ns; bram 2.0 vs 1.42).
- Per connection, Vivado's critical nets are shorter (5.3 grid hops per step against 5.6-7.7) and faster (498 ps against
  640-710 ps per step); the delay per hop is about the same (88-124 vs 94 ps). So it is distance, not routing quality per
  unit of distance: the worst paths' cells still sit further apart.
- Our worst paths have more LUT levels (rv_soc 7.2-7.8 vs 6.3 cells). Vivado's reference ran opt_design, which can merge
  LUTs, so part of this is netlist, not placement.
- LUT->FF steps on the worst paths share a slice 41-45 % in ours against 54 % in Vivado's. **Checked: not a pairing
  problem.** Every split step is a LUT driving a flip-flop's CE or R pin (its D comes from another LUT, which nextpnr
  does put in the same slice). By endpoint pin (100 worst paths, Vivado timer): Vivado's own rv_soc has 57 D / 38 CE /
  3 R endpoints, ours 39-43 D / 34-40 CE / 19-21 R. Ending at D, Vivado's paths carry 1.70 ns of net delay and ours
  3.4-3.9 ns with the last step in the same slice, so the stretch is upstream in the logic cone; ending at CE, 4.09 vs
  4.95-5.18 ns. rv_mul base: 38 D (4.19 ns net) / 45 CE (6.04) / 15 R (5.13).
- Carry chains are not the problem (adjacent CARRY4 steps 100 % in ours, 80-94 % in Vivado's).
- Next lever from this: critical-connection distance. The earlier timing-weight tests (`--placer-static-timingweight` 20,
  Finding 13) ran with the ICAP-flattened criticality, so they say nothing; tu10 + cq02 + timing weight 15 was measured (ablation table: no gain), and the
  DREAMPlaceFPGA-style arc term with the quantile criticality is the next run.

### Ablations (2026-11-08 12:45; Vivado timer, mean of seeds 1-3, corrected extraction)
"anc" = anchored start + ip-wait; "tu10" = anc + target utilisation 1.0; ra = `-o static-ram-assign`; tw15 =
`--placer-static-timingweight 15`.

| variant | rv_soc | bram | rv_big | rv_mul (dspq) |
|---|---|---|---|---|
| base | 112.56 | 155.87 | 102.32 | 106.19 |
| cq02 alone | 108.85 (-3.3 %) | 152.85 (-1.9 %) | 95.20 (-7.0 %) | 110.03 (+3.6 %) |
| anc | 114.85 (+2.0 %) | 152.93 (-1.9 %) | 88.28 (-13.7 %) | - |
| tu10 | 114.53 (+1.8 %) | 154.82 (-0.7 %) | - | 116.63 (+9.8 %) |
| anc + ra | 114.16 | 151.84 | 95.88 | - |
| tu10 + ra | 110.98 | 157.26 (+0.9 %) | 94.36 | - |
| tu10 + cdb | 113.34 | 150.46 | 94.05 | 106.81 |
| tu10 + cq02 | 109.34 | 155.47 | 99.13 | 116.57 |
| tu10 + cq02 + tw15 | 113.25 | 157.61 (+1.1 %) | 98.92 | 108.91 |
| tu10 + cq02 + cdb | **120.45 (+7.0 %)** | 148.25 | 96.77 | 113.56 |
| tu10 + cq02 + tw15 + cdb | 118.31 | - | 90.63 | - |
| tu10 + cq02 + dpl quantile | 108.68 | 154.98 | 99.80 (2 seeds) | 116.13 |

Correction to the reading above: **on rv_mul the gain comes from the target density, not from cq02** (tu10 alone
116.63, tu10 + cq02 116.57, cq02 alone 110.03). cq02 alone loses on rv_soc, bram and rv_big. The rv_soc +7.0 % appears
only in the combination tu10 + cq02 + cdb; tu10 + cdb (113.34) and tu10 + cq02 (109.34) do not show it, and rv_soc's
seed-to-seed spread on one variant is up to 12 MHz (104.7-115.8), so with three seeds that result is not separable from
noise. The anchored start costs rv_big 13.7 %, and nothing here beats rv_big's base.
- No variant wins on all four designs. The one consistent result is **target density on rv_mul** (all three seeds
  110.9-121.7 against the base's 100.1-112.5). Next: target density without the anchored start (`pl15_tuonly_*`), since
  anchoring is what hurts rv_big; and more seeds before any default.
- The ICAP-flattening explanation for cq02 stands as a mechanism (criticalities were compressed), but Vivado's timer does
  not show it as a Fmax lever on its own.

Target density without the anchored start (`--placer-static-target-util 1.0` only; Vivado timer, seeds 1-3):

| design | base | target util 1.0 | + cq02 | HPWL base -> tu | slices base -> tu | nextpnr s base -> tu |
|---|---|---|---|---|---|---|
| rv_soc | 112.56 | 112.98 (113.65 / 111.46 / 113.83) | 115.15 | 17363 -> 15320 (-12 %) | 492 -> 473 | 42 -> 28 |
| bram | 155.87 | 155.87 (158.83 / 155.71 / 153.07) | 152.86 | 22485 -> 21637 (-4 %) | 323 -> 316 | 27 -> 20 |
| rv_big | 102.32 | 100.05 (102.52 / 99.63 / 97.99) | 99.37 | 25539 -> 24394 (-4 %) | 748 -> 666 (-11 %) | 33 -> 26 |
| rv_mul (dspq) | 106.19 | 109.91 (121.11 / 98.55 / 110.08) | 107.53 | 26733 -> 25491 (-5 %) | 633 -> 572 (-10 %) | 39 -> 29 |

- Target utilisation 1.0 alone is Fmax-neutral within the seed spread (+0.4 / 0.0 / -2.2 / +3.5 %) and gives
  4-12 % less HPWL, 2-11 % fewer slices and 20-33 % less nextpnr time on all four designs. That makes it the candidate
  for a default (area, wirelength and build time better, Fmax not worse), to be confirmed on the QoR suite.
- The rv_mul +9.8 % needs the anchored start together with it (tu10), and the anchored start costs rv_big 13.7 %.
  A design-dependent switch would need a rule that predicts it; none is in hand.

### Re-timed with the exact import (2026-11-08 evening; supersedes the placed-mode Fmax above)
flow/exact_src.py + vivado/build_rte.tcl "fixed" mode: our netlist, placement and LUT pins imposed, Vivado only
routes (Vivado timer; build/exact and build/exact_sa). Placed mode was optimistic by 10-14 % on the bases. Both
compare placements with nextpnr's LUT pins locked (same pin policy for all rows). Reference, Vivado placing the same
exact netlists (vref, no opt_design): rv_soc 136.0, bram 164.1, rv_big 110.9 MHz.

| variant | rv_soc | bram | rv_big | rv_mul (dspq) |
|---|---|---|---|---|
| base | 101.39 / 103.35 / 100.22 -> **101.65** | 139.12 / 145.90 / 144.36 -> **143.13** | 88.75 / 85.91 / 90.88 -> **88.51** | 103.09 / 94.95 / 95.02 -> **97.69** |
| target util 1.0 | 100.20 (-1.4 %) | 143.68 (+0.4 %) | 85.43 (-3.5 %) | 99.04 (+1.4 %) |
| tu10 (anchored + target util 1.0) | 101.78 (+0.1 %) | 143.69 (+0.4 %) | pending | **106.33 (+8.8 %; 104.29 / 104.29 / 110.40)** |
| tu10 + cq02 + cdb | 103.01 (+1.3 %) | 138.99 (-2.9 %) | 90.72 (+2.5 %) | 104.57 (+7.0 %) |

- The one result that holds on the exact yardstick is **tu10 on rv_mul: +8.8 %, every seed above the base's best seed**,
  as in placed mode (+9.8 %). The worst-100 hops fall from 70.3 (target util alone) to 52.2.
- Everything else is within the seed spread. rv_soc's placed-mode +7.0 % for tu10 + cq02 + cdb shrinks to +1.3 %.
- Target util 1.0 alone stays Fmax-neutral within noise (-3.5 to +1.4 %) with less HPWL, fewer slices and less run
  time; rv_big -3.5 % is the largest move, with that design's seed spread at 5 MHz.
- Our best rows remain 25-35 % below Vivado on the same netlists (rv_soc 103 vs 136, bram 144 vs 164, rv_big 91 vs 111).

Conclusion so far: keep all options opt-in. A design-aware choice is suggested by the data (crit-quantile where a hard
block dominates the worst slack), but a default needs the ablation runs and the QoR suite.

## Summary: what closed, what is open, why
Best openXC7 result per design at 5 ns against Vivado at 5 ns, each with its own timer, plus Vivado's timer on the openXC7 placement where measured:

| design | Vivado (Vivado timer) | openXC7 before: nightly, heap, blind timer (nextpnr timer) | openXC7 now: hardblock-timing + static placer, best of 8 (nextpnr timer) | openXC7 static placement, seed 1, Vivado routing + timer | runtime openXC7 now / Vivado, s |
|---|---|---|---|---|---|
| blinky | 393.86 | 372.58 | 375.94 | 358.29 | 8 / 80 |
| rv_soc | 135.83 (171.00 excl. ICAP) | 140.90 (ICAP and BRAM36 untimed) | 138.29 (ICAP path); 145.62 excl. ICAP | 121.36 | 274 (8 seeds) / 205 |
| rv_mul | 135.78 (172.35 excl. ICAP) | 149.43 (DSP untimed) | 107.08; with yosys -pipeline 140.13 (Finding 8) | 93.15; with -pipeline 112.69, + calibrated chipdb 121.82 | 281 / 216 |
| rv_big | 178.73 | 112.85 (DSP, BRAM36 untimed) | 106.36; with yosys -pipeline 143.12 | 106.25; with -pipeline 109.09, + calibrated chipdb 110.95 | 259 / 203 |
| bram | 173.73 | 238.78 (BRAM36 untimed) | 155.45 | 155.09 | 181 / 191 |
| fir | 203.09 | does not place | places with -o dsp-cascade-place: 234.41 (heap), 209.69 (static) (Finding 9) | 203.05 (static, default yosys netlist) | 25 / 96 |

Closed or improved:
- nextpnr now times ICAPE2, DSP48E1 and RAMB36 (opt-in). With it, nextpnr's Fmax for the ICAP-bound rv_soc agrees with Vivado's (134.07-134.19 vs 134.72-135.83).
- Vivado-timed Fmax of openXC7 placements up 3-34 % with `--placer static` (and bram-place); best-of-N on top.
- DFX keep-out cost: 141.16 -> 149.34 MHz (no keep-out 152.09) with 55 instead of 958 static pips in the region; all RMs route, 15/15 pr_check.
- Runtime: a single openXC7 run is 8-53 s against Vivado's 73-233 s; best-of-8 is about the same as one Vivado run.

Open, with the reason:
- **Synthesis of wide multipliers (rv_mul, rv_big):** mostly closed by yosys `-pipeline` (Finding 8): Vivado on the yosys netlist 111 -> 159 (rv_mul excl. ICAP) and 157 (rv_big) MHz against 172-179 on its own netlist; rv_big is now limited by a RAMB36 read path, the multiplier path is at about 177 MHz. Opt-in draft, not upstream.
- **Placement quality:** even the static placer's result, timed by Vivado, is 23 % (rv_soc, 121.4 vs 157.6) and 9 % (bram, 155.1 vs 170.9) below Vivado placing the same yosys netlist.
  - Finding 11: Vivado packs denser (rv_soc 398 vs 501 slices) and flatter, and nextpnr's critical paths are about twice as long in hop distance.
  - Ten opt-in placer options were tried (docs/drafts/nextpnr-placer-tuning.patch); the best moves rv_soc's mean by +3 % (stub chipdb only), and none helps bram, rv_big, DDR or eth.
  - Period-aware criticality is worse on bram and rv_big.
  - On the LiteX SoCs (DDR WNS -1.9, eth -4.3 to -5.2 ns at 100 MHz) the static placer is not better than the heap placer under Vivado's timer.
  - nextpnr's interconnect estimate is about 30 % below Vivado's on eth's critical path, so the placer optimises an optimistic cost; routing-delay calibration is the next lever.
- **FIR (32-DSP PCIN cascade):** fixed by `-o dsp-cascade-place` (Finding 9): chains could not cross a clock-region (HCLK/BRKH) row. Opt-in draft.
- **`-widemux 5`:** the placement failure is fixed (MUXF8 with a constant input, docs/drafts/nextpnr-muxf-const-inputs; Finding 12), but the `-widemux 5` netlist fails the rv_soc firmware test in netlist and bitstream simulation, and the formal check leaves `reg_pc`/`reg_next_pc` unproven, so it stays off for correctness. Root cause not established.
- **Area (Finding 12):**
  - Counted post-route with Vivado's rule, yosys's LUT *cells* equal Vivado's on the CPUs (rv_soc 1107 vs 1106). The older "+7 %" compared cells without INV against Vivado's sites.
  - The LUT-site gap is packing: Vivado combines LUTs into O5/O6 sites, and nextpnr spends LUT1s on carry feed-throughs. The CARRY4 gap is unshared adders and small adders.
  - Opt-in drafts (nextpnr `carry-di-bypass`, `lut-pair`; yosys `-share_aggressive`, `-carry_minwidth`) bring rv_soc to 1078 vs 1041 LUT sites and 64 vs 63 CARRY4. rv_mul/rv_big end below Vivado (1442/1478 vs 1483/1554 sites, 98 vs 123 CARRY4); arty_ddr3 4931 vs 4340 sites and 163 vs 178 CARRY4.
  - Cost: 1-3.5 % median nextpnr Fmax on the CPUs (bram +7 %), and 10-13 % on the LiteX SoCs for one seed.
  - Still open: LiteX LUTRAM (320 vs 142 sites: a 256-deep memory in RAM256X1S instead of block RAM), bram's three-operand adders (98 vs 80 CARRY4), FIR FFs without `-dsp_pipeline`, control sets.
- **Timer:** nextpnr's LUT and FF models are optimistic against Vivado (LUT 0.10-0.125 vs 0.12-0.35 ns, FF clk->Q 0.35 vs 0.456 ns). A Vivado-measured chipdb (Finding 10) cuts the mean error of nextpnr's Fmax claim against Vivado's timer on the same placement from 9.6 % to 6.3 % (6 designs), still optimistic on the CPU designs; Vivado's LUT delay is per input and route-dependent (0.12 or 0.30 ns), which per-pin cell arcs cannot express. A timer-only comparison on identical routes (FIXED_ROUTE) was not done.
- **The clock constraint does not drive nextpnr's effort** (Finding 2); only the flow-level seed loop does.
- Nothing ran on hardware. The rkcrit90 DFX builds passed pr_check only (no native_check.sh / region2v / SAT run).

## Files
- flow/qor_bench.py, flow/qor_summary.py, flow/qor_xtime.py, flow/dfx_keepout_cost.py (new); vivado/run_qor.ps1, vivado/build_xtime.tcl (new); flow/build_pr_native.py (variant `rkcrit90` added).
- designs/qor/qor_rv_big, qor_fir, qor_bram (new RTL).
- docs/drafts/nextpnr-hardblock-timing.patch, docs/drafts/nextpnr-router-keepout-crit.patch.
- Finding 12: flow/qor_area.py, flow/qor_area_litex.py, flow/qor_area_equiv.sh, flow/qor_area_sim.sh (new); flow/qor_bench.py (variants area_*, dcp_wm5, nextpnr build `qorarea`, `yosys` field); flow/gap_build.py (`synth_opts` tool key, default unchanged); flow/bit2netlist.sh (qor_rv_soc/rv_mul/rv_big entries); docs/drafts/nextpnr-area-pack.{patch,md}, nextpnr-muxf-const-inputs.{patch,md}, yosys-xilinx-area-opts.{patch,md}. Results build/qor/area/ (area_*.json/md, yexp, equiv, sim, sim_wm5, b2n, litex, run_*.log), build/qor/oxc7/area_*, dcp_wm5.
- Finding 11: flow/place_bench.py, flow/place_compare.py, vivado/place_dump.tcl (new); docs/drafts/nextpnr-placer-tuning.{patch,md}; results build/qor/place/ (run*.log, table_*.md, compare/, noop_rvppa/), build/qor/oxc7/pl*/, C:/Users/finnf/open-dfx-xc7-vivado/build/place_xtime and build/place_dump.
- Results: build/qor/ (src, synth, oxc7, xtime, dfx, run_*.log, table_*.md); Vivado: C:/Users/finnf/open-dfx-xc7-vivado/build/qor and build/qor_xtime.
- 2026-11-06 (Findings 8-10): docs/drafts/yosys-xilinx-dsp-pipeline.{patch,md}, nextpnr-dsp-cascade-place.{patch,md}, nextpnr-cell-timing-cal.{patch,md}; flow/qor_bench.py (variants dspq*, dcp*, cal_static, nextpnr builds qordsp/qordsp_cal, `plugin` field); flow/vivado_cell_timing.py, vivado/build_arcs.tcl (new); toolchain/buildenv/build_yosys_dsp_plugin.sh, build_yosys_full.sh (new), gen_chipdb.sh (META, GEN_ARGS; defaults unchanged). Results: build/qor/dsp (explore, sim, run_pnr_*.log), build/chipdb-cal, Vivado build/qor_xtime (*dspq*, *dcp*, *cal*) and build/qor_arcs{,2,3,4}.
- Table of every nextpnr run of Findings 8-10 (5 ns; Vivado row = Vivado's own synthesis and P&R):

<!-- qor_bench:dsp:begin -->

**rv_mul @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 135.78 (Vivado) | 172.35 | 1433 + 50 mem | 1065 | 123 | 2.0 | 4 | 215.90 |
| openXC7 fix_static | 104.90 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 32.40 |
| openXC7 fix_static_s8 (best of 8, seed 5; median 102.49, worst 100.57) | 107.08 (nextpnr) | - | 1397 / 2443 | 1073 | 148 | 2.00 | 4 | 252.30 |
| openXC7 dspq | 137.84 (nextpnr) | - | 1422 / 2474 | 1011 | 148 | 2.00 | 4 | 41.80 |
| openXC7 dspq_s8 (best of 8, seed 6; median 134.78, worst 124.91) | 140.13 (nextpnr) | - | 1422 / 2474 | 1011 | 148 | 2.00 | 4 | 292.90 |
| openXC7 dspq_heap | 130.80 (nextpnr) | - | 1422 / 2474 | 1011 | 148 | 2.00 | 4 | 41.30 |
| openXC7 dspq_dcp | 137.84 (nextpnr) | - | 1422 / 2474 | 1011 | 148 | 2.00 | 4 | 40.70 |
| openXC7 dspq_cal | 132.96 (nextpnr) | - | 1422 / 2474 | 1011 | 148 | 2.00 | 4 | 42.60 |

**rv_big @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 178.73 (Vivado) | 178.73 | 1504 + 50 mem | 1159 | 123 | 16.0 | 4 | 202.60 |
| openXC7 fix_static | 102.33 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 53.10 |
| openXC7 fix_static_s8 (best of 8, seed 3; median 104.24, worst 102.24) | 106.36 (nextpnr) | - | 1448 / 2494 | 1108 | 148 | 16.00 | 4 | 243.60 |
| openXC7 dspq | 125.69 (nextpnr) | - | 1463 / 2515 | 1046 | 148 | 16.00 | 4 | 53.70 |
| openXC7 dspq_s8 (best of 8, seed 2; median 128.07, worst 116.89) | 143.12 (nextpnr) | - | 1463 / 2515 | 1046 | 148 | 16.00 | 4 | 273.40 |
| openXC7 dspq_heap | 116.41 (nextpnr) | - | 1463 / 2515 | 1046 | 148 | 16.00 | 4 | 50.50 |
| openXC7 dspq_dcp | 125.69 (nextpnr) | - | 1463 / 2515 | 1046 | 148 | 16.00 | 4 | 48.10 |
| openXC7 dspq_cal | 124.18 (nextpnr) | - | 1463 / 2515 | 1046 | 148 | 16.00 | 4 | 54.10 |

**fir @ 5 ns (200.0 MHz)**

| flow | Fmax MHz (timer) | Vivado Fmax excl. ICAP | LUTs (yosys / nextpnr bels; Vivado logic + mem) | FF | CARRY4 | BRAM36 | DSP | runtime s |
|---|---|---|---|---|---|---|---|---|
| Vivado | 203.09 (Vivado) | 203.09 | 18 + 2 mem | 598 | - | 0.0 | 32 | 95.50 |
| openXC7 dcp_heap | 234.41 (nextpnr) | - | 22 / 25 | 1589 | 0 | 0.00 | 32 | 21.40 |
| openXC7 dcp_static | 209.69 (nextpnr) | - | 22 / 25 | 1589 | 0 | 0.00 | 32 | 25.00 |
| openXC7 dspq_dcp | 198.65 (nextpnr) | - | 22 / 57 | 597 | 0 | 0.00 | 32 | 22.70 |
| openXC7 dspq_dcp_s8 (best of 8, seed 8; median 199.24, worst 191.09) | 209.69 (nextpnr) | - | 22 / 57 | 597 | 0 | 0.00 | 32 | 141.20 |
| openXC7 dspq_cal | 214.73 (nextpnr) | - | 22 / 57 | 597 | 0 | 0.00 | 32 | 21.50 |
<!-- qor_bench:dsp:end -->
