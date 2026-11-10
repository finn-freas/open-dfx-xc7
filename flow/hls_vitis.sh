#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT=$1; shift
VITIS_RUN="/mnt/c/AMDDesignTools/2025.2/Vitis/bin/vitis-run.bat"
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado/hls_cmp
source "$ROOT/vivado/vivado_slot.sh"
trap 'exit 143' INT TERM
mkdir -p "$W/src" "$OUT"
for k in "$@"; do rm -rf "$W/src/$k"; mkdir -p "$W/src/$k"; cp "$ROOT/designs/hls/$k"/*.[ch] "$W/src/$k/"; done
cp "$ROOT/flow/hls_vitis.tcl" "$W/run.tcl"
export HLS_KERNELS="$*"
export WSLENV="HLS_KERNELS:HLS_CLK_NS:HLS_PART:HLS_COSIM:HLS_DF_STRICT"
vivado_acquire
echo "$(date +%T) vitis start on $VIV_HELD"
t0=$(date +%s)
(cd "$W" && cmd.exe /c "$(wslpath -w "$VITIS_RUN")" --mode hls --tcl run.tcl > "$W/vitis_stdout.txt" 2>&1)
rc=$?
vivado_release
echo "$(date +%T) vitis rc=$rc wall $(( $(date +%s)-t0 ))s"
grep HLS_RESULT "$W/vitis_stdout.txt"
cp "$W/vitis_stdout.txt" "$OUT/"
for k in "$@"; do
  s="$W/prj_$k/sol"
  mkdir -p "$OUT/$k/rtl"
  cp "$s/syn/verilog/"* "$OUT/$k/rtl/" 2>/dev/null
  cp "$s/syn/report/${k}_csynth.xml" "$s/syn/report/${k}_csynth.rpt" "$OUT/$k/" 2>/dev/null
  cp "$s/sim/report/${k}_cosim.rpt" "$OUT/$k/" 2>/dev/null
done
