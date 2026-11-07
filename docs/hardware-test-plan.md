# Hardware test plan (Arty A7-35T): run in this order, stop at the first failure

This is the single, ordered plan for when the board arrives. Every expected value below comes from offline runs (sims, decoders, byteman) that are linked in the phase docs. Nothing here has run on silicon yet.

Each stage tests one new assumption. If a stage fails, stop there and bring the exact output back: later stages depend on it.

## Before anything
- Plug the board in through a **USB power meter**. Note the idle current before each step, and unplug at once if it jumps during a load or swap.
- Find the Arty's serial port on Windows (Device Manager → Ports): `COMx` below.
- Every host script defaults to DryRun. It prints what it would send and sends it only with `-Run`. Do a dry run first.
- `openFPGALoader` below is `toolchain/oss-cad-suite/bin/openFPGALoader` (stock v1.2.0), run from the repo root in WSL. USB passthrough to WSL may need `usbipd`; otherwise run the Windows build of the same version.
- Only load files that have a `.check.json` next to them. The loaders refuse anything else.

## Stage 1: an open-tools full bitstream configures the chip
Tests: a full bitstream from openXC7 works on this board; pins; clock.
- Command: `openFPGALoader -b arty_a7_35t build/openxc7/pr_uart/pr_count_c/top_icapbits.bit`
- Expected: DONE LED on; the 4 LEDs show the counter's top bits counting.
- If it fails: try `top.bit` (without the 3 Vivado ICAP bits). If that fails too, the problem is in the base flow, not in DFX.

## Stage 2: ICAP works and the bit order is right
Tests: ICAPE2 from nextpnr works; the byte bit-swap matches UG470 Table 5-5 (docs/icap-bit-order.md); the 3 Vivado ICAP bits.
- Command: `powershell -File host\icap_load.ps1 -ReadIdcode -Run -Port COMx`
- Expected: `IDCODE 0x0362D093 seen`.
- If it fails: reload with `top.bit` (no ICAP bits) and retry. Note which of the two works. **Do not continue to partials until this passes.**

## Stage 3: first partial swap (CLB region, UART → ICAP)
Tests: the partial format (two passes, CTL0 masking, pad frame), the region gate and static continuity.
- Command: `powershell -File host\icap_load.ps1 -Partial build\partials\pr_uart\rm_shift_from_count.bin -Run -Port COMx`
- Expected: the loader prints `K` with the word count. The LEDs change from counting to a walking one, and DONE stays on.
- Then swap back: `rm_count_from_shift.bin` brings the counting LEDs back.
- Stop if: DONE goes low, the current jumps, or the LEDs freeze.

## Stage 4: RISC-V swapping its own custom instruction (rv_pr)
- Load: `openFPGALoader -b arty_a7_35t build/openxc7/rv_soc/rv_pr_xor_c/rv_soc_icapbits.bit`
- `powershell -File host\icap_load.ps1 -Target rvsoc -Custom 12345678,0F0F0F0F -Run -Port COMx` → `1D3B5977` (xor)
- Then each swap below, using `... -Target rvsoc -Partial build\partials\rv_pr\<file> -Custom 12345678,0F0F0F0F -Run -Port COMx`:

| partial | expected result |
|---|---|
| rm_andn_from_xor.bin | 10305070 |
| rm_add_from_andn.bin | 21436587 (uses CARRY4) |
| rm_grey_from_add.bin | 00000000 (greybox) |
| rm_xor_from_grey.bin | 1D3B5977 |

- A timed-out custom instruction returns 00000000, so any wrong or zero result (other than greybox) is a failure. The rv_soc firmware has no status command (only W and C).

## Stage 5: CPU loads partials from flash by itself (rv_flash)
Follow docs/phase6-flash-selfload.md, "Hardware steps", exactly. Key points:
- Dump the flash at 0x400000 first.
- Write the slots at 0x400000/0x410000/0x420000.
- Load `build/openxc7/rv_flash/pr_xor_c/rv_flash_icapbits.bit` to SRAM, not flash.
- Then J, R, C, S 0 + C (10305070), S 1 + C (21436587), S 2 + C (1D3B5977).

Do **not** write offset 0 unless you want this design to boot by itself.

## Stage 6: native-flow partials (in-tool confinement), other regions, BRAM/DSP
These use builds from the patched nextpnr (docs/phase8, 9, 11). Load the matching full bitstream from `build/patched/<design>_native/...`, then send partials from `build/patched/partials/...` the same way as stage 4.
- Order:
  1. rv_pr native (CLB);
  2. rv_b (bottom half);
  3. rv_c (two rows, shared frames);
  4. rv_m (BRAM table plus DSP multiply: check several table entries);
  5. rv_soc2 (two regions: swap each independently, check C and D).
- The exact file list and expected values are in each phase doc.

## Stage 7: Vivado-parity options
- RESET_AFTER_RECONFIG partials (`partial.py --reset-after-reconfig`, docs/phase10): the RM's FFs should come up at their init values after the swap, and the static logic must keep running (the LED counter must not reset).
- Compressed partials (`--compress`): same results as stage 4.

## Stage 8: JTAG partial with patched openFPGALoader
- Command: `build/.../openFPGALoader -b arty_a7_35t --partial <partial.bit>`, using the build from docs/buildenv.md.
- Expected: the same result as the ICAP path, with no JPROGRAM. The DONE LED and static logic stay up.

## Known unknowns this plan settles
- Whether the 3 Vivado ICAP bits are needed (stage 2).
- Whether the run-end pad frame is committed (stages 3 and 4 work either way, because the pad carries the target's own content).
- The pass-1 all-ones minors 24/25 (stage 3 onward).
- What the RESET_AFTER_RECONFIG mask bits mean (stage 7).
- Board current during reconfiguration (every stage).
