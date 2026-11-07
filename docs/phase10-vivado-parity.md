# Phase 10: RESET_AFTER_RECONFIG, compressed partials, and pass-1 parity with Vivado

Offline work, 2026-11-05. Nothing has run on hardware. Every number below comes from a run, and the log or output path is
given next to it.

- Reference: Vivado v2025.2 (SW Build 6299465). Analysis: flow/bitparse.py, flow/partial_compare.py, flow/partial.py.
- Documents read for this phase:
  - UG470 v1.10 (local text, build/rv_flash/ref/ug470.txt): Table 5-25 (commands), Tables 5-26/5-27 (CTL0), the MASK, MFWR and CTL1 register entries, and Table 5-24 (FAR).
  - UG909, section "Apply Reset After Reconfiguration", from the AMD web page (2024.2 revision). This was the only UG909 text read.

## 1. Vivado references built

`vivado/write_variants.tcl`: new, run through `vivado/run_vivado.ps1 -Script write_variants.tcl`.
- It opens every existing `cfg_*_routed.dcp` of a design and sets the pblock's `RESET_AFTER_RECONFIG` and `BITSTREAM.GENERAL.COMPRESS`.
- It then writes the full and partial bitstreams into `build/vivado/<design>/{rar,cmp,rarcmp}/`.
- Logs: `build/vivado/<design>/vivado_variants.log`.

| check | dfx_ref | dfx_bram |
|---|---|---|
| Vivado message | `Partition "pblock_rm" has RESET_AFTER_RECONFIG = TRUE.` (6×) | same (6×) |
| DRC / warnings | 0 errors; `0 Warnings, 0 Critical Warnings and 0 Errors` for every write | same |
| full .bin with RAR vs without | byte-identical (3/3) | byte-identical (3/3) |
| compressed full .bit, expanded by bitparse (strict model) vs uncompressed full | 5408 frames, 0 differ (3/3) | 5408 frames, 0 differ (3/3) |

Log for the last two rows: `build/phase10/vivado_full_variants.log`.

Both pblocks span exactly one clock row, so no SNAPPING_MODE was needed and Vivado reported nothing about alignment.

**Limitation.** The property was set on the already-routed checkpoints at `write_bitstream` time; implementation was not re-run with it. The full bitstreams are byte-identical, so it did not change placement or routing here.

Partial sizes (.bin bytes; the counts in parentheses are dfx_ref configurations count/shift/grey and dfx_bram configurations lut/lutmul/grey):

| | default | RAR | compressed | RAR + compressed |
|---|---|---|---|---|
| dfx_ref | 59,272 | 112,700 | 34,432 / 35,112 / 34,736 | 41,004 / 41,684 / 41,308 |
| dfx_bram | 208,816 | 262,244 | 168,880 / 188,492 / 78,120 | 175,452 / 195,064 / 84,692 |

## 2. RESET_AFTER_RECONFIG (matrix item 11)

### 2.1 What changes in Vivado's partial (decoded, `flow/bitparse.py`; packet dumps compared word by word)

The pass-1 and pass-2 frames are identical to the RAR=false partial (73/73 per burst, dfx_ref, all three configurations). Everything else that differs is listed here.

| position | RAR=false | RAR=true |
|---|---|---|
| after IDCODE | `CMD NULL` | `CMD WCFG`, NOOP, `FAR 0x01000000` (block type 2 = CFG_CLB, top row 0, column 0), NOOP, `FDRI` type 1 (0 words) + type 2 (13,332 words = 132 frames) |
| then | – | `CRC`, `CMD SHUTDOWN`, NOOP, `CRC`, 4 NOOPs, `CMD NULL` |
| CTL0 steps, both passes | same | same |
| after pass 2 | `MASK 0x100`, `CTL0 0` | `CMD GRESTORE`, NOOP, `MASK 0x100`, `CTL0 0`, `CMD START`, NOOP |
| tail | `FAR 0x03BE0000`, CRC, DESYNC, 16 NOOPs | same |

There are three CRC checks instead of one, and all of them match bitparse's CRC.

### 2.2 The 132 CFG_CLB frames

**Layout.** There is one frame per CLB_IO_CLK configuration column per clock row, in FAR order (top r0, then top r1, then bottom r0), and each row is followed by 2 zero pad frames: 44+2 + 38+2 + 44+2 = 132. The column counts per row come from prjxray `part.json`.

**Content.** Each frame is all zero except word 50, which is either 0 or `0xE00009BC`. That value is bits 31:29 set plus a valid frame ECC (`0x9BC`; checked with `bitparse.frame_ecc`).

**Which frames are zero** (`build/phase10/rar_negative_controls.log` and t_mask runs):
- dfx_ref: top r1 c10, c11, i.e. exactly the region's two columns.
- dfx_bram: top r1 c6–c9, i.e. exactly the region's four columns, including the BRAM column c6 and the DSP column c9.
- Both designs: top r0 and bottom r0 c12–c17. These are columns that have no tiles in prjxray's tilegrid (the configuration-centre area).
- Every other column is `0xE0000000`+ECC. The content is identical across the three configurations of a design.

**Interpretation.**
- UG909 says that RAR "uses the SHUTDOWN sequence (masked to the reconfiguring region only)", and that "Each partial bitstream opens the mask for the target region, loads new configuration data", issues GSR, and that "the mask for the entire design begins as closed after the initial configuration".
- The data fit this reading: word-50 bits 31:29 = 1 is "closed", and 0 is "open", for the clock-row column.
- UG470 v1.10 does not describe the CFG_CLB block type beyond its name (Table 5-24). It also does not describe a GSR mask, so the bit meaning is inferred, not documented.

The command meanings below are from UG470 Table 5-25:
- `SHUTDOWN`: "Begin Shutdown Sequence … activates on the next successful CRC check or RCRC". This explains the CRC written right after it.
- `GRESTORE`: "Pulses the GRESTORE signal: sets/resets … IOB and CLB flip-flops".
- `START`: "Begins the Startup Sequence".

UG909 adds that the DONE pin goes low at the start of reconfiguration and high when it completes. It also says that STARTUP cannot be used for other purposes and that the XADC DRP is held in reset during reconfiguration. These are board and design constraints, and our flow does not check them.

The mask is not rewritten at the end of the partial. How it gets "closed" again (UG909's wording) is not visible in the bitstream; presumably this happens on START/EOS in hardware. Not verified.

### 2.3 Implementation: `partial.py --reset-after-reconfig` (default off, like Vivado)

**Stream.** The stream is exactly the sequence of 2.1. The mask is computed by `rar_mask()`:
- region columns (CLB_IO_CLK base address of a region tile) are zero;
- columns without tiles are zero;
- every other column gets `{50: 0xE0000000}`+ECC.

**Safety gates.** All of the following refuse the partial, and all earlier gates are unchanged.
1. **Before writing** (`rar_columns`): every tile whose CLB_IO_CLK frames lie in an opened column must be a region tile or an HCLK tile (no flip-flops). Otherwise the partial is refused and nothing is written.
   - This is UG909's "Pblocks must align vertically to clock regions … static logic is not permitted within these reconfigurable frames".
   - Controls: rv_c's region (`SLICE_X12Y75:SLICE_X15Y124`, half of two rows) has 200 static tiles in the opened columns and is refused. `SLICE_X12Y100:SLICE_X15Y124` has 100 and is refused. dfx_ref and dfx_bram have 0 and are accepted (`rar_negative_controls.log`).
2. **After writing** (`check_rar_stream`, on the parsed output):
   - the CFG_CLB frames written must be exactly the 126 computed ones, with identical content;
   - every region column must be open;
   - every other column with tiles must be closed (this follows from the equality with the computed mask);
   - the commands must appear in the order SHUTDOWN, GRESTORE, START, DESYNC;
   - no CFG_CLB write may come after SHUTDOWN.
   Any failure deletes the outputs.
3. **Without the option**: any CFG_CLB frame, or any SHUTDOWN, GRESTORE or START, is a refusal.
4. **Negative controls** (`build/phase10/rar_negative_controls.log`):
   - Vivado's dfx_ref RAR partial checked against the dfx_bram mask, and the reverse: refused (mask differs, region columns not open).
   - Vivado's default partial checked as RAR: refused.
   - Vivado's RAR partial checked as non-RAR: refused (126 CFG_CLB frames; SHUTDOWN/GRESTORE/START).
5. **Simulation**: CFG_CLB frames are excluded from base + partial == target and checked by gate 2 instead.
6. The `.check.json` gets `reset_after_reconfig` with `{mask_frames, closed_frames, zero_frames, region_columns, commands}`.

### 2.4 Verification against Vivado (Vivado's own full bitstreams as input)

Script: `flow/vivado_variant_compare.sh`. Log: `build/phase10/vivado_variant_compare.log`. Per-file outputs: `build/phase10/vivado_compare/<design>/`. The pass-1 options of section 4 were used.

| | words | words differing from Vivado's partial |
|---|---|---|
| dfx_ref count / shift / grey | 28,162 | 0 / 0 / 0 |
| dfx_bram lut / grey | 65,548 | 0 / 0 |
| dfx_bram lutmul | 65,548 | 4 (pass-1 DSP residue, section 4; not RAR) |

The mask burst is word-identical in all six. All partials pass CRC and base + partial == target, both with and without committing each burst's last frame.

Our own builds: see section 5.

## 3. Compression (matrix item 12)

### 3.1 What Vivado writes (decoded, dfx_ref and dfx_bram)

**Header.** CTL0 steps as before, then `MASK 0x1000`, `CTL1 0x1000`. At the end: `MASK 0x1000`, `CTL1 0` before the usual `MASK 0x100`, `CTL0 0`. UG470 v1.10 lists CTL1 as "reserved", so bit 12 is undocumented.

**Body.** Per pass, for each (block type, half, row) separately, frames are visited in address order.
- **Group.** A frame whose 101 words, ECC included, occur more than once in that pass and row is written once: `WCFG`, NOOP, `FAR`, NOOP, `FDRI` (101 words). Then `CMD MFW`, 12 NOOPs, `MFWR` with 8 zero words. Then, for each other member in address order, `FAR` and `MFWR` with 4 zero words. In BLOCK_RAM rows every MFWR is followed by 8 NOOPs (dfx_bram grey).
- **Run.** Consecutive frames that occur once and are not yet written are written as one FDRI, followed by one extra (flush) frame at the next address. If the next address starts a group that has not been written, the flush frame is that group's frame, and `MFW`/`MFWR` follow at once (the first MFWR lands on the current, auto-incremented address).
- FDRI headers are type 1 with the count up to 2047 words, and type 1 (0) + type 2 above that (BRAM runs of 129 frames).
- The mask of RAR+compress is grouped the same way, per clock row.
- In dfx_bram rm_lut the 128 BLOCK_RAM frames are all distinct, so they go out as one 129-frame run (no MFWR). In grey they are all zero, so they form one group.

**MFWR semantics.** UG470 says only "MFWR … used by the bitstream compression option" and "MFW: … write of a single frame data to multiple frame addresses". The model below is inferred and checked by expansion:
- the last frame pushed through FDRI stays in a frame buffer;
- MFWR writes that buffer to the current FAR;
- the first MFWR after an FDRI goes to the FDRI's own last address.

This model expands every Vivado compressed partial and full bitstream to exactly the uncompressed result (section 1 table; `t_parse` runs: 72/72 and 256/256 region frames equal).

**Flush frames.** The flush frame of a run is usually zero, and Vivado does not always write the next frame's data there.
- In dfx_bram grey, pass 1 run c8 m10..m11 is followed by a zero flush at c8 m12. c8 m12 was written earlier by MFW with non-zero data, and nothing rewrites it later in pass 1.
- Pass 2 has the same pattern at c8 m22.
- If the device committed the flush frame, Vivado's own partial would leave c8 m22 wrong, so Vivado relies on the last FDRI frame not being committed.
- This is consistent with the old question about the uncompressed pad frame (docs/phase2, phase9): its zero content is harmless if it is not committed. Not verified on hardware.
- bitparse now has `--strict` / `parse(strict=True)`: the last frame of each FDRI write stays uncommitted until the next frame or an MFWR. In the default (loose) model every frame is committed.

### 3.2 Implementation: `partial.py --compress` (default off)

**Behaviour.**
- The exact algorithm of 3.1 is used for the region frames of both passes and, with RAR, for the mask.
- `--compress-flush next` (the default) puts the next frame's own pass data into flush frames inside the region. That output is correct whether or not the device commits the flush frame.
- `--compress-flush zero` writes zeros as Vivado does. It is then correct only if the flush frame is not committed. `--simulate` requires the strict model, reports the loose model, and prints a WARNING when the two differ.
- Flush frames outside the region (when a run ends at the region's last frame) always carry the full bitstream's content. The region gate and pad check are unchanged.
- No frame outside the region was written by any compressed partial built here: `region check: 0 frame(s) outside region`.

**Simulation now always runs twice** (all modes): base + partial == target with every frame committed, and with each FDRI write's last frame left uncommitted. Both must pass, except the strict-only rule for `--compress-flush zero`.

### 3.3 Verification against Vivado (same script and log as 2.4)

| design / configuration | words | differ, flush zero | differ, flush next | sim (loose / strict) |
|---|---|---|---|---|
| dfx_ref compressed: count / shift / grey | 8,595 / 8,765 / 8,671 | 0 / 0 / 0 | 0 / 0 / 0 | pass / pass |
| dfx_ref RAR+compressed: count / shift / grey | 10,238 / 10,408 / 10,314 | 0 / 0 / 0 | 0 / 0 / 0 | pass / pass |
| dfx_bram compressed: lut / lutmul / grey | 42,207 / 47,110 / 19,517 | 0 / 4 / 0 | 3 / 6 / 10 | pass / pass, except flush zero grey: loose 1 frame differs, strict pass (same as Vivado's file) |
| dfx_bram RAR+compressed: lut / lutmul / grey | 43,850 / 48,753 / 21,160 | 0 / 4 / 0 | 3 / 6 / 10 | same |

- The 4 lutmul words are the pass-1 DSP residue (section 4).
- With flush next, the extra differences are exactly the flush frames at c8 m12 (2 words + CRC) and c8 m22 (7 words), plus the CRC.

### 3.4 byteman

byteman (upstream/FPGA-Research_byteman, build 2475287) names MFW and MFWR in its tables (`inlineCAP.h`), but its stream reader (`inlineInput.h`) handles FDRI and not MFWR. So frames written only through MFWR are not applied. Log: `build/phase10/byteman/summary.log`.
- Our compressed partials: 22 frames (dfx_ref) and 35 frames (dfx_bram) differ from the target after byteman.
- Vivado's own compressed partials: exactly the same 22 and 35 frames.
- Uncompressed RAR partials (ours and Vivado's): 0 frames differ. byteman ignores the CFG_CLB mask burst for the result.

So byteman cannot check compressed partials. The expansion check is bitparse plus `partial.py --simulate`.

## 4. Pass-1 parity (Vivado's hold-back rule)

**Evidence.**
- `vivado/dump_pips.tcl` (new) writes every pip of every net, for `static_routed.dcp` and each `cfg_*_routed.dcp`, together with the partition-pin locations (`build/vivado/<design>/pips/`).
- `flow/vivado_pips.py` (new) converts a dump to FASM pip features.
- The three INT pips that Vivado held back in dfx_ref pass 1 (`INT_L_X10Y106.ER1BEG2.SR1END1`, `INT_L_X10Y106.ER1BEG3.SR1END2`, `INT_R_X11Y101.SL1BEG2.ER1END2`) are common to all three configurations. They belong to the boundary nets (`rm_out[1]`, `rm_out[3]`, `count_reg[21]`) on the RM side of a partition pin; for example, the PPLOC of `din[1]` is `INT_L_X10Y101/ER1BEG2`.
- They are **not** in `static_routed.dcp`.
- The clock net's partition pin is `CLK_HROW_TOP_R_X60Y130/CLK_HROW_CK_BUFHCLK_L6`, so the HCLK leaf pips in the region columns (`HCLK_R_X32Y130 …BOT5`) are also absent from the static checkpoint.

**Rule (fits every configuration of both designs).** Pass 1 keeps exactly the pips of the static checkpoint (static routing up to the partition pins). It holds back every other pip:
- in the region's INT tiles;
- the DSP tie-offs (already done);
- the HCLK leaf pips (`HCLK_LEAF_CLK_B_*`, and `ENABLE_BUFFER` when no kept leaf uses that buffer) of the HCLK tiles that share the region's frames.

**Implementation.** Both are opt-in, so default outputs are unchanged.
- `--static-pip-list FILE`: static pips as FASM features. It is added to `--static-pips` if both are given.
- `--pass1-hold-hclk`: an HCLK pip is held back only if it is not a static pip. This keeps static clocks running wherever static uses the leaf.

Results on Vivado's full bitstreams (`build/phase10/vivado_compare/<d>/compare_p1sl*_*.json` and `vivado_variant_compare.log`, rows `base_zero_*`):

| | common-pips rule (phase 9) | static list only | static list + HCLK |
|---|---|---|---|
| dfx_ref count / shift / grey | 13 words + CRC each | 3 words + CRC (HCLK) | **0 / 0 / 0** |
| dfx_bram lut / grey | 23 words | 3 + CRC | **0 / 0** |
| dfx_bram lutmul | 29 words | 9 + CRC | **4** (c9 m27 words 1, 3, 50, and the CRC) |

**Residue.**
- In the lutmul DSP tile, Vivado's pass 1 lacks the config features `DSP_R_X9Y100.DSP48.DSP_0.AREG_1` and `BREG_1`. All its other DSP config features (MASK, the Z*REG and inversion features) are identical to the final state.
- This is a configuration bit, not a pip, and there is a single example, so no rule was inferred and nothing was implemented.

**Native flow.** For our own builds the existing `--static-pips` (nextpnr `-o prerouted`) is already the same ownership rule. `--pass1-hold-hclk` adds the HCLK part; results are in section 5.

## 5. Our own builds with the new options

Command: `python3 flow/regen_check.py --run --out build/phase10/native_<opt> --extra="<opt>" --match '^rm_(xor_from_andn|andn_from_xor|tbl_from_xorc|xorc_from_tbl)\.'`. Summary: `build/phase10/native_options.log`.

There are 7 partials per option set (rv_pr, rv_b, rv_c, rv_m native builds). Every partial that was built passed CRC and base + partial == target in both commit models, and its region gate passed.

| option | rv_pr | rv_b | rv_c (2 clock rows, half each) | rv_m (CLB+BRAM+DSP) |
|---|---|---|---|---|
| `--reset-after-reconfig` | 112,700 B | 112,700 B ×2 | **REFUSED ×2** (static CLBLM/INT tiles `CLBLM_L_X10Y125…` in the opened columns; nothing written) | 262,244 B ×2 |
| `--compress` | 58,732 B | 58,588 B ×2 | 118,352 B ×2 (default 118,320) | 202,028 / 103,476 B |
| both | 65,304 B | 64,664 B ×2 | REFUSED ×2 | 208,600 / 110,048 B |
| `--pass1-hold-hclk` | identical to default (sha256 = record) | identical | identical | identical |

- **Lengths.** The RAR partials have the same lengths as Vivado's RAR partials for the same regions:
  - rv_pr's region equals dfx_ref's;
  - rv_m's region equals dfx_bram's.
- **Packet layout and mask, rv_pr and rv_m** (`build/phase10/rar_layout_own_vs_vivado.log`):
  - Every packet header and every non-data payload is identical to Vivado's (61/61 and 73/73 packets).
  - The 126 mask frames are identical to Vivado's.
- **Compression.** It saves little on our builds, and in rv_c it is 32 bytes larger. The reason is that the openXC7 builds have few identical frames in the region.
- **rv_c.** This is the only compressed partial that spans two clock rows (per-row grouping). It simulates exactly, but there is no Vivado reference for it.
- **`--pass1-hold-hclk`.** It changes nothing on these builds: the HCLK leaf pips of the region columns are in the static nets' `static.prerouted`. A likely reason, not checked further, is that the static anchor cells inside the region are clocked.

## 6. Regression with the new options off

| check | result | log |
|---|---|---|
| native partials (rv_native, rv_b_native, rv_c_native, rv_m_native) regenerated, .bin sha256 vs `.check.json` | 42/42 identical, run twice: once mid-phase and once after the last code edit (`flow/regen_check.py --run`) | `build/phase10/regen_default.log`, `regen_default_final.log` |
| `DESIGNS="pr_uart rv_pr rv_b rv_c rv_flash" flow/make_partials.sh` | 24/24 OK, run twice. All 58 .bin hashes in `hash_before.txt` (taken before any change) reappear unchanged in `hash_after.txt`, and the final run reproduces all 24 external .bin files byte for byte (`hash_before_final.txt` = `hash_after_final.txt`) | `build/phase10/make_partials.log`, `make_partials_final.log`, `hash_*.txt` |
| `flow/byteman_check.sh` | 24/24 PASS, run twice | `build/phase10/byteman_check.log`, `byteman_check_final.log` |

- During this session, other processes added partials under `build/partials/rv_native` and `build/patched/partials/rv2`. Those files are not in `hash_before.txt` and are not compared.
- The `.check.json` records now also contain `frames_differ_last_frame_uncommitted`.

## 7. Files

- **Changed**:
  - `flow/partial.py`: options `--reset-after-reconfig`, `--compress`, `--compress-flush`, `--static-pip-list` and `--pass1-hold-hclk`; RAR gates; strict simulation.
  - `flow/bitparse.py`: CFG_CLB frame order, MFWR, `strict` model and `--strict`.
- **New**:
  - `vivado/write_variants.tcl`, `vivado/dump_pips.tcl`;
  - `flow/vivado_pips.py`, `flow/vivado_variant_compare.sh`, `flow/regen_check.py`;
  - this document.

## 8. Open

- Nothing on hardware. The following are inferred from Vivado's output, not tested:
  - the mask bit meaning;
  - the flush frame not being committed;
  - how the mask closes again.
- Multi-row regions: RAR still refuses them unless every row is fully covered (no static tiles in opened columns). The two-row layout of the mask and of compression is now checked against Vivado (section 9.4).
- The DSP AREG_1/BREG_1 pass-1 hold-back: rule found and implemented (section 9). Why Vivado does it is not known.
- CTL1 bit 12 (compression) and CTL0 0x100/0x400 meanings:
  - UG470 Table 5-27 names CTL0 bit 8 `GLUTMASK_B` and bit 10 `ConfigFallback`;
  - CTL1 is "reserved";
  - why the partials set them is not documented in what was read.
- byteman does not support MFWR.

## 9. Round 2: pass-1 configuration hold-back (DSP, carry) and a two-row reference

Offline work, 2026-11-05, same Vivado (v2025.2, SW Build 6299465). Every number comes from a run; logs are under `build/phase10/round2/` unless another path is given.

Documents read for this section, in addition to those listed at the top:
- UG479 v1.10 (7 Series DSP48E1 Slice User Guide, 2018-03-27), text extracted to `build/phase10/round2/ref/ug479_v1.10.txt`. Table 2-3 (Attribute Setting Description) and the A/B input-port text were read.

### 9.1 Vivado references built

| design | pblock | configurations | Vivado logs |
|---|---|---|---|
| `designs/dfx_dsp` | same as dfx_bram (`SLICE_X8Y100:SLICE_X11Y149`, RAMB18/36, `DSP48_X0Y40:DSP48_X0Y59`; one clock row) | `rm_dspa` (13 DSP48E1), `rm_dspb` (9 DSP48E1), `rm_nodsp` (LUT/carry, no DSP), `rm_carry` (adders, subtractor, add with carry-in, compare), grey | `build/vivado/dfx_dsp/vivado_build.log`, `vivado_build_carry.log`, `vivado_pips.log`, `vivado_sitepips.log`, `vivado_pr_verify_all.log` |
| `designs/dfx_2row` | `SLICE_X12Y50:SLICE_X15Y149` (two full clock rows, top r0 and r1, columns c10/c11) | dfx_ref's `rm_count`, `rm_shift`, plus `rm_big` (48×32 FF pipeline), grey | `build/vivado/dfx_2row/vivado_build.log`, `vivado_variants.log`, `vivado_pips.log` |

- The DSP RMs instantiate `DSP48E1` directly with every register attribute set explicitly. They are generated by `designs/dfx_dsp/gen_rms.py`; its CONFIG lists the settings.
  - rm_dspa covers AREG/BREG 0, 1 and 2, AREG=2 with ACASCREG 1 and 2, MREG only, PREG only, AREG≠BREG, the other registers (C, D, AD, INMODE, OPMODE, ALUMODE, CARRYIN, CARRYINSEL) at 1, all unisim defaults, CEA/CEB driven by logic, and a 2-DSP A/B/P cascade.
  - rm_dspb covers a 3-DSP cascade, AREG=2/BREG=1, AREG=1/BREG=2, AREG=0 with BREG/MREG/PREG=1, `USE_MULT=NONE`, and `IS_CLK_INVERTED=1`.
- `pr_verify`: all pairs are "compatible". For dfx_dsp, `vivado/pr_verify_all.tcl` (new) checks all five configurations (`build/vivado/dfx_dsp/pr_verify_all.rpt`). For dfx_2row, the check is in build_dfx.tcl's `pr_verify.rpt`.
- write_bitstream logs report 0 errors. The warnings are Vivado's "not ideal for floorplanning" notes (Netlist 29-43/29-101) and one Constraints 18-8777.
- dfx_2row: `region.py --drc` reports 0 split INT pairs (`region_drc_2row.log`). The variants (RAR, compress, RAR+compress) were written without SNAPPING_MODE (`GRID_RANGES=SLICE_X12Y50:SLICE_X15Y149` in the log). The full bitstreams with and without RAR are byte-identical (4/4).
- Tool for the analysis: `flow/dsp_pass1.py` (new). For every DSP tile of the region, it decodes pass 1 (first burst) and the final bitstream with prjxray's segbits and lists the features and named bits that differ.

### 9.2 What Vivado holds back in pass 1

**DSP48E1** (`build/phase10/round2/dsp/dsp_pass1_*.log`; per-cell table `dsp_rule_table.txt`, which joins Vivado's cell attributes from `vivado/query_sitepips.tcl` with the decoded tiles):

| cells | AREG_1 held back | BREG_1 held back |
|---|---|---|
| AREG=1 | 13/13 | |
| AREG=0 or 2 | 0/9 | |
| BREG=1 | | 13/13 |
| BREG=0 or 2 | | 0/9 |

- Plus dfx_bram rm_lutmul (AREG=BREG=1): both held back, as in section 4. That makes 23 DSP sites in 3 configurations.
- The rule is independent of the other settings in the cells: A_INPUT/B_INPUT CASCADE or DIRECT, CE tied or driven by logic, USE_MULT, IS_CLK_INVERTED, MREG/PREG, and the other registers.
- In prjxray terms, Vivado clears the one positive bit of `AREG_1` (DSP_0: 27_111, DSP_1: 27_271) and of `BREG_1` (27_38 / 27_198). `AREG_0` uses the same bit 27_111 and is not cleared.
- Nothing else in the DSP tiles differs between pass 1 and the final state: not AREG_0/2, BREG_0/2, ZMREG, ZPREG, ZAREG_2_ACASCREG_1, A_INPUT, the inverters, MASK or PATTERN. The only exceptions are the tie-off pips, which were already held back, and minors 24/25.
- Tiles without a used DSP (rm_nodsp, rm_carry, grey) have no difference.

**Carry chain (CARRY4)**:
- `PRECYINIT.CIN` (carry-in from the slice below) is held back on every RM slice that has it: rm_nodsp 3/3, rm_carry 14/14.
- `PRECYINIT.AX` (3) and `PRECYINIT.C1` (1) in rm_carry are not held back.
- Vivado's pip dump lists the RM carry nets as routed RM nets (`u_rm/..._n_0` through `CLBLM_L_COUT->CLBLM_L_COUT_N`, `build/vivado/dfx_dsp/pips/cfg_rm_nodsp_routed.pips.txt`).
- `PRECYINIT.CIN` is the configuration bit by which the next slice consumes that net. This fits the existing rule "pass 1 holds back RM routing", but that it is the reason is an interpretation.

**Why the DSP bits.** Not determined.
- UG479 Table 2-3 says for AREG: "When 1 is selected, the A2 register is used". The A/B input text says "Multiplexers controlled by configuration bits select flow through paths, optional registers, or cascaded inputs".
- So the held-back bit is plausibly one of those multiplexer selects, but UG479 does not map attributes to bits.
- Vivado's used site pips on these DSP sites are only the inverter pips (`CLKINV`, `OPMODE*INV`, `ALUMODE*INV`, `INMODE*INV`, `CARRYININV`; `build/vivado/dfx_dsp/sitepips/`). AREG/BREG do not appear as site pips, so the site-pip model does not explain the hold-back either.

**prjxray gap found on the way.** DSP_R_X9Y130 DSP_1 in rm_dspb (`USE_MULT=NONE`) has bit 26_277 set in the final bitstream and in Vivado's pass 1. prjxray-db names no feature for it.
- Our pass 1 is rebuilt from FASM, so it lacked the bit: 1 word plus ECC plus CRC differed.
- phase 9 already noted that `USE_MULT` has no prjxray feature; this bit is consistent with that, but it is not decoded.

### 9.3 Implementation: three opt-in options in `flow/partial.py`

All options are off by default, and default outputs are unchanged (9.5).

| option | effect |
|---|---|
| `--pass1-hold-dsp` | the region's `DSP_[LR]….DSP48.DSP_[01].[AB]REG_1` features are left out of pass 1 |
| `--pass1-hold-carry` | the region's `….SLICE[LM]_X[01].PRECYINIT.CIN` features are left out of pass 1 |
| `--pass1-keep-unknown` | region bits of the full bitstream that no `--fasm` feature explains (full bitstream AND NOT fasm2frames(--fasm)) are kept in pass 1 |

- All three need `--fasm`.
- The `.check.json` `pass1` record lists the held-back features and the unknown bits per frame.
- No gate was changed. Pass 2 still writes the final frames, and the region gate, the LUTRAM/SRL/BRAM refusals, the RAR gates and both simulation models run as before.

### 9.4 Comparison with Vivado (Vivado's full bitstreams as input)

Script: `flow/vivado_variant_compare.sh`.
- It now knows dfx_dsp and dfx_2row and takes `EXTRA=` for additional partial.py options.
- "new options" = `--pass1-hold-dsp --pass1-hold-carry --pass1-keep-unknown`, together with section 4's `--static-pip-list` and `--pass1-hold-hclk`.

| design / configurations | words | differ, without new options | differ, with new options | log |
|---|---|---|---|---|
| dfx_bram rm_lut / rm_lutmul / grey, uncompressed | 52,191 | 0 / 4 / 0 | **0 / 0 / 0** | `dsp_compare.log` |
| dfx_bram RAR, compressed and RAR+compressed (flush zero), 3 configurations each | 65,548 / 42,207–47,110 / 43,850–48,753 | lutmul 4 each (section 2.4, 3.3) | **0 in all 9** | `variants_all_options.log` |
| dfx_ref all variants, 18 partials | 8,595–28,162 | 0 | 0 | `variants_all_options.log` |
| dfx_dsp rm_dspa / rm_dspb / rm_nodsp / grey | 52,191 | 43 / 49 / 35 / 31 | **31 / 31 / 31 / 31** | `dsp_compare.log`, `dsp_compare_all.log` |
| dfx_dsp rm_carry | 52,191 | 48 | **31** | `carry_compare.log` |
| dfx_2row 4 configurations × base, RAR, compressed and RAR+compressed (flush zero and next) = 24 partials | 29,567 / 42,924 / 9,969–22,915 / 11,612–24,558 | **0 in all 24** | 0 in all 24 | `vivado_compare_noopt/`, `tworow_compare.log` |

- Every partial above passed CRC and base + partial == target in both commit models. The only exception is the known strict-only case: dfx_bram compressed grey with flush zero fails the loose model in 1 frame, and so does Vivado's own file (section 3.3).
- With flush next, dfx_bram still differs in the section 3.3 flush frames: 3 / 3 / 10 words. lutmul was 6 before; the 3 that are gone were the DSP residue.

**dfx_dsp residue (31 words, all five configurations): the run-end pad frame, not a pass-1 bit.**
- Each region burst ends with pad frame c10 m0, which lies outside the region.
- In this build, Vivado placed the static counter in CLBLM_L_X10 (c10), so the full bitstream has 15 non-zero words there: words 32–45 and the ECC word 50.
- Vivado writes the pad as zeros (as in dfx_bram_pad, phase 9). partial.py writes the full bitstream's own content, which is the existing pad-frame gate ("pad frames carry the full bitstream's own content").
- Total: 2 passes × 15 words + CRC = 31.
- This difference is deliberate: a zero pad would be correct only if the device does not commit the pad frame, which is untested. It was not changed. In dfx_ref, dfx_bram and dfx_2row the full bitstream's pad frames are zero, so they match.

**Two clock rows.** The phase-10 assumptions hold, word for word, on 24 partials. No partial.py change was needed.
- **RAR mask.** Vivado's mask opens T r0 c10/c11 and T r1 c10/c11, i.e. the region's columns in both rows, plus the tile-less columns as before. It closes 110 of 126 frames, the same frames partial.py computes (`rar_zero_rm_big.check.json`).
- **Compression.** Grouping per (block, half, row) is identical to Vivado's in both rows, for flush zero and for flush next.
- **Pass 1, HCLK.** HCLK leaf hold-back covers the HCLK tiles of both rows (`HCLK_[LR]_X31/32Y78` and `…Y130`).
- **Row coverage.** rm_big has flip-flops in both rows (1,556 FF feature lines in r0, 1,524 in r1, from its decoded FASM). So both rows carry RM logic, not only padding.
- **Sizes** (.bin bytes): default 118,320 (equal to rv_c's default partial, which has the same frame count); RAR 171,748; compressed 39,928 (grey) / 44,896 (count) / 42,808 (shift) / 91,712 (big); RAR+compressed 46,500 / 51,468 / 49,380 / 98,284.

### 9.5 Regression with the new options off

| check | result | log |
|---|---|---|
| `DESIGNS="pr_uart rv_pr rv_b rv_c rv_flash" flow/make_partials.sh` | 24/24 OK. All 24 .bin sha256 identical before and after (`hash_before.txt` = `hash_after.txt`; `hash_before.txt` also equals phase 10's `hash_after_final.txt`) | `make_partials.log`, `hash_result.txt` |
| `flow/regen_check.py --run` (native partials, sha256 vs `.check.json`) | 48/48 identical. These are the 42 of section 6 plus 6 `rv_native` records added since by other runs | `regen_default.log` |
| `flow/byteman_check.sh` | 24/24 PASS | `byteman_check.log` |

**Native builds with the new options on** (`native_newopts.log`; `regen_check.py --extra=` with the three options, 48 partials):
- All 48 were written and passed every gate, CRC, and base + partial == target in both commit models.
- 24 are unchanged. 24 differ only by held-back `PRECYINIT.CIN` features (93 in total; the RMs' adders).
- No DSP feature was held back (the rv_m DSPs have AREG=BREG=0). No unknown bits were found (0 in every partial; expected, since these bitstreams are made from their FASM).

### 9.6 Files

- **Changed:**
  - `flow/partial.py`: `--pass1-hold-dsp`, `--pass1-hold-carry`, `--pass1-keep-unknown`; the helpers `held_feature`, `fasm_frames` and `unknown_bits`.
  - `flow/vivado_variant_compare.sh`: dfx_dsp, dfx_2row, `EXTRA`.
- **New:**
  - `flow/dsp_pass1.py`, `vivado/query_sitepips.tcl`, `vivado/pr_verify_all.tcl`;
  - `designs/dfx_dsp/` (with `gen_rms.py`), `designs/dfx_2row/`.

### 9.7 Open

- Why Vivado holds back AREG_1/BREG_1 (and not AREG_0/2) is unknown. The rule is empirical: 23 DSP sites in 3 configurations, one device, one Vivado version.
- The CIN rule rests on 17 slices in 2 configurations of one region. Carry chains that cross a clock row inside a region were not tested.
- Bit 26_277 (DSP_1, seen with `USE_MULT=NONE`) is not in prjxray-db; `--pass1-keep-unknown` copies it, but it is not decoded.
- Pad frames outside the region: Vivado writes zeros, partial.py writes the static content (residue of 31 words in dfx_dsp). Whether the device commits the pad frame is still untested.
- Still nothing on hardware.
