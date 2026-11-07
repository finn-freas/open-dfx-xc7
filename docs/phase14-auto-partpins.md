# Phase 14: automatic partition-pin placement (native flow, opt-in)

Offline work, 2026-11-05. Nothing here has run on hardware. Every number below comes from a run, and the log or output
path is given next to it. All paths are under `build/patched/rv_ppa_native/` unless stated otherwise. This closes the
gap left in matrix item 6 (`docs/dfx-vs-vivado.md`): rv_pp (phase 13) took its pins from a reference build that still
used the anchor shell. Design `rv_ppa` has no anchored build anywhere.

## 1. Flow (`flow/build_pr_native.py --design rv_ppa`, variant `partpin2`)

| step | build / file | what |
|---|---|---|
| 1 | `partpin2/greybuf_p` | Static placement with a **greybox with port buffers**: one unplaced LUT1 per port bit, placed freely in the pblock (input → LUT1 with no load; LUT1 tied to 0 → output). Its only purpose is to let the placer see the ports. |
| 2 | `partpin2/static_pp_assign.{partpins,json}` | **Pin assignment** (`flow/partpin_assign.py assign`, section 2), from step 1's placed static endpoints. |
| 3 | `partpin2/grey_s` | **Static build with an empty greybox** (no cells, inputs unloaded, outputs undriven). The static placement comes from step 1 (`-o preplaced`, `u_rm.` excluded). With `-o partition-pins=… -o partition-pins-route`, nextpnr routes every boundary net's static side to its pin, outside the pblock, and locks it (new patch, section 3). router2 then routes the rest of static. |
| 4 | `partpin2/static.{preplaced,prerouted}`, `static_pp.{prerouted,partpins,json}` | **Lock static.** `replay_dump.py` on step 3, then `partpin_assign.py export`. Export checks, for each net, that the pin is on the route once and that the route has no pip in the region. For an output net it drops the pin's own source entry, so that the module build binds the pin through its region pip. The output has the same format as `flow/partpins.py`. |
| 5 | `partpin2/<rm>_p` | **Module placement against the pins.** A placement-only netlist (`partpin_assign.py proxy` → `pp_proxy.v/.xdc`): the module plus one BEL-fixed LUT1 per pin, in the region logic tile beside the pin's INT tile, standing in for the static side. Only the `u_rm.` cells' placement is kept (`<rm>_place.preplaced`). The proxies never appear in a module build. |
| 6 | `partpin2/<rm>_n` | **Module build**: the full design with `-o preplaced=<static + module placement> -o prerouted=static_pp.prerouted -o partition-pins=static_pp.partpins` (the phase-13 mechanism). There are no anchors, and the shell is `rm_shell_pp.v` (only `ready` is registered, as in rv_pp). |
| 7 | `partpin2/checks/` | `region_pips` (6 builds), `pr_check` (grey_s and the 4 modules, 10 pairs), `partpin_check` (4 modules). |

Run: `python3 flow/build_pr_native.py --design rv_ppa --run`. DRY_RUN is the default, and every step is cached.
To honour the "at most 2 nextpnr" rule, the runs here went through a waiting wrapper outside the repo
(`~/npwait/drive.py`, `~/npwait/npwait.sh`). The wrapper only changes the variant's binary path to a script that
waits and then execs the same binary.

### Why steps 1 and 5 exist (found by run)

- **Empty greybox placement** (`exp0/`): the static endpoints are placed with no pull towards the region, at a mean of
  91.8 tiles and a maximum of 113 tiles from their pins (`exp0/pins.json`). In addition, the pin-to-sink route of 12
  `rd` nets could not be found (`exp0/grey_pp/nextpnr.log`), because undriven `pcpi_rd` flip-flops had been packed
  two to a slice where both need the same AX bypass pin. With the port-buffer greybox the outputs have drivers, so the
  packer and placer respect this. The static distance falls to a mean of 35.4 and a maximum of 59 tiles
  (`partpin2/static_pp_assign.json`), and all 108 routes are found.
- **Without step 5** (`attempt2_wrap_wire_pin/`, `debug_overuse/`): nextpnr's placer does not see partition pins. It
  pulls the module's cells towards the far static endpoints, and put all 32 xor LUTs into the region corner
  `X30Y49..X30Y51` (`debug_overuse/xor_placed.json`). Every pin's route then had to reach that corner. Router2 was still
  at 13–16 overused wires after 1873 iterations, all in `X31Y49..X31Y51`, mostly on `slot_rs2[*]` nets
  (`debug_overuse/xor_n.log`, overuse logged by a temporary, since-removed debug line). Vivado's placer treats
  PartPins as fixed terminals; step 5 gives nextpnr the same view without changing its placer.
- **Hex pins** (`attempt1_hex_pins/`): the first assignment chose 108 hex pins (NE6/NN6/NW6 in, SW6/SS6 out), because
  hex wires reach furthest towards the static endpoints. A hex `END` in an INT tile drives only other routing `BEG`
  wires (and CTRL), never an IMUX: the fanout from `X31Y31/NE6END2` is 18 pips, all to `*BEG*`/CTRL. In a region two
  INT columns wide, most of those `BEG` wires leave the region. The xor build was at 13–16 overused wires after 1873
  iterations and was stopped. Input pins are now required to drive an `IMUX`/`BYP_ALT` pip in their own tile, and output
  pins to be driven by `LOGIC_OUTS` there.
- **Wrap wires** (`attempt2_wrap_wire_pin/`): pin `X31Y51/ER1END_N3_3` (a `_N`/`_S` wrap alias at the region's bottom
  row) made `xor_n` fail with "region has no route" for `slot_rs1[27]`. The pin is the node member that prjxray's
  tileconn joins; nextpnr's node for it evidently has no region pip from it. I did not dig further. Wires matching
  `.*_[NS]\d.*` are now excluded.

## 2. Pin assignment (`flow/partpin_assign.py`, new)

**Candidates, from prjxray-db only** (`tile_type_*.json` pips, without pseudo or bidirectional pips; nodes from
`tileconn.json`, built with `partpins.Nodes`):

- An **input** pin is a node that is driven by a pip outside the region and drives a pip in a region INT tile, with no
  driver inside. An **output** pin is driven from inside and drives a pip outside, with no driver outside.
- The node must be a directional general routing wire (`EE|WW|NN|SS|NE|NW|SE|SW|EL|ER|WL|WR|NL|NR|SL|SR` + digit, so
  no long lines, GCLK, IMUX or FAN). It must be **direct**: an input pin drives IMUX/BYP_ALT in its pin tile, and an
  output pin is driven by LOGIC_OUTS there. It must not be a `_N`/`_S` wrap alias.
- **Capacity per region INT tile** (`python3 flow/partpin_assign.py capacity -v`): the region has 100 INT tiles, all on
  its edge (it is two INT columns wide).

| count | input pins per tile | output pins per tile |
|---|---|---|
| boundary-crossing directional wires (before the direct/wrap filters) | 43–61, total 4661 | 44–56, total 4654 |
| usable pins (direct, no wrap alias), used by the assignment | 23–32, total 2330 | 42–54, total 4453 |

  The class split per tile is in `static_pp_assign.json` `capacity`. For example, `X31Y40` (INT_L, mid-row) has 44
  crossing input wires: 4 each of EE2, EL1, ER1, NE2, NE6, NW6, SE2, SE6, SW6, WW2, WW4.

**Assignment.** Each boundary net (75 in, 33 out; `clk` excluded) gets one pin:

- cost = `w_static` × Manhattan distance from the net's placed static endpoint (driver for an input, mean of the sinks
  for an output) to the nearest outside pip of the pin node
- \+ `w_slice` × |pin row − bit-slice target row|, for buses of 8 bits or more. The targets are spread linearly over a
  band of rows with enough capacity (`tile_cap` × columns × `band_slack`), at the region end nearest the static
  endpoints, with bit 0 at the far end of the band.
- \+ `w_load` × pins already in the tile.

There is a hard cap of `tile_cap` = 3 pins per INT tile, and each node is used once. The assignment is greedy by
regret: the net whose best and second-best choices differ most is placed first. The CONFIG block at the top of the file
has all the weights (1.0/1.0/2.0, slack 1.25).

**Result** (`partpin2/static_pp_assign.json`):

- 108 pins in 42 INT tiles, at most 3 per tile (28 tiles hold 3, 10 hold 2, 4 hold 1); 63 in INT_L `X31` and 45 in
  INT_R `X32`; band rows 29–51.
- Inputs: EE2 41, ER1 13, NW2 12, NN2 6, NE2 3. Outputs: SW6 18, SS6 15.
- Bit slicing: rs1 / rs2 / rd bit 0 → bit 31 run from row 30 to row 49 / 51 / 49, with 2 / 2 / 4 steps out of order.
  The mean deviation from the target row is 1.02 rows (max 8.66).
- Static distance: mean 35.4, max 59 tiles.

For comparison, the anchored reference of rv_pp gave 39 INT tiles with up to 11 pins in one; the unanchored reference
of phase 13 put 54 pins in one INT tile.

## 3. nextpnr patch (`docs/drafts/nextpnr-partition-pins-route.{md,patch}`, variant `partpin2`)

The patch goes on top of the unchanged `partpin` stack. It has 3 files, +188/−1:

- `xilinx.cc/.h`: `-o partition-pins-route` (a flag). After `apply_partition_pins`, for each partition-pin net with no
  cell in a routing-contained pblock (and not already reaching its pin), it routes with A*: from the net's source to
  the pin, or, for an undriven net, from the pin to each sink. The search uses pips outside every routing-contained
  pblock, no LUT route-through, free wires only and no other net's pin, and the route is bound `STRENGTH_LOCKED`. If a
  net has no route, the build fails with its name.
- `router1.cc` `checkRoutedDesign`: a net may end at its partition pin. This covers a net without sinks whose wires are
  exactly the path to its pin, and a leaf that is the net's pin. Without it, the greybox build asserted at
  `router1.cc:1357` (`net_info->wires.empty()`, a sinkless input net) and then at `:1321` (stub).

Build: `DRY_RUN=0 VARIANT=partpin2 BASE_REV=router-region PATCHES="nextpnr-pblock-replay.patch
nextpnr-pblock-routethru.patch nextpnr-partition-pins.patch nextpnr-pblock-lutff.patch nextpnr-carry-replay-order.patch
nextpnr-partition-pins-route.patch" bash toolchain/buildenv/build_nextpnr_variant.sh`. The script uses `-j8`; here it
was built with `ninja -j4` to spare memory (`build/nextpnr-build/partpin2.build.log`; the only warning is the
pre-existing `-Wsign-compare` in `apply_prerouted`). The six patches applied to `router-region` in a scratch worktree
give exactly the `build/src/nextpnr-partpin2` worktree (`git diff HEAD` identical).

**No-op:** rv_soc without pblock (`build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.json`), `partpin2` against the
`partpin` build `build/patched/rv_pp_native/noop/rv_soc_partpin`: `.frames` identical (`cmp`), and FASM identical
apart from comments (`noop/rv_soc_partpin2`).

## 4. Results (`partpin2/`)

| check | result | evidence |
|---|---|---|
| greybox static routed to the pins | `75 net(s) routed from their source to the pin, 33 from the pin to their sinks, outside the pblocks (1059 pips, locked)` | `grey_s/nextpnr.log` |
| module builds | `Partition pins: 108 net(s) … 0 arc(s) without the locked route outside`. Pins given to the pblock: xor 98, andn 99, add 98, rot 72; the rest are on ports the module does not use. | `*_n/nextpnr.log` |
| pr_check, module pairs | **STATIC IDENTICAL OUTSIDE REGION 6/6**; 71 frames differ (pairs of xor/andn/add) or 72 (pairs with rot), all inside the region | `checks/pr_check_*_n_*_n.log` |
| pr_check, greybox static vs modules | **STATIC DIFFERS, 4/4**: 4 frames outside the region, all clocking. There is word 50 (HCLK) in the region's own columns, and words in `c23` and `c1` minor 26/27 of rows r0/r1. grey_s has no clocked cell in the region; the modules' `ready` FF adds a clock leaf. See section 6. | `checks/pr_check_grey_s_*.log` |
| partpin_check | **PASS 4/4**: for all 108 nets in all 4 builds, the pips outside the region equal the locked route, and the pin wire is on the route | `checks/partpin_check.log` |
| region_pips | static pips in the region = **0** in all 6 builds (greybuf_p, grey_s, 4 modules); module-only nets' pips outside = **0** (add_n 40 nets, rot_n 128; xor_n/andn_n have none) | `checks/pips_*.json` |
| native_check (`PARTPINS`, `STATIC_PIPS=static_pp.prerouted`, `SHELLV=rm_shell_pp.v`, `FORMAL_MEM_KB=3000000`) | **exit 0, every line PASS.** 12 partials: 59,272 B `.bin`, 72 region frames + 1 run-end static pad, CRC OK, simulated base + partial = target (0 frames differ, also with the last frame uncommitted). Pass-1 dropped pips: 261 (xor), 318 (andn), 649 (add), 1515 (rot). byteman vs the original target: 0 frames differ, 12/12. region2v `--partpins`: 16/16 SIM + PROVED (4 full + 12 byteman). 309.5 s. | `native_check.log`, `partials/*.check.json` |
| negative controls | xor_n checked as andn → `FAIL … pass=223 fail=3359`; add_n with one LUT bit flipped (`--corrupt`) → `FAIL … pass=2815 fail=767`; export with two pins swapped → refused (`pin … on the route 0 times`); nextpnr with a pin inside the region (`X31Y40/IMUX_L5`) → `ERROR: Partition pins: no route outside the pblocks for 1 net(s), e.g. 'slot_rs1[5]'` | `neg_xor_as_andn.log`, `neg_add_corrupt.log`, `neg_export_swapped_pins.log`, `neg_pin_inside/grey_s/nextpnr.log` |

### 4.1 Region use (module cells, `checks/partpin_check.json`)

| RM | rv_ppa LUT / FF / CARRY4 | rv_pp (phase 13) | anchor flow `rv_pr_native/router` |
|---|---|---|---|
| xor | 32 / 1 / 0 | 32 / 1 / 0 | 140 / 33 / 0 |
| andn | 32 / 1 / 0 | 32 / 1 / 0 | 140 / 33 / 0 |
| add | 32 / 1 / 8 | 32 / 1 / 8 | 172 / 33 / 8 |
| rot | 150 / 1 / 2 | 150 / 1 / 2 | 258 / 33 / 2 |

### 4.2 Timing and router runtime (one seed)

| build | Fmax | router2 | critical path |
|---|---|---|---|
| `greybuf_p` (placement build) | 153.21 MHz | 20.68 s | static |
| `grey_s` (greybox static, routed to pins) | 158.13 MHz | 15.93 s | static |
| `<rm>_p` (placement proxies) | – | 1.41–1.58 s | – |
| `xor_n`, `andn_n` | **158.13 MHz** | 1.45 s, 1.51 s | static (the same as grey_s) |
| `add_n` | **135.48 MHz** | 1.66 s | through the module: `slot_rs2[1]` 2.116 ns routing, adder, `slot_rd[28]` 2.836 ns routing, 7.381 ns total |
| `rot_n` | **124.15 MHz** | 1.93 s | through the module: `slot_rs2[1]` 1.832 ns, `slot_rd[13]` 2.523 ns |
| rv_pp (phase 13), all 4 RMs | 145.62 MHz | 2.54–3.09 s | static; the reference build `xor_a` took 76.86 s in router2 |
| anchor flow `rv_pr_native/router/*_n` | 141.16 MHz | 1.99–2.97 s | (phase 13 §5.4) |

All builds close at 100 MHz. Compared with rv_pp, static alone is faster (158.13 against 145.62 MHz: a different static
placement), and xor/andn are faster. add and rot are slower, and their critical path is the combinational `rd` path,
which phase 13 never saw as critical. About 5 ns of add's 7.38 ns path is the two boundary routes. Their length comes
from the static endpoints, which sit a mean of 35 tiles from the pins. rv_pp's reference placement had the real
module in it and kept them closer. This is one seed and one placement, so the comparison is not general.

Whole flow from scratch: 171.09 s and 169.91 s wall time (`repro_a.out`, `repro_b.out`). That includes waits for
other jobs' nextpnr runs.

### 4.3 Reproducibility

rv_ppa was rebuilt from scratch twice with the final binary (`--out build/patched/rv_ppa_native/repro_a`,
`…/repro_b`):

- `.frames` identical for all 10 nextpnr builds (greybuf_p, grey_s, 4 × `_p`, 4 × `_n`), between a and b and also
  against `partpin2/`.
- `static_pp_assign.partpins`, `static_pp.partpins`, `static_pp.prerouted` and `static.preplaced` are identical too.
- Both rebuilds: module pairs static identical 6/6, partpin_check PASS 4/4 (`repro_compare.log`).

`partpin2/` was built before a whitespace-only source fix and an env-gated debug line had been removed from
`router2.cc`. Its outputs are identical to the rebuilds, so native_check on `partpin2/` holds for the final binary.

## 5. Vivado naming (UG909)

I checked UG909 online (docs.amd.com, 2025.2, pages "Partition Pins" and "Partition Pin Placement"; no copy on disk):

- `HD.PARTPIN_LOCS` names one interconnect tile (`INT_R_X4Y153`) for a port, set on the hierarchical pin with
  `get_pins`, and overrides `HD.PARTPIN_RANGE`. UG909 says not to use it on clock ports or dedicated connections.
- `HD.PARTPIN_RANGE` is a range of sites (SLICE/DSP/RAMB) or INT tiles. It defaults to the whole pblock.
- On automatic placement, the PartPin placer "attempts to spread the partition pins, minimizing the number of partition
  pins per interconnect along the edges, and increasing the PartPin density towards the middle of the Pblock" and notes
  that routing is limited along the edges and especially in the corners.

Here the pin is a node (one wire), not just a tile. Our `-o partition-pins` file is closer to a resolved
`HD.PARTPIN_LOCS` plus the node choice. A range/tile constraint input to `partpin_assign.py` (Vivado names, a tile per
port, or a range) is **not implemented**. This region has no "middle" (every INT tile is an edge tile), so the density
rule is not mirrored. The tile cap does the spreading.

## 6. Open problems

- **Greybox static ≠ module static in 4 clocking frames.** grey_s has no clocked cell in the region. The `ready` FF of
  every module adds a clock leaf (`1 sink(s) the reference does not reach keep their dedicated clock route`), which
  enables HCLK/clock-column bits outside the region. All module builds agree with each other (6/6), so partials
  between modules are exact. A greybox *partial* built from grey_s would not be a valid swap target. The fix would be
  to route the clock to the region in the greybox build (a clock partition pin) or to put one clocked cell in it. I
  have tried neither.
- **Placement proxies are a pass outside nextpnr's placer.** The module placement is decided in a separate run with
  BEL-fixed stand-ins, and the real build only routes. Making nextpnr's placer treat partition pins as fixed terminals
  would remove step 5. That is not done.
- **Static timing does not see the pins.** The static endpoints are placed in step 1 against free LUT buffers, not
  against the pins. The boundary routes cost about 2–2.8 ns each, and add/rot fall to 135/124 MHz. No timing-driven
  pin or endpoint refinement has been done.
- One region, one device, one seed; `tile_cap` and the weights are hand-set, with no sweep. The wrap-wire exclusion
  is empirical (one failure, cause not traced in nextpnr's node model).
- No range/LOC input (Vivado's `HD.PARTPIN_RANGE`/`HD.PARTPIN_LOCS`), and no clock partition pins.
- Not compared with a Vivado build that uses partition pins; nothing on hardware.

## 7. Files

| file | |
|---|---|
| `flow/partpin_assign.py` (new) | `capacity`, `assign`, `export`, `proxy` |
| `flow/gen_shell2.py` | `--greybox [--buffers]` (the default and `--partpins` outputs are unchanged: regenerated rv_pp shells `cmp`-identical, `dry/gen_shell2_check/`) |
| `flow/build_pr_native.py` | design `rv_ppa`, variant `partpin2`, `main_auto` (taken only when `partpins == "auto"`) |
| `docs/drafts/nextpnr-partition-pins-route.{md,patch}` (new) | variant `partpin2` |
| unchanged | `flow/partial.py`, `flow/build_pr.py`, `flow/partpins.py`, `flow/region2v.py`, `flow/native_check.sh`, `flow/partpin_check.py`, all existing patches and variants |

Existing designs' dry runs are identical to the committed `build_pr_native.py` (`cmp`) for rv_pr, rv_pr with 6 RMs and
`--timing-allow-fail`, rv_b, rv_c, rv_c `--no-shared-frame-pblock`, rv_m, rv2 and rv_pp: every step is `[skip]`
(`dry/{before,after}_*.txt`).
