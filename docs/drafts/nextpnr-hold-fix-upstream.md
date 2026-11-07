# nextpnr-hold-fix-upstream (draft, not posted)

Base: the release tree (install/patches/nextpnr, TREE 961ea46e; `git apply --check` passes on build/src/nextpnr-rel01).
Worktree build/src/nextpnr-hold (unstaged diff = this patch), build build/nextpnr-build/hold. 4 files:
common/kernel/timing.cc, himbaechel/arch.h, himbaechel/uarch/xilinx/hold_fix.cc, himbaechel/uarch/xilinx/xilinx.cc.
All opt-in.

## Problem
- Upstream openXC7's `-o hold-fix` (hold_fix.cc) fixes a hold violation on the path's last arc only: a detour, or a
  feed-through LUT. bufr's violating arc is a LUT5 O5 -> its own FF D inside one site: no detour exists and the
  slice has no free output mux, so the fixer gives up and the run ends with an error (release: hold slack -0.05 ns,
  nextpnr timer).
- The hold report's segments leave out the clock-to-clock delay of a related cross-clock pair, so the segments do not
  sum to the slack, and the fixer's deficit estimate was wrong (+0.42 read where the slack was -0.05).
- nextpnr has one routing delay for setup and hold (the slow max), so hold slack is optimistic.

## Change
- `-o hold-fix-upstream`: when the last arc cannot be fixed, detour an earlier arc of the same path; also sets
  `timing/holdSlackSegment`, which adds the missing clock-to-clock difference as one segment so the segments sum to
  the analyser's slack.
- `-o route-min-scale=K`: min routing delay = K x max for hold analysis (`timing/routeMinDelay`); K = 0.39 is
  Vivado's fast-min / slow-max ratio over 23.6k routed arcs (Finding 13 data). A clock pin keeps the max on both sides,
  so launch and capture clock routes are judged at the same corner.

## Evidence (nextpnr timer; build/qor/oxc7/hold_*/<design>/s1, flow/hold_bench.py)
- No-op: the hold binary without options gives FASM identical to the release binary on bufr, rv_soc and bram
  (`hold_bench.py --noop`, 2026-11-06).
- bufr (10 ns): release -0.05 ns, error exit; `hold-fix` alone leaves it (no output mux free); `hold-fix` +
  `hold-fix-upstream` +0.06 ns, rc 0 (1 detour on an earlier arc). With K = 0.39: -0.17 ns before, +0.02 ns after
  (6 detours, 4 on earlier arcs).
- rv_soc, bram (5 ns) with K = 0.39: no hold violation in nextpnr's timer. Vivado reports WHS -0.135 / -0.094 ns on
  the identical implementations (Finding 13): those come from cell hold arcs (RAMB36 hold 0.50-0.64 ns low, DSP48E1
  0.74 ns low), i.e. fast-corner cell timing, which this patch does not model.

## Open
- Vivado validation of bufr (Vivado timer on the identical implementation, hold_rel / hold_up / hold_msfix):
  exported (build/xroute/src/bufr_p10_hold_*_s1), not yet run.
- Fast-corner cell hold arcs (multi-corner work).
- An "unroutable AFFMUX with many buffers" case was reported by the previous owner; no reproducing build was found
  in the tree (no log mentions AFFMUX), so it is not addressed here.

## x_iodly_minmax (input hold from `set_input_delay -min 1`; nextpnr timer, hold binary, release chipdb; build/rte/iodly/)
- Without the fixer the four input registers fail hold (docs/xdc-coverage.md: -0.10 to -0.63 ns).
- `-o hold-fix -o hold-fix-upstream`: 3 detours + 2 feed-through buffers, 0 hold violations left.
- With `-o route-min-scale=0.39` as well: 4 detours + 18 buffers over 5 passes, 0 left.
- Setup Fmax 72.34 MHz in all three runs (unchanged); the runs exit 1 only because the design's output delay fails
  setup (13.82 ns against the constraint), which Vivado also reports failing (docs/xdc-coverage.md, -3.76 ns).
- Not yet checked in Vivado's timer.
