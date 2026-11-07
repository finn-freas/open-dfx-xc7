# Phase 7: any region, shared frames, static routing through the region

Offline work, 2026-11-05. Open tools only; nothing has run on hardware.

## Region is a per-design setting
- `flow/build_pr.py` takes a `region` key per design, with SLICE_X12Y100:SLICE_X15Y149 as the default, and writes it to `build/pr/<design>/region.txt`.
- It passes the region to:
  - rm_place.py;
  - region_route.py;
  - the shell generator, via the `shell_spec` key (gen_shell2.py `--region`; the anchor centre defaults to the middle of the region).
- make_partials.sh and regress.sh read region.txt and pass it to partial.py and pr_check.py.
- gen_shell2.py's output for the default region is byte-identical to the committed designs/rv_soc/pr/rm_shell.v (diff, verified).

## Results (verified by run)

| design | region | frames | static outside region | partial | Fmax (target 100 MHz) |
|---|---|---|---|---|---|
| rv_pr | SLICE_X12Y100:SLICE_X15Y149 (top row 1) | 72 | identical | 59,272 B, simulated exact | 160.33 MHz |
| rv_b | SLICE_X12Y0:SLICE_X15Y49 (bottom half, row 0) | 72 | identical (71 frames differ, all inside) | 59,272 B, simulated exact | 167.62 MHz |
| rv_c | SLICE_X12Y75:SLICE_X15Y124 (spans top rows 0 and 1) | 144 in 2 runs | identical (137 frames differ, all inside) | 118,320 B, simulated exact | 159.87 MHz |

- Fmax numbers come from the `_c` builds' nextpnr.log.
- Partials are build/partials/<design>/rm_<t>_from_<b>.bin. Every pair passed the region gate, CRC and the simulated load.

## Frames shared with static logic (region C)
- A 7-series CLB frame spans the full height of one clock row: 50 CLB rows, 25 above and 25 below the HCLK row.
- Region C covers only half of each of two rows. Its 144 frames therefore also hold 204 static tiles: CLB and INT tiles at Y50–74 and Y125–149 in the same columns.
- A partial writes whole frames, so it rewrites those static tiles. That is harmless for logic and routing, which get identical values; pr_check proves the static words are equal. It is **not** harmless for state kept in configuration memory, i.e. LUTRAM and SRL.
- **Found by run:** in the first rv_c build, the PicoRV32 register file (LUTRAM, RAM32M) was placed in CLBLM_L_X10Y125/Y126 and CLBLM_R_X11Y125..127, all inside region C's frames. Those partials simulated "exact" frame for frame, but loading one on hardware would have reset the register file to its power-up values.
- **Fixes:**
  - partial.py finds the static tiles that share the region's frames (`region.shared_frame_tiles`). If the full design's FASM shows any LUTRAM or SRL feature in them (`[A-D]LUT.(RAM|SRL|SMALL)`), it refuses and deletes its output. The safety record gains `shared_frame_static_tiles` and `shared_frame_dynamic_tiles`.
    - Negative test: one injected `CLBLM_L_X10Y125.SLICEM_X0.ALUT.RAM` line → REFUSED (run).
  - gen_shell2.py adds one input-less, INIT=0 LUT1 "keep-out" per shared CLBLM tile; turn this off with `--no-keepout`. nextpnr freezes any tile holding a pinned cell (xilinx_place.cc:666), so static LUTRAM/SRL cannot land there. An INIT=0 LUT with no inputs produces no FASM features.
    - rv_c rebuilt: 100 keep-outs; 0 shared tiles with LUTRAM/SRL; static identical; partials exact.
  - Pass 1 used to write minors 24/25 as all-ones across the whole frame, copying Vivado. It now writes all-ones only in the words the region owns, and keeps static words at their final value.
    - For clock-row-aligned regions the output is byte-identical to before (sha256 of all rv_pr partials unchanged, verified).
    - Those minors are not in prjxray-db, so their effect on static tiles is unknown. This is the reason for the change.
- Vivado DFX also restricts what static may place in frames shared with a reconfigurable partition (UG909). Our rule was derived from the frame layout, not copied from UG909's exact wording, which has not been checked line by line.

## Static routes through the region
- **Found by run:** the rot RM (barrel rotate: 128 LUT5) fails to route in its replay build. The router reached iteration 39,064 with 2 wires still overused.
- The same RM, built as the first configuration, routes in 7 iterations at 146.61 MHz (`build/openxc7/rv_soc/exp_rot_first`).
- **Cause:** rv_pr's static replay holds 545 static nets that use pips in the region's tiles (1,643 pips).
- **External fix, flow/static_detour.py: EXPERIMENTAL, KNOWN DEFECTIVE.**
  - It re-routes the static segments that cross the region around it. A* over INT pips; rip-up rounds; constants, clock, deliveries into the region and RM egress are kept; LUT route-throughs are handled.
  - On rv_pr it converged in 6 rounds and cut the static nets touching the region from 545 to 132, and the region pips from 1,643 to 741.
  - **Defect (verified):** its output holds 235 route loops. The original has 0, and neither has a multi-driven node or a node shared between nets.
  - nextpnr accepted the file (3131 nets, 0 collided, 39 dangling wires pruned), then made no progress for 65 minutes, and was stopped. The rv_d design that uses it does not build.
  - It is kept for reference and not used by default.
- **Adopted fix: native confinement in nextpnr** (docs/drafts/nextpnr-router-region.*, built with toolchain/buildenv; flow/build_pr_native.py). See docs/phase8-native.md.

## Reproducibility fix (2026-11-05 night)
- **Found:** two from-scratch builds of the external flow gave different, though valid, bitstreams for some configurations: rv_pr andn and rv_b add changed after the 17:20 rebuild.
- **Cause, confirmed by a control run:** flow/region_route.py iterates sets of wire names. Python randomises string hashing per process, so the BFS order, and with it the chosen routes, change from run to run. Same inputs: PYTHONHASHSEED 1, 2 and 0 gave three different outputs; seed 0 twice gave identical outputs.
- **Fix:** flow/build_pr.py runs every step with PYTHONHASHSEED=0.
- **Verified:** rv_pr (4 configurations) and rv_b (2) built from scratch twice; all 6 have identical frame data (build/det_keep vs the rebuild).
- **Note:** the .bit header carries a build date and time, so compare .frames, not whole .bit files.
