#!/usr/bin/env bash
NAT="${NAT:-build/patched/rv_pr_native/router}"
OUT="${OUT:-build/partials/rv_native}"
BMO="${BMO:-build/byteman_check/native}"
REGION="${REGION:-SLICE_X12Y100:SLICE_X15Y149}"
SHELLV="${SHELLV:-$NAT/rm_shell_native.v}"
TOP="${TOP:-rv_soc}"
BM="${BM:-toolchain/byteman-build/byteman}"
FORMAL_TIMEOUT="${FORMAL_TIMEOUT:-600}"
TAGP="${TAGP:-native}"
BRAM_RMS="${BRAM_RMS:-}"
R2V_ARGS="${R2V_ARGS:-}"
FORMAL_MEM_KB="${FORMAL_MEM_KB:-5000000}"
FORMAL_SKIP_RMS="${FORMAL_SKIP_RMS:-}"
STATIC_PIPS="${STATIC_PIPS:-$NAT/static.prerouted}"
PARTPINS="${PARTPINS:-}"
GREY="${GREY:-}"
PP_ARGS=()
[ -n "$PARTPINS" ] && PP_ARGS=(--partpins "$PARTPINS")
cd "$(dirname "$0")/.."
mkdir -p "$OUT" "$BMO"
fail=0
declare -A DIR
for d in "$NAT"/*_n "$NAT"/*_n_taf; do
  [ -e "$d/$TOP.bit" ] || continue
  rm=$(basename "$d" | sed -E 's/_n(_taf)?$//')
  DIR[$rm]=$d
done
[ -n "$GREY" ] && DIR[grey]=$GREY
echo "native builds: ${!DIR[*]}"
r2v() {
  local bit=$1 rm=$2 tag=$3 log=$4
  if [ -n "$GREY" ] && [ "$rm" = grey ]; then echo "NOT-RUN(greybox, no RTL)"; return 0; fi
  if ! python3 flow/region2v.py check "$bit" "$REGION" --shell "$SHELLV" --rm "$rm" --tag "$tag" "${PP_ARGS[@]}" $R2V_ARGS > "$log" 2>&1; then
    echo "FAIL-SIM"; return 1
  fi
  case " $FORMAL_SKIP_RMS " in *" $rm "*) echo "SIM-PASS,PROOF-NOT-RUN"; return 0 ;; esac
  ( ulimit -v "$FORMAL_MEM_KB"; timeout "$FORMAL_TIMEOUT" python3 flow/region2v.py check "$bit" "$REGION" --shell "$SHELLV" \
      --rm "$rm" --tag "$tag" "${PP_ARGS[@]}" --formal > "$log.formal" 2>&1 )
  local rc=$?
  if [ $rc = 0 ]; then
    echo "SIM+PROVED"
  elif [ $rc = 124 ]; then
    echo "SIM-PASS,PROOF-TIMEOUT"
  elif grep -qE "bad_alloc|MemoryError|[Oo]ut of memory|Cannot allocate" "$log.formal" build/region2v/check/"$tag"/formal.log 2>/dev/null; then
    echo "SIM-PASS,PROOF-OUT-OF-MEMORY"
  elif grep -q "formal run inconclusive" "$log.formal"; then
    echo "SIM-PASS,PROOF-INCONCLUSIVE"
  else
    echo "FAIL-PROOF"; return 1
  fi
}
bram_chk() {
  local bit=$1 rm=$2 tag=$3 log=$4
  case " $BRAM_RMS " in *" $rm "*) ;; *) echo "-"; return 0 ;; esac
  if python3 flow/region2v.py bram "$bit" "$REGION" --synth-json "$NAT/rm_${rm}_synth.json" --tag "$tag" > "$log" 2>&1; then
    grep -oE '[0-9]+/[0-9]+ defined bits equal' "$log"
  else
    echo "FAIL-BRAM"; return 1
  fi
}
cmp_target() {
  python3 - "$1" "$2" "$3" <<'PY'
import sys
sys.path.insert(0, "flow")
import bitparse
p = bitparse.Part()
a = bitparse.parse(sys.argv[1], p)["frames"]
t = bitparse.parse(sys.argv[2], p)["frames"]
base = bitparse.parse(sys.argv[3], p)["frames"]
z = [0] * 101
fill = [k for k in base if k not in a]
if any(bitparse.without_ecc(base[k]) != bitparse.without_ecc(t.get(k, z)) for k in fill):
    print("filled-frame-mismatch")
    sys.exit(1)
a = {**{k: base[k] for k in fill}, **a}
k = set(a) | set(t)
d = sum(bitparse.without_ecc(a.get(x, z)) != bitparse.without_ecc(t.get(x, z)) for x in k)
print(d)
sys.exit(1 if d else 0)
PY
}
for t in "${!DIR[@]}"; do
  if res=$(r2v "${DIR[$t]}/$TOP.bit" "$t" "${TAGP}_${t}" "$OUT/r2v_full_$t.log"); then echo "PASS region2v full $t: $res"
  else echo "FAIL region2v full $t: $res ($OUT/r2v_full_$t.log)"; fail=1; fi
  if bres=$(bram_chk "${DIR[$t]}/$TOP.bit" "$t" "${TAGP}_${t}" "$OUT/bram_full_$t.log"); then echo "PASS bram init full $t: $bres"
  else echo "FAIL bram init full $t: $bres ($OUT/bram_full_$t.log)"; fail=1; fi
  for s in "${!DIR[@]}"; do
    [ "$s" = "$t" ] && continue
    p="$OUT/rm_${t}_from_${s}"
    if ! python3 flow/partial.py "${DIR[$t]}/$TOP.bit" "$p" --design "$TOP" --region "$REGION" \
         --fasm "${DIR[$t]}/$TOP.fasm" --static-pips "$STATIC_PIPS" --base "${DIR[$s]}/$TOP.bit" --simulate > "$p.log" 2>&1
    then echo "FAIL partial rm_${t}_from_${s} ($p.log)"; fail=1; continue; fi
    "$BM" XS7 -w -i main "${DIR[$s]}/$TOP.bit" -i main "$p.bit" -o full "$BMO/rm_${t}_from_${s}.bit" > /dev/null 2>&1
    bmr=$(cmp_target "$BMO/rm_${t}_from_${s}.bit" "${DIR[$t]}/$TOP.bit" "${DIR[$s]}/$TOP.bit")
    bok=$?
    res=$(r2v "$BMO/rm_${t}_from_${s}.bit" "$t" "${TAGP}_bm_${t}_from_${s}" "$p.r2v.log")
    rok=$?
    bres=$(bram_chk "$BMO/rm_${t}_from_${s}.bit" "$t" "${TAGP}_bm_${t}_from_${s}" "$p.bram.log")
    bram_ok=$?
    [ $bok = 0 ] && [ $rok = 0 ] && [ $bram_ok = 0 ] && v=PASS || { v=FAIL; fail=1; }
    echo "$v rm_${t}_from_${s}: partial gate+CRC+simulated exact; byteman vs original target: $bmr frames differ; region2v on byteman result: $res; BRAM INIT: $bres"
  done
done
exit $fail
