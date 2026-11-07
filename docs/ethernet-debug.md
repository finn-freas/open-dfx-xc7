# Ethernet (LiteEth) and on-chip debug (LiteScope) on the Arty A7-35T through the open flow

Date: 2026-11-06. **No hardware was used.** Every number below comes from a run whose log is named next to it.
Timer labels: "nextpnr" = nextpnr's own timer, "Vivado" = Vivado 2025.2's signoff timer. They are different models, so
no cell mixes them.

This is the open counterpart of two Vivado items: the Tri-mode Ethernet MAC IP (here: LiteEth, MAC + UDP/IP +
Etherbone) and the ILA / hardware manager (here: LiteScope, with a MARK_DEBUG-to-LiteScope insertion step).

## Summary
- **Ethernet.** A LiteX digilent_arty SoC with LiteEth (MII PHY, MAC for the CPU, hardware UDP/IP + Etherbone) and the
  same SoC with a LiteScope analyzer go **synth → pnr → fasm → bitstream** with our flow, stock nightly and gapfix.
  **No fix was needed.** MII pins: 27 ports per design checked against Digilent's master XDC, 0 mismatches.
- Bitstream decode against Vivado's build of the same Verilog: the MII pins' IOI tiles are identical (285 / 288
  features, 0 differences); IOB tiles differ only in the PUDC_B pair (known) and, in arty_eth, in the input buffer of
  the three MII inputs the design never reads (eth_col, eth_crs, eth_rx_er: Vivado removes the unloaded IBUF, openXC7
  enables it). The PLL sits in a different CMT and the BUFGs on different GCLK indices; both tools put the two PHY
  clocks on BUFGs.
- Timing: nextpnr says sys_clk 87.06 MHz (FAIL at 100). Vivado's timer on nextpnr's placement: **WNS -4.730 ns at
  10 ns** (arty_eth). Vivado placing and routing the yosys netlist: WNS -0.121 ns. Vivado's own build: WNS +0.374 ns.
  So synthesis is close and placement is the gap, as for the DDR3 SoC. The 25 MHz MII domains pass with margin in every
  run. A 60 MHz build (arty_eth_s60) meets all constraints in Vivado's timer on nextpnr's placement (WNS +2.096 ns).
- Simulation: LiteEth unit tests 489 passed, 12 skipped (after rerunning 7 that first failed on a PATH problem); an
  MII PHY + MAC loopback written here passes 6 frames (preamble, SFD, CRC checked against zlib); the full LiteX SoC in
  litex_sim, put on a TAP device inside a user network namespace (no root), answers ping and Etherbone, and LiteScope
  captures over Etherbone work.
- **On-chip debug.** LiteScope is the ILA counterpart. LiteScope's own tests pass (62), including a litex_sim capture
  over a virtual UART. `flow/mark_debug.py` turns a Vivado debug XDC (MARK_DEBUG nets or Vivado's create_debug_core /
  connect_debug_port lines) into a LiteScope core inserted on those nets before synthesis, with a UART or a JTAG
  (BSCANE2) bridge. Three test designs build in our flow and in Vivado
  from the same files; their IOB/IOI/BSCAN bits match Vivado's except the known PUDC_B pair.
- One LiteX issue found and drafted (docs/drafts/litex-sim-analyzer-csv.patch): litex_sim writes the analyzer CSV only
  at exit, so litescope_cli cannot connect to a running simulation.
- Nothing ran on hardware; the board commands are below, marked untested.

## Sources and versions
Same LiteX tree as docs/ddr3-litedram.md (toolchain/litex, pinned commits in toolchain/litex/COMMITS.txt; migen must be
LiteX's pin 4c2ae8df). Added for this work:

| item | version / commit | source |
|---|---|---|
| liteeth | 9712c3899c4b9d162aca5aef403889ab2c8c4542 (already installed) | github.com/enjoy-digital/liteeth |
| litescope | d45c2387d77e9833719e335e98e64d293e351ea3 (2026-11-05), `pip install --no-deps -e` | github.com/enjoy-digital/litescope |
| pytest 9.2.0, pexpect 4.9.0 | PyPI, into toolchain/litex/venv (pexpect is needed by LiteScope's litex_sim test) | pypi.org |

toolchain/litex/pip-freeze.txt was regenerated. The venv had no setuptools, so `pip install --no-build-isolation`
failed; plain `pip install --no-deps -e src/litescope` (isolated build) worked.

## Pins (Digilent master XDC)
The Arty A7 PHY is a TI DP83848J on MII (Digilent reference manual; the master XDC names the signals). LiteX's
platform file (litex_boards/platforms/digilent_arty.py lines 136-155) defines the MII pins.
`flow/eth_pins_check.py` compares every LOC and IOSTANDARD in both generated XDCs with
toolchain/litex/ref/digilent-xdc/Arty-A7-35-Master.xdc (digilent-xdc c8644a9f):
**27 ports checked per design, 0 mismatches, all 18 eth_* ports of the master XDC used, no port unchecked**
(build/eth/pins_check.json).

| LiteX port | pin | master XDC name | pin type (master XDC comment) |
|---|---|---|---|
| eth_clocks_tx | H16 | eth_tx_clk | IO_L13P_T2_MRCC_15 |
| eth_clocks_rx | F15 | eth_rx_clk | IO_L14P_T2_SRCC_15 |
| eth_ref_clk (25 MHz out) | G18 | eth_ref_clk | IO_L22P_T3_A17_15 |
| eth_rx_dv / rx_er | G16 / C17 | eth_rx_dv / eth_rxerr | |
| eth_rx_data[3:0] | G17 E18 E17 D18 | eth_rxd[3:0] | |
| eth_tx_en | H15 | eth_tx_en | |
| eth_tx_data[3:0] | H17 J13 J14 H14 | eth_txd[3:0] | |
| eth_col / crs | D17 / G14 | eth_col / eth_crs | |
| eth_mdc / mdio / rst_n | F16 / K13 / C16 | eth_mdc / eth_mdio / eth_rstn | |

All LVCMOS33, bank 15. Both MII clocks enter on clock-capable pins.

## Designs
Generated by `flow/eth_build.py` (CONFIG block, DRY_RUN default, cached; reuses flow/ddr_build.py's generate/stage/pnr):

| design | generator | what |
|---|---|---|
| arty_eth | `python3 -m litex_boards.targets.digilent_arty --toolchain vivado --variant a7-35 --sys-clk-freq 100e6 --integrated-main-ram-size 0x10000 --with-ethernet --with-etherbone --eth-ip 192.168.1.50` | VexRiscv + BIOS, 64 KiB integrated main RAM (no DDR3, to isolate Ethernet), LiteEthPHYMII, LiteEthMAC for the CPU (BIOS IP 192.168.1.51) and a hardware LiteEthUDPIPCore + Etherbone at 192.168.1.50 sharing the PHY (`interface="hybrid"`) |
| arty_scope | `python3 -m flow.eth_scope_soc` with the same arguments | arty_eth + a LiteScopeAnalyzer (depth 1024, 26 bits) in the eth_rx clock domain: rx_dv, rx_er, rx_data, crs, col pads, the PHY's 8-bit rx stream (valid, last, data) and a frame counter. Read out over Etherbone |
| arty_eth_s60 | arty_eth with `--sys-clk-freq 60e6` (PLL VCO 1500 MHz, sys /25 = 60 MHz, eth /60 = 25 MHz; build/eth/gen_arty_eth_s60.log) | the bitstream to try first on the board, see Timing |

Logs: build/eth/gen_arty_eth.log, build/eth/gen_arty_scope.log. Staged into designs/eth/<design>/ (Verilog, VexRiscv.v,
*.init, LiteX's Vivado XDC, nextpnr/digilent_arty.xdc = the same without set_false_path / set_max_delay /
set_clock_groups / INTERNAL_VREF, csr.csv, analyzer.csv). **The same Verilog goes to both flows.**

Clocking (LiteX): PLLE2_ADV from clk100 makes sys 100 MHz and eth 25 MHz (driven out on eth_ref_clk G18 as the PHY's
reference clock). eth_tx_clk and eth_rx_clk come from the PHY on H16/F15 and are used directly as clocks (no MMCM).
The MII registers are plain fabric flip-flops in LiteX (no IOB attribute, no ILOGIC/OLOGIC primitives).
LiteX's XDC: `create_clock -name eth_rx_clk -period 40.0 [get_nets eth_rx_clk]` (same for tx), and asynchronous clock
groups eth_rx/eth_tx/sys.

## Open-flow builds
`python3 flow/eth_build.py arty_eth arty_scope --variant gapfix --variant stock --run` (log build/eth/build_all.log).

| design | variant | synth | pnr | fasm | bitstream | seconds (synth + pnr + fasm + bit) | log |
|---|---|---|---|---|---|---|---|
| arty_eth | gapfix | ok | ok | ok | ok | 43.33 + 208.42 + 11.41 + 0.11 | build/eth/arty_eth/gapfix/status.json |
| arty_eth | stock | ok | ok | ok | ok | 53.30 + 282.03 + 12.01 + 0.11 | build/eth/arty_eth/stock/status.json |
| arty_scope | gapfix | ok | ok | ok | ok | 45.88 + 257.63 + 11.65 + 0.11 | build/eth/arty_scope/gapfix/status.json |
| arty_scope | stock | ok | ok | ok | ok | 58.27 + 324.25 + 12.10 + 0.11 | build/eth/arty_scope/stock/status.json |
| arty_eth_s60 | gapfix | ok | ok | ok | ok | 46.80 + 189.13 + 10.95 + 0.12 | build/eth/arty_eth_s60/gapfix/status.json (log build/eth/build_s60.log) |

Runtimes are indicative only (machine shared with other agents' nextpnr and Vivado runs).

- **Nothing had to be fixed to build either design, with the stock nightly flow or with gapfix.** gapfix vs stock FASM
  differs only in the DSP48E1 tiles of the CPU multiplier (MASK[47:46], AREG_1/BREG_1: the G1 draft) and comment lines
  (`diff` of the sorted .fasm files, 20 lines for arty_eth).
- nextpnr's stock XDC reader warns `ignoring unsupported XDC option '-name'` on the three create_clock lines, but still
  creates the clocks on the nets (eth_tx_clk and eth_rx_clk are timed at 25 MHz in nextpnr.log). The clock names come
  from the nets, which here equal the `-name` values. (docs/drafts/nextpnr-xdc-timing.patch reads `-name`.)
- nextpnr cannot use LiteX's set_clock_groups, so it reports eth_rx/eth_tx ↔ sys as cross-domain paths (all < 3 ns).

Utilisation (gapfix, yosys_stat.txt and nextpnr.log):

| | arty_eth | arty_scope | LiteScope cost |
|---|---|---|---|
| LUT (yosys LUT2-6) | 5958 | 6225 | +267 |
| FF (FDRE/FDSE/FDCE/FDPE) | 5358 | 5877 | +519 |
| CARRY4 | 519 | 548 | +29 |
| LUTRAM (RAM32M + RAM64M) | 147 + 8 | 161 + 8 | +14 RAM32M |
| RAMB36E1 / RAMB18E1 | 27 / 12 | 28 / 12 | +1 RAMB36E1 (1024 x 26 capture buffer) |
| DSP48E1 | 4 | 4 | |
| BUFG | 5 | 5 | |
| nextpnr SLICE_LUTX (incl. route-throughs) | 10754 | 11355 | |

## Vivado builds of the same Verilog
`vivado/run_ddr3.ps1 -SrcSub designs\eth -Tag eth -Names arty_eth,arty_scope -Run` (unchanged vivado/build_gap.tcl:
synth, opt, place, route, bitstream, default directives; LiteX's full XDC). Outputs in
C:\Users\finnf\open-dfx-xc7-vivado\build\eth\, copied to build/eth/<design>/viv_eth/ by flow/eth_compare.py.

| design | synth | opt | place | route | bitstream (s) | LUTs (of which memory) | FF | BRAM tiles | bonded IOB | log |
|---|---|---|---|---|---|---|---|---|---|---|
| arty_eth | 133.36 | 18.11 | 81.36 | 51.07 | 27.79 | 5432 (512) | 5264 | 43.5 | 24 | build/eth/arty_eth/viv_eth/{times.txt,util.rpt} |
| arty_scope | 139.46 | 17.54 | 81.43 | 63.70 | 29.39 | 5825 (566) | 5787 | 44.5 | 27 | build/eth/arty_scope/viv_eth/{times.txt,util.rpt} |

Vivado maps more of LiteX's memories to block RAM (43.5 tiles vs 27 RAMB36 + 12 RAMB18 from yosys). arty_eth has 24
bonded IOBs in Vivado and 27 pads in nextpnr: Vivado drops the input buffers of eth_col, eth_crs and eth_rx_er, which
LiteEth's MII PHY never reads (see the FASM comparison below). In arty_scope LiteScope reads those three pads, and
Vivado has 27.

## Bitstream comparison with Vivado (MII IOs and clocking)
`python3 flow/eth_compare.py arty_eth arty_scope` (wraps flow/ddr_compare.py: decode both .bit files with
flow/bit2fasm.py, canonicalise, diff IO/clock/hard-block tiles; INT/CLB routing excluded). Output: build/eth/cmp_gapfix.txt,
build/eth/<design>/cmp_gapfix_vs_eth/{fasm_compare.json,eth_summary.json}. Unknown bits: 0 in all four bitstreams. All
MII pins are LOC'd, so IOB/IOI tiles are compared at the same coordinates.

| group (exact, same tile) | arty_eth common / Vivado only / openXC7 only | arty_scope | what the difference is |
|---|---|---|---|
| IOB | 137 / 8 / 3 | 140 / 8 / 0 | Vivado only: the 8 features of LIOB33_X0Y43 (L15/L16, PUDC_B pull-up/pull-down pair, known G13 item, as in docs/ddr3-litedram.md). openXC7 only (arty_eth): `LVCMOS25_LVCMOS33_LVTTL.IN` on eth_col (D17), eth_crs (G14), eth_rx_er (C17), the three inputs the design does not read; yosys keeps an IBUF on every top-level input and nextpnr enables it, Vivado removes the unloaded IBUF and leaves the input buffer off. With LiteScope reading them (arty_scope) the difference disappears |
| IOI (ILOGIC/OLOGIC/IDELAY of the MII pins) | 285 / 0 / 0 | 288 / 0 / 0 | identical. Neither tool packs the MII registers into ILOGIC/OLOGIC flip-flops (LiteX sets no IOB property): outputs use the OLOGIC pass-through (OMUX.D1, OQUSED), inputs the ILOGIC bypass, with the same default bits |
| CMT (PLLE2_ADV) | 0 / 61 / 49 (46 common by type) | same | different CMT: Vivado X106Y44, openXC7 X106Y96 (same as the DDR3 SoC). By type, Vivado only: HIGH/LOW/NO_COUNT on the unused CLKOUT2-5 (G13) |
| CLK_BUFG / CLK_HROW / HCLK_CMT | 38/85/90, 8/43/47, 10/12/18 | 35/85/95, 5/39/50, 8/12/19 | 5 BUFGs in each tool (sys, eth 25 MHz, clk100 feed, eth_rx, eth_tx). Vivado uses BUFG sites in both halves (GCLK0, 1, 16-18), openXC7 only the top half (GCLK16, 21-24); HROW/HCLK_CMT differences follow the GCLK index choice |
| IOI clock-pin partition | no SERDES clock pins in this design | | |

Per pin (IOB, both flows, arty_eth): every MII and MDIO pad has LVCMOS33, PULLTYPE.NONE, IN_TERM.NONE; outputs
DRIVE I12_I16 and SLEW SLOW (LiteX sets none, so both use the 12 mA/slow default); inputs IN_ONLY + IN. The two MII
clocks enter at H16/F15 (MRCC/SRCC) and both tools put them on a BUFG; neither uses BUFR/BUFIO or a CMT for them.

## Timing
| run | timer | sys_clk (10 ns) | eth_rx_clk (40 ns) | eth_tx_clk (40 ns) | hold | log |
|---|---|---|---|---|---|---|
| arty_eth openXC7 gapfix | nextpnr | **87.06 MHz, FAIL** | 190.29 MHz | 131.15 MHz | not checked | build/eth/arty_eth/gapfix/nextpnr.log |
| arty_eth openXC7 stock | nextpnr | 87.06 MHz, FAIL | 190.29 MHz | 131.15 MHz | not checked | build/eth/arty_eth/stock/nextpnr.log |
| arty_eth Vivado own synth + P&R | Vivado | **WNS +0.374 ns** (103.9 MHz) | WNS +1.262 ns (a 2 ns set_max_delay on the reset synchroniser) | WNS +1.118 ns (same) | WHS +0.024 ns | build/eth/arty_eth/viv_eth/timing.rpt |
| arty_eth yosys netlist, Vivado P&R ("free") | Vivado | WNS -0.121 ns, 6 failing (98.8 MHz) | +28.358 ns | +29.553 ns | WHS +0.031 ns | build/eth/xtime/out/arty_eth_gapfix_free/timing.rpt |
| arty_eth nextpnr placement, Vivado routing ("placed") | Vivado | **WNS -4.730 ns, 2185 failing endpoints (67.9 MHz)** | +29.421 ns | +23.517 ns | WHS +0.027 ns | build/eth/xtime/out/arty_eth_gapfix_placed/timing.rpt |
| arty_scope openXC7 gapfix | nextpnr | 86.72 MHz, FAIL | 133.30 MHz | 144.61 MHz | not checked | build/eth/arty_scope/gapfix/nextpnr.log |
| arty_scope Vivado own | Vivado | WNS +0.137 ns (101.4 MHz) | +1.241 ns (max_delay) | +1.118 ns (max_delay) | WHS +0.024 ns | build/eth/arty_scope/viv_eth/timing.rpt |
| arty_scope "free" | Vivado | WNS -0.107 ns, 25 failing (98.9 MHz) | +27.983 ns | +28.389 ns | WHS +0.024 ns | build/eth/xtime/out/arty_scope_gapfix_free/timing.rpt |
| arty_scope "placed" | Vivado | **WNS -4.639 ns, 2948 failing (68.3 MHz)** | +24.577 ns | +24.581 ns | WHS +0.037 ns | build/eth/xtime/out/arty_scope_gapfix_placed/timing.rpt |
| arty_eth_s60 openXC7 gapfix | nextpnr | 85.70 MHz, PASS at 60 MHz | 156.64 MHz | 122.70 MHz | not checked | build/eth/arty_eth_s60/gapfix/nextpnr.log |
| arty_eth_s60 Vivado own | Vivado | WNS +1.073 ns at 16.667 ns | +1.262 ns (max_delay) | +0.846 ns (max_delay) | WHS +0.024 ns | build/eth/arty_eth_s60/viv_eth/timing.rpt |
| arty_eth_s60 "placed" | Vivado | **WNS +2.096 ns at 16.667 ns, 0 failing** | +28.532 ns | +23.540 ns | WHS +0.036 ns | build/eth/xtime/out/arty_eth_s60_gapfix_placed/timing.rpt |

- Method: `python3 flow/eth_xtime.py --run` (wraps flow/ddr_xtime.py / flow/qor_xtime.py) then
  `vivado/run_ddr3.ps1 -Script build_xtime.tcl -SrcSub build\eth\xtime\src -Tag eth_xtime -Names ... -Run`.
  "placed": 12015 (arty_eth) / 12860 (arty_scope) / 11995 (arty_eth_s60) cells keep nextpnr's site and BEL; the other entries of place.txt are
  nextpnr-made cells (route-through and constant-feed LUTs for CARRY4 DI/S inputs) that do not exist in the yosys
  netlist, plus 156 / 139 / 175 placements Vivado rejects (Vivado 12-1409 "bel is occupied" on CARRY4 and LUT/FF BELs of split
  carry chains, and "routing contention" at the slice output muxes); Vivado places those itself
  (place_missed.txt). Vivado routes. So it is Vivado's timer on nextpnr's placement, not on our bitstream.
- The MII domains have large margins everywhere (40 ns period). In Vivado's own build their WNS is set by LiteX's
  `set_max_delay 2` between the two reset-synchroniser flops; that constraint selects cells by the `ars_ff1/ars_ff2`
  attributes, which the yosys EDIF does not carry, so in the "free"/"placed" runs it does not apply.
- sys_clk: Vivado's timer on Vivado's placement of the yosys netlist misses 100 MHz by only 0.121 ns; on nextpnr's
  placement it misses by 4.73 ns. On nextpnr's own critical path (Etherbone record receiver base_addr → CARRY4 chain
  → CE of a FF) nextpnr reports 11.486 ns; Vivado's timer on the same placement reports slack -2.973 ns, path 12.670 ns
  (build/eth/xtime/out/arty_eth_gapfix_placed/paths_vivado.txt). As for the DDR3 SoC, placement is the gap, not
  synthesis and not the MAC/PHY.
- Vivado's own build meets 100 MHz with +0.374 ns (arty_eth) and +0.137 ns (arty_scope); the worst path is CSR read
  muxing from a block RAM (mem_3_reg → csr bank dat_r, 7 logic levels).
- nextpnr cannot read LiteX's set_clock_groups; it reports the eth ↔ sys crossings as cross-domain paths (< 2.6 ns in
  nextpnr.log), all through LiteX's CDC FIFOs.

## Simulation
1. **LiteEth unit tests** (liteeth 9712c389, `python -m pytest test`, 71 files): 482 passed, 12 skipped, 7 failed, 1113
   subtests passed, 1368 s (build/eth/sim/liteeth_pytest.log). The 7 failures (test_mac_100g x4,
   test_wide_datapath_rtl full_mac_core at 128/256/512 bit) were an environment error: the shell's PATH found the
   Windows /mnt/c/oss-cad-suite verilator first (`verilator_bin: not found`). Rerun with the project's
   toolchain/oss-cad-suite on PATH: **7 passed, 12 subtests passed** (build/eth/sim/liteeth_pytest_verilator.log). So
   489 passed, 12 skipped, 0 failed. `flow/eth_unittests.sh` (DRY_RUN default) sets the PATH correctly.
2. **MII PHY + MAC over a pad loopback** (designs/eth/mii_tb/test_mii_loopback.py, written here; migen simulator): the
   Arty's PHY (LiteEthPHYMIITX/RX, eth_tx/eth_rx at 40 ns) under LiteEthMACCore (preamble/CRC on) with tx_en/tx_data
   wired to rx_dv/rx_data. Six frames of 60, 61, 64, 100, 257 and 1514 bytes: **all received equal, error flag 0; on
   the wire each frame starts with 15 nibbles 0x5 + 0xD (preamble + SFD, low nibble first) and ends with the CRC-32 that
   zlib computes for the frame** (build/eth/sim/mii_loopback.log, 232 s). LiteEth has no functional test of the MII PHY
   itself (test_phy_imports.py only imports it; the gen test builds a "wishbone_mii" core).
3. **Full SoC over a virtual network** (`flow/eth_sim.sh`, DRY_RUN default): litex_sim `--cpu-type vexriscv
   --with-ethernet --with-etherbone --with-analyzer` (Verilator, sys_clk 1 MHz), run inside `unshare -r -n` so the
   simulator's TAP device (tap0, 192.168.1.100) lives in a private network namespace and needs no root. litex_sim calls
   `sudo` to start Vsim when Ethernet is on; inside the namespace we are already uid 0, so the script puts a `sudo` shim
   (just `exec "$@"`) first on PATH. Results (build/eth/sim/litex_sim_eth/run.log and the logs next to it):
   - BIOS: "Ethernet init... Local IP: 192.168.1.50", then a netboot attempt to 192.168.1.100 (no TFTP server).
   - `ping 192.168.1.51` (Etherbone's hardware UDP/IP core): 3 sent, 3 received, 0% loss (ping_etherbone.log).
   - `ping 192.168.1.50` (CPU MAC, BIOS stack): 3 sent, 3 received (ping_ethmac.log).
   - `litex_server --udp --udp-ip 192.168.1.51`, `litex_cli --ident`: "LiteX Simulation 2026-11-06 04:07:50";
     `litex_cli --regs`: 48 CSRs read (ctrl_scratch 0x12345678, ethmac_sram_writer_length 0x46).
   - LiteScope over Etherbone: immediate capture (scope_immediate.vcd), rising-edge trigger on `simsoc_dbus_stb`
     (scope_rising_dbus_stb.vcd) and the same with `--json`: `{"triggered": true, "samples": 124, "offset": 16}`
     (litescope_json.log). The VCD holds the 16 CPU ibus/dbus signals plus scope_clk and scope_trig.
   - Note: this is the sim's own PHY model (LiteEthPHYModel, a byte stream), not the MII PHY; item 2 covers MII.
   - **LiteX issue found:** litex_sim writes analyzer.csv only when the simulation exits (LiteScopeAnalyzer.do_exit), and
     relative to the gateware directory, so litescope_cli cannot be used on a running litex_sim. flow/eth_sim_soc.py
     wraps litex_sim and exports the CSV from the pre-run callback. Draft upstream fix:
     docs/drafts/litex-sim-analyzer-csv.patch (+3/-1, litex_sim.py). Without it the first run printed
     "analyzer.csv not found" (build/eth/sim/litex_sim_eth/litescope_immediate.log of the 04:05 run, overwritten).
4. **LiteScope's own tests** (litescope d45c2387, `pytest test`): **62 passed in 70.87 s**, including
   test_sim.py::test_litescope_analyzer_over_virtual_uart (a litex_sim SoC with two analyzers, captures read back over
   the BIOS console, RLE on and off) and test_examples.py::test_arty (build/eth/sim/litescope_pytest.log).

## MARK_DEBUG → LiteScope (how a Vivado debug habit carries over)
Vivado users mark nets with `set_property MARK_DEBUG true [get_nets ...]` and then either let "Set up Debug" write
`create_debug_core u_ila_0 ila` / `connect_debug_port u_ila_0/probeN [get_nets ...]` / `C_DATA_DEPTH` lines into the
XDC, or instantiate an ILA. Vivado inserts the ILA into the synthesized netlist and talks to it over JTAG (BSCANE2 +
debug hub). Our nextpnr accepts MARK_DEBUG with a "NOT applied" warning (docs/xdc-coverage.md) and has no debug-core
commands.

`flow/mark_debug.py` (CONFIG block, DRY_RUN default) does the same job with open tools, before synthesis:
1. Reads the XDC: MARK_DEBUG nets, `connect_debug_port .../probeN` nets, `connect_debug_port .../clk`, `C_DATA_DEPTH`.
   Vivado post-synthesis names are mapped back to RTL (`dq[3]` → `dq`, `s_reg[*]` → `s`, `clk_IBUF_BUFG` → `clk`,
   `/` → `.`). Without a debug clock it uses the first `create_clock ... [get_ports X]`.
2. yosys: `read_verilog; hierarchy; proc; flatten; expose <nets>; rename <top> <top>_dbg_inner; write_verilog`. The
   marked nets become ports of the user's (flattened) design, so they survive synthesis like MARK_DEBUG nets do in
   Vivado.
3. `flow/scope_core_gen.py` (LiteX venv) generates a standalone `scope_core` (LiteX SoCMini, no CPU): one probe bus,
   LiteScopeAnalyzer, and either UARTBone (2 pins) or JTAGBone (BSCANE2 USER1, no pins, like Vivado's ILA). It writes
   analyzer.csv / csr.csv for litescope_cli.
4. A wrapper with the original top name instantiates the inner design and the core. Debug-core commands and
   MARK_DEBUG are removed from the XDC; UART pins are added for the UART bridge (Arty D10/A9, checked against the master
   XDC); the core's CDC false paths go into Vivado's copy only.

Test cases (the 16-bit x_dbg_net design from docs/xdc-coverage.md):

| design | XDC | bridge | probes |
|---|---|---|---|
| x_dbg_net_uart | designs/xdc/x_dbg_net/x_dbg_net.xdc (`MARK_DEBUG true [get_nets {dq[*]}]`) | UART | dq (16) |
| x_dbg_net_jtag | same | JTAG (BSCANE2) | dq (16) |
| x_dbg_ila_uart | designs/dbg/src/x_dbg_ila.xdc (Vivado "Set up Debug" style: create_debug_core, C_DATA_DEPTH 2048, clk = clk_IBUF_BUFG, probe0 = dq[0..15], probe1 = s_reg[0..15]) | UART | dq (16), s (16), depth 2048 |

Open flow (`python3 flow/mark_debug.py --run`, build/dbg/build_all.log): all three synth/pnr/fasm/bitstream ok
(build/dbg/<design>/gapfix/status.json).

| design | open flow: synth + pnr + fasm + bit (s) | yosys cells (LUT2-6 / FF / RAMB18E1 / BSCANE2) | nextpnr Fmax, debug clock (constraint 100 MHz) | log |
|---|---|---|---|---|
| x_dbg_net_uart | 6.54 + 11.36 + 1.92 + 0.11 | 564 / 795 / 1 / 0 | 124.66 MHz | build/dbg/x_dbg_net_uart/gapfix/ |
| x_dbg_net_jtag | 6.34 + 13.36 + 1.82 + 0.11 | 574 / 797 / 1 / 1 | 140.13 MHz (JTAG TCK domain 247.65 MHz, unconstrained in nextpnr, timed at the 100 MHz default) | build/dbg/x_dbg_net_jtag/gapfix/ |
| x_dbg_ila_uart | 7.49 + 15.93 + 1.77 + 0.11 | 661 / 951 / 0 (2 RAMB36E1: 2048 x 32) / 0 | 141.72 MHz | build/dbg/x_dbg_ila_uart/gapfix/ |

Vivado on the same files (`vivado/run_ddr3.ps1 -SrcSub designs\dbg -Tag dbg -Names x_dbg_net_uart,x_dbg_net_jtag,x_dbg_ila_uart -Run`;
outputs copied to build/dbg/<design>/viv_dbg/):

| design | Vivado synth / opt / place / route / bit (s) | LUTs / FF / BRAM tiles / BSCANE2 | Vivado WNS (10 ns) | worst path | FASM vs openXC7 (IOB, IOI, CFG) |
|---|---|---|---|---|---|
| x_dbg_net_uart | 57.58 / 16.77 / 6.92 / 31.10 / 16.45 | 571 / 801 / 0.5 / 0 | +2.861 ns | uartbone FSM → storage | IOB 62 common, 8 Vivado-only (the PUDC_B pair), IOI 126 common, 0 diff |
| x_dbg_net_jtag | 58.45 / 9.21 / 7.98 / 23.95 / 10.59 | 559 / 797 / 0.5 / 1 | +1.272 ns (clk) and +1.272 ns (jtag_tck, 50 ns), both set by the 2 ns set_max_delay on reset synchronisers | FDPE_2 → FDPE_3 | IOB 53 / 8 (PUDC_B), IOI 108 / 0, CFG 1 common (the BSCAN bit), 0 diff |
| x_dbg_ila_uart | 60.35 / 14.28 / 6.62 / 32.55 / 11.84 | 609 / 829 / 3 / 0 | +1.953 ns | bus address → analyzer offset | IOB 62 / 8 (PUDC_B), IOI 126 / 0 |

Unknown bits 0 in all six bitstreams (`python3 flow/dbg_compare.py`: build/dbg/cmp_gapfix.txt, build/dbg/<design>/cmp_gapfix_vs_dbg/). Vivado warns
"No cells matched ... ars_ff" for the UART designs (they have no reset synchroniser); harmless. In the JTAG design
Vivado times jtag_tck only because flow/mark_debug.py adds `create_clock -name jtag_tck -period 50
[get_pins u_dbg/BSCANE2/TCK]` and an asynchronous clock group to Vivado's XDC; nextpnr has no clock on TCK and times it
at its 100 MHz default (warning in nextpnr.log).

A hierarchical net also maps: `set_property MARK_DEBUG true [get_nets {u_core/cnt_reg[*]}]` on a two-module test
becomes the yosys wire `u_core.cnt` (8 bits), exposed as `\u_core.cnt` and wired to the core
(build/dbg/t_hier/, generated by a throw-away script; not built further).

Limits of the mapping (by design, not tested against every XDC form): nets must exist after `proc; flatten` under the
mapped name (yosys `select -assert-min 1` fails otherwise); bit selects are widened to the whole wire; probes in
different clock domains need one core per domain (one `connect_debug_port .../clk`); Vivado's ILA trigger features
(advanced trigger state machine, capture control, TRIGIN/OUT) have no equivalent beyond LiteScope's value/edge
triggers, subsampling and RLE; there is no GUI waveform viewer (litescope_cli writes .vcd/.sr/.csv for GTKWave or
PulseView).

## Board test plan (untested on hardware; for when the Arty is connected)
From the repo root in WSL, USB through usbipd as in docs/hardware-test-plan.md. Environment:
`export PATH=$PWD/toolchain/litex/venv/bin:$PWD/toolchain/oss-cad-suite/bin:$PATH`.
Host network: plug the Arty's RJ45 into a host NIC and give it 192.168.1.100/24, e.g.
`sudo ip addr add 192.168.1.100/24 dev <nic>` (Windows: static IPv4 192.168.1.100, mask 255.255.255.0).

1. Ethernet / Etherbone (arty_eth):
   - `openFPGALoader -b arty_a7_35t build/eth/arty_eth/viv_eth/arty_eth.bit` (Vivado reference) first, then the open
     flow's 60 MHz build `openFPGALoader -b arty_a7_35t build/eth/arty_eth_s60/gapfix/digilent_arty.bit` (meets timing
     in Vivado's timer on its placement), then the 100 MHz one, build/eth/arty_eth/gapfix/digilent_arty.bit (fails
     timing by 4.7 ns in that check: expect errors or nothing). For arty_eth_s60 use
     designs/eth/arty_eth_s60/csr.csv (same register map; only the clock frequency and ident constants differ).
   - Console: `litex_term /dev/ttyUSB1 --speed 115200`; expect "Ethernet init..." and "Local IP: 192.168.1.51" (the
     CPU MAC), then a netboot attempt to 192.168.1.100.
   - LEDs on the RJ45 (link/activity) are driven by the PHY itself; link up needs the PHY out of reset (eth_rst_n, C16).
   - `ping -c 10 192.168.1.50` (hardware UDP/IP core), `ping -c 10 192.168.1.51` (BIOS).
   - `litex_server --udp --udp-ip 192.168.1.50 &`, then with `C=designs/eth/arty_eth/csr.csv`:
     `litex_cli --csr-csv $C --ident` (expect "LiteX SoC on Arty A7 ..."), `litex_cli --csr-csv $C --regs`,
     `litex_cli --csr-csv $C --write 0x40000000 0x12345678` and `litex_cli --csr-csv $C --read 0x40000000` (main_ram
     at 0x40000000 per csr.csv).
   - Pass: both pings reply, ident matches, ctrl_scratch reads 0x12345678 and the main_ram write reads back.
2. LiteScope on the MII receive side (arty_scope):
   - Load build/eth/arty_scope/gapfix/digilent_arty.bit (or viv_eth/arty_scope.bit); start litex_server as above.
   - `litescope_cli --csv designs/eth/arty_scope/analyzer.csv --csr-csv designs/eth/arty_scope/csr.csv --list`
   - Trigger on a received frame and dump it: `litescope_cli --csv designs/eth/arty_scope/analyzer.csv --csr-csv
     designs/eth/arty_scope/csr.csv -r eth_rx_dv --offset 32 --length 1024 --dump mii_rx.vcd`, then from the host
     `ping -c 1 192.168.1.50` in a second terminal. Expect rx_dv high for the frame, rx_data = 5,5,...,5,D (preamble,
     SFD) then the frame, and main_liteethphymiirx_source_* carrying the bytes; open with `gtkwave mii_rx.vcd`.
   - The analyzer runs on the PHY's rx clock (25 MHz at 100 Mb/s, 2.5 MHz at 10 Mb/s).
3. MARK_DEBUG designs:
   - UART bridge (x_dbg_net_uart, x_dbg_ila_uart): load build/dbg/<design>/gapfix/x_dbg_net.bit (Vivado reference: build/dbg/<design>/viv_dbg/<design>.bit);
     `litex_server --uart --uart-port /dev/ttyUSB1 --uart-baudrate 115200 &`;
     `litescope_cli --csv designs/dbg/<design>/analyzer.csv --csr-csv designs/dbg/<design>/csr.csv -v main_dq 0x1234
     --dump dq.vcd` (signal names as printed by `--list`; the switches sw[3:0] change the counter step).
   - JTAG bridge (x_dbg_net_jtag), the Vivado-ILA-like case, needs no extra pins:
     `litex_server --jtag --jtag-config toolchain/litex/src/litex-boards/litex_boards/prog/openocd_xc7_ft2232.cfg &`
     (openocd from toolchain/oss-cad-suite), then the same litescope_cli command with designs/dbg/x_dbg_net_jtag/*.csv
     and signal `dq`. openFPGALoader and openocd cannot hold the cable at the same time; load first, then start the
     server.

## Open problems
- **sys_clk placement.** nextpnr's placement costs 4.6-4.7 ns at 100 MHz in Vivado's timer (Vivado's own placement of
  the same netlist: -0.12 ns). nextpnr's own timer says 87 MHz, so it is also optimistic here (its critical path
  11.49 ns vs 12.67 ns in Vivado's timer on the same placement). Placement quality is the placement agent's item; this
  design is a new benchmark for it (build/eth/xtime/src/). A board build at 100 MHz from our flow fails timing; the 60 MHz build
  (arty_eth_s60) meets all constraints in Vivado's timer on nextpnr's placement (+2.096 ns) and is the one to try
  first. Its routing is still ours, not Vivado's, and no open timer checks our routed result.
- Unloaded input pads: openXC7 enables the input buffer (IN) of top-level inputs nobody reads; Vivado does not. It has no
  logic effect; the electrical effect (an input receiver left on) was not measured. A fix would belong in nextpnr's FASM
  writer or in yosys' iopadmap; not drafted.
- The XDC constraints nextpnr cannot use: set_clock_groups, set_false_path/set_max_delay on `ars_ff*`/`mr_ff`
  attributes (dropped for nextpnr; the yosys EDIF also lacks those attributes, so the "free"/"placed" Vivado runs do not
  apply them either). `create_clock -name` is warned and ignored by the stock reader (handled by the
  nextpnr-xdc-timing draft).
- The litex_sim Ethernet run uses LiteEth's simulation PHY model, not MII; MII is covered only by the migen loopback,
  without PHY-side timing (no setup/hold of the DP83848J against the 25 MHz clocks; LiteX gives no set_input_delay /
  set_output_delay for MII, and neither do we).
- MARK_DEBUG mapping limits: see the MARK_DEBUG section. Probes are inserted at RTL level after `proc; flatten`, not into
  the post-synthesis netlist as Vivado does, so a net that only exists after synthesis (e.g. a `*_reg` net Vivado
  creates, or a LUT output) is found only if the RTL has a wire of the mapped name.
- No hardware: Ethernet link, PHY reset/strapping, MDIO, UART/JTAG bridges and captures are all untested on the board.

## Files
- flow/eth_build.py, flow/eth_scope_soc.py, flow/eth_pins_check.py, flow/eth_compare.py, flow/eth_xtime.py,
  flow/eth_sim.sh, flow/eth_sim_soc.py, flow/eth_unittests.sh
- flow/mark_debug.py, flow/scope_core_gen.py, flow/dbg_compare.py, designs/dbg/src/x_dbg_ila.xdc, designs/dbg/<design>/
- designs/eth/arty_eth/, designs/eth/arty_scope/, designs/eth/mii_tb/test_mii_loopback.py
- docs/drafts/litex-sim-analyzer-csv.patch
- toolchain/litex/src/litescope (new), toolchain/litex/COMMITS.txt, toolchain/litex/pip-freeze.txt
- build/eth/ (builds, compares, sims, logs), build/dbg/
