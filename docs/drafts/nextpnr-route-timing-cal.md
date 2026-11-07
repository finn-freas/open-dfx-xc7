# nextpnr-route-timing-cal (draft, not posted)

Base: openXC7/nextpnr ce3f7c18 + nextpnr-cell-timing-cal.patch (worktree build/src/nextpnr-rcal). +32/-9 in
himbaechel/uarch/xilinx/gen/xilinx_gen.py. Opt-in: chipdb generator option `--route-timing FILE`.

## Problem
On identical placement and routing (docs/qor-vivado.md Finding 13: nextpnr's implementation imposed on Vivado
pip for pip), nextpnr's routed arc delays are 0.28-0.71 ns lower than Vivado's (slow corner, mean per wire
class over 5 designs), on every class of route: arcs that only go LOGIC_OUTS -> IMUX -> pin are already
0.28-0.34 ns low. The pip and node RC values come from prjxray-db's tile timing (`timing_pip_classs`, node
cap/res); they are not wrong per wire type so much as missing a fixed cost at the interconnect input stage.

## Change
`--route-timing FILE` (JSON): `classes` is a list of [name, regex] matched against a tile pip's destination
wire; `pip_add` maps a class to [fast, slow] ps added to that pip's intrinsic delay (clamped at 0). Such pips get
their own timing class (`<prjxray class>_<name>`); a bidirectional pip is classed per direction. Without the
option the generated chipdb is unchanged.

The JSON for xc7a35t-1 (build/chipdb-rcal/route_timing_xc7a35t_1.json) is fitted by flow/xroute_fit.py: least
squares of (Vivado net delay - nextpnr net delay) per arc against the count of pips of each class on the arc,
on 9079 arcs of blinky, rv_soc and bram (identical routes, nextpnr SDF with `-o lut-perm-timing`; the rv_soc data was the
run with Vivado-placed LUTRAM, `_lutramunfixed`). Refitting on the current data (10017 arcs, rv_soc with LUTRAM placed as nextpnr
did) moves no class by more than 21 ps (ctrl 280 -> 259) and the test error by 7 ps (mean -49 -> -42). Pips into
CLB pins and out of CLB outputs are not separate features (each always follows one IMUX/BYP/CTRL or precedes
one LOGIC_OUTS pip, so they are collinear). Fitted slow adds (ps): imux +413, ctrl (FAN/CTRL) +280,
byp +98, quad +26, hex +26, long +30, double +30, single +22, bounce +5, bram_in -44, hard_out -10,
clb_site_out -56. Only the slow value is used by nextpnr (`getPipDelay` reads `int_delay.slow_max`, and the
result is a single value for min and max).

## Evidence
- Applies: docs/drafts/nextpnr-cell-timing-cal.patch then this patch on ce3f7c18 (`git apply --check`); the result equals
  build/src/nextpnr-rcal's xilinx_gen.py.
- No-op: chipdb generated without `--route-timing` is byte-identical to build/chipdb-cal/on (re-generated 2026-11-06,
  build/xroute/verify/chipdb-off, `cmp` of .bba and .bin). With the JSON above the chipdb equals build/chipdb-rcal/on
  (build/xroute/verify/chipdb-on), so the rcal runs used this calibration.
- Net-arc error, nextpnr minus Vivado (slow max), designs not used for the fit (rv_mul, rv_big; 13885 arcs on nets whose
  ROUTE Vivado accepted): mean -517 -> -49 ps, mean absolute 520 -> 166 ps (build/xroute/fit/eval.json). Counting also the
  nets whose ROUTE failed but whose final pips equal nextpnr's (16937 arcs): -492 -> -19, 504 -> 183 ps.
- End to end (nextpnr re-run with the chipdb, its new implementation imposed on Vivado): docs/qor-vivado.md
  Finding 13.

## Open
- One part and corner (xc7a35t-1 slow max); the fast corner is not modelled by nextpnr at all.
- Per setup path (offline, identical routes, paths without a Vivado-unrouted net): rv_mul -688 -> +35 ps, rv_big
  -552 -> +6 ps mean. An earlier "0.6-0.7 ns residual" counted paths through nets Vivado had left unrouted (their
  delay is in Vivado's path but missing on nextpnr's side); it was a measurement artifact.
- The added delay is also used for hold (nextpnr has one routing delay): hold slack gets more optimistic.
