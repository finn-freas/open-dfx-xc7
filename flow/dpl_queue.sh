#!/usr/bin/env bash
cd ~/open-dfx-xc7
WORKERS=${1:-2}
OUT=/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/dpl_xtime
Q=build/qor/dpl/queue
log=build/qor/dpl_queue.log
mkdir -p $Q
NAMES=(
  rv_soc_p5_free rv_soc_p5_dp0_s1_placed bram_p5_free bram_p5_dp0_s1_placed rv_mul_p5_free rv_mul_p5_dp0_s1_placed
  rv_soc_p5_dp0_s1_mix_vpack_nglob rv_soc_p5_dp0_s1_mix_npack_vglob rv_soc_p5_dp0_s1_mix_vpack_vglob
  bram_p5_dp0_s1_mix_vpack_nglob bram_p5_dp0_s1_mix_npack_vglob bram_p5_dp0_s1_mix_vpack_vglob
  rv_mul_p5_dp0_s1_mix_vpack_nglob rv_mul_p5_dp0_s1_mix_npack_vglob rv_mul_p5_dp0_s1_mix_vpack_vglob
  rv_soc_p5_dp1_s1_placed rv_soc_p5_dp2dp_s1_placed bram_p5_dp1_s1_placed bram_p5_dp2dp_s1_placed
  rv_mul_p5_dp1_s1_placed rv_mul_p5_dp2dp_s1_placed
  rv_soc_p5_dp0_s2_placed rv_soc_p5_dp1_s2_placed rv_soc_p5_dp2dp_s2_placed bram_p5_dp0_s2_placed bram_p5_dp1_s2_placed bram_p5_dp2dp_s2_placed
  rv_soc_p5_dp0_s3_placed rv_soc_p5_dp1_s3_placed rv_soc_p5_dp2dp_s3_placed bram_p5_dp0_s3_placed bram_p5_dp1_s3_placed bram_p5_dp2dp_s3_placed
  rv_mul_p5_dp0_s2_placed rv_mul_p5_dp1_s2_placed rv_mul_p5_dp2dp_s2_placed rv_mul_p5_dp0_s3_placed rv_mul_p5_dp1_s3_placed rv_mul_p5_dp2dp_s3_placed
  eth_p10_free eth_p10_dp0_s1_placed eth_p10_dp1_s1_placed eth_p10_dp2dp_s1_placed
  rv_big_p5_free rv_big_p5_dp0_s1_placed rv_big_p5_dp1_s1_placed rv_big_p5_dp2dp_s1_placed
  rv_big_p5_dp0_s2_placed rv_big_p5_dp1_s2_placed rv_big_p5_dp2dp_s2_placed rv_big_p5_dp0_s3_placed rv_big_p5_dp1_s3_placed rv_big_p5_dp2dp_s3_placed
  eth_p10_dp0_s2_placed eth_p10_dp1_s2_placed eth_p10_dp2dp_s2_placed eth_p10_dp0_s3_placed eth_p10_dp1_s3_placed eth_p10_dp2dp_s3_placed
)
printf "%s\n" "${NAMES[@]}" > $Q/names.txt
echo 0 > $Q/next

take() {
  (
    flock 9
    i=$(cat $Q/next)
    echo $((i + 1)) > $Q/next
    sed -n "$((i + 1))p" $Q/names.txt
  ) 9> $Q/lock
}

prepare_mix() {
  local n=$1 design ours
  design=${n%%_p*}
  ours=${n%_mix_*}_placed
  until [ -f $OUT/${design}_p5_free/status.txt ] && [ -f $OUT/$ours/status.txt ]; do sleep 30; done
  (
    flock 8
    [ -d build/qor/dpl/xsrc/$n ] || python3 flow/dpl_mix.py --free ${design}_p5_free --ours $ours >> $log 2>&1
  ) 8> $Q/mixlock
}

worker() {
  while true; do
    n=$(take)
    [ -n "$n" ] || break
    case $n in *_mix_*) prepare_mix $n ;; esac
    flow/dpl_vivado.sh --run $n >> $log 2>&1
  done
  echo "$(date +%T) worker $1 done" >> $log
}

for w in $(seq 1 $WORKERS); do worker $w & done
wait
echo "$(date +%T) QUEUE DONE" >> $log
