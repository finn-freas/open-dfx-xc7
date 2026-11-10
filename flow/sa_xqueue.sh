#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
Q="$ROOT/build/sa/xq"
VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
SRC="/mnt/c/Users/finnf/open-dfx-xc7-vivado/designs/exact"
OUT="/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact_sa"
OTHER="/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/exact"
mkdir -p "$Q"
touch "$Q/names.txt"
[ -f "$Q/next" ] || echo 0 > "$Q/next"
take() {
  (
    flock 9
    i=$(cat "$Q/next")
    n=$(sed -n "$((i + 1))p" "$Q/names.txt")
    if [ -n "$n" ]; then echo $((i + 1)) > "$Q/next"; echo "$n"; fi
  ) 9> "$Q/lock"
}
case "${1:-}" in
  add)
    shift
    for n in "$@"; do (flock 9; echo "$n" >> "$Q/names.txt") 9> "$Q/lock"; done ;;
  worker)
    LOCK=vivado.lock2; SPIN=0.5; SPINS=60; MEM=3500
    [ "${2:-2}" = 1 ] && { LOCK=vivado.lock; SPIN=10; SPINS=3; MEM=2000; }
    [ "${2:-2}" = 3 ] && { LOCK=vivado.lock3; SPIN=5; SPINS=6; MEM=5000; }
    [ "${2:-2}" = 1 ] && [ "${SA_FAST:-0}" = 1 ] && { SPIN=0.5; SPINS=60; }
    source "$ROOT/vivado/vivado_slot.sh"
    mkdir -p "$OUT"
    cp "$ROOT/vivado/build_rte.tcl" "$OUT/build_rte.tcl"
    export RTE_ROUTE_DUMP=0
    export WSLENV="${WSLENV:+$WSLENV:}RTE_ROUTE_DUMP"
    trap 'exit 143' INT TERM
    HELD=0
    until_s=0; [ -n "${SA_UNTIL:-}" ] && until_s=$(date -d "$SA_UNTIL" +%s)
    while [ ! -f "$Q/STOP" ]; do
      if [ $until_s -gt 0 ] && [ $(date +%s) -ge $until_s ]; then echo "$(date +%T) window over, exiting"; break; fi
      e=$(take)
      if [ -z "$e" ]; then sleep 30; continue; fi
      set -- $e
      name="$1_p5_$2_s$3_exact"
      [ -f "$OUT/$name/status.txt" ] && continue
      [ -d "$OTHER/$name" ] && { echo "$(date +%T) $name: timed by another agent in $OTHER, skipped"; continue; }
      python3 "$ROOT/flow/exact_src.py" "$1" "$2" "$3" --run > "$Q/src_$name.log" 2>&1
      [ -f "$SRC/$name/netlist.edf" ] || { echo "$(date +%T) $name: no exact source (see $Q/src_$name.log)"; continue; }
      got=$HELD
      while [ $got = 0 ]; do
        a=$(timeout 20 powershell.exe -NoProfile -Command "[int](Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue" 2>/dev/null | tr -dc 0-9)
        if [ -n "$a" ] && [ "$a" -ge $MEM ]; then
          for i in $(seq $SPINS); do
            if [ ! -d /mnt/c/Users/finnf/$LOCK ] && _viv_mkdir $LOCK; then VIV_HELD=$LOCK; got=1; break; fi
            sleep $SPIN
          done
        else
          sleep 5
        fi
      done
      trap '_viv_rmdir "$VIV_HELD"' EXIT
      echo "$(date +%T) $name on $VIV_HELD"
      log="$OUT/vivado_$name.log"
      (cd /mnt/c/Users/finnf && exec cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log "$(wslpath -m "$log")" \
        -source "$(wslpath -m "$OUT/build_rte.tcl")" -tclargs "$(wslpath -m "$SRC")" "$(wslpath -m "$OUT")" "$name" \
        > "$OUT/stdout_$name.txt" 2>&1 < /dev/null) &
      cpid=$!
      t0=$(date +%s); done_at=""
      while kill -0 $cpid 2>/dev/null; do
        sleep 1
        now=$(date +%s)
        if [ ! -f "$log" ] && [ $((now - t0)) -gt 120 ]; then echo "$(date +%T) $name watchdog: no Vivado log after 120 s"; kill $cpid; break; fi
        if [ -f "$OUT/$name/status.txt" ]; then
          [ -z "$done_at" ] && done_at=$now
          if [ $((now - done_at)) -gt 60 ]; then echo "$(date +%T) $name watchdog: status written, cmd.exe still up"; kill $cpid; break; fi
        fi
      done
      wait $cpid 2>/dev/null
      if [ "${SA_HOLD:-0}" = 1 ]; then HELD=1; else vivado_release; fi
      echo "$(date +%T) $name $(head -1 "$OUT/$name/status.txt" 2>/dev/null) $(grep wns_noicap "$OUT/$name/slack.txt" 2>/dev/null | head -1)"
    done ;;
  *) echo "usage: $0 worker | add \"DESIGN VARIANT SEED\"..."; exit 2 ;;
esac
