# yosys-xilinx-dsp-pipeline (draft, not posted)

Base: YosysHQ/yosys 3718f7f13 (= oss-cad-suite's Yosys 0.70+186). Worktree build/src/yosys-dspqor.
+425/-3 in techlibs/xilinx/{xilinx_dsp.cc, xilinx_dsp_cascade.pmg, synth_xilinx.cc}.
Opt-in: `xilinx_dsp -pipeline`, `synth_xilinx -dsp_pipeline`. Without the option the pass takes exactly the old path.

## Problem (docs/qor-vivado.md Finding 5)
picorv32's `rd <= $signed(rs1) * $signed(rs2)` (33x33, registers before and after) maps to 4 DSP48E1 in two PCIN
pairs. Two things were lost:
1. The input registers of the signed (upper) slices were not packed (AREG/BREG = 0 on two DSPs). `opt_dff` gives
   the sign bit `rs1[32]` its own `$sdffce` (reset = "operand unsigned"), so the 16 bits feeding the upper A slice
   come from two register cells, and `in_dffe` only matches one cell.
2. The output register `rd` sits after the fabric adder that sums the two PCIN pairs, so it never reaches PREG;
   the critical path was FF -> A->PCOUT -> PCIN->P -> CARRY4 chain -> FF.
In the FIR (designs/qor/qor_fir), the x delay line (two registers per tap) stayed in the fabric (1024 FFs) because
the A cascade only accepted one register between DSPs ("TODO: Check for two levels of flops").

## Change (all under `-pipeline`, xc7 only)
- `xilinx_dsp_merge_input_ffs`: when one DSP's A or B input is driven by several register cells with the same
  clock and enable, they are merged into one cell; a synchronous reset that not all bits share is first moved
  into the D logic (`FfData::unmap_srst`). Then the normal matcher packs A2REG/B2REG.
- xilinx_dsp_cascade.pmg: if the upstream DSP has AREG=2 (BREG=2) and the downstream A (B) input is two registers
  after the upstream A (B) input, with matching enables/resets, use ACOUT->ACIN with ACASCREG=2 (BCASCREG=2).
- `xilinx_dsp_retime_output_ffs` (after cascade detection): a `$dff`/`$dffe` without reset, with positive clock and
  an all-x init, whose D is a tree of fabric `$add` cells whose leaves are all DSP48E1 P bits (PREG=0) is moved
  back to the leaves (one register per DSP); the adder tree then follows the register. Each moved register is
  packed into PREG when the DSP's P feeds nothing else and PCOUT is unused; otherwise it stays in the fabric
  (17 bits per PCIN pair on picorv32, like Vivado's `*_psdsp` registers).

## Evidence (offline)
- Plugin build of the same sources (toolchain/buildenv/build_yosys_dsp_plugin.sh -> build/yosys-plugin/xilinx_dsp_qor;
  flow/qor_bench.py variants `dspq_off` / `dspq` run synth_xilinx in two halves around `xilinx_dsp_qor`).
- No-op: without `-pipeline`, the yosys JSON is byte-identical to plain synth_xilinx for fir, rv_soc, bram,
  blinky; for rv_mul/rv_big only two auto-generated cell names differ (pmgen header line numbers in `$auto$...`),
  and the nextpnr `.frames` are identical (build/qor/oxc7/dspq_off vs fix_static).
- picorv32_pcpi_fast_mul alone: all 4 DSPs AREG=BREG=1, two with PREG=1; 34 retimed FFs stay in fabric.
  Random simulation of the off and on netlists (iverilog + yosys cells_sim.v, 200000 cycles, MUL/MULH/MULHSU/MULHU
  with corner operands): 59503 results compared, 0 mismatches (build/qor/dsp/sim/fm_off_vs_on.log).
- FIR, whole design: 200000 cycles with random coefficient loads, LEDs and UART bit compared every cycle: 0
  mismatches (build/qor/dsp/sim/fir/result.log). FF count 1589 -> 597 (Vivado 598).
- Cell counts (stat -tech xilinx): rv_mul LUT 1397 -> 1422, FF 1073 -> 1011; rv_big LUT 1448 -> 1463, FF 1108 -> 1046.
- Timing: docs/qor-vivado.md Finding 8.

## Open
- Full in-tree build done (toolchain/buildenv/build_yosys_full.sh, bison/flex from conda-forge in
  toolchain/buildenv/env-bisonflex, log build/yosys-build/yosys-dspqor.build2.log; no warning in the changed files):
  `synth_xilinx -dsp_pipeline` gives the same cell types and DSP register settings as the plugin on rv_mul, rv_big,
  fir and rv_soc, and without the option the same as the oss-cad-suite yosys. No yosys test suite was run.
- On the FIR, Vivado's P&R of the pipelined netlist is slower than of the default one (205.68 vs 215.75 MHz).
- Only `$add` trees are retimed (no `$sub`, no `$alu`, no registers with reset or init).
- MREG is not used for multiplier pairs without a following register.
