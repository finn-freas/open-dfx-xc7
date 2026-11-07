#!/usr/bin/env bash
set -e
ref=$1; js=$2; xdc=$3; top=$4; out=$5; rep=${6:-1}
R=$(cd "$(dirname "$0")/.." && pwd)
export OFX_NEXTPNR_BIN=${OFX_NEXTPNR_BIN:-$R/toolchain/openxc7/bin/nextpnr-xilinx} OFX_MAX_NEXTPNR=${OFX_MAX_NEXTPNR:-2}
DB=$R/toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7
mkdir -p $out
P=$out/prep
/usr/bin/time -f "%e %U" -o $out/match.time python3 $R/flow/incremental.py $ref $js $P --top $top --xdc $xdc
run() {
  local name=$1; shift
  local O=$out/$name.r$rep
  mkdir -p $O
  while [ "$(pgrep -c nextpnr)" -ge "$OFX_MAX_NEXTPNR" ]; do sleep 10; done
  echo "$name r$rep start $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg) nextpnr $(pgrep -c nextpnr)" >> $out/bench.log
  /usr/bin/time -f "%e %U %M" -o $O/nextpnr.time $R/ofx/npwait.sh --device xc7a35tcsg324-1 --seed 1 --freq 100 \
    --write $O/${top}_routed.json -o fasm=$O/$top.fasm --report $O/report.json "$@" > $O/nextpnr.log 2>&1 || echo "$name FAILED" >> $out/bench.log
  if [ -f $O/$top.fasm ]; then
    $R/toolchain/openxc7/bin/fasm2frames --part xc7a35tcsg324-1 --db-root $DB $O/$top.fasm > $O/$top.frames
    $R/toolchain/openxc7/bin/xc7frames2bit --part_file=$DB/xc7a35tcsg324-1/part.yaml --part_name=xc7a35tcsg324-1 \
      --frm_file=$O/$top.frames --output_file=$O/$top.bit > /dev/null
  fi
  echo "$name r$rep end $(date +%T) $(cat $O/nextpnr.time) $(grep -o "Max frequency for clock '[^']*': [0-9.]* MHz" $O/nextpnr.log | tail -1)" >> $out/bench.log
}
run full --json $js -o xdc=$xdc
run inc --json $P/$top.json -o xdc=$P/inc.xdc -o preplaced=$P/inc.preplaced -o prerouted=$P/inc.prerouted
tail -4 $out/bench.log
