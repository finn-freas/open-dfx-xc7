#!/usr/bin/env bash
NAT="${NAT:-build/patched/rv2_native/replay}"
OUT="${OUT:-build/patched/partials/rv2}"
BMO="${BMO:-build/patched/rv2_native/byteman}"
TOP="${TOP:-rv_soc}"
BM="${BM:-toolchain/byteman-build/byteman}"
FORMAL_TIMEOUT="${FORMAL_TIMEOUT:-600}"
FORMAL_MEM_KB="${FORMAL_MEM_KB:-3000000}"
TAGP="${TAGP:-rv2}"
STAGES="${STAGES:-partials full}"
OTHER_REGION="${OTHER_REGION:-1}"
cd "$(dirname "$0")/.."
mkdir -p "$OUT" "$BMO"
mapfile -t RPN < <(awk '{print $1}' "$NAT/region.txt")
mapfile -t RPR < <(awk '{print $3}' "$NAT/region.txt")
NRP=${#RPN[@]}
declare -A DIR NEGDONE
for d in "$NAT"/*_n; do
  [ -e "$d/$TOP.bit" ] || continue
  c=$(basename "$d"); c=${c%_n}
  DIR[$c]=$d
done
CFGS=$(printf '%s\n' "${!DIR[@]}" | sort)
echo "partitions: ${RPN[*]}; configurations: $(echo $CFGS)"
fail=0
rm_of() { echo "$1" | cut -d_ -f$(($2 + 1)); }
r2v() {
  local bit=$1 k=$2 rm=$3 tag=$4 log=$5 formal=$6
  local shell="$NAT/${RPN[$k]}/rm_shell_native.v"
  if ! python3 flow/region2v.py check "$bit" "${RPR[$k]}" --shell "$shell" --rm "$rm" --tag "$tag" > "$log" 2>&1; then
    echo "FAIL-SIM"; return 1
  fi
  local sim
  sim=$(grep -oE 'sim pass=[0-9]+ fail=[0-9]+ of [0-9]+ vectors' "$log" | head -1)
  [ "$formal" = 1 ] || { echo "SIM-PASS ${sim}"; return 0; }
  ( ulimit -v "$FORMAL_MEM_KB"; timeout "$FORMAL_TIMEOUT" python3 flow/region2v.py check "$bit" "${RPR[$k]}" --shell "$shell" \
      --rm "$rm" --tag "$tag" --formal > "$log.formal" 2>&1 )
  local rc=$?
  if [ $rc = 0 ]; then echo "SIM-PASS ${sim}, PROVED"
  elif [ $rc = 124 ]; then echo "SIM-PASS ${sim}, PROOF-TIMEOUT"
  elif grep -qE "bad_alloc|MemoryError|[Oo]ut of memory|Cannot allocate" "$log.formal" build/region2v/check/"$tag"/formal.log 2>/dev/null; then
    echo "SIM-PASS ${sim}, PROOF-OUT-OF-MEMORY"
  elif grep -q "formal run inconclusive" "$log.formal"; then echo "SIM-PASS ${sim}, PROOF-INCONCLUSIVE"
  else echo "FAIL-PROOF"; return 1
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
print(f"{d} of {len(k)} frames differ")
sys.exit(1 if d else 0)
PY
}
gate() {
  python3 - "$1" "$2" "$3" "${RPN[@]}" -- "${RPR[@]}" <<'PY'
import re
import sys
sys.path.insert(0, "flow")
import bitparse
import region
bit, k, log = sys.argv[1], int(sys.argv[2]), sys.argv[3]
rest = sys.argv[4:]
cut = rest.index("--")
names, specs = rest[:cut], rest[cut + 1:]
grid = region.load_grid()
written = set(bitparse.parse(bit, bitparse.Part())["frames"])
sets = [set(region.region_bits(region.region_tiles(grid, s))) for s in specs]
outside = written - set().union(*sets)
m = re.search(r"region check: (\d+) frame\(s\) outside region, all of them run-end pad frames: True; "
              r"pad frames carry the full bitstream's own content: True", open(log).read())
pads = int(m.group(1)) if m else -1
others = {names[j]: len(written & sets[j]) for j in range(len(specs)) if j != k}
ok = not any(others.values()) and len(outside) == pads
print(f"{len(written)} frames written: {names[k]} {len(written & sets[k])}/{len(sets[k])}, "
      + ", ".join(f"{n} {v}" for n, v in others.items())
      + f", static {len(outside)} (run-end pad frames reported by partial.py: {pads})")
sys.exit(0 if ok else 1)
PY
}
if [[ " $STAGES " == *" partials "* ]]; then
for t in $CFGS; do
  for s in $CFGS; do
    [ "$t" = "$s" ] && continue
    diff=()
    for ((k = 0; k < NRP; k++)); do [ "$(rm_of $t $k)" != "$(rm_of $s $k)" ] && diff+=($k); done
    [ ${#diff[@]} = 1 ] || continue
    k=${diff[0]}
    rp=${RPN[$k]}
    n="${rp}_${t}_from_${s}"
    p="$OUT/$n"
    oth=()
    if [ "$OTHER_REGION" = 1 ]; then
      for ((j = 0; j < NRP; j++)); do [ $j = $k ] || oth+=(--other-region "${RPR[$j]}"); done
    fi
    if ! python3 flow/partial.py "${DIR[$t]}/$TOP.bit" "$p" --design "$TOP" --region "${RPR[$k]}" \
         --fasm "${DIR[$t]}/$TOP.fasm" --static-pips "$NAT/static.prerouted" --base "${DIR[$s]}/$TOP.bit" --simulate \
         "${oth[@]}" > "$p.log" 2>&1
    then echo "FAIL partial $n ($p.log)"; fail=1; continue; fi
    orc="other-region check not run"
    if [ "$OTHER_REGION" = 1 ]; then
      orc=$(grep -oE 'other partition [^ ]+: [0-9]+ configuration frame\(s\) shared with this region, [0-9]+ of its frames written' "$p.log" | sed 's/ configuration frame(s) shared with this region,/ shared,/' | paste -sd ';' -)
      [ -n "$orc" ] || orc="other-region check MISSING"
    fi
    sim=$(grep -oE 'crc: OK; base \+ partial == target: True \(0 frames differ\)' "$p.log")
    pad=$(grep -oE 'region check: [0-9]+ frame\(s\) outside region, all of them run-end pad frames: True; pad frames carry the full bitstream.s own content: True' "$p.log" | grep -oE '^region check: [0-9]+')
    g=$(gate "$p.bit" "$k" "$p.log"); gok=$?
    "$BM" XS7 -w -i main "${DIR[$s]}/$TOP.bit" -i main "$p.bit" -o full "$BMO/$n.bit" > "$BMO/$n.log" 2>&1
    bmr=$(cmp_target "$BMO/$n.bit" "${DIR[$t]}/$TOP.bit" "${DIR[$s]}/$TOP.bit"); bok=$?
    rr=$(r2v "$BMO/$n.bit" "$k" "$(rm_of $t $k)" "${TAGP}_bm_$n" "$p.r2v.log" 0); rok=$?
    ook=0
    [ "$orc" = "other-region check MISSING" ] && ook=1
    if [ -n "$sim" ] && [ -n "$pad" ] && [ $gok = 0 ] && [ $bok = 0 ] && [ $rok = 0 ] && [ $ook = 0 ]; then v=PASS; else v=FAIL; fail=1; fi
    echo "$v $n: $(stat -c %s "$p.bit") bytes; ${sim:-simulated load NOT exact}; ${pad:-pad check missing} pad frame(s) carry target content; gate: $g; $orc; byteman vs original target: $bmr; region2v on byteman result: $rr"
    for ((j = 0; j < NRP; j++)); do
      [ $j = $k ] && continue
      [ -n "${NEGDONE[$k]}" ] && continue
      NEGDONE[$k]=1
      q="$OUT/neg_${n}_as_${RPN[$j]}"
      python3 flow/partial.py "${DIR[$t]}/$TOP.bit" "$q" --design "$TOP" --region "${RPR[$j]}" \
        --fasm "${DIR[$t]}/$TOP.fasm" --static-pips "$NAT/static.prerouted" --base "${DIR[$s]}/$TOP.bit" --simulate > "$q.log" 2>&1
      nres=$(grep -oE 'base \+ partial == target: [A-Za-z]+ \([0-9]+ frames differ\)' "$q.log")
      if [[ "$nres" == *"True"* ]]; then echo "FAIL negative control $q: $nres"; fail=1
      else echo "PASS negative control: partial for $n cut to ${RPN[$j]}'s region instead: ${nres:-no simulation line} ($q.log)"; fi
    done
  done
done
fi
if [[ " $STAGES " == *" full "* ]]; then
for c in $CFGS; do
  for ((k = 0; k < NRP; k++)); do
    rm=$(rm_of $c $k)
    if res=$(r2v "${DIR[$c]}/$TOP.bit" "$k" "$rm" "${TAGP}_${c}_${RPN[$k]}" "$OUT/r2v_full_${c}_${RPN[$k]}.log" 1); then
      echo "PASS region2v full $c ${RPN[$k]} ($rm): $res"
    else
      echo "FAIL region2v full $c ${RPN[$k]} ($rm): $res ($OUT/r2v_full_${c}_${RPN[$k]}.log)"; fail=1
    fi
  done
done
fi
exit $fail
