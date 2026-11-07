# Phase 9: native flow for other regions, and regions with BRAM and DSP columns

Offline work, 2026-11-05. Nothing has run on hardware. Every number below comes from a run; the log or output path is
given next to it. "Verified" means checked by a run here; "not verified" is said explicitly.

Tools: patched nextpnr `router` (`e62fafd1`, `docs/drafts/nextpnr-router-region.md`) and the new `replay` variant
(`e62fafd1-replay`, `docs/drafts/nextpnr-pblock-replay.md`); yosys 0.70+186; prjxray-db a8b09269; Vivado v2025.2
(SW Build 6299465) as the reference only.

## 1. What changed in the flow

| file | change |
|---|---|
| `flow/build_pr_native.py` | `designs` dict in CONFIG (`rv_pr` default, `rv_b`, `rv_c`, `rv_m`), `--design`; the shell is generated per region (`gen_shell2.py --no-keepout`, blockers stripped); `shared_frame_pblock`; variant `replay`; `--no-shared-frame-pblock` (negative control). `rv_pr` outputs and XDC text are unchanged (cached steps all skip). |
| `flow/region.py` | region spec is now a comma-separated list of site ranges: `SLICE_..:SLICE_..,RAMB36_..:RAMB36_..,DSP48_..:DSP48_..` (also `RAMB18`). BRAM/DSP tiles take the interface tiles and the INT tile on each of their 5 rows. `pblock_ranges()` adds the RAMB18 range of a RAMB36 range. For the three SLICE-only regions `region_tiles`, `region_bits` and `shared_frame_tiles` are identical to the old code (compared by script, all `True`). |
| `flow/gen_shell2.py` | spec key `core_clk` passes `clk` to `rm_core`; default output still byte-identical to `designs/rv_soc/pr/rm_shell.v` (`cmp`). |
| `flow/partial.py` | see section 4: pass-1 all-ones on every CLB_IO_CLK column of the region with minors 24/25 (BRAM and DSP columns too); BLOCK_RAM frames in pass 1 are the full bitstream's frames; DSP tile tie-off pips held back in pass 1; **new refusal**: any frame the partial writes (region or pad) that holds LUTRAM/SRL/BRAM state of a static tile; the shared-frame refusal also covers used static BRAMs. rv_pr/rv_b/rv_c partials are byte-identical to before (section 2.4). |
| `flow/pr_check.py` | opt-in `--hclk-full-column` (default unchanged, strict). |
| `flow/region2v.py` | models RAMB36E1 (`BRAM_L/R`) and DSP48E1 (`DSP_L/R`) tiles, interface tiles, clocked RM cores, `--sweep N`, and a `bram` subcommand; section 5. |
| `flow/native_check.sh` | `TAGP`, `BRAM_RMS`, `R2V_ARGS`, `FORMAL_MEM_KB`, `FORMAL_SKIP_RMS`; formal runs under `ulimit -v`. |
| new | `flow/partial_passes.py`, `flow/partial_compare.py`, `flow/pass1_fasm.py`, `flow/vivado_bram_compare.sh`, `flow/r2v_controls.sh`, `designs/rv_soc/tb/r2v_ramb36e1.v`, `designs/rv_soc/pr/{ports_clk.json,rm_core_tbl.v,rm_core_tbl2.v,rm_core_xorc.v}`, `designs/dfx_bram/`, `designs/dfx_bram_pad/`, `docs/drafts/nextpnr-pblock-replay.{md,patch}` |
| Vivado scripts | `vivado/build_dfx.tcl` takes an optional RM list (argv 5.., comma or space separated; `vivado.bat` splits commas); `vivado/run_vivado.ps1 -Rms`. Defaults unchanged. |

## 2. Task A: native flow on rv_b and rv_c (verified)

Commands:

```bash
python3 flow/build_pr_native.py --design rv_b --run      # build/patched/rv_b_native.out
python3 flow/build_pr_native.py --design rv_c --run      # build/patched/rv_c_native.out
NAT=build/patched/rv_b_native/router OUT=build/patched/partials/rv_b_native BMO=build/patched/byteman_check/rv_b_native \
  REGION=SLICE_X12Y0:SLICE_X15Y49 TAGP=native_rv_b bash flow/native_check.sh      # build/patched/native_check_rv_b.log
NAT=build/patched/rv_c_native/router OUT=build/patched/partials/rv_c_native BMO=build/patched/byteman_check/rv_c_native \
  REGION=SLICE_X12Y75:SLICE_X15Y124 TAGP=native_rv_c bash flow/native_check.sh    # build/patched/native_check_rv_c.log
```

### 2.1 Builds (RMs xor, andn, add; `router` variant, keep-out on)

| design | region | static pips in region tiles | RM pips outside | pr_check (3 pairs) | router2 first build | Fmax |
|---|---|---|---|---|---|---|
| rv_b | SLICE_X12Y0:SLICE_X15Y49 | 0 in all 4 builds | 0 / 0 nets | identical; 68, 72, 72 frames differ, all inside | 33.61 s | 157.48 MHz |
| rv_c | SLICE_X12Y75:SLICE_X15Y124 | 0 in all 4 builds | 0 / 0 nets | identical; 132, 138, 139 frames differ, all inside | 60.39 s | 155.88 MHz |

Sources: `build/patched/<d>_native/router/checks/{pips_*.json,pr_check_*.log}`, `*/nextpnr.log`. Replay builds route in
1.85–2.56 s. Fmax is the same in every build of a design (static from the first build; single seed).

### 2.2 Shared frames in rv_c: second pblock

rv_c covers half of two clock rows, so 204 static tiles share its 144 frames (`region.shared_frame_tiles`), 100 of them
CLBLM. Instead of keep-out LUTs the native flow adds an empty exclusive pblock over the **SLICEM** sites of those CLBLM
tiles (SLICEL stays open to static logic; LUTRAM and SRL exist only in SLICEM):

```tcl
create_pblock pblock_shared_dyn
resize_pblock [get_pblocks pblock_shared_dyn] -add {SLICE_X12Y50:SLICE_X12Y74 SLICE_X12Y125:SLICE_X12Y149 SLICE_X14Y50:SLICE_X14Y74 SLICE_X14Y125:SLICE_X14Y149}
set_property EXCLUDE_PLACEMENT true [get_pblocks pblock_shared_dyn]
set_property CONTAIN_ROUTING false [get_pblocks pblock_shared_dyn]
```

The existing patched nextpnr already expresses this (no new patch): nextpnr logs
`pblock 'pblock_shared_dyn': 0 cell(s) on 2000 bel(s), exclusive`. `CONTAIN_ROUTING false` is needed because routing
containment otherwise follows `EXCLUDE_PLACEMENT`.

- With it: 0 shared tiles with LUTRAM/SRL in all rv_c builds; partial.py reports `shared frames: 204 static tiles …;
  with LUTRAM/SRL contents: 0` and `state frames: 0` for all 6 partials (`build/patched/partials/rv_c_native/*.log`).
  The SLICEMs of shared tiles still carry route-through LUT INITs from the router (8 LUT INIT features in `xor_n`) and
  `NOCLKINV` defaults, no cells.
- **Negative control** (`--no-shared-frame-pblock`, `build/patched/rv_c_native_noshared/`): 11 shared tiles get
  LUTRAM/SRL (the PicoRV32 register file), and partial.py **refuses** (`REFUSED: rewriting shared frames would reset
  LUTRAM/SRL/BRAM state in static tiles ['CLBLM_L_X10Y125', …]`, `build/patched/partials/rv_c_noshared/rm_andn_from_xor.log`).
  The new state-frame check finds the same 11 tiles in 8 frames (c10 minors 32–35 …).

### 2.3 Verification (native_check)

rv_b and rv_c: **9/9 PASS each** — region2v on the 3 full builds SIM+PROVED; 6 partials each: region gate, CRC,
simulated load exact; byteman applied to the base vs the original target: 0 frames differ; region2v on each byteman
result SIM+PROVED (3582 vectors; `FORMAL_TIMEOUT=600`).

### 2.4 Regression of partial.py

All existing native partials were regenerated with the final partial.py and compared by sha256 with the files on disk:
26/26 identical (14 rv_pr partials in `build/partials/rv_native`, 6 rv_b, 6 rv_c) (`build/patched/regen.log`).

## 3. Task B: the BRAM/DSP region

### 3.1 Region choice

xc7a50t tile grid (prjxray `tilegrid.json`), grid columns 19–28:
`BRAM_L(19) | BRAM_INT_INTERFACE_L | INT_L_X6 | INT_R_X7 | CLBLM_R_X7 | CLBLM_L_X8 | INT_L_X8 | INT_R_X9 | INT_INTERFACE_R | DSP_R_X9(28)`.
Both INT pairs (21/22 and 25/26) are inside; the left neighbour pair (15/16) and right pair (31/32) are outside, so the
INT-pair rule of Phase 2 holds. Region:

`SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59` (one full clock row, top row 1)

`python3 flow/region.py --list <spec>`: 420 tiles, 256 frames — CLB_IO_CLK c6 (28, BRAM column), c7 (36), c8 (36),
c9 (28, DSP column), BLOCK_RAM c0 (128). It is clock-row aligned, so no static CLB or BRAM tile shares its frames
(only the 4 HCLK tiles in word 50).

### 3.2 Vivado reference (designs/dfx_bram, build/vivado/dfx_bram)

Static: 28-bit counter, `rm_slot(clk, din[15:0], dout[15:0])`. RMs: `rm_lut` (1K×16 ROM with an INIT pattern,
Vivado maps it to one RAMB18E1) and `rm_lutmul` (ROM + 8×8 multiply in a DSP48E1, `use_dsp`), plus the greybox.
Pblock = the region above (Vivado form with a RAMB18 range). Command (one Vivado job at a time):

```powershell
vivado\run_vivado.ps1 -Design dfx_bram -Top top -Script build_dfx.tcl -Rms "rm_lut,rm_lutmul" -Run
```

`pr_verify`: all three pairs "compatible" (`pr_verify.rpt`). Partials (all three): 208,944 bytes, 52,191 words.

Packet structure (`flow/bitparse.py`, `flow/partial_passes.py`):

| item | Vivado partial |
|---|---|
| sequence | RCRC, IDCODE, NULL, MASK/CTL0 0x100, MASK/CTL0 0x400, then per pass `WCFG FAR=0x00020300` (CLB_IO_CLK) and `WCFG FAR=0x00820000` (BLOCK_RAM), MASK 0x100 CTL0 0, FAR 0x03BE0000, CRC, DESYNC. No START/GRESTORE. Same CTL0 steps as the CLB-only partial of Phase 2. |
| bursts | 4: pass 1 CLB (129 frames = 128 + pad), pass 1 BRAM (129), pass 2 CLB, pass 2 BRAM |
| CLB run | c6..c9 contiguous: 28+36+36+28 = 128 frames, pad c10 m0 |
| BRAM run | BLOCK_RAM c0 m0..127, pad BLOCK_RAM c1 m0 |
| pass 1, CLB | minors 24/25 all-ones in **all four** columns (also the BRAM and DSP columns); RM interconnect pips held back; differences only in minors 0–25 for rm_lut/grey. For rm_lutmul also minors 26/27 of the DSP column: the DSP tile tie-off pips (`DSP_0_*.DSP_GND_R`, 39) and `AREG_1`/`BREG_1` are held back (decoded with `flow/pass1_fasm.py`) |
| pass 1, BRAM tile | BRAM_L routing pips (`BRAM_ADDR…IMUX`) and BRAM config (minors 26/27) are **not** held back: equal to the final values |
| HCLK | the RM's clock-leaf pips in the region columns (`HCLK_R_X22Y130`, `HCLK_R_X26Y130` `ENABLE_BUFFER`/`HCLK_LEAF_CLK_B_BOT5`) differ between modules and are held back in pass 1 |
| BLOCK_RAM content | written in **both** passes, identical to the full bitstream (INIT); the greybox partial writes the 128 BRAM frames as zeros |
| BLOCK_RAM word 50 | 0 in every BRAM frame (full and partial); openXC7's full bitstreams carry a frame ECC there (`ecc_ok` in all 4 non-zero BRAM frames of rv_pr `xor_n`) |
| GLUTMASK | no separate step; CTL0 is written exactly as in the CLB-only partial (meaning of 0x100/0x400 still not checked against UG470) |

**Pad frames (designs/dfx_bram_pad):** the same design plus a static, LOC'd, initialised RAMB18 at `RAMB18_X1Y50`, i.e. in
the BRAM column of the BRAM pad frame. Vivado still writes **all-zero** pad frames (BLOCK_RAM c1 m0, and CLB c10 m0),
although the full bitstream has data there (words 51–55 of BLOCK_RAM c1 m0). So Vivado does not rely on the pad frame
being written with static content; this is consistent with the pad not being committed, but it is not a proof.

**pr_check on Vivado's own configurations:** with the default (strict) rule they "differ" only in word 50 (HCLK) of 3–6
region frames; with `--hclk-full-column` (a region frame whose other 100 words all belong to the region) all three pairs
are identical outside the region.

### 3.3 partial.py against Vivado's partials (flow/vivado_bram_compare.sh)

partial.py run on Vivado's full bitstreams (pass-1 pips = pips common to the three configurations), compared word by
word with Vivado's partials (`flow/partial_compare.py`, `build/patched/vivado_compare/dfx_bram/compare_*.json`):

| configuration | length | pass 2 (CLB + BRAM) | pass 1 BRAM | pass 1 CLB |
|---|---|---|---|---|
| rm_lut | 52,191 words, same | identical | identical | 23 words differ in 7 frames |
| rm_lutmul | same | identical | identical | 29 words in 11 frames |
| grey | same | identical | identical | 23 words in 7 frames |

The remaining pass-1 words are (a) pips common to all configurations that Vivado still holds back (c6 m11/m13,
c9 m7/m13; the pip-ownership difference already seen in Phase 2) and (b) word 50 of c7/c9 m0/m2/m5, the HCLK leaf pips
Vivado holds back. Before the partial.py changes of this phase, pass-1 BRAM frames differed in word 50 of 127 frames
(recomputed ECC) and the DSP minors 26/27 were not held back.

## 4. partial.py changes (safety)

- Region gate unchanged (only region frames plus the documented run-end pads; pads carry the full bitstream's content).
- Shared-frame refusal unchanged, and now also refuses used static BRAMs (`RAMB18_Y?.IN_USE`) in shared tiles.
- **New refusal:** every frame the partial writes (region frames and pads) is checked against the state bits of static
  tiles: LUTRAM/SRL tiles → their `SLICEM_X0.?LUT.INIT` minors (32–35), used BRAMs → all 128 BLOCK_RAM minors. Any hit
  refuses and deletes the output; the record gets `static_state_frames_written`. Tested: the rv_c no-pblock control
  (8 frames, 11 tiles); a synthetic `BRAM_L_X30Y125.RAMB18_Y0.IN_USE` hits the rv_m BRAM pad `BLOCK_RAM c1 m0`.
- Pass 1: all-ones minors 24/25 for every CLB_IO_CLK column with those minors in the region; non-CLB_IO_CLK frames
  (BLOCK_RAM) taken from the full bitstream; DSP tie-off pips held back with the INT pips.

## 5. RV RMs with BRAM and DSP (rv_m)

### 5.1 RMs and shell

`designs/rv_soc/pr/ports_clk.json` (= ports.json + `core_clk`) → shell with `rm_core(.clk(clk), …)`; same anchors.
Clocked cores, one cycle of latency, `ready` registered:

| RM | funct[0]=0 | funct[0]=1 | yosys (OOC) |
|---|---|---|---|
| tbl | `rd = tbl[rs1[9:0]]`, `tbl[i] = i*i*i + 0x9E3779B9` | `rd = rs1[15:0]*rs2[15:0]` | 1 RAMB36E1 (READ_WIDTH_A 36), 1 DSP48E1 (AREG=BREG=0, MREG=1, PREG=0) |
| tbl2 | `tbl[i] = (i*0x01000193) ^ (i<<22) ^ 0xA5A5A5A5` | `rd = rs1[15:0]*rs2[31:16]` | same |
| xorc | `rd = rs1 ^ rs2` | `rd = rs1 & rs2` | LUT/FF only |

**DSP gap fix:** these DSPs have AREG=BREG=0 and the default MASK; the decoded FASM has `AREG_0`, `BREG_0` and
`MASK[45:0]` all ones (bits 46/47 0 = the unisim default). So `nextpnr-dsp-mask-areg.patch` would not change their FASM;
it was **not merged**. An RM with AREG/BREG=1 or MASK[47:46] set would need it.

### 5.2 Build

```bash
VARIANT=replay BASE_REV=e62fafd1 PATCHES=nextpnr-pblock-replay.patch DRY_RUN=0 bash toolchain/buildenv/build_nextpnr_variant.sh
python3 flow/build_pr_native.py --design rv_m --run          # variant replay; build/patched/rv_m_native_replay.out
```

- First build `tbl_a` (router binary, keep-out on): router2 1317.55 s, 127.83 MHz. Without keep-out
  (`router_nokeepout/tbl_a`) 71.16 s, 147.08 MHz: the 10-column-wide region makes static detour around it. One seed each.
- The replay builds failed with the `router` binary (`ERROR: Bel 'X23Y30/SLICE_X0Y0.A6LUT' … not valid for cell
  'u_rm.ain_valid_0'`): replay closes the anchor tiles, and the RM's input registers were packed next to the anchors.
  Fixed by `docs/drafts/nextpnr-pblock-replay.patch` (+13/-2). The `replay/` directory was seeded with the router
  binary's `tbl_a` (the patch only changes behaviour under `-o prerouted`; `tbl_a`'s FASM header says `e62fafd1`,
  the replays say `e62fafd1-replay`).
- Static RAM (2 RAMB36) went to `BRAM_L_X6Y90/95` (clock row 0), outside the region; RM BRAM `BRAM_L_X6Y125`,
  DSP `DSP_R_X9Y130.DSP_0` (tbl) / `DSP_R_X9Y125.DSP_1` (tbl2).

| check | result |
|---|---|
| static pips in region / RM pips outside | 0 / 0 in tbl_a, tbl_n, tbl2_n, xorc_n (`checks/pips_*.json`) |
| pr_check, strict (no HCLK option) | identical outside; tbl/tbl2 244, tbl/xorc 254, tbl2/xorc 251 frames differ, all inside |
| replay router2 | 1.69–2.06 s, 127.83 MHz |
| partial size | 208,816 bytes body = Vivado's data length for the same region; 256 frames in 2 runs × 2 passes |

### 5.3 Verification (native_check with BRAM checks)

```bash
NAT=build/patched/rv_m_native/replay OUT=build/patched/partials/rv_m_native BMO=build/patched/byteman_check/rv_m_native \
  REGION=SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59 TAGP=native_rv_m \
  FORMAL_TIMEOUT=300 BRAM_RMS="tbl tbl2" R2V_ARGS="--sweep 1024" FORMAL_SKIP_RMS="tbl tbl2" bash flow/native_check.sh
```

**12/12 PASS** (`build/patched/native_check_rv_m.log`, partial logs and `.check.json` in `build/patched/partials/rv_m_native/`):

| item | tbl | tbl2 | xorc |
|---|---|---|---|
| region2v on the full build | sim 4605/4605 compared (1 warm-up), proof not run | same | sim 4605/4605, **PROVED** |
| BRAM INIT of the full build vs yosys | 31,744/31,744 bits equal | 29,696/29,696 | - |
| partial from each of the 2 other RMs: gate, CRC, simulated load exact | 2/2 | 2/2 | 2/2 |
| byteman (base + partial) vs original target | 0 frames differ, 2/2 | 2/2 | 2/2 |
| region2v on the byteman result | sim pass 2/2 | 2/2 | sim + PROVED 2/2 |
| BRAM INIT on the byteman result | 31,744/31,744, 2/2 | 29,696/29,696, 2/2 | - |
| partial.py safety | shared tiles 4 (HCLK), with state 0; state frames 0 (all 6 partials) | | |

Loading xorc over tbl/tbl2 rewrites the BRAM frames with the xorc build's content; the
simulated load and the byteman comparison cover those 128 BLOCK_RAM frames. tbl2 has 29 defined (non-x) bits per word in yosys's INIT; the cause of the 3
undefined positions was not examined.

- region2v: each check first reads all 1024 table entries (`--sweep 1024`, funct=0, rs1=0..1023), then the usual 3582
  vectors, against the RTL core with its clock; 1 warm-up cycle is not compared.
- BRAM INIT: `region2v bram` decodes the RAMB36 INIT/INITP from the bitstream (RAMB18_Y0/Y1 halves remapped as in
  fasm2bels `remap_init`) and compares every defined bit with the RAMB36E1 INIT that yosys produced
  (`rm_<rm>_synth.json`). 31,744 bits = 1024 words × 31: yosys stores the table in 9-bit lanes (memory bit 8 → DOP0,
  17 → DOP1, 26 → DOP2) and drops bit 31, which is 1 in every entry of `tbl`. The RTL-level check is the 1024-entry sweep.
- Formal for tbl/tbl2 is not run: one attempt (tbl, 5 GB `ulimit -v`) ended inconclusive inside yosys `sat` (the BRAM
  model has 36,864 bits of state). xorc is proved.

Negative controls (`flow/r2v_controls.sh`, `build/patched/controls_rv_m.log`): 

| corruption of the decoded `tbl_n` FASM | region2v check (sweep + vectors) | BRAM INIT check |
|---|---|---|
| one LUT INIT bit (`--corrupt`) | FAIL, 133 of 3582 | - |
| BRAM `RAMB18_Y0.INIT_00` bit 0 | FAIL, 49 of 4606 | FAIL, 1 bit differs in INIT_00 |
| DSP `ZMREG[0]` added (MREG 1 → 0) | FAIL, 1573 of 4606 | PASS (BRAM untouched) |
| DSP `ZIS_OPMODE_INVERTED` bit 0 flipped | ERROR: the yosys DSP48E1 model stops on the illegal OPMODE | PASS |

### 5.4 region2v model notes (not verified on hardware)

- `designs/rv_soc/tb/r2v_ramb36e1.v` is our behavioural model (the yosys `RAMB36E1` in cells_sim is a blackbox with
  timing only; `gl_ramb36e1.v` rejects width 36). Supported: TDP, widths up to 36, DOA/DOB_REG, IS_*_INVERTED.
- Decoded but not taken from FASM: a port whose write enables are all tied to 0 is modelled with WRITE_WIDTH 0 (the
  zero-encoded width features decode as `_1`). L/U pins of RAMB36 must have the same source (constant or the same clock).
- DSP: decoded per the prjxray feature names (inverse of nextpnr's writer and checked against Vivado's FASM in the gap
  analysis); `USE_MULT` is assumed `MULTIPLY` (no feature). Inverted pins are folded into the netlist because the yosys
  DSP48E1 model rejects `IS_ALUMODE_INVERTED != 0`. Unused DSP inputs (C, D, PCIN, …) are x in sim: 98 undriven nodes.
- Zero-bit default pips that the verbose decoder emits beside a real pip on the same wire are dropped; with several
  always-on pips into one wire, the one whose source is driven is used.

## 6. Not verified / open

- Nothing on hardware: no BRAM/DSP partial was loaded; whether the pad frame is committed is still unknown (Vivado's
  zero pads point to "not committed"); whether openXC7's frame ECC in BLOCK_RAM word 50 matters is unknown.
- HCLK leaf bits: our three rv_m RMs needed no HCLK change; an RM that clocks a column the static does not would differ in
  word 50, which strict pr_check rejects (Vivado treats it as RM routing). `--hclk-full-column` is opt-in only.
- Vivado's remaining pass-1 differences (common pips held back, HCLK held back, AREG_1/BREG_1 held back) are not copied.
- Formal equivalence for the BRAM RMs; only simulation (incl. the exhaustive table read) and the INIT comparison.
- Keep-out on a wide region costs router time (1317 s vs 71 s) and, on one seed, Fmax (127.83 vs 147.08 MHz).
- `docs/phase8-native.md`, referenced from phase 7, does not exist; the native-flow write-up is in
  `docs/drafts/nextpnr-router-region.md` and this file.
