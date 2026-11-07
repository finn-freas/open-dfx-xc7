# DRAFT (not posted): prjxray-db features for DIFF_TERM, the FIFO width code and the ICAP/DNA_PORT enables (xc7a35t)

Target: openXC7/prjxray-db (artix7). Posting needs the user's approval. Nothing here ran on hardware.

Files (one line per feature, prjxray segbits syntax; `flow/prim_db.py --run` appends them to a symlinked copy of the
toolchain's prjxray-db in `build/prjxray-db-prim/`, and refuses a feature name the database already has):
- `docs/drafts/prjxray-db-diff-term.segbits`: `LIOB33/RIOB33.IOB_Y0.LVDS_25.IN_ONLY_DIFF_TERM`
- `docs/drafts/prjxray-db-fifo.segbits`: `BRAM_L/BRAM_R.FIFO_PORT_WIDTH_{4,9,18,36}`
- `docs/drafts/prjxray-db-cfg-in-use.segbits`: `CFG_CENTER_MID.ICAP.IN_USE`, `CFG_CENTER_MID.DNA_PORT.IN_USE`

The names are proposals; prjxray-db a8b09269 has no feature on any of these bits.

## Method
- Vivado v2025.2, xc7a35tcsg324-1, non-project flow `vivado/build_gap.tcl` (batch `prim`, `vivado/run_gap.ps1 -Tag prim`).
  Designs from `flow/prim_designs.py` (new) and `flow/gap_designs.py`. Outputs `C:\Users\finnf\open-dfx-xc7-vivado\build\prim\<d>\`,
  copied to `build/gap/<d>/viv/`.
- Decode: `flow/bit2fasm.py --verbose` with the stock database; unknown bits mapped to tile and tile-relative
  segbit by `flow/gap_report.py` (`unknown_bits`). Decode with the draft database: `flow/prim_eval.py`
  (`build/gap/<d>/viv/<d>.viv.prim.fasm`).
- Collisions: a candidate bit set is accepted only if it appears identically in every build that has the setting
  and in no build without it.

## DIFF_TERM (IBUFDS LVDS_25, input only)
| build | pairs with DIFF_TERM TRUE | unknown bits (stock db) |
|---|---|---|
| diff_lvds (gap) | 1 (LIOB33_X0Y91) | 6: 38_100 38_118 39_97 39_113 39_119 39_125 |
| dt_a | 7: LIOB33_X0Y{97,83,65,123}, RIOB33_X43Y{47,29,11} | 42 = the same 6 in each of the 7 tiles |
| dt_b | 7 other pairs: LIOB33_X0Y{95,75,55,127}, RIOB33_X43Y{39,21,3} | 42 = the same 6 in each tile |
| dt_a_none (dt_a, DIFF_TERM FALSE) | 0 | 0 |
| dt_xdc (independent check: DIFF_TERM set by `set_property DIFF_TERM TRUE [get_ports ...]`, not by the parameter) | 2: LIOB33_X0Y59, RIOB33_X43Y33 | 12 = the same 6 in each |

- The 6 bits are the four set bits of the existing `IOB_Y0...TMDS_33.IN_ONLY` key plus 38_100 and 39_97, which that
  key requires clear. So the feature is the IN_ONLY key with those two bits flipped (same negated bits otherwise),
  and it replaces IN_ONLY on a terminated P half. A two-bit "delta" feature does not work: fasm2frames clears the
  IN_ONLY key's negated bits and rejects the pair (`FasmInconsistentBits`, build/gap/diff_lvds/ofx-prim/fasm2frames.log
  of the first try), and the decoder would see 38_100/39_97 inside every LVDS_25 output's `DRIVE.I_FIXED`.
- Same bits on LIOB33 and RIOB33 (17 tiles, both bank types of this part). Only Y0 (P half). 0 collisions.
- IOBUFDS (bidirectional) with DIFF_TERM TRUE (dt_xdc, LIOB33_X0Y121): Vivado's decoded tile is identical to the
  iobufds gap design without DIFF_TERM (LIOB33_X0Y79, compared feature by feature with coordinates stripped). The two
  extra bits are already set by `LVDS_25.DRIVE.I_FIXED`, so no feature is needed there.
- Not measured: HP banks (none on this part), other DIFF_TERM-capable standards (MINI_LVDS_25, PPDS_25, RSDS_25),
  other families.

## FIFO width code (BRAM_L/BRAM_R 27_172, 27_173, 27_174)
| build | primitive, DATA_WIDTH | width of one RAMB18 half | bits set | tile |
|---|---|---|---|---|
| f18_w4 | FIFO18E1, 4 | 4 | 27_172 | BRAM_L_X30Y30 |
| f18_w9_fwft | FIFO18E1, 9 | 9 | 27_173 | BRAM_L_X30Y30 |
| fifo18e1, fifo18e1_async, f18_async_o | FIFO18E1, 18 | 18 | 27_172 27_173 | BRAM_L |
| f18_w36 | FIFO18E1 FIFO18_36, 36 | 36 | 27_174 | BRAM_R_X37Y10 |
| f36_w9_async | FIFO36E1, 9 | 4 | 27_172 | BRAM_R_X37Y10 |
| f36_w18 | FIFO36E1, 18 | 9 | 27_173 | BRAM_L_X30Y20 |
| fifo36e1 | FIFO36E1, 36 | 18 | 27_172 27_173 | BRAM_L_X30Y25 |
| f36_w72 | FIFO36E1 FIFO36_72, 72 | 36 | 27_174 | BRAM_L_X30Y20 |

- The three bits are a code of the half width: 4 = 1, 9 = 2, 18 = 3, 36 = 4. Derived from the five FIFO18E1 builds;
  the four FIFO36E1 builds were predicted from it before they were decoded and all matched (independent check).
- The RAMB gap builds (ramb18e1, ramb36e1, ramb36_cascade, ramb36_ecc2, bram_infer) decode with 0 unknown bits, so none
  of them sets these bits.
- Not measured: FIFO36E1 DATA_WIDTH 4 (half width 2; nextpnr refuses it), BRAM_R with every width.
- The earlier note "2 bits for every FIFO" (prjxray-db-vivado-unknown-bits.md) came from three builds that were all
  18 bits per half.

## ICAPE2 and DNA_PORT enables (CFG_CENTER_MID_X46Y32)
| build | ICAPE2 | DNA_PORT | unknown bits |
|---|---|---|---|
| icape2 (gap) | X32 | - | 26_2206 26_2207 27_2205 |
| icape2_x8 | X8 | - | 26_2206 26_2207 27_2205 |
| icape2_x16 | X16 | - | 26_2206 26_2207 27_2205 |
| dna_port (gap) | - | yes | 26_2213 27_2210 27_2215 |
| dna_port2 (DNA_PORT on a BUFG of a divided clock, READ/SHIFT from flip-flops) | - | yes | 26_2213 27_2210 27_2215 |
| icap_dna (both) | X32 | yes | the union of the two sets |
| lut_ff, bscane2, startupe2, usr_accesse2, frame_ecce2 (gap controls) | - | - | 0 |

- The ICAP bits do not depend on ICAP_WIDTH (the width has its own keys). 3-bit triples, like the other
  CFG_CENTER_MID keys (e.g. `STARTUP.PROG_USR`).
- The DNA_PORT site is in CFG_CENTER_TOP_X46Y42; its bits are in the CFG_CENTER_MID segment.
- Only ICAP_X0Y0 was placed (Vivado and nextpnr). The second ICAP site's bits are not known.
- Effect on silicon unknown (no board): whether an ICAPE2 or DNA_PORT works without these bits was not tested.

## Check
With the three files added, every Vivado build above decodes with 0 unknown bits, and the openXC7 builds of the same
RTL with the `ofx-prim` nextpnr decode to the same non-routing features (table in docs/gap-vivado.md).
