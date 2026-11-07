# Draft: openFPGALoader `--partial` (7-series partial bitstream over JTAG)

Status: LOCAL DRAFT. Built and run against a simulated TAP on 2026-11-05 (results at the end of this file). **Not tested on hardware**, not sent upstream.

- Clone: `~/open-dfx-xc7/upstream/trabucayre_openFPGALoader`
- Base: tag `v1.2.0` = `befbab4f` (2026-10-18). Master HEAD when read: `e3d8d947` (2026-11-03).
- Branch `partial-load`, commit `35364c8` (local only).
- Patch file: `openfpgaloader-partial.patch` (`git format-patch`, applies with `git am`).

## Why

In v1.2.0, `Xilinx::program_mem()` always does this:

1. TLR (`src/xilinx.cpp:964`)
2. **JPROGRAM** (`:978`), then poll INIT_B with BYPASS (`:980-983`), then 120000 TCK in RTI (`:987-988`)
3. CFG_IN (`:996`), then shift the whole file in bursts, ending in UPDATE-DR (`:1011-1034`)
4. **JSTART** (`:1067`), then 2000 TCK (`:1073-1074`), then TLR (`:1079`)
5. One BYPASS IR capture that prints isc_done/init/done (`:1081-1089`). If DONE=0 it only reads STAT (`:1091-1093`). It does not fail.

JPROGRAM clears configuration memory, so a partial load is impossible as-is. No existing option avoids it:

- `--skip-reset` (`src/main.cpp:1037`) only affects `post_flash_access()` (`src/xilinx.cpp:739-746`), which is on the flash path.
- `grep -i partial` over `src/` finds nothing.

Bitstream handling:

- `.bit` goes through `BitParser`. It strips the header and checks the declared length (`src/bitparser.cpp:146-181`).
- `.bin` goes through `RawParser` (`src/rawParser.cpp:19-35`).
- MEM mode bit-reverses every byte (`src/xilinx.cpp:678-679`, `bitparser.cpp:171`).
- The bitstream is never checked or edited: no sync-word check, no IDCODE match. `BitParser::get_idcode` (`bitparser.cpp:213`) has no caller in `src/`.

Master differs from v1.2.0 only in `xc2c_init` (`xilinx.cpp:~2046`). `main.cpp` and `xilinx.hpp` are unchanged, so the patch should also apply on master (not tried).

## What the patch changes

- `--partial` CLI flag (`main.cpp`). It is passed to the `Xilinx` constructor as a new defaulted parameter and stored in `_partial`.
- `Xilinx::program()`: with `--partial`, anything other than SRAM (MEM) mode on Artix-7, Spartan-7, Kintex-7 or Zynq-7000 throws an error.
- `program_mem()` with `--partial`:
  - Skips JPROGRAM, the INIT_B poll and the 120000-clock wait. It goes straight to RTI.
  - Keeps the CFG_IN load unchanged.
  - Skips JSTART but still clocks 2000 TCK in RTI.
  - Keeps the final IR capture and DONE print. DONE should stay 1 if the static design survives.
- `tx_buf = BYPASS` moves out of the JPROGRAM branch, because the final IR capture (`:1081`) uses it.
- Checked: `g++ -fsyntax-only` passes for `xilinx.cpp` and `main.cpp`. A full build was not possible: no cmake, pkg-config, libftdi or libusb headers are installed, and nothing was installed.

## UG470 / sequence: UNVERIFIED

I could not fetch the text of UG470. docs.amd.com returned only metadata (UG470 v1.17, 2023-12-05).

These points are therefore unverified:

- that UG470/UG909 say a partial load over JTAG is CFG_IN only, with no JPROGRAM
- whether JSTART is needed or harmful afterwards
- whether Vivado partial bitstreams contain a START command

The step comments in openFPGALoader (`xilinx.cpp:957-1078`) mark JSTART as "(optional)" (`:1062`), but they cover full configuration. There are no partial `.bit` files in the project yet (only `blinky.bit`). Checking a Vivado partial bitstream for the CMD values START/DESYNC is the next step.

## Risks

- If the partial bitstream assumes a sequence the patch does not do (for example, it needs JSTART), the RM may not start. The device should not be wiped either way.
- A wrong or full bitstream passed with `--partial` is not rejected. A full bitstream without JPROGRAM can corrupt the running design.
- With `.bit` input, BitParser warns or fails if the header length is wrong.
- Daisy chains, Zynq PS-side state and encrypted or compressed partials were not considered.

## Command (once a board is attached; not run)

```
~/open-dfx-xc7/upstream/trabucayre_openFPGALoader/build/openFPGALoader \
    -b arty_a7_35t --partial rm_partial.bit
```

Build first with upstream's cmake flow (needs libftdi1-dev and libusb-1.0-0-dev). Load the full static bitstream normally first, without `--partial`. The board name `arty_a7_35t` is defined at `src/board.hpp:137`.

## Alternatives

- **OpenOCD**: the installed `~/open-dfx-xc7/toolchain/oss-cad-suite/bin/openocd` is 0.12.0+dev-01523.
  - Its `share/openocd/scripts/cpld/xilinx-xc7.cfg:43` creates `pld ... virtex2 ... -no_jstart`.
  - The deprecated `xc7_program` proc in the same file (`:51-62`) sends JSHUTDOWN and JPROGRAM.
  - What `virtex2 program`/`pld load` sends, and whether it does JPROGRAM: UNVERIFIED (source not read, no docs installed).
- **xc3sprog**: not read. UNVERIFIED.
- **Upstream**: issue #367, "Support load partial bitstream", is listed as open (from `docs/phase0-prior-art.md:107`; not re-checked).

## Build and virtual-cable results (2026-11-05)

Commands: `docs/buildenv.md`. Stock `v1.2.0` (`befbab4f`) and branch `partial-load-build` (= `partial-load`, `35364c8`)
were built with conda-forge GCC 14.4.0, libftdi 1.5 and libusb 1.0.30, with `-DENABLE_UDEV=OFF -DENABLE_LIBGPIOD=OFF`.

- **Compile:** both builds succeed with 0 warnings. Both print `openFPGALoader v1.2.0`.
- **`--help`:** the patched binary lists `--partial  load a partial bitstream to SRAM without clearing the device (Xilinx 7-series only)`. The stock binary has no `partial` in its help.
- **Code path:** `src/xilinx.cpp` `Xilinx::program_mem()` on the branch.
  - With `_partial`, the `JPROGRAM` shift, the INIT_B poll and the 120000-TCK wait are replaced by `printInfo("Partial bitstream: skip JPROGRAM"); _jtag->set_state(Jtag::RUN_TEST_IDLE);`.
  - `JSTART` is guarded by `if (!_partial)`. The 2000-TCK RTI wait, TLR and the final BYPASS IR capture stay.
  - The full hunks are in `openfpgaloader-partial.patch`.

### Simulated JTAG sequence (no hardware)

`flow/xvc_trace.py` (new) is an XVC server that simulates one 7-series TAP:
- IR length 6, IDCODE 0x0362D093 (xc7a35t), IR capture 0b110101;
- IDCODE/BYPASS data registers;
- it logs every IR update, DR update and run of RTI clocks, and keeps the bits shifted under CFG_IN.

openFPGALoader connects to it with `-c xvc-client --ip 127.0.0.1 --port 2542`. `flow/ofl_virtual_test.sh` (DRY_RUN=1 by default) runs three cases. The input is `build/partials/rv_pr/rm_andn_from_xor.bin` (59,272 bytes). Traces are in `build/patched/ofl_virtual/` (before fix1) and `build/patched/ofl_virtual_fix1/` (after).

| case | IR sequence after IDCODE scan | CFG_IN bytes | exit |
|---|---|---|---|
| stock, no flag | JPROGRAM, BYPASS (INIT poll), RTI 120001 TCK, CFG_IN, DR 474176 bits, JSTART, RTI 2001 TCK, TLR, BYPASS | 59,272 | 0 |
| patched, no flag | identical to stock | 59,272 | 0 |
| patched, `--partial` | CFG_IN, DR 474176 bits, RTI 2001 TCK, TLR, BYPASS | 59,272 | 0 |

- **No JPROGRAM or JSTART:** with `--partial`, no JPROGRAM and no JSTART instruction is ever loaded.
- **Data:** in all three cases the CFG_IN data equals the input file with each byte bit-reversed, the MEM-mode reversal at `xilinx.cpp:678-679`.
- **`.bit` input:** `--partial` with `rm_andn_from_xor.bit` sends the same CFG_IN bytes as the `.bin`.
- **Limits of the model:** the simulated TAP only answers IDCODE and the IR capture value. It models no configuration logic, CRC or DONE behaviour. This shows the command sequence openFPGALoader sends; it does not show what a real device does with it.

### Bug found and fixed (`openfpgaloader-partial-fix1.diff`, uncommitted in `build/src/ofl-partial`)

- **The problem:** the patch's guard that rejects `--partial` outside SRAM mode sat inside the non-SPI `else` branch of `Xilinx::program()`. So `-f --partial` skipped it and went on into `program_spi()`.
- **Why it matters:** that path loads the SPI-over-JTAG bridge bitstream through `program_mem()` (`xilinx.cpp:743`, `809`, `840`). With `_partial` set, the bridge, a full bitstream, would have been loaded without JPROGRAM.
- **What was run:** in the run, the old binary stopped earlier, on `Can't program SPI flash: missing device-package information`. The bridge load is shown by reading the code, not by a run.
- **The fix:** fix1 moves the guard ahead of the mode branch, and frees `secondary_bit` too.
- **After the fix:** `-f --partial` exits 1 with `Error: --partial is only supported for SRAM load of Xilinx 7-series devices` before any CFG_IN. The three traces above are unchanged (sequences compared).
- `openfpgaloader-partial.patch` itself is unchanged. Apply fix1 on top of it.

Still unverified: everything in "UG470 / sequence" above, and behaviour on a real Arty A7-35T. The Phase 2 Vivado partial has no START command (docs/phase2-vivado-partial.md), which is consistent with skipping JSTART but does not prove it.
