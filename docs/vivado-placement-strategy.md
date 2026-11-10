# How Vivado places: observations and rules for our placer (2026-11-08)

Question (user): "watch how Vivado places to learn its strategy". The method is black-box. We read only Vivado's
outputs: placements dumped with `get_cells` LOC/BEL, `get_timing_paths`, `report_*`, the `place_design` log, and our own
placements of the same netlist. No Vivado binary is inspected.

Every timing number below is from **Vivado's timer** after `route_design` unless it says otherwise. Distances are in
prjxray tile-grid Manhattan units: one CLB tile is one unit in y, and a CLB column plus its INT column are 2 in x.
"Ours" is the base static placer (pl14_off_stub: `--placer static -o hardblock-timing`, stub chipdb, 5 ns, seeds 1-3).

## Data

| set | what | where |
|---|---|---|
| **same-netlist pair** | Vivado places and routes **our exported netlist** itself (`place_design` default, no opt_design). This is the exact-import netlist, with nextpnr's carry splits and 519-569 feed-through LUT1. Ours: the same netlist with nextpnr's placement imposed exactly and LUT pins locked; Vivado only routes. The cell names are identical, so every comparison is cell for cell. | build/exact/{rv_soc,bram,rv_big}_p5_vref_exact and _p5_pl14_off_stub_s{1,2,3}_exact |
| pin-lock pair | the same nextpnr placement (dp0 s1) imported with and without the LUT pin locks | build/exact/rv_soc_p5_dp0_s1_exact{,_nolock} |
| QoR suite | Vivado's own synthesis + P&R (nets_sites.txt) against the open flow's base run (routed JSON), 13 designs | build/qor_suite/<d>__free, ~/open-dfx-xc7/build/qor_suite/<d>/open/base |
| directive sweep (queued) | vivado/viv_strategy.tcl `edif` mode: the same exported netlist, one `place_design -directive D` per directive, with post-place and post-route dumps and `report_design_analysis` | build/viv_strategy/{rv_soc,bram}_edif |
| hierarchy (queued) | vivado/viv_strategy.tcl `rtl` mode: Vivado synthesises the RTL (default `-flatten_hierarchy rebuilt`, which keeps the hierarchical names), then opt_design and place_design Default | build/viv_strategy/<d>_rtl, for rv_soc bram rv_mul rv_big aes sha256 or1200 serv |
| import control (queued) | Vivado's own placement re-imported through the exact flow without pin locks (flow/viv_own_exact.py), so the cost of the measurement itself can be seen | build/viv_strategy/{rv_soc,bram}_vivown_exact |

Tools:
- flow/viv_strategy.py: `compare` (paths, packing, density, hard blocks), `hier`, `directives`, `log`;
- flow/viv_conn.py: `classes`, `distance`, `arcs`, `bels`, `steps`, `startff`;
- flow/viv_suite_shape.py;
- flow/viv_own_exact.py;
- flow/viv_strategy_run.sh (Vivado runner: slot 1 only, takes it only after it has stayed free for 60 s);
- vivado/viv_strategy.tcl.

Outputs: build/viv_strategy/compare_<d>.json.

Reference points. Fmax excludes the ICAPE2 endpoint. 5 ns clock.

| design | Vivado places the exported netlist | ours, exact import, s1 / s2 / s3 | Vivado places the yosys netlist (rte vref: no LUT1 feed-throughs; rv_big there is the `-pipeline` netlist) |
|---|---|---|---|
| rv_soc | WNS -1.720 (148.8 MHz) | -4.863 / -4.676 / -4.978 (102.4 / 103.4 / 100.2) | -0.774 (173.2) |
| bram | -1.095 (164.1) | -2.188 / -1.854 / -1.927 (139.3 / 145.4 / 144.0) | -0.805 (172.3) |
| rv_big | -4.018 (110.9) | -6.267 / -6.640 / -6.004 (88.9 / 86.0 / 90.9) | -0.999 (166.7; different netlist) |

So the like-for-like placement gap (same netlist, Vivado timer) is 31-33 % on rv_soc, 11-15 % on bram and 18-22 % on
rv_big. The "101.7 vs 173" figure mixes the placement gap with a netlist effect (Observation 9).

## Observations

### 1. LUT input-pin assignment is the largest single lever measured (same placement, rv_soc dp0 s1)
| import of the same nextpnr placement | WNS | Fmax | worst-100 logic / net ns | LUT arc on the reported paths |
|---|---|---|---|---|
| LUT pins locked to nextpnr's choice | -4.664 | 102.6 | 2.49 / 5.54 | 0.232 (6LUT bel) / 0.247 (5LUT bel) |
| pins free (Vivado's router picks) | -3.359 | 119.6 (+17 %) | 2.08 / 4.82 | 0.231 / 0.211 |
| Vivado's own placement (vref_exact) | -1.720 | 148.8 | 2.03 / 3.75 | 0.152 |

- Vivado's placer has a phase "3.7 Re-assign LUT pins" in detail placement (log).
- With nextpnr's pins, each LUT on the critical paths costs 0.21-0.25 ns, against 0.124-0.152 in Vivado's.
  - The 7-series LUT delay depends on the physical input pin.
  - The extra net delay comes from routing to a fixed pin.
- Unlocking alone recovers +17 % Fmax, with no placement change.
- Which physical pin the critical input uses. Vivado's own routed critical paths (vivado/viv_strategy.tcl, `get_bel_pins`; RTL runs; distinct LUT input pins on the worst 1000 paths):

  | design | 6LUT A6 | 6LUT A5 | A6+A5 | inputs on a 5LUT bel |
  |---|---|---|---|---|
  | rv_soc | 18 % | 27 % | 45 % | 7 % |
  | rv_mul | 20 % | 24 % | 44 % | 13 % |
  | rv_big | 33 % | 32 % | 65 % | 12 % |
  | aes | 37 % | 29 % | 66 % | 10 % |
  | bram | 10 % | 7 % | 17 % | 35 % (carry-S structure) |

  - Ours (lockpins of the exact imports, worst 200 paths): rv_soc s1/s2 and rv_big s1 use A6 2-3 % and A5 3-7 %. Most critical inputs land on A1/A2, and 51-66 % sit on a 5LUT bel, where A6 is unusable (tied high in dual mode).


### 2. Vivado's critical paths are compact and monotone in x; ours zigzag
Worst 100 paths (Vivado timer), own placement:

| | rv_soc Vivado | rv_soc ours s1 / s2 / s3 | bram Vivado | bram ours s1 / s2 / s3 | rv_big Vivado | rv_big ours s1 / s2 / s3 |
|---|---|---|---|---|---|---|
| hops per path | 21.9 | 54.6 / 31.7 / 66.5 | 15.9 | 16.8 / 18.3 / 16.3 | 30.2 | 41.4 / 48.8 / 33.4 |
| bbox half-perimeter | 19.3 | 35.2 / 25.7 / 45.6 | 14.0 | 13.2 / 14.6 / 12.1 | 23.9 | 32.9 / 32.8 / 26.1 |
| hops / bbox (1 = monotone) | 1.17 | 1.57 / 1.39 / 1.45 | 1.16 | 1.32 / 1.27 / 1.35 | 1.35 | 1.30 / 1.46 / 1.34 |
| monotone paths | 41 % | 1 / 22 / 2 % | 42 % | 11 / 32 / 25 % | 26 % | 35 / 27 / 1 % |
| x reversals per path | **0.09** | 1.62 / 0.44 / 0.92 | 0.48 | 0 / 0.14 / 0.53 | 0.73 | 1.28 / 1.28 / 0.60 |
| y reversals per path | 0.79 | 1.45 / 1.63 / 1.22 | 0.57 | 0.89 / 0.68 / 0.64 | 1.53 | 0.82 / 1.31 / 1.26 |
| hops per step | 3.1 | 7.7 / 4.1 / 9.8 | 1.55 | 1.82 / 1.89 / 1.72 | 3.95 | 5.4 / 6.2 / 4.2 |
| net / logic ns | 3.75 / 2.03 | 5.85 / 2.50 ... 6.17 / 2.55 | 1.73 / 4.00 | 2.50 / 4.06 ... | 2.80 / 4.53 | 5.37 / 4.02 ... |

- Vivado's paths on rv_soc almost never reverse in x (0.09 per path). They fold in y instead.
- A worked example, rv_soc's worst Vivado path, FF -> LUT1 -> CARRY4 -> 4 LUTs -> FF CE:
  - Vivado keeps it inside SLICE_X34-39 / Y15-20.
  - Our s1 spreads the same cells over X34-44 / Y65-81, s2 over X30-46 / Y46-53.
- The top 100 paths come from only 2-6 distinct start FFs. The path statistics therefore describe a few cones, and
  the design-wide statistics below are the unbiased check.

### 3. High-fanout critical connections stay short in Vivado
Unique steps of each placement's own worst 200 paths, mean distance by the fanout of the net (rv_soc):

| fanout | Vivado's paths in Vivado | ours s1 / s2 / s3, our paths | the same steps in Vivado's placement |
|---|---|---|---|
| 1 | 0.9 | 1.4 / 2.0 / 1.1 | 0.6 / 0.6 / 0.5 |
| 2-3 | 2.4 | 3.7 / 4.1 / 3.8 | 1.9 / 2.0 / 3.4 |
| 9-32 | 8.2 | 9.0 / 8.6 / 9.5 | **4.2 / 4.5 / 4.5** |
| >32 | 12.7 | 9.5 / 20.4 / 11.8 | 8.2 / 6.9 / 5.2 |

- On the connections that are critical for us, Vivado's placement has the critical sink of a 9-32 fanout net at half our distance.
- A net-based wirelength model weights all sinks of a net alike. Vivado's result looks pin-based: the critical sink is pulled to the driver.

### 4. Critical start FFs sit between their D cone and their Q cone
| rv_soc, start FFs of the worst 100 paths | Vivado | ours s1 / s2 / s3 |
|---|---|---|
| distinct start FFs | 2 | 3 / 6 / 2 |
| FF -> first LUT, mean distance | 0.5 | 14.7 / 5.0 / 16.5 |
| D-LUT -> first Q-side LUT distance | 0, 1 | 24, 20, 0 / 11, 0, 1, 11, 1, 6 / 22, 11 |
| hops per path in the FF -> LUT step | 0.0 | 15.6 / 2.1 / 16.0 |

- Vivado places the FF's D-driver LUT and its critical Q load next to each other, so the FF can sit with both.
- We pack the FF onto its D-LUT before global placement (99.2-99.7 % D-pairing, Vivado 83-87 %). When the D cone and the Q cone end up far apart, the critical Q step is long.
- In Vivado, critical FFs still pair with their D-LUT 89-100 %. Pairing is right, but the two cones must be co-placed.

### 5. Footprint: flat and wide (13 of 13 QoR-suite designs, plus rv_soc, rv_big)
- In slice coordinates, Vivado's own runs have sd_x 7-20 and sd_y 6-17.
- Ours are narrow and tall: sd_x 2.3-9.3, sd_y 9.7-20.
- Every one of the 13 suite designs has a smaller sd_x and a larger sd_y in ours (flow/viv_suite_shape.py).
- Same netlist: rv_soc Vivado slice rows Y12-43 (32 rows) against ours Y29-94 (45-65 rows); rv_big Y0-32 against Y40-100.

| design | Vivado slices / bbox w x h / sd x,y | ours slices / bbox / sd x,y |
|---|---|---|
| aes | 1061 / 36x45 / 8.4,10.9 | 1200 / 46x64 / 7.1,17.0 |
| axi_xbar | 1119 / 38x40 / 10.7,9.8 | 962 / 22x51 / 5.9,13.7 |
| blob_merge | 1728 / 58x51 / 15.2,12.2 | 1750 / 41x75 / 9.3,18.7 |
| bram | 246 / 55x45 / 7.1,7.5 | 307 / 8x89 / 2.3,14.0 |
| epfl_mult | 1365 / 38x42 / 10.3,10.8 | 1306 / 26x52 / 7.4,14.8 |
| epfl_sin | 831 / 31x37 / 7.8,9.1 | 759 / 22x46 / 5.1,12.5 |
| mkpktmerge | 259 / 52x72 / 20.1,17.3 | 1567 / 45x75 / 8.3,19.1 |
| or1200 | 670 / 33x31 / 8.3,7.0 | 683 / 22x47 / 6.3,9.7 |
| rv_big | 480 / 52x29 / 8.4,5.7 | 454 / 12x74 / 3.4,11.4 |
| serv | 1608 / 52x62 / 10.9,14.5 | 1425 / 42x74 / 6.8,19.9 |
| sha256 | 997 / 52x34 / 9.8,9.0 | 1222 / 32x61 / 6.9,14.9 |
| sha512 | 1060 / 57x42 / 13.9,8.0 | 1262 / 30x55 / 8.6,13.0 |
| vtr_sha | 1312 / 60x89 / 13.5,11.4 | 1345 / 26x65 / 6.6,17.5 |

How the two sides are counted:
- Vivado slices = SLICE sites on any signal net in nets_sites.txt. Ours = slices with a placed cell.
- The suite runs are each tool's own netlist, so read the shape columns, not the slice counts.
- Our run is the base `p<period>_s1`.

### 6. Packing conventions
Same netlist, whole design:

| | rv_soc Vivado | rv_soc ours s1 | rv_big Vivado | rv_big ours s1 | bram Vivado | bram ours s1 |
|---|---|---|---|---|---|---|
| slices used (dump) | 456 | 484 (s2 513, s3 479) | 600 | 735 (747, 762) | 295 | 333 |
| LUTs per LUT slice / FFs per FF slice | 4.19 / 2.02 | 4.01 / 2.04 | 4.54 / 2.29 | 3.70 / 1.95 | 5.17 / 3.01 | 4.81 / 2.78 |
| LUTs alone on an x5LUT bel (6LUT empty) | 28 (25 LUT1) | 432 (285 LUT5, 100 LUT4) | 28 | 573 | 19 | 149 |
| FFs on x5FF bels | 25 / 764 (3 %) | 409 / 764 (54 %) | 46 / 1108 (4 %) | 545 / 1108 (49 %) | 12 / 494 | 73 / 494 |
| LUTs on 5LUT, worst-100 paths | 4 % | 52 % (s2 52, s3 64) | 1 % | 53 % (s2 50) | 0 % | 18 % |
| LUT -> FF (D) in one slice | 84 % | 99.4 % | 87 % | 99.3 % | 64 % | 80 % |
| control-set x slice pairs (minimum) | 378 (128) | 375 (128) | 485 (176) | 569 (176) | 164 (62) | 178 (62) |
| carry S-LUT in the carry's slice | 91.5 % | 100 % | 94 % | 100 % | 96 % | 100 % |

- Vivado uses the 5LUT almost only as the second LUT of an input-sharing pair. It holds LUT1 feed-throughs and small LUT2-4 next to a LUT on the 6LUT.
- Vivado uses the xFF bels (driven from O6/AX/carry) and leaves x5FF nearly empty.
- We put 149-3351 lone LUTs on 5LUT bels and half of all FFs on x5FF. This holds for every QoR-suite design: sha256 has 2457 lone 5LUTs out of 5581 LUTs, and 2154 of 2676 FFs on x5FF.
- The cell arc does not show the cost (with free pins, 5LUT 0.211 ns against 6LUT 0.231 ns). The cost is on the outgoing net: the xMUX output is about 250 ps slower (observation 7).
- The second cost is density: rv_big uses 22-27 % more slices.
- Control sets are not a difference: equal slice x control-set pairs on rv_soc.
- Vivado's placer combines LUTs after global placement ("Physical Synthesis In Placer: LUT Combining"): 46 LUTs on rv_soc and 122 on bram (log, Physopt 32-1138).

### 7. Net delay at equal distance: the xMUX outputs (cause found)
Design-wide, every routed connection (net_delays.txt), mean net delay by Manhattan distance:

| distance | rv_soc Vivado n / ps | Vivado's placement re-imported (control) | ours s1 | ours dp0 s1, pins free | rv_big Vivado | rv_big ours s1 |
|---|---|---|---|---|---|---|
| same slice | 1599 / 188 | 1599 / 189 | 1681 / 192 | 1687 / 191 | 2452 / 185 | 2524 / 191 |
| same tile | 269 / 571 | 269 / 567 | 281 / 691 | 302 / 712 | 291 / 597 | 399 / 734 |
| 1 | 603 / 586 | 603 / 592 | 391 / 704 | 394 / 660 | 748 / 575 | 690 / 694 |
| 3-4 | 609 / 792 | 609 / 790 | 699 / 948 | 567 / 888 | 1132 / 810 | 695 / 976 |
| 9-16 | 1249 / 1208 | 1249 / 1196 | 1545 / 1404 | 1583 / 1328 | 2060 / 1316 | 1994 / 1423 |
| >32 | 389 / 1877 | 389 / 1745 | 230 / 2713 | 235 / 2610 | 388 / 1883 | 472 / 2807 |

- Design-wide, Vivado's connections are not shorter: rv_soc mean distance 8.94 against ours 7.7-8.5, rv_big 8.34 against 9.62. They are faster: rv_soc 894 ps against 996-1062 ps, rv_big 923 against 1125.
- At the same (dx, dy), ours is 100-250 ps slower. Example: LUT-input sinks in another slice of the same tile cost 550 ps in Vivado's placement against 689-701 ps in ours.
- **The import is not the cause.** Control: Vivado's own placement put back through the exact flow (flow/viv_own_exact.py, no pin locks). Vivado accepted 2637 of 2638 cells at the same site and bel and re-placed the 14 LUTRAM macros at the same sites.
  - WNS without ICAP: -1.713, against -1.720 for Vivado's own flow.
  - The per-distance delays are identical (table).
  - bram control: all 1987 cells imposed, WNS -1.095, identical to Vivado's own -1.095.
- **Not the cause:**
  - congestion: Vivado's post-place estimate is 1x1 / 2x2 / 4x4 region levels in all three runs, with 0-3 overlapping nodes after its first routing iteration;
  - LUT-input pin density per tile: ours is lower (12.0-13.0 distinct input nets per used CLB tile against 15.0-15.3), and ours is slower in every density bin;
  - the sink's bel.
- **The cause is the driver's output pin.** A LUT on an x5LUT bel and an FF on an x5FF bel both leave the slice through the AMUX..DMUX output. That route is about 250 ps slower even in Vivado's own placement (rv_soc, distance 0-2):

  | driver | Vivado's placement n / ps (0-2, 3-8, 9+) | ours s1 n / ps |
  |---|---|---|
  | LUT on 6LUT (A..D out) | 493 / 610, 675 / 857, 927 / 1284 | 279 / 772, 531 / 953, 382 / 1551 |
  | LUT on 5LUT (AMUX..DMUX out) | 75 / 869, 85 / 1021, 56 / 1271 | 160 / 939, 261 / 1114, 584 / 1839 |
  | FF on xFF (AQ..DQ out) | 423 / 644, 714 / 943, 1559 / 1570 | 267 / 697, 385 / 1011, 634 / 1828 |
  | FF on x5FF (AMUX..DMUX out) | 9 / 892, 21 / 982, 11 / 1460 | 184 / 944, 443 / 1179, 857 / 1611 |

  rv_big shows the same: LUT 633 against 889 ps, FF 663 against 895 ps at distance 0-2 in Vivado's placement.
- In ours, about half of all drivers use xMUX:
  - rv_soc s1: 1005 LUT and 1484 FF connections, against 216 and 41 in Vivado's placement.
- Inter-slice steps driven from xMUX on the worst 100 paths, per path:

  | design | Vivado | ours s1 / s2 / s3 | ours, pins free |
  |---|---|---|---|
  | rv_soc | 0.15 of 4.04 | 2.44 / 2.45 / 4.10 of 5.3-6.0 | 2.69 |
  | rv_big | 0.02 of 5.71 | 2.16 / 1.99 | |
  | bram | 0.00 of 8.29 | 0.35 / 0.22 | |

  At 0.16-0.26 ns each, that is about 0.4-1.0 ns per critical path on rv_soc, about 0.5 ns on rv_big and under 0.1 ns on bram. It matches the order of the three designs' gaps.
- Fit over all inter-slice connections, net ps = a + b dx + c dy + d fanout (dx, dy in grid units):
  - Vivado: 583 + 28.4 dx + 49.6 dy;
  - ours s1: 768 + 30.5 dx + 45.4 dy;
  - ours, pins free: 720 + 35.4 dx + 36.5 dy;
  - rv_big Vivado: 616 + 21.7 dx + 67.0 dy;
  - rv_big ours: 747-800 + 21-24 dx + 54-55 dy.
- **A unit of y costs about twice a unit of x**, and Vivado's connections are x-dominant: mean dx 8.4 / dy 3.2 on rv_soc and 7.5 / 3.5 on rv_big, against ours 5.0-6.3 / 4.9-5.5 and 6.4-6.5 / 6.5-6.8.

### 8. Hard blocks
- rv_soc: Vivado puts the two RAMB36 at X0Y3/X0Y4 and the logic in rows Y12-43, next to the fixed ICAP_X0Y1. Its overall worst path is FF -> ICAPE2 RDWRB (0.46 ns net; ICAP setup 6.4 ns).
  - The ICAP's connected logic centroid is 18.8 units from it in Vivado's placement, 41-58 in ours. Our RAMs sit in mid-device rows (RAMB36_X1Y11-18).
- bram:
  - Vivado puts the timing-critical bank RAMs 1-27 units from their logic centroid and the uncritical `big` array far away (55-101), using three RAM columns (X0-X2).
  - Ours scatter both (bank 7-65).
  - The worst Vivado path RAMB36_X1Y8 -> LUT6 X50Y40 -> carry chain X48Y39-47 starts on the RAM's own rows.
- rv_big: the same pattern. Critical RAMs (ram.0.11/0.15/0.3) sit 10-16 units from their logic, others 55-66.

### 9. Netlist effect inside the "101.7 vs 173"
- Vivado placing the yosys netlist reaches 173.2 MHz (rv_soc). Placing our exported netlist, which carries 519 extra feed-through LUT1 and split carries, it reaches 148.8 MHz.
- In Vivado's placement of the exported netlist, 88 of the worst 100 paths (rv_soc) and 95 (bram) contain a LUT1 feed-through. Vivado places those LUT1s on 5LUT bels (382 of 569), paired with the logic LUT.
- That part of the gap is the packer's (carry-di-bypass, Finding 15), not placement.

### 10. Vivado's process (log, default directive)
Phases, in order:
1. Phase 1, Placer Initialization: netlist sorting, IO/clock placement, netlist model, clock/macro constraints.
2. Phase 2, Global Placement:
   - 2.1 Floorplanning;
   - 2.2 UpdateTiming;
   - 2.3 Post-Processing in Floorplanning;
   - 2.4 Global Place Phase1;
   - 2.5 Global Place Phase2, with 2.5.1 UpdateTiming before 2.5.2 **Physical Synthesis In Placer**, which runs LUT combining, retiming, high-fanout replication, DSP/BRAM/SRL register moves.
3. Phase 3, Detail Placement:
   - 3.1 Commit Multi Column Macros;
   - 3.2 Commit Most Macros & LUTRAMs;
   - 3.3 Area Swap Optimization;
   - 3.4 Pipeline Register Optimization;
   - 3.5 Fast Optimization;
   - 3.6 Small Shape Detail Placement;
   - 3.7 **Re-assign LUT pins**;
   - 3.8 Pipeline Register Optimization;
   - 3.9 Fast Optimization.
4. Phase 4, Post Placement Optimization and Clean-Up: BUFG insertion, Post Placement Timing Optimization, estimated congestion.

What the log shows:
- Timing is updated twice before the final global placement. Physical synthesis runs **inside** global placement, between Phase 1 and Phase 2 of it.
- Macros (carry chains, LUTRAMs) are committed first in detail placement, then the "small shapes" (LUT-FF pairs).
- Vivado's post-place timing estimate matches its routed result:
  - rv_soc: estimated WNS -2.353 against -2.352 routed;
  - bram: -1.308 against -1.095.
  - The placer optimises against a delay model that is right to within about 0.2 ns. Our placer's model was 433 ps per arc optimistic before calibration (Finding 13).
- The default log has no wirelength or iteration metrics. Directive comparisons: queued (section "Directives").

### 11. Directives (Vivado placing our exported netlist; one `place_design -directive D` each, then route_design)
bram (5 ns, Vivado timer; "est" = Vivado's estimate after place_design; worst-100 = route-time worst 100 paths):

| directive | est WNS | WNS | Fmax MHz | TNS | slices | sd x / y (slices) | worst-100 logic / net ns | hops | place s |
|---|---|---|---|---|---|---|---|---|---|
| Default | -1.308 | -1.095 | 164.1 | -135.7 | 295 | 11.3 / 5.7 | 4.00 / 1.73 | 15.9 | 43 |
| Explore | -1.308 | -1.055 | 165.2 | -128.2 | 293 | 11.3 / 5.5 | 4.07 / 1.65 | 16.0 | 376 |
| ExtraTimingOpt | -2.139 | -1.770 | 147.7 | -214.0 | 317 | 18.9 / 9.5 | 3.83 / 2.17 | 29.5 | 631 |
| AltSpreadLogic_high | -1.496 | -1.238 | 160.3 | -171.3 | 300 | 19.1 / 9.5 | 4.06 / 1.82 | 26.8 | 344 |
| Default, `-no_psip` | -1.308 | -1.179 | 161.8 | -131.9 | 314 | 13.6 / 5.9 | 4.15 / 1.59 | 13.8 | 28 |

- Default is reproducible: -1.095 here and in the earlier vref_exact run.
- **Compact wins.** The two spreading directives double the footprint spread and the worst-path hops (27-30 against 16) and lose 2-10 % Fmax. Explore spends 9x the place time for +0.6 %.
- Physical synthesis in placer (LUT combining, 122 LUTs here, 97 under the spreading directives) saves 19 slices (295 against 314) and is worth +1.4 % Fmax.
- Phase lists are the same for all directives (log), except:
  - Explore skips "3.9 Fast Optimization";
  - `-no_psip` drops 2.5.1/2.5.2;
  - ExtraTimingOpt adds a physical-synthesis pass in post-placement optimisation.
- Directives change effort and spreading inside the same phases, not the algorithm structure.

### 12. Hierarchy (Vivado synthesises the RTL with hierarchy names; opt_design; place_design Default)
flow/viv_strategy.py `hier`:
- slice bounding boxes are the 10-90 % quantiles;
- "shared" is the share of a module's slices that also hold cells of another module.

| design (Fmax, Vivado timer, excl. ICAP) | module: cells, slices, centroid (slice x, y), sd x/y, shared |
|---|---|
| rv_soc (171.3) | u_cpu 1542 cells, 312 sl, (37, 31), 9.5/3.9, 22 %; u_bridge 145, (43, 32), 57 %; u_rm 65, 67 %; u_tx 76, (36, 21), 3.0/1.3, 7 %; u_rx 73, (42, 20), 8 % |
| rv_mul (172.4) | u_cpu 2388, (38, 30), 9.5/4.9, 11 %; u_bridge 29 %; u_tx 76, (43, 42), 1.8/1.0, 7 %; u_rx 73, (43, 46), 14 % |
| rv_big (178.7) | u_cpu 2501, (45, 8), 8.2/4.8, 11 %; u_bridge 58 %; u_tx 76, (29, 15), 0.9/0.9, 8 %; u_rx 73, (31, 19), 14 % |
| aes (6 ns; WNS -2.994) | keymem 4509, (54, 45), 7.4/9.7, 47 %; enc_block 979, (48, 43), 86 %; sbox 48, (56, 42), 100 %; dec_block 675, (42, 60), 4.8/5.2, 67 % |

- **Leaf modules off the critical path become small, tight islands at the edge of the main block.** The UART tx/rx have sd 0.6-3.6 slices and share only 7-14 % of their slices.
- **Modules that talk on the critical path are interleaved, not kept as regions.**
  - aes: the worst paths run enc_block -> sbox -> keymem -> enc_block (100 paths cross enc_block -> sbox, 84 sbox -> keymem). Those three overlap almost completely (47-100 % shared slices, centroids within 6 slices).
  - dec_block, off the critical path, gets its own area: centroid y 60 against 43-45.
- The bus glue (u_bridge, u_rm) is mixed into the CPU's edge (29-67 % shared).
- The CPUs (picorv32) are single modules, so no dataflow order inside them can be read from names.
- **Rule:** no hierarchy-based region constraint. Placement follows connectivity and criticality. Hierarchy is useful only as a hint for clustering leaf modules that are not timing-critical.

## Rules for our placer, ranked by measured potential
Potential is the measured difference under Vivado's timer, on the same netlist (rv_soc, rv_big, bram). Where a number
is an upper bound or one component of the gap, it says so. The rv_soc gap to Vivado's own placement is 2.96-3.26 ns of
WNS.

1. **Timing-driven LUT input-pin assignment after placement** (router or detailed placer; Vivado: Phase 3.7 "Re-assign LUT pins").
   - Put the most critical input on A6, the next on A5, then A4, consistent with the routing. Vivado's critical inputs are 44-66 % on A6/A5, ours 5-11 %.
   - A LUT with a critical input must not sit on, or share its letter with, a 5LUT, which forces A6 high.
   - Measured: **+17 % Fmax** on rv_soc dp0 s1 with an identical placement (WNS -4.664 -> -3.359, 102.6 -> 119.6 MHz).
   - Logic delay per worst path falls from 2.49 to 2.08 ns (Vivado 2.03); net delay from 5.54 to 4.82 ns.
   - Owner: router / packing (the LUT-pin queue is running).
2. **Drive critical nets from the direct outputs: logic LUTs on the 6LUT bel, FFs on AFF-DFF.**
   - Use the 5LUT only as the input-sharing partner of a 6LUT (LUT1 feed-throughs first), and x5FF only when both FFs of a letter are needed. Never use x5FF for a critical FF.
   - Measured: an xMUX-driven connection costs about 250 ps more at short range, even in Vivado's own placement.
   - Ours has 2.0-4.1 such steps per worst path (Vivado 0.02-0.15): about **0.4-1.0 ns per critical path on rv_soc**, about 0.5 ns on rv_big, under 0.1 ns on bram.
   - Area side effect: rv_big uses 600 slices in Vivado against 735-762 in ours.
   - Owner: packing; detailed placement must keep it.
3. **Short critical LUT->LUT arcs: pin-weighted (arc) attraction, independent of the net's other sinks.**
   - In the global placer and SA refinement, pull the critical sink toward its driver.
   - Worst-100 paths, LUT->LUT steps per path:
     - rv_soc: Vivado 14.6 hops / 1.87 ns, ours 18.1-36.1 hops / 3.70-4.84 ns;
     - rv_big: 16.6 / 1.25 ns against 17.3-31.3 / 3.59-3.88 ns.
   - The delay part shares the per-connection component with rules 1 and 2. The distance part alone is 4-22 hops x 25-40 ps per unit = 0.1-0.9 ns.
   - Target on 9-32 fanout nets: the critical sink within about 4.5 grid units of the driver (Vivado 4.2-4.5, ours 8.6-9.5).
4. **Spend distance in x, not in y.**
   - Make the global placer's wirelength and arc cost anisotropic by the measured delay: about 22-35 ps per x unit against 37-67 ps per y unit, from the fits of observation 7.
   - Vivado's connections are x-dominant (dx/dy = 8.4/3.2 rv_soc, 7.5/3.5 rv_big; ours about 1:1).
   - Its critical paths reverse x direction 0.09-0.73 times per path and fold in y; ours reverse x 0.4-1.6 times.
   - The footprint follows: wide and flat, with sd_x > sd_y in 13/13 QoR-suite designs for Vivado, and the opposite for ours.
   - Finding 13's `static-grad-y` test (y weight 2) made the footprint taller, not flatter, in nextpnr's timer. Apply the anisotropy to the delay model of the arc term (rule 3), not as a global y gradient scale, and judge it with Vivado's timer.
5. **Monotone critical cones.**
   - In SA refinement, penalise x reversals along a critical path.
   - Target: hops per worst path at Vivado's 22 (rv_soc) / 16 (bram) / 30 (rv_big), against ours 32-67 / 16-18 / 33-49.
6. **Co-place an FF's D cone and its critical Q cone.**
   - Do not freeze LUT-FF pairs before global placement. Move the pair as a unit toward the criticality-weighted point between the D-driver and the critical Q load.
   - Measured: the FF -> first-LUT step is 15.6/16.0 hops per worst path in ours s1/s3 against 0 in Vivado.
   - The delay cost is small (0.89/1.03 against 0.83 ns per path), but those detours stretch the downstream cone.
7. **Hard blocks by criticality.**
   - Place critical RAMs/DSPs next to their logic (1-27 units) and push uncritical ones out of the way (55-100 units), using all RAM columns.
   - Pull logic toward a fixed critical hard block (ICAP: 18.8 units against 41-58).
8. **A placer delay model as accurate as Vivado's.** Vivado's post-place estimate is 0.0-0.2 ns from its routed result. The model must include the xMUX output penalty (rule 2) and the x/y asymmetry (rule 4).
9. **(Netlist, not placement) Avoid feed-through LUT1s on carry DI** (carry-di-bypass, Finding 15). Vivado's own placement drops from 173 to 149 MHz on rv_soc with the exported netlist's LUT1s and carry splits.

Not rules (no difference found):
- control-set grouping (equal pairs);
- carry chain alignment (ours 100 %, Vivado 91-96 % S-LUT in the carry's slice);
- LUTs per path (8.0 against 8.1);
- white space around critical cells. Vivado's 5x5-slice fill around critical cells is 0.28-0.37 against 0.31-0.36 for other cells, and ours is 0.26-0.29 against 0.25-0.29, so neither placement leaves more room around critical cells.
