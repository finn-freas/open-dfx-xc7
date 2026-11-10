#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EV=${1:-$ROOT/build/hls_eval}
VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado/hls_impl
source "$ROOT/vivado/vivado_slot.sh"
trap 'exit 143' INT TERM
mkdir -p "$W" "$EV/vivado"
python3 "$ROOT/flow/hls_compare.py" vivado-prep "$W"
cp "$ROOT/flow/hls_vivado.tcl" "$W/run.tcl"
vivado_acquire
echo "$(date +%T) vivado start on $VIV_HELD"
t0=$(date +%s)
(cd "$W" && cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log vivado.log -source run.tcl > stdout.txt 2>&1)
rc=$?
vivado_release
echo "$(date +%T) vivado rc=$rc wall $(( $(date +%s)-t0 ))s"
for d in "$W"/*/; do
  n=$(basename "$d"); mkdir -p "$EV/vivado/$n"
  cp "$d"/status.txt "$d"/result.txt "$d"/util*.rpt "$d"/timing.rpt "$EV/vivado/$n/" 2>/dev/null
  echo "$n $(cat "$d/status.txt" 2>/dev/null)"
done
python3 "$ROOT/flow/hls_compare.py" vivado-collect
