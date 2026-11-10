#!/usr/bin/env bash
set -uo pipefail
VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
SRC="${SRC:-/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/rte}"
OUT="${RTE_OUT:-/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/rte_arcs}"
DRY=1
if [ "${1:-}" = "--run" ]; then DRY=0; shift; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "[$([ $DRY = 1 ] && echo dry || echo run)] build_rte.tcl + route dump on: $*"
[ $DRY = 1 ] && exit 0
source "$ROOT/vivado/vivado_slot.sh"
export VIV_SLOT1_ONLY=1
mkdir -p "$OUT"
cp "$ROOT/vivado/build_rte.tcl" "$OUT/build_rte.tcl"
export RTE_ROUTE_DUMP="${RTE_ROUTE_DUMP:-1}"
export RTE_LUT_ARCS="${RTE_LUT_ARCS:-0}"
export WSLENV="${WSLENV:+$WSLENV:}RTE_ROUTE_DUMP:RTE_LUT_ARCS"
for n in "$@"; do
  [ -f "$OUT/$n/status.txt" ] && continue
  [ -d "$SRC/$n" ] || { echo "no source $n"; continue; }
  if [ "${RTE_ANY_SLOT:-0}" = 1 ]; then
    mkdir -p "$ROOT/build/exact/claims"
    mkdir "$ROOT/build/exact/claims/$n" 2>/dev/null || continue
    vivado_acquire
  else
    until _viv_mkdir vivado.lock; do sleep 3; done; VIV_HELD=vivado.lock; trap '_viv_rmdir "$VIV_HELD"' EXIT
  fi
  echo "$(date +%T) $n on $VIV_HELD"
  (cd /mnt/c/Users/finnf && cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal \
    -log "$(wslpath -m "$OUT/vivado_$n.log")" -source "$(wslpath -m "$OUT/build_rte.tcl")" \
    -tclargs "$(wslpath -m "$SRC")" "$(wslpath -m "$OUT")" "$n" > "$OUT/stdout_$n.txt" 2>&1 < /dev/null)
  vivado_release
  echo "$(date +%T) $n $(head -1 "$OUT/$n/status.txt" 2>/dev/null) dump=$(tail -1 "$OUT/$n/routes_dump.txt" 2>/dev/null)"
done
