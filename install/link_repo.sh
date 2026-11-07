#!/usr/bin/env bash
set -euo pipefail

PREFIX="${OFX_PREFIX:-$HOME/.local/ofx}"
REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
NATIVE_VARIANTS="${NATIVE_VARIANTS:-stock router router_nokeepout pblock replay rtkeep partpin partpin2 partpin3 rkcrit}"
DRY_RUN=1

while [ $# -gt 0 ]; do
    case "$1" in
        --run) DRY_RUN=0 ;;
        --prefix) PREFIX="$2"; shift ;;
        --repo) REPO="$2"; shift ;;
        -h|--help) echo "usage: link_repo.sh [--run] [--prefix DIR] [--repo DIR]: point a checkout's toolchain/ paths at an installed prefix"; exit 0 ;;
        *) echo "unknown option $1" >&2; exit 2 ;;
    esac
    shift
done
PREFIX="$(realpath -m "$PREFIX")"
REPO="$(realpath -m "$REPO")"
[ -x "$PREFIX/bin/nextpnr-himbaechel" ] || [ "$DRY_RUN" = 1 ] || { echo "no toolchain in $PREFIX (run install/install.sh --run first)" >&2; exit 1; }

link() {
    local target=$1 path=$2
    if [ -L "$path" ] && [ "$(readlink "$path")" = "$target" ]; then
        echo "[ok]   $path"
        return
    fi
    if [ -e "$path" ] || [ -L "$path" ]; then
        echo "[keep] $path exists and is not a link to $target; left alone" >&2
        return
    fi
    echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] ln -s $target $path"
    [ "$DRY_RUN" = 1 ] || { mkdir -p "$(dirname "$path")"; ln -s "$target" "$path"; }
}

link "$PREFIX" "$REPO/toolchain/openxc7"
link "$PREFIX/share/ofx/openxc7-BUILD-INFO.json" "$REPO/toolchain/openxc7-BUILD-INFO.json"
if [ -d "$PREFIX/opt/oss-cad-suite" ] || [ "$DRY_RUN" = 1 ]; then
    link "$PREFIX/opt/oss-cad-suite" "$REPO/toolchain/oss-cad-suite"
fi
link "$PREFIX/bin/byteman" "$REPO/toolchain/byteman-build/byteman"
for v in $NATIVE_VARIANTS; do
    link "$PREFIX/bin/nextpnr-himbaechel" "$REPO/build/nextpnr-build/$v/nextpnr-himbaechel"
done
