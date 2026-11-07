# AXI interconnect: 2 masters x 4 slaves with the open flow and with Vivado

Roadmap row "AXI interconnect / Block Design". Vivado's equivalent is an AXI Interconnect/SmartConnect IP in a block
design. The open equivalent here is hand-instantiated RTL: Alex Forencich's verilog-axi (MIT, 516bd5d, 2025-02-27)
`axi_crossbar` with `axi_ram` slaves. There is no block-design GUI or IP packager; the wiring is Verilog.

## Design: examples/axi_xbar
- `src/axi_xbar.v`: two `axi_tg` masters -> `axi_crossbar` (S_COUNT 2, M_COUNT 4, 32-bit data, 14-bit address,
  4-bit master IDs, 5-bit slave IDs, default register slices and 2 threads / 16 accepts per master) -> four 4 KB
  `axi_ram` slaves at 0x0000/0x1000/0x2000/0x3000. 100 MHz Arty A7-35T clock pin, 4 LEDs (sticky error, per-master
  progress, heartbeat). Power-on reset from a 4-bit shift register, so no reset pin.
- `src/axi_tg.v` (written here): a traffic generator and checker per master: a 4-beat INCR write burst to an
  LFSR-chosen address (16-byte aligned, every slave reachable, bit 9 fixed per master so the two masters never write
  the same words), wait for B, read the burst back and compare data, RRESP, RID and RLAST. Any mismatch sets `err`.
- verilog-axi files copied unchanged into `src/` with their MIT headers: axi_crossbar{,_addr,_rd,_wr}.v,
  axi_register_{rd,wr}.v, arbiter.v, priority_encoder.v, axi_ram.v.

## Verification (offline)
- RTL simulation (`sim/tb_axi_xbar.v`, iverilog 2 ms at 100 MHz): 8333 / 8332 write+read-back transactions by the two
  masters, writes reach all four slaves (4122 / 4184 / 4183 / 4177 bursts), no error: PASS.
- Fault injection (`-DINJECT`: one read-data bit forced to 1 after 1 ms): the checker flags it at 1000.815 us: the
  test can fail.
- Gate-level simulation of the yosys netlist (`write_verilog` of build/impl/axi_xbar.json + yosys' Xilinx
  `cells_sim.v`, LED-only testbench): both masters' progress LEDs toggle > 100 times in 2 ms, error LED stays 0: PASS.
- Not on a board.

## Open flow
`bin/ofx build` (yosys 0.70+186 `synth_xilinx -flatten -abc9`, openXC7 nextpnr-xilinx ce3f7c18, stock chipdb):
- yosys cells: 1476 LUTs (1/342/427/363/239/104 for LUT1..LUT6), 1258 FFs (1223 FDRE, 35 FDSE), 95 CARRY4,
  4 RAMB36E1, 1 MUXF7, 1 SRL16E.
- nextpnr: 2172 LUT bels, 1258 FFs, 99 CARRY4, 4 RAMB36E1; **152.63 MHz** (nextpnr's own timer).
- Same result with a 5 ns target (build/axi_xbar/ofx_5ns): 152.63 MHz again, so nextpnr's placement does not react to
  the period here (as noted in docs/qor-vivado.md); nextpnr then fails the build at 200 MHz without
  `--timing-allow-fail`.

## Vivado 2025.2 on the same RTL
Pending (vivado/build_rtl.tcl through run_qor.ps1 -Tag axi; Vivado timer on nextpnr's placement via
flow/xtime_prep.py + vivado/build_xtime.tcl -Tag axi_xtime).

## Files
- examples/axi_xbar/ (ofx project, sources, testbench), build/axi_xbar/ (5 ns build, Vivado sources, xtime staging)
- vivado/build_rtl.tcl, flow/xtime_prep.py
