# Draft: a pblock member is not a "new cell" in a tile that replay closed

Status: **draft. Compiled and run offline on 2026-11-05; not on hardware, not reviewed upstream.**
Nothing has been pushed or posted, and nothing was committed: the patch is `git diff` output.

- Patch: `docs/drafts/nextpnr-pblock-replay.patch`, against `router-region` (`e62fafd1`), one file,
  `himbaechel/uarch/xilinx/xilinx_place.cc`, +13/-2.
- Build: `VARIANT=replay BASE_REV=e62fafd1 PATCHES=nextpnr-pblock-replay.patch DRY_RUN=0 bash toolchain/buildenv/build_nextpnr_variant.sh`
  (worktree `build/src/nextpnr-replay`, binary `build/nextpnr-build/replay/nextpnr-himbaechel`, `--version` prints
  `e62fafd1-replay`, log `build/nextpnr-build/replay.build.log`). The only compiler warning is the pre-existing
  `xilinx.cc:1240` `-Wsign-compare`.
- `flow/build_pr_native.py` uses it as variant `replay`, the default for design `rv_m`.

## Problem (found by run)

`-o prerouted` (the replay of the static design) closes every logic and block-RAM tile that a reference route passes
through, and the tiles beside an interconnect tile whose site-pin wires (`IMUX`, `BYP`, `FAN`, `CTRL`, `GFAN`) a reference
route uses (`close_routed_tiles`, xilinx.cc 810-881). `isBelLocationValid` then rejects any cell in such a tile that has no
`BEL` attribute (xilinx_place.cc 664-688).

In the native PR flow the static nets that feed the partition pins are replayed up to the anchor LUT inputs inside the
pblock, so the anchor tiles are closed. The anchors themselves carry `BEL`, but RM cells that the packer puts into the
same slice do not:

- `rv_m`, RM `tbl` (`designs/rv_soc/pr/rm_core_tbl.v`): the registers `r <= valid` and `f <= funct[0]` are packed as
  `AFF`/`BFF` into the slice of the anchors `ain_valid_0`/`ain_funct_0` (`SLICE_X8Y121`, from
  `build/patched/rv_m_native/router/tbl_a/rv_soc_routed.json`).
- The replay build then stops with
  `ERROR: Bel 'X23Y30/SLICE_X0Y0.A6LUT' of type 'SLICE_LUTX' is not valid for cell 'u_rm.ain_valid_0'`
  (`build/patched/rv_m_native/router/tbl_n/nextpnr.log`; the same error in `router_nokeepout/tbl_n`).
- The combinational RMs of `rv_pr`/`rv_b`/`rv_c` never put an RM cell next to an anchor, so they did not hit this.

## Change

A cell that is a member of an `EXCLUDE_PLACEMENT` pblock and sits on one of that pblock's own bels is not counted as
new. Static cells cannot use those bels anyway (the exclusion check below it), and the reference routes that close such
a tile are the static ends of the partition pins.

## Results (2026-11-05)

- `rv_m` replay builds `tbl_n`, `tbl2_n`, `xorc_n` all complete with this binary
  (`build/patched/rv_m_native/replay/*/nextpnr.log`). Results: `docs/phase9-native-bram-dsp.md`.
- No pblock, or a cell outside every pblock: the function returns as before (the new test is guarded by
  `ci->region != nullptr` and a non-empty `exclusive_pblock_bels`).

## Not checked

- A reference route that uses a **route-through LUT** inside the pblock, in the slice an RM cell then takes. With
  `--router2-region-keep-out` no static route uses pblock tiles except the partition-pin ends, so this did not arise;
  without keep-out it could, and the conflict would show only when the router binds the locked pip.
- Block-RAM tiles: the same rule now admits a pblock-member BRAM in a closed BRAM tile. Not exercised separately.
- Not compared with Vivado: Vivado's DFX flow locks the static routing and has no notion of closed tiles.
