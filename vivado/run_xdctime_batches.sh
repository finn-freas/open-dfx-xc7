#!/usr/bin/env bash
OUT=/c/Users/finnf/open-dfx-xc7-vivado/build/xdc_xtime
LOCK=C:/Users/finnf/vivado.lock
batches=("x_iodly_xdc3,x_iodly_minmax_xdc3,x_iodly_fall_xdc3" "x_mcp_from_xdc3,x_mcp_thru_xdc3" "x_maxdly_cells_xdc3,x_maxdly_dp_xdc3" "rv_soc_xdc3")
first=1
for names in "${batches[@]}"; do
  todo=""
  for n in ${names//,/ }; do [ -f $OUT/$n/in_setup_slow.rpt ] && [ -f $OUT/$n/reg_setup_slow.rpt ] && [ -f $OUT/$n/status.txt ] || { rm -f $OUT/$n/status.txt; todo="$todo,$n"; }; done
  todo=${todo#,}
  [ -z "$todo" ] && continue
  [ $first = 0 ] && sleep 300
  first=0
  until mkdir $LOCK 2>/dev/null; do sleep 30; done
  trap 'rmdir C:/Users/finnf/vivado.lock 2>/dev/null' EXIT
  echo "lock taken $(date +%H:%M) for $todo"
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File '\\wsl.localhost\Ubuntu\home\finnf\open-dfx-xc7\vivado\run_qor.ps1' -Names "$todo" -Tag xdc_xtime -Script build_xdctime.tcl -SrcRel 'build\xdc_xtime\src' -Run >> /c/Users/finnf/open-dfx-xc7-vivado/xdc_xtime_run5.log 2>&1
  echo "batch rc=$? $(date +%H:%M)"
  rmdir $LOCK; trap - EXIT
done
echo all-batches-done
