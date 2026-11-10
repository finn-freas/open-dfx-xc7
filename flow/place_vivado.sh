#!/usr/bin/env bash
set -uo pipefail

VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
WIN_WORK="/mnt/c/Users/finnf/open-dfx-xc7-vivado/gplace"
OUT="/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/place_xtime2"
EXACT_SRC="/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact"
EXACT_OUT="/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact"
DRY_RUN=1

if [ "${1:-}" = "--run" ]; then DRY_RUN=0; shift; fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/build/qor/place/xsrc"
echo "[$([ $DRY_RUN = 1 ] && echo dry || echo run)] vivado build_xtime.tcl on $# source(s): $*"
[ $DRY_RUN = 1 ] && exit 0
source "$ROOT/vivado/vivado_slot.sh"
win_avail_mb() { timeout 30 powershell.exe -NoProfile -Command "[int](Get-Counter '\\Memory\\Available MBytes').CounterSamples.CookedValue" 2>/dev/null < /dev/null | tr -d '\r'; }
SLOT1_MIN=${SLOT1_MIN:-6}
slot1_ok() {
  local q="$ROOT/build/qor/place/gp/vq"
  if [ -f "$q/names.txt" ] && [ -f "$q/next" ]; then
    local left=$(( $(wc -l < "$q/names.txt") - $(cat "$q/next") ))
    [ "$left" -ge "$SLOT1_MIN" ] && echo 1 || echo 0
  else
    echo 1
  fi
}
trap 'exit 143' INT TERM
mkdir -p "$WIN_WORK/src" "$OUT"
cp "$ROOT/vivado/build_xtime.tcl" "$WIN_WORK/run.tcl"
cp "$ROOT/vivado/build_rte.tcl" "$WIN_WORK/run_rte.tcl"
mkdir -p "$EXACT_OUT"
for n in "$@"; do
  if [ "${n%_exact}" != "$n" ]; then
    o="$EXACT_OUT"; s="$EXACT_SRC"; tcl="$WIN_WORK/run_rte.tcl"
    [ -f "$o/$n/status.txt" ] && continue
    [ -f "$o/../exact_sa/$n/status.txt" ] && continue
    [ -d "$s/$n" ] || { echo "no source $n"; continue; }
    touch "$s/$n/dump.flag"
  else
    o="$OUT"; s="$WIN_WORK/src"; tcl="$WIN_WORK/run.tcl"
    [ -f "$OUT/$n/status.txt" ] && continue
    [ -d "$SRC/$n" ] || { echo "no source $n"; continue; }
    rm -rf "$WIN_WORK/src/$n"
    cp -r "$SRC/$n" "$WIN_WORK/src/$n"
  fi
  while true; do
    if [ "${VIV_SLOT:-2}" = any ] && [ "$(slot1_ok)" = 1 ] && _viv_mkdir vivado.lock; then VIV_HELD=vivado.lock; break; fi
    a=$(win_avail_mb); if [ -n "$a" ] && [ "$a" -ge 3500 ] && _viv_mkdir vivado.lock2; then VIV_HELD=vivado.lock2; break; fi
    sleep 5
  done
  trap '_viv_rmdir "$VIV_HELD"' EXIT
  echo "$(date +%T) $n on $VIV_HELD (VIV_SLOT=${VIV_SLOT:-2})"
  log="$o/vivado_${n}.log"
  (cd "$WIN_WORK" && exec cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log "$(wslpath -m "$log")" \
    -source "$(wslpath -m "$tcl")" -tclargs "$(wslpath -m "$s")" "$(wslpath -m "$o")" "$n" \
    > "$WIN_WORK/stdout_$n.txt" 2>&1 < /dev/null) &
  cpid=$!
  t0=$(date +%s); done_at=""
  while kill -0 $cpid 2>/dev/null; do
    sleep 5
    now=$(date +%s)
    if [ ! -f "$log" ] && [ $((now - t0)) -gt 120 ]; then echo "$(date +%T) $n watchdog: no Vivado log after 120 s, killing cmd.exe"; kill $cpid; break; fi
    if [ -f "$o/$n/status.txt" ]; then
      [ -z "$done_at" ] && done_at=$now
      if [ $((now - done_at)) -gt 60 ]; then echo "$(date +%T) $n watchdog: status written, cmd.exe still up after 60 s, killing it"; kill $cpid; break; fi
    fi
  done
  wait $cpid 2>/dev/null
  vivado_release
  echo "$(date +%T) $n $(head -1 "$o/$n/status.txt" 2>/dev/null)"
done
