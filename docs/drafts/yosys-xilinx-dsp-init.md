# yosys-xilinx-dsp-init (draft, not posted)

Base: YosysHQ/yosys 3718f7f13 (= oss-cad-suite's Yosys 0.70+186). Worktree build/src/yosys-dspinit, build
build/yosys-build/yosys-dspinit (toolchain/buildenv/build_yosys_full.sh, log build/yosys-build/yosys-dspinit.build.log).
+21/-21 in techlibs/xilinx/xilinx_dsp.cc. Every changed line replaces one line, so the `__LINE__` in `NEW_ID` names
below the edits does not move and netlists that do not hit the bug keep their cell names.

## Problem
`synth_xilinx` aborts in `xilinx_dsp` with
`ERROR: Assert 'it->second[i] == State::S0 || it->second[i] == State::Sx' failed in techlibs/xilinx/xilinx_dsp.cc:400`
when a register feeding a multiplier, or the register after it, is one cell with other bits that have a 1 init.
Repro (plain Verilog, build/ofx/vhdl/yosys_dsp_init_assert/rep.v):

```verilog
reg [31:0] q = 32'h1;   // bit 0 is 1
...
prod <= q[31:16] * acc; // only q[31:16] go to the DSP
```

## Cause
The matchers (`in_dffe` and `out_dffe` in xilinx_dsp.pmg, xilinx_dsp48a.pmg, xilinx_dsp_CREG.pmg) check the init of
the bits that go into the DSP register (`argQ`) and reject a match with a 1 there, since the DSP48 registers
power up at 0. The packer (`f` in `xilinx_dsp_pack`, `xilinx_dsp48a_pack`, `xilinx_dsp_packC`) then walks
**all** of the register cell's Q bits, asserts that each init is 0 or x and sets it to x. A bit outside the slice
that went into the DSP can have a 1 init; that bit stays in the fabric, and the assert fires.

## Change
`f` gets the bits that are absorbed (the DSP port before the replacement, or `sigM`/`sigP` for MREG/PREG) and only
walks `Q.extract(pm.sigmap(absorbed))`. The behaviour is now:
- bits that go into AREG/BREG/DREG/CREG/MREG/PREG: as before (their init must be 0 or x, otherwise no match, and it
  is cleared to x);
- a register whose absorbed bits have a 1 init: not packed, stays in the fabric (unchanged, matches Vivado: DSP48E1
  registers have no init);
- other bits of the same register cell: their init is kept (before: the assert for a 1; a 0 was turned into x).

## Evidence (offline, 2026-11-06; flow/yosys_dsp_init_check.py, results build/yosys_dsp_init/report.json)
| case | stock yosys (oss-cad-suite) | fixed | simulation, 5000 cycles | SAT on gold (before map_dsp) vs gate (after) |
|---|---|---|---|---|
| rep (q init 32'h1, q[31:16] to A) | assert | 1 DSP48E1 AREG=2 BREG=1 MREG=1; 48 FF, q[0] INIT 1 | 0 mismatches | no counterexample in 12 cycles (induction does not close) |
| rep2 (init 0; passed before) | 1 DSP, AREG=2 | same DSP; 15 fabric FFs of q keep INIT 0 (stock: x) | 0 / 0 | 12 cycles, no counterexample |
| rep_in1 (1 init inside the A slice) | AREG=0 (stays in fabric) | identical netlist | 0 / 0 | 12 cycles, no counterexample |
| rep_p1 (product register shares a cell with a 1-init bit) | assert | MREG=1, the 1-init bit stays an FDRE with INIT 1 | 0 mismatches | proven (temporal induction) |
| rep_p1in (product register with its own 1 init) | MREG=0, PREG=0 (stays in fabric) | identical netlist | 0 / 0 | SAT timeout at 900 s |

- Simulation: iverilog, RTL against the full `synth_xilinx` netlist with yosys' cells_sim.v (DSP48E1 model), random
  `en`/`a`/`b`, outputs compared every cycle from power-up. FDRE INIT x is simulated as 0, the FDRE default.
- "identical netlist": the written Verilog differs only in the yosys version header.
- No-op: `synth_xilinx -flatten -abc9` JSON of blinky, rv_soc and qor_rv_mul (which maps its multiplier to DSPs) is
  identical between oss-cad-suite's yosys and the fixed build, apart from the `creator` line and the share directory
  in `src` attributes of abc9_model.v cells (build/yosys_dsp_init/noop/).
