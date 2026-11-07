# DRAFT issue (not posted): ICAPE2 instances set 3 CFG_CENTER_MID bits that prjxray-db does not document

Target repo: openXC7/prjxray-db, or f4pga/prjxray-db; possibly openXC7/nextpnr-xilinx as well. Posting needs the user's approval.

## Observation
- Part: xc7a35tcsg324-1 (fabric xc7a50t). prjxray-db revision a8b09269.
- Vivado v2025.2 (SW Build 6299465) builds of one ICAPE2 instance, decoded with prjxray bit2fasm --verbose, show three unknown bits in tile CFG_CENTER_MID_X46Y32, segment 0x00400900:
  - `26_2206` (bit 0040091a_68_30)
  - `26_2207` (bit 0040091a_68_31)
  - `27_2205` (bit 0040091b_68_29)
- The same three bits are set for ICAP_WIDTH X32, X16 and X8. X16 and X8 additionally decode as the known `ICAP.ICAP_WIDTH_X16` / `ICAP.ICAP_WIDTH_X8`.
- A design without ICAPE2 (blinky) has 0 unknown bits.
- The bits sit directly next to the documented ICAP_WIDTH bits:
  - X16 = 26_2199 27_2200 27_2201
  - X8 = 26_2203 26_2204 27_2202
- nextpnr-xilinx (openXC7 ce3f7c18, himbaechel/uarch/xilinx/fasm.cc:3289-3298) writes only ICAP_WIDTH_X16/X8 for an ICAP. So an openXC7 ICAPE2 bitstream does not have these bits.

## Reproduce
- designs/icap_probe{,_x16,_x8}: ICAPE2 fed from a counter, O xor-ed to LEDs.
- Run vivado/run_vivado.ps1 -Design icap_probe -Run, then flow/bit2fasm.py --verbose.

## Not known
- Whether ICAPE2 works on silicon without these bits. This has not been tested; there is no board yet.
- What the bits mean. A plausible name is an "ICAP in use" enable, but that is a guess.

## Proposed test before posting
- On an Arty A7-35T, load two builds:
  - the openXC7 build without the bits (build/openxc7/icap_probe/.../icap_probe.bit);
  - the same build with the bits set by flow/set_bits.py (icap_probe_icapbits.bit).
- Check whether ICAP reads (for example the IDCODE through ICAP) work in each.

## Update 2026-11-05 (gap analysis, docs/gap-vivado.md)
- DNA_PORT alone (designs/gap/dna_port) also sets 3 unknown CFG_CENTER_MID_X46Y32 bits, but different ones: 26_2213, 27_2210, 27_2215.
- STARTUPE2, USR_ACCESSE2, FRAME_ECCE2 and BSCANE2 builds have 0 unknown bits.
- Evidence: build/gap/{dna_port,icape2}/report.json. Combined draft: docs/drafts/prjxray-db-vivado-unknown-bits.md.
