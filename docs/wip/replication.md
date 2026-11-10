# WIP: replication / location split of critical high-fanout flip-flops -- state file

Owner: the replication agent (resumed 2026-11-10 11:40 after the hard stop; the first agent left no notes).
Earlier stages (v1 fanout mode, v2 critical-cell mode `cc=1`): docs/drafts/nextpnr-replicate.md and
docs/wip/gap-analysis.md. This file covers the third stage, **split mode**, and its evaluation.

Yardstick for every Fmax below unless marked: **Vivado 2025.2 timer on the exact import** (flow/exact_src.py +
vivado/build_rte.tcl mode `fixed`: Vivado places nothing of ours, routes with -preserve; Fmax = 1000 / (5 - WNS excl.
ICAPE2), slack.txt `wns_noicap`). "nextpnr timer" is marked where used and decides nothing.

## What the killed agent had done (reconstructed from disk)
- Source: worktree build/src/nextpnr-afo (HEAD e0a13c17 + uncommitted edits). replicate.cc there = the cc=1 pass of
  docs/drafts/nextpnr-replicate.patch + ~250 lines:
  - `split=1` (runs before cc): the `snets` (16) worst flip-flop nets with fanout >= `sminfo` (8) whose worst sink slack
    is within `swin` (800 ps) of the worst such net; movable sinks k-means-clustered by position into k = 2..`skmax` (4)
    groups; the original keeps the nearest group, every other group gets a copy (FF, together with its D LUT) on the
    free bel that serves it best by the model bound; the k with the best bound is made if it beats the unsplit bound
    by `sgain` (30 ps) per copy. No margin rules ("loose").
  - `ssettle` (1: the cc pass's settle step after the split; the bench uses 0), `sctrl`, `sins` (0: the copy's own
    D/CE/SR arcs are left out of the estimate, the copy goes where its sinks are), `resa` (1: `-o sa-refine` once more
    after the pass if copies were made; 2: always = control). xilinx.cc/.h: `replicate_resa` hook in postPlace.
  - The other uncommitted edits in that worktree (placer_static.*, sa_refine.cc, xilinx.cc options arc-fanout /
    chain-*) are the earlier, not-adopted afo / chain experiments (docs/wip/gap-analysis.md).
- Binaries: build/nextpnr-build/split (10:35, before `sins` existed) and split2 (10:46, current source).
- Bench variants (flow/place_bench.py, uncommitted; all = cb_all2 arguments + `-o replicate=...`):

  | variant | binary | replicate= | meaning |
  |---|---|---|---|
  | cb2_splnoop | split | (none) | no-op control: FASM identical to ua_dxy (= cb_all2) rv_soc s1-3, rv_mul s1-2 (re-checked) |
  | cb2_resa | split | cc=0:resa=2 | control: sa-refine twice, no copies |
  | cb2_splnr | split | cc=0:split=1:ssettle=0 | split only |
  | cb2_spl | split | cc=0:split=1:ssettle=0:resa=1 | split + sa-refine again |
  | cb2_splcc | split | split=1:ssettle=0:resa=1 | split + critical-cell pass + sa-refine again |
  | cb2_splc | split2 | cc=0:split=1:ssettle=0:sins=0 | split, copy placed for its sinks only |
  | cb2_splcr | split2 | ...:sins=0:resa=1 | same + sa-refine again |

  rv_mul uses the `_dq` forms.
- Probes build/split_probe/ (nextpnr only): the pass does split the target registers on rv_mul s1: pcpi_rs1[1] (fanout
  28) into 3 groups, pcpi_rs1[0] (27) into 4, pcpi_rs2[1], pcpi_rs2[0]; 11 FF copies, each with its D LUT. Its own
  model's worst slack gets WORSE (-4.516 -> -5.273, sins=0: -6.255 ns): the copies' own D/CE input paths become worst.
- Runs (logs build/exact/spl_run.log, splc_run.log): nextpnr + exact export finished for seed 1, all four designs, all
  six option variants; seed 2 only in part. **No Vivado run of any split variant had been made**: there was no result.
- nextpnr timer, s1 (for the record only): rv_mul ua_dxy 102.09, resa 102.34, splnr 102.87, spl 96.87, splc 100.55,
  splcr 100.11, splcc 95.89; rv_soc 97.98 / resa 100.59 / splnr 100.18 / spl 95.78 / splc 100.18 / splcr 99.86 /
  splcc 100.45.
- Copies made at s1: rv_mul 11 FF (+11 D LUTs), rv_soc 4, bram 16-17, rv_big 0 (rv_big's split variants without resa
  are the cb_all2 placement itself).

## Oracle: Vivado's own replication on the cb_all2 placement (ceiling for this lever)
Already run by the first agent 2026-11-09 (build/exact/po_run.sh; mode `fixed_po` = our placement, then
`phys_opt_design -fanout_opt -critical_cell_opt`, then route; names `<d>_p5_cb2po_s<s>_exact`), all four designs,
seeds 1-3. WNS excl. ICAPE2, ns, Vivado timer:

| design | s1 base -> po | s2 | s3 | Fmax gain |
|---|---|---|---|---|
| rv_mul | -3.012 -> -2.716 | -3.780 -> -3.395 | -3.722 -> -3.415 | +3.8 / +4.6 / +3.8 %, mean +4.1 % |
| rv_soc | -3.677 -> -3.086 | -4.138 -> -3.259 | -3.915 -> -3.427 | +7.3 / +10.6 / +5.8 % |
| rv_big | -6.248 -> -4.915 | -5.165 -> -4.726 | -4.473 -> -4.473 | +13.4 / +4.5 / 0.0 % |

- On rv_mul phys_opt replicated pcpi_rs1[1] 1-3x, pcpi_rs1[0] 1-2x, pcpi_rs2[0/1] 2-3x (s2, s3) and one LUT net
  (reintegrate$87353.A[3]) -- 6-8 new cells per run. After it the worst path is a RAM-output path on s1 and s3.
  So the ceiling on rv_mul is about +4 %: the next path class (block-RAM outputs) sits ~0.3 ns behind.
- On Vivado's own placement (vref_po) phys_opt gains 0.
- **Caveat found now:** in the `fixed` exact import Vivado's place_design itself runs a fanout-replication step:
  on rv_mul ua_dxy_dq s1 (the control!) the log has "Processed net pcpi_rs2[N]. Replicated 1 times" for 12 pcpi_rs2
  bits ("Created 12 new instances"), and "Net pcpi_rs2[*] was not replicated" for the rest. Those replicas are new,
  unfixed cells that Vivado places. So the rv_mul control already contains a little Vivado replication, the same
  for every variant unless our pass has split the net first.

## Export of the copies (checked)
- flow/exact_src.py exports each copy as a new cell (xr_N; names.json maps `<cell>$repN` -> xr_N) with a row in
  place.txt; export.json `new_FDRE` = number of FF copies.
- build/splitres/prep.py appends `set_property DONT_TOUCH true [get_cells {xr_..}]` for every copy to the export's
  constraints.xdc before the Vivado run (the `fixed` mode runs no opt_design / phys_opt_design, but place_design's
  internal passes exist, see the caveat). Control sets: a copy has its original's C/CE/R nets (build/repl/cmp_copies.py).

## Evaluation (running)
- Scripts: build/splitres/npr.sh (nextpnr one at a time via place_bench/npwait + export), build/splitres/viv.sh
  (prep + 2 Vivado workers through flow/rte_dump_vivado.sh, RTE_ANY_SLOT=1 = vivado_slot.sh locks),
  build/splitres/table.py (table).
- Started 11:52: Vivado on the 20 distinct seed-1 exports (build/splitres/s1_names.txt, log viv_s1.out);
  nextpnr seeds 2-3 for splc splcr resa spl splnr (log npr_s23.out).

Results: (pending)

## Resume
```
cd ~/open-dfx-xc7
# nextpnr + export (skips finished runs):
setsid nohup bash build/splitres/npr.sh "2 3" "splc splcr resa spl splnr" >> build/splitres/npr_s23.out 2>&1 < /dev/null &
# Vivado (skips names with a status.txt):
setsid nohup bash build/splitres/viv.sh build/splitres/s1_names.txt 2 >> build/splitres/viv_s1.out 2>&1 < /dev/null &
python3 build/splitres/table.py
```
