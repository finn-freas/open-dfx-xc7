# yosys-xilinx-area-opts (draft, not posted)

Base: YosysHQ/yosys 3718f7f13 (= oss-cad-suite's Yosys 0.70+186). Worktree build/src/yosys-area, full in-tree
build build/yosys-build/yosys-area/yosys (toolchain/buildenv/build_yosys_full.sh, log
build/yosys-build/yosys-area.build.log; no warning in the changed files). +35/-3 in
techlibs/xilinx/{synth_xilinx.cc, arith_map.v}. Both options are off by default.

## Problem (docs/qor-vivado.md Finding 11)
yosys gives the same number of LUT cells as Vivado on the CPU benchmarks (rv_soc 1107 vs 1106 at 5 ns) but
20-46 % more CARRY4:
- `synth_xilinx` runs `share` without `-aggressive`, and plain `share` never considers `$alu` cells. picorv32
  computes `alu_add_sub` as `instr_sub ? reg_op1 - reg_op2 : reg_op1 + reg_op2` and has several more 32-bit
  additions whose results are selected by the state machine (`reg_pc + decoded_imm`, `reg_op1 + decoded_imm`, ...),
  so each becomes its own 8-CARRY4 chain (rv_soc: 7 x 32-bit `$alu` = 56 of the 92 CARRY4).
- `arith_map.v` maps every `$alu`/`$lcu` of 3 bits or more to CARRY4; rv_soc has 8 adders of 3-8 bits
  (counters, FIFO pointers) that take 18 CARRY4.

## Change
- `synth_xilinx -share_aggressive`: runs `share -aggressive` instead of `share` in the `coarse` step.
- `synth_xilinx -carry_minwidth <n>`: passes `-D CARRY_MINWIDTH=<n>` to the `fine` techmap; `_80_xilinx_alu` and
  `_80_xilinx_lcu` in arith_map.v refuse widths below it (default 3 = the old `<= 2` test), so the generic
  techmap.v implementation (LUTs) is used instead.
- The help text and `help synth_xilinx` script show both.

## Evidence
See docs/qor-vivado.md Finding 11: cell counts, nextpnr post-route area and Fmax (variants `area_share`,
`area_cmw`, `area_all`), yosys `equiv_*` proofs (flow/qor_area_equiv.sh) and lockstep simulation of the old and
new netlists under the rv_soc firmware test (flow/qor_area_sim.sh).
