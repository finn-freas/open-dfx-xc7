# WIP: synthesis QoR (Finding 14) -- state 2026-11-06 ~21:00

## Done, verified
- LiteX LUTRAM gap root cause: arty_ddr3 `tag_mem` (512x22, write-first, 2 constant data bits). opt_dff turns the
  constant bits of the read register into $sdff, splitting it; memory_dff then finds no output FF, the read port stays
  asynchronous and maps to 44 RAM256X1S (176 LUTRAM sites). Draft fix docs/drafts/yosys-opt-dff-keep-memrd-regs.{patch,md}
  (opt-in scratchpad `opt_dff.keep_memrd_regs`), built at build/yosys-build/yosys-synx/yosys.
  - Option off: same binary gives byte-identical netlists on rv_soc/rv_mul/rv_big/bram/fir; only arty_ddr3 changes with it on.
  - arty_ddr3 nextpnr post-route (seed 1): LUTRAM 320 -> 144 (Vivado 142); LUT sites 5153 -> 5040 (area_ref),
    4850 -> 4682 (area_pnr; Vivado 4340). sys_clk nextpnr timer 110.89 -> 97.2 / 107.02 -> 102.33 (one seed):
    the BRAM clk->Q (2.45 ns) now starts the critical path.
  - flow/qor_memdff_sim.sh: RTL vs stock vs patched netlist, 200000 random cycles, 0 mismatches; negative control 100422.
  - arty_eth: no change (its LUTRAM is 147 RAM32M + 8 RAM64M from FIFOs; a different gap).
- Lockstep firmware sims PASS (157836 cycles, 0 mismatches): rv_soc t_dff, t_retime_full, t_cal, t_cal_dff, m_nosdff;
  rv_big t_dff, t_retime_full, d_dff, d_retime_full, m_nosdff.
- FSM: yosys extracts 0 FSMs on arty_ddr3 (15 state registers rejected only for their init value); Vivado extracts 4
  (3 'sequential', 1 one-hot). rv_soc: yosys recodes cpu_state/mem_wordsize (already one-hot in the RTL).
- abc9 ignores BRAM clock-to-out: rv_soc top module byte-identical with RAMB36E1 DO arrival 0 / 2454 / 5000 ps, also with
  an &if-only abc9 script and with `&DOx_REG` changed to `!DOx_REG` (build/qor/synx/arrival/). Vivado's critical paths
  BRAM -> reg_out: 3 LUTs on its own netlist, 6 on yosys's.

## Round 2 (coordinator leads, 2026-11-06 night) -- written up in Finding 14 "round 2"
1. abc9 BRAM clock-to-out: root cause = abc9's default writer write_xaiger2 emits no arrival times; `scratchpad -set
   abc9.xaiger 1` restores them (existing option). Vivado timer, Default, one run: rv_soc x1_cal 176.77 MHz (Vivado
   171.00, -retiming 179.50), rv_big dx1_cal 169.15 (Vivado 177.68). nextpnr 3 seeds: rv_soc x1_cal 147.11 (ys 143.82),
   rv_big dx1 148.24 (ys_dspq 133.09) but dx1_cal 131.68. LiteX (nextpnr, 1 seed): no gain shown. All lockstep PASS.
2. pw_dsp: `k_mul` prepare variant, no-op on 5 designs, pw_dsp32 LUT 2352 -> 1047, CARRY4 384 -> 0; lockstep PASS.
3. arty_eth LUTRAM: Vivado puts 3 sync FIFOs in BRAM; flow/synth_blockrule.py (opt-in) -> LUTRAM sites 636 -> 548
   (nextpnr), Vivado 512; unisim lockstep PASS; nextpnr sys_clk lower on one seed.

## Not run (Vivado never free before the 01:00 wrap; my waiters stopped, lock released 00:30)
- rv_soc_x1_cal_dirs / rv_big_dx1_cal_dirs (Explore + ExtraTimingOpt, noise check of x1_cal; sources ready in
  build/qor/synx/src/): under the lock, `vivado\run_qor.ps1 -Tag qor_synx -Script build_synx.tcl -SrcRel
  build\qor\synx\src -Names rv_soc_x1_cal_dirs,rv_big_dx1_cal_dirs -Run`.
- arty_eth_blockrule_free (Vivado P&R of the block-RAM-rule netlist; source ready in build/eth/xtime/src/):
  `vivado\run_ddr3.ps1 -Script build_xtime.tcl -SrcSub build\eth\xtime\src -Tag eth_xtime -Names
  arty_eth_blockrule_free -Run`; compare with arty_eth_gapfix_free.
- Nothing of mine is running.

## Next
- Decide a preset: abc9.xaiger=1 looks safe to propose as default (it only feeds ABC real arrival times); the calibrated
  LUT model is placer-dependent (helps rv_soc, hurts rv_big under nextpnr). Measure on flow/qor_suite.py when it lands.
- Upstream view: write_xaiger2 lacks the `i` (input arrival) extension; a yosys patch to emit it would make the default
  path timing-aware without falling back to write_xaiger.
- TDP WRITE_FIRST for single-port write-first memories; FSM extraction with init values.

