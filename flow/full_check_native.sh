#!/usr/bin/env bash
DRY_RUN="${DRY_RUN:-1}"
LOG="${LOG:-build/full_check_native}"
cd "$(dirname "$0")/.."
mkdir -p "$LOG"
M=SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59
steps=(
  "decoupler_prove|flow/decoupler_prove.sh"
  "rtl_rv_flash|bash designs/rv_flash/run_sim.sh"
  "rtl_rv_soc2|bash designs/rv_soc2/run_sim.sh"
  "build_rv_pr|python3 flow/build_pr_native.py --design rv_pr --rms xor andn add rot popc minmax --timing-allow-fail popc minmax --run"
  "build_rv_b|python3 flow/build_pr_native.py --design rv_b --run"
  "build_rv_c|python3 flow/build_pr_native.py --design rv_c --run"
  "build_rv_m|python3 flow/build_pr_native.py --design rv_m --run"
  "build_rv2|python3 flow/build_pr_native.py --design rv2 --run"
  "check_rv_pr|FORMAL_SKIP_RMS=popc FORMAL_MEM_KB=3000000 bash flow/native_check.sh"
  "check_rv_b|NAT=build/patched/rv_b_native/router OUT=build/patched/partials/rv_b_native BMO=build/patched/byteman_check/rv_b_native REGION=SLICE_X12Y0:SLICE_X15Y49 TAGP=native_rv_b FORMAL_MEM_KB=3000000 bash flow/native_check.sh"
  "check_rv_c|NAT=build/patched/rv_c_native/router OUT=build/patched/partials/rv_c_native BMO=build/patched/byteman_check/rv_c_native REGION=SLICE_X12Y75:SLICE_X15Y124 TAGP=native_rv_c FORMAL_MEM_KB=3000000 bash flow/native_check.sh"
  "check_rv_m|NAT=build/patched/rv_m_native/replay OUT=build/patched/partials/rv_m_native BMO=build/patched/byteman_check/rv_m_native REGION=$M TAGP=native_rv_m FORMAL_TIMEOUT=300 FORMAL_MEM_KB=3000000 BRAM_RMS='tbl tbl2' R2V_ARGS='--sweep 1024' FORMAL_SKIP_RMS='tbl tbl2' bash flow/native_check.sh"
  "check_rv2|NAT=build/patched/rv2_native/rtkeep OUT=build/patched/partials/rv2/rtkeep BMO=build/patched/rv2_native/byteman/rtkeep TAGP=rv2rt bash flow/native_check_multi.sh"
)
fail=0
for s in "${steps[@]}"; do
  name=${s%%|*}; cmd=${s#*|}
  if [ "$DRY_RUN" = 1 ]; then echo "[dry] $name: $cmd"; continue; fi
  start=$(date +%s)
  if bash -c "$cmd" > "$LOG/$name.log" 2>&1; then r=PASS; else r=FAIL; fail=1; fi
  echo "$r $name ($(( $(date +%s) - start )) s, $LOG/$name.log): $(grep -c -E '^(PASS|OK|ok|PROVED)' "$LOG/$name.log") pass lines, $(grep -c '^FAIL' "$LOG/$name.log") fail lines"
done
exit $fail
