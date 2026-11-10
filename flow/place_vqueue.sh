#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
Q="$ROOT/build/qor/place/gp/vq"
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
    for n in "$@"; do
      touch "$ROOT/build/qor/place/xsrc/$n/dump.flag" 2>/dev/null
      (flock 9; echo "$n" >> "$Q/names.txt") 9> "$Q/lock"
    done ;;
  worker)
    id=${2:-1}
    while [ ! -f "$Q/STOP" ]; do
      n=$(take)
      if [ -z "$n" ]; then sleep 30; continue; fi
      echo "$(date +%T) w$id take $n"
      if [ "$id" = 2 ]; then VIV_SLOT=2 "$ROOT/flow/place_vivado.sh" --run "$n"; else "$ROOT/flow/place_vivado.sh" --run "$n"; fi
    done ;;
  *) echo "usage: $0 worker ID | add NAME..."; exit 2 ;;
esac
