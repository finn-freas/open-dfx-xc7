# WIP: synthesis area (LUT / FF / carry gap to Vivado synth)

Goal: close the area gap between our yosys synthesis and Vivado's synth_design on the benchmark designs without losing
Fmax. Driver: `flow/synth_area.py` (variants in `VARIANTS`, results cached by hash in `build/qor/synarea/synth/<design>/
<variant>_<key>/meta.json`). Tool: `tools/mt_lut/mt_lut.cpp` (mockturtle LUT mapper, binary `build/mt_lut/mt_lut`).

## Reconstruction of the first session (2026-11-10 10:32-11:12, killed mid-work, no notes)

Everything below is read back from disk (meta.json files, logs in `build/qor/synarea/logs/`, Vivado output in
`C:\Users\finnf\open-dfx-xc7-vivado\build\synarea\`).

What ran:
- 10:32-11:12 yosys: `synth_area.py synth --run` of 34 variants; `base` on 16 designs (rv_soc rv_mul rv_big bram fir
  aes sha256 sha512 serv axi_xbar or1200 vtr_sha mkpktmerge vexriscv blob_merge arty_ddr3), the first-round variants
  (syn2, c_unit, c_flat2, c_l6, c_l6b, a_mfse, a_fa, a_R10, a_area, s_share) on 15 of them (not vexriscv), the
  second-round ones (cu_*, c_unit8, c_u6w, a_rep, a_synch2, m_lr*, s_cmw*) on 5-8 designs. The run was cut while it
  was on serv / sha512.
- No-op checks: `noop` (custom map_luts path with the default settings) and `noop_abc` (default ABC script passed
  explicitly) give the base cell counts on rv_soc (1107 LUT).
- 10:42-10:43 abc9 dumps (`abc9 -nocleanup -showtmp`) of rv_soc, sha256, aes into `build/qor/synarea/mt/`
  (`<d>.xaig`, `<d>.box`, `<d>.lut`, `<d>.plain.aig`, the ABC script). `mt_lut` was built at 10:51; no mt_lut result
  was recorded anywhere.
- Vivado (`vivado/slot_run.sh synarea build_synx.tcl build/qor/synarea/src ...`, Default directive, full P&R):
  `rv_soc_viv` and `rv_soc_base` finished (rc 0); `rv_soc_hl1` was killed during the run (no status.txt). Sources were
  prepared for `<d>_viv` and `<d>_base` of 15 designs and for rv_soc hl1 / hl2 / c_unit / cu_hl1; none of those ran.
- Equivalence (`synth_area.py equiv`): bram c_unit sequential miter PROVEN (ABC dprove; equiv_struct leaves 1 of 1103
  cells unproven, lfsr[59], same as in docs/wip/synthesis.md); aes c_unit miter and the rv_soc c_unit lockstep sim
  were cut by the kill (119 cycles, no verdict): not evidence.

Results of that session, Vivado P&R of rv_soc (Default, Vivado timer; `build/qor/synarea/report.json`):

| netlist | LUT sites post-route | LUTRAM sites | FF | CARRY4 | slices | LUTs using O5+O6 | Fmax MHz | levels |
|---|---|---|---|---|---|---|---|---|
| Vivado synth_design (`viv`) | 1041 | 50 | 771 | 63 | 377 | 115 | 171.00 | 3 |
| yosys default (`base`) | 1122 | 56 | 768 | 92 | 398 | 41 | 157.63 | 6 |

Results of that session, yosys cell counts (LUT = LUT1-6 + INV cells of the yosys netlist, before any LUT pairing):
see "Area table" below (regenerated from the cache with `synth_area.py table`).

Variant families (definitions in `flow/synth_area.py`):
- `syn2`: the x1_cal_syn2 preset of docs/wip/synthesis.md (abc9.xaiger=1, flat 200 ps LUT model, -W 450, `&syn2`).
- `c_*`: abc9 LUT area costs. Yosys default: LUT1 1, LUT2 2, LUT3-5 3, LUT6 5, LUT7 10, LUT8 20. `c_unit` = 1 per
  LUT1-6, LUT7 2, LUT8 4 (the mapper then minimises LUT count); `c_l6` only LUT6 5 -> 4; `c_unit8` all 1 (MUXF7 flood).
- `a_*`: ABC script changes on the default cost model (`&mfs -e`, `&if` flow/area iterations, second `&dch; &if`
  round, `&synch2`, `&if -R`, `&if -a`).
- `cu_*`: c_unit combined with an ABC script change, abc9.xaiger=1, the calibrated model, or `abc9 -dff`.
- `hl*` / `cu_hl*`: SOFT_HLUTNM LUT-pair hints for Vivado P&R only (netlist logic unchanged, yosys counts unchanged).
- `m_lr*`: LUTRAM cost scale in memory_libmap. `s_cmw*`: narrow adders to LUTs instead of CARRY4. `s_share`:
  `share -aggressive`. `s_nowide`, `s_dff`: defined, never run.

## Area table: yosys recipes against Vivado synth_design (resumed session, 2026-11-10 11:40-12:05)

`python3 flow/synth_area.py compare --designs <all 16> --variants base syn2 c_unit cu_fa cu_rep --exclude fir
mkpktmerge vexriscv` (output kept in `build/qor/synarea/compare.md` / `compare.json`). No new Vivado run: the Vivado
column is Vivado's own synth_design of the same RTL from existing runs (`qor_synx/<d>_viv/synth_util.rpt` = after
synth, else `qor_suite/<d>__free/run0/util.rpt` = after route). LUT = LUT cells: LUT1-6 (+ INV) cells of the yosys
netlist, LUT1-6 rows of Vivado's Primitives table; both before LUT6_2 pairing, so not "Slice LUTs" (sites).
rv_mul, vexriscv (the Vivado run is of an "untied" wrapper) and arty_ddr3 have no usable Vivado reference here.

| design | Vivado LUT (stage) | base | syn2 (x1_cal_syn2) | c_unit | cu_fa | cu_rep | FF V / ours | CARRY4 V / base / syn2 | MUXF7 V / base / syn2 / c_unit / cu_fa / cu_rep |
|---|---|---|---|---|---|---|---|---|---|
| rv_soc | 1104 (synth) | 1107 (+0.3%) | 1141 (+3.4%) | 1070 (-3.1%) | 1075 (-2.6%) | 1060 (-4.0%) | 767 / 764 | 63 / 92 / 88 | 0 / 1 / 0 / 17 / 17 / 15 |
| rv_mul | - | 1575 | 1581 | 1529 | 1510 | 1512 | - / 1073 | - / 148 / 143 | - / 0 / 0 / 19 / 15 / 27 |
| rv_big | 1678 (synth) | 1626 (-3.1%) | 1607 (-4.2%) | 1583 (-5.7%) | 1564 (-6.8%) | 1556 (-7.3%) | 1094 / 1108 | 123 / 148 / 146 | 0 / 0 / 2 / 22 / 16 / 25 |
| bram | 945 (route) | 869 (-8.0%) | 860 (-9.0%) | 868 (-8.1%) | 868 (-8.1%) | 868 (-8.1%) | 509 / 494 | 80 / 98 / 98 | 0 / 0 / 0 / 0 / 0 / 0 |
| fir | 18 (route) | 23 | 15 | 23 | 22 | 23 | 598 / 1589 | 0 / 0 / 0 | 0 |
| aes | 3766 (route) | 3957 (+5.1%) | 5105 (+35.6%) | 3736 (-0.8%) | 3450 (-8.4%) | 3525 (-6.4%) | 2661 / 2665 | 0 / 5 / 5 | 16 / 106 / 47 / 367 / 298 / 257 |
| sha256 | 3961 (route) | 4797 (+21.1%) | 4663 (+17.7%) | 4498 (+13.6%) | 4437 (+12.0%) | 4352 (+9.9%) | 2729 / 2676 | 208 / 198 / 198 | 128 / 0 / 0 / 115 / 47 / 76 |
| sha512 | 4319 (route) | 5001 (+15.8%) | 4898 (+13.4%) | 4712 (+9.1%) | 4628 (+7.2%) | 4468 (+3.4%) | 2711 / 2705 | 220 / 209 / 209 | 187 / 0 / 22 / 271 / 179 / 154 |
| serv | 3890 (route) | 4206 (+8.1%) | 4091 (+5.2%) | 3987 (+2.5%) | 3926 (+0.9%) | 3923 (+0.8%) | 4539 / 4535 | 0 / 98 / 98 | 272 / 48 / 124 / 172 / 125 / 115 |
| axi_xbar | 3305 (route) | 3519 (+6.5%) | 3459 (+4.7%) | 3091 (-6.5%) | 3071 (-7.1%) | 3137 (-5.1%) | 2989 / 3021 (syn2 2997) | 0 / 82 / 82 | 4 / 4 / 17 / 165 / 176 / 164 |
| or1200 | 2472 (route) | 2534 (+2.5%) | 2500 (+1.1%) | 2387 (-3.4%) | 2358 (-4.6%) | 2340 (-5.3%) | 1106 / 1170 | 133 / 134 / 126 | 7 / 0 / 0 / 125 / 126 / 129 |
| vtr_sha | 5626 (route) | 5376 (-4.4%) | 5406 (-3.9%) | 5327 (-5.3%) | 5276 (-6.2%) | 5305 (-5.7%) | 3781 / 3759 | 224 / 206 / 206 | 0 / 40 / 80 / 19 / 8 / 88 |
| mkpktmerge | 484 (route) | 2083 | 2008 | 2046 | 1965 | 2039 | 342 / 5329 | 0 / 74 / 74 | 0 / 0 / 0 / 4 / 2 / 2 |
| vexriscv | - | 2320 | 2285 | 2179 | 2175 | 2178 | - / 1388 | - / 130 / 131 | - / 2 / 5 / 78 / 73 / 69 |
| blob_merge | 6117 (route) | 4158 (-32.0%) | 4176 (-31.7%) | 4041 (-33.9%) | 3994 (-34.7%) | 4038 (-34.0%) | 674 / 674 | 1053 / 1008 / 1008 | 0 / 0 / 0 / 93 / 59 / 74 |
| arty_ddr3 | - | 5454 | 5465 | 5063 | 5044 | 5157 | - / 3741 | - / 255 / 255 | - / 2 / 20 / 136 / 94 / 107 |

LUT cells against Vivado, geometric mean over the 11 designs with a reference and the same memories/DSPs (aes
axi_xbar blob_merge bram or1200 rv_big rv_soc serv sha256 sha512 vtr_sha): base +0.1 %, syn2 +1.6 %, c_unit -4.6 %,
cu_fa -6.1 %, cu_rep -6.3 %. Without blob_merge (Vivado 47 % more LUTs there): base +4.0 %, syn2 +5.7 %,
c_unit -1.0 %, cu_fa -2.6 %, cu_rep -2.9 % (10 designs).
FF and CARRY4 are the same in every c_* / a_* / cu_* recipe as in base (only syn2 and the s_cmw / cu_dff recipes
change them), so the columns show base (and syn2 for CARRY4).

What the table says about the gap:
- LUT cells: on the mean we are level with Vivado already; the gap is per design (sha256 +21 %, sha512 +16 %, serv
  +8 %, axi_xbar +6.5 %, aes +5 %) and is where Vivado uses MUXF7 (sha256 128, sha512 187, serv 272) and we use none:
  yosys prices a LUT7 (2 LUT6 + MUXF7) at 10 against 5 for a LUT6. The unit-cost recipes remove most of it.
- CARRY4: +19 to +46 % on the CPUs (rv_soc 92 vs 63, rv_big 148 vs 123), 98 vs 0 on serv, 82 vs 0 on axi_xbar:
  Vivado maps short adders/comparators to LUTs. `s_cmw5` / `s_cmw8` (adders < 5 / < 8 bits to LUTs) cut CARRY4
  92 -> 88 / 76 on rv_soc but cost LUTs (+0.4 / +2.9 %): mean over 7 designs +0.6 % / -0.2 % LUT. Not pursued.
- FF: within 1 % everywhere except fir (1589 vs 598: Vivado's DSP48 registers / SRLs, the DSP pipeline topic of
  docs/wip/synthesis.md) and mkpktmerge (5329 FF + 1920 LUTRAM sites vs 342 FF + 40 block RAMs: Vivado infers block
  RAM for the FIFOs; `m_lr8`, LUTRAM cost x8, gives 1657 FF / 0 LUTRAM / block RAM on mkpktmerge but +11.9 % LUT and
  +1408 FF on arty_ddr3, and `m_lr4` +6 % LUT on rv_soc: no single scale works, not adopted).
- LUT sites after packing are a separate gap: on rv_soc Vivado's P&R packs 115 LUT pairs (O5+O6) on its own netlist
  and 41 on ours (1041 vs 1122 sites). The `hl*` SOFT_HLUTNM hints were meant to test that; the one Vivado run
  (rv_soc_hl1) was killed and is not rerun yet (resume command below).

All recipes, LUT cells against base (`synth_area.py table --summary`, full table `build/qor/synarea/table_all.txt`):

| recipe | what | designs | mean | median | best | worst |
|---|---|---|---|---|---|---|
| syn2 | x1_cal_syn2 preset | 16 | -1.2 % | -1.3 % | -34.8 % (fir, 23 -> 15) | +29.0 % (aes) |
| c_unit | unit LUT cost | 16 | -4.3 % | -4.3 % | -12.2 % (axi_xbar) | +0.0 % |
| cu_fa | c_unit + `&if -F 3 -A 4 -C 16` | 16 | -5.9 % | -6.0 % | -12.8 % (aes) | -0.1 % |
| cu_rep | c_unit + second `&dch; &if; &mfs` round | 16 | -5.4 % | -4.9 % | -10.9 % (aes) | +0.0 % |
| cu_x1 | c_unit + abc9.xaiger=1 | 8 | -4.5 % | -4.5 % | -9.8 % | +2.2 % (rv_soc) |
| cu_dff | c_unit + `abc9 -dff` (changes FFs) | 7 | -6.0 % | -5.4 % | -9.9 % | -0.9 % |
| cu_syn2 | c_unit + the syn2 settings | 7 | -2.1 % | -4.4 % | -6.8 % | +11.2 % (aes) |
| cu_cal | c_unit + xaiger + flat 200 ps model | 8 | -2.5 % | -3.2 % | -6.8 % | +5.4 % (rv_soc) |
| cu_plain | c_unit, no `&dc2; &dch` | 10 | -5.4 % | -5.1 % | -15.7 % (aes) | +4.0 % (rv_soc) |
| a_plain | no `&dc2; &dch` | 10 | -0.7 % | -0.5 % | -11.8 % (aes) | +8.0 % (rv_soc) |
| c_l6 | LUT6 cost 5 -> 4 | 15 | -1.1 % | -1.0 % | -4.0 % | +0.3 % |
| a_fa | `&if -F 3 -A 4 -C 16` | 15 | -1.4 % | -1.0 % | -5.6 % | +0.1 % |
| a_area | `&if -a` | 15 | -0.3 % | -1.0 % | -8.7 % | +23.8 % |
| a_R10 | `&if -R 10` | 15 | -0.1 % | 0.0 % | -4.3 % | +9.5 % |
| a_mfse | `&mfs -e` | 15 | 0.0 % | 0.0 % | 0.0 % | 0.0 % |
| a_rep | second mapping round, default costs | 7 | +1.5 % | -0.2 % | -1.2 % | +12.9 % (bram) |
| a_synch2 | `&synch2` instead of `&dc2; &dch` | 6 | +0.6 % | +2.5 % | -12.0 % (aes) | +11.9 % (bram) |
| c_flat2 / c_l6b | other cost tables | 15 | +0.7 % / +1.3 % | | | |
| c_unit8 | all costs 1 (LUT7/8 too) | 6 | +8.4 % | | | +16.0 % |
| c_u6w | unit, LUT7 3, LUT8 6 | 7 | -2.8 % | -3.1 % | -4.2 % | -0.1 % |
| s_share | `share -aggressive` | 15 | +2.1 % | +0.4 % | -5.0 % | +23.3 % |
| s_cmw5 / s_cmw8 | short adders to LUTs | 7 | +0.6 % / -0.2 % | | | |
| hl1-3, cu_hl1-2 | LUT pair hints only | 16 | 0 (logic unchanged) | | | |

## mt_lut (mockturtle `lut_map`) against ABC on the same AIGs

`bash build/sa_mt1.sh` (log `build/qor/synarea/logs/mt1.log`): the abc9 input of rv_soc, sha256, aes as a plain
combinational AIG (`build/qor/synarea/mt/<d>.plain.aig`: boxes and flip-flops cut, so no carry-chain or arrival
timing), 6-LUTs, unit cost and unit delay on both sides. LUTs / depth:

| mapper | rv_soc | sha256 | aes |
|---|---|---|---|
| ABC `&if -K 6` | 1132 / 5 | 4241 / 5 | 3593 / 8 |
| ABC `&dc2; &dch -f -r; &if -K 6; &mfs` (the abc9 default flow) | 1034 / 4 | 4387 / 5 | 3995 / 8 |
| ABC the same with `&if -a` | 1014 / 9 | 4372 / 8 | 3886 / 13 |
| ABC `&syn2; &dc2; &dch; &if; &mfs` | 1022 / 4 | 4307 / 5 | 4418 / 8 |
| mt_lut delay mode (no AIG optimisation) | 1436 / 5 | 4499 / 5 | 4316 / 7 |
| mt_lut delay mode, best of fr / rw / resub / all | 1375 / 5 | 4499 / 5 | 4275 / 7 |
| mt_lut area mode (no AIG optimisation) | 1276 / 10 | 4183 / 7 | 3341 / 12 |
| mt_lut area mode, best of fr / rw / resub / all | 1242 / 9 | 4183 / 7 | 3316 / 11 |
| mt_lut delay mode, relax 20 %, 16 cuts | 1391 / 7 | 4381 / 7 | 4174 / 11 |

Runtime under 4 s for every run on both sides. At equal depth mockturtle needs more LUTs than ABC on all three
(+33 % rv_soc, +2.6 % sha256, +7 % aes against the default flow); its area mode wins LUTs only on aes (-14 % vs
`&if -a`) and sha256 (-4 %) and only by giving up depth (7 vs 5, 11-12 vs 8), and loses 22 % on rv_soc.
**Verdict: not adopted.** It would also need box (CARRY4, LUTRAM, DSP) and arrival-time support plus a path back into
yosys (abc9 reads the mapping back through its own XAIGER flow); nothing in the numbers pays for that work.
Side result: the plain `&if` beating `&dc2; &dch` on sha256 / aes led to the `a_plain` / `cu_plain` recipes above,
which do not hold up through the full abc9 flow (rv_soc +8.0 % / +4.0 %).

## Status
(updated below as the resumed session proceeds)
