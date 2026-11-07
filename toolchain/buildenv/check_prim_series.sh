#!/usr/bin/env bash
set -eu
ROOT="${ROOT:-$HOME/open-dfx-xc7}"
REPO="${REPO:-$ROOT/upstream/openXC7_nextpnr}"
BASE_REV="${BASE_REV:-ce3f7c18}"
TMP="${TMP:-/tmp/prim_series_check}"
REF="${REF:-$ROOT/build/src/nextpnr-ofx-prim}"
OFX_SERIES="${OFX_SERIES:-pblock-xdc router-region pblock-replay pblock-routethru partition-pins pblock-lutff carry-replay-order partition-pins-route dsp-mask-areg iserdes-const-pins muxf7-mixed-loads}"
SERIES="${SERIES:-io-buffer-params mmcm-base-ties bufh-region diff-term cfg-in-use clkout-unused fifo}"
DRY_RUN="${DRY_RUN:-1}"

run() { echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $*"; [ "$DRY_RUN" = 1 ] || "$@"; }
run rm -rf "$TMP"
run git -C "$REPO" worktree prune
run git -C "$REPO" worktree add --detach "$TMP" "$BASE_REV"
for p in $OFX_SERIES $SERIES; do
    run git -C "$TMP" apply "$ROOT/docs/drafts/nextpnr-$p.patch"
done
if [ "$DRY_RUN" != 1 ]; then
    diff -r -q --exclude=.git "$TMP" "$REF" && echo "tree identical to $REF"
fi
run git -C "$REPO" worktree remove --force "$TMP"
