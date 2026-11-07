#!/usr/bin/env bash
set -euo pipefail

VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
LOCK="/mnt/c/Users/finnf/vivado.lock"
WIN_WORK="/mnt/c/Users/finnf/open-dfx-xc7-vivado/ip"
POLL_S=30
YIELD_S=300
PRIORITY="${OFX_VIVADO_PRIORITY:-high}"
DRY_RUN=1

if [ "${1:-}" = "--run" ]; then DRY_RUN=0; shift; fi
TCL="$1"; SUB="$2"; shift 2
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$WIN_WORK/$SUB"
args=()
for x in "$@"; do
  if [ "${x:0:1}" = "@" ]; then args+=("$(wslpath -m "$WORK/${x:1}")"); else args+=("$x"); fi
done
echo "[$([ $DRY_RUN = 1 ] && echo dry || echo run)] vivado -mode batch -source $TCL -tclargs ${args[*]}  (work $WORK)"
[ $DRY_RUN = 1 ] && exit 0

mkdir -p "$WORK"
cp "$ROOT/$TCL" "$WORK/run.tcl"
others_waiting() {
  pgrep -f 'ip_vivado.s[h] --run' | grep -vx -e "$$" -e "$PPID" | grep -q . && return 0
  pgrep -f 'until mkdir .*vivado.loc[k]' >/dev/null
}
while :; do
  while tasklist.exe 2>/dev/null | grep -qi '^vivado.exe'; do sleep "$POLL_S"; done
  if [ "$PRIORITY" = low ] && others_waiting; then echo "low priority: another Vivado job is waiting, sleep $YIELD_S s"; sleep "$YIELD_S"; continue; fi
  mkdir "$LOCK" 2>/dev/null && break
  sleep "$POLL_S"
done
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT INT TERM
cd "$WORK"
cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log "$(wslpath -m "$WORK/vivado.log")" \
  -source "$(wslpath -m "$WORK/run.tcl")" -tclargs "${args[@]}" > "$WORK/stdout.txt" 2>&1 || true
tail -3 "$WORK/stdout.txt"
