# IP generators and ILA debug (`ofx ip`, `ofx debug`)

Open equivalents of the Vivado IP wizards people use most (Clocking Wizard, FIFO Generator, Block Memory
Generator) and of the ILA / MARK_DEBUG flow. Each one is usable from the `ofx` CLI and from `ofx.toml`, and each is
checked against what Vivado 2025.2 itself generates (Artix-7 parts only; that is all the installed Vivado has).
Nothing here ran on hardware.

| Vivado | ofx | Code | Check against Vivado |
|---|---|---|---|
| Clocking Wizard (clk_wiz 6.0) | `ofx ip clk`, `[[ip.clk]]` | `ofx/ip_clk.py` | `flow/ip_compare.py clk` (parameters, achieved frequencies, simulation with Vivado's MMCME2_ADV/PLLE2_ADV unisim models) |
| FIFO Generator (13.2) | `ofx ip fifo`, `[[ip.fifo]]` | `ofx/ip_fifo.py` | `flow/ip_compare.py fifo` (cycle compare against fifo_generator's behavioural model) |
| Block Memory Generator (8.4) | `ofx ip bram`, `[[ip.bram]]` | `ofx/ip_bram.py` | `flow/ip_compare.py bram-sim` (unisim RAMB read-back) and `bram-bits` (INIT in both bitstreams) |
| ILA + MARK_DEBUG, Hardware Manager | `ofx debug insert`, `ofx debug capture`, `[debug]` | `ofx/debug.py`, `flow/dbg_capture.py` | simulated capture of the whole synthesized design through Vivado's JTAG_SIME2 TAP model |

Vivado references are made in batch mode with `create_ip` / `generate_target` (`vivado/ip_clk_ref.tcl`,
`vivado/ip_fb_ref.tcl`) through `flow/ip_vivado.sh`, which takes the machine-wide Vivado lock.
The simulators read Vivado's own primitive models (`data/verilog/src/unisims`) and fifo_generator's behavioural
model from the Vivado install at run time; nothing from Vivado is copied into the repository.

## Project file

```toml
[[ip.clk]]
name = "clk_gen"            # module name; ports clk_in1, clk_out1.., reset, locked (as clk_wiz)
input_mhz = 100
outputs = [148.5, {freq = 74.25, phase = 90, duty = 50}]
primitive = "MMCM"          # MMCM | PLL | auto
# in_buf = "ibuf"           # default none: the flow adds the pad buffer

[[ip.fifo]]
name = "fifo0"              # ports as fifo_generator: clk/srst or wr_clk/rd_clk/rst, din, wr_en, rd_en, dout, full, empty, ...
impl = "Common_Clock_Block_RAM"   # or Vivado's other Fifo_Implementation names
width = 32
depth = 1024
fwft = true
data_count = true
prog_full = 1000

[[ip.bram]]
name = "rom0"               # ports as blk_mem_gen: clka, wea, addra, dina, douta (+ port B)
type = "Single_Port_ROM"    # Single_Port_RAM | Simple_Dual_Port_RAM | True_Dual_Port_RAM | Single_Port_ROM | Dual_Port_ROM
width = 8
depth = 4096
init = "src/rom.coe"        # .coe or .mem
reg_a = true                # primitive output register (read latency 2)

[debug]
insert = true               # ofx build builds the design with the analyzer
probes = ["u_core.state"]   # optional; MARK_DEBUG nets in the XDC and (* mark_debug *) in the RTL are added
clock = "clk"               # default: connect_debug_port .../clk or the first create_clock port
depth = 1024                # default: C_DATA_DEPTH from the XDC, else 1024
bridge = "jtag"             # jtag (BSCANE2, USER1) or uart
```

`ofx build` generates every `[[ip.*]]` into `build/ip/` and adds it to the sources; `ofx ip gen` does only that.

## Results (2026-11-06, offline)

### ILA / MARK_DEBUG (`ofx debug`)

How it works:
1. `ofx debug insert` (also run by `ofx build` when `[debug] insert = true`) synthesizes the user design with
   yosys (`synth_xilinx -flatten -noiopad -noclkbuf`) after setting `keep` on every debug net, so the nets are
   taken from the *synthesized* netlist as Vivado's Set Up Debug does. The nets are exposed as ports of that
   netlist (`yosys expose`), and a wrapper with the original top's name connects them to a LiteScope analyzer.
2. The analyzer core comes from `flow/scope_core_gen.py` (LiteX/LiteScope). Its host bridge is JTAGBone on a
   BSCANE2 (USER1), so no UART pins are needed. A UARTBone bridge is the other option.
3. `ofx debug capture` arms a trigger, waits, uploads and writes a VCD with LiteScope's own driver.
   - The byte stream runs over USER1 DR scans in the wire format of openocd's `jtagstream`.
   - `--via sim` drives those scans through Vivado's `JTAG_SIME2` TAP model in iverilog. The model is
     connected to the BSCANE2 unisim of the **synthesized netlist of the whole design**: user logic, analyzer
     and IO/clock buffers, i.e. what `ofx build` places.
   - `--via jtag` uses a running `litex_server --jtag`, which is LiteX's openocd jtagstream, on a board. It
     has not been run on hardware.

The capture check (`ofx/debug.py` `check_trace`) works as follows:
- The testbench records the probe bus at every clock edge.
- The arming CSR writes are bracketed with simulation cycle counts.
- A capture passes when the uploaded samples are a contiguous window of that recording that starts after arming.
- With a trigger, the sample at `offset` must meet the condition, and no sample between arming and it may meet it.

| design | probes | build (open flow) | capture (`--via sim`) |
|---|---|---|---|
| `examples/dbg_ila` (XDC `MARK_DEBUG` on `dq[*]`, depth 256) | dq[16] | bitstream: 1241 LUT, 773 FF, 1 RAMB18, 1 BSCAN (FASM `CFG_CENTER_MID_X46Y32.BSCAN.JTAG_CHAIN_1`), sys clock 250.7 MHz (nextpnr timer, PASS at 100) | no trigger: 252 samples, PASS; trigger `dq=0b1111xxxxxxxx0000` offset 32: PASS (trigger sample = first match after arming, cycle 16392); 117 DR scans, 21,008 TCK cycles, ~45 s wall each |
| `examples/dbg_rtl` (RTL `(* mark_debug = "true" *)` on two regs of a submodule, depth 128) | u_core.cnt[8], u_core.state[3] | insert only | trigger `u_core.state=0x2` offset 4: PASS, 124 samples |

Findings:
- **LiteScope stores the trigger sample 2 samples before `offset`.** In the first triggered run the condition was
  first met at `data[offset-2]`. ofx asks the analyzer for `offset + 2` (`CONFIG["trigger_latency"]`), so the
  trigger sample lands at the requested index, as in Vivado's ILA.
- **LiteScope returns depth − 4 samples.** It keeps 4 samples in its 4-deep clock-crossing FIFO, and `upload()`
  reads only `mem_level`. 252 of 256 and 124 of 128 are LiteScope's behaviour, not a transport loss.
- **No tx byte was refused.** No target-not-ready bit was seen on any tx word after the first scan.
- **The JTAG TCK domain has no create_clock.** Vivado's ILA flow constrains it; this is a gap.

Not done:
- hardware;
- ILA advanced trigger state machines;
- a waveform GUI (the output is VCD);
- capture in a simulation of the bitstream-decoded netlist.

### Block Memory Generator (`ofx ip bram`)

Primitive read-back (`flow/ip_compare.py bram-sim`):
- Each of the 7 configurations of `designs/ip/bram_configs.txt` was generated.
- The generated memory was simulated with Vivado's RAMB36E1/RAMB18E1 unisim models.
- Every address was read back against the `.coe`, on both ports for true dual port. For RAMs, a 64-word write and
  read-back followed.
- Result: **13,568 reads, 0 mismatches.**

| config | memory | ofx tiling |
|---|---|---|
| b01 | Single_Port_RAM 32x1024 | 1 RAMB36E1 TDP 36x1024 |
| b02 | Single_Port_ROM 8x4096, output register | 1 RAMB36E1 TDP 9x4096 |
| b03 | True_Dual_Port_RAM 16x2048 | 1 RAMB36E1 TDP 18x2048 |
| b04 | Simple_Dual_Port_RAM 36x512, output register | 1 RAMB18E1 SDP 36x512 |
| b05 | Single_Port_ROM 18x1024 | 1 RAMB18E1 TDP 18x1024 |
| b06 | Single_Port_ROM 64x2048 | 4 RAMB36E1 TDP 18x2048 (4 columns) |
| b07 | Single_Port_RAM 72x512 | 2 RAMB36E1 TDP 36x1024 |

Bit mapping, as blk_mem_gen: the low data bits go to DI and the top bits to DIP. An 18-bit word is
{DIP[1:0], DI[15:0]}.

All 7 test tops (`designs/ip/bram/<n>_top.v`) build to bitstreams with `ofx build` from a project file with
`[[ip.bram]]` (`build/ip_compare/bram_bits/<n>/ofx.toml`).

### Clocking Wizard (`ofx ip clk`)

Simulation (`flow/ip_compare.py clk`):
- Each of the 26 requests of `designs/ip/clk_requests.txt` was solved and its Verilog generated.
- The Verilog was simulated with Vivado's MMCME2_ADV / PLLE2_ADV unisim models.
- Checks on every output:
  - frequency within 200 ppm of the request (all achieved frequencies are exact or within 10 ppm by construction);
  - duty within 0.2 %;
  - phase relative to CLKOUT0 within 60 ps.
- Result: **26 of 26 pass**:
  - MMCM: 18 requests on -1, 2 on -2 and 1 on -3 parts;
  - PLL: 5 requests (one on -3);
  - up to 7 outputs;
  - phases 45/90/180/270°;
  - duties 25 % and 40 %.
- The MMCM outputs are aligned to the input edge (offset 0 to 2 ps).
- The PLL model puts every output 0.25 to 0.33 ns before the input edge, the same for all outputs of a PLL.
  This is recorded, not hidden; it will be checked on Vivado's own clk_wiz output in the same testbench.

### FIFO Generator (`ofx ip fifo`)

Scoreboard check (`flow/ip_compare.py fifo-self`):
- All 10 configurations of `designs/ip/fifo_configs.txt` were simulated:
  - built-in FIFO18E1 with Vivado's unisim models: common clock standard, common clock FWFT, independent clocks;
  - block and distributed RAM, common and independent clocks, standard and FWFT;
  - prog_full/prog_empty, counts and flags.
- Stimulus: 6000 cycles of random writes and reads in fill-heavy, drain-heavy and balanced phases. The independent
  clocks were 10 ns and 13.7 ns.
- Every word was read back in order: **0 mismatches**. Each FIFO accepted 3170 to 4578 words.
- The primitive model found one ofx bug, now fixed: FWFT is not allowed with EN_SYN = TRUE. A common-clock FWFT
  built-in FIFO now runs the primitive with EN_SYN = FALSE and DO_REG = 1.

Not yet compared with Vivado. The cycle-by-cycle comparison with fifo_generator's behavioural model (`fifo`
subcommand) is written but has no Vivado references yet, so flag timing (empty/full latency, prog thresholds,
counts) is unchecked against Vivado.

## Pending: Vivado references

The clk_wiz, fifo_generator and blk_mem_gen references have not been generated. After about 2.5 hours behind the
placer/router Vivado jobs, the low-priority queue was stopped.

Restart it with `bash flow/ip_vivado_queue.sh`. It runs 4 batches of under 20 minutes each, releases the lock
between them, and yields to other waiters. Then run:

```
python3 flow/ip_compare.py clk --run
python3 flow/ip_compare.py fifo --run
python3 flow/ip_compare.py bram-bits --run
```

The open-flow bitstreams for `bram-bits` are already built and cached.
