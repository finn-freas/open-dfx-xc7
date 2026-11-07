#!/bin/bash
ROOT=$HOME/open-dfx-xc7
LX=$ROOT/toolchain/litex
DRY_RUN=${DRY_RUN:-1}
OUT=${OUT:-$ROOT/build/ddr3/sim/litex_sim}
TIMEOUT_S=${TIMEOUT_S:-1800}
SIM_ARGS=${SIM_ARGS:-"--cpu-type vexriscv --with-sdram --sdram-module MT41K128M16 --sdram-data-width 16 --sdram-verbosity 0 --non-interactive"}
SYSROOT=$LX/sysroot/usr
ZROOT=$ROOT/toolchain/buildenv/env
MAX_NEXTPNR=2

export PATH=$LX/venv/bin:$LX/riscv/usr/bin:$ROOT/toolchain/oss-cad-suite/bin:$PATH
export CFLAGS="-I$SYSROOT/include -I$ZROOT/include"
export LDFLAGS="-L$SYSROOT/lib/x86_64-linux-gnu -Wl,-rpath,$SYSROOT/lib/x86_64-linux-gnu -L$ZROOT/lib -Wl,-rpath,$ZROOT/lib"
export LD_LIBRARY_PATH=$SYSROOT/lib/x86_64-linux-gnu

CMD="litex_sim $SIM_ARGS --output-dir $OUT"
if [ "$DRY_RUN" = 1 ]; then
  echo "[dry] $CMD  (timeout ${TIMEOUT_S}s, log $OUT.log); DRY_RUN=0 to run"
  exit 0
fi
while [ "$(pgrep -c nextpnr)" -ge $MAX_NEXTPNR ] || pgrep -x make >/dev/null || pgrep -x ninja >/dev/null; do sleep 30; done
mkdir -p "$(dirname $OUT)"
cd "$(dirname $OUT)"
echo "start $(date -Is) $CMD" > $OUT.log
/usr/bin/time -f '%e s %M KB' timeout --foreground $TIMEOUT_S $CMD < /dev/null >> $OUT.log 2>&1
echo "exit $? $(date -Is)" >> $OUT.log
grep -a -E 'Memtest|memtest|Initializing SDRAM|bandwidth|KO|OK|errors|Booting|litex>' $OUT.log | head -40
