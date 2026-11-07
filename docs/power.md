# `ofx power`: a vectorless power estimate, fitted to Vivado report_power

`ofx power` estimates on-chip power for a routed open build, with no simulation activity (the same setting as Vivado's default report_power). It prints a report laid out like report_power: totals, the per-component breakdown, the supply rails, and junction temperature.

```
bin/ofx power                                  # the project's routed build
bin/ofx power --build build/power/open/pw_xor32 --xdc designs/power/pw_xor32/pw_xor32.xdc --json p.json
```

## Model

1. **Clock frequency of every net.** Clocks come from `create_clock` and propagate through IBUF/BUFG/BUFR and through MMCM/PLL multiply and divide settings. A data net gets the frequency of the clock domain that drives it.
2. **Activity of every net (vectorless).** Each net gets a static probability p and a transition density d (transitions per cycle).
   - Primary inputs start at p = 0.5, d = 0.125, as in Vivado.
   - LUT outputs are computed from the LUT INIT truth table. p is the sum of the minterm probabilities, and d = Σᵢ P(∂f/∂xᵢ)·dᵢ (Najm transition density, with inputs treated as independent). CARRY4 and MUXF7/F8 are evaluated as their XOR/MUX functions.
   - A register output copies p from its D input, with d capped at 2p(1−p).
   - Register loops are solved by 6 damped sweeps over a levelized order.

   Activity matters even for small outputs. For the same 4 LEDs, Vivado reports 3 mW of I/O when they come from counter MSBs (drc_cfgbvs) and 10 mW when they come from XORed DSP bits (drc_dsp_nopipe). With one global toggle rate, the model can't tell those cases apart.
3. **Features per Vivado component class.** Each feature is MHz-weighted (rate = d × f):
   - Clocks: clock pins × f, clock-net PIPs × f, BUFG × f.
   - Slice Logic: LUT and register output rates, CARRY4 and MUXF rates, LUTRAM/SRL.
   - Signals: rate × routed PIPs per net, and rate × fanout.
   - Block RAM: RAMB18 units × f.
   - DSPs: DSP48E1 × f.
   - MMCM and PLL: count and VCO frequency.
   - I/O: output rate × VCCO², inputs, VREF and differential standards.
4. **Fit.** `flow/power_fit.py` fits each class to Vivado's number for that class with non-negative least squares (mW per feature unit). Device static is fitted as s0 + s1 × dynamic, which covers the temperature rise. Supply rails are split by a second NNLS. The result is `ofx/power_model.json`.

## Reference data

The reference is Vivado 2025.2 report_power on xc7a35tcsg324-1 (vectorless defaults, 25 °C ambient, ΘJA 4.8 °C/W), run on the same RTL and XDC as the open build. `vivado/build_drcpow.tcl` also writes `power_mw.rpt`: the same report after `set_units -power mW`. That keeps three decimals in mW instead of 1 mW steps. The earlier DRC designs (`drcpow` batch) only have the 1 mW-step report.

The designs:
- `designs/power/` (`flow/power_designs.py`): 18 calibration designs, each scaling one resource class at a time.
  - xorshift logic: 8 / 32 / 128 lanes, plus 5 ns and 20 ns clock variants;
  - DSP MACs: 8 / 32 / 64, plus 5 ns;
  - BRAM: 4 / 16 / 40, plus 5 ns;
  - toggling outputs: 8 / 24, plus 5 ns;
  - logic behind an MMCM at 150 and 200 MHz.
- The QoR designs (`build/qor/src`).
- The DRC test designs.
- The primitive designs.

**Important:** each tool's estimate is for its own implementation of the RTL. Vivado's report_power uses Vivado's netlist, while `ofx power` uses the yosys/nextpnr netlist. The fit table therefore has a "LUTs ofx/Vivado" column, so a reader can tell a model error from a difference between the two implementations (see pw_dsp below).

## Validation (honest error, no fitting on the evaluated design)

Two held-out measures:
- **Fixed held-out families.** `heldout_families` in `flow/power_fit.py`: rv_mul, fir, arty_eth, mmcme2, ramb36, dsp, oserdes_pin, srl, pw_mmcm. These are never used to fit the shipped model. Size and frequency variants of one design form one family, so a held-out design has no sibling in training.
- **Leave-one-family-out (LOFO).** Every design is predicted by a model fitted without any design of its family.

<!-- power-results (generated from build/; rerun after new Vivado data) -->
```
Held-out (2): total 1.7 % mean abs error (max 1.8 %), dynamic 3 % mean abs (5.1 mW mean abs)
Held-out with Vivado dynamic >= 10 mW (2): dynamic 3 % mean abs
Training (39): total 3.2 %, dynamic 15 %
Leave-one-family-out over all (41): total 8.1 % (max 75.2 %), dynamic 23 % mean abs (16.5 mW); with Vivado dynamic >= 10 mW (28): dynamic 22 %
```

Held-out designs (shipped model, never trained on these families):

| Design | Vivado total W | ofx total W | err % | Vivado dynamic W | ofx dynamic W | err % | worst class (Vivado W / ofx W) | LUTs ofx/Vivado |
|---|---|---|---|---|---|---|---|---|
| pw_mmcm32_150 | 0.258 | 0.254 | 1.6 | 0.186 | 0.181 | 3 | Slice Logic 0.024 / 0.018 | 1.96 |
| pw_mmcm32_200 | 0.270 | 0.265 | 1.8 | 0.198 | 0.193 | 3 | Slice Logic 0.032 / 0.024 | 1.96 |

Leave-one-family-out, all designs except the tiny drc_* tests (those are in build/power/fit.md):

| Design | Vivado total W | ofx total W | err % | Vivado dynamic W | ofx dynamic W | err % | worst class (Vivado W / ofx W) | LUTs ofx/Vivado |
|---|---|---|---|---|---|---|---|---|
| blinky_p10 | 0.075 | 0.076 | 1.3 | 0.004 | 0.004 | 21 | Clocks 0.001 / 0.001 | 56.00 |
| blinky_p5 | 0.079 | 0.081 | 1.9 | 0.007 | 0.009 | 17 | Clocks 0.001 / 0.002 | 56.00 |
| blinky_p7 | 0.077 | 0.078 | 1.6 | 0.005 | 0.006 | 19 | Clocks 0.001 / 0.001 | 56.00 |
| bram_p10 | 0.213 | 0.190 | 10.7 | 0.140 | 0.118 | 16 | Signals 0.017 / 0.008 | 2.49 |
| bram_p5 | 0.365 | 0.308 | 15.6 | 0.292 | 0.236 | 19 | Signals 0.048 / 0.017 | 1.71 |
| pw_bram16 | 0.165 | 0.164 | 1.1 | 0.093 | 0.091 | 1 | Block RAM 0.056 / 0.060 | 1.61 |
| pw_bram16_p5 | 0.271 | 0.255 | 5.8 | 0.198 | 0.183 | 8 | Signals 0.035 / 0.020 | 1.61 |
| pw_bram4 | 0.105 | 0.105 | 0.5 | 0.033 | 0.033 | 1 | Block RAM 0.014 / 0.015 | 1.59 |
| pw_bram40 | 0.290 | 0.281 | 3.2 | 0.216 | 0.208 | 3 | Block RAM 0.140 / 0.149 | 1.61 |
| pw_dsp32 | 0.133 | 0.180 | 35.4 | 0.061 | 0.108 | 76 | Slice Logic 0.009 / 0.059 | 7.61 |
| pw_dsp32_p5 | 0.199 | 0.288 | 45.0 | 0.127 | 0.215 | 70 | Slice Logic 0.017 / 0.119 | 7.61 |
| pw_dsp64 | 0.182 | 0.276 | 51.5 | 0.110 | 0.203 | 84 | Slice Logic 0.017 / 0.118 | 7.78 |
| pw_dsp8 | 0.096 | 0.110 | 14.1 | 0.025 | 0.038 | 54 | Slice Logic 0.002 / 0.015 | 6.83 |
| pw_io24 | 0.156 | 0.151 | 3.4 | 0.084 | 0.079 | 7 | I/O 0.082 / 0.077 | 1.30 |
| pw_io24_p5 | 0.241 | 0.230 | 4.7 | 0.169 | 0.157 | 7 | I/O 0.163 / 0.153 | 1.30 |
| pw_io8 | 0.109 | 0.107 | 1.7 | 0.037 | 0.035 | 6 | I/O 0.035 / 0.033 | 1.41 |
| pw_mmcm32_150 | 0.258 | 0.254 | 1.6 | 0.186 | 0.181 | 3 | Slice Logic 0.024 / 0.018 | 1.96 |
| pw_mmcm32_200 | 0.270 | 0.265 | 1.8 | 0.198 | 0.193 | 3 | Slice Logic 0.032 / 0.024 | 1.96 |
| pw_xor128 | 0.219 | 0.200 | 8.6 | 0.147 | 0.128 | 13 | Slice Logic 0.065 / 0.038 | 1.97 |
| pw_xor128_p20 | 0.145 | 0.136 | 6.3 | 0.074 | 0.064 | 13 | Slice Logic 0.032 / 0.019 | 1.97 |
| pw_xor32 | 0.118 | 0.114 | 3.3 | 0.046 | 0.042 | 9 | Slice Logic 0.016 / 0.009 | 1.96 |
| pw_xor32_p5 | 0.164 | 0.156 | 5.0 | 0.093 | 0.084 | 9 | Slice Logic 0.032 / 0.019 | 1.96 |
| pw_xor8 | 0.092 | 0.092 | 0.4 | 0.020 | 0.020 | 0 | Slice Logic 0.004 / 0.002 | 1.93 |
<!-- /power-results -->

### What the errors say
- **pw_dsp (LOFO dynamic +54 … +84 %).** This is an implementation difference, not a model error. The open flow uses 6.8–7.8× Vivado's LUTs. yosys keeps the 48-bit accumulator `p <= p + m` in LUTs and CARRY4. Vivado folds it into the DSP48E1 P register. Vivado's Slice Logic for pw_dsp32 is 9 mW; on the open netlist the estimate is 59 mW. For the open flow, this is a synthesis QoR finding (DSP accumulator absorption), not a power model issue.
- **Logic in general.** The xorshift designs use about 1.96× Vivado's LUTs, and Slice Logic still comes out lower than Vivado's, because the fitted per-toggle LUT coefficient is shared with designs that are packed differently. Signals is the class with the largest misses on bram_p5/bram_p10.
- **Small designs.** Under about 10 mW dynamic, Vivado's 1 mW report steps and the ~4 mW of LED I/O dominate, so relative dynamic errors look large. Absolute errors there are a few mW.

## Limits
- Artix-7 xc7a35t only, with one environment (25 °C, default board/airflow). The device static fit (s0 ≈ 72 mW) is for this die.
- No SAIF/VCD input yet. Activity is vectorless only.
- Rails: Vccint/Vccaux/Vcco/Vccbram are split by fitted shares. Only the totals are validated.
- MMCM/PLL coefficients come from few designs: the drc MMCM/PLL tests for training, and pw_mmcm is held out.

## Files
- `ofx/power.py`: features, activity propagation, estimate, report; `ofx power` (`ofx/cli.py`).
- `ofx/power_model.json`: the fitted model, including its training/held-out lists and errors.
- `flow/power_designs.py`, `designs/power/`: the calibration designs. Their open builds are in `build/power/open/`.
- `flow/power_fit.py`: the fit, the held-out and LOFO evaluation, and `build/power/fit.md`.
- `vivado/build_drcpow.tcl`, `vivado/run_drcpow.ps1`: the Vivado references.
