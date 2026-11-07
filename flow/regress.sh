#!/usr/bin/env bash
DESIGNS="${DESIGNS:-pr_open pr_uart pr_add pr_xor rv_pr rv_b rv_c rv_flash}"
DRY_RUN="${DRY_RUN:-1}"
cd "$(dirname "$0")/.."
declare -A SRC=([pr_open]=pr_open [pr_uart]=pr_uart [pr_add]=pr_open [pr_xor]=pr_open [rv_pr]=rv_soc [rv_b]=rv_soc [rv_c]=rv_soc [rv_d]=rv_soc [rv_flash]=rv_flash)
declare -A TOP=([pr_open]=top [pr_uart]=top [pr_add]=top [pr_xor]=top [rv_pr]=rv_soc [rv_b]=rv_soc [rv_c]=rv_soc [rv_d]=rv_soc [rv_flash]=rv_flash)
declare -A PFX=([pr_open]=pr [pr_uart]=pr [pr_add]=pr_add [pr_xor]=pr_xor [rv_pr]=rv_pr [rv_b]=rv_b [rv_c]=rv_c [rv_d]=rv_d [rv_flash]=pr)
fail=0
for d in $DESIGNS; do
  if [ "$DRY_RUN" = 1 ]; then echo "[dry] rebuild $d from scratch (DRY_RUN=0 to run)"; continue; fi
  rm -rf "build/pr/$d" build/openxc7/${SRC[$d]}/${PFX[$d]}_*
  python3 flow/build_pr.py --design "$d" --run > "build/regress_$d.log" 2>&1 || { echo "FAIL build $d (build/regress_$d.log)"; fail=1; continue; }
  bits=(build/openxc7/${SRC[$d]}/${PFX[$d]}_*_c/${TOP[$d]}.bit)
  first="${bits[0]}"
  for b in "${bits[@]:1}"; do
    if python3 flow/pr_check.py "$first" "$b" --region "$(cat build/pr/$d/region.txt)" > /dev/null; then echo "PASS $d: $(basename $(dirname $first)) vs $(basename $(dirname $b))"
    else echo "FAIL $d: $(basename $(dirname $first)) vs $(basename $(dirname $b))"; fail=1; fi
  done
done
exit $fail
