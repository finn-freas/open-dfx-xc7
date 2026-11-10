#!/usr/bin/env bash
set -uo pipefail

VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
WIN_WORK="/mnt/c/Users/finnf/open-dfx-xc7-vivado/dpl"
OUT="/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/${DPL_XTIME:-dpl_xtime2}"
DRY_RUN=1

if [ "${1:-}" = "--run" ]; then DRY_RUN=0; shift; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/build/qor/dpl/xsrc"
echo "[$([ $DRY_RUN = 1 ] && echo dry || echo run)] vivado dpl_dump.tcl on $# source(s): $*"
[ $DRY_RUN = 1 ] && exit 0
source "$ROOT/vivado/vivado_slot.sh"
trap 'exit 143' INT TERM
mkdir -p "$WIN_WORK/src" "$OUT"
cp "$ROOT/vivado/dpl_dump.tcl" "$WIN_WORK/run.tcl"
for n in "$@"; do
  [ -f "$OUT/$n/status.txt" ] && continue
  [ -d "$SRC/$n" ] || { echo "no source $n"; continue; }
  rm -rf "$WIN_WORK/src/$n"
  cp -r "$SRC/$n" "$WIN_WORK/src/$n"
  while true; do
    if _viv_mkdir vivado.lock; then VIV_HELD=vivado.lock; break; fi
    sleep 3
  done
  trap '_viv_rmdir "$VIV_HELD"' EXIT
  echo "$(date +%T) $n on $VIV_HELD"
  log="$OUT/vivado_${n}.log"
  (cd "$WIN_WORK" && cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log "$(wslpath -m "$log")" \
    -source "$(wslpath -m "$WIN_WORK/run.tcl")" -tclargs "$(wslpath -m "$WIN_WORK/src")" "$(wslpath -m "$OUT")" "$n" \
    > "$WIN_WORK/stdout_$n.txt" 2>&1)
  vivado_release
  echo "$(date +%T) $n $(head -1 "$OUT/$n/status.txt" 2>/dev/null)"
done
