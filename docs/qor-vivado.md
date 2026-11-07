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
