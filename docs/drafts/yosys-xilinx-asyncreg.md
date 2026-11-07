# Draft: yosys-xilinx-asyncreg (YosysHQ/yosys, on 3718f7f13 = 0.70+186)

Not posted anywhere. Patch: `docs/drafts/yosys-xilinx-asyncreg.patch` (`git diff` of `build/src/yosys-asyncreg`, +329, 3 files).

## Problem

`synth_xilinx` turns a 3-flop synchronizer into one SRL16E even with `(* ASYNC_REG = "TRUE" *)` on the registers. Nothing in yosys reads ASYNC_REG: the attribute sits on the wire, and `shregmap` only skips flip-flops with `keep`. An SRL is not a synchronizer: its stages are not metastability-hardened flops in one slice. Vivado keeps 3 FDREs with ASYNC_REG=1 (`synth_cells.txt` of x_async_rtl).

## Change

- New pass `xilinx_asyncreg` (`techlibs/xilinx/xilinx_asyncreg.cc`):
  - It finds registers with ASYNC_REG = TRUE: the attribute on a wire or on a flip-flop cell. The name is matched in any case, and TRUE/YES/1 count as true, as in Vivado.
  - `-xdc <file>` also reads `set_property ASYNC_REG TRUE [get_cells ...]` and the `-dict` form. Names are Vivado's: `<reg>_reg`, `<reg>_reg[<bit>]`, `<inst>/<reg>_reg`. Globs, `-hier` and `-filter {NAME =~ ...}` are taken. A target that matches nothing gets a warning.
  - Every such wire gets `ASYNC_REG = "TRUE"`. The flip-flops that drive it get `ASYNC_REG = "TRUE"` and `keep`. `keep` stops `shregmap` and keeps the stages from being merged or removed. The attribute stays on the FDRE cell and the netname in the JSON, for place and route.
- `synth_xilinx` runs `xilinx_asyncreg` in `prepare`, after `flatten`. The CMake entry is added.

## How it was built and run

There is no full yosys build here (no flex/bison), so the pass is built as a plugin from the same file:

```bash
SRC=build/src/yosys-asyncreg/techlibs/xilinx/xilinx_asyncreg.cc PASS=xilinx_asyncreg OUT=build/yosys-plugin/asyncreg \
  DRY_RUN=0 bash toolchain/buildenv/build_yosys_plugin.sh
```

The flow emulates the `synth_xilinx` call. `flow/gap_build.py` takes a new `asyncreg_pass` tool and runs:

```
synth_xilinx ... -run :coarse; xilinx_asyncreg -xdc <xdc>; synth_xilinx ... -run coarse:
```

`flow/xdc_audit.py` variant `xdc2` uses it. The `synth_xilinx.cc` hunk itself is not compiled.

## Evidence (logs `build/xdc/<design>/{base,xdc2}/yosys.log`, cell counts `yosys_stat.txt`)

| Design | base (stock yosys) | with the pass | pass log |
|---|---|---|---|
| x_async_rtl (RTL attribute) | 1 SRL16E | 3 FDRE | `ASYNC_REG on 3 wire(s) (0 from the XDC), 3 flip-flop cell(s) kept.` |
| x_async_xdc (XDC `set_property ASYNC_REG TRUE [get_cells s1_reg]` ...) | 1 SRL16E | 3 FDRE | `ASYNC_REG on 3 wire(s) (3 from the XDC), 3 flip-flop cell(s) kept.` |
| x_async_none (no ASYNC_REG) | 1 SRL16E | 1 SRL16E | `ASYNC_REG on 0 wire(s) ...` |

- **Vivado:** 3 FDRE with ASYNC_REG=1 for x_async_rtl and x_async_xdc. For x_async_none it also keeps 3 FDRE (no SRL); the difference without ASYNC_REG is yosys' normal SRL inference.
- **No-op:** yosys JSON of blinky and rv_soc with the pass against without it (`flow/xdc_noop.py --yosys`, results in `build/xdc_noop/noop.json`). See docs/xdc-coverage.md.

## Not done

- Retiming: `synth_xilinx -retime` (abc -dff) was not tested with the kept cells.
- A multi-bit `$dff` with only some ASYNC_REG bits is kept whole.
- With hierarchy kept, an XDC name sets the wire in the module, so it applies to every instance of that module.
