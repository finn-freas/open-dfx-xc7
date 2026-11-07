# ofx 0.1 release: working state (WIP)

Owner: the release agent. The release notes are in docs/release-0.1.md. This file records exactly what is done,
what is running and what is left.

## Commits
- 3fe1468: release tooling.
  - The `cli` stage in install/release_regress.sh.
  - `install/defaults_noop.py --candidates`.
  - The new `install/hardblock_regress.py`.
  - The `rel_new_tmg` variant in flow/release_bench.py.
- 48f6d0e: the 0.1 defaults, `hardblock_timing` on and `--placer static` at every size, plus fixes:
  - smoke_test path_only;
  - the openFPGALoader used by `dfx load --via jtag`;
  - power SKIP in the cli stage.
- The docs commit (this file, docs/release-0.1.md, the docs/ofx.md table and the roadmap rows) follows them.

## Done (evidence)
- regress6, the full regression with the defaults from before 48f6d0e:
  - PASS: install, series, noop, defaults, ofx, smoke, identity, revalidate.
  - FAIL: smoke_rvpr (a test bug, fixed and re-evaluated as INFO x3) and cli (see below).
- Candidate checks (~/ofx-test/candidates/run.log, 4/6 pass).
  - hardblock_timing: the blinky no-op passes.
  - clkbuf_keep_buffer_inputs:
    - PASS: blinky no-op, fixes bufio_iddr, fixes oserdes.
    - FAIL: rv_soc no-op (the BUFG `$auto$` name changes nextpnr's hash order), fixes bufr (hold violation stop).
  - static_all_sizes: 2/2. Designs above 3000 cells are judged on the placement agent's Vivado-timer evidence.
- The hardblock regression PASSes on all 6 designs (build/hardblock_regress/summary.json).

## Open findings
- **dfxpp_a50 (`ofx dfx build`, automatic partition pins, xc7a50t Nexys A7-50T):** the release nextpnr stops with
  "Partition pins: no route outside the pblocks for 'ready'", which goes to a slice CE (CEUSEDMUX_OUT).
  - Same command, same inputs: the `partpin2` variant binary routes (~/ofx-test/ppx), and the `partpin3` variant
    fails like the release (~/ofx-test/ppx3).
  - So the regression comes from the pinfeed step (partpin2 -> partpin3, release patch 0012).
  - rv_ppa and rv_ppt pass with the release binary. Not fixed.
- **`ofx power`:** the fitted ofx/power_model.json is untracked, so a release copy has no model.

## Since the first docs commit
- regress7 (defaults, ofx and cli with the new defaults and fixes): defaults PASS 6/6, ofx PASS, cli 42 PASS / 1 FAIL.
  The only failure is dfxpp_a50.
- Clean install into an empty prefix and cache: exit 0 (final attempt 13:21, peak RSS 1.8 GB, after two WSL
  kills). The 3 chipdbs have the same sha256 as the cached prefix.
- Smoke test against the clean prefix: PASSED (~/ofx-test/clean/smoke.out).

## Left to do
1. Done: the clean-prefix smoke result is in docs/release-0.1.md.
2. Keep these logs outside the repository: ~/ofx-test/regress6, regress7, clean, candidates, hbt.
3. dfxpp_a50: bisect patch 0012 against CE-pin partition nets, and add dfxpp_a50 to the noop/revalidate set.
4. Make clkbuf_keep_buffer_inputs a true no-op: give the inserted cell the stock clkbufmap `$auto$` name.
5. Vivado-timer check of the hardblock-timing placements, since this release used nextpnr's timer only.
