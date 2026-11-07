# WIP: incremental compile + XDC leftovers (xdc4)

Owner: the "rows nobody else owns" agent, 2026-11-06. Results so far: docs/incremental.md,
docs/xdc-coverage.md section "xdc4", roadmap rows (incremental, I/O delays, latency/jitter, DIFF_TERM/KEEP).

## Done and committed
- flow/incremental.py (structural matching, LUT pin canonicalisation, slice/tile/carry-chain replay rules,
  --ripple, --whole-tiles), `ofx build --incremental REF [--incremental-routes]` (ofx/cli.py),
  flow/incremental_bench.sh, flow/incremental_variants.sh, flow/incremental_xtime.py, test project
  designs/incr/proj_edit, edit designs/incr/rv_soc_edit/rv_soc.v. Numbers in docs/incremental.md (nextpnr timer).
- docs/drafts/nextpnr-incremental-weak-routes.patch (applies on the 27-patch install series; built as
  build/nextpnr-build/incr from build/src/nextpnr-incr, a worktree of upstream/openXC7_nextpnr).
- flow/xdc_keep.py + gap_build hook + xdc_audit variant xdc4; KEEP/DONT_TOUCH/MARK_DEBUG results.
- docs/drafts/nextpnr-xdc4-constraints.patch (base: build/src/nextpnr-xdc4 commit "diff-term draft" = xdc3 tree +
  nextpnr-diff-term.patch): DIFF_TERM applied, KEEP/MARK_DEBUG messages, set_clock_latency (with the fix of the
  early return in apply_xdc_clock_exceptions).
- 14 xdc4 test designs (flow/xdc_designs.py), vivado/build_xdc4.tcl, vivado/run_polite.sh, flow/xdc_pads.py.

## Not run: stopped at hand-back (Vivado and nextpnr slots held by higher-priority agents all session); relaunch with `bash build/incr/viv_batches.sh`, `bash build/incr/viv_xtime.sh`, `bash build/incr/q2.sh` (scripts in build/, not committed)
- Vivado: build/incr/viv_batches.sh (xdc4a: x_pad_a/b + x_lat_*; xdc4b: x_jit_* + x_keep_* + x_dbg_rtl; then
  vivado/run_incr.sh = Vivado ref/full/incremental on the rv_soc edit), build/incr/viv_xtime.sh (Vivado timer on
  our ref/full/w0p placements, then flow/incremental_xtime.py --collect).
- nextpnr (OFX_MAX_NEXTPNR=1): build/incr/q2.sh = x_lat_src/early/xsrc with the fixed xdc4 binary, then the
  series binary (build/nextpnr-build/incr) variants full/s0k/w0k/w0p/s0 (SFX=.series).

## Next
1. When Vivado's pad_arcs.txt exist: `python3 flow/xdc_pads.py`, put the table into xilinx.cc getCellDelay
   (xdc4 tree), rebuild, re-run x_pad_a/b, compare per-port slack with Vivado's in_paths/out_paths.
2. Compare x_lat_* / x_jit_* / x_keep_* with Vivado (paths.rpt clock uncertainty, pairs.txt, synth_cells.txt).
3. Weak-route variants (s0k/w0k) and the Vivado incremental numbers into docs/incremental.md.
