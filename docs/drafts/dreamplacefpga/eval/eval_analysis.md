Variants, all through nextpnr's legaliser, placer1 refinement and router, on the stub chipdb:
- `pl14_off_stub`: our static placer, the default options, with the same packer, legaliser and router.
- `pl_dpf_wl` ("cold"): DREAMPlaceFPGA wirelength- and routability-driven GP with the ISPD'16 defaults, then
  nextpnr legalises it directly.
- `pl_dpf_warm`: the same GP as the start of nextpnr's own spreading.
- `pl_dpf_td`, `pl_dpf_td_warm`: DREAMPlaceFPGA's timing-driven GP (FCCM'24), with a 7-series delay model:
  - net delay: our static-delay fit, 786 + 63/29 ps per row and 37/7 ps per column;
  - logic delays approximate: LUT 124, FF 456, RAMB36 2454 ps;
  - constraint 5000 ps.

### Global placement alone, one metric
flow/dpf_gpcmp.py measures HPWL on the gp-dump nets in placer grid units. "Ours" is nextpnr's static GP just before
logic legalisation (`--placer-static-gp-out`), seed 1. Neither side is legal at that point.

| design | ours: HPWL / sd_x / sd_y | DREAMPlaceFPGA wl: HPWL / sd_x / sd_y | DREAMPlaceFPGA td: HPWL |
|---|---|---|---|
| rv_soc | 11829 / 3.2 / 16.4 | 8261 / 5.8 / 5.0 (-30 %) | 8726 |
| bram | 15470 / 9.1 / 14.2 | 40343 / 7.9 / 26.8 (+161 %) | 40340 |
| rv_big | 15370 / 5.6 / 10.4 | 12188 / 6.4 / 5.8 (-21 %) | 13198 |

- **On the two CPUs, DREAMPlaceFPGA's GP is clearly better in wirelength.**
  - It also has the flat, compact shape of Vivado's placement: sd_y 5.0 on rv_soc, against Vivado's 5.5 and our 16.4
    (Finding 13 / place_diag).
  - With nextpnr's x weight of 2 the gain shrinks to -14 % and -4 %.
  - Part of the gain is density: DREAMPlace stops at overflow 0.1 at target density 1.0, while our GP spreads to
    0.7.
- **bram is the opposite.** DREAMPlace's RAM handling spreads the 24 RAMB36 over Y2..Y29 of three columns, and the
  logic follows. Ours packs them into Y8..Y22 of two columns.
  - The RAMs are legalised mid-GP by its DSP/RAM legaliser while their overflow is still high.
  - On UltraScale ISPD designs this is probably harmless. Here it costs 2.6x the wirelength.

### Why the CPU wirelength gain does not turn into Fmax
- **Cold import:** nextpnr's strict legalisation adds +40-50 % HPWL to the dense DREAMPlace GP (rv_soc 16889 ->
  24323 in nextpnr's metric). On our own GP it adds +17 % (rv_soc s1, 15301 -> 17946).
  - nextpnr has to pack 7-series slices: carry chains in one column, one CE/SR per slice, LUT/FF pairing, LUTRAM in
    SLICEM. It does that out of a solution that ignores all of them.
  - DREAMPlaceFPGA's own packer-legaliser is built for exactly this step, but it models the UltraScale CLB and has no carry or
    LUTRAM support.
- **Warm import:** nextpnr re-spreads to its own density, so the result looks like our own placement.
  - HPWL is within 2 % on rv_soc and +14 % on rv_big.
  - Vivado-timed Fmax is within the seed spread on the CPUs (see the table).
- **Timing-driven GP:** gives nothing measurable on top. Its delay model is ours, so it cannot know more than our
  placer's timing term does.

### Runtime
- DREAMPlaceFPGA's GP takes 73-145 s on 4 CPU threads, plus about 1 s for the bridge.
- nextpnr's whole static placement takes a few seconds; its total pnr time is 15-42 s including routing.
- On these 2-4k-cell designs an external GPU/CPU placer costs runtime instead of saving it. Its speed advantage is
  for 100k+ cell designs.
