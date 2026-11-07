# nextpnr-router-timing (draft, not posted)

Base: the release tree (install/patches/nextpnr, TREE 961ea46e; `git apply --check` on build/src/nextpnr-rel01).
Worktree build/src/nextpnr-rte, build build/nextpnr-build/rte (runs use the copy build/nextpnr-build/rte-run).
Files: common/kernel/command.cc, common/route/router2.{cc,h}, himbaechel/uarch/xilinx/xilinx.{cc,h}.
Everything is opt-in; without the options the router and placer behave as before.

## Changes
- `-o place-import=FILE` (xilinx): after packing, bind the cells listed as `<cell>\t<bel>` to those bels, locked,
  where the bel is free and the tile stays legal; a cluster (carry chain) is bound as a whole at its root's bel or not
  at all; the placer places the rest. Used to route another tool's (Vivado's) placement with nextpnr's router
  (flow/route_xtime.py writes the file from Vivado's cell LOC/BEL dump). Up to 10 cluster failures are logged with
  the reason.
- `--router2-opt KEY=VALUE` (repeatable): sets `router2/KEY`, so router settings need no new command-line flag each.
- router2 settings (defaults = the current behaviour):
  - `critSeedDelay=F` (0): a forward search seed on the net's existing routing costs F x criticality x that wire's
    routed delay from the source (ns). Before, every existing wire of the net was a free start, so a critical arc
    branched off whatever tree was nearby, however slow that tree's path from the source was.
  - `critRipupIters=N` (0), `critRipupThresh=T` (0.9), `critRipupResetCong` (1), `critRipupKeepBest` (1): once
    routing is legal, N rounds rip up every net with an arc at criticality >= T (criticality from the routed delays)
    and negotiate again; the best legal routing by worst setup slack is kept (a snapshot of every arc's wires,
    restored through router2's own bind functions, so congestion bookkeeping stays exact). A partial rip-up of a net
    tripped router2's tree reconstruction assertion, so the whole net is ripped, as `--tmg-ripup` does.
  - `critExp` (2), `critFloor` (0.05): crit_weight = max(floor, 1 - crit^exp).
  - `critEstWeight` (-1 = off), `critEstThresh` (0.9): A* estimate weight for arcs at or above the threshold.

## Evidence
See docs/qor-vivado.md Finding 16 for the Vivado-timed results. No-op and runtime checks are listed there.

## No-op
Built without options (build/nextpnr-build/rte-run), FASM (sorted, comments dropped) identical to the release binary
build/nextpnr-build/rel01 on rv_soc, rv_mul, rv_big and bram (calibrated chipdb, static placer, seed 1, 5 ns;
build/rte/noop/, 2026-11-06).
