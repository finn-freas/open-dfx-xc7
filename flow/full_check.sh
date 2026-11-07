#!/usr/bin/env bash
DRY_RUN="${DRY_RUN:-1}"
LOG="${LOG:-build/full_check}"
cd "$(dirname "$0")/.."
mkdir -p "$LOG"
steps=(
  "regress|DRY_RUN=0 flow/regress.sh"
  "partials|DESIGNS='pr_uart rv_pr rv_b rv_c rv_flash' flow/make_partials.sh"
  "byteman|DESIGNS='pr_uart rv_pr rv_b rv_c rv_flash' flow/byteman_check.sh"
  "icapbits|flow/icap_variant.sh"
  "gl_sim|JOBS=2 bash flow/gl_sim.sh"
  "region2v|CORRUPT='rv_pr:xor rv_b:add rv_c:xor rv_flash:andn' bash flow/region2v_check.sh"
)
fail=0
for s in "${steps[@]}"; do
  name=${s%%|*}; cmd=${s#*|}
  if [ "$DRY_RUN" = 1 ]; then echo "[dry] $name: $cmd"; continue; fi
  start=$(date +%s)
  if bash -c "$cmd" > "$LOG/$name.log" 2>&1; then r=PASS; else r=FAIL; fail=1; fi
  echo "$r $name ($(( $(date +%s) - start )) s, $LOG/$name.log): $(grep -c '^PASS\|^OK' "$LOG/$name.log") pass lines, $(grep -c '^FAIL' "$LOG/$name.log") fail lines"
done
exit $fail
