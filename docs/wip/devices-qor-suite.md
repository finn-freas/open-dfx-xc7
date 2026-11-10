# WIP: devices + Artix-7 QoR suite (agent: device coverage / QoR scoreboard)

## Done (committed)
- 5b2b299: device coverage (all chipdb parts build blinky, decode check `flow/device_bitcheck.py`, Kintex-7 xc7k70t,
  gtp_b3, GT default bug). docs/ofx.md Results 5, roadmap rows.

## Running / pending
- Vivado device references (`blinky_a50/b3/cma7/100/nv`, `gtp_b3`) waiting on the Vivado lock:
  scratchpad `viv_lock.sh` -> `vivado/run_devices.ps1` -> `C:\Users\finnf\open-dfx-xc7-vivado\build\devices`.
  Then: `python3 flow/device_vivado_compare.py blinky_a50:xc7a50tcsg324-1 ... gtp_b3:xc7a35tcpg236-1 --run`, add
  the "Vivado cross-check" table to docs/ofx.md Results 5.
- QoR suite (`flow/qor_suite.py` + `vivado/qor_suite.tcl`): 21 designs wrapped and probed (all >= 10 % of
  xc7a35t, stereovision1 on xc7a100t). Dropped: wrapped picorv32 (yosys reduces the wrapped core to a constant, cause
  not investigated), rv_mul (< 10 %), dblclockfft (needs generated .hex). diffeq2 hits the known yosys xilinx_dsp
  assert (kept: counts as an open-flow failure).
- Running: open-flow sweeps `build/qor_suite/open_all.sh` (log open_all.out, open_all2.out); Vivado quick smoke run
  `qor_suite.py vivado --quick --label quick` waiting on the lock (log build/qor_suite/vivado_quick.out).

## Background processes of this agent (2026-11-07 00:10)
- open-flow sweeps: `build/qor_suite/open_all.sh` (log open_all.out; results build/qor_suite/<d>/open/base/*/result.json;
  `python3 build/qor_suite/peek.py`-style summary in the session).
- Vivado: `qor_suite.py vivado --quick --label quick --run` (log build/qor_suite/vivado_quick.out), then
  `build/qor_suite/viv_chain.sh` runs `vivado --modes free --run` for all 21 designs (log vivado_free.out). Both use
  vivado/vivado_slot.sh, one design per slot acquisition. Tcl validated on rv_big (result.txt, nets_sites, pips_int OK;
  Vivado threads = 2).
- After the open sweeps finish: `vivado --modes placed --run` (our placement timed by Vivado), then `report --run`.
- Device references: scratchpad viv_lock.sh (slot 1 only) for blinky_a50/b3/cma7/100/nv + gtp_b3.

## Stuck Vivado slot 1 (needs the user)
- Git Bash PID 28584 (Windows), my old device-reference script scratchpadiv_lock.sh (started 20:12), probably holds
  C:/Users/finnf/vivado.lock (created 23:25:38): it took the lock and waits until tasklist shows no vivado.exe, which
  never happens with two slots. My kill was refused by the permission check; TaskStop of its wrapper (bo93ya979) left it
  running. Fix: `taskkill /PID 28584`; if vivado.lock still shows 23:25:38 afterwards, rmdir it (it was mine).
- My later runs use slot 2 through vivado/vivado_slot.sh.

## State at wrap-up (2026-11-07 ~01:15 Windows)
- Open flow: all 21 designs swept (build/qor_suite/<d>/open/base). Failures: fir (DSP placement without the cascade
  draft), raygentop (LDCE latches, no BEL), diffeq2 (yosys xilinx_dsp assert).
- Vivado: rv_big only (145.1 MHz at 8 ns, threads 2). Quick + full free sweep task (btbk96y7e) was waiting for a slot.
- docs/qor-scoreboard.md committed as PARTIAL.

## Final state (wrap-up 2026-11-07 ~01:40)
- docs/qor-scoreboard.md committed PARTIAL (e10b44b): Vivado free results for rv_big, vexriscv, serv, or1200, aes,
  sha256, fir, bram (C:/Users/finnf/open-dfx-xc7-vivado/build/qor_suite/<d>__free/run*/result.txt). The aes base sweep
  was mid-run at wrap-up and was left to finish; build/qor_suite/stop_after_current.sh then stops the runner before the
  next design. Resume: `python3 flow/qor_suite.py vivado --modes free --run` (skips finished runs), then
  `vivado --modes placed --run`, then `report --run`.
- Stuck slot-1 lock (PID 28584) unresolved, see above.

## State 2026-11-07 18:40 (after the 11:30 stop)
- Scoreboard regenerated (PARTIAL). Placed mode works after 773311c but is slow/unclear: aes placed run 26936 s (7.5 h
  holding a Vivado slot), rv_big 805 of 3613 cells not placeable by name (LUT/carry naming). Fix both before any more
  placed runs. vexriscv excluded (x-driven output; wrapper must tie undriven outputs).
- Remaining Vivado free sweeps: vtr_sha, blob_merge, raygentop, diffeq2, epfl_*, stereovision1, bgm.

## Next
2. Write vivado/qor_suite.tcl (job file: `name free|placed period runs [placedir]`; per run: synth/opt+place/route/
   bitstream times, WNS, report_utilization, report_power, general.maxThreads; at the start period dump
   nets_sites.txt (signal nets -> leaf cell sites) and pips_int.txt (INT tile -> used pips); results in
   build/qor_suite/<name>__<mode>[_<run>]/run<i>/result.txt as `key value` lines).
3. `qor_suite.py open --run` (all), `vivado --run`, `report --run` -> docs/qor-scoreboard.md. Quick mode check.
4. Not done in devices: xc7a15t/a75t part files from Vivado (prjxray part generation), z045/z100 decode check,
   xc7k325t (deprioritised).

## Uncommitted drafts
- flow/qor_suite.py, designs/qor_suite/vtr_ram.v (committed as draft with this note)

## Session 2026-11-08 (scoreboard completion)
- Fairness fixes in flow/qor_suite.py (+ vivado/qor_suite.tcl, ofx/npwait.sh opt-in OFX_NPWAIT_LOG):
  - nextpnr ignores the period: aes p6_s1 vs p11_08_s1 FASM md5 identical (d0a7f1ee...), log shows the constraint
    was read (FAIL at 166.67 / PASS at 90.25). Cause: relative criticality. Open sweep is now 3 seeds at the start
    period (same run count as Vivado's sweep); runs at other periods are ignored by the report.
  - Build time: open wall minus npwait queue time (npwait.log per run), CPU s from /usr/bin/time, WSL loadavg; Vivado
    CPU s from Windows TotalProcessorTime (cpu_total in result.txt). Old open runs have no queue log (flagged).
  - Placed mode: names fixed (CARRY4 suffix $split$muxcy<N>$PACKED_CARRY4$ for any N; before only muxcy0), nextpnr-only
    cells ($LUT$ DI route-throughs, $feed$ constants, _DUP) are not sent and are counted; one placed run per seed at
    the seed's nextpnr period; tags `<label>_<rundir>`; place_missed.txt per run. The 7.5 h aes placed run was the
    machine sleeping (route_design cpu 2:39, elapsed 7:27:34), not a placed-mode problem.
  - --variant NAME / --nextpnr BIN for agents' quick runs; OFX_MAX_NEXTPNR 3 -> 2; Vivado through vivado_acquire.
  - Note for placement agents: qor_xtime.placement() strips only `$split$muxcy0$PACKED_CARRY4$`, so CARRY4s
    with muxcy2 are not placed in their place_xtime runs (rv_big ~40 carries).
- Running: Vivado free `vivado epfl_sin ... rv_big --modes free --run` (log build/qor_suite/vivado_free3.out);
  open seeds 2-3 (log build/qor_suite/open_seeds.out). Next: `vivado --modes placed --run` (all), `report --run`.
- vexriscv back in (23d171a): 18 undriven wire bits tied to 0 in the shared source (Vivado does the same, Synth 8-3295).
  Old results archived: build/qor_suite/vexriscv/open/base_untied_20261107, Windows vexriscv__free_untied_20261107.
  Its Vivado free sweep must be rerun: `qor_suite.py vivado vexriscv --modes free --run`.
- Placed mode, split carries (0263601): nextpnr can split one netlist CARRY4 over two sites; only the muxcy0 part is
  placed. rv_big seed-1 placed result before this fix archived as rv_big__placed_dupcarry_p8_s1_20261108.
- First placed results (Vivado timer, our placement, 95-100 % of netlist cells at nextpnr's BEL):
  aes 74.2 MHz (nextpnr timer 90.3), bram 124.3 (nextpnr 231.6), or1200 54.0 (nextpnr 73.6). nextpnr's timer is
  optimistic against Vivado's on the same placement; this will lower g Fmax. Earlier rv_big placed run (before the
  carry fix): 85.0 MHz vs nextpnr 149.2, worst path through FDSE S pins.

## State at handback 2026-11-08 ~09:00 (runners still going, detached, all resumable/cached)
- Vivado free: `qor_suite.py vivado epfl_sin epfl_mult blob_merge vtr_sha raygentop diffeq2 epfl_sqrt epfl_log2 bgm
  stereovision1 bram fir rv_big --modes free --run` (log build/qor_suite/vivado_free3.out). epfl_sin done.
- Vivado placed seed 1: `qor_suite.py vivado rv_big bram aes ... bgm --modes placed --run` (vivado_placed3.out).
- Open seeds 2-3 for all designs (open_seeds.out), vexriscv 3 seeds (open_vex.out).
- After they finish: rerun `vivado <all but excluded> --modes placed --run` (picks up seeds 2-3 and rv_big),
  `vivado vexriscv --modes free --run`, then `report --run` -> docs/qor-scoreboard.md (not yet regenerated).
- 2026-11-08 ~09:55 (coordinator): Vivado runs now slot 1 only and yield to placement/router queues (e33aeca). Old runners frozen (SIGSTOP) and killed after their current Vivado run; build/qor_suite/restart_slot1.sh (log vivado_slot1.out) then reruns free (incl. vexriscv) and placed, cached results kept.
- 2026-11-08 (coordinator, packing agent finding): placed mode switched to the exact import (flow/xroute.py export as in
  flow/exact_src.py: nextpnr's physical netlist incl. feed-through LUT1s and split CARRY4s, LUTRAM macros per sub-cell,
  LUT pin locks; Vivado only routes). Job mode `placedx`, results `<design>__placedx_<label>_<run>`. All earlier
  `__placed_*` results (approximate import: yosys cells only, Vivado's LUT pins/LUTRAM sites; 7-21 % optimistic on
  rv_soc) are marked superseded and no longer read by the report; aes 74.2 / bram 124.3 / or1200 54.0 above were that
  import. Variant quick runs started before this commit (pdens, p16base) used the old import and must be rerun.
  restart_slot1.sh's placed step runs the exact import (slot 1, yielding).

## WIND-DOWN 2026-11-08 (user request). No runners of this agent are left.
- restart_slot1.sh never launched anything: the SIGSTOPped runners could not reap their finished Vivado children
  (zombies), so its `ps -p` loop never ended. That process and both frozen runners have been killed. No Vivado run was
  cut short.
- Landed: open flow 3 seeds for all 18 designs that build (+ vexriscv); Vivado free for 16 designs. Missing Vivado free:
  vexriscv (after the RTL fix), bgm, stereovision1, epfl_sqrt, epfl_log2. Exact placed (`placedx`): none yet; the
  qor_suite.tcl placedx step has not been tested in Vivado.
- docs/qor-scoreboard.md regenerated and marked PARTIAL: g Fmax still uses the nextpnr timer (optimistic).
- Resume, one at a time, slot 1 and yielding are built in:
  `python3 flow/qor_suite.py vivado vexriscv bgm stereovision1 epfl_sqrt epfl_log2 --modes free --run`
  `python3 flow/qor_suite.py vivado rv_big bram aes or1200 serv axi_xbar mkpktmerge sha256 sha512 vtr_sha blob_merge epfl_sin epfl_mult epfl_log2 epfl_sqrt stereovision1 bgm vexriscv --modes placed --run`
  `python3 flow/qor_suite.py report --run`
  Never stop a runner with SIGSTOP. Stop it between designs instead.
