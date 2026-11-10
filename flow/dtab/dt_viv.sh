#!/usr/bin/env bash
set -u
R=/home/finnf/open-dfx-xc7
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado
cd "$R" || exit 1
TAG="${TAG:-dt}"
ID="${1:-1}"
Q="$R/build/dtab/q_${TAG}.txt"
export SRC=$W/designs/exact RTE_OUT=$W/build/exact RTE_ROUTE_DUMP=0 RTE_ANY_SLOT=1
while true; do
  [ -f "$R/build/dtab/STOP" ] && { echo "STOP file, leaving"; exit 0; }
  did=0
  for n in $(grep -v "_DONE$" "$Q" 2>/dev/null); do
    [ -f "$W/build/exact/$n/status.txt" ] && continue
    [ -d "$R/build/exact/claims/$n" ] && continue
    bash flow/rte_dump_vivado.sh --run "$n" >> "build/dtab/${TAG}_viv_w${ID}.log" 2>&1
    did=1
    break
  done
  if [ $did = 0 ]; then
    grep -q "^${TAG}_DONE$" "$Q" 2>/dev/null && break
    sleep 20
  fi
done
echo "worker $ID done"
