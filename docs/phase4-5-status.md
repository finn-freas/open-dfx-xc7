# Phases 4 and 5: status (offline work, 2026-11-05)

Everything here was built with the open tools only. Vivado was not used. None of it has run on hardware, because there is no board yet.

## Phase 4: confinement without modifying nextpnr
- **Placement: flow/rm_place.py.** It pins every RM cell (LUT1–6, FD*E, CARRY4) to legal bels in the region. The region stays closed to unpinned cells through the blocker shell. It respects these nextpnr behaviours (read at ce3f7c18):
  - pack.cc `pack_lutffs` (around line 460) clusters an FF with the LUT O6 or CARRY4 O[z] that drives its D, without checking the FF's BEL. rm_place pairs the same way, and the shells put an output-anchor LUT before each output FF.
  - pack_carry.cc (around line 225) builds new CARRY4 cells `<orig>$split$muxcy0$PACKED_CARRY4$` without the BEL. rm_place writes preplaced entries under those names.
  - Yosys auto names collide between separately synthesized netlists. RMs are renamed `rmx_N`.
  - Cells go next to the pinned cells they connect to (affinity placement).
- **Routing: flow/region_route.py.**
  - It takes the RM nets of a build and keeps their pin heads and tails, which lie in region CLB tiles.
  - It re-routes the fabric part by BFS over pips of the region's INT tiles only. Pseudo-pips and non-directional pips are excluded. Nodes come from tileconn.json by union-find. Nodes used by static nets or by other RM nets are avoided.
  - The routes go back to nextpnr as `-o prerouted`, in nextpnr's own pip names `X<gx>Y<gy>/<dst>/<src>`.
  - Because only region pips are used, no RM configuration bit can land in a static frame.
- **flow/build_pr.py** runs all of this (CONFIG confine=True). The confined builds are `<design>_<rm>_c`.

## Phase 5: RISC-V with a reconfigurable custom instruction (`flow/build_pr.py --design rv_pr --run`)
- **Static part:**
  - PicoRV32 ef203c2b with PCPI. custom-0 is bridged to rm_slot (valid, funct[10], rs1, rs2 → rd, ready), with a 64-cycle timeout.
  - 8 KiB BRAM firmware (flow/rvasm.py), UART and ICAPE2 MMIO.
  - Simulations pass (designs/rv_soc/run_sim.sh, docs/phase5-rv-soc.md).
- **RMs:** xor (rd = rs1 ^ rs2) and andn (rd = rs1 & ~rs2, or rs1 | ~rs2 when funct[0]).
  - Bit-sliced shell: 75 input anchors, 33 output anchor/FF pairs, 82 blockers.
  - 32 LUTs each, placed by rm_place.
- **Results (verified by run):**
  - Static replay: 2840 cells pinned (BRAMs as `RAMB36E1~RAMB36E1` plus LOC).
  - Pre-routes: 3271 nets (static plus all RM nets), 0 collided, 0 pruned.
  - region_route: 129 and 97 fabric connections, 0 unroutable.
  - Timing: 160 MHz against 100 MHz.
  - flow/pr_check.py, xor_c vs andn_c: 71 frames differ, all inside the region. The static part is identical outside it.
  - Partials build/partials/rv_pr/rm_<target>_from_<base>.bin (flow/make_partials.sh; every pair simulated exact, and a target's partial is byte-identical whatever the base):
    - two-pass, with 317/402 RM pips held back in pass 1;
    - region gate passed and CRC valid;
    - simulated load in both directions is exact;
    - .check.json safety records written.
- **Hardware steps (not run, no board):**
  1. `openFPGALoader -b arty_a7_35t build/openxc7/rv_soc/rv_pr_xor_c/rv_soc_icapbits.bit` (stock loader; full bitstream plus the 3 Vivado ICAP bits, made by flow/icap_variant.sh; rv_soc.bit is the fallback).
  2. `powershell -File host\icap_load.ps1 -Target rvsoc -Custom 12345678,0F0F0F0F -Run -Port COMx`. Expected result: 1D3B5977 (xor).
  3. `powershell -File host\icap_load.ps1 -Target rvsoc -Partial build\partials\rv_pr\rm_andn_from_xor.bin -Custom 12345678,0F0F0F0F -Run -Port COMx`.
     - The CPU writes the partial into its own ICAP, then runs custom0 again.
     - Expected result: 10305070 (andn = 0x12345678 & ~0x0F0F0F0F).
  - Safety: watch board current on a USB power meter, and unplug if it jumps.
  - Untested on silicon, any of which could make step 3 fail:
    - the ICAP byte bit-swap;
    - the 3 Vivado-only ICAP bits (docs/drafts/prjxray-db-icap-bits.md);
    - the minor 24/25 all-ones pass-1 pattern.

## CARRY4 RMs (fixed)
- **Cause:** pack_carry.cc creates DI feed-through LUTs (pack.cc:129 `feed_through_lut`, named `<net>$LUT$<carry>$DI[z]`, placed on the 5LUT of position z). They have no BEL, so the closed-tile rule rejects them, and the CARRY4 site fails. The error did not say this.
- **Fix:** flow/packer_pins.py runs `nextpnr --pack-only`, finds the packer-made CARRY4s and feed-through LUTs by name, and pins them to the carry slice rm_place chose.
- **Results:**
  - pr_add (4-bit adder): static identical outside the region.
  - rv_pr add (32-bit, 8 CARRY4 + 40 packer cells pinned): static identical against xor; partial build/partials/rv_pr/rm_add_from_xor.bin passes the region gate and CRC, and the simulated load from xor is exact.
  - Expected custom0(0x12345678, 0x0F0F0F0F) after loading rm_add: 0x21436587.

## Still open
- **Upstreaming:** the confinement lives outside nextpnr. The proper upstream form is router region support; that is drafted in docs/drafts/nextpnr-router-region.* and the pblock patch, and is uncompiled.
- **Timeout tagging:** a timed-out custom instruction plus a late RM answer could be taken by the next instruction (agent note, docs/phase5-rv-soc.md).
