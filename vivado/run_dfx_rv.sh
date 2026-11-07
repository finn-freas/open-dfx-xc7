#!/usr/bin/env bash
set -u
NAME=$1
PERIOD=$2
RMS=${3:-xor,andn,add,rot}
PPX=${4:-}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
WIN=/mnt/c/Users/finnf/open-dfx-xc7-vivado
SRC=$WIN/designs/$NAME
OUT=$WIN/build/$NAME
LOCK=/mnt/c/Users/finnf/vivado.lock
mkdir -p "$SRC" "$WIN/vivado"
R=$ROOT/designs/rv_soc
cp "$R/rv_soc.v" "$R/uart.v" "$R/picorv32.v" "$R/pr/rm_stub.v" "$R/fw/main.hex" "$R/arty_a7_35t.xdc" "$SRC/"
for rm in ${RMS//,/ }; do cp "$R/pr/rm_core_$rm.v" "$SRC/"; done
cp "$ROOT/designs/dfx_rv/rm_slot_pp.v" "$ROOT/designs/dfx_rv/pblock.xdc" "$SRC/"
rm -f "$SRC/partpin.xdc"
[ -n "$PPX" ] && cp "$PPX" "$SRC/partpin.xdc"
cp "$ROOT/vivado/build_dfx_rv.tcl" "$WIN/vivado/"
w() { wslpath -w "$1" | tr '\\' '/'; }
for batch in $(seq 1 12); do
  until ! tasklist.exe 2>/dev/null | grep -qi '^vivado.exe' && mkdir "$LOCK" 2>/dev/null; do sleep 30; done
  trap 'rmdir "$LOCK" 2>/dev/null' EXIT
  mkdir -p "$OUT"
  cd "$OUT"
  cmd.exe /c "C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat" -mode batch -nojournal -log "$(w "$OUT")/vivado_$batch.log"     -source "$(w "$WIN/vivado/build_dfx_rv.tcl")" -tclargs "$NAME" rv_soc "$(w "$SRC")" "$(w "$SRC")/arty_a7_35t.xdc"     "$(w "$OUT")" "$PERIOD" "$RMS" > "$OUT/console_$batch.log" 2>&1
  echo "batch $batch: vivado exit $?"
  rmdir "$LOCK" 2>/dev/null; trap - EXIT
  grep -q DFX_RV_DONE "$OUT/console_$batch.log" && break
  sleep 90
done
