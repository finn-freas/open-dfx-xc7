#!/usr/bin/env bash
set -eu
ROOT="${ROOT:-$HOME/open-dfx-xc7}"
REPO="${REPO:-$ROOT/upstream/openXC7_nextpnr}"
BASE_REV="${BASE_REV:-ce3f7c18}"
VARIANT="${VARIANT:?set VARIANT, e.g. dsp}"
PATCHES="${PATCHES:?space-separated patch files under docs/drafts}"
SRC="$ROOT/build/src/nextpnr-$VARIANT"
BLD="$ROOT/build/nextpnr-build/$VARIANT"
DRY_RUN="${DRY_RUN:-1}"

case "$VARIANT" in stock|router|pblock) echo "refusing to touch $VARIANT"; exit 1;; esac
run() { echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $*"; [ "$DRY_RUN" = 1 ] || "$@"; }
source "$ROOT/toolchain/buildenv/env.sh"
if [ ! -d "$SRC" ]; then
    run git -C "$REPO" worktree add --detach "$SRC" "$BASE_REV"
fi
if [ "$DRY_RUN" != 1 ] && git -C "$SRC" diff --quiet; then
    for p in $PATCHES; do
        run git -C "$SRC" apply "$ROOT/docs/drafts/$p"
    done
fi
if [ ! -f "$BLD/build.ninja" ]; then
    run cmake -S "$SRC" -B "$BLD" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCURRENT_GIT_VERSION="$(git -C "$SRC" rev-parse --short=8 HEAD)-$VARIANT" \
        -DARCH=himbaechel -DHIMBAECHEL_UARCH=xilinx -DHIMBAECHEL_XILINX_DEVICES= \
        -DHIMBAECHEL_PRJXRAY_DB="$ROOT/toolchain/openxc7/share/nextpnr/external/prjxray-db" \
        -DBUILD_GUI=OFF -DBUILD_TESTS=OFF -DBUILD_PYTHON=OFF \
        -DPython3_EXECUTABLE="$BUILDENV_PREFIX/bin/python3.12" -Wno-deprecated
fi
run ninja -C "$BLD" -j"${JOBS:-8}" nextpnr-himbaechel
[ "$DRY_RUN" = 1 ] || git -C "$SRC" diff --stat
