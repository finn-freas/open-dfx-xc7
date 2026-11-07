# Draft: nextpnr-xdc2-constraints (openXC7/nextpnr, on nextpnr-xdc-timing)

Not posted anywhere. Patch: `docs/drafts/nextpnr-xdc2-constraints.patch`. It is a `git diff` of `build/src/nextpnr-xdc2` against router-region e62fafd1 plus nextpnr-xdc-timing.patch: 13 files, +1515/-56. Built as variant `xdc2`:

```bash
VARIANT=xdc2 BASE_REV=e62fafd1 PATCHES="nextpnr-xdc-timing.patch nextpnr-xdc2-constraints.patch" DRY_RUN=0 JOBS=4 \
  bash toolchain/buildenv/build_nextpnr_variant.sh
```

- **Build:** log `build/nextpnr-build/xdc2.build.log`. The only compiler warning is the existing `xilinx.cc` `-Wsign-compare`.
- **Chipdb:** no `gen/` file and no `constids.inc` change, so the nightly chipdb still fits.
- **Patch check:** both patches apply to a fresh e62fafd1 checkout (`git apply --check`).
- **Style:** there is no clang-format here. Added lines were checked by hand against the 120-column limit.

## What it does

### 1. ASYNC_REG (packer, placer)
- `pack_async_reg_chains` runs after `pack_ffs`, before `pack_lutffs`. It finds the flip-flops with ASYNC_REG = TRUE: on the cell (from yosys, see yosys-xilinx-asyncreg, or from the XDC) or on the net they drive (an RTL attribute).
- A chain is a run of such flip-flops where each D is the previous Q, with the same clock, enable, set/reset and polarity. Each chain becomes a cluster: AFF..DFF of one slice, rooted at the first stage. A longer chain is split into groups of four.
- `getClusterPlacement` refuses a root bel that would push a stage into the other slice of the tile.
- The XDC property `ASYNC_REG` is applied (it was "NOT applied").

### 2. set_input_delay / set_output_delay (timer)
- **XDC reader:** takes `-clock`, `-clock_fall`, `-max`, `-min` and `-add_delay`. It writes `NEXTPNR_INPUT_DELAY` / `NEXTPNR_OUTPUT_DELAY = "<clock> <edge> <min> <max>"` on the port cell.
- **Startpoints and endpoints:** the timer (`setup_io_delays`) makes the input buffer's output a startpoint of the clock's domain, and the output buffer's input an endpoint.
  - Arrival at an input buffer = input delay + buffer delay − the capture clock's delay from its pad.
  - Required at an output buffer = −(output delay + buffer delay + the launch clock's delay from its pad).
  - Min values go to hold.
- **Clock delay from the pad** (`clock_source_latency`): the clock net is walked back through cells with a timing arc, adding their delays and routing.
  - With `with_clock_skew` (the final analysis) the register's own clock-net delay is added per register, as before. Without it, the min/max over the net's sinks is used.
- **Report:** a path report gets `in-delay`, `out-delay` and `clk-latency` segments. The final report prints, per clock pair, `Max delay for set_input_delay|set_output_delay <a> -> <b> (worst at <port>, clock delay from its pad <min>..<max> ns): <d> ns (PASS|FAIL at requirement <r> ns, slack <s> ns)`.
- **Missing delays in the chipdb:** the chipdb has no delays for pad buffers or BUFGCTRL, so `XilinxImpl::getCellDelay` supplies them.
  - BUFGCTRL I→O is 0.026/0.096 ns, from prjxray `CLK_BUFG_*.sdf`.
  - Pad buffers come from a table of the values Vivado reports for xc7a35tcsg324-1: IBUF LVCMOS33 1.489 ns and OBUF LVCMOS33 12 mA SLOW 3.569 ns (x_iodly `paths.rpt`, Prop_ibuf_I_O, Prop_obuf_I_O).
  - Any other standard gets a warning and no buffer delay.
  - These arcs are only used by the port-path code: the cells' ports keep their timing class (TMG_IGNORE), so no other path changes.

### 3. IOB TRUE (packer, FASM)
- `pack_iob_registers` runs before `pack_iologic`. It takes a register with IOB TRUE on itself, on its input port, or on the port its Q drives.
  - If its D comes from an input buffer alone, it becomes the ILOGIC IFF: an IDDR in OPPOSITE_EDGE mode, Q1 = Q, INIT_Q1 = INIT, INIT_Q2 = 1, SRTYPE SYNC for FDRE/FDSE and ASYNC for FDCE/FDPE.
  - Otherwise, if its Q drives an output buffer alone, it becomes the OLOGIC OUTFF: an ODDR in SAME_EDGE mode with D1 = D2.
  - The input side wins when both apply, as Vivado chose for x_io_iob q_reg[1].
- `pack_iologic` then places it as it places an IDDR/ODDR.
- FASM: a register in the IFF (`X_IOB_SDR`) gets ZSRVAL_Q1 only, as Vivado writes; an IDDR writes Q1..Q4.
- A port with IOB TRUE and no register next to it gets a warning.

### 4. Path exceptions (timer, XDC reader)
- **Exception list:** `set_false_path` (two-sided cells, or `-through`), `set_multicycle_path` with `-from` or `-through`, `set_max_delay [-datapath_only]` and `set_min_delay` go to `ctx->timing_exceptions`. These are TimingException: from/to cells, through pins, from/to clocks.
  - Cells are resolved at XDC time and pins after packing (C→CK, R/S/CLR/PRE→SR, I<n>→A<n+1>). Clocks are resolved with the clock exceptions.
  - The earlier forms (multicycle `-to`, false path on one side) are unchanged.
- **Tags:** the timer tags its clock domains (ClockDomainKey::tag).
  - A startpoint in an exception's `-from` launches in a tagged domain.
  - A `-through` pin moves an arrival into the exception's domain.
  - An endpoint in a `-to` captures in a tagged domain.
  - Each domain pair takes at most one setup and one hold exception, by Vivado's precedence: false path, then max/min delay, then multicycle.
- **Requirement:** a max delay replaces the pair's requirement. A multicycle path adds N-1 capture periods. `-datapath_only` drops clock skew, uncertainty and the hold check.
- **Reports:** exception pairs are left out of the Fmax of their clock and reported as `Max delay for <exception> (line N) ...`.
  - Their criticality is the path delay over the requirement, so placement sees the relaxed or tightened budget.
  - A design without exceptions has no tagged domain, and nothing changes.

### 5. Hold between related clocks; uncertainty and jitter (timer)
- **Hold between related clocks:** pairs of clocks of one primary get a hold check against the hold relationship. That is the latest of the capture edge before each setup capture edge, and the setup capture edge against the next launch edge (`clock_hold_relationship`). Before, only one clock with itself was checked.
  - A summary line `Min delay (hold) for <a> -> <b> ...` is printed for these pairs and for set_min_delay.
- **Uncertainty:** `set_clock_uncertainty [-setup|-hold] <ns> <clocks>` is taken off the setup requirement, and added to the hold requirement, of paths the clock captures. It enters Fmax as extra path delay.
- **Jitter:** `set_input_jitter` and `set_system_jitter` turn on Vivado's jitter term sqrt(TSJ² + TIJ²)/2, with a system jitter of 0.050 ns unless set.
  - It is applied only when the XDC sets a jitter, so Fmax of other designs does not move.
  - MMCM output jitter, discrete jitter and phase error are not modelled.

### 7. Clock placement DRC (Vivado Place 30-574, rule_gclkio_bufg)
- `check_clock_placement` runs in `postPlace`. An input pad that drives a BUFGCTRL straight through its buffer must meet three conditions:
  - It is clock capable.
  - It is the P side of its pair (the IOB33M/IOB18M bel).
  - It is in the BUFGCTRL's half of the device. The split is between the global sites BUFGCTRL_X0Y15 and X0Y16.
- **No pin functions in the chipdb:** the chipdb's pad function strings are empty (the generator passes ""). So "clock capable" means the buffer reaches, within 12 pips, the clock wire of its own I/O tile that continues into the clock management tile. That node is named HCLK_CMT_CCIO*, *_I2GCLK_* or HCLK_IOI_I2IOCLK_*; only the pad's own ILOGIC drives it, and in the other I/O tiles it is a stub. Checked: E3 and D15 (MRCC) pass; B11 (not CC) and A8 (N side) are refused.
- **Severity:** a violation is an error, as in Vivado. `CLOCK_DEDICATED_ROUTE FALSE` on the net makes it a warning; that property is now applied to nets. `--force` continues anyway.

## Evidence
docs/xdc-coverage.md, section "xdc2", with log paths.
