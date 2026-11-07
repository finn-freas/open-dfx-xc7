#!/usr/bin/env bash
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="${SRC:-$ROOT/build/src/yosys-clkbuf/passes/techmap/clkbufmap.cc}"
PASS="${PASS:-clkbufmap_gapfix}"
OUT="${OUT:-$ROOT/build/yosys-plugin}"
OCS="${OCS:-$ROOT/toolchain/oss-cad-suite}"
CXX="${CXX:-g++}"
YOSYS_VER="${YOSYS_VER:-0.70+186}"
DRY_RUN="${DRY_RUN:-1}"

run() { echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $*"; [ "$DRY_RUN" = 1 ] || "$@"; }
mkdir -p "$OUT"
if [ "$DRY_RUN" != 1 ]; then
    sed -e "s/Pass(\"clkbufmap\",/Pass(\"$PASS\",/" -e 's/ClkbufmapPass/ClkbufmapGapfixPass/g' "$SRC" > "$OUT/$PASS.cc"
fi
run "$CXX" -std=c++20 -fPIC -O2 -D_YOSYS_ "-DYOSYS_VER=\"$YOSYS_VER\"" -DYOSYS_MAJOR=0 -DYOSYS_MINOR=70 -DYOSYS_COMMIT=186 \
    -I"$OCS/share/yosys/include" -shared -o "$OUT/$PASS.so" "$OUT/$PASS.cc"
run "$OCS/bin/yosys" -m "$OUT/$PASS.so" -q -p "help $PASS"
