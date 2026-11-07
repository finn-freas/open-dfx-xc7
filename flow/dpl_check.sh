#!/usr/bin/env bash
set -euo pipefail
DB="${DB:-$HOME/ofx-test/prefix/share/nextpnr/external/prjxray-db/artix7}"
PART=xc7a35tcsg324-1
RUN="$1"; TOP="$2"; NAME="$3"
cd "$(dirname "$0")/.."
source flow/../toolchain/buildenv/env.sh 2>/dev/null || true
F2F=$(python3 -c "import sys; sys.path.insert(0,'flow'); from build_openxc7 import tool; print(tool('fasm2frames'))")
F2B=$(python3 -c "import sys; sys.path.insert(0,'flow'); from build_openxc7 import tool; print(tool('xc7frames2bit'))")
OUT="$RUN/check"
mkdir -p "$OUT"
"$F2F" --part $PART --db-root "$DB" "$RUN/$TOP.fasm" > "$OUT/$TOP.frames" 2> "$OUT/fasm2frames.log" || { echo "FAIL fasm2frames ($OUT/fasm2frames.log)"; exit 1; }
"$F2B" --part_file="$DB/$PART/part.yaml" --part_name=$PART --frm_file="$OUT/$TOP.frames" --output_file="$OUT/$TOP.bit" > "$OUT/frames2bit.log" 2>&1 || { echo "FAIL xc7frames2bit"; exit 1; }
bash flow/bit2netlist.sh "$NAME" "$OUT/$TOP.bit" "$TOP" xor pass 2>&1 | tail -4
