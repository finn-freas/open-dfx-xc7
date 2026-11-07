#!/usr/bin/env bash
set -euo pipefail

VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
LOCK="/mnt/c/Users/finnf/vivado.lock"
WIN_WORK="/mnt/c/Users/finnf/open-dfx-xc7-vivado/ip"
WAITERS='vivado[.]lock|ip_vivado[.]sh --run|run_runtime[.]sh|dpl_bench.*--vivado|vivado/run_[a-z0-9_]*[.](ps1|sh)'
YIELD_S=300
POLL_S=30

TCL="$1"; SUB="$2"; shift 2
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$WIN_WORK/$SUB"
args=()
for x in "$@"; do
  if [ "${x:0:1}" = "@" ]; then args+=("$(wslpath -m "$WORK/${x:1}")"); else args+=("$x"); fi
done
mkdir -p "$WORK"
cp "$ROOT/$TCL" "$WORK/run.tcl"

others() { pgrep -f "$WAITERS" | grep -v -x -e "$$" -e "$PPID" | while read -r p; do
  [ -r /proc/$p/cmdline ] && ! tr '\0' ' ' < /proc/$p/cmdline | grep -q vivado_polite && echo "$p"; done; }
while :; do
  if [ -n "$(others)" ]; then sleep "$YIELD_S"; continue; fi
  if tasklist.exe 2>/dev/null | grep -qi '^vivado.exe'; then sleep "$POLL_S"; continue; fi
  if mkdir "$LOCK" 2>/dev/null; then break; fi
  sleep "$POLL_S"
done
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT
echo "lock taken $(date +%T)"
cd "$WORK"
cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log "$(wslpath -m "$WORK/vivado.log")" \
  -source "$(wslpath -m "$WORK/run.tcl")" -tclargs "${args[@]}" > "$WORK/stdout.txt" 2>&1 || true
echo "vivado done $(date +%T)"
tail -3 "$WORK/stdout.txt"
