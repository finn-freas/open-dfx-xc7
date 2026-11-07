# Phase 5: rv_soc, a PicoRV32 static design with a reconfigurable custom-instruction slot

Status: simulated and built with the open flow (yosys + nextpnr-xilinx + prjxray). **Not run on a board.**

## What exists

| Path | Content |
|---|---|
| `upstream/YosysHQ_picorv32` | `git clone --filter=blob:none https://github.com/YosysHQ/picorv32`, commit `ef203c2b0a3fb793280f5114941416c425c5b461` (2026-09-07, "Merge pull request #296 from YosysHQ/krys/archiving") |
| `designs/rv_soc/picorv32.v` | byte-identical copy of `picorv32.v` from that commit (`cmp` clean) |
| `designs/rv_soc/rv_soc.v` | top `rv_soc` (CPU, 8 KiB BRAM, MMIO, UART, ICAPE2) and `rm_bridge` (PCPI to `rm_slot` adapter with timeout) |
| `designs/rv_soc/uart.v` | `uart_rx`/`uart_tx`, lines 1-57 of `designs/pr_uart/uart_icap.v` unchanged |
| `designs/rv_soc/sim/rm_add.v`, `sim/rm_xor.v` | the two RMs (`module rm_slot`), rd = rs1+rs2 / rs1^rs2, registered, ready one cycle after valid. Plain synthesizable Verilog; `rm_add.v` is also used for the implementation check |
| `designs/rv_soc/tb/` | `icape2_model.v` (captures writes, returns `C0DE0000+n` on reads), `rm_dead.v` (never answers, tests the timeout), `tb_isa.v`, `tb_rv_soc.v` |
| `designs/rv_soc/fw/main.s`, `fw/main.hex` | firmware and its 2048-word `$readmemh` image |
| `designs/rv_soc/fw/isa_test.s` | assembler/CPU self-test program |
| `designs/rv_soc/arty_a7_35t.xdc` | same pins as `designs/pr_uart` (clk E3, led H5/J5/T9/T10, uart_txd_in A9, uart_rxd_out D10, LVCMOS33, Digilent Arty-A7-35-Master.xdc) |
| `designs/rv_soc/run_sim.sh` | assembles both programs and runs all five simulations |
| `flow/rvasm.py` | two-pass RV32I assembler |

## CPU configuration and the PCPI mapping

`picorv32` (the native-memory core, not axi/wb) with `ENABLE_PCPI=1, ENABLE_MUL=0, ENABLE_FAST_MUL=0, ENABLE_DIV=0, ENABLE_IRQ=0, ENABLE_COUNTERS=0, ENABLE_COUNTERS64=0, TWO_STAGE_SHIFT=0, BARREL_SHIFTER=0, COMPRESSED_ISA=0, CATCH_MISALIGN=0, CATCH_ILLINSN=1, ENABLE_REGS_DUALPORT=1, PROGADDR_RESET=0`.

What the source says (line numbers in `picorv32.v` at the commit above):

- 110-117: PCPI ports. 191-192: `pcpi_rs1 = reg_op1`, `pcpi_rs2 = reg_op2`.
- 679-685: `instr_trap` is every instruction the core does not decode itself; custom-0 (opcode `0001011`) is one of them, so it goes to PCPI. 1038: `pcpi_insn <= mem_rdata_q`.
- 1585-1616 (with `ENABLE_REGS_DUALPORT=1`): in `cpu_state_ld_rs1` the core raises `pcpi_valid` and keeps re-asserting it with rs1/rs2 every cycle until `pcpi_int_ready`; then it takes `reg_out <= pcpi_int_rd`, `latched_store <= pcpi_int_wr` and drops `pcpi_valid`. So `pcpi_valid` is a level, not a pulse, and `pcpi_wr` must be high with `pcpi_ready` for rd to be written.
- 326-335: `pcpi_int_ready/wr/rd` come straight from the external `pcpi_ready/wr/rd` when `ENABLE_PCPI` and the mul/div units are off.
- 1423-1430 and 1605: with `CATCH_ILLINSN=1` the core has its own 16-cycle timeout that counts only while `pcpi_valid && !pcpi_wait`; on expiry it traps. `CATCH_ILLINSN` is kept on so a truly unknown instruction still traps instead of hanging.
- 565-637: after `mem_ready` the core drops `mem_valid` for at least one cycle, so a single `mem_valid && !mem_ready` access strobe is safe for side-effect registers (UART RX pop).

`rm_bridge` therefore does:

- `pcpi_wait = pcpi_valid && pcpi_insn[6:0] == 7'b0001011` (combinational), which stops the 16-cycle trap counter for custom-0 only.
- IDLE: on a custom-0 `pcpi_valid`, register `funct = {insn[31:25], insn[14:12]}`, rs1, rs2, and pulse `valid` for one cycle. rs1/rs2/funct stay in static registers until the next instruction.
- BUSY: accept `ready` only after the `valid` cycle, latch `rd`, and return `pcpi_ready=pcpi_wr=1` for one cycle. If `ready` has not come after `TIMEOUT=64` cycles, complete with `rd=0` and count it (`timeouts`, readable at `+0x18`).
- DONE: one cycle back to IDLE (the core drops `pcpi_valid` on the edge where it saw `pcpi_ready`).

`ready` is ignored outside BUSY, so a reconfiguring RM toggling its outputs cannot complete an instruction that was never issued. It can still answer a *later* instruction with a stale `ready` from one that timed out: there is no transaction tag in the fixed `rm_slot` interface.

## Memory map

| Address | Access | Function |
|---|---|---|
| `0x0000_0000`-`0x0000_1FFF` | R/W, byte strobes | 8 KiB BRAM (2048 x 32), `$readmemh(MEM_INIT)`, default `designs/rv_soc/fw/main.hex` (path is relative to the repo root; yosys and iverilog are run from there). Aliased over `0x0xxx_xxxx` |
| `0x1000_0000` | W / R | LEDs, bits 3:0 |
| `0x1000_0004` | W | UART TX byte. Also blocks in hardware (no `mem_ready` while busy) |
| `0x1000_0008` | R | bit0 = TX busy |
| `0x1000_000C` | R | `{valid(bit8), byte[7:0]}`, pops a 16-deep RX FIFO when valid |
| `0x1000_0010` | W | ICAP write: `I = per-byte bit swap(wdata)`, `CSIB=0, RDWRB=0` for one cycle |
| `0x1000_0014` | R | ICAP read: `RDWRB=1` (CSIB high), then one `CSIB=0` cycle, wait 4 cycles, return `bswap(O)`, `RDWRB=0` |
| `0x1000_0018` | R | status `{8'd0, rx_overruns[7:0], slot_timeouts[15:0]}` (extra, not in the original spec) |

UART: 8N1, `CLKS_PER_BIT=100` (1 Mbaud at 100 MHz). `ICAPE2 #(.ICAP_WIDTH("X32"))`.

## Assembler: flow/rvasm.py

`python3 flow/rvasm.py SRC -o OUT.hex [--lst OUT.lst] [--base 0] [--words 2048]`. Two passes. Labels (`name:`), whole-line `#` comments only, `.equ`, `.word`, `.org`. Immediates: decimal, hex, binary, `'c'`, symbols, `+`/`-`.
RV32I: lui auipc jal jalr beq bne blt bge bltu bgeu lb lh lw lbu lhu sb sh sw addi slti sltiu xori ori andi slli srli srai add sub sll slt sltu xor srl sra or and ecall ebreak fence. Pseudos: li (1 or 2 words, lui+addi with rounding), la (always lui+addi), mv, not, nop, j, call, ret, beqz, bnez. `custom0 rd, rs1, rs2, funct7, funct3` emits R-type with opcode `0001011`. Range checks on every immediate/offset.

## Evidence

All commands from `~/open-dfx-xc7`.

### Encoding cross-check against a published reference

`upstream/YosysHQ_picorv32/testbench_ez.v` lines 64-69 contain a hand-assembled program with its source. Assembling the same source plus `nop` / `ret` / `ecall` (canonical encodings `00000013`, `00008067`, `00000073`; the RISC-V unprivileged spec defines NOP as `ADDI x0, x0, 0`):

```
3fc00093 3fc00093 MATCH      li x1, 1020
0000a023 0000a023 MATCH      sw x0, 0(x1)
0000a103 0000a103 MATCH      lw x2, 0(x1)
00110113 00110113 MATCH      addi x2, x2, 1
0020a023 0020a023 MATCH      sw x2, 0(x1)
ff5ff06f ff5ff06f MATCH      j loop   (backward jal)
00000013 00000013 MATCH      nop
00008067 00008067 MATCH      ret
00000073 00000073 MATCH      ecall
```

### Encodings against picorv32's own decoder (tb/tb_isa.v)

`fw/isa_test.s` runs on the full `rv_soc` and stores 38 results to `0x1000+4k`: every R/I/shift ALU op (incl. sign cases), `lui`, `auipc` (checked against `la`), all loads with sign/zero extension at offsets 0/2, `sb`/`sh` into byte/halfword lanes, all six branches taken and not taken plus a backward loop, `jal` and `jalr` link values, `custom0` with funct `{0,0}` and `{0x7f,7}`, and an ICAP read through `+0x14`. The testbench checks every value, that the CPU never traps (an encoding the core does not decode would go to PCPI and, without `pcpi_wait`, trap after 16 cycles), and that the RM saw funct `000` then `3ff`.

`bash designs/rv_soc/run_sim.sh` output (verbatim):

```
isa_test[rm_add]: 38 results checked, 2 custom0 issues, timeouts=0, finished in 772 cycles
PASS: tb_isa rm_add
isa_test[rm_xor]: 38 results checked, 2 custom0 issues, timeouts=0, finished in 772 cycles
PASS: tb_isa rm_xor
isa_test[rm_dead]: 38 results checked, 2 custom0 issues, timeouts=2, finished in 896 cycles
PASS: tb_isa rm_dead
```

`rm_dead` never asserts `ready`: both custom0 complete with rd=0 via the 64-cycle timeout and the program continues (124 cycles more, i.e. about 2 x 62).

### UART-level SoC test (tb/tb_rv_soc.v), firmware fw/main.hex, CLKS_PER_BIT=100

```
ok:   C 12345678 11111111 -> 23456789 (rm_add)
ok:   led=9
ok:   C ffffffff 00000003 -> 00000002 (rm_add)
ok:   led=2
ok:   W 8 words -> 'K'
ok:   ICAP word 0 sent ffffffff captured ffffffff
ok:   ICAP word 1 sent aa995566 captured 5599aa66
ok:   ICAP word 2 sent 20000000 captured 04000000
ok:   ICAP word 3 sent 30008001 captured 0c000180
ok:   ICAP word 4 sent 00000007 captured 000000e0
ok:   ICAP word 5 sent 12345678 captured 482c6a1e
ok:   ICAP word 6 sent 80000001 captured 01000080
ok:   ICAP word 7 sent 0f1e2d3c captured f078b43c
ok:   C a5a5a5a5 0f0f0f0f -> b4b4b4b4 (rm_add)
ok:   led=4
PASS: tb_rv_soc rm_add
ok:   C 12345678 11111111 -> 03254769 (rm_xor)
ok:   led=9
ok:   C ffffffff 00000003 -> fffffffc (rm_xor)
ok:   led=c
ok:   W 8 words -> 'K'
ok:   ICAP word 0 sent ffffffff captured ffffffff
...(same 8 ICAP lines)...
ok:   C a5a5a5a5 0f0f0f0f -> aaaaaaaa (rm_xor)
ok:   led=a
PASS: tb_rv_soc rm_xor
```

Same firmware, same static logic; only the `rm_slot` file differs, and the `C` results change from a+b to a^b. That is how the swap is modelled (it is a re-elaboration, not a simulated partial reconfiguration). The sync word `AA995566` arrives at ICAP as `5599AA66`, the per-byte bit-swapped form ICAP X32 expects.

### Implementation with the open flow

```
python3 flow/build_openxc7.py rv_soc --top rv_soc --rtl rv_soc.v uart.v picorv32.v sim/rm_add.v --run
```

`--rtl` is needed because the default glob would miss `sim/rm_add.v`. Outputs in `build/openxc7/rv_soc/xc7a35tcsg324-1_s1/` (`rv_soc.bit`, 2192181 bytes; logs; `versions.json`: yosys 0.70+186, openXC7 `upstream-2026-11-04`, nextpnr-xilinx `ce3f7c18`, prjxray-db `a8b09269`).

| Resource | Used | Source |
|---|---|---|
| LUTs (yosys LUT2-6) | 1062 (+14 RAM32M = regfile and RX FIFO) | `yosys.log` |
| SLICE_LUTX (nextpnr) | 1786 / 65200 | `nextpnr.log` (counts LUT bels incl. RAM32M and carry-shared LUTs) |
| FFs | 764 (749 FDRE + 15 FDSE) | both |
| CARRY4 | 108 | nextpnr |
| RAMB36E1 | 2 / 75 | `report.json` |
| ICAP | 1 / 2 | `report.json` |

Timing: `Info: Max frequency for clock 'u_bridge.clk': 159.92 MHz (PASS at 100.00 MHz)` (final, post-route; the pre-route estimate was 185.43 MHz). 0 errors, 1 warning (`ignoring unsupported XDC option '-name'` from `create_clock`, same as other designs). The critical path starts at `u_cpu.latched_branch` and runs through a CARRY4 chain inside the CPU, not through the slot.

BRAM init: the `RAMB36E1` `INIT_00` parameters in the yosys netlist match `main.hex` (`ram.0.0` = low 16 bits of words 0-15, `ram.0.1` = high 16 bits). The two used BRAM tiles have non-zero `INIT_xx` lines in the FASM; their bit-level FASM encoding was **not** checked against the hex.

## Unverified

- No hardware run: UART at 1 Mbaud, LEDs, BRAM contents after configuration and ICAPE2 behaviour are simulated or inferred only.
- ICAP read timing (`+0x14`) follows the model in `tb/icape2_model.v`, not the real ICAPE2 latency (UG470); a real readback also needs a command sequence written first.
- The custom-instruction slot is not yet a reconfigurable partition: `rm_slot` is flattened into the static netlist here. Region floorplanning, the PR shell and decoupling are future work.
- No proof that the slot boundary signals are stable while reconfiguring; the bridge only ignores `ready` outside BUSY and times out.
- A late `ready` from a timed-out instruction can be taken as the answer to the next custom0 (the interface has no tag).
- The firmware echoes nothing on unknown command bytes and has no checksum on `W` data.
