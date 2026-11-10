# prjxray-db DSP48E1 USE_MULT=NONE bit (draft, not posted)

prjxray-db (artix7, a8b09269) names no feature for DSP48E1 `USE_MULT`. Phase 10 found one unnamed bit set in a
Vivado DFX bitstream on a DSP with `USE_MULT=NONE` (docs/phase10-vivado-parity.md §9, called 26_277 there; it is
26_245 in prjxray-db's segbit numbering, docs/phase16-dfx-gaps.md §6).

## Run
- Designs `designs/gap/dsp_um_{none,multiply,dynamic}`: four DSP48E1 at DSP48_X0Y0, X0Y1, X1Y0, X1Y1 (one DSP_L and
  one DSP_R tile, both sites of each), identical settings (AREG=BREG=CREG=PREG=1, ACASCREG=BCASCREG=1, MREG=0,
  USE_DPORT=FALSE, OPMODE A:B + C) except USE_MULT. MREG=0 because USE_MULT=NONE requires it.
- Vivado 2025.2, xc7a35tcsg324-1, `vivado/build_gap.tcl` (run by the validation agent on slot 3, 2026-11-08,
  `C:\Users\finnf\open-dfx-xc7-vivado\build\dspum`, status rc 0 for all three).
- Decoded with `flow/dsp_use_mult.py` (bit2fasm --verbose; unknown bits per DSP tile): `build/dfxgaps/dspum/`.

## Result
| variant | unnamed bits in DSP_L_X34Y0 | unnamed bits in DSP_R_X9Y0 | named DSP features |
|---|---|---|---|
| USE_MULT=NONE | 26_85, 26_245 | 26_85, 26_245 | 24 per tile, equal in all three |
| USE_MULT=MULTIPLY | none | none | same |
| USE_MULT=DYNAMIC | none | none | same |

So one bit per DSP site, set exactly when USE_MULT=NONE: DSP_0 26_85, DSP_1 26_245 (DSP_1 = DSP_0 + 160, the same
offset as every other DSP_1 feature, e.g. AREG_1 27_111 / 27_271). It sits next to `USE_SIMD_FOUR12_TWO24`
(26_84 / 26_244). MULTIPLY and DYNAMIC give the same configuration bits in this run.

## Limits
- One device, one Vivado version, one setting of the other attributes. Not checked: whether the bit depends on
  USE_SIMD, on MREG (MREG=1 is illegal with NONE), or on other parts.
- What the bit does on silicon is not known (plausibly a multiplier enable/power gate; not measured).

## Writing it from the open flow
`docs/drafts/nextpnr-dsp-use-mult.patch` (on the router stack, build/src/nextpnr-dspum, 2 files: fasm.cc, xilinx.cc):
`-o dsp-use-mult-none` (opt-in) writes `DSP48.DSP_n.USE_MULT_NONE` for a DSP48E1 with `USE_MULT="NONE"`; the
database needs the four segbits lines above (a copy with them: build/prjxray-db-dspum, passed as `--db-root`).

Check (build/dfxgaps/umtest, `build/dfxgaps/um_cmp.py`): the same `dsp_um_*` designs built with the open flow at the
same DSP sites. USE_MULT=NONE with the option: unnamed bits (decoded with the stock database) DSP_L_X34Y0 and
DSP_R_X9Y0 26_85 + 26_245, the same as Vivado's; without the option none. The FASM with and without the option
differs in exactly the four USE_MULT_NONE lines and the bitstreams in exactly 4 bits. USE_MULT=MULTIPLY: `.frames`
identical with and without the option (no-op).
