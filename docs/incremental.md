# Incremental implementation (`ofx build --incremental`)

Date: 2026-11-06. No hardware was used. Every timing number names its timer.

## What it does

`ofx build --incremental <ref>` reuses the placement and routing of a reference build for everything a small RTL
change left alone, like Vivado's `read_checkpoint -incremental`:

1. yosys synthesizes the changed design as usual (`<impl>/synth/<top>.json`).
2. `flow/incremental.py` matches its cells and nets to the reference's netlist and writes
   `<impl>/incremental/{<top>.json, inc.preplaced, inc.prerouted, inc.xdc, match.json}`.
3. nextpnr-xilinx places and routes that netlist with `-o preplaced` / `-o prerouted` (already in openXC7's
   nextpnr, used by the DFX flow). The pinned cells keep their bels, the replayed nets keep their routes (locked),
   and only the rest is placed and routed. No nextpnr change is needed.

`<ref>` is a finished build directory (`<top>.json` and `<top>_routed.json`). If it is the project's own
`build/impl`, it is copied to `build/incremental_ref` first, since the build replaces it.

### Matching by name, when yosys renumbers its names
Vivado matches cells by hierarchical name. yosys keeps the HDL names of registers and ports, but numbers its
internal cells and nets (`$abc$72663$lut$aiger$o1800`), and one small edit renumbers most of them (on the rv_soc
edit below only 633 of 2010 cells kept their name). So `flow/incremental.py` gives every cell a structural label:
its type, parameters, the HDL names of the nets it reads and drives, and, through unnamed nets, the labels of the
cells feeding it, 8 levels deep. A LUT's label is taken with its inputs sorted (and its INIT permuted to match),
since abc permutes LUT pins from one run to the next. Cells whose label is unique in both netlists are matched, and
the new netlist is rewritten so that matched cells and nets carry the reference's names; the cells nextpnr's packer
makes (named after the cells they come from) then get the reference's names too.

### What is replayed
- A cell is pinned only if it is matched, and a packer cell only if every net it touches is driven by a pinned cell.
- A slice is replayed whole or not at all: if any of its reference cells changed, all of them are placed again. (A
  first version pinned cells one by one; nextpnr then rejected a LUTRAM slice whose neighbour had changed.) A carry
  chain is replayed whole or placed again whole.
- `--whole-tiles` (the `ofx build --incremental` default) does the same per tile: nextpnr closes the tile of a
  pinned cell to new cells, so a slice freed beside a pinned one would otherwise stay empty and the new logic would
  land wherever the frozen reference left room.
- `--ripple N` also places again the slices within N nets (fanout <= 16) of a changed cell.
- With `-o prerouted` a net's reference route is replayed when its driver is pinned; nextpnr prunes the branches to
  sinks that moved and routes those. The routes are locked; `docs/drafts/nextpnr-incremental-weak-routes.patch`
  (opt-in, `-o prerouted-strength=weak`, on the install series) gives them to the router as a starting routing it
  may rip up instead. `ofx build --incremental` replays placement only, unless `--incremental-routes`.

## rv_soc, one small edit

Edit (`designs/incr/rv_soc_edit/rv_soc.v`): the I/O register at address 6 also returns `rxf_wp`
(`io_q <= {3'd0, rxf_wp, rx_overruns, slot_timeouts}` instead of `{8'd0, ...}`). Reference: the original rv_soc,
built with the same flow (`build/incr/rv_soc/ref`, nextpnr 159.92 MHz).

### Matching
`flow/incremental.py` (3.0 s wall, `build/incr/bench_rv_soc/match.time`): the reference netlist has 2001 cells, the
changed one 2010. 1738 are matched (713 under the same name); 263 reference cells changed or are gone. Most of these
are not near the edit: abc maps unchanged CPU cones differently after a change elsewhere (for example the clock
enable LUT of `mem_wdata` becomes LUT2 INIT 1000 instead of 0100, its input inverted), so they are new logic to the
matcher. Without the LUT pin canonicalisation it matched 1527.

The reference placement has 2678 placed cells (packer cells included) and 3209 routed nets. Replayed:

| Mode | Cells pinned (netlist + packer) | Slices placed again | Nets replayed |
|---|---|---|---|
| per slice (`s0`) | 1197 + 579 = 1776 | 135 | 2205 |
| whole tiles (`w0`, the ofx default) | 460 + 158 = 618 | 266 (139 tiles) | 825 |

### Runtime and QoR (nextpnr's timer)
nextpnr-xilinx of the toolchain (openXC7, stock), seed 1, `--freq 100`, same options in every run; only the replay
options differ. Fmax is nextpnr's final "Max frequency" (nextpnr's timer). CPU is /usr/bin/time's user time of the
nextpnr process; the wall time includes the wait for a nextpnr slot on a shared machine, so CPU is the number to
compare. Load is the 1-minute load average when the run started (16 threads, other agents' jobs running).
Runs: `flow/incremental_variants.sh` (`build/incr/var_rv_soc/variants.log`) and `flow/incremental_bench.sh`
(`build/incr/bench_rv_soc/bench.log`).

| Run | Replay | CPU s (r1 / r2 / r3) | Router2 s | Fmax MHz (nextpnr) |
|---|---|---|---|---|
| reference (original RTL) | - | not timed alone | 70.5 | 159.92 |
| full rebuild of the change | - | 122.0 (load 12.7) / 99.3 (4.0) / 99.2 (5.3) | 108 / 88 / 88 | 169.09 |
| `w0p`: whole tiles, placement only (**ofx default**) | 618 cells | 69.2 / 52.3 (3.5) / 64.0 (5.5) | 57 / 46 / 58 | **161.71** |
| `s0p`: per slice, placement only | 1776 cells | 46.6 / 47.5 (4.4) / 45.0 (6.1) | 38 / 38 / 37 | 135.03 |
| `s0`: per slice, placement and routes (locked) | 1776 cells, 2205 nets | 66.2 / 46.0 (4.7) / 46.3 (5.7) | 56 / 39 / 38 | 123.43 |
| `w0`: whole tiles, placement and routes (locked) | 618 cells, 825 nets | 40.4 | 27 | 111.48, then ERROR: hold violations |

nextpnr is deterministic here: every repeat gave the same Fmax to the 0.01 MHz.

- **Whole-tile placement replay** (the default): 47 % / 35 % less nextpnr CPU than the full rebuild in the repeats
  run back to back (r2, r3), at 161.71 MHz against 169.09 (-4.4 %, nextpnr's timer); the reference itself was
  159.92 MHz, so the result is within the spread nextpnr shows between two netlists of this design.
- **Per-slice replay** pins three times as many cells and is faster still, but the new logic has to go where the
  frozen tiles leave room: 135.03 MHz (-20 %).
- **Locked routes** cost more: 123.43 MHz, and with whole tiles the run fails hold (nextpnr's router cannot move a
  locked route). `docs/drafts/nextpnr-incremental-weak-routes.patch` replays them weak instead (results below).
- Most of the time saved is in router2, not in the placer (HeAP + SA take 3-7 s in every run).

### `ofx build --incremental` end to end
`designs/incr/proj_edit` (the changed RTL as an ofx project), reference `build/incr/rv_soc/ref`:
`ofx build --incremental ../../../build/incr/rv_soc/ref --run` writes a bitstream (2192175 bytes) at 148.24 MHz
(nextpnr's timer), 960 cells pinned; `ofx build --run` of the same project, from scratch: 160.59 MHz. nextpnr took
152.6 s and 134.4 s wall, router2 68.0 s and 66.1 s: **no runtime gain and -7.7 % Fmax** on this netlist. The ofx
flow synthesizes from the staged copies of the sources, and yosys gives a different netlist for the same RTL from
other file paths (2001 cells against 2010; 1822 of 2001 matched), so this is a second, independent sample of the
same edit. Logs: `build/incr/ofx_e2e.log`, `build/incr/ofx_e2e_full.log`, `build/incr/ofx_e2e_inc/`.

### Verdict so far
The replay is exact (every pinned cell and replayed route lands where it was, "0 not in this design, 0 collided"),
and a bitstream comes out. It does not yet give Vivado's runtime savings at equal QoR: on one sample the whole-tile
replay saves 35-47 % of nextpnr's CPU at -4.4 % Fmax, on the other it saves nothing at -7.7 %. The limits found:
1. yosys/abc re-maps unchanged logic after a small edit, so 10-15 % of the cells are new to the matcher, spread over
   the whole design;
2. nextpnr closes a pinned cell's tile to new cells, so either many cells are pinned and the new ones land badly
   (per slice), or few are pinned (whole tiles);
3. locked routes cannot be ripped up, which costs Fmax and can fail hold.

RESULTS_MORE
