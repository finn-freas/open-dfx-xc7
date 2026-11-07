# yosys-opt-dff-keep-memrd-regs (draft, not posted)

Base: YosysHQ/yosys 3718f7f13 (= oss-cad-suite's Yosys 0.70+186). Worktree build/src/yosys-synx, full in-tree
build build/yosys-build/yosys-synx/yosys (toolchain/buildenv/build_yosys_full.sh, JOBS=2, log
build/yosys-build/yosys-synx.build.log). +26/-0 in passes/opt/dff/{simple.cc, opt_dff.cc}. Off by default; on with
`scratchpad -set opt_dff.keep_memrd_regs 1` before `synth_xilinx` (no synth_xilinx change needed).

## Problem (docs/qor-vivado.md Findings 12 and 14)
The LiteX DDR3 SoC (arty_ddr3) used 320 LUTRAM sites against Vivado's 142. 176 of them are one memory: the L2
cache tag memory `tag_mem`, 512 x 22, single port, synchronous write-first read:

    if (we) tag_mem[adr] <= dw;
    if (we) tag_mem_dat0 <= dw; else tag_mem_dat0 <= tag_mem[adr];

Two bits of the written tag are constant 0 in this SoC. During `synth_xilinx`'s `prepare` step, `opt` (opt_dff)
sees `tag_mem_dat0[20:19] <= we ? 0 : rdata` and turns those two bits into a `$sdff` with sync reset `we`. The
read-data register is now split into a `$sdff` (2 bits) and a `$dff` (20 bits). `memory_dff` runs later
(`memory -nomap` in `coarse`) and, since no single FF covers the read data, reports "no output FF found" for
tag_mem. The read port stays asynchronous, block RAM cannot implement it, and memory_libmap maps it to 44
RAM256X1S (176 LUT sites) plus a fabric register. Vivado maps the same memory to one RAMB18.

Reproduced on an 11-line module (build/qor/synx/lutram/tm2.v, the tag_mem pattern with two constant data bits):
stock yosys gives 44 RAM256X1S; without the constant bits (tm.v) it gives 1 RAMB18E1.

## Change
- `SimpleContext` (opt_dff's mux-merging worker) collects the read-data bits of `$memrd`/`$memrd_v2` cells when
  the scratchpad option `opt_dff.keep_memrd_regs` is set.
- `try_merge_srst`: if a sync reset was found on a bit whose remaining D input is a `$memrd` data bit, and the
  reset would cover only part of the register, the FF is left unchanged (whole) and a log line says so. A reset that
  covers the whole register is still inferred (memory_dff takes it as a read-port reset).
- Help text of `opt_dff` documents the option.

## Evidence
- No-op: with the option off the netlist does not change. Same binary, option on vs off: byte-identical JSON on
  rv_soc, rv_mul, rv_big, bram and fir (build/qor/synx/noop.json, m_synxref vs m_keepmem); the rebuilt binary has
  the same cell counts as the oss-cad-suite yosys on all six designs (auto-generated names differ because the
  source path is part of NEW_ID).
- Effect: only arty_ddr3 changes, and only `tag_mem_dat0` is kept whole (one "Keeping" line per opt run).
  See docs/qor-vivado.md Finding 14 for cell counts, post-route LUT sites and Vivado's numbers.
- Function: flow/qor_memdff_sim.sh simulates the RTL, the stock netlist and the patched netlist of tm.v and tm2.v
  in lockstep for 200000 random cycles after filling the memory: 0 mismatches (build/qor/synx/lutram/sim/*.sim.log).
  Negative control: one LUT3 INIT of the patched tm2 netlist set to 0 gives 100422 mismatching cycles
  (build/qor/synx/lutram/sim/neg/tm2.sim.log).
- Not done: a gate-level simulation of the whole arty_ddr3 SoC (no gate-level testbench exists for it).

## Known limit
The block RAM is used in SDP x36 mode with READ_FIRST, and yosys emulates the write-first behaviour in fabric
(tm2: 21 FDRE + 22 LUT3 next to the RAMB18E1). Vivado uses the RAMB18's own WRITE_FIRST mode. Choosing TDP
WRITE_FIRST for a single-port write-first memory is a memory_libmap cost question, not addressed here.
