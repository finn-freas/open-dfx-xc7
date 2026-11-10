#!/usr/bin/env bash
set -uo pipefail
VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
SRC=/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact
OUT=/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact
DRY=1
if [ "${1:-}" = "--run" ]; then DRY=0; shift; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "[$([ $DRY = 1 ] && echo dry || echo run)] build_rte.tcl (exact import, no route dump) on slot 3: $*"
[ $DRY = 1 ] && exit 0
source "$ROOT/vivado/vivado_slot.sh"
mkdir -p "$OUT"
cp "$ROOT/vivado/build_rte.tcl" "$OUT/build_rte.tcl"
export RTE_ROUTE_DUMP=0 RTE_LUT_ARCS=0
export WSLENV="${WSLENV:+$WSLENV:}RTE_ROUTE_DUMP:RTE_LUT_ARCS"
for n in "$@"; do
  [ -f "$OUT/$n/status.txt" ] && { echo "$(date +%T) $n skip"; continue; }
  [ -d "$SRC/$n" ] || { echo "no source $n"; continue; }
  while true; do
    a=$(win_avail_mb)
    if [ -n "$a" ] && [ "$a" -ge 5000 ] && _viv_mkdir vivado.lock3; then VIV_HELD=vivado.lock3; break; fi
    if [ "$(date +%H%M)" -ge 2115 ] && _viv_mkdir vivado.lock; then VIV_HELD=vivado.lock; break; fi
    sleep 5
  done
  trap '_viv_rmdir "$VIV_HELD"' EXIT
  echo "$(date +%T) $n on $VIV_HELD"
  (cd /mnt/c/Users/finnf && cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal \
    -log "$(wslpath -m "$OUT/vivado_$n.log")" -source "$(wslpath -m "$OUT/build_rte.tcl")" \
    -tclargs "$(wslpath -m "$SRC")" "$(wslpath -m "$OUT")" "$n" > "$OUT/stdout_$n.txt" 2>&1 < /dev/null)
  vivado_release
  echo "$(date +%T) $n $(head -1 "$OUT/$n/status.txt" 2>/dev/null)"
  sleep 30
done
echo "end $(date +%T)"
