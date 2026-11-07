# Draft: nextpnr-xdc-timing (openXC7/nextpnr, on router-region e62fafd1)

Not posted anywhere. Patch: `docs/drafts/nextpnr-xdc-timing.patch` (`git diff` of `build/src/nextpnr-xdc`). Built as variant `xdc`:

```bash
VARIANT=xdc BASE_REV=e62fafd1 PATCHES=nextpnr-xdc-timing.patch DRY_RUN=0 JOBS=4 bash toolchain/buildenv/build_nextpnr_variant.sh
```

`build_nextpnr_variant.sh` now takes `JOBS` (default 8, as before). The patch applies to the router-region stack because rv_pr native uses that variant. It touches no `gen/` file and no `constids.inc`, so the nightly chipdb still fits. Build log: `build/nextpnr-build/xdc.build.log`. The only compiler warning is the existing `xilinx.cc` `-Wsign-compare`.

## What it does

Timer, in `common/kernel`:
- `ClockConstraint` gets `name`, `master` (the primary clock it is generated from), `offset` (the first rising edge) and `false_path_to` (capture clock names).
- **Clocks of one primary are timed against each other.** This covers the outputs of one MMCM/PLL, a generated clock and its source, and a BUFR divide. The setup requirement is the shortest launch-to-next-capture edge time over the common period, at most 1000 launch edges. `set_multicycle_path -setup N` on the endpoint adds N-1 capture periods.
  - The final report prints `Max delay for <launch> -> <capture>: <d> ns (PASS|FAIL at requirement <r> ns, slack <s> ns)`.
  - A FAIL is a non-fatal error, or a warning with `--timing-allow-fail` / `--ignore-rel-clk`, like the existing related-clock check.
  - Before the patch these paths were only listed as "cross-domain" and never checked.
- **Clock exceptions:** a launch/capture pair in `false_path_to` gets no criticality, no cross-domain report and no hold report.
- **Cell exceptions:** cells tagged `NEXTPNR_FALSE_PATH_TO` / `_FROM` are not endpoints or startpoints.
- Criticality of non-excepted paths is unchanged. The period still only enters the pass/fail check, as before (docs/qor-vivado.md Finding 2), so designs without the new constraints place and route identically.

Packer (`pack_clocking.cc` `generate_constraints`):
- The constraint copied through a buffer (ratio 1) keeps the clock's name, primary and exceptions.
- BUFR/ODIV2 dividers and MMCM/PLL outputs record their primary.
- MMCM/PLL outputs also take `CLKOUT<n>_PHASE` as offset. The period arithmetic is unchanged.

XDC reader (`xdc.cc`):
- Object queries `[get_ports|get_cells|get_pins|get_nets|get_clocks ...]` take:
  - `{a b c}` lists and globs;
  - `-hier`, `-filter {NAME =~ x}` / `{NAME == x}`, `-quiet`, `-include_generated_clocks`.
  - Any other option warns and drops the command.
- **Vivado register names resolve:** `cnt_reg[3]` finds the flip-flop that drives `cnt[3]`, and `u_a/q_reg` finds the one that drives `u_a.q`. Yosys calls them `$auto$ff.cc:...`, so before the patch every `get_cells *_reg*` in an XDC matched nothing.
- A backslash continues a line.
- `set_property`:
  - **Targets:** ports, cells, nets and pins. Nets and pins used to be a fatal error; now they warn.
  - **Pull-ups:** `PULLUP|PULLDOWN|KEEPER TRUE` become `PULLTYPE`.
  - **BEL:** a site-local `BEL` such as `CFF` or `SLICEL.CFF` works with `LOC`.
  - **Repeats:** a later value of the same property replaces the earlier one with a warning. Before, a repeat was a non-fatal error.
  - **Properties that place and route does not read:** `DIFF_TERM`, `IOB`, `ASYNC_REG`, `KEEP`, `DONT_TOUCH`, `MARK_DEBUG`, `CLOCK_DEDICATED_ROUTE` and any unknown property each get a "NOT applied: <reason>" warning.
  - **`[current_design]`:** `CFGBVS`/`CONFIG_VOLTAGE` are info. `BITSTREAM.*` and `CONFIG_MODE` warn that xc7frames2bit uses its defaults.
- `create_clock`: `-name` and `-waveform` are applied. A virtual clock warns that it is NOT supported.
- `create_generated_clock`: takes `-name`, `-source`, `-divide_by`, `-multiply_by`, `-duty_cycle`, `-invert` and `-edges`. A target can be a pin, net or port.
- `set_clock_groups -asynchronous|-logically_exclusive|-physically_exclusive -group ...`: one group alone is apart from all other clocks. These and `set_false_path` between clocks are resolved after packing (`apply_xdc_clock_exceptions`), so MMCM output clocks can be named.
- `set_false_path`: takes clocks to clocks, or `-to`/`-from` cells or pins alone. Ports only gives an info line, because port paths are untimed anyway. Any other form warns and is NOT applied.
- `set_multicycle_path -to` uses the same queries, so Vivado names resolve.
- `set_max_delay`, `set_min_delay`, `set_input_delay`, `set_output_delay`, `set_clock_uncertainty|latency`, `set_*_jitter`, `set_case_analysis` and `set_disable_timing` each get a specific "NOT applied" warning. Any other command gets "unsupported XDC command '<x>' is NOT applied".

## Evidence

All of it is in docs/xdc-coverage.md, with log paths.
