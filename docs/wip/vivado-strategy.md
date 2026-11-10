# WIP: Vivado placement strategy study (state file)

Owner: the Vivado-strategy agent.
- Goal: learn Vivado's placement strategy from its outputs only (placements, Tcl reports, logs; no binary
  inspection), and turn it into ranked rules for our placer.
- Result doc: docs/vivado-placement-strategy.md.

## Data
- Same-netlist pair (identical cell names):
  - Vivado places our exported netlist itself: build/exact/<d>_p5_vref_exact, place_design default, no opt_design.
  - Ours: the exact imports build/exact/<d>_p5_pl14_off_stub_s{1,2,3}_exact.
  - Designs: rv_soc, bram, rv_big.
- Pin-lock pair: build/exact/rv_soc_p5_dp0_s1_exact{,_nolock}. The cells were rebuilt with flow/exact_dump.py into
  build/viv_strategy/xdump.
- QoR suite: Vivado's free runs (nets_sites.txt) against the open flow's base routed JSON (flow/viv_suite_shape.py).
- New Vivado runs, prepared and not run yet:
  - Runner: flow/viv_strategy_run.sh with vivado/viv_strategy.tcl, slot 1 only. It takes slot 1 only after the slot
    has stayed free for 60 s.
  - Sources: C:\Users\finnf\open-dfx-xc7-vivado\designs\viv_strategy\<name>.
  - Output: build/viv_strategy/<name> on the Windows side; log ~/open-dfx-xc7/build/viv_strategy/run1.log.
  - Names:
    - `*_vivown_exact`: Vivado's own placement through the exact import, no pin locks (flow/viv_own_exact.py).
    - `rv_soc_edif`, `bram_edif`: directive sweep on the exported netlist.
    - `*_rtl`: Vivado synthesis with hierarchy names, opt, place Default.

## State (2026-11-08 22:05, wound down at the user's request)
- No runner and no waiter is left; no Vivado run of mine was in progress when I stopped. The runner had been waiting
  for slot 3, held by another agent.
- Done:
  - rv_soc_vivown_exact and bram_vivown_exact (the import is faithful);
  - bram_edif (directive sweep);
  - rv_soc_rtl, bram_rtl, rv_mul_rtl, rv_big_rtl, aes_rtl.
- Doc: docs/vivado-placement-strategy.md, observations 1-12 and ranked rules.
- Pending (sources prepared):
  - sha256_rtl, or1200_rtl, serv_rtl: hierarchy on more designs;
  - rv_soc_edif: directive sweep on rv_soc. Its first try failed on the EDIF name, fixed in 41326ea.
  - After they run, add the rv_soc directive table and the extra hierarchy rows to observations 11/12.

## To resume
- Resume: `setsid nohup bash flow/viv_strategy_run.sh run rv_soc_edif sha256_rtl or1200_rtl serv_rtl > build/viv_strategy/run3.log 2>&1 &`
  (it uses slot 3 via vivado_acquire3).
- Start the runner (general form): `setsid nohup bash flow/viv_strategy_run.sh run <names> > build/viv_strategy/run1.log 2>&1 &`.
  Names with a status.txt are skipped. Check it with `pgrep -af viv_strategy_ru[n]`.
- Tables:
  - `python3 flow/viv_strategy.py directives rv_soc_edif`;
  - `python3 flow/viv_strategy.py hier rv_soc_rtl --depth 2`;
  - `python3 flow/viv_conn.py distance rv_soc ...`.
