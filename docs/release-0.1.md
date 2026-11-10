# ofx 0.1 release notes (draft, 2026-11-07)

ofx 0.1 is the first packaged release of the open-dfx-xc7 toolchain for Xilinx 7-series. It is built from pinned
upstream sources plus our patch series by `install/install.sh` into a user prefix. Use it through `bin/ofx` and an
`ofx.toml` project file.

Status: **not tagged.** The lead tags and publishes. Everything below was measured offline on one machine (WSL2
Ubuntu, 11 GB), and nothing was tested on hardware. Numbers carry the timer that measured them.

## What is in it

| Component | Pin | Our changes |
|---|---|---|
| nextpnr-himbaechel (xilinx) | openXC7/nextpnr ce3f7c18 | 27 patches (install/patches/nextpnr, tree 961ea46e) |
| yosys | oss-cad-suite 2026-10-21 binary | 3 plugins built from patches on yosys 3718f7f13 (tree 45078a66) |
| openFPGALoader | v1.2.0 (befbab4f) | 2 patches, `--partial` (tree 7694eafd) |
| prjxray, prjxray-db, nextpnr-xilinx-meta, byteman | install/sources.toml | db additions (FIFO, XADC, DIFF_TERM, ...) |
| chipdb | xc7a50t fabric (Artix-7 35T/50T parts) by default | `ofx/` chipdb with the XADC bel; `cal/` chipdb with measured cell timing |

The patches and plugins are listed in docs/install.md and docs/drafts/README.md.

## Defaults of `ofx build` in 0.1

The rule: an option is on by default only if
- every option off still gives the plain flow, and
- the option is a no-op where it must not change anything, and
- where it changes results on purpose, a regression run shows it is not worse.

The flow scripts (`flow/build_openxc7.py`, `flow/build_pr_native.py`, ...) keep their old defaults, so earlier
results stay reproducible.

| key | 0.1 default | evidence |
|---|---|---|
| `hardblock_timing` | **on** (new in 0.1) | see "hardblock-timing" below |
| `placer` | `auto` = **static placer at every size** (new: was static up to 3000 cells, else HeAP) | no-op up to 3000 cells (same arguments); above that, Vivado's timer on the placement agent's runs: LiteX DDR SoC static 83.92 MHz vs HeAP 84.46 (-0.6 %), eth SoC 68.64 vs 67.39 (+1.9 %); HeAP does not route mc12_a100 (docs/wip/placement-global.md, commit b82fe04). DDR static mean is over 2 seeds (Vivado could not place seed 3 around the imposed cells) |
| `dsp_cascade` | on (unchanged) | `.frames` identical to off on blinky and rv_soc (release binary) |
| `async_reg` | on (unchanged) | yosys JSON identical to plain synth_xilinx on blinky and rv_soc |
| `clkbuf_keep_buffer_inputs` | **on** (after 0.1; off in 0.1) | 0.1: not a no-op, the plugin's BUFG was named `$auto$clkbufmap_gapfix.cc:278` instead of `$auto$clkbufmap.cc:268`, which changed nextpnr's hash order. Now the installer maps each NEW_ID line of the plugin to the stock line with `#line`: yosys JSON identical on 22 QoR-suite designs plus blinky and rv_soc (`install/synth_noop_suite.py clkbuf_keep_buffer_inputs`, `install/defaults_noop.py --candidates`); bufio_iddr and oserdes build with it and fail without; bufr fails either way (hold). An install whose plugin predates the fix (no `clkbufmap_gapfix.stock-names`) keeps it off |
| `dsp_init` | **on** (after 0.1) | synth_xilinx's map_dsp with plugin `xilinx_dsp_init` (stock xilinx_dsp + install/patches/yosys-dsp-init, same `$auto$xilinx_dsp.cc` names): yosys JSON identical on 22 QoR-suite designs plus blinky and rv_soc (`install/synth_noop_suite.py dsp_init`); diffeq2 synthesizes (stock asserts); repro cases simulate with 0 mismatches. An install without the plugin keeps it off with a note |
| `carry_di_bypass` | off (opt-in; patch 0031 after 0.1) | nextpnr release patch 0031 `-o carry-di-bypass`, on with `carry_di_bypass = true` in [build]. Off = no-op; `.frames` identical with it on fir (no CARRY4). Area: slices -6 to -16 %. Fmax under Vivado's timer with the exact placement import (3 seeds, paired): rv_soc -3.6 %, bram +1.3 %, rv_mul -0.3 %, rv_big -1.3 % (mean -1.0 %), so it stays off; the placed-mode measurement (+1.7 %) was optimistic (Finding 15, round 3). Release regress with it on: install, series, noop, defaults, ofx, identity PASS (prefix copy, 2026-11-08) |
| `dsp_pipeline` | off | changes every multiplier netlist; equivalence by random simulation only; FIR slower in Vivado P&R (Finding 8) |
| `cell_timing` | `stub` | changes placement everywhere; Vivado's timer is better on 4 designs and worse on bram (Finding 10) |

### hardblock-timing (`-o hardblock-timing`)

Without it, nextpnr's timer does not see DSP48E1, ICAPE2 or RAMB36E1 pins, so it optimises and reports the wrong
paths (docs/qor-vivado.md Finding 1). The previous default's own Fmax numbers therefore cannot be compared with
the new one's.

How it was checked (`install/hardblock_regress.py`):
- Every build of the 0.1 defaults without the option (`flow/release_bench.py` variant `rel_new`) was replayed with
  `-o preplaced/-o prerouted` and `-o hardblock-timing`.
- The replay must reproduce the placement and routing exactly (route strength ignored). It did on all 15 builds;
  the FASM differed in at most 10 slice configuration bits, such as NOCLKINV.
- Both placements were then timed by the same honest timer.
- Setup: 5 ns, seeds 1-3, release nextpnr, xc7a35t.

| design | 0.1 defaults without it, blind timer's claim (mean) | same placement, honest timer (mean) | with hardblock-timing, honest timer (mean) | change |
|---|---|---|---|---|
| blinky | 374.82 | `.frames` identical with and without (3 seeds) | | no-op |
| rv_soc (ICAP) | 158.21 | 119.95 | 135.37 | +12.9 % |
| rv_mul (DSP) | 150.73 | 100.76 | 102.51 | +1.7 % |
| rv_big (DSP, BRAM) | 135.05 | 100.03 | 103.64 | +3.6 % |
| bram (RAMB36) | 237.63 | 135.92 | 149.45 | +10.0 % |
| fir (DSP cascade) | 239.74 | 210.44 | 207.27 | -1.5 % (inside the 2 % rule) |

What this shows:
- The blind timer overstated Fmax by 13-75 % on these designs.
- Placing with the honest timer gives equal or better real Fmax.
- This is nextpnr's timer, not Vivado's. Vivado-timer confirmation is not part of this release check.

Sources:
- the summary JSON: build/hardblock_regress/summary.json;
- the bench output: build/qor/release_0_1.json and build/qor/oxc7/rel_new{,_tmg}/.

## Release regression (`install/release_regress.sh --run`)

Run regress6, 2026-11-06/07, prefix ~/ofx-test/prefix (cached install), `OFX_MAX_NEXTPNR=2`. It was made with the
defaults before the change above. The stages affected by the change were re-run in regress7 (see below).

| stage | result | detail |
|---|---|---|
| install | PASS | every step cached and checked by sha/stamp |
| series | PASS | nextpnr 27, yosys 3, openFPGALoader 2 patches apply with `git am` on the pinned revs; trees equal TREE |
| noop | PASS | release nextpnr on the recorded netlists of blinky, rv_soc, rv_pp, rv_ppa, rv_ppt: 9/27 `.frames` identical, 18 differ only by `CFG_CENTER_MID_X46Y32.ICAP.IN_USE` (patch 0024, intended), 0 other differences |
| defaults | PASS | 6/6 (all off = plain flow, XADC chipdb choice, async_reg and dsp_cascade no-ops) |
| ofx | PASS | `ofx new arty-a7-35t` + build with the defaults and with every option off (plain flow) |
| cli (new) | FAIL in regress6, fixed (see below) | 34 PASS, 9 FAIL: 5x `ofx power` (no fitted model), 3x `dfx load --via jtag` dry run (wrong openFPGALoader path), dfxpp_a50 `dfx build` |
| smoke (rv_ppt) | PASS | blinky + rv_ppt from RTL, pr_check 5/5, native_check 6 PASS, `.frames` identical or ICAP line only |
| smoke_rvpr | FAIL in regress6: test bug, fixed | the comparison mis-handled the gated (symlinked) prefix path; on the same outputs the fixed check gives INFO x3 ("netlist differs only in source paths"), as before the gating change |
| identity | PASS | blinky/rv_soc recorded; rv_pr built from RTL with the previous and the release nextpnr: 3/3 identical apart from the ICAP line |
| revalidate | PASS | rv_pr, rv_b, rv_c, rv2, rv_ppa, rv_ppt, rv_m rebuilt: every pr_check STATIC IDENTICAL OUTSIDE REGION (rv_ppa greybox pairs DIFFER as in the reference), region pips 0/0 |

Fixes from this run (commit 48f6d0e):
- `install/smoke_test.sh`: also maps the resolved oss-cad-suite path.
- `ofx/cli.py`: `dfx load --via jtag` uses the release install's openFPGALoader, which has `--partial`. The dry
  runs on rv_pr, dfx_a50 and dfx_vhdl now print the command.
- `install/release_regress.sh`: `ofx power` without a fitted model is a known-gap SKIP.

The `cli` stage covered:
- 5 flat examples on the installed fabric (blinky_a50, blinky_b3, blinky_cma7, vhdl_blinky, vhdl_mixed): build,
  timing, drc, report and program (dry run) all pass.
- DFX examples rv_pr, dfx_a50 and dfx_vhdl: dfx build, then dfx verify with 10 PASS, 0 FAIL each, then
  timing --dfx.

regress7 re-ran the stages that the new defaults and the fixes touch (defaults, ofx, cli; `OFX_MAX_NEXTPNR=1`):

| stage | result | detail |
|---|---|---|
| defaults | PASS | 6/6. blinky: `.frames` with `-o hardblock-timing -o dsp-cascade-place` identical to the plain flow. rv_soc: the `dsp-cascade-place` no-op (its hardblock change is intended and covered above) |
| ofx | PASS | the new project builds with the 0.1 defaults; every option off is still the plain flow |
| cli | 42 PASS, 1 FAIL | flat examples: build, timing, drc, power, report, program (dry run) all pass. rv_pr, dfx_a50, dfx_vhdl: dfx build, verify 10 PASS / 0 FAIL, timing --dfx, `dfx load --via jtag` (dry run) all pass. The FAIL is dfxpp_a50 (Known gaps). `ofx power` passed here only because the copied `ofx/` held the locally fitted, untracked `power_model.json` |

## Clean install

`install/install.sh --run --prefix ~/ofx-test/clean/prefix --cache ~/ofx-test/clean/cache --jobs 2 --devices xc7a50t`
was run into an empty prefix and an empty cache, so every download and every build step ran again.

- **Interruptions:** WSL was killed twice during the run (unrelated to the installer). The installer resumed from
  what it had, and the final run completed: exit 0, 13 min 21 s of wall time, peak RSS 1.8 GB (with `-j2`).
- **chipdbs:** the default, `ofx/` and `cal/` xc7a50t chipdbs have the same sha256 as the cached release prefix,
  and the default one equals the openXC7 nightly (ee4ff400...).
- **Smoke test** against the clean prefix: PASSED (`~/ofx-test/clean/smoke.out`): blinky `.frames` identical; rv_ppt built from RTL; pr_check 5/5 static identical outside the region; native_check 6 PASS / 0 FAIL; of the 7 `.frames`, 3 are identical to the repository's builds and 4 differ only by the intended ICAP line.

## Known gaps in 0.1 (honest list)

- **Hardware:** nothing in this release was run on a board (no partial over JTAG/ICAP, no Zynq boot).
- **dfxpp_a50 (automatic partition pins, Nexys A7-50T) fails `ofx dfx build` with the release nextpnr.** The
  greybox static P&R stops with "Partition pins: no route outside the pblocks for 1 net(s), e.g. 'ready'". The
  same command with the older `partpin2` variant binary routes. The `partpin3` variant fails in the same way, so the regression comes from the pinfeed step (release patch 0012) when the partition net drives a slice CE input; not fixed in 0.1. Anchor-pin DFX (dfx_a50) and
  automatic pins on rv_ppa/rv_ppt are not affected.
  - **Fixed after 0.1** by install/patches/nextpnr/0028 (docs/drafts/nextpnr-partition-pins-ce-sr.patch, tree 63da8585): a CE pin is fed from the interconnect FAN wires (SR from CTRL), which the pinfeed step did not follow on the direct approach. With it `ofx dfx build` + `dfx verify` of dfxpp_a50 pass (10 PASS, 0 FAIL); `install/noop_check.py` on rv_pp/rv_ppa/rv_ppt: 8/25 `.frames` identical, 17 differ only by the ICAP line, 0 otherwise (docs/wip/fixes.md).
- **Latches (LDCE/LDPE) had no BEL** (QoR suite raygentop). Fixed after 0.1 by patches 0029/0030 (tree 7929c4a5): raygentop places, routes and assembles; the latch slice bits of designs/gap/latch_* equal Vivado's (`flow/latch_check.sh`, 4/4); noop_check 0 unexpected differences. Latches are timed like flipflops on their gate.
- **`ofx power`**: the fitted `ofx/power_model.json` is in the repository since 2026-11-08 (b075540); docs/power.md has its error (held-out total 10 % mean).
- **bufr-style designs** (a BUFR-divided clock with paths to its source clock):
  - with `clkbuf_keep_buffer_inputs` the routing failure is gone;
  - but nextpnr then stops on a hold violation (xdc2 hold check, no hold fixing in nextpnr);
  - without the option they fail to route.
- **Devices:** the default install builds the xc7a50t chipdb only, so only Artix-7 35T/50T parts work. Other
  parts need `--devices`. Kintex-7 and Virtex-7: no database.
- **QoR against Vivado (docs/qor-vivado.md):**
  - placement is about 25 % slower under Vivado's timer;
  - LiteX LUT sites +14 %; LUTRAM 320 vs 142;
  - one timing corner;
  - no phys_opt or incremental compile.
- **Untested:**
  - `install/Dockerfile`;
  - `--yosys source`;
  - other Linux distributions;
  - the region2v formal proofs in the smoke test.
- **Not in 0.1:** a GUI, encryption/eFuse, GTP transceivers.

## Files

- `install/release_regress.sh`: the whole regression. Stages: install, series, noop, defaults, ofx, cli, smoke,
  smoke_rvpr, identity, revalidate.
- `install/noop_check.py`, `install/defaults_noop.py` (`--candidates` for proposed defaults),
  `install/hardblock_regress.py`, `flow/release_bench.py`.
- Logs from this run: `~/ofx-test/regress6/logs`, `~/ofx-test/regress7/logs`, `~/ofx-test/candidates/run.log`,
  `~/ofx-test/hbt/`. These are outside the repository.
