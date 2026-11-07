# Draft: no LUT route-through of a pblock for a net that leaves it

Status: **draft. Compiled and run offline on 2026-11-05; not on hardware, not reviewed upstream.**
Nothing has been pushed or posted, and nothing was committed: the patch is `git diff` output.

- Patch: `docs/drafts/nextpnr-pblock-routethru.patch`, against `router-region` (`e62fafd1`) **plus**
  `nextpnr-pblock-replay.patch` (the worktree has that patch staged in its index; the file here is the unstaged diff on
  top of it). 3 files, +36/-1: `himbaechel/uarch/xilinx/{xilinx.h,xilinx.cc,xdc.cc}`.
- Worktree `build/src/nextpnr-rtkeep`, binary `build/nextpnr-build/rtkeep/nextpnr-himbaechel`, `--version` prints
  `e62fafd1-rtkeep`. Built with the commands of `toolchain/buildenv/build_nextpnr_variant.sh` (cmake flags identical) but
  `ninja -j3` instead of `-j8` because of the WSL memory limit; 132 s; log `build/nextpnr-build/rtkeep.build.log`,
  summary `build/nextpnr-build/rtkeep.out`. The only compiler warning is the pre-existing `-Wsign-compare` in
  `xilinx.cc` (line 1240 upstream, 1267 after this patch's 27 added lines).
- `flow/build_pr_native.py` uses it as variant `rtkeep`, the default for design `rv2` only.

## Does router2 need a change for two regions? No.

Read in `build/src/nextpnr-router/common/route/router2.cc` (branch `router-region`):

- `setup_route_regions()` loops over every `ctx->region` with `constr_pips`/`constr_wires`, gives each an index, and
  `log_error`s if two regions share a pip tile or a wire.
- An arc is held to its sink's region when its driver is in the same region (`contain_region`), so an RP1 net can only
  use RP1 pips.
- `--router2-region-keep-out` keeps every other arc out of every region except its driver's and its sink's
  (`hop_allowed_for_arc`). So a static net, and a boundary net of RP1, cannot enter RP2.
- The xilinx XDC reader keeps any number of pblocks (`dict<IdString, XdcPblock>`), refuses a cell in two pblocks, and
  `log_error`s on overlapping `EXCLUDE_PLACEMENT` pblocks.

Run on `rv2` (two pblocks): nextpnr prints `Routing regions: 2 region(s); 558 arc(s) held inside one, 282 arc(s)
cross a region edge` and `flow/region_pips.py` finds 0 static pips in either region and 0 RM pips outside its own region in all
7 builds, with both the `replay` and the `rtkeep` binary (`build/patched/rv2_native/{replay,rtkeep}/checks/pips_*.json`).
So router2 itself needed no change.

## Problem this patch fixes (found by run)

In the first `rv2` build with the `replay` binary (`build/patched/rv2_native/replay/xor_add_a`), two **boundary nets**
of RP2 (output anchor FF in the pblock, load in static) took a **LUT route-through** in a free LUT of RP2:

```
slot2_rd[10]: X33Y127/CLBLM_L_C/CLBLM_L_C1
slot2_rd[19]: X33Y128/CLBLM_L_D/CLBLM_L_D5
```

(`flow/routethru_scan.py`, `build/patched/rv2_native/routethru_scan/rv2_replay.log`; the same 2 pips in all 7 builds,
because the replay locks them.) Router2 allows this: the arc is not held (it crosses the edge) and keep-out lets it use
its driver's region. The xilinx `is_pip_unavail` only refuses a route-through when a cell already sits on the LUT.

Why it matters for partial reconfiguration:

- The flow replays boundary routes as static (`--keep` of the partition ports). The route-through therefore becomes
  locked static routing that **occupies a LUT of the reconfigurable module's area**. A later module for the same
  pblock could want that LUT; nothing told its placer the LUT was taken.
- `flow/region2v.py` cannot trace an output anchor through a LUT to the region edge, so it rejected the RP2 netlists:
  `output anchor q_rd_10 at CLBLM_R_X11Y26.SLICEL_X1.AQ reaches no output port`
  (`build/patched/partials/rv2/replay/rp2_*.r2v.log`).
- Scan of the earlier single-region builds (`build/patched/rv2_native/routethru_scan/{rv_pr,rv_b,rv_c,rv_m}.log`):
  0 such route-throughs on boundary or static nets in rv_pr (7 builds), rv_b, rv_c, rv_m (4 each). The case first
  appeared in rv2.

Whether Vivado allows a static or partition-pin route to use a LUT route-through inside an RP was **not checked**.

## Change

`XilinxImpl::checkPipAvailForNet` (which router2 calls in both search directions) now also refuses a
`PIP_LUT_ROUTETHRU` pip in a site tile of a pblock that contains its routing, unless the net's driver and every user are
members of that pblock. The site tiles are recorded in `add_pblock_routing_tiles` (`pblock_site_tiles`). With no such
pblock the new test returns at its first line.

## Results (2026-11-05)

- **No-op:** rv_soc with no pblock, same yosys JSON (`build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.json`):
  `.frames` byte-identical (`cmp`) to the `replay` binary and to `build/patched/baseline/rv_soc_stock`; FASM identical
  after the version line (`build/patched/rv2_native/noop/`).
- **rv2 with `rtkeep`** (`build/patched/rv2_native/rtkeep/`): 0 LUT route-throughs on boundary or static nets in
  regions in all 7 builds; 2–5 per build remain on nets held inside their region
  (`checks/routethru.log`). First build: router2 16.50 s, Fmax 142.35 MHz (the `replay` binary: 26.04 s,
  145.14 MHz; one seed each, not a benchmark).
- region2v now accepts the RP2 netlists; results in `docs/phase11-multi-rp.md`.

## Not checked

- `router1`, hold-fix detours and `route_clocks` do not call `checkPipAvailForNet` with this rule in mind; they were not
  exercised.
- A constant net (GND/VCC) has users everywhere, so it can never take a route-through in a pblock; no build needed one.
- Only LUT route-throughs are covered. Other site-internal pass-throughs (e.g. through a flip-flop bypass) were not
  examined.
