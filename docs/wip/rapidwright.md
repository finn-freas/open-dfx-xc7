# WIP: RapidWright evaluation (agent notes, 2026-11-06)

## Milestone 1: installed (project-local, official sources only)
- toolchain/rapidwright/ (gitignored via toolchain/):
  - jdk-21.0.13+9 (Adoptium Temurin, sha256 checked against api.adoptium.net), link `jdk`;
  - dl/rapidwright-2025.2.2-standalone-lin64.jar (GitHub release v2025.2.2-beta, md5 matches the release's MD5SUM.TXT), link `rapidwright.jar`;
  - 2025.2.2 chosen to match the installed Vivado 2025.2.
- Device files: RapidWright downloaded data/devices/artix7/xc7a35t_db.dat (2.1 MB) itself on first use, from its official data server. No Vivado-generated device files were needed.
- Run: `RAPIDWRIGHT_PATH=toolchain/rapidwright toolchain/rapidwright/jdk/bin/java -Xmx3g -jar toolchain/rapidwright/rapidwright.jar script.py` (Jython) or compiled Java with `-cp`.
- Check: xc7a35t loads, 18055 tiles, 15817 sites; INT_L_X10Y50 has 3737 PIPs; SLICE_X12Y50 = SLICEM with the A-D 5/6LUT and FF BELs.

## Next
- (b) DCP writer from build/xroute/src/<design> (netlist.edf, place.txt, macros.txt, lockpins.txt, routes.txt, const_routes.txt).
- (a) DCP reader -> nextpnr -o preplaced / -o prerouted.

## Milestone 2: DCP writer and DCP reader built (offline; Vivado check pending)
- flow/rapidwright/XrouteDcp.java (`flow/rapidwright/rw.sh xdcp build/xroute/src/<name> out.dcp`): reads the same inputs as vivado/build_xroute.tcl and writes a placed+routed DCP directly.
  Fixes needed for the yosys EDIF: library LIB -> hdi_primitives; yosys writes primitive ports as INOUT (copied from RapidWright's unisim cells); ports yosys omitted (RAM32M DID/DOD, RAMB36 ECC/cascade) added; floating macro inputs tied to GND before macro expansion.
  Site pins follow the route: output/input site pins taken from the PIP tree (e.g. CARRY4 O0 out through AMUX), RapidWright's own site-routing choice is undone where it disagrees.
  rv_mul_p5_dspq_cal_s1: 3658 cells placed (incl. 112 RAM32M sub-cells placed directly, the 14 macros that Vivado's place_cell refused), 2601 nets / 34875 PIPs, 0 PIP lookup failures. Only 6 BUFGCTRL CE/S/IGNORE tie pins are dropped (BUFG site type).
- flow/rapidwright/DcpExport.java + flow/rw_vivado_replay.py: DCP -> cells/nets/pins/sitepips TSV -> nextpnr -o preplaced / -o prerouted (full ROUTING strings: source site wire, site PIPs, site pins, interconnect PIPs in nextpnr names).
- Vivado-written DCPs carry an encrypted EDIF: RapidWright needs `write_edif` next to the DCP (vivado/rw_vref.tcl does both).
- Queued Vivado runs: vivado/rw_check.tcl on the rv_mul DCP (open_checkpoint, report_route_status); vivado/rw_vref.tcl (Vivado P&R of the rv_soc yosys netlist, DCP+EDIF).

## Wrap-up (usage limit)
See docs/rapidwright.md. Neither Vivado job ran (lock queue). Both waiters stopped; no lock held.
