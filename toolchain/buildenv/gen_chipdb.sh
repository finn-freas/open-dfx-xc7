#!/usr/bin/env bash
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIE="${DIE:-xc7a50t}"
FAMILY="${FAMILY:-artix7}"
META_REV="${META_REV:-8a3f5a09}"
META_URL="${META_URL:-https://github.com/openXC7/nextpnr-xilinx-meta.git}"
SRC="${SRC:-$ROOT/build/src/nextpnr-stock}"
BBASM="${BBASM:-$ROOT/build/nextpnr-build/stock/bba/bbasm}"
XRAY="${XRAY:-$ROOT/toolchain/openxc7/share/nextpnr/external/prjxray-db}"
OUT="${OUT:-$ROOT/build/chipdb}"
META="${META:-$OUT/meta}"
GEN_ARGS="${GEN_ARGS:-}"
DRY_RUN="${DRY_RUN:-1}"

source "$ROOT/toolchain/buildenv/env.sh"
run() { echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $*"; [ "$DRY_RUN" = 1 ] || "$@"; }
mkdir -p "$OUT"
if [ ! -d "$META/.git" ]; then
    run git clone --no-checkout "$META_URL" "$META"
    run git -C "$META" checkout --detach "$META_REV"
fi
if [ ! -f "$OUT/chipdb-$DIE.bba" ]; then
    export PYTHONDONTWRITEBYTECODE=1
    run python3 "$SRC/himbaechel/uarch/xilinx/gen/xilinx_gen.py" --xray "$XRAY/$FAMILY" --device "$DIE" \
        --metadata "$META/$FAMILY" --bba "$OUT/chipdb-$DIE.bba.tmp" $GEN_ARGS
    [ "$DRY_RUN" = 1 ] || mv "$OUT/chipdb-$DIE.bba.tmp" "$OUT/chipdb-$DIE.bba"
fi
if [ ! -f "$OUT/chipdb-$DIE.bin" ]; then
    run "$BBASM" --le "$OUT/chipdb-$DIE.bba" "$OUT/chipdb-$DIE.bin"
fi
