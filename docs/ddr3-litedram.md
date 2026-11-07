# DDR3 on the Arty A7-35T with LiteDRAM through the open flow

Date: 2026-11-06. **No hardware was used.** Every number below comes from a run whose log is named next to it.
Timer labels: "nextpnr" = nextpnr's own timer, "Vivado" = Vivado 2025.2's signoff timer. They are different models, so
no cell mixes them.

## Summary
- LiteX/LiteDRAM's stock Arty A7 SoC (VexRiscv, LiteX BIOS with SDRAM init, read leveling and memtest, UART, LiteDRAM
  DDR3 controller, A7DDRPHY) is generated as Verilog and goes **synth → pnr → fasm → bitstream** with our flow. This
  works with the **stock nightly openXC7 flow too**: no fix was needed to build it. The gapfix build (G1/G3/G8 + clkbufmap
  plugin) gives the same placement and routing; the only FASM difference is the G1 DSP fix in the CPU's multiplier.
- Bitstream decode against Vivado's build of the same Verilog: all DDR pad settings (SSTL135, DIFF_SSTL135, IN_TERM
  UNTUNED_SPLIT_40, SLEW FAST, VREF 0.675 V, STEPDOWN) and every IDELAYE2 setting are identical. The IOI clocking
  partition (which of the 167 SERDES clock pins share a clock net) is identical. The remaining differences are explained
  below: inverters absorbed differently, a known unused-OCLK default, PLL/BUFG site choice and Vivado's unused-counter
  defaults.
- Timing: nextpnr says sys_clk 111.04 MHz (107.72 MHz with the hard-block timing option). Vivado's timer on nextpnr's
  placement (Vivado routing) says **WNS -1.584 ns at 10 ns (about 86.3 MHz)**. Vivado's own build of the same RTL meets
  100 MHz (WNS +0.574 ns). nextpnr does not time OSERDES/ISERDES at all (prjxray-db has no data for them); Vivado's timer
  gives those paths positive slack in every run. An 80 MHz build (DDR3 at 320 MHz) meets all constraints in
  Vivado's timer on nextpnr's placement (WNS +0.607 ns at 12.5 ns).
- Simulation: LiteDRAM's unit tests pass (175 run, 1 skipped); LiteX's own litex_sim (VexRiscv + BIOS + LiteDRAM
  controller + SDRAMPHYModel) prints "Memtest OK". A PHY-level xsim run (A7DDRPHY with Vivado's unisim/secureip models
  and a small behavioural DDR3 model written here) verifies the write path. The read path levels and passes a 24-burst
  check only when the model returns data at least 6.25 ns (2.5 tCK) later than an ideal CL-6 device; with 0-5 ns
  extra it finds no window. The cause is open (simulation models or PHY RTL, see "Open problems"); it is not our flow, since
  both bitstreams implement the same PHY.
- Upstream LiteX's Arty target still says "with --toolchain=yosys+nextpnr: DDR3 should be disabled"
  (litex_boards/targets/digilent_arty.py, header comment). That note predates this result. Whether it works on a board is
  untested.

## Sources and versions
| item | version / commit | source |
|---|---|---|
| migen | 4c2ae8dfeea37f235b52acb8166f12acaaae4f7c (the pin in litex/litex_repos.py; migen HEAD e19524c9 breaks LiteDRAM's BIST tests, see below) | github.com/m-labs/migen |
| litex | 9187839f2d275352ef6f0d7ab14431e2a66b8f81 | github.com/enjoy-digital/litex |
| litedram | f2d22975d67229676e10308ae6e71b819b6afe42 | github.com/enjoy-digital/litedram |
| litex-boards | 791258c669220cedfe5c79d67fe1db43e3de4f78 | github.com/litex-hub/litex-boards |
| liteeth, litespi, liteiclink, litepcie | in toolchain/litex/COMMITS.txt | github.com/enjoy-digital, litex-hub |
| pythondata-cpu-vexriscv, -software-picolibc, -software-compiler_rt, -misc-tapcfg | in toolchain/litex/COMMITS.txt | github.com/litex-hub |
| RISC-V GCC (BIOS) | gcc-riscv64-unknown-elf 14.2.0+19, binutils-riscv64-unknown-elf 2.45.50.20251209-1ubuntu1+7build1 | Ubuntu 26.04 archive, `apt-get download` + `dpkg-deb -x` (no root); sha256 in toolchain/litex/dl/deb/SHA256SUMS |
| libevent-dev, libjson-c-dev (litex_sim only) | Ubuntu 26.04 archive | toolchain/litex/sysroot, sha256 in toolchain/litex/dl/deb-sim/SHA256SUMS |
| Digilent master XDC | digilent-xdc c8644a9f, Arty-A7-35-Master.xdc | github.com/Digilent/digilent-xdc |
| Digilent MIG pinout | vivado-boards d8d43ed9, new/board_files/arty-a7-35/E.0/1.1/mig.prj | github.com/Digilent/vivado-boards |

Everything is in `toolchain/litex/` (venv: Python 3.12 from toolchain/buildenv; `pip freeze` in
toolchain/litex/pip-freeze.txt). LiteX's own installer would use `sudo apt install gcc-riscv64-unknown-elf`; the
packages were unpacked locally instead, nothing system-wide was changed.

The board part: litex-boards uses xc7a35ticsg324-1L (the chip on the Arty A7-35T); both flows here build for
xc7a35tcsg324-1 as in the rest of the project. Same die and package; Vivado's timing for -1L may differ slightly.

## Pins
The Digilent master XDC has no DDR pins; Digilent publishes them in the MIG project of its board files.
`flow/ddr_pins_check.py` compares every LOC and IOSTANDARD in the generated XDC with mig.prj (48 DDR pins) and the
master XDC (clk100 E3, reset C2, UART D10/A9, LEDs, eth_ref_clk): **57 ports checked, 0 mismatches, all 48 MIG pins
present** (build/ddr3/pins_check.json). IN_TERM and SLEW come from LiteX's platform file (litex_boards/platforms/
digilent_arty.py lines 106-134: DQ/DQS `IN_TERM=UNTUNED_SPLIT_40`, `SLEW=FAST`); mig.prj leaves those fields empty.

## Design and build
- Generated by `flow/ddr_build.py` (CONFIG block, DRY_RUN default, cached):
  `python3 -m litex_boards.targets.digilent_arty --toolchain vivado --variant a7-35 --sys-clk-freq 100e6 --build
  --no-compile-gateware` into build/ddr3/gen/arty_ddr3 (log build/ddr3/gen_arty_ddr3.log). This writes the Verilog,
  the Vivado XDC and compiles the BIOS into the ROM init file.
- Staged into designs/ddr3/arty_ddr3/: digilent_arty.v, VexRiscv.v, *.init, digilent_arty.xdc (LiteX's Vivado XDC,
  used by Vivado) and nextpnr/digilent_arty.xdc (the same file without set_false_path, set_max_delay, set_clock_groups
  and INTERNAL_VREF, which nextpnr cannot use). **The same Verilog goes to both flows.**
- Clocks: one PLLE2_ADV (VCO 1600 MHz) makes sys 100 MHz, sys4x 400 MHz, sys4x_dqs 400 MHz at 90°, idelay 200 MHz and
  eth 25 MHz. The PHY uses only BUFG clocks: 45 OSERDESE2, 16 ISERDESE2, 16 IDELAYE2, 1 IDELAYCTRL, 16 IOBUF,
  2 IOBUFDS (DQS), 1 OBUFDS (CK). No BUFIO, BUFR, BUFH or ODELAYE2 (A7DDRPHY is built `with_odelay=False`).
- Variants (`--variant`): `gapfix` (G1/G3/G8 nextpnr + clkbufmap plugin, docs/drafts/README.md), `stock` (nightly
  yosys + nextpnr), `qorfix` (gapfix + `-o hardblock-timing`, docs/qor-vivado.md). nextpnr gets `--timing-allow-fail`
  and `--freq 100`; it derives the PLL output constraints itself from the 10 ns clk100 constraint (nextpnr.log
  "Derived frequency constraint").
- Vivado: `vivado/run_ddr3.ps1 -Run` runs the unchanged vivado/build_gap.tcl (synth, opt, place, route, bitstream;
  default directives) on designs/ddr3/<name>. Outputs C:\Users\finnf\open-dfx-xc7-vivado\build\ddr3\, copied to
  build/ddr3/arty_ddr3/viv_ddr3/ by flow/ddr_compare.py.

| flow | synth | pnr | fasm | bitstream | seconds (synth + pnr + fasm + bit) | log |
|---|---|---|---|---|---|---|
| gapfix | ok | ok | ok | ok | 33.83 + 80.19 + 8.84 + 0.11 | build/ddr3/arty_ddr3/gapfix/status.json |
| stock | ok | ok | ok | ok | 33.14 + 79.42 + 8.49 + 0.11 | build/ddr3/arty_ddr3/stock/status.json |
| qorfix | ok | ok | ok | ok | 35.26 + 88.84 + 9.36 + 0.06 | build/ddr3/arty_ddr3/qorfix/status.json |
| Vivado | ok | ok | | ok | 134.27 + 18.36 (opt) + 28.61 (place) + 36.91 (route) + 17.65 | build/ddr3/arty_ddr3/viv_ddr3/times.txt |

Runtimes are indicative only (machine shared with four other agents).

gapfix vs stock: the yosys JSON differs only in clkbufmap cell names; FASM differs in 21 lines, all in the four
DSP48E1 tiles (MASK[47:46], AREG_1/BREG_1: the G1 draft). Placement and routing are otherwise identical.

Utilisation (gapfix nextpnr.log and yosys_stat.txt; Vivado util.rpt):

| | yosys / nextpnr | Vivado |
|---|---|---|
| LUTs | 5141 LUT + 313 INV (yosys); 7368 SLICE_LUTX (nextpnr, incl. route-throughs) | 4340 (4198 logic, 142 memory) |
| FF | 3741 | 3677 |
| CARRY4 | 255 (nextpnr 266) | 178 |
| LUTRAM | 80 cells | 142 LUTs |
| BRAM | 37 RAMB18E1 + 3 RAMB36E1 | 23.5 tiles |
| DSP48E1 | 4 | 4 |
| PHY | 45 OSERDESE2, 16 ISERDESE2, 16 IDELAYE2, 1 IDELAYCTRL, 1 PLLE2_ADV, 6 BUFGCTRL | same |

## What had to be fixed
Nothing to make it build. The cases listed in the brief do not occur or already work:
- BUFH / BUFIO / BUFR: not used by A7DDRPHY (BUFG clocking only).
- ISERDESE2 constant pins: LiteDRAM leaves OCLK/SHIFTIN unconnected and ties only CE1=1, BITSLIP=0; the stock build
  routes them (G3 not needed here).
- IDELAYCTRL: one instance with no LOC. prjxray-db has no IDELAYCTRL configuration bits; the only trace in the
  bitstream is its REFCLK pip, which both flows set in HCLK_IOI3_X113Y26 (the DDR bank's), from a different leaf clock
  index. (Vivado's Place 30-578 failure in docs/gap-vivado.md did not occur here.)
- SSTL135, DIFF_SSTL135, IN_TERM, VREF: nextpnr's fasm.cc writes them, and they decode identically to Vivado's
  (table below). nextpnr ignores `INTERNAL_VREF` from the XDC (xdc.cc: "INTERNAL_VREF isn't supported, ignoring") but
  writes VREF.V_675_MV for any bank with SSTL inputs, which is what this XDC asks for. A different VREF would be silently
  wrong.
- One setup fix: **migen must be LiteX's pinned commit 4c2ae8df.** With migen HEAD (e19524c9, "specials: memory: add
  read_capable option") 47 of LiteDRAM's BIST unit tests fail in migen's simulator (`AttributeError: 'NoneType' object
  has no attribute 'eq'`), and the generated Verilog gains unused `wrport_dat_r` wires. ddr_build.py refuses to generate
  with another migen.

New draft: docs/drafts/prjxray-db-ioi-serdes-timing.md (prjxray-db has no ISERDESE2/OSERDESE2 timing; see Timing).

## Bitstream comparison with Vivado (same Verilog)
`flow/ddr_compare.py --variant gapfix` decodes both .bit files with flow/bit2fasm.py (via gap_report.decode), canonicalises
them and diffs the IO, clocking and hard-block tiles (INT/CLB routing excluded). Output:
build/ddr3/arty_ddr3/cmp_gapfix.txt and cmp_gapfix_vs_ddr3/fasm_compare.json. Unknown bits: 0 in both.
The DDR pins are LOC'd, so IOB and IOI tiles are compared at the same coordinates ("exact").

| group | common | Vivado only | openXC7 only | what the difference is |
|---|---|---|---|---|
| IOB (all) | 328 | 8 | 0 | all 8 in LIOB33_X0Y43 (PUDC_B/EMCCLK pair; gap G13). **DDR bank IOBs: no difference.** |
| IOI site features | 275 by type | 4 | 34 | see below |
| IOI clock pips | | 167 | 167 | leaf-clock index choice only; partition identical (below) |
| IDELAYE2 | 193 lines | 0 | 0 | identical at the same sites (16 used: DELAY_SRC_IDATAIN, HIGH_PERFORMANCE_MODE, IDELAY_TYPE_VARIABLE, IN_USE; ZIDELAY_VALUE and IDELAY_TYPE_FIXED defaults on the rest) |
| HCLK_IOI3 | 7 | 10 pips | 10 pips | VREF.V_675_MV, STEPDOWN and BUFR_DIVIDE.BYPASS identical; pips = leaf choice |
| PLLE2_ADV (by type) | 56 | 3 | 0 | CLKOUT5 HIGH/LOW/NO_COUNT on the unused output (G13). Placed in different CMTs (Vivado X106Y44 next to bank 34, openXC7 X106Y96 next to clk100's bank 35) |
| BUFGCTRL (by type) | config identical | | | 6 BUFGs each; different BUFG sites and GCLK indices |

Common DDR-bank IOB features (both flows, by type): SSTL135.DRIVE.I_FIXED and SSTL135_SSTL15.SLEW.FAST on 48 outputs,
SSTL135_SSTL15.IN on 16 inputs, IN_TERM.UNTUNED_SPLIT_40 on 20 sites (16 DQ + both halves of 2 DQS), LVDS_25_SSTL135_
SSTL15.IN_DIFF on the DQS pairs, OUT_DIFF on 3 pairs (2 DQS, CK), STEPDOWN, VREF.V_675_MV.

IOI site differences, each checked against the yosys netlist (build/ddr3/arty_ddr3/gapfix/digilent_arty.json):
- `OLOGIC.ZINV_T1` set by openXC7 on 18 sites (16 DQ + 2 DQS). LiteDRAM drives OSERDES T1 with `~oe`; yosys keeps the
  inverter as an INV cell (18 OSERDES have T1 driven by INV), nextpnr implements it in fabric and leaves the OLOGIC T1
  inverter off (ZINV set = not inverted). Vivado folds the inverter into the OLOGIC (ZINV clear). Same function.
- `ILOGIC.IFF.ZINV_OCLK` set by openXC7 on the 16 DQ ISERDES. OCLK is unconnected in the netlist. Known G13 item
  (iserdes_min in docs/gap-vivado.md); harmless only if an unused OCLK inverter has no effect, unverified on silicon.
- `OLOGIC.IS_D1/3/5/7_INVERTED` set by Vivado on the CK OSERDES. LiteDRAM feeds the constant pattern 0,1,0,1,...
  Vivado ties the D pins to one constant and inverts the odd ones; openXC7 routes GND/VCC per pin (INT routing, outside
  this diff). Same pattern.

IOI clocking: for each SERDES clock pin (OCLK, OCLKM, CLKDIV, ILOGIC CLK/CLKB) the leaf GCLK is resolved through the
HCLK_IOI3 `LEAF_GCLK_{TOP,BOT}n -> IGCLKm` pips of the same bitstream, and pins on the same IGCLK form one class.
Result: **167 clock pins, partition identical, 0 mismatches**; 3 classes in both flows (4 = DQS OCLK/OCLKM on
sys4x_dqs, 45 = CLKDIV on sys, 118 = OCLK/OCLKM/ILOGIC CLK/CLKB on sys4x).

## Timing
| run | timer | sys_clk (10 ns) | idelay_clk (5 ns) | hold | PHY fabric↔SERDES/IDELAY paths | log |
|---|---|---|---|---|---|---|
| openXC7 gapfix | nextpnr | 111.04 MHz, PASS | 404.20 MHz | not checked by nextpnr | not timed | build/ddr3/arty_ddr3/gapfix/nextpnr.log |
| openXC7 stock | nextpnr | 111.04 MHz, PASS | 404.20 MHz | not checked | not timed | build/ddr3/arty_ddr3/stock/nextpnr.log |
| openXC7 qorfix (`-o hardblock-timing`) | nextpnr | 107.72 MHz, PASS | 378.36 MHz | not checked | not timed | build/ddr3/arty_ddr3/qorfix/nextpnr.log |
| Vivado, own synth + P&R | Vivado | WNS +0.574 ns (106.09 MHz) | WNS +1.223 ns | WHS +0.036 ns | worst +1.911 ns (OSERDES RST) | build/ddr3/arty_ddr3/viv_ddr3/timing.rpt, worst_paths.txt |
| Vivado P&R of the yosys netlist ("free") | Vivado | WNS +0.418 ns (104.36 MHz) | WNS +1.418 ns | WHS +0.022 ns | worst +1.977 ns (OSERDES D6) | build/ddr3/xtime/out/arty_ddr3_gapfix_free/ |
| nextpnr placement, Vivado routing ("placed") | Vivado | **WNS -1.584 ns, 465 failing endpoints (86.33 MHz)** | WNS +1.474 ns | WHS +0.011 ns | worst +0.585 ns (OSERDES D6) | build/ddr3/xtime/out/arty_ddr3_gapfix_placed/ |
| 80 MHz build, nextpnr placement, Vivado routing | Vivado | WNS +0.607 ns at 12.5 ns, 0 failing (84.08 MHz) | WNS +1.513 ns | WHS +0.046 ns | worst +2.957 ns (OSERDES D5) | build/ddr3/xtime/out/arty_ddr3_s80_gapfix_placed/ |
| 80 MHz build | nextpnr | 101.00 MHz, PASS at 80 MHz | 394.01 MHz | not checked | not timed | build/ddr3/arty_ddr3_s80/gapfix/nextpnr.log |

- sys4x / sys4x_dqs have no timed paths in either tool other than pulse width (Vivado WPWS +0.345 ns): all their loads
  are SERDES CLK pins. The sys → OSERDES D/T and ISERDES Q → sys paths are the PHY's real timing interface.
- nextpnr times none of the SERDES pins: the chipdb has no timing for them and prjxray-db's IOI SDF files have no
  ISERDESE2/OSERDESE2 cells (draft issue docs/drafts/prjxray-db-ioi-serdes-timing.md). Vivado's timer finds those paths
  positive in all three Vivado-timed runs.
- "placed" uses flow/ddr_xtime.py + vivado/build_xtime.tcl (the QoR agent's method, docs/qor-vivado.md Finding 3):
  9455 cells keep nextpnr's site and BEL, 997 nextpnr-made cells (route-through LUTs, duplicated carry selects) are left to
  Vivado (place_missed.txt). Vivado routes. So this is Vivado's timer on nextpnr's placement, not on our bitstream.
- On nextpnr's own critical path (RegFilePlugin_regFile ADDRARDADDR6) nextpnr reports 9.006 ns; Vivado's timer on the
  same placement reports slack -1.051 ns, path 10.344 ns (paths_vivado.txt). nextpnr's timer is optimistic here, as the
  QoR study found for other designs. The failing paths are VexRiscv and LiteDRAM controller logic, not the PHY.
- CDC: Vivado gets LiteX's set_false_path/set_max_delay/set_clock_groups; nextpnr cannot read them and reports the
  sys_clk → clk100 domain crossing as an unconstrained cross-domain path (nextpnr.log).

80 MHz variant (arty_ddr3_s80: same pins, PLL VCO 1600 MHz /20 = 80 MHz sys, /5 = 320 MHz sys4x, CL 6 / CWL 5 in the
generated init sequence): synth/pnr/fasm/bitstream ok (33.86 + 64.78 + 9.45 + 0.11 s,
build/ddr3/arty_ddr3_s80/gapfix/status.json). nextpnr: sys_clk 101.00 MHz, PASS at 80 MHz; idelay_clk 394.01 MHz.
Vivado's timer on its placement (9550 cells from nextpnr, Vivado routing): **all constraints met**, sys_clk WNS +0.607 ns at 12.5 ns, WHS +0.046 ns, worst PHY path +2.957 ns (build/ddr3/xtime/out/arty_ddr3_s80_gapfix_placed/timing.rpt). It is the bitstream to try first on the board if the 100 MHz one misbehaves.

## Simulation
1. LiteDRAM unit tests (controller, bank machine, multiplexer, refresh, crossbar, wishbone, DFII, BIST, init, modules,
   timing, A7/K7 PHY settings): **175 run, OK, 1 skipped** (build/ddr3/sim/litedram_unittest.log). With migen HEAD:
   47 errors, all the BIST memory-port error above.
2. LiteX simulation, `flow/ddr_sim.sh` (`litex_sim --cpu-type vexriscv --with-sdram --sdram-module MT41K128M16
   --sdram-data-width 16`, verilator from oss-cad-suite): the BIOS boots and prints "BIOS CRC passed", "SDRAM: 256.0MiB
   16-bit ... (CL-6 CWL-5)", "Initializing SDRAM @0x40000000...", "Memtest at 0x40000000 (8.0KiB)... Memtest OK",
   "Memspeed ... Write speed: 1.6MiB/s, Read speed: 492.9KiB/s" (build/ddr3/sim/litex_sim.log). This is the controller,
   BIOS and CPU against LiteDRAM's DFI-level SDRAMPHYModel. **It does not include the 7-series PHY.**
3. PHY-level simulation (designs/ddr3/phy_sim/, vivado/run_ddr3_phy_sim.ps1, xsim 2025.2):
   - `gen_phy.py` generates the A7DDRPHY alone (same LiteDRAM commit and parameters as the SoC: DDR3, 4 phases,
     100 MHz) with its DFI and read-leveling controls as ports (phy_top.v; settings CL 6, CWL 5, rdphase 3, wrphase 3,
     read_latency 8, write_latency 1 in phy_settings.json).
   - Primitives are Vivado's unisims + secureip (OSERDESE2/ISERDESE2 are secureip). This is behavioural RTL simulation
     of the generated PHY, not of either bitstream.
   - `ddr3_model.v` is a minimal behavioural DDR3 device written here (ACT/WRITE/READ, BL8, fixed CL 6/CWL 5, no
     timing checks, no ODT, MRS ignored). No vendor model was used: the Micron DDR3 model is not available offline and its
     licence was not checked. `+RD_EXTRA=<ps>` adds a fixed read delay (board flight + tDQSCK).
   - `tb_phy.v` drives the DFI like the BIOS's DFII: two write bursts, then the BIOS's read-leveling scan (per module,
     8 bitslips x 32 IDELAY taps, two patterns), then 24 write/read bursts over all banks at the chosen setting.
   - Write path: **pass.** All 16 beats land on the pins in DFI phase order; the first write DQS edge comes 11 875 ps
     after the WRITE command's CK edge (CWL x tCK = 12 500 ps, i.e. -0.25 tCK, the edge of DDR3's tDQSS window)
     (build/ddr3/sim/phy/xsim_extra0.out).
   - Read path with RD_EXTRA=0: **no leveling window.** The ISERDES output carries the right bytes in the right order,
     but they reach `rddata` one to two sys cycles before `rddata_valid` (read_latency 8): DFI READ sampled at
     1 635 000 ps, READ at the pins at 1 645 100 ps, data beat 0 at 1 660 100 ps, aligned word in rddata during
     1 695 000-1 705 000 ps, rddata_valid at 1 715 000 ps. BitSlip can add at most 7 beats.
   - RD_EXTRA sweep (build/ddr3/sim/phy/xsim_extra<ps>.out; each run is the full scan plus the 24-burst check):

     | extra read delay | m0 window | m1 window | 24-burst check |
     |---|---|---|---|
     | 0 ps | none | none | FAIL: 50 errors |
     | 1250 ps | none | none | FAIL: 50 errors |
     | 2500 ps | none | none | FAIL: 50 errors |
     | 3750 ps | none | none | FAIL: 50 errors |
     | 5000 ps | none | none | FAIL: 50 errors |
     | 6250 ps | bitslip 1, delay 27, 8 taps | bitslip 1, delay 27, 8 taps | PASS |
     | 7500 ps | bitslip 1, delay 15, 16 taps | bitslip 1, delay 15, 16 taps | PASS |
     | 8750 ps | bitslip 2, delay 15, 16 taps | bitslip 2, delay 15, 16 taps | PASS |
     | 10000 ps | bitslip 3, delay 15, 16 taps | bitslip 3, delay 15, 16 taps | PASS |

     So in this simulation the PHY works only if read data comes back at least 2.5 tCK later than an ideal CL-6
     device returns it (wider windows from 3 tCK; later data is absorbed by higher bitslips). A real board adds trace
     flight and tDQSCK (a few hundred ps in JEDEC DDR3), far less than 6.25 ns.
     See Open problems.

## Board test plan (for when the board arrives)
Bitstreams: open flow build/ddr3/arty_ddr3/gapfix/digilent_arty.bit (also stock/, qorfix/, and
build/ddr3/arty_ddr3_s80/gapfix/digilent_arty.bit at 80 MHz); Vivado reference build/ddr3/arty_ddr3/viv_ddr3/arty_ddr3.bit.
1. Load into SRAM (from the repo root in WSL, USB via usbipd as in docs/hardware-test-plan.md):
   `toolchain/oss-cad-suite/bin/openFPGALoader -b arty_a7_35t build/ddr3/arty_ddr3/viv_ddr3/arty_ddr3.bit` first (Vivado
   reference), then the open-flow bitstream.
2. Console: `toolchain/litex/venv/bin/litex_term /dev/ttyUSB1 --speed 115200` (the Arty's second FTDI channel; the
   index may differ, check `ls /dev/serial/by-id/`). Press the red RESET button (C2, cpu_reset_n) to restart the BIOS.
3. Expected output. The fixed strings are from litex/soc/software (bios, liblitedram/sdram.c, libbase/memtest.c) at
   the pinned commit and from the litex_sim run; the scan bits, delays, CRC and speeds will differ, and the exact
   spacing of the progress lines was not checked:
   ```
    BIOS CRC passed (xxxxxxxx)
   CPU:        VexRiscv @ 100MHz
   SDRAM:      256.0MiB 16-bit @ 800MT/s (CL-6 CWL-5)
   --=========== Initialization ===========--
   Initializing SDRAM @0x40000000...
   Switching SDRAM to software control.
   Read leveling:
     m0, b00: |00000000000000000000000000000000| delays: -
     m0, b01: |00000111111111111110000000000000| delays: NN+-NN
     ... (b00..b07 for m0, then m1)
     best: m0, bNN delays: NN+-NN
     best: m1, bNN delays: NN+-NN
   Switching SDRAM to hardware control.
   Memtest at 0x40000000 (2.0MiB)...
   Memtest OK
   Memspeed at 0x40000000 (Sequential, 2.0MiB)...
     Write speed: ...
      Read speed: ...
   ```
   (litex_sim prints the same lines with "VexRiscv @ 1MHz", "8MT/s" and an 8.0KiB memtest, because it is a simulation
   build.) The 80 MHz bitstream prints "@ 80MHz" and "640MT/s".
   Pass: a non-empty window for both modules and "Memtest OK". Record the leveling windows of both bitstreams.
4. Longer tests at the `litex>` prompt: `mem_test 0x40000000 0x1000000` (16 MiB), `mem_test 0x40000000 0x10000000`
   (all 256 MiB), `mem_speed 0x40000000 0x1000000`, `sdram_test`, `sdram_cal` (re-runs leveling and prints the scan).
5. If it fails:
   - all-zero leveling scans on both bitstreams: the read-latency question in Open problems is real on silicon. It is
     then a LiteDRAM issue, not ours; save the `sdram_cal` output of both bitstreams.
   - all-zero scans on the open bitstream only: a PHY difference between the flows; rerun flow/ddr_compare.py and check
     the IOI/IDELAY lines first.
   - Vivado bitstream passes, open one fails with a window: timing; try the 80 MHz bitstream.
   - leveling passes, memtest KO: write path or timing; compare with the Vivado bitstream and the 80 MHz build.

## Open problems
- **PHY simulation read latency.** In xsim with an ideal zero-delay DDR3 model, data reaches the A7DDRPHY's `rddata`
  1-2 sys cycles before `rddata_valid`, and leveling only works with at least 6.25 ns of extra read delay.
  - LiteDRAM 624444c (2026-07-22, "Align Artix-7 reads without altering CL") changed the A7 schedule from rdphase 2 with
    MR0 CL 7 to rdphase 3 with MR0 CL 6. Both put the first read beat 9 tCK after the start of the command's sys cycle,
    and read_latency is 8 in both (from the diff, `git show 624444c`). So the older schedule, which LiteX has used on
    Arty boards for years, would show the same gap in this simulation. That points at the simulation rather than at
    LiteDRAM: Vivado's unisim/secureip SERDES latencies, or my model's idea of when a device returns data. Not confirmed.
  - This concerns LiteDRAM's RTL, not our flow: both bitstreams implement the same PHY. The board test settles it.
- Timing signoff: nextpnr's timer is optimistic on this design and blind to SERDES; Vivado's timer on nextpnr's placement
  fails 100 MHz by 1.584 ns. No open timer checks our routed result.
- Not checked on silicon: ZINV_OCLK on unused OCLK, ZINV_T1 vs folded inverter, PLL/BUFG site choice.
- nextpnr ignores INTERNAL_VREF and always writes 0.675 V for SSTL inputs.
- The DFI-level litex_sim and the PHY-level xsim are separate; there is no single simulation of BIOS + controller + 7-series PHY + DDR3.

## Files
- flow/ddr_build.py, flow/ddr_pins_check.py, flow/ddr_compare.py, flow/ddr_xtime.py, flow/ddr_sim.sh
- vivado/run_ddr3.ps1, vivado/run_ddr3_phy_sim.ps1 (vivado/build_gap.tcl and build_xtime.tcl unchanged)
- designs/ddr3/arty_ddr3/, designs/ddr3/arty_ddr3_s80/, designs/ddr3/phy_sim/
- docs/drafts/prjxray-db-ioi-serdes-timing.md
- toolchain/litex/ (sources, venv, COMMITS.txt, pip-freeze.txt, riscv/, sysroot/, ref/)
- build/ddr3/ (all outputs and logs)
