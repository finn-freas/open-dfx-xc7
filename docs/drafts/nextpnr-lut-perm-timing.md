# nextpnr-lut-perm-timing (draft, not posted)

Base: the qorfix/qordsp stack on openXC7/nextpnr ce3f7c18 (build `qorperm` = `qordsp` + this patch; worktree
build/src/nextpnr-qorperm, build log build/nextpnr-build/qorperm.build2.log). +38/-0 in
himbaechel/uarch/xilinx/xilinx_place.cc and xilinx.cc. Opt-in: `-o lut-perm-timing`.

## Problem
router2 may enter a LUT through any of A1..A5 (LUT permutation pseudo pips: tile wire of pin j -> site wire of
pin i). After routing, `XilinxImpl::fixup_routing` moves the cell's port connections to the physical pins and
records the permutation in `X_ORIG_PORT_*`, but the net's routing still ends on site wire i through the
permutation pip. A permuted arc's sink pin wire (site wire j) is therefore not in `net->wires`, so
`Context::getNetinfoRouteDelay` cannot walk it and returns `predictArcDelay` instead of the routed delay.
Everything evaluated after `postRoute` is affected: the SDF (`--sdf`) and any later timing query. The Fmax
printed at the end and `--report` are not: they are computed before `fixup_routing` (checked: identical
report.json and Fmax with and without the option on 6 designs, build/xroute/npr/*_s1{,_perm}).

Measured on the 6 designs of docs/qor-vivado.md Finding 13: 51 (blinky) to 4931 (rv_big) LUT input hops are
permuted, i.e. 30-65 % of all LUT input arcs (flow/xroute.py rerun logs, build/xroute/npr/*_perm/nextpnr.log).

## Change
With `-o lut-perm-timing`, `fixup_routing` additionally unbinds the site wire reached through each non-identity
permutation pip and binds the identity permutation pip of the same tile wire (tile wire j -> site wire j), so
the routing ends on the wire of the pin the cell is now connected to. Pseudo pips only.

## Evidence
- Applies on build/src/nextpnr-qordsp (`patch --dry-run`); the result equals build/src/nextpnr-qorperm file for file.
- Without the option: FASM, SDF and report.json byte-identical to the `qordsp` binary on the same command (blinky,
  re-run 2026-11-06, build/xroute/verify/det; only the version header line differs). The stored FASMs in
  build/qor/oxc7 (03:54) have the same lines in another order, and today's `qordsp` reruns give the new order, not the
  stored one, so the order change does not come from the patch. build/xroute/npr/*_perm_off equal the source builds as
  sorted lines (blinky, rv_soc).
- With the option: FASM identical as a set of lines (only the order differs) on all 6 designs; every permuted
  hop rebound ("0 not" in each log).
- Effect on the SDF against Vivado on the identical implementation: docs/qor-vivado.md Finding 13.

## Open
- The same mismatch probably affects any other post-route consumer of `net->wires` (e.g. a post-route timing
  report or hold fixing run after `fixup_routing`); not checked.
