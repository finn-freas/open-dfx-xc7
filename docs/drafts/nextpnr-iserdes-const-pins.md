# DRAFT (not posted): ISERDESE2 with constant-tied dedicated pins fails to route in nextpnr-xilinx

Status: **compiled and tested offline 2026-11-05; iserdes_pin and iserdes_noshift now build and match Vivado's decoded IOI features except one pre-existing bit; no hardware test.** Nothing pushed or posted.

Patch: docs/drafts/nextpnr-iserdes-const-pins.patch, against openXC7/nextpnr ce3f7c18, himbaechel/uarch/xilinx/pack_io.cc only (+6 lines).
- Worktree build/src/nextpnr-iserdes, build build/nextpnr-build/iserdes (`ce3f7c18-iserdes`), log build/nextpnr-build/iserdes.build.log. Also in build/nextpnr-build/gapfix.
- **Change from the first draft:** the first version (kept as build/nextpnr-build/iserdes.v1.patch) disconnected SHIFTIN1/2, OFB, DDLY, OCLK, OCLKB. Run against the gap designs it got past those pins and then failed on CLKDIVP in all three cases: `Failed to route arc ... '$PACKER_VCC_NET' ... ILOGIC_X0Y0.CLKDIVPINV_OUT` (the GND tie on the invertible CLKDIVP pin becomes VCC plus inversion). CLKDIVP was added. DYNCLKDIVSEL and DYNCLKSEL tied to 0 route without the patch touching them.

## What it fixes
A constant tie on SHIFTIN1, SHIFTIN2, OFB, DDLY, OCLK, OCLKB or CLKDIVP of an ISERDESE2 is disconnected in the packer, as already done for OSERDESE2 SHIFTIN1/2 and TBYTEIN. The packer's GND/VCC nets cannot reach these ILOGIC pins.

## Evidence (run 2026-11-05)
Command: `python3 flow/gap_patch_eval.py iserdes iserdes iserdes_pin iserdes_noshift iserdes_min oserdes_pin iddr_oddr bufio_pin qor_blinky qor_rv_soc --run`. Same JSON for stock and patched runs. Results build/gap/patch_eval_iserdes.json; logs build/gap/<d>/{stock,iserdes}/nextpnr.log.

| design | stock (ce3f7c18) | patched | Vivado diff by type (exact), viv-only / oxc7-only |
|---|---|---|---|
| iserdes (BUFIO/BUFR from a pin that also clocks fabric) | FAIL: VCC to OCLKBINV_OUT | FAIL: `BUFGCTRL_X0Y0.O to ... BUFIO_X0Y3.I` (gap G4, yosys). Builds in the combined flow, see gap-vivado.md. | - |
| iserdes_pin | FAIL: GND to SHIFTIN2 | ok | 0 / 1 (0 / 1) |
| iserdes_noshift | FAIL: GND to DDLY | ok | 0 / 1 (0 / 1) |
| iserdes_min (no ties) | ok | ok, FASM identical | 0 / 1 (0 / 1) |

- The single openXC7-only feature in all of them is `ILOGIC_Y1.IFF.ZINV_OCLK`, which stock already writes for iserdes_min. fasm.cc writes INV_OCLK/ZINV_OCLK as complements on purpose (comment "Port of nextpnr-xilinx c05f0d05"); Vivado writes neither when OCLK is unused. This patch does not change that.

## Regression
FASM and .frames identical to stock: iserdes_min, oserdes_pin, iddr_oddr, bufio_pin, qor_blinky, qor_rv_soc.

## Workaround without the patch
Leave those ISERDESE2 ports unconnected in the RTL (iserdes_min).

## Not known
- Hardware behaviour (no board).
- SHIFTIN1, OFB and OCLK are disconnected by analogy; each was not isolated in its own design.
