**On our designs, DREAMPlaceFPGA gains nothing measurable, judged by Vivado's timer.**
- All numbers below come from Vivado routing and timing the exact nextpnr implementation.
- They are the mean of seeds 1-2. Both sides use the same seeds; seed 3 of the DREAMPlace variants could not get a
  Vivado slot, see Status.

| design | ours (pl14_off_stub) | cold | warm | timing-driven cold | timing-driven warm |
|---|---|---|---|---|---|
| rv_soc | @@rv_soc|pl14_off_stub@@ | @@rv_soc|pl_dpf_wl@@ | @@rv_soc|pl_dpf_warm@@ | @@rv_soc|pl_dpf_td@@ | @@rv_soc|pl_dpf_td_warm@@ |
| bram | @@bram|pl14_off_stub@@ | @@bram|pl_dpf_wl@@ | @@bram|pl_dpf_warm@@ | @@bram|pl_dpf_td@@ | @@bram|pl_dpf_td_warm@@ |
| rv_big | @@rv_big|pl14_off_stub@@ | @@rv_big|pl_dpf_wl@@ | @@rv_big|pl_dpf_warm@@ | @@rv_big|pl_dpf_td@@ | @@rv_big|pl_dpf_td_warm@@ |

- **Every cold import is worse:** -3 to -15 %. "Cold" means nextpnr legalises DREAMPlace's global placement directly.
- **Warm import is within the seed spread on the CPUs** (-2.7 % to +1.9 %) **and clearly worse on bram** (-8 to
  -11 %). "Warm" means nextpnr's own spreading starts from DREAMPlace's global placement.
- **Timing-driven mode** (FCCM'24, with our 7-series delay table) is no better than wirelength-driven.
- **Vivado placing the same netlist itself** reaches rv_soc 136.02 (148.81 MHz excluding ICAP), bram 164.07 and
  rv_big 110.89 MHz. None of the variants closes any of that gap.
- **What DREAMPlaceFPGA does show:**
  - Its global placement has 21-30 % less wirelength than ours on the two CPUs.
  - It has Vivado's flat shape (rv_soc sd_y 5.0, Vivado 5.5, ours 16.4).
  - That does not survive nextpnr's 7-series legalisation. DREAMPlaceFPGA's own legaliser cannot do 7-series.

**Recommendation: drop it as a placer. Do not port it.** Keep the GP-exchange draft as a research oracle. The lever it
points at is a packing-aware legaliser in nextpnr. Details under Recommendation.

**Status:**
- Seed 3 of the four DREAMPlace variants (12 Vivado runs) was not timed. Their exact sources are exported in
  C:\Users\finnf\open-dfx-xc7-vivado\designs\exact\.
- To finish:
  1. Run `setsid nohup flow/dpf_vivado.sh --run <names>`. The names are line 1 of build/dpf/logs/viv_q3.log; finished
     ones are skipped.
  2. Then run `python3 flow/dpf_mkdoc.py`.
