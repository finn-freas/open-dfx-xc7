# Paused 2026-11-06 evening (third pause): where to resume

The user says the next resume will run for a long time without pauses. On resume, restart every workstream below at once and keep going.

## Goal and standing rules
- **Goal (user):** an open-source Vivado for the 7-series that performs at or better than Vivado, covering all of it. At every planning step, scan docs/open-vivado-roadmap.md. Every none/gap/untested row needs an owner or a recorded reason for deferral.
- **Pushes:** RESUMED, at most ~2 per day.
  - Push only a comment-free export. Comments are fine locally.
  - The user chose to rewrite GitHub history: one force-push of a root commit holding a comment-free snapshot of HEAD, then normal fast-forward pushes from the local `publish` branch.
  - The strip must ONLY remove comments, never change code:
    - keep Python docstrings, insert nothing, reformat nothing;
    - prove per file that every removed character was inside a comment;
    - in patches, only the comment text in `+` lines is removed.
- **Never touch:** the Tang Nano and `~/friendbot`.
- **Resource limits:** WSL has ~11 GB of RAM. Every nextpnr goes through `ofx/npwait.sh` (OFX_NEXTPNR_BIN, OFX_MAX_NEXTPNR=2). Wait for >= 4 GB free before chipdb or big compiles. Use only one Vivado instance at a time.
- **Vivado parts:** the installed Vivado 2025.2 has only Artix-7 device data (no Spartan-7/Zynq/Kintex). Vivado cross-checks are possible for Artix-7 only.

## Committed and verified
- 59f8e6b: Area vs Vivado (Finding 12).
- 180cd11: Vivado references for the 22 xdc2 designs.
- e7bb8c0: Zynq PS7.
  - `examples/ps7_axi_z7` builds.
  - The boot files are made with open tools (U-Boot SPL + ps7_init_gpl, FIT, SD image, OpenOCD JTAG).
  - Offline checks pass: QEMU jtag/sd boot, ps7_init.tcl selftest, and the GP0 trace (34/34) on both the RTL and the bitstream-decoded netlist. I re-ran them myself.
  - Not yet on silicon.
  - The `ofx boot` hook is in ofx/cli.py, which is in the WIP checkpoint below.

## Stopped mid-task: in the "WIP pause checkpoint 3" commit, UNVERIFIED
Restart each one with the same brief as last time, which is the same as items 1-8 of the previous RESUME (git show 65bbd82:docs/RESUME.md). Re-verify what is on disk first.
1. **Route-timing calibration + placement round 2 (Finding 13):** `flow/xroute*.py`, `flow/place_bench.py`, `flow/replay_dump.py`. Nothing reported yet.
2. **ofx 0.1 release:**
   - `install/release_regress.sh`, `install/noop_check.py`, `install/defaults_noop.py`.
   - Last seen: the series stage PASSed (yosys, prjxray-db and openFPGALoader patches apply with the expected TREE). It was running the noop stage.
3. **Timing reports vs Vivado:** `ofx/timing.py`, `flow/timing_report_check.py`, `flow/timing_vivado_compare.py`, `vivado/build_xtime.tcl`.
4. **Devices:**
   - New `flow/device_vivado_compare.py`, `vivado/build_devices.tcl`, `vivado/run_devices.ps1`.
   - Examples `blinky_k70t` (Kintex-7 attempt; status unknown), `dfx_b3`, `dfx_cms7`, `dfx_s75`, `dfx_z035`, `dfxpp_cora`.
   - It was writing the docs/ofx.md device results section.
5. **DRC + power:** `ofx/drc.py`, `flow/drc_compare.py`, `flow/power_fit.py`, `vivado/build_drcpow.tcl`.
6. **Timing-driven synthesis (Finding 14):** `flow/synth_timing*.py`, `flow/qor_synx.py`, `flow/qor_area_sim.sh`.
7. **XDC/bitstream fixes:**
   - New draft `docs/drafts/nextpnr-ologic-iob-sdr.{patch,md}` (the OLOGIC SDR fix).
   - Changes to `flow/bitstream_props.py` (CTL1 bit 12 / EXTMASTERCCLK_EN / CMD 0x13).
   - New `flow/xdc_xtime.py` and `vivado/build_xdctime.tcl` (exceptions timed on our placement in Vivado).
   - Edits to `flow/xdc_audit.py`, `flow/xdc_noop.py`, `docs/xdc-coverage.md`.
8. **Comment-free publish tool:** nothing on disk yet; it must be built from scratch.
   - Tool: `tools/publish_strip.py`.
   - Export: `git archive` into build/publish/tree.
   - Stripping: per-language lexers.
   - Proofs:
     - the only-comments-removed proof;
     - Python AST equality;
     - yosys RTLIL equality ignoring src;
     - `bash -n` plus a token comparison;
     - XDC parse;
     - `.frames` identical for blinky/rv_soc/rv_pr native;
     - zero comments left.
   - Branch: build `publish` with plumbing only; the first commit is a ROOT commit.
   - Doc: docs/publish.md.
   - Then the lead force-pushes once (`git push --force origin publish:master`), verifies the remote, and from then on pushes at most ~2 a day.

## Deferred, with reasons
- **Multi-corner timing:** waits for item 1.
- **phys_opt / post-route optimisation:** waits for placement round 2.
- **GTP:** needs a part with GTP data (item 4 reports which).
- **GUI:** waits until the core flow matches Vivado.

## Biggest remaining gaps vs Vivado
- **Placement:** ~25 % slower under Vivado's timer.
- **LiteX SoC area:** +14 % LUT sites; LUTRAM 320 vs 142.
- **XDC fixes:** the list in item 7.
- **Not yet in Finding 13/14:** the calibration and synthesis results above.
- **Zynq PS7:** board test pending.
- **Kintex-7:** unknown.
