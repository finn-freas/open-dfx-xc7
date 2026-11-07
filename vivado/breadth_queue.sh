#!/usr/bin/env bash
LOCK=C:/Users/finnf/vivado.lock
PROJ='\wsl.localhost\Ubuntu\home\finnf\open-dfx-xc7'
VIV="C:/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
W=C:/Users/finnf/open-dfx-xc7-vivado
WSL=//wsl.localhost/Ubuntu/home/finnf/open-dfx-xc7
held=0
release() { if [ $held = 1 ]; then rmdir "$LOCK" 2>/dev/null; held=0; echo "lock released $(date +%T)"; fi; }
trap 'release' EXIT
trap 'release; exit 1' INT TERM
acquire() {
  while true; do
    while [ -d "$LOCK" ] || tasklist | grep -qi vivado.exe; do sleep 30; done
    sleep 300
    if [ ! -d "$LOCK" ] && ! tasklist | grep -qi vivado.exe && mkdir "$LOCK" 2>/dev/null; then held=1; echo "lock acquired $(date +%T)"; return; fi
  done
}
stage() { acquire; echo "stage $1 $(date +%T)"; shift; "$@"; echo "rc=$? $(date +%T)"; release; }
stage xadc powershell -NoProfile -ExecutionPolicy Bypass -File "$PROJ\vivado\run_gap.ps1" -Names xadc_inv_dclk,xadc_inv_cclk,xadc_cclk_clk,xadc_dclk0 -Tag xadcinv -Run
stage axi powershell -NoProfile -ExecutionPolicy Bypass -File "$PROJ\vivado\run_qor.ps1" -Names axi_xbar_10ns,axi_xbar_5ns -Tag axi -Script build_rtl.tcl -SrcRel 'build\axi_xbar\vsrc' -Run
stage axi_xtime powershell -NoProfile -ExecutionPolicy Bypass -File "$PROJ\vivado\run_ddr3.ps1" -Script build_xtime.tcl -SrcSub 'build\axi_xbar\xtime\src' -Tag axi_xtime -Names axi_xbar_10ns_placed,axi_xbar_10ns_free -Run
stage cores cmd //c "$VIV" -mode batch -nojournal -log $W/svcores/vivado.log -source $W/svcores/sv_core_synth.tcl -tclargs $W/svcores/manifest.tsv $W/svcores/out
stage phy_pll powershell -NoProfile -ExecutionPolicy Bypass -File "$PROJ\vivado\run_ddr3_phy_sim.ps1" -Extras 0,2500,5000,6250 -Defines PLL_CLOCKS -Tag _pll -Run
for first in $(seq 0 60 600); do
  stage "svtests_$first" cmd //c "$VIV" -mode batch -nojournal -log $W/svtests/vivado_$first.log -source $W/svtests/svtests_elab.tcl -tclargs $W/svtests/manifest.tsv xc7a35tcsg324-1 $first 60
done
if [ -f $WSL/build/eth_rgmii/vsrc/nv_rgmii/constraints.xdc ]; then
  stage rgmii powershell -NoProfile -ExecutionPolicy Bypass -File "$PROJ\vivado\run_qor.ps1" -Names nv_rgmii -Tag rgmii -Script build_rtl.tcl -SrcRel 'build\eth_rgmii\vsrc' -Run
fi
for n in ddr3_static_s3_placed ddr3_static_s1_placed ddr3_static_s2_placed ddr3_heap_s2_placed ddr3_heap_s3_placed; do
  stage "$n" powershell -NoProfile -ExecutionPolicy Bypass -File "$PROJ\vivado\run_ddr3.ps1" -Script build_xtime.tcl -SrcSub 'build\ddr3\sweep\xtime' -Tag ddr3_sweep -Names $n -Run
done
for n in nv_rgmii_placed nv_rgmii_free; do
  stage "$n" powershell -NoProfile -ExecutionPolicy Bypass -File "$PROJ\vivado\run_ddr3.ps1" -Script build_xtime.tcl -SrcSub 'build\eth_rgmii\xtime\src' -Tag rgmii_xtime -Names $n -Run
done
echo "done $(date +%T)"
