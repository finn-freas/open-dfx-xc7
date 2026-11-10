#!/bin/bash
R=~/open-dfx-xc7
source $R/toolchain/buildenv/env.sh 2>/dev/null
NAME=${1:-rte}
until [ $(free -m | awk '/Mem:/{print $7}') -ge 4000 ]; do sleep 30; done
B=$R/build/nextpnr-build/$NAME
if [ ! -f $B/build.ninja ]; then
cmake -S $R/build/src/nextpnr-dpf -B $B -G Ninja -DCMAKE_BUILD_TYPE=Release -DCURRENT_GIT_VERSION=ce3f7c18-dpf -DARCH=himbaechel -DHIMBAECHEL_UARCH=xilinx -DHIMBAECHEL_XILINX_DEVICES= -DHIMBAECHEL_PRJXRAY_DB=$R/toolchain/openxc7/share/nextpnr/external/prjxray-db -DBUILD_GUI=OFF -DBUILD_TESTS=OFF -DBUILD_PYTHON=OFF -DPython3_EXECUTABLE=$R/toolchain/buildenv/env/bin/python3.12 -Wno-deprecated > $R/build/nextpnr-build/$NAME.cmake.log 2>&1 || { echo cmake failed; tail -20 $R/build/nextpnr-build/$NAME.cmake.log; exit 1; }
fi
ninja -C $B -j2 nextpnr-himbaechel > $R/build/nextpnr-build/$NAME.build.log 2>&1; rc=$?
echo "ninja rc=$rc"; grep -E "error" $R/build/nextpnr-build/$NAME.build.log | head -30; tail -3 $R/build/nextpnr-build/$NAME.build.log
