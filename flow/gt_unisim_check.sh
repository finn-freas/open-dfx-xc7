#!/usr/bin/env bash
set -u
R="$(cd "$(dirname "$0")/.." && pwd)"
NEXTPNR="${NEXTPNR:?draft nextpnr-himbaechel}"
OUT="${OUT:-$R/build/gt_unisim}"
YOSYS="${YOSYS:-$R/toolchain/oss-cad-suite/bin/yosys}"
CHIPDB="${CHIPDB:-$R/toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin}"
DB="${DB:-$R/toolchain/openxc7/share/nextpnr/external/prjxray-db}"
export OFX_NEXTPNR_BIN="$NEXTPNR" OFX_MAX_NEXTPNR="${OFX_MAX_NEXTPNR:-1}"
G="$R/build/ofx/gt"
fail=0
mkdir -p "$OUT"

pnr() {
    local js=$1 xdc=$2 part=$3 o=$4; shift 4
    mkdir -p "$o"
    "$R/ofx/npwait.sh" --device "$part" --json "$js" -o xdc="$xdc" --seed 1 --freq 100 \
        -o fasm="$o/a.fasm" --chipdb "$CHIPDB" "$@" > "$o/nextpnr.log" 2>&1 || { echo "nextpnr failed: $o"; return 1; }
    "$R/toolchain/openxc7/bin/fasm2frames" --part "$part" --db-root "$DB/artix7" "$o/a.fasm" > "$o/a.frames" 2> "$o/frames.log" ||
        { echo "fasm2frames failed: $o"; return 1; }
}

body() { grep -v '^#' "$1" | grep -v '\.SPARE_' | sort; }

for d in pcie_bare gtp_lbm; do
    src="$G/hook_pcie"
    [ "$d" = gtp_lbm ] && src="$G/hook_lbm"
    o="$OUT/$d"; mkdir -p "$o"
    "$YOSYS" -q -p "read_verilog -sv $src/src/$d.v; synth_xilinx -flatten -abc9 -arch xc7 -top $d; write_json $o/unfilled.json" > "$o/yosys.log" 2>&1 || { echo "yosys failed $d"; fail=1; continue; }
    cp "$o/unfilled.json" "$o/filled.json"
    python3 "$R/flow/gt_json_defaults.py" "$o/filled.json"
    xdc="$src/build/stage/$d.xdc"
    pnr "$o/filled.json" "$xdc" xc7a35tcpg236-1 "$o/A" || { fail=1; continue; }
    pnr "$o/unfilled.json" "$xdc" xc7a35tcpg236-1 "$o/B" -o gt-unisim-defaults || { fail=1; continue; }
    spare=$(grep -c '\.SPARE_' "$o/B/a.fasm")
    spare1=$(grep '\.SPARE_' "$o/B/a.fasm" | grep -c "'b[01]*1")
    if cmp -s <(body "$o/A/a.fasm") <(body "$o/B/a.fasm") && cmp -s "$o/A/a.frames" "$o/B/a.frames"; then
        echo "PASS $d: draft (-o gt-unisim-defaults, unfilled netlist) = flow workaround (gt_json_defaults): FASM same apart from $spare SPARE_* lines ($spare1 non-zero), .frames identical"
    else
        echo "FAIL $d: draft differs from the flow workaround ($(diff <(body "$o/A/a.fasm") <(body "$o/B/a.fasm") | grep -c '^[<>]') FASM lines)"
        fail=1
    fi
    if pnr "$o/unfilled.json" "$xdc" xc7a35tcpg236-1 "$o/C" > /dev/null; then
        echo "INFO $d: unfilled netlist without the option (writer defaults) differs from the workaround in $(diff <(body "$o/A/a.fasm") <(body "$o/C/a.fasm") | grep -c '^[<>]') FASM lines"
    else
        echo "INFO $d: unfilled netlist without the option (writer defaults) does not build: $(grep -m1 ERROR "$o/C/nextpnr.log")"
    fi
done

o="$OUT/blinky"
pnr "$R/build/patched/baseline/blinky_stock/blinky.json" "$R/designs/blinky/arty_a7_35t.xdc" xc7a35tcsg324-1 "$o/off" &&
pnr "$R/build/patched/baseline/blinky_stock/blinky.json" "$R/designs/blinky/arty_a7_35t.xdc" xc7a35tcsg324-1 "$o/on" -o gt-unisim-defaults &&
if cmp -s <(grep -v '^#' "$o/off/a.fasm") <(grep -v '^#' "$o/on/a.fasm"); then
    echo "PASS blinky: FASM identical with and without -o gt-unisim-defaults"
else
    echo "FAIL blinky: the option changes a design without GT/PCIe cells"; fail=1
fi
exit $fail
