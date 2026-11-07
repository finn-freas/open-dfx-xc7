# PROGRESS

## Current status (2026-11-05, evening). Everything is offline; nothing has run on hardware.
- **Feature checklist against Vivado DFX:** docs/dfx-vs-vivado.md.
- **Default flow:** native confinement in a patched nextpnr (docs/phase8, 9, 11).
  - Regions: CLB only, bottom half, two clock rows (shared frames), CLB+BRAM+DSP, and two independent partitions.
- **Fallback flow:** stock openXC7 with the external confinement scripts (docs/phase3–7).
- **Partial format:** on Vivado's own full bitstreams, partial.py output is word-identical to Vivado's partials in every reference: default, RESET_AFTER_RECONFIG, compressed, both together; CLB, BRAM/DSP and two-row regions.
  - The one deliberate exception is the run-end pad frame: we write the static content, Vivado writes zeros (docs/phase10).
- **Loading:** ICAP over UART, ICAP from SPI flash with the CPU loading its own partials (docs/phase6), and patched openFPGALoader --partial (JTAG trace on a virtual TAP only).
- **Rebuild from scratch:** `DRY_RUN=0 flow/full_check.sh` (2026-11-05, logs build/full_check/):
  - regress: 11/11 pairs show static identical outside the region;
  - partials: 24/24;
  - byteman against the original target: 24/24;
  - icapbits: 8/8;
  - gl_sim: 33/33, plus greybox 11/11;
  - region2v: 48 PASS, and the 4/4 corrupted controls are detected.
- **Native rv_pr:** 42/42 (docs/phase8). Native rv_b, rv_c and rv_m, and rv_soc2: all checks pass (docs/phase9, 11).
- **Board day:** docs/hardware-test-plan.md, ordered, with expected values and stop conditions.
- **Unknown until hardware:**
  - the 3 Vivado ICAP bits (the bit order itself matches UG470);
  - whether the pad frame is committed;
  - the meaning of the RAR mask and pass-1 minors 24/25;
  - board current during reconfiguration.
- **Upstream:** every patch is a local draft in docs/drafts/. Nothing has been posted.

## Done
- Phase 0 prior-art gate. Full findings with evidence: `docs/phase0-prior-art.md`.
- Upstream clones (blob:none) in `upstream/`: f4pga/openXC7/antmicro prjxray, openXC7/nextpnr, openXC7 + gatecat nextpnr-xilinx, f4pga-arch-defs, byteman. PR #1492 is fetched as branch `pr1492` in `upstream/f4pga_prjxray`.

## Verified (in code)
- prjxray (openXC7 a5589d51 and f4pga c9f02d85): xc7frames2bit and xc7patch emit only full bitstreams. The partial work (6212c4a7 → f4pga/prjxray PR #1492) is open and unmerged, last touched 2021.
- nextpnr (openXC7 ce3f7c18): cell regions constrain placement only. `Region::constr_wires/pips` are never read by any router. RegionPlug (partition-pin pseudo-cell) is used only by gowin. There is no pblock XDC. ICAPE2 is packed and written to FASM.
- f4pga-arch-defs PR doc: "does not support partial bitstream generation"; PR #1534 was closed unmerged.
- byteman writes region-only Series-7 bitstreams itself. Maverick needs a Vivado static design and partial template.
- openFPGALoader always issues JPROGRAM before a JTAG load.

## Verdict
GO (see docs/phase0-prior-art.md). Phase 1 approved and started 2026-11-04.

## Phase 1 (done, hardware load pending)

### Toolchain, pinned
- toolchain/openxc7 (link to ~/xc7-qor/toolchain/openxc7-20261104/root), nightly upstream-2026-11-04:
  - nextpnr-xilinx ce3f7c18
  - prjxray a5589d51
  - prjxray-db a8b09269
  - fasm 2f57ccb1
- toolchain/oss-cad-suite 20261021: Yosys 0.70+186 (3718f7f13), openFPGALoader v1.2.0.
- byteman 1.3 build 226, built from FPGA-Research/byteman 24752871 into toolchain/byteman-build.

### Board and part
- Project X-Ray has Arty harness configs: minitests/roi_harness/arty-*.sh, with XRAY_PART=xc7a35tcsg324-1.
- xc7a35tcsg324-1 is in the openXC7 parts inventory (it uses the xc7a50t chipdb).

### Blinky, openXC7 (verified by build)
- Build: flow/build_openxc7.py blinky --run, output in build/openxc7/blinky/xc7a35tcsg324-1_s1/.
- Resources: 56 LUTs, 28 FFs, 7 CARRY4.
- Timing: nextpnr reports 372.58 MHz against a 100 MHz target.
- Bitstream: 2,192,181 bytes. byteman parses it without errors.
- Not loaded on hardware; there is no board yet.

### Blinky, Vivado (reference only, verified by build)
- Vivado v2025.2 (64-bit), SW Build 6299465, ML Standard, installed at C:\AMDDesignTools\2025.2. 2026.1's free BASIC tier excludes DFX (UG973 2026.1).
- Scripts: vivado/run_vivado.ps1 (Windows, DryRun by default), vivado/build_full.tcl, vivado/ingest.py. Results in build/vivado/blinky/.
- Resources: 1 LUT, 28 FFs, 7 CARRY4 (util.rpt).
- Timing: WNS +7.461 ns at 100 MHz (timing.rpt).
- Bitstream: 2,192,130 bytes, written with a .ll logic-location file.

### Cross-check: prjxray-db decodes both bitstreams (verified by run)
- flow/bit2fasm.py runs bitread and bit2fasm's bits_to_fasm directly. The packaged bit2fasm's shell=True call hits a hardcoded /nix/store sh path.
- Results in build/compare/blinky/. Both bitstreams have 5408 configuration frames.
  - Vivado: 510 FASM lines, 0 unknown bits.
  - openXC7: 526 FASM lines, 0 unknown bits.
- So prjxray-db a8b09269 accounts for every bit Vivado set for this design on xc7a35t.

### Phase 1 status
- Done 2026-11-04, except the hardware load (no board).
- Phase 2 started on the user's standing instruction to continue through phases.

## Phase 2: Vivado DFX reference, analysed (done offline)
- Full write-up with evidence: docs/phase2-vivado-partial.md.
- Region SLICE_X12Y100:SLICE_X15Y149 = 72 frames (columns 10 and 11, top row 1). The first choice, X8..X11, split an INT pair, and Vivado refused it.
- Vivado partial:
  - packet sequence: RCRC, IDCODE, CTL0 writes, two FDRI passes of 73 frames, CTL0, FAR, CRC, DESYNC;
  - no START/GRESTORE;
  - the CRC rule is verified.
- Pass 2 equals the full bitstream's region frames.
- Pass 1 has the same logic, only the 24 static route-through pips, and minors 24/25 all-ones. The all-ones bits are undocumented in prjxray-db (12,800 unknown bits).
- flow/partial.py reproduces Vivado's partial from Vivado's full bitstream except 13 pass-1 words (pip-ownership choice).

## Phase 3: open-tools swap (done offline; hardware pending)
- Full write-up and exact hardware commands: docs/phase3-open-swap.md.
- flow/build_pr.py does five things:
  - synthesizes the static design once;
  - synthesizes the RMs out of context;
  - links the netlists;
  - pins the RM shell and fills the region with blocker LUTs;
  - replays static placement and routing (PR #30).
- Result: configurations A and B differ in 16 frames, all inside the region, 0 outside (flow/pr_check.py).
- Open partials build/partials/open_{shift,count}.bit:
  - region gate passed;
  - CRC passed;
  - the simulated load A+partial(B) equals B exactly.
- Not done: the JTAG load. There is no board, and openFPGALoader needs the drafted `--partial` patch, which isn't built (no cmake, libftdi or libusb headers here).

## Self-loading path (designs/pr_uart, done offline)
- A UART-to-ICAPE2 bridge in the static part. It passes simulation.
- The open PR build gives static frames identical outside the region.
- Partials are written with .check.json safety records. host/icap_load.ps1 refuses unchecked or tampered partials; this was tested.
- This is the preferred first hardware test, with the stock openFPGALoader (docs/phase3-open-swap.md).

## ICAPE2 bits (verified by Vivado vs prjxray decode)
- Vivado sets 3 bits in CFG_CENTER_MID that prjxray-db does not know (26_2206, 26_2207, 27_2205) for every ICAP_WIDTH.
- openXC7 does not set them.
- A variant with the bits set is ready for the hardware test (docs/drafts/prjxray-db-icap-bits.md).

## Phases 4 and 5 (offline; see docs/phase4-5-status.md)
- Phase 4 confinement is done without modifying nextpnr:
  - rm_place.py pins the RM cells inside the region;
  - region_route.py routes the RM nets through region INT tiles only;
  - nextpnr takes both as -o preplaced/-o prerouted (0 collided).
  - CARRY4 RMs work: packer-made carry and DI feed-through LUTs are pinned via `--pack-only` (packer_pins.py).
- RISC-V SoC (PicoRV32 + PCPI custom-instruction slot), `build_pr.py --design rv_pr --run`:
  - xor/andn configurations: static identical outside the region (71 frames differ, all inside);
  - partials pass the region gate and CRC, and the simulated swap is exact;
  - 160 MHz against 100 MHz;
  - hardware steps are in docs/phase4-5-status.md.

## Phase 6: CPU loads partials from SPI flash itself (offline; docs/phase6-flash-selfload.md)
- designs/rv_flash: firmware 'S n' checks the slot header and sum, then streams flash → ICAP. 'A' loads the slots in turn and runs custom0 after each.
- Sim: the ICAP word stream is identical to the partial (sha256 match). Erased and bit-flipped slots are rejected before any ICAP write.
- Open PR build: static identical outside the region, 152 MHz.
- rm_bridge_fenced fixes the late-answer-after-timeout tagging.
- STARTUPE2/USRCCLKO is supported by openXC7 (built and decoded). The Arty also routes SCK to L16 (not checked against the schematic).

## Phase 7: any region, shared frames, static routing (offline; docs/phase7-regions.md)
- Region is a per-design setting; the shell is generated for it.
  - rv_b (bottom half) and rv_c (spans two clock rows, 144 frames): static identical outside the region; partials exact.
- Shared frames: rv_c's first build put the CPU register file (LUTRAM) in frames the partial rewrites.
  - partial.py now refuses that case (negative test: refused).
  - gen_shell2 adds keep-outs.
  - Pass-1 all-ones is limited to region words (aligned partials byte-identical to before).
- rm_place handles INV (as LUT1).
- New RMs rot/popc/minmax. rot fails to route in replay because 545 static nets cross the region. Built first (no fixed static), it routes in 7 iterations.
  - flow/static_detour.py re-routes static around the region: A* with rip-up rounds; constants, clock and RM egress are kept; LUT route-throughs in the region are handled. In progress.

## Verification added 2026-11-05
- flow/gl_sim.sh: real firmware on each linked gate-level netlist; 66/66 custom0 vectors pass (6 RMs × 11). Only funct=0 is exercised.
- flow/byteman_check.sh: byteman, an independent tool, applies each partial to its base. 18/18 match byteman's own round trip of the target in the 5295 frames byteman writes; strengthened: the 113 frames byteman omits are kept from the base (asserted equal in base and target), then compared with the ORIGINAL target: 18/18 match in all 5408 frames. A wrong-target control differs in 72 frames.
  - Correction (found by the fasm2bels check): byteman's full output omits 113 of the 5408 frames. Those are I/O column 43 of row 0 and column 37 of top row 1, far from the region.
  - So this check covers 5295/5408 frames, including all region frames. The real partials never pass through byteman.
- flow/bit2netlist.sh: f4pga fasm2bels 24d1e31a rebuilds a netlist from the bitstream alone, and the firmware test runs on it. Three launcher-side patches: ICAPE2 stub; orphan REGCLK allowed by an allow-list; zero-source BRAM pins.
  - rv_pr xor/andn/add full bitstreams: 11/11 each.
  - 31 byteman-applied bitstreams: 11/11 each. The frames byteman omitted are filled from the base; each filled frame is asserted identical in base and target.
  - Negative controls fail.
- flow/region2v.py: region bits → netlist from prjxray-db only. Sim (3582 vectors) plus Yosys SAT equivalence against the RTL: all builds and byteman results PASS/PROVED; 6/6 corrupted controls detected.
- Agents in progress:
  - flow/region2v.py: region bits → netlist → sim against the RTL;
  - fasm2bels on whole bitstreams;
  - build env plus compiling the nextpnr/openFPGALoader drafts;
  - Vivado gap analysis (docs/gap-vivado.md).

## Drafts for the user (nothing pushed or posted)
- docs/drafts/prjxray-db-icap-bits.md: issue draft.
- docs/drafts/nextpnr-router-region.{md,patch}: router confinement (being drafted).
- docs/drafts/openfpgaloader-partial.{md,patch}: local branch partial-load in upstream/trabucayre_openFPGALoader. It passes a syntax check only.
- docs/drafts/nextpnr-pblock-xdc.{md,patch}: local branch pblock-xdc in upstream/openXC7_nextpnr. It is not compiled (no boost/eigen); it was syntax-checked against stub headers.

## Blocked on the user
- A board (Arty A7-35T). The hardware test is deliberately deferred until the offline evidence is complete (user, 2026-11-05).
- The build environment and safe package installs are allowed (user, 2026-11-05). Fetches may still need the user to run `! git clone` when the permission classifier blocks them.

## Open questions
- Board not bought yet (Arty A7-35T planned).
- Does byteman produce a correct region-only partial from an openXC7 bitstream? Parsing works (blinky). This is no longer on the critical path: flow/partial.py writes partials.
- Does ICAPE2 from nextpnr work on hardware (Arty)? Does the FASM need any extra bits?
- Can openFPGALoader load a partial bitstream? Not as-is (JPROGRAM at src/xilinx.cpp:978). A `--partial` patch is drafted. OpenOCD `virtex2` with `-no_jstart` is unverified.
- Does PR #1492 rebase onto openXC7/prjxray (which has changed xc7frames2bit since: findFramesNotInPart, input checks)?
- PR #30 replay with OOC-synthesized RMs gave 0 static diffs on pr_open. Larger designs are untested.
- Static routes through the RM region: they are replayed, and partial pass 1 keeps exactly those pips.
- CTL0 0x100/0x400 meaning; the minor 24/25 all-ones in pass 1; whether the run-end pad frame is committed (docs/phase2-vivado-partial.md).
- Is UG470 ch.5 RCRC/no-GRESTORE sequencing plus the GSR/GLUTMASK behaviour needed for LUTRAM/SRL in the RM?
- IPRDF (MCSoC 2018) full text was not read; AutoPR and "Dreams (TU Dresden)" were not found.

## Gap analysis vs Vivado (2026-11-05, offline)
- Write-up: docs/gap-vivado.md. Primitive table, QoR table and prioritised gaps, all from runs in build/gap/.
- Scripts: flow/gap_designs.py, flow/gap_build.py, flow/gap_report.py, flow/gap_xadc_segbits.py, vivado/build_gap.tcl, vivado/run_gap.ps1. Designs are in designs/gap/.
- openXC7 build failures:
  - FIFO18E1/36E1 and XADC have no bel;
  - BUFH loads are placed outside the clock region;
  - BUFIO/BUFR inputs get a yosys BUFG when the pin also clocks fabric;
  - ISERDESE2 constant ties do not route;
  - MUXF7 dual fanout fails to place.
- Silent differences:
  - DSP MASK[47:46] and AREG/BREG_1;
  - DIFF_TERM;
  - IOBUF DRIVE parameter;
  - DNA_PORT CFG bits.
- Drafts:
  - nextpnr-dsp-mask-areg, nextpnr-iserdes-const-pins (patches, not compiled);
  - prjxray-db-vivado-unknown-bits.md;
  - prjxray-db-xadc-init.segbits (512 XADC INIT bits, mapped from 11 Vivado builds).

## Phase 9: native flow on rv_b/rv_c, BRAM/DSP region (offline; docs/phase9-native-bram-dsp.md)
- build_pr_native.py takes --design rv_pr|rv_b|rv_c|rv_m. rv_b, rv_c: 0 static pips in region, 0 RM pips outside, static identical, native_check 9/9 each. rv_c uses an empty exclusive pblock over the shared SLICEMs (no-pblock control: partial refused).
- Region spec now takes RAMB36/RAMB18/DSP48 ranges. rv_m = SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59 with BRAM+DSP RMs (tbl, tbl2) and xorc: static identical, native_check 12/12 incl. BRAM INIT vs yosys and a 1024-entry table sweep; needs the nextpnr draft docs/drafts/nextpnr-pblock-replay.patch.
- Vivado DFX reference with BRAM/DSP analysed (designs/dfx_bram, dfx_bram_pad); partial.py matches Vivado's packet layout, pass 2 and the BRAM bursts word for word; partial.py gained a refusal for frames holding static LUTRAM/SRL/BRAM state.
