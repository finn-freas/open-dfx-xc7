#!/usr/bin/env bash
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
YOSYS=$ROOT/toolchain/oss-cad-suite/bin/yosys
name=$1; top=$2; flist=$3; shift 3
out=$ROOT/build/svcores/$name; mkdir -p "$out"
files=$(grep -v '^\s*$' "$flist" | tr '\n' ' ')
inc=""; sinc=""
for d in "$@"; do inc="$inc -I$d"; sinc="$sinc -I $d"; done
SYN="synth_xilinx -flatten -abc9 -arch xc7 -noiopad -top $top; stat"
echo "== builtin"
/usr/bin/time -f "%e s %M KB" "$YOSYS" -q -l "$out/builtin.log" -p "read_verilog -sv -DSYNTHESIS $inc $files; $SYN" > /dev/null 2> "$out/builtin.time"
echo "rc=$? $(tail -1 "$out/builtin.time")"; grep -m1 "ERROR" "$out/builtin.log"
echo "== slang"
/usr/bin/time -f "%e s %M KB" "$YOSYS" -q -l "$out/slang.log" -p "plugin -i slang; read_slang -DSYNTHESIS --top $top $sinc $files; $SYN" > /dev/null 2> "$out/slang.time"
echo "rc=$? $(tail -1 "$out/slang.time")"; grep -m1 "ERROR" "$out/slang.log"
for fe in builtin slang; do
  echo "-- $fe cells"
  awk '/Printing statistics/{n=0} {buf[n++]=$0} END{for(i=0;i<n;i++) print buf[i]}' "$out/$fe.log" | grep -E "^\s+[0-9]+ +(LUT|FD|CARRY|RAM|DSP|MUXF|SRL)" | awk '{printf "%s=%s ", $2, $1} END {print ""}'
done
