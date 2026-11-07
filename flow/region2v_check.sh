#!/usr/bin/env bash
DESIGNS="${DESIGNS:-rv_pr rv_b rv_c rv_flash}"
OUT="${OUT:-build/region2v}"
BM="${BM:-build/byteman_check}"
CORRUPT="${CORRUPT:-rv_pr:xor rv_pr:add rv_b:add}"
cd "$(dirname "$0")/.."
declare -A SRC=([rv_pr]=rv_soc [rv_b]=rv_soc [rv_c]=rv_soc [rv_flash]=rv_flash)
declare -A TOP=([rv_pr]=rv_soc [rv_b]=rv_soc [rv_c]=rv_soc [rv_flash]=rv_flash)
declare -A PFX=([rv_pr]=rv_pr [rv_b]=rv_b [rv_c]=rv_c [rv_flash]=pr)
declare -A SHELL=([rv_pr]=designs/rv_soc/pr/rm_shell.v [rv_b]=build/pr/rv_b/rm_shell.v [rv_c]=build/pr/rv_c/rm_shell.v [rv_flash]=designs/rv_soc/pr/rm_shell.v)
mkdir -p "$OUT"
LOG="$OUT/check.log"
: > "$LOG"
fail=0
run() {
  local tag=$1 bit=$2 reg=$3 shell=$4 rm=$5; shift 5
  if [ ! -e "$bit" ]; then echo "SKIP $tag: no $bit" | tee -a "$LOG"; return; fi
  python3 flow/region2v.py check "$bit" "$reg" --shell "$shell" --rm "$rm" --tag "$tag" --formal "$@" 2>&1 | tee -a "$LOG"
  return "${PIPESTATUS[0]}"
}
for d in $DESIGNS; do
  reg=$(cat "build/pr/$d/region.txt")
  sh=${SHELL[$d]}
  for b in build/openxc7/${SRC[$d]}/${PFX[$d]}_*_c/${TOP[$d]}.bit; do
    rm=$(basename "$(dirname "$b")" | sed -E "s/^${PFX[$d]}_(.*)_c$/\1/")
    run "${d}_${rm}_c" "$b" "$reg" "$sh" "$rm" || fail=1
  done
  for b in "$BM"/${d}_rm_*_from_*.bit "$BM"/${d}_*_rt.bit; do
    [ -e "$b" ] || continue
    n=$(basename "$b" .bit)
    rm=$(echo "$n" | sed -E "s/^${d}_rm_(.*)_from_.*$/\1/; s/^${d}_(.*)_rt$/\1/")
    run "bm_${n}" "$b" "$reg" "$sh" "$rm" || fail=1
  done
  for b in "$BM"/${d}_*_plus_*.bit; do
    [ -e "$b" ] || continue
    n=$(basename "$b" .bit)
    rm=$(echo "$n" | sed -E "s/^.*_plus_(.*)$/\1/")
    run "bm_assumed_${n}" "$b" "$reg" "$sh" "$rm" || fail=1
  done
done
for c in $CORRUPT; do
  d=${c%%:*}; rm=${c##*:}
  reg=$(cat "build/pr/$d/region.txt")
  if run "${d}_${rm}_c" "build/openxc7/${SRC[$d]}/${PFX[$d]}_${rm}_c/${TOP[$d]}.bit" "$reg" "${SHELL[$d]}" "$rm" --corrupt; then
    echo "NEGATIVE-CONTROL-NOT-DETECTED ${d}_${rm}_c" | tee -a "$LOG"; fail=1
  else
    echo "NEGATIVE-CONTROL-DETECTED ${d}_${rm}_c" | tee -a "$LOG"
  fi
done
exit $fail
