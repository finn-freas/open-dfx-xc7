#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
D="$(cd "$1" && pwd)"; shift
A=$ROOT/toolchain/vtr/arch/share/f4pga/arch/xc7a50t_test
VPR=$ROOT/toolchain/vtr/vtr-verilog-to-routing/build/vpr/vpr
MIN_AVAIL_MB=${MIN_AVAIL_MB:-7000}
OPTS=(--device xc7a50t-test --read_rr_graph $A/rr_graph_xc7a50t_test.rr_graph.real.bin
  --read_router_lookahead $A/rr_graph_xc7a50t_test.lookahead.bin
  --read_placement_delay_lookup $A/rr_graph_xc7a50t_test.place_delay.bin
  --max_router_iterations 500 --routing_failure_predictor off --router_high_fanout_threshold -1
  --constant_net_method route --route_chan_width 500 --router_heap bucket --clock_modeling route
  --place_delta_delay_matrix_calculation_method dijkstra --place_delay_model delta
  --router_lookahead extended_map --check_route quick --strict_checks off --allow_dangling_combinational_nodes on
  --disable_errors check_unbuffered_edges:check_route --congested_routing_iteration_threshold 0.8
  --incremental_reroute_delay_ripup off --base_cost_type delay_normalized_length_bounded --bb_factor 10
  --acc_fac 0.7 --astar_fac 1.8 --initial_pres_fac 2.828 --pres_fac_mult 1.2 --check_rr_graph off
  --suppress_warnings sum_pin_class:check_unbuffered_edges:load_rr_indexed_data_T_values:check_rr_node:trans_per_R:check_route:set_rr_graph_tool_comment:calculate_average_switch
  --sdc_file $D/design.sdc)
wait_mem() { while [ "$(free -m | awk '/Mem:/{print $7}')" -lt "$MIN_AVAIL_MB" ]; do sleep 30; done; }
tm() { /usr/bin/time -f "%e s %M KB" -o "$1" "${@:2}"; }
cd "$D"
if [ ! -f design.net ]; then
  wait_mem
  tm pack.time $VPR $A/arch.timing.xml design.eblif "${OPTS[@]}" --pack > pack.log 2>&1
fi
python3 "$ROOT/flow/vpr_ioplace.py" "$D" > io.place
P=${VPR_TAG:+${VPR_TAG}_}s
for s in "$@"; do
  mkdir -p $P$s
  [ -f $P$s/design.place ] && continue
  wait_mem
  tm $P$s/place.time $VPR $A/arch.timing.xml design.eblif "${OPTS[@]}" --net_file design.net --place \
    --fix_clusters io.place --seed $s --place_file $P$s/design.place ${VPR_PLACE_OPTS:-} > $P$s/place.log 2>&1 \
    || echo "$P$s failed"
  echo "$P$s: $(cat $P$s/place.time)"
done
