# RapidWright as a Vivado bridge (evaluation, 2026-11-06/07)

RapidWright (github.com/Xilinx/RapidWright, Apache-2.0) is AMD's Java library that reads and writes Vivado design checkpoints (DCP).

**Status: the tools are built and checked offline. No Vivado verdict yet.** Both Vivado jobs waited in the shared lock queue until the session ended. The 294-net import errors are therefore **not yet shown to be fixed**.

## Install (project-local, official sources only)
- Location: `toolchain/rapidwright/`, gitignored through `toolchain/`.
- JDK: Adoptium Temurin 21.0.13+9, in `jdk -> jdk-21.0.13+9`. The sha256 matched api.adoptium.net.
- RapidWright: `dl/rapidwright-2025.2.2-standalone-lin64.jar`, from GitHub release v2025.2.2-beta, linked as `rapidwright.jar`.
  - The md5 matched the release's MD5SUM.TXT.
  - 2025.2.2 was chosen to match the installed Vivado 2025.2.
- Device data: on first use, RapidWright downloaded `data/devices/artix7/xc7a35t_db.dat` (2.1 MB) from its own official data server. Nothing had to be generated from Vivado.
  - Checks: Artix-7 xc7a35t loads with 18055 tiles and 15817 sites. Its PIPs, BELs and site types match Vivado's names.
- Wrapper: `flow/rapidwright/rw.sh build|xdcp|export|jython`.
  - Java is capped with `-Xmx3g` (`RW_XMX` overrides it).
  - It waits until at least 4 GB is free.

## (b) Our placement and routing as a DCP: flow/rapidwright/XrouteDcp.java
- Usage: `rw.sh xdcp build/xroute/src/<name> out.dcp`.
- It takes the same inputs that vivado/build_xroute.tcl imposes through Tcl: netlist.edf, place.txt, macros.txt, lockpins.txt, routes.txt, const_routes.txt and the XDC.
- It writes the placement and the PIPs directly, so no Vivado place or route step is involved.

Root cause of most of the 294 rv_mul errors, from the stored `route_log.txt`, `place_log.txt` and `route_diag.txt`:
- 14 RAM32M macros failed `set_property LOC` ("Cannot expand macro instance").
  - So the LUTRAMs landed elsewhere, and every net into them shows unrouted pins or antennas.
- Most other failures are LUT site-pin mismatches, such as "CLBLL_LL_A1 not downhill of IMUX_L7", and the clock leaf (CLBLM_M_CLK).

RapidWright avoids both problems:
- RAM32M sub-cells (RAMA, RAMA_D1, ...) are placed directly on their BELs.
- LUT pin maps come from LOCK_PINS as physical pin mappings.
- Site pins come from the PIP tree. For example, CARRY4 O0 leaves through AMUX as nextpnr routed it. RapidWright's own site-routing choice is undone where it disagrees.

Fixes the yosys EDIF needed, all done in memory:
- The library `LIB` is renamed to `hdi_primitives`.
- yosys writes every primitive port as INOUT. The directions are copied from RapidWright's unisim cells; without this, the parent-net map breaks.
- Ports that yosys omitted are added (RAM32M DID/DOD, RAMB36 ECC and cascade ports).
- Floating macro inputs are tied to GND before macro expansion.

Offline results (rv_mul_p5_dspq_cal_s1):
- 3658 cells placed, including the 112 RAM32M sub-cells.
- 2601 nets and 34875 PIPs set, with 0 PIP lookup failures.
- 0 site-routing failures.
- The only loss is 6 BUFGCTRL CE/S/IGNORE tie pins. The BUFG is placed as site type BUFG, which has no such pins.

DCPs from the same tool, all written offline:
- blinky, rv_soc, rv_big and bram (`build/rapidwright/xdcp/<name>/<name>.dcp`, with a `.dcp.log` stats file).
- These carry no Vivado verdict yet.

Caveat: RapidWright's own ReportRouteStatus reports every net as "unrouted" on these DCPs, so it does not judge them. Only Vivado's `report_route_status` counts.

## (a) Vivado's placement and routing into nextpnr: flow/rapidwright/DcpExport.java + flow/rw_vivado_replay.py
- `rw.sh export in.dcp outdir [readable.edf]` writes four TSV files:
  - cells.tsv: site, BEL, pin map, and output site wire with its net;
  - nets.tsv: PIPs, with reversed bidirectional PIPs marked;
  - pins.tsv: site pins with their tile wire and site wire;
  - sitepips.tsv: the site PIPs in use.
- Vivado DCPs carry an encrypted EDIF, so Vivado must also `write_edif`. vivado/rw_vref.tcl does that.
- `python3 flow/rw_vivado_replay.py <export> <nextpnr routed.json> <prefix>` writes `<prefix>.preplaced` and `<prefix>.prerouted`.
  - The routes are full nextpnr ROUTING strings: the source site wire, site PIPs, site-pin PIPs and interconnect PIPs, in nextpnr's `X{gx}Y{gy}/dst/src` naming.
  - Unlike the cells.txt Tcl dump (flow/route_xtime.py `-o place-import`), this carries Vivado's exact routing.
- The round trip on our own rv_mul DCP is not a clean test, because the xroute netlist renames the cells nextpnr made (`xr_*`).
  - 2729 cells were pinned, then nextpnr's SA refinement asserted (base_arch.h:156) on the partial pre-placement.
  - The rv_soc Vivado reference DCP was never produced, because its Vivado job did not run.

## (c) Other uses, checked
- **RWRoute does not support Series7.** It raises "re-target to UltraScale/UltraScalePlus/Versal", so it cannot serve as a second router for us. RapidWright's timing models are UltraScale+ as well.
- Useful on 7-series:
  - exact DCP read and write, so Vivado's placement and routing can be diffed against ours net by net, without Tcl dumps;
  - ECO-style edits, such as moving a cell or re-routing a net, then letting Vivado time or route_design -preserve the result;
  - FPGA Interchange export (`interchange.*`, DeviceResourcesWriter) as an independent check of our chipdb's PIP and site data;
  - DesignImplementationDiff.

## Exact next steps
1. Take the Vivado lock and run the rv_mul check: `vivado/rw_check.tcl` on `build/rapidwright/xdcp/rv_mul_p5_dspq_cal_s1/rv_mul_p5_dspq_cal_s1.dcp`.
   - Copy the DCP to `C:\Users\finnf\open-dfx-xc7-vivado\build\rapidwright\r1\rv_mul_p5_dspq_cal_s1\in.dcp`.
   - Run `vivado -mode batch -source rw_check.tcl -tclargs <in.dcp> <outdir>`.
   - It writes route_status.rpt, bad_nets.txt, route_diag.txt, vpips.txt, drc.rpt and timing.rpt.
   - Success means 2603 of 2603 routable nets fully routed and 0 with routing errors, against 294 errors today.
   - Then diff vpips.txt against routes.txt.
2. Expect to fix:
   - IOB pad/port representation: the IBUF/OBUF cells are placed as IOB33 on INBUF_EN/OUTBUF;
   - the BUFG CE/S tie pips into a BUFG-type site;
   - possibly per-LUTRAM site configuration.
   Repeat one design per lock (blinky first, since it is the smallest).
3. For (a), run vivado/rw_vref.tcl (args `xc7a35tcsg324-1 <designs/rte/rv_soc_vref> <out>`), which writes routed.dcp and routed.edf.
   - Then run `rw.sh export routed.dcp out routed.edf` and `flow/rw_vivado_replay.py out build/rte/npr/rv_soc_own_cal_s1/routed.json build/rapidwright/replay/rv_soc_vref`.
   - Then replay through `ofx/npwait.sh` with `-o preplaced= -o prerouted=` (qordsp binary, rv_soc status.json command), and count bound and collided nets in the "Pre-routed" log lines.
