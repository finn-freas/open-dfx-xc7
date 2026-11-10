# WIP: queued Vivado comparisons (2026-11-08)

Runs every Vivado queue left over from 2026-11-07 (RESUME.md "Vivado queues NOT run"), one design per Vivado
invocation, Vivado slot 1 only (`vivado/vivado_slot.sh`, `VIV_SLOT1_ONLY=1`); slot 2 stays with the placement agents.

## Infrastructure (done)
- `vivado/vivado_slot.sh`: `VIV_SLOT1_ONLY=1` never takes slot 2.
- `vivado/slot_run.sh TAG SCRIPT SRCREL NAME...`: run_qor.ps1's layout without its "no other vivado.exe" check
  (that check fails whenever slot 2 is busy), one name per acquire.
- Lock logic moved to `vivado_acquire` in: docs/wip/dfx-gaps/job_vq.sh, vivado/run_dfx_rv.sh, flow/ip_vivado.sh,
  flow/vivado_polite.sh, vivado/run_polite.sh, vivado/run_xdctime_batches.sh, build/timing_rv/tmr_viv5.sh (untracked).

- 09:14 coordinator rule: the global placer's re-timing queue (build/qor/place/gp/vq/names.txt) goes first.
  `VIV_YIELD_PLACER_Q=1` makes `vivado_acquire` wait in 5-minute steps while any name there lacks
  build/place_xtime/<name>/status.txt. All my queues set it. job_vq.sh was restarted (it was waiting, no run of
  mine was active) with skips for finished designs.
- `-Slotted` switch on vivado/run_ddr3.ps1 and run_ddr3_phy_sim.ps1 skips their "no other vivado.exe" check.
- Chains (restart them with nohup setsid if the session dies; every step skips finished designs):
  docs/wip/dfx-gaps/job_vq.sh -> build/vq/chain_234.sh (q2-q4) -> build/vq/chain_5to9.sh (q5-q9). Logs in build/vq/.
  nextpnr side of q7: build/incr/q2.sh (OFX_MAX_NEXTPNR=1 through npwait), launched 09:17.

- 18:44 coordinator: queues moved to Vivado slot 3 (`VIV_SLOT=3` makes vivado_acquire call vivado_acquire3; set it
  BEFORE sourcing vivado_slot.sh). One slip: dsp_um_dynamic ran on slot 2 at 18:58 (env set after source); fixed
  in e04a77c, nothing else ran outside slot 1/3.

## STOPPED 2026-11-08 ~22:00 (wind-down). No runner, chain or wait loop of mine is left.

## Queue status
| # | queue | status | write-up |
|---|---|---|---|
| 1 | DFX (job_vq.sh) | DONE: dsp_um_* (3), dfx_dev_xc7a50t, dfx_dev_xc7a100t + die checks. PENDING: dfx_dev_xc7a200t, 16 dfx_xtime, dfx_rv_p10, dfx_rv_p5 | docs/phase16-dfx-gaps.md §4, §6, §7 |
| 2 | timer gaps (build/timing_rv/tmr_viv5.sh) | pending (not started) | docs/timing-reports.md |
| 3 | multi-corner (vivado/run_xdctime_batches.sh) | pending | corner_compare.py --collect |
| 4 | synthesis: qor_synx *_dirs (6 sources made: rv_soc_{ys,x1,x1_cal}_dirs, rv_big_{ys_dspq,dx1,dx1_cal}_dirs) + eth arty_eth_blockrule_free | pending; xaiger default undecided (no new evidence) | docs/wip/synthesis.md |
| 5 | IP (flow/ip_vivado_queue.sh) | pending | ip_compare.py |
| 6 | GTP (flow/gt_vivado_queue.sh) | pending | docs/gtp.md |
| 7 | incremental + xdc4 | nextpnr part (build/incr/q2.sh) DONE (log build/vq/q2_incr_nextpnr.log, not analysed); Vivado part pending (build/incr/viv_batches.sh, viv_xtime.sh) | docs/incremental.md |
| 8 | breadth (vivado/breadth_queue.sh, now WSL) | pending | docs/wip/breadth.md |
| 9 | RapidWright (build/vq/q9_rw.sh: rw_check then rw_vref) | pending | docs/rapidwright.md |

## Resume (each step skips finished designs)
```
cd ~/open-dfx-xc7
nohup setsid bash docs/wip/dfx-gaps/job_vq.sh > build/dfxgaps/job_vq.nohup 2>&1 < /dev/null &
nohup setsid bash build/vq/chain_234.sh > build/vq/chain_234.log 2>&1 < /dev/null &   # waits for job_vq
nohup setsid bash build/vq/chain_5to9.sh > build/vq/chain_5to9.log 2>&1 < /dev/null & # waits for chain_234
```
After DFX: `bash build/vq/die_check.sh xc7a200t xc7a200tsbg484-1`, `python3 flow/dfx_vivado_compare.py --json
build/dfxgaps/compare.json`. build/vq/*.sh, build/incr/*.sh and build/timing_rv/tmr_viv5.sh are untracked (build/).
