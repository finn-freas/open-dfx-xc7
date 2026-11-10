# WIP: DFX toward Vivado parity (wind-down 2026-11-08 ~22:10)

Results: docs/phase16-dfx-gaps.md, docs/phase17-dfx-quality.md (§1-5 written; §6 Vivado table incomplete).

State at wind-down:
- Vivado exact-import results so far (python3 flow/dfx_exact_table.py): anchor as built 100.72 MHz (108.72 without
  ICAPE2), anchor ICAP-timed HeAP (rthb_t) 95.15, rv_ppt seed 1 as built 102.57 (5 ns, Vivado timer). Too few
  for the per-seed comparison or the partition-pin default decision.
- Still alive (stopping them was refused by the permission classifier): build/dfxgaps/job_exactp.sh,
  job_exactq2.sh, job_exactq3.sh (wait for Vivado slot 3, then run one build_rte.tcl per name; none was running at
  22:10), job_reg3.sh (pptreg3 seed 3, nextpnr in progress). docs/wip/dfx-gaps/job_vq.sh is the validation agent's.

Resume:
- Vivado (slot 3): bash flow/dfx_exact_vivado.sh --run $(cat build/dfxgaps/exact_prio.txt) anchb28_1_xor_n_p5
  anchb28_2_xor_n_p5 anchb28_3_xor_n_p5 flat1_s1_p5 flat2_s2_p5 flat3_s3_p5   (finished names are skipped)
- Then fill phase 17 §6 from flow/dfx_exact_table.py, decide the partition-pin default on Vivado's numbers,
  update docs/dfx-vs-vivado.md rows 6/15.
- Placer-stack aborts in the partition-pin flow (phase 17 §3) are for the placer agents.
