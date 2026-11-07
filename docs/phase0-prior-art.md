# Phase 0: prior-art findings (2026-11-04)

Method: repos were cloned with `--filter=blob:none` into `~/open-dfx-xc7/upstream/`. The evidence comes from the source at the commits listed below, plus `gh api` / `gh pr view` (read-only) and web searches. Anything I could not open myself is marked **UNVERIFIED**.

| Repo | Commit read | Notes |
|---|---|---|
| openXC7/prjxray | a5589d51 (2026-11-03) | = nightly's prjxray |
| f4pga/prjxray | c9f02d85 (2025-06-05) | last push 2025-06-05 |
| openXC7/nextpnr | ce3f7c18 (2026-11-03) | = nightly's "nextpnr-xilinx ce3f7c18"; the commit is in **openXC7/nextpnr**, not in openXC7/nextpnr-xilinx |
| openXC7/nextpnr-xilinx | bc9b2346 (2026-09-25) | **archived** |
| gatecat/nextpnr-xilinx | 8f178fc6 (2024-10-11) | |
| f4pga/f4pga-arch-defs | 3d4df2ea (origin/main) | |
| FPGA-Research/byteman | 24752871 (2026-02-20) | |
| trabucayre/openFPGALoader | e3d8d947 (HEAD, read via gh api) | |
| byuccl/maverick | be380664 (2020-05-25) | |

---

## Q1. Project X-Ray

**Verdict: no supported partial-bitstream output on any maintained branch.**

- `xc7frames2bit` always builds a full-device bitstream. It calls `frames.addMissingFrames(part)` to fill every frame in the part (openXC7/prjxray `tools/xc7frames2bit.cc:82`), then `createConfigurationPackage` (`:95`), which is the full-config sequence. Its flags are only `part_name`, `part_file`, `frm_file`, `output_file` and `architecture` (`:18-29`; confirmed with `--helpon=xc7frames2bit` on the nightly binary). It has no partial or region option.
- `xc7patch` reads a base bitstream (`-bitstream_file`), overwrites the frames listed in a `.frm` file, and writes out a full bitstream again with `createType2ConfigurationPacketData` / `createConfigurationPackage` (`tools/xc7patch.cc:21-30, 125-132`). It is a full-bitstream patcher, not a partial writer.
- `fasm2frames --sparse` (`utils/fasm2frames.py:619-620`, "Don't zero fill all frames"): without `--sparse`, every frame of the part is zero-initialised. With it, only frames in tiles the FASM touches are emitted and zero-filled (`prjxray/fasm_assembler.py:47-56`). `--roi design.json` marks the ROI tiles' frames as in use (`fasm2frames.py:272-284`, `fasm_assembler.py:220`). So `--sparse` limits *which frames are listed* in the .frm. Because xc7frames2bit then adds all the missing frames back (`:82`), the result is still a full bitstream.
- `minitests/roi_harness` (README `minitests/roi_harness/README.md:1-5`): it "Creates an harness bitstream which maps peripherals into a region of interest which can be reconfigured". It supports the Arty A7-35T (SWBUT/PMOD/UART). The harness is **built with Vivado**: `runme.tcl:318-323` creates pblock `roi` with `EXCLUDE_PLACEMENT` and `CONTAIN_ROUTING`, and `:588` runs `write_bitstream`. `minitests/partial_reconfig_flow/README.md` says plainly that Vivado's PR flow (UG909/UG947) implements the harness, and that ROI FASM is merged with `fasm2frame`+`xc7patch` into a **full** bitstream (`harness_implement.tcl:140` `HD.RECONFIGURABLE TRUE`).
- **Antmicro 6212c4a7 "WIP partial support"** (Jan Kowalewski, 2020-11-24; https://github.com/f4pga/prjxray/commit/6212c4a73cab16658d8355e6779e5aa9d731a504). It adds `Configuration<Series7>::createPartialConfigurationPackage` (no GRESTORE/START; a FAR+FDRI write per block; then DESYNC) and `xc7frames2bit --partial_bitstream --clb_start_addr/--clb_end_addr/--bram_start_addr/--bram_end_addr`. Status:
  - The object is reachable on GitHub, but it is **not on master** of antmicro/prjxray, f4pga/prjxray or openXC7/prjxray (`git cat-file` fails in all three clones).
  - Its successor is **f4pga/prjxray PR #1492 "Partial bitstream support"** (tmichalak, antmicro:partial-bitstream-support): **OPEN, unmerged**, created 2020-11-10, last updated 2021-12-22, zero comments. https://github.com/f4pga/prjxray/pull/1492
  - The PR has 3 commits (1c079d59 "Enable partial bitstream generation for Series7", 4bab4e7f "...to xc7frames2bit", 161e4f9f test). It changes 5 files, +421/−26, based on 2353b22c (2020-11-20). 6212c4a7 itself is *not* an ancestor of the PR head; it is a WIP predecessor.
  - Hardware validation of the PR is **UNVERIFIED**: the PR shows no test on a board.
- `git log --grep` on f4pga/prjxray finds only the 2018 Vivado-harness work (PRs #33, #55, #63–#69, #71). Issue #62 (2018, closed) "xc7patch needs option to add initialization and finalization sequences".

## Q2. nextpnr (openXC7/nextpnr = what the nightly ships; legacy nextpnr-xilinx)

**Verdict: hooks exist in the generic core. None are wired up for Xilinx and the router doesn't enforce any of them. There is no partial-bitstream output.**

- `docs/netlist.md:27`: a cell `region` constrains *placement* ("e.g. for partial reconfiguration or out-of-context flows").
- `docs/netlist.md:28-41`: PseudoCell API, "implementing partition pins for partial reconfiguration regions" (`getLocation`, `getPortWire`, timing hooks).
- `docs/netlist.md:55`: net `region` is "*N.B. not supported by the current router*".
- `docs/generic.md:40`: pip Loc 'z' "only important if region constraints (e.g. for partial reconfiguration regions) are used".
- `common/kernel/nextpnr_types.h:53-64`: `struct Region { constr_bels, constr_wires, constr_pips, bels, wires, piplocs }`. `constr_wires`/`constr_pips` are only *declared*, set to false in `basectx.cc:119-120`, and bound to Python (`pybindings.cc:259-262`). **No reader exists in `common/route/`** (grep finds nothing). Placers do honour cell regions (`placer_heap.cc:1037-1045,1334`, `place_common.cc:368`, `parallel_refine.cc:200-209`, `placer_static.cc:555`).
- `nextpnr_types.h:293-305`: `struct RegionPlug : PseudoCell` has the comment "TODO: partial reconfiguration region timing". Its only users are in **gowin** (`himbaechel/uarch/gowin/pack.cc:349,384,412`, `globals.cc:1201-1232`). The xilinx uarch doesn't use it.
- Xilinx uarch: the only `createRectangularRegion`/`constrainCellToRegion` use is to keep BUFR/BUFIO sinks in their clock region (`pack_clocking.cc:558,569`). The XDC parser has no `create_pblock`/`resize_pblock` (`xdc.cc` handles `set_property`, `create_clock`, `set_multicycle_path`, ...; selectors are limited to get_ports/get_cells/get_nets, `xdc.cc:118-120,183`).
- There's no "partial"/"reconfig"/"pblock"/"partition" code in `himbaechel/uarch/xilinx/`. The only "partial" hit is a comment about a partial *file* write (`fasm.cc:5470`).
- In the archived legacy openXC7/nextpnr-xilinx (bc9b2346), the same doc text appears (`docs/netlist.md:31,46`, `docs/generic.md:29`) and `constr_wires` exists only in `common/nextpnr.h:284`, `nextpnr.cc:520` and `pybindings.cc:233`. It has no RegionPlug or pblock.
- Historic: YosysHQ commit 84fec7e8 (David Shah, 2020-01-18) "Fixes for partial reconfig demo" touches only `common/router1.cc`/`frontend_base.h`. It isn't a Xilinx flow.
- **ICAPE2 is supported:** `pack_io.cc:1465` `cfg_rules[id_ICAPE2].new_type = id_ICAP_ICAP`; `fasm.cc:3289-3298` emits `ICAP` + `ICAP_WIDTH_X16/X8`. Legacy: `xilinx/pack_io_xc7.cc:1263`. Whether it works on hardware is **UNVERIFIED**.
- **PR #30** (https://github.com/openXC7/nextpnr/pull/30, jrrk2, merged 2026-09-30, merge c68c1358; this is in openXC7/nextpnr, while openXC7/nextpnr-xilinx PR #30 is an unrelated 2024 RAM256X1D fix):
  - `-o preplaced=` pins cells by name to their reference bel.
  - `-o prerouted=` binds each net's reference route `STRENGTH_LOCKED`.
  - `-o holdbufs=` re-creates the reference's hold-fix buffers.
  - Tiles touched by locked routing are closed to new cells.
  - Options are at `himbaechel/uarch/xilinx/xilinx.cc:85-94`, implementation at `:700-885`.
  - The PR's own claims: 0 differing FASM features on a small BSCAN/BRAM test; 27 differing `NOCLKINV` features on a 17k-cell VC707 design. Those numbers come from the PR body (it is AI-assisted, "Generated with Claude Code"). **I have not reproduced them.**
  - Relevance: PR #30 gives *static-side identity*, i.e. the same static bits across builds. It does **not** keep the new logic's routing inside a region, and it doesn't stop new nets from using wires inside the RM region.
- Related open issue: openXC7/nextpnr #36 "region-aware clocking pass" (clock-region work, not PR).

## Q3. F4PGA PR flow

**Verdict: confirmed, it produces full bitstreams only.**

- `docs/bitdoc/prjxray/partial-reconfig.rst` (present on origin/main; last touched 41b3c631, 2022-09-09):
  - lines 4-7: ".. Note:: F4PGA currently does not support partial bitstream generation... partial FASM must be concatenated with an overlay to generate a full bitstream."
  - Flow at lines 43-55 ends "Concatenate FASM ... and generate final bitstream".
  - The example is `xilinx/xc7/tests/switch_processing` (Arty, xc7a50t).
- `common/cmake/devices.cmake:1125-1175` (`add_bitstream_target USE_FASM`) concatenates all included targets' FASM and runs the arch's single `FASM_TO_BIT`.
- PR #1534 "WIP: Partial Reconfiguration Regions" (andrewb1999): **CLOSED unmerged** 2020-07-10. Its body is "Test pull request to invoke CI". https://github.com/f4pga/f4pga-arch-defs/pull/1534. The work later landed as #1587 (overlay generation) and #1649 (docs), both VPR-based.

## Q4. Bitstream / PR tools and vendor dependence

| Tool | Vendor dependence (evidence) |
|---|---|
| **byteman** (Apache-2.0, active 2026-02) | byteman itself needs no vendor tool. It **writes region-only Series-7 bitstreams**: `-output ... <StartY> <StartX> <SizeY> <SizeX>` (README "-help output"). `src/Devices/Xilinx/Series7/XS7_Output.cpp:54` adds GRESTORE only `if(fullBitstream)`, and `:155` has a `partialNotFull` path. Arty A7-35 / XC7A35 are listed. All of its examples start from vendor `.bit` files. **Nobody has been shown to feed it openXC7/prjxray bitstreams** (no GitHub hits for byteman+nextpnr/prjxray). It is a bitstream manipulator, not a PR flow: it does no routing isolation and no static/RM implementation. |
| BitMan (khoapham/bitman, last push 2020-03) | README:21-32: relocate/merge/extract regions; "Write module bitstream into partial file". It works on vendor-generated bitstreams; the DATE'17 paper says it targets bitstreams from "ISE and Vivado" (https://past.date-conference.com/proceedings-archive/2017/html/0138.html). For 7-series, operations are limited to one clock-region height. |
| GoAhead | Per the UiO project page and FCCM'12, it "interacts with the Xilinx vendor tools and triggers the physical implementation phases all the way down to the final configuration bitstreams" (https://mn.uio.no/ifi/english/research/projects/cosrecos/goahead). Vendor-dependent. |
| EFCAD (khoapham/efcad, 2019) | README:9-11: "Architectural model generated initially by Xilinx Vivado tool and extracted by GoAhead"; bitstreams by BitMan; shell by ZUCL. Vendor-dependent. |
| ZUCL (zuclfpl/zucl_fsp, 2020) | Zynq US+ only. The README flow merges `{module}_full.bit` (vendor-built) into a static bitstream with `bitman.exe`. It moved into FOS (khoapham/fos). Vendor-dependent. |
| IPRDF | "IPRDF: An Isolated Partial Reconfiguration Design Flow for Xilinx FPGAs", MCSoC 2018, DOI 10.1109/MCSoC2018.2018.00018 (Crossref). **Full text not accessible (ResearchGate 403); vendor dependence UNVERIFIED.** The title says it is a design flow *for Xilinx FPGAs*. |
| RapidWright (Xilinx, active) | README:9-10: "a new bridge to Vivado through reading and writing design checkpoint (DCP) files". It has `rwroute/PartialDFXRouter.java`. `util/RelocateBitstreamByRow.java` is UltraScale/US+ only. Device data and final bitstreams come from Vivado. Vendor-dependent. |
| **Maverick** (byuccl/maverick, FCCM'19, last push 2020-05) | Closest prior art. Yosys + RapidSmith2 + Project X-Ray compile an RM to a **partial bitstream** without vendor tools, but the README "Static Design Phase" step 1 is "Use Vivado's PR flow to create an initial static design... Generate an initial full and partial bitstream". `byuccl/prjxray@0fb0991d tools/xc7PartialPatch.cc:27` takes that Vivado partial `bitstream_file` and patches frames into it (FAR hardcoded `0x1000000`, `:213-219`). Tested on XC7Z020. Vivado is needed for the static design and the template partial. |

## Q5. Searches

- GitHub repo/issue searches found no open-flow 7-series PR project. Terms: "open-source partial reconfiguration", "nextpnr partial reconfiguration", "openxc7 partial", "partial bitstream prjxray", "byteman nextpnr", "DFX open source", plus the openXC7/f4pga/YosysHQ issue trackers. Only related: openXC7/scratchpad#1 (fuzzer ROI question, 2022) and f4pga/prjxray#1490 (PR bitstream size question, 2020).
- Web/arXiv searches for 2024-2026 FPL/FCCM/FPT found no Vivado-free 7-series PR flow. They surfaced arXiv 2408.08626 (cross-chip PR via the Linux FPGA manager; vendor bitstreams), OpenPR (ISE era) and PR-ESP (Columbia; Vivado-based). **Caveat:** I could not search the proceedings indexes directly (dblp blocked the fetch), so coverage of paywalled FPL/FPT 2025-26 papers is incomplete.
- **Dreams (TU Dresden):** not confirmed. "DREAMS" (Otero et al., SPIE 2013, UPM Madrid) and "DReAMS" (a DRESD/Politecnico di Milano branch) exist; neither is TU Dresden or open-flow. **UNVERIFIED / likely a name conflation.**
- **AutoPR:** no project found. **UNVERIFIED.**
- **PR-HMPSoC:** Nguyen & Kumar, FPL 2014 (DOI 10.1109/FPL.2014.6927492), listed on the TU Dresden research portal (https://fis.tu-dresden.de/portal/en/publications/prhmpsoc(80cb2caa-20d0-427b-9abf-2483075c831b).html). It's a MicroBlaze/NoC architecture built on the vendor flow. No code found. (This may be the "Dresden" item.)
- **BitMaT:** Virginia Tech thesis, "BitMaT - Bitstream Manipulation Tool for Xilinx FPGAs", targets Virtex-II (https://vtechworks.lib.vt.edu/items/52f427a2-b1b3-4083-a805-08dd14e73a04). Not 7-series and not an open flow.

## Verdict: GO (no STOP condition found)

No open project produces working 7-series partial bitstreams with zero vendor tools, and no active effort is visible.
- Maverick needs a Vivado static design and template partial, and has been dormant since 2020.
- F4PGA's flow only produces full bitstreams.
- prjxray PR #1492 has been dormant since 2021.
- byteman/BitMan are writers or manipulators that have only been shown on vendor bitstreams.

### Precise gap
1. **Implementation (nextpnr, openXC7/nextpnr himbaechel xilinx):**
   - a. no pblock/region XDC;
   - b. the router doesn't enforce `Region::constr_wires/constr_pips`, so static nets can cross the RM region and RM nets can leave it;
   - c. no partition pins (RegionPlug exists, gowin only);
   - d. no RM-against-locked-static build mode with region-confined routing. PR #30 provides the "locked static" half.
2. **Bitstream:** no merged open 7-series partial-bitstream writer driven by an open flow. Candidates to *reuse rather than rewrite*: prjxray PR #1492 (reviving it upstream is a natural contribution), byteman's `-output <rect>`, and Maverick's xc7PartialPatch as a reference.
3. **Loading:** openFPGALoader `Xilinx::program_mem` always issues JPROGRAM (`src/xilinx.cpp:978` at e3d8d947), which clears configuration memory. Issue #367 "Support load partial bitstream" is open (https://github.com/trabucayre/openFPGALoader/issues/367).
4. **End-to-end:** nobody has demonstrated Yosys → nextpnr → prjxray → partial .bit → JTAG/ICAPE2 swap on hardware with no Vivado step.

### Implication for Phase 3
Rather than writing a fresh Python partial-bitstream writer, first evaluate (a) PR #1492 rebased on openXC7/prjxray and (b) byteman `-output` on openXC7 full bitstreams. A Python writer stays useful as an independent cross-check against Vivado DFX output.
