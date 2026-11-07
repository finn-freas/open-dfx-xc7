# Draft: no LUT-FF pair across a pblock edge

Status: **draft. Compiled and run offline on 2026-11-05; not on hardware, not reviewed upstream.** Not committed, not
posted. Patch: `docs/drafts/nextpnr-pblock-lutff.patch`, 3 files, +31: `himbaechel/uarch/xilinx/{pack.cc,xdc.cc,xilinx.h}`.
Base: `nextpnr-partition-pins.patch` (variant `partpin`, see `nextpnr-partition-pins.md`).

## Problem (found by run)

`pack_lutffs` clusters a flip-flop with the LUT (O6) or CARRY4 that drives its D, and `apply_pblocks_after_packing`
then gives the whole cluster the pblock of the member that has one. When a module output is combinational and the
static side registers it, the static flip-flop joins the module's pblock:

```
Warning: 32 cell(s) outside any pblock were packed into a cluster with pblock cells, and are now in that pblock
```

(the first rv_pp reference build, before this fix; that log was overwritten when the build was redone with the fix,
so the line is quoted from the session, not from a file. The routed result had the 32 `pcpi_rd` flip-flops in
D5FF/DFF sites of the region, packed with the module's LUTs.)
The anchor shells never hit this: their outputs are flip-flops in the pblock, and an FF-to-FF connection is not paired.

## Change

`XilinxImpl::cells_in_different_pblocks(a, b)` answers from `pblock_prepack_cells` (the record the XDC reader keeps),
counting a packer-made cell under the netlist cell it is named after, the same longest-prefix rule as
`apply_pblocks_after_packing`. `pack_lutffs` skips a pairing when it says yes. With no pblock the record is empty and
the function returns at once.

## Results

- No-op: rv_soc without pblock, `.frames` identical to `rtkeep` (see `nextpnr-partition-pins.md`).
- In every rv_pp build (`build/patched/rv_pp_native/partpin/*/nextpnr.log`) the "packed into a cluster with pblock
  cells" warning is absent; `pr_check` finds static identical outside the region for all 6 module pairs.

## Not checked

- Other packer clusters (carry, MUXF, SRL, LUT6_2 pairs) can still join cells across a pblock edge. Only `pack_lutffs`
  was seen to do it here.
- Vivado keeps partition boundaries out of such packing by construction; its rule was not compared.
