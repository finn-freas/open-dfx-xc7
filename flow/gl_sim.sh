#!/usr/bin/env bash
NETDIR="${NETDIR:-build/pr/rv_pr}"
OUT="${OUT:-build/glsim}"
RMS="${RMS:-}"
JOBS="${JOBS:-4}"
TB=designs/rv_soc/tb/gl_tb_rv_soc.v
PRIMS=(designs/rv_soc/tb/gl_ramb36e1.v designs/rv_soc/tb/icape2_model.v)
RTL_DIR=designs/rv_soc/pr
FW_HEX=designs/rv_soc/fw/main.hex
TOOLS=toolchain/oss-cad-suite
VECTORS=(
  "12345678 0F0F0F0F"
  "00000000 00000000"
  "FFFFFFFF FFFFFFFF"
  "FFFFFFFF 00000000"
  "00000000 FFFFFFFF"
  "80000000 80000000"
  "80000000 FFFFFFFF"
  "7FFFFFFF 80000000"
  "FFFFFFFF 00000001"
  "A5A5A5A5 0000001F"
  "00000001 00000021"
)
declare -A REF=(
  [xor]='a ^ b'
  [andn]='f[0] ? (a | ~b) : (a & ~b)'
  [add]='a + b'
  [grey]="32'd0"
  [rot]='rotl32(a, f[0] ? 32 - b[4:0] : b[4:0])'
  [popc]='f[0] ? clz32(a) : popc32(a)'
  [minmax]='((a < b) ^ f[0]) ? a : b'
)

cd "$(dirname "$0")/.."
export PATH=$PWD/$TOOLS/bin:$PATH
CELLS_SIM=$(yosys-config --datdir 2>/dev/null)/xilinx/cells_sim.v
[ -f "$CELLS_SIM" ] || CELLS_SIM=$TOOLS/share/yosys/xilinx/cells_sim.v
[ -f "$CELLS_SIM" ] || { echo "FAIL no cells_sim.v ($CELLS_SIM)"; exit 2; }
stale() {
  local t=$1; shift
  [ -f "$t" ] || return 0
  for s in "$@"; do [ "$s" -nt "$t" ] && return 0; done
  return 1
}

mkdir -p "$OUT"
SIM_LIB=$OUT/cells_sim_glsim.v
if stale "$SIM_LIB" "$CELLS_SIM" "${PRIMS[@]}"; then
  over=$(sed -nE 's/^module ([A-Za-z0-9_]+).*/\1/p' "${PRIMS[@]}" | paste -sd'|')
  awk -v re="^module ($over)[ (#]" '$0 ~ re {skip=1} !skip {print} skip && /^endmodule/ {skip=0}' "$CELLS_SIM" > "$SIM_LIB"
fi

: > "$OUT/vec_a.hex"; : > "$OUT/vec_b.hex"
for v in "${VECTORS[@]}"; do
  set -- $v
  echo "$1" >> "$OUT/vec_a.hex"; echo "$2" >> "$OUT/vec_b.hex"
done
NV=${#VECTORS[@]}

bram_check() {
  python3 - "$1" "$FW_HEX" <<'EOF'
import re, sys
src = open(sys.argv[1]).read()
words = [int(l.split()[0], 16) for l in open(sys.argv[2]) if l.strip()]
insts = re.findall(r'RAMB36E1\s*#\((.*?)\)\s*(\S+)\s*\(', src, re.S)
if len(insts) != 2:
    print("FAIL bram: expected 2 RAMB36E1 instances, found %d" % len(insts)); sys.exit(1)
halves = {}
for params, name in insts:
    p = dict(re.findall(r'\.(INIT_[0-9A-F]{2})\(256\'h([0-9a-fA-Fx]+)\)', params))
    if len(p) != 128:
        print("FAIL bram %s: %d INIT_xx parameters, expected 128" % (name, len(p))); sys.exit(1)
    if any('x' in v.lower() for v in p.values()):
        print("FAIL bram %s: INIT_xx contains x" % name); sys.exit(1)
    bits = 0
    for i in range(128):
        bits |= int(p["INIT_%02X" % i], 16) << (256 * i)
    halves[name] = [(bits >> (16 * k)) & 0xFFFF for k in range(2048)]
lo = [w & 0xFFFF for w in words] + [0] * (2048 - len(words))
hi = [w >> 16 for w in words] + [0] * (2048 - len(words))
names = sorted(halves)
match = None
for nl in names:
    nh = [n for n in names if n != nl][0]
    if halves[nl] == lo and halves[nh] == hi:
        match = (nl, nh)
if not match:
    for n in names:
        print("FAIL bram %s: lo-half diffs %d, hi-half diffs %d" % (n, sum(x != y for x, y in zip(halves[n], lo)), sum(x != y for x, y in zip(halves[n], hi))))
    sys.exit(1)
nz = sum(1 for w in words if w)
print("ok   bram: %s = low halves, %s = high halves of %s (%d words, %d non-zero) match INIT_00..7F" % (match[0], match[1], sys.argv[2], len(words), nz))
EOF
}

run_rm() {
  local name=$1 json=$2
  local net=$OUT/cfg_${name}.v vvp=$OUT/cfg_${name}.vvp vh=$OUT/cfg_${name}_ref.vh log=$OUT/cfg_${name}.log
  local rtl=$RTL_DIR/rm_core_${name}.v
  {
    if stale "$net.raw" "$json"; then
      yosys -q -p "read_json $json; write_verilog -noattr $net.raw" > "$OUT/cfg_${name}.yosys.log" 2>&1 \
        || { echo "FAIL $name: yosys write_verilog ($OUT/cfg_${name}.yosys.log)"; rm -f "$net.raw"; return 1; }
    fi
    if stale "$net" "$net.raw"; then
      sed "s/\.INIT(1'hx)/.INIT(1'h0)/" "$net.raw" > "$net"
    fi
    echo "ok   ff init: $(grep -c "\.INIT(1'hx)" "$net.raw") FDRE/FDSE with INIT x simulated as 0 (nextpnr-xilinx fasm.cc: zinit = INIT != 1)"
    bram_check "$net" || return 1
    printf '`define REF_EXPR (%s)\n`define VEC_A "%s"\n`define VEC_B "%s"\n' "${REF[$name]}" "$OUT/vec_a.hex" "$OUT/vec_b.hex" > "$vh.new"
    cmp -s "$vh.new" "$vh" && rm -f "$vh.new" || mv "$vh.new" "$vh"
    local srcs=("$vh" "$net" "$SIM_LIB" "${PRIMS[@]}" "$TB") defs=()
    if [ -f "$rtl" ]; then srcs+=("$rtl"); defs+=(-DRTL_REF); fi
    if stale "$vvp" "${srcs[@]}"; then
      rm -f "$vvp.nortl"
      if ! iverilog -g2012 -o "$vvp" -s gl_tb_rv_soc "${defs[@]}" "${srcs[@]}" > "$OUT/cfg_${name}.iverilog.log" 2>&1; then
        if [ -f "$rtl" ]; then
          touch "$vvp.nortl"
          iverilog -g2012 -o "$vvp" -s gl_tb_rv_soc "$vh" "$net" "$SIM_LIB" "${PRIMS[@]}" "$TB" >> "$OUT/cfg_${name}.iverilog.log" 2>&1 \
            || { echo "FAIL $name: iverilog ($OUT/cfg_${name}.iverilog.log)"; rm -f "$vvp"; return 1; }
        else
          echo "FAIL $name: iverilog ($OUT/cfg_${name}.iverilog.log)"; rm -f "$vvp"; return 1
        fi
      fi
    fi
    [ -f "$rtl" ] || echo "note $name: no $rtl, table expression only"
    [ -f "$vvp.nortl" ] && echo "note $name: RTL reference $rtl did not compile, table expression only ($OUT/cfg_${name}.iverilog.log)"
    local t0=$SECONDS
    vvp -n "$vvp" +RM="$name" +NVEC="$NV" > "$log" 2>&1
    grep -E '^(PASS|FAIL) ' "$log"
    grep -q '^DONE ' "$log" || echo "FAIL $name: simulation did not finish ($log)"
    echo "time $name: $((SECONDS - t0)) s simulated $(sed -n 's/^DONE .*time=\([0-9]*\).*/\1/p' "$log") ps"
  } > "$OUT/cfg_${name}.result" 2>&1
}

shopt -s nullglob
jsons=("$NETDIR"/cfg_*_linked.json)
[ ${#jsons[@]} -gt 0 ] || { echo "FAIL no $NETDIR/cfg_*_linked.json"; exit 2; }
names=()
for json in "${jsons[@]}"; do
  rm=$(basename "$json" | sed -E 's/^cfg_(.*)_linked\.json$/\1/')
  if [ -n "$RMS" ] && ! [[ " $RMS " == *" $rm "* ]]; then continue; fi
  if [ -z "${REF[$rm]+x}" ]; then echo "SKIP $rm: no reference expression in REF table"; continue; fi
  while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do wait -n; done
  run_rm "$rm" "$json" &
  names+=("$rm")
done
wait
fail=0
for rm in "${names[@]}"; do
  cat "$OUT/cfg_${rm}.result"
  grep -q '^FAIL' "$OUT/cfg_${rm}.result" && fail=1
  grep -q '^PASS' "$OUT/cfg_${rm}.result" || fail=1
done
exit $fail
