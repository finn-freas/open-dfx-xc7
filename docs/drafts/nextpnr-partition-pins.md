# Draft: partition pins for routing regions (router2 + xilinx)

Status: **draft. Compiled and run offline on 2026-11-05; not on hardware, not reviewed upstream.** Nothing was
committed, pushed or posted: the patch is `git diff` output with a written header.

- Patch: `docs/drafts/nextpnr-partition-pins.patch`, 5 files, +352/-41:
  `common/kernel/nextpnr_types.h`, `common/route/router2.cc`, `common/route/router1.cc`,
  `himbaechel/uarch/xilinx/{xilinx.cc,xilinx.h}`.
- Base: `router-region` (`e62fafd1`) + `nextpnr-pblock-replay.patch` + `nextpnr-pblock-routethru.patch` (the `rtkeep`
  stack). Two more drafts go on top of it and are needed by the same flow: `nextpnr-pblock-lutff.patch` and
  `nextpnr-carry-replay-order.patch`.
- Variant `partpin` (worktree `build/src/nextpnr-partpin`, binary `build/nextpnr-build/partpin/nextpnr-himbaechel`,
  `--version` prints `e62fafd1-partpin`):

  ```bash
  DRY_RUN=0 VARIANT=partpin BASE_REV=router-region PATCHES="nextpnr-pblock-replay.patch nextpnr-pblock-routethru.patch \
    nextpnr-partition-pins.patch nextpnr-pblock-lutff.patch nextpnr-carry-replay-order.patch" \
    bash toolchain/buildenv/build_nextpnr_variant.sh
  ```

  The five patches applied in that order to `router-region` give exactly the worktree (checked with a scratch git
  index: `git diff` against it is empty). Build log of the first build: `build/nextpnr-build/partpin.build.log`; later
  edits were rebuilt with `ninja -C build/nextpnr-build/partpin`. The only compiler warning left is the pre-existing
  `-Wsign-compare` of the prerouted pruning loop in `xilinx.cc`.

## What was there before (read in router2.cc and xilinx.cc of the `rtkeep` stack)

- **`-o prerouted`** (`XilinxImpl::apply_prerouted`) binds each listed net's reference route `STRENGTH_LOCKED`, then
  **prunes every wire that is not on a path from the source to a sink of this design**. A route that ends at a wire
  (a partition pin) and not at a sink would be removed completely.
- **router2 and partly routed nets.** `setup_wires` copies every bound wire into the net's `nd.wires` and marks a
  wire bound at `STRENGTH_PLACER` or stronger as reserved for its net. An arc whose route is complete is kept
  (`check_arc_routing`). An incomplete arc is searched from the source wire forwards and from the sink backwards;
  forward expansion may enter a wire of the net only through its bound pip, so **the search can walk the locked tree
  and branch off it anywhere**. Mode-0 seeds come only from wires of arcs already routed (`wire_by_loc`). The trace back
  from the meeting point uses `nd.wires` and asserts that it reaches the source; `nd.wires` entries of locked wires
  are erased once no arc holds them.
- **router-region.** An arc that crosses a region edge (driver and sink in different regions) is *not held*; with
  `--router2-region-keep-out` it may use pips outside all regions and in its driver's or sink's region. So a
  boundary arc could branch off the locked static tree outside the region and add static pips, and an RM output arc
  could leave and re-enter the region.
- `RegionPlug` (`nextpnr_types.h`, `BaseCtx::createRegionPlug`/`addPlugPin`) is nextpnr's existing partition-pin
  pseudo cell, used by the FABulous and Gowin flows. It splits a boundary net into two nets that meet at a wire. It
  suits a flow that builds static and module separately; in a combined build (static locked, module routed, one
  netlist) both nets would bind the same wire, so it is not used here.

## Change

**Kernel.** `Region::partition_pins`: net name -> the wire at which the net crosses the region's edge.

**router2** (`setup_route_regions`, `setup_nets`, `route_arc`, `arc_route_breaks_region`):

- An arc of a net with a partition pin in region R that *enters* R (sink in R, driver not) is held to R and searched
  **from the pin** to the sink; an arc that *leaves* R (driver in R, sink not) is held to R and searched **from the
  source to the pin**. Only when the far side is already locked routing all the way (from the source to the pin, or
  from the pin to the sink; `part_pin_route_is_locked`); otherwise a warning and the old behaviour.
- After the search, the locked far side is added to the arc: towards the source by the existing "tack onto existing
  routing" walk, which now falls back to the net's locked Arch binding when `nd.wires` no longer has the wire; towards
  the sink by a walk from the sink up to the pin.
- The region rules, the seed filter and the summary only look at the part inside R. The log gains
  `Partition pins: N net(s); a arc(s) routed inside a region from one, b to one; c arc(s) without the locked route
  outside are not`.
- No partition pins: every new test returns at once; the forward/backward roots are the source and sink as before.

**router1** (final check): the route to a region's partition pin is not counted as a stub. A module that does not use
a port leaves that net ending at the pin.

**xilinx** (`xilinx.cc`):

- `-o partition-pins=<file>`, lines `<net>\t<wire>`. Read before `-o prerouted`; the pruning keeps the path to the
  pin (`read_partition_pins`). After it, each pin is given to the pblock of the net's driver (net leaves the pblock) or
  else of a sink (net enters it); for a net that touches no pblock in this design, to the pblock whose pips the pin
  reaches (`apply_partition_pins`).
- In `apply_prerouted`, for a net `route_clocks` had routed: a sink that the reference route does not reach keeps
  route_clocks' dedicated route from where it joins the reference tree. Without this, the global clock's arc to a
  module flip-flop that moved was left to router2 and, in one build, went through a LUT route-through in a static
  CLB outside the pblock (6 static frames changed; `build/patched/rv_pp_native/attempt2_fabric_clock_leaf/checks/`).

How the pins are chosen is up to the caller. `flow/partpins.py` takes them from a reference build (see
`docs/phase13-partition-pins.md`).

## Results (2026-11-05; details and log paths in docs/phase13-partition-pins.md)

- **No-op:** rv_soc without pblock, same JSON as the earlier no-op checks: `.frames` identical (`cmp`) to the `rtkeep`
  binary (`build/patched/rv_pp_native/noop/rv_soc_partpin`, compared with `build/patched/rv2_native/noop/rv_soc_rtkeep`).
  The FASM differs in 8 comment lines only (`# routing for net ...$S_DUP<n>`, from `nextpnr-carry-replay-order.patch`).
- **rv_pp** (rv_pr static, region `SLICE_X12Y100:SLICE_X15Y149`, RMs xor/andn/add/rot, no anchors): 108 partition pins;
  every module build prints `Partition pins: 108 net(s)` and `0 arc(s) without the locked route outside`;
  static identical outside the region for all 6 pairs; 0 static pips in the region; for all 108 nets the pips outside
  the region equal the locked route and the pin wire is on the route in all 4 builds.

## Not checked / not handled

- Vivado's own partition-pin placement (HD.PARTPIN_LOCS / HD.PARTPIN_RANGE, names as I remember them, **not checked
  against UG909**) is not reproduced: the pins must be given. A reference build without anchors put 54 of 108 pins in
  one INT tile, and a module build on them did not converge (section 3 of phase 13).
- One pin per net. A net that leaves the region at two different wires in the reference is refused by
  `flow/partpins.py`, not split.
- Hold-fix detours, `--router router1` and nets whose module side is a constant were not exercised.
- Only xc7a50t (xc7a35t package) and one region.
