# Phase 2: Vivado DFX reference bitstreams, analysed

All numbers below are from runs in this repo. The tools are Vivado v2025.2 (SW Build 6299465, ML Standard) for the reference, and flow/bitparse.py, flow/region.py and flow/partial.py for the analysis. UG470 text was not consulted in this pass (it was not fetched), so register meanings are given as raw values unless stated.

## Reference design
- designs/dfx_ref:
  - static part: a 28-bit counter and a 4-bit LED register;
  - reconfigurable slot: u_rm (rm_slot);
  - two reconfigurable modules: rm_count (dout <= din[7:4]) and rm_shift (dout <= 1 << din[7:6]);
  - plus a greybox.
- vivado/build_dfx.tcl: the UG909 non-project flow. Output is in build/vivado/dfx_ref/.
- Pblock: SLICE_X12Y100:SLICE_X15Y149, in clock region X0Y2 (one clock region tall). It has RESET_AFTER_RECONFIG false and SNAPPING_MODE OFF.
- The first pblock tried was SLICE_X8Y100:SLICE_X11Y149. Vivado rejected it with Constraints 18-993, because it split the interconnect pair INT_L_X6/INT_R_X7, and placement then failed.
  - Rule: a region edge must not separate INT_L_X(2k) from INT_R_X(2k+1).
  - Tile layout from tilegrid.json: CLB_L | INT_L_X2k | INT_R_X2k+1 | CLB_R.
- pr_verify: count, shift and grey are compatible. It compared 13 partition pins, 204 static tiles and 424 static pips (pr_verify.rpt).

## Frames the region owns
- Region frames: flow/region.py --list gives 200 tiles (50 each of CLBLM_L, CLBLM_R, INT_L and INT_R).
- They map to 72 frames: CLB_IO_CLK, top half, row 1, column 10 minors 0..35 and column 11 minors 0..35.
- Every frame also carries word 50, which holds the HCLK row and the frame ECC in bits 12:0.
  - So 52 of the 72 frames carry words that belong to tiles outside the 200.
  - In every partial seen, those words hold the static values.
- Vivado's full bitstreams for count, shift and grey differ from each other in 53 to 56 frames, all inside the region. None differ outside it (flow/pr_check.py logic, ECC masked).

## Packet sequence of a Vivado partial (cfg_rm_count_pblock_rm_partial.bit, 59,400 bytes)
- Header field a: `top;UserID=0XFFFFFFFF;PARTIAL=TRUE;Version=2025.2`.
- Before the sync word: 8 x FFFFFFFF, then 000000BB 11220044 (bus-width detect), then 2 x FFFFFFFF, then AA995566.
- After sync, word by word:
  1. NOOP, CMD RCRC, NOOP x2.
  2. IDCODE 0x0362D093.
  3. CMD NULL.
  4. MASK 0x100, CTL0 0x100.
  5. MASK 0x400, CTL0 0x400.
  6. Pass 1:
     - CMD WCFG, NOOP, FAR 0x00020500, NOOP;
     - FDRI as a type-1 header with 0 words, then a type-2 header with 7373 words (73 frames).
  7. Pass 2: the same packet layout again.
  8. MASK 0x100, CTL0 0x000.
  9. FAR 0x03BE0000.
  10. CRC 0xF405B482, which matches the CRC computed by bitparse.py.
  11. CMD DESYNC, then 16 NOOPs.
- No START, GRESTORE, SHUTDOWN or GCAPTURE command appears. The full-bitstream sequence (blinky) does contain GRESTORE, LFRM and START.
- CRC rule, verified on two full bitstreams and on this partial:
  - CRC-32C over (5-bit register address, 32-bit data) for each word written;
  - reset by CMD RCRC;
  - compared and then reset at each CRC write.
  - This is the same as prjxray's icap_crc.

## The 73rd frame
- After 72 region frames, each pass writes one more frame, at 0x00020600 (column 12 minor 0). That address is the next one in frame order and lies outside the region.
- In the Vivado partial that frame is all zero, and the full bitstream also has zero there.
- It is consistent with a frame-buffer flush. Whether the device actually commits it was not determined.
- flow/partial.py therefore writes the full bitstream's own content for that frame, which is safe either way. Its gate refuses any outside frame that is not such a pad.

## The two passes (main finding)
- Pass 2 is word-identical to the region frames of the matching full bitstream: 153/153, 175/175 and 196/196 non-zero words for count, shift and grey.
- Pass 1, decoded through prjxray-db (reconstructed full bitstream, then bit2fasm):
  - The CLB (logic) features are identical to pass 2.
  - Its routing pips are a subset of pass 2: the same 24 pips in all three configurations. These are the static routes through the region.
  - Pass 2 adds 49, 36 and 35 pips for count, shift and grey.
  - Minors 24 and 25 of both region columns are written as 0xFFFFFFFF in every word except word 50, with a valid ECC. prjxray-db decodes those as 12,800 unknown bits.
  - segbits_int_l.db has 1536 entries that use bits in minors 24/25, so these frames hold interconnect mux bits.
  - The all-ones state is not a documented configuration in prjxray-db.
  - Interpretation, not verified against UG909/UG470 or on hardware: pass 1 parks the RM's interconnect in a state that drives nothing while it keeps the static route-through pips, and pass 2 then enables the new routing. This avoids transient contention while columns are rewritten one after another.
- Reproduction by flow/partial.py, run on Vivado's full cfg_rm_count.bit with the pass-1 pip set taken as the pips common to all three configs:
  - output is 14805 words, the same length as Vivado's;
  - pass 2 and the packet layout are identical;
  - 13 words differ in pass 1, plus the CRC word that depends on them.
  - The 13 words are pips common to all three configurations that Vivado nevertheless holds back, because it knows which nets own them.
  - The open flow uses the static nets' own pips (from the replay file) instead, which is the same ownership rule.

## Open questions from Phase 2
- What do CTL0 bits 0x100 and 0x400 do during the partial, and why does the end of the stream clear only 0x100? This needs UG470 table 5-25 (not fetched).
- Is the all-ones minor 24/25 pattern required? Is it specific to CLB columns? What is written for BRAM/DSP columns?
- Does the 73rd frame get committed?
- RESET_AFTER_RECONFIG true and compression were not tried. Both are expected to change the sequence (GRESTORE/GSR masking, MFWR).
