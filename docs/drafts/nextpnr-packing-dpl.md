# nextpnr-packing-dpl (draft, not posted)

Base: openXC7/nextpnr ce3f7c18 + install/patches/nextpnr 0001-0027 (TREE 961ea46e). Worktree build/src/nextpnr-dpl,
builds build/nextpnr-build/dpl0 (base), dpl1 (carry-di-bypass only), dpl2 (both). Files:
himbaechel/uarch/xilinx/{pack_carry.cc, xilinx.cc, xilinx.h, CMakeLists.txt, detail_place.cc (new)}.
Both options are off by default.

## -o carry-di-bypass (packing)
Problem: `pack_carries` gives every CARRY4 DI input that no single-load LUT drives a feed-through LUT on the 5LUT of
the carry position (rv_soc: 366 of 368 DI inputs), and only accepts LUT1-LUT5 as the S LUT. The S LUT and the DI
feed-through then share the 5 inputs of one LUT6 site, so an S LUT with 5 inputs, or a LUT6, gets a feed-through as
well and sits elsewhere (rv_soc 145 of 376 S inputs, bram 125/392, rv_big 144/603). Vivado feeds DI from the
slice's X pin (AX..DX through the xCY0 mux) and keeps the S LUT, a LUT6 included, in the carry slice
(Vivado's own placement of rv_soc: 100 % of S LUTs in the carry slice).

Change: a DI input that is not a constant, and is not DI0 of a chain head whose CYINIT already uses AX, is left
connected to the CARRY4; the carry's X-pin use is recorded (attribute X_DI_BYPASS, read into the cell tags'
`x_sigs`) so the slice validity check keeps a flip-flop bypass or MUXF7/F8 select off that X pin. The S LUT may then
be a LUT6. The chipdb already has the AX -> ACY0 site pip and the FASM writer emits no ACY0 bit for it (AX is the
default), so routing and bitstream needed no change.

## -o dpl[=RADIUS,PASSES,CRIT,EXP] (detailed placement)
After legalisation and placer1 refinement (XilinxImpl::postPlace, before fixup_placement): every unclustered LUT
and flip-flop with an arc of criticality >= CRIT (default 0.8) is offered every compatible bel within RADIUS tiles
(default 2) of the criticality-weighted centre of its connections, as a move to a free bel or a swap with an
unclustered cell of the same type. A change is kept when the slice stays legal (isBelLocationValid on both tiles)
and the criticality^EXP-weighted predicted delay of both cells' arcs drops. Arc model: a LUT input costs 665/682 ps
from its own slice/tile, a LUT feeding the flip-flop of its own position 0, between tiles 313 + 1.235 x the delay
matrix (the fit of docs/drafts/nextpnr-placer-delay-cal.md). PASSES rounds (default 3), timing re-analysed between
them. Not run with -o preplaced / -o prerouted.

## Evidence
docs/qor-vivado.md, Finding "packing and detailed placement". Harness flow/dpl_bench.py, metrics
flow/dpl_metrics.py, Vivado runner flow/dpl_vivado.sh + vivado/dpl_dump.tcl, bitstream check flow/dpl_check.sh.

## Status (2026-11-07)
- No-op with both options off (FASM identical to the base on rv_soc and bram). Bitstreams assemble for 5 designs x 3 seeds; rv_soc decoded bitstreams pass the firmware bench 11/11.
- Area: LUT cells -6 to -20 %, slices -3 to -16 % (bram 287 slices, Vivado 290).
- Vivado's timer, mean of seeds 1-3 (docs/qor-vivado.md Finding 15): rv_soc 117.18 -> 112.35, bram 149.35 -> 152.44, rv_mul 102.11 -> 97.06 MHz, all within the seed spread; slices -7 to -16 %, HPWL -2 to -8 %, routed PIPs -1 to -3 %. An area/wirelength option, Fmax-neutral; not a default candidate on Fmax grounds. `-o dpl`: no measured gain yet.
