# XDC coverage of the open flow, against Vivado 2025.2 (xc7a35tcsg324-1)

Date: 2026-11-06. No hardware was used. Every number below comes from a run whose log is named.

## What was run

- **Test designs:** `flow/xdc_designs.py` writes 34 small designs to `designs/xdc/<name>/`, each one `.v` and one `.xdc`. Both flows get the same RTL and the same XDC.
- **Open flow:** `flow/xdc_audit.py` (CONFIG block, DRY_RUN, `--run`) runs yosys, then nextpnr through `ofx/npwait.sh`, then fasm2frames and xc7frames2bit. It uses `--timing-allow-fail`, so failing timing still gives a full report.
  - `base` is `build/nextpnr-build/router` (router-region stack e62fafd1; its XDC reader is upstream ce3f7c18 plus pblocks).
  - `xdc` is the same stack plus `docs/drafts/nextpnr-xdc-timing.patch`.
  - Logs: `build/xdc/<name>/<variant>/{yosys,nextpnr}.log` and `status.json`. Parsed summary: `build/xdc/summary.json` (`summary_base.json` holds the base run).
- **Vivado:** `vivado/run_xdc.ps1 -Run` runs `vivado/build_xdc.tcl` (synth, opt, place, route, bitstream). Outputs are in `C:\Users\finnf\open-dfx-xc7-vivado\build\xdc\<name>\`:
  - `timing.rpt`, `clock_interaction.rpt`, `exceptions.rpt`, `check_timing.rpt`, `io.rpt`;
  - `pairs.txt`: the worst setup path per clock pair, with Vivado's EXCEPTION, REQUIREMENT and DATAPATH_DELAY;
  - `synth_cells.txt`, `placed_cells.txt`, and the `.bit` file.
- **Bitstream decode:** `flow/xdc_compare.py --fasm --run` decodes all bitstreams with prjxray (`flow/bit2fasm.py`) into `build/xdc/<name>/{vivado.fasm,<variant>/decoded.fasm}`, so features are compared under one naming. It writes `build/xdc/compare.json`.
- **Timers:** nextpnr's timer and Vivado's timer are different models. Only the effect of a constraint (fail to pass, path removed, feature changed) is compared across the tools, never absolute delays. Same-path delay agreement is the QoR agent's item (docs/qor-vivado.md).

Legend:
- **accepted:** the base reader takes the line without an error.
- **effective:** the line changes timing analysis or the bitstream as it should.
- **silent:** accepted and ignored with no message. This is the worst case.

## Coverage table

Abbreviations:
- **V** = Vivado's result. Its directory is `C:\Users\finnf\open-dfx-xc7-vivado\build\xdc\<design>\`; x_syn_cont and x_loc2 are in `...\build\xdc2\`.
- **base / xdc** = nextpnr's log, `build/xdc/<design>/{base,xdc}/nextpnr.log`.
- **Frames** = configuration frames that differ between the base and xdc bitstreams of the same design (`bitparse`).

### Clocks and timing exceptions
| Command | Accepted (base) | Effective (base) | With xdc draft | Verified vs Vivado (design: evidence) |
|---|---|---|---|---|
| create_clock -period on a port | yes | yes | same | all designs |
| create_clock -name / -waveform | yes, warns "ignoring" | no | applied: name used by get_clocks; waveform sets high time and offset | Not exercised by an exception test. The default name (the port, clk_a/clk_b) is verified in x_cdc_groups; `-name` on create_generated_clock is verified in x_gen_div |
| create_clock without a target (virtual clock) | warns | no | warns NOT supported | not built |
| create_generated_clock -divide_by on [get_pins div_reg/Q] | warns "ignoring" | no: clk_div timed at --freq 100 MHz, 79.0 MHz FAIL | applied: clk_div 20 ns, 79.0 MHz **PASS at 50** | x_gen_div: V clk_div requirement 20 ns, slack +0.834. x_gen_none: V reports 20 endpoints `no_clock` (unconstrained); nextpnr times them at the default and FAILs. Frames 0 (only the check changes) |
| MMCM/PLL outputs: periods | automatic | yes (c1 100 MHz, c2 200 MHz) | same | x_mmcm_*: V the same periods |
| MMCM outputs: paths between them | automatic | **no**: c1 to c2 only listed as cross-domain, never checked | checked: `Max delay for posedge c1 -> posedge c2: 5.84 ns (FAIL at requirement 5.00 ns, slack -0.84 ns)` | x_mmcm_none: V requirement 5.000, slack -1.806, 4 failing endpoints. Frames 0 |
| set_clock_groups -asynchronous | warns "ignoring" | no | applied after packing, both directions; no criticality, no cross-domain report | x_cdc_groups: V `Asynchronous Clock Groups`, WNS -8.099 to +5.544. x_mmcm_groups (generated clock names c1_mmcm/c2_mmcm): V same. Frames 211 / 233 (placement no longer weighs the path) |
| set_false_path -from [get_clocks] -to [get_clocks] | warns "ignoring" | no | applied | x_cdc_fpclk: V `False Path`, WNS +5.544 |
| set_false_path -to [get_cells {bq_reg[*]}] | warns "ignoring" | no | applied to 16 cells (Vivado names resolved) | x_cdc_fpcell: V `False Path` |
| set_false_path -from cells -to cells, or -through | warns "ignoring" | no | warns NOT applied | not built |
| set_multicycle_path N -setup -to [get_cells] | yes | **no**: `-to list matches no cells` (yosys names flops `$auto$ff...`) | applied to 4 cells: 68.8 MHz FAIL to **140.5 MHz PASS** | x_mcp_to: V `MultiCycle Path Setup -end 2`, requirement 20 ns. Frames 227 |
| set_multicycle_path between MMCM clocks | as above | no | requirement 10 ns, PASS, slack +4.12 | x_mmcm_mcp: V requirement 10.000, slack +1.629 |
| set_multicycle_path -hold | info | hold stays on the launch edge | same | V: -hold 1 is the matching Vivado form |
| set_multicycle_path -from | warns "ignoring" | no | same (gap); **xdc2: applied** (x_mcp_fromto requirement 20 ns, as V) | x_mcp_fromto: V applies it (requirement 20 ns) |
| set_max_delay -datapath_only, set_min_delay | warns "ignoring" | no | warns NOT applied (gap); **xdc2: applied** (x_cdc_maxdly FAIL at 5.00 ns, slack -2.42) | x_cdc_maxdly: V `MaxDelay Path 5.000ns -datapath_only`, slack -4.730 |
| set_input_delay / set_output_delay | warns "ignoring" | no: nextpnr does not time port paths | warns NOT applied (gap); **xdc2: timed** (x_iodly output slack -7.82 ns, V -7.764) | x_iodly: V WNS -7.764 at ja[*], 8 failing endpoints. x_iodly_none: V +5.200 |
| set_clock_uncertainty | warns "ignoring" | no | warns NOT applied (gap); **xdc2: applied** (x_uncert +1.00 ns on the path) | x_uncert: V clock uncertainty 1.035 ns (user 1.000) against 0.035 ns in x_mcp_none |
| get_clocks -include_generated_clocks | n/a | n/a | applied (a clock made from a match) | not built separately |

### Object queries and file syntax
| Form | Base | With xdc | Evidence |
|---|---|---|---|
| `[get_ports {a b c}]` brace list | **crash**: `Assertion failure: str.back() == '}'` (xdc.cc:57) | resolved | x_syn_list: xdc gives DRIVE.I4 on ja[0..5], as V does (8/8 ports match V) |
| `[get_ports {ja[*]}]` glob | no match and no message. It ended in `port ja[7] has no IOSTANDARD`; a DRIVE-only glob would be silently lost | resolved; a glob with no match warns | x_syn_glob: 8/8 ports DRIVE.I4, same as V |
| Line ending in `\` | error `expected at least four arguments` | joined | x_syn_cont: G13 DRIVE.I4 in xdc and in V (xdc2) |
| `get_cells` with Vivado register names (`q_reg[0]`, `s1_reg`, `dq_reg[*]`) | **silent no match** (LOC, ASYNC_REG, KEEP) or warned no match (multicycle) | resolved through the register's Q net. A miss warns `matches no cell, so it is NOT applied` | x_loc, x_mcp_to, x_keep_cell. x_async_xdc: still no match, because yosys made an SRL16E of s1..s3, and it now says so |
| `get_cells -hier`, `-filter {NAME =~ ...}` | in multicycle only | everywhere | x_mcp_* |
| `get_nets` / `get_pins` as a set_property target | **fatal** `targets other than 'get_ports' or 'get_cells' are not supported` | accepted, warns NOT applied | x_dbg_net, x_cdr build with xdc |
| Repeated property with a new value | non-fatal error | later value wins, with a warning (as in V) | x_syn_cont (before the generator fix): warning on ja[0] |

### Pad and cell properties (bitstream decoded with prjxray for both flows)
| Property | Base | With xdc | Verified vs Vivado |
|---|---|---|---|
| PACKAGE_PIN, IOSTANDARD | effective | same | all designs |
| DRIVE 4/8/12/16, LVTTL 24 | effective | same | x_io_drive: 8/8 ports match V (I4, I12_I8, I12_I16, I16, LVTTL I24) |
| SLEW FAST | effective | same | x_io_drive ja[4], ja[5] match V |
| PULLTYPE PULLUP | effective | same | x_io_pull btn[3] matches V |
| PULLUP TRUE / PULLDOWN TRUE / KEEPER TRUE | **silent: PULLTYPE.NONE** | PULLTYPE.PULLUP / PULLDOWN / KEEPER | x_io_pull btn[0..2] match V. Frames 2 |
| IN_TERM UNTUNED_SPLIT_50 (SSTL135) | effective | same | x_interm: IN_TERM.UNTUNED_SPLIT_50 matches V. Seen alongside: without IN_TERM, nextpnr still writes `STEPDOWN` on the SSTL135 pad and V does not (x_interm_none) |
| INTERNAL_VREF on [get_iobanks] | warns "isn't supported" | same | nextpnr always writes HCLK_IOI3 VREF.V_675_MV for SSTL; this is right for 0.675 V only |
| DIFF_TERM | silent | warns NOT applied | earlier evidence: gap-vivado.md G2 (6 Vivado-only bits) |
| IOB TRUE | silent | warns NOT applied; **xdc2: packed** into ILOGIC/OLOGIC (x_io_iob: same 2 registers as V, 105/109 IOI FASM lines identical) | x_io_iob: V packs the input flops into ILOGIC (IFF.SRTYPE.SYNC, IFF.ZINV_C, IFF.ZINIT_Q1 at LIOI3_X0Y127 and LIOI3_TBYTETERM_X0Y137); both nextpnr builds keep them in slices |
| LOC SLICE / site BEL (CFF) on a flop | silent: no match | applied: SLICE_X10Y20/CFF; x_loc2 SLICE_X10Y120/CFF | x_loc2: V SLICE_X10Y120 SLICEM.CFF, BUFGCTRL_X0Y20 (same as xdc) |
| LOC on a BUFG instance | effective | same | x_loc: **V refuses** BUFGCTRL_X0Y5 for a clock pin in the top half (Place 30-574), and nextpnr accepts it: there is no dedicated-clock-placement DRC. **xdc2 refuses it** with the same rule (rule_gclkio_bufg) |
| ASYNC_REG (XDC or RTL) | silent | warns NOT applied; **xdc2: 3 FDRE in one slice** (yosys plugin + nextpnr cluster) | x_async_*: V 3 FDRE in one slice (AFF/BFF/CFF or AFF/A5FF/B5FF). Yosys 0.70+186 makes one **SRL16E** in all three variants, even with `(* ASYNC_REG = "TRUE" *)`; `(* keep *)` on the registers gives 3 FDRE |
| KEEP / DONT_TOUCH (XDC) | silent | warns NOT applied (synthesis is over) | x_keep_cell |
| MARK_DEBUG on nets | fatal | warns NOT applied | x_dbg_net. V also warns `'set_property' expects at least one object`, because the net does not exist when the XDC is read for synthesis |
| CLOCK_DEDICATED_ROUTE FALSE on a net | fatal | warns NOT applied | x_cdr |

### Design and bitstream properties
| Property | Base | With xdc | Vivado |
|---|---|---|---|
| CFGBVS, CONFIG_VOLTAGE | warns "[current_design] isn't supported" | info: nothing to do | x_cfg against x_cfg_none: no configuration (CFG tile) feature differs. The decoded FASM differs only in LUT/routing of the two separate implementations |
| BITSTREAM.GENERAL.COMPRESS | warns | warns NOT applied (gap); **flow/bitstream_props.py**: MFWR compression, frames identical (strict model), 206036 bytes | V writes MFWR and multi-frame FDRI bursts; file 251335 against 2192134 bytes |
| BITSTREAM.CONFIG.CONFIGRATE 33 | warns | warns NOT applied (gap); **bitstream_props: COR0 0x02423fe5, as V** | V COR0 0x02003fe5 to 0x02423fe5 |
| BITSTREAM.CONFIG.SPI_BUSWIDTH 4 | warns | warns NOT applied (gap); **bitstream_props: BSPI + BSPI_READ, as V** | V adds BSPI 0x0000026b and CMD 0x12 (BSPI_READ) |
| BITSTREAM.CONFIG.USR_ACCESS | warns | warns NOT applied (gap); **bitstream_props: AXSS, as V** | V AXSS 0x12345678 |
| Pblock commands | existing pblock draft | unchanged | docs/phase8 |

## No-op check: existing designs are frame-identical when their XDC uses nothing new

`flow/xdc_noop.py` (results: `build/xdc_noop/noop.json`):

| Design | Comparison | Frames differing |
|---|---|---|
| blinky | router variant against xdc variant, same yosys JSON | 0 |
| rv_soc | the same | 0 |
| rv_pr native (static xor_a, xor_n, andn_n, add_n, rot_n, popc_n_taf, minmax_n_taf) | xdc variant (`build/xdc_noop/rv_pr/xdc/xdc/`) against `build/patched/rv_pr_native/router` | 0 in 7/7 |
| 20 test designs with no new or no effective constraint | base against xdc (x_mmcm_none, x_gen_div, x_cdc_none, x_cdc_maxdly, x_cfg*, x_io_drive, x_io_iob, x_iodly*, x_mcp_none, x_mcp_fromto, x_uncert, x_interm*, x_keep_cell, x_async_*) | 0 |

The new checks (MMCM cross-clock check, generated-clock period) change only the pass/fail report, not placement. This is also why x_mmcm_none and x_gen_div are frame-identical.

## xdc2: the seven gaps (2026-11-06)

`xdc2` is nextpnr variant `build/nextpnr-build/xdc2`. It consists of nextpnr-xdc-timing.patch plus docs/drafts/nextpnr-xdc2-constraints.patch. Yosys runs with the plugin of docs/drafts/yosys-xilinx-asyncreg.patch.

**How it ran:**
- `flow/xdc_audit.py --variant xdc2 --run` built 57 designs. 22 are new in `flow/xdc_designs.py`:
  - x_io_oiob, x_io_onoiob, x_io_iiob;
  - x_iodly_minmax, x_iodly_fall;
  - x_mcp_from, x_mcp_thru, x_fp_thru;
  - x_maxdly_cells, x_maxdly_dp;
  - x_clk_noncc, x_clk_nside, x_clk_noncc_cdr;
  - x_cfg_compress, _rate, _spi4, _usr, _startclk, _cycles, _spifall, _extclk, _nocrc.
- **Logs:** `build/xdc/<design>/xdc2/{yosys,nextpnr}.log`. The per-design summary of the final analysis is in `build/xdc/xdc2_results.txt`.
- **Vivado:** the references for the new designs ran on 2026-11-06 (Vivado 2025.2, `vivado/run_xdc.ps1`); comparison in `build/xdc2_scratch/postviv.out` and in "Remaining gaps" item 1.
- **Slack is not compared exactly:** as before, nextpnr's and Vivado's timers and placements differ, so slacks agree only roughly.

### 1. ASYNC_REG synchronizers
| | yosys | placement | Vivado |
|---|---|---|---|
| x_async_rtl (`(* ASYNC_REG = "TRUE" *)`) | base 1 SRL16E; xdc2 3 FDRE, ASYNC_REG + keep on the cells (`yosys_stat.txt`, `ASYNC_REG on 3 wire(s) (0 from the XDC), 3 flip-flop cell(s) kept.`) | `Constrained 1 ASYNC_REG chain(s) of 3 flip-flops to one slice each.` s1/s2/s3 at SLICE_X54Y90 A5FF/B5FF/C5FF (`x_async_rtl_routed.json`) | 3 FDRE ASYNC_REG=1 at SLICE_X34Y88 AFF/A5FF/B5FF |
| x_async_xdc (`set_property ASYNC_REG TRUE [get_cells s1_reg]` ...) | 3 FDRE (`3 from the XDC`) | same: one slice, SLICE_X54Y90 | same as above |
| x_async_none | 1 SRL16E in both (the pass is not run: no ASYNC_REG in the sources) | frames identical to base | 3 FDRE |

The XDC case works because the plugin reads the XDC (`xilinx_asyncreg -xdc`), as Vivado's synthesis does. nextpnr has no retiming, so nothing moves across the chain.

### 2. set_input_delay / set_output_delay
Final analysis, worst port (`build/xdc/<d>/xdc2/nextpnr.log`):

| Design | xdc2 input | xdc2 output | Vivado |
|---|---|---|---|
| x_iodly (in 7, out 7) | +3.92 ns (sw[2]) | **-7.82 ns** (ja[7]) | from_ports +2.607 (sw[3]); **to_ports -7.764** (ja[1]) |
| x_iodly_minmax (in max 4 / min 1, out max 3 / min -1) | +6.73 (sw[1]) | -3.82 (ja[7]) | from_ports +3.493 (sw[2], datapath 7.266); **to_ports -3.764** (ja[1]); 8 failing endpoints |
| x_iodly_fall (in -clock_fall 2, out 2) | +4.17 ns against the 5 ns half period (negedge -> posedge) | -2.82 | from_ports +2.826 against 5.000 (sw[1]); **to_ports -2.764** |
| x_iodly_none | no port line; frames identical to base | | +5.200 (reg to reg) |

**Breakdown of x_iodly's output path:**
- **Vivado:** clock latency 5.174, made of IBUF 1.489, route 1.967, BUFG 0.096 and route 1.623. Then FDRE clk-to-q 0.456, route 1.530 and OBUF 3.569. Against these, the output delay of 7 and an uncertainty of 0.035.
- **nextpnr:** the clock delay to the BUFG output is 3.35..3.42 ns, against Vivado's 3.551 at the same point. The per-register clock net comes on top with `with_clock_skew`.
- **Pad buffer delays:** they are not in the chipdb, so they come from a table of Vivado's values. Only LVCMOS33 input and LVCMOS33 12 mA SLOW output are filled in; other standards warn and get none.
- **Placement:** port paths now take part in placement: x_iodly differs from base in 179 frames.

### 3. IOB TRUE
| Design | xdc2 | Vivado |
|---|---|---|
| x_io_iob (IOB TRUE on led[0], led[1], btn[0]) | `IOB TRUE: 2 input and 0 output register(s) in the I/O logic`: q[0] and q[1] in ILOGIC, as Vivado. q[1] goes in because its Q drives led[1] (IOB TRUE) and its D comes from btn[1] | q_reg[0] ILOGIC_X0Y137, q_reg[1] ILOGIC_X0Y128 |
| x_io_iob decoded ILOGIC/OLOGIC features (`build/xdc/x_io_iob/{vivado.fasm,xdc2/decoded.fasm}`) | 105 of 109 lines identical. The 4 others are the clock leaf track: IOI_LEAF_GCLK0 here, GCLK5 in Vivado (a routing choice) | IDDR.IN_USE, IFF.DDR_CLK_EDGE.OPPOSITE_EDGE, SRTYPE.SYNC, ZINIT_Q1, ZINV_C, ZSRVAL_Q1: the same |
| x_io_iiob (btn[*]) | 4 input registers in ILOGIC | 4 input registers in ILOGIC (ILOGIC_X0Y137/128/127/126) as here; decoded IOI features 115 of 123 lines identical, the 8 others are the clock leaf track (GCLK0 here, GCLK5 in Vivado, a routing choice) |
| x_io_oiob (led[*], D from fabric) | 4 output registers in OLOGIC (ODDR SAME_EDGE, D1 = D2) | 4 output registers in OLOGIC (OUTFF). xdc2: decoded 119 of 123 lines identical; the 4 others were a bug, `OSERDES.DATA_RATE_OQ.DDR` where Vivado writes `.SDR` (same logic value, D1 = D2). **xdc3 (docs/drafts/nextpnr-ologic-iob-sdr): 123 of 123 identical** |
| x_io_noiob, x_io_onoiob | nothing moved; x_io_noiob frames identical to base | no packing without IOB TRUE (x_io_noiob) |

### 4. set_max_delay, set_min_delay, set_multicycle_path -from/-through, set_false_path -through
| Design | xdc2 (final analysis) | Vivado |
|---|---|---|
| x_mcp_fromto (`-setup 2 -from s_reg -to dq_reg`) | applied: requirement 20.00 ns, slack +5.34. In xdc this `-from` was "ignoring" | MultiCycle Path Setup -end 2, requirement 20.000 |
| x_mcp_from (`-from s_reg[*]` only) | requirement 20.00, slack +4.99; every register path starts at s, so no Fmax line remains | requirement 20.000 (MultiCycle Setup -end 2) as here; slack -1.209, datapath 21.225 on Vivado's placement |
| x_mcp_thru (`-through dq_reg[*]/D`) | requirement 20.00, slack +5.35 | requirement 20.000 as here; slack -1.209 |
| x_fp_thru (`set_false_path -from s_reg -through dq_reg/D`) | the s -> dq paths are gone: Fmax 436.68 MHz, the same as x_mcp_thru without the exception pair | the s -> dq paths are gone as here; worst path s_reg -> s_reg, slack +7.409 |
| x_cdc_maxdly (`-datapath_only 5 -from clk_a -to clk_b`) | `Max delay for set_max_delay -datapath_only (line 13) ...: 7.42 ns (FAIL at requirement 5.00 ns, slack -2.42 ns)`. Before, this pair was only listed | MaxDelay 5.000 -datapath_only, slack -4.730 (datapath 9.792) |
| x_maxdly_cells (the same on `-from a_reg[*] -to bq_reg[*]`) | 7.42 ns, FAIL at 5.00, slack -2.42 | FAIL at 5.000 (`-datapath_only`) as here; slack -4.730, datapath 9.792, 16 failing endpoints |
| x_maxdly_dp (`set_max_delay 6 -to dq_reg[*]`) | FAIL at 6.00, slack -9.23 | FAIL at 6.000 as here; slack -15.203, datapath 21.203 |

All exception designs build and route.

### 5. Hold between related clocks, uncertainty, jitter
| Design | xdc2 | Vivado |
|---|---|---|
| x_mmcm_none (c1 100 MHz -> c2 200 MHz, one MMCM) | `Min delay (hold) for posedge c1 -> posedge c2 ...: 1.32 ns (PASS at requirement 0.00 ns, slack 1.32 ns)`. Before, this pair had no hold check. Frames identical to base | inter-clock WHS c1_mmcm -> c2_mmcm +0.311 |
| x_mmcm_mcp | hold slack +1.38 | +0.224 |
| x_uncert (`set_clock_uncertainty 1.000`) | Fmax 64.41 MHz, against 68.85 for the same placement without it. 1000/64.41 - 1000/68.85 = 1.00 ns, the uncertainty. Frames identical to base, because it is report only | uncertainty 1.035 (user 1.000 + jitter 0.035); WNS -12.227 against -10.739 in x_mcp_none |

The jitter model (sqrt(TSJ² + TIJ²)/2) is applied only when the XDC has set_input_jitter or set_system_jitter. No test design sets them, so it is not checked against Vivado.

### 6. BITSTREAM.* (flow/bitstream_props.py, a post-pass on xc7frames2bit's .bit)
- **x_cfg** (COMPRESS + CONFIGRATE 33 + SPI_BUSWIDTH 4 + USR_ACCESS) against Vivado's x_cfg.bit, register writes other than frames and CRC values (`--vivado`):
  - COR0 0x02423fe5, BSPI 0x0000026b + CMD BSPI_READ, AXSS 0x12345678, and the CRC words in place of RCRC: as Vivado.
  - MASK/CTL1 0x00001000 before the frames and CTL1 cleared after LFRM: x_cfg_compress shows it belongs to COMPRESS; written since 2026-11-06.
- **CRC alone, on x_cfg_none:** the packet sequence is identical to Vivado's x_cfg_none (546/546 packets). The second CRC word matches Vivado's value, 0xe3ad7ea5.
- **Compression:** in a row, the zero frames are written once and copied with MFWR. A frame that recurs later ends its FDRI burst and is copied too. A burst not followed by MFW gets one pad frame. This is the packet vocabulary of Vivado's own stream.
  - **Check:** bitparse in the strict (frame-buffer) model gives 0 frames differing from the uncompressed bitstream (x_cfg_none, x_cfg). The non-strict model gives 2; on Vivado's own compressed x_cfg.bit the two models also differ by 2 frames.
  - **Size:** 238,779 bytes for x_cfg_compress since the BRAM NOOP fix (206,036 before), against 2,192,170 uncompressed and Vivado's 251,335 for its own placement. On Vivado's frames the stream is word-identical to Vivado's (below).
  - **prjxray cannot decode it:** `bitread` cannot check a compressed bitstream. It decodes only the 90 FDRI-written frames and ignores MFWR (x_cfg_none_c.bit). This also applies to Vivado's compressed bitstreams.
- **Which values are implemented:** CONFIGRATE 33, SPI_BUSWIDTH 4 and USR_ACCESS are measured (x_cfg). The STARTUP cycle fields and STARTUPCLK are coded from UG470's COR0 layout; the per-setting designs x_cfg_* give register writes identical to Vivado's for rate, spi4, usr, startclk, cycles and nocrc (2026-11-06).
- **Fixed 2026-11-06 (item 8 of docs/RESUME.md), measured on Vivado's x_cfg_* bitstreams:**
  - COMPRESS: `MASK 0x00001000 / CTL1 0x00001000` in place of the MASK/CTL1 0 pair before the frames, and `MASK 0x00001000 / CTL1 0x00000000` right after `CMD LFRM`.
  - EXTMASTERCCLK_EN DIV-1: COR0 ECLK_EN (bit 26) set and OSCFSEL = 0x30, so 0x02003fe5 -> 0x06603fe5. Only DIV-1 is measured; other dividers are reported as unsupported.
  - SPI_FALL_EDGE YES: `CMD 0x13` is FALL_EDGE (UG470 command table, "switch to negative-edge clocking"); Vivado writes it between IDCODE and `CMD SWITCH`, and so does bitstream_props now.
  - Length: Vivado takes the words a setting adds (BSPI + BSPI_READ + NOOP, AXSS, FALL_EDGE) off the trailing NOOPs, so the file keeps its size; bitstream_props does the same.
  - Compression: block-RAM MFWR copies get 8 NOOPs after `MFWR x8` and after each `MFWR x4` (the check for a BRAM row compared a block name with a number and never matched), and no extra 8 NOOPs at the end when the last copy already has them. Frames are taken from the strict (frame-buffer) model.
- **Word-identical check (`--vivado`, key `compare.on_vivado_frames`):** the same settings applied to the xc7frames2bit template, with Vivado's own frames (its FDRI data, or for COMPRESS its frames read in the strict model and compressed by bitstream_props), give Vivado's bitstream word for word, CRC words included: 547990/547990 words for x_cfg_rate, _spi4, _usr, _startclk, _cycles, _spifall, _extclk, _nocrc and 62788/62788 for x_cfg_compress and x_cfg (results `build/xdc2_bitprops_v2/<d>.json`; re-run after the WIP checkpoint on the xdc3 bitstreams, same result: `build/xdc_bitprops_v3/<d>.json`). On our own frames the register writes of the 8 uncompressed designs are identical to Vivado's (packets identical too); for the 2 compressed ones the MASK/CTL1 writes now match (`only_vivado` and `only_open` empty), and the number of WCFG/MFW commands differs only because the frames (our placement) differ. Strict frames differ from the uncompressed input: 0 in all 10.

### 7. Clock placement DRC (rule_gclkio_bufg)
| Design | xdc2 | Vivado |
|---|---|---|
| x_loc (E3, BUFGCTRL_X0Y5 LOC) | ERROR `... the BUFGCTRL is in the bottom half of the device and the pin in the top half` | Place 30-574, same rule, same reason |
| x_loc2 (BUFGCTRL_X0Y20) | accepted | accepted |
| all designs with E3/D15 clocks (MRCC) | accepted | accepted |
| x_clk_noncc (B11, IO_L4P_T0_15) | ERROR, not clock capable | ERROR at place_design (Placer could not place all instances), as here |
| x_clk_nside (A8, IO_L12N_T1_MRCC_16) | ERROR; the N-side pad does not reach the clock wire, so it reports "not clock capable" | ERROR at place_design, as here |
| x_clk_noncc_cdr (B11 + CLOCK_DEDICATED_ROUTE FALSE [get_nets clk_ibuf]) | warning, builds | builds (rc 0), as here |

### No-op check for xdc2
| Check | Result |
|---|---|
| blinky, rv_soc: router variant against xdc2, same JSON (`flow/xdc_noop.py`) | 0 frames differ |
| rv_pr native, 7 statics: xdc2 (`build/xdc_noop/rv_pr/xdc2/`) against `build/patched/rv_pr_native/router` | 0 in 7/7 |
| yosys: blinky and rv_soc, plain `synth_xilinx` against the flow's script, against the split `-run :coarse; xilinx_asyncreg; -run coarse:`, and against the split alone (`flow/xdc_noop.py --yosys`, `build/xdc_noop/yosys/`) | JSON byte-identical in all three |
| xdc against xdc2 frames on the 34 earlier test designs | identical on 28 |

- **Where xdc and xdc2 differ:** the other 6 are exactly those where xdc2 applies something xdc did not: x_async_rtl/xdc 82, x_cdc_maxdly 196, x_io_iob 187, x_iodly 179 and x_mcp_fromto 224 frames.
- **The pass interned names in a first version:** that version changed rv_soc's netlist even when it found nothing. It now interns nothing unless it sets an attribute. The flow also runs it only when "ASYNC_REG" appears in the RTL or the XDC (`flow/gap_build.py`).

## Vivado's timer on our placement (2026-11-06)

`flow/xdc_xtime.py --run` writes three things for each design to `build/xdc_xtime/src/<d>_xdc3/`: the yosys netlist as EDIF with Vivado register names, the XDC, and nextpnr's placement (xdc3 variant).

`vivado/build_xdctime.tcl` reads them. Run it with `vivado/run_qor.ps1 -Tag xdc_xtime -Script build_xdctime.tcl -SrcRel build\xdc_xtime\src -Run`. It:
- places every netlist cell where nextpnr put it, with LOC and BEL fixed;
- lets place_design add only the cells nextpnr's netlist does not have;
- routes with Vivado's router.

**Outputs:** `C:\Users\finnf\open-dfx-xc7-vivado\build\xdc_xtime\<d>_xdc3\`, holding `pairs.txt`, `in_setup*.rpt`, `in_hold*.rpt`, `out_setup*.rpt` and `place_missed.txt`. `flow/xdc_xtime.py --collect` compares them with nextpnr's results.

**What is ours and what is Vivado's:**
- Every flip-flop, LUT and CARRY4 of the netlist got our site and BEL.
- The only cells not placed from our placement:
  - the pass-through LUTs that nextpnr's packer adds in front of carry inputs. They are named `...$LUT$...`, are not in the netlist, and number 24 to 122 per design;
  - in the x_iodly designs, 4 INV cells.
- The routing is Vivado's.

### Exceptions on one placement
Which timer is behind each column:
- **nextpnr:** nextpnr's own timer, final analysis in `build/xdc/<d>/xdc3/nextpnr.log`.
- **Vivado on ours:** Vivado 2025.2's timer on our placement.
- **Vivado own:** Vivado's timer on its own implementation.

| Design | Requirement (all three) | nextpnr | Vivado on ours (datapath) | Vivado own (datapath) |
|---|---|---|---|---|
| x_mcp_from | 20.000 (MultiCycle -end 2) | +4.99 | +2.711 (17.284) | -1.209 (21.225) |
| x_mcp_thru | 20.000 (MultiCycle -end 2) | +5.35 | +2.499 (17.511) | -1.209 (21.225) |
| x_maxdly_cells | 5.000 (-datapath_only) | -2.42 | -3.534 (8.643) | -4.730 (9.792) |
| x_maxdly_dp | 6.000 (MaxDelay) | -9.23 | -11.173 (17.161) | -15.203 (21.203) |

**Findings:**
- **Same exception handling:** on the same placement, both timers apply each exception with the same requirement and cut the same paths.
- **The slack gap has two parts:**
  - **Placement:** Vivado's own build is 1.2 to 4.0 ns worse than Vivado's timer on our placement.
  - **Timer:** on the same cells, nextpnr is 1.1 to 2.9 ns more optimistic than Vivado. The paths are carry chains with 8.6 to 17.5 ns of data path. This is nextpnr's general delay under-estimate (route-timing calibration, docs/RESUME.md item 1), not an exception bug.

### Port paths on one placement: why our input slack looked optimistic
Which timer is behind each column:
- **nextpnr:** the xdc3 final analysis (`build/xdc_iodly_dbg/<d>/report.json`, a rerun with `--report-paths 12` whose FASM is identical to `build/xdc/<d>/xdc3`).
- **Vivado on ours:** Vivado 2025.2 on that placement.
- **Vivado own:** Vivado's timer on its own implementation.

| Design | Check | nextpnr | Vivado on ours | Vivado own |
|---|---|---|---|---|
| x_iodly (in 7, out 7) | input setup | +3.92 (sw[2]) | +3.354 (sw[2], **Fast corner**, datapath 1.187) | +2.607 |
| | output setup | -7.82 | -8.852 (Slow) | -7.764 |
| x_iodly_minmax (in max 4 / min 1) | input setup | +6.73 (sw[1]); sw[2] +6.92 | +3.969 (sw[2], Slow, datapath 6.989 = IBUF 1.515 + **route 5.474**) | +3.493 |
| | input hold | **-0.10 to -0.63 on all 4 inputs (FAIL)** | +1.028 | |
| | output setup | -3.82 | -4.852 (Slow) | -3.764 |
| x_iodly_fall (in -clock_fall 2) | input setup | +4.17 | +3.310 (sw[0], **Fast corner**, datapath 1.236) | +2.826 |
| | output setup | -2.82 | -3.852 (Slow) | -2.764 |

The input gap has three causes, measured on the same cells:
1. **Vivado fixes hold in the router, and the open flow does not.**
   - In x_iodly_minmax, `-min 1` makes all four input registers fail hold in nextpnr's own analysis (-0.10 to -0.63 ns). nextpnr reports this but does not repair it.
   - Vivado's router repairs it with a detour on the input net: sw[2] to r_reg[2] takes 5.474 ns of route at the Slow corner. In x_iodly, the same pad to the neighbouring SLICE_X1Y106 takes 0.716 ns at the Fast corner.
   - That detour is the 6.989 ns data path, and Vivado pays for it in setup slack.
   - So the +6.73 was not wrong for the routing we have. Our build fails input hold, and Vivado's build does not.
2. **Vivado checks setup at both process corners. nextpnr checks one.**
   - For x_iodly and x_iodly_fall, Vivado's worst input setup path is at the Fast corner. The capture clock's insertion delay shrinks from 5.05 to 1.59 ns, more than the short data path does (IBUF 1.515 to 0.471).
   - nextpnr has a single corner. Its routing delays have min = max (the hold reports use the same route values).
   - prjxray-db has fast_min/fast_max/slow_min/slow_max for every pip (`tile_type_*.json`). A Fast-corner check of port paths needs those values carried into the chipdb.
3. **The clock insertion delay is too short at the Slow corner.**
   - Breakdown of the x_iodly_minmax output path on the same cells (Vivado, then nextpnr):

     | Element | Vivado | nextpnr |
     |---|---|---|
     | clock pad to BUFG output | 3.551 | 3.424 |
     | BUFG to register (clock leaf route) | 1.620 | 0.896 |
     | clk-to-q | 0.456 | 0.35 |
     | data route | 2.683 | 2.585 |
     | OBUF at K16 | 3.506 | 3.569 (table value) |
     | uncertainty (system jitter) | 0.035 | 0 |

   - Sum: nextpnr is 1.03 ns optimistic on outputs, mostly from the clock leaf route.
   - That missing 0.72 ns of clock delay makes inputs about 0.7 ns *pessimistic* at the Slow corner, which hides part of causes 1 and 2.
   - The earlier "outputs agree within 0.06 ns" came from comparing two different placements. On one placement, outputs are 1.03 ns optimistic.

**Check with one corner at a time.** `vivado/build_xdctime.tcl` sets `config_timing_corners -delay_type none` on the other corner and writes `in_setup_{slow,fast}.rpt`, `in_hold_*` and `out_setup_*`.

At the Slow corner alone, which is the corner nextpnr models, Vivado's input setup slack on our placement is:
- x_iodly: +4.891 (IBUF 1.515, route 1.552), against nextpnr's +3.92 (IBUF 1.489, route 1.742).
- x_iodly_fall: +4.873, against nextpnr's +4.17.

So at one corner nextpnr is 0.70 to 0.97 ns *pessimistic* on inputs, as cause 3 predicts. What made it look optimistic was only cause 2: Vivado's Fast corner gives +3.354 and +3.310.

In x_iodly_minmax both corners carry the hold-repair detour:

| Corner | Input setup slack | Route | Input hold slack |
|---|---|---|---|
| Slow | +3.969 | 5.474 | +1.028 |
| Fast | +4.520 | 2.550 | +1.098 |

## xdc4: latency, jitter, KEEP/DONT_TOUCH/MARK_DEBUG, DIFF_TERM, pad delays (2026-11-06, in progress)

`xdc4` is nextpnr variant `build/nextpnr-build/xdc4`: the xdc3 tree (router stack + xdc-timing + xdc2 +
ologic-iob-sdr) plus `docs/drafts/nextpnr-diff-term.patch` plus `docs/drafts/nextpnr-xdc4-constraints.patch`
(draft). In `flow/xdc_audit.py` the variant also runs `flow/xdc_keep.py` in yosys. 14 new designs in
`flow/xdc_designs.py`: x_lat_src, x_lat_net, x_lat_early, x_lat_xsrc, x_jit_in, x_jit_sys, x_jit_both, x_jit_two,
x_keep_none, x_keep_dt, x_keep_k, x_dbg_rtl, x_pad_a, x_pad_b. Vivado script `vivado/build_xdc4.tcl`
(build_xdc.tcl plus `pad_arcs.txt`, the Slow/Fast min/max rise/fall delay of every pad buffer's timing arc, and
per-port path reports), run in batches of at most ~20 min through `vivado/run_polite.sh`.

**Status of the Vivado references:** queued, not run yet (the Vivado slot was taken by higher-priority agents
for the whole session). Every "vs Vivado" cell below that says *pending* is unmeasured.

### KEEP / DONT_TOUCH / MARK_DEBUG
Vivado reads the XDC before synthesis; nextpnr reads it after. `flow/xdc_keep.py` turns
`set_property KEEP|DONT_TOUCH|MARK_DEBUG true [get_cells|get_nets ...]` (Vivado names: `a/b/q_reg[3]` is the
flattened yosys wire `a.b.q`) and RTL `(* mark_debug = "true" *)` / `(* dont_touch = "true" *)` into yosys
`setattr -set keep 1` on the wire and the cells driving it, run on the flattened design before synth_xilinx's
optimisation (`synth_xilinx -run :prepare; proc; flatten; <keep>; synth_xilinx -run prepare:`). Only when the
XDC or RTL asks for one of them; otherwise the yosys script is unchanged. nextpnr's warning now says the flow
applied it.

| Design | xdc3 (no pass) | xdc4 | Vivado |
|---|---|---|---|
| x_keep_cell (DONT_TOUCH + KEEP on dq_reg[*], only dq[15:12] used) | 20 FDRE | **32 FDRE** | 32 FDRE (`build\xdc\x_keep_cell\synth_cells.txt`) |
| x_keep_dt (DONT_TOUCH on dq_reg[*]; dd_reg is a duplicate of dq_reg) | 0 FDRE (LEDs constant, all optimised away) | 32 FDRE | pending |
| x_keep_k (KEEP on dd_reg[*]) | 0 FDRE | 32 FDRE | pending |
| x_dbg_rtl (`(* mark_debug *)` on dq) | 0 FDRE | 32 FDRE | pending |

(`build/xdc/<d>/xdc4/yosys_stat.txt`.) x_keep_none's LEDs are a constant (dq ^ dd of two equal registers), so
it has no flip-flop left in either flow; it is the control. MARK_DEBUG here only keeps the net, which is what
Vivado's synthesis does with it; inserting a debug core is `flow/mark_debug.py` (LiteScope), not yet called by
`ofx build`.

### DIFF_TERM
With `nextpnr-diff-term.patch` in the stack, the XDC reader now counts DIFF_TERM as applied (no "NOT applied"
warning). gap design dt_xdc (`build/xdc4_dt/dt_xdc/`): the IOB FASM lines are identical to the `ofx-prim`
build's (diff empty), including `LVDS_25.IN_ONLY_DIFF_TERM` on both terminated receivers, and ofx-prim's
dt_xdc was 0 / 0 against Vivado's decoded bitstream (gap-vivado.md G2). Frames need the db segbits of
`docs/drafts/prjxray-db-diff-term.segbits` (as for ofx-prim).

### set_clock_latency
The draft implements Vivado's documented rules; whether Vivado's numbers agree is pending (x_lat_*):
- network latency (no `-source`): no effect, with an info line, since every clock is propagated after placement
  and Vivado ignores network latency on a propagated clock;
- `-source` with one value: on the clock's own paths (registers and the ports timed against it) it is on both the
  launch and the capture side and cancels, so slack does not change;
- `-source -early/-late` (or `-min/-max`): the spread late - early is charged to setup (late launch, early
  capture) and to hold (early launch, late capture), like an uncertainty;
- between two clocks of one primary (MMCM outputs, generated clocks), the clock's edges move by the latency (its
  waveform offset), and clocks generated from it move with it.
A first build had the latency lines parsed but never applied (the post-pack function returned early when no
other clock setting existed); fixed, re-run pending.

### Jitter (set_input_jitter, set_system_jitter)
nextpnr (xdc3 = xdc4 here, nextpnr's timer, same placement as x_mcp_none at 68.85 MHz): the period lost is
1000/Fmax - 1000/68.85:

| Design | nextpnr Fmax | uncertainty taken | sqrt(TSJ^2 + TIJ^2)/2, TSJ = sqrt(2) x system jitter, TIJ = rss of both clocks' input jitter | Vivado |
|---|---|---|---|---|
| x_jit_in (input jitter 0.3) | 67.84 | 0.216 | 0.215 (system jitter 0.05, Vivado's default) | pending |
| x_jit_sys (system jitter 0.2) | 68.18 | 0.143 | 0.141 | pending |
| x_jit_both | 67.66 | 0.256 | 0.255 | pending |

Vivado's own report of x_mcp_none shows the default term: `Clock Uncertainty: 0.035ns ((TSJ^2 + TIJ^2)^1/2 + DJ) / 2
+ PE`, which is the formula above with system jitter 0.05; nextpnr adds no jitter at all unless the XDC sets one,
so on every other design it is 0.035 ns optimistic against Vivado. MMCM discrete jitter (DJ) and phase error (PE)
are not modelled.

### Pad buffer delays for other I/O standards
x_pad_a / x_pad_b put registered inputs and outputs on LVCMOS33 (4/8/12/16 mA x SLOW/FAST), LVTTL, LVCMOS25,
LVCMOS18 (4-24 mA), LVCMOS15, LVCMOS12, SSTL15, SSTL135, SSTL18_I, HSTL_I, HSTL_I_18, HSUL_12, LVDS_25 and
DIFF_SSTL15/DIFF_SSTL135 (in and out), each bank at its own VCCO, INTERNAL_VREF for the referenced standards.
Both build with xdc3 (`build/xdc/x_pad_{a,b}/xdc3/`); nextpnr warns "no ... buffer delay is known" for every
standard but LVCMOS33 input and LVCMOS33/12/SLOW output, as before. `flow/xdc_pads.py` turns Vivado's
`pad_arcs.txt` into the table for the draft (keys as nextpnr builds them); pending the Vivado run.

## Remaining gaps, in order of importance
1. **Vivado references for the 22 new designs: done 2026-11-06** (`build/xdc2_scratch/postviv.out`). They agree on every exception (requirement and which paths are cut), every clock DRC case and the IOB packing. The differences found, and where each stands (re-verified after WIP checkpoint 791d27d):
   - **OLOGIC SDR bug:** fixed by docs/drafts/nextpnr-ologic-iob-sdr (variant xdc3).
     - x_io_oiob: 123/123 IOI lines are now as Vivado.
     - The other 53 XDC designs give identical frames.
     - The no-op check passes on blinky, rv_soc and rv_pr (7/7).
   - **BITSTREAM words:** fixed in flow/bitstream_props.py.
     - CTL1 bit 12 with COMPRESS, COR0 0x06603fe5 for EXTMASTERCCLK_EN DIV-1, and CMD 0x13 for SPI_FALL_EDGE.
     - With Vivado's own frames, all 10 x_cfg_* settings give Vivado's .bit word for word.
     - On our frames, the 8 uncompressed settings give the same packets as Vivado (`build/xdc_bitprops_v3/`).
   - **Input-port slack:** cause found on one placement ("Port paths on one placement" above). It has three parts:
     - Vivado's router fixes hold on inputs, and ours does not. In x_iodly_minmax our build fails input hold by 0.10 to 0.63 ns.
     - Vivado also checks setup at the Fast corner, and nextpnr has one corner.
     - Our clock leaf delay is 0.72 ns short.
     - **Still to fix:**
       - a hold-repair step in routing;
       - a Fast-corner check for port paths, using prjxray's fast pip delays in the chipdb;
       - the clock leaf calibration (route-timing calibration).
     - **Output slack:** on one placement it is 1.03 ns optimistic, not within 0.06 ns as first reported.
     - **Fast corner:** docs/drafts/nextpnr-timing-corners (`-o timing-corners`) reports both corners. On one placement its worst input setup is 3.306 vs Vivado's 3.354 ns (x_iodly) and 3.420 vs 3.310 (x_iodly_fall).
   - **Exception slacks:** compared on one placement ("Exceptions on one placement" above).
     - Same requirements and same cut paths in both timers.
     - nextpnr is 1.1 to 2.9 ns more optimistic on the same cells. That is the general delay calibration, not the exceptions.
2. **Pad buffer delays** for standards other than LVCMOS33. They are not in prjxray. The table needs one Vivado run per standard and drive.
3. **BITSTREAM values** beyond the measured ones. Compression is valid but not word-identical to Vivado's ordering.
4. **One exception per path:** each domain pair takes one setup and one hold exception, and an endpoint or startpoint takes one exception tag. Several `-through` lists are taken as one (OR).
   - **Not done:** `-from/-to [get_ports]`, `set_multicycle_path -start`, -hold moves, and uncertainty `-from/-to`.
5. **Jitter:** MMCM output jitter, discrete jitter and phase error are not modelled.
6. **DIFF_TERM bits** (gap-vivado.md G2).
7. **Clock names in reports** are still the buffered net names.
