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
   report_methodology. timing_xtime2 = the 7 designs below plus the DFX module build (all rc 0, 539 s).
4. `flow/timing_vivado_compare.py` reads both and writes build/timing_rv/compare.json; `--pulse-table` checks
   the pulse width table in ofx/timing.py against every pulse width report Vivado wrote.

Same placement, **not the same routes**: Vivado routes our placement itself. Loading our routes as FIXED_ROUTE
exists only in the route-calibration flow (vivado/build_xroute.tcl, workstream 1) and still leaves routing errors
on the CPU designs (rv_mul: 294 of 2603 routable nets with errors), so it was not used here.

## Report structure: what agrees now

| item | ofx before | ofx now | Vivado | result |
|---|---|---|---|---|
| check_timing items | 8, own order | Vivado's 12 in Vivado's order, then 4 marked [ofx] | 12 | 11 of 12 counts equal on all 11 compared runs; `pulse_width_clock` printed as "-" (not computed) |
| Design Timing Summary | WNS/TNS/WHS/THS | + WPWS/TPWS with pulse width endpoint counts | the same 12 columns | TPWS totals equal on the 3 small designs (x_mmcm_none 31 = 31, x_iodly 13 = 13, x_gen_none 2 = 2) |
| Clock Summary | flat | generated clocks indented under their master; MMCM/PLL outputs without endpoints derived (feedback clock `fb`) | the same | x_mmcm_none: clk, c1_mmcm, c2_mmcm, fb = Vivado |
| Intra Clock Table | setup/hold | + pulse width; clocks with only pulse width checks (clk, fb) | the same | x_mmcm_none: every per-clock count equal (setup 16/4; pulse width 1/18/10/2) and every WPWS equal (3.000/4.500/2.000/8.751 ns) |
| Other Path Groups | absent | printed; nextpnr has no recovery/removal, so it says how many async set/reset pins would be in `**async_default**` | table | gap, see below |
| Timing Details | the N worst paths overall | one block per path group in Vivado's order (intra in Clock Summary order, then inter): Setup/Hold/PW summary lines, N Max Delay and N Min Delay paths, Pulse Width Checks per clock | the same | x_mmcm_none group list identical: clk, c1_mmcm, c2_mmcm, fb, c1_mmcm -> c2_mmcm |
| path header | source/destination pins | + "(rising edge-triggered cell FDRE clocked by c1_mmcm {rise@0.000ns fall@5.000ns period=10.000ns})", requirement as an edge difference, logic/route %, Logic Levels by cell type ("5 (CARRY4=4 LUT2=1)", equal to Vivado's line for the same x_mmcm_none path) | the same | |
| names | nextpnr cell/bel pin (`.../SR`, `.../DPR3_1/WA1`) | Vivado cell/pin (`.../R`, `.../RAMD_D1/WADR0`) from X_ORIG_PORT and the LUTRAM macro | | rv_soc endpoint names in common 1307 -> 2118 of 2386 |
| hold | only with `--hold` | always, as Vivado; `--hold` is still accepted | always | |
| clock interaction | Inter Clock Table only | report_clock_interaction-like table (edges, WNS, TNS, endpoints, WNS requirement, Inter-Clock Constraints) | | "Timed" on every pair of the 8 runs, equal to Vivado |
| CDC | none | report_cdc-like table (Safely Timed; Safe = ASYNC_REG capture fed directly by a FF; Unsafe = logic before the capture; Unknown = no ASYNC_REG) | | x_mmcm_none c1_mmcm -> c2_mmcm: Info, Safely Timed, 4 endpoints, 4 safe, equal to Vivado |
| ofx extras | | 13 ignored_constraints, 14 unrelated_clocks, 15 async_pins_untimed, 16 sequential_cells_untimed | not in Vivado | 16 finds SRLs that nextpnr does not time (x_async_none: 0 endpoints, one SRL16E) |

Pulse width requirements: ofx/timing.py CONFIG `pulse_width` holds the "Required" values Vivado prints for speed
grade -1 (FDRE/C high and low 0.500 ns, BUFG/I min period 2.155 ns, MMCME2_ADV/CLKIN1 min period 1.249, max period
100.000, pulse 2.000 ns, MMCM outputs max period 213.360 ns). The clock of each pin comes from walking the routed
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
| rv_soc | 2268 / 2386 (2118) | same | 765 / 880 | -2.097 / -4.158 | 0.398 / 0.057 | 2.000 / -5.000 | +1.279 | 0.914 / 0.752 | 0 / 55 |
| rv_soc_hb (`-o hardblock-timing`) | 2384 / 2386 (2214) | same | 765 / 880 | -2.459 / -4.347 | 0.359 / 0.037 | 2.000 / -5.000 | +1.307 | 0.941 / 0.818 | 0 / 56 |
| rv_mul | 2781 / 3035 (2631) | same | 1074 / 1189 | -1.692 / -6.822 | 0.398 / 0.026 | 2.000 / -5.000 | +1.666 | 0.885 / 0.712 | 0 / 33 |
| rv_mul_hb | 3033 / 3068 (2791) | same | 1074 / 1205 | -6.041 / -7.420 | 0.373 / 0.060 | 2.000 / -5.000 | +1.242 | 0.932 / 0.767 | 10 / 86 |
| dfx_rv_pr_xor_n (DFX module build) | 2305 / 2423 (2155) | same | 785 / 900 | 3.133 / 0.236 | 0.398 / 0.149 | 4.500 / 0.000 | +1.248 | 0.910 / 0.844 | 0 / 34 |

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
- Pulse width: Vivado's WPWS -5.000 ns on the CPUs and the 115-131 missing pulse width endpoints are pins with
  no requirement in the ofx table (ICAPE2, RAMB36E1, RAMD32, DSP48E1 clock pins). vivado/build_xtime.tcl now
  also writes `report_pulse_width -all`, the input for extending the table (not yet run on the CPUs).

## Gaps that remain (and why)

| gap | Vivado | ofx | why / what is needed |
|---|---|---|---|
| `pulse_width_clock` check | count | "-" | needs set_min_pulse_width in the XDC reader |
| recovery/removal (`**async_default**`) | timed | not timed; check 15 counts the pins | nextpnr has no async set/reset arcs |
| SRL16E/SRLC32E | timed | not timed; check 16 lists them | nextpnr's xilinx arch has no timing arcs for SRLs |
| pulse width of BRAM/LUTRAM/DSP/ICAP pins | checked | missing from the table | add the -1 values from `report_pulse_width -all` |
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
