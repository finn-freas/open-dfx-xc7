#!/bin/bash
ROOT=$HOME/open-dfx-xc7
LX=$ROOT/toolchain/litex
DRY_RUN=${DRY_RUN:-1}
OUT=${OUT:-$ROOT/build/eth/sim}
SUITES=${SUITES:-"liteeth litescope"}
TIMEOUT_S=${TIMEOUT_S:-5400}
SYSROOT=$LX/sysroot/usr
ZROOT=$ROOT/toolchain/buildenv/env

export PATH=$LX/venv/bin:$LX/riscv/usr/bin:$ROOT/toolchain/oss-cad-suite/bin:$PATH
export CFLAGS="-I$SYSROOT/include -I$ZROOT/include"
export LDFLAGS="-L$SYSROOT/lib/x86_64-linux-gnu -Wl,-rpath,$SYSROOT/lib/x86_64-linux-gnu -L$ZROOT/lib -Wl,-rpath,$ZROOT/lib"
export LD_LIBRARY_PATH=$SYSROOT/lib/x86_64-linux-gnu

for s in $SUITES; do
  CMD="python -m pytest -v -p no:cacheprovider test"
  if [ "$DRY_RUN" = 1 ]; then
    echo "[dry] (cd $LX/src/$s && $CMD) > $OUT/${s}_pytest.log; DRY_RUN=0 to run"
    continue
  fi
  mkdir -p $OUT
  (cd $LX/src/$s && echo "commit $(git rev-parse HEAD) start $(date -Is)" && timeout $TIMEOUT_S $CMD; echo "exit $? $(date -Is)") \
    > $OUT/${s}_pytest.log 2>&1
  tail -n 4 $OUT/${s}_pytest.log
done
