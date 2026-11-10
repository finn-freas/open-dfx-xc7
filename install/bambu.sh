#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
B=$ROOT/toolchain/bambu
URL=https://github.com/ferrandi/PandA-bambu.git
TAG=2026.11
REV=cda4db2e724df357f749c0c41b12bdc065462ced
SUBS="ext/abseil/abseil-cpp ext/mockturtle/mockturtle ext/pugixml ext/buddy ext/gcem ext/glaze etc/ac_types etc/ac_math"
JOBS=${JOBS:-4}
chk() { f=$(df -BG --output=avail /mnt/c 2>/dev/null | tail -1 | tr -dc 0-9); echo "$(date +%T) C: free ${f:-?}G"; [ -z "$f" ] || [ "$f" -ge 40 ]; }
chk || { echo "C: below 40 GB, stop"; exit 2; }
for t in git cmake bison flex clang-19 clang++-19 llvm-config-19 opt-19 llvm-link-19; do
  command -v $t > /dev/null || { echo "missing $t (see docs/hls.md for the apt packages)"; exit 3; }
done
mkdir -p "$B"
[ -d "$B/src/.git" ] || git clone --quiet --depth 1 --branch "$TAG" "$URL" "$B/src"
cd "$B/src"
[ "$(git rev-parse HEAD)" = "$REV" ] || { echo "toolchain/bambu/src is not $TAG ($REV)"; exit 4; }
for s in $SUBS; do git submodule update --init --depth 1 --quiet "$s"; done
G=""; command -v ninja > /dev/null && G="-G Ninja"
cmake -S "$B/src" -B "$B/build" $G -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$B/install" \
  -DPANDA_BUILD_EUCALYPTUS=OFF -DPANDA_ENABLE_WERROR=OFF -DPANDA_SYNC_PARAMETER_METADATA=OFF > "$B/cmake.log" 2>&1 \
  || { tail -40 "$B/cmake.log"; exit 5; }
( while sleep 300; do chk || { echo "C: below 40 GB, stopping the build"; pkill -f "cmake --build $B/build"; exit; }; done ) &
W=$!
rc=0; nice -n 10 cmake --build "$B/build" -j "$JOBS" > "$B/build.log" 2>&1 || rc=$?
kill $W 2> /dev/null || true
[ $rc -eq 0 ] || { tail -40 "$B/build.log"; exit 6; }
nice -n 10 cmake --install "$B/build" > "$B/install.log" 2>&1 || { tail -20 "$B/install.log"; exit 7; }
chk || true
du -sh "$B/src" "$B/build" "$B/install"
"$B/install/bin/bambu" --version 2>&1 | head -5
