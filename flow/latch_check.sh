#!/usr/bin/env bash
set -u
R="$(cd "$(dirname "$0")/.." && pwd)"
NEXTPNR="${NEXTPNR:?nextpnr-himbaechel with LDCE/LDPE support}"
OUT="${OUT:-$R/build/latch_check}"
VIV="${VIV:-/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/gap}"
T="$R/toolchain/openxc7"
export OFX_NEXTPNR_BIN="$NEXTPNR" OFX_MAX_NEXTPNR="${OFX_MAX_NEXTPNR:-1}"
FEAT='\.(LATCH|CLKINV|NOCLKINV|FFSYNC|[A-D]FF\.ZRST|[A-D]FF\.ZINI|SRUSEDMUX|CEUSEDMUX)$'
mkdir -p "$OUT"
fail=0
slice_cfg() {
    for t in $(grep '\.LATCH$' "$1" | sed 's/\.LATCH$//'); do
        grep -F "$t." "$1" | grep -E "$FEAT" | sed "s/^.*$(basename "$t")\.//" | sort | tr '\n' ' '; echo
    done | sort
}
for d in latch_ldce latch_ldce_ginv latch_ldpe latch_ldpe_ginv; do
    o="$OUT/$d"; mkdir -p "$o"
    "$R/toolchain/oss-cad-suite/bin/yosys" -q -p "read_verilog -sv $R/designs/gap/$d/$d.v; synth_xilinx -flatten -abc9 -arch xc7 -top $d; write_json $o/$d.json" > "$o/yosys.log" 2>&1 ||
        { echo "FAIL $d: yosys"; fail=1; continue; }
    "$R/ofx/npwait.sh" --device xc7a35tcsg324-1 --json "$o/$d.json" -o xdc="$R/designs/gap/$d/arty_a7_35t.xdc" --seed 1 \
        -o fasm="$o/$d.fasm" --chipdb "$T/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin" > "$o/nextpnr.log" 2>&1 ||
        { echo "FAIL $d: nextpnr ($o/nextpnr.log)"; fail=1; continue; }
    if [ ! -f "$VIV/$d/$d.bit" ]; then echo "INFO $d: builds; no Vivado bitstream in $VIV/$d"; continue; fi
    PATH="$T/bin:$PATH" "$T/libexec/tabbypy3" "$R/flow/bit2fasm.py" "$VIV/$d/$d.bit" "$o/$d.vivado.fasm" > "$o/bit2fasm.log" 2>&1 ||
        { echo "FAIL $d: bit2fasm"; fail=1; continue; }
    ours=$(slice_cfg "$o/$d.fasm"); viv=$(slice_cfg "$o/$d.vivado.fasm")
    if [ -n "$ours" ] && [ "$ours" = "$viv" ]; then
        echo "PASS $d: latch slice configuration = Vivado's: $ours"
    else
        echo "FAIL $d: ours [$ours] Vivado [$viv]"; fail=1
    fi
done
exit $fail
