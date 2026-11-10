# ofx: a project file and one command for the open 7-series flow

`bin/ofx` is a Vivado-like project flow on top of the scripts in `flow/`. It does not reimplement them: every step
calls the existing, verified script (`build_openxc7.py`, `build_pr_native.py`, `partial.py`, `region.py`,
`pr_check.py` through `build_pr_native.py`, `region2v.py`, byteman, openFPGALoader, `host/icap_load.ps1`).
The tools underneath are Yosys, nextpnr-xilinx (openXC7, and the patched builds for DFX), Project X-Ray and
openFPGALoader.

Everything that builds or touches hardware is a **dry run unless `--run`** is given. Nothing in this document was
run on hardware.

## Quickstart

```
bin/ofx boards                          # board presets
bin/ofx new arty-a7-35t myblinky        # skeleton: ofx.toml, src/, constraints/
cd myblinky
../bin/ofx build                        # dry run: prints every step
../bin/ofx build --run                  # yosys -> nextpnr -> fasm2frames -> xc7frames2bit
../bin/ofx report                       # utilisation, Fmax, bitstream
../bin/ofx timing [--paths N] [--hold]  # Vivado-style summary ([timing] in ofx.toml); exit 1 on a failing endpoint
../bin/ofx program                      # prints the openFPGALoader command
../bin/ofx program --run [--flash]      # programs SRAM (or SPI flash)
```

A part instead of a board also works (`ofx new xc7z020clg400-1 z`); the XDC then has no pins and ofx says so.
Five boards have presets (`ofx boards`): Arty A7-35T and A7-100T, Arty S7-50, Zybo Z7-20 (PL only) and Nexys Video.
Built offline so far: xc7a35t, xc7a100t, xc7s50, xc7z020 (PL) and xc7a200t (see Results 4).
`ofx device <part>` shows how a part maps to the prjxray-db family, the fabric and the chipdb.

`OFX_MAX_NEXTPNR=N` makes every nextpnr run wait until fewer than N nextpnr processes are running
(`ofx/npwait.sh`), for shared machines.

## Commands

| command | does | wraps |
|---|---|---|
| `ofx new <board\|part> [dir] [--dfx] [--partpins auto\|anchors]` | skeleton project; `--dfx` adds a partition with two RMs | |
| `ofx build [--run]` | synth, place and route, bitstream into `build/impl/` | `flow/build_openxc7.py` |
| `ofx report [--dfx]` | utilisation and Fmax from the nextpnr logs | |
| `ofx timing [--dfx] [--build DIR] [--paths N] [--hold] [--from G] [--to G]` | Vivado-style timing summary: check_timing, WNS/TNS/WHS/THS with endpoint counts, clock summary, intra- and inter-clock tables, exceptions, ignored and unconstrained paths, slack histograms, the N worst paths with every cell and net delay (see "Timing reports") | nextpnr `--report` JSON (`--report-paths`, docs/drafts/nextpnr-timing-report.patch) |
| `ofx program [--flash] [--board B] [--run]` | load the bitstream | openFPGALoader (oss-cad-suite) |
| `ofx boot [--qemu] [--sim] [--run]` | Zynq: U-Boot SPL `boot.bin` (ps7_init), FIT with the PL bitstream and the `[zynq]` app, SD image, OpenOCD JTAG script; `--qemu` boots it in QEMU, `--sim` replays the app's M_AXI_GP0 accesses on the PL (RTL and bitstream netlist) (see "Zynq-7000") | `flow/zynq_boot.py`, `flow/ps7init.py`, `flow/zynq_pl_sim.py`, `flow/zynq_app_trace.py` |
| `ofx ip clk --in MHz --out F[@phase][/duty%] ... [--primitive MMCM\|PLL\|auto] [--run]` | Clocking Wizard: MMCME2/PLLE2 parameters for the part's speed grade, Verilog with clk_wiz ports, XDC (see docs/ip.md) | `ofx/ip_clk.py` |
| `ofx ip fifo --width W --depth D [--impl ...] [--fwft] [flags] [--run]` | FIFO Generator: fabric or built-in FIFO with fifo_generator ports | `ofx/ip_fifo.py` |
| `ofx ip bram --type T --width W --depth D [--init f.coe] [--reg-a] [--run]` | Block Memory Generator: RAMB36E1/RAMB18E1 with INIT | `ofx/ip_bram.py` |
| `ofx ip gen [--run]` | generate every `[[ip.clk]]`, `[[ip.fifo]]`, `[[ip.bram]]` of ofx.toml into `build/ip/` (`ofx build` does it too) | `ofx/ip.py` |
| `ofx debug insert [--run]`, `ofx debug capture [--via sim\|jtag\|uart] [--trigger p=v] [--offset N] [--run]` | ILA: analyzer on MARK_DEBUG nets of the synthesized design over BSCANE2 JTAG; capture to VCD (`--via sim` simulates the whole design with Vivado's JTAG TAP model) | `ofx/debug.py`, `flow/dbg_capture.py`, LiteScope |
| `ofx dfx build [--rms ...] [--run]` | region DRC, the native DFX flow for every RM, pr_check, then one partial per ordered RM pair with `--simulate` and a `.check.json` | `flow/region.py --drc`, `flow/build_pr_native.py`, `flow/partial.py` |
| `ofx dfx partials [--force] [--run]` | only the partials step | `flow/partial.py` |
| `ofx dfx verify [--formal] [--no-region2v] [--run]` | region DRC, pr_check results, every safety record (sha256, region gate, clean simulated load), byteman applied to each base and compared with the original target, region2v on each full build and byteman result, optional decoupler proof | `flow/region.py`, byteman, `flow/region2v.py`, `flow/decoupler_prove.sh` |
| `ofx dfx load <partial> [--via icap\|jtag] [--port COMx] [--run]` | refuses a partial without a clean safety record, then sends it | `host/icap_load.ps1` (UART to ICAPE2) or the patched openFPGALoader `--partial` (`docs/drafts/openfpgaloader-partial.md`) |

`ofx dfx load --via icap` without `--run` calls `icap_load.ps1` without `-Run`, which is its own dry run.

Caching: each step is skipped when its output exists (the scripts' own caching). ofx stores a hash of all inputs
in `build/impl/.ofx-inputs.json` and `build/dfx/.ofx-inputs.json`; when it changes, that build directory is deleted
and rebuilt.

## Project file reference (`ofx.toml`)

```toml
[project]
name = "dfx100"
top = "dfx100"
board = "arty-a7-100t"
sources = ["src/dfx100.v"]
constraints = ["constraints/dfx100.xdc"]
seed = 1

[clocks]
clk = 10.0

[dfx]
partpins = "anchors"
rar = false
compress = false
decoupler = false

[[dfx.partition]]
name = "rp0"
inst = "u_rm"
region = "SLICE_X12Y100:SLICE_X15Y149"
ports = "rm/ports.json"
register = ["ready"]
rms = { xor = "rm/rm_core_xor.v", andn = "rm/rm_core_andn.v" }
```

`[project]`

| key | meaning |
|---|---|
| `name`, `top` | project name; top module |
| `board` | a preset in `boards/` (gives the part and the openFPGALoader board name) |
| `part` | full part, e.g. `xc7a100tcsg324-1`; overrides the board's part |
| `sources` | Verilog/SystemVerilog (`.v`, `.sv`) and VHDL (`.vhd`, `.vhdl`) files of the static design, relative to `ofx.toml` (VHDL: see the VHDL section) |
| `vhdl_std`, `vhdl_units`, `vhdl_generics` | VHDL options (see the VHDL section) |
| `constraints` | XDC files, concatenated in order |
| `seed` | nextpnr seed (default 1) |
| `seeds` | `"auto"` (default) or `"auto:N"`: place and route `seed` alone, and only when it misses timing (worst clock below its target) or fails, also seeds `seed`+1 .. `seed`+N-1 (N default 3) and keep the best; a number N: always place and route seeds `seed` .. `seed`+N-1; `1`: one seed, no `seeds/` directory. The seeds run in parallel (up to `OFX_SEED_JOBS`, default 4, at once) and the one with the best routed Fmax (worst clock relative to its target) is kept; the runs are in `build/impl/seeds/`, the choice in `seeds.json`. Best of 3 raised Vivado-timed Fmax by 2.8 % on average over rv_soc / bram / rv_big / rv_mul (exact placement import, every 3-of-6-seed subset), best of 4 by 3.7 %; each extra seed costs one more nextpnr run |
| `build_dir` | default `build` |

`[clocks]`: `port = period_ns`. A `create_clock` is added for a port that no XDC already constrains, and the
fastest clock sets nextpnr's `--freq` (default 100 MHz when `[clocks]` is absent).

`[timing]` (optional): `nextpnr = "build/nextpnr-build/timrep/nextpnr-himbaechel"` (a nextpnr with docs/drafts/nextpnr-timing-report.patch, path relative to the repository or absolute) and `report_paths = 10` (worst paths per clock pair and check written to `report.json`). Without it `ofx timing` only has the Fmax per clock and says so.

The part decides the rest (`flow/device.py`): family from the openXC7 parts inventory, device and fabric from
prjxray-db `mapping/parts.yaml` and `mapping/devices.yaml` (xc7a35t uses the xc7a50t fabric), and the chipdb
`chipdb-<fabric>.bin`. ofx passes them to every script as `OFX_PART`, `OFX_FAMILY`, `OFX_FABRIC`, `OFX_PART_NAME`
and `OFX_FREQ_MHZ`. Unset, every script keeps its old defaults (xc7a35tcsg324-1, artix7, xc7a50t, 100 MHz).

`[dfx]`

| key | meaning |
|---|---|
| `partpins` | `"auto"` (default): automatic partition pins, `build_pr_native.py` `main_auto`, variant `partpin2` (docs/phase14). `"anchors"`: anchor LUT shell, variant `router` (docs/phase8) |
| `variant` | override the nextpnr variant (a key of `build_pr_native.py` `variants`) |
| `rar` | partials with `--reset-after-reconfig` (refused unless the region covers whole clock-row columns) |
| `compress` | partials with `--compress` |
| `decoupler` | adds `designs/common/dfx_decoupler.v` to the static sources and runs its proof in `ofx dfx verify`, with the partition's port widths |
| `timing_allow_fail` | RMs built with `--timing-allow-fail` |
| `configs` | several partitions only: the configurations, e.g. `[["xor", "add"], ["andn", "add"]]` (default: all combinations) |

`[[dfx.partition]]`

| key | meaning |
|---|---|
| `name`, `inst` | partition name; instance path of the reconfigurable module in the static top |
| `module` | the RM's module name in the static design (default `rm_slot`) |
| `region` | site ranges, e.g. `SLICE_X12Y100:SLICE_X15Y149` or with `RAMB36_…`/`DSP48_…` ranges; checked with `region.py --drc` first. ofx refuses a region with 0 frames on the part's fabric (e.g. `SLICE_X12Y100:SLICE_X15Y149` on xc7z020, where `region.py --drc` alone reports `0 tiles, 0 frames` and passes) |
| `ports` | the RM port spec: a `ports.json` path or an inline table `{clk = "clk", inputs = [["a", 8]], outputs = [["y", 8]]}` |
| `rms` | `name = "file.v"` (or `.vhd`); each file defines `module rm_core` (VHDL: `entity rm_core`) with the spec's ports minus `clk` |
| `shell` | anchors mode only: a hand-written `rm_slot` shell instead of a generated one |
| `register` | auto mode: outputs registered by an unplaced FF of the module |
| `stub` | the blackbox `rm_slot` used in static synthesis; generated from `ports` if no source defines the module |
| `default_rms` | which RMs `ofx dfx build` builds (default: all) |

Several partitions need `partpins = "anchors"`, one port spec shared by all partitions and unique RM names
(this is what `build_pr_native.py` `main_multi` supports). `ofx dfx verify` then checks the region DRC, pr_check
and the safety records, but does not run byteman and region2v for them.

Limits that come from the wrapped tools:

- region2v simulates the RM interface of the RISC-V custom-instruction slot (`valid`, `funct`, `rs1`, `rs2` to `rd`,
  `ready`). For other interfaces use `ofx dfx verify --no-region2v`.
- `partpins = "auto"` and region2v on a fabric other than xc7a50t: the device parameter is applied
  (`region2v.CONFIG["fabric"]` follows `region.CONFIG`), and since 2026-11-06 their caches are per fabric
  (`build/region2v/<fabric>/`, see Results 4, fix 3).
- `ofx dfx verify` reports pr_check pairs with the greybox static build (`grey_s`, auto mode) as INFO, not PASS/FAIL:
  that build differs from the module builds in the region's HCLK clock-leaf word by design and is never loaded
  (docs/phase14-auto-partpins.md section 6).

## Release defaults (`[build]`, ofx 0.1)

`ofx build` uses the options below when the toolchain under `toolchain/openxc7` is an ofx release install
(`share/ofx/VERSION` exists, i.e. a checkout linked to an `install/install.sh` prefix with `install/link_repo.sh`).
With any other toolchain (e.g. the openXC7 nightly) it prints that the release defaults are off and runs the plain
flow exactly as before. The flow scripts themselves (`flow/build_openxc7.py`, `flow/build_pr_native.py`, ...) keep
their old defaults, so every recorded result stays reproducible; `ofx dfx` builds also keep the variants of
`build_pr_native.py` unchanged (see "Open problems").

Rule for 0.1: a draft is opt-in unless it has been checked to be a no-op where it must not change anything, and
with every option off the build is the plain flow (`.frames` identical to the builds made before the release). A
default is on only where that check exists (column "evidence"); the rest are opt-in until a regression run against
Vivado's timer (`flow/release_bench.py`, variants `rel_new` and `rel_qor*`) has been made.

| key | default | what it does | evidence for the default |
|---|---|---|---|
| `hardblock_timing` | `true` (0.1) | nextpnr `-o hardblock-timing`: DSP48E1, ICAPE2 and RAMB36E1 pins are timed (otherwise those paths are untimed) | off = no-op (noop_check); on: blinky `.frames` identical; on the qor designs every blind placement replayed under the honest timer is equal or slower than the hardblock-timing placement (rv_soc +12.9 %, rv_mul +1.7 %, rv_big +3.6 %, bram +10.0 %, fir -1.5 %, 3 seeds, nextpnr timer; `install/hardblock_regress.py`, docs/release-0.1.md) |
| `dsp_cascade` | `true` | nextpnr `-o dsp-cascade-place`: DSP48E1 PCOUT->PCIN chains placed along the chipdb cascade wires | on = `.frames` identical to off on designs without a long chain (Finding 9: 5 designs; release binary: blinky, rv_soc in `install/defaults_noop.py`); FIR places only with it |
| `dsp_pipeline` | `false` | yosys: `xilinx_dsp_qor -pipeline` (plugin) instead of synth_xilinx's `xilinx_dsp` | changes the netlist of every multiplier design; equivalence by random simulation only, and the FIR is slower in Vivado's P&R with it (215.75 -> 205.68 MHz, Finding 8) |
| `async_reg` | `true` | yosys: `xilinx_asyncreg -xdc <the project XDC>` (plugin) after flatten: ASYNC_REG flip-flops are kept as flip-flops | JSON identical to plain synth_xilinx on designs without ASYNC_REG (blinky, rv_soc in `install/defaults_noop.py`); x_async_* match Vivado (3 FDRE, no SRL) |
| `clkbuf_keep_buffer_inputs` | `false` | yosys: `clkbufmap_gapfix` instead of `clkbufmap` (BUFIO/BUFR inputs stay on the unbuffered clock) | not a no-op: rv_soc's netlist differs only in the inserted BUFG's `$auto$` name, which changes nextpnr's hash order and the bitstream; fixes bufio_iddr and oserdes; bufr then stops on a hold violation (`install/defaults_noop.py --candidates`, docs/release-0.1.md) |
| `carry_di_bypass` | `false` | nextpnr `-o carry-di-bypass` (release patch 0031): a CARRY4 DI comes in through the slice X pin (AX..DX) instead of a feed-through LUT, and the S LUT may be a LUT6, as in Vivado | off = no-op; on: `.frames` identical on fir (no carry chain; `install/defaults_noop.py`); slices -6 to -16 %; Fmax with the exact placement import (flow/exact_src.py, Vivado timer, 3 seeds, paired): rv_soc -3.6 %, bram +1.3 %, rv_mul -0.3 %, rv_big -1.3 % (mean -1.0 %), so opt-in. The earlier +1.7 % came from the placed mode, which drops nextpnr's feed-through LUTs and leaves the LUT-RAMs and LUT pins to Vivado (Finding 15, round 3) |
| `cell_timing` | `"stub"` | `auto`: the calibrated chipdb (`cal/chipdb-xc7a50t.bin`) for xc7a35t*-1 parts; `stub`: never | changes placement everywhere; Vivado's timer on the calibrated placements is better on 4 designs and worse on bram (155.09 -> 149.88), one seed each (Finding 10) |
| `placer` | `"auto"` | `auto`: `--placer static` at every size (0.1; was: up to 3000 cells, else heap); `static`, `heap` force one | upstream placer, no draft; Vivado's timer on the static placements is 3-34 % better than on heap placements on all 5 qor designs (Finding 7); LiteX DDR/eth SoCs equal within 2 % under Vivado's timer and HeAP does not route mc12_a100 (docs/wip/placement-global.md) |

All options off (`hardblock_timing`, `dsp_cascade`, `dsp_pipeline`, `async_reg`, `clkbuf_keep_buffer_inputs`, `carry_di_bypass` false,
`cell_timing = "stub"`, `placer = "heap"`) gives the plain flow: no yosys script change, no nextpnr argument and the
default chipdb (`install/defaults_noop.py` checks this).

Chipdb: the default `chipdb-<fabric>.bin` (identical to the openXC7 nightly's). The `ofx/` chipdb (with the XADC bel)
is used only when the yosys netlist has an XADC cell, because the extra bel changes placement of designs without one
(docs/install.md, "prjxray-db and nextpnr-xilinx-meta additions"); the calibrated chipdb only with
`cell_timing = "auto"`.

`ofx build` writes what it used to `build/impl/ofx_defaults.json` (options, yosys script, nextpnr arguments, the
placer and chipdb decisions). With `placer = "auto"`, or when the fabric has an XADC chipdb, it runs yosys first
(`build_openxc7.py --stop-after yosys`), reads the cell count and cell types of the top module, then runs the rest.
The options are part of the input hash, so changing one rebuilds.

Example, all QoR drafts on:

```toml
[build]
hardblock_timing = true
dsp_pipeline = true
cell_timing = "auto"
```

The XDC and primitive drafts in the release nextpnr (XDC timing commands, ASYNC_REG/IOB/I/O delays/exceptions,
DIFF_TERM, FIFO, XADC, BUFH, IO buffer parameters, MMCM/PLL ties and unused outputs, ICAPE2/DNA_PORT enables) have
no option: they are in the binary for every flow. ICAPE2 designs therefore need the release prjxray-db (installed in
the same prefix).

## Timing reports (`ofx timing`)

`ofx timing` prints a report in the layout of Vivado's `report_timing_summary` (ofx/timing.py). Its data is
nextpnr's `--report` JSON. The per-endpoint parts need nextpnr with docs/drafts/nextpnr-timing-report.patch and
`--report-paths N`; set `[timing] nextpnr` and `report_paths` in ofx.toml (variant `timrep`,
build/nextpnr-build/timrep). Without them `ofx timing` prints the Fmax lines as before and says what is missing.

```
ofx timing [--paths N] [--hold] [--from GLOB] [--to GLOB] [--list K] [--build DIR] [--dfx]
```

| section | what | Vivado counterpart |
|---|---|---|
| check_timing | `no_clock` (endpoints of a clock with no create_clock; nextpnr times them at the `--freq` default), `constant_clock` (clock pins on `$PACKER_VCC/GND`), `unconstrained_internal_endpoints`, `no_input_delay`, `no_output_delay` (top ports from the routed JSON, clock ports of the XDC excluded), `generated_clocks` (create_generated_clock warnings), `ignored_constraints` (every XDC line the reader accepted but did not apply), `unrelated_clocks` | check_timing items 1, 2, 4, 5, 6, 8; the last two are not in Vivado |
| Design Timing Summary | WNS, TNS, failing and total endpoints; WHS, THS, failing and total | the same (no pulse width) |
| Clock Summary | name (create_clock -name), waveform, period, frequency, master of a generated clock | Clock Summary |
| Intra / Inter Clock Table | the summary per capture clock and per launch -> capture pair | Intra / Inter Clock Table |
| Timing Exceptions | the summary per exception (set_max_delay, set_multicycle_path, ...) | in Vivado these paths stay in their clock tables |
| User Ignored Paths, Unconstrained Paths | endpoints per clock pair that a false path removes, or that have no launch/capture clock | the same tables |
| Slack histogram | worst slack per endpoint, setup (and hold with `--hold`) | report_design_analysis / the histogram in the GUI |
| Timing Details | the N worst setup (and hold) paths: source, destination, requirement, data path delay (logic/route), logic levels, every cell and net with incremental and cumulative delay and tile | report_timing -max_paths N |

- Endpoints are nextpnr cell pins (FF D/CE/SR, LUTRAM WE/WA/DI, BRAM and DSP pins), counted once with their worst
  slack, like Vivado's endpoint counts.
- `--from`/`--to` match start/end cells, `cell/pin` or clock names (glob). The endpoint tables honour `--to`; paths
  exist only for the N worst endpoints per clock pair that nextpnr wrote.
- Exit code 1 when an endpoint fails setup or hold.
- Paths on a clock with no create_clock (timed by nextpnr at the `--freq` default) are left out of Timing Details and
  counted in one line, as Vivado does not time them; they are in check_timing `no_clock` and Unconstrained Paths.
- DFX builds: `--dfx` reads the module builds. The DFX variants (partpin*, router) have no `--report-paths`, so by
  default they get the Fmax fallback. Opt-in: `flow/build_pr_native.py --variant rel01tr --report-paths N` uses
  build/nextpnr-build/rel01tr (the release head 86fe629a, i.e. install/patches/nextpnr 0001-0027, plus
  nextpnr-timing-report, which applies to it unchanged) and the release prjxray-db (build/prjxray-db-prim-xadc, needed
  for the ICAPE2 enable bits); then `ofx timing --build <out>/rel01tr` reports every module build. On rv_pr
  (xor, andn) the FASM and `.frames` of all 3 builds are identical between `rel01`, `rel01tr` and
  `rel01tr --report-paths 10`, and the report JSON is identical in all old keys (build/timing/dfx_rv_pr). Default
  (`--report-paths 0`) unchanged; `ofx dfx build` does not pass it yet.

Example (rv_soc at 5 ns, the qor netlist, `build/timing/rv_soc/ofx_timing.txt`, from
build/timing/rv_soc/timrep_paths/report.json):

```
check_timing
  1. checking no_clock (0)
  2. checking constant_clock (1): clock pins tied to a constant ($PACKER_VCC_NET)
  3. checking unconstrained_internal_endpoints (9)
  4. checking no_input_delay (1): uart_txd_in
  5. checking no_output_delay (5): led[0..3], uart_rxd_out
Design Timing Summary
      WNS(ns)     TNS(ns)  TNS Fail  TNS Tot      WHS(ns)     THS(ns)  THS Fail  THS Tot
     -2.097     -55.625       98     2268      0.398       0.000        0     2268
Unconstrained Paths
  (none)            sys_clk                   9  no launch clock
1. Slack (VIOLATED) : -2.097ns  (setup)
   Requirement:     5.000ns
   Data Path Delay: 6.997ns  (logic 2.204ns, route 4.793ns)
   Logic Levels:    10
     clk-to-q         0.350     0.350     X30Y101  $auto$ff.cc:337:slice$10792/Q
     routing          0.764     1.114      X24Y92  u_cpu.latched_branch
     ...
     setup            0.100     7.097      X17Y91  $auto$ff.cc:337:slice$11111/D
```

### Comparison with Vivado (2026-11-06)

The full comparison of the report format (check_timing items, pulse width, clock summary, path groups, CDC,
endpoint sets, ordering, histograms) on the same placement, and the remaining gaps, is in docs/timing-reports.md.
Since then hold and pulse width are always reported, and names are Vivado's cell/pin names.

`flow/timing_report_check.py --run` places and routes each netlist with the timrep nextpnr (and with xdc2 for the no-op
check) into build/timing/<design>/; `flow/timing_vivado_compare.py` reads ofx's numbers and Vivado's
`report_timing_summary` and writes build/timing/compare.json. The timers differ (docs/qor-vivado.md Findings 3 and
10), so slacks are not expected to agree; what is compared is the report structure and the endpoint counts.

**Vivado's own synthesis and P&R of the same RTL and XDC** (C:\Users\finnf\open-dfx-xc7-vivado\build\xdc\<d>\timing.rpt):

| design | check | ofx timing (nextpnr) | Vivado |
|---|---|---|---|
| x_gen_none (create_generated_clock missing) | check_timing no_clock / unconstrained_internal / no_input_delay / no_output_delay | 20 / 20 / 4 / 4 | 20 / 20 / 4 / 4 |
| | timed endpoints (setup, hold) | 1, 1 (clk only; the 20 clk_div endpoints are listed as unconstrained) | 1, 1 |
| x_mmcm_none (c1 100 MHz, c2 200 MHz from one MMCM) | intra c1 / intra c2 / inter c1 -> c2 endpoints | 16 / 4 / 4 | 16 / 4 / 4 |
| | failing endpoints, inter c1 -> c2 | 4 of 4, WNS -0.844 | 4 of 4, WNS -1.806 |
| | WHS inter c1 -> c2 | +1.320 | +0.311 |
| x_iodly (set_input/output_delay 7 ns) | no_input_delay / no_output_delay | 0 / 4 | 0 / 4 |
| | setup: WNS, failing / total | -7.824, 8 / 20 | -7.764, 8 / 20 |
| | hold: WHS, failing / total | +1.502, 0 / 20 | +0.999, 0 / 20 |

## Board presets (`boards/*.toml`)

| preset | part | pins |
|---|---|---|
| `arty-a7-35t` | xc7a35tcsg324-1 | verified: Digilent `Arty-A7-35-Master.xdc` (github.com/Digilent/digilent-xdc) and the existing designs |
| `arty-a7-100t` | xc7a100tcsg324-1 | verified: Digilent `Arty-A7-100-Master.xdc` ("Rev. D and Rev. E"), same pins as the 35T for clock, LEDs and UART |
| `arty-s7-50` | xc7s50csga324-1 | verified: Digilent `Arty-S7-50-Master.xdc` ("Arty S7-50 Rev. E"). Clock: the 12 MHz `CLK12MHZ` (F14, LVCMOS33); the 100 MHz `CLK100MHZ` (R2) is in the DDR3 bank with SSTL135 and is not used. LEDs E18 F13 E13 H15, UART V12 (in) / R12 (out) |
| `zybo-z7-20` | xc7z020clg400-1 | verified: Digilent `Zybo-Z7-Master.xdc` ("Zybo Z7 Rev. B", Z7-10 and Z7-20). PL only: `sysclk` K17 (125 MHz), LEDs M14 M15 G14 D18; no UART pins in Digilent's file |
| `nexys-video` | xc7a200tsbg484-1 | verified: Digilent `Nexys-Video-Master.xdc` ("Nexys Video Rev. A"). Clock R4 (LVCMOS33, 100 MHz); LEDs T14 T15 T16 U16 (led[0..3] of 8) with **LVCMOS25** as in Digilent's file (new preset key `led_iostandard`); UART V18 (in) / AA19 (out) |
| `nexys-a7-50t` | xc7a50tcsg324-1 | verified: Digilent `Nexys-A7-50T-Master.xdc`. Clock E3 (100 MHz); LEDs H17 K15 J13 N14 (LED[0..3] of 16); UART C4 (in) / D4 (out). Digilent's `board.xml` names the part xc7a50ti**csg324-1L** (industrial, -1L), which is not in the openXC7 parts inventory; the preset uses xc7a50tcsg324-1 (same die, IDCODE and package pins) |
| `basys3` | xc7a35tcpg236-1 | verified: Digilent `Basys-3-Master.xdc` ("Basys3 rev B"). Clock W5 (100 MHz); LEDs U16 E19 U19 V19 (led[0..3] of 16); UART `RsRx` B18 (in) / `RsTx` A18 (out) |
| `cmod-a7-35t` | xc7a35tcpg236-1 | verified: Digilent `Cmod-A7-Master.xdc` ("CmodA7 rev. B"). Clock `sysclk` L17 (12 MHz); led[0..1] = the two LEDs A17 C16, led[2..3] = the RGB LED's blue B17 and green B16; UART J17 (in) / J18 (out) |
| `arty-s7-25` | xc7s25csga324-1 | verified: Digilent `Arty-S7-25-Master.xdc` ("Arty S7-25 Rev. E"). Same pins as the Arty S7-50 (12 MHz F14, LEDs E18 F13 E13 H15, UART V12 / R12) |
| `cmod-s7-25` | xc7s25csga225-1 | verified: Digilent `Cmod-S7-25-Master.xdc` ("Cmod S7-25 Rev. B"). Clock `clk` M9 (12 MHz); LEDs E2 K1 J1 E1; UART `uart_rx` K15 (in) / `uart_tx` L12 (out) |
| `zybo-z7-10` | xc7z010clg400-1 | verified: Digilent `Zybo-Z7-Master.xdc` (the Z7-10 and Z7-20 share it). PL only, same pins as `zybo-z7-20` |
| `arty-z7-10` | xc7z010clg400-1 | verified: Digilent `Arty-Z7-10-Master.xdc` ("ARTY Z7-10 Rev.B"). PL only: clock H16 (125 MHz), LEDs R14 P14 N16 M14; no PL UART pins in Digilent's file |
| `cora-z7-07s` | xc7z007sclg400-1 | verified: Digilent `Cora-Z7-07S-Master.xdc` ("Cora Z7-07S Rev. B"). PL only: clock H16 (125 MHz); no single LEDs, so led[0..3] = `led0_b` L15, `led0_g` G17, `led0_r` N15, `led1_b` G14; no PL UART pins; no openFPGALoader board name (`ofx program` needs `--board` or a cable). xc7z007s is the xc7z010 die |

Each preset pin was checked by `build/ofx/devices/pincheck.py` (2026-11-06, `build/ofx/devices/pincheck.json`): the
`PACKAGE_PIN` in Digilent's master XDC carries the expected port (clock, LED index, UART direction) and the same
`IOSTANDARD` as the preset, the preset part equals the `board.xml` part (except `nexys-a7-50t`, see above), and the
`openfpgaloader_board` name is in `openFPGALoader --list-boards`. All 8 new presets pass. The digilent-xdc and
vivado-boards files were downloaded again from GitHub on 2026-11-06 (`build/ofx/ref/fresh_20261106/`) and are
byte-identical to the copies below.

The part of each new preset is the `part_name` in Digilent's vivado-boards `board.xml`
(`new/board_files/arty-s7-50/B.0`, `zybo-z7-20/A.0`, `nexys_video/A.0/1.2`, `nexys-a7-50t/D.0/1.3`, `basys3/C.0`,
`cmod_a7-35t/B.0`, `arty-s7-25/E.0`, `cmod-s7-25/B.0`, `zybo-z7-10/A.0`, `arty-z7-10/A.0`, `cora-z7-07s/B.0`). Digilent's files were read on
2026-11-06 (digilent-xdc master `c8644a9f`, vivado-boards master `d8d43ed9`). Copies, with `SHA256SUMS`, are in
`build/ofx/ref/` (not in git):

| file | sha256 |
|---|---|
| `Arty-S7-50-Master.xdc` | `26d472164373dff063f3cbdc3c10e958d1e8251d9e3b86776e5ab6889ba53ab5` |
| `Zybo-Z7-Master.xdc` | `63a843355f360ce2594cec40952c46fd9498002e0044a18a8b711ee1bdced478` |
| `Nexys-Video-Master.xdc` | `2debf0afb537c0a9f8f2c1569aa99e0366629a354f2fbdf369bd5142670086cc` |
| `board_arty-s7-50_B.0.xml` | `e015e1521707498225517b2d7ff3ecbb792577039106061d96250ac197e3b97a` |
| `board_zybo-z7-20_A.0.xml` | `650c4ca19979c156f059eee2b2f9a1862cbc1eb25927f2ab1d1904968ab342cc` |
| `board_nexys_video_A.0_1.2.xml` | `5fe56998aaae57825f28e999b1415126be8ce273030398d38678912af6f14a58` |
| `Nexys-A7-50T-Master.xdc` | `7c395ac9bb104fdbd805d805d8e3cf7f2b7674cd4aa02dcc511a64ad831677f4` |
| `Basys-3-Master.xdc` | `f6f289e967f1dab96349a8c7aaee9c7e9db1c0a5346848635ec2f056b922d89c` |
| `Cmod-A7-Master.xdc` | `56568df3868ef359e938ef8defab33e1814fe4153435e99e13da9260d9db4eaf` |
| `Arty-S7-25-Master.xdc` | `a2bdf7e355e21f179ac5789631de7e7ceda694d5efa87e8213704fdd8d4243c8` |
| `Cmod-S7-25-Master.xdc` | `212ad0209c3d61af8d07cc8d4ecb1147025691896404298b84ec82d965c956aa` |
| `Arty-Z7-10-Master.xdc` | `431481b25be07a87c83bf5950f1ec618b8a99b22c57e7bfa9795639e85e646d2` |
| `Cora-Z7-07S-Master.xdc` | `7d689e023461834428a4f3b2b803ac94c66efb8d6994947d583bc4f5095c6eb5` |
| `board_nexys-a7-50t_D.0_1.3.xml` | `6e16bf49652244953ddcf805594df0003df58c609cbf9c9af7b3a50595c1ebb0` |
| `board_basys3_C.0.xml` | `c97c8ee883ff02fa7d324e6e8eb29a2376632d5c8e429c1e1aa2ea774cd1ee7a` |
| `board_cmod_a7-35t_B.0.xml` | `0f8ead5f1161170374aa6f0777da82ed6c27eb132ee741dc966b390baa33aabb` |
| `board_arty-s7-25_E.0.xml` | `26602f194fcf847dbb74fb15e835d971de6f2c123fa8201dd644f3b71502db89` |
| `board_cmod-s7-25_B.0.xml` | `2af490267a34e052d9b98926b7bf6c0d9de2f11bbcaa2130d13604d1d5ee5490` |
| `board_zybo-z7-10_A.0.xml` | `42719beb0128dd3a4f36a997d31bdffbe92d93c1f3303957e62dc0a13f40fd25` |
| `board_arty-z7-10_A.0.xml` | `89a3b94370c8ecdc31bf9615b81c7929721342d53ce1dfcc401482fa66cbac28` |
| `board_cora-z7-07s_B.0.xml` | `590e97354f625e2fdd28ca4e033a110f0dbfb6ca0bf247dc9188e56f7af46247` |

Preset keys: `[board]` `name`, `part`, `openfpgaloader_board` (checked against `openFPGALoader --list-boards`:
`arty_s7_50`, `zybo_z7_20`, `nexysVideo`, `nexys_a7_50`, `basys3`, `cmoda7_35t`, `arty_s7_25`, `cmod_s7`,
`zybo_z7_10`, `arty_z7_10`), `iostandard`, `led_iostandard` (optional, default `iostandard`),
`pins_verified`, `pin_source`, `notes`; `[clock]`; `[leds]`; `[uart]`; `[dfx] example_region` (checked with
`region.py --drc` on the preset's fabric: 200 tiles, 72 frames each).

## Worked DFX example

See the results section below for the numbers of each run.

```
bin/ofx new arty-a7-100t examples/dfx100 --dfx --partpins anchors
cd examples/dfx100
../../bin/ofx dfx build            # dry run
../../bin/ofx dfx build --run      # static + 2 RMs + pr_check + 2 partials
../../bin/ofx dfx verify --run     # DRC, pr_check, records, byteman, region2v
../../bin/ofx report --dfx
../../bin/ofx dfx load rm_xor_from_andn            # dry run through icap_load.ps1
../../bin/ofx dfx load rm_xor_from_andn --via jtag  # dry run of openFPGALoader --partial
```

The static design drives the partition from an LFSR and an adder and folds `rd` onto the four LEDs.

## Results (2026-11-06, offline, all verified by run)

### 1. ofx reproduces the existing rv_pr native build
`examples/rv_pr/ofx.toml` declares rv_pr (static rv_soc, region `SLICE_X12Y100:SLICE_X15Y149`, the hand-written
anchor shell, RMs xor and andn). `ofx dfx build --run` (log `build/ofx/rv_pr_dfx_build.log`; outputs in
`examples/rv_pr/build/dfx/router/`), compared with the verified build `build/patched/rv_pr_native/router/`
(`build/ofx/rv_pr_proof.txt`):

- `.frames` identical (`cmp`) for xor_a, xor_n and andn_n;
- `static.prerouted`, `static.preplaced`, `pblock.xdc`, `replay.xdc`, `rm_shell_native.v` identical;
- partials `rm_xor_from_andn.bin` and `rm_andn_from_xor.bin` identical to `build/partials/rv_native/` (59,272 B);
- pr_check xor_n vs andn_n: 69 frames differ, all inside the region;
- Fmax 141.16 MHz for all three builds (`ofx timing --dfx`), the same as docs/phase8.

`ofx dfx verify --run` (`build/ofx/rv_pr_verify.log`): 10 PASS, 0 FAIL (region DRC, pr_check, 2 safety records,
byteman 0 frames differ from the original target ×2, region2v 3582/3582 vectors on 2 full builds and 2 byteman
results). Negative control: the xor build checked as andn through the same wrapper fails
(`examples/rv_pr/build/dfx/router/verify/neg_xor_as_andn.log`, exit 1, MISMATCH lines).

`ofx dfx load` refuses a partial with one flipped byte ("sha256 does not match the safety record") and one with no
record (`build/ofx/neg/`).

Dry runs of `ofx dfx build` for a two-partition project equal to rv2 and an auto-partpin project equal to rv_ppa
give the same step lists as `build_pr_native.py --design rv2` (47 steps) and `--design rv_ppa` (58 steps)
(`build/ofx/try/rv2/`, `build/ofx/try/ppa/`). Neither was built through ofx.

### 2. Second device: xc7a100t (Arty A7-100T)

| | result | evidence |
|---|---|---|
| blinky (`examples/blinky100`, `ofx build --run`) | 56 LUT, 28 FF, 7 CARRY4; 375.94 MHz at 100 MHz; 3,825,951 B; IDCODE 0x03631093 in the bitstream, equal to prjxray-db `xc7a100tcsg324-1/part.json`; byteman parses it (exit 0) | `build/ofx/blinky100_build.log`, `build/ofx/blinky100_bitparse.txt`, `build/ofx/blinky100_byteman.log` |
| DFX design (`examples/dfx100`, made by `ofx new arty-a7-100t --dfx --partpins anchors`) | region `SLICE_X12Y100:SLICE_X15Y149` on the xc7a100t fabric: DRC 0 split INT pairs, 200 tiles, 72 frames (columns 10/11 of top row 0) | `build/ofx/dfx100_build.log` |
| builds | static + xor/andn, 270 LUT, 140 FF, 11 CARRY4; Fmax 366.17 (xor_a), 365.23 (xor_n), 356.00 (andn_n) MHz | `ofx report --dfx`, `*/nextpnr.log` |
| pr_check xor_n vs andn_n | STATIC IDENTICAL OUTSIDE REGION, 63 frames differ, all inside | `checks/pr_check_xor_n_andn_n.log` |
| partials | 2 × 59,272 B, 72 region frames + 1 run-end static pad, CRC OK, simulated base + partial = target (0 frames differ, also with the last frame uncommitted); header part `7a100tcsg324`, IDCODE 0x03631093 | `partials/*.log`, `*.check.json` |
| `ofx dfx verify --run` | 10 PASS, 0 FAIL; byteman: 0 frames differ from the original target (144 frames byteman omits kept from the base, asserted equal); region2v PASS on 2 full builds and 2 byteman results | `build/ofx/dfx100_verify.log` |
| load / program | dry runs only (`icap_load.ps1` without `-Run`, openFPGALoader `--partial -b arty_a7_100t`) | `build/ofx/dfx100_load_dry.log` |

The dfx100 static design has no UART-to-ICAP bridge, so the ICAP loader is not usable with it on a board; JTAG
`--partial` is. Nothing ran on hardware.

### 3. The device parameter does not change existing results
After the `flow/device.py` changes (`build/ofx/regress/`):

- `DESIGNS="pr_uart rv_pr rv_b rv_c rv_flash" flow/make_partials.sh`: 24 OK, exit 0, all 24 `.bin` sha256 identical
  to before (`before/bins.txt`, `after/bins.txt`).
- `python3 flow/regen_check.py --run`: 48 identical, 0 differ, before and after, with identical hash lines.
- Dry runs of `flow/build_pr_native.py` for all 8 designs, with the original and the new core modules at the same
  moment: identical (`drycmp/`). A plain before/after comparison differed for rv_ppt only because another job was
  rebuilding rv_ppt in between.
- `flow/build_openxc7.py blinky --run`: `.frames` identical to `build/openxc7/blinky/xc7a35tcsg324-1_s1/`.

### 4. Spartan-7, Zynq-7000 PL and Artix-7 200T (2026-11-06)
Projects made with `ofx new <preset> [--dfx --partpins anchors|auto]` and built with `ofx build --run`,
`ofx dfx build --run` and `ofx dfx verify --run` (`OFX_MAX_NEXTPNR=2`). Logs in `build/ofx/devices/`; build outputs
under each `examples/<name>/build/`. Nothing ran on hardware.

**blinky** (`examples/blinky_s7`, `blinky_z7`, `blinky_nv`): 56 LUT, 28 FF, 7 CARRY4 on all three (as on xc7a100t).

| | Arty S7-50 (xc7s50csga324-1) | Zybo Z7-20 PL (xc7z020clg400-1) | Nexys Video (xc7a200tsbg484-1) |
|---|---|---|---|
| Fmax (nextpnr) | 391.54 MHz (target 12 MHz) | 391.54 MHz (target 125 MHz) | 372.58 MHz (target 100 MHz) |
| bitstream | 2,192,174 B | 4,045,726 B | 9,730,815 B |
| IDCODE in the bitstream = prjxray-db `part.json` | 0x0362F093 = 0x0362F093 | 0x03727093 = 0x03727093 | 0x03636093 = 0x03636093 |
| byteman round trip (`-o full`): frames byteman writes that differ / non-zero frames byteman omits | 0 / 0 | 1 / 24 (column `T r0 c73`) | 0 / 3 (column `B r0 c105`) |
| nextpnr peak RSS (`ofx build`) | 0.65 GB | 1.29 GB | 2.50 GB |
| evidence | `blinky_s7_build.log`, `blinky_s7.json`, `.bitparse.txt`, `.byteman.log` | `blinky_z7_*` | `blinky_nv_*` |

The byteman omissions are its device model, not the bitstreams: byteman writes only 1 frame for the right-hand IO
column of the row (42 in the prjxray-db bitstream). The same happens on the earlier xc7a100t blinky (12 non-zero
frames of `c57` omitted, `build/ofx/devices/blinky100.json`). `ofx dfx verify` handles this already (`_bmcmp.py`
keeps the frames byteman omits from the base and asserts that base and target agree there). The full bitstreams of
all three end with FAR 0x03BE0000, the value `partial.py` writes (`end_far`).

**DFX with anchors** (`examples/dfx_s7`, `dfx_z7`, `dfx_nv`; static LFSR + adder, RMs xor/andn, 2 RMs):

| | Arty S7-50 | Zybo Z7-20 PL | Nexys Video |
|---|---|---|---|
| region (preset `example_region`) | `SLICE_X12Y100:SLICE_X15Y149` (top row 1, columns 10/11) | `SLICE_X40Y50:SLICE_X43Y99` (bottom row 0, columns 28/29) | `SLICE_X12Y100:SLICE_X15Y149` (bottom row 0, columns 10/11) |
| region DRC | 0 split INT pairs, 200 tiles, 72 frames | same | same |
| builds (static + RM) | 270 LUT, 140 FF, 11 CARRY4 | same | same |
| Fmax xor_a / xor_n / andn_n | 366.17 / 343.29 / 342.23 MHz | 366.17 / 364.43 / 366.17 MHz | 366.17 / 363.24 / 332.23 MHz |
| pr_check xor_n vs andn_n | STATIC IDENTICAL OUTSIDE REGION, 64 frames, all inside | 66, all inside | 65, all inside |
| partials (×2) | 59,272 B, 72 region frames + 1 run-end pad, CRC OK, simulated base + partial = target (0 frames differ, also with the last frame uncommitted); header `7s50csga324`, IDCODE 0x0362F093 | same; `7z020clg400`, 0x03727093 | same; `7a200tsbg484`, 0x03636093 |
| `ofx dfx verify --run` | 10 PASS, 0 FAIL | 10 PASS, 0 FAIL | 10 PASS, 0 FAIL |
| byteman base + partial vs original target | 0 frames differ (113 omitted by byteman kept from the base) | 0 (1867) | 0 (205) |
| region2v | PASS 3582/3582 vectors on 2 full builds + 2 byteman results | same | same |
| `ofx dfx build` peak RSS | 0.72 GB | 1.33 GB | 2.64 GB |
| logs | `dfx_s7_build.log`, `dfx_s7_verify.log`, `summary_s7_z7.txt` | `dfx_z7_*` | `dfx_nv_*`, `summary_nv.txt` |

The verify results above were first computed with a shared region2v cache (fix 3 below) and were re-run after the
fix: `*_verify_fabcache.log`, same PASS/FAIL counts.

**DFX with automatic partition pins** (`examples/dfxpp_s7`, `dfxpp_z7`, `dfxpp_nv`, `--partpins auto`, variant `partpin2`):

| | Arty S7-50 | Zybo Z7-20 PL | Nexys Video |
|---|---|---|---|
| pins (`partpin_assign`) | 108 (75 in, 33 out) in 44 tiles, band rows 29..51, static distance mean 12.3 / max 26 tiles | 108 in 38 tiles, rows 76..99, mean 32.4 / max 96 | 108 in 42 tiles, rows 109..132, mean 16.8 / max 31 |
| greybox static routed to the pins | 75 + 33 nets, 692 pips locked | 877 pips | 736 pips |
| partpin_check (xor_n, andn_n) | 2 PASS: 108 nets, outside route == locked route | 2 PASS | 2 PASS |
| Fmax grey_s / xor_n / andn_n | 322.37 / 257.07 / 247.83 MHz | 366.17 / 191.31 / 171.35 MHz | 349.53 / 240.27 / 215.52 MHz |
| pr_check xor_n vs andn_n | STATIC IDENTICAL OUTSIDE REGION, 58 frames inside | same, 58 | same, 58 |
| partials (×2) | 59,272 B, CRC OK, simulated exact, IDCODE 0x0362F093 | same, 0x03727093 | same, 0x03636093 |
| `ofx dfx verify --run` | 10 PASS, 0 FAIL, 2 INFO (greybox pairs) | 10 PASS, 0 FAIL, 2 INFO | 10 PASS, 0 FAIL, 2 INFO |
| logs | `dfxpp_s7_verify_fabcache.log` | `dfxpp_z7_verify.log` | `dfxpp_nv_build_fabcache.log`, `dfxpp_nv_verify_fabcache.log` |

All in `build/ofx/devices/summary_auto.txt`. dfxpp_s7 rebuilt after fix 3 is byte-identical to the build before it
(pins, both `.frames`, both partials), because the xc7s50 and xc7a50t candidate caches for this region are equal.
dfxpp_nv only builds after fix 3. dfxpp_z7 was built before fix 3 from caches that the xc7z020 run had computed
itself (no other design uses that region), so it was not rebuilt.

**Fixes made for these devices** (all in ofx except fix 3; each with a no-op check on the existing designs):

1. `ofx dfx build`/`verify` refuse a region that has 0 frames on the part's fabric. `SLICE_X12Y100:SLICE_X15Y149`
   (the Arty example region) does not exist on xc7z020; `region.py --drc` printed `0 tiles, 0 frames` and exited 0,
   so the build would have gone on with an empty pblock (`build/ofx/devices/neg_empty_region_z7.log`: refused, exit 1).
2. `ofx dfx verify` counted the pr_check of the greybox static build (`grey_s`, auto mode) against each module as
   FAIL. Those pairs differ by design in the region's HCLK clock-leaf word (docs/phase14 section 6) and are now
   INFO (first seen on dfxpp_s7: `dfxpp_s7_verify.log` 10 PASS 2 FAIL, `dfxpp_s7_verify2.log` 10 PASS 0 FAIL 2 INFO).
3. **region2v, partpins and partpin_assign caches were keyed by the region string only.** `cand3_<region>.pkl`,
   `nodes_<region>.pkl` and `uf_<box>.pkl` under `build/region2v/` are computed from one fabric's tilegrid and
   tileconn, but reused for any fabric with the same region string. dfxpp_nv (xc7a200t) loaded the xc7a50t
   candidates of `SLICE_X12Y100:SLICE_X15Y149` and nextpnr stopped:
   `ERROR: Partition pin X31Y51/ER1END0 of net 'v' reaches no pblock that contains its routing`
   (`examples/dfxpp_nv/build/dfx_sharedcache_*/partpin2/grey_s/nextpnr.log`). Fix: `flow/region2v.py`
   `CONFIG["cache"]` is `build/region2v/<fabric>/` when the fabric is not the default xc7a50t (one line;
   `build/ofx/devices/noop_r2v/region2v_cache.patch`); `partpins.py` and `partpin_assign.py` derive their caches
   from it, so they follow. No-op: with no `OFX_*` variables and with `OFX_FABRIC=xc7a50t` the three cache paths are
   identical before and after (`noop_r2v/cfg_*`), and `ofx dfx verify --run` on rv_pr gives the same PASS/FAIL lines
   as `build/ofx/rv_pr_verify.log` (`noop_r2v/rv_pr_verify_after.log`).
   What it had affected: the xc7s50 graph for that region is equal to the xc7a50t one (compared after unpickling),
   so dfx_s7 was unaffected; the xc7a100t graph is not (40,447 vs 40,251 nodes: Y149 is the top edge of xc7a50t but
   not of xc7a100t), so the earlier region2v PASS of dfx100 and dfx_nv used a wrong graph. With the right graphs:
   dfx100 10 PASS 0 FAIL (`build/ofx/devices/dfx100_verify_fabcache.log`), dfx_nv 10 PASS 0 FAIL, dfx_s7 and dfx_z7 also 10 PASS 0 FAIL (`*_verify_fabcache.log`). Three files that the
   xc7z020 runs had written into the xc7a50t cache (region `SLICE_X40Y50:SLICE_X43Y99`) were moved to
   `build/ofx/devices/cache_quarantine_xc7z020/`.
4. Board presets: `led_iostandard` (Nexys Video LEDs are LVCMOS25); the XDCs written for the two Arty presets are
   unchanged (`ofx/cli.py` `xdc_from_board`, compared with `examples/blinky100/constraints/blinky100.xdc`).

No-op of the ofx changes: dry runs of `ofx build`, `ofx dfx build`, `ofx dfx verify` for blinky100, dfx100 and rv_pr
with the committed ofx (`git archive HEAD`) and the new one are identical, and no input stamp changed
(`build/ofx/devices/noop/*.old`, `*.new3`); `ofx dfx verify --run` on dfx100 gives the same lines as
`build/ofx/dfx100_verify.log` (`noop/dfx100_verify_run.log`).

### 5. All other parts, Kintex-7 and GTP (2026-11-06)
Status: the user asked to put Artix-7 first. Results for the other families are recorded as they stand.
Unfinished items are marked "deprioritised (user: Artix-7 first)".

Every blinky and DFX example was rebuilt from an empty `build/` (`build/ofx/devices/v3/drive3.sh`, `OFX_MAX_NEXTPNR=2`).
- Logs and tables: `build/ofx/devices/v3/` (`summary.py` prints the tables).
- Kintex-7 logs: `build/ofx/devices/k7/`.
- Nothing ran on hardware.

**Bitstream decode check** (new `flow/device_bitcheck.py <example>...`). For each build it runs two checks:
1. **Frames:** it parses the `.bit` and compares every frame with the `.frames` file that fasm2frames wrote. The ECC word is masked.
2. **Decode and re-encode:** it decodes the `.bit` back to FASM (prjxray `bit2fasm`), then encodes that FASM again with fasm2frames. The frames must be identical to the build's own.

If both pass, every set bit decodes to a known prjxray-db feature and nothing is lost on the way back. "Unknown-bit lines" is the count of `unknown` lines in the decoded FASM.

The decoded feature set never equals nextpnr's `.fasm` line for line, on any family. Each blinky shows about 215 lines that only nextpnr writes and 92-128 lines that only the decoder writes. These are aliases: pips without bits, `PRECYINIT` and BUFG input aliases written in a different form. The re-encode check shows they encode the same bits. Results are in `build/ofx/devices/bitcheck/<example>.json` and `summary1.txt`.

**blinky on every part with a chipdb** (56 LUT, 28 FF, 7 CARRY4 on each):

| example | part | IDCODE bit = prjxray-db | bitstream | Fmax (nextpnr) | frames check | decoded FASM re-encoded | unknown bits | byteman round trip (differ / omitted) | peak RSS |
|---|---|---|---|---|---|---|---|---|---|
| blinky_a50 | xc7a50tcsg324-1 | 0x0362C093 | 2,192,176 B | 391.54 MHz | match | 0 frames differ | 0 | 0 / 3 | 0.62 GB |
| blinky_b3 | xc7a35tcpg236-1 | 0x0362D093 | 2,192,174 B | 391.54 | match | 0 | 0 | 0 / 3 | 0.62 GB |
| blinky_cma7 | xc7a35tcpg236-1 | 0x0362D093 | 2,192,178 B | 372.58 | match | 0 | 0 | 0 / 0 | 0.62 GB |
| blinky_s25 | xc7s25csga324-1 | 0x037C4093 | 1,241,968 B | 372.58 | match | 0 | 0 | 0 / 0 | 0.39 GB |
| blinky_cms7 | xc7s25csga225-1 | 0x037C4093 | 1,241,970 B | 391.54 | match | 0 | 0 | 0 / 20 | 0.39 GB |
| blinky_s75 | xc7s75fgga484-1 | 0x037C8093 | 3,686,976 B | 391.54 | match | 0 | 0 | 0 / 0 | 1.22 GB |
| blinky_s100 | xc7s100fgga484-1 | 0x037C7093 | 3,686,979 B | 391.54 | match | 0 | 0 | 0 / 0 | 1.22 GB |
| blinky_z10 | xc7z010clg400-1 | 0x03722093 | 2,083,904 B | 372.58 | match | 0 | 0 | 1 / 26 | 0.39 GB |
| blinky_az10 | xc7z010clg400-1 | 0x03722093 | 2,083,906 B | 391.54 | match | 0 | 0 | 0 / 36 | 0.39 GB |
| blinky_cora | xc7z007sclg400-1 | 0x03723093 | 2,083,907 B | 391.54 | match | 0 | 0 | 0 / 20 | 0.39 GB |
| blinky_z030 | xc7z030sbg485-1 | 0x0372C093 | 5,980,082 B | 372.58 | match | 0 | 0 | 0 / 0 | 1.32 GB |
| blinky_z035 | xc7z035ffg676-1 | 0x03732093 | 13,321,570 B | 391.54 | match | 0 | 0 | 0 / 0 | 4.65 GB |
| blinky_z045 | xc7z045ffg900-1 | 0x03731093 | 13,321,570 B | 391.54 | not run (deprioritised) | | | 0 / 0 | 4.65 GB |
| blinky_z100 | xc7z100ffg900-1 | 0x03736093 | 17,416,514 B | 391.54 | not run (deprioritised) | | | 0 / 0 | 4.66 GB |
| blinky_k70t | xc7k70tfbg676-1 | 0x03647093 | 3,011,490 B | 399.04 | match | 0 | 0 | 0 / 0 | 0.75 GB |

Rebuild determinism: these blinkies were also built in an earlier, unverified run (`build/ofx/devices/v2/`).
- For the 12 parts in both runs (a50, b3, cma7, s25, cms7, s75, s100, z10, az10, cora, z030, z035), the `.frames` are byte-identical (`v2/*.after.sha` vs `v3/*.after.sha`).
- The `.bit` files differ only in the date in the header.

Notes on the parts:
- xc7s75 uses the xc7s100 fabric and xc7z035 uses the xc7z045 fabric, so they have the same frame counts. xc7z007s is the xc7z010 die.
- The byteman "omitted" frames come from its device model, as described in Results 4.

**DFX** (`ofx dfx build --run` + `ofx dfx verify --run`; static LFSR + adder; RMs xor/andn):

| example | part | verify | `ofx dfx build` peak RSS |
|---|---|---|---|
| dfx_a50, dfxpp_a50 | xc7a50tcsg324-1 | 10 PASS 0 FAIL; auto pins 10 PASS 0 FAIL 2 INFO (re-run 2026-11-06 20:4x, `v3/dfx_a50_verify.log`) | |
| dfx_b3 | xc7a35tcpg236-1 | 10 PASS 0 FAIL | 0.67 GB |
| dfx_cms7 | xc7s25csga225-1 | 10 PASS 0 FAIL | 0.35 GB |
| dfx_s75 | xc7s75fgga484-1 | 10 PASS 0 FAIL | 1.26 GB |
| dfxpp_s100 | xc7s100fgga484-1 | 10 PASS 0 FAIL 2 INFO | 1.27 GB |
| dfx_z035 | xc7z035ffg676-1 | 10 PASS 0 FAIL | 4.89 GB |
| dfxpp_cora | xc7z007sclg400-1 | 10 PASS 0 FAIL 2 INFO | 0.37 GB |
| dfxpp_z030 | xc7z030sbg485-1 | 10 PASS 0 FAIL 2 INFO | 1.35 GB |
| dfx_k70t | xc7k70tfbg676-1 | 10 PASS 0 FAIL | 0.77 GB |

Not re-run in this pass (deprioritised, user: Artix-7 first):
- dfx_s25, dfxpp_s25, dfx_z10, dfxpp_z10, dfx_cora, dfx_z030, dfx_s100, dfx_z045: 10 PASS 0 FAIL in the earlier unverified run (`v2/`, `drive_devices.out`).
- dfx_z100 and dfxpp_z045/z100: never verified.

**Kintex-7.** Two separate sources:
- **The installed openXC7 package (`upstream-2026-11-04`) has no kintex7 directory.**
- **openXC7's prjxray-db at the same revision (a8b09269) has one.** It has fabrics xc7k70t, xc7k160t, xc7k325t and xc7k480t (the xc7k420t parts map to the xc7k480t fabric), plus their parts. It also has the core segbits: CLB, INT, BRAM, DSP, IOB33/IOB18/IOI, clocking, CMT, CFG, GTX, PCIe.
  - A project-local sparse checkout is in `build/src/meta-openXC7-prjxray-db`, holding the xc7k70t and xc7k325t fabrics.
  - Tile types in the xc7k70t tilegrid that have config bits but no segbits: `GTX_INT_INTERFACE`, `HCLK_*_BOT_UTURN`, `LIOB33_SING`, `LIOI3_SING`, `RIOB18_SING`, `RIOI_SING`, `MONITOR_BOT_FUJI2`.
- `flow/device.py` now falls back to that checkout for families missing from the installed package:
  - new `extra_dbs` and `extra_chipdb_dirs`;
  - `db_root()` and the `OFX_DB_ROOT` variable, which bitparse and bit2fasm now use.
  - `ofx build` and `ofx dfx build` pass `--chipdb`/`--db-root` for such parts. `ofx/design.py` reads their package pins.
  - With an installed part nothing changes: `device.env()` is the same and `bitparse.DB` is the same path.
- **xc7k70t: works offline.**
  - The chipdb is generated with the stock nextpnr-xilinx generator and openXC7's kintex7 metadata (meta 8a3f5a0): 57 s, 2.4 GB peak, `build/chipdb/k7/chipdb-xc7k70t.bin`.
  - The generator reports 1918 of 31067 tile pips (6.17 %) "NOT expressible", against 6.04 % on xc7a50t.
  - `examples/blinky_k70t` builds with `ofx build`: 399 MHz, IDCODE 0x03647093 = prjxray-db, the decode check passes. Pins are HR bank 16 pins from the prjxray-db package file, not a board.
  - `examples/dfx_k70t` (region `SLICE_X12Y100:SLICE_X15Y149`, region DRC 0 split INT pairs, 200 tiles, 72 frames) gives verify 10 PASS 0 FAIL.
  - Partial headers say `7k70tfbg676` with IDCODE 0x03647093. region2v ran on the xc7k70t graph (`build/region2v/xc7k70t/`).
  - No Vivado cross-check is possible: the installed Vivado has no Kintex-7 part data. So the prjxray kintex7 bits themselves are unchecked against Vivado.
- **xc7k325t: not built, deprioritised (user: Artix-7 first).**
  - The chipdb generator was OOM-killed at 5.9 GB RSS while other jobs ran on this 12 GB machine.
  - A retry with an 8 GB cap was stopped by the change of priority.
  - `examples/blinky_k325t` exists (bank 12 HR pins, xc7k325tffg900-2) and is not built.
- **Virtex-7:** openXC7's prjxray-db has `virtex7` (xc7vx485t, the VC707 part), and nextpnr-xilinx ships VC707 examples. Not fetched or tried; deprioritised.

**Artix-7 dies.**
- prjxray-db (installed and openXC7) has only the xc7a50t, xc7a100t and xc7a200t fabrics, with parts xc7a35t/a50t/a100t/a200t.
- The openXC7 inventory has nothing more.
- **xc7a12t, xc7a15t, xc7a25t and xc7a75t have no part files in any prjxray-db, so no open build is possible today.**
  - xc7a15t and xc7a75t are the xc7a50t and xc7a100t dies, so they would need only `part.json`/`part.yaml`/`package_pins.csv` (IDCODE, packages). prjxray generates these from Vivado, which has Artix-7 data here.
  - xc7a12t and xc7a25t are a separate die and need a fuzzed fabric.
- The Vivado cross-check of the Artix-7 blinkies (a35t cpg236, a50t, a100t, a200t) and of `gtp_b3` is below, under "Vivado cross-check".

**GTP (transceivers).**
- Which of our parts have usable GT data (`build/ofx/devices/gt_survey.txt`):
  - **artix7:** GTP_CHANNEL_0..3 / GTP_COMMON segbits (with the xc7a200t MID_LEFT/RIGHT variants) and PCIE_BOT. The chipdbs have the GTPE2/IBUFDS_GTE2 site types. **Usable:** xc7a35t/a50t (cpg236: 2 lanes, csg325/fgg484: 4; csg324 bonds none), xc7a100t, xc7a200t.
  - **spartan7:** the xc7s25/xc7s50 tilegrids contain GTP tiles but the family has no segbits. Spartan-7 parts have no transceivers.
  - **zynq7:** the xc7z030/045/100 tilegrids have GTX tiles, but there are no zynq7 GT segbits or site metadata. **Not usable.**
  - **kintex7 (openXC7 db):** GTX_CHANNEL/COMMON segbits, and the generated xc7k70t chipdb has GTXE2 site types. Not built.
- **`examples/gtp_b3` builds** (xc7a35tcpg236-1, Basys 3 part, MGT pins from prjxray-db; the Basys 3 board does not wire the MGTs). It contains:
  - IBUFDS_GTE2 on MGTREFCLK0 (B8/A8);
  - GTPE2_COMMON PLL0;
  - GTPE2_CHANNEL 0 (TX D2/D1, RX B4/A4), 16-bit TX/RX, TXOUTCLK through a BUFG clocking a TX counter;
  - RX data folded into the LEDs.
  
  Results:
  - nextpnr places the COMMON at GTP_COMMON_X97Y127 and the channel at GTP_CHANNEL_0_X97Y110, and routes them. 464 MHz usrclk.
  - The FASM has 171 GTPE2_CHANNEL and 21 GTPE2_COMMON parameter lines.
  - The decode check passes: frames match, 135 non-zero frames, decoded FASM re-encodes to 0 differing frames, 0 unknown bits.
- **Bug found: nextpnr-xilinx's GT FASM writer does not use the UNISIM defaults.**
  - yosys writes only the parameters an instance sets. For every missing parameter, nextpnr's writer (`fasm.cc` `write_gtp_channel`/`write_gtp_pll`, and the same for GTX) uses its own default, mostly 0.
  - `build/ofx/devices/gt_defaults.py` compares those defaults with yosys `cells_xtra.v`:

    | primitive | defaults that differ from UNISIM | parameters never read |
    |---|---|---|
    | GTPE2_CHANNEL | 114 of the 227 parameters it reads | 15 |
    | GTPE2_COMMON | 4 of 24 (PLL0/1_FBDIV 1 vs 4, PLL0/1_FBDIV_45 4 vs 5) | 9 |
    | GTXE2_CHANNEL | 111 of 195 | 15 |
    | GTXE2_COMMON | 3 of 13 | 16 |

    Examples: CHAN_BOND_MAX_SKEW 0 vs 7, RX_DATA_WIDTH 0 vs 20, RX/TX_CLKMUX_EN 0 vs 1, PMA_RSV 0 vs 0x333.
  - **Impact:** a GTP instance that relies on defaults either stops with `ERROR: CHAN_BOND_MAX_SKEW may only range from 1 to 14, but is: 0` (the first gtp_b3 build), or gets wrong configuration bits silently.
  - **Workaround in the example:** `examples/gtp_b3/gt_params.py` writes every UNISIM parameter with its default, and the design carries the full lists. Not fixed in nextpnr, not reported upstream.
  - Nothing GT-related is timed, simulated or tried on silicon.

### Zynq-7000: PL, PS7 and booting the PS (2026-11-06)

ofx builds the Zynq **programmable logic (PL)**, including a design that instantiates the `PS7` cell, and makes
the files that boot the **processing system (PS)** from open sources. Nothing here has run on a board yet.

**PS7 in the PL flow.** The toolchain already has what is needed; no patch was required:

- yosys: `PS7` is a blackbox in `cells_xtra`. nextpnr-xilinx (openXC7 himbaechel): `pack_io.cc` maps it to the
  `PS7_PS7` bel, `pack_clocking.cc` places it on the one PS7 site, and `xilinx_place.cc` ties every unused PS7
  input to GND (except `TEST*`, `DEBUGSELECT*`, `MIO*`, `DDR*` and the `_PAD_` pins). prjxray-db `zynq7` has
  `site_type_PS7.json`, `ps7_ports.json` (690 ports), the `PSS0..4` tiles and `INT_INTERFACE_PSS_L`. The PSS tiles
  have no configuration bits: all their pips are pseudo-pips, so the PS-PL connection is set by ordinary INT pips.
- `examples/ps7_axi_z7` (Zybo Z7-20 preset): `PS7` with `FCLKCLK[0]` through a `BUFG` as the PL clock,
  `FCLKRESETN[0]` (two-flop synchroniser) as reset, and `M_AXI_GP0` connected to an AXI3 slave (`axi_regs.v`:
  LED, scratch, free-running counter, ID `0x0F5A7020` at `0x40000000 + 0x0/0x4/0x8/0xC`). The four LEDs show
  the LED register. `create_clock -period 20.000 [get_nets clk]` gives FCLK0's 50 MHz (IO PLL 1000 MHz / 5 / 4,
  from the board's `ps7_init`).
- Result (seed 1): 131 LUTs, 165 FFs, 9 CARRY4, 1 BUFGCTRL, 1 PS7; `clk` 285.63 MHz against the 50 MHz
  constraint; bitstream 4045728 bytes.

**PS configuration and boot files: `ofx boot`** (`flow/zynq_boot.py`, dry run unless `--run`). The board
preset's `[zynq]` section names the U-Boot device tree and `ps7_init_gpl.c`; the project's `[zynq]` section
names the bare-metal app:

```toml
[zynq]
app = ["sw/start.S", "sw/main.c"]
app_ld = "sw/link.ld"
```

| Vivado/Vitis step | open replacement used by `ofx boot` |
|---|---|
| ZYNQ7 IP + `ps7_init.c/.tcl` (MIO, PLLs, clocks, DDR, UART) | U-Boot v2025.10 `board/xilinx/zynq/zynq-zybo-z7/ps7_init_gpl.c` (GPL-2.0+; its header says it was generated by Vivado 2018.2 from Digilent's Zybo-Z7-20 board preset) |
| FSBL | U-Boot SPL (`xilinx_zynq_virt_defconfig`, device tree `zynq-zybo-z7`), built with arm-none-eabi-gcc 14.2 into `build/zynq/uboot` (cached on the U-Boot rev and the config fragment) |
| `bootgen` BOOT.bin | `spl/boot.bin` from U-Boot's `mkimage -T zynqimage`; the PL bitstream and the app go in a FIT (`ofx.itb`, `u-boot.img` on the SD card) that SPL loads: `fpga` image (`u-boot,fpga-legacy`, PCAP) then the app as `firmware` |
| `ps7_init.tcl` for XSDB (JTAG boot) | `ps7_init.tcl` for OpenOCD, generated from the same C tables by `flow/ps7init.py` |
| Vitis bare-metal app | `arm-none-eabi-gcc -mcpu=cortex-a9 -marm`, the project's linker script; the app must not overlap SPL's areas (checked) |

Outputs in `build/boot/`: `boot.bin` (copied path in `manifest.json`), `ofx.itb`, `sd.img` (64 MiB, MBR, one FAT32
partition with `boot.bin` and `u-boot.img`), `app.elf`, `pl.bin` (the `.bit` without its header), `ps7_init.tcl`,
`jtag_boot.tcl`, `manifest.json` (sha256 of each file, checks below).

Memory map used: app at `0x04000000` (link.ld), FPGA image loaded to `0x06000000`, FIT at `0x10000000`
(`CONFIG_SPL_LOAD_FIT_ADDRESS`); SPL's BSS (`0x100000-0x200000`) and stack/malloc (`0x200000-0x2200000`) are
refused as app locations.

**Boot paths** (not run on a board):

1. **SD card**: write `sd.img` to a card (or copy `boot.bin` and `u-boot.img` to its FAT partition), set the
   boot-mode jumper to SD. BootROM runs SPL, SPL runs `ps7_init`, loads `u-boot.img`, programs the PL through PCAP,
   runs `ps7_post_config` (level shifters on, FPGA resets released) and jumps to the app. UART1 (MIO 48/49, the
   USB-UART) at 115200 8N1 shows SPL's banner and the app's output.
2. **JTAG**: set the boot-mode jumper to JTAG, then
   `openocd -f interface/ftdi/digilent_jtag_smt2.cfg -f target/zynq_7000.cfg -f build/boot/jtag_boot.tcl`.
   The script halts the CPU, runs `ps7_init`, loads the `.bit` with OpenOCD's `pld load` (virtex2 driver on the
   PL TAP), runs `ps7_post_config`, loads `app.elf` and resumes at its entry. The interface file is the one
   OpenOCD's `digilent_zedboard.cfg` uses; that it matches the Zybo Z7's on-board FTDI JTAG was not checked.
   `ofx program --run` (openFPGALoader `-b zybo_z7_20`) loads the PL alone.

**Checked offline** (`ofx boot --qemu --sim --run`):

| check | result |
|---|---|
| `boot.bin` header (width word `0xAA995566`, `XNLX`, header checksum, SPL fits the 192 KiB OCM) | ok; SPL 119636 bytes at offset `0x8C0` |
| `ps7_init.tcl` against the C tables: the C file compiled with host gcc and a register-file mock of `ps7_config()`, the Tcl run in OpenOCD's own Jim Tcl with the same mock | identical: 209 table ops, 203 register writes, 5 polls, 1 delay |
| QEMU 10.2.1 `xilinx-zynq-a9`, `boot-mode=jtag`: `u-boot-spl.bin` at 0, `ofx.itb` at `0x10000000` | SPL banner, "Trying to boot from RAM", app banner, `FPGA0_CLK_CTRL = 0x00400500` (the value `ps7_init` writes) |
| QEMU, `boot-mode=sd`, `sd.img` on SD0 | SPL banner, "Trying to boot from MMC1", app runs from the FIT read off the FAT partition |
| app in Unicorn 2.1.4 (Cortex-A9) against a register model of `axi_regs`, `DEVCFG_INT_STS.PCFG_DONE` set | ID, scratch, LED read back, counter advances, `ofx-app: PASS`; the 10 M_AXI_GP0 accesses are written to `trace.hex` |
| `sim/tb_axi_regs.v` (the AXI slave alone: bursts, byte strobes, W before AW, B/R back-pressure) | 48 checks, 0 errors |
| PL RTL with a PS7 bus-functional model (`sim/ps7_bfm.v`, 620 ports from `ps7_ports.json`) replaying `trace.hex` (AW and W together, varying IDs) | 10 accesses, 34 checks (data, BID/RID, BRESP/RRESP, RLAST, LED pins), 0 errors |
| the same BFM against the netlist decoded from the bitstream (`bit2fasm` + fasm2bels, which instantiates `PS7` from the PSS site) | 10 accesses, 34 checks, 0 errors; the decoded netlist has the `PS7` instance (`FPGAIDLEN` tied to `1'b0` as nextpnr routed it), 0 orphan sinks. Negative control: one wrong expected ID word in the trace gives 1 error, FAIL |

The netlist step builds a fasm2bels connection database for xc7z020clg400-1 once (`build/b2n/`, about 3 min,
4.7 GB peak RSS); `ofx boot --sim` refuses to start it with less than 4 GB available.

QEMU limits: upstream QEMU has no DDR controller model, so `ps7_init`'s DCI poll at `0xF8000B74` times out
(about 15 s) and SPL continues without the peripheral table; QEMU's SLCR IDCODE reads 0, so SPL registers no FPGA
device ("Invalid device number 0", "Cannot load the image to the FPGA"); QEMU has no PL, so the app sees
`PCFG_DONE=0` and stops before touching M_AXI_GP0. The QEMU runs therefore check SPL, the FIT, both boot media and
the app's start-up, not the PCAP load or the AXI path; those are covered by the Unicorn trace and the simulations,
and on silicon only by a board test.

Not done: other Zynq boards (only the Zybo Z7-20 preset has `[zynq]`; Zybo Z7-10 would need its own `ps7_init`
check), S_AXI/HP/ACP ports, interrupts (IRQF2P), EMIO, more than one FCLK, Linux. Vivado cross-check of the PS7
design: not possible with the installed Vivado 2025.2. Its `data/parts/xilinx` has `artix7` as the only 7-series
family directory (no `zynq`, and `devint` data only for Artix-7), so it has no xc7z020 to implement the same design
on; `get_parts xc7z*` was not run because the shared Vivado was busy for the whole session.

## VHDL

`[project] sources` may contain `.vhd`/`.vhdl` files next to Verilog. ofx turns the VHDL into a Verilog netlist
before anything else runs (`ofx/vhdl.py`): yosys with the GHDL plugin (`plugin -i ghdl; ghdl --std=<std> <files>
-e <unit>; write_verilog`), output cached in `build/stage/vhdl/vhdl_<unit>_<hash>.v` (hash of the VHDL files, unit,
standard). That file then goes to `build_openxc7.py` or the DFX flow like any Verilog source, so no flow script
changed and the same synthesis (`synth_xilinx -flatten -abc9`) runs for VHDL and Verilog.

| key (`[project]`) | meaning |
|---|---|
| `vhdl_std` | `"08"` (default), `"93"`, `"93c"`, `"87"`, `"00"`, `"02"`: GHDL `--std` |
| `vhdl_units` | entities to elaborate. Default: the top if it is a VHDL entity, otherwise every VHDL entity that no other VHDL file instantiates |
| `vhdl_generics` | generics of the elaborated entities, e.g. `{ WIDTH = 20 }` (GHDL `-gWIDTH=20`; vhdl_blinky with it: 20 FDRE instead of 28) |

- All VHDL files of a project are analysed together in the order given (put packages first) into library `work`.
- Mixed designs work both ways: a VHDL architecture can instantiate a Verilog module through a `component`
  declaration (GHDL leaves it unbound, yosys binds it to the Verilog module; the generic map becomes the Verilog
  parameters: `W => 12` gives a 12-FDRE counter, `build/ofx/vhdl/vparam/`), and a Verilog module can instantiate a VHDL entity (it becomes a module of the converted file; a Verilog top
  with two `vhdl_blinky` instances synthesizes to 56 FDRE, `build/ofx/vhdl/vtop/`).
- A VHDL entity is elaborated once, with its default generics (or `vhdl_generics`): the converted module has no
  parameters, so a Verilog parent cannot set them (`#(.WIDTH(26))` gives `does not have a parameter named 'WIDTH'`),
  and two Verilog instances cannot use different generic values. Two VHDL roots that share an entity are refused
  (the module would be defined twice); give a single root in `vhdl_units`.
- GHDL lower-cases VHDL names: write `top` in lower case.
- DFX: VHDL works for the static sources and for RMs (`rms = { a = "rm/rm_core_a.vhd" }`, entity `rm_core`), through
  the same conversion (each RM file converted on its own; `examples/dfx_vhdl`). region2v's reference model for a
  VHDL RM is the converted Verilog, so it checks the bitstream against GHDL's reading of the VHDL, not against an
  independent VHDL simulator.
- Toolchain: GHDL and its yosys plugin come with oss-cad-suite (`toolchain/oss-cad-suite/bin/ghdl`, `GHDL 7.0.0-dev
  (6.0.0.r546.g71b3e1ac7)`, `share/yosys/plugins/ghdl.so`). An installer prefix built with `--yosys source` has no
  GHDL, so no VHDL.

### VHDL results (2026-11-06, offline, Arty A7-35T preset)
Logs in `build/ofx/vhdl/`.

| design | sources | yosys (open flow) | nextpnr | evidence |
|---|---|---|---|---|
| `examples/vhdl_blinky` | one VHDL-2008 entity (28-bit counter, generic width) | 28 FDRE, 7 CARRY4, 1 INV (the same cells as the Verilog blinky) | 56 SLICE_LUTX, 28 FF; 372.58 MHz at 100 MHz; 2,192,178 B | `vhdl_blinky_build.log`, `examples/vhdl_blinky/build/impl/` |
| `examples/vhdl_mixed` | VHDL-2008 top (record-typed FSM state, enumerated type) + VHDL package (CRC-32 and fold functions) + Verilog `prbs32` instantiated as a VHDL component | 95 FF (94 FDRE, 1 FDSE), 87 LUT (41 LUT2, 14 LUT3, 16 LUT4, 11 LUT5, 5 LUT6), 6 CARRY4, 1 DSP48E1 | 120 SLICE_LUTX, 95 FF; 344.12 MHz at 100 MHz; 2,192,176 B | `vhdl_mixed_build.log` |
| `examples/dfx_vhdl` | Verilog static (template), both RMs in VHDL | | static + RM 270 LUT, 140 FF, 11 CARRY4; 349.90 MHz all three builds; pr_check 64 frames, all inside; partials 2 × 59,272 B simulated exact; `ofx dfx verify --run` 10 PASS 0 FAIL | `build/ofx/devices/dfx_vhdl_*.log`, `summary_dfx_vhdl.txt` |

- The converted VHDL RMs are proven equivalent to the hand-written Verilog RMs of `examples/dfx100`
  (`equiv_make`/`equiv_simple`/`equiv_induct`, 33 of 33 `$equiv` cells proven, both RMs; `equiv/rm_*.log`).
- Conversion vs GHDL in the same yosys session as synthesis: vhdl_blinky gives the same cells; vhdl_mixed gives the
  same totals (87 LUT, 95 FF, 6 CARRY4, 1 DSP48E1) with a slightly different LUT-size mix (direct: 43/12/17/11/4 for
  LUT2..LUT6, converted: 41/14/16/11/5) (`vhdl_mixed_direct.log`, `vhdl_mixed_conv.log`).
- The first version of vhdl_mixed made yosys abort in `xilinx_dsp` (`log_assert` at xilinx_dsp.cc:400) with both
  routes. The same happens with plain Verilog: a register whose wire has a 1 init bit feeding a multiplier
  (`yosys_dsp_init_assert/rep.v` aborts, `rep2.v` with init 0 builds). The example's LFSR now starts from 0 with XNOR
  feedback. This is a yosys bug, not a VHDL one; not reported upstream.

**Same VHDL in Vivado** (v2025.2, one batch run for both designs: `read_vhdl -vhdl2008`, `read_verilog`, same XDC,
`synth_design`/`opt_design`/`place_design`/`route_design` at the 10 ns clock, xc7a35tcsg324-1; `vivado/build_vhdl.tcl`
through `vivado/run_qor.ps1 -Tag vhdl -Script build_vhdl.tcl -SrcRel build\ofx\vhdl_src`; reports copied to
`build/ofx/vhdl/vivado/`, log `vivado_20261106_075004.log`):

| | open flow: yosys cells | Vivado (`util.rpt`, primitives) | open flow: nextpnr timer | Vivado timer |
|---|---|---|---|---|
| vhdl_blinky | 28 FDRE, 7 CARRY4, 1 INV | 28 FDRE, 7 CARRY4, 1 LUT1 (1 Slice LUT) | 372.58 MHz | WNS +7.461 ns at 10 ns (393.9 MHz) |
| vhdl_mixed | 95 FF (94 FDRE, 1 FDSE), 87 LUT (41/14/16/11/5 for LUT2..LUT6), 6 CARRY4, 1 DSP48E1 | 95 FDRE, 103 LUT primitives (2/39/7/11/13/31 for LUT1..LUT6) in 90 Slice LUTs, 8 CARRY4, 1 DSP48E1 | 344.12 MHz | WNS +5.833 ns at 10 ns (240.0 MHz) |

- The two Fmax columns come from different timers on different placements, and both tools stop optimizing once the
  10 ns constraint is met, so they are not a QoR comparison. nextpnr's timer reads optimistic against Vivado's
  (docs/qor-vivado.md Finding 10); timing the open placement in Vivado was not done here.
- Both front ends read the same VHDL without errors. Vivado warned once that the FSM state register
  `ctrl_reg[state]` has no reset (`Synth 8-13157`); GHDL/yosys gave no such warning.

**Standards and features** (each a small design run through `ghdl --std=93` and `--std=08` + `synth_xilinx`,
`build/ofx/vhdl/probe/`, `summary.txt` and `*.msg`):

| feature | `--std=93` | `--std=08` |
|---|---|---|
| inferred block RAM (array signal, sync read); `attribute ASYNC_REG` on signals; component instantiation of a Xilinx primitive (BUFG) | ok | ok (1 RAMB18E1; the converted Verilog keeps `(* ASYNC_REG = "TRUE" *)` on both wires, `p_attr_conv.v`) |
| `process (all)`, conditional assignment in a process, `case ... generate`, `ieee.numeric_std_unsigned`, generic packages, `ieee.fixed_pkg`, `ieee.float_pkg` | fail (not VHDL-93) | ok (float32 adder: 79 CARRY4, 575 LUT) |
| matching operators `?=`, `??`, unary reduction `and v` | fail | ok |
| external names `<< signal u.t : std_logic >>` | fail | fail: `cannot use signal value during elaboration` (GHDL synthesis) |
| `library unisim; use unisim.vcomponents.all;` | fail | fail: `cannot find resource library "unisim"` |

- Default standard is VHDL-2008 (`vhdl_std = "08"`); Vivado's default for `.vhd` files is VHDL-93 and VHDL-2008 is
  opt-in per file. ofx applies one standard to all VHDL files of a project.
- **unisim**: there is no unisim library. Declare each primitive as a `component` in the architecture, with only the
  generics you set and no defaults: GHDL passes only those generics, and yosys's own models supply the rest. Tested:
  MMCME2_BASE + BUFG (`p_comp2.vhd`): the MMCME2_BASE cell carries exactly `CLKFBOUT_MULT_F`, `CLKIN1_PERIOD`,
  `CLKOUT0_DIVIDE_F`. A stub `vcomponents` package analysed into `--work=unisim` also works with the plugin
  (`unisim_stub.vhd`), but GHDL then passes every generic with the stub's default, so a stub must copy Xilinx's
  defaults exactly; ofx does not ship one.
- GHDL lower-cases VHDL identifiers (top module name, instance names in nextpnr reports, XDC object names).

## Device audit
Every hard-coded device reference in `flow/` and what was done with it:

| file | reference | now |
|---|---|---|
| `bitparse.py` | part, family | `device.get()`; `OFX_PART`/`OFX_FAMILY`, default unchanged |
| `region.py` | fabric xc7a50t | `device.get("fabric")` |
| `partial.py` | header part name `7a35tcsg324` | `device.part_name()` (from the part) |
| `build_openxc7.py` | part, family, 100 MHz | `device.get()`, `OFX_FREQ_MHZ`; new `--family` and `--freq`; the family is looked up for a `--part` other than the configured one |
| `bit2fasm.py`, `packer_pins.py` | part, family | `device.get()` |
| `bit2netlist.sh`, `icap_variant.sh` | `PART`, `FAMILY` defaults | fall back to `OFX_PART`/`OFX_FAMILY` |
| `build_pr_native.py` | chipdb-xc7a50t | `chipdb-{device.get('fabric')}` (the device-param patch, applied in commit a718368); ofx also sets the chipdb in-process |
| `region2v.py` (and `partpins.py`, `partpin_assign.py` through it) | fabric xc7a50t; caches keyed by region only | `region.CONFIG["fabric"]` (commit a718368); cache root `build/region2v/<fabric>/` for fabrics other than xc7a50t (2026-11-06, Results 4 fix 3) |
| `b2n_multi.sh` | `conn_xc7a35tcsg324-1.db` | unchanged (fasm2bels connection database is built per part) |
| `xvc_trace.py` | simulated TAP with the xc7a35t IDCODE | unchanged (a test fixture) |
| `gap_*.py`, `qor_*.py`, `gap_patch_eval.py` | xc7a50t paths | unchanged (Vivado comparison research scripts) |
| `partial.py` `end_far` 0x03BE0000 | | unchanged: the xc7a100t, xc7s50, xc7z020 and xc7a200t full bitstreams from openXC7 write the same FAR |
| `host/icap_load.ps1` | IDCODE 0x0362D093 | unchanged; used only by the `-ReadIdcode` diagnostic |

## Open problems
- Nothing has run on hardware, on any device.
- Zynq-7000: PS7 + M_AXI_GP0 + FCLK0 and the PS boot files (SPL, FIT, SD image, JTAG script) are built and
  checked offline on the Zybo Z7-20 preset only; nothing booted on a board. QEMU cannot check the PCAP load or
  the AXI path. Other PS7 ports (S_AXI, HP, ACP, IRQ, EMIO) untested; partial loading on a Zynq board untested.
- byteman's device model writes 1 frame for the right-hand IO column of some rows (xc7a100t c57, xc7z020 c73,
  xc7a200t c105, xc7s50 c43 and T r1 c37), so a byteman `-o full` of a design with IOs there loses their
  configuration; `ofx dfx verify` compensates (`_bmcmp.py`), a plain byteman round trip does not.
- Built per family (Results 4 and 5): every part with an installed chipdb (xc7a35t/a50t/a100t/a200t, xc7s25/s50/s75/s100,
  xc7z007s/z010/z020/z030/z035/z045/z100) and xc7k70t from openXC7's kintex7 prjxray-db. Not possible: xc7a12t/a15t/a25t/a75t
  (no prjxray part files). Deprioritised (user: Artix-7 first): xc7k325t (chipdb generation needs > 6 GB), Virtex-7.
- nextpnr-xilinx's GT FASM writer uses its own defaults (mostly 0) for GT parameters missing from the netlist instead of
  the UNISIM defaults (Results 5, GTP); a GT design must set every parameter.
- region2v's simulation vectors are tied to the custom-instruction slot interface.
- VHDL: no `library unisim`; no external names; the GHDL/yosys path does not report what Vivado's VHDL front end
  would warn about. VHDL designs larger than the examples untested.
- ofx uses the in-repo `toolchain/` paths; it does not yet read the installer's prefix (`install/`, `~/.local/ofx`).
