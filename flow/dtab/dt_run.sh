#!/usr/bin/env bash
set -u
R=/home/finnf/open-dfx-xc7
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado
cd "$R" || exit 1
V="${V:-cb2_dt cb2_dtnf}"
TAG="${TAG:-dt}"
SEEDS="${SEEDS:-1 2 3}"
DESIGNS="${DESIGNS:-rv_soc bram rv_big rv_mul}"
Q="$R/build/dtab/q_${TAG}.txt"
touch "$Q"
for s in $SEEDS; do
  for v in $V; do
    for d in $DESIGNS; do
      [ -f "$R/build/dtab/STOP" ] && { echo "STOP file, leaving"; exit 0; }
      free=$(df -BG /mnt/c | awk 'NR==2{gsub("G","",$4); print $4}')
      [ "${free:-0}" -ge 40 ] || { echo "C: only ${free} GB free"; exit 1; }
      vv=$v; [ "$d" = rv_mul ] && vv=${v}_dq
      n="${d}_p5_${vv}_s${s}_exact"
      if [ ! -f "$W/build/exact/$n/slack.txt" ]; then
        python3 flow/place_bench.py --designs "$d" --variants "$vv" --seeds "$s" --run
        python3 flow/exact_src.py "$d" "$vv" "$s" --run > /dev/null 2> "build/dtab/exsrc_$n.err" || { echo "exact_src failed $n"; continue; }
        rm -f "build/dtab/exsrc_$n.err"
      fi
      grep -qx "$n" "$Q" || echo "$n" >> "$Q"
    done
  done
done
echo "${TAG}_DONE" >> "$Q"
echo "${TAG}_DONE"
