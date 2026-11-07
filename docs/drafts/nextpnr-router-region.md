# Draft: router2 keeps a region's routing inside it

Status: **draft. Compiled and run offline on 2026-11-05 (results at the end of this file); not on
hardware, not reviewed upstream.** It lives on the local branch `router-region` (commit `e62fafd1`)
in `upstream/openXC7_nextpnr`, based on `pblock-xdc` (`5a62e6e8`). Nothing has been pushed or posted.
Patch: `docs/drafts/nextpnr-router-region.patch`. It is `git format-patch` output against
`pblock-xdc`: 5 files, +362/-9.

Line numbers: "base" means `pblock-xdc`. `router2.cc`, `router1.cc` and the uarch files
other than `xdc.cc`/`xilinx.h`/`xilinx_place.cc`/`bram_place.cc`/`pack.cc` are the same as
in `ce3f7c18`. "branch" means `router-region`.

## Problem

In our PR flow every RM net is internal to the region. Even so, router2 sends 9–13 nets of
a 32-bit RM through INT tiles just outside the pblock. Those pips are in static frames.
Phase 0 found that no router reads `Region::constr_wires/constr_pips`. This patch adds a
reader to router2, and has the xilinx XDC code fill `piplocs` for a pblock.

## Design

**Which arcs are held** (branch router2.cc:299-309). An arc is *held* to region R when
both of these are true:

- R constrains routing (`constr_pips` or `constr_wires`).
- The arc's sink cell is in R, and either its driver cell is in R too, or the net is a
  constant net and `router2/regionContainConstants` is set (the default).

The constant-net case is needed because the GND/VCC nets are global nets driven by a
pseudo cell (pack.cc:913-923). Without it, an RM LUT's tie-off could be routed from
outside the region. An arc that crosses the edge of R is never held: for example
anchor→static or static→anchor, where the anchor LUTs are pblock members. It has to
leave R.

**What "inside" means** (branch router2.cc:217-230). With `constr_pips`, the pip's tile
`(x,y)` must be in `piplocs` (z ignored). With `constr_wires`, the wire the search enters
must be in `wires`. Both are supported generically. The xilinx code uses only `piplocs`,
for these reasons:

- A pip's configuration bits are written under its own tile. The FASM writer emits
  `uarch->tile_name(pip.tile)` (fasm.cc:421, 504), and `getPipLocation` is that tile's
  `(x,y)` with z=0 (himbaechel/arch.h:573-579). So "pip tile in the region" is exactly
  "frame bits in the region".
- A wire in a pool identifies a node only through whichever tile wire the chipdb uses for
  it, so a wire pool would depend on how the arch represents nodes.

A node that starts inside the region and leaves it (for example a hex line at the top
row) is still allowed, as long as no pip outside the region is used. **I did not check
this against Vivado's DFX rules.**

**Where the check sits.** `hop_allowed_for_arc` (branch 243-254) is called in
`route_arc`'s forward expansion (branch 1226) and backward expansion (branch 1306),
right after the existing `reserved_net` check (base 994, 1071). Because the check does
not depend on `is_bb`, the bounding box cannot defeat it:

- `hit_test_pip(nd.bb, …)` is skipped when `is_bb` is false (base 975, 1050).
- The retry without a box is `route_arc(..., false)` (base 1246).
- Box growth only changes `nd.bb`: `expandBoundingBox` (base 1388) and `apply_budget_bb`
  (base 1299-1309). `nd.bb` is read only by `hit_test_pip` and by thread binning
  (base 1712-1735).

The unbounded loop runs until a midpoint is found or both queues are empty
(base 953-955). If the region has no path, the queues empty, `ARC_RETRY_WITHOUT_BB`
comes back (base 1180), and route_net reaches its `log_error`. For a held arc the patch
first prints an error that names the region (branch 1502-1511). In multi-threaded
mode a failure is deferred to the single-threaded pass (base 1239-1241, 1781-1783), so
it ends in the same place. In the smoothing pass that `log_error` is caught as a
declined move and undone (base 2199-2214), which is the behaviour it already had.

**Holes closed besides expansion:**

1. *Seeds.* route_arc seeds its forward search with the net's existing wires near the
   sink, in both modes (base 915-935). It then reuses their route back to the source
   unchanged (base 1123-1139). Another arc of the same net may cross the edge, so a held
   arc only takes a seed whose route back stays inside (branch 743-756, 1147).
2. *Routing that is already there.* route_net keeps any arc that `check_arc_routing`
   accepts (base 1217-1220). This covers a loaded routed design, a second router2 run
   (hold-fix calls router2 again, hold_fix.cc:656), and routes bound before the region
   existed. Such an arc is now ripped up if its route breaks the region rules
   (branch 1451-1461), **unless it is locked**: a wire bound above `STRENGTH_STRONG`,
   which `bind_and_check_all` never unbinds (base 1518).
3. *Locked routing.* Wires at `STRENGTH_PLACER` or above are reserved for their own net
   (base 239-249), so a held RM arc cannot take the replayed static routes (`-o
   prerouted`, bound LOCKED at xilinx.cc:1192/1208). A locked route of a *held* arc that
   breaks its region is reported with a warning, at most 10 names plus a count
   (branch 785-820), and left in place. The summary line `Routing regions: …` gives the
   counts of held and crossing arcs.
4. *Ripup and reroute* all go through `route_net`/`route_arc`: the main loop, the
   smoothing pass (base 2200, 2236), and hold-fix's router2 calls. So they are held as
   well.
5. *The final router1 pass* (base 2437) queues only arcs whose route is incomplete
   (router1.cc:446-461). Once router2 has finished, it should not reroute anything.

**Static nets.** By default an arc that is not held may cross any region. This is the
"route-through allowed" policy. `--router2-region-keep-out` (`router2/regionKeepOut`,
branch command.cc:431, 601; router2.cc:2722) keeps such an arc out of every region except
its driver's and its sink's (branch 247-251). Locked routes are untouched, so prerouted
static nets keep their paths through the region. Only the arcs that the router
places fresh are kept out.

**Overlap.** If two routing regions share a pip tile or a wire, that is a `log_error`
(branch 153-202), because one arc cannot be held to both.

**Cost when unused.** When no region constrains routing, `hop_allowed_for_arc` returns
at its first test, and `arc_route_breaks_region` also returns immediately. A held arc
costs one `dict` lookup per expansion.

## xilinx: which tiles a pblock's routing may use

- `set_property CONTAIN_ROUTING true|false [get_pblocks p]` is now parsed
  (branch xdc.cc:321-340).
- If it is not set, containment follows `EXCLUDE_PLACEMENT` (branch xdc.cc:933-936,
  xilinx.h:184-192).
- `CONTAIN_ROUTING` is the Vivado property name as I remember it. **I did not check it
  against UG903.**

`add_pblock_routing_tiles` (branch xdc.cc:965-1029; function at 977) fills `piplocs` with these tiles:

- the tile of every site in the pblock;
- walking from that tile toward its `_L`/`_R` side, over 1 row for a CLB tile and 5 rows
  (grid y-4..y) for a BRAM or DSP tile, the interface tiles up to and including the first
  `INT_L`/`INT_R`.

It then sets `constr_pips`. The rule comes from prjxray `artix7/xc7a50t/tilegrid.json`.
I checked it there with a script; the results:

- All 4075 CLB tiles have `INT_<side>` at x+1 (`_L`) or x-1 (`_R`).
- All 55 BRAM_L, 20 BRAM_R, 30 DSP_L and 30 DSP_R tiles, ×5 rows, have
  `[BRAM_]INT_INTERFACE_<side>` and then `INT_<side>`.
- For `SLICE_X12Y100:SLICE_X15Y149`, the tiles are columns 30-33 (CLBLM_L, INT_L, INT_R,
  CLBLM_R) for grid rows 1-25 and 27-51.
- Row 26 (`HCLK_*_X..Y130`) holds no site and is not taken.

So a held net cannot use `INT_L_X12Y1xx` / `INT_R_X9Y1xx`, the detours that were seen.
A site tile with no interconnect found beside it gets a warning.

## Syntax check (what exactly was run)

There are no boost or eigen headers and no sudo, so the code was not built. I wrote stand-in
headers into the scratch directory: `boost/functional/hash`, `thread`, `lexical_cast`,
`container/flat_map`, `iostreams/device/mapped_file`, `algorithm/string[/predicate,join]`
and a minimal `program_options`. Then I ran `g++ 15.2 -std=c++17 -fsyntax-only -Wall
-Wextra -include cmath -include climits -include cstring -DNO_GUI -DNO_PYTHON` on each
file, both on the branch and on a `git archive` of `pblock-xdc`, and diffed the
diagnostics:

| File | Result |
|---|---|
| `router2.cc` | 0 errors; warnings identical to base |
| `xdc.cc` | 0 errors; warnings identical to base |
| `xilinx_place.cc` | 0 errors; warnings identical to base |
| `xilinx.cc` | 3 errors, identical to base (from the `program_options` stub) |
| `command.cc` | 15 errors, identical to base (the stub lacks `positional_options_description`, `store`, …) |

For `command.cc`, none of the errors is on the edited lines. Its 5 new lines copy the
neighbouring `router2-slack-order` code, but the check proves little for them.

This checks syntax and types only. It says nothing about linking or behaviour.

## Untested or not handled

- **Never run.** I have not checked that held RM nets route inside the region, how
  run time changes, or whether router2 converges when an RM is dense.
- **Constant sources inside the region.** A held GND/VCC arc needs a wire with
  `const_value` set (himbaechel/arch.h:546-549), reachable through region pips. I did
  not check the chipdb for that. If there is none, the arc fails with the region error;
  `router2/regionContainConstants=false` turns that containment off.
- **Hold-fix detours** are bound by hold-fix's own search (hold_fix.cc `detour_arc`, 73-260, pips bound LOCKED at
  253), which checks only `checkPipAvailForNet`. Hold-fix buffer cells get no region. So
  `-o hold-fix` can take an RM arc outside the region. The next router2 run then reports
  it as a locked arc that breaks its region. A follow-up could have the xilinx
  `checkPipAvailForNet` (xilinx.h:176) read regions, which would also cover hold-fix and
  router1.
- **`--router router1`** and xilinx `route_clocks` (pack_clocking.cc:584-711, run in
  preRoute, xilinx.cc:1107) ignore regions. An RM-internal clock net would not be held.
- **Not checked against Vivado:** whether Vivado lets a contained net use a node that
  crosses the boundary, and whether Vivado's partition-pin handling treats the boundary
  arcs like this patch does.
- Pblocks reach routing only through `apply_pblocks_after_packing`. A flow that loads an
  already-packed design without packing gets no routing regions.
- Only xc7a50t's tile grid was checked. Other 7-series parts are expected to follow the
  same `_L`/`_R` pairing, but I did not check them.
- `region_keep_out` blocks a static arc whose sink is outside the region from passing
  through the region, even where the region is the only path. Such an arc then fails with
  the generic error.

## Build and run results (2026-11-05)

Build environment and exact commands: `docs/buildenv.md`. The branch was built unchanged, as
`router-region-build` = `e62fafd1` in worktree `build/src/nextpnr-router`, with conda-forge GCC 14.4.0,
Boost 1.81.0 and Eigen 3.4.0.

- **Compile:** 0 errors. One warning, `xilinx.cc:1240` `-Wsign-compare`, which the stock ce3f7c18 build prints too. **No source fixes were needed.**
- **No-op check:** rv_soc (no pblock) built with the stock, pblock and router binaries from the same yosys JSON.
  - The FASM differs only in line 1, the version comment (`# nextpnr-himbaechel e62fafd1`).
  - `.frames` are identical (`cmp`).
  - With no region, the patch changes nothing in this design.
- **PR flow:** `flow/build_pr_native.py` (new, DRY_RUN default). It uses rv_pr (rv_soc + PCPI `rm_slot`) with pblock `SLICE_X12Y100:SLICE_X15Y149`:
  - `EXCLUDE_PLACEMENT true`;
  - `CONTAIN_ROUTING true`;
  - `--router2-region-keep-out`.
- **Replaced hacks:** the RM shell is `designs/rv_soc/pr/rm_shell.v` with the 82 `blk*` blocker LUTs removed, keeping the BEL-pinned anchor LUTs/FFs (the partition interface). No rm_place.py, packer_pins.py, region_route.py or static_detour.py runs.
- **Flow:** the first build (`xor_a`, everything free) is dumped with `replay_dump.py`. Every RM is then built on the replayed static (`-o preplaced`/`-o prerouted`).

Measured with `flow/region_pips.py` (new) and `flow/pr_check.py`. Outputs are in `build/patched/rv_pr_native/<variant>/`.

| variant | static pips in region tiles (INT) / nets | RM pips outside region / nets | pr_check (static outside region) |
|---|---|---|---|
| router + keep-out | **0 (0) / 0** in all 7 builds | **0 / 0** in all 7 builds | **identical in all 15 RM pairs** (xor, andn, add, rot, popc, minmax): 69–72 frames differ, all inside |
| router, no keep-out | 958 (937) / 402 | 0 / 0 | identical (xor vs andn: 70 frames, all inside) |
| pblock only (`pblock-xdc` binary) | 953 (938) / 412 | 25 / 19 (xor_n), 26 / 20 (andn_n) | **differs**: 100 frames, 33 outside the region |
| reference: current hack flow, `build/openxc7/rv_soc/rv_pr_xor_c` | 955 (934) / 434 | 0 / 0 | identical (Phase 4/5) |

- **Containment and keep-out do different jobs.** Containment alone (no keep-out) keeps RM nets in and makes static identical. Static still crosses the region, replayed identically each time, as in the hack flow without `static_detour.py`. Keep-out removes that crossing: 0 static pips in region tiles. This is what `static_detour.py` was being built to do (docs/phase7-regions.md).
- **Placement:** no cell outside `u_rm.` lands in the region, and no `u_rm.` cell lands outside it (checked from `NEXTPNR_BEL`), with one exception. rot/popc/minmax have 4–11 packer feed-through LUTs named `$PACKER_GND_NET$LUT$u_rm.rmx_N$split$...` in RM carry slices. They are RM logic that got the pblock through their CARRY4 cluster, not static cells.
- **Constant nets:** `router2/regionContainConstants` (default on) routed the held GND/VCC arcs inside the region for all 6 RMs. Among the boundary-class nets (nets with both static and RM cells), the only one whose routing differs between xor_n and andn_n is `$PACKER_VCC_NET`.
- **Dense RM:** rot (128 LUT5 barrel rotate; 883 held arcs) routes in 2.97 s of router2 time on the static from xor_a. In Phase 7 the same RM, replayed against a static design that crossed the region, was stopped at router iteration 39,064 with 2 wires still overused (docs/phase7-regions.md).
- **popc:** it routes, with 591 held arcs and 0 RM pips outside, but fails timing at 99.45 MHz against 100 MHz. It is built with `--timing-allow-fail` (`popc_n_taf`). minmax went through the same option but passes (141.16 MHz).
- **Run time and Fmax** (single seed, one run each, not a benchmark):

  | first build | router2 time | Fmax |
  |---|---|---|
  | router + keep-out | 150.0 s | 141.16 MHz |
  | router, no keep-out | 92.6 s | 152.09 MHz |
  | pblock only | 94.2 s | 154.01 MHz |
  | stock rv_soc with no PR | 46.1 s | |
  | hack flow first build `rv_pr_xor` (nightly binary) | 71.4 s | |

  - Replay builds route in 2–4 s.
  - The 141.16 MHz critical path runs through static PicoRV32 logic (`u_cpu.latched_store` → ALU carry chain at grid x=38). So it is a property of the first build's static placement, not of the RM.
  - The hack flow's rv_pr builds reached 160 MHz. Whether keep-out costs Fmax in general is not established from one seed.

Still open after these runs:
- Hold-fix, `--router router1`, `route_clocks` and region overlap were not exercised.
- Partials were not generated from these builds (flow/partial.py, make_partials.sh), so the region gate and simulated load were not run on them.
- The boundary-node question against Vivado DFX rules stays unchecked.
