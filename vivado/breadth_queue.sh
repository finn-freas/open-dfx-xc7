#!/usr/bin/env bash
cd "$(dirname "$0")/.."
source vivado/vivado_slot.sh
PROJ='\\wsl.localhost\Ubuntu\home\finnf\open-dfx-xc7'
VIV='C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat'
W=C:/Users/finnf/open-dfx-xc7-vivado
WM=/mnt/c/Users/finnf/open-dfx-xc7-vivado
trap 'exit 143' INT TERM
stage() { vivado_acquire; echo "stage $1 $(date +%T) on $VIV_HELD"; shift; (cd $WM && "$@" < /dev/null); echo "rc=$? $(date +%T)"; vivado_release; sleep 60; }
ps() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
for n in xadc_inv_dclk xadc_inv_cclk xadc_cclk_clk xadc_dclk0; do
  [ -f $WM/build/xadcinv/$n/status.txt ] || stage "xadc $n" ps "$PROJ\vivado\run_gap.ps1" -Names $n -Tag xadcinv -Run
done
bash vivado/slot_run.sh axi build_rtl.tcl build/axi_xbar/vsrc axi_xbar_10ns axi_xbar_5ns
for n in axi_xbar_10ns_placed axi_xbar_10ns_free; do
  [ -f $WM/build/axi_xtime/$n/status.txt ] || stage "$n" ps "$PROJ\vivado\run_ddr3.ps1" -Script build_xtime.tcl -SrcSub 'build\axi_xbar\xtime\src' -Tag axi_xtime -Names $n -Run -Slotted
done
stage cores cmd.exe /c "$VIV" -mode batch -nojournal -log $W/svcores/vivado.log -source $W/svcores/sv_core_synth.tcl -tclargs $W/svcores/manifest.tsv $W/svcores/out
stage phy_pll ps "$PROJ\vivado\run_ddr3_phy_sim.ps1" -Extras 0,2500,5000,6250 -Defines PLL_CLOCKS -Tag _pll -Run -Slotted
for first in $(seq 0 60 600); do
  [ -f $WM/svtests/vivado_$first.log ] && grep -q "Exiting Vivado" $WM/svtests/vivado_$first.log && continue
  stage "svtests_$first" cmd.exe /c "$VIV" -mode batch -nojournal -log $W/svtests/vivado_$first.log -source $W/svtests/svtests_elab.tcl -tclargs $W/svtests/manifest.tsv xc7a35tcsg324-1 $first 60
done
[ -f build/eth_rgmii/vsrc/nv_rgmii/constraints.xdc ] && bash vivado/slot_run.sh rgmii build_rtl.tcl build/eth_rgmii/vsrc nv_rgmii
for n in ddr3_static_s3_placed ddr3_static_s1_placed ddr3_static_s2_placed ddr3_heap_s2_placed ddr3_heap_s3_placed; do
  [ -f $WM/build/ddr3_sweep/$n/status.txt ] || stage "$n" ps "$PROJ\vivado\run_ddr3.ps1" -Script build_xtime.tcl -SrcSub 'build\ddr3\sweep\xtime' -Tag ddr3_sweep -Names $n -Run -Slotted
done
for n in nv_rgmii_placed nv_rgmii_free; do
  [ -f $WM/build/rgmii_xtime/$n/status.txt ] || stage "$n" ps "$PROJ\vivado\run_ddr3.ps1" -Script build_xtime.tcl -SrcSub 'build\eth_rgmii\xtime\src' -Tag rgmii_xtime -Names $n -Run -Slotted
done
echo "done $(date +%T)"
