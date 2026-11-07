# Build time: open flow vs Vivado on Artix-7

Date: 2026-11-06. Workstream: tool build time.

## Method and how to read the numbers

- **Machine:** 16 threads, WSL2 with about 11 GB RAM, shared with about 12 other agents. The 1-minute load average
  was 6-18 during every run, with 1-3 other nextpnr processes, so the times move by up to 2x between identical
  runs (rv_soc, unchanged flow: total 80.9-151.0 s). Every cell below is therefore "median (min-max, n)", and the
  load at the start of each run is in the table. Waiting for a nextpnr slot (`ofx/npwait.sh`, limit 3) is not
  counted. Compare medians and only trust differences much larger than the spread.
- **Open flow:** `flow/build_openxc7.py`, which is what `ofx build` runs: yosys `synth_xilinx -flatten -abc9`, then
  the nightly nextpnr-xilinx (ce3f7c18, heap placer, router2), then fasm2frames and xc7frames2bit.
  - Harness: `flow/runtime_prof.py` (dry run unless `--run`; `--variant`, `--reps`).
  - Stage times come from build_openxc7's own timer.
  - The nextpnr phases come from timestamping every log line as it is printed (`flow/runtime_np.sh` and
    `flow/runtime_ts.py`; the log itself is unchanged). The phase boundaries are:
    - start: process start to "Packing constants" (chipdb mmap, JSON, XDC);
    - pack: to "Device utilisation";
    - placement (it includes the delay-matrix build): to "Routing global clocks";
    - routing (it includes the final timing report and the FASM write): to the end.
  - Results: `build/runtime/<variant>/<design>/r<k>/runtime.json`, with each run's logs next to it.
  - Tables: `flow/runtime_table.py`.
- **Vivado:** 2025.2, `vivado/build_runtime.tcl` run through `vivado/run_runtime.sh` (shared lock, one design per
  Vivado process).
  - Steps: read_verilog/read_xdc, synth_design, opt_design, place_design, route_design and write_bitstream, all
    with default directives. This is the same step list as `vivado/build_gap.tcl`.
  - `general.maxThreads` is recorded in times.txt.
  - "Total" is the wall time of the whole Vivado process, start-up and exit included.
  - Results: `C:\Users\finnf\open-dfx-xc7-vivado\build\runtime\<design>\r<k>\` (times.txt, vivado.log,
    util.rpt, timing.rpt).
- **Designs:**
  - **blinky:** `designs/blinky`, xc7a35t.
  - **rv_soc:** `designs/rv_soc` (picorv32 SoC with ICAP), xc7a35t, built from the same sources as the e2e check.
  - **litex_ddr3:** the LiteX/VexRiscv/LiteDRAM SoC `designs/ddr3/arty_ddr3`, xc7a35t, 100 MHz. nextpnr gets the XDC
    without the lines it cannot read; Vivado gets LiteX's full XDC.
  - **mc12_a100:** new, `designs/runtime/mc12_a100`, xc7a100t. It has twelve `qor_rv_big` cores (picorv32 with
    fast multiplier, divider and a 16 KB RAM each). Each core gets the UART input through a different number of
    flip-flops, so synthesis cannot merge them. nextpnr reports 29915 SLICE_LUTX (23 %), 13264 SLICE_FFX and 48
    DSP48E1.
- **Fmax:** only nextpnr's own timer is quoted, and only as a sign of whether an option changes QoR. This document
  makes no Vivado-timer claim.

## Results

### blinky

| stage | open flow, before (base) | open flow, after (dmc) | Vivado 2025.2 | Vivado step |
|---|---|---|---|---|
| synthesis | 4.8 (4.1-5.4, n=3) | 5.3 (4.4-5.4, n=4) | - | read+synth |
| P&R start: chipdb, netlist, pack | 0.4 (0.4-0.5, n=3) | 0.5 (0.5-0.7, n=4) | - | opt |
| placement (incl. delay matrix) | 3.9 (3.6-5.3, n=3) | 0.5 (0.4-4.3, n=4) | - | place |
| routing (incl. final timing, FASM) | 2.3 (1.9-2.5, n=3) | 2.1 (2.1-2.7, n=4) | - | route |
| bitstream (fasm2frames + xc7frames2bit) | 1.2 (1.0-1.3, n=3) | 1.1 (1.0-1.6, n=4) | - | bitstream |
| flow overhead (Python / Vivado start+exit) | 0.2 (0.2-0.5, n=3) | 0.2 (0.2-0.4, n=4) | - | overhead |
| total | 13.2 (11.1-15.1, n=3) | 10.5 (8.5-13.6, n=4) | - | process_wall |
| nextpnr CPU (user+sys) | 6.6 (5.8-8.3, n=3) | 3.4 (2.9-7.0, n=4) | | |
| load average at start | 8.6 (8.1-14.2, n=3) | 13.4 (10.8-14.2, n=4) | - | |

### rv_soc

| stage | open flow, before (base) | open flow, after (dmc) | Vivado 2025.2 | Vivado step |
|---|---|---|---|---|
| synthesis | 13.4 (10.1-38.3, n=3) | 10.6 (10.5-11.9, n=3) | - | read+synth |
| P&R start: chipdb, netlist, pack | 0.6 (0.6-0.9, n=3) | 0.6 (0.5-0.8, n=3) | - | opt |
| placement (incl. delay matrix) | 10.3 (8.7-18.7, n=3) | 6.1 (5.6-6.2, n=3) | - | place |
| routing (incl. final timing, FASM) | 57.9 (50.8-88.0, n=3) | 57.5 (44.3-60.7, n=3) | - | route |
| bitstream (fasm2frames + xc7frames2bit) | 3.5 (2.9-4.6, n=3) | 2.9 (2.7-3.7, n=3) | - | bitstream |
| flow overhead (Python / Vivado start+exit) | 0.2 (0.2-0.6, n=3) | 0.2 (0.2-0.2, n=3) | - | overhead |
| total | 80.9 (78.2-151.0, n=3) | 79.2 (64.0-81.9, n=3) | - | process_wall |
| nextpnr CPU (user+sys) | 68.1 (62.8-108.8, n=3) | 65.5 (51.4-68.5, n=3) | | |
| load average at start | 8.4 (7.6-14.3, n=3) | 7.9 (7.4-11.5, n=3) | - | |
| Fmax u_bridge.clk, MHz (nextpnr timer) | 159.9 (159.9-159.9, n=3) | 159.9 (159.9-159.9, n=3) | | |

Opt-in trade-offs, rv_soc:

| variant | placement | routing | total | nextpnr CPU | Fmax (nextpnr timer) | load |
|---|---|---|---|---|---|---|
| exitbb | 7.1 (6.4-27.1, n=5) | 9.9 (8.1-10.7, n=5) | 35.6 (33.1-51.1, n=5) | 19.0 (18.7-30.8, n=5) | 163.3 (163.3-163.3, n=5) | 9.4 (7.9-13.0, n=5) |

### litex_ddr3

| stage | open flow, before (base) | open flow, after (dmc) | Vivado 2025.2 | Vivado step |
|---|---|---|---|---|
| synthesis | 53.2 (45.7-60.6, n=2) | 44.4 (43.5-45.3, n=2) | - | read+synth |
| P&R start: chipdb, netlist, pack | 1.4 (1.1-1.7, n=2) | 1.1 (1.0-1.1, n=2) | - | opt |
| placement (incl. delay matrix) | 100.0 (86.0-113.9, n=2) | 69.6 (67.8-71.5, n=2) | - | place |
| routing (incl. final timing, FASM) | 50.2 (45.9-54.6, n=2) | 47.1 (42.3-51.8, n=2) | - | route |
| bitstream (fasm2frames + xc7frames2bit) | 13.4 (12.7-14.1, n=2) | 13.5 (12.8-14.2, n=2) | - | bitstream |
| flow overhead (Python / Vivado start+exit) | 0.2 (0.1-0.2, n=2) | 0.3 (0.3-0.3, n=2) | - | overhead |
| total | 218.3 (200.3-236.3, n=2) | 175.9 (171.5-180.4, n=2) | - | process_wall |
| nextpnr CPU (user+sys) | 157.3 (155.7-159.0, n=2) | 132.7 (129.1-136.2, n=2) | | |
| load average at start | 12.4 (7.3-17.5, n=2) | 8.6 (8.3-9.0, n=2) | - | |
| Fmax sys_clk, MHz (nextpnr timer) | 111.0 (111.0-111.0, n=2) | 111.0 (111.0-111.0, n=2) | | |

Opt-in trade-offs, litex_ddr3:

| variant | placement | routing | total | nextpnr CPU | Fmax (nextpnr timer) | load |
|---|---|---|---|---|---|---|
| exitbb | 61.6 (n=1) | 46.4 (n=1) | 162.8 (n=1) | 123.2 (n=1) | 111.7 (n=1) | 8.1 (n=1) |
| pr_t4 | 53.9 (n=1) | 41.6 (n=1) | 149.0 (n=1) | 134.6 (n=1) | 102.7 (n=1) | 6.7 (n=1) |

### mc12_a100

| stage | open flow, before (base) | open flow, after (dmc) | Vivado 2025.2 | Vivado step |
|---|---|---|---|---|
| synthesis | - | - | - | read+synth |
| P&R start: chipdb, netlist, pack | - | - | - | opt |
| placement (incl. delay matrix) | - | - | - | place |
| routing (incl. final timing, FASM) | - | - | - | route |
| bitstream (fasm2frames + xc7frames2bit) | - | - | - | bitstream |
| flow overhead (Python / Vivado start+exit) | - | - | - | overhead |
| total | - | - | - | process_wall |
| nextpnr CPU (user+sys) | - | - | | |
| load average at start | - | - | - | |
| Fmax g_core[0].u_core.clk, MHz (nextpnr timer) | - | - | | |

Opt-in trade-offs, mc12_a100:

| variant | placement | routing | total | nextpnr CPU | Fmax (nextpnr timer) | load |
|---|---|---|---|---|---|---|
| static | 173.1 (n=1) | 86.5 (n=1) | 396.8 (n=1) | 398.5 (n=1) | 124.2 (n=1) | 8.2 (n=1) |

**How to read the tables:**
- "before" is the flow as it was, run with `OFX_DM_CACHE=0`.
- "after" is the flow with the delay-matrix cache, which is now the default. Its .frames are identical to "before"
  in every run.
- The first "after" run of each device fills the cache. That run is the 4.3 s outlier in blinky placement.
- The faster fasm2frames (item 5) was switched on after these runs and is measured on its own.
- The opt-in tables are QoR trade-offs. None of them is on by default.

**mc12_a100 with the default (heap) placer never finished** (build/runtime/base/mc12_a100/r1, load 14.4 at start):
- HeAP took 921 s and the annealing refinement 267 s.
- router2 then went from 51188 overused wires at iteration 1 down to 3979 at iteration 10 (2476 s into the run).
- After that it climbed again, to 5764 at iteration 17 (4194 s).
- I stopped it at 4340 s. It has no column in the table.
- With `--placer static`, the same netlist placed in 173 s, routed in 10 iterations with 0 overuse, and gave 124.21 MHz
  (nextpnr timer). The whole flow took 397 s.

## Vivado reference

My own Vivado runs (`vivado/run_runtime.sh`) did not start in this session: other agents held the shared Vivado lock
the whole time, and this workstream yields to them. Until those runs exist, the Vivado reference is
the earlier runs of `vivado/build_gap.tcl`:
- It runs the same steps (synth, opt, place, route, write_bitstream) with default directives.
- The runs were made 2026-11-05 on the same machine, which two other agents were using; the load was not recorded.
- They give the step times but not the process start-up or the time to read the sources.

| design | Vivado synth | opt | place | route | write_bitstream | sum of steps | open flow "after", total (median) |
|---|---|---|---|---|---|---|---|
| blinky (qor_blinky = designs/blinky with the module renamed; C:\...\build\qor\blinky_p10) | 32.96 | 14.05 | 5.08 | 24.28 | 9.90 | 86.3 | 10.5 |
| qor_rv_soc (the rv_soc variant of docs/qor-vivado.md; not the same RTL as designs/rv_soc; C:\...\build\qor\rv_soc_p10) | 43.12 | 13.57 | 6.89 | 20.51 | 11.43 | 95.5 | 79.2 (designs/rv_soc); 35.6 with exit-bb |
| LiteX arty_ddr3 (same digilent_arty.v; C:\...\build\ddr3\arty_ddr3) | 134.27 | 18.36 | 28.61 | 36.91 | 17.65 | 235.8 | 175.9 |

Reading the table:
- On small designs the open flow finishes first, because Vivado has a large fixed cost per step: 33 s synth,
  14 s opt, 19-24 s route and 9 s bitstream even for blinky.
- On the LiteX SoC the open flow is about 25 % faster in total (175.9 s against a 235.8 s sum of steps). By stage:
  - Vivado synthesis takes 134 s against yosys's 44 s;
  - but Vivado placement takes 29 s against nextpnr's 70 s;
  - and the bitstream takes 18 s in Vivado against 13.5 s in the open flow.
- On the 100T design the stock open flow does not finish (above). With the static placer it takes 397 s; Vivado has
  not been run on it yet.

## Where the time goes, and what was done

1. **nextpnr builds its delay matrix in every run, which costs 3.9-6.1 s.**
   - The table is a Dijkstra search from three fixed sources (`himbaechel/uarch/xilinx/delay_matrix.cc`). It reads
     only the device: pips, pip delays and bel pins.
   - No pip is bound before the table is built:
     - In all 39 nextpnr trees under build/src (2026-11-06), the only pre-placement steps are apply_holdbufs,
       apply_preplaced and close_routed_tiles, and none of them binds a pip.
     - So the pip delays have no design-dependent drive or load terms.
   - nextpnr can already save the table and load it again with `-o delay-matrix=FILE`. Loading recomputes the edge
     rates exactly.
   - **Done: `flow/dm_cache.py`, used by `flow/build_openxc7.py`.**
     - Cache key:
       - the binary and the chipdb (path, size, mtime);
       - the part;
       - every nextpnr argument except per-run files, seed, frequency, `--threads`, `--parallel-refine` and
         `--timing-allow-fail`.
     - nextpnr only reads and writes a private copy in the build directory. The shared copy in
       `build/cache/delay_matrix/` is replaced atomically.
     - The cache is not used:
       - when the user passes their own delay-matrix option;
       - for a binary whose default chipdb is unknown;
       - with `OFX_DM_CACHE=0`.
   - **Proof: .frames are byte-identical with and without the cache.**
     - blinky: 4 runs.
     - rv_soc: 3 runs.
     - LiteX ddr3: 2 runs.
     - rv_pr: `ofx dfx build` in two fresh copies, cache off and on (`build/rt_rv_pr_{off,on}`,
       `build/runtime/rt_pr.log`).
       - All 3 configurations and both partial bitstreams are identical between the two builds.
       - They are also identical to `examples/rv_pr/build/dfx/router`.
   - **Effect:**
     - blinky: nextpnr CPU 6.6 s -> 3.4 s (median), placement 3.9 s -> 0.5 s.
     - LiteX ddr3: placement 100.0 s -> 69.6 s, but the load was lower too, so part of that drop is the load.
2. **On rv_soc the router spends most of its time on 24 ICAP nets.**
   - With the stock flow, routing takes 50.8-88.0 s.
   - Every `icap_o[*]` net takes 1.7-5.9 s (the "slowest nets" table in nextpnr.log).
   - `--debug-router` on icap_o[24] (build/runtime/prof/icapdbg/out.txt):
     - its routing box is (12,117)-(48,126);
     - the bounded search fails after 2.06 s;
     - the retry without a box takes 0.04 s;
     - the final route enters the interconnect at X48Y131, outside the box.
   - **Draft: `docs/drafts/nextpnr-exit-bb.patch`.**
     - The option is `-o exit-bb` and is opt-in (docs/drafts/nextpnr-exit-bb.md). The build is
       `build/nextpnr-build/rtbb`.
     - It anchors a non-logic pin at the first general wire that is in an INT_L/INT_R tile.
     - Without the option, the binary gives rv_soc frames identical to stock.
   - **With exit-bb on rv_soc (5 runs, identical frames among them):**
     - routing: 9.9 s (8.1-10.7);
     - total: 35.6 s, against 80.9 s before;
     - nextpnr Fmax: 163.35 MHz, against 159.92 MHz (same seed).
   - **On LiteX ddr3 (no ICAP):** routing does not change beyond the noise; sys_clk is 111.74 MHz against 111.04 MHz.
   - Routes change, so it is a QoR trade-off and not the default.
   - Next steps for the lead: the QoR seeds, rv_pr, and inclusion in the ofx nextpnr series.
3. **Placement dominates LiteX ddr3 and mc12_a100.**
   - On LiteX ddr3 (stock), HeAP takes 42 s and annealing 64 s.
   - The existing `--parallel-refine --threads 4` turns the 64 s of annealing into 27.7 s.
   - But sys_clk drops from 111.04 to 102.67 MHz (nextpnr timer, one seed), so it stays off.
   - mc12_a100: see above. HeAP's legaliser takes most of the 921 s (the 19 iterations take 50-164 s each).
   - The static placer (an existing option) both finishes and is fast there.
   - `ofx/defaults.py` (the ofx 0.1 defaults) picks heap above 3000 cells. That threshold should be rechecked on
     large designs. That is for the placer workstream and the lead; nothing was changed here.
4. **yosys has a fixed cost.**
   - Timestamped log for rv_soc (build/runtime/prof/ys_rv_soc), 20.7 s in total:
     - techmap: 5.7 s;
     - abc9: 3.95 s (a single yosys-abc process);
     - reading cells_sim/cells_xtra: 2.8 s;
     - picorv32: 0.6 s.
   - LiteX ddr3: techmap 17 s, abc9 6 s.
   - mc12_a100: yosys alone takes 89-106 s.
   - Nothing was changed here. The options are:
     - pre-parsed cell libraries (needs a change to yosys);
     - abc9 per partition (changes the netlist).
5. **fasm2frames is Python and does work per FASM feature.**
   - Times: 1.0-1.6 s on blinky, 2.6-4.6 s on rv_soc, 12.7-14.2 s on LiteX ddr3 (207k lines), 28 s on mc12.
   - One part of that is redundant work. `FasmAssembler.enable_feature` adds all frames of a tile to
     `frames_in_use` again for every feature: 2.3 M set inserts on rv_soc, into a set that only grows.
   - **Done: `flow/fasm2frames_fast.py`.**
     - It runs the toolchain's own fasm2frames, with that loop deduplicated per (tile, block type).
     - `flow/build_openxc7.py` uses it. `OFX_FAST_F2F=0` turns it off.
   - **Proof:** `flow/fasm2frames_check.sh` compares frames, stderr and exit code on 41 .fasm files:
     - 39 are identical;
     - 2 are invalid FASM from another agent's experiment, and both versions fail on them;
     - blinky end-to-end is also identical.
   - **Effect, minimum over alternating runs:**
     - rv_soc: 3.74 -> 3.43 s CPU (5 runs);
     - LiteX ddr3: 15.26 -> 13.06 s CPU (3 runs).
   - A C++ fasm2frames would be the real fix. It was not done.
6. **Small items:**
   - chipdb, netlist and XDC loading: 0.4-2.2 s. The chipdb is already memory-mapped.
   - Python/ofx overhead: 0.1-0.6 s.
   - xc7frames2bit: 0.1-0.2 s.
7. **Shared-machine finding (`ofx/npwait.sh`).**
   - `pgrep -c nextpnr` does not count the toolchain's `nextpnr-xilinx`.
   - Its wrapper execs `ld-linux-x86-64.so.2 ... libexec/nextpnr-xilinx`, so the process name is `ld-linux-x86-64`.
   - So stock-flow nextpnr runs are invisible to the limit (checked 2026-11-06 with the mc12 run).
   - `pgrep -fc nextpnr` would count them. The file belongs to the lead and was not changed here.

## Not done / next

- **Vivado:** run `vivado/run_runtime.sh 1 blinky rv_soc litex_ddr3 mc12_a100` once the lock is free, then
  regenerate this file's tables with `flow/runtime_table.py`.
- **exit-bb:** QoR seeds, rv_pr, and the ofx series.
- **Placement:** the heap placer on large designs (mc12) and the static-placer threshold.
- **Bitstream:** a C++ fasm2frames, or a resident database process.
- **Incremental reuse:** belongs to the incremental-compile agent (`ofx build --incremental`).
- **Noise:** repeat on a quiet machine.

## Reproduce

```
python3 flow/runtime_prof.py blinky rv_soc litex_ddr3 mc12_a100 --variant base --run   # OFX_DM_CACHE=0
python3 flow/runtime_prof.py blinky rv_soc litex_ddr3 --variant dmc --run
python3 flow/runtime_prof.py rv_soc litex_ddr3 --variant exitbb --run   # needs build/nextpnr-build/rtbb
python3 flow/runtime_prof.py mc12_a100 --variant static --run
vivado/run_runtime.sh 1 blinky rv_soc litex_ddr3 mc12_a100
python3 flow/runtime_table.py
```
