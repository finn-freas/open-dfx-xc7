#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EV=$ROOT/build/hls_eval
names=()
for n in "$@"; do
  k=${n#*_}
  run=$EV/impl/$n/build/impl
  [ -f "$run/hlsw_${k}_routed.json" ] || { echo "$n: no routed build"; continue; }
  python3 "$ROOT/flow/xtime_prep.py" --run-dir "$run" --top "hlsw_$k" --xdc "$EV/impl/$n/constraints/hlsw.xdc" \
    --name "$n" --part xc7a35tcsg324-1 --out "$EV/xtime/src" --modes placed > /dev/null || { echo "$n: prep failed"; continue; }
  names+=("${n}_placed")
done
SLOT_GAP_S=${SLOT_GAP_S:-5} bash "$ROOT/vivado/slot_run.sh" hls_xtime build_xtime.tcl build/hls_eval/xtime/src "${names[@]}"
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/hls_xtime
for n in "${names[@]}"; do
  mkdir -p "$EV/xtime/out/$n"
  cp "$W/$n"/{status.txt,timing.rpt,util.rpt,place_missed.txt} "$EV/xtime/out/$n/" 2>/dev/null
  wns=$(awk '/WNS\(ns\)/{getline; getline; print $1; exit}' "$W/$n/timing.rpt" 2>/dev/null)
  echo "$n status=$(head -1 "$W/$n/status.txt" 2>/dev/null) wns=$wns placed=$(head -1 "$W/$n/place_missed.txt" 2>/dev/null)"
done
