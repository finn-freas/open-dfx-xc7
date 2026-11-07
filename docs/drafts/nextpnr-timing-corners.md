# nextpnr-timing-corners (draft, not posted)

**Base:** openXC7/nextpnr e62fafd1 with the xdc3 series applied in order:
1. nextpnr-xdc-timing
2. nextpnr-xdc2-constraints
3. nextpnr-timing-report
4. nextpnr-ologic-iob-sdr

**Worktree and build:** worktree `build/src/nextpnr-corners`, build `build/nextpnr-build/corners`.

**Opt-in in two places:**
- the chipdb generator option `--corners`;
- nextpnr `-o timing-corners[=RC]`.

Without either, nothing changes.

## Problem
nextpnr times one delay model: route delays at prjxray's slow maximum, and cells at (fast min, slow max). Vivado checks setup and hold at both the Slow and the Fast process corner and reports the worse.

On a port path the Fast corner can be the worse one. The capture clock's insertion delay shrinks more than a short data path does. Example, x_iodly on our placement in Vivado:
- the input setup slack is +3.354 at the Fast corner and +4.891 at the Slow corner;
- nextpnr reported +3.92 (docs/xdc-coverage.md, "Port paths on one placement").

prjxray-db already holds both corners:
- **Pips:** four values in `tile_type_*.json` (fast_min, fast_max, slow_min, slow_max).
- **SDF IOPATHs:** `(fast_min::fast_max)(slow_min::slow_max)`. CLK_BUFG gives (0.026::0.029)(0.091::0.096), which are Vivado's own BUFG figures.

The generator folded these into one pair.

## Change
- **`gen/xilinx_gen.py --corners`:** writes a second speed grade, CORNERS, beside DEFAULT. DEFAULT keeps its values.
  - Without the option, the chipdb is byte-identical to the toolchain's (`build/chipdb-corners/off`, `cmp`).
  - With it, the pip timing classes are split by their four values, which changes no DEFAULT value.
  - CORNERS holds:
    - pips with all four prjxray values;
    - node RC as before (prjxray has one RC set, with no corners);
    - CARRY4, F7/F8 MUX and BRAM IOPATHs per corner;
    - LUT6/LUT5 A1..A6 arcs and the flip-flop's CLK->Q (REG_INIT_FF) per corner, from CLBLL_L.sdf. These replace the stubs, which have no corner split.
    - Setup/hold checks: the SDF has a single triple, which is used for both corners.
- **`himbaechel/arch.{h,cc}`:** `setTimingCorner(0|1|2)` switches the arch to the CORNERS grade, and reads (slow_min, slow_max) or (fast_min, fast_max) of every pip, cell arc, setup, hold and clk-to-q.
  - The RC part of a route delay is the slow one, times `RC` (default 1) at the Fast corner.
  - Corner 0 is the old model. It checks that both grades list the same cell types in the same order, because cells keep their timing index.
- **`common/kernel`:**
  - ArchAPI gains `getTimingCornerCount`, `setTimingCorner` and `getTimingCornerName`. BaseArch defaults to no corners.
  - `log_timing_corners(ctx)` runs one full TimingAnalyser per corner and prints, per corner, the worst setup and hold slack of three path kinds: from an input port (`in`), to an output port (`out`) and register to register (`reg`). It also prints the worst over all corners.
  - The Arch calls it at the state of the final timing analysis: after routing, before the uarch's post-route changes.
  - Placement, routing and the normal report never see the corners.
- **`uarch/xilinx/xilinx.cc`:**
  - Per-corner BUFG delay (the SDF values above).
  - Per-corner LVCMOS33 pad buffers, measured in Vivado 2025.2 one corner at a time (`config_timing_corners`): IBUF at pad E3, OBUF 12 mA SLOW at pad K16.
  - Other standards fall back to the single value, with a warning.

## Evidence (offline, 2026-11-06)
**Report only.** With chipdb `on` and `-o timing-corners`, every one of the 8 validation designs writes FASM identical to its xdc3 build (`flow/corner_compare.py --collect`, `build/corners/compare.json`): x_iodly, x_iodly_minmax, x_iodly_fall, x_mcp_from, x_mcp_thru, x_maxdly_cells, x_maxdly_dp and rv_soc.

**Binary no-op.** The corners binary with the toolchain chipdb and no option (flow/xdc_noop.py --new corners): blinky and rv_soc have 0 frames differing from the router variant; rv_pr native has 0 in 7/7 against build/patched/rv_pr_native/router.

**Chipdb no-op.** Without `--corners`, the generator's output is byte-identical to the toolchain chipdb.

**Patch check.** The five patches (the xdc3 series plus this one) apply in order to a fresh e62fafd1 export and give the worktree's files byte for byte.

**Port paths, compared on one placement.**
- The placement is nextpnr's xdc3 placement.
- "Vivado" is Vivado 2025.2's timer on that placement, with Vivado's routing, at one corner at a time (`vivado/build_xdctime.tcl`, `config_timing_corners`).
- "nextpnr" is this draft's corner report.
- Slack is in ns. The error is nextpnr minus Vivado, so a positive error means nextpnr is optimistic.

| Design | Check | Slow: nextpnr / Vivado (error) | Fast: nextpnr / Vivado (error) |
|---|---|---|---|
| x_iodly | input setup | 4.248 / 4.891 (-0.643) | **3.306 / 3.354 (-0.048)** |
| x_iodly | input hold | 4.565 / 3.696 (+0.869) | 5.726 / 5.488 (+0.238) |
| x_iodly | output setup | -8.004 / -8.852 (+0.848) | -1.190 / -1.664 (+0.474) |
| x_iodly_fall | input setup | 4.498 / 4.873 (-0.375) | **3.420 / 3.310 (+0.110)** |
| x_iodly_fall | output setup | -3.004 / -3.852 (+0.848) | 3.810 / 3.336 (+0.474) |
| x_iodly_minmax | input setup | 7.059 / 3.969 | 6.221 / 4.520 |
| x_iodly_minmax | input hold | -0.928 / 1.028 | -0.027 / 1.098 |

**What the table shows.**
- **The Fast corner now decides input setup, as in Vivado.** The worst input setup slack over the corners is 3.306 against Vivado's 3.354 (x_iodly), and 3.420 against 3.310 (x_iodly_fall).
  - The single-corner analysis gave +3.92 and +4.17, which was 0.57 and 0.86 ns optimistic.
  - Like Vivado, the report now picks the Fast corner for these checks.
- **The Slow-corner output error (+0.85 ns) and the input errors of the opposite sign have one main cause: the clock leaf route is short.**
  - nextpnr has 0.896 ns from BUFG to register; Vivado has 1.620 at the Slow corner.
  - prjxray gives the clock spine and HCLK nodes no resistance (clock_tree.cc).
  - This calibration belongs to the route-timing work, not to this draft. At the Fast corner the same gap is about half as large.
- **x_iodly_minmax is not comparable.**
  - Vivado's router lengthened the four input nets to repair hold (route 5.474 ns at the Slow corner). Our routing has no such detour.
  - nextpnr's own report says those inputs fail hold, at both corners. That is the correct verdict for our routing.

**Register-to-register paths at both corners.** Vivado's per-corner `reg_{setup,hold}_{slow,fast}.rpt` for the 8 designs (rv_soc included) are queued under the Vivado lock. They will be added here.

## Open
- **RC at the Fast corner.** prjxray has one RC set. The RC part is taken at the Slow value times `RC` (default 1, which is pessimistic for Fast-corner setup). The factor is still to be fitted on the register paths.
- **Clock leaf delay:** as above.
- **Cell setup and hold checks:** prjxray's SDF has one triple, used at both corners. The flip-flop's CLK->Q per corner comes from the SDF: 0.139 / 0.340 ns, against Vivado's FDRE 0.175 / 0.456 at the Fast / Slow corner. A measured per-corner cell table would replace it.
- **Pad buffers:** LVCMOS33 only, one pad each (E3 and K16). Other pins of the standard differ by up to 0.07 ns.
- **Hold between the two edges of one clock** (a negedge input into a posedge register, x_iodly_fall) is not checked, at any corner. This gap is in the base timer.
- **One corner pair only:** no temperature or voltage derating; the speed grade is -1.
