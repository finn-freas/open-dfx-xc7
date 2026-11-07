# Phase 11: two reconfigurable partitions in one design (native flow)

Offline work, 2026-11-05. Nothing has run on hardware. Every number below comes from a run; the log or output path is
given next to it. Matrix item 14 in `docs/dfx-vs-vivado.md`.

Tools: patched nextpnr variant `rtkeep` (`e62fafd1-rtkeep` = `router-region` + `nextpnr-pblock-replay.patch` +
the new `docs/drafts/nextpnr-pblock-routethru.patch`), and for comparison the existing `replay` variant (`e62fafd1-replay`).

## 1. Design `designs/rv_soc2`

A copy of `designs/rv_soc` (rv_soc is not modified). Top module is still `rv_soc`, so `partial.py --design rv_soc` and
`bit2netlist.sh ... rv_soc` work unchanged; the XDC is a byte copy.

- `rm_bridge2` replaces `rm_bridge`: one PCPI bridge that decodes custom-0 (`0001011`) for slot `u_rm` (module
  `rm_slot`) and custom-1 (`0101011`) for slot `u_rm2` (module `rm_slot2`, same ports). Each slot has its own
  `valid/funct/rs1/rs2` registers, so each slot's partition inputs are driven by static FFs of its own. A `sel` FF picks
  which slot's `rd/ready` is returned. Timeout and the timeout counter (IO 6) are as before, shared.
- `designs/rv_soc2/pr/rm_stub.v`: blackboxes `rm_slot` and `rm_slot2`.
- Firmware `designs/rv_soc2/fw/main.s`: new command `'D' a b` → `custom1 s6, s4, s5, 0, 0`, reply and LEDs as `'C'`.
  `flow/rvasm.py` gained the `custom1` mnemonic (opcode `0101011`); `designs/rv_soc/fw/main.s` still assembles to a
  byte-identical `main.hex` (`cmp`). ICAP (`'W'`) and UART are unchanged.
- RMs are the existing `designs/rv_soc/pr/rm_core_{xor,andn,add,grey}.v`. RP2 modules are synthesised with top
  `rm_slot` and then renamed to `rm_slot2` (`rename rm_slot rm_slot2`).

**RTL simulation** (`designs/rv_soc2/run_sim.sh`; logs `build/rv_soc2/tb_rv_soc2_<rp1>_<rp2>.log`): all 4 combinations
RP1 ∈ {xor, andn} × RP2 ∈ {add, grey} PASS. Each run sends 3 `C` and 4 `D` commands, checks reply and LEDs against a
model, checks that `C` strobes only slot 1 and `D` only slot 2, then a `W` of 8 ICAP words (captured words = bit-swapped
sent words), no trap, 0 timeouts. The slot models (`designs/rv_soc2/tb/slot_models.v`) wrap the real `rm_core_*.v`
with the registered outputs of the shell.

## 2. Regions

| RP | instance | region | tiles | frames | `region.py --drc` |
|---|---|---|---|---|---|
| rp1 | `u_rm` | `SLICE_X12Y100:SLICE_X15Y149` | 200 | 72 (CLB_IO_CLK T r1 c10, minors 0..35 ×2 columns) | 0 INT pairs split |
| rp2 | `u_rm2` | `SLICE_X12Y0:SLICE_X15Y49` | 200 | 72 (CLB_IO_CLK B r0 c10…) | 0 INT pairs split |

`region.region_bits`: 0 common frames, 0 common tiles. Both regions span a whole clock-region height, so neither
shares frames with the other. `build_pr_native.py` refuses partitions that share a tile or a frame
(`check_partitions`).

## 3. Router: no change needed for two regions; one new draft patch for route-throughs

See `docs/drafts/nextpnr-pblock-routethru.md` for details.

- **Multiple regions:** router2 on `router-region` already indexes every routing region, refuses overlapping ones,
  holds RM arcs to their own region and, with `--router2-region-keep-out`, keeps every other arc out of every region
  except its driver's and sink's. Measured: nextpnr prints `Routing regions: 2 region(s); …`, and `flow/region_pips.py`
  (run once per region, the other RP counted as static) gives **0 static pips in each region and 0 RM pips outside its
  own region in all 7 builds** (`build/patched/rv2_native/{replay,rtkeep}/checks/pips_*_rp{1,2}.json`).
  Placement: every cell in rp1's sites is a `u_rm.` cell and vice versa, same for rp2, in all 7 replay-variant
  builds (`build/patched/rv2_native/placement_check.log`).
- **Found by run, fixed by a draft patch:** with the `replay` binary, two RP2 boundary nets (output anchor → static)
  used **LUT route-throughs inside RP2** (`slot2_rd[10]` via `X33Y127 CLBLM_L_C1→C`, `slot2_rd[19]` via
  `X33Y128 CLBLM_L_D5→D`; `build/patched/rv2_native/routethru_scan/rv2_replay.log`). That route is replayed as static
  and occupies a LUT of the module area; region2v rejected these netlists. The earlier single-RP builds have 0 such cases
  (`routethru_scan/{rv_pr,rv_b,rv_c,rv_m}.log`). The patch makes `checkPipAvailForNet` refuse a LUT route-through in a
  routing-contained pblock unless the whole net is inside that pblock. No-op without pblocks: rv_soc frames
  byte-identical to the `replay` binary and to the stock build (`build/patched/rv2_native/noop/`). With it: 0 such
  route-throughs in all 7 rv2 builds (`build/patched/rv2_native/rtkeep/checks/routethru.log`).

## 4. Flow: `flow/build_pr_native.py --design rv2`

New design entry `rv2` with `partitions` (name, instance, module, region, RM list) and `configs`. Single-RP designs take
the old code path unchanged (section 6). Steps, all cached; `DRY_RUN` default as before:

1. synth static; per RP a shell from `gen_shell2.py ports.json --region <RP> --no-keepout` (blockers stripped), and
   each RM synthesised into it.
2. one pblock per RP: `create_pblock pblock_rpN`, `add_cells_to_pblock … [get_cells u_rm|u_rm2]`, `resize_pblock`,
   `EXCLUDE_PLACEMENT true`, `CONTAIN_ROUTING true`; `--router2-region-keep-out`.
3. `xor_add_a`: first build, everything free (the reference configuration).
4. `static.*`: `replay_dump.py` with both instances excluded and both sets of partition ports kept (used by
   `partial.py --static-pips`).
5. **Module builds, one RP changing at a time, static and the other RP locked:**
   - `rp1_andn_m` = config (andn, add): static from `xor_add_a` + **RP2 locked** from `xor_add_a`; RP1 placed and
     routed fresh.
   - `rp2_grey_m` = config (xor, grey): static + **RP1 locked** from `xor_add_a`; RP2 fresh.
   - The lock files come from the new `flow/replay_compose.py`, which takes each area of the device from its own
     reference build **by location**: cells by bel site, route entries by pip tile (or wire tile for a source wire),
     `outside` = no region, or one region. A wire taken twice with different pips is an error.
6. **Configurations, assembled** (`<rp1>_<rp2>_n`): static from `xor_add_a`, RP1 from the build that implemented that RP1
   module (`xor_add_a` or `rp1_andn_m`), RP2 likewise. Everything is pre-placed and pre-routed: nextpnr reports
   `0 not in this design, 0 collided` for all 4 (`rtkeep/*_n/nextpnr.log`).
7. Checks: `region_pips.py` per build per RP, `pr_check.py` for every pair that differs in one RP (with that RP's
   region), the new `flow/pr_check_multi.py` over all 7 builds, and the new `flow/routethru_scan.py`.

Run: `python3 flow/build_pr_native.py --design rv2 --run` (`build/patched/rv2_native/build_rtkeep.out`;
outputs `build/patched/rv2_native/rtkeep/`). The `replay`-binary run is kept in `build/patched/rv2_native/replay/`
(`--variant replay`).

| build | config (rp1, rp2) | router2 | Fmax |
|---|---|---|---|
| `xor_add_a` | xor, add | 16.50 s | 142.35 MHz |
| `rp1_andn_m`, `rp2_grey_m` | andn, add / xor, grey | 1.42 s / 1.40 s | 142.35 MHz |
| `xor_add_n`, `andn_add_n`, `xor_grey_n`, `andn_grey_n` | assembled | 1.37–1.93 s | 142.35 MHz |

Single seed. With the `replay` binary the first build took 26.04 s and reached 145.14 MHz.

## 5. Verification

### 5.1 Static and the other RP unchanged (`flow/pr_check_multi.py`, new)

For every pair of the 7 builds it diffs all frames (ECC masked) and assigns each differing frame to rp1, rp2 or
static. Pass: no static frame differs, no frame of an RP whose module is the same differs, and no differing word in a
changed RP's frame belongs to a tile outside that RP.

`build/patched/rv2_native/rtkeep/checks/pr_check_multi.log`: **21/21 pairs PASS**.

- Pairs that differ only in RP1: 59 frames differ, all in rp1; rp2 0, static 0.
- Pairs that differ only in RP2: 66 frames differ, all in rp2; rp1 0, static 0.
- Both differ: 125 = 59 + 66.
- Same modules: 0 frames differ. This holds for `xor_add_a` vs the assembled `xor_add_n`, `rp1_andn_m` vs `andn_add_n`
  and `rp2_grey_m` vs `xor_grey_n`. So the assembled configuration is bit-identical to the build that implemented the
  module.
- `andn_grey_n` was never routed as a whole: it is RP1 from `rp1_andn_m` + RP2 from `rp2_grey_m`. It differs from
  `andn_add_n` only in rp2 and from `xor_grey_n` only in rp1.
- The existing `pr_check.py` with the changed RP's region agrees: `STATIC IDENTICAL OUTSIDE REGION`, 0 foreign words,
  for the 4 single-RP pairs (`rtkeep/checks/pr_check_*_n_*_n.log`). Its "outside" includes the other RP's frames.

Same result, 21/21, on the `replay`-binary builds (58 instead of 59 rp1 frames; `replay/checks/pr_check_multi.log`).

### 5.2 Partials per RP (`flow/native_check_multi.sh`, new)

`NAT=build/patched/rv2_native/rtkeep OUT=build/patched/partials/rv2/rtkeep BMO=build/patched/rv2_native/byteman/rtkeep TAGP=rv2rt bash flow/native_check_multi.sh`
→ `build/patched/rv2_native/native_check_rtkeep.log`, **18/18 PASS, exit 0** (8 partials, 2 negative controls, 8 region2v full).

For every ordered pair of assembled configurations that differ in exactly one RP, it runs
`partial.py <target> --region <that RP> --fasm --static-pips static.prerouted --base <base> --simulate` (partial.py not
modified). 8 partials: rp1 andn↔xor with rp2 = add and with rp2 = grey; rp2 add↔grey with rp1 = xor and with rp1 = andn.

| check | result for all 8 |
|---|---|
| size | 59,406 bytes `.bit` (59,272 `.bin`); 72 region frames, 1 run × 2 passes |
| CRC, simulated load | `crc: OK; base + partial == target: True (0 frames differ)` |
| frames written (`gate`, from the partial's own frames) | 73: own RP 72/72, **other RP 0**, static 1 |
| the 1 static frame | the run-end pad: `0x00020600` (c12 m0, row T1) for rp1, `0x00400600` (c12 m0, row B0) for rp2; partial.py: `all of them run-end pad frames: True; pad frames carry the full bitstream's own content: True` |
| byteman (base + partial) vs the original target | 0 of 5408 frames differ |
| region2v on the byteman result | sim 3582/3582 |

Pass-1 held-back pips (partial.py `pass1_dropped_pips`): 222 / 125 (rp1, to andn / to xor), 426 / 35 (rp2, to add / to
grey) (`build/patched/partials/rv2/rtkeep/*.check.json`).

**Region gate for that RP only (negative control):** the same target cut to the other RP's region
(`partial.py --region <other RP>`) does not reproduce the target: `base + partial == target: False (66 frames differ)`
for rp2's target cut to rp1, `(59 frames differ)` for rp1's target cut to rp2
(`build/patched/partials/rv2/rtkeep/neg_*.log`).

### 5.3 region2v per RP, simulation and proof

On each of the 4 assembled full bitstreams, for each RP, with that RP's shell and region: **8/8 sim 3582/3582 and
PROVED** (yosys SAT, `ulimit -v 3000000` KB, 600 s timeout; `build/patched/partials/rv2/rtkeep/r2v_full_*.log[.formal]`).
This includes `grey` (rd = 0) in rp2.

With the `replay` binary, region2v rejected every RP2 netlist (`output anchor q_rd_10 … reaches no output port`, the
route-through of section 3) and passed every RP1 netlist (`build/patched/rv2_native/replay_checks/native_check_partials.log`).

### 5.4 Whole-bitstream firmware test of both custom instructions (fasm2bels)

`NAT=build/patched/rv2_native/rtkeep CFGS='andn_grey xor_add' NEG='andn_grey:andn:add xor_add:xor:grey' bash flow/b2n_multi.sh`
→ `build/patched/rv2_native/b2n_multi.log`. `flow/b2n_multi.sh` (new) decodes the full bitstream with
`flow/bit2netlist.sh <name> <bit> rv_soc -` (decode only, unchanged script) and simulates the netlist with
`designs/rv_soc2/tb/b2n_tb_rv_soc2.v`: boot from the bitstream's own BRAM init, then 11 vector pairs, each as `C` and as
`D` over the UART.

- `andn_grey_n` (never routed as a whole, see 5.1): **22/22 commands PASS**.
- `xor_add_n`: **22/22 PASS**.
- Negative controls (same netlists, wrong expected RP2 module): `andn_grey_n` checked as (andn, add) and `xor_add_n`
  as (xor, grey) each give 8 FAIL lines, all on `D` (14/22 pass: the 11 `C` commands and the 3 vectors whose sum is
  0 mod 2^32, where add and grey agree). So the test tells the RP2 modules apart.
- Decoded netlists: 2 RAMB36E1, 1 ICAPE2, CARRY4 98 (andn_grey) / 106 (xor_add); 32 orphan sinks, all BRAM REGCLK
  (the existing `ORPHAN_OK` rule); fasm2bels 12–13 s.
- Placement in the `rtkeep` builds: every cell in rp1's sites is a `u_rm.` cell and vice versa, same for rp2
  (`build/patched/rv2_native/placement_check_rtkeep.log`; 173 cells in rp1, 213 (add) / 141 (grey) in rp2).

## 6. Existing single-RP designs unchanged

- Dry runs of `rv_pr`, `rv_b`, `rv_c`, `rv_m`, rv_pr with all 6 RMs and `--timing-allow-fail popc minmax`, and the rv_c
  `--no-shared-frame-pblock` control: output identical before and after the change
  (`build/patched/rv2_native/dry_{before,final}_*.txt`, `cmp`).
- Cached `--run` reruns of rv_b, rv_c, rv_m: every step `[skip]` (24 each; `cached_rerun_*.out`).
- rv_pr: the dry run shows every step `[skip]` except `[dry] region.txt`, exactly as before this change (that file
  was never written into `build/patched/rv_pr_native/router`). A `--run` would write it, so it was not run, because that
  directory must not be modified.
- rv2 cached `--run`: 55 skip, nothing rebuilt (`cached_rerun_rv2.out`).

## 7. Files

| file | |
|---|---|
| `designs/rv_soc2/` | rv_soc.v (rm_bridge2, u_rm2), uart.v, picorv32.v, xdc, fw/main.{s,hex}, pr/rm_stub.v, run_sim.sh, tb/{tb_rv_soc2.v, slot_models.v, b2n_tb_rv_soc2.v, icape2_model.v, b2n_ramb36e1.v, gl_ramb36e1.v} |
| `flow/build_pr_native.py` | `rv2` design, `partitions`/`configs`, `main_multi`, variant `rtkeep` |
| `flow/replay_compose.py` | new: pre-placement/pre-routing files assembled per area from several builds |
| `flow/pr_check_multi.py` | new: per-RP frame comparison of all configuration pairs |
| `flow/routethru_scan.py` | new: LUT route-throughs inside regions, per net class |
| `flow/native_check_multi.sh` | new: per-RP partials, gate, negative control, byteman, region2v (+proof) |
| `flow/b2n_multi.sh` | new: fasm2bels + firmware test of `C` and `D` |
| `flow/rvasm.py` | `custom1` mnemonic |
| `docs/drafts/nextpnr-pblock-routethru.{md,patch}` | new draft patch, variant `rtkeep` |

## 8. Open problems

- Two RPs with **disjoint frames** only. RPs that share frames (e.g. two pblocks in one clock-region column) would need
  each partial to carry the other RP's current content in the shared frames; `build_pr_native.py` refuses such a layout.
- The assembled configurations are bit-identical to the module builds here, but the composition relies on routes being
  attributable to an area by pip tile. A route of a static net that used a pip in a region tile would be taken from
  the region's source; keep-out made that 0 in these builds (5.1, section 3).
- Partition pins are still the anchor LUT/FF shells; the RP2 shell is the same generator output as rv_b's (identical
  BELs).
- Not compared against a Vivado two-RP reference build; the Vivado rule for static/partition-pin LUT route-throughs
  inside an RP was not checked.
- A partial is loaded into a base that differs from the target only in that RP. Loading an RP1 partial into a base with a
  different RP2 module is fine by construction (frame sets disjoint) but was simulated only through 5.1's identities,
  not as its own partial run.
- Nothing on hardware.
