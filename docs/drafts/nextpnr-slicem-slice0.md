# nextpnr-slicem-slice0 (release patch candidate 0032, on series 0001-0031 = tree f97b9b11)

xc7_logic_tile_valid() (xilinx_place.cc) checked the SLICEM-only LUTs (LUT-RAM, SRL) per tile type: rejected in a
CLBLL tile, accepted in either slice of a CLBLM tile, although only slice 0 of a CLBLM is a SLICEM. (SRLs in slice 1
were caught only in the dirty-gated per-eight loop; LUT-RAM not at all.) The unconditional guard now checks LUTs 4..7
(slice 1) of a CLBLM like all LUTs of a CLBLL. Found by the SA agent (docs/wip/placement-sa.md, c585b37).

Evidence (2026-11-08, ~/ofx-test/fixes):
- `flow/slicem_check.sh` (designs/gap/slicem_ram64x1s, a free build replayed with -o preplaced; "bad" moves the
  LUT-RAM's position to slice 1 of its CLBLM):
  - release prefix rel03 (0001-0031): ok PASS; bad FAIL: placement accepted, then
    `Assertion failure: index < length (relptr.h:56)`, the crash the SA agent saw;
  - with the patch (build rel04): ok PASS; bad PASS, refused by the placement check ("illegal placement in logic tile").
- No-op: FASM identical with and without the patch on lutram_infer, ram32m, ram64m, ram128x1d, srl, ram64x1d;
  `install/noop_check.py` on blinky, rv_soc, rv_ppt, rv_ppa: 9/22 identical, 13 ICAP line only, 0 other.
