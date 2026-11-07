#!/usr/bin/env bash
set -e
ref=$1; js=$2; xdc=$3; top=$4; out=$5; shift 5
R=$(cd "$(dirname "$0")/.." && pwd)
export OFX_NEXTPNR_BIN=${OFX_NEXTPNR_BIN:-$R/toolchain/openxc7/bin/nextpnr-xilinx} OFX_MAX_NEXTPNR=${OFX_MAX_NEXTPNR:-2}
mkdir -p $out
sfx=${SFX:-}
for v in "$@"; do
  m=${v:0:1}; n=${v:1:1}
  P=$out/prep_$m$n
  wt=""
  if [ $m = w ]; then wt=--whole-tiles; fi
  if [ $v != full ] && [ ! -f $P/inc.preplaced ]; then
    python3 $R/flow/incremental.py $ref $js $P --top $top --xdc $xdc --ripple $n $wt > $P.log
  fi
  O=$out/$v$sfx; mkdir -p $O
  if [ $v = full ]; then
    opts="--json $js -o xdc=$xdc"
  else
    opts="--json $P/$top.json -o xdc=$P/inc.xdc -o preplaced=$P/inc.preplaced"
    case $v in
      *p) ;;
      *k) opts="$opts -o prerouted=$P/inc.prerouted -o prerouted-strength=weak";;
      *) opts="$opts -o prerouted=$P/inc.prerouted";;
    esac
  fi
  while [ "$(pgrep -c nextpnr)" -ge "$OFX_MAX_NEXTPNR" ]; do sleep 5; done
  load=$(cut -d' ' -f1 /proc/loadavg)
  /usr/bin/time -f "%e %U %M" -o $O/nextpnr.time $R/ofx/npwait.sh --device xc7a35tcsg324-1 --seed 1 --freq 100 \
    --write $O/${top}_routed.json -o fasm=$O/$top.fasm --report $O/report.json $opts > $O/nextpnr.log 2>&1 \
    || echo "$v$sfx FAILED" >> $out/variants.log
  echo "$v$sfx load $load $(tail -1 $O/nextpnr.time) $(grep -o "Max frequency for clock '[^']*': [0-9.]* MHz" $O/nextpnr.log | tail -1) $(grep -o 'Router2 time [0-9.]*' $O/nextpnr.log | tail -1)" >> $out/variants.log
done
cat $out/variants.log
