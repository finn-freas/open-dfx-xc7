cd ~/open-dfx-xc7
F=build/patched/fresh
mkdir -p $F
run() { d=$1; shift; echo "== build $d $(date +%T)"; python3 flow/build_pr_native.py --design $d --out $F/$d "$@" --run > $F/$d.log 2>&1; echo "   rc=$? $(date +%T)"; }
run rv_pr --rms xor andn add rot popc minmax --timing-allow-fail popc minmax
run rv_b
run rv_c
run rv2
run rv_m
echo "== compare"
for d in rv_pr rv_b rv_c rv2 rv_m; do
  old=$(python3 -c "import sys; sys.path.insert(0,'flow'); import build_pr_native as b; print(b.CONFIG['designs']['$d'].get('out', b.CONFIG['out']))")
  for nb in $(find $F/$d -name '*.bit' -not -name '*icapbits*'); do
    rel=${nb#$F/$d/}
    ob=$old/$rel
    [ -e "$ob" ] || { echo "NEW-ONLY $d/$rel"; continue; }
    r=$(python3 - "$nb" "$ob" <<'PY'
import sys
sys.path.insert(0, "flow")
import bitparse
p = bitparse.Part()
a = bitparse.parse(sys.argv[1], p)["frames"]; b = bitparse.parse(sys.argv[2], p)["frames"]
z = [0] * 101
print(sum(a.get(k, z) != b.get(k, z) for k in set(a) | set(b)))
PY
)
    [ "$r" = 0 ] && echo "SAME $d/$rel" || echo "DIFF $d/$rel ($r frames)"
  done
done
