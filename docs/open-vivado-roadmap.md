# Open Vivado for 7-series: capability checklist

The user's goal (2026-11-06): "essentially vivado but open source for 7 series. it should be able to do everything vivado can at the same level, if not better."

- Every row needs measured evidence, with the tool and timer named.
- "Untested" means not measured yet. It does not mean it works.
- Status values:
  - **ok:** measured at or better than Vivado.
  - **gap:** measured worse, or failing.
  - **partial:** some of it works.
  - **untested:** not measured.
  - **none:** no open equivalent.

## Devices
| Capability | Status | Evidence / next action |
|---|---|---|
| Artix-7 35T/50T | ok (flow) | All work so far uses xc7a35tcsg324-1 |
| Artix-7 100T | ok (offline) | `examples/blinky100` and `examples/dfx100` (anchor DFX): pr_check identical, partials simulated exact, byteman, region2v; pins from Digilent's Arty-A7-100 master XDC (docs/ofx.md) |
| Spartan-7 (xc7s50) | ok (offline) | `examples/blinky_s7`, `dfx_s7` (anchors), `dfxpp_s7` (auto partition pins) on the Arty S7-50 preset: bitstream IDCODE 0x0362F093 = prjxray-db, verify 10 PASS 0 FAIL each (pr_check, simulated partials, byteman, region2v); pins from Digilent's master XDC (docs/ofx.md Results 4) |
| Artix-7 200T (xc7a200t) | ok (offline) | `examples/blinky_nv`, `dfx_nv`, `dfxpp_nv` on the Nexys Video preset: IDCODE 0x03636093 = prjxray-db, anchor DFX verify 10 PASS 0 FAIL; auto partition pins needed a per-fabric region2v cache (fixed, docs/ofx.md Results 4 fix 3). nextpnr peak 2.5-2.6 GB |
| Zynq-7000 PL (xc7z020) | ok (offline) | `examples/blinky_z7`, `dfx_z7`, `dfxpp_z7` on the Zybo Z7-20 preset: IDCODE 0x03727093 = prjxray-db, verify 10 PASS 0 FAIL. A design with `PS7` builds unpatched (yosys blackbox, nextpnr PS7 bel and constant tie-off, PSS tiles have no config bits): `examples/ps7_axi_z7` (FCLK0 via BUFG, FCLKRESETN0, M_AXI_GP0 to an AXI3 register/LED block), and its bitstream, decoded back to a netlist with fasm2bels, passes a PS7-model replay of the app's GP0 accesses (34 checks, 0 errors; docs/ofx.md, Zynq). Not on a board |
| Zynq-7000 PS configuration and boot (ps7_init, FSBL, BOOT.bin, XSDB) | partial (offline, Zybo Z7-20 only) | `ofx boot`: U-Boot v2025.10 SPL with the board's `ps7_init_gpl.c` (GPL) as FSBL, `mkimage -T zynqimage` boot.bin, FIT with PL bitstream + bare-metal app, SD image, OpenOCD `ps7_init.tcl` generated from the C tables (selftest: 203 writes identical). QEMU xilinx-zynq-a9 boots SPL -> FIT -> app in JTAG and SD modes; QEMU cannot load the PL or reach GP0. Next: board test (SD and JTAG), more presets, S_AXI/HP/IRQ/EMIO |
| Other Spartan-7/Artix-7/Zynq parts | untested | Resolve in flow/device.py (chipdbs for xc7s25/s100, xc7z010/z030/z045/z100); not built |
| Kintex-7, Virtex-7 | none | No prjxray-db in the toolchain |

## Synthesis
| Capability | Status | Evidence / next action |
|---|---|---|
| Verilog / SystemVerilog | partial | Yosys; SV coverage is narrower than Vivado's (untested on large SV code). yosys `xilinx_dsp` aborts (`log_assert`, xilinx_dsp.cc:400) when a multiplier input register comes from a register wire with a 1 init bit: 11-line Verilog repro in `build/ofx/vhdl/yosys_dsp_init_assert/` (upstream bug, not reported). Fixed as a draft (docs/drafts/yosys-xilinx-dsp-init: only the bits that go into the DSP are checked; build build/yosys-build/yosys-dspinit): repro passes, 5 cases simulated 0 mismatches, no-op JSON on blinky/rv_soc/qor_rv_mul. The flow's yosys (oss-cad-suite) still has the bug |
| VHDL | ok (offline) | GHDL + its yosys plugin from oss-cad-suite; ofx converts VHDL to a Verilog netlist (`ofx/vhdl.py`), so flat builds, DFX static and VHDL RMs use the existing flow. `examples/vhdl_blinky`, `vhdl_mixed` (VHDL-2008 top + package + Verilog module) build to bitstreams; `dfx_vhdl` (VHDL RMs) verify 10 PASS 0 FAIL, RMs proven equivalent to the Verilog RMs. VHDL-2008 and 93; no `library unisim` (component declarations instead), no external names. Same VHDL in Vivado 2025.2: blinky identical cells (28 FDRE, 7 CARRY4, 1 LUT); vhdl_mixed 87 LUT / 95 FF / 6 CARRY4 / 1 DSP (yosys) vs 103 LUT primitives in 90 Slice LUTs / 95 FF / 8 CARRY4 / 1 DSP (Vivado); timing only from each tool's own timer, not comparable (docs/ofx.md VHDL) |
| LUT/FF/CARRY/SRL/LUTRAM/BRAM/DSP inference | partial | Wide multipliers: opt-in `synth_xilinx -dsp_pipeline` (docs/drafts/yosys-xilinx-dsp-pipeline, built in-tree and as a plugin) packs A/B/P registers and the A cascade; Vivado P&R of the yosys netlist 111 -> 159 MHz (rv_mul excl. ICAP) and 111 -> 157 (rv_big) against 172-179 on Vivado's own netlist (Vivado timer); FIR 1589 -> 597 FFs (Vivado 598). Off by default. Area (Finding 12, post-route, Vivado's LUT-site rule): yosys LUT cells equal Vivado's on the CPUs (rv_soc 1107 vs 1106); the site gap is packing (O5/O6 combining, nextpnr carry feed-through LUT1s), CARRY4 +20-46 % from unshared and small adders. Opt-in drafts (nextpnr `carry-di-bypass`/`lut-pair`, yosys `-share_aggressive`/`-carry_minwidth`): rv_soc 1078 vs 1041 LUT sites, 64 vs 63 CARRY4; rv_mul/rv_big below Vivado (1442/1478 vs 1483/1554 sites, 98 vs 123 CARRY4), at 1-3.5 % median nextpnr Fmax. Open: LiteX LUTRAM 320 vs 142 sites, LiteX LUT sites +14 %, `-widemux` netlist fails simulation |
| Timing-driven synthesis | gap | abc9 delay target from the clock: no change; `-dff` gives -3% LUTs; `-retime` not in this yosys; the DSP draft moves only registers after DSP adder trees (docs/qor-vivado.md Findings 5, 8) |
| Retiming, resource sharing, FSM extraction | untested | QoR agent |
| Out-of-context / hierarchical synthesis | ok | DFX flow synthesizes RMs out of context |

## Implementation
| Capability | Status | Evidence / next action |
|---|---|---|
| Placement and routing | gap | With `-o hardblock-timing` (draft): rv_soc 138.3 vs 135.8 MHz (both ICAP-limited); bram 155.5 vs 173.7; with the yosys DSP draft rv_mul 140.1 / rv_big 143.1 MHz best of 8 (nextpnr timer), but Vivado times nextpnr's placements at 121.8 / 111.0 against 159 / 157 when Vivado places the same netlist: placement is now the largest gap. 32-DSP FIR places with `-o dsp-cascade-place` (draft; heap 234.4, static 209.7 nextpnr timer; Vivado timer on that placement 203.1, Vivado's own 203.1). nextpnr ignores the period during optimization; `--placer static` better on every qor design. Runtime 8-53 s vs Vivado 73-233 s (docs/qor-vivado.md Findings 7-9). **Placement algorithms (Finding 11, Vivado timer on nextpnr's placement, 3 seeds):** Vivado packs denser and flatter (rv_soc 398 vs 501 slices, y-sd 5.5 vs 16.9), and nextpnr's critical paths are about twice as long. The opt-in options of docs/drafts/nextpnr-placer-tuning.patch (period-aware criticality, BRAM legalisation wait, overlap stop, static weights, FF area, x wirelength weight) move rv_soc 116.8 to at most 120.6 MHz (stub chipdb only; Vivado's own placement 157.6) and do not help bram, rv_big, DDR or eth. Period-aware criticality is worse on bram/rv_big. LiteX SoCs at 100 MHz: DDR WNS -1.9 ns, eth -4.3 to -5.2 ns (Vivado P&R of the same netlist +0.42 / -0.12). Next: routing-delay calibration (nextpnr's interconnect estimate is about 30 % below Vivado's on eth's critical path) |
| phys_opt / post-route optimization, incremental compile | none | Vivado's in-placer physical synthesis did only LUT combining on rv_soc (no replication; Finding 11), so replication is not what makes Vivado's placement faster there. nextpnr `-o timing-opt=3,10` on the static placer is within seed noise (nextpnr timer). Candidates: seed selection, nextpnr incremental via -o preplaced/prerouted replay. **Deferred (recorded 2026-11-06):** waits for placement round 2 (Finding 13, RESUME item 1): with placement ~25 % slower than Vivado's under Vivado's timer, post-placement optimisation would be tuned against a placement that is about to change |
| Pblocks, floorplanning | ok | nextpnr-pblock-xdc draft |
| Multiple clock domains, MMCM/PLL | ok (build); bits ok after fixes (draft) | gap-vivado.md: MMCME2/PLLE2 build. `ofx-prim` (nextpnr-mmcm-base-ties, nextpnr-clkout-unused): mmcme2_adv/base, mmcme2_base_rst, plle2_adv/base 0 / 0 by type against Vivado; a BASE is now packed like an ADV with the same ties, which both flows already agreed on. Not on silicon |
| BUFG/BUFGCTRL/BUFR/BUFIO | ok after fixes | Fixed by the yosys clkbufmap draft (plugin only) |
| BUFH/BUFHCE | ok after fixes (draft) | nextpnr-bufh-region: bufh builds, 0 / 0 exact against Vivado (gap-vivado.md G7) |

## Constraints (XDC)
Full table: docs/xdc-coverage.md. 34+1 test designs ran in both flows. "xdc" means the draft nextpnr-xdc-timing (variant `xdc`).

| Capability | Status | Evidence / next action |
|---|---|---|
| Pins, IOSTANDARD, create_clock | ok | All designs. `-name`/`-waveform` were ignored before; they are applied with xdc |
| Object queries (globs, `{a b}` lists, `-hier`, `-filter NAME`, line continuation, Vivado `*_reg` names) | ok with xdc; gap before | Base: a `{a b}` list crashes nextpnr (assertion), a continued line is an error, globs silently match nothing, and `get_cells x_reg` matches nothing because yosys names flip-flops `$auto$ff...`. With xdc all of these resolve (x_syn_*, x_mcp_to, x_loc) |
| Generated clocks (create_generated_clock) | ok with xdc | x_gen_div: base ignores it and times clk_div at the --freq default (79.0 MHz FAIL at 100). xdc: PASS at 50 MHz. Vivado: clk_div at 20 ns, slack +0.834 |
| MMCM/PLL-derived clocks: periods | ok | Derived by the packer (all variants) |
| MMCM/PLL-derived clocks: paths between them | ok with xdc; gap before | x_mmcm_none: c1 (100 MHz) to c2 (200 MHz) was never checked. xdc: `Max delay ... FAIL at requirement 5.00 ns, slack -0.84 ns`. Vivado: requirement 5 ns too (docs/xdc-coverage.md) |
| set_clock_groups, set_false_path (clocks; cells on one side) | ok with xdc; ignored (warned) before | x_cdc_groups/fpclk/fpcell, x_mmcm_groups: cross-domain report gone, no criticality; Vivado: path removed (EXCEPTION Asynchronous Clock Groups / False Path) |
| set_multicycle_path -to | ok with xdc | x_mcp_to: 68.8 MHz FAIL to 140.5 MHz PASS. Base matched no cell, because of yosys names, and warned |
| set_multicycle_path -from/-through, set_max_delay [-datapath_only], set_min_delay, set_false_path -through | ok with xdc2 (checked against Vivado, also on one placement: same requirements and cut paths; docs/xdc-coverage.md) | x_mcp_fromto: requirement 20 ns, as Vivado. x_cdc_maxdly: `-datapath_only 5` gives FAIL, slack -2.42 (Vivado -4.730). Exceptions are tagged clock domains in the timer (docs/drafts/nextpnr-xdc2-constraints) |
| set_input_delay / set_output_delay | ok with xdc2 (LVCMOS33 pad delays only) | x_iodly: output slack -7.82 ns against Vivado's -7.764; input +3.92 against +2.607. Clock delay from the pad and the pad buffers are included. On one placement (Vivado on ours) outputs are 1.03 ns optimistic (clock leaf route 0.72 short). Inputs differ because Vivado repairs input hold in routing and checks the Fast corner; the open flow does neither (x_iodly_minmax fails input hold, reported). docs/xdc-coverage.md "Port paths on one placement" |
| set_clock_uncertainty, latency, jitter | uncertainty ok with xdc2; jitter modelled but not checked; latency gap | x_uncert: +1.00 ns on the path. Jitter uses Vivado's formula when the XDC sets one. set_clock_latency is still warned |
| DRIVE / SLEW / IN_TERM | ok | Same IOB features as Vivado on x_io_drive / x_interm (docs/xdc-coverage.md) |
| PULLUP / PULLDOWN / KEEPER TRUE | ok with xdc; silent gap before | x_io_pull: base wrote PULLTYPE.NONE with no message. xdc writes PULLUP/PULLDOWN/KEEPER, as Vivado does |
| DIFF_TERM, IOB, ASYNC_REG, KEEP/DONT_TOUCH, MARK_DEBUG, CLOCK_DEDICATED_ROUTE | IOB, ASYNC_REG, CLOCK_DEDICATED_ROUTE ok with xdc2; the rest warned | IOB: x_io_iob packs the same 2 registers as Vivado into ILOGIC, 105/109 IOI FASM lines identical (the 4 others are the clock leaf track); OLOGIC: x_io_oiob 123/123 with docs/drafts/nextpnr-ologic-iob-sdr (xdc3). ASYNC_REG: the yosys plugin (docs/drafts/yosys-xilinx-asyncreg) keeps 3 FDRE, and nextpnr puts them in one slice, as Vivado. CLOCK_DEDICATED_ROUTE FALSE demotes the clock DRC. DIFF_TERM, KEEP/DONT_TOUCH, MARK_DEBUG still warned. DIFF_TERM is applied (XDC or IBUFDS parameter) by the separate `ofx-prim` draft nextpnr-diff-term (dt_xdc 0 / 0 exact vs Vivado); combined with xdc2, its DIFF_TERM "NOT applied" warning must go |
| LOC / site-local BEL on cells | ok with xdc | Base: the Vivado name matched nothing, silently. xdc: q_reg[0] at SLICE_X10Y20/CFF. xdc2 adds Vivado's rule_gclkio_bufg (Place 30-574): x_loc refused for the same reason as Vivado; x_loc2 and the MRCC clocks accepted |
| CFGBVS, CONFIG_VOLTAGE | ok | No configuration feature differs in Vivado's bitstream (x_cfg vs x_cfg_none) |
| BITSTREAM.* (COMPRESS, CONFIGRATE, SPI_BUSWIDTH, USR_ACCESS, STARTUP, SPI_FALL_EDGE, EXTMASTERCCLK_EN, CRC) | ok for the measured values (flow/bitstream_props.py) | Word for word as Vivado on Vivado's own frames (CRC words included) for all 10 x_cfg_* settings: COMPRESS (with CTL1 bit 12), CONFIGRATE 33, SPI_BUSWIDTH 4, USR_ACCESS, STARTUPCLK, the STARTUP cycles, SPI_FALL_EDGE (CMD 0x13), EXTMASTERCCLK_EN DIV-1 (COR0 0x06603fe5), CRC DISABLE. On our frames the 8 uncompressed settings give packets identical to Vivado's. Not measured: other CONFIGRATE/SPI_BUSWIDTH/EXTMASTERCCLK values (reported unsupported). docs/xdc-coverage.md section 6 |

## Timing analysis
| Capability | Status | Evidence / next action |
|---|---|---|
| Setup/hold, worst path, Fmax | partial | Opt-in Vivado-measured chipdb (docs/drafts/nextpnr-cell-timing-cal: FF clk->Q 0.456, LUT mean 0.200/0.228, FF bypass 0.290 ns): error of nextpnr's Fmax against Vivado's timer on the same placement 9.6% -> 6.3% mean over 6 designs, still optimistic on CPUs (+6 to +12%). Vivado's LUT delay is per input and route-dependent (0.12 or 0.30 ns). Compared on identical placements only, not identical routes (docs/qor-vivado.md Finding 10) |
| report_timing_summary / report_timing / check_timing | partial (opt-in) | `ofx timing` (ofx/timing.py) follows Vivado's layout: check_timing with Vivado's 12 items in Vivado's order (+4 ofx checks: ignored constraints, unrelated clocks, untimed async set/reset pins, untimed SRLs), WNS/TNS/WHS/THS/WPWS/TPWS, Clock Summary with generated and derived MMCM clocks, intra (with pulse width) and inter tables, clock interaction, a report_cdc-like CDC table, slack histograms, Timing Details per path group with Vivado cell/pin names, hold always. Data: nextpnr `--report-paths N` (docs/drafts/nextpnr-timing-report.patch, FASM and old report keys unchanged on the 10 designs added 2026-11-06). Against Vivado 2025.2 on the same placement (docs/timing-reports.md): check_timing 11 of 12 counts equal on 11 runs; small designs equal in endpoints, clocks, path groups and pulse width (x_mmcm_none TPWS 31 = 31, WPWS per clock equal); CPUs: 2118-2791 common endpoint names, setup slack rank correlation 0.89-0.94, nextpnr timer optimistic by 1.2-1.7 ns per endpoint. Not yet: pulse_width_clock, recovery/removal, SRL timing, pulse width of BRAM/LUTRAM/DSP/ICAP pins, clock path detail, `-through`, more than N paths per group, `ofx dfx build` passing `--report-paths` |
| Multi-corner, slack histograms | none/partial | Slack histograms in `ofx timing`, compared with Vivado's endpoint slacks in docs/timing-reports.md. One delay corner only: deferred until route-delay calibration (Finding 13). Needs slow/fast delays per arc (a calibrated chipdb pair or min/max DelayQuad per arc), setup on the slow max and hold on the fast min in nextpnr, and validation against Vivado one corner at a time (docs/timing-reports.md "Multi-corner") |
| Cross-clock checks between related clocks (MMCM outputs, generated clocks) | ok with xdc; gap before | Edge relationship over the common period, plus multicycle. x_mmcm_none FAIL / x_mmcm_mcp PASS, as in Vivado (docs/xdc-coverage.md). xdc2 adds the hold check between them: x_mmcm_none hold slack +1.32 ns (Vivado +0.311) |
| Timing exceptions (false path, clock groups, multicycle, max/min delay) | ok with xdc2 | docs/xdc-coverage.md. Not yet: several -through lists in order, `-from/-to [get_ports]`, `-start` |
| Timing of hard-block pins (ICAP, DSP, BRAM) | partial | Fixed opt-in by docs/drafts/nextpnr-hardblock-timing.patch (prjxray-db SDF). Default still blind; make it the ofx default after a no-op/regression pass |

## IP catalog equivalents
| Vivado IP | Open equivalent | Status |
|---|---|---|
| Clocking Wizard | direct MMCM/PLL instantiation | ok (build) |
| MIG (DDR3) | LiteDRAM | partial (offline) | LiteX digilent_arty SoC + DDR3 builds to a bitstream with the open flow (stock and gapfix). DDR IOB/IDELAY/SERDES-clocking FASM matches Vivado on the same Verilog (every difference explained). Pins checked against Digilent's mig.prj (0 mismatches). LiteDRAM unit tests 175/175; litex_sim BIOS Memtest OK. Timing: nextpnr says 111 MHz, but Vivado's timer on nextpnr's placement gives WNS -1.58 ns at 100 MHz (+0.61 at 80 MHz); placement is the gap (CPU/controller logic, not the PHY). OSERDES/ISERDES untimed (no prjxray-db timing). PHY sim read window needs extra delay (likely the model). docs/ddr3-litedram.md |
| FIFO Generator | FIFO18E1/36E1 hard FIFOs | ok after fixes (draft, offline): nextpnr-fifo + prjxray-db-prim-segbits; 10 FIFO designs (4 to 72 bits, sync/async/FWFT) 0 / 0 by type against Vivado, data pins on the same signals as Vivado's netlist (gap-vivado.md G5). ECC FIFOs and FIFO36E1 DATA_WIDTH 4 refused; FIFO pins probably untimed; not on silicon |
| XADC Wizard | XADC primitive | partial (draft, offline): variant `ofx-prim-xadc` with a regenerated chipdb (XADC site metadata drafted) places it and writes INIT_40..5F; 6 XADC designs 0 / 0 exact; 3 INT_L/HCLK_L bits Vivado sets are still unknown; analog inputs untested (gap-vivado.md G6) |
| Tri-mode Ethernet MAC | LiteEth | partial (offline, 10/100 MII only) | LiteX digilent_arty SoC with LiteEth MAC + hardware UDP/IP + Etherbone (and a LiteScope variant) builds to a bitstream with the open flow, stock and gapfix, no fix needed. MII pins checked against Digilent's master XDC (27 ports, 0 mismatches). FASM vs Vivado on the same Verilog: MII IOI identical, IOB identical except the input buffer of 3 pads the design never reads (Vivado drops them), PLL/BUFG site choice. Timing: nextpnr says sys 87 MHz (fail at 100); Vivado's timer on nextpnr's placement WNS -4.73 ns, on Vivado's placement of the yosys netlist -0.12 ns, Vivado's own build +0.37 ns: placement is the gap; a 60 MHz build meets all constraints in Vivado's timer on nextpnr's placement (+2.10 ns); MII domains have > 1 ns margin at 25 MHz in all runs. Sim: LiteEth tests 489 pass / 12 skipped; MII PHY + MAC loopback (6 frames, CRC vs zlib); litex_sim SoC answers ping and Etherbone over a TAP in a user namespace. RGMII/GMII (1G) not covered: the Arty has an MII PHY. docs/ethernet-debug.md |
| GTP transceivers (PCIe, high-speed serial) | none built yet; bit database exists for GTP (artix7) and GTX (kintex7) | none (not built or tested). The Arty's csg324 bonds no MGT pins; Basys 3 / Cmod A7 (xc7a35tcpg236, 2 lanes) and Nexys Video (xc7a200tsbg484, 4 lanes) do. openXC7 prjxray-db a8b09269 (the installed revision): artix7 has GTP_CHANNEL_0..3 / GTP_COMMON segbits (with the xc7a200t MID_LEFT/RIGHT variants) and PCIE_BOT, nextpnr-xilinx-meta has GTPE2_CHANNEL/COMMON, IBUFDS_GTE2 and PCIE_2_1 site types; kintex7 (not in the installed package) has GTX_CHANNEL/COMMON + PCIe segbits and GTXE2 site types; zynq7 has GTX tiles in the xc7z030/045/100 tilegrids but no GT segbits or site metadata; spartan7 has no transceivers. Upstream f4pga/prjxray-db (0a0added, 2021) has the artix7 GTP bits but no kintex7 GTX bits. `build/ofx/devices/gt_survey.txt` |
| AXI interconnect / Block Design | hand-written RTL / LiteX SoC builder | partial (no GUI block design) |
| MicroBlaze | open soft CPUs (PicoRV32, VexRiscv) | ok as a different CPU, not ISA-compatible |
| DFX Decoupler, DFX Controller | dfx_decoupler.v, rv_flash loader | ok offline (docs/dfx-vs-vivado.md) |

## DFX (partial reconfiguration)
- Full matrix: docs/dfx-vs-vivado.md. Partial format word-identical to Vivado on its own references; RAR, compression, multiple RPs, partition pins (automatic) done offline. Not on hardware.

## Bitstream and programming
| Capability | Status | Evidence / next action |
|---|---|---|
| Full bitstream, .bin | ok | Byte-level parity checks against Vivado decodes |
| Compression | ok | Partials; full bitstreams with flow/bitstream_props.py (BITSTREAM.GENERAL.COMPRESS): Vivado's own frames compressed by it give Vivado's x_cfg_compress.bit word for word (62788/62788); on our frames 0 frames differ from the uncompressed bitstream (strict model). prjxray's bitread cannot decode MFWR, so this is checked with flow/bitparse.py |
| Encryption, eFuse, readback CRC, SEU mitigation | none/untested | **Deferred (recorded 2026-11-06): out of scope until the user requests it.** AES bitstream encryption and eFuse/BBRAM key programming write one-time or security-relevant state on the device and cannot be checked offline against Vivado without a key flow; nothing in the current goal list depends on them |
| JTAG program, SPI flash program | ok (openFPGALoader) | Partial over JTAG: patch built, traced, not on hardware |
| Hardware manager / ILA debug | partial (offline) | LiteScope (logic analyzer) + litex_server / litescope_cli. Built in both flows inside the LiteEth SoC (analyzer on the MII rx domain, read over Etherbone). `flow/mark_debug.py` maps a Vivado debug XDC (MARK_DEBUG nets, or create_debug_core / connect_debug_port / C_DATA_DEPTH) onto a LiteScope core inserted before synthesis (yosys `expose` + a standalone core with a UART or JTAG/BSCANE2 bridge); 3 test designs build to bitstreams with the open flow. Captures simulated offline: LiteScope's own litex_sim test over a virtual UART, and over Etherbone in litex_sim. No GUI waveform viewer (VCD/sigrok out), no ILA advanced triggers. Untested on hardware. docs/ethernet-debug.md |

## Verification and analysis
| Capability | Status | Evidence / next action |
|---|---|---|
| Behavioural simulation | ok | iverilog (Verilator available in oss-cad-suite) |
| Post-implementation simulation from the bitstream | ok (beyond Vivado) | region2v, fasm2bels |
| Power analysis | none | |
| DRCs | partial | Region/INT-pair/shared-frame DRCs; no general DRC deck |

## Usability
| Capability | Status | Evidence / next action |
|---|---|---|
| One-command install | ok (this machine, offline-verified) | `install/install.sh --run` into a fresh prefix (no sudo): pinned upstream sources (install/sources.toml), 11-patch nextpnr series with no conflicts, chipdb sha256 = nightly. Smoke test with only the prefix on PATH: blinky and rv_ppa `.frames` identical, native_check PASS (docs/install.md). Combined `ofx` nextpnr is a no-op for stock/rv_pp/rv_ppa. It changes older pblock designs (patches 0004/0007, intended); rv_pr/rv_b/rv_c/rv_m/rv2 rebuilt with it pass all checks (rv_m 2026-11-06: 3/3 static identical, region pips 0/0). Dockerfile untested; other machines untested |
| Project flow, CLI | ok (offline) | `bin/ofx` + `ofx.toml`: new/build/program/report/timing/dfx build/partials/verify/load; reproduces rv_pr native frames and partials byte-for-byte (docs/ofx.md) |
| GUI | none | **Deferred (recorded 2026-11-06):** waits until the core flow (placement, timing, synthesis QoR) matches Vivado; the CLI (`bin/ofx`) and text reports are the interface until then (RESUME "Deferred, with reasons") |
| Reproducible builds | ok | Native 26/26 and external 6/6 frame-identical rebuilds |

## Next, in priority order (after the running agents report)
1. Benchmark real system designs in both tools: LiteX SoC + DDR3 (done offline), LiteEth (done offline, docs/ethernet-debug.md), a DSP pipeline, a BRAM-heavy design.
2. Timer agreement with Vivado (QoR agent). XDC coverage audit: done (docs/xdc-coverage.md); IO delays, exceptions, IOB packing, ASYNC_REG, BITSTREAM.* and the clock DRC are in xdc2; next are the Vivado references of the new test designs and pad delays for more I/O standards.
3. QoR, in order of size:
   1. yosys DSP48E1 mapping for wide multipliers (MREG/PREG/cascade): opt-in draft done (Finding 8); remaining: rv_big BRAM read path, FIR netlist slower in Vivado P&R than the default one;
   2. DSP cascade placement: opt-in draft done, FIR places (Finding 9);
   3. placement quality (static placer as default; period-aware criticality);
   4. calibrate the delay model: Vivado-measured chipdb draft (Finding 10; prjxray SDF has stub-like values); remaining: routing delays, identical-route comparison;
   5. area: opt-in drafts done (Finding 12, LUT sites within +4 % of Vivado (rv_soc) or below it (rv_mul, rv_big), CARRY4 at Vivado's level, at 1-3.5 % median Fmax); remaining: LiteX LUTRAM mapping (RAM256X1S vs block RAM), LiteX LUT sites +14 %, bram three-operand adders, `-widemux` correctness, a Vivado-timer check of the new placements.
4. Hard FIFO, BUFH, DIFF_TERM, IOBUF DRIVE, MMCM/PLL defaults, ICAP/DNA enables, XADC: drafted and matched to Vivado's decoded bitstreams offline (`ofx-prim`, `ofx-prim-xadc`; docs/drafts/nextpnr-prim-gaps.md). Next: review, the install series (the db drafts must ship with it), the 3 XADC INT/HCLK bits, a board test.
5. An open ILA-style debug core: LiteScope + MARK_DEBUG insertion done offline (docs/ethernet-debug.md); next is a board test of the JTAG bridge and the same insertion inside `ofx build`.
