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
Held-out (10): total 10.0 % mean abs error (max 30.2 %), dynamic 71 % mean abs (11.6 mW mean abs)
Held-out with Vivado dynamic >= 10 mW (8): dynamic 37 % mean abs
Training (45): total 5.6 %, dynamic 30 %
Leave-one-family-out over all (55): total 7.4 % (max 86.1 %), dynamic 34 % mean abs (10.9 mW); with Vivado dynamic >= 10 mW (39): dynamic 33 %
```

Held-out designs (shipped model, never trained on these families):

| Design | Vivado total W | ofx total W | err % | Vivado dynamic W | ofx dynamic W | err % | worst class (Vivado W / ofx W) | LUTs ofx/Vivado |
|---|---|---|---|---|---|---|---|---|
| dsp48e1 | 0.087 | 0.087 | 0.2 | 0.015 | 0.015 | 0 | Signals 0.001 / 0.000 | 1.31 |
| dsp_cascade | 0.087 | 0.092 | 5.8 | 0.015 | 0.020 | 32 | Slice Logic 0.000 / 0.004 | 1.31 |
| fir_p5 | 0.173 | 0.225 | 30.2 | 0.101 | 0.152 | 51 | DSPs 0.045 / 0.086 | 1.28 |
| mmcme2_adv | 0.190 | 0.193 | 1.6 | 0.118 | 0.121 | 2 | I/O 0.010 / 0.012 | 2.25 |
| oserdes_pin | 0.079 | 0.084 | 5.4 | 0.008 | 0.012 | 54 | Slice Logic 0.000 / 0.008 | 3.00 |
| pw_mmcm32_150 | 0.258 | 0.254 | 1.4 | 0.186 | 0.182 | 2 | Slice Logic 0.024 / 0.019 | 1.96 |
| pw_mmcm32_200 | 0.270 | 0.266 | 1.7 | 0.198 | 0.193 | 3 | Slice Logic 0.032 / 0.025 | 1.96 |
| ramb36e1 | 0.088 | 0.089 | 0.9 | 0.017 | 0.017 | 4 | Signals 0.001 / 0.000 | 1.29 |
| rv_mul_p10 | 0.084 | 0.109 | 29.8 | 0.012 | 0.037 | 202 | Signals 0.003 / 0.010 | 1.69 |
| srl | 0.077 | 0.094 | 23.2 | 0.005 | 0.023 | 355 | Slice Logic 0.000 / 0.019 | 1.00 |

Leave-one-family-out, all designs except the tiny drc_* tests (those are in build/power/fit.md):

| Design | Vivado total W | ofx total W | err % | Vivado dynamic W | ofx dynamic W | err % | worst class (Vivado W / ofx W) | LUTs ofx/Vivado |
|---|---|---|---|---|---|---|---|---|
| blinky_p10 | 0.075 | 0.076 | 0.7 | 0.004 | 0.004 | 10 | I/O 0.003 / 0.003 | 56.00 |
| blinky_p5 | 0.079 | 0.080 | 0.9 | 0.007 | 0.008 | 8 | I/O 0.006 / 0.006 | 56.00 |
| blinky_p7 | 0.077 | 0.078 | 0.8 | 0.005 | 0.006 | 8 | I/O 0.004 / 0.005 | 56.00 |
| bram_p10 | 0.213 | 0.183 | 14.3 | 0.140 | 0.111 | 21 | Block RAM 0.090 / 0.077 | 2.49 |
| bram_p5 | 0.365 | 0.293 | 19.7 | 0.292 | 0.221 | 24 | Signals 0.048 / 0.016 | 1.71 |
| dsp48e1 | 0.087 | 0.086 | 0.4 | 0.015 | 0.015 | 3 | Signals 0.001 / 0.000 | 1.31 |
| dsp_cascade | 0.087 | 0.088 | 1.3 | 0.015 | 0.016 | 6 | Signals 0.001 / 0.000 | 1.31 |
| fir_p5 | 0.173 | 0.213 | 23.2 | 0.101 | 0.140 | 39 | DSPs 0.045 / 0.086 | 1.28 |
| lutram_infer | 0.085 | 0.081 | 5.0 | 0.013 | 0.009 | 33 | I/O 0.012 / 0.006 | 1.00 |
| mmcme2_adv | 0.190 | 0.193 | 1.6 | 0.118 | 0.121 | 2 | I/O 0.010 / 0.012 | 2.25 |
| oserdes_pin | 0.079 | 0.077 | 2.4 | 0.008 | 0.006 | 27 | I/O 0.007 / 0.003 | 3.00 |
| plle2_adv | 0.202 | 0.249 | 23.4 | 0.130 | 0.177 | 36 | PLL 0.118 / 0.162 | 2.25 |
| pw_bram16 | 0.165 | 0.158 | 4.5 | 0.093 | 0.086 | 7 | Signals 0.013 / 0.010 | 1.61 |
| pw_bram16_p5 | 0.271 | 0.244 | 9.8 | 0.198 | 0.172 | 13 | Signals 0.035 / 0.020 | 1.61 |
| pw_bram4 | 0.105 | 0.104 | 1.1 | 0.033 | 0.032 | 3 | Slice Logic 0.002 / 0.002 | 1.59 |
| pw_bram40 | 0.290 | 0.267 | 7.7 | 0.216 | 0.195 | 10 | Signals 0.035 / 0.025 | 1.61 |
| pw_dsp32 | 0.133 | 0.153 | 14.8 | 0.061 | 0.081 | 32 | Slice Logic 0.009 / 0.030 | 7.61 |
| pw_dsp32_p5 | 0.199 | 0.233 | 17.5 | 0.127 | 0.161 | 27 | Slice Logic 0.017 / 0.060 | 7.61 |
| pw_dsp64 | 0.182 | 0.221 | 21.5 | 0.110 | 0.149 | 35 | Slice Logic 0.017 / 0.060 | 7.78 |
| pw_dsp8 | 0.096 | 0.103 | 6.6 | 0.025 | 0.031 | 25 | Slice Logic 0.002 / 0.008 | 6.83 |
| pw_io24 | 0.156 | 0.150 | 3.9 | 0.084 | 0.078 | 7 | I/O 0.082 / 0.076 | 1.30 |
| pw_io24_p5 | 0.241 | 0.228 | 5.2 | 0.169 | 0.156 | 8 | I/O 0.163 / 0.152 | 1.30 |
| pw_io8 | 0.109 | 0.106 | 2.2 | 0.037 | 0.034 | 7 | I/O 0.035 / 0.033 | 1.41 |
| pw_mmcm32_150 | 0.258 | 0.254 | 1.4 | 0.186 | 0.182 | 2 | Slice Logic 0.024 / 0.019 | 1.96 |
| pw_mmcm32_200 | 0.270 | 0.266 | 1.8 | 0.198 | 0.193 | 3 | Slice Logic 0.032 / 0.025 | 1.96 |
| pw_xor128 | 0.219 | 0.201 | 8.3 | 0.147 | 0.129 | 13 | Slice Logic 0.065 / 0.040 | 1.97 |
| pw_xor128_p20 | 0.145 | 0.136 | 6.2 | 0.074 | 0.064 | 12 | Slice Logic 0.032 / 0.020 | 1.97 |
| pw_xor32 | 0.118 | 0.114 | 3.5 | 0.046 | 0.042 | 9 | Slice Logic 0.016 / 0.010 | 1.96 |
| pw_xor32_p5 | 0.164 | 0.156 | 5.1 | 0.093 | 0.084 | 9 | Slice Logic 0.032 / 0.020 | 1.96 |
| pw_xor8 | 0.092 | 0.092 | 0.2 | 0.020 | 0.020 | 2 | Slice Logic 0.004 / 0.002 | 1.93 |
| ramb36e1 | 0.088 | 0.089 | 0.8 | 0.017 | 0.017 | 4 | Signals 0.001 / 0.000 | 1.29 |
| rv_big_p10 | 0.086 | 0.161 | 86.1 | 0.014 | 0.088 | 541 | Block RAM 0.000 / 0.058 | 1.63 |
| rv_mul_p10 | 0.084 | 0.108 | 28.4 | 0.012 | 0.036 | 193 | Block RAM 0.000 / 0.007 | 1.69 |
| rv_soc_p10 | 0.080 | 0.100 | 25.3 | 0.008 | 0.028 | 250 | Block RAM 0.000 / 0.007 | 1.75 |
| srl | 0.077 | 0.082 | 7.0 | 0.005 | 0.010 | 105 | Slice Logic 0.000 / 0.007 | 1.00 |
<!-- /power-results -->

### What the errors say
- **pw_dsp (LOFO dynamic +25 … +35 %).** This is an implementation difference, not a model error. The open flow uses 6.8–7.8× Vivado's LUTs. yosys keeps the 48-bit accumulator `p <= p + m` in LUTs and CARRY4. Vivado folds it into the DSP48E1 P register. Vivado's Slice Logic for pw_dsp32 is 9 mW; on the open netlist the estimate is 30 mW. For the open flow, this is a synthesis QoR finding (DSP accumulator absorption), not a power model issue.
- **Logic in general.** The xorshift designs use about 1.96× Vivado's LUTs, and Slice Logic still comes out lower than Vivado's, because the fitted per-toggle LUT coefficient is shared with designs that are packed differently. Signals is the class with the largest misses on bram_p5/bram_p10.
- **Block RAM on the CPU designs (rv_soc/rv_mul/rv_big, LOFO dynamic +190 … +540 %).** Vivado reports 0 W of Block RAM for them, the model 7-58 mW. The model charges every RAMB18 unit at its clock frequency; it does not yet look at the enable and write-enable activity, which vectorless Vivado evidently does. Largest open model error (the 2026-11-08 refit added these designs).
- **DSPs on fir_p5 (held out, total +30 %).** DSPs 86 mW vs Vivado 45 mW: the DSP coefficient is per DSP48E1 and MHz only, without the data activity of the cascaded P path.
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
