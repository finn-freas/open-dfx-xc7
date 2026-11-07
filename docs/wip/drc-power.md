# WIP: DRC deck + power analysis (roadmap rows "DRCs", "Power analysis")

Updated 2026-11-06, about 22:10.

## Done (committed)
- 89058a3 `ofx drc` deck checked against Vivado.
- 1fe268f power: vectorless activity, 18 calibration designs, family holdout / LOFO.
- 5abcac9 docs/drc.md, docs/power.md, roadmap rows.
  - Results are generated blocks (`<!-- drc-results -->`, `<!-- power-results -->`).
  - Note: this commit also picked up another agent's uncommitted roadmap line ("Build time vs Vivado").

## Running
- Vivado, one design per lock, in the lowest-priority group.
  - Script: scratchpad dp_viv_batch.ps1. Log: C:/Users/finnf/open-dfx-xc7-vivado/drcpow_c_run.log. Tag: drcpow_b1.
  - Queue: drc_idelay_ref200, drc_idelay_ref200g, ramb36e1, mmcme2_adv, dsp_cascade, rv_mul_p10, fir_p5, srl, oserdes_pin, dsp48e1, plle2_adv, lutram_infer, rv_soc_p10, rv_big_p10.

## Next (each step is rerunnable)
1. `python3 flow/power_fit.py --run`. This refits; the held-out set grows as the queue lands.
2. `python3 flow/drc_compare.py`.
3. `python3 <scratchpad>/dp_filldocs.py`, which refreshes the generated doc blocks. The script is small: it reads build/drc/compare.md and build/power/fit.md.
4. Rerun the roadmap row script (dp_roadmap.py) and commit.
5. IDELAY: compare Vivado on drc_idelay_ref200 and drc_idelay_ref200g against gap/idelay (Place 30-578), then add the finding to docs/drc.md (the "IDELAY note below" is still missing).
