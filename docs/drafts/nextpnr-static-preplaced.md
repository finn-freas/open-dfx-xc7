# nextpnr-static-preplaced (draft, not posted)

Base: build/src/nextpnr-combo HEAD 51875c16 (release 0001-0032 + placer-delay-cal + placer-density + lut-a6-perm +
placer-sa-refine, docs/drafts/nextpnr-combo-stack.md); applies with `git apply` there. Worktree
build/src/nextpnr-dfxfix (uncommitted diff = this patch), build build/nextpnr-build/dfxfix
(build/nextpnr-build/dfxfix_build.sh, combo's cmake flags, ninja -j4). One file: common/place/placer_static.cc.
Fixes the two aborts of the static placer in the partition-pin flow (docs/phase17-dfx-quality.md §3).

## Root causes
Both come from clusters that `-o preplaced` (BEL attributes) pins only in part. The static placer bound each named
cell and nothing else; HeAP got the "pinned root carries its members" rule in the release ("placer_heap: constraints
as a set"), the static placer never did.
- **grey_s, `entry == nullptr` (base_arch.h:156).** A carry chain that runs through a boundary endpoint slice is pinned
  in that slice only (ppt_tu/seed2: slice[6] of the 8-slice chain `replace_alu$8447`, root slice[0] free). The strict
  legaliser placed the free root with getClusterPlacement and bound the pinned slice[6] CARRY4 and LUTs a second time
  at the root's new position (bindBel does not check that the cell already has a bel). Their pinned bels kept stale
  bindings; the SA refinement (placer1) then bound another cell to one of them and hit the assertion.
- **`<rm>_n`, `bel != BelId()` (nextpnr_types.cc:192, router2 setup).** The pinned root of a carry chain has members the
  file does not name (the packer's DI feed-through LUTs, `...$PACKED_CARRY4$$DI[n]`: 32 in add_n, 11 in rot_n). The
  legaliser places a cluster only through its root, and the root is fixed (it has a bel), so the members are never
  placed; the placer1 refinement moves only roots too: they reach the router without a bel.
- Latent, same area: the legaliser's rip-up (non-cluster path) ripped up any unclustered cell, pinned ones
  (STRENGTH_USER) included; in a tile closed by `-o preplaced` the move is refused and the pinned cell is rebound with
  STRENGTH_WEAK, after which placer1, lut6-first and sa-refine see it as movable.

## Changes (placer_static.cc)
- `prepare_cells`: a BEL attribute naming an unknown bel, a bel of the wrong type or a taken bel is a log_error naming
  the cells (was NPNR_ASSERT). Then `place_pinned_clusters`: for every cluster with a pinned member, the root's bel is
  the pinned root's, or, for a free root, the bel in the tile at (member - cluster offset) whose getClusterPlacement
  keeps every bound member on its bel; the members without a bel are bound there with STRENGTH_USER. No such root bel,
  or a wanted bel held by another cell: log_error. Logged as "Placed N cluster member(s) with their pinned cluster."
- Strict legaliser: rip-up skips cells bound stronger than STRENGTH_STRONG; a cluster candidate fails when one of its
  members already has a bel (no cell is bound twice).
- Unchanged, checked: lut6-first skips clustered cells and strength >= LOCKED; sa-refine's fixed() is strength > STRONG
  or a region, every move is checked with isBelLocationValid, and it is off under `-o preplaced`/`-o prerouted`
  (sa_refine.cc, sa_v4), so in partition-pin builds it does not run (the anchor flow's BEL attributes keep it on).

## Evidence (build/dfxfix/)
- Reproduced on the combo binary with the cb_all2 options (flow/place_bench.py), phase 17 inputs, chipdb-rcal-a6pd
  (`repro.sh`): grey_s ppt_tu/seed2 `entry == nullptr`, add_n ppt_tu/seed1 `bel != BelId()`. Same inputs, fixed binary:
  both place and route; grey_s: 139 pinned cells on union_p's bels, 63 members carried; add_n: 2622 pinned cells kept,
  32 carried. (Both FAIL 100 MHz on the route-calibrated chipdb with the static paths pre-routed: HeAP gives the same
  86.01 MHz on add_n.)
- Same DFX flow, combo vs fixed binary, pp3pl_tu options (`dfx/combo_tu/seed2`): union_p `.frames` identical, combo
  aborts in grey_s (`entry == nullptr`).
- No-op on flat designs: place_bench `cb_all2` (combo) vs `dfx_all2` (this binary), rv_soc and bram seeds 1-3:
  `.frames` 6/6 IDENTICAL (`bench_noop.out`).
- rv_ppt, whole partition-pin flow (`dfx_run.py`; the release stack writes CFG_CENTER_MID ICAP.IN_USE, so fasm2frames
  and the checks use build/prjxray-db-prim-xadc):
  - `dfxfix_tu` (pp3pl_tu options, stock chipdb), seeds 1-3: all builds complete; module pairs 6/6 and greybox
    `--hclk-full-column` 4/4 STATIC IDENTICAL OUTSIDE REGION; greybox strict 4/4 differ only in word 50 of 3 frames
    (the HCLK leaf, as phase 17 §4.3); partpin_check 4/4. nextpnr Fmax, ICAP timed: 140.13 / 137.55 / 133.80 MHz.
  - `dfxfix_cb` (cb_all2 + hardblock-timing + --timing-allow-fail, chipdb-rcal-a6pd, static_try_unfixed), seeds 1-3:
    all builds complete (both greybox modes; the unfixed one selected at every seed); module pairs 6/6, greybox
    `--hclk-full-column` 4/4 and partpin_check 4/4 at every seed; greybox strict 4/4 IDENTICAL at seeds 2 and 3, HCLK
    word only at seed 1. nextpnr Fmax on the route-calibrated chipdb: 100.42 / 100.40 / 92.91 MHz (rot_n 92.02 / 98.12
    / 92.91); the endpoint-mode greybox (`grey_s_cf0`, the phase 17 failure mode) carried 63 and 81 members at seeds 2
    and 3.
  - Pinned cells (`check_pinned.py`): grey_s's endpoint (and unfixed-mode) cells on union_p's bels at every seed;
    module builds differ from grey_s only in the module cells (33/33/41/153).
  - native_check on `dfxfix_tu` seed 1 (GREY, PARTPINS, proofs not run): 30 PASS, 0 FAIL (`native_check_dfxfix_tu_s1.log`,
    OFX_DB_ROOT=build/prjxray-db-prim-xadc): 20 partials gate+CRC+simulated exact, byteman 0 frames differ, region2v
    SIM-PASS on the 4 module bitstreams and the byteman results with a module target.
  - Anchor flow (rv_pr, `--rms xor andn add rot`, pp3pl_tu options, `dfx/anc_dfxfix_tu/seed1`): pr_check 6/6 STATIC
    IDENTICAL, nextpnr 127.29 MHz (the doc's anc_tu seed 1 value).

## Not fixed here
- HeAP has the free-root half of the problem: the combo binary's HeAP on the same grey_s input moves the 9 pinned cells
  of the slice[6] chain slice off union_p's bels (SLICE_X10Y72 -> SLICE_X4Y87; `repro/dfxfix_grey2_heap`); no abort,
  because no later bind hits the stale bels. The same root-bel rule in place_constraints would fix it.
- sa-refine stays off under `-o preplaced`; grey_s in endpoint mode has movable static cells it could refine.
