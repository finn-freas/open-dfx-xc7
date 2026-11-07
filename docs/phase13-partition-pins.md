# Phase 13: partition pins instead of anchor cells (native flow, opt-in)

Offline work, 2026-11-05. Nothing here has run on hardware. Every number comes from a run; the log or output path is
given next to it. Matrix item 6 in `docs/dfx-vs-vivado.md`.

## 1. Goal

The native flow (phase 8) fixes the partition boundary with a generated RM shell: per input bit a BEL-pinned LUT1, per
output bit a BEL-pinned LUT1 + FDRE, at the same BELs in every module. That costs 108 LUTs and 33 FFs of the region
and puts a register on every module output. Vivado instead fixes a routing node per crossing net, the partition pin:
the static route ends (or starts) there, and the module's route continues from it, with no cell.

This phase adds that as an alternative: design `rv_pp` in `flow/build_pr_native.py`, nextpnr variant `partpin`.
The anchor flow and its designs are unchanged (section 7).

## 2. Mechanism

Read in the `rtkeep` stack (`build/src/nextpnr-rtkeep`), details in `docs/drafts/nextpnr-partition-pins.md`:

- `-o prerouted` binds the reference route `STRENGTH_LOCKED` and then **prunes everything that does not lead to a sink
  of this design**, so a route that stops at a boundary node would be removed entirely.
- router2 routes a partly routed net from its source; the forward search may walk the locked tree and **branch off it
  anywhere**. With region containment an arc that crosses the region edge is not held, and with keep-out it may still
  use static pips outside the region. So the existing replay alone does not give "static ends at the pin, module
  starts there".
- nextpnr's own `RegionPlug` pseudo cell splits a net at a wire; it fits separate static/module builds, not this
  combined build (both halves would bind the same wire).

The draft patch stack (all on `router-region` + `pblock-replay` + `pblock-routethru`):

| patch | what | why it was needed (found by run) |
|---|---|---|
| `nextpnr-partition-pins.patch` (5 files, +352/-41) | `Region::partition_pins`; router2 searches an arc into a region from its pin and an arc out of it to its pin, held to the region, then adds the locked far side; router1's stub check accepts a route that ends at a pin; xilinx `-o partition-pins=<file>`, kept by the prerouted pruning; a clock sink the reference does not reach keeps route_clocks' dedicated route | the mechanism; the clock part: without it the global clock arc to the module's moved FF went through a LUT route-through in static CLB `CLBLL_L_X12Y147`, changing 6 static frames (`build/patched/rv_pp_native/attempt2_fabric_clock_leaf/checks/pr_check_xor_n_rot_n.json`) |
| `nextpnr-pblock-lutff.patch` (3 files, +31) | `pack_lutffs` does not pair a FF with a LUT/CARRY4 of another pblock | with combinational module outputs, 32 static `pcpi_rd` FFs were packed with module LUTs and pulled into the pblock |
| `nextpnr-carry-replay-order.patch` (1 file, +17/-2) | S-source copies numbered per source; with pblocks, carry chains packed in name order | `add_n` failed: `attempting to reserve sink input path wire 'X42Y8/SLICE_X0Y0.D6LUT_O6' for nets '…3335.A[0]' and '…3335.A[0]$S_DUP1'` – the module's carry chains changed how the static carries were packed |

Build: `DRY_RUN=0 VARIANT=partpin BASE_REV=router-region PATCHES="nextpnr-pblock-replay.patch nextpnr-pblock-routethru.patch nextpnr-partition-pins.patch nextpnr-pblock-lutff.patch nextpnr-carry-replay-order.patch" bash toolchain/buildenv/build_nextpnr_variant.sh`.
Applying the five patches to `router-region` reproduces the worktree exactly (scratch-index `git diff` empty).

**No-op:** rv_soc without pblock (`build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.json`), `partpin` vs `rtkeep`:
`.frames` identical (`cmp`); FASM identical except 8 comment lines naming `…$S_DUP<n>` nets
(`build/patched/rv_pp_native/noop/rv_soc_partpin` vs `build/patched/rv2_native/noop/rv_soc_rtkeep`).

## 3. Choosing the pins (`flow/partpins.py`, new)

From a reference build's routed JSON and its `replay_dump.py` output, per boundary net (driver static and a sink in
the module, or the reverse; constants and global clocks excluded):

- the route tree is rebuilt with prjxray `tileconn.json` node unions (a pip names its source by a tile-local alias);
- **input net:** the static part is what is reachable from the source through pips outside the region; the pin is the
  wire on it whose next pip is inside (if there are several, the one with most sinks below; the rest is dropped). The
  locked route kept = the path to the pin + the branches to static sinks.
- **output net:** the pin is the wire driven by a region pip below which the route never re-enters the region; the
  locked route kept = the subtree below the pin. More than one such wire, or a static sink not below it, is refused.
- Writes `<prefix>.prerouted` (boundary lines cut), `<prefix>.partpins` (for nextpnr) and `<prefix>.json` (net, port,
  bit, pin wire, and an alias of the pin in a region tile for region2v).

**Which reference.** First attempt: a reference module with no anchors (`rm_core_ppref.v`, rd = rs1 ^ rs2 ^ funct, so
that every input has a sink; since removed). Its 33 cells were placed in the region corner nearest the static logic,
and the 108 pins landed in 6 INT tiles, 54 of them in `INT_L_X10Y100`
(`build/patched/rv_pp_native/attempt1_ppref_unpinned/static_pp.json`). The first module build on those pins did not
converge: 12 overused wires at router iteration 1346 when it was stopped
(`attempt1_ppref_unpinned/ppref_n/nextpnr.log`).

Used now: the reference build `xor_a` uses the **anchor shell** (as in phase 8), so its static routes end at anchors
spread around the region's middle rows. The anchors only serve to place the pins (in Vivado terms they play the role of
pin location constraints); **no module build has anchors**. Result: 75 input and 33 output pins in 39 INT tiles, at most
11 in one (`INT_R_X11Y126`); 0 input nets entered the region more than once
(`build/patched/rv_pp_native/partpin/static_pp.{json,log}`).

Ports a module does not use (e.g. `funct[1..9]` for xor) keep their static route up to the pin, as unused partition
pins do; nextpnr reports them (`Partition pins: 98 given to their pblocks, 10 on nets that no longer enter or leave a
pblock`, `xor_n/nextpnr.log`).

## 4. Shell and design

- `flow/gen_shell2.py --partpins [--register NAME]`: `rm_slot` = `rm_core` wired straight to the ports, no anchors, no
  blockers. Outputs are combinational unless named in `--register`, which adds an **unplaced** FDRE `r_<port>_<bit>`
  (module logic, placed freely inside the pblock).
- `rv_pp` registers only `ready` (1 FF): the unchanged static bridge samples `slot_rd` when `!slot_valid && slot_ready`,
  i.e. one cycle after `valid`; with `ready = valid` combinational that never happens. `rd` is combinational: the path
  is static `slot_rs1/rs2` FF → partition pin → module logic → partition pin → static `pcpi_rd` FF.
- `flow/build_pr_native.py --design rv_pp` (same static RTL as rv_pr, region `SLICE_X12Y100:SLICE_X15Y149`, RMs
  xor/andn/add/rot, variant `partpin`): synth static; anchor shell (reference only) and partition-pin shell
  `rm_shell_pp.v`; `xor_ref` (xor in the anchor shell) and every RM in the pp shell; `xor_a` reference build;
  `replay_dump.py`; `partpins.py` → `static_pp.*`; module builds `<rm>_n` with `-o preplaced=static.preplaced -o
  prerouted=static_pp.prerouted -o partition-pins=static_pp.partpins`; region_pips and pr_check as before.
  Run: `python3 flow/build_pr_native.py --design rv_pp --run` (`build/patched/rv_pp_native/build_partpin.out`); a
  cached rerun skips all 35 steps (`cached_rerun_rv_pp.out`).

## 5. Results (`build/patched/rv_pp_native/partpin/`)

### 5.1 Routing and static
| check | result |
|---|---|
| nextpnr, every module build | `Partition pins: 108 net(s); … 0 arc(s) without the locked route outside`; clock: `1 sink(s) the reference does not reach keep their dedicated clock route` (`*_n/nextpnr.log`) |
| pr_check, 6 module pairs | `STATIC IDENTICAL OUTSIDE REGION` 6/6; 52 frames differ (xor/andn/add pairs) or 72 (pairs with rot), all inside, 0 foreign words (`checks/pr_check_*.json`) |
| region_pips, 5 builds | 0 static pips in region tiles in all 5; module-only nets: 0 pips outside the region (add_n, rot_n, xor_a; xor_n and andn_n have no module-only routed nets) (`checks/pips_*.json`) |
| partition-pin nets, 4 module builds | for 108/108 nets the pips outside the region equal the locked route, and the pin wire is on the route (`flow/partpin_check.py`, new; `checks/partpin_check.log`) |
| no-op check | section 2 |

### 5.2 Partials, byteman, region2v (`flow/native_check.sh`)

Run with the new opt-in variables: `NAT=build/patched/rv_pp_native/partpin OUT=build/patched/rv_pp_native/partials
BMO=build/patched/rv_pp_native/byteman SHELLV=$NAT/rm_shell_pp.v STATIC_PIPS=$NAT/static_pp.prerouted
PARTPINS=$NAT/static_pp.json TAGP=rvpp FORMAL_MEM_KB=3000000 bash flow/native_check.sh`
→ `build/patched/rv_pp_native/native_check.log`: **20 PASS, 0 FAIL, exit 0** (partial.py not modified).

- 12 partials (every target × base): 59,272 bytes `.bin` (59,406 `.bit`), 72 region frames, 1 run × 2 passes; the 1
  frame outside is the run-end pad with the full bitstream's own content; `crc: OK; base + partial == target: True (0
  frames differ)`; pass-1 dropped pips 451 for add targets (`partials/*.check.json`, `*.log`).
- byteman (base + partial) vs the original target: 0 frames differ, 12/12.
- region2v on the 4 full bitstreams and the 12 byteman results: 16/16 sim 3582/3582 and PROVED (yosys SAT,
  `ulimit -v 3000000`, 600 s).
- **region2v partition-pin mode** (`region2v.py check … --partpins static_pp.json`): ports are the nodes of the pins
  (found through the pin's alias in a region tile), clocks are traced from the region's FFs, outputs not registered by
  the shell are compared combinationally in the proof. Without `--partpins` the anchor path is unchanged (rv_pr
  `xor_n` re-check: PASS 3582/3582, no new keys in `region.json`).
- Negative controls: xor_n checked as andn → `FAIL … pass=223 fail=3359` (`build/patched/rv_pp_native/neg_xor_as_andn.log`);
  add_n with one LUT INIT bit flipped (`--corrupt`) → `FAIL … pass=2815 fail=767` (`neg_add_corrupt.log`).

### 5.3 Region use (module cells, from the routed JSON)

| RM | anchor flow (`build/patched/rv_pr_native/router/<rm>_n`) LUT / FF / CARRY4 | partition pins (`rv_pp_native/partpin/<rm>_n`) LUT / FF / CARRY4 |
|---|---|---|
| xor | 140 / 33 / 0 | 32 / 1 / 0 |
| andn | 140 / 33 / 0 | 32 / 1 / 0 |
| add | 172 / 33 / 8 | 32 / 1 / 8 |
| rot | 258 / 33 / 2 | 150 / 1 / 2 |

108 LUTs and 32 FFs fewer per module; the remaining FF is the `ready` register of section 4.

### 5.4 Timing (one seed each)

| build | router2 | Fmax |
|---|---|---|
| `xor_a` (reference, anchor shell) | 76.86 s | 145.62 MHz |
| `xor_n`, `andn_n`, `add_n`, `rot_n` | 2.54–3.09 s | 145.62 MHz |
| anchor flow `rv_pr_native/router/*_n` (for comparison) | 1.99–2.97 s | 141.16 MHz |

The critical path is the same static FF pair (`$auto$ff.cc:337:slice$10925` → `…$11247`) in all five rv_pp builds and does not pass through `u_rm`
(`report.json` `critical_paths`). So every path through the combinational `rd` (static FF → module → static FF),
including the 32-bit adder and the barrel rotate, has at least that path's slack: the bridge closes at 100 MHz with
45.62 MHz margin. nextpnr reports only the worst path, so the module path's own delay was not measured. The 141.16
vs 145.62 MHz difference comes from two different reference placements of the static logic and is not attributable to
partition pins (one seed).

The module builds were rebuilt with the final binary (after a cast-only source edit): frames identical for all 4 and
for `xor_a` (`build/patched/rv_pp_native/rebuild_check/`).

## 6. Files

| file | |
|---|---|
| `docs/drafts/nextpnr-partition-pins.{md,patch}`, `nextpnr-pblock-lutff.{md,patch}`, `nextpnr-carry-replay-order.{md,patch}` | new drafts, variant `partpin` |
| `flow/partpins.py` | new: pins from a reference build, cut prerouted file, pin list |
| `flow/partpin_check.py` | new: locked route == outside route, pin on route, module cell counts |
| `flow/gen_shell2.py` | `--partpins`, `--register` |
| `flow/build_pr_native.py` | design `rv_pp`, variant `partpin`, `partpins`/`pp_register` keys |
| `flow/region2v.py` | `check --partpins` |
| `flow/native_check.sh` | opt-in `STATIC_PIPS`, `PARTPINS` |

## 7. Existing designs unchanged

- Dry runs of rv_pr, rv_pr with all 6 RMs and `--timing-allow-fail popc minmax`, rv_b, rv_c, rv_c
  `--no-shared-frame-pblock`, rv_m and rv2: output identical to the committed `build_pr_native.py` (`cmp`), every step
  `[skip]` (`build/patched/rv_pp_native/dry/{before,after}_*.txt`).
- region2v default path re-run on rv_pr `xor_n`: PASS (section 5.2). native_check.sh without the new variables runs
  the same commands as before.
- No existing variant or `build/patched/*_native` output was rebuilt.

## 8. Open problems

- **Pin placement.** The pins come from a reference build that still uses the anchor shell to spread them. Without it
  they clustered and the first module did not route (section 3). Vivado places partition pins itself (and takes
  location constraints, `HD.PARTPIN_LOCS`/`HD.PARTPIN_RANGE` as I remember them, **not checked against UG909**); here
  there is no placer for pins.
- One pin per net; a net that leaves the region at two wires in the reference is refused. A module that drives an
  output with a constant, or passes an input straight to an output, has no boundary net for that port (not exercised).
- `ready` stays registered (1 FF) because the static bridge needs it a cycle after `valid`; this is a property of the
  bridge, not of the pins.
- The clock leaf of a moved module FF is route_clocks' choice and is locked. Here the clock net's pips differ between
  builds by 8 (xor_n vs andn_n, xor_n vs add_n) or 0 (xor_n vs rot_n), all in region tiles (6 `CLBLM_R`, 2 `INT_R`),
  none in an HCLK tile. A module FF in the other half of the clock region could need an HCLK leaf pip; that case did not
  occur and was not tested (Vivado holds the region columns' HCLK leaf pips back in pass 1, phase 10).
- `nextpnr-carry-replay-order.patch` changes the packing order only when the XDC has pblocks; other packer decisions
  that depend on the netlist's cell order were not audited.
- Not compared with a Vivado DFX build that uses partition pins; nothing on hardware.
