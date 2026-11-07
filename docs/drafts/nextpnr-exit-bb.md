# nextpnr draft: `-o exit-bb` (routing box anchor for non-logic pins)

Opt-in; without the option the binary is identical in behaviour to stock (rv_soc .frames identical,
build/runtime/rtbb_off/rv_soc/r1 vs build/runtime/base/rv_soc/r1).

## Problem
On rv_soc, router2 spent 86.6 s of a 107.6 s nextpnr run (build/runtime/base/rv_soc/r1/nextpnr.log, load 14).
The "slowest nets by runtime" table is the 24 ICAP outputs `icap_o[*]`, 1.7-5.9 s each.
`--debug-router` on icap_o[24] (build/runtime/prof/icapdbg/out.txt):
- box (12,117)-(48,126); the bounded search fails after 2.06 s;
- the retry without a box routes the arc in 0.04 s; the route enters the interconnect at X48Y131, outside the box.

The box comes from `XilinxImpl::getRouteBoundingBox`, which adds `source_locs`/`sink_locs` from
`find_source_sink_locs()`. That search stops at the first general-routing wire, which for these pins
does not give the row the route actually leaves through.

## Change
`-o exit-bb`: the search continues until the general-routing wire is in an INT_L/INT_R tile.
Same iteration caps as before (sources 20000, sinks 500). If no such wire is found within the cap, no anchor is recorded (stock would have recorded the first general wire).

## Results
rv_soc (5 runs): routing 8.1-10.7 s instead of 50.8-88.0 s, total 35.6 s median instead of 80.9 s, nextpnr Fmax 163.35 vs 159.92 MHz. LiteX ddr3: routing unchanged within noise, sys_clk 111.74 vs 111.04 MHz. Details in docs/runtime.md. Routes change wherever a non-logic pin's anchor moves, so this is a QoR
trade-off and is measured there (Fmax with nextpnr's timer, one seed per design).

## Build
`build/nextpnr-build/rtbb_build.sh` (worktree build/src/nextpnr-rtbb at ce3f7c18 + this patch, -j2).
