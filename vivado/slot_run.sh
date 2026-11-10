#!/usr/bin/env bash
set -uo pipefail
TAG=$1; SCRIPT=$2; SRCREL=$3; shift 3
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado
SRC_ROOT=$W/designs/$TAG; OUT_ROOT=$W/build/$TAG
source "$ROOT/vivado/vivado_slot.sh"
trap 'exit 143' INT TERM
mkdir -p "$SRC_ROOT" "$OUT_ROOT" "$W/vivado"
cp "$ROOT/vivado/$SCRIPT" "$W/vivado/$SCRIPT"
for n in "$@"; do
  [ -f "$OUT_ROOT/$n/status.txt" ] && { echo "$(date +%T) $n skip (status.txt)"; continue; }
  [ -d "$ROOT/$SRCREL/$n" ] || { echo "$(date +%T) $n no source"; continue; }
  rm -rf "$SRC_ROOT/$n"; mkdir -p "$SRC_ROOT/$n"; cp -r "$ROOT/$SRCREL/$n/." "$SRC_ROOT/$n/"
  vivado_acquire
  echo "$(date +%T) $n start on $VIV_HELD"
  t0=$(date +%s)
  (cd "$W" && cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log "$(wslpath -m "$OUT_ROOT/vivado_$n.log")" \
    -source "$(wslpath -m "$W/vivado/$SCRIPT")" -tclargs "$(wslpath -m "$SRC_ROOT")" "$(wslpath -m "$OUT_ROOT")" "$n" \
    > "$OUT_ROOT/stdout_$n.txt" 2>&1)
  rc=$?
  vivado_release
  echo "$(date +%T) $n rc=$rc wall $(( $(date +%s)-t0 ))s $(head -1 "$OUT_ROOT/$n/status.txt" 2>/dev/null)"
  sleep "${SLOT_GAP_S:-60}"
done
