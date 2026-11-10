# Where to resume (updated 2026-11-06 night, long run)

## RESUMED 2026-11-10 evening (user: "continue where we left off", long run) - start here
- 7 agents, each keeps its own note current (read these first after an abrupt stop):
  replication / FF split -> docs/wip/replication.md; Vivado-calibrated delay table -> docs/wip/delay-table.md;
  packing / legaliser gap decomposition on the exact import (new) -> docs/wip/packing-decomposition.md;
  synthesis area -> docs/wip/synthesis-area.md; EQY `ofx check equiv` -> docs/wip/equiv.md; Bambu HLS -> docs/wip/hls.md;
  DFX exact-import table + partition-pin default -> docs/wip/dfx-gaps.md.
- DECIDED by the user (2026-11-10 evening): carry-DI chipdb patch GOES INTO the release, but only after the replication,
  delay-table and packing agents have reported (they use the current chipdb as their control); then as its own commit
  behind the full release regression (draft docs/drafts/nextpnr-carry-di-arcs.patch, worktree build/src/nextpnr-cb2rel).
  If the delay table and the packing decomposition both come back flat: stop option tuning and tell the user that the
  remaining gap needs a structural packing / legalisation change.
- Still waiting on the user: pushes (none since 099c2ee).

## WRAP-UP 2026-11-10 afternoon (user asked to wrap up)
- Committed today (local only, nothing pushed): e4a5125 release placer stack 0033-0039 + placer_tuning default;
  503e8b9 `seeds` + `ofx hls`; 9d6e660 placement experiments/drafts/xdc tests; 5ffdd16 RESUME; 0638c76 seeds = "auto" default
  (seed 1 alone, seeds 2-3 only if it misses timing or fails; regression ofx stage PASS).
- Uncommitted on purpose: docs/wip/user-assumptions.md, docs/wip/guess-requests.md (user's assumed values; repo goes public),
  examples/dbg_ila/build_run.log. Plus each agent's WIP below (review, then commit).
- Placement levers queued, in order (background reading is kept local and gitignored, never published): 1 Vivado-calibrated segment-aware
  (dx,dy) delay table, 2 per-arc adaptive-exponent timing weights, 3 replication, 4 carry macros absorbing peripheral LUT/FF,
  5 critical-path DP detailed placement. Caution: Vivado's own phys_opt declined to replicate rv_mul's pcpi_rs2 nets.
- STOPPED HARD (user: "stop everything right now"): all 5 agents killed mid-work, every nextpnr/yosys/Vivado/bench
  loop killed, Vivado locks removed. Nothing running. C: 119 GB free. The agents did NOT get to write their notes;
  their state is only what is on disk:
  - Replication for rv_mul: builds build/nextpnr-build/split, split2 (source: build/src/nextpnr-afo, uncommitted edits),
    bench variants cb2_splc_dq / cb2_splcr_dq in flow/place_bench.py, probes in build/split_probe/. No result recorded;
    check whether vivado/build_rte.tcl *_po (Vivado phys_opt replication oracle) was run on cb_all2 rv_mul first.
  - Calibrated delay model: worktree build/src/nextpnr-dtab, build build/nextpnr-build/dtab, data in build/dtab/.
    No result recorded.
  - Synthesis area: flow/synth_area.py, tools/mt_lut/mt_lut.cpp (mockturtle LUT tool), build/mt_lut/, Vivado runs in
    build/qor/synarea/. docs/wip/synthesis-area.md was not written yet.
  - EQY equivalence: flow/equiv.py, flow/equiv_bench.py, flow/bit2netlist.sh (modified), ofx/cli.py (+47 lines, an
    equiv command), build/equiv/. No docs yet; was working on constant-pin handling after reconcile.
  - Bambu: BUILT OK (toolchain/bambu/install/bin/bambu, 2026-11-10 10:48). docs/hls.md, ofx/hls.py, flow/hls_compare.py,
    install/bambu.sh (example submodules + a clang-19 workaround) modified; agent was updating docs/hls.md's install
    section. Vitis-vs-Bambu comparison status: see docs/hls.md "Bambu vs Vitis HLS".
  - Next session: review each of these diffs, rerun the agent briefs from where they stopped, commit what passes.
- Waiting on the user: carry-DI patch into the release (changes every chipdb sha, needs full regression); pushes (none today).
- Hardware: no 7-series board yet; the biggest unproven area is on-silicon DFX / bitstreams (docs/hardware-test-plan.md, Arty A7-35T).

## Earlier 2026-11-10 (morning)
- Not adopted: timing weight sweep, twrepl / twcdirepl (rv_soc to 81 % of Vivado but rv_mul loses), fanout-aware arc delay (afo), sa-refine chain overlap, chain-aware global placement / legalisation (item 0b below).
- Experimental code only in worktrees build/src/nextpnr-afo (uncommitted: arc-fanout, fo, chainovl, chain-* options) and build/src/nextpnr-cb2rel (a4b08d86 carry-DI arcs, patch in docs/drafts/nextpnr-carry-di-arcs.patch).
- Friendbot (separate repo, for reference): ~/friendbot main e60c1e0 (link version 4 "run" mode, ~5 s replies, in flash); pushed by user request to github finn-freas/roastbot-fpga 95d1e2d. One uncommitted edit left: ~/friendbot/scripts/fast_upload.sh.

## Goal and priorities (user)
- An open-source Vivado for the 7-series. **Artix-7 first**; the other families come after Artix is finished.
- The goal is whole builds on par with Vivado or better: Fmax, area, power, build time and routability, weighted about equally.
  - **The placer is the main work focus.** The ~25% Fmax gap under Vivado's timer comes mostly from placement.
- Order of work: 1) build quality, 2) DFX parity with Vivado, 3) keep every other gap row staffed.
  - Scan docs/open-vivado-roadmap.md for EVERY row that is not plain "ok", including partial rows and the IP table.
- Pushes:
  - only through `python3 tools/publish_strip.py` (docs/publish.md), then `git push origin publish:master`;
  - at most ~2 per day;
  - the one-time force-push is done: remote master = 099c2ee (from c0649b3).
- Never touch the Tang Nano or ~/friendbot.
- Resource rules:
  - WSL has ~11 GB.
  - nextpnr only through ofx/npwait.sh: the QoR agents use a cap of 3, the others 2.
  - At least 4 GB free before builds.
  - Vivado: wait until tasklist shows no vivado.exe, then take the atomic lock `mkdir /mnt/c/Users/finnf/vivado.lock`, and remove it with `rmdir` from a trap.
  - Wait loops use `pgrep -f 'patter[n]'`.
  - Each agent uses its own scratch-file prefix.

## Workstreams running at this checkpoint (each commits its own verified work)
1. **Global placement + delay calibration (Finding 13):** HeAP, net weights, delay model. Clock leaf is 0.72 ns short; carry paths are 1.1-2.9 ns optimistic.
2. **Packing / legalization / detailed placement (new):** first diagnoses against Vivado's placement (mixed placements), then timing-driven packing and a detailed placer.
3. **Router (new):**
   - measures the routing share of the gap by routing Vivado's placement with our router;
   - improves timing-driven routing;
   - owns HOLD REPAIR. Draft `docs/drafts/nextpnr-hold-fix-upstream.patch` (`-o hold-fix-upstream`, `-o route-min-scale=K`) and `flow/hold_bench.py` were UNCOMMITTED at handover. bufr becomes +0.06 ns on the nextpnr timer; Vivado validation is pending.
4. **Synthesis QoR (Finding 14):** Fmax, area (LUT sites +14%, LUTRAM 320 vs 142) and runtime, balanced.
5. **Artix-7 QoR benchmark suite + scoreboard (device agent):**
   - flow/qor_suite.py and docs/qor-scoreboard.md, with a quick mode;
   - 15-25 designs, both tools doing their own P&R;
   - balanced verdict plus placement-quality columns.
   - Device coverage itself: 5b2b299. Kintex-7 k70t builds; GTP: gtp_b3 minimal, nextpnr GT FASM default mismatch.
6. **Build time vs Vivado (new):** stage-by-stage profile and speed-ups; output must stay bit-identical; docs/runtime.md.
7. **Timer gaps:** unrelated clocks "Timed (unsafe)", partial I/O delays, recovery/removal, SRL endpoints, x_iodly_minmax hold. Report work is done (8b41703, 12e0d93).
8. **Multi-corner (XDC agent):** fast pip/cell delays in the chipdb plus a Fast-corner setup/hold check. The XDC fixes are done (e969551, adde7f4, 6eb3348, 36e97c8).
9. **DRC + power:** the DRC deck is committed (89058a3); the power estimate is in progress.
10. **IP wizards + ILA (new):** `ofx ip clk|fifo|bram` and `ofx debug` (JTAG BSCANE2 ILA), each checked against Vivado's IP.
11. **Incremental compile + XDC leftovers (new):** latency, jitter, DIFF_TERM/KEEP/MARK_DEBUG, I/O delays for non-LVCMOS33 standards.
12. **Breadth:** SystemVerilog coverage (yosys-slang?), XADC bits, AXI interconnect example, DDR3 read-delay and 100 MHz timing, gigabit RGMII on an Artix board.
13. **DFX parity (new):**
    - full native_check, `--other-region`;
    - per-configuration timing with hardblock-timing against Vivado;
    - HD.PARTPIN_RANGE/LOCS, partition pins winning at every seed;
    - DSP bit 26_277;
    - other Artix dies;
    - DFX QoR against Vivado's DFX flow;
    - `ofx dfx` workflow parity.
14. **GTP + PCIe (new):** prjxray-db audit, a minimal GTPE2 build, bit comparison with Vivado, fuzzing missing bits.
15. **Release 0.1:**
    - Tooling committed in 3fe1468. install, series and noop PASS.
    - hardblock-timing on the honest timer: rv_soc +12.9%, rv_mul +1.7%. rv_big, bram and fir pending, then the default decision.
    - clkbuf_keep_buffer_inputs stays opt-in.
    - Detached jobs live in ~/ofx-test/jobs (regress6, bench, replay). Still to do: clean install, docs/release-0.1.md.

## Night of 2026-11-06: results so far (checkpoint 22:49; each agent's state is in docs/wip/*.md)
- **Placement is now the top priority (user).**
  - The placer agents get first claim: other agents run nextpnr with OFX_MAX_NEXTPNR=1, and placer/router/benchmark jobs go first in the Vivado queue.
  - The global placer also adopts techniques from open contest placers (elfPlace, DREAMPlace-FPGA, UTPlaceF, RippleFPGA).
- **Finding 13:**
  - On identical implementations, nextpnr's timer is 37-49 % optimistic on rv_soc/rv_mul/rv_big. All of the error is routing delay.
  - The route-delay calibration draft brings it within -8..+5 %.
  - The global placer uses a fixed formula that is 433 ps per arc low. The draft nextpnr-placer-delay-cal fixes it to about -30 ps, but its Vivado-timer QoR is still pending.
  - HeAP is slow and unroutable on mc12_a100; `--placer static` works there.
- **Finding 14:**
  - Synthesis Fmax is within 3-5 % of Vivado's synth_design (Vivado P&R).
  - LUTRAM on arty_ddr3: 320 -> 144 (Vivado 142) with the opt-in yosys draft opt_dff.keep_memrd_regs.
  - Next: abc9 loses the BRAM clock-to-out arrival time (6 logic levels vs Vivado's 3); pw_dsp merges multipliers before DSP packing (7.6x LUTs).
- **Timing:**
  - Multi-corner draft (nextpnr-timing-corners): port slack now matches Vivado at the Fast corner. Its Vivado register-path batches are queued (vivado/run_xdctime_batches.sh).
  - Timer gaps draft nextpnr-vivado-checks is in progress.
  - Hold-fix draft committed (a623b07).
- **DRC/power:**
  - DRC agrees with Vivado on 35 of 42 rules over 198 designs.
  - Power: 8.1 % total error leave-one-family-out. Its Vivado queue is a low-priority PowerShell waiter.
- **Build time:**
  - Delay-matrix cache and fast fasm2frames are default and bit-identical.
  - LiteX ddr3: 176 s vs Vivado 236 s; blinky 10.5 s vs 86 s.
  - The exit-bb router draft cuts rv_soc routing from 51-88 s to 8-11 s.
  - npwait now counts nextpnr-xilinx runs that run under ld-linux (8f53d02).
- **DFX:** native_check 42/0, multi 18/0, HD.PARTPIN_LOCS/RANGE supported; Vivado DFX references prepared.
- **Features:**
  - `ofx debug` (MARK_DEBUG ILA over BSCANE2) works in simulation; `ofx ip bram` done; clk and fifo generators in progress.
  - yosys-slang: sv-tests 590/622 (vs 292); ibex synthesizes.
  - GTP audit plus a minimal gtp_b3 build. nextpnr GT FASM uses the wrong defaults (114 of 227 parameters).
- **QoR suite:** 21 designs registered; the first Vivado run is waiting for the lock.
- **RapidWright evaluation:** started 22:4x (docs/wip/rapidwright.md).
- **Decision:** we do NOT decompile Vivado with REA. That needs a verifiable signed AMD agreement covering decompiling and publishing derived code.

## Checkpoint 23:50 additions
- **Default to decide next session, through the release regression and QoR suite:** `--placer static` at every size, i.e. remove `static_max_cells`.
  - Vivado timer: DDR 83.92 vs HeAP 84.46 MHz; eth 68.64 vs 67.39. The difference is within seed noise.
  - Static has 15-28 % lower wirelength and fewer router iterations, and routes mc12_a100, which HeAP can't (b82fe04).
  - Also still pending: the hardblock_timing default. rv_soc +12.9 % and rv_mul +1.7 % on the honest timer; rv_big, bram and fir not yet measured.
- **DFX (eae939e, docs/phase16-dfx-gaps.md):**
  - Per-configuration timing with ICAP timed (nextpnr timer): 104-119 MHz. ICAPE2 clock-to-out of 5.2 ns limits it.
  - HD.PARTPIN_* supported; child runs added; partition pins stay opt-in.
  - The Vivado DFX comparison queue is docs/wip/dfx-gaps/job_vq.sh, queued.
- **Breadth (2d11324):**
  - slang front end `--frontend slang`.
  - AXI xbar example; RGMII builds on xc7a200t.
  - DDR3 placer sweep: static 108-115 MHz on the nextpnr timer.
  - Vivado batches: vivado/breadth_queue.sh, queued.
- **Multi-corner:** the register-path Vivado batches (vivado/run_xdctime_batches.sh) are queued.
- **Vivado capacity:**
  - Slot 2 via vivado/vivado_slot.sh, for priority agents when Windows has at least 3.5 GB available.
  - Option for next session: lower WSL memory from 12 to 10 GB at a quiet moment, to give Vivado more room. Decide with the user.

## Checkpoint 00:50 additions
- **Release 0.1:** done locally (48f6d0e, 3598e68, 08807d0, 5745c23, 140f7be; docs/release-0.1.md, docs/wip/release.md).
  - New defaults: hardblock_timing ON; static placer at every size.
  - CLI e2e: 42 PASS, 1 FAIL. dfxpp_a50 greybox fails "no route outside the pblocks for 'ready'"; it is a regression from the pinfeed step, patch 0012.
  - Clean install PASS.
  - No fitted power model is shipped: ofx/power_model.json is untracked.
- **Router is its own 15-20 % lever.** On the same nextpnr placement, nextpnr routing (rcal timer, close to Vivado's) vs Vivado routing:
  - rv_soc 99.1 vs 117.2 MHz;
  - bram 125.4 vs 149.4 MHz;
  - eth 57.1 vs 69.0 MHz.
  - The placer delay calibration alone gives at most about ±3 % (bram +3 %).
- **Synthesis round 2 (Finding 14 r2):**
  - `scratchpad -set abc9.xaiger 1` gives ABC the real BRAM/DSP/FF arrival times. Candidate default.
  - rv_soc on Vivado P&R: 157.6 -> 162.4 MHz, and 176.8 with the calibrated LUT model, against Vivado's own netlist at 171.0. Single runs; needs the placement-noise checks.
  - k_mul DSP accumulator fix: pw_dsp32 LUTs 2352 -> 1047.
  - Block-RAM rule for arty_eth: LUTRAM 636 -> 548 (Vivado 512).
- **IP/ILA:** done offline (docs/ip.md); the Vivado IP comparisons run via flow/ip_vivado_queue.sh.
- **GTP/PCIe (docs/gtp.md):**
  - pcie_bare matches Vivado bit for bit.
  - GT defaults are filled by flow/gt_json_defaults.py.
  - The Vivado GTP comparison runs via flow/gt_vivado_queue.sh.
- **Incremental + xdc4 (docs/incremental.md):** works, but no runtime/QoR win yet. The queues are in build/incr/*.sh.
- **QoR suite:**
  - 21 designs in the open flow; 3 fail (fir needs the dsp-cascade draft; raygentop has LDCE latches; diffeq2 hits the yosys assert).
  - nextpnr ignores the target period.
  - Vivado sweeps run via vivado_slot.sh.
- **Vivado lock incident:** benchmark agent PID 28584 (old viv_lock.sh) may re-take vivado.lock. The kill was refused by the classifier and is left for the user.

## WRAP-UP 01:45 (2026-11-07): stopped for the usage limit (~89 %)
All agents were told to commit and stop. Each workstream's exact state is in docs/wip/*.md. Last results:
- **QoR scoreboard (PARTIAL, e10b44b, docs/qor-scoreboard.md):**
  - Verdicts on 7 designs: better on bram 1.39, or1200 1.14, vexriscv 1.13; on par on serv 1.04, aes 0.99, rv_big 0.98; worse on sha256 0.92.
  - Geometric mean overall 1.07: Fmax 0.93 (nextpnr timer, not yet like-for-like), area 1.01, power 0.77, build time 2.17, wirelength 0.92.
  - Resume with `python3 flow/qor_suite.py vivado --modes free --run`, then `--modes placed`, then `report --run`.
- **Placement gap split on rv_soc (Finding 15, Vivado timer):**
  - global placement about 10.4 MHz;
  - packing and detailed placement about 11.7 MHz;
  - imposition overhead about 9 MHz.
  - The carry-DI feed-through LUT in pack_carry.cc is the packing cause. The draft `-o carry-di-bypass` brings slices to Vivado's level (bram 287 vs 290), but its Fmax change is within seed noise.
  - Next lever: packing that follows the global placement.
- **Router (Finding 16):**
  - nextpnr routing is 15-20 % slower than Vivado routing on the same placement.
  - Draft router2 options `critSeedDelay=1` + `critRipupIters=3` give +2..+6 % on the rcal timer. Vivado confirmation is pending.
- **Timer gaps closed, opt-in (`-o vivado-timing`, nextpnr-vivado-checks.patch):** unrelated clocks, partial I/O delays, recovery/removal, SRL endpoints. Vivado check pending (build/timing_rv/tmr_viv5.sh).
- **Vivado queues NOT run, to restart next session (scripts ready):**
  - vivado/breadth_queue.sh;
  - docs/wip/dfx-gaps/job_vq.sh;
  - vivado/run_xdctime_batches.sh;
  - flow/ip_vivado_queue.sh;
  - flow/gt_vivado_queue.sh;
  - build/incr/*.sh;
  - build/timing_rv/tmr_viv5.sh;
  - the router and detailed-placement queues (docs/wip/router.md, build/qor/dpl/queue/);
  - synthesis confirmation runs (docs/wip/synthesis.md).
- **Infrastructure to fix first next session:**
  - (a) `mkdir` on /mnt/c is not an atomic lock: two jobs took one slot at least 3 times. Move the Vivado lock to a WSL-side lock (flock on a Linux file) or a Windows mutex.
  - (b) Verify that npwait (8f53d02) does not count compiler or ninja processes.
  - (c) Benchmark agent's Git Bash PID 28584 (old viv_lock.sh) may still be alive and could take vivado.lock. Its kill was refused by the classifier; it is the user's call.
  - (d) Consider lowering WSL to 10 GB for more Vivado room (decide with the user).
- **Defaults to decide:** abc9.xaiger=1 (synthesis arrival times), the router options, carry-di-bypass. Each needs a Vivado-timer confirmation over seeds first.

## If a session ends abruptly
- Uncommitted work is on disk in ~/open-dfx-xc7 (git status) and under ~/ofx-test.
- Re-verify it before trusting it, then restart the workstreams above with the same briefs.

## Deferred, with reasons
- GUI: waits for the core flow.
- Encryption/eFuse: until requested.
- Hardware tests: no board yet.
- Non-Artix families: after Artix.

## Late addition (global placement wrap-up, d296ce0)
- **Placement round 2: no win on Vivado's timer.** No round-2 variant beats the old stub-chipdb placement: rv_soc 116.81, bram 155.87, rv_big 104.95 MHz.
  - The calibrated cell chipdb itself lowers Vivado-timed Fmax: bram -5.5 %, rv_big -12 %.
  - Calibrated placer delays win part of that back.
  - Lesson: a more accurate nextpnr timer does not by itself make the placer better. Keep the stub chipdb for placement until the placer uses the calibrated delays well.
- **Clock-leaf calibration (c89f838):** nextpnr clock-pin delay goes 0.896 -> 1.671 ns; Vivado shows 1.645 ns.
- **Opt-in placer options from the literature (6cf1182, 6d49d45, d8a090f):** pl8 (timing-arc term) and pl9 (weighted preconditioner). Their Vivado timing is not run yet; the sources are ready.

## RapidWright (3a9d417, f70691a, 0206979; docs/rapidwright.md)
- RapidWright 2025.2.2 + Temurin JDK 21 are installed in toolchain/rapidwright; the Artix-7 device file works.
- The writer from our placement+routing to a DCP sets all 34875 PIPs on rv_mul offline, including the RAM32M macros behind most of the 294 import errors. Whether Vivado opens it fully routed is untested: run vivado/rw_check.tcl first.
- The Vivado DCP -> nextpnr replay path is written but untested (vivado/rw_vref.tcl for rv_soc).
- RapidWright cannot route 7-series.

## FINAL STOP 2026-11-07 (~87-88 % usage; the machine slept 11:10-18:30)
Morning session results (all opt-in, no-op verified, committed):
- **Vivado lock fixed** (826eb38): vivado/vivado_slot.sh creates the lock dirs through Windows `cmd mkdir`, which is atomic. A `vivado.lock` dir may be left over from before the sleep; check that no vivado.exe is running, then rmdir it.
- **Published:** GitHub master = dbf3e37 (from e8232b7). The publish_strip proof (c) false positive is fixed (e8232b7).
- **Global placer diagnosis (aea2a3c, flow/place_diag.py):**
  - Vivado builds around the fixed ICAP/RAMs in a flat, wide shape: sd_y 5.5 vs our 16.9. Our top-100 paths take 65.7 hops vs 20.0.
  - The y-weighted wirelength failed.
  - The anchored start `--placer-static-anchor-init 20 --placer-static-ip-wait 0.5` gives Vivado's shape on rv_soc. Vivado timer, 3 seeds, rcal chipdb: rv_soc 119.22 (+2.1 % vs stub base 116.81), bram 151.44, rv_big 101.41. That is +1.4..+8.1 % against the same chipdb without anchoring.
  - **Next:**
    1. Vivado-time the stub-chipdb anchored placements (sources `{rv_soc,bram}_p5_pl11_anc20ipw_stub_s{1,2,3}_placed`; nextpnr timer looks slightly positive on rv_soc).
    2. Target-density spreading.
    3. Combine with carry-di-bypass.
    4. Optionally try DREAMPlaceFPGA as an external placer for about 1 week.
- **Router Finding 16:** Vivado's timer over 3 seeds shows no confirmed gain from critSeedDelay+critRipupIters (small, design-dependent). The options stay off.
- **QoR scoreboard:** PARTIAL, Vivado done on 11 of 21 (c774b9c); placed mode in progress.
- 18 uncommitted paths remain in the work tree (other agents' scratch). Check `git status` before trusting them.
- **Packing that follows the global placement (d7f70a3, Finding 15 round 2):** cluster-aware detailed placement (dp4) cuts slices further (rv_soc 462 -> 440, Vivado 398), but Vivado-timed Fmax moves -5 / -4 / +3 %, inside the seed spread. Conclusion: the remaining gap is global placement plus the delay model, not slice composition. The dp2dp seeds 2-3 Vivado runs are pending (build/qor/dpl/xsrc).
- **Router final (6f0d60f):** Vivado timer, 3 seeds: critSeedDelay+critRipupIters average +1.9 % (rv_soc 0.0, rv_mul +4.0, rv_big +0.5, bram +3.1 %). Small, design-dependent, stays opt-in. The rv_soc critRipupIters=3 run was cut off; rerun it.

## Router + packing session 2026-11-08 (router/dpl agent)
- **Router share is ~5 %, not 15-20 %** (Finding 16, Vivado timer, exact placement via xroute, 3 seeds x 4 designs): Vivado routing the identical placement is +4.9 % on average (rv_soc +3.7, rv_mul +5.4, rv_big +4.7, bram +5.7 %). The 15-20 % came from place_xtime imports with the qor_xtime cell-miss bug (fixed efcb64f).
- Per-arc tool (vivado/build_rte.tcl RTE_ROUTE_DUMP=1, flow/rte_dump_vivado.sh, flow/route_arcs.py): LUT route-throughs (free in the chipdb) carry most of nextpnr's excess delay on the CPUs' critical arcs; Vivado uses none. Draft `-o no-lut-routethru` (nextpnr-router-timing.patch, opt-in, no-op on 4 designs): +2.0/+1.8/+2.4/-1.0 % (rv_soc/rv_mul/rv_big/bram, 3 seeds), router2 faster. Not a default yet.
- rv_soc critRipupIters=3 s1 finished: identical routes to the base (keep-best), 101.40 MHz.
- **carry-di-bypass**: re-timed with the fixed export, +1.7 % mean Fmax, slices -6..-16 %, no-op on a carry-free design (fir), rv_soc decode+sim 3/3 seeds. Proposed as default (Finding 15 round 3); eth re-timed: 0.0 %, slices -2 %. dp2dp re-timed: no gain over dp1.
- Vivado slot rules now: slot 2 = global placer only; my runners take slot 1 only.
- **Evening 2026-11-08 (router/dpl agent):** (1) flow/exact_src.py = exact placement import for Vivado (the dpl/place "placed" mode is 7-21 % optimistic: it drops nextpnr's feed-through LUTs/split carries, leaves LUT-RAMs and LUT pins to Vivado). (2) With it, carry-di-bypass is -1.0 % mean Fmax, so the ofx default went back to off (822fe36); patch 0031 stays opt-in; release patch 0032 (fixes agent) committed, TREE 591d1144. (3) Router share excluded LUT pin choice: with free pins Vivado routing is +17 % on rv_soc s1. LUT-pin drafts (docs/drafts/nextpnr-lut-a6-perm*.patch, chipdb variants build/chipdb-rcal-a6{,pd}): s1 exact-import Vivado gains lpA +3.0 %, lpB +5.5 %, lpAB +6.1 % mean on 4 designs; s2/s3 and `-o lut6-first` (lpX/lpXAB) queued (build/exact/lpa_viv2.sh, lpx_viv.sh). See docs/wip/router.md.

## WIND-DOWN 2026-11-08 ~22:30 (session 2 of the placement push)
Every agent finished its in-flight runs, committed docs/wip/*.md with resume commands, and stopped. Nothing pushed today after dbf3e37.

**Measurement:** use ONLY flow/exact_src.py (the exact import: Vivado only routes our implementation). It is validated: Vivado's own placement re-imported gives -1.713 vs -1.720 ns. Placed mode was 7-21 % optimistic, and Findings 15-17 placed-mode rows are superseded.
**Vivado reference** (same netlists, Vivado places itself: place_design + route_design, no opt/phys_opt): rv_soc 136.0
incl. ICAPE2 / **148.8 excl. ICAPE2** (the like-for-like number: our Fmax figures exclude ICAPE2), bram 164.1,
rv_big 110.9 MHz. cb_all2 6-seed means against it: rv_soc 116.2 (78 %), bram 147.6 (90 %), rv_big 98.0 (88 %).
Earlier "83 % of Vivado" for rv_soc used the incl.-ICAPE2 reference. rv_mul and syn2-netlist references: vref_add.sh.

**Results (Vivado timer, exact import):**
- Combined stack `cb_all` (tu10 + SA v4 + LUT pins + lut6-first) vs `cb_off`, 3 seeds:
  - rv_soc 107.1 -> 112.8 (+5.3 %, 83 % of Vivado);
  - bram 142.3 -> 147.6 (+3.7 %, 90 %);
  - rv_big 92.4 -> 94.1 (+1.8 %, 85 %);
  - rv_mul +4.1 % (2 seeds).
  - Commit 672ea50, docs/wip/placement-global.md "FINAL STATE".
- 2026-11-09: new best stack `cb_all2` = cb_all + `-o static-delay=816,40,40,18,18` (the user's alpha 816 ps with the
  measured y/x slopes): +2.6 % mean over 6 seeds x 4 designs (rv_soc +3.0, bram -0.1, rv_big +3.0, rv_mul +4.5).
  Equal LUT pin costs contradicted (-3.9 %); target util 0.75, 400 ps crit window, y-weighted HPWL neutral.
  docs/wip/user-assumptions.md. LUT-pin s1-s3 complete: lpXAB +7.7 %, 12/12 runs (docs/wip/router.md).
- 2026-11-09 evening: **cb_all2 promoted into the release (uncommitted working tree).** nextpnr patches 0033-0038
  (four combo layers + chipdb generator `--route-timing`, `--lut-a6-perm`/`--lut-pin-delay`), TREE 9488cf16, install.sh
  builds `share/nextpnr/himbaechel/xilinx/tuned/chipdb-<dev>.bin` (sha b913385a for xc7a50t), ofx/defaults.py key
  `placer_tuning` (default on, xc7a35t-1 only, static placer only, graceful off for old installs). Checks: key off =
  12/12 frames identical to rel04 (release prjxray-db); ofx default rv_soc frames identical to place_bench cb_all2;
  decode + firmware 11/11; blinky builds. Scratch build/promote_cb2/, test install ~/ofx-test/prefix-cb2.
  Caveats: install/gen_patch_series.sh is stale (lists 0001-0028 only; running it would delete 0029-0038); full
  release_regress.sh not run; the bench's rv_soc .frames are 0 bytes (nightly prjxray-db lacks ICAP.IN_USE), so
  rv_soc no-op checks must compare FASM or use the release prjxray-db.
- 2026-11-09 evening: **static placer + partition pins fixed** (docs/drafts/nextpnr-static-preplaced.patch + .md,
  worktree build/src/nextpnr-dfxfix, binary build/nextpnr-build/dfxfix, evidence build/dfxfix/). Cause: carry clusters
  pinned only in part by `-o preplaced` (free root -> pinned members bound twice; pinned root -> unpinned DI
  feed-through LUTs never placed). Flat no-op: FASM identical to cb_all2 on rv_soc + bram s1-3 (rechecked). rv_ppt
  partpin flow at s1-3 with pp3pl_tu and with cb_all2: every build completes, STATIC IDENTICAL / partpin_check pass,
  native_check 30/0, region2v SIM-PASS. `git apply --check` clean on the release tree (cb2rel).
  **Next:** add it as release patch 0039 after the running release_regress (build/promote_cb2/regress.log) finishes,
  rebuild the test install, rerun the regression. Open: HeAP also moves the pinned members of a free-root chain
  (place_constraints; same root-bel rule would fix it); sa-refine stays off under -o preplaced (its replay gate).
  2026-11-10 ~00:00: added as install/patches/nextpnr/0039 (TREE 114b9705); test install rebuild + full regression:
  build/promote_cb2/add_0039.log, regress_0039.log. **All 9 stages PASS** (revalidate first failed on rv_ppa only
  because the crash left 0-byte outputs that the skip logic reused; after removing that dir: PASS,
  regress_0039_reval.log). Release tree 0001-0039 + ofx placer_tuning default is ready to commit (not committed).
- 2026-11-09 23:16: **WSL crashed on a full C: drive** (ext4.vhdx 307 GB; the Bambu AppImage unpack tipped it).
  Cleaned (user-approved): old ~/ofx-test installs, ~/.cache uv/pip/huggingface, toolchain/dreamplacefpga, ~/ofx-rel01,
  ~/deployed-cnn-fpga; build/qor/oxc7 *.frames/*.bit/check *.db + routed JSON of variants older than 2026-11-08;
  *.bit and pre-11-08 *_routed.json in other build/ experiment dirs (not build/patched, build/openxc7); *.o of
  nextpnr builds older than 2026-11-08 (binaries kept). vhdx compacted to 182 GB, C: 150 GB free. After the restart
  \\wsl.localhost is broken on the Windows side (\\wsl$ works): Windows exes from a Linux cwd fail "Invalid argument";
  vivado/vivado_slot.sh now runs them from /mnt/c. dpl_check.sh's default DB prefix (~/ofx-test/prefix) is gone: pass
  DB=~/ofx-test/prefix-cb2/share/nextpnr/external/prjxray-db/artix7. Agents stop if C: < 40 GB free.
- 2026-11-10: **driver replication pass** (docs/drafts/nextpnr-replicate.patch + .md; worktree build/src/nextpnr-repl,
  binary build/nextpnr-build/repl; place_bench variants cb2_repl / cb2_repl_dq). No-op FASM identical; rv_soc
  decode + firmware 11/11 (s1, s3); copies 10-31 per design (bram 0). nextpnr timer ~flat; Vivado timing running
  (build/exact/repl_viv.log). Motivation: Vivado replication on our placements +7.9 % rv_soc (docs/wip/gap-analysis.md).
  dpl_check cannot decode DSP tiles (KeyError DSP_L): rv_mul/rv_big have no functional check that way.
- 2026-11-10: replication v2 (critical-cell, cc=1) rv_soc +5.1 % (3/3 seeds) but mean +0.2; carry-DI arcs in the
  chipdb (build/chipdb-rcal-a6pd-cdi) QoR-neutral, a correctness fix; global-placer timing weight sweep
  (tw10/tw20/ce1/tw20ce4) mean -2.2..+0.3, none adopted. All three help rv_soc and hurt rv_mul: a stronger timing
  pull stretches high-fanout critical arcs on rv_mul (dy 3 -> 10-14 rows) and the placer's estimate cannot see it
  (est. vs Vivado -8.6 % -> -16..-20 %). Details + tables: docs/wip/gap-analysis.md.
  Later the same night, all with the same split (none adopted): tw20ce4 + replication +1.2 % mean (rv_soc +6.7,
  rv_mul -4.0), + carry-DI chipdb +1.4 % (rv_soc +7.8 = 81 % of Vivado); fanout-aware arc delay (-o arc-fanout,
  worktree nextpnr-afo) K 100 +-0.0 %, K 200 -3.9 %; sa-refine chain-move effort / overlapping chain shifts
  (chainovl): no more chain moves accepted. rv_mul's losing paths all zig-zag between two carry chains whose
  relative position global placement fixes: chain-aware global placement / legalisation is the next real lever.
- 2026-11-10: **`seeds = N`** (ofx.toml; flow/build_openxc7.py --seeds): N seeds in parallel, keep the best routed
  Fmax. Best of 3 = +2.8 % mean Vivado-timed Fmax (all 4 designs up), best of 4 +3.7 %. Tested on axi_xbar (frames
  identical to a plain build of the kept seed); release_regress.sh ofx stage builds blinky with seeds = 2 (PASS,
  regress_seeds_ofx.log). Default 1 (user: default 3?).
  The draft generator fix for carry DI arcs is docs/drafts/nextpnr-carry-di-arcs.patch (release worktree
  build/src/nextpnr-cb2rel a4b08d86, not yet in install/patches: needs chipdb shas + full regression).
- LUT pins (packing agent, 84c601e), seed 1, A6 + per-pin delay + lut6-first ("full"): rv_soc +17.3 %, rv_mul +12.1 %, rv_big +11.0 %, bram +3.4 %. Seed 2: rv_soc +14.1 %. Seed 3 is pending. lut6-first=2 gives rv_soc +17.2 % and rv_mul +18.6 % (s1 only). The drafts need rebasing onto 0032; the A6 chipdb needs the patched binary.
- SA refine sa_v4 (`site=750:tile=850`) vs tu: rv_soc +6.0 %, rv_big +5.1 % (3/3 seeds each); bram s1 +0.9 %. Commits f59e01f, ddd2d29.
- Synthesis preset x1_cal_syn2 (216f796): rv_soc +17.3 %, rv_mul +12.4 %, rv_big flat, bram lower. Mixed on the QoR suite, so NOT a default. Idea: apply it only when LUT depth bounds the critical path. All 4 netlists verified (bram seq-equiv proven).
- carry-di-bypass: -1.0 % mean on the exact import, so its default is back to OFF (patch 0031 stays opt-in).
- Router share with free LUT pins is about +17 % on rv_soc. The LUT-input policy is the router-side lever.
- VPR (removed from disk) and DREAMPlaceFPGA (installed in toolchain/dreamplacefpga, no gain) are both dropped as placers. DREAMPlace showed that our LEGALISER loses its 21-30 % better global placement. Ring legaliser draft `nextpnr-legal-ring`: nextpnr-side only so far.
- Vivado-strategy rules: docs/vivado-placement-strategy.md (8df8702).
- DFX phase 17 (1e4c98a): greybox in anchors mode, multi-partition child runs, timed ICAP, USE_MULT bits. Partition pins disagree on Vivado's timer. The new placer options crash the partpin flow (reproducers in phase17 §3).
- Release fixes: rel03 prefix (all 21 suite designs build in the open flow, incl. fir/raygentop/diffeq2); patch 0032 SLICEM legality fix; TREE 591d1144.
- QoR scoreboard (33d92cc): PARTIAL; Fmax still on nextpnr's timer, so verdicts are too high. Run placedx (exact) first.

**Next session, in order:**
0. User decisions: commit the release tree 0001-0039 + placer_tuning + seeds; `seeds` default 1 or 3; carry-DI
   generator patch (docs/drafts/nextpnr-carry-di-arcs.patch) into the release (changes every chipdb sha).
0b. DONE 2026-11-10, not adopted: chain-aware global placement / legalisation (opt-in `chain-legal`, `chain-net-w`, `chain-snap`, `chain-rigid`, `chain-log` in worktree nextpnr-afo) all neutral, all lose rv_mul. Chains already stay rigid and close; the long hops are fanout-28 pcpi_rs1/rs2 FF -> first chain and second chain -> LUT3/LUT4/FF. Next lever: critical-cell replication of pcpi operand FFs (phys_opt-style), see gap-analysis "Carry chains in global placement".
1. LUT-pin rebase onto 0032 (s1-s3 done 2026-11-09); carry cb_all2 static-delay into the release defaults with it.
2. cb_all_syn2 exact (sources ready).
3. Ring legaliser exact + merge.
4. QoR scoreboard placedx.
5. DFX vs Vivado per-RM comparison (validation queue 1).
6. Remaining validation queues 2-9.
**Infrastructure:**
- 3 Vivado slots (vivado/vivado_slot.sh; slot 1 also needs >= 1.5 GB free).
- Memory: WSL page cache starves Windows; a drop_caches watcher helps. Consider lowering .wslconfig memory=12GB to about 9GB (user to decide).
**Leftover runners at wind-down (the user may stop them):**
- DFX queues build/dfxgaps/job_exact{p,q2,q3}.sh (the classifier refused the agent's kill);
- old-import qor quick variants (pdens/p16base, superseded);
- job_reg3.sh (nextpnr finishing).
