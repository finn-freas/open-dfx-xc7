# nextpnr-timing-report (draft, not posted)

Base: openXC7/nextpnr e62fafd1 + nextpnr-xdc-timing + nextpnr-xdc2-constraints (the `xdc2` variant). Worktree
build/src/nextpnr-timrep, build build/nextpnr-build/timrep (toolchain/buildenv/build_nextpnr_variant.sh, VARIANT=timrep).
+316/-29 in common/kernel/{command.cc, context.h, nextpnr_types.h, report.cc, timing.cc, timing.h}. Only the common
kernel is touched; nothing is xilinx-specific except that constant nets named `$PACKER_*` are not reported as
unclocked startpoints.

## Problem
The `--report` JSON has the Fmax per clock and the worst path per clock (and per cross-domain pair). A Vivado-style
`report_timing_summary` needs more: the slack of every endpoint (WNS, TNS, failing and total endpoints), hold slack,
the N worst paths per clock pair, the endpoints that are not timed and why, and the clock definitions.

## Change (opt-in: `--report-paths N`)
- New option `--report-paths N` (`Context::timing_report_paths`). With N = 0 (the default) no new code runs.
- `TimingAnalyser::build_endpoint_reports(N)`, called from `timing_analysis()` only when it updates
  `ctx->timing_result` (the final analysis after routing, and hold-fix's re-analysis). For every endpoint and every
  launch domain that reaches it:
  - setup: requirement (the pair's period: clock period, edge relationship between clocks of one primary, max delay
    or multicycle, less the setup uncertainty; plus the N-1 periods of a `NEXTPNR_MCP_SETUP` endpoint) and slack
    (`period + setup_slack`, the same number the placer and the Fmax use);
  - hold: requirement and slack with the rules of `get_min_delay_violations()` (one clock, related clocks or a hold
    relationship; set_min_delay; no hold under a false path or -datapath_only);
  - `untimed`: `no clock`, `no launch clock`, `no capture clock`, `false path`, `false path between the clocks`,
    `unrelated clocks` (different primaries, no exception: Vivado times these, nextpnr does not);
  - an endpoint that no startpoint reaches (driven from an unclocked port or cell, not from a constant) is listed with
    `no launch clock`.
- For each (launch clock, capture clock) pair the N worst setup and the N worst hold endpoints get a full path, built
  with the existing `build_critical_path_report()`.
- report.cc: new keys `clocks` (net, name, period, high, offset, master), `endpoints`, `paths`. The per-path segment
  writer of `critical_paths` is factored out (`json_report_path_segments`) and shared; `critical_paths` itself is
  unchanged.
- No IdString is interned by the new code, so the IdString table (and with it hash order) is unchanged.

## Evidence (offline, 2026-11-06)
- No-op (flow/timing_report_check.py, results build/timing/noop.json): xdc2 binary against timrep without the option
  and timrep with `--report-paths 10`, same yosys JSON, same seed, on blinky, rv_soc (qor, 5 ns), x_mmcm_none,
  x_iodly, x_gen_none: the FASM is identical in all 15 comparisons apart from the version header line, and the
  report JSON is identical (without the option) or identical in all old keys (with it).
- The report is read by `ofx timing` (docs/ofx.md); comparison with Vivado's report_timing_summary in docs/ofx.md
  "Timing reports".

## Limits
- One endpoint pin is a nextpnr cell port (FF D/CE/SR, LUTRAM WA/WE/DI, BRAM/DSP pins). Vivado counts the same pins,
  but nextpnr has no timing arcs for some hard-block pins unless `-o hardblock-timing` (another draft) is used.
- Paths are only written for the N worst endpoints of each pair; `--from` filters in ofx work on those paths only.
- The register clock delays that `with_clock_skew` adds to arrival and required times are not itemized as segments
  (the existing path report does not do it either); ofx prints the difference as one "clock" line.
- No pulse-width checks, no multi-corner analysis.
