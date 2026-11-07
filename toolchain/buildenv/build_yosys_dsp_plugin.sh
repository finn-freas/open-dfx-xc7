#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="${SRC:-$ROOT/build/src/yosys-dspqor}"
PASS="${PASS:-xilinx_dsp_qor}"
OUT="${OUT:-$ROOT/build/yosys-plugin/$PASS}"
OCS="${OCS:-$ROOT/toolchain/oss-cad-suite}"
PY="${PY:-$ROOT/toolchain/buildenv/env/bin/python3.12}"
CXX="${CXX:-g++}"
YOSYS_VER="${YOSYS_VER:-0.70+186}"
PMGS="${PMGS:-xilinx_dsp xilinx_dsp48a xilinx_dsp_CREG xilinx_dsp_cascade}"
DRY_RUN="${DRY_RUN:-1}"

run() { echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $*"; [ "$DRY_RUN" = 1 ] || "$@"; }
[ "$DRY_RUN" = 1 ] || mkdir -p "$OUT/techlibs/xilinx"
for p in $PMGS; do
    run "$PY" "$SRC/passes/pmgen/pmgen.py" -o "$OUT/techlibs/xilinx/${p}_pm.h" "$SRC/techlibs/xilinx/$p.pmg"
done
if [ "$DRY_RUN" != 1 ]; then
    sed -e "s/XilinxDspPass() : Pass(\"xilinx_dsp\"/XilinxDspPass() : Pass(\"$PASS\"/" -e 's/XilinxDspPass/XilinxDspQorPass/g' \
        "$SRC/techlibs/xilinx/xilinx_dsp.cc" > "$OUT/$PASS.cc"
    git -C "$SRC" diff --stat > "$OUT/source_diff.txt" || true
fi
run "$CXX" -std=c++20 -fPIC -O2 -D_YOSYS_ "-DYOSYS_VER=\"$YOSYS_VER\"" -DYOSYS_MAJOR=0 -DYOSYS_MINOR=70 -DYOSYS_COMMIT=186 \
    -I"$OCS/share/yosys/include" -I"$OUT" -shared -o "$OUT/$PASS.so" "$OUT/$PASS.cc"
run "$OCS/bin/yosys" -m "$OUT/$PASS.so" -q -p "help $PASS"
