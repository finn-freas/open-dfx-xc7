# nextpnr-vivado-checks.patch (draft, opt-in `-o vivado-timing`)

Closes four timer gaps against Vivado that docs/timing-reports.md found. Off unless `-o vivado-timing` is given.

Base: build/src/nextpnr-timrep (upstream openXC7 nextpnr e62fafd1 + the xdc-timing/xdc2 drafts + nextpnr-timing-report),
i.e. the tree of build/nextpnr-build/timrep. Files: common/kernel/timing.{h,cc} (small: one helper, two one-line
conditions, the I/O sentinel in walk_forward/walk_backward and two report conditions), himbaechel/uarch/xilinx/xdc.cc,
xilinx.{h,cc}. Built as build/nextpnr-build/tmrfix (build/src/nextpnr-tmrfix).

| gap | Vivado | without the option | with `-o vivado-timing` |
|---|---|---|---|
| clocks of different primaries, no exception | timed from a common time zero, "Timed (unsafe)" | not timed ("unrelated clocks") | timed: the root check in clock_setup/hold_relationship is skipped |
| set_input/output_delay with only `-max` or only `-min` | only setup or only hold is timed | both, with the one value | xdc.cc appends " max"/" min" to NEXTPNR_INPUT/OUTPUT_DELAY (only when a side is missing, so existing attributes are unchanged); the missing side gets an arrival/required time of +-0.5 ms and its check is left out of the report |
| FDCE CLR / FDPE PRE | recovery/removal, `**async_default**` | timed as a synchronous input with the chipdb's SR stub (setup 0.100, hold 0.000) | recovery 0.404 (CLR) / 0.358 (PRE), removal -0.248 ns (prjxray-db artix7 CLBLL_*.sdf FF_INIT_QL/QH, slow corner) |
| SRL16E/SRLC32E | D/CE setup/hold, CLK->Q | no arcs: no endpoint at the SRL input, no startpoint at its output | DI1 0.170/0.093, DI2 0.173/0.094, WE 0.638/0.014 ns setup/hold; CLK->O6 1.186-1.472, O5 1.177-1.461, MC31 0.898-1.114 ns (CLBLM_*.sdf LUT_OR_MEM6/5SHFREG) |

The `**async_default**` grouping itself is in ofx/timing.py (the report keeps nextpnr's clock pair).

## No-op

Without the option, tmrfix gives the same FASM and the same report.json as timrep on x_cdc_none, x_iodly_partial,
x_iodly_minmax, x_arst, x_srl, x_mmcm_none, blinky and rv_soc (flow/timing_report_check.py --fix,
build/timing_rv/noop_fix.json).

## With the option (nextpnr timer)

| design | without | with |
|---|---|---|
| x_cdc_none | 32 setup / 32 hold endpoints, clk_a -> clk_b untimed | 48 / 48 (Vivado 48 / 48); clk_a -> clk_b WNS -5.048 ns, requirement 2.000 ns (Vivado: -6.670, 2.00) |
| x_iodly_partial | 20 / 20 | 12 / 16 (Vivado 12 / 16) |
| x_srl | 8 endpoints (FF D only) | 12 (+4 SRL16E DI2) |
| x_arst | 12 SR endpoints with the stub | 12, recovery/removal values |
| x_mmcm_none, x_iodly_minmax, rv_soc | | unchanged endpoint counts and WNS/WHS |

Comparison with Vivado on the same placement: docs/timing-reports.md.
