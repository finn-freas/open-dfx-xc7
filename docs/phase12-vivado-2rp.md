# Phase 12: Vivado two-RP reference, and RPs that share frames

Offline work, 2026-11-05. Nothing has run on hardware. Every number below comes from a run; the log or output path is
given next to it. Matrix item 14 in `docs/dfx-vs-vivado.md`.

- Reference: Vivado v2025.2 (SW Build 6299465), xc7a35tcsg324-1. One Vivado job at a time.
- Analysis: flow/bitparse.py, flow/partial.py, flow/partial_compare.py, the new flow/vivado_2rp_compare.py.
- Vivado outputs are copied from `C:\Users\finnf\open-dfx-xc7-vivado\build\<design>` to `build/vivado/<design>/`.

## 1. Vivado two-RP reference `designs/dfx_2rp`

### 1.1 Design

- `top.v`: a 28-bit counter. `u_rp1` (module `rm_rp1`) gets `count[27:20]` and drives `led[3:0]`. `u_rp2` (module
  `rm_rp2`) gets `count[19:12]` and drives `rgb[3:0]` (Arty LD0 R/G/B, LD1 R). Both outputs are registered in static.
- RMs, each `clk, din[7:0] -> dout[3:0]` registered:
  - RP1: `rp1_count.v` (`din[7:4]`), `rp1_shift.v` (`1 << din[7:6]`), and greybox.
  - RP2: `rp2_count.v` (`din[7:4] ^ din[3:0]`), `rp2_shift.v` (`8 >> din[7:6]`), and greybox.
- `pblock.xdc`: `pblock_rp1` = `SLICE_X12Y100:SLICE_X15Y149` and `pblock_rp2` = `SLICE_X12Y0:SLICE_X15Y49`, the
  rv_soc2 regions of phase 11. `SNAPPING_MODE OFF`, `RESET_AFTER_RECONFIG false`.

### 1.2 Build (`vivado/build_dfx2.tcl`, new)

Run: `vivado/run_vivado.ps1 -Design dfx_2rp -Top top -Script build_dfx2.tcl -Run`. Log: `build/vivado/dfx_2rp/vivado_build.log`.

1. Static synthesis with both RPs as black boxes; each RM synthesised out of context.
2. `cfg_count_count`: both RMs read in, `HD.RECONFIGURABLE` on both cells, opt/place/route.
3. Three locked checkpoints from it (`update_design -black_box`, then `lock_design -level routing`):
   `static_routed.dcp` (both RPs empty), `keep_rp2_count.dcp` (RP1 empty, static and RP2 locked), `keep_rp1_count.dcp`.
4. `cfg_shift_count` from `keep_rp2_count` and `cfg_count_shift` from `keep_rp1_count`. Each also writes its new RM
   as a routed cell checkpoint (`write_checkpoint -cell`).
5. `cfg_shift_shift`: `static_routed.dcp` plus both routed cell checkpoints (`read_checkpoint -cell`), then
   place/route. A first attempt that black-boxed `u_rp2` in the locked `cfg_shift_count` failed with
   `ERROR: [Constraints 18-11729] Failed to unroute clock net because the routing node CLBLM_L_X10Y45/CLBLM_L_CLK is locked`
   (`build/vivado/dfx_2rp/vivado_build_try2.log`; try 1 stopped at `report_utilization -pblocks` with two pblocks,
   `vivado_build_try1.log`).
6. Greyboxes (`update_design -buffer_ports`): `cfg_grey_grey` from `static_routed`, `cfg_grey_count` from
   `keep_rp2_count`, `cfg_count_grey` from `keep_rp1_count`.
7. `pr_verify` over all 7 configurations, then `write_bitstream` for each. Vivado writes one partial per pblock per
   configuration: `cfg_<rp1>_<rp2>_pblock_rp{1,2}_partial.bit`.

Results:
- DRC: `DFX DRC finished with 0 Errors` (4×), every command `0 Critical Warnings and 0 Errors`. Boundary pins: 13 on
  `u_rp1`, 13 on `u_rp2` (Constraints 18-13253).
- `pr_verify` (`build/vivado/dfx_2rp/pr_verify_all.rpt`): **6/6 pairs compatible** (`cfg_count_count` against each
  other configuration). Each pair: 2 reconfigurable modules, 26 partition pins, 408 static tiles, 23 sites, 54 cells,
  655 routed nodes, 595 routed pips compared. As in dfx_2row, the initial checkpoint gets `HDPRVerify-43 ... has unlocked
  static portion`.
- All 7 full bitstreams and 14 partials written. Partial size: 59,272 bytes `.bin` for both RPs, the same as dfx_ref's.

### 1.3 Full bitstreams: only the changed RP differs

`build/phase12/full_pairs.py` (ECC masked, words attributed to rp1 tiles, rp2 tiles or other), log
`build/phase12/full_pairs_dfx_2rp.log`: 21/21 pairs.
- In every pair, **0 words differ outside the two RPs' tiles**.
- If an RP has the same RM in both configurations, 0 of its words differ. This includes `cfg_shift_shift`, built from
  the two routed cell checkpoints: it is identical to `cfg_shift_count` in RP1 and to `cfg_count_shift` in RP2.
- RP1 count↔shift: 171 words (61 frames); RP2 count↔shift: 167 words (49 frames).

### 1.4 Variants (`vivado/write_variants.tcl`, adapted)

- `write_variants.tcl` now sets `RESET_AFTER_RECONFIG` on every pblock of `CONFIG_PBLOCKS {pblock_rm pblock_rp1 pblock_rp2}`
  that exists in the checkpoint. A `write_bitstream` error is logged as `WRITE_BITSTREAM_ERROR` instead of stopping.
  For single-RP designs only `pblock_rm` exists, so the behaviour is as before.
- `vivado/dump_pips.tcl`: owners `u_rm` (`rm`, as before), `u_rp1`, `u_rp2`, and pplocs for each.
- Log: `build/vivado/dfx_2rp/vivado_variants.log`. 42 partials (7 configurations × rar/cmp/rarcmp × 2 RPs), 21/21
  writes `0 Critical Warnings and 0 Errors`, `Partition "pblock_rp1" has RESET_AFTER_RECONFIG = TRUE` 14× and the
  same for `pblock_rp2`.

Sizes (.bin bytes, the same for every configuration unless a range is shown):

| | default | RAR | compressed | RAR + compressed |
|---|---|---|---|---|
| RP1 | 59,272 | 112,700 | 34,632 – 36,128 | 41,204 – 42,700 |
| RP2 | 59,272 | 112,700 | 37,848 – 41,184 | 43,924 – 47,260 |

### 1.5 Does an RP1 partial touch RP2's frames or static frames? (Vivado's own partials)

Frames written by each Vivado partial, classified against `region.region_bits` of both RPs
(`flow/vivado_2rp_compare.py`, `vivado frames` column of `build/phase12/compare_dfx_2rp.log`):

| partials | frames | own RP | other RP | static |
|---|---|---|---|---|
| default and RAR, RP1 (14) | 73 | 72 | **0** | 1: `0x00020600` (T r1 c12 m0), the run-end pad |
| default and RAR, RP2 (14) | 73 | 72 | **0** | 1: `0x00400600` (B r0 c12 m0), the run-end pad |
| compressed and RAR+compressed, both RPs (28) | 72 | 72 | **0** | 0 |

- So no Vivado partial writes a frame of the other RP, and the only static frame is the pad after the run.
- **RAR mask.** The RP1 RAR partial opens T r1 c10/c11 (plus the tile-less columns c12–c17 of T r0 and B r0) and keeps
  RP2's columns B r0 c10/c11 closed; RP2's does the reverse. 112 of 126 mask frames are closed in both
  (`rar_cfg_count_count_rp{1,2}.check.json`). So the GSR of an RP1 load is masked away from RP2.
- **The pad frame holds static configuration here.** Vivado placed static flip-flops in `CLBLL_L_X12Y100`; the full
  bitstream has words 0, 1 (and ECC word 50) non-zero in T r1 c12 m0. Vivado writes the pad as zeros. Simulated on its
  own base, each Vivado default/RAR RP1 partial gives `loose 1 frames differ ['0x00020600 ...']; strict 0`
  (`build/phase12/vivado_partials_simulated.log`). So Vivado's RP1 partial is correct only if the device does not commit
  the last frame of the FDRI write. The rv_soc2 RP1 pad (phase 11) is the same frame address.

## 2. partial.py on Vivado's full bitstreams vs Vivado's partials

Command (per configuration, per RP, per variant), in `flow/vivado_2rp_compare.py`:
`partial.py build/vivado/dfx_2rp/cfg_<c>.bit OUT --design top --region <RP> --fasm cfg_<c>.fasm --static-pip-list static_pips.fasm --pass1-hold-hclk --pass1-hold-dsp --pass1-hold-carry --pass1-keep-unknown --compress-flush zero [--reset-after-reconfig] [--compress] --base <cfg differing only in this RP> --simulate`.
FASM is from `flow/bit2fasm.py` of Vivado's full bitstream; static pips are from Vivado's `static_routed.dcp`
(`flow/vivado_pips.py`). These are phase 10's parity options. partial.py was not changed for this comparison.

Logs: `build/phase12/compare_dfx_2rp.log` (flush zero), `build/phase12/compare_dfx_2rp_flushnext.log`; per-partial
outputs and `compare_*.json` in `build/phase12/compare/dfx_2rp/`; `summary.json`, `summary_next.json`.

| variant | RP1 (7 configurations) | RP2 (7 configurations) |
|---|---|---|
| default (14,805 words) | 7 words each: pad frame only | **0 / 7** |
| RAR (28,162 words) | 7 words each: pad frame only | **0 / 7** |
| compressed, flush zero (8,645 – 10,283 words) | **0 / 7** | **0 / 7** |
| RAR + compressed, flush zero (10,288 – 11,802 words) | **0 / 7** | **0 / 7** |

- **Word-identical: 42 of 56.** The 14 others differ only in the run-end pad frame `0x00020600`, words 0, 1 and 50 in
  both passes, plus the CRC word (2 × 3 + 1 = 7). Vivado writes zeros there, partial.py writes the full bitstream's
  content (static FFs, 1.5). This is phase 10 §9.4's deliberate difference (dfx_dsp, 31 words); it was not changed.
  RP2's pad (B r0 c12 m0) is zero in the full bitstream, so RP2 matches.
- Packet structure, pass-1 contents (held-back pips: 36–50 for RP1, 41–49 for RP2; 0 DSP or carry features held), RAR
  mask and compression grouping are all identical to Vivado's.
- **Simulation** (base = Vivado's configuration that differs only in this RP): CRC OK in 56/56, and base + partial ==
  target in the strict model in 56/56. In the loose model the RP1 compressed partials with flush zero fail in 1–2 frames
  (`c10 m12`, `c11 m1`, or `c10 m25`), and so do Vivado's own files, in exactly the same frames
  (`vivado_partials_simulated.log`). With `--compress-flush next` all 28 compressed partials pass both models; they then
  differ from Vivado's in the flush frames only (RP1 0–8 words, RP2 103 words).
- Frames written by our partials: own RP 72 (+1 pad uncompressed), other RP 0, the same classification as Vivado's.

## 3. Two RPs that share frames

### 3.1 Stacked in one clock row: `designs/dfx_2rp_shared` (refused by Vivado)

Same sources as dfx_2rp; `pblock_rp1` = `SLICE_X12Y100:SLICE_X15Y124`, `pblock_rp2` = `SLICE_X12Y125:SLICE_X15Y149`.
By prjxray: 100 tiles each, 0 common tiles, **72 common frames** (all of each region's frames: T r1 c10/c11 m0..35),
0 common words; `region.py --drc` 0 split INT pairs for each (`build/phase12/region_overlap.log`).

Vivado (`build/vivado/dfx_2rp_shared/vivado_build.log`, `cfg_count_count_pre_place_drc.rpt`): `report_drc` before
placement and the DRC that precedes `opt_design` both report

```
ERROR: [DRC HDPR-25] Reconfigurable Pblocks must not overlap same frame: Reconfigurable Pblocks cannot share a column within a Clock Region.  Reconfigurable cell 'u_rp2' in Pblock 'pblock_rp2' and reconfigurable cell 'u_rp1' in Pblock 'pblock_rp1' violate this rule.  The following are 10 of the tiles that are causing overlaps:
 CLBLM_L_X10Y149
 INT_L_X10Y149
 ...
ERROR: [Vivado_Tcl 4-78] Error(s) found during DRC. Opt_design not run.
```

So Vivado does not accept it: no implementation, no pr_verify, no bitstream. The question of how Vivado would write an
RP1 partial in shared frames therefore has no Vivado answer.

**Vivado's frame-tile lists** (`hd_visual/pblock_rp{1,2}_FrameTiles.tcl`; `build/phase12/frametiles_vs_region.log`):
- In the shared layout, both RPs' FrameTiles are the same 204 tiles: the 200 tiles of both halves, prjxray's 2 HCLK
  tiles, and `HCLK_CLB_X30Y130`, `HCLK_CLB_X33Y130`, which have no entry in prjxray's tilegrid under that name.
- In dfx_2rp each RP's FrameTiles are its 200 tiles plus the same kind of 4 HCLK tiles. Our region tiles plus
  `shared_frame_tiles` cover every tile Vivado lists, except those two Vivado-only HCLK_CLB names.

### 3.2 Forced: HDPR-25 lowered to a warning (`designs/dfx_2rp_forced`, experiment only)

`hook.tcl`: `set_property SEVERITY {Warning} [get_drc_checks HDPR-25]`, sourced after every `open_checkpoint`
(new `hook` in build_dfx2.tcl; no effect without a `hook.tcl`). Log: `build/vivado/dfx_2rp_forced/vivado_build.log`.
- `CRITICAL WARNING: [Vivado 12-4430] You are lowering the severity from an ERROR. This can potentially lead to board damage or other functionality issues on hardware.`
- `opt_design` then ran, but `place_design` failed: `WARNING: [Place 30-769] High register utilization is forcing place_design to place up to 8 registers per slice in pblock PBLOCK: pblock_rp1`,
  `ERROR: [Place 30-433] Unplaced instances found` (`u_rp1/dout_reg[0..3]`), `ERROR: [Place 30-99] Placer failed with error: 'failed to commit all instances'`.
- Why the placer found no site for 4 flip-flops in a 100-slice pblock was not investigated. No further forcing was tried.

### 3.3 Side by side in one INT pair: `designs/dfx_2rp_side` (refused)

`pblock_rp1` = `SLICE_X12Y100:SLICE_X13Y149` (CLBLM_L_X10, column c10), `pblock_rp2` = `SLICE_X14Y100:SLICE_X15Y149`
(CLBLM_R_X11, c11). Their frames are disjoint (different columns), but the edge between them splits the
`INT_L_X10`/`INT_R_X11` pair. `region.py --drc`: 50 split pairs for each (`build/phase12/region_drc_side.log`).
Vivado (`build/vivado/dfx_2rp_side/vivado_build.log`):
- `CRITICAL WARNING: [Constraints 18-993] The Pblock pblock_rp1 has defined an area that causes the splitting of interconnect tile columns. ... placement will be prohibited from both of these columns.`
- `CRITICAL WARNING: [Constraints 18-998] The split between the left and right columns occurs between two reconfigurable Pblocks. ... The other Pblock is pblock_rp2 to the right.`
- `Constraints 18-994/18-995/18-992`: 50 SLICEL + 50 SLICEM sites excluded from each pblock, i.e. all of them; then
  `Place 30-640` (no compatible site), `ERROR: [Place 30-642] Placement Validity Check : Failed to find legal placement.`,
  `ERROR: [Place 30-99]`.

Side by side "in the same columns" is not possible in 7-series: a frame covers a whole column of a clock row, so two
pblocks in the same column of one row are always the stacked case of 3.1.

### 3.4 What partial.py did, and what was changed

partial.py has one region. Before this phase it did not know about other RPs. The refusal of shared frames was in
`build_pr_native.py` (`check_partitions`), not in partial.py. Given the stacked RP1 region, partial.py counts RP2's 100
tiles among the 102 "static tiles that share frames", writes all 72 frames with the full bitstream's content (RP2's
current bits included), and passes its gates (`build/phase12/gate/gate_tests.log`, case 3). That partial is only
correct while RP2 holds the same module as in the full bitstream, and nothing recorded that.

To match Vivado, which refuses, partial.py gets an opt-in gate (default off; outputs without it unchanged, section 4):

- `--other-region SPEC` (repeatable): the region of another RP of the same design.
- Refused, with nothing written, if this region shares a configuration frame with that RP or if the partial would write
  any of its frames (region frames or run-end pad frames). The message cites HDPR-25.
- `.check.json` field `other_regions`: `{SPEC: {"common_frames": n, "frames_written": n}}`.

Tests (`build/phase12/gate/gate_tests.log`, on Vivado's `cfg_shift_count.bit`, parity options):

| case | result |
|---|---|
| 1. dfx_2rp RP1 with `--other-region` RP2 | written; `other_regions: {'SLICE_X12Y0:SLICE_X15Y49': {'common_frames': 0, 'frames_written': 0}}`; `.bin` identical (`cmp`) to the run without the option; CRC OK, simulated exact |
| 2. stacked RP1 with `--other-region` stacked RP2 | **REFUSED**: 72 common frames, 72 written; no output files |
| 3. stacked RP1 without the option | written as before (old behaviour) |
| 4. side by side, RP1 `X12–13` with `--other-region` `X14–15` | **REFUSED**: 0 common frames, but 1 frame written: RP1's run-end pad (c11 m0) is RP2's first frame |

Case 4 is a real hazard that the frame-overlap test alone would miss: with disjoint frames in adjacent columns, an
uncompressed partial's pad frame lands in the neighbouring RP. Vivado refuses that layout for the INT-pair reason anyway.

**What supporting shared frames would need** (not implemented, since Vivado has no such mode to match):
- Each RP1 partial would have to be written per (RP1 module, RP2 module) pair, because the shared frames carry RP2's
  bits. That is n1 × n2 partials instead of n1 + n2.
- A load-time check that the device's RP2 holds exactly the RP2 module the partial was cut with (e.g. a hash of RP2's
  words in the shared frames in the `.check.json`, checked by the loader), and a simulation gate that RP2's words in the
  written frames are equal in base and target.
- Pass-1 rules for the other RP's bits inside the shared frames (keep them at their current values in pass 1).
- RAR could not be used: the GSR mask opens whole clock-row columns, which would reset RP2 (partial.py already refuses
  RAR when opened columns contain non-region tiles).

## 4. Regression with the new option off

All in `build/phase12/regress/`.

| check | result | log |
|---|---|---|
| `DESIGNS="pr_uart rv_pr rv_b rv_c rv_flash" flow/make_partials.sh` with the unchanged partial.py (sha256 `5f98a022…`) | 24/24 OK | `make_partials_before.log`, `hash_before.txt` |
| the same with the changed partial.py (sha256 `90956e06…`) | 24/24 OK; **all 24 .bin sha256 identical** (`diff hash_before.txt hash_after.txt` empty) | `make_partials_after.log`, `hash_after.txt`, `hash_result.txt` |
| `flow/regen_check.py --run` (native partials, sha256 vs `.check.json`) | **48 identical, 0 differ, 0 failed** | `regen_default.log` |

- The `build/partials` files found at the start of this phase (written 21:09–21:10, not by this work) already differed
  from phase 10 round 2 (`build/phase10/round2/hash_after.txt`) in 10 of the 24 hashes (rv_pr andn ×3, rv_b add,
  rv_flash ×6). The cause was not investigated; presumably the inputs were rebuilt in between. The baseline is therefore a fresh make_partials run with the unchanged partial.py, taken before the edit.
- The unchanged copy is `build/phase12/regress/partial.py.before`.
- A first regression run was stopped part-way to reword the refusal message, and then rerun in full. The table is from
  the full rerun.

## 5. Files

| file | |
|---|---|
| `designs/dfx_2rp/` | new: top.v, rm_stub.v, rp1_{count,shift}.v, rp2_{count,shift}.v, arty_a7_35t.xdc, pblock.xdc |
| `designs/dfx_2rp_shared/`, `designs/dfx_2rp_side/`, `designs/dfx_2rp_forced/` | new: same sources, other pblocks; `dfx_2rp_forced/hook.tcl` |
| `vivado/build_dfx2.tcl` | new: two-RP DFX build (locked checkpoints per RP, routed cell reuse, greyboxes, pr_verify, bitstreams); optional `hook.tcl` |
| `vivado/write_variants.tcl` | RAR set on every pblock in `CONFIG_PBLOCKS`; write errors logged |
| `vivado/dump_pips.tcl` | owners and pplocs for `u_rm`, `u_rp1`, `u_rp2` |
| `flow/vivado_2rp_compare.py` | new: per-RP partials on Vivado's full bitstreams, comparison, frame classification of Vivado's partials |
| `flow/partial.py` | `--other-region`, `other_region_check`, `.check.json` `other_regions` |
| `build/phase12/` | logs: compare, full pairs, simulations, region overlap, frame tiles, gate tests, regress |

## 6. Open

- Nothing on hardware. Whether the device commits the run-end pad frame is still untested. dfx_2rp is the second
  Vivado reference where the pad holds static configuration and Vivado zeroes it (after dfx_dsp).
- Shared frames between RPs: Vivado 2025.2 refuses them (HDPR-25), so there is no reference for how such a partial
  would look. partial.py now refuses them with `--other-region`; without the option it still writes them silently, and
  `build_pr_native.py` refuses such layouts.
- `--other-region` must be passed by the caller; `flow/native_check_multi.sh` (phase 11) does not pass it yet.
- The forced run's placement failure (3.2) was not analysed.
- One device, one Vivado version, small RMs (4 FFs + a few LUTs per RM).
