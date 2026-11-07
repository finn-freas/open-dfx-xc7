#!/usr/bin/env bash
BUILDS="${BUILDS:-build/openxc7/pr_uart/pr_count_c build/openxc7/pr_uart/pr_shift_c build/openxc7/rv_soc/rv_pr_xor_c build/openxc7/rv_soc/rv_pr_andn_c build/openxc7/rv_soc/rv_pr_add_c build/openxc7/rv_flash/pr_xor_c build/openxc7/rv_flash/pr_andn_c build/openxc7/rv_flash/pr_add_c}"
PART="${PART:-${OFX_PART:-xc7a35tcsg324-1}}"
cd "$(dirname "$0")/.."
DB=$(python3 -c "import sys; sys.path.insert(0, 'flow'); import bitparse; print(bitparse.DB)")
F2B=toolchain/openxc7/bin/xc7frames2bit
fail=0
for b in $BUILDS; do
  fr=$(ls "$b"/*.frames 2>/dev/null | grep -v _icapbits | head -1)
  [ -n "$fr" ] || { echo "SKIP $b (no .frames)"; continue; }
  top=$(basename "$fr" .frames)
  rm -f "$b/${top}_icapbits.frames"
  python3 flow/set_bits.py "$fr" "$b/${top}_icapbits.frames" > /dev/null
  "$F2B" --part_file="$DB/$PART/part.yaml" --part_name="$PART" --frm_file="$b/${top}_icapbits.frames" \
         --output_file="$b/${top}_icapbits.bit" > "$b/${top}_icapbits.log" 2>&1 || { echo "FAIL $b xc7frames2bit"; fail=1; continue; }
  r=$(python3 - "$b/$top.bit" "$b/${top}_icapbits.bit" <<'PY'
import sys
sys.path.insert(0, "flow")
import bitparse
p = bitparse.Part()
a = bitparse.parse(sys.argv[1], p)["frames"]
b = bitparse.parse(sys.argv[2], p)["frames"]
z = [0] * 101
diff = []
for k in sorted(set(a) | set(b)):
    x, y = bitparse.without_ecc(a.get(k, z)), bitparse.without_ecc(b.get(k, z))
    for w in range(101):
        d = x[w] ^ y[w]
        for i in range(32):
            if d >> i & 1:
                diff.append(f"{k:08x}_{w}_{i}")
want = {"0040091a_68_30", "0040091a_68_31", "0040091b_68_29"}
print(" ".join(diff))
sys.exit(0 if set(diff) == want else 1)
PY
)
  if [ $? = 0 ]; then echo "OK   $b/${top}_icapbits.bit differs from $top.bit in exactly: $r"
  else echo "FAIL $b: differences: $r"; fail=1; fi
done
exit $fail
