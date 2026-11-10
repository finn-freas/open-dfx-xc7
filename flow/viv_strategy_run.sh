#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VW=/mnt/c/Users/finnf/open-dfx-xc7-vivado
VIVADO_BAT="/mnt/c/AMDDesignTools/2025.2/Vivado/bin/vivado.bat"
SRC=$VW/designs/viv_strategy
OUT=$VW/build/viv_strategy
WORK=$VW/viv_strategy
ALL_DIRS="Default Explore ExtraTimingOpt AltSpreadLogic_high SpreadLogic_high ExtraNetDelay_high Default_nopsip"

prep_edif() {
  local d=$SRC/$1; mkdir -p "$d"; cp "$VW/designs/exact/$2/netlist.edf" "$VW/designs/exact/$2/constraints.xdc" "$d/"
  printf 'mode edif\ntop %s\ndirectives %s\n' "$(cat "$VW/designs/exact/$2/top.txt" | tr -d '\r')" "$3" > "$d/job.txt"
}
prep_qor() {
  local d=$SRC/$1; mkdir -p "$d"; cp "$VW/designs/qor/$2_p5/"* "$d/"; rm -f "$d/top.txt.bak"
  printf 'mode rtl\ntop %s\ndirectives %s\n' "$(cat "$d/top.txt" | tr -d '\r')" "$3" > "$d/job.txt"
}
prep_suite() {
  local d=$SRC/$1; mkdir -p "$d"; cp "$VW/designs/qor_suite/$2/"* "$d/" 2>/dev/null
  printf 'mode rtl\ntop suite_top\npart %s\nperiod %s\ndirectives %s\n' "$(cat "$d/part.txt" | tr -d '\r')" "$3" "$4" > "$d/job.txt"
}

if [ "${1:-}" = prep ]; then
  prep_edif rv_soc_edif rv_soc_p5_vref_exact "$ALL_DIRS"
  prep_edif bram_edif bram_p5_vref_exact "Default Explore ExtraTimingOpt AltSpreadLogic_high Default_nopsip"
  for d in rv_soc bram rv_mul rv_big; do prep_qor ${d}_rtl $d "Default"; done
  prep_suite aes_rtl aes 6 Default; prep_suite sha256_rtl sha256 6 Default
  prep_suite or1200_rtl or1200 10 Default; prep_suite serv_rtl serv 5 Default
  ls "$SRC"; exit 0
fi
[ "${1:-}" = run ] || { echo "usage: $0 prep | run NAME..."; exit 1; }
shift
source "$ROOT/vivado/vivado_slot.sh"
mkdir -p "$OUT" "$WORK"
cp "$ROOT/vivado/viv_strategy.tcl" "$WORK/run.tcl"
cp "$ROOT/vivado/build_rte.tcl" "$WORK/run_rte.tcl"
for n in "$@"; do
  [ -f "$OUT/$n/status.txt" ] && continue
  vivado_acquire3
  echo "$(date +%T) $n on $VIV_HELD"
  log="$OUT/vivado_${n}.log"
  tcl="$WORK/run.tcl"; [ -f "$SRC/$n/mode.txt" ] && tcl="$WORK/run_rte.tcl"
  (cd "$WORK" && exec cmd.exe /c "$(wslpath -w "$VIVADO_BAT")" -mode batch -nojournal -log "$(wslpath -m "$log")" \
    -source "$(wslpath -m "$tcl")" -tclargs "$(wslpath -m "$SRC")" "$(wslpath -m "$OUT")" "$n" \
    > "$WORK/stdout_$n.txt" 2>&1 < /dev/null)
  vivado_release
  echo "$(date +%T) $n $(head -1 "$OUT/$n/status.txt" 2>/dev/null)"
done
echo "$(date +%T) all done"
