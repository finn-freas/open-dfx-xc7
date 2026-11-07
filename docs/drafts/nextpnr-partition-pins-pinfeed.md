# Draft: keep the pre-router partition-pin routes off other cells' pin-feed wires (xilinx)

Status: **draft. Compiled and run offline on 2026-11-06. It has not run on hardware and has not been reviewed
upstream.** Nothing was committed, pushed or posted. The patch file is `git diff` output with a written header.

- Patch: `docs/drafts/nextpnr-partition-pins-pinfeed.patch`, 1 file, `himbaechel/uarch/xilinx/xilinx.cc`.
- Base: the `partpin2` stack, unchanged (router-region + pblock-replay + pblock-routethru + partition-pins +
  pblock-lutff + carry-replay-order + partition-pins-route).
- Variant `partpin3`: worktree `build/src/nextpnr-partpin3`, binary `build/nextpnr-build/partpin3/nextpnr-himbaechel`,
  `--version` prints `e62fafd1-partpin3`. Build: `DRY_RUN=0 VARIANT=partpin3 BASE_REV=router-region
  PATCHES="nextpnr-pblock-replay.patch nextpnr-pblock-routethru.patch nextpnr-partition-pins.patch
  nextpnr-pblock-lutff.patch nextpnr-carry-replay-order.patch nextpnr-partition-pins-route.patch
  nextpnr-partition-pins-pinfeed.patch" bash toolchain/buildenv/build_nextpnr_variant.sh` (that script uses `-j8`;
  here it was built with `ninja -j4`).

## Problem (found by run, `docs/phase15-partpin-timing.md` §3)

`-o partition-pins-route` (draft `nextpnr-partition-pins-route`) routes the pin nets one after another with an A*
whose cost is delay only, and locks each route before router2 starts. A route may then take a bypass or input-mux
wire (`BYP_ALT*`, `IMUX*`) in a tile it passes as a bounce hop. When the static placement puts boundary FFs in the
slices next to the region, those wires are the only way into another FF's bypass input:

- rv_ppt, first attempt: `slot_rd[17]`, `slot_rd[12]` and `slot_rd[6]` found no route to their static FF
  (`X30Y55/SLICE_X1Y0.CFFMUX_OUT`, `X30Y53/SLICE_X0Y0.A5FFMUX_OUT`, `.C5FFMUX_OUT`) after the search had visited
  every reachable wire. A temporary, since-removed diagnostic showed the bypass wires in front of them held by
  `slot_rd[24]`, `slot_rd[30]` and `slot_rd[13]` (`X31Y55/BYP_ALT2`, `X31Y53/BYP_ALT1`, `X31Y53/BYP_ALT3`).
- With a reservation only for the pin nets' own sinks, the pin pass succeeded but router2 then failed a static net:
  `Failed to route arc 10.0 of net 'pcpi_rs1[29]' … to X33Y56/SLICE_X1Y0.B5FFMUX_OUT`, because a locked pin route
  held the bypass wire of that FF.

## Change

In `route_outside_pblocks`, a pin-feed wire may be entered only if it is on the direct approach to the search's own
target, or on the way out of the net's own site pins.

- Pin-feed wire: a site wire, `CLBL*`, `BYP*`, `IMUX*`, `FAN*`, `GFAN*`, `CTRL*`, or any `*BOUNCE*` wire.
- Direct approach: the wires reached uphill from the target through site pins (not LUT, carry, mux or XOR
  internals), `CLBL*`, `BYP*` and `IMUX*` wires, with no bounce wire.
- Way out: the wires reached downhill from the net's own site wires through pin-feed wires.

A static net that router2 routes later is no longer blocked at its pin by a locked pin route. No other change; the
routes stay `STRENGTH_LOCKED`, and a net that finds no route still fails the build by name.

## Results (2026-11-06; log paths in `docs/phase15-partpin-timing.md` §3, §5)

- **No-op:** rv_soc without pblock, against the `partpin2` binary: `.frames` identical (`cmp`), FASM identical apart
  from comment lines (`build/patched/rv_ppt_native/noop/rv_soc_partpin3`).
- **rv_ppt** (pins next to static FFs placed beside the region): the greybox build routes all 108 pins (`75 net(s)
  routed from their source to the pin, 33 from the pin to their sinks … (864 pips, locked)`) and router2 completes;
  module builds static identical 6/6, greybox vs modules 4/4 and partpin_check 4/4 at seeds 1, 2 and 3; 20/20
  partials (native_check) at seed 1.
- **rv_ppa at seed 3** (phase-14 design, only the binary changed): with `partpin2` its greybox build fails in router2
  (`Failed to route arc 15.0 of net '$abc$71968$aiger$o3449' … CEUSEDMUX_OUT`); with `partpin3` it builds, module pairs
  6/6 static identical, partpin_check 4/4 (`build/patched/rv_ppt_native/baseline/rv_ppa_seed3/`).
- The seven patches applied to `router-region` give exactly the `build/src/nextpnr-partpin3` worktree (`diff -r`).

## Not checked / not handled

- The pin-feed test is by wire name, for 7-series INT/CLB tiles only (the only tiles a pin route crosses here).
- A target that can only be entered through a bounce wire is now refused; that did not occur.
- Still no rip-up: the pin nets are routed in file order. Two attempts during this work (a LUT route-through
  fallback and a one-level rip-up with a penalised search) did not help, because the blocked wire was a bounce hop,
  not a missing route-through, and were dropped.
- Only xc7a50t (in the xc7a35t package) and one region.
