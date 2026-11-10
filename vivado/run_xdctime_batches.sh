#!/usr/bin/env bash
cd "$(dirname "$0")/.."
OUT=/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/xdc_xtime
NAMES="x_iodly_xdc3 x_iodly_minmax_xdc3 x_iodly_fall_xdc3 x_mcp_from_xdc3 x_mcp_thru_xdc3 x_maxdly_cells_xdc3 x_maxdly_dp_xdc3 rv_soc_xdc3"
for n in $NAMES; do
  [ -f $OUT/$n/in_setup_slow.rpt ] && [ -f $OUT/$n/reg_setup_slow.rpt ] || rm -f $OUT/$n/status.txt
done
export VIV_SLOT=3
bash vivado/slot_run.sh xdc_xtime build_xdctime.tcl build/xdc_xtime/src $NAMES
echo all-batches-done
