# SystemVerilog front end: yosys read_verilog -sv vs yosys-slang vs Vivado

Roadmap row "Verilog / SystemVerilog". Question: how much real SystemVerilog does the open flow's front end accept,
compared with Vivado synthesis, and is yosys-slang the practical fix?

## Tools
- yosys built-in parser: `read_verilog -sv`, yosys 0.70+186 (toolchain/oss-cad-suite, the flow's yosys).
- yosys-slang: the `slang` plugin already shipped in the same oss-cad-suite (`share/yosys/plugins/slang.so`,
  slang 12.0.0+545f88b2e; licence in `license/LICENSE.yosys-slang-plugin`). Nothing had to be built: `plugin -i slang;
  read_slang ...` works with the flow's yosys as it is. synlig was not tried (yosys-slang covers the need, see below).
- Vivado 2025.2: `synth_design -rtl` (RTL elaboration) for sv-tests, full `synth_design -mode out_of_context` for
  the cores (vivado/svtests_elab.tcl, vivado/sv_core_synth.tcl).

## sv-tests (chipsalliance/sv-tests 3969249, 2026-11-06)
`flow/svtests_run.py` follows sv-tests' own rules (tools/runner, runners Yosys.py and yosys_slang.py):
- tests whose `:type:` includes `elaboration`, minus `:unsynthesizable: 1` tests: 622 tests (607 LRM chapter/generic
  tests plus 15 generated real-core tests);
- each front end runs the sv-tests elaboration script (`hierarchy`, `proc`, `check`, `memory_dff`, `memory_collect`,
  `stat`); yosys-slang gets the sv-tests runner's flags (`--ignore-timing --ignore-initial --ignore-assertions
  --single-unit --timescale=1ns/1ns`, `-Wno-error=` for out-of-range index warnings, the per-core defines);
- pass = (exit code != 0) == should_fail; exit >= 126 (crash) or a timeout fails.
- The core tests were generated with sv-tests' generators (ariane/cva6, black-parrot, scr1, rsd, tnoc, fx68k) from
  the pinned submodules. Ariane/rsd/scr1 were rerun with yosys-slang one at a time with a 3600 s timeout (the sv-tests
  timeouts, 100-360 s, are shorter than the elaboration takes on this shared machine; cva6 64-bit takes 525-747 s).
- Results: build/svtests/results.json; `python3 flow/svtests_run.py report`.

| group | tests | yosys read_verilog -sv | yosys-slang | Vivado 2025.2 synth_design -rtl |
|---|---|---|---|---|
| generic | 139 | 72/139 | 139/139 | pending |
| sanity.sv | 1 | 1/1 | 1/1 | pending |
| chapter-5 | 46 | 35/46 | 46/46 | pending |
| chapter-6 | 71 | 27/71 | 58/71 | pending |
| chapter-7 | 73 | 31/73 | 72/73 | pending |
| chapter-8 | 9 | 2/9 | 8/9 | pending |
| chapter-9 | 19 | 14/19 | 18/19 | pending |
| chapter-10 | 10 | 7/10 | 8/10 | pending |
| chapter-11 | 84 | 62/84 | 84/84 | pending |
| chapter-12 | 25 | 11/25 | 20/25 | pending |
| chapter-13 | 11 | 3/11 | 11/11 | pending |
| chapter-15 | 2 | 0/2 | 2/2 | pending |
| chapter-16 | 16 | 3/16 | 16/16 | pending |
| chapter-18 | 46 | 8/46 | 46/46 | pending |
| chapter-20 | 32 | 10/32 | 32/32 | pending |
| chapter-21 | 11 | 0/11 | 11/11 | pending |
| chapter-22 | 6 | 4/6 | 6/6 | pending |
| chapter-23 | 3 | 2/3 | 3/3 | pending |
| chapter-25 | 1 | 0/1 | 1/1 | pending |
| chapter-26 | 2 | 0/2 | 2/2 | pending |
| core: ariane/cva6 | 5 | 0/5 | 3/5 | pending |
| core: black-parrot | 6 | 0/6 | 0/6 | pending |
| core: fx68k | 1 | 0/1 | 1/1 | pending |
| core: rsd | 1 | 0/1 | 1/1 | pending |
| core: scr1 | 1 | 0/1 | 0/1 | pending |
| core: tnoc | 1 | 0/1 | 1/1 | pending |
| **total** | 622 | **292/622 (47 %)** | **590/622 (95 %)** | pending |

### What the built-in parser fails on (330 tests; first error per test, grouped)
- 102 syntax errors at an identifier (`unexpected TOK_ID`; constructs the grammar does not know, e.g. 10.6.2
  `force`/`release`; not broken down further).
- 36 + 28 + 12 + 12 + 9 + 9 + ... other syntax errors: `let`, bit-selects on concatenations, tagged unions,
  `type(...)`/`$bits(type)`, streaming operators `{<<{}}`/`{>>{}}`, string localparams, `assert final`,
  `interface class`, `vectored`/`scalared`, enum ranges `name[N]`, `foreach` in synthesizable code.
- 18 "Invalid nesting of always blocks and/or initializations" (automatic tasks/functions with locals).
- 11 "Only PACKED supported at this time" (unpacked structs, arrays of structs).
- 10 `break`/`continue`, 7 `$itor`/format characters, 4 non-constant ranges (queues, associative arrays), unpacked
  array slices, recursive functions, `repeat` with a variable count.
- 12 should-fail tests it accepts (it does not detect illegal procedural assignments).
- Every real core fails in its first files (first error each): ibex `ibex_pkg.sv:322` named assignment pattern
  `'{field: value}`; cva6 `SyncDpRam.sv:76` `void'(...)` cast (`unexpected TOK_VOID`); rsd `BasicTypes.sv:6`
  `import` (`unexpected TOK_IMPORT`); scr1 `scr1_hdu.svh:22` `$clog2` of a non-constant (package parameter);
  tnoc `tbcm_counter.sv:28` `unexpected '.'`; fx68k `fx68k.sv:48` "Only PACKED supported"; black-parrot
  `bsg_wormhole_router_pkg.sv:4` `unexpected '['` (typedef in a package).

### What yosys-slang fails on (32 tests)
- chapter tests (23): `force`/`release` and `assign`/`deassign` (unsupported language feature), unpacked unions and
  union pattern matching in `case`/`casex`/`casez`/`if`/`?:` (6), string methods `len/getc/compare/icompare/ato*` (8), `@(edge)`
  (needs `--allow-dual-edge-ff`), the `interconnect` net type ("Feature unimplemented"), `vectored`/`scalared` (plugin
  assertion "unreachable"), one class `extends` test (yosys `count_id` assertion), and 2 should-fail tests it accepts
  (mixed/multiple continuous+procedural assignments to a variable).
- cores (9): black-parrot 6/6 ("expected a declaration name" in basejump_stl `bsg_mem_1rw_sync_mask_write_bit_synth.sv:108`;
  sv-tests' own yosys-slang runner skips all black-parrot tests), cva6 32-bit (slang rejects a reversed part-select
  `[31:34]` in `cva6_mmu.sv:400` as an error, `-Wrange-select-reversed`), the cva6 testbench (duplicate module `lzc`
  in the file list), scr1 (plugin assertion `branch_updates.empty() || finished`, statements.h:421, after 1752 s).

## Real cores through synthesis (synth_xilinx, out of context)
`flow/sv_core_synth.sh <name> <top> <filelist> <incdirs>` runs both front ends, then `synth_xilinx -flatten -abc9
-arch xc7 -noiopad`. Logs in build/svcores/<name>/.

### lowRISC ibex (626034d, 2026-11-06), top `ibex_top`, default parameters
File list: what slang resolves for `ibex_top` with `-y` over vendor/lowrisc_ip prim and prim_generic
(build/svcores/ibex/files.f, 63 files, packages first).
- built-in parser: fails at once, `ibex_pkg.sv:322: syntax error, unexpected ':'` (named assignment pattern).
- yosys-slang: fails on one construct, `ibex_top.sv:659: reading net state during design initialization
  unsupported`: a variable declaration with an initializer that reads signals
  (`logic unused_scramble_inputs = scramble_key_valid_i & ...;`). `--ignore-initial` does not cover declaration
  initializers. In SystemVerilog this is an initial value, not a continuous assignment; the signal is a lint sink
  ("unused_*") and drives nothing.
- With that one declaration split into `logic x; assign x = ...;` (build/svcores/ibex/patched/ibex_top.sv, the only
  edit), yosys-slang elaborates and synthesizes ibex_top in 23.5 s / 365 MB: 4444 LUTs (6/492/729/881/1523/813 for
  LUT1..LUT6), 1963 FFs (1670 FDCE, 10 FDPE, 283 FDRE), 83 CARRY4, 18 MUXF7, 6 MUXF8, 1 DSP48E1.
- Vivado OOC synthesis of the original and the patched file list: pending (vivado/sv_core_synth.tcl).
- The yosys-slang netlist was not simulated or checked for equivalence.

## yosys-slang in the build flow
`flow/build_openxc7.py --frontend slang [--slang-arg=...]` replaces `read_verilog -sv` with `plugin -i slang;
read_slang -DSYNTHESIS --top <top>` (default stays `builtin`; versions.json records the front end). Checked on
examples/axi_xbar (build/axi_xbar/slang):
- plain Verilog that the plugin rejects: verilog-axi's `axi_crossbar_addr.v:285` has `initial begin
  thread_count_reg[n] <= 0; end` (a non-blocking assignment in an initial block): "non-blocking assignments
  unsupported in design initialization". The built-in parser and Vivado take it. With `--slang-arg=--ignore-initial`
  (initial blocks dropped; the register is reset synchronously and powers up at 0 anyway) it builds.
- netlist: 1454 LUTs (0/340/424/232/214/244 for LUT1..LUT6), 1254 FFs, 103 CARRY4, 4 RAMB36E1, 1 SRL16E (built-in
  front end: 1476 LUTs, 1258 FFs, 95 CARRY4); nextpnr 152.42 MHz (built-in: 152.63).
- gate-level simulation of the slang netlist with the same LED testbench: PASS.
- Not yet: an `ofx.toml` key for the front end (ofx/cli.py passes no `--frontend`), include directories.

## The xilinx_dsp log_assert (roadmap row)
`build/ofx/vhdl/yosys_dsp_init_assert/rep.v` (a multiplier input register whose wire has a 1 init bit), re-run
2026-11-06:
- yosys 0.70+186 (flow) and 0.70+201 (~/oss-cad-suite): abort, `xilinx_dsp.cc:400` assertion.
- yosys-slang front end + the same yosys: the same abort (the bug is in the `xilinx_dsp` pass, not in the parser).
- the draft fix build (build/yosys-build/yosys-dspinit/yosys, docs/drafts/yosys-xilinx-dsp-init): passes.
- Upstream yosys source in upstream/YosysHQ_yosys (3718f7f13, 2026-10-20) still has the assertion at lines 400 and
  587. Status unchanged: fixed only by the draft, not in any shipped yosys.

## Files
- flow/svtests_run.py, vivado/svtests_elab.tcl (sv-tests, three front ends)
- flow/sv_core_synth.sh, vivado/sv_core_synth.tcl (cores)
- flow/build_openxc7.py `--frontend slang`
- upstream/chipsalliance_sv-tests (with the core submodules), upstream/lowRISC_ibex (clones, not committed)
- build/svtests/, build/svcores/
