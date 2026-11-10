# nextpnr-lut-a6-perm (draft, not posted)

Base: release series 0001-0031 (applies on 0001-0032). Worktree build/src/nextpnr-lpa; binaries build/nextpnr-build/lpa
(A6 gating) and lpb (+ `-o lut6-first`). Files: himbaechel/uarch/xilinx/xilinx.{cc,h}; chipdb generator change in
nextpnr-lut-a6-perm-gen.patch (against the rcal generator of build/src/nextpnr-rcal).

## Changes
- Chipdb variants (generator env): `OFX_LUT_A6_PERM=1` adds LUT permutation pseudo-pips from physical A6 to logical
  inputs 1-5 (build/chipdb-rcal-a6); `OFX_LUT_PIN_DELAY=a1,...,a6` times every permutation pip by its physical pin
  (build/chipdb-rcal-a6pd: 350,330,190,160,0,0 ps, from Vivado-timed arc net delays per pin on rv_soc).
- `-o lut-a6-perm`: the A6 pips are usable only with this option and only for a LUT alone on the 6LUT (empty 5LUT, no
  A6 net, not memory/SRL). fixup_routing and the FASM INIT writer already handle any permutation.
- `-o lut6-first`: after placement, a LUT alone on a 5LUT moves to its 6LUT and a lone x5FF flip-flop to its xFF where
  the tile stays legal (clustered and locked cells stay).

## REQUIREMENT
The A6 chipdb variants must be used with a binary that contains this patch. A binary without it does not know that
the A6 pips are special, routes through them and fails in FASM ("X_ORIG_PORT_A6 names logical input ''").

## Evidence
docs/wip/router.md and docs/qor-vivado.md Finding 16: no-op (lpa/lpb without options, A6 chipdb or rcal chipdb: FASM
identical to dp0 on 4 designs x 3 seeds); bitstreams decode and pass the rv_soc firmware bench (lpA, lpAB, lpX, lpXAB
s1); Vivado-timed exact-import results.
