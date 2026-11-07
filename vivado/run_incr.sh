#!/usr/bin/env bash
set -e
R=$(cd "$(dirname "$0")/.." && pwd)
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado
rm -rf $W/designs/incr && mkdir -p $W/designs/incr $W/build/incr $W/vivado
cp -r $R/build/runtime/vsrc/rv_soc $W/designs/incr/ref
cp -r $R/build/runtime/vsrc/rv_soc $W/designs/incr/edit
cp $R/designs/incr/rv_soc_edit/rv_soc.v $W/designs/incr/edit/rv_soc.v
cp $R/vivado/build_incr.tcl $W/vivado/
echo "start $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg) nextpnr $(pgrep -c nextpnr)"
cd $W
cmd.exe /c 'C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat -mode batch -nojournal -log build/incr/vivado.log -source vivado/build_incr.tcl -tclargs C:/Users/finnf/open-dfx-xc7-vivado/designs/incr/ref C:/Users/finnf/open-dfx-xc7-vivado/designs/incr/edit C:/Users/finnf/open-dfx-xc7-vivado/build/incr' > /dev/null 2>&1 || true
echo "end $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg) nextpnr $(pgrep -c nextpnr)"
