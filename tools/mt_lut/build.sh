#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MT="${MOCKTURTLE:-$ROOT/toolchain/bambu/src/ext/mockturtle/mockturtle}"
OUT="${1:-$ROOT/build/mt_lut/mt_lut}"
OBJ="$ROOT/build/mt_lut/obj"
CXX="${CXX:-g++}"
[ -d "$MT/include/mockturtle" ] || { echo "mockturtle not found at $MT (set MOCKTURTLE)"; exit 1; }
mkdir -p "$OBJ" "$(dirname "$OUT")"
INC=(-I"$MT/include")
for l in abcesop abcsat bill fmt json kitty lorina nauty parallel_hashmap percy rang; do INC+=(-I"$MT/lib/$l"); done
for f in "$MT"/lib/abcesop/*.cpp; do
  o="$OBJ/esop_$(basename "${f%.*}").o"
  [ -f "$o" ] || "$CXX" -std=c++17 -O2 -w "${INC[@]}" -c "$f" -o "$o"
done
"$CXX" -std=c++17 -O2 -w -DFMT_HEADER_ONLY "${INC[@]}" "$ROOT/tools/mt_lut/mt_lut.cpp" "$OBJ"/esop_*.o -o "$OUT" -lpthread
echo "built $OUT"
