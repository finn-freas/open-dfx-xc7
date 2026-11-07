#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARTIAL="${PARTIAL:-$ROOT/build/partials/rv_pr/rm_andn_from_xor.bin}"
STOCK="${STOCK:-$ROOT/build/ofl-build/stock/openFPGALoader}"
PATCHED="${PATCHED:-$ROOT/build/ofl-build/partial/openFPGALoader}"
OUT="${OUT:-$ROOT/build/patched/ofl_virtual}"
PORT="${PORT:-2542}"
DRY_RUN="${DRY_RUN:-1}"

cases=("stock_noflag:$STOCK:" "patched_noflag:$PATCHED:" "patched_partial:$PATCHED:--partial")
if [ "$DRY_RUN" = 1 ]; then
    for c in "${cases[@]}"; do IFS=: read -r name bin flag <<< "$c"; echo "[dry] $name: $bin -c xvc-client --ip 127.0.0.1 --port $PORT $flag $PARTIAL"; done
    exit 0
fi
mkdir -p "$OUT"
for c in "${cases[@]}"; do
    IFS=: read -r name bin flag <<< "$c"
    python3 "$ROOT/flow/xvc_trace.py" "$OUT/$name.json" --cfg-out "$OUT/$name.cfg_in.bin" --port "$PORT" > "$OUT/$name.trace.txt" 2>&1 &
    srv=$!
    sleep 1
    "$bin" -c xvc-client --ip 127.0.0.1 --port "$PORT" $flag "$PARTIAL" > "$OUT/$name.ofl.txt" 2>&1
    echo "$name: openFPGALoader exit $?"
    wait $srv
    tail -1 "$OUT/$name.trace.txt"
done
python3 - "$PARTIAL" "$OUT" <<'EOF'
import sys
from pathlib import Path
src = Path(sys.argv[1]).read_bytes()
rev = bytes(int(f"{b:08b}"[::-1], 2) for b in src)
for p in sorted(Path(sys.argv[2]).glob("*.cfg_in.bin")):
    d = p.read_bytes()
    print(f"{p.name}: {len(d)} bytes; equals file: {d == src}; equals bit-reversed file: {d == rev}")
EOF
