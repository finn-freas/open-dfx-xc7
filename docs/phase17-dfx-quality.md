# Phase 17: DFX build quality and workflow toward Vivado (Artix-7, offline)

Work of 2026-11-08. Nothing ran on hardware. Every timing number names its timer. Paths are under `build/dfxgaps/`
unless stated. Earlier state: docs/phase16-dfx-gaps.md.

## 1. Workflow: greybox in anchors mode, child runs with several partitions (matrix §8 gaps of phase 16)

**Greybox RM in any mode.** `[[dfx.partition]] greybox = true` adds an RM `grey` (`greyN` with several partitions)
whose core drives every output with 0 and leaves the inputs unused, as Vivado's `update_design -buffer_ports`
greybox does. ofx writes it to `build/stage/greybox_<partition>.v` from the partition's port spec (`core_clk`
honoured). In anchors mode the shell's anchor LUTs/FFs stay, so the greybox module build has 108 LUT + 33 FF in the
region (the anchors and `ready`) and no logic of its own.

- Check (`childrun/`, copy of `examples/dfx_a50`, xc7a50t): adding `greybox = true` to a built project ran a child
  run for `grey` only ("child runs for RM(s) ['grey']", one `pnr grey_n`); `static.*`, `xor_a`, `xor_n`, `andn_n`,
  `add_n` `.frames` sha256-identical to before (`run3.sha`, `grey.sha`); `ofx dfx verify --run` 47 PASS, 0 FAIL
  (4 RMs, 12 partials including 6 to/from the greybox, region2v on the greybox against its generated RTL).

**Child runs with several partitions.** The static key of `ofx dfx build` now covers the first RM of every partition
(the multi-partition flow implements static with that configuration, `<cfg0>_a`) and leaves out the other RMs and the
configuration list. When only those change, the outputs that depend on a changed RM or on a removed configuration are
found by name (build_pr_native's and ofx's file names are made of RM names: `cfg_<a>_<b>_linked`, `<rp>_<rm>_m`,
`<a>_<b>_n`, `asm_<a>_<b>`, `pr_check_*`, partials) and removed; everything else is kept.

- Check (`multirun/dfx2`, 2 RPs on xc7a50t, RMs xor/andn and add/andn2, variant rtkeep): run 1 full (static,
  2 module builds, 4 configurations). Run 2 `greybox = true` on rp2: child run for `grey2` only (`rp2_grey2_m`,
  `xor_grey2_n`, `andn_grey2_n`; 1 output removed: the aggregate pr_check). Run 3 one byte appended to
  `rm_core_andn2.v`: child run for `andn2` only (82 outputs removed, 3 builds). Run 4 no change: nothing built.
  Every static and unchanged-configuration `.frames` sha256-identical from run to run (`run*.sha`); run 3's
  rebuilt andn2 frames identical to run 2's (same netlist). `ofx dfx verify --run`: 30 PASS, 0 FAIL.

## 2. DSP48E1 USE_MULT=NONE decoded (phase 16 §6)

The validation agent ran `designs/gap/dsp_um_*` on Vivado slot 3. `flow/dsp_use_mult.py`: with USE_MULT=NONE one
unnamed bit per DSP site, DSP_0 **26_85** and DSP_1 **26_245**, in both DSP_L and DSP_R tiles; MULTIPLY and DYNAMIC
give no unnamed bit and identical named features. Draft `docs/drafts/prjxray-db-dsp-use-mult.{segbits,md}`.
The open flow writes it with draft `nextpnr-dsp-use-mult` (`-o dsp-use-mult-none`, opt-in) and those segbits:
the same two bits as Vivado in both tiles, 4 bits different from the option off, MULTIPLY unchanged.

## 3. Placer improvements in the DFX stack

`build/src/nextpnr-pp3pl` = the placer agents' worktree `build/src/nextpnr-place` (openXC7 ce3f7c18 + release
patches 0001-0011, hardblock-timing, placer-tuning, placer-delay-cal, packing-dpl, placer-density) + release patches
0012 (partition-pin pin-feed) and 0028 (FAN/CTRL pin feed), the two DFX patches that stack lacks. Variants
(build_pr_native): `pp3pl` (no extra options), `pp3pl_tu` (static placer, anchored start, target util 1.0,
crit-quantile 0.02, hardblock-timing: Finding 17's `tu10 + cq02`), `pp3pl_tucdb` (+ carry-di-bypass).

- No-op: rv_ppt seed 1 with `pp3pl` gives `.frames` identical to the committed partpin3 build (`repro_a`) for all
  6 builds (union_p, grey_s, 4 modules) and identical pins (`noop_pp3pl/seed1/pp3pl`).
- A third from-scratch partpin3 rebuild (`repro_c_partpin3/`) is again identical to `repro_a` (6/6).

**Anchor flow with the placer options** (`anc_tu`, rv_pr with `--rms xor andn add rot`, variant `pp3pl_tu`):
builds at seeds 1-3, pr_check 6/6 STATIC IDENTICAL at every seed. nextpnr with ICAPE2 timed (the build runs with
`-o hardblock-timing`): seed 1 127.29, seed 2 134.66, seed 3 139.45 MHz (rot 125.66), against the same timer on the
HeAP-placed anchor builds (§4: 104.31 / 110.84 / 108.89). Vivado's timer on them: §5.

**Partition-pin flow with the placer options: aborts** (not fixed here; the static placer belongs to the placer
agents, reported to them with these reproducers):

- `grey_s` with preplaced static cells (the boundary endpoint slices, or all static cells in unfixed mode):
  `Assertion failure: entry == nullptr (common/kernel/base_arch.h:156)` in the simulated-annealing refinement after
  the static placer (`ppt_tu/seed2`, `seed3`, `ppt_tucdb/seed1`, `.../grey_s/nextpnr.log`; command line in
  `rv_soc.log`): a bel is bound twice, i.e. the static placer put a cell on a bel a preplaced cell holds.
- module build (`<rm>_n`, every module cell and all static preplaced): `Assertion failure: bel != BelId()
  (common/kernel/nextpnr_types.cc:192)` at router setup, a cell left without a bel (`ppt_tu/seed1/.../add_n`,
  `ppt_tucdb/seed2/.../add_n`).
- The anchor flow's static build has only the anchor LUTs/FFs preplaced (BEL attributes) and works.

## 4. Partition pins against the anchor flow at every seed

### 4.1 What was compared before, and why it was not like for like

- **Timer.** Phase 15/16 ranked the flows with nextpnr's timer as built, where the ICAPE2 pins are untimed. With
  them timed (§4.3) every configuration of both flows is limited by a static ICAPE2 path, as in Vivado.
- **Placement objective.** The builds were placed with the ICAPE2 untimed, so the placer never saw the ICAP path.
- **The RM function differs.** The anchor shell (`rm_shell_native.v`) registers `rd` (32 FDRE) and `ready` inside
  the region; the partition-pin shells (`rm_shell_pp.v`) register only `ready`. So a partition-pin RM does
  static FF -> pins -> RM logic -> pins -> static FF in one cycle, an anchor RM only static FF -> RM FF. rot (the
  barrel shifter, 150 LUTs) loses on that, not on the pins.

### 4.2 Selection of the static and module builds (opt-in keys, build_pr_native)

- `static_try_unfixed`: also build the greybox static with the whole union placement kept (phase 15 "A0"), next to
  the boundary-endpoint-slices mode, and keep the faster (`grey_s_cf0` / `grey_s_cu0` -> `grey_s`, `selected.json`).
- `static_seeds N`, `module_seeds N`: N candidate builds with seeds s, s+1000, ...; `module_place_alts`: extra
  module placement candidates with other placer arguments; `pin_tile_cap`: partition pins per INT tile (default 3).
- The choice is by nextpnr Fmax of the candidate; each candidate is a complete build, so every check runs on the
  selected one unchanged. Off by default: dry runs of every existing design unchanged.

nextpnr timer, ICAPE2 untimed (as phase 15), MHz, xor/andn are equal (static-limited):

| seed | flow | xor / andn | add | rot | evidence |
|---|---|---|---|---|---|
| 1 | anchor flow | 141.16 | 141.16 | 141.16 | `rv_pr_native/router` |
| 1 | rv_ppt, selection (unfixed + 2 static seeds, 3 module seeds) | 175.32 | 153.89 | 152.11 | `pptsel/seed1` |
| 1 | rv_ppt, pin_tile_cap 4 + selection | 175.41 | 167.84 | 153.07 | `pptcap4/seed1` |
| 1 | rv_ppt, `rd` registered (as the anchor shell) + selection | 153.61 | 153.61 | 153.61 | `pptreg/seed1` |
| 2 | anchor flow | 148.48 | 148.48 | 146.54 | `baseline/rv_pr_seed2` |
| 2 | rv_ppt, selection | 157.18 | 152.46 | **144.05** | `pptsel/seed2` (static placer for rot: 145.31, `pptsela`) |
| 2 | rv_ppt, pin_tile_cap 4 + selection | 162.44 | 162.44 | **144.30** | `pptcap4/seed2` |
| 2 | rv_ppt, `rd` registered + selection | 159.44 | 159.44 | 159.44 | `pptreg/seed2` |
| 3 | anchor flow | 158.38 | 158.38 | 153.42 | `baseline/rv_pr_seed3` |
| 3 | rv_ppt, selection | 159.29 | 159.29 | 159.29 | `pptsel/seed3` |
| 3 | rv_ppt, pin_tile_cap 4 + selection | **156.91** | **156.91** | 156.91 | `pptcap4/seed3` |
| 3 | rv_ppt, `rd` registered + selection | **132.59** | **132.59** | **132.59** | `pptreg/seed3` (static path) |

Bold: below the anchor flow. With the ICAP pins untimed no single setting is above the anchor flow at all three
seeds: the static build's Fmax moves by seed in every flow (anchor 141-158, rv_ppt 132-175) and decides most rows.

### 4.3 With the ICAPE2 pins timed (the honest timer)

Re-timed as built (`flow/dfx_retime.py`, hard-block timing on, placement and routing unchanged; nextpnr timer):

| seed | anchor flow (as built) | rv_ppt selection (as built) |
|---|---|---|
| 1 | 104.31 | 118.95 |
| 2 | 110.84 | 129.13 |
| 3 | 108.89 | 117.07 |

Every configuration of a build has the same value (a static ICAPE2 path); `retime/rv_pr_s{2,3}`, `retime/pptsel_s*`.

Built with hard-block timing on, so the HeAP placer sees the ICAPE2 path too (variants `rthb_t` for the anchor flow,
`pp3hb_t` for rv_ppt; same binaries as the re-timing; selection `static_try_unfixed` + `module_seeds 2` for rv_ppt):

| seed | anchor flow (rthb_t, region2v fails, see below) | anchor flow (pp3hb28_t) | rv_ppt (pp3hb_t), endpoints fixed only | rv_ppt (pp3hb_t), selection |
|---|---|---|---|---|
| 1 | 135.48 | 135.15 | 135.50 | **137.59** |
| 2 | 126.01 | 134.99 | 132.07 | **137.61** |
| 3 | 135.56 | 135.06 | 135.56 | **137.55** |

Checks of the pp3hb28_t anchor builds: native_check 20 PASS 0 FAIL at seeds 1 and 2 (seed 3 running), pr_check 6/6;
of the rv_ppt selection builds: native_check (GREY, partpins, proofs not run) 30 PASS 0 FAIL at seeds 1 and 2.

nextpnr timer with ICAPE2 timed; every configuration (xor, andn, add, rot) has the same value in each build; the
critical path is static FF -> `u_icap.RDWRB` (6.43 ns setup in the prjxray-db SDF), e.g. `ppthb/seed1/pp3hb_t/
rot_n/nextpnr.log`. **With the selection, rv_ppt is above the anchor flow at every seed for every RM, and its worst
seed (137.55) is above the anchor flow's best (135.56).** Without the selection it ties at seed 3 and is +0.02 MHz at
seed 1. Checks: anchor builds pr_check 6/6 at each seed; rv_ppt module pairs 6/6 and greybox `--hclk-full-column` 4/4
STATIC IDENTICAL, greybox strict 4/4 differ in the HCLK leaf word only (the unfixed greybox's clock-leaf FF uses the
other leaf, phase 15 §9), partpin_check 4/4, at each of the three seeds. Vivado's timer on these builds: §5.
Cost: the selection builds 2 greybox statics and 2 placements per RM. Wall times (with waits for other agents'
nextpnr runs, so only indicative): rv_ppt 346 / 1053 / 312 s, anchor flow 425 / 183 / 138 s.

### 4.4 `ofx dfx` with `timed = true`

`[dfx] timed = true` (opt-in) builds with the ICAPE2 pins timed: anchors mode uses `rthb_t`; automatic partition
pins use the rv_ppt model (union RM placement, endpoint slices, module-end pin cost, wrap-exit filter, greybox
clock leaf) with `static_try_unfixed` and `module_seeds 2` on variant `pp3hb28_t` (= `pp3hb` + release patch 0028:
without 0028 the greybox build of dfxpp_a50 stops with `Partition pins: no route outside the pblocks ... 'ready'`,
the case 0028 fixes). Check on a copy of `examples/dfxpp_a50` (xc7a50t): `ofx dfx build --run` exit 0,
`ofx dfx verify --run` 12 PASS, 0 FAIL, 2 INFO (`timedrun/`). Without `timed` nothing changes: `ofx dfx build` dry
runs of examples/dfx_a50 and dfxpp_a50 skip every step.

## 5. Where DFX loses against a flat build (nextpnr timer)

The same static RTL built flat (rv_soc with the default `rm_slot` of `designs/rv_soc/sim`, so the RM logic differs:
an `add` with registered outputs), same nextpnr stacks, seeds 1-3 (`flat_nohb/`, `flat_hb/`):

| seed | timer | flat | anchor flow | rv_ppt (best setting of §4) |
|---|---|---|---|---|
| 1 | ICAPE2 untimed (partpin3 binary) | 159.92 | 141.16 | 175.32 / 153.89 / 152.11 |
| 2 | ICAPE2 untimed | 181.39 | 148.48 / 146.54 (rot) | 159.44 (rd registered) |
| 3 | ICAPE2 untimed | 146.20 | 158.38 / 153.42 (rot) | 159.29 |
| 1 | ICAPE2 timed in the build (pp3hb / rthb) | 134.14 | 135.48 | 137.59 |
| 2 | ICAPE2 timed | 133.69 | 126.01 | 137.61 |
| 3 | ICAPE2 timed | 135.30 | 135.56 | 137.55 |

- With the ICAPE2 timed, no DFX-specific loss is visible: every build is limited by the same static path into
  `u_icap.RDWRB` (6.43 ns setup in the prjxray-db SDF), so the region, the pins and the module do not show.
- With it untimed, Fmax depends on the seed by up to 35 MHz in every flow (flat 146-181), more than the differences
  between the flows; one seed per flow does not measure a DFX loss. The anchor flow is below flat at seeds 1 and 2
  (static placement around the pblock with the anchor LUTs/FFs fixed), the partition-pin flow above flat at seeds 1
  and 3. A seed-independent measure needs Vivado's timer without the ICAPE2 paths (§6).

**Correction to the anchor rows of §4.3.** The anchor builds with `rthb_t` (router stack + hard-block draft) route
RM nets out of the region through LUT route-throughs, which region2v cannot follow: `native_check` 4 PASS, 16 FAIL
(region2v FAIL-SIM on all four RMs, e.g. `slot_rd[15]` through `X33Y22` D6; every partial, CRC, simulated load and
byteman result exact; `anchb_native_check_s1.log`). The router stack lacks the pblock-routethru patch (release 0004)
that the partpin3 stack has. Rebuilt on `pp3hb28_t` (partpin3 stack + hard-block draft + 0028): 20 PASS, 0 FAIL at
seed 1 (`anchb28_native_check.log`), pr_check 6/6; nextpnr with ICAPE2 timed seed 1 135.15, seed 2 134.99 MHz (every
RM). `ofx dfx` `timed = true` uses `pp3hb28_t` in both modes.

## 6. Vivado's timer on the DFX builds (exact placement import)

`flow/dfx_exact_src.py` exports each configuration build's own placement (every cell of nextpnr's netlist, LUT pin
locks) and `flow/dfx_exact_vivado.sh` runs `vivado/build_rte.tcl` in "fixed" mode on slot 3: Vivado keeps the
placement, routes, and times at 5 ns (`flow/dfx_exact_table.py`). So these numbers measure our placement with
Vivado's router and timer.

**First result, and why the nextpnr numbers of §4.3 do not carry over.** The anchor flow as built (HeAP, ICAPE2
untimed) gets 100.72 MHz from Vivado (108.72 without ICAPE2 paths; xor, andn, add; rot 102.36). The anchor flow
built with the ICAPE2 timed (`anchb1`, rthb_t) gets **95.15 MHz**, with or without ICAPE2 paths: Vivado's worst
path is FF -> FF reset, 6 LUT levels, 8.13 ns of routing. nextpnr's own timer gave that build 135.48 MHz. With the
ICAPE2 path timed, nextpnr's criticality (relative to the worst path, the 6.43 ns ICAPE2 setup) makes every other
path look uncritical to HeAP, so the logic spreads: the effect Finding 17 measured for the static placer and fixed
there with `--placer-static-crit-quantile`. HeAP has no such option. **So the "honest" nextpnr numbers of §4.3 rank
builds by the ICAPE2 path only; Vivado's timer is the measure.**

TODO(results: Vivado table for anc / ppt / pptsel / pptreg / anctu / anchb / ppthb)
