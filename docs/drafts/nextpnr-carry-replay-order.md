# Draft: carry S sources packed the same way whatever the module

Status: **draft. Compiled and run offline on 2026-11-05; not on hardware, not reviewed upstream.** Not committed, not
posted. Patch: `docs/drafts/nextpnr-carry-replay-order.patch`, 1 file, +17/-2: `himbaechel/uarch/xilinx/pack_carry.cc`.
Base: `nextpnr-pblock-lutff.patch` (variant `partpin`, see `nextpnr-partition-pins.md`).

## Problem (found by run)

`pack_carries` moves a LUT that drives the S inputs of several carry chains into the first chain's carry site and gives
the others a copy named `<lut>$S_DUP<n>`. The first chain is the first in the cell table, and `<n>` is the global
`autoidx`. Both depend on every cell of the netlist: erasing and creating cells reorders nextpnr's `dict`, and other
copies advance the counter. In the native PR flow the static logic is packed again with each module and `-o preplaced`
/ `-o prerouted` look its cells and nets up by name. With the `add` module (its own carry chains) the static carries
packed differently from the reference, and the build stopped with

```
ERROR: attempting to reserve sink input path wire 'X42Y8/SLICE_X0Y0.D6LUT_O6' for nets
'$techmap72495$abc$71968$lut$aiger71967$3335.A[0]' and '$techmap72495$abc$71968$lut$aiger71967$3335.A[0]$S_DUP1'
```

(rv_pp `add_n`; the first version of this patch numbered copies per source only, and the error remained with
`$S_DUP1`; the failing build directories were replaced by the passing ones, so the line is quoted from the session.)
The anchor-shell flows did not hit it in their builds.

## Change

- Copies are numbered per source cell (`dict<IdString, int>`), not by `autoidx`.
- When the XDC has pblocks, the root MUXCYs are sorted by name before the chains are built. Without pblocks the order
  is the old one.

## Results

- No-op: rv_soc without pblock, `.frames` identical to `rtkeep`; the FASM differs in 8 comment lines that name the
  copies' nets (`$S_DUP1` instead of `$S_DUP16` etc.; `build/patched/rv_pp_native/noop/`).
- rv_pp: `add_n` and `rot_n` build; static identical outside the region for all 6 pairs (`docs/phase13-partition-pins.md`).

## Not checked

- Other packer passes whose choices depend on cell-table order (LUT6_2 pairing, MUXF, SRL, feed-through LUT names) were
  not audited; none caused a failure here.
- Sorting changes which chain takes a shared LUT for designs with pblocks; timing impact not measured beyond the rv_pp
  builds (145.62 MHz, phase 13).
