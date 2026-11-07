#!/usr/bin/env bash
DESIGNS="${DESIGNS:-pr_uart rv_pr rv_b rv_c}"
cd "$(dirname "$0")/.."
declare -A SRC=([pr_open]=pr_open [pr_uart]=pr_uart [rv_pr]=rv_soc [rv_b]=rv_soc [rv_c]=rv_soc [rv_d]=rv_soc)
declare -A TOP=([pr_open]=top [pr_uart]=top [rv_pr]=rv_soc [rv_b]=rv_soc [rv_c]=rv_soc [rv_d]=rv_soc)
declare -A PFX=([pr_open]=pr [pr_uart]=pr [rv_pr]=rv_pr [rv_b]=rv_b [rv_c]=rv_c [rv_d]=rv_d)
SRC[rv_flash]=rv_flash
TOP[rv_flash]=rv_flash
PFX[rv_flash]=pr
fail=0
for d in $DESIGNS; do
  B=build/openxc7/${SRC[$d]}
  out=build/partials/$d
  rm -rf "$out"; mkdir -p "$out"
  builds=()
  for x in $B/${PFX[$d]}_*_c; do
    [[ "$(basename "$x")" =~ ^${PFX[$d]}_[^_]+_c$ ]] && builds+=("$x")
  done
  for t in "${builds[@]}"; do
    rm_name=$(basename "$t" | sed -E "s/^${PFX[$d]}_(.*)_c$/\1/")
    for s in "${builds[@]}"; do
      [ "$s" = "$t" ] && continue
      base_name=$(basename "$s" | sed -E "s/^${PFX[$d]}_(.*)_c$/\1/")
      python3 flow/partial.py "$t/${TOP[$d]}.bit" "$out/rm_${rm_name}_from_${base_name}" --design "${TOP[$d]}" --region "$(cat build/pr/$d/region.txt)" \
        --fasm "$t/${TOP[$d]}.fasm" --static-pips "build/pr/$d/static.prerouted" --base "$s/${TOP[$d]}.bit" --simulate \
        > "$out/rm_${rm_name}_from_${base_name}.log" 2>&1 && echo "OK   $d rm_${rm_name} (simulated from ${base_name})" \
        || { echo "FAIL $d rm_${rm_name} from ${base_name} ($out/rm_${rm_name}_from_${base_name}.log)"; fail=1; }
    done
  done
done
exit $fail
