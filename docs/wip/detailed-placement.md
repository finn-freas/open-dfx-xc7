# WIP: packing, legalisation, detailed placement (dpl agent)

## Done
- Own nextpnr tree build/src/nextpnr-dpl = ce3f7c18 + install/patches/nextpnr (TREE 961ea46e verified); build build/nextpnr-build/dpl0 (base, no change).
- flow/dpl_metrics.py: packing metrics of a Vivado dump (slices, LUT/FF per slice, LUT-FF direct pairs, dual LUTs, carry alignment, carry S-LUT co-location, hard-block distance, HPWL, control-set fragmentation, critical-path HPWL).
- vivado/dpl_dump.tcl: Vivado place/route + dumps (cells, worst paths as pin lists, util, congestion, PIP count, times, site list).
- First measurement (rv_soc s1 static placer, existing place_dump): LUT-FF direct pairs nextpnr 98.8 % vs Vivado 83 %; carry S LUT in carry slice 65.6 % vs 100 %; slices 501 vs 398; HPWL 19680 vs 17141.
- nextpnr pack_carry inserts a DI feed-through LUT for almost every carry bit (rv_soc 366/368) and an S feed-through for ~40 % (145/376): S drivers that are LUT6, or whose inputs plus the DI feed exceed 5. Vivado feeds DI from the AX bypass.

## Next
- Draft `-o carry-di-bypass`: DI straight from AX (x_sigs), S LUT may be LUT6; measure with Vivado timer.
- Timing-driven detailed placement pass in XilinxImpl::postPlace (opt-in).

## State 2 (running)
- flow/dpl_bench.py (variants dp0 base, dp1 = carry-di-bypass, dp2* = + detailed placer), flow/dpl_vivado.sh (Vivado lock).
- Source edits uncommitted in build/src/nextpnr-dpl (worktree, base commit = series): pack_carry.cc, xilinx.cc/.h, new detail_place.cc, CMakeLists.txt. Snapshot of carry stage: build/nextpnr-build/dpl1.patch. Scratch copies of the edit scripts: dpl_patch1.py / dpl_patch2.py / detail_place.cc in the agent scratchpad.
- Running: dp0 and dp1 nextpnr on rv_soc rv_mul rv_big bram eth, seeds 1-3 (logs build/qor/dpl_run_dp*.log); dpl2 build.
- Next: --xprep, --vivado (one batch), --report; b2n decode+sim of rv_soc/rv_mul dp1; Finding.

## State 3
- dp1 (carry-di-bypass) rv_soc s1 bitstream: decodes (fasm2bels) and passes the firmware bench 11/11 (flow/dpl_check.sh; ICAP bits need ~/ofx-test prefix prjxray-db).
- nextpnr-side (mean of 3 seeds, nextpnr timer, rcal chipdb): LUT cells rv_soc 1748 -> 1538, rv_mul 2443 -> 2147, rv_big 2494 -> 2198; slices 495 -> 449, 683 -> 639, 744 -> 677; nextpnr Fmax 99.1 -> 92.1, 90.3 -> 86.9, 87.1 -> 84.0 (critical paths are LUT chains, not carry; placement noise or systematic, Vivado pending).
- dp2dp (dpl default) rv_soc 93.2, rv_mul 89.9 (nextpnr timer). dp2w = dpl=3,4,0.5,3 tried on s1 only.
- Vivado batch 1 (rv_soc, rv_mul dp0/dp1 + free) queued behind the drcpow Vivado batch.

## State 4
- nextpnr runs done: dp0, dp1, dp2dp x {rv_soc rv_mul rv_big bram eth} x seeds 1-3 (nextpnr timer means: bram 125.4/130.4/134.8, eth 57.0/60.2/60.6, rv_soc 99.1/92.1/93.2, rv_mul 90.3/86.9/89.9, rv_big 87.1/84.0/87.2; slices bram 341/287/287, eth 2868/2796/2785).
- Vivado batches queued behind the drcpow batch: build/qor/dpl_viv{1,2,3}.log; results go to C:\Users\finnf\open-dfx-xc7-vivado\build\dpl_xtime.
- After Vivado: python3 flow/dpl_bench.py --designs rv_soc rv_mul rv_big bram eth --variants dp0 dp1 dp2dp --report

## State 5
- No-op: dp1off and dp2off FASM identical to dp0 (rv_soc, bram s1); dp1 differs. All 30 dp1/dp2dp FASMs assemble (patched db). rv_soc dp1 and dp2dp s1 pass decode+firmware sim 11/11; rv_mul cannot be decoded (fasm2bels has no DSP_L, same on dp0).
- Diagnosis on Finding 11 dumps (fix_static s1): Vivado vs ours rv_soc slices 398/501, LUT-FF direct 83/98.8 %, carry S-LUT in slice 100/65.6 %, HPWL 17141/19680, FF slice x control-set pairs 319/381 (min 130); bram 290/333, 73.7/86.0 %, 92.0/81.6 %, 21092/23183, 157/178 (min 62).
- Vivado queue: detached `dpl_bench.py ... --vivado` (setsid), 18-min chunks, waiting for the lock.

## State 6 (22:55)
- Vivado queue = flow/dpl_queue.sh (detached; log build/qor/dpl_queue.log): free + dp0 s1 for rv_soc/bram/rv_mul, then mixes (flow/dpl_mix.py: vpack_nglob, npack_vglob, vpack_vglob control), then dp1/dp2dp, seeds 2-3, rv_big, eth.
- Results land in C:\Users\finnf\open-dfx-xc7-vivado\build\dpl_xtime\<name>; metrics: python3 flow/dpl_metrics.py <dir> <netlist json> (netlist path in build/qor/dpl/xsrc/<design>_free/netlist.txt).

## State 7 (00:27)
- Finding 15 committed with Vivado-timed diagnosis (rv_soc, bram, rv_mul vs Vivado) and the first rv_soc mixes (vpack_nglob 137.91, npack_vglob 114.90 vs ours 126.17 / Vivado 157.63).
- Still queued (flow/dpl_queue.sh, detached): rv_soc vpack_vglob control, dp1/dp2dp s1 rv_soc/bram/rv_mul, bram mixes, then seeds 2-3, eth, rv_big. On resume: python3 flow/dpl_summary.py '<design>_p*' and update Finding 15's last table.

## State 8 (00:47)
- Finding 15 complete for seed 1 (commit 28d5dcd). Queue (1 worker) continues with round2 (build/qor/dpl/queue/round2.txt order): rv_soc/bram seeds 2-3, rv_mul dp1/dp2dp, bram mix controls.
- After the stop: python3 flow/dpl_summary.py 'rv_soc_p5_*' 'bram_p5_*' 'rv_mul_p5_*' and add seed means to Finding 15.

## State 9 (01:27, stopped for wrap-up)
- Finding 15 has the 3-seed Vivado-timed means for rv_soc/bram/rv_mul (dp0 vs dp1) and the rv_soc/bram mixes. Queue stopped cleanly (no Vivado of ours running, no slot held).
- Not done: dp2dp seeds 2-3, rv_big, eth under Vivado; bram/rv_mul mix controls; qor_suite quick mode.
- Resume: NAMES_FILE=<list> flow/dpl_queue.sh 1 (remaining order in build/qor/dpl/queue/names.txt from index in next_saved2), then python3 flow/dpl_summary.py and update Finding 15.
- Next technical step (from the mixes): packing must follow the global placement (our slices group cells Vivado keeps apart); a cluster-aware legaliser / slice-level detailed placement, and the global-placement half belongs to the global-placement agent.
