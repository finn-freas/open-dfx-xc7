# Draft: route a greybox build's static side to given partition pins (xilinx + router1 check)

Status: **draft. Compiled and run offline on 2026-11-05. It has not run on hardware and has not been reviewed
upstream.** Nothing was committed, pushed or posted. The patch file is `git diff` output with a written header.

- Patch: `docs/drafts/nextpnr-partition-pins-route.patch`, 3 files, +188/-1: `himbaechel/uarch/xilinx/{xilinx.cc,xilinx.h}`,
  `common/route/router1.cc`.
- Base: the `partpin` stack, unchanged (router-region + pblock-replay + pblock-routethru + partition-pins + pblock-lutff
  + carry-replay-order).
- Variant `partpin2`: worktree `build/src/nextpnr-partpin2`, binary `build/nextpnr-build/partpin2/nextpnr-himbaechel`,
  `--version` prints `e62fafd1-partpin2`. Build it with the five `partpin` patches followed by this one, in
  `toolchain/buildenv/build_nextpnr_variant.sh` (command in `docs/phase14-auto-partpins.md` §3). The six patches
  applied to `router-region` give the worktree exactly (`git diff HEAD` compared in a scratch worktree).

## Problem

The partition-pin patch replays a static route that ends (or starts) at a pin, and routes the module from or to it.
Its pins had to come from a reference build that already crossed the region edge. Without a module there is nothing
to route to: in a greybox build, an input port's net has no sink and an output port's net has no driver. router2
skips both, and `checkRoutedDesign` rejects a sinkless net with wires (`log_assert(net_info->wires.empty())`) as well
as a route ending at a non-sink (stub).

## Change

- **`-o partition-pins-route`** (flag, with `-o partition-pins`). This runs in `preRoute` after `apply_partition_pins`.
  It acts on each partition-pin net with no cell in a routing-contained pblock whose route does not yet reach the pin:
  - **driven net:** A* from the net's wires (its source wire is bound first) to the pin;
  - **undriven net:** the pin is bound as the source, then A* from the tree to each sink wire.

  The search avoids pips at any routing-contained pblock's tile locations and LUT route-through pips. It uses only
  pips for which `checkPipAvailForNet` holds and only free wires, and it does not use another net's pin. The cost is
  pip plus wire delay, with `estimateDelay` as the heuristic, and the search stops after 2,000,000 visited wires. The
  route is bound `STRENGTH_LOCKED`. The pass logs one summary line. A net with no route is named, and the build fails.
- **`checkRoutedDesign`**: a net without sinks passes if its wires are exactly the path back from its region partition
  pin, and a route leaf that is the net's partition pin is not a stub.

How the pins are chosen is up to the caller (`flow/partpin_assign.py`, phase 14).

## Results (2026-11-05; log paths in `docs/phase14-auto-partpins.md`)

- **No-op:** rv_soc without pblock, against the `partpin` binary: `.frames` identical (`cmp`), FASM identical apart from
  comment lines.
- **rv_ppa greybox build** (`build/patched/rv_ppa_native/partpin2/grey_s`): `75 net(s) routed from their source to the
  pin, 33 from the pin to their sinks, outside the pblocks (1059 pips, locked)`; 0 static pips in the region.
- **rv_ppa module builds** on that static: static identical 6/6 pairs; partpin_check 108/108 in 4/4 builds; 12/12
  partials, byteman and region2v PROVED; two from-scratch rebuilds `.frames`-identical.
- **Negative control:** a pin given inside the region (`X31Y40/IMUX_L5`) gives `ERROR: Partition pins: no route outside
  the pblocks for 1 net(s), e.g. 'slot_rs1[5]'`.

## Not checked / not handled

- No rip-up: the pins are routed one after another, in file order, before router2, so a congested static could block
  a later pin (this did not happen here).
- Clock nets are not handled: the clock has no partition pin, so a greybox build has no clock leaf in the region
  (phase 14 §6).
- The placer still does not see partition pins; phase 14 works around this with a separate placement run.
- Only xc7a50t (in the xc7a35t package) and one region.
