# WIP: offline DFX gaps on Artix-7 (2026-11-06 brief, items 1-7)

Stopped 2026-11-06 23:20. Results: docs/phase16-dfx-gaps.md (all committed). Nothing of this work is running.

Open, with ready inputs (re-run from the repo root; both wait for resources as the shared rules require):
- Vivado (phase 16 §4, §6, §7): `nohup setsid bash docs/wip/dfx-gaps/job_vq.sh &` runs, in ~20-minute
  invocations with the lock released between them: dsp_um_* (USE_MULT fuzz), dfx_dev_xc7a{50,100,200}t,
  Vivado's timer on our placements (build/dfxgaps/xtime/src, made by flow/xtime_prep.py; untracked, regenerate
  with the commands in phase 16 if build/ was cleaned), then dfx_rv_p10 and dfx_rv_p5. Then:
  `python3 flow/dsp_use_mult.py`, `python3 flow/dfx_vivado_compare.py --json build/dfxgaps/compare.json`,
  `flow/vivado_variant_compare.sh` per die (DESIGN/V/REGION/CFGS="rm_xor rm_andn grey", device env vars).
- rv_ppt seeds 1 and 3 with fix_endpoints off (phase 16 §5.2): `bash docs/wip/dfx-gaps/job_s13.sh`
  (OFX_MAX_NEXTPNR=1).
- rv2 re-timing needs an rtkeep + hardblock-timing binary (as rthb was made from router).
