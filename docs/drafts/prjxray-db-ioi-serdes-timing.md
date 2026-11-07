# Draft issue for f4pga/prjxray-db: no ISERDESE2/OSERDESE2 timing in the IOI SDF files

Not posted. Needs the user's approval.

## Title
artix7 timings: IOI3 SDF files have IDELAYE2 and ILOGIC IFF cells but no ISERDESE2/OSERDESE2

## Body
`artix7/timings/RIOI3.sdf` (and LIOI3, *_SING, *_TBYTESRC, *_TBYTETERM) list these CELLTYPEs for the SERDES/delay sites:
`IDELAYE2_DELAY_SRC_DATAIN`, `IDELAYE2_DELAY_SRC_IDATAIN`, `IDELAYE2_IDELAY_TYPE_VARIABLE`, `IDELAYE2_IDELAY_TYPE_VAR_LOAD`,
`IDELAYE2_IDELAY_TYPE_VAR_LOAD_PIPE`, and the `ILOGICE3_IFF*` variants. There is no `ISERDESE2*` or `OSERDESE2*` cell
(checked with `grep -o 'CELLTYPE "[^"]*"' RIOI3.sdf | sort -u` at prjxray-db a8b09269).

Effect downstream: a DDR3 PHY built from OSERDESE2/ISERDESE2 (LiteDRAM A7DDRPHY on an Arty A7-35T) places and routes with
openXC7 nextpnr, but none of the fabric-to-OSERDES `D1..D8`/`T1`/`RST` setups, the ISERDES `Q1..Q8` clock-to-outs or the
CLKDIV-domain checks are timed. In that design 63 of Vivado 2025.2's 2000 worst setup paths end on OSERDES/IDELAY pins
(worst slack +1.911 ns at 10 ns on its own placement); with the openXC7 placement imposed it is 33 of 2000, worst
+0.585 ns. So they are not
limiting today, but nothing in the open flow would notice if they were.

Request: add ISERDESE2/OSERDESE2 cells (per DATA_RATE/DATA_WIDTH/INTERFACE_TYPE variant, like the IDELAYE2 split) with
setup/hold to CLKDIV and CLKDIV->Q arcs, from the same Vivado timing extraction that produced the IDELAYE2 entries.

## Evidence (local)
- prjxray-db: `toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7/timings/RIOI3.sdf`
- Vivado, own placement: `build/ddr3/arty_ddr3/viv_ddr3/worst_paths.txt`
- Vivado timer, openXC7 placement: `build/ddr3/xtime/out/arty_ddr3_gapfix_placed/worst_paths.txt`
- write-up: docs/ddr3-litedram.md
