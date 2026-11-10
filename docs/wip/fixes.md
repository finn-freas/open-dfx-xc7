# WIP: known failures where Vivado succeeds (fix agent, 2026-11-08)

Each item: root cause, fix (opt-in, or default with no-op evidence), regression test, commit.
Scratch outputs live under ~/ofx-test/fixes (outside the repository). nextpnr work tree: build/src/nextpnr-fixes
(detached at the rel01 series head 86fe629a = release 0.1 series, TREE 961ea46e), build build/nextpnr-build/fixes.
Commits there: ea469ae9 partition-pins CE/SR, 4ebb488d gt-unisim-defaults, 3056c773 timing_log crash; latch support
uncommitted until the Vivado reference lands.

## Status (2026-11-08 afternoon)

| # | item | state |
|---|---|---|
| 1 | dfxpp_a50 "no route outside the pblocks for 'ready'" | DONE bc2a3c5: release patch 0028; dfx build + verify 10/0; noop_check rv_pp/rv_ppa/rv_ppt 0 unexpected |
| 2a | fir: DSP48E1 placement illegal without dsp-cascade | already fixed by the 0.1 default `dsp_cascade`; release binary + defaults route the suite netlist |
| 2b | raygentop: no BEL for LDCE | DONE 509c8df: release patches 0029 (timing_log crash) + 0030 (latches), series tree 7929c4a5 (TREE now owned by the packing agent). Exact series binary (rel02): flow/latch_check.sh 4/4 = Vivado latch bits; noop_check blinky/rv_soc/rv_ppt/rv_ppa 9/22 identical, 13 ICAP-only, 0 other; raygentop routes 158.45 MHz (nextpnr timer, 125 MHz target) |
| 2c | diffeq2: yosys xilinx_dsp log_assert | DONE 7a130a7: `dsp_init` default on; 22/22 suite JSON identical; diffeq2 synthesizes and routes (57.9 MHz nextpnr timer at 10 ns) |
| 3 | fitted power model | DONE b075540 |
| 4 | GT/PCIe FASM defaults | DONE b2b3b09 (opt-in draft) |
| 5 | clkbuf_keep_buffer_inputs stock names | DONE 5c70623: default on; 22/22 suite JSON identical |

All new defaults together (`install/defaults_noop.py --prefix <installer-built plugins>`): 6/6 PASS, blinky and rv_soc
yosys JSON identical to plain synth_xilinx. `ofx build` of examples/blinky_a50 with them: bitstream (~/ofx-test/fixes/cli2).
An existing install keeps dsp_init/clkbuf off with a note until install/install.sh rebuilds the plugins (stamp key changed).

## Release prefix rel03 and the suite variant (follow-up)
- `install/install.sh --run --prefix ~/ofx-test/prefix-rel03 --cache ~/ofx-test/cache-rel03 --jobs 2 --devices "xc7a50t xc7a100t"`
  from repo c1a08d7 (series 0001-0031 incl. carry-di-bypass): exit 0. nextpnr ce3f7c18-ofx; plugins xilinx_asyncreg,
  xilinx_dsp_qor, xilinx_dsp_init, clkbufmap_gapfix (+ stock-names marker); chipdbs xc7a50t, xc7a100t (+ ofx/, cal/).
  The cache is a copy (dl, src, mamba) so the existing prefix and cache are untouched.
- `flow/qor_suite.py --release PREFIX` (ffd748c): open runs with that prefix's nextpnr/chipdb/db/plugins and the
  `ofx build` defaults. Running: `open fir raygentop diffeq2 --variant rel03 --release ~/ofx-test/prefix-rel03` (seeds
  1-3), then all designs seed 1; then `vivado --variant rel03 --modes placed` on slot 1 and `report --variant rel03`
  (log ~/ofx-test/fixes/rel03_suite.log, script ~/ofx-test/fixes/fx_suite.sh).
- Open flow rel03 done 16:23: all 21 designs build (before: fir, raygentop, diffeq2 failed). nextpnr-timer best Fmax:
  fir 207.0 MHz (5 ns), raygentop 164.58 (8 ns), diffeq2 58.78 (10 ns), seeds 1-3; the other 18 seed 1
  (build/qor_suite/<d>/open/rel03). Vivado placedx (exact import) for those three + free refs for them queued on slot 1
  (~/ofx-test/fixes/fx_suite2.sh), then `report --variant rel03`.

## Wind-down state (2026-11-08 evening)
- SLICEM fix: draft docs/drafts/nextpnr-slicem-slice0.{patch,md} (401dfa7), handed to the packing agent as release patch
  0032 (they own TREE). Test: `NEXTPNR=<bin> OUT=<dir> bash flow/slicem_check.sh`.
- Still running (left to finish, nothing else running of mine): ~/ofx-test/fixes/fx_suite2.sh = qor_suite `vivado fir
  raygentop diffeq2 --variant rel03 --modes placed`, then `--modes free` for them, then `report --variant rel03`; log
  ~/ofx-test/fixes/rel03_suite.log. If it was cut off, resume with (OFX_MAX_NEXTPNR=1 VIV_SLOT1_ONLY=1):
  `python3 flow/qor_suite.py vivado fir raygentop diffeq2 --variant rel03 --modes placed --run`;
  `python3 flow/qor_suite.py vivado fir raygentop diffeq2 --modes free --run`;
  `python3 flow/qor_suite.py report --variant rel03 --run` (finished runs are skipped).

Left:
- QoR suite: a variant with the release toolchain (`qor_suite.py open --variant ... --nextpnr <release>`) would put
  fir/raygentop/diffeq2 on the scoreboard; Vivado timing of raygentop's latches (time borrowing) not compared.
- Existing installs need `install/install.sh` again for the new plugins (dsp_init, stock-name clkbufmap) and patches 0028-0030.

## 1. dfxpp_a50 (partition-pin pre-route, release patch 0012)

Root cause: patch 0012 (`route_outside_pblocks`, xilinx.cc) lets a pin route enter a pin-feed wire only on the
"direct approach" to its own target. The approach set is built uphill from the target through wires named
site-pin / CLBL* / BYP* / IMUX*. A slice CE pin is fed from the INT tile's FAN wires
(`CLBLM_M_CE <- FAN7 <- FAN_ALT7 <- general routing`, as in the route partpin2 found, ~/ofx-test/ppx/routed.json),
and SR from the CTRL wires. FAN*/CTRL* count as pin-feed wires but were not in the direct-approach list, so every
path to `SLICE_X0Y0.CEUSEDMUX_OUT` was cut off: "no route outside the pblocks to X17Y5x/SLICE_X0Y0.CEUSEDMUX_OUT
(566242 wires visited)". rv_ppa/rv_ppt have no partition net on a CE/SR pin, so they never hit it.

Fix (default; a bug in a default patch): FAN* and CTRL* (not their BOUNCE wires) are direct-approach wires
(docs/drafts/nextpnr-partition-pins-ce-sr.patch, to become release patch 0028). For a target fed through IMUX/BYP
the approach set does not change.

Evidence:
- grey_s of dfxpp_a50 with the regress7 inputs: routes (108 pin nets, 686 locked pips), ~/ofx-test/fixes/pp.
- Full `ofx dfx build --run` + `ofx dfx verify --run` of examples/dfxpp_a50 in a repo copy linked to a prefix whose
  nextpnr is the fixed binary (~/ofx-test/fixes/cli, prefix_pinfeed): build exit 0; verify 10 PASS, 0 FAIL, 2 INFO
  (partials crc OK, base + partial == target, byteman, region2v).
- No-op: `install/noop_check.py --candidate <fixed> --only rv_pp rv_ppa rv_ppt` (running).

## 2a. fir

The QoR suite's open flow (`flow/qor_suite.py`, label base) runs the stock nightly nextpnr-xilinx, which places a
DSP48E1 cascade with a fixed 5-row step and cannot place fir's 32-DSP chain. The release has `-o dsp-cascade-place`
on by default (`dsp_cascade`, docs/release-0.1.md; its no-op evidence is there). The suite netlist
(build/qor_suite/fir/open/base/p5_s1/impl/qor_fir.json) with the release nextpnr and the 0.1 defaults
(`-o hardblock-timing -o dsp-cascade-place --placer static`) places and routes: 197.82 MHz on nextpnr's timer at the
5 ns target (~/ofx-test/fixes/fir). Nothing to fix in the release; a suite variant with the release toolchain
(`qor_suite.py open --variant rel01 --nextpnr <prefix>/bin/nextpnr-xilinx --np-opt ...`) would show it in the
scoreboard.

## 2b. raygentop / latches

yosys maps raygentop's latches to 1356 LDCE + 12 LDPE (1034 with IS_G_INVERTED). nextpnr-xilinx had the latch
infrastructure (X_FF_AS_LATCH in the control-set and placer checks, a LATCH bit in the FASM writer), but no pack
rule, so LDCE/LDPE had no BEL. Change (draft, default: only netlists with latches can change):
- pack.cc: LDCE/LDPE -> SLICE_FFX, G->CK, GE->CE, CLR/PRE->SR, IS_G_INVERTED->IS_C_INVERTED, X_FF_AS_LATCH.
- fasm.cc: LDCE = ZRST, LDPE = no ZRST, LATCH set, FFSYNC clear, LDPE INIT default 1, and the clock inverter has the
  opposite sense for a latch (CLKINV for a non-inverted gate; prjxray fasm2bels decodes IS_G_INVERTED = !CLKINV).
  To be checked against Vivado: designs/gap/latch_{ldce,ldce_ginv,ldpe,ldpe_ginv} (slot 1 queue).
- timing_log.cc: log_fmax threw dict::at for a related clock pair where neither clock has an Fmax (two latch gate
  nets); such a pair is skipped now.
Limit: nextpnr times a latch as a flipflop on its gate (no time borrowing).

## 2c. diffeq2 / yosys-xilinx-dsp-init

The draft (docs/drafts/yosys-xilinx-dsp-init.md) was not a no-op: it kept a 0 init on register bits outside the DSP
that stock xilinx_dsp turns into x, and that changed later optimisation (bgm: +146 FDRE, +239 cells). Reworked
(install/patches/yosys-dsp-init/0001-xilinx_dsp-init.patch, still line-neutral): every bit is handled as before
(0/x -> x), the assert only fires for a 1 init on a bit that goes into the DSP (the matcher already rejects those),
and a 1 init on a bit outside the DSP is kept instead of asserting.
- The release flow runs the oss-cad-suite yosys binary, so the fix ships as plugin `xilinx_dsp_init`: the
  unpatched xilinx_dsp.cc/.pmg + the patch, compiled with `#line 1 "xilinx_dsp.cc"` so every `$auto$xilinx_dsp.cc`
  name equals the stock pass's. The unpatched source built the same way gives an RTLIL identical to the built-in
  pass on bgm after map_dsp (checked).
- `ofx/defaults.py` option `dsp_init`: synth_xilinx's map_dsp step with `xilinx_dsp_init`.
- Repro cases (`flow/yosys_dsp_init_check.py --plugin`): rep and rep_p1 assert with stock, build with the plugin,
  5000-cycle random simulation 0 mismatches; rep2, rep_in1, rep_p1in yosys JSON identical to stock.
- Suite no-op (`install/synth_noop_suite.py dsp_init`): running.
Note: yosys output depends on the source path strings (hash order), so compare runs with the same paths only.

## 3. Power model

Refit `python3 flow/power_fit.py --run` on 2026-11-08 with the Vivado data that landed since 2026-11-06
(drcpow_b1: 14 more designs, incl. the held-out families rv_mul, fir, dsp, ramb36, oserdes_pin, srl, mmcme2):
- before (untracked): 41 designs, held-out n=2 (total 1.7 %), LOFO total 8.1 %.
- now: 55 designs, 45 train, 10 held out: held-out total 10.0 % mean abs (max 30.2 %), dynamic 37 % mean abs on
  designs with >= 10 mW; LOFO total 7.4 % (max 86.1 %).
- Worst: Block RAM on the rv_* CPUs (Vivado 0 W, model 7-58 mW: no enable activity in the model), DSPs on fir_p5.
Decision: ship it (b075540). `ofx power` cannot run without a model; ~10 % total error is printed in docs/power.md
and stored in the model (`heldout_error`, `lofo_error`).

## 4. GT/PCIe FASM defaults

docs/drafts/nextpnr-gt-unisim-defaults.{patch,md}, opt-in `-o gt-unisim-defaults`; `flow/gt_unisim_check.sh`:
pcie_bare and gtp_lbm from unfilled netlists give the workaround's `.frames` exactly; blinky FASM unchanged.

## 5. clkbuf_keep_buffer_inputs

Root cause: the plugin is clkbufmap.cc compiled as clkbufmap_gapfix.cc with the draft's extra lines, so its BUFG
is `$auto$clkbufmap_gapfix.cc:278:execute$N` instead of `$auto$clkbufmap.cc:268:execute$N`; nextpnr's hash order
follows the name. Fix (install/install.sh): each `NEW_ID` line of the plugin source gets a `#line` with the line of
the same call in the unpatched clkbufmap.cc and the file name clkbufmap.cc.
Evidence (`install/defaults_noop.py --candidates clkbuf_keep_buffer_inputs --plugins <new>`): blinky PASS, rv_soc
PASS (yosys JSON identical; before: names differed, bitstream differed); fixes bufio_iddr and oserdes PASS; bufr
fails with and without (hold stop, as in 0.1). Installer function tested in isolation (~/ofx-test/fixes/instgen:
generated sources equal the tested ones).
