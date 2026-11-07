# Phase 6: the CPU loads its own partial bitstreams from SPI flash (designs/rv_flash)

Status: simulated, built with the open flow, partials written and checked offline. **Nothing here has run on a board.**

The CPU no longer needs a host to stream a partial. Firmware reads a slot from the Arty's configuration flash and writes it into ICAPE2 itself (`'S' n`), or walks the slots by itself and runs `custom0` after each one (`'A' a b`).

## What exists

| Path | Content |
|---|---|
| `designs/rv_flash/rv_flash.v` | top `rv_flash`: `rv_soc` plus an SPI x1 master on MMIO, the fenced bridge, and the flash pins. ICAP path and `rm_slot` instance unchanged |
| `designs/rv_flash/spi_master.v` | 32-bit-per-transfer SPI mode 0 master, `SCK = clk / (2*DIV)`, `DIV=2` (25 MHz at 100 MHz) |
| `designs/rv_flash/rm_bridge_fenced.v` | PCPI-to-`rm_slot` bridge with the timeout fence (see below) |
| `designs/rv_flash/uart.v`, `picorv32.v` | byte-identical copies of `designs/rv_soc/` (`cmp` clean) |
| `designs/rv_flash/fw/main.s`, `fw/main.hex` | firmware: `W` and `C` as in rv_soc, plus `S`, `A`, `J`, `R` |
| `designs/rv_flash/arty_a7_35t.xdc` | rv_soc pins plus the six flash pins |
| `designs/rv_flash/tb/` | `spiflash_model.v` (READ 0x03, RDID 0x9F, SCK period check), `icape2_rec.v` (records every ICAP write, 64 Ki words), `rm_lat.v` (RM with selectable latency or stuck `ready`), `tb_bridge.v`, `tb_rv_flash.v`, `check_icap.py` |
| `designs/rv_flash/run_sim.sh` | assembles, packs a flash image, runs all simulations, checks the ICAP stream against the partial file |
| `designs/rv_flash/startupe2_test/` | 1-counter design that drives `STARTUPE2.USRCCLKO`, used only to test toolchain support |
| `flow/flash_image.py` | packs checked partials into flash slots, writes `manifest.json` with the exact write commands |
| `host/rvflash_cmd.ps1` | host side for `J`/`R`/`S`/`C`/`A` (DryRun by default) |
| `flow/build_pr.py` | one new line: design `rv_flash` |
| `flow/make_partials.sh` | three new lines: `SRC/TOP/PFX[rv_flash]` |

`designs/rv_soc` was not modified. The bridge test reads its `rm_bridge` by extracting it with `sed` into `build/rv_flash/sim/rm_bridge_rv_soc.v` (checked identical with `diff`).

## Research (with sources)

### Flash part and pins

- Arty A7 Reference Manual, copy hosted by Reichelt: <https://cdn-reichelt.de/documents/datenblatt/A300/DIGILENT_410-319-1.pdf> (sha256 `6b16326e...bb4`, saved as `build/rv_flash/ref/arty_a7_rm_reichelt.pdf`; the digilent.com pages return HTTP 403 to automated fetches, so the official page was not read). Text extracted with a local zlib/ToUnicode script:
  - "FPGA configuration files can be written to the Quad-SPI Flash (Spansion part number S25FL128SAGMF100 for Rev.E and Micron part number N25Q128A13ESF40 alias mt25ql128 for Rev. C)"
  - "An Artix-7 35T configuration file requires 17,536,096 bits of memory, leaving about 87% of the flash device (or ~14MB) available for user data."
  - "All signals in the SPI bus are general-purpose user I/O pins after FPGA configuration. On other boards, SCK is an exception because it remains a dedicated pin even after configuration, however, on the Arty A7 the SCK signal is routed to an additional general purpose pin that can be accessed after configuration (see Figure below). This allows access to this pin without having to instantiate the special FPGA primitive called STARTUPE2."
- Digilent master XDC, <https://raw.githubusercontent.com/Digilent/digilent-xdc/master/Arty-A7-35-Master.xdc>, Quad SPI section: `L13 qspi_cs (IO_L6P_T0_FCS_B_14)`, `K17 qspi_dq[0] (IO_L1P_T0_D00_MOSI_14)`, `K18 qspi_dq[1] (IO_L1N_T0_D01_DIN_14)`, `L14 qspi_dq[2] (IO_L2P_T0_D02_14)`, `M14 qspi_dq[3] (IO_L2N_T0_D03_14)`. The file has no SCK line and no `PACKAGE_PIN L16`.
- The extra SCK pin: the manual names it only in a figure (not readable here). LiteX `digilent_arty.py` (<https://raw.githubusercontent.com/litex-hub/litex-boards/master/litex_boards/platforms/digilent_arty.py>) uses `spiflash clk = L16`. prjxray-db `xc7a35tcsg324-1/package_pins.csv`: `L16, bank 14, IO_L3N_T0_DQS_EMCCLK_14` (a user I/O). **L16 is from LiteX, not from the schematic; unverified on the board.**
- A Digilent PCN reportedly allows S25FL128SAGMFx00 or S25FL127SABMFx00 from PCA revision E.1 (<https://files.digilent.com/resources/programmable-logic/documents/S25FL127S_PCN.pdf>). The PDF returned 403; this comes from a search summary only. **Unverified.** The design uses only READ 0x03 and RDID 0x9F, which every part named above has (assumption, not checked against the datasheets here).

### CCLK and STARTUPE2 (UG470)

- UG470 v1.10 (June 24, 2015), mirror <https://www.eng.auburn.edu/~nelson/courses/elec4200/FPGA/ug470_7Series_Config.pdf> (sha256 `49911883...a68`, `build/rv_flash/ref/ug470_v1.10_mirror.pdf`). Chapter 5, STARTUPE2 port table: "USRCCLKO Input CCLK pin. An input from the FPGA logic driving a custom, logic-generated clock frequency onto the FPGA CCLK pin after configuration. Useful for post-configuration access of external SPI flash devices." Section "USRCCLKO" (p. 92 in v1.10): "The USRCCLKO input on the STARTUPE2 primitive allows the user logic to drive the CCLK pin after configuration. [...] The first three clock cycles on USRCCLKO after End of Startup are used to switch the clock source and will not be output on the external CCLK pin."
- The current revision on docs.amd.com is 1.17 (2023-12-05, page metadata only); its text was not read.
- UG953 STARTUPE2 (<https://docs.amd.com/r/en-US/ug953-vivado-7series-libraries/STARTUPE2>): "USRCCLKO: User CCLK input." "USRCCLKTS: User CCLK 3-state enable input."

So on 7-series the CCLK pin needs STARTUPE2.USRCCLKO, but on the Arty A7 the flash clock is also on a user pin, which this design uses by default (`SCK_STARTUPE2=0`). `SCK_STARTUPE2=1` drives CCLK through STARTUPE2 instead and tri-states L16. That variant is yosys-checked only. The firmware clocks one dummy 32-bit transfer with CS high at boot, which covers the three swallowed USRCCLKO cycles in that variant.

### Toolchain support for STARTUPE2 / USRCCLKO: supported (verified by build and decode)

The toolchain's `nextpnr-xilinx ce3f7c18` is openXC7/nextpnr (himbaechel) `ce3f7c18c6b5` (2026-11-03, "Merge pull request #160 from cavearr/fix/remove-stray-fasm0"), in `upstream/openXC7_nextpnr`. It is not in `upstream/openXC7_nextpnr-xilinx` (`git cat-file` fails there).

- `himbaechel/uarch/xilinx/pack_io.cc:1467` `cfg_rules[id_STARTUPE2].new_type = id_STARTUP_STARTUP;` and `:1509` preplaces STARTUP_STARTUP on its single site.
- `himbaechel/uarch/xilinx/fasm.cc:3301-3312` writes `STARTUP.PROG_USR` and `STARTUP.USRCCLKO_CONNECTED` (set when USRCCLKO has a real driver, not a constant).
- `tests/pack_test.cc:51` `pack_cfg_startupe2`.
- prjxray-db `a8b09269`, `artix7/segbits_cfg_center_mid.db`: `CFG_CENTER_MID.STARTUP.USRCCLKO_CONNECTED 26_2196 27_2197 27_2198` (origin `038-cfg-startup`). `ppips_cfg_center_mid.db`: `CFG_CENTER_MID.CFG_CENTER_STARTUP_USRCCLKO.CFG_CENTER_CLK1_7 always`. `tile_type_CFG_CENTER_MID.json` has site `STARTUP X0Y0` with pin `USRCCLKO`.
- Run: `python3 flow/build_openxc7.py rv_flash/startupe2_test --top startupe2_test --name startupe2_test --run` (counter bit 3 → USRCCLKO, constant ties on the other inputs). nextpnr: `STARTUP: 1/1`, `1 warning, 0 errors` (the usual `create_clock -name` warning). FASM: `CFG_CENTER_MID_X46Y32.STARTUP.USRCCLKO_CONNECTED` and `CFG_CENTER_MID_X46Y32.CFG_CENTER_STARTUP_USRCCLKO.CFG_CENTER_CLK1_7`. The net `cnt[3]` routes through `X49Y127/CLK_L1` to `CFG_CENTER_CLK1_7` to `STARTUP_X0Y0.USRCCLKO` (12 pips).
- Decoding the bitstream back (`flow/bit2fasm.py`, run with `toolchain/openxc7/libexec/tabbypy3`): 421 FASM lines, 0 unknown, and `CFG_CENTER_MID_X46Y32.STARTUP.USRCCLKO_CONNECTED` is present.
- **Not verified:** that CCLK actually toggles on silicon. No drafted fix is needed.

### openFPGALoader v1.2.0: raw data at a flash offset (read in source, `upstream/trabucayre_openFPGALoader` tag `v1.2.0`)

- `--help`: `-f, --write-flash`, `-o, --offset arg  Start address (in bytes) for read/write into non volatile memory`, `--verify`, `--file-type`, `--dump-flash`, `--file-size`, `--skip-reset`.
- `src/device.cpp:12-27`: the file type is the extension unless `--file-type` overrides it.
- `src/xilinx.cpp:339-346`: `.bit`/`.bin` with `-f` give SPI_MODE. `:228-246` `.bin` opens a `RawParser`. `:646-684` `reverse` stays false outside MEM_MODE, so raw bytes are written in file order. `:937-950` `program_spi` writes `FlashInterface::write(offset, data, length)`.
- `src/spiFlash.cpp:207-247` `sectors_erase`: the end is rounded up to 4 KiB when the part supports subsector erase (64 KiB otherwise), and 4 KiB erases are used at the tail. A 59,288-byte slot at a 64 KiB boundary therefore erases only inside its own 64 KiB slot.
- `src/xilinx.cpp:748-756, 739-746`: flash access first loads the spiOverJtag bridge bitstream (this **replaces the running FPGA design**), and resets the FPGA afterwards unless `--skip-reset`.
- `src/board.hpp:137`: `arty_a7_35t`, `xc7a35tcsg324`, SPI_FLASH.
- `src/cxxopts.hpp:494-495`: integer options accept a `0x` prefix, so `-o 0x400000` parses.
- `src/flashInterface.cpp:249-258`: `--dump-flash` writes to the file named on the command line.

## Design

### Memory map (new and changed entries only; `0x00-0x18` as in rv_soc)

| Address | Access | Function |
|---|---|---|
| `0x1000_001C` | R | `late_answers[15:0]`: `ready` rising edges seen while no instruction was outstanding |
| `0x1000_0020` | W / R | bit0 = 1 asserts flash CS (pin low) |
| `0x1000_0024` | W / R | one 32-bit SPI transfer, MSB first, blocks until done. W shifts out `wdata`; R shifts out zeros and returns the 32 received bits, the first byte in bits 31:24 |
| `0x1000_0028` | R | last received word (for example RDID after a W) |

The address decode widened from `mem_addr[4:2]` to `mem_addr[5:2]`.

### Flash layout and byte order

Slot n is at `0x400000 + n*0x10000`, n = 0..15. It holds a 16-byte header, `magic 0x50524631, nbytes, sum32 of the big-endian data words, 0`, then the partial `.bin` bytes unchanged. `flow/flash_image.py` refuses partials without a valid `.check.json`, slot numbers outside 0..15, offsets below `0x400000`, and data larger than a slot.

The ICAP byte order is the same as before. Flash bytes are read in file order, MSB first, and packed big-endian (byte 0 → bits 31:24), exactly like the `W` path's `getw`. The word goes to `+0x10`, where the unchanged `bswap` (per-byte bit reversal) feeds `ICAPE2.I`. The simulation checks this end to end (below).

### Firmware commands (`fw/main.s`)

- `'S' n` loads slot n. It reads the header and refuses (`'E'`, no ICAP write) a wrong magic, `nbytes` of 0, more than 0xFFF0, or not a multiple of 4.
  - Pass 1 reads all data words and sums them. On a mismatch it replies `'X'` without writing ICAP.
  - Pass 2 reads the slot again and writes each word to ICAP, then replies `'K'`.
- `'A' a b` runs `'S'` for slots 0, 1, ... On `'K'` it runs `custom0(a, b)`, sets the LEDs and replies the 4 result bytes. It stops after the first non-`'K'` and sends `'.'`. This is the "firmware picks the module itself" mode.
- `'J'` replies the RDID bytes. `'R' addr` replies the flash word at `addr`.
- `'W'` and `'C'` are unchanged from rv_soc, so `host/icap_load.ps1 -Target rvsoc` still works for them.

### Timeout tagging fix (`rm_bridge_fenced.v`)

The `rm_slot` interface has no tag, so a late `ready` cannot be told apart from a real one. The bridge therefore bounds when an issue may happen:

- **Fence after a timeout.** After a timeout, the next instruction is issued only after `slot_ready` has been low for `FENCE=64` consecutive cycles, counted from the timeout. Any `ready` in that window restarts the count.
- **Stray answer while idle.** A `ready` seen with no instruction outstanding arms the same fence.
- **Edge-only acceptance.** In BUSY only a rising edge of `ready` is accepted, so a `ready` stuck high cannot answer an instruction.
- **No hang.** If the fence never clears (ready stuck high), the waiting instruction completes with rd=0 after `TIMEOUT+FENCE` cycles and is counted as a timeout. `pcpi_wait` stays high meanwhile, so the core's own 16-cycle trap does not fire.

Remaining limit: an RM whose answer comes more than `TIMEOUT+FENCE` cycles late, after a fully quiet window, can still be taken by the next instruction. RMs are expected to answer within `TIMEOUT`.

## Verified by run

### Simulation (`bash designs/rv_flash/run_sim.sh`, iverilog from oss-cad-suite, `SPI_DIV=2`, CLKS_PER_BIT=100)

Bridge, old (`designs/rv_soc` rm_bridge, unchanged) vs new, same stimulus (`tb/tb_bridge.v`, RM latency 1/100/40 cycles by funct, funct 3 = ready stuck high for 300 cycles):

```
ok:   fast answer: funct 0 rd=00000003 (5 cycles)
ok:   slow answer times out: funct 1 rd=00000000 (66 cycles)
ok:   next after late answer: funct 2 rd=00000300 (33 cycles)
ok:   ready stuck high: funct 3 rd=deadbeef (4 cycles)
ok:   issue while ready stuck: funct 0 rd=00000030 (4 cycles)
ok:   after stuck ends: funct 0 rd=0000000f (5 cycles)
rm_bridge (designs/rv_soc, unchanged): timeouts=1 late_answers=0
REPRODUCED: rm_bridge (designs/rv_soc, unchanged) takes stale answers (0x300, 0x30) as shown above
ok:   fast answer: funct 0 rd=00000003 (5 cycles)
ok:   slow answer times out: funct 1 rd=00000000 (66 cycles)
ok:   next after late answer: funct 2 rd=00000030 (140 cycles)
ok:   ready stuck high: funct 3 rd=deadbeef (4 cycles)
ok:   issue while ready stuck: funct 0 rd=00000000 (129 cycles)
ok:   after stuck ends: funct 0 rd=0000000f (5 cycles)
rm_bridge_fenced (designs/rv_flash): timeouts=2 late_answers=1
PASS: tb_bridge rm_bridge_fenced (designs/rv_flash)
```

With the old bridge, the instruction after a timeout returned the timed-out instruction's sum (0x300 instead of 0x30). The fifth instruction returned 0x30, the late answer of the third. In the first run the fifth result had been predicted as 0xDEADBEEF; the tb expectation for the old bridge was changed to the observed 0x30 afterwards. The new bridge returns the correct value or 0 with a counted timeout in every case.

SoC (`tb/tb_rv_flash.v`). The flash model holds a real partial at slot 0, slot 1 erased (0xFF), and slot 2 the same partial with one data bit flipped after the checksum. The ICAPE2 stub records every write. The RM in sim is `designs/rv_soc/sim/rm_add.v`.

Run 1, `PARTIAL=build/partials/rv_pr/rm_andn_from_xor.bin` (the default), and run 2, `PARTIAL=build/partials/rv_flash/rm_andn_from_xor.bin` (this design's own partial). The tb lines are identical in both runs:

```
ok:   J -> 01 20 18
ok:   R 00400000 -> 50524631 (slot 0 magic)
ok:   S 0 -> 'K' after 45544 us simulated
ok:   S 0: 14818 ICAP words == bswap(partial words), first ffffffff last 04000000
ok:   S 1 (erased slot) -> 'E', 0 ICAP writes
ok:   S 2 (one flipped bit) -> 'X', 0 ICAP writes
ok:   C 12345678 0F0F0F0F -> 21436587 (rm_add in sim)
ok:   A -> 'K' 21436587 'E' '.' (slot 0 loaded and run, stopped at erased slot 1)
ok:   A slot 0: 14818 ICAP words == bswap(partial words), first ffffffff last 04000000
flash model: 11 READ transactions, 1 RDID; SPI_DIV=2; slot timeouts=0 late=0
PASS: tb_rv_flash
```

The independent byte comparison:

```
run 1: captured 14818 words, partial 14818 words; sha256 captured-unswapped f020b25d466aa2c1 partial f020b25d466aa2c1; IDENTICAL
run 2: captured 14818 words, partial 14818 words; sha256 captured-unswapped 9bedd49ff4db04ce partial 9bedd49ff4db04ce; IDENTICAL
```

iverilog also prints `WARNING: ... $readmemh(build/rv_flash/sim/slot0_words.hex): Not enough words in the file for the requested range [0:16383]`. This is expected: the array is larger than the partial, and the tb counts the loaded words.

`check_icap.py` undoes the per-byte bit swap on every captured `ICAPE2.I` word and compares the result byte for byte with the `.bin` file. The SPI clock period check in the flash model (minimum 20 ns, assumed 50 MHz READ limit, not taken from a datasheet) reported 0 violations.

One `'S'` takes about 45.5 ms of simulated time at 100 MHz: two full passes at 25 MHz SCK plus CPU overhead. That is a sim measurement, not a board one.

### Implementation (`python3 flow/build_pr.py --design rv_flash --run`)

- Entry: `rm_dir rv_soc/pr`, RMs `andn, xor, add`, the same RM files and region (`SLICE_X12Y100:SLICE_X15Y149`) as rv_pr. The order differs from rv_pr on purpose; see open problems.
- Static replay: `Pre-routed: 3659 net(s) given their reference route (0 dangling wire(s) pruned), 0 not in this design, 0 collided`.
- region_route: andn 129, xor 97, add 97 fabric connections, 0 unroutable.
- Timing, all three `_c` builds: `Max frequency for clock 'u_bridge.clk': 152.07 MHz (PASS at 100.00 MHz)`, `1 warning, 0 errors`.
- Utilisation (pr_andn_c, nextpnr): SLICE_LUTX 2138/65200, SLICE_FFX 927/65200, CARRY4 112, PAD 13. Bitstreams are 2,192,175-2,192,176 bytes.
- `flow/pr_check.py` on andn_c vs xor_c, andn_c vs add_c and xor_c vs add_c: each `frames differing: 72; inside region: 72; outside region: 0`, `STATIC IDENTICAL OUTSIDE REGION`.
- `DESIGNS=rv_flash flow/make_partials.sh`: all six `OK (simulated from ...)`. For each target the partial is byte-identical whatever the base (`cmp`). Each is 59,272 bytes, with 72 region frames, `crc: OK`, `base + partial == target: True`, and `outside_are_static_pads: true` (one run-end pad frame, `0x00020600`).
- `python3 flow/flash_image.py --slot 0=.../rm_andn_from_xor.bin --slot 1=.../rm_add_from_xor.bin --slot 2=.../rm_xor_from_andn.bin --out build/rv_flash/flash` wrote `slot0.bin` at 0x400000 (sum32 0x668b0405), `slot1.bin` at 0x410000 (0x73c7dcdd) and `slot2.bin` at 0x420000 (0x52825bde), 59,288 bytes each.

## Unverified

- Everything on hardware: flash pins (especially SCK on L16), SPI timing at 25 MHz, whether the flash answers READ 0x03 as modelled, ICAPE2 behaviour with a CPU-fed partial, and the board's current draw during reconfiguration.
- The flash model is behavioural and written from the SPI mode 0 convention: data out on the falling edge, 8 ns valid delay, reads past the window return 0xFF. It is not derived from the S25FL128S or N25Q128 datasheet.
- The RDID value 01 20 18 in the testbench is a model parameter; the real value is whatever the board's part returns.
- The `SCK_STARTUPE2=1` variant is not simulated (no STARTUPE2 model) and not built in the PR flow.
- The ICAP points from docs/phase4-5-status.md still apply: the 3 Vivado-only ICAP bits (docs/drafts/prjxray-db-icap-bits.md) and the minor 24/25 pass-1 pattern.

## Hardware steps for later (not run, no board)

Run from the repo root in WSL for the loader. The serial commands are PowerShell on Windows. Before every step, plug the board through a USB power meter and note the idle current. Unplug if it jumps.

1. Rebuild the slot files if needed (offline, already done):
   `python3 flow/flash_image.py --slot 0=build/partials/rv_flash/rm_andn_from_xor.bin --slot 1=build/partials/rv_flash/rm_add_from_xor.bin --slot 2=build/partials/rv_flash/rm_xor_from_andn.bin --out build/rv_flash/flash`
2. Optional: read the region first to see what is there, and keep a backup:
   `openFPGALoader -b arty_a7_35t --dump-flash -o 0x400000 --file-size 0x30000 build/rv_flash/flash/before_0x400000.bin`
3. Write the three slots, each into its own 64 KiB block. openFPGALoader replaces the running design with its SPI bridge and resets the FPGA afterwards:

   ```
   cd build/rv_flash/flash
   openFPGALoader -b arty_a7_35t -f -o 0x400000 --verify slot0.bin
   openFPGALoader -b arty_a7_35t -f -o 0x410000 --verify slot1.bin
   openFPGALoader -b arty_a7_35t -f -o 0x420000 --verify slot2.bin
   ```

4. Load the static design with the xor RM into SRAM (not flash):
   `openFPGALoader -b arty_a7_35t build/openxc7/rv_flash/pr_xor_c/rv_flash.bit`
5. Serial checks (`COMx` = the Arty's USB serial port). Each command prints what it will send unless `-Run` is given:

| Command | Expected output |
|---|---|
| `powershell -File host\rvflash_cmd.ps1 -Cmd J -Run -Port COMx` | `JEDEC ID: xx xx xx`, the board's flash ID. Not all FF or 00; compare with `openFPGALoader -b arty_a7_35t --detect -f` |
| `... -Cmd R -Addr 400000 -Run -Port COMx` | `flash[400000] = 50524631` (slot magic) |
| `... -Cmd C -Custom 12345678,0F0F0F0F -Run -Port COMx` | `1D3B5977` (xor, the SRAM-loaded RM) |
| `... -Cmd S -Slot 0 -Run -Port COMx`, then `-Cmd C` | `'K'`, then `10305070` (andn) |
| `... -Cmd S -Slot 1 -Run -Port COMx`, then `-Cmd C` | `'K'`, then `21436587` (add) |
| `... -Cmd S -Slot 2 -Run -Port COMx`, then `-Cmd C` | `'K'`, then `1D3B5977` (xor) |
| `... -Cmd A -Custom 12345678,0F0F0F0F -Run -Port COMx` | slot 0 `'K' 10305070`, slot 1 `'K' 21436587`, slot 2 `'K' 1D3B5977`, then slot 3 `'E'` (if 0x430000 does not happen to hold the magic), end |

   - If `J` returns FF FF FF or 00 00 00, the SPI path is not working. Check SCK on L16 first, then try a `SCK_STARTUPE2=1` build.
   - If `S` returns `'X'`, the flash data differs from what was written; re-run step 3 with `--verify`.
   - If `S` returns `'K'` but `C` does not change, see the ICAP items under Unverified.
6. Optional, only if the board should boot this design by itself: `openFPGALoader -b arty_a7_35t -f build/openxc7/rv_flash/pr_xor_c/rv_flash.bit`. **This overwrites the configuration area at offset 0** (the board's current boot image). The full bitstream is 2,192,175 bytes, which ends near 0x217300, below the slots at 0x400000.

## Safety

- Never write below 0x400000 unless replacing the boot image is intended (step 6). `flow/flash_image.py` refuses slot offsets below `protect_below = 0x400000` and offsets that overlap the full bitstream size.
- Keep partial slots above the full bitstream. The manual's 17,536,096 bits (2,192,012 bytes) and our 2,192,175-byte files both end well below 0x400000.
- Each slot is 64 KiB-aligned and smaller than 64 KiB. openFPGALoader v1.2.0 erases from the offset to the end rounded up to 4 KiB, so writing one slot does not erase its neighbours (source above, not run).
- Only partials with a valid `.check.json` (region gate, CRC, simulated load) can be packed. The firmware refuses a slot with a bad header or checksum before writing a single ICAP word (simulated: `'E'`/`'X'`, 0 ICAP writes).
- Watch board current on a USB power meter during steps 3-5, and unplug if it jumps.

## Open problems

- **Static LUT route-throughs inside the RM region.** The replayed static routing uses LUTs in region tiles as route-throughs: 78 in the first rv_flash attempt, 43 in rv_pr, 61 in the final rv_flash build.
  - With `xor` as the first (static-routing) configuration, `pcpi_rs2[13]` used `X33Y32/CLBLM_M_C/CLBLM_M_C2`, the LUT the andn RM needs. nextpnr then stopped with `ERROR: CLBLM_R_X11Y119.SLICEM_X0.CLUT holds cell 'u_rm.rmx_55' and a route-through: two INITs for one LUT.`
  - Putting `andn` first gave 0 collisions for all three RMs (checked with a script that intersects static route-through LUTs with each RM's preplaced LUT sites; it also reports 0 for rv_pr, consistent with rv_pr building).
  - This is order luck, not a fix. The proper fix is for static routing to never use region LUTs as route-throughs, for example a shell or blocker change or a router rule, in files owned by another worker (`flow/rm_place.py`, `flow/gen_shell*.py`). Adding more RMs to any design can hit this. While this was being written, another worker added a `detour` option to `flow/build_pr.py` (`flow/static_detour.py`, "static_detour draft" in commit d022ef1) that appears aimed at static routes in the region. It was not used or evaluated for rv_flash.
- Commit d022ef1 contains the first version of the `rv_flash` line (RM order xor, andn, add), which fails as described above. The working tree has the order andn, xor, add, which is the one that built.
- The SPI master is x1 at 25 MHz. Quad read and a higher clock would cut the roughly 45 ms (simulated) per load.
- The firmware reads each slot twice (checksum, then ICAP) so that bad data never reaches ICAP. A CRC32 or a hash, instead of the 32-bit sum, would catch more corruption patterns.
- `host/rvflash_cmd.ps1` was dry-run only.

## Update 2026-11-05 evening: decoupler added (static changed, slots regenerated)
- rv_flash now contains `designs/common/dfx_decoupler.v` between the bridge and the RP. MMIO +0x2C is the decouple
  register. 'W' and 'S' decouple during ICAP writes (docs/dfx-vs-vivado.md item 19).
- The static design changed, so all rv_flash builds, partials and flash slots were regenerated. **The slot files from
  09:53 are stale; use the new ones:**
  - slot0.bin at 0x400000: rm_andn_from_xor, sum32 0xc3d5b097
  - slot1.bin at 0x410000: rm_add_from_xor, sum32 0x8bfc9d23
  - slot2.bin at 0x420000: rm_xor_from_andn, sum32 0x38f1fc95
  - Each slot is 59,288 bytes.
- Sim with rv_flash's own partial in flash (PARTIAL=build/partials/rv_flash/rm_andn_from_xor.bin): PASS.
  - The ICAP stream is identical to the partial (sha256 907226e4...).
  - 0 of 29,636 ICAP writes happened while coupled.
- The hardware steps above are unchanged. Load the new `pr_xor_c/rv_flash_icapbits.bit` together with these slots.

## Update 2026-11-05 night: deterministic rebuild (PYTHONHASHSEED=0)
- The external flow was rebuilt from scratch: full_check passes every step.
  - regress 11/11, partials 24/24, byteman 24/24, icapbits 8/8, gl_sim 44/44, region2v 48 (4/4 negatives caught).
- Flash slots regenerated. Use these (slot 0 changed):
  - slot0 0x42f3ed76 (rm_andn_from_xor)
  - slot1 0x8bfc9d23
  - slot2 0x38f1fc95
- End-to-end sim with the new slot 0 partial: ICAP stream identical (sha256 e48072c0...), 0/29,636 ICAP writes while coupled.
