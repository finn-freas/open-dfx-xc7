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
