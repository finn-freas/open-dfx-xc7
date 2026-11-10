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

## State 10 (09:50, resumed session)
- `-o dpl=R,P,C,E,1`: 5th field moves small LUT/FF clusters (a LUT and up to 3 flip-flops) as one piece to a free legal cluster placement near the crit-weighted centre of their connections (detail_place.cc try_cluster/improve_cluster). Rebuilt dpl2 in place (the old dpl2 code path is unchanged when the 5th field is absent).
- Variant dp4 = carry-di-bypass + dpl=2,2,0,1,1 (all cells and clusters). nextpnr side, mean of 3 seeds: slices rv_soc 449 -> 425, bram 287 -> 281, rv_mul 639 -> 582 vs dp1; nextpnr s 31/19/33.
- Vivado: runner for dp4 (build/qor/dpl_viv_dp4.log) and the queue for dp2dp seeds (build/qor/dpl_queue.log) both use vivado_slot.sh.

## State 11 (10:40)
- dp4 (cluster moves) measured, 3 seeds x rv_soc/bram/rv_mul under Vivado's timer: area down again, Fmax not better (Finding 15, round 2). dp2dp seeds 2-3 still waiting for a slot (runner log build/qor/dpl_viv_dp2.log).

## State 12 (final for this session)
- dp2dp seeds 2-3 under Vivado's timer did NOT run: the runner never got a Vivado slot before the stop and was stopped while waiting (it held no slot). Names: rv_soc/bram dp2dp s2-s3, rv_mul dp2dp s1-s3, bram vpack_vglob control (sources ready in build/qor/dpl/xsrc; run with flow/dpl_vivado.sh --run NAME...).
- No dpl processes or Vivado slots of this workstream are left.

## State 13 (2026-11-08 morning)
- Vivado-timed (Vivado timer, dpl_dump.tcl "placed" mode), now complete for dp2dp seeds 1-3: rv_soc 109.45 / 117.97 / 110.99 (mean 112.80; dp1 112.35), bram 155.35 / 153.99 / 150.22 (153.19; dp1 152.44), rv_mul 103.75 / 89.42 / 94.37 (95.85; dp1 97.06). dpl adds nothing measurable on top of carry-di-bypass.
- bram legaliser control `vpack_vglob` (Vivado's own slices at Vivado's positions through dpl_mix's legaliser): 165.51 MHz, 291 slices (Vivado's own run 170.88). So on bram the legaliser costs ~3 %, and Vivado's packing at our positions (145.82) and ours at Vivado's (147.58) both lose ~11 % against the control.
- **Bias warning (benchmark agent, 2026-11-08):** qor_xtime.placement(), used by place_bench.xprep for every dpl "placed" source, strips only the muxcy0 carry suffix. Measured on our runs (imposed / cells in Vivado's netlist): rv_soc 1889-1938 / 2104 (8-10 % left to Vivado), rv_mul 2666-2715 / 2941 (8-9 %), bram 1483-1486 / 1496 (1 %). The share is similar for dp0/dp1/dp2dp/dp4 (within 2 points), so the variant comparisons in Finding 15 stand roughly, but the absolute "ours" Fmax includes Vivado-placed cells. Re-xprep and re-run after the global-placer agent's qor_xtime fix lands. flow/route_xtime.py (Finding 16) has its own exporter (xroute.py; rv_soc own_rcal_s1: placed 2615, failed 2) and is not affected.
- carry-di-bypass default check: fir (no CARRY4 instance in the netlist), dpl1 binary, `-o dsp-cascade-place`, seed 1: FASM identical with and without the option (18763 lines; build/qor/dpl/noop_fir). Note: fir with the static placer and no `-o dsp-cascade-place` (variant dp0) spins in "Strict legalising 19 cells" (17 min, stopped); pre-existing, not the option.
- rv_big and eth dp0/dp1 Vivado runs held back until the qor_xtime fix (sources would carry the bias).
- 09:15: qor_xtime.placement fixed upstream (efcb64f) (the dpl_mix sources do not use it, so the mixes and the vpack_vglob control are not affected). All dp0/dp1 "placed" sources re-prepared (rv_soc s1 now 1966 rows, was 1894-1938 imposed); results go to a new root C:\Users\finnf\open-dfx-xc7-vivado\build\dpl_xtime2 (flow/dpl_vivado.sh, dpl_summary.py and dpl_bench.py default to it; DPL_XTIME=dpl_xtime reads the old, biased root). Runner: build/qor/dpl_viv_fix.log (24 runs, rv_soc/bram/rv_mul/rv_big x dp0/dp1 x s1-3). The State 13 dp2dp and vpack_vglob numbers are from the old export and are biased the same way.
- 13:06 re-timed dp0/dp1 (fixed export, dpl_xtime2), 3 seeds x 4 designs, Vivado timer: paired dp1 vs dp0 rv_soc +2.4 %, bram +2.1 %, rv_mul -2.2 %, rv_big +4.6 % (mean +1.7 %); slices -6..-16 %. rv_soc dp1 s2/s3 decode + firmware sim 11/11 (s1 already). Proposal in Finding 15 round 3: carry-di-bypass as default after an eth re-time.
- Open: eth dp0/dp1 re-xprep + Vivado (9 min each); dp2dp/dp4 and the mixes were not re-timed (old export). The imposed count is still 1892-1934 of 2104 on rv_soc after the fix (Vivado refuses some place_cell; see place_missed.txt), check that next.
- 13:20 dp2dp re-timed (dpl_xtime2): means rv_soc 115.64, bram 153.19, rv_mul 97.22 vs dp1 116.35 / 152.44 / 97.76 (Vivado timer). eth dp0/dp1 running.
- 13:41 eth dp0/dp1 re-timed: 68.99 -> 68.97 MHz mean (0.0 % paired), slices 3026 -> 2956. carry-di-bypass default proposal stands (Finding 15 round 3).
- 14:45 carry-di-bypass default: release patch 0031 + TREE f97b9b11 (624fac1), ofx default carry_di_bypass = true with escape `carry_di_bypass = false` and auto-off on a nextpnr without the option. release_regress in a prefix copy (~/ofx-test/prefix-cdb, cache-cdb, work ~/ofx-test/regress-cdb): install, series (31 patches = TREE), noop, identity PASS; defaults and ofx PASS after two harness fixes (3e88602 fir check with XDC + cascade rule; 7080368 all-off project lists dsp_init and carry_di_bypass). The shared ~/ofx-test/prefix was not touched.
- CAUTION: the Vivado evidence behind the default came from the "placed" mode, which is optimistic (it drops nextpnr's feed-through LUTs and split carries, leaves the LUTRAM register file to Vivado, and lets Vivado pick LUT pins). flow/exact_src.py (exact xroute import) seed 1: rv_soc dp0 103.48 / dp1 99.72, bram dp0 140.21 / dp1 142.01 MHz, against placed 116.40 / 120.39 / 150.13 / 157.18. dp0/dp1 x 4 designs x 3 seeds under the exact import are queued (build/exact/viv2.log); the default stands or falls with that.
- Wind-down 2026-11-08 ~22:05: carry-di-bypass back to default off (822fe36; exact import -1.0 % mean). The bram packing-vs-global split with the fixed export was NOT run: the dp0/dp1 x s1-3 mix sources sit in build/qor/dpl/xsrc_hold (resume: move them back to xsrc and `flow/dpl_vivado.sh --run bram_p5_dp1_s1x_mix_vpack_vglob bram_p5_dp{0,1}_s{1,2,3}x_mix_{vpack_nglob,npack_vglob}`). Note the mixes use the placed mode, which is optimistic (it drops nextpnr's own cells); an exact-import version of the mixes is the better next step. LUT-pin and xMUX work (lut6-first) is in docs/wip/router.md.
