# nextpnr-replicate (draft, not posted)

Base: build/src/nextpnr-cb2rel HEAD 1a771b24 (release patches 0001-0038) + docs/drafts/nextpnr-static-preplaced.patch
(pending 0039), committed locally as 49a2d45e in the worktree build/src/nextpnr-repl. nextpnr-replicate.patch is the
diff against 49a2d45e only (`git apply --check` clean). Build build/nextpnr-build/repl
(build/nextpnr-build/repl_build.sh, cmake flags of docs/buildenv.md, ninja -j4). Files: new
himbaechel/uarch/xilinx/replicate.cc; xilinx.{cc,h} (option, call, declarations); hardblock_timing.cc (carry DI arcs,
only while the pass runs); CMakeLists.txt.

Why: Vivado's fanout / critical-cell replication on our placements gives +5.0 % Fmax (cb_all2, 12 runs; rv_soc
+7.3/+10.6/+5.8 %), 0 % on Vivado's own placement. Its log shows a few targeted actions per run: on rv_soc s1 one copy
of pcpi_rs1[1] (29 sinks) and new drivers for two LUTs on the worst path ($abc$72565$lut$aiger72564$3473,
$abc$72565$lut$not$aiger72564$1207); on s2/s3 pcpi_rs2[0/1] or pcpi_rs1[1], plus 2-3 LUTs.

## Version 1 (fanout mode) and why it did not help
v1 (`cb2_repl`, Vivado-timed -0.2 %) copied the drivers of nets with fanout >= 8.
- On rv_soc s1 it refused pcpi_rs1[1] ("inputs bear the copy"): one more sink on the 32-sink CE net cost 3 ps in the
  model, on a net already at the model's worst slack.
- It never looked at 3473 (fanout 5) or 1207 (fanout 2).

Two measurement findings changed the pass.

1. **nextpnr does not time any CARRY4 DI input.**
   - The chipdb has no DIk -> O/CO arcs: all 368 carry DI arcs of rv_soc s1 are unconstrained, and
     `getCellDelay(CARRY4, DI0, CO3)` returns false.
   - Cause: the generator (gen/xilinx_gen.py, `import_sdf_timings(carry, slicem_sdf.cells[("CARRY4", "SLICEM")])`)
     imports the SDF cell type CARRY4 only. prjxray lists the DI arcs under CARRY4_AX..DX, e.g.
     `IOPATH DI0 CO3 (0.169::0.21)(0.444::0.55)`.
   - Effect: every path through a carry DI pin is invisible to nextpnr's timing: the placer's and sa-refine's
     criticalities, the router, and the reported Fmax.
   - Example: Vivado's worst rv_soc s1 path runs FF -> LUT2 -> CARRY4 S1 -> O2 -> LUT1 1207 -> LUT1 -> CARRY4 DI0 ->
     CO3 -> ... -> FDSE S. Our analysis had 1207/I0 unconstrained.
   - The real fix belongs in the chipdb generator (import the DI arcs of the _AX.._DX variants into CARRY4). It changes
     every design's timing, so it is not in this patch.
   - Here, only while -o replicate runs (flag `replicate_carry_di`, key `carrydi`, default 1), getCellDelay answers
     DIk -> X with the same carry's Sk -> X arc. prjxray's DI and S arcs differ by tens of ps.
   - With it, no pin of Vivado's paths with slack < -1.5 ns is unconstrained in our analysis (before: 1 of 239, the
     1207 arc on the worst path).
2. **The arc model.**
   - sa-refine's model (313 + 1.235 x matrix) plus v1's fanout term over-estimated arcs by +154 ps on average and
     +440 ps on the critical ones. Measured on rv_soc s1-3, rv_big s1-3 and rv_mul s1: 41888 arcs between tiles,
     matched by pin to Vivado's routed net delays of the ua_dxy exact imports (build/repl/arc_fit.py).
   - Refit between tiles: delay = -228 + 1.711 x matrix + 102 x log2(sinks/2), minus 275 ps for a CE/SR pin (bias 0,
     rms 394 ps).
   - Inside a tile: 650 ps (LUT input, same slice), 720 ps (other pin, same slice), 680 ps (other slice).
   - This is now the default; `samodel=1` restores sa-refine's model.

Ranking against Vivado: endpoint slack, Spearman rank correlation over the endpoints both list (build/repl/rank_cmp.py).

| design | v1 model, s1 / s2 / s3 | new model + carry DI, s1 / s2 / s3 |
|---|---|---|
| rv_soc | 0.66 / 0.72 / 0.81 | 0.60 / 0.76 / 0.83 |
| rv_big | 0.61 / 0.48 / 0.42 | 0.60 / 0.61 / 0.68 |

Vivado's worst rv_soc s1 endpoint (slice$10845, -3.677 ns) went from model rank #49 (-2.651 ns, with its worst path
untimed) to #38 (-3.381 ns, the same path as Vivado's).

Not fixed: the model still puts the CE paths of the pcpi_rs1 register bank first (-4.4 ns, Vivado -2.5 ns).
- Their arcs read 1.3 ns too long: a 128-sink net +490 ps, short LUT arcs +300 ps.
- Their cell/setup part reads 0.65 ns too long.
- The chipdb's setup values (CE 169, D 1, SR 100 ps) do not match Vivado's (SR 430-520 ps).

## -o replicate[=key=value:...]
Off unless given; skipped (with a log line) under -o preplaced / -o prerouted.

Position in XilinxImpl::postPlace: after replace_around_brams, sa-refine and timing-opt, before lut6-first and
fixup_placement.
- After sa-refine, so the SA does not undo the copies.
- Before lut6-first, which then also moves a copy left on a 5LUT / x5FF bel.
- Before fixup_placement, which renames LUT ports: copies are made from the packer's cells and go through it like
  any LUT.

**Critical-cell mode** (cc=1, the default). Per round (at most `ccrounds`):
- A setup-only timing analysis on the model above; endpoints (FF/BRAM/DSP data and control inputs) sorted by slack.
- For each of the worst endpoints (up to `ccpaths` new paths): its worst path, walked back through the input of least
  slack to a register. Drivers already looked at this round without result are skipped, so a register bank behind one
  decoder counts as one path.
- On the path, every driver that can be copied is tried:
  - plain FDRE/FDSE/FDCE/FDPE on a BUFG clock, or a plain LUT1-6 that is alone or the root of a LUT+FF cluster;
  - not carry, mux, LUTRAM/SRL, LUT pair, fixed/locked/BEL/LOC, region (DFX/pblock), KEEP/DONT_TOUCH/MARK_DEBUG/
    ASYNC_REG/IOB, or a cell named by a timing exception;
  - fanout 2..`maxfo`.
  The copy serves the path's sink and the sinks of that net within `ccwin` ps of it (never all of them), on the best
  free bel by the bound.
- The driver whose copy raises the group's bound most is copied (up to 3 tries per path), at most `ccmax` per round.
- A flip-flop whose D comes from a plain LUT in its own tile is copied together with that LUT (`dlut`). That is the
  packer's LUT+FF pair: its D is a direct in-slice connection, and a second, fabric sink on that LUT output would need
  the position's one output mux. The LUT copy takes the 6LUT of the copy's eighth and feeds its D directly.
- Then a fresh analysis; a round that lowers the model's worst slack by more than `tol` is taken back.

**Fanout mode** (fanout=1; v1): nets with fanout `minfo`..`maxfo` and a sink of criticality >= `critmin`, the `nets`
worst. Sink groups: the critical sinks, and k-means (k = 2..`kmax`) of the critical and of all sink positions.

**Acceptance (both modes):**
- A path through driver input j and sink i has slack >= max(slack(j), slack(i)). After the change it has at least that
  minus the growth of the two arcs (a lower bound; for the D-LUT pair, the growth of the LUT's input arcs).
- The copy's group must clear its own worst slack + `margin`.
- None of these may fall below that level: the original's remaining sinks, a flip-flop copy's own D/CE/SR arcs, and
  the other sinks of the input nets (which get one more load, the `fops` term; a cost below `tol` is ignored). Losses
  up to `tol` are allowed away from the worst slack.
- Every touched tile must stay legal (isBelLocationValid after dropping the tiles' validity caches); otherwise netlist
  and placement are restored.
- Optionally (moveorig) the original moves to where its remaining sinks gain >= `margin`.

**Correctness:**
- A copy has the type, params (INIT), attributes (without BEL/LOC) and input nets of its original.
- Names are `<cell>$repN` and `<net>$repN`, deterministic.
- At the end every copy is checked against its original (inputs equal, or nets of copies of the same driver) and every
  cell for a valid bel; a mismatch is a log_error.

**Log lines:**
- `replicate: N nets considered, C copies made (F flip-flops, L LUTs; M originals moved) ... model slack worst a -> b`
- `replicate: critical-cell mode: P paths walked, X copies`
- `replicate: K flip-flops copied together with the LUT that feeds their D`
- `dump=FILE` writes the model's endpoint slacks, and FILE.arcs every arc (model delay, fanout, slack).

**Keys (default):**
- Critical-cell mode: cc 1, ccpaths 20, ccmax 3, ccrounds 8, ccwin 100.
- Fanout mode: fanout 0, minfo 8, maxfo 400, critmin 0.8, nets 100, rounds 10, batch 8, kmax 3.
- Common: copies 100, perroot 3 (copies per original), radius 12, tiles 12, tries 24, margin 50, tol 10, kinds 3
  (1 FF, 2 LUT), moveorig 1, ctrl 1 (FF CE/SR sinks may move in fanout mode), dlut 1, carrydi 1.
- Model: alpha -228, beta 1.711, fops 102, ctrlps -275, site 650, siteother 720, tile 680, quant 0.02, samodel 0.
- dump, verbose 0..2.

**Recommended:** `-o replicate=cc=1:fanout=0` (= the defaults) on the cb_all2 arguments. In flow/place_bench.py: binary
`repl`, variants `cb2_repl2` / `cb2_repl2_dq` (rv_mul). `cb2_repl` / `cb2_repl_dq` are v1's runs, built from the v1
source; with the current binary, `-o replicate` means the new defaults.

## No-op
- Option absent: replicate() returns at once and the carry DI flag stays off. build/repl/noop0.sh with the final
  binary: FASM without `#` lines IDENTICAL to cb_all2 on rv_soc and bram, seeds 1-3. sha256 of the bodies: rv_soc
  19fa1232 / 6c032c4f / 7c60e2b1, bram cbbb365a / 1b4ebd9a / eb0b0472.
- The bench's .frames are not compared (0 bytes for rv_soc).
- bram s1 with the option: 0 copies, FASM identical to cb_all2.
- The binary rebuilt after a final comment-only edit places rv_soc s1 cb2_repl2 identically to the bench run.

## Results (seeds 1-3)
These Fmax figures come from nextpnr's own timer, which does not see carry DI paths, so read them with care. For
rv_big / rv_mul the "without" column is ua_dxy / ua_dxy_dq, which has arguments identical to cb_all2.

| design | seed | Fmax without (MHz) | Fmax cb2_repl2 (MHz) | copies (FF/LUT) | FF + D LUT pairs | originals moved | model worst slack ns | model 2 % slack ns |
|---|---|---|---|---|---|---|---|---|
| rv_soc | 1 | 97.98 | 100.39 | 11 (1/10) | 1 | 5 | -4.417 -> -3.392 | -2.816 -> -2.708 |
| rv_soc | 2 | 98.47 | 98.78 | 17 (4/13) | 4 | 8 | -4.996 -> -3.625 | -2.911 -> -2.737 |
| rv_soc | 3 | 94.75 | 99.68 | 14 (0/14) | 0 | 6 | -4.665 -> -3.816 | -2.724 -> -2.556 |
| bram | 1 | 120.06 | 120.06 | 0 | 0 | 0 | -1.810 (unchanged) | -1.232 (unchanged) |
| bram | 2 | 130.41 | 124.19 | 2 (0/2) | 0 | 0 | -1.878 (unchanged) | -1.173 -> -1.160 |
| bram | 3 | 123.33 | 113.84 | 1 (0/1) | 0 | 0 | -2.096 (unchanged) | -1.253 -> -1.211 |
| rv_big | 1 | 85.57 | 85.97 | 16 (2/14) | 2 | 4 | -6.200 -> -5.350 | -5.009 -> -4.771 |
| rv_big | 2 | 89.59 | 82.17 | 20 (0/20) | 0 | 7 | -5.856 -> -5.733 | -4.906 -> -4.564 |
| rv_big | 3 | 89.83 | 86.65 | 12 (0/12) | 0 | 2 | -5.708 -> -5.363 | -5.165 -> -5.129 |
| rv_mul | 1 | 102.09 | 96.78 | 5 (0/5) | 0 | 2 | -4.516 -> -3.928 | -3.215 -> -3.110 |
| rv_mul | 2 | 97.78 | 101.30 | 14 (4/10) | 4 | 3 | -4.703 -> -4.007 | -3.306 -> -3.223 |
| rv_mul | 3 | 97.01 | 93.78 | 13 (0/13) | 0 | 3 | -4.126 -> -3.524 | -3.227 -> -2.844 |

- Means on nextpnr's timer: rv_soc +2.6 %, bram -4.2 %, rv_big -3.8 %, rv_mul -1.7 %.
- The model's worst slack improves by 0.1 to 1.4 ns on rv_soc, rv_big and rv_mul. On bram it does not move: its worst
  path starts at a block RAM output, which cannot be copied, and the 1-2 LUT copies only move the 0.5 % and 2 %
  quantiles.
- On rv_soc the pass now makes the copies Vivado makes: pcpi_rs1[1] (slice$10967, s1 and s2, with its D LUT),
  pcpi_rs2[0/1] (slice$10925/10926, s2), pcpi_rs1[0] (slice$10966, s2), LUT 3473 (s1-s3) and LUT 1207 (s3).
- Vivado timing of these placements is the real measurement (exact-import sources below).
- The pass takes 0.3-1.5 s.

## Functional
- flow/dpl_check.sh, run with DB=~/ofx-test/prefix-cb2/share/nextpnr/external/prjxray-db/artix7 (the script's default
  ~/ofx-test/prefix no longer exists):
  - cb2_repl2 rv_soc s1 (11 copies, one FF with its D LUT): `DONE qor_rv_soc xor vectors=11 fails=0`.
  - cb2_repl2 rv_soc s2 (17 copies, four FFs with their D LUT): `DONE qor_rv_soc xor vectors=11 fails=0`.
  - v1: rv_soc s1 and s3 fails=0.
  - rv_mul / rv_big cannot be checked this way: fasm2bels has no DSP tile decoder (`KeyError: 'DSP_L'`).
- Exact import:
  - flow/exact_src.py exports the copies as new cells of their original's type with its INIT/params, placed on their
    bels, with their sinks rewired. No change to exact_src.py / xroute.py was needed.
  - build/repl/cmp_copies.py checks every copy against its original in the exported netlist: same type and params,
    and the same input bits or bits of copies of the same driver.
  - All 12 cb2_repl2 exports pass: 12/12, 21/21, 14/14 (rv_soc); 0/0, 2/2, 1/1 (bram); 18/18, 20/20, 12/12 (rv_big);
    5/5, 18/18, 13/13 (rv_mul). These counts include the D LUT copies.
  - Location: designs/exact/<d>_p5_cb2_repl2[_dq]_s<s>_exact on the Windows side.

## Limits
- The model's endpoint ranking still differs from Vivado's (Spearman 0.6-0.8): high-fanout CE paths read too slow,
  and the chipdb's setup values differ from Vivado's. A copy on a path the model over-rates costs a LUT and nothing
  else.
- The estimate is a bound only: no reconvergence, no congestion. Copies go on free bels only (no ripple moves).
- The carry DI arcs are a stand-in (the Sk arcs) and exist only inside the pass; the real fix belongs in the chipdb
  generator.
- Not copied: carries, F7/F8 muxes, LUTRAM/SRL, BRAM/DSP outputs, IO drivers, flip-flops on regional clocks. No
  un-replication.
