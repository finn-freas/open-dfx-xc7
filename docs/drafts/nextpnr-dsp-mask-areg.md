# DRAFT (not posted): nextpnr-xilinx DSP48E1 FASM differs from Vivado for MASK[47:46] and AREG/BREG=1

Status: **compiled and tested offline 2026-11-05; FASM matches Vivado's decoded DSP features on all four DSP gap designs; no hardware test.** Nothing pushed or posted.

Patch: docs/drafts/nextpnr-dsp-mask-areg.patch, against openXC7/nextpnr ce3f7c18, himbaechel/uarch/xilinx/fasm.cc only.
- Worktree: build/src/nextpnr-dsp (detached at ce3f7c18, patch applied, not committed). Build: build/nextpnr-build/dsp (`nextpnr-himbaechel --version` prints `ce3f7c18-dsp`), log build/nextpnr-build/dsp.build.log. Built with `VARIANT=dsp PATCHES=nextpnr-dsp-mask-areg.patch DRY_RUN=0 bash toolchain/buildenv/build_nextpnr_variant.sh`. The only compiler warning is the pre-existing xilinx.cc:1240 `-Wsign-compare`.
- Also part of the combined build build/nextpnr-build/gapfix.

## What it fixes
- ce3f7c18 writes AREG/BREG only for 0 and 2 (comment: "no bit is 1"). prjxray-db a8b09269 has `DSP_0.AREG_1 !26_113 !26_137 27_111` (and BREG_1), and Vivado 2025.2 sets it.
- ce3f7c18 truncates MASK to 46 bits ("prjxray only recognizes 46 bits"). The db has MASK[46] and MASK[47] for DSP_0/DSP_1 in DSP_L/DSP_R. The patch writes all 48 bits; unset bits 46/47 default to 0, as Vivado writes them for the unisim default 48'h3FFF_FFFF_FFFF.

## Evidence (run 2026-11-05)
Command: `python3 flow/gap_patch_eval.py dsp dsp48e1 dsp_cascade dsp_patdet dsp_infer qor_rv_mul qor_blinky qor_rv_soc --run`.
Each design is placed and routed twice from the same yosys JSON (build/gap/<d>/oxc7/<d>.json): with the stock rebuild (build/gap/<d>/stock/) and with the patch (build/gap/<d>/dsp/). Results: build/gap/patch_eval_dsp.json, log build/gap/patch_eval_dsp.log; per-run logs build/gap/<d>/{stock,dsp}/nextpnr.log.
Stock FASM is byte-identical to the nightly's (build/gap/<d>/oxc7/) for all seven designs.

Decoded non-CLB/non-INT features against Vivado, viv-only / oxc7-only, by tile type (gap_report "by_tile_type"):

| design | stock | patched | FASM lines changed (patched vs stock) |
|---|---|---|---|
| dsp48e1 | 2 / 0 (AREG_1, BREG_1) | **0 / 0** | +3 / -1: AREG_1, BREG_1, MASK[47:0] replaces MASK[45:0] |
| dsp_cascade | 2 / 0 | **0 / 0** | +6 / -2 (both DSPs) |
| dsp_patdet | 4 / 0 (AREG_1, BREG_1, MASK[46], MASK[47]) | **0 / 0** | +3 / -1; MASK[47:0] = 48'hffff_ffff_0000 |
| dsp_infer | 2 / 0 | **0 / 0** | +3 / -1 |
| qor_rv_mul (4 DSPs) | 35 / 25 | 33 / 25 | +8 / -4, DSP lines only |

- qor_rv_mul: AREG_1/BREG_1 no longer appear on the Vivado-only side. The remaining DSP entries (Vivado AREG_2/BREG_2; openXC7 AREG_0/BREG_0/A_INPUT/ZCREG) come from the two synthesizers mapping the multiplier differently, not from the FASM writer. The other residuals are BRAM.
- Only DSP FASM lines changed in every DSP design; placement and routing are the same as stock. nextpnr Fmax for qor_rv_mul is 140.69 MHz in both runs.

## Regression
- qor_blinky and qor_rv_soc: FASM and .frames identical to stock (patch_eval_dsp.json `fasm_identical`, `frames_identical`).

## Not known
- Whether AREG_1 (bit 27_111) changes silicon behaviour, or whether the all-zero state already acts as AREG=1. The MASK[47:46] case is a real functional difference for pattern detect with those mask bits set. No hardware test was done.
