# Phase 15: timing-aware partition-pin placement and a greybox with the static clock leaf (native flow, opt-in)

Offline work, 2026-11-05/06. Nothing here has run on hardware. Every number below comes from a run; the log or output
path is next to it. Paths are under `build/patched/rv_ppt_native/` unless stated otherwise. This works on the two open
problems of phase 14 (`docs/phase14-auto-partpins.md` §6) and on matrix item 6 (`docs/dfx-vs-vivado.md`):

1. rv_ppa's pin choice ignores timing: add 135.48 MHz and rot 124.15 MHz, below rv_pp (145.62 MHz) and the anchor flow
   (141.16 MHz).
2. rv_ppa's greybox static (`grey_s`) has no clock leaf in the region, so it differs from every module build in 4
   clocking frames, and a partial built against it is not a valid swap.

The new design is `rv_ppt` (`flow/build_pr_native.py --design rv_ppt`), with the new nextpnr variant `partpin3`. Same
static RTL, region `SLICE_X12Y100:SLICE_X15Y149`, RMs xor/andn/add/rot and shell (`rm_shell_pp.v`, only `ready`
registered) as rv_pp and rv_ppa. rv_ppa, rv_pp and every other design and variant are unchanged (§7).

## 1. What changed in the flow (`main_auto`, keys used only by rv_ppt)

| step | rv_ppa (phase 14) | rv_ppt (this phase) | key |
|---|---|---|---|
| 1 placement model | `greybuf_p`: greybox with one free LUT1 per port bit (no timing path through the region) | `union_p`: a **union RM** in the pblock. `gen_shell2.py --union xor andn add rot` writes an `rm_core` that instantiates `rm_core_<rm>` for every RM and selects among them with `funct[9:8]`. It is synthesized in the pp shell (244 LUTs, 10 CARRY4, 1 FF in the region), so the timing-driven placer sees every module's paths through the region. | `place_union` |
| 2 pin assignment | cost: static distance + bit-slice target row + load | static distance + **`w_module` × distance to the net's module-side cells** in `union_p` (sinks for an input, driver for an output; replaces the bit-slice row), + load; `w_module` = 0.5. Candidates whose wires outside the region are all `_N`/`_S` wrap aliases are dropped (§5). | `pin_module_ends`, `pin_w_module`, `pin_exclude_wrap_exits` |
| 3 greybox static | `grey_s` preplaced with **all** static cells from step 1 | `grey_s` preplaced with only the **boundary endpoint slices** from step 1: the 109 static cells at the ends of the 108 boundary nets (`static_pp_assign.endpoints`) and everything else in their 36 slices (223 cells, `grey_place_endpoints.preplaced`). The rest of static is placed again by `grey_s` itself. | `fix_endpoints` |
| 3 greybox | empty: no cell | one **clock-leaf FF** (`gen_shell2.py --greybox --clock-leaf`: `FDRE` on `clk`, D=0, Q unused, unplaced, so in the pblock) | `grey_clock_leaf` |
| 3 pin routes | nextpnr `partpin2` | nextpnr `partpin3` (§3) | `variant` |
| 4–6 | unchanged | unchanged: export, proxies at the pins, module placement, module builds on the locked static | |
| 7 checks | region_pips, pr_check (10 pairs), partpin_check | the same, plus `pr_check --hclk-full-column` greybox vs each module | `grey_clock_leaf` |

Run: `python3 flow/build_pr_native.py --design rv_ppt --run` (DRY_RUN default; every step cached). `--seed N` (new,
for every nextpnr run of a design; use with `--out`) was added for the seed runs; without it the command lines are
unchanged. The runs went through a waiting wrapper outside the repo (`~/npwait/drive_v.py`, `~/npwait/npwait2.sh`): it
replaces the variant's binary by a script that waits until fewer than two nextpnr processes run and then execs the
same binary (`--version` is not delayed), and lets an experiment override design keys (`DESIGN_OVERRIDE`).

## 2. Pin choice and timing: what was measured (seed 1)

Every row is a full flow. `exp_*` directories reuse the steps before the one they change (copied, so identical inputs).

| run | step-1 model | static cells kept from step 1 | pin cost | grey_s / xor / andn | add | rot | static dist. mean / max | evidence |
|---|---|---|---|---|---|---|---|---|
| rv_ppa (phase 14) | greybox + free LUT1s | all | bit-slice | 158.13 | 135.48 | 124.15 | 35.4 / 59 | `rv_ppa_native/partpin2/*/nextpnr.log` |
| A0 | union RM | all | bit-slice | 134.37 | 134.37 | 130.60 | 17.5 / 50 | `attempt3_union_full_static/` |
| A | union RM | endpoint slices | bit-slice | 175.41 | 145.69 | 131.58 | 17.5 / 50 | `attempt4_configA_pre_modends/` |
| B | union RM | endpoint slices | module ends, `w_module` 1.0 | 158.15 | 153.66 | 145.31 | 16.5 / 58 | `exp_modends/partpin3/` |
| B + HeAP timing weight 40 in step 1 | union RM | endpoint slices | module ends 1.0 | 185.87 (grey_s only; stopped) | – | – | 26.0 / 65 | `exp_tw40/partpin3/` |
| **C** (rv_ppt before the wrap-exit filter of §5) | union RM | endpoint slices | module ends, **`w_module` 0.5** | **177.78** | **155.64** | **154.89** | 16.3 / 58 | `exp_wm05/partpin3/` |
| **rv_ppt final** (C + wrap-exit filter) | union RM | endpoint slices | module ends 0.5 | **175.32** | **153.89** | **152.11** | 16.3 / 58 | `repro_a/partpin3/` (§5) |
| rv_pp (phase 13) | anchored reference | – | from reference | 145.62 | 145.62 | 145.62 | – | `rv_pp_native/partpin/` |
| anchor flow | – | – | – | 141.16 | 141.16 | 141.16 | – | `rv_pr_native/router/` |

Fmax in MHz, nextpnr's `Max frequency for clock 'u_bridge.clk'`; every build closes at 100 MHz.

What each step did, from the critical paths (`nextpnr.log`, "Critical path report"):

- **Union RM in step 1 (A0).** The boundary FFs move to just below the region: static distance mean 35.4 → 17.5.
  But keeping the whole static placement from that build pulls CPU logic towards the region too: the critical path of
  `grey_s` is now inside the CPU (`u_cpu.latched_branch` → adder → FF, 7.44 ns), and static drops to 134.37 MHz.
- **Keep only the endpoint slices (A).** The rest of static is placed by `grey_s` around the fixed boundary FFs: static
  is back at 175.41 MHz (its critical path is static, `grey_s/nextpnr.log`). add reaches 145.69 MHz. rot stays at
  131.58 MHz: its path is `slot_rs2[1]` 1.64 ns → barrel shifter → `slot_rd[*]` 1.93–2.21 ns.
- **Bit order (A → B).** The bit-slice targets put bit 0 at the band's far end (row 29) and bit 31 at the near end
  (row 51). The adder's carry chain runs from bit 0 upwards, so add's module sat at rows 18–25, above the pins, and its
  boundary routes were 2.60 and 2.26 ns (`attempt4…/add_n`). With the module-end term, each pin goes between the
  static end and where the union RM placed that net's module cells; for the rot-critical nets the pins move from rows
  30–31 to rows 35–48 (`static_pp_assign.json` `module_end`). add 153.66, rot 145.31 MHz (6.88 ns, 0.013 ns over
  rv_pp's period).
- **`w_module` 0.5 (C).** Pins sit nearer the static end. rot's path becomes `slot_rs2[1]` 1.57 ns → module →
  `slot_rd[8]` 1.47 ns, 6.46 ns in total: 154.89 MHz. add 155.64 MHz.

Tried and not kept (logs kept):

- **Tighter clock for the placement builds** (`--freq 160`, then a `create_clock -period 6.25` placement XDC): the
  XDC's `create_clock` overrides `--freq`, and with the 6.25 ns XDC `union_p` came out `.frames`-identical to the
  10 ns build (`exp_freq160/`, `exp_p625/`). This placer's result here does not depend on the period. The code was
  removed.
- **HeAP timing weight 40** for step 1: endpoints further away (mean 26.0) and `union_p` 128.49 MHz (`exp_tw40/`).
- **Moving the endpoint slices next to their pins** (own placement): 11 of those 36 slices also hold a CARRY4 of a
  static carry chain (`grey_place_endpoints.preplaced`), and an FF preplaced alone is refused (`ERROR: Bel
  'X30Y58/SLICE_X0Y0.DFF' of type 'SLICE_FFX' is not valid for cell '$auto$ff.cc:337:slice$10343'`, first
  `fix_endpoints` attempt, which preplaced the 109 endpoint cells only; that log was overwritten by the next run). This
  is why whole slices are kept. Moving them was not pursued.

## 3. nextpnr: pin routes that do not block other cells' inputs (variant `partpin3`)

Draft `docs/drafts/nextpnr-partition-pins-pinfeed.{md,patch}`, 1 file (`himbaechel/uarch/xilinx/xilinx.cc`), +41/−3,
on top of the unchanged `partpin2` stack. Found by run:

- With the union placement the boundary FFs sit in the slices just outside the region. `-o partition-pins-route`
  (phase 14) then failed: `no route outside the pblocks to X30Y55/SLICE_X1Y0.CFFMUX_OUT` for `slot_rd[17]`, and the
  same for `slot_rd[12]` and `slot_rd[6]`, after the search had visited every reachable wire
  (`attempt1_partpin2_no_routethru/grey_s/nextpnr.log`). A LUT route-through fallback and a one-level rip-up did not
  help (`attempt2_bypass_stolen/`; the search hit its 2,000,000-wire cap; both were dropped). A temporary, since-removed diagnostic
  (`debug_greys/nextpnr.log`, `PPDBG` lines) showed the bypass wires in front of those FFs held by earlier pin nets as
  bounce hops: `X31Y55/BYP_ALT2` by `slot_rd[24]`, `X31Y53/BYP_ALT1` by `slot_rd[30]`, `X31Y53/BYP_ALT3` by
  `slot_rd[13]`.
- Reserving only the pin nets' own sinks fixed the pin pass (all 108 routed), but then router2 failed a static net:
  `ERROR: Failed to route arc 10.0 of net 'pcpi_rs1[29]' … to X33Y56/SLICE_X1Y0.B5FFMUX_OUT`, because a locked pin
  route held that FF's bypass wire. Blocking every pin-feed wire except on an approach that ran through LUT inputs and
  bounce wires failed the pin pass again (3 nets). The `grey_s` logs of these two runs were overwritten by later runs;
  the excerpts captured at the time are in `attempt3_union_full_static/intermediate_grey_s/`.
- **The change:** a pin route may enter a pin-feed wire (site pin, `CLBL*`, `BYP*`, `IMUX*`, `FAN*`, `GFAN*`, `CTRL*`,
  `*BOUNCE*`) only on the direct approach to its own target (uphill through site pins, `CLBL*`, `BYP*`, `IMUX*`; not
  through a LUT, not through a bounce) or on the way out of its own site pins. With it, `grey_s` routes all pins
  (`Partition pins: 75 net(s) routed from their source to the pin, 33 from the pin to their sinks … (868 pips, locked)`,
  `exp_wm05/partpin3/grey_s/nextpnr.log`) and router2 finishes.

Build: the six `partpin2` patches plus this one, on `router-region`, `ninja -j4` (`build/nextpnr-build/partpin3.build.log`;
the only warning is the pre-existing `-Wsign-compare` in `apply_prerouted`). The seven patches applied to `router-region`
in a scratch worktree give exactly the `build/src/nextpnr-partpin3` worktree (`diff -r`, no difference). The no-op check
is in §5.

## 4. Greybox static with the region's clock leaf

**Cause** (phase 14 §6, re-read from the FASM): in rv_ppa's `grey_s` no static clocked cell needs the left-hand HCLK
row of the region's clock region (`…Y130`; the HROW's `BUFHCE_X0Y0` is off). A module's `ready` FF makes
`route_clocks` open it: `CLK_BUFG_REBUF` GCLK16 up to it, `CLK_HROW_TOP_R_X60Y130` `BUFHCE_X0Y0` and
`CLK_HROW_CK_BUFHCLK_L0`, `HCLK_CMT_X8Y130`
`HCLK_CMT_CK_BUFHCLK0_USED`, then in the region's own column `HCLK_R_X32Y130` `ENABLE_BUFFER` and the leaf
`HCLK_LEAF_CLK_B_BOT0` (diff of `rv_ppa_native/partpin2/{grey_s,add_n}/rv_soc.fasm`). The first three are outside the
region's frames (r0/r1 `c23` and `c1`); the HCLK bits are word 50 of the region's own frames.

**Fix:** the greybox gets one clock-leaf FF (`rm_grey.v`: `(* keep *) FDRE gb_clock_leaf (.C(clk), …, .D(1'b0), .Q())`).
So the static clock tree of `grey_s` already reaches the region's clock row, and `static.prerouted` carries it to every
module build. The FF is a module cell (in the pblock, in the region's frames); its pin nets are unaffected (it touches
none). This follows Vivado's model, where clocks reach a reconfigurable partition over the global clock spine and not
through partition pins (UG909 says not to use `HD.PARTPIN_LOCS` on clocks; checked online in phase 14 §5): static owns
the spine up to the region's HCLK row, and the HCLK leaf bits of a column the region fills belong to the module
(phase 10: Vivado holds them back in pass 1; `pr_check --hclk-full-column` names this case).

The greybox still drives no output (`rd`/`ready` pins undriven), as in phase 14; it is a valid swap target for static,
not a functional RM.

Results: §5.

## 5. Results (rv_ppt, final configuration: C plus the wrap-exit filter)

**One more fix, found by the seed-2 run.** With seed 2, `grey_s` failed: `Partition pins: net 'slot_rd[1]': no route
outside the pblocks to X33Y53/SLICE_X1Y0.CFFMUX_OUT (1 wires visited)` (`final1_no_wrap_filter/seed2/partpin3/grey_s/
nextpnr.log`). Its pin `X31Y51/EL1BEG0` is on the region's bottom row; per prjxray's tileconn the node is
`X31Y51/EL1BEG0`, `X32Y51/EL1END0` (both in the region), `X32Y52/BRKH_INT_EL1END_S3_0`, `X32Y53/EL1END_S3_0`, so its
only wire outside the region is an `_S` wrap alias, which nextpnr's node evidently does not have (the same effect as
phase 14's `ER1END_N3_3`, there excluded by the pin's own name). `partpin_assign.py assign --exclude-wrap-exits`
(new, rv_ppt key `pin_exclude_wrap_exits`) drops a candidate whose wires outside the region are all wrap aliases. Wrap
aliases as such are harmless: 1071 of the 6783 usable candidates have one as a member, and the seed-1 assignment used
38 of them. The filter changed 26 of the seed-1 pins, so every rv_ppt result below was rebuilt with it; the earlier set
is kept in `final1_no_wrap_filter/` (seed 1 there: 177.78 / 155.64 / 154.89 MHz).

Final builds: `repro_a/partpin3/` (copied to the default output `partpin3/`), seed 1.

| check | result | evidence |
|---|---|---|
| Fmax | grey_s, xor_n, andn_n **175.32 MHz** (critical path static, 5.70 ns); add_n **153.89 MHz**; rot_n **152.11 MHz** | `*/nextpnr.log` |
| critical paths | add_n: `slot_rs2[1]` 1.86 ns → adder → `slot_rd[31]` 2.12 ns, 6.50 ns. rot_n: `slot_rs2[1]` 1.67 ns → shifter → `slot_rd[17]` 1.35 ns, 6.57 ns | `add_n`, `rot_n/nextpnr.log` |
| greybox static routed to the pins | `75 net(s) routed from their source to the pin, 33 from the pin to their sinks, outside the pblocks (864 pips, locked)` | `grey_s/nextpnr.log` |
| module builds | `Partition pins: 108 net(s) … 0 arc(s) without the locked route outside`; pins given to the pblock: xor 98, andn 99, add 98, rot 72 | `*_n/nextpnr.log` |
| pr_check, module pairs | **STATIC IDENTICAL OUTSIDE REGION 6/6**; 71–72 frames differ, all inside, 0 foreign words | `checks/pr_check_*_n_*_n.log` |
| pr_check, **greybox vs modules** | **STATIC IDENTICAL OUTSIDE REGION 4/4**, strict (0 frames outside, 0 foreign words; 54/71/72/72 frames inside), and 4/4 with `--hclk-full-column` (0 HCLK-only frames) | `checks/pr_check_grey_s_*.log`, `checks/pr_check_hclk_grey_s_*.log` |
| partpin_check | **PASS 4/4**: 108/108 nets, outside route == locked route, pin on route | `checks/partpin_check.log` |
| region_pips | static pips in the region **0** in all 6 builds (union_p, grey_s, 4 modules); module-only nets' pips outside **0** (add_n 40 nets, rot_n 128, union_p 264) | `checks/pips_*.json` |
| native_check with the greybox (`GREY=partpin3/grey_s`, `PARTPINS`, `STATIC_PIPS=static_pp.prerouted`, `SHELLV=rm_shell_pp.v`, `FORMAL_MEM_KB=3000000`) | **30 PASS, 0 FAIL, exit 0**, 556.37 s. 20 partials (each of grey/xor/andn/add/rot from each other), all 59,272 B, 72 region frames + 1 run-end static pad, CRC OK, simulated base + partial = target (0 frames differ, also with the last frame uncommitted). The 8 greybox partials (to and from `grey`) included. byteman vs the original target: 0 frames differ, 20/20. region2v `--partpins` SIM+PROVED on the 4 module bitstreams and the 16 byteman results with a module target; not run for the greybox target (no RTL). | `repro_a/native_check.log`, `repro_a/partials/*.check.json` |
| region use | xor/andn 32 LUT + 1 FF, add 32 LUT + 1 FF + 8 CARRY4, rot 150 LUT + 1 FF + 2 CARRY4 (the same as rv_pp and rv_ppa); greybox 1 FF | `checks/partpin_check.log` |
| router2 | modules 2.20–2.64 s; grey_s 178.26 s (8 iterations), see §9; union_p 47.17 s | `*/nextpnr.log` |

Per-RM Fmax, seed 1, against the references (MHz):

| RM | rv_ppa before (phase 14) | rv_pp (phase 13) | anchor flow | **rv_ppt** |
|---|---|---|---|---|
| xor | 158.13 | 145.62 | 141.16 | **175.32** |
| andn | 158.13 | 145.62 | 141.16 | **175.32** |
| add | 135.48 | 145.62 | 141.16 | **153.89** |
| rot | 124.15 | 145.62 | 141.16 | **152.11** |
| greybox static | 158.13 | – | – | **175.32** |

**No-op (variant `partpin3`):** rv_soc without pblock (`build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.json`, the
input of phase 14's no-op), `partpin3` against the `partpin2` build `build/patched/rv_ppa_native/noop/rv_soc_partpin2`:
`.frames` identical (`cmp`), FASM identical apart from comments (`noop/rv_soc_partpin3`, `noop/rv_soc_partpin3.log`;
the same chipdb file, `cmp`-identical to the toolchain's).

### 5.1 Seeds 2 and 3, against the references at the same seeds

`flow/build_pr_native.py --seed N --out …` sets the seed of every nextpnr run of a flow (`build_openxc7.py --seed`).
rv_ppt: `seed2/partpin3/`, `seed3/partpin3/`. The references were rebuilt with the same seeds into
`baseline/{rv_pp,rv_ppa,rv_pr}_seed{2,3}/` (rv_pr = the anchor flow with `--rms xor andn add rot`). Seed 1 is §5 and
the committed phase-13/14 builds. MHz; "(s)" = the critical path is in static, so it is the same for every RM.

| seed | RM | rv_ppa | rv_pp | anchor flow | **rv_ppt** |
|---|---|---|---|---|---|
| 1 | xor / andn | 158.13 (s) | 145.62 (s) | 141.16 (s) | **175.32 (s)** |
| 1 | add | 135.48 | 145.62 (s) | 141.16 (s) | **153.89** |
| 1 | rot | 124.15 | 145.62 (s) | 141.16 (s) | **152.11** |
| 2 | xor / andn | 156.13 (s) | 146.39 (s) | 148.48 (s) | 144.32 (s) |
| 2 | add | 128.77 | 146.39 (s) | 148.48 (s) | 144.32 (s) |
| 2 | rot | 121.58 | 146.39 (s) | 146.54 | 142.59 |
| 3 | xor / andn / add | failed: `grey_s` router2, `Failed to route arc 15.0 of net '$abc$71968$aiger$o3449' … CEUSEDMUX_OUT` | failed: `slot_ready: route leaves the region for good at 2 wires` (`partpins.py`) | 158.38 (s) | 155.06 (s) |
| 3 | rot | failed (as above) | failed (as above) | 153.42 | **155.06 (s)** |
| mean of the seeds that built | xor / andn | 157.13 | 146.01 | 149.34 | **158.23** |
| | add | 132.13 | 146.01 | 149.34 | **151.09** |
| | rot | 122.87 | 146.01 | 147.04 | **149.92** |

- rv_ppt built at all three seeds, with all checks passing: pr_check 14/14 STATIC IDENTICAL (including the greybox,
  strict) and partpin_check 4/4 in each (`seed*/partpin3/checks/`).
- **Per seed, the goal is met at seed 1 only.** At seed 2 rv_ppt is below rv_pp and the anchor flow for every RM (its
  static build is at 144.32 MHz); at seed 3 it is above the anchor flow for rot and below it for xor/andn/add (the
  static path, 155.06 against 158.38). Over the seeds that built, rv_ppt's mean is above both references for every RM.
- Static Fmax alone varies by seed in every flow (anchor flow 141.16–158.38 MHz), so one seed does not rank flows.
- rv_ppa's seed-3 failure is in its greybox static build's router2, on a static net into an FF's `CE`; the pin-feed
  patch is aimed at exactly that kind of failure. rv_ppa at seed 3 with `--variant partpin3` (only the binary
  changes; `baseline/rv_ppa_seed3/partpin3/`, `build_partpin3.out`) builds: grey_s 158.45, xor/andn 158.45, add 137.84,
  rot 129.23 MHz; module pairs 6/6 static identical, partpin_check 4/4; greybox vs modules 4/4 STATIC DIFFERS (rv_ppa's
  greybox has no clock leaf, §4).

## 6. Reproducibility

rv_ppt was rebuilt from scratch twice with the final binary and code (`--out build/patched/rv_ppt_native/repro_a`,
`…/repro_b`; `repro_compare.log`):

- `.frames` identical for all 10 nextpnr builds (union_p, grey_s, 4 × `_p`, 4 × `_n`).
- Identical intermediates: `static_pp_assign.partpins`, `static_pp_assign.endpoints`, `grey_place_endpoints.preplaced`,
  `static_pp.partpins`, `static_pp.prerouted`, `static.preplaced`, `rm_union_core.v`, `rm_grey.v`.
- Both: pr_check 14/14 STATIC IDENTICAL, partpin_check 4/4.
- Wall time 600.89 s and 432.75 s (`repro_*/build.out`), including waits for other jobs' nextpnr runs.
- A cached rerun of `python3 flow/build_pr_native.py --design rv_ppt --run` skips all 68 steps
  (`cached_rerun_rv_ppt.out`).
- Earlier, independent evidence: `exp_freq160/` (the same inputs as `exp_modends/`, because `--freq` had no effect)
  reproduced union_p, grey_s, xor_p/n and andn_p/n `.frames`-identically; `final1_no_wrap_filter/repro_{a,b}` were
  10/10 identical too, and identical to `exp_wm05/` built with the binary before a comment-only rebuild.

## 7. Existing designs and variants unchanged

- Dry runs of rv_pr, rv_pr with 6 RMs and `--timing-allow-fail popc minmax`, rv_b, rv_c, rv_c
  `--no-shared-frame-pblock`, rv_m, rv2, rv_pp and rv_ppa: byte-identical to the dry runs taken before any edit
  (`dry/{before,after}_*.txt`), every step `[skip]`.
- No existing variant or `build/patched/*_native` output was rebuilt. `partpin2` and its worktree are untouched.
- `flow/partial.py`, `flow/build_pr.py`, `flow/partpins.py`, `flow/region2v.py`, `flow/partpin_check.py`,
  `flow/pr_check.py` are unchanged. `flow/native_check.sh` only gained the opt-in `GREY` variable.
- `partpin_assign.py assign` writes the same `.partpins`/`.json` as before unless `--module-ends`,
  `--exclude-wrap-exits` or `--endpoint-cells` is given (the new keys are left out of the JSON otherwise): on rv_ppa's
  `greybuf_p` the committed and the new script give byte-identical `.partpins` and `.json`. The candidate cache file is
  renamed (`cand3_…`, one new field, `outer_wires`).
- `gen_shell2.py`: the rv_ppa/rv_pp outputs (`rm_shell_pp.v`, `rm_grey.v`, `rm_greybuf.v`, rv_pp's `rm_shell_gen.v`)
  regenerate `cmp`-identical.

## 8. Files

| file | |
|---|---|
| `flow/build_pr_native.py` | design `rv_ppt`, variant `partpin3`; keys `place_union`, `grey_clock_leaf`, `fix_endpoints`, `pin_module_ends`, `pin_w_module`, `pin_exclude_wrap_exits`, `place_args` (extra nextpnr arguments for the step-1 build; unused by rv_ppt); `--seed` |
| `flow/gen_shell2.py` | `--union RM… [--union-select]`, `--greybox --clock-leaf` |
| `flow/partpin_assign.py` | `assign --endpoint-cells FILE`, `--module-ends`, `--w-module`, `--keep-per-net`, `--exclude-wrap-exits` |
| `flow/native_check.sh` | opt-in `GREY=<dir>`: a greybox build as base and target of the partials (no region2v for it) |
| `docs/drafts/nextpnr-partition-pins-pinfeed.{md,patch}` (new) | variant `partpin3` |

## 9. Open problems

- **Not above the references at every seed (§5.1).** At seed 1 rv_ppt is above rv_pp and the anchor flow for every
  RM; at seed 2 it is below both for every RM (rv_pp 146.39, anchor 148.48/146.54, rv_ppt 144.32 static / 142.59 rot);
  at seed 3 it is above the anchor flow for rot only (155.06 against 153.42; xor/andn/add 155.06 against 158.38, static
  paths). Only the mean over seeds is above both for every RM. At seed 2 the critical
  path of the static build itself is in the CPU (6.93 ns): with the boundary FFs fixed next to the region, the CPU
  logic between them and the rest of static spreads out (`seed2/partpin3/grey_s`). The static endpoints are still
  placed by one union build (seed 2: mean 20.0, max 76 tiles from their pins; seed 3: 3.5 / 39). Nothing feeds the
  module builds' timing back into the pin or endpoint choice.
- **`w_module` = 0.5 was picked from two values on seed 1** (1.0 and 0.5) and then kept; no sweep, and seeds 2/3 were
  run only with it.
- **add's carry chain is placed above its pins.** The adder's 8 CARRY4 sit at rows 18–25 (seeds 1 and 2) or 27–34
  (seed 3) while its pins are in rows 29–51 (`add_place.preplaced`; seed-1 `add_n` critical path: two boundary routes
  of about 2 ns each). The module placement against the proxies does not pull the chain down; not investigated.
- **The union RM needs every RM up front.** Vivado implements static with one configuration; here step 1 synthesizes
  all known RMs into one model. A module added later uses the existing pins and is not in the model.
- **grey_s router2 is slow**: 178–192 s against 15.93 s in rv_ppa, dominated by the static ICAP output nets
  (`icap_o[*]` 6.9–14.0 s each against 0.25–0.35 s; "1000 slowest nets" in `grey_s/nextpnr.log`). Those nets do not
  touch the region; the cause was not traced. The machine was loaded by other jobs (load average about 3–4), so the
  wall-clock times are not comparable to phase 14's.
- **Pin-feed and wrap-exit rules are by wire name** (7-series INT/CLB), found by run, not derived from nextpnr's
  node model. Why nextpnr's node lacks the `_N`/`_S` wrap members prjxray's tileconn has was not traced.
- **The placer still does not see the pins**; module placement still uses the separate proxy run (phase 14 §6).
- **The greybox drives no output** (`rd`/`ready` undriven); it is a valid swap target for static, not a functional RM.
  Its clock-leaf FF and a module's `ready` FF can use different HCLK leaves (`TOP` against `BOT`, seen in
  `attempt3_union_full_static/`); that difference is in word 50 of a column the region fills, which pr_check reports
  as foreign unless `--hclk-full-column` is given. In the final builds the strict check passes too.
- One region, one device. No `HD.PARTPIN_RANGE`/`HD.PARTPIN_LOCS` input. Not compared with a Vivado build that uses
  partition pins; nothing on hardware.
