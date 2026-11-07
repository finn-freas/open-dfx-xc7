# WIP: multi-corner timing (timing-corners)

Owner: the XDC and bitstream agent. Updated 2026-11-06 22:45.

## Done (committed)
- **Draft:** `docs/drafts/nextpnr-timing-corners.{patch,md}`.
  - Generator option `--corners`: a CORNERS speed grade.
  - nextpnr `-o timing-corners`: Slow and Fast corner, report only.
- **Chipdb no-op:** without `--corners` the chipdb is byte-identical to the toolchain's.
- **Binary no-op:** blinky, rv_soc and rv_pr (7/7) are frame-identical.
- **Report only:** FASM is identical to xdc3 on 8 designs.
- **Port paths, Vivado on our placement, per corner:**
  - worst input setup: 3.306 vs 3.354 ns (x_iodly), 3.420 vs 3.310 (x_iodly_fall);
  - Slow-corner outputs are 0.85 ns optimistic, from the clock leaf route (route-timing agent).
- **Docs:** roadmap Multi-corner row → partial (opt-in draft); xdc-coverage gaps item 1.

## Not done (waiting on the Vivado lock; nothing of mine is running)
- **Register-to-register paths at both corners** for the 8 designs, rv_soc included. Then the Fast RC factor fit.
  1. Run `bash vivado/run_xdctime_batches.sh` from Windows Git Bash. It uses the lock, runs short batches split between designs, and pauses 5 min between batches. Sources are already in `build/xdc_xtime/src/*_xdc3`.
  2. Then run `python3 flow/corner_compare.py --collect`. The nextpnr corner logs are already in `build/corners/<d>/nextpnr.log`.
  3. Add the reg rows to the draft md "Evidence" section, and fit RC (`-o timing-corners=RC`) if the Fast reg errors show a consistent factor.

## Known gaps
- No hold check between edges of one clock (x_iodly_fall). This is in the base timer.
- Per-corner cell setup/hold: prjxray has one triple.
- FF clk-to-q from the SDF (0.139 / 0.340) against Vivado (0.175 / 0.456).
