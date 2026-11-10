# nextpnr-combo-stack (draft, not posted)

One binary with the opt-in placement drafts on top of the release series, to test whether their gains add up.
Base: openXC7/nextpnr ce3f7c18 + install/patches/nextpnr 0001-0032 (tree = TREE 591d1144). Worktree
build/src/nextpnr-combo, one commit per layer; build build/nextpnr-build/combo (build/nextpnr-build/combo_build.sh,
cmake flags as the other himbaechel builds). The patch is the whole stack against the release tree.

Layers, in order:
1. docs/drafts/nextpnr-placer-delay-cal.patch (static-delay / predict-cal, anchored start, arc term, weighted
   preconditioner, y gradient). One rejected hunk (option registration in xilinx.cc) merged by hand.
2. docs/drafts/nextpnr-placer-density.patch without its detail_place.cc hunk (the release has no `-o dpl`): group
   target utilisation, RAM assignment, criticality quantile, driver-crit fanout, arc quad. One option-registration
   hunk merged by hand.
3. docs/drafts/nextpnr-lut-a6-perm.patch (`-o lut-a6-perm`, `-o lut6-first`; the A6 permutation pips and pin delays
   come from the chipdb build/chipdb-rcal-a6pd), applied cleanly.
4. docs/drafts/nextpnr-placer-sa-refine.patch at sa_v4 (`-o sa-refine`): sa_refine() is called right after
   replace_around_brams() in postPlace (the original follows `dpl`, absent here). Three hunks merged by hand.

No-op: with no option, `.frames` identical to the release binary build/nextpnr-build/rel04 (= TREE) on rv_soc and bram,
seeds 1-3, route-calibrated chipdb (flow/place_bench.py rel_off_rcal vs cb_off_rcal). The release binary cannot be
compared on chipdb-rcal-a6pd: without `-o lut-a6-perm` its router takes the A6 permutation pips and the FASM writer
stops (`X_ORIG_PORT_A6 names logical input ''`); the combo binary's lut-a6-perm layer guards that.

Variants (flow/place_bench.py, chipdb-rcal-a6pd): cb_off (none), cb_lp (`lut-a6-perm`, `lut6-first`), cb_all (tu10
= `--placer-static-anchor-init 20 --placer-static-ip-wait 0.5 --placer-static-target-util 1.0`, `-o sa-refine=
t0=0.01:quant=0.002:exp=8:rmin=3:pcent=0.6:site=750:tile=850:alpha=313:beta=1.235` (SA's sa4 keys with the
route-calibrated fit of the arc model), `lut-a6-perm`, `lut6-first`). rv_mul uses the dspq netlist (`_dq`).
Results: docs/qor-vivado.md Finding 17 (exact import, Vivado timer).
