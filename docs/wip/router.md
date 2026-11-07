# WIP: router workstream (router2, Vivado-timed routing share) + hold repair

State 2026-11-06 ~21:50. Owner: router agent. Hold repair handed over (second priority).

## Done
- Harness `flow/route_xtime.py` + `vivado/build_rte.tcl` (committed). Stages vref/own/import/npr/export/vivado/report.
  - vref: Vivado places+routes the yosys netlist (no opt_design) -> cells.txt + slack.txt (WNS with/without ICAPE2).
  - import: Vivado cells mapped onto nextpnr's packed names -> `-o place-import=FILE`.
  - export: flow/xroute.py export; `<name>` = nextpnr pips imposed, `<name>_vr` = same placement, Vivado routes.
- nextpnr worktree build/src/nextpnr-rte (release tree 961ea46e), build build/nextpnr-build/rte
  (build/nextpnr-build/rte_build.sh). UNCOMMITTED source changes there (to become docs/drafts/nextpnr-router-timing.patch):
  - `-o place-import=FILE` (xilinx.cc apply_place_import)
  - `--router2-opt KEY=VALUE` (command.cc) and router2 settings critExp, critFloor, critEstWeight/Thresh,
    critRipupIters/Thresh/ResetCong/KeepBest (router2.cc/.h). Keep-best snapshot is in source, NOT yet built.
- Hold: docs/drafts/nextpnr-hold-fix-upstream.{patch,md} + flow/hold_bench.py committed (a623b07).
  x_iodly_minmax (nextpnr timer, hold binary): hold-fix + upstream repairs input hold (3 detours + 2 buffers, 0 left),
  route-min-scale 0.39 needs 4 detours + 18 buffers; Fmax 72.34 unchanged (build/rte/iodly/).

## Screening so far (nextpnr timer, NOT Vivado)
- cal chipdb timer is 0.3-0.6 ns/arc optimistic (Finding 13 draft), so screening uses the rcal chipdb.
- rv_soc rcal, own placement, mean of seeds 1-3: base 99.13, crr3 (no keep-best) 101.84, ew1 100.45, cexp8 96.33 MHz.
- crr3 (rip-up rounds with congestion reset) crashed on a partial-net rip-up (assert in route_arc); fixed by ripping
  the whole net.

## Blocked
- Vivado: another agent's vivado.exe (pid 26308) holds /mnt/c/Users/finnf/vivado.lock since before 20:40.
  Queued: vref runs (python flow/route_xtime.py vref --run, pid 100350, waits for lock); then bufr hold runs
  (designs/rte/bufr_p10_hold_{rel,up,msfix}_s1, mode fixed).

## Next
1. After vref: `import --run`, `npr --variants vimp --run`, `export --variants own vimp --run`, `vivado`, `report`.
2. Rebuild rte with keep-best; screen crr3 variants with rcal; take best + rcal to Vivado.
3. Write Finding (routing share, each change: Vivado timer mean over seeds, runtime).

## Update ~22:35
- Vivado vref (Vivado places+routes the yosys netlist, no opt_design; Vivado timer, excl. ICAPE2):
  rv_soc 173.2, rv_mul 157.9, rv_big 166.7, bram 172.3 MHz (WNS_noicap -0.774/-1.363/-0.999/-0.805 ns at 5 ns);
  place+route 82/76/99/93 s. /mnt/c/Users/finnf/open-dfx-xc7-vivado/build/rte/<d>_vref/.
- place-import works (option registered); rv_soc binds 1908 cells, ~35-85 carry clusters per design cannot sit at
  Vivado's root (nextpnr re-chunks chains / duplicates S LUTs) and go to the placer.
- nextpnr timer with rcal chipdb, nextpnr router on Vivado's placement (vimp, seed 1): rv_soc 103.92, rv_mul 102.16,
  rv_big 104.13, bram 131.87 MHz; on its own placement (own, mean s1-3) 99.13 / 87.15 / 90.40 / 125.40.
  To be confirmed by Vivado's timer (queued: <d>_vimp_cal_s1 / _vr, <d>_own_cal_s1 / _vr, rcal --no-vr).
- Router options, rcal, own placement, paired mean of seeds 1-3 (nextpnr timer): sd1crk3 (critSeedDelay=1 +
  critRipupIters=3 keep-best) +4.0/+5.7/+2.1/+4.3 % (rv_soc/rv_mul/rv_big/bram), router time not higher;
  crk3 +3.4/+1.9/+2.1/+1.8; sd1 -0.1/+5.0/+2.0/+3.5; cexp8 and ew1 within noise.
- Run binary: build/nextpnr-build/rte-run (copy; never rebuild in place while runs are queued).

## State at the 01:40 stop (2026-11-07)
- Committed: Finding 16 in docs/qor-vivado.md (nextpnr rcal timer numbers; Vivado reference placements), draft
  docs/drafts/nextpnr-router-timing.{patch,md} (no-op verified on 4 designs), hold draft md with x_iodly_minmax.
- NOT measured: every Vivado-timed router number. Exported and ready (C:\Users\finnf\open-dfx-xc7-vivado\designs\rte\):
  <d>_vimp_cal_s1 (+_vr), <d>_own_cal_s1 (+_vr), <d>_vimp_rcal_s1, <d>_vimp_sd1crk3_rcal_s1, <d>_own_rcal_s{1,2,3},
  <d>_own_sd1crk3_rcal_s{1,2,3}, bufr_p10_hold_{rel,up,msfix}_s1. My runs waited for a slot 22:02-01:15 without one.
- Resume: `python3 flow/route_xtime.py vivado --variants vimp --chipdb cal --run` (pairs), then
  `vivado --variants vimp vimp_sd1crk3 --chipdb rcal --no-vr --run`, `vivado --variants own own_sd1crk3 --chipdb rcal
  --seeds 1 2 3 --no-vr --run`, `vivado --variants own --chipdb cal --run`, `vivado --names bufr_p10_hold_*_s1 --run`;
  then `report`, `python3 flow/route_cmp.py <name>...` for per-path routing deltas, and fill Finding 16.
- Next router ideas: load/fanout-aware cost for critical arcs; packer mode keeping yosys CARRY4 boundaries so the
  Vivado import is exact.
