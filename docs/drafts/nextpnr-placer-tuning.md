# nextpnr-placer-tuning (draft, not posted)

Base: openXC7/nextpnr ce3f7c18 + the `ofx` series (install/patches/nextpnr/0001-0011) + nextpnr-hardblock-timing.
Applies with `git apply` on that stack (worktree build/src/nextpnr-place, 2026-11-06). 9 files, +106/-11.
Every option is off by default; without them the binary gives the same output as the base (No-op in docs/qor-vivado.md Finding 11).

## Problem
Vivado's timer on nextpnr's static-placer placement, with Vivado routing (flow/qor_xtime.py method), is 23 % (rv_soc)
and 9 % (bram) below Vivado placing the same yosys netlist (docs/qor-vivado.md Finding 3). Comparing Vivado's own
placement cell by cell (vivado/place_dump.tcl, flow/place_compare.py, Finding 11 of docs/qor-vivado.md) shows
nextpnr spreads the logic over more slices and in a tall narrow shape, with block RAMs fixed early.

## Change
Kernel (common/):
- `Context::setting_or(name, default)`: reads a setting without interning the name or storing the default, so an
  unset option leaves the IdString table and the settings as they were.
- `--tmg-crit-target F`, `--tmg-crit-floor C` (timing.cc `compute_criticality`): criticality from the slack against
  F times each clock's period instead of from the delay relative to the worst path. Failing endpoints map to
  [C, 1] by how far they fail, the rest to [0, C) by the fraction of the budget they leave. Applies to every user
  of the analyser (placers, timing-opt, router2). Pairs without a period (unrelated clocks) keep the old formula.
- `--placer-static-timingweight W`, `--placer-static-critexp E`: the static placer's arc weight `1 + W * crit^E`
  (was fixed at 5 and 2).
- `--placer-static-target-util U`: fillers fill U of the device (was a constant 0.7).
- `--placer-static-ip-wait L`: legalise block RAMs and DSPs only once the logic overlap is below L. Before, they were
  legalised as soon as their own overlap fell below 0.15, which on small-BRAM designs happens in the first ~7
  iterations, while the logic still overlaps 96 %.
- `--placer-static-overlap-stop S`: stop spreading and legalise the logic once its overlap is below S (was 0.1;
  the "stalled" exit stays at 2S).
- `--placer1-critexp`, `--placer1-timing-tradeoff`: placer1 / refinement crit exponent (8) and timing weight (0.5).

xilinx uarch:
- `-o static-hpwl-x=N`: wirelength weight of a horizontal step in the static placer and its refinement (was 2).
- `-o static-ff-area=A`: flip-flop area in slice-bel units (was 1.4).

## Evidence
All numbers and log paths: docs/qor-vivado.md Finding 11 (the "placement" section); per-run tables are made by
`python3 flow/place_bench.py --report ...` into build/qor/place/table_*.md.

## Open
- None of the options closes the gap; the best combination moves Vivado-timed rv_soc by a few percent.
- `--tmg-crit-target` was worse on bram and rv_big under Vivado's timer at 5 ns; not a default candidate.
