# WIP: tool build time vs Vivado (runtime workstream)

Status 2026-11-06 22:10: report written (docs/runtime.md), roadmap row updated. All committed.
Open items:
- Vivado runs with vivado/run_runtime.sh (low-priority back-off; never got the lock this session), then
  regenerate docs/runtime.md tables with flow/runtime_table.py.
- exit-bb draft (docs/drafts/nextpnr-exit-bb.*, build/nextpnr-build/rtbb): QoR seeds, rv_pr, ofx series.
- mc12_a100 heap placement/routing divergence -> placer workstream; static threshold in ofx/defaults.py.
- ofx/npwait.sh undercounts toolchain nextpnr (process name ld-linux-x86-64).
