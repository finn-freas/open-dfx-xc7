# Draft: pblock commands in the openXC7 nextpnr XDC parser

Status: **draft. Compiled and run offline on 2026-11-05 (results at the end of this file); not on
hardware, not reviewed upstream.** It lives on the local branch `pblock-xdc`
(commit `5a62e6e8`, based on `ce3f7c18`) in `upstream/openXC7_nextpnr`. Nothing has
been pushed or posted anywhere. Patch: `docs/drafts/nextpnr-pblock-xdc.patch`
(`git format-patch` output, 5 files, about +440/-4 lines).

Line numbers below are for `ce3f7c18` unless marked "branch".

## What it adds

```tcl
create_pblock pblock_rm
add_cells_to_pblock [get_pblocks pblock_rm] [get_cells u_rm]
resize_pblock [get_pblocks pblock_rm] -add {SLICE_X12Y100:SLICE_X15Y149}
set_property EXCLUDE_PLACEMENT true [get_pblocks pblock_rm]   ;# optional: exclusive
```

| Command | Behaviour in the patch |
|---|---|
| `create_pblock <name>` | Creates an empty `Region` of that name with `constr_bels = false`, so it constrains nothing until it has a site. Reusing a pblock or region name is an error. |
| `add_cells_to_pblock [get_pblocks p] <sel>...` | `<sel>` uses the same forms as the existing `get_cells` lambda (`[get_cells name]`, `[get_cells -hier name]`, quoted or braced names, `get_ports`). An exact leaf-cell name wins. Otherwise the name is treated as a hierarchical instance (see below). A cell can be in only one pblock (error otherwise). `-top`, `-add_primitives` and `-clear` are errors. |
| `resize_pblock [get_pblocks p] -add {R1 R2 ...}` | Each range is `TYPE_XaYb:TYPE_XcYd`, or a single site. It takes every bel whose **site** has that name prefix and site X/Y coordinates inside the range. `-add` can be repeated. `-remove`, `-locs` and `-replace` are errors. |
| `set_property EXCLUDE_PLACEMENT true [get_pblocks p]` | Makes the pblock exclusive (see below). Any other property on `[get_pblocks]`, such as `RESET_AFTER_RECONFIG` or `SNAPPING_MODE` from `designs/dfx_ref/pblock.xdc`, now gets a warning and is ignored. Before this patch such a line hit `log_error` in `get_cells` (xdc.cc:118-120). |

Files touched: `xdc.cc` (parser and the post-pack pass), `xilinx.h` (state),
`xilinx_place.cc` (exclusion check), `bram_place.cc` (region check), `pack.cc`
(one call).

## How nextpnr regions work (evidence)

- `Region` holds `constr_bels/constr_wires/constr_pips` plus a `pool<BelId> bels`
  (common/kernel/nextpnr_types.h:53-64). `CellInfo::testRegion` passes when the cell has
  no region, when `!constr_bels`, or when the bel is in `bels` (nextpnr_types.cc:56-59).
- `createRectangularRegion` adds every bel of every tile in the grid box, using
  `getBelsByTile(x, y)`, and sets `constr_wires`/`constr_pips` to false
  (common/kernel/basectx.cc:114-128). `constrainCellToRegion` sets `cell->region`, or
  walks `ctx->hierarchy` (basectx.cc:130-147).
- **Routing ignores regions.** `constr_wires`/`constr_pips`/`piplocs` are written only at
  basectx.cc:119-120 and declared in nextpnr_types.h:58-63. A grep over `common/` and
  `himbaechel/` finds no reader.
- **Placers only keep members in.** Heap is the default placer (himbaechel/arch.cc:444).
  It computes a bounding box per region (placer_heap.cc:584-600), clamps solver results
  (placer_heap.cc:1037-1045) and the legaliser search box (1334-1345) to it, and calls
  `testRegion` for single cells (1357) and for **every target of a cluster** (1444). The
  SA placer does the same (placer1.cc:443, 686, 775), as do static (placer_static.cc:289,
  1431, 1511, 1582), place_common.cc:368 and parallel_refine.cc:235. **Nothing keeps a
  cell with no region out of a region.** The kernel cannot exclude.
- Every placer binds a bel and then calls `isBelLocationValid(bel)`: placer_heap.cc:1376,
  1484 and the final check at 542; placer1.cc:176/398/456/522; place_common.cc:381. So
  do the uarch's own placers: bram_place.cc:283 and hold_fix.cc:299. The uarch already
  uses that hook to close tiles (`frozen_tiles`, xilinx_place.cc:666-691, xilinx.h:188).
  The exclusion check copies that pattern.

## Design decisions

1. **Site ranges are matched by site name, not the tile grid.** The chipdb tile (x,y) is
   prjxray's `grid_x/grid_y` (gen/xilinx_device.py:489-495, gen/xilinx_gen.py:587;
   `Loc` = tile % width, tile / width, himbaechel/arch.h:71-74, 507-510). From
   `prjxray-db/artix7/xc7a50t/tilegrid.json` (the 35t uses the 50t chipdb):
   SLICE_X12Y100 and X13Y100 sit in CLBLM_L_X10Y100 at grid (30,51), X14/X15Y100 in
   CLBLM_R_X11Y100 at (33,51), X12Y149 in CLBLM_L_X10Y149 at (30,1), and X15Y149 in
   CLBLM_R_X11Y149 at (33,1). So the equivalent `createRectangularRegion` is x 30..33,
   y 1..51, with grid y running opposite to site Y. That box also covers the INT_L/INT_R
   columns 31-32 and any rows in between. A box that crosses a BRAM or DSP column (DSP_R
   at x=28 nearby) would also take those bels, which Vivado's SLICE range does not. The
   patch reads each bel's `SiteInstPOD{name_prefix, site_x, site_y}`
   (uarch/xilinx/extra_data.h:62-68; it is the source of `get_site_name`, xilinx.cc:227-231)
   and uses the same bel→site walk as `apply_loc_constraints` (xilinx.cc:596-607). The
   result: a SLICE range contains only SLICE bels, and a BRAM needs a `RAMB18_*` or
   `RAMB36_*` range. A member with no bel of its type in its pblock is a clear `log_error`
   after packing. Without that check the placer would just fail.
2. **Hierarchy matching.** The flattened JSON has no hierarchy: nextpnr's frontend builds
   `ctx->hierarchy` only from unflattened submodules (frontend/frontend_base.h:271-275,
   542) and skips `$scopeinfo` cells (frontend_base.h:456). So `[get_cells u_rm]` matches
   no cell, and the existing lambda silently ignores it. With `expand_hierarchy` the patch
   takes (a) cells named `u_rm.*` (`/` is accepted as the separator and mapped to `.`), and
   (b) cells whose `scopename` attribute is `u_rm` or `u_rm ...`. Attributes are copied to
   `ci->attrs` (frontend_base.h:503). Evidence for (a):
   `build/openxc7/pr_open/cfg_count/top.json` has `u_rm.ain0` (LUT1, hdlname `u_rm ain0`),
   `u_rm.core.l0`, `u_rm.q0` (FDRE), and those names survive packing (`top_routed.json`:
   `u_rm.core.l0` SLICE_LUTX at SLICE_X13Y121/A6LUT).
3. **Order relative to packing, and clusters.** `parse_xdc` runs **before** packing
   (pack.cc:1533-1536), so the XDC constrains pre-pack netlist cells. Packing then
   - transforms most cells in place (`xform_cell`, pack.cc:51), which keeps `region`;
   - creates new cells: carry split `<cell>$split$xorcy/muxcy` (pack_carry.cc:90-91), new
     `<muxcy>$PACKED_CARRY4$` (pack_carry.cc:224), `$S_DUP` (pack_carry.cc:343), feed-through
     LUTs/MUXes (pack.cc:136, 153), DRAM cells (pack_dram.cc:53, 85). It deletes the
     originals (pack.cc:39-48). Only the LUT6_2 split copies `region` today (pack.cc:258);
   - forms clusters that the placer moves by root. pack_clocking.cc:561-566 makes the same
     point and constrains the root.

   So `apply_pblocks_after_packing()` (branch xdc.cc:816) runs right after
   `pack_lutffs()` (branch pack.cc:1573) and **before** the BUFR/BUFIO pass. That pass
   only constrains a root whose `region == nullptr` (pack_clocking.cc:567), so it leaves
   pblock cells alone. The new function:
   (i) gives a packer-made cell the pblock of the longest pre-pack cell name that is a
   `$`-delimited prefix of its own name. This uses a name→pblock record taken at the end
   of `parse_xdc`;
   (ii) puts every cell of a cluster into its members' pblock. A cluster spanning two
   pblocks is an error. A *pre-pack* cell from outside that gets pulled in is counted in a
   warning (`-v` lists them);
   (iii) runs the type-coverage check;
   (iv) builds the exclusive bel map. The patch puts the region on every cluster member,
   not only the root, because the heap legaliser tests every target (placer_heap.cc:1444).
4. **Exclusion (flagged: my design, not a kernel feature).** I considered constraining
   every non-member cell to a complement region. I rejected it for three reasons: a cell
   has only one region, so it would clash with the clock-region constraints (pack_clocking.cc:569);
   it would not cover cells created later (hold-fix buffers, hold_fix.cc:270-300); and its
   bounding box would be the whole die anyway. Instead, `isBelLocationValid` rejects a bel
   in an exclusive pblock when the cell bound there has a different region (branch
   xilinx_place.cc:692-700). There is one `dict` lookup, guarded by `empty()`. Because
   every placer and the uarch's BRAM and hold-fix placers call this hook after binding,
   one check covers them all. Cells that packing already bound inside an exclusive pblock
   are reported as an error. Overlapping exclusive pblocks are an error.
5. `bram_place.cc` regrows block RAM groups after the heap placement. It bound sites
   checking only availability, type and location validity (bram_place.cc:278-290), so it
   could move a pblock BRAM out. It now also calls `testRegion` (branch bram_place.cc:279-281).

## What is NOT verified or not handled

- **Not compiled with real dependencies and never executed.** There is no boost or eigen,
  and nextpnr could not be built. I ran `g++ 15.2 -std=c++17 -fsyntax-only -Wall -Wextra`
  against **hand-written boost stand-in headers**, written to a scratch directory only. It
  ran on `xdc.cc`, `xilinx_place.cc`, `bram_place.cc`, `pack.cc`, `xilinx.cc` and
  `pack_clocking.cc`, with no errors and no new warnings. The only extra flags were
  `-include cmath -include climits`, which pre-existing code gets through boost. This
  checks syntax and types of the new code (which uses no boost). It says nothing about
  linking or behaviour.
- **Yosys naming limits hierarchy matching.** This is checked with the bundled yosys
  0.70+186 and `synth_xilinx -flatten -abc9`. Inferred logic inside `u_rm` comes out as
  `$abc$...` LUTs, `$auto$alumacc...carry4` and `$auto$ff.cc...` FDREs, with no `u_rm`
  in the name and no `hdlname`. With `flatten -scopename` run before `synth_xilinx`, only
  the FDREs carried `scopename "u_rm core"`; the LUTs and CARRY4 did not. Only
  explicitly instantiated, named primitives (as in `designs/pr_open`) are reliably found.
  An RM synthesized out of context, or a yosys-side fix, is needed for real designs.
- Packer-made cells that are neither named after their source nor clustered with a
  member stay outside the pblock. Examples: MUX feed-throughs named `net$MUX$cell$...`
  (pack.cc:153), and DRAM cells, whose names I did not check. With EXCLUDE_PLACEMENT they
  are kept *out*. For partial reconfiguration that is wrong, but no warning names them.
  The `$`-prefix inheritance is a heuristic. A feed-through named after a *net* that
  shares a name with a pblock cell would inherit wrongly.
- A static cell that the packer clusters with an RM cell (for example a LUT-FF pair across
  the boundary) is pulled into the pblock with only a warning. The proper fix is for
  `pack_lutffs` and the carry packers not to cluster across pblocks.
- `-o timing-opt` (common/place/timing_opt.cc:153-155) checks only `isBelLocationValid`
  and never `testRegion`, so it can move members out of their pblock. Not fixed.
- LOC'd and `-o preplaced` cells are bound in `prePlace` with STRENGTH_LOCKED
  (xilinx.cc:693), after this pass, without the exclusion pre-check. I expect the placer's
  final validity check (placer_heap.cc:542) to flag one inside an exclusive pblock, but I
  did not test that.
- The heap placer's analytic phase does not know about exclusion. A crowded design may
  legalise slowly or fail near a large exclusive pblock. Untested.
- The router is unconstrained (see above). Static nets may route through the RP, and RM
  nets may leave it. Partition pins and route containment are out of scope.
- I did not check Vivado semantics here: whether Vivado moves a cell that is added to a
  second pblock (the patch errors), whether it accepts a bare pblock name without
  `[get_pblocks]` (the patch requires `[get_pblocks]`), and whether DFX implies exclusivity
  for RP pblocks (the patch needs EXCLUDE_PLACEMENT set explicitly). `EXCLUDE_PLACEMENT`
  is the Vivado pblock property name as I remember it; I did not check it against UG903.
- `CLOCKREGION_X..Y..` ranges are not supported: they match no site and produce a warning.

## Example (`designs/pr_open`-style design, Arty A7-35T)

```tcl
# pblock for the reconfigurable module instance u_rm
create_pblock pblock_rm
add_cells_to_pblock [get_pblocks pblock_rm] [get_cells u_rm]
resize_pblock [get_pblocks pblock_rm] -add {SLICE_X12Y100:SLICE_X15Y149}
# keep static logic out of the reconfigurable region
set_property EXCLUDE_PLACEMENT true [get_pblocks pblock_rm]
# accepted and ignored, with a warning
set_property RESET_AFTER_RECONFIG false [get_pblocks pblock_rm]
```

For `designs/pr_open` this should select the 16 named cells (`u_rm.ain0..7`,
`u_rm.core.l0..3`, `u_rm.q0..3`) from `top.json`. The parser would log
`add_cells_to_pblock: 16 cell(s) in pblock 'pblock_rm'` and then
`resize_pblock: pblock 'pblock_rm' has N bel(s)`. Here N is the bel count of 200 SLICE
sites (columns X12-X15, rows Y100-Y149), which I did not compute. Both numbers are
predictions from reading the code, not from a run.

## Build and run results (2026-11-05)

Commands: `docs/buildenv.md`. Built unchanged as `pblock-xdc-build` = `5a62e6e8` (worktree `build/src/nextpnr-pblock`).

- **Compile:** 0 errors. The only warning is the pre-existing `xilinx.cc:1240` `-Wsign-compare`, also in the stock build. **No source fixes were needed.**
- **No-op check:** rv_soc without a pblock gives `.frames` identical to stock ce3f7c18. The FASM differs only in the version comment on line 1.
- **rv_pr with the XDC from `flow/build_pr_native.py` (`build/patched/rv_pr_native/*/pblock.xdc`).** The log prints:
  - `add_cells_to_pblock: 173 cell(s) in pblock 'pblock_rm'`;
  - `resize_pblock: pblock 'pblock_rm' has 4000 bel(s)`;
  - `pblock 'pblock_rm': 173 cell(s) on 4000 bel(s), exclusive`.
  The router binary adds `routing held to 200 tile(s)`.
  - With RM add (8 CARRY4): 181 pre-pack cells were added, and 213 cells are in the pblock after packing. The packer-made CARRY4 and DI/S feed-through LUTs were inherited, so `flow/packer_pins.py` was not needed.
  - Hierarchy matching works here because the RM is synthesized out of context and renamed `rmx_N` before linking: every RM cell is named `u_rm.*` after `flatten`. The yosys naming limit described above still applies to in-context synthesis.
- **Placement**, checked from `NEXTPNR_BEL` in 13 builds over 6 RMs:
  - 0 RM cells outside the region;
  - 0 static cells inside it.
  - The only cells inside without a `u_rm.` prefix are packer feed-through LUTs named after the GND net (`$PACKER_GND_NET$LUT$u_rm.rmx_N$split$...`). They joined through their CARRY4 cluster, as rule (ii) intends.
  - **Exclusive placement replaces the 82 blocker LUTs** of the hack flow.
- **Placement only is not enough for PR.** With this binary alone (no router region), 19–20 RM nets used 25–26 pips outside the region in the replay builds. pr_check found 33 frames outside the region differing between xor and andn. Static also routed through the region: 953 pips in region tiles. Full table: `nextpnr-router-region.md`.
- **Not tested:** `pr_open` (the 16-cell prediction above), `-o timing-opt`, BRAM pblocks, LOC'd cells inside an exclusive pblock, and Vivado semantics.
