#!/usr/bin/env bash
DESIGNS="${DESIGNS:-pr_uart rv_pr rv_b rv_c rv_flash}"
BM="${BM:-toolchain/byteman-build/byteman}"
OUT="${OUT:-build/byteman_check}"
cd "$(dirname "$0")/.."
declare -A SRC=([pr_open]=pr_open [pr_uart]=pr_uart [rv_pr]=rv_soc [rv_b]=rv_soc [rv_c]=rv_soc [rv_d]=rv_soc [rv_flash]=rv_flash)
declare -A TOP=([pr_open]=top [pr_uart]=top [rv_pr]=rv_soc [rv_b]=rv_soc [rv_c]=rv_soc [rv_d]=rv_soc [rv_flash]=rv_flash)
declare -A PFX=([pr_open]=pr [pr_uart]=pr [rv_pr]=rv_pr [rv_b]=rv_b [rv_c]=rv_c [rv_d]=rv_d [rv_flash]=pr)
mkdir -p "$OUT"
fail=0
cmp_frames() {
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
    print(f"filled frame differs between base and target")
    sys.exit(1)
a = {**{k: base[k] for k in fill}, **a}
k = set(a) | set(t)
d = sum(bitparse.without_ecc(a.get(x, z)) != bitparse.without_ecc(t.get(x, z)) for x in k)
print(f"{len(k)} frames vs original target ({len(fill)} not written by byteman, kept from base), {d} differ")
sys.exit(1 if d else 0)
PY
}
for d in $DESIGNS; do
  B=build/openxc7/${SRC[$d]}
  for pb in build/partials/$d/rm_*_from_*.bit; do
    [ -e "$pb" ] || continue
    n=$(basename "$pb" .bit)
    t=$(echo "$n" | sed -E 's/^rm_(.*)_from_(.*)$/\1/')
    s=$(echo "$n" | sed -E 's/^rm_(.*)_from_(.*)$/\2/')
    "$BM" XS7 -w -i main "$B/${PFX[$d]}_${s}_c/${TOP[$d]}.bit" -i main "$pb" -o full "$OUT/${d}_${n}.bit" > /dev/null 2>&1
    if r=$(cmp_frames "$OUT/${d}_${n}.bit" "$B/${PFX[$d]}_${t}_c/${TOP[$d]}.bit" "$B/${PFX[$d]}_${s}_c/${TOP[$d]}.bit"); then echo "PASS $d $n (byteman: $r)"
    else echo "FAIL $d $n (byteman: $r)"; fail=1; fi
  done
done
exit $fail
