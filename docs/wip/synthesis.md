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

## Round 3 (2026-11-08): path depth on rv_soc (coordinator: 8.1 cells/path vs Vivado's 6.3)
- flow/path_cells.py: cells per path and their kinds on a Vivado run's 100 worst non-ICAP paths (paths_noicap.txt +
  the run's EDIF). Results (build/qor/synx/path_cells_tu.json):
  - tu baseline (pl15_tuonly_stub, exact import, exact_sa s1-3): 8.20 / 8.13 / 8.19 cells/path; per path LUT2-6
    5.58 / 5.39 / 5.85 (LUT2 alone ~2.8), nextpnr-made LUTs (xr_*) 0.21 / 0.27 / 0.07, CARRY4 0.36 / 0.42 / 0.22.
  - the same yosys netlist placed by Vivado itself (vref_exact): 8.02, with 1.0 CARRY4 + 0.88 LUT1 inverters per path.
  - Vivado's own netlist after opt_design (qor_synx rv_soc_viv opt_paths): 6.27 cells/path (4.19 LUTs, 0.08 CARRY4).
  - yosys netlist after opt_design in Vivado: `ys` 7.16, `t_cal_dff` 6.53, `x1_cal` 6.63, `x1` 7.84 cells/path.
  => the extra depth is synthesis (abc LUT chains, mostly LUT2), about 0.9 cells/path; nextpnr's own LUTs add only
     ~0.2. abc9 with arrival times + the flat calibrated model (`x1_cal`) removes ~0.5 of it.
- flow/depth_bench.py: tu placer (v15, pl15_tuonly_stub args) on `x1`, `x1_cal`, `x1_cal` + `-o carry-di-bypass`
  (nextpnr made LUT1s 497 -> 285); rv_soc s1-3 done (nextpnr timer is ICAP-bound, 134-138 MHz). The x1_cal netlist
  is byte-identical (src aside) to the lockstep-simulated synth_timing x1_cal netlist.
- x1_cal_syn2 (ABC `&syn2; &dc2; &dch` before `&if`, with arrival times + calibrated model): graph depth max 6 -> 5 LUT
  levels, 1130 -> 1087 LUT cells; lockstep sim PASS; dp_tu_x1calsyn2 s1-3 placed and exported.
- Result (exact import, Vivado timer, rv_soc, seeds 1-3): tu 105.03 / 96.07 / 99.50 (mean 100.20), cells/path 8.17;
  tu + x1_cal 111.48 / 100.23 / 101.45 (mean 104.39, +4.2 %), cells/path 7.24 (LUTs 5.66 -> 4.45 per path).
  tu + x1_cal_syn2 122.80 / 114.08 / 115.81 (mean 117.56, +17.3 % over tu), cells/path 7.05.
  Vivado's own netlist after opt_design: 6.27. Pending: x1_cal + carry-di-bypass, x1.
- Runs: flow/depth_vivado_slot3.sh (slot 3; slot 1 too from 21:00), summary flow/depth_summary.py.
- Superseded: exact-import Vivado runs (slot 1, from 21:00, 60 s gap): rv_soc_p5_dp_tu_{x1cal,x1cal_cdb,x1}_s{1,2,3}_exact
  via flow/rte_dump_vivado.sh (RTE_OUT=build/exact, RTE_ROUTE_DUMP=0); log build/qor/synx/logs/depth_vivado.log.
  Then: `python3 flow/path_cells.py <W>/build/exact/rv_soc_p5_dp_tu_*_exact` and Fmax from slack.txt / sa_summary.
- Verification of x1_cal_syn2 (the netlists handed to the global placer, byte-identical to the checked ones):
  rv_soc / rv_big (x1_cal_syn2) / rv_mul (dx1_cal_syn2, DSP draft): firmware lockstep 157836 cycles, 0 mismatches.
  bram: sequential equivalence PROVEN (miter of default vs x1_cal_syn2, ABC dprove "Networks are equivalent";
  build/qor/synx/equiv/bram/x1_cal_syn2_*/seq.log). flow/synth_timing_equiv.py now maps SRL16E/SRLC32E/IBUF/OBUF to
  their cells_sim models (expose -evert did not cut them from a JSON netlist) and runs setundef -zero before aigmap.
  Negative controls (flow/equiv_negctl.py, one LUT INIT bit flipped): 7 of 8 flips found NOT EQUIVALENT; the
  remaining flip (k=0) proved equivalent, i.e. that bit is not observable. The structural check alone leaves 37 of 1103
  cells unproven (lfsr[59], y[35:0]); the random-input simulation (flow/netlist_randsim.py) is not sensitive on bram
  (broken netlists also pass) and is not used as evidence.
- QoR suite quick set, open flow with the preset (`qor_suite.py open --quick --variant x1calsyn2 --synth <script>`,
  script in build/qor/synx/x1calsyn2_suite_synth.txt), seed 1, nextpnr timer vs the base label (base run dirs as found):
  rv_big 149.16 -> 133.24, serv 137.32 -> 121.65, aes 90.27 -> 91.84, sha256 75.05 -> 79.92, bram 231.64 -> 210.57,
  axi_xbar 124.29 -> 144.18 MHz. yosys time 29.5 -> 25.2, 24.4 -> 22.7, 34.4 -> 30.1, 18.8 -> 15.8, 7.9 -> 7.1,
  19.5 -> 15.5 s (shared machine). LUT cells: aes 3951 -> 5079 (+29 %); the others -1 to -3 %.
  Vivado-timer exact import (placedx) for base and x1calsyn2 queued after 21:15 (log build/qor/synx/logs/suite_vivado.log).
  Suite designs have no testbenches: their netlists are not verified (the preset is verified on rv_soc/rv_big/rv_mul/bram).

## State at wind-down (2026-11-08 22:05): nothing of mine running, no lock held
x1_cal_syn2 under the exact import (tu placer, Vivado timer, flow/depth_summary.py --design D):
| design | tu baseline (s1/s2/s3, mean) | + x1_cal_syn2 (s1/s2/s3, mean) | cells/path |
|---|---|---|---|
| rv_soc | 105.03 / 96.07 / 99.50 = 100.20 | 122.80 / 114.08 / 115.81 = 117.56 (+17.3 %) | 8.17 -> 7.05 |
| rv_mul (DSP draft) | 99.97 / 95.10 / 102.05 = 99.04 | 118.33 / 109.13 / 106.54 = 111.33 (+12.4 %) | 8.24 -> 7.30 |
| rv_big (no DSP draft) | 89.01 / 82.45 / 84.84 = 85.43 | 83.04 / 84.38 / 87.88 = 85.10 (-0.4 %) | 8.76 -> 8.64 |
| bram | 144.47 / 144.74 / 141.82 = 143.68 | 132.47 / 144.84 / - (s3 not run) | 10.46 -> 10.08 |
- Helps LUT-depth-bound CPU paths (rv_soc, rv_mul); neutral where carry/DSP chains dominate (rv_big: 1.8 CARRY4 per
  path; bram: 6.5). Not a default yet: bram s3 and the QoR-suite Vivado check are missing; suite nextpnr-timer results
  were mixed and aes grew 29 % in LUTs (see above).
- Verification: rv_soc/rv_big/rv_mul lockstep PASS; bram sequential equivalence proven. Suite designs unverified.

Resume (all under the Vivado slot rules; scripts skip names whose status.txt exists):
1. bram s3:  `bash flow/depth_vivado_slot3.sh --run bram_p5_dp_tu_x1calsyn2_s3_exact`
2. rv_soc x1_cal + carry-di-bypass and x1-only (exported, not run):
   `bash flow/depth_vivado_slot3.sh --run rv_soc_p5_dp_tu_x1cal_cdb_s{1,2,3}_exact rv_soc_p5_dp_tu_x1_s{1,2,3}_exact`
   (log >> build/qor/synx/logs/depth_vivado.log)
3. QoR-suite Vivado exact check (open runs done for x1calsyn2):
   `python3 flow/qor_suite.py vivado --quick --variant x1calsyn2 --modes placedx --run` and the same with `--variant base`.
4. Summaries: `python3 flow/depth_summary.py --design rv_soc|rv_mul|rv_big|bram`.

