# Timing reports: `ofx timing` against Vivado (2026-11-06)

`ofx timing` (ofx/timing.py) prints a report in the layout of Vivado's `report_timing_summary`, plus the parts of
`check_timing`, `report_timing`, `report_clock_interaction`, `report_cdc` and `report_pulse_width` that the data
supports. This document records how it compares with Vivado 2025.2 on the same placed design, what was fixed, and
what is still missing.

**Timers.** Every slack in this document names its timer. "nextpnr" = nextpnr-himbaechel's timer (one corner, the
openXC7 chipdb delays, `--report-paths 10` from docs/drafts/nextpnr-timing-report.patch). "Vivado" = the Vivado
2025.2 timer (slow and fast corners, xc7a35tcsg324-1, speed file -1 PRODUCTION 1.23). "ofx model" = the pulse
width checks ofx computes from the clock periods and the requirement table. The timers differ (docs/qor-vivado.md
Findings 3 and 10), so slacks are not expected to agree; the comparison is about the report: which endpoints,
which checks, which order, which categories.

## Method

1. `flow/timing_report_check.py --out build/timing_rv --run` places and routes each netlist with the `timrep`
   nextpnr (and with `xdc2` for the no-op check) through ofx/npwait.sh. For every design the FASM with
   `--report-paths 10` is identical to xdc2's and the report JSON is identical in all old keys
   (build/timing_rv/noop.json; the 10 designs added today all pass: x_cdc_none, x_cdc_groups, x_cdc_fpclk,
   x_cdc_maxdly, x_async_rtl, x_async_none, x_iodly_minmax, x_mmcm_groups, x_gen_div, and x_iodly_partial =
   x_iodly_minmax with only `-max` input and only `-min` output delays, designs/timing/x_iodly_partial.xdc).
2. The same script writes Vivado sources (build/timing_rv/xtime/src): the yosys netlist as EDIF, the XDC, and our
   placement (LOC/BEL of every cell, fixed).
3. `vivado/run_qor.ps1 -Tag timing_xtime2 -Script build_xtime.tcl -SrcRel build\timing_rv\xtime\src -Run`:
   Vivado reads the netlist and XDC, places the fixed cells where nextpnr put them, routes (Vivado's router), then
   writes report_timing_summary (plain and `-max_paths 10 -report_unconstrained -check_timing_verbose`),
   report_timing setup and hold, every setup and hold endpoint (`get_timing_paths -unique_pins`),
   check_timing -verbose, report_clock_interaction, report_pulse_width (worst and `-all`), report_cdc and
   report_methodology. timing_xtime2 = the 7 designs below plus the DFX module build (all rc 0, 539 s);
   timing_xtime3 = the 10 new designs plus x_gen_none, x_mmcm_none, x_iodly again (all rc 0, 538 s).
4. `flow/timing_vivado_compare.py` reads both and writes build/timing_rv/compare.json; `--pulse-table` checks
   the pulse width table in ofx/timing.py against every pulse width report Vivado wrote.

Same placement, **not the same routes**: Vivado routes our placement itself. Loading our routes as FIXED_ROUTE
exists only in the route-calibration flow (vivado/build_xroute.tcl, workstream 1) and still leaves routing errors
on the CPU designs (rv_mul: 294 of 2603 routable nets with errors), so it was not used here.

## Report structure: what agrees now

| item | ofx before | ofx now | Vivado | result |
|---|---|---|---|---|
| check_timing items | 8, own order | Vivado's 12 in Vivado's order, then 4 marked [ofx] | 12 | 11 of 12 counts equal on 20 of the 21 compared runs (x_gen_div: see below); `pulse_width_clock` printed as "-" (not computed). no_input/no_output_delay now skip unused inputs and constant-driven outputs as Vivado does (x_async_rtl was 4/4 vs Vivado 1/1, now 1/1) |
| Design Timing Summary | WNS/TNS/WHS/THS | + WPWS/TPWS with pulse width endpoint counts | the same 12 columns | pulse width endpoint totals equal on 18 of 21 runs (rv_soc 880 = 880, dfx_rv_pr_xor_n 900 = 900, x_mmcm_none 31 = 31); rv_mul 1192 vs 1189, rv_mul_hb 1192 vs 1205, x_gen_div (artefact, below); WPWS equal on all 21 (CPUs -5.000 = -5.000: ICAPE2/CLK needs 10 ns, the clock is 5 ns) |
| Clock Summary | flat | generated clocks indented under their master; MMCM/PLL outputs without endpoints derived (feedback clock `fb`) | the same | x_mmcm_none: clk, c1_mmcm, c2_mmcm, fb = Vivado |
| Intra Clock Table | setup/hold | + pulse width; clocks with only pulse width checks (clk, fb) | the same | x_mmcm_none: every per-clock count equal (setup 16/4; pulse width 1/18/10/2) and every WPWS equal (3.000/4.500/2.000/8.751 ns) |
| Other Path Groups | absent | printed; nextpnr has no recovery/removal, so it says how many async set/reset pins would be in `**async_default**` | table | gap, see below |
| Timing Details | the N worst paths overall | one block per path group in Vivado's order (intra in Clock Summary order, then inter, including untimed crossings with "NA"): Setup/Hold/PW summary lines, N Max Delay and N Min Delay paths, Pulse Width Checks per clock | the same | group list identical on 16 of the 18 same-placement runs (x_mmcm_none: clk, c1_mmcm, c2_mmcm, fb, c1_mmcm -> c2_mmcm); x_cdc_maxdly: Vivado lists clk_a -> clk_b twice; x_gen_div: see below |
| path header | source/destination pins | + "(rising edge-triggered cell FDRE clocked by c1_mmcm {rise@0.000ns fall@5.000ns period=10.000ns})", requirement as an edge difference, logic/route %, Logic Levels by cell type ("5 (CARRY4=4 LUT2=1)", equal to Vivado's line for the same x_mmcm_none path) | the same | |
| names | nextpnr cell/bel pin (`.../SR`, `.../DPR3_1/WA1`) | Vivado cell/pin (`.../R`, `.../RAMD_D1/WADR0`) from X_ORIG_PORT and the LUTRAM macro | | rv_soc endpoint names in common 1307 -> 2118 of 2386 |
| hold | only with `--hold` | always, as Vivado; `--hold` is still accepted | always | |
| clock interaction | Inter Clock Table only | report_clock_interaction-like table (edges, WNS, TNS, endpoints, WNS requirement, Inter-Clock Constraints in Vivado's words) | | constraint class equal on every pair of every run (Timed, Asynchronous Groups, False Path, Max Delay Datapath Only) except unrelated clocks (x_cdc_none: Vivado "Timed (unsafe)", nextpnr does not time them) |
| CDC | none | report_cdc-like table: severity, CDC type (Safely Timed / User Ignored / No Common Primary Clock), exceptions, Safe (ASYNC_REG capture fed directly by a FF), Unsafe (ASYNC_REG capture behind logic), Unknown (no ASYNC_REG) | | equal to report_cdc in every column on all 6 crossing pairs (x_mmcm_none, x_mmcm_groups, x_cdc_none, x_cdc_groups, x_cdc_fpclk, x_cdc_maxdly) |
| ofx extras | | 13 ignored_constraints, 14 unrelated_clocks, 15 async_pins_untimed, 16 sequential_cells_untimed | not in Vivado | 16 finds SRLs that nextpnr does not time (x_async_none: 0 endpoints, one SRL16E) |

Pulse width requirements: ofx/timing.py CONFIG `pulse_width` holds the "Required" values Vivado prints for speed
grade -1 (FDRE/C high and low 0.500 ns, BUFG/I min period 2.155 ns, MMCME2_ADV/CLKIN1 min period 1.249, max period
100.000, pulse 2.000 ns, MMCM outputs max period 213.360 ns, RAMD32/CLK pulse 1.250, SRL16E/CLK pulse 0.980,
ICAPE2/CLK min period 10.000, PLLE2, XADC, IDELAYCTRL, ISERDES/OSERDES, FIFO). `timing_vivado_compare.py
--pulse-table` read every -1 pulse width report under C:\Users\finnf\open-dfx-xc7-vivado\build (31 lib pins): 29
match exactly; RAMB36E1/CLKARDCLK (2.576-3.361 ns seen) and DSP48E1/CLK (2.545-3.884) depend on the block's mode,
and ofx uses the largest value seen (pessimistic; marked `mode_dependent`). The clock of each pin comes from walking the routed
netlist from the nextpnr clock nets and the XDC clock ports through IBUF/BUFG/BUFGCTRL/BUFH, and out of MMCM/PLL
outputs (period from CLKIN1, DIVCLK_DIVIDE, CLKFBOUT_MULT_F and CLKOUTn_DIVIDE).

## Endpoints, ordering, slack (same placement, Vivado's own routes)

Endpoints are counted once each with their worst slack, as Vivado counts them. "common" = the endpoint has the
same Vivado-style name in both. Delta = nextpnr slack minus Vivado slack on common endpoints (positive: nextpnr is
optimistic). Spearman = rank correlation of the slacks of the common endpoints (ordering agreement). "Shared" =
how many of the 10 (100) worst setup endpoints of one timer are among the 10 (100) worst of the other.

| design | setup endpoints nextpnr / Vivado (common) | hold endpoints | pulse width endpoints ofx / Vivado | WNS nextpnr / Vivado (ns) | WHS nextpnr / Vivado | WPWS ofx model / Vivado | setup delta mean | Spearman setup / hold | shared top 10 / top 100 |
|---|---|---|---|---|---|---|---|---|---|
| x_gen_none | 1 / 1 (1) | 1 / 1 | 2 / 2 | 9.024 / 7.977 | 0.596 / 0.619 | 4.500 / 4.500 | +1.047 | - | - |
| x_mmcm_none | 24 / 24 (24) | 24 / 24 | 31 / 31 | -0.844 / -1.887 | 0.398 / 0.184 | 2.000 / 2.000 | +0.624 | 0.999 / 0.149 | 10 / - |
| x_iodly | 20 / 20 (20) | 20 / 20 | 13 / 13 | -7.824 / -8.852 | 1.502 / 0.735 | 4.500 / 4.500 | +1.163 | 0.959 / 0.994 | 10 / - |
| rv_soc | 2268 / 2386 (2118) | same | 880 / 880 | -2.097 / -4.158 | 0.398 / 0.057 | -5.000 / -5.000 | +1.279 | 0.914 / 0.752 | 0 / 55 |
| rv_soc_hb (`-o hardblock-timing`) | 2384 / 2386 (2214) | same | 880 / 880 | -2.459 / -4.347 | 0.359 / 0.037 | -5.000 / -5.000 | +1.307 | 0.941 / 0.818 | 0 / 56 |
| rv_mul | 2781 / 3035 (2631) | same | 1192 / 1189 | -1.692 / -6.822 | 0.398 / 0.026 | -5.000 / -5.000 | +1.666 | 0.885 / 0.712 | 0 / 33 |
| rv_mul_hb | 3033 / 3068 (2791) | same | 1192 / 1205 | -6.041 / -7.420 | 0.373 / 0.060 | -5.000 / -5.000 | +1.242 | 0.932 / 0.767 | 10 / 86 |
| dfx_rv_pr_xor_n (DFX module build) | 2305 / 2423 (2155) | same | 900 / 900 | 3.133 / 0.236 | 0.398 / 0.149 | 0.000 / 0.000 | +1.248 | 0.910 / 0.844 | 0 / 34 |

The "Vivado's own P&R" rows of docs/ofx.md (x_gen_none, x_mmcm_none, x_iodly) were re-read with the new compare:
check_timing 11/12 equal, setup/hold/pulse width totals equal, clock sets equal.

Setup slack histograms (endpoints per bin; bins < -10, [-10,-5), [-5,-2), [-2,-1), [-1,-0.5), [-0.5,0), [0,0.5),
[0.5,1), [1,2), [2,5), >= 5 ns):

| design | nextpnr | Vivado |
|---|---|---|
| x_mmcm_none | 0 0 0 0 4 0 0 0 0 4 16 | 0 0 0 4 0 0 0 0 0 4 16 |
| rv_soc | 0 0 4 23 4 67 166 306 431 1257 0 | 0 0 79 391 333 161 130 124 264 904 0 |
| rv_mul_hb | 0 23 131 239 148 251 201 218 467 1325 0 | 0 49 495 627 230 149 133 82 400 903 0 |

What the numbers say:
- On the small designs the reports agree item by item: check_timing, endpoint sets, clocks, path groups, pulse
  width totals and worst pulse width slacks. Only the setup/hold slack values differ, by the timer.
- On the CPUs the endpoint sets differ in three known ways: (a) without `-o hardblock-timing` nextpnr has no
  BRAM/ICAP/DSP pin arcs (rv_soc 2268 vs 2386 endpoints; with the option 2384 vs 2386); (b) names the Vivado-name
  mapping does not cover yet: BRAM WEA2/WEA3 (physical) vs WEA[0]/WEA[1] (logical), RAM32M port D (Vivado: RAMS32
  ADR0-4, nextpnr: WA1-5), and the `I` pin of RAMx_D1 (Vivado times both LUT halves, nextpnr one DI per pair);
  (c) 8-72 FFs fed by ICAP or DSP outputs that nextpnr leaves untimed ("no launch clock") without hardblock timing.
- Ordering: the nextpnr timer is optimistic by 1.2-1.7 ns per endpoint on the CPUs, and the rank correlation of
  setup slack is 0.89-0.94. The worst endpoint differs: nextpnr's worst is rank 52-69 in Vivado's list, except
  rv_mul_hb (rank 1). This is the timer and route-delay gap of Finding 13, not a report-format gap.
- Pulse width: with the extended table, pulse width endpoint counts and WPWS equal Vivado's on rv_soc, rv_soc_hb
  and the DFX build; rv_mul/rv_mul_hb differ by 3 and 13 pins (not analysed; vivado/build_xtime.tcl now writes
  `report_pulse_width -all`, which lists every pin, for that).

## Clock crossings, asynchronous designs, I/O delays (timing_xtime3)

Same method; nextpnr timer vs Vivado timer.

| design | what it tests | setup endpoints nextpnr / Vivado | clock interaction (ofx = Vivado?) | report_cdc row (ofx = Vivado?) | notes |
|---|---|---|---|---|---|
| x_cdc_none | clk_a (10 ns) -> clk_b (8 ns), no constraint | 32 / 48 | Vivado "Timed (unsafe)", WNS -6.670 (Vivado); ofx "Not timed (nextpnr: no common primary)" | equal: Critical, No Common Primary Clock, None, 16 endpoints, 16 Unknown | nextpnr does not time unrelated clocks; ofx check 14 lists the pair |
| x_cdc_groups | set_clock_groups -asynchronous | 32 / 32 | equal: Asynchronous Groups | equal: Critical, No Common Primary Clock, Asynch Clock Groups, 16 Unknown | |
| x_cdc_fpclk | set_false_path between the clocks | 32 / 32 | equal: False Path | equal: ..., False Path, 16 Unknown | |
| x_cdc_maxdly | set_max_delay -datapath_only 5 | 48 / 48 | equal: Max Delay Datapath Only | equal: ..., Max Delay Datapath Only, 16 Unknown | WNS -2.420 (nextpnr) / -3.534 (Vivado) |
| x_mmcm_groups | async groups between two MMCM outputs | 20 / 20 | equal: Asynchronous Groups | equal: Critical, User Ignored, Asynch Clock Groups, 4 Unknown | pulse width 31 = 31 |
| x_async_rtl | 3-FF synchroniser with ASYNC_REG | 2 / 2 | equal | (no crossing) | check_timing 11/12 after the port fix |
| x_async_none | same chain without ASYNC_REG (yosys made it an SRL16E) | 0 / 0 timed | - | - | pulse width 2 = 2, WPWS 4.020 = 4.020 (SRL16E/CLK); Vivado still lists SRL16E/D as an (untimed) endpoint, nextpnr has no endpoint for the SRL |
| x_iodly_minmax | set_input/output_delay -max and -min | 20 / 20 | equal | - | hold WNS -0.626 (nextpnr) vs +0.530 (Vivado): the hold side of I/O delays differs by more than the timer gap elsewhere (not analysed) |
| x_iodly_partial | only -max input, only -min output delay | 20 / 12 (hold 20 / 16) | equal | - | partial_input/output_delay 4/8 equal; Vivado does not time setup of the -min-only outputs (8) nor hold of the -max-only inputs (4), nextpnr times both with the one value it has: an XDC-reader gap |
| x_gen_div | create_generated_clock on `div_reg/Q` | 21 / 1 | ofx times clk_div; Vivado has no clk_div | - | test artefact: the EDIF from yosys has no `div_reg` (Vivado: "No pins matched 'div_reg/Q'"), so Vivado drops the clock (no_clock 20); nextpnr's reader found it |

## Timer gaps: draft fix (docs/drafts/nextpnr-vivado-checks.patch, opt-in `-o vivado-timing`)

Details and values in docs/drafts/nextpnr-vivado-checks.md. Without the option the patched nextpnr gives the same
FASM and report as timrep on 8 designs including blinky and rv_soc. With it (nextpnr timer):

| design | without | with | Vivado (same placement as "without") |
|---|---|---|---|
| x_cdc_none | 32 / 32 setup/hold endpoints, clk_a -> clk_b untimed | 48 / 48; clk_a -> clk_b "Timed (unsafe)", WNS -5.048 ns, requirement 2.000 ns | 48 / 48, WNS -6.670 ns, requirement 2.00 ns |
| x_iodly_partial | 20 / 20 | 12 / 16 | 12 / 16 |
| x_srl | 8 (flip-flop D only) | 12 (+4 SRL16E data inputs) | see below |
| x_arst | 12 SR endpoints, stub values | 12, recovery 0.404 / removal -0.248 ns | see below |

## Why x_iodly_minmax hold differs (analysis vs hold repair)

Endpoint `$auto$ff.cc:337:slice$1564/D` (input sw[0], set_input_delay -min 1.0): nextpnr timer -0.626 ns, Vivado
timer +1.028 ns (Vivado's own route of our placement; the design's Vivado WHS +0.530 is a different endpoint).
nextpnr's clock-pin delay (0.896 ns) is derived from its own setup slack on the same endpoint (7.256 ns), which gives
the same hold slack, so the itemisation is consistent.

| item | nextpnr | Vivado | effect on slack (Vivado minus nextpnr) | kind |
|---|---|---|---|---|
| data route IBUF -> FF | 1.405 | 4.141 | +2.736 | routing: Vivado's router detours this net to repair hold (nextpnr has no hold repair here) |
| input buffer (data) | 1.489 | 1.470 | -0.019 | analysis (cell value) |
| clock: IBUF -> BUFG route | 1.839 | 1.967 | -0.128 | analysis (clock-tree delay model) |
| clock: BUFG -> FF route | 0.896 | 1.805 | -0.909 | analysis (clock-tree delay model) |
| FF hold time | 0.200 (stub) | 0.191 | +0.009 | analysis (cell value) |
| clock uncertainty | 0 | 0.035 | -0.035 | analysis (jitter) |
| total | -0.626 | +1.028 | +1.654 | |

So 2.736 ns is the missing router hold repair (route-timing agent) and -1.037 ns is nextpnr underestimating the
global clock network delay against Vivado's slow-corner model; the rest is small. Vivado's IBUF/BUFG are the same in
both (1.489 / 0.096). The clock-tree delay belongs with route-delay calibration (Finding 13).

## Gaps that remain (and why)

| gap | Vivado | ofx | why / what is needed |
|---|---|---|---|
| `pulse_width_clock` check | count | "-" | needs set_min_pulse_width in the XDC reader |
| recovery/removal (`**async_default**`) | timed | timed, but as a synchronous input with the chipdb's SR stub (setup 0.100, hold 0.000 ns); ofx now groups them as `**async_default**` | correction: an earlier version of this table said "not timed"; x_arst shows 12 timed SR endpoints. Recovery/removal values: draft below |
| SRL16E/SRLC32E | timed | no endpoint or startpoint (no arcs in the chipdb); check 16 lists them | draft below |
| paths between unrelated clocks | timed ("Timed (unsafe)") | not timed; check 14 lists the pairs | draft below |
| partial I/O delays (-max only / -min only) | setup or hold only | both timed with the one value | draft below |
| pulse width of mode-dependent pins (RAMB36E1, DSP48E1) | per mode | largest value seen | needs the mode (width, DOA_REG, pipeline) to pick the requirement |
| report_cdc rules beyond Safe/Unsafe/Unknown (CDC-2..CDC-18: multi-bit, fanout, reconvergence) | yes | no | a netlist pass per crossing; ofx matches report_cdc on the 6 crossing pairs tested |
| multi-corner (slow/fast) | both corners | one corner | see below |
| clock uncertainty, jitter, pessimism removal | per path | not printed | nextpnr's report has no clock path (only a clk-skew total when enabled) |
| full clock path in report_timing | itemised | one "clock" line (launch minus capture) | nextpnr does not write clock network delays |
| more than N paths per group, `-through` | yes | N per clock pair (`--report-paths N`) | needs a timer that answers queries, not a report file |
| unconstrained path details (`-report_unconstrained`) | paths | endpoint counts per pair | nextpnr writes no paths for untimed endpoints |
| same routes in both timers | | | FIXED_ROUTE import (vivado/build_xroute.tcl) must route every net first |

## Multi-corner (deferred)

Deferred until route-delay calibration (workstream 1, Finding 13) lands. What it needs:
1. Delays per corner. Vivado times a slow (max) and a fast (min) corner and reports the worse; the openXC7 chipdb
   has one delay per arc (prjxray-db's SDF has slow/fast triples for cells; the interconnect has one value). It
   needs a calibrated chipdb pair (slow, fast), or a min/max DelayQuad per arc filled from both corners.
2. nextpnr: the timer already carries min/max (DelayQuad); setup must use the slow max and hold the fast min.
   ofx would then print "Setup (Max at Slow Process Corner)" / "Hold (Min at Fast Process Corner)" like Vivado.
3. Validation: the same placement timed by Vivado with one corner at a time (`config_timing_corners -corner Slow
   -delay_type max`, `-corner Fast -delay_type min`), compared per endpoint like the table above.
