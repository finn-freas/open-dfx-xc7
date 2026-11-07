# DRAFT (not posted): yosys clkbufmap puts the inserted BUFG in front of BUFIO/BUFR/BUFG inputs

Status: **tested offline 2026-11-05 as a yosys plugin with the same yosys binary; bufr, bufio_iddr, oserdes (and iserdes in the combined flow) now build; clock structure matches Vivado's decode; no hardware test. A full yosys build was not done (see Build).** Nothing pushed or posted.

Patch: docs/drafts/yosys-clkbufmap-keep-buffer-inputs.patch, against YosysHQ/yosys 3718f7f13 (the oss-cad-suite 20261021 yosys, `Yosys 0.70+186 (git sha1 3718f7f13)`), passes/techmap/clkbufmap.cc only (+36/-1).
- Source: upstream/YosysHQ_yosys (clone of github.com/YosysHQ/yosys, blob-less), worktree build/src/yosys-clkbuf (detached at 3718f7f13, not committed).

## Problem
`synth_xilinx` runs `clkbufmap -buf BUFG O:I` at the end. When an input pin clocks fabric flip-flops and also drives a BUFIO/BUFR (or a user BUFG/BUFGCE/BUFGCTRL/BUFH), clkbufmap inserts one BUFG and moves every load of the net behind it, including the existing buffer's input (build/gap/bufr/oxc7/yosys.log: `Inserting BUFG on bufr.$abc$20951$aiger$o20[0].`). A BUFIO/BUFR input cannot be reached from a BUFG output, so nextpnr fails: `Failed to route arc 4.0 of net ... from X60Y103/BUFGCTRL_X0Y0.O to X113Y130/BUFR_X0Y1.I` (bufr), same shape for bufio_iddr, oserdes and iserdes.

## Change
Cell types with a `clkbuf_driver` output (in the xilinx techlib only clock buffers: BUFG*, BUFH*, BUFIO*, BUFR, BUFMR*, ...) are collected. After the inserted buffers are wired, every non-`clkbuf_sink` input bit of such a cell that sits on a newly buffered net is moved back to the inserted buffer's input, i.e. the unbuffered clock. The help text says so; the pass logs `Connecting <module>.<cell>.<port> to the unbuffered clock.`

## Build
- A full yosys build needs flex and bison; neither is on this machine. `micromamba install bison flex` from conda-forge failed twice with TLS resets on repodata shards (build/buildenv_bison_flex.log, "Could not load repodata.json for conda-forge/noarch"). So yosys was not rebuilt.
- Instead the patched clkbufmap.cc was built as a plugin against the oss-cad-suite headers with only the pass name changed (`clkbufmap_gapfix`): build/yosys-plugin/clkbufmap_gapfix.{cc,so}, g++ 15.2, 0 warnings (build/yosys-plugin/build.log).
- flow/gap_build.py `--yosys-plugin SO --clkbuf-pass NAME` runs `synth_xilinx ... -run :finalize; NAME -buf BUFG O:I; clean; synth_xilinx ... -run check:`, i.e. the same script with the finalize step replaced.
- Harness check: the same split with the stock `clkbufmap` (`--base-synth`, tag ystock) gives a yosys JSON byte-identical to the normal flow's for all 14 designs tested (bufr, bufio_iddr, oserdes, bufr_pin, bufio_pin, bufg, bufgctrl, bufh, mmcme2_adv, mmcme2_base, plle2_adv, iddr_oddr, qor_blinky, qor_rv_soc).

## Evidence (run 2026-11-05)
Command: `python3 flow/gap_patch_eval.py yclk <designs> --base ystock --base-synth --nextpnr-variant stock --yosys-plugin build/yosys-plugin/clkbufmap_gapfix.so --clkbuf-pass clkbufmap_gapfix --run`. nextpnr is the stock rebuild in both runs. Results build/gap/patch_eval_yclk.json, log build/gap/patch_eval_yclk.log, per run build/gap/<d>/{ystock,yclk}/{yosys,nextpnr}.log.

Decoded non-CLB/non-INT features against Vivado, viv-only / oxc7-only, exact (by type):

| design | stock | patched |
|---|---|---|
| bufr | FAIL (BUFG to BUFR.I) | **0 / 0 (0 / 0)** |
| bufio_iddr | FAIL (BUFG to BUFIO.I) | 0 / 4 (0 / 4): ILOGIC IFF.ZSRVAL_Q1..Q4, the same 4 as bufio_pin with stock |
| oserdes | FAIL (BUFG to BUFIO.I) | 7 / 2 (7 / 2): the same 7 / 2 as oserdes_pin with stock (gap G13: DATA_RATE_TQ, IS_D5..8_INVERTED, TDDR.SRUSED, CLKDIV RCLK mux) |

Clock tiles are excluded from that diff, so the clock structure was compared by hand in the decoded FASM (CLK_HROW_TOP_R_X60Y78 and HCLK_CMT_L_X106Y78):
- bufg (user BUFG on the pin that also clocks fabric): Vivado feeds both BUFGs from one HROW input (`CK_BUFG_CASCO0` and `CASCO2` <- `CK_IN_R0` <- `HCLK_CMT_CCIO0`). Patched: both from one input (`CASCO0`, `CASCO10` <- `CK_IN_R3` <- CCIO0). Stock: the user BUFG is fed from the inserted BUFG through a BUFHCE (`CASCO10` <- `CK_IN_L0`, `BUFHCE_X0Y0.IN_USE`).
- bufgctrl (BUFGCE and BUFGCTRL on the pin): Vivado feeds three BUFGs from `CK_IN_R0`; patched feeds three from `CK_IN_R7`; stock again feeds two through a BUFHCE loop.

## Regression
- FASM and .frames identical to stock: bufr_pin, bufio_pin, mmcme2_adv, mmcme2_base, plle2_adv, iddr_oddr, qor_blinky, qor_rv_soc.
- Changed on purpose: bufg (+37 / -47 FASM lines) and bufgctrl (+14 / -17), as described above; their non-CLB/non-INT Vivado diff stays 0 / 0.
- bufh still fails (gap G7, placement region), with or without the patch.

## Not known
- Hardware behaviour (no board).
- Other architectures that use clkbufmap (gatemate, efinix, intel_alm, sf2, microchip) were not tested; the change applies to their `clkbuf_driver` cells too.
- Not tested with `-inpad` (synth_xilinx does not use it; iopadmap inserts the IBUF earlier).
