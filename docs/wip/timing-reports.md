# WIP: timing reports and nextpnr timer gaps (timing-report agent)

Updated 2026-11-07 00:52.

## Done (committed)
- 8b41703, 12e0d93: `ofx timing` in Vivado's report_timing_summary layout, compared with Vivado 2025.2 on 21 runs
  (docs/timing-reports.md).

## In progress: nextpnr timer gaps (opt-in `-o vivado-timing`), NOT verified yet
- Source tree: build/src/nextpnr-tmrfix (copy of nextpnr-timrep without .git). Build: build/nextpnr-build/tmrfix
  (built OK, 20:43). Build script: the scratchpad tmr_build.sh (cmake as corners_build.sh, ninja -j2).
- Draft patch (uncommitted, regenerate with the diff loop over the 5 files against nextpnr-timrep):
  docs/drafts/nextpnr-vivado-checks.patch. Changes:
  1. unrelated clocks timed from a common time zero (timing.cc clock_setup/hold_relationship root check);
  2. -max-only / -min-only port delays: xdc.cc writes " max"/" min" after the 4 numbers only when one side is
     missing; timing.cc puts an out-of-range arrival/required on the missing side and drops that check from the
     report;
  3. FDCE/FDPE SR recovery/removal from prjxray SDF (xilinx.cc getPortClockingInfo);
  4. SRL arcs (DI1/DI2/WE setup/hold, CLK->O6/O5/MC31) from prjxray SDF (xilinx.cc getPortTimingClass/ClockingInfo).
- Uncommitted script/ofx changes: ofx/timing.py (async_default group, "Timed (unsafe)", checks 14-16 wording),
  flow/timing_vivado_compare.py (Other Path Groups), flow/timing_report_check.py (`--fix` variants tmrfix_paths /
  vivado_paths, designs x_arst, x_srl), designs/timing/x_arst.{v,xdc}, designs/timing/x_srl.{v,xdc}.
- Finding (analysis only, from existing runs): x_iodly_minmax hold -0.626 (nextpnr) vs +1.028 (Vivado) on
  slice$1564/D: Vivado's data route 4.141 ns vs nextpnr 1.405 (+2.736, Vivado's router detours for hold = hold
  repair); clock BUFG->FF 1.805 vs 0.896 and IBUF->BUFG 1.967 vs 1.839 (-1.037, clock-tree delay model);
  uncertainty 0.035 (-0.035); IBUF/hold cell values -0.010. (The +0.530 in the earlier report is the design WHS,
  another endpoint.)

## Verified so far
- No-op: tmrfix without -o vivado-timing gives the same FASM and report.json as timrep on x_cdc_none,
  x_iodly_partial, x_iodly_minmax, x_arst, x_srl, x_mmcm_none, blinky, rv_soc (build/timing_rv/noop_fix.json).
- With the option (nextpnr timer): x_cdc_none 48/48 setup endpoints (was 32), x_iodly_partial setup 12 / hold 16
  (was 20/20; Vivado 12/16), x_srl 12 endpoints incl. 4 SRL DI2 (was 8), x_arst SR uses recovery/removal values.
- Baseline nextpnr already times FDCE/FDPE SR (x_arst: 12 SR endpoints, stub 0.100/0.000): the earlier ofx check 15
  "nextpnr does not time them" was wrong; fixed in ofx/timing.py.

## Committed since: 128c9da (draft patch, no-op), 6e09ee4 (ofx async_default / Timed (unsafe)), 0a6f69e (docs).

## Not run (Vivado busy with other agents 22:16-00:52; my batch yielded, was stopped, never held the lock)
- Vivado batch timing_xtime5: script build/timing_rv/tmr_viv5.sh (Git Bash; takes the lock after 10 min idle), i.e.
  run_qor.ps1 -Tag timing_xtime5 -Script build_xtime.tcl -SrcRel build\timing_rv\xtime\src -Names
  x_cdc_none_vt_placed,x_iodly_partial_vt_placed,x_iodly_minmax_vt_placed,x_arst_vt_placed,x_srl_vt_placed,
  x_mmcm_none_vt_placed,x_arst_tr_placed,x_srl_tr_placed (sources ready; ~10 min; lock C:/Users/finnf/vivado.lock).

## Next steps
1. (done) fix builds and no-op.
2. Vivado (lock C:/Users/finnf/vivado.lock + no vivado.exe): run_qor.ps1 -Tag timing_xtime5 -SrcRel
   build\timing_rv\xtime\src -Names <the *_vt_placed names>.
3. `python3 flow/timing_vivado_compare.py --designs x_cdc_none_vt x_iodly_partial_vt x_iodly_minmax_vt x_arst_vt
   x_srl_vt x_mmcm_none_vt x_arst x_srl` (config already added); update docs/timing-reports.md, roadmap
   rows, commit patch + scripts.
