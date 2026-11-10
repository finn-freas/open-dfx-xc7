# VPR as a placement engine for 7-series (evaluation, 2026-11-08)

Question: would VPR (verilog-to-routing), the timing-driven placer F4PGA used for Artix-7, place our netlists better
than our base nextpnr placer? Our placements lag Vivado by 25-30 % Fmax, mostly as net delay from distance
(docs/qor-vivado.md Finding 17).

**Result: no. VPR does not close the gap.** On Vivado's timer (exact import, mean of 3 seeds), VPR's placement
finished by nextpnr against the base:

| design | VPR + nextpnr | base | change | Vivado on its own placement |
|---|---|---|---|---|
| rv_soc | 104.80 MHz | 101.65 | +3.1 % | 136.0 |
| bram | 134.66 | 143.13 | -5.9 % | 164.1 |
| rv_big | 87.43 | 88.51 | -1.2 % | 110.9 |

The rv_big change is inside the seed spread. 10x more annealing effort (`--inner_num 5`) does not help: 103.41 /
134.65 / 86.71. VPR's own wirelength is 6-29 % above the base's, and nextpnr keeps only
about half of VPR's cells where VPR put them.

**Recommendation: drop VPR as an engine.** Do not port its annealer either: nextpnr already has one (placer1). One
idea is worth testing cheaply: VPR's place-delay table measured from the routing graph. Details at the end.

## What was built

| piece | what it does |
|---|---|
| VTR `vtr-verilog-to-routing` @ 25e723a24 | v8.0.0-5699: the `vtr-optimized` build that F4PGA's f4pga-examples `xc7/environment.yml` pins. `make -j2 vpr` in toolchain/vtr/vtr-verilog-to-routing (build notes in docs/wip/vpr.md), not committed. |
| F4PGA arch packages | `symbiflow-arch-defs-{install-xc7,xc7a50t_test}-007d1c1` (20220920-124259) from F4PGA's GCS bucket, the URLs in f4pga-examples docs/getting.rst. Contents: arch.timing.xml, a 2.75 GB rr graph, lookahead, place delay, grid map, pinmaps. VPR warns that the arch was made for VPR c012f19d3 and runs anyway. |
| flow/vpr_export.py | Takes our yosys JSON (the same netlist as the base runs) through F4PGA's xc7_vpr techmaps only (carry_map, fix_xc7_carry.py, clean_carry_map, cells_map) and writes eblif. Nothing is re-synthesised, so every VPR atom traces back to one of our cells. |
| flow/vpr_run.sh | VPR pack once, then place per seed with F4PGA's xc7 option set (platforms.yml). I/O is fixed to the XDC pins (flow/vpr_ioplace.py). `VPR_TAG=hi`: `--inner_num 5`. |
| flow/vpr_import.py | VPR clusters to sites (vpr_grid_map.csv; sub-tile order follows arch-defs prjxray_import_tile_capacity.py: site type, then X). pb path to bel. Writes nextpnr generic bel names. Re-picks bels inside the slice to nextpnr's LUT->FF cluster convention. |
| flow/vpr_bench.py | nextpnr (`rte-run` binary) with `-o place-import` (locked binds), the base command otherwise. Then flow/exact_src.py. |
| flow/vpr_report.py, flow/exact_dump.py | Table: Vivado exact Fmax, HPWL, slices, place_paths metrics on the exact runs, import fidelity. |

Measurement: flow/exact_src.py + vivado/build_rte.tcl ("exact"). Vivado gets nextpnr's complete placement and only
routes. This is the end-to-end flow "VPR places, nextpnr legalises and places the rest". The base is pl14_off_stub
(stub chipdb, `--placer static -o hardblock-timing`, 5 ns), timed the same way. Vivado placed-mode numbers are
optimistic (coordinator: by 7-21 %), so none are used here.

## Limits of the port (why "VPR place" is not "VPR's placement" in the end)

- F4PGA's xc7 architecture has **no DSP48E1 and no ICAPE2 model**. They are dropped from VPR's copy (rv_big: 4 DSPs;
  rv_soc: ICAPE2) and nextpnr places them.
- F4PGA's carry fixup adds LUTs when a CARRY4 bit uses both O and CO. Those cells exist only for VPR.
  Distributed RAM, I/O and BUFG are left to nextpnr.
- **nextpnr keeps only about half of VPR's placement.** nextpnr's packer forms LUT->FF and carry clusters with fixed
  relative bels. VPR packs by its own pb rules. Results:
  - 180-240 clusters per design cannot sit at VPR's root bel ("tile not legal", bel taken).
  - 300-600 cluster members land off VPR's bel.
  - 48 % (rv_soc), 43 % (bram) and 49 % (rv_big) of VPR's cells end on VPR's bel.
  - 1100-1700 cells (rv_soc, rv_big) go to nextpnr's static placer around the locked ones.

  Re-picking bels inside each slice to nextpnr's convention raised this only from 47 to 49 %.

## Results

### Vivado's timer, exact import, 5 ns, seeds 1-3

Source: flow/vpr_report.py. Vivado runs are in C:\Users\finnf\open-dfx-xc7-vivado\build\exact\<design>_p5_{pl14_off_stub,vpr_imp}_s<n>_exact.
- Fmax = 1000 / (5 - WNS).
- HPWL is over non-clock nets on the tile grid, from the routed nextpnr JSON, for both rows.
- Hops, net ns, net ps / step and LUT->FF come from flow/place_paths.py on the 100 worst ICAP-excluded Vivado paths
  (flow/exact_dump.py).
- s (seconds) is nextpnr with npwait time removed, then VPR place and VPR pack.

| design | placer | Vivado Fmax per seed | mean | mean, ICAP excl. | HPWL | slices | worst-100 hops | net ns | net ps / step | LUT->FF in one slice | VPR cells on VPR's bel | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rv_soc | base | 101.39 / 103.35 / 100.22 | 101.65 | 101.65 | 17566 | 492 | 50.9 | 5.72 | 798 | 38 % | - | 42 |
| rv_soc | VPR + nextpnr | 105.75 / 105.70 / 102.95 | **104.80** | 105.99 | 25836 | 467 | 49.3 | 5.66 | 810 | 42 % | 48 % | 129 / 23 / 31 |
| rv_soc | VPR `--inner_num 5` + nextpnr | 100.55 / 105.44 / 104.23 | 103.41 | 105.10 | 26074 | 463 | 46.1 | 5.75 | 824 | 43 % | 47 % | 132 / 59 / 31 |
| bram | base | 139.12 / 145.90 / 144.36 | 143.13 | 143.13 | 24009 | 323 | 17.1 | 2.44 | 259 | - | - | 27 |
| bram | VPR + nextpnr | 130.17 / 140.08 / 133.73 | **134.66** | 134.66 | 24048 | 252 | 35.8 | 2.91 | 333 | - | 43 % | 21 / 21 / 23 |
| bram | VPR `--inner_num 5` + nextpnr | 130.51 / 139.68 / 133.76 | 134.65 | 134.65 | 23290 | 250 | 34.5 | 2.89 | 363 | - | 48 % | 23 / 40 / 23 |
| rv_big | base | 88.75 / 85.91 / 90.88 | 88.51 | 88.51 | 25533 | 748 | 40.9 | 5.41 | 731 | 46 % | - | 33 |
| rv_big | VPR + nextpnr | 82.99 / 90.51 / 88.80 | **87.43** | 87.43 | 37900 | 663 | 39.9 | 5.04 | 702 | 59 % | 49 % | 26 / 22 / 43 |
| rv_big | VPR `--inner_num 5` + nextpnr | 88.05 / 86.49 / 85.58 | 86.71 | 86.71 | 37346 | 670 | 38.9 | 5.05 | 713 | 53 % | 49 % | 30 / 87 / 43 |

Vivado placing and routing the same yosys netlist itself, same harness (build_rte.tcl `vref` mode, no opt_design,
run by another agent): rv_soc 136.0 MHz (WNS -2.352; 148.3 with ICAP excluded), bram 164.1 MHz (WNS -1.095),
rv_big 110.9 MHz (WNS -4.018).

Reading:
- rv_soc gains 3.1 %, and two of VPR's three seeds beat the base's best seed. The worst-path metrics barely move
  (hops 49.3 vs 50.9, net 5.66 vs 5.72 ns). VPR closes about a tenth of the gap to Vivado (101.65 -> 104.80 against
  136.0).
- bram loses 5.9 % in every seed. Its worst paths double their hops (35.8 vs 17.1).
- rv_big: -1.2 % with overlapping seeds (82.99-90.51 vs 85.91-90.88), so no change. VPR shortens its worst-path net
  delay a little (5.04 vs 5.41 ns), but total HPWL rises 48 %.
- HPWL of the finished placement is 0-48 % worse. Part of that comes from nextpnr re-placing the ~half of VPR's cells
  it could not keep (see "Limits").
- Area: VPR packs denser (rv_soc 467 vs 492 slices, bram 252 vs 323, rv_big 663 vs 748; Vivado: rv_soc 398, bram 290).

### VPR's placement alone (before nextpnr), same cells and nets, tile-grid HPWL

Compares VPR's raw positions with the base's positions of the same cells. Nets: the base's packed netlist among the
cells VPR placed, clock pins excluded. Mean of seeds 1-3:

| design | base HPWL | VPR (F4PGA options, inner_num 0.5) | VPR `--inner_num 5` |
|---|---|---|---|
| rv_soc | 13605 | 15162 (+11 %) | 14772 (+9 %) |
| bram | 23478 | 24957 (+6 %) | 22951 (-2 %) |
| rv_big | 21890 | 28139 (+29 %) | 25390 (+16 %) |

Per seed (default): rv_soc +13 / +17 / +5 %, bram +20 / -14 / +19 %, rv_big +27 / +26 / +34 %.

On the base's own 100 worst Vivado paths (exact runs), VPR's positions put the same connections closer: rv_soc
3.8-5.3 vs 5.2-9.6 hops per step, rv_big 5.2-8.0 vs 5.1-9.6, bram 6.2-8.6 vs 7.0-7.1. **This is selection-biased.**
These paths are the base's worst because the base stretched them, so any other placement looks better on them.
VPR's own critical paths are the fair test, and that is what the exact table measures.

### Runtime (shared machine)

VPR pack: 23-43 s. VPR place: 15-31 s per seed with default options, 40-93 s with `--inner_num 5`. Each VPR run spends
~17 s just loading the rr graph, and needs 3.4 GB RSS. nextpnr after the import: 21-27 s (bram, rv_big), about
120-150 s (rv_soc, slow routing). Base nextpnr: 27-42 s. The VPR path costs about 2-4x the base's time.

## Recommendation

**Drop VPR as a placement engine or external placer option.** Reasons, strongest first:
1. **No Fmax win** on Vivado's timer: +3.1 / -5.9 / -1.2 %. Our gap to Vivado is 25-35 %.
2. **Coverage.** F4PGA's xc7 architecture has no DSP48E1 and no ICAPE2 model, and the last arch package is from
   2022 (F4PGA is unmaintained). Adding DSP would mean regenerating the arch and the 2.75 GB rr graph with arch-defs:
   days of work plus hours of build per device. Each further device (a100t, a200t, Zynq, Spartan-7) needs its own
   graph.
3. **Interop loss.** About half of VPR's placement does not survive nextpnr's packer rules. Fixing that means either
   teaching nextpnr's packer VPR's packing (pin VPR's LUT/FF/carry groupings as nextpnr clusters, est. 3-5 days), or
   using VPR's router too, which drops our nextpnr-side work (hold fix, DFX, region routing).
4. **Cost.** VPR pack + place takes 45-135 s and 3.4 GB per design for these small designs (most of it rr-graph
   load), against 27-42 s for the base.

**Porting VPR's algorithms into nextpnr:** VPR's placer is simulated annealing. Its timing cost is
sum(crit^e x delay(dx, dy)) with a criticality exponent ramped from 1 to 8, plus median / centroid / feasible-region
moves. nextpnr already ships a timing-driven annealer of the same family (placer1, the HeAP refinement), and Findings
13-17 tried its knobs. VPR's anneal did not beat our base here, so a port is not expected to pay off. Not recommended.

**One idea worth a small test:** VPR's place-delay model is a delta table filled by Dijkstra over the real routing
graph (`--place_delta_delay_matrix_calculation_method dijkstra`). Our static placer works on an estimated / calibrated
delay. The `-o static-delay=matrix` work (Finding 13, place_v7) is the same idea. If it is revisited, fill the matrix
from nextpnr's own routing graph with a Dijkstra per (dx, dy) instead of fitting. About 1-2 days, and it should be
checked on Vivado's exact timer like everything here.

## Reproduce

```
python3 flow/vpr_bench.py --stage export       # build/vpr/<design>/design.eblif
python3 flow/vpr_bench.py --stage vpr          # pack + place seeds 1-3 (VPR_TAG via --tag hi: --inner_num 5)
python3 flow/vpr_bench.py --stage import       # import.txt (nextpnr bels), import_vpr.txt (raw VPR bels)
python3 flow/vpr_bench.py --stage npr          # nextpnr -o place-import, build/qor/oxc7/vpr_imp/...
python3 flow/vpr_bench.py --stage exact        # flow/exact_src.py -> designs/exact/<d>_p5_vpr_imp_s<n>_exact
RTE_OUT=.../build/exact RTE_ROUTE_DUMP=0 SRC=.../designs/exact flow/rte_dump_vivado.sh --run NAME...
python3 flow/vpr_report.py
```
flow/vpr_xsrc.py + flow/vpr_vivado.sh build Vivado "placed"-mode runs from the raw VPR placement. That mode is
optimistic, so none of its numbers are used here.
