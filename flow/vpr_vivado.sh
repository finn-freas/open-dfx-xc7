#!/usr/bin/env bash
set -uo pipefail
VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
WIN_WORK="/mnt/c/Users/finnf/open-dfx-xc7-vivado/vpr"
OUT="/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/vpr_xtime"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/build/qor/place/xsrc"
source "$ROOT/vivado/vivado_slot.sh"
export VIV_SLOT1_ONLY=1
mkdir -p "$WIN_WORK/src" "$OUT"
cp "$ROOT/vivado/build_xtime.tcl" "$WIN_WORK/run.tcl"
for n in "$@"; do
  [ -f "$OUT/$n/status.txt" ] && continue
  [ -d "$SRC/$n" ] || { echo "no source $n"; continue; }
  rm -rf "$WIN_WORK/src/$n"
  cp -r "$SRC/$n" "$WIN_WORK/src/$n"
  vivado_acquire
  echo "$(date +%T) $n on $VIV_HELD"
  log="$OUT/vivado_${n}.log"
  (cd "$WIN_WORK" && cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log "$(wslpath -m "$log")" \
    -source "$(wslpath -m "$WIN_WORK/run.tcl")" -tclargs "$(wslpath -m "$WIN_WORK/src")" "$(wslpath -m "$OUT")" "$n" \
    > "$WIN_WORK/stdout_$n.txt" 2>&1)
  vivado_release
  echo "$(date +%T) $n $(head -1 "$OUT/$n/status.txt" 2>/dev/null)"
done
