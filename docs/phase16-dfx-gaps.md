# Phase 16: closing offline DFX gaps against Vivado (Artix-7)

Offline work, 2026-11-06. Nothing here ran on hardware; JTAG partial loading on a board stays open. Every number
comes from a run, and the log or output path is next to it (paths under `build/dfxgaps/` unless stated). Every timing
number names its timer.

## 1. native_check in full (matrix "Next" item 6)

`FORMAL_SKIP_RMS=popc FORMAL_MEM_KB=3000000 OUT=build/partials/rv_native_rr BMO=build/byteman_check/native_rr
TAGP=native_rr flow/native_check.sh` on `build/patched/rv_pr_native/router` (6 RMs: rot, add, popc, andn, minmax,
xor) with the current `flow/partial.py` (phase 10-15 edits included): **42 PASS, 0 FAIL, exit 0**, 1589 s
(`native_check_rr.log`).

- 30 partials (every target x base): region gate + CRC + exact simulated load; byteman base + partial = original
  target (0 frames differ); region2v on the byteman result: 25 SIM+PROVED, 5 SIM-PASS with the proof not run (popc
  targets, skipped as in phase 8: the 32-bit popcount proof did not finish in 600 s).
- 6 full builds: region2v SIM+PROVED for rot, add, andn, minmax, xor; popc SIM-PASS (proof skipped).
- Same counts as the phase-8 run of 2026-11-05 (`build/native_check_final.log`), so the later partial.py changes did
  not change these results.

## 2. `--other-region` from flow/native_check_multi.sh (matrix row 14)

`flow/native_check_multi.sh` now passes `--other-region <spec>` for every other partition to each partial
(default on; `OTHER_REGION=0` restores the old command line) and fails a partial whose log lacks the check. Run on
`build/patched/rv2_native/rtkeep` (2 RPs, 4 configurations): **18 PASS, 0 FAIL, exit 0**, 532 s
(`native_check_multi_or.log`): 8 partials, each "other partition ...: 0 shared, 0 of its frames written", recorded
as `other_regions` in every `.check.json`; 2 negative controls; 8 region2v full.

## 3. Per-configuration timing with the hard-block timer (matrix row 15)

Every DFX configuration was built by a nextpnr variant without `-o hardblock-timing`, so its ICAPE2 pins were
untimed. `flow/dfx_retime.py` (new) replays each configuration's own placement and routing (`replay_dump.py`,
`-o preplaced/prerouted`) with `-o hardblock-timing` and checks the replay:

- The replay binary must pack like the build's variant. The release binary (rel01tr) and the partpin3 stack both
  refuse rv_pr's replayed CARRY4/LUT BELs (`ERROR: Bel 'X42Y12/SLICE_X0Y0.CARRY4' ... is not valid`,
  `build/dfxgaps/retime_rel01tr/`, first `retime/rv_pr` attempt). So the hard-block draft
  (`docs/drafts/nextpnr-hardblock-timing.patch`, unchanged, applies with offsets) was built on each DFX stack:
  `pp3hb` = partpin3 + draft (for rv_ppt), `rthb` = router + draft (for rv_pr). Both are opt-in variants used only
  for this re-timing (`build/nextpnr-build/{pp3hb,rthb}`, one pre-existing `-Wsign-compare` warning each).
- Check: placement identical, and per net the replay's (wire, pip) set equal to the original's or a subset of it
  (the strength field and the wire order differ by construction). rv_pr: 6/6 strictly identical. rv_ppt: placement
  identical 5/5; the replay drops the partition-pin branches that reach no sink (grey_s 75 nets, 74 of them with no
  sink at all, the 75th `slot_valid` loses only its branch to the pin; modules 9-36 nets, all without sinks), so
  every sink keeps its original path ("timing-equivalent", 5/5 PASS, `retime/rv_ppt_recheck.log`).
- rv2 (variant rtkeep) was not re-timed: pp3hb refuses its BELs the same way, and no rtkeep + draft binary was built.

Fmax per configuration, nextpnr's timer (MHz):

| flow | configuration | without hard-block timing (as built) | with `-o hardblock-timing` | critical path with it |
|---|---|---|---|---|
| anchor flow (rv_pr router) | xor, andn, add, rot, minmax | 141.16 | **104.31** | static, ICAPE2 `u_icap` output to an FF |
| anchor flow | popc (`_taf`) | 99.45 | **99.45** | the module's own path (unchanged) |
| rv_ppt (partpin3) | grey_s, xor, andn | 175.32 | **118.95** | `u_icap.O7` clk-to-q 5.20 ns (SDF) + 2.35 ns route + LUTs to an FF, 8.41 ns |
| rv_ppt | add | 153.89 | **118.95** | same static ICAP path |
| rv_ppt | rot | 152.11 | **118.95** | same static ICAP path |

Evidence: `retime/rv_pr.log`, `retime/rv_ppt_recheck.log`, `retime/*/*/retime.json`, `.../nextpnr.log`.

- With the ICAP pins timed, every configuration except popc is limited by the same static path out of ICAPE2, so
  per-RM differences disappear behind it. Vivado also reports an ICAPE2 path as the worst path of rv_soc
  (docs/gap-vivado.md: FF -> ICAPE2 setup at `u_icap/RDWRB`, 134.72 MHz overall at 10 ns), but the direction
  differs (Vivado: into ICAPE2; nextpnr with the draft: out of ICAPE2); not traced further.
- `ofx timing --build build/dfxgaps/retime/<flow>` reads these builds (Fmax fallback; the DFX stacks have no
  `--report-paths`).

## 4. Vivado's DFX build of the same design (build quality, matrix row 15 / "DFX build quality")

**Still not run (2026-11-08).** The queue (now one design per Vivado invocation, slot 3, `docs/wip/dfx-gaps/job_vq.sh`)
finished the DSP fuzz (§6) and the xc7a50t/xc7a100t die builds (§7), then stopped at the wind-down before
dfx_rv_p10/p5 and the xtime runs. Until those run, the per-RM Fmax/area/partial-size/build-time comparison below has
only the open side. Earlier note: the Vivado slot was held by the placer/router/benchmark agents for the whole session
(from 21:43, when my queue started, to the end of the session it never found `vivado.lock` free with no other `vivado.exe` running), so there are no Vivado
numbers here; none are estimated. What is ready:

- `vivado/build_dfx_rv.tcl` + `vivado/run_dfx_rv.sh NAME PERIOD_NS`: Vivado's DFX flow on the same RTL and pblock
  as rv_pr/rv_ppt (rv_soc, u_rm in `SLICE_X12Y100:SLICE_X15Y149`, RMs xor/andn/add/rot with the rv_ppt shell
  `designs/dfx_rv/rm_slot_pp.v`, greybox), per configuration: report_timing_summary, WNS overall / without ICAPE2
  paths / through u_rm, pblock utilisation, step times, pr_verify, full and partial bitstreams. It stops only
  between configurations after 900 s and resumes (no change to Vivado's directives).
- `flow/xtime_prep.py` inputs for Vivado's timer on our placements (rv_ppt and anchor-flow module builds, 10 ns and
  5 ns): `build/dfxgaps/xtime/src/` (for `vivado/build_xtime.tcl`).
- `flow/dfx_vivado_compare.py`: the per-RM table (Fmax of both tools with the timer named, area, partial bytes,
  build time) from those outputs; today it prints only the open side (e.g. rv_ppt xor: 32 LUT + 1 FF in the
  region, 59,272 B partial, 6.6 s nextpnr; anchor flow xor: 140 LUT + 33 FF including the anchors).
- The queue that runs all Vivado jobs of this phase in ~20-minute invocations: `docs/wip/dfx-gaps/job_vq.sh`.

## 5. Partition pins (matrix row 6)

### 5.1 `HD.PARTPIN_LOCS` / `HD.PARTPIN_RANGE` from the XDC

`flow/partpin_assign.py assign --xdc FILE` reads Vivado's two partition-pin properties on the RP's pins:

- `set_property HD.PARTPIN_LOCS INT_R_X11Y140 [get_pins u_rm/valid]`: the pin must be in that interconnect tile.
- `set_property HD.PARTPIN_RANGE {SLICE_X14Y100:SLICE_X15Y109} [get_pins {u_rm/rd[0]} ...]` or an `INT_L/INT_R` tile
  range: the pin must be in an INT tile of that range (SLICE ranges are mapped with `region.region_tiles`).
- `get_pins` patterns use Vivado's `*`/`?` wildcards with literal brackets; several properties on one pin intersect.
  A pattern that matches no boundary pin, an unknown tile, an empty range or an empty intersection is an error.
- The constrained pins are placed only on candidates in their allowed tiles; everything else is unchanged. The
  `.json` records `xdc_partpins` and `xdc_tiles` per pin.
- `build_pr_native.py`: design key `partpin_xdc`; HD.PARTPIN lines are removed from the XDC given to nextpnr.
  `ofx dfx build` with `partpins = "auto"` passes the project XDC that holds HD.PARTPIN lines (one file at most).
- UG909 says not to put HD.PARTPIN_LOCS on clocks; the clock is not a partition pin here (phase 15 §4).

Checks:

- No-op: without `--xdc`, the rv_ppt step-1 assignment (`repro_a/partpin3/union_p`) gives `.partpins` and
  `.endpoints` `cmp`-identical to the committed ones; the `.json` differs only in the `placed_json` path string.
  Dry runs of rv_pr, rv_b, rv_c, rv_m, rv2, rv_pp, rv_ppa and rv_ppt after the change: every build step `[skip]`
  (`dry/after_*.txt`); rv_pr and rv2 byte-identical to phase 15's dry runs.
- `designs/dfx_rv/partpin_example.xdc` (rd[0..3] in SLICE_X14Y100:SLICE_X15Y109, rs1[*] in INT_L_X10Y100:INT_L_X10Y149,
  valid in INT_R_X11Y140): 37 of 108 pins constrained; every constrained pin lands in its allowed tiles
  (`partpin_xdc/xdc.json`).
- Full flow, design `rv_ppx` = rv_ppt + this XDC (`rv_ppx_build.out`, wall 5632 s including waits for other jobs'
  nextpnr runs; outputs `build/patched/rv_ppx_native/partpin3/`): 37 of 37 constrained pins in their allowed tiles,
  68 of 108 pin wires differ from rv_ppt's; `grey_s` routed all 108 pin nets (850 pips, locked); pr_check 14/14
  STATIC IDENTICAL OUTSIDE REGION (6 module pairs, 4 greybox strict, 4 greybox `--hclk-full-column`);
  partpin_check 4/4 PASS (108/108 nets, outside route == locked route). nextpnr Fmax (nextpnr timer, ICAPE2 untimed):
  grey_s/xor/andn 174.03, add 152.86, rot 149.86 MHz, against rv_ppt's 175.32 / 153.89 / 152.11 at the same seed.
  Partials (`flow/native_check.sh` with `GREY`, `PARTPINS=static_pp.json`, proofs not run):
  **30 PASS, 0 FAIL**, 650 s (`ppx_native_check.log`): 20 partials (59,272 B each, gate + CRC + exact simulated
  load, byteman = original target), region2v simulation PASS on the 4 module builds and the 16 byteman results with
  a module target (no RTL for the greybox target).

### 5.2 Timing feedback into the static endpoints (rv_ppt at every seed)

Phase 15 found rv_ppt above the references at seed 1 only. At seed 2 its static build (`grey_s`) was the limit
(144.32 MHz, critical path in the CPU), which phase 15 traced to the boundary endpoint slices fixed from the union
placement (`fix_endpoints`). The feedback tried here is a selection over that one choice, judged by the module
builds' timing: build the flow with and without `fix_endpoints` and keep the one whose worst configuration is
faster. Same seed, same pins (the assignment is identical: static distance mean 20.0 / max 76 in both).

| seed | RM | rv_ppt, endpoints fixed (phase 15) | rv_ppt, endpoints not fixed | rv_pp | anchor flow |
|---|---|---|---|---|---|
| 2 | xor / andn (static path) | 144.32 | **157.18** | 146.39 | 148.48 |
| 2 | add | 144.32 | **148.37** | 146.39 | 148.48 |
| 2 | rot | 142.59 | **144.05** | 146.39 | 146.54 |

nextpnr's timer, MHz, ICAPE2 untimed as in phase 15 (`ppt_seed2_nofix/partpin3/*/nextpnr.log`; references from
`build/patched/rv_ppt_native/baseline/`). Checks of the no-fix build: pr_check module pairs 6/6 and greybox
`--hclk-full-column` 4/4 STATIC IDENTICAL; greybox strict 4/4 differ only in word 50 (HCLK leaf, the phase-15
TOP/BOT case); partpin_check 4/4 PASS.

- Without fixed endpoints static is 12.86 MHz faster at seed 2 and every RM improves, but add stays 0.11 MHz below
  the anchor flow and rot 2.34/2.49 MHz below rv_pp and the anchor flow. So the selection does not make rv_ppt beat
  the references at every seed.
- Seeds 1 and 3 without fixed endpoints: not finished (their nextpnr runs waited behind the placer agents with
  `OFX_MAX_NEXTPNR=1`; stopped at the end of the session; resume with `docs/wip/dfx-gaps/job_s13.sh`).
- Not done: a feedback loop that moves pins or endpoints using per-net slack from the module builds. The DFX stacks
  have no `--report-paths`, so per-net slacks would need the timing-report draft on the partpin3 stack first.

### 5.3 Partition pins as the default?

Decision: **no; anchors stay the default and `partpins = "auto"` stays opt-in.** Evidence:

- Fmax is not better at every seed (§5.2, phase 15 §5.1). With the ICAPE2 pins timed (§3), rv_ppt (118.95 MHz)
  is above the anchor flow (104.31 MHz) at seed 1, but both are limited by the same static ICAP path, so this says
  little about the partition pins themselves.
- The best variant (rv_ppt) needs every RM up front (union model), which conflicts with child runs for RMs added
  later (§8); `ofx dfx` auto mode uses the phase-14 model (partpin2), which was slower than the anchors for add/rot.
- It depends on a 7-patch nextpnr draft stack (partpin3) that is not in the release; the no-op evidence for that
  stack is only rv_soc without a pblock (phase 15 §5: `.frames` identical to partpin2).
- What is in its favour: every check passes on rv_pp, rv_ppa, rv_ppt, rv_ppx and the dfxpp_* device examples, the
  RMs are 108 LUT + 32 FF smaller than with anchors, and builds are reproducible.

## 6. DSP bit "26_277" (`USE_MULT=NONE`) and the pass-1 rules

**Numbering.** In Vivado's `cfg_rm_dspb.bit` (dfx_dsp) the only DSP bit that prjxray-db does not name is frame
0x0002049a, word 68, bit 21 (`unknown_bit` of bit2fasm). Tile DSP_R_X9Y130 has base 0x00020480, offset 61, 10 words
(xc7a35t tilegrid), so in prjxray-db's segbit numbering it is **26_245** (minor 26, bit (68-61)*32+21). Phase 10
called it 26_277; with offset 60 that would be the same bit. `flow/dsp_use_mult.py` and `dsp_pass1.tile_bits`
(which also derives the named features correctly, e.g. DSP_1 `AREG_1` 27_271) both give 26_245. Its neighbour
in DSP_1 is `USE_SIMD_FOUR12_TWO24` at 26_244.

**Decoding run** (`designs/gap/dsp_um_{none,multiply,dynamic}`: four DSP48E1 at DSP48_X0Y0, X0Y1, X1Y0, X1Y1 with
identical settings except USE_MULT; MREG=0 so NONE is legal): **run 2026-11-08** (Vivado 2025.2, one invocation per
variant, `C:/Users/finnf/open-dfx-xc7-vivado/build/dspum/<variant>/`), decoded by `flow/dsp_use_mult.py`
(`build/dfxgaps/dspum/dsp_use_mult.json`, `dsp_um_*.fasm`). Result:

| variant | named DSP features (both tiles, both sites) | bits prjxray-db does not name |
|---|---|---|
| USE_MULT=NONE | AREG_1, BREG_1, MASK, ZADREG, ZAREG_2_ACASCREG_1, ZBREG_2_BCASCREG_1, ZDREG, ZIS_*_INVERTED, ZMREG | **26_85 and 26_245** in DSP_L_X34Y0 and DSP_R_X9Y0 |
| USE_MULT=MULTIPLY | the same | none |
| USE_MULT=DYNAMIC | the same | none |

- So **26_85 = DSP_0 `USE_MULT_NONE`** and **26_245 = DSP_1 `USE_MULT_NONE`**, in both DSP_L and DSP_R tiles. The
  DSP_0/DSP_1 offset (+160) matches the neighbours prjxray-db names: SEL_MASK_C 26_83/26_243, USE_SIMD_FOUR12_TWO24
  26_84/26_244, PATTERN[24] 26_86/26_246, ZINMODEREG[0] 26_87/26_247. The bit is set only with USE_MULT=NONE.
- MULTIPLY and DYNAMIC give identical DSP bits: no configuration bit tells them apart (DYNAMIC only allows INMODE
  selection at run time; on this OPMODE the bitstream is the same).
- This decodes phase 10's 26_277 (= 26_245 in DSP_1, see "Numbering"). One device (xc7a35t), 4 DSP sites, one
  setting combination. Next: add `DSP48.DSP_{0,1}.USE_MULT_NONE` to the open flow's DSP segbits (prjxray-db is
  untouched; an overlay) so yosys `USE_MULT="NONE"` cells write the bit, and drop `--pass1-keep-unknown` for it.

**Remaining uncertainty of the empirical pass-1 rules** (`--pass1-hold-dsp`, `--pass1-hold-carry`):

- One device (xc7a35t), one Vivado version (2025.2), one region with DSP columns (dfx_dsp/dfx_bram), 26 DSP cells
  with AREG/BREG=1 and 17 CARRY4 with PRECYINIT.CIN. Not seen: DSP cells with AREG/BREG=1 in a DSP_L column of
  another die, cascaded DSP chains across the region edge, CARRY4 chains that enter the region from static.
- Why Vivado holds these bits back is not known (phase 10 §9); the rules reproduce Vivado's words, they are not
  derived from a documented mechanism.
- Without the hold-back options the partials are still correct for the device by simulation (pass 1 only writes
  bits that pass 2 rewrites); the options only matter for word identity with Vivado.

## 7. Other Artix-7 dies

Open flow (from the device work of 2026-11-06, docs/ofx.md "Devices"; re-checked here only by reading the logs):
the same DFX example (static LFSR + adder, RMs xor/andn, region `SLICE_X12Y100:SLICE_X15Y149`, anchors) passes
`ofx dfx verify` with 10 PASS, 0 FAIL on xc7a50t (`examples/dfx_a50`, `build/ofx/devices/dfx_a50_verify.log`),
xc7a100t (`examples/dfx100`, `dfx100_verify_fabcache.log`) and xc7a200t (`examples/dfx_nv`,
`dfx_nv_verify_fabcache.log`); auto partition pins on xc7a200t (`dfxpp_nv`) 10 PASS 0 FAIL 2 INFO. This phase
added the child-run check on xc7a50t (§8: verify 25 PASS, 0 FAIL with a third RM added later).

Vivado cross-check, **run 2026-11-08** for xc7a50t and xc7a100t (xc7a200t not run: wind-down). Vivado 2025.2,
`vivado/build_dfx_dev.tcl` on `designs/dfx_dev` (RMs rm_xor/rm_andn + greybox, pblock SLICE_X12Y100:SLICE_X15Y149),
then phase 10's check `flow/vivado_variant_compare.sh` (partial.py on Vivado's own full bitstreams, `--static-pip-list
--pass1-hold-hclk`, uncompressed, no RAR) per die with `OFX_PART`/`OFX_FABRIC` set (`build/vq/die_check.sh`; outputs
`build/dfxgaps/die/<die>/`, logs `build/dfxgaps/die/<die>.log`):

| die | Vivado build (wall, one invocation) | partials rm_xor / rm_andn / grey | words | differ from Vivado's partial | CRC, base + partial == target (both commit models) |
|---|---|---|---|---|---|
| xc7a50t | 321 s | 3 / 3 / 3 | 14,805 | 13 / 13 / 13 | OK, 0 frames differ |
| xc7a100t | 600 s | 3 / 3 / 3 | 14,805 | **0 / 0 / 0** | OK, 0 frames differ |

- xc7a50t: the 13 words are 2 bursts x 6 words + CRC, all in the burst's **pad frame** c12 m0 (`0x00020600`, words
  34/35, 38/39, 49 + ECC 50), outside the region. That frame holds the static design's routing in INT_L_X12Y117/Y119
  (`CLK_L1.GCLK_L_B5`, bits 00_23/00_27) and INT_L_X12Y124 (`LVB_L12.NE2END2`, 00_45). Vivado writes the pad frame as
  zeros; partial.py writes the full bitstream's own content. This is the known, deliberate difference of phase 10
  §9.4 (dfx_dsp residue, 31 words), not a new gap: same behaviour, a different die. `--pass1-hold-dsp
  --pass1-hold-carry --pass1-keep-unknown` change nothing (`xc7a50t_opt.log`, 13/13/13).
- xc7a100t: **word-identical** to Vivado's partials (the pad frame is zero in this build). Vivado's partials are
  59,272 B on both dies (.bin; the same size as our rv_ppt xor partial in §4). Vivado's timer on xc7a100t: WNS 5.185 ns (rm_xor) / 3.997 ns
  (rm_andn) at 10 ns; rm_xor 42 LUT + 1 FF in the pblock.
- Vivado's own side on xc7a50t (`C:/Users/finnf/open-dfx-xc7-vivado/build/dfx_dev_xc7a50t/`): WNS at 10 ns 4.155 ns
  (rm_xor) / 3.582 ns (rm_andn), Vivado's timer; rm_xor in the pblock 42 LUT + 1 FF; pr_verify compatible (194 static
  cells, 1520 static pips compared).
- Resume: `nohup setsid bash docs/wip/dfx-gaps/job_vq.sh &` (skips finished builds), then `bash build/vq/die_check.sh
  xc7a200t xc7a200tsbg484-1`. Ready: `designs/dfx_dev/` (the same RTL as `examples/dfx_a50`,
module `top`, RMs as `rm_slot` with the rv_ppt shell, per-die pin XDCs) and `vivado/build_dfx_dev.tcl` (build_dfx.tcl
with the part as an argument, plus the static pip dump), for xc7a50tcsg324-1, xc7a100tcsg324-1, xc7a200tsbg484-1.
The planned check is phase 10's: `flow/vivado_variant_compare.sh` (partial.py on Vivado's own full bitstreams vs
Vivado's partials, word for word) per die, with the die's `OFX_*` device variables.

## 8. `ofx dfx` against Vivado's DFX project flow

| Vivado DFX project flow (UG909) | ofx | status |
|---|---|---|
| partition definitions, reconfigurable modules | `[[dfx.partition]]` with `rms = {...}` in ofx.toml | covered |
| configurations (`create_pr_configuration`) | one RP: one configuration per RM; several RPs: `[dfx] configs` or every combination | covered |
| parent run (static implemented with one configuration, then locked) | anchors: `<first RM>_a` build, static locked (`static.preplaced/.prerouted`); auto partition pins: greybox static `grey_s` | covered |
| child runs reusing the locked static | every module build starts from the locked static | covered |
| adding or changing an RM later re-runs only its child run | **new** (`ofx/cli.py` `child_runs`): before, any input change deleted the whole DFX build, static included | closed here (one partition; several partitions still rebuild everything) |
| `pr_verify` | `pr_check` in `ofx dfx build` and `ofx dfx verify` (bitstream frames, stronger) | covered |
| `write_bitstream` writes every configuration's full and partial bitstreams in one step | `ofx dfx build` writes a partial for every ordered pair (multi-RP: every single-RP change, with `--other-region`) | covered |
| greybox configuration (`update_design -buffer_ports`) | auto mode: `grey_s`; anchors mode: none | gap (anchors mode) |
| per-run timing reports | `ofx timing --dfx` (nextpnr timer, ICAPE2 untimed by the DFX variants); `flow/dfx_retime.py` re-times with the hard-block draft (opt-in, §3) | partial |
| `report_utilization -pblocks` | **new**: `ofx report --dfx` prints each partition instance's cells per build | closed here |
| RESET_AFTER_RECONFIG, BITSTREAM.GENERAL.COMPRESS | `[dfx] rar`, `compress` | covered |
| HD.PARTPIN_LOCS / HD.PARTPIN_RANGE | **new** (§5.1), auto mode only | closed here (auto mode) |
| DFX Decoupler IP | `[dfx] decoupler` | covered |
| one command for everything | `ofx dfx build --run` (region DRC, static, every configuration, pr_check, every partial) | covered |

**Child runs, checked** (`build/dfxgaps/childrun/`, a copy of `examples/dfx_a50`, xc7a50t, anchors):

- The stamp now holds a key of the static implementation's inputs (static sources, XDC, partition spec, region,
  variant, part, clock, and the anchor RM in anchors mode; none in auto mode) and one key per RM. When only RMs
  change, the outputs of the changed RMs are removed (module build, synthesis, linked netlist, proxy/placement
  files, pr_check/pip logs, partials and verify files that name them) and everything else is kept.
- run 1: full build with xor, andn. run 2: `add` added to `rms` -> "static inputs unchanged: child runs for RM(s)
  ['add'] ...", only `pnr add_n` ran; `static.preplaced`, `static.prerouted`, `xor_a`, `xor_n`, `andn_n` `.frames`
  sha256-identical to run 1 (`run1.sha`, `run2.sha`); 4 new partials. run 3: a byte appended to `rm_core_andn.v`
  -> child run for `andn` only (27 outputs removed); every hash identical to run 2 (same netlist). run 4: no
  change, nothing rebuilt (30 `[skip]`). `ofx dfx verify --run`: 25 PASS, 0 FAIL (`verify.log`).
