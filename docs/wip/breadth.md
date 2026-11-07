# WIP: breadth workstream (SV front end, XADC bits, AXI interconnect, deferrals, DDR3 PHY/timing, RGMII)

Updated 2026-11-06 23:15. Paused waiting for Vivado: since 20:18 the lock was never free for 5 minutes (priority
placer/router/benchmark jobs), so none of the Vivado stages below has run. Nothing of mine is running now.

## Done (committed)
- f630714 roadmap deferral reasons (phys_opt, encryption/eFuse, GUI).
- ef0d7e3 sv-tests yosys 292/622 vs yosys-slang 590/622 (docs/sv-frontend.md), ibex via slang, xilinx_dsp assert
  re-check; examples/axi_xbar (RTL + gate-level sim PASS, open flow 152.63 MHz nextpnr timer).
- 77acc1a build_openxc7.py --frontend slang (+ --slang-arg); axi_xbar via slang 152.42 MHz, gate-level sim PASS;
  docs/axi-interconnect.md (open side).
- ce8ce62 RGMII Nexys Video SoC builds to a bitstream (flow/eth_rgmii_build.py); DDR3 placer sweep builds
  (flow/ddr_place_sweep.py, nextpnr timer: static 108.5-115.1 MHz, heap s2 103.6, s3 98.2, sa fails to route);
  XADC variant designs; flow/xadc_bits_probe.py.

## Vivado stages to run (each one invocation, release the lock between them; take the lock only when free 5 min)
Work dir C:/Users/finnf/open-dfx-xc7-vivado (sources already staged there or copied by the ps1 scripts):
1. XADC: `vivado\run_gap.ps1 -Names xadc_inv_dclk,xadc_inv_cclk,xadc_cclk_clk,xadc_dclk0 -Tag xadcinv -Run`,
   then `python3 flow/xadc_bits_probe.py`. Hypothesis to test: the 3 bits are MONITOR_BOT bits (the tile spans frames
   0-29, words 0-100 of column 0x900, overlapping INT_L_X18Y79 and HCLK_L_X49Y78): 26_1888 / 27_1928 (ZINV_DCLK /
   ZINV_CONVSTCLK?) and 25_1613.
2. AXI: `vivado\run_qor.ps1 -Names axi_xbar_10ns,axi_xbar_5ns -Tag axi -Script build_rtl.tcl -SrcRel build\axi_xbar\vsrc -Run`;
   `vivado\run_ddr3.ps1 -Script build_xtime.tcl -SrcSub build\axi_xbar\xtime\src -Tag axi_xtime -Names axi_xbar_10ns_placed -Run` (and _free).
3. ibex OOC: `vivado -mode batch -source C:/Users/finnf/open-dfx-xc7-vivado/svcores/sv_core_synth.tcl -tclargs
   .../svcores/manifest.tsv .../svcores/out` (2 designs: original and one-declaration-patched file list).
4. DDR3 PHY xsim with PLL clocks: `vivado\run_ddr3_phy_sim.ps1 -Extras 0,2500,5000,6250 -Defines PLL_CLOCKS -Tag _pll -Run`
   (uncommitted: designs/ddr3/phy_sim/tb_phy.v `ifdef PLL_CLOCKS`, run_ddr3_phy_sim.ps1 -Defines/-Tag). Compare
   rddata vs rddata_valid timing with build/ddr3/sim/phy/xsim_extra*.out (ideal tb clocks).
5. sv-tests Vivado: `vivado -mode batch -source .../svtests/svtests_elab.tcl -tclargs .../svtests/manifest.tsv
   xc7a35tcsg324-1 <first> 60` for first = 0, 60, ..., 600 (log vivado_<first>.log), then
   `python3 flow/svtests_run.py vivado-ingest <log>` per log and `report`.
6. DDR3 sweep, Vivado timer on each placement: `vivado\run_ddr3.ps1 -Script build_xtime.tcl -SrcSub build\ddr3\sweep\xtime
   -Tag ddr3_sweep -Names ddr3_static_s3_placed -Run` (also static_s1, static_s2, heap_s2, heap_s3).
7. RGMII: `vivado\run_qor.ps1 -Names nv_rgmii -Tag rgmii -Script build_rtl.tcl -SrcRel build\eth_rgmii\vsrc -Run`
   (200T, writes io_in.rpt/io_out.rpt and a .bit for an IOI FASM comparison); then xtime
   `-SrcSub build\eth_rgmii\xtime\src -Tag rgmii_xtime -Names nv_rgmii_placed` (and nv_rgmii_free).
All of it, with the polite lock, in order: run `bash vivado/breadth_queue.sh` from Git Bash on Windows (not in WSL). Check the
current Vivado slot rules first (another agent added vivado_slot.sh at 2850232).

## Rules in force
nextpnr with OFX_MAX_NEXTPNR=1 (placer agents first); Vivado: yield to placer/router/benchmark jobs.
