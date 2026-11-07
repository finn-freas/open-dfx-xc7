#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC="${SRC:-$ROOT/build/src/yosys-dspqor}"
BLD="${BLD:-$ROOT/build/yosys-build/$(basename "$SRC")}"
BISONFLEX="${BISONFLEX:-$ROOT/toolchain/buildenv/env-bisonflex}"
ABC="${ABC:-$ROOT/toolchain/oss-cad-suite/bin/yosys-abc}"
JOBS="${JOBS:-2}"
DRY_RUN="${DRY_RUN:-1}"

run() { echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $*"; [ "$DRY_RUN" = 1 ] || "$@"; }
source "$ROOT/toolchain/buildenv/env.sh"
export PATH="$BISONFLEX/bin:$PATH"
if [ ! -f "$BLD/build.ninja" ] || [ "${RECONFIGURE:-0}" = 1 ]; then
    run cmake -S "$SRC" -B "$BLD" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_FLAGS="-I$BUILDENV_PREFIX/include" -DCMAKE_CXX_FLAGS="-I$BUILDENV_PREFIX/include" \
        -DCMAKE_PREFIX_PATH="$BUILDENV_PREFIX" \
        -DYOSYS_ABC_EXECUTABLE="$ABC" -DYOSYS_SKIP_ABC_SUBMODULE_CHECK=ON \
        -DYOSYS_WITHOUT_SLANG=ON -DYOSYS_WITHOUT_TCL=ON -DYOSYS_WITHOUT_READLINE=ON -DYOSYS_WITHOUT_EDITLINE=ON \
        -DYOSYS_WITHOUT_LIBFFI=ON -DYOSYS_ENABLE_UNIT_TESTS=OFF \
        -DBISON_EXECUTABLE="$BISONFLEX/bin/bison" -DFLEX_EXECUTABLE="$BISONFLEX/bin/flex" \
        -DPython3_EXECUTABLE="$BUILDENV_PREFIX/bin/python3.12"
fi
run nice ninja -C "$BLD" -j"$JOBS"
