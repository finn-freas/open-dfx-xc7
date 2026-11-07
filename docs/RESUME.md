# Where to resume (updated 2026-11-06 night, long run)

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
