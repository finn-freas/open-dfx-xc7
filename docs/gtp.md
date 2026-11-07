# GTP transceivers and the PCIe hard block (Artix-7)

Status of GTPE2_CHANNEL / GTPE2_COMMON / IBUFDS_GTE2 and PCIE_2_1 in the open flow, compared with Vivado 2025.2.
Scripts: `flow/gt_audit.py` (database audit), `flow/gt_fill.py` (UNISIM defaults for GT/PCIe instances),
`flow/gt_compare.py` (GT/PCIe tile bits of two bitstreams), `vivado/gtp_wizard.tcl`, `vivado/pcie_ip.tcl`.

## 1. What the database documents (artix7, openXC7 prjxray-db a8b09269)

`python3 flow/gt_audit.py` writes `build/ofx/gt/audit.txt`. It matches each UNISIM parameter (yosys
`cells_xtra.v`) against the segbits features of the tile. String attributes count as covered when they appear as
`NAME.VALUE` features, `IS_<pin>_INVERTED` as `INV_<pin>`.

| primitive | UNISIM params (non-SIM) | with bits | missing | tile segbits | fuzzer |
|---|---|---|---|---|---|
| GTPE2_CHANNEL | 238 | 238 | none | 1627 features, 1636 bits (GTP_CHANNEL_0..3, plus `_MID_LEFT/_MID_RIGHT` on xc7a200t) | 064-gtp-channel-conf |
| GTPE2_COMMON | 24 | 22 | `IS_GTGREFCLK0_INVERTED`, `IS_GTGREFCLK1_INVERTED` | 279 features (GTP_COMMON) | 063-gtp-common-conf |
| IBUFDS_GTE2 | 3 | 3 | none (`CLKSWING_CFG` sits under GTPE2_COMMON) | 3 per buffer (`CLKCM_CFG`, `CLKRCV_TRST`, `IN_USE`) | 063 |
| PCIE_2_1 | 283 | 283 | none | 1711 features = 1711 mask bits (PCIE_BOT) | 061-pcie-conf |

Other GT features: `IN_USE`, and on GTP_COMMON `ENABLE_DRP`, `GTREFCLK0/1_USED`, `GTGREFCLK0_USED`,
`BOTH_GTREFCLK_USED`. Interconnect: GTP_INT_INTERFACE(_L/_R) and PCIE_INT_INTERFACE_L/_R have only the
IMUX delay pips as bits; the GT and PCIe tiles' own pips are pseudo-pips (`ppips_*.db`). PCIE_TOP has no bits.
The xc7a200t `GTP_COMMON_MID_LEFT/RIGHT` tiles carry 168 more features than GTP_COMMON: the `HCLK_GTP_CK_IN0..`
muxes, which the non-mid GTP_COMMON tile type does not have as pips at all.

"Has bits" means only that the fuzzer found a bit for every attribute bit. Whether the values are right, and
whether Vivado sets bits that no attribute explains, is checked against Vivado below.

MGT pins bonded (prjxray-db `package_pins.csv`):

| part / package | GTP lanes | refclk pairs | quads |
|---|---|---|---|
| xc7a35t/50t cpg236 | 2 | 2 | 216 |
| xc7a35t/50t csg325, fgg484 | 4 | 2 | 216 |
| xc7a100t fgg484 | 4 | 2 | 216 |
| xc7a100t fgg676 | 8 | 4 | 213, 216 |
| xc7a200t fbg484 / sbg484 (+ fbv/sbv) | 4 | 2 | 216 |
| xc7a200t fbg676 (+ fbv) | 8 | 4 | 213, 216 |
| xc7a200t ffg1156 (+ ffv) | 16 | 8 | 113, 116, 213, 216 |
| any csg324, ftg256 | 0 | 0 | - |

Every Artix-7 die with GTPs has one PCIE_2_1 site (PCIE_X0Y0; on xc7a50t-class dies tile PCIE_BOT_X71Y115).

## 2. nextpnr-xilinx FASM writer defaults

yosys passes only the parameters an instance sets; for every other parameter nextpnr-xilinx's writer
(`fasm.cc`) uses its own default. Compared with UNISIM (`build/ofx/devices/gt_defaults.py`, extended to PCIE_2_1):

| primitive | parameters the writer reads | default differs from UNISIM | never written |
|---|---|---|---|
| GTPE2_CHANNEL | 227 | 114 (e.g. CHAN_BOND_MAX_SKEW 0 vs 7, RX_DATA_WIDTH 0 vs 20, PMA_RSV 0 vs 0x333) | 15 |
| GTPE2_COMMON | 24 | 4 (PLL0/1_FBDIV 1 vs 4, PLL0/1_FBDIV_45 4 vs 5) | 9, including IS_GTGREFCLK0/1_INVERTED |
| PCIE_2_1 | 267 | 2: AER_CAP_VERSION 1 vs 2, **PL_FAST_TRAIN TRUE vs FALSE** | 17: SPARE_BIT0..8, SPARE_BYTE0..3, SPARE_WORD0..3 |

PL_FAST_TRAIN=TRUE shortens the LTSSM timers for simulation. A PCIe instance that does not set it explicitly
gets the simulation-only training timers from nextpnr. The Vivado PCIe IP sets it, so the IP is not affected.
The SPARE_* attributes have bits in the database, but nextpnr never writes them. An instance that sets one
loses the value silently.

Workaround used here (no nextpnr change): `flow/gt_fill.py in.v out.v` writes every missing GTPE2_CHANNEL,
GTPE2_COMMON and PCIE_2_1 parameter into the instance with its UNISIM default. The file means the same to Vivado.

## 3. PCIE_2_1 against Vivado

`examples/pcie_bare` is PCIE_2_1 alone on xc7a35tcpg236-1:
- every parameter at its UNISIM default (`gt_fill.py`);
- PIPECLK/USERCLK/USERCLK2/DRPCLK from one BUFG;
- the resets from a pin;
- four status outputs on LEDs.

| | open flow | Vivado 2025.2 |
|---|---|---|
| placement | PCIE_X0Y0 (nextpnr pre-places the only site) | PCIE_X0Y0 |
| decoded PCIE_BOT features | 370 | 370 |
| unknown bits after decoding | 0 | 0 |

`flow/gt_compare.py` compared the PCIE_BOT / PCIE_INT_INTERFACE tiles: 123 attributes (PCIE_BOT attributes and
interface pips) are equal, 0 differ, and none is only in one bitstream (`build/ofx/gt/cmp_pcie_bare/gt_compare.txt`).
So for the default configuration, the database and nextpnr reproduce Vivado's PCIe block bits exactly. This
covers one configuration only. The endpoint built from the Vivado IP is in section 5.

## 4. The open flow now applies the UNISIM defaults itself

`flow/build_openxc7.py` runs `flow/gt_json_defaults.py` on the yosys netlist before nextpnr. It adds every
GTPE2_CHANNEL / GTPE2_COMMON / PCIE_2_1 parameter the design leaves out, with its UNISIM default in yosys' own
JSON encoding. `OFX_GT_DEFAULTS=0` turns it off. So a GT or PCIe instance no longer needs the full parameter list
(`gt_fill.py` / `gt_params.py` are still useful for sources that also go to Vivado). Checks:
- yosys JSON of a fully-filled source vs JSON of the sparse source + `gt_json_defaults.py`: identical parameters
  (GTPE2_CHANNEL 242, GTPE2_COMMON 28, PCIE_2_1 284; 0 differ) for gtp_lbm and pcie_bare (`build/ofx/gt/jtest`).
- `pcie_bare` built end to end from the sparse source (`src/pcie_bare.in.v`, only PL_FAST_TRAIN set): the FASM is
  byte-identical to the build from the filled source (`build/ofx/gt/hook_pcie`).
- gtp_lbm built end to end from a sparse source (only the rate attributes set): every GTPE2_* FASM line, and all
  143 GT-tile attributes after decoding, are the same as in the filled build (`build/ofx/gt/cmp_hook_lbm`). The
  rest of the FASM differs because the test's sparse source also lost some single-line port ties, LOOPBACK among
  them. So this test checks the attribute bits only.
- A netlist without these cells is not rewritten (blinky_b3 JSON md5 unchanged), so other designs cannot change.

This is a flow-side fix. The fix that belongs upstream is in nextpnr-xilinx's `fasm.cc` (UNISIM defaults in
`write_gtp_channel`, `write_gtp_pll`, `write_pcie_2_1`, plus the SPARE_* attributes). It is not drafted here.

## 5. GTP against Vivado, and the PCIe endpoint (stretch)

Designs, all on xc7a35tcpg236-1 unless noted; each builds in the open flow, and its bitstream decodes with 0
unknown bits:

| design | what | open flow |
|---|---|---|
| `examples/gtp_b3` | IBUFDS_GTE2 + GTPE2_COMMON PLL0 + GTPE2_CHANNEL 0, 16-bit, no 8b/10b, every parameter explicit | builds, 192 GT parameter lines |
| `examples/gtp_lbm` | one lane in near-end PMA loopback (LOOPBACK=010), 8b/10b TX/RX with K28.5 commas and comma alignment, 2.5 Gb/s from 125 MHz (PLL0 FBDIV 4 x FBDIV_45 5, OUT_DIV 2, 20-bit internal), TXOUTCLK via BUFG, error checker on LEDs | builds; only the rate attributes are set (`gen_top.py manual`), the rest UNISIM |
| `examples/gtp_lb` | the same top with the attribute values of the Vivado 7 Series Transceivers Wizard (`vivado/gtp_wizard.tcl` generates the wizard sources; `gen_top.py <dir>` copies its GTPE2_* attribute values) | waiting for the wizard run |
| `examples/gtp_nv` | gtp_b3 on xc7a200tsbg484-1 (Nexys Video part): GTP_CHANNEL_0_MID_LEFT / GTP_COMMON_MID_LEFT tiles | builds; 289 + 58 decoded GT features |
| `examples/pcie_bare` | PCIE_2_1 alone | builds; equal to Vivado (section 3) |

Vivado side (`vivado/build_gtp.tcl`; same Verilog and XDC as the open build; compare with
`flow/gt_compare.py <part> <ours.bit> <vivado.bit> <outdir>`): only `pcie_bare` has run so far. The GTP builds
(gtp_b3, gtp_lbm, gtp_nv), the wizard sources and the pcie_7x IP sources waited about 2.5 hours behind
higher-priority Vivado work (placer/router benchmarks) and did not get a slot. They were stopped before taking the
lock. `flow/gt_vivado_queue.sh [wizard gtp_b3 pcie_ip fuzz gtp_nv gtp_lbm]` runs all of them, one design per
Vivado call, through `flow/vivado_polite.sh`. **Not yet known:** whether the GTP tile bits match Vivado's.

## 6. Fuzzing what the database lacks

The only attributes without bits are GTPE2_COMMON `IS_GTGREFCLK0_INVERTED` / `IS_GTGREFCLK1_INVERTED` (and there
is no `GTGREFCLK1_USED` feature). `flow/gt_fuzz_gtgrefclk.py` writes five specimens from gtp_b3: GTGREFCLK0/1
driven from a BUFG, and each inversion set alone. The first Vivado attempt stopped at DRC REQP-49 ("Use of the
GTGREFCLK is reserved for test purposes only"). `build_gtp.tcl` now downgrades REQP-49 to a warning for `fz_*`
designs only, as prjxray fuzzers do. The rerun is step `fuzz` of `flow/gt_vivado_queue.sh`. No results yet.
After the run, the bits are the decoded-FASM differences between fz_gref_base and fz_gref_inv0/inv1 (and
fz_gref_g0/g1 for the *_USED bits). They belong in a prjxray-db segbits draft under docs/drafts/.

## 7. Summary and effort

Works (offline, no hardware):
- yosys passes GTPE2_CHANNEL / GTPE2_COMMON / IBUFDS_GTE2 / PCIE_2_1 through as blackboxes.
- nextpnr-xilinx places them on their sites (GT by the MGT pin LOCs; PCIe on its only site), routes them, and
  writes their FASM.
- The prjxray database has bits for every GTP/PCIe attribute except two GTGREFCLK inversions.
- Every bitstream decodes with 0 unknown bits.
- The PCIe block at defaults is bit-identical to Vivado in the PCIe tiles.
- The flow now applies the UNISIM defaults (section 4).

Missing / unknown:
- **GTP tile bits vs Vivado:** not run yet (`flow/gt_vivado_queue.sh`).
- **GTGREFCLK inversion bits:** fuzz specimens ready, not run yet.
- **No timing on GT paths:** nextpnr has no GT timing arcs. TXOUTCLK/RXOUTCLK-domain logic is timed only as a
  plain clock net.
- **No simulation and no silicon test.**
- **No wizard equivalent:** the attribute values (RXCDR_CFG, PMA_RSV, ...) come from Vivado's wizard or UG482.
- **No reset/startup sequencer IP:** the wizard's TX/RX startup FSMs are fabric logic that would have to be
  written.
- **No PCIe endpoint IP:** the pcie_7x sources are not generated yet (`vivado/pcie_ip.tcl`); the IP is plain Verilog plus BRAM buffers. Building it
  through the open flow is the stretch goal.

Effort to close, rough:
- the Vivado comparisons and the 2-bit fuzz: hours of Vivado time, once the queue allows;
- a GT attribute calculator (`ofx ip gt`: line rate / refclk -> dividers, CDR, CLK25 settings for the common
  protocols) plus an open TX/RX startup FSM: about a week;
- GT timing arcs in nextpnr (TXUSRCLK/RXUSRCLK setup/hold): days, as an opt-in draft;
- the PCIe endpoint (open build of pcie_7x sources, compare, then an open wrapper for PCIE_2_1 and the GTP PIPE
  interface in place of the Xilinx IP, which LitePCIe's 7-series PHY also instantiates): weeks;
- silicon: needs a board with MGTs wired (the Arty's csg324 bonds none).
