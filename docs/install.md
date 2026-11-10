# Installing the open-dfx-xc7 toolchain

`install/install.sh` builds the whole open toolchain for this flow from pinned upstream sources into one
user-local directory (the *prefix*). It needs no root access and changes nothing outside the prefix and
its cache directory. It does nothing until you pass `--run`.

What you get in the prefix:

| Tool | From | Notes |
|---|---|---|
| `nextpnr-himbaechel` (`nextpnr-xilinx` is a link to it), `bbasm` | openXC7/nextpnr `ce3f7c18` + 27 local patches (`install/patches/nextpnr/`) | xilinx uarch only, no device built in |
| `fasm2frames`, `bit2fasm`, `xc7frames2bit`, `bitread`, `xc7patch` | openXC7/prjxray `a5589d51`, openXC7/fasm `2f57ccb1` | python tools run with the prefix's own Python 3.12 |
| prjxray-db | openXC7/prjxray-db `a8b09269` + 5 additions (`install/patches/prjxray-db/`, artix7 only) | only the families needed for the chosen devices |
| `chipdb-<device>.bin` | generated from the above with nextpnr's `xilinx_gen.py` + `bbasm` | checked against the openXC7 nightly's sha256 (identical) |
| `ofx/chipdb-<device>.bin` (artix7 dies) | the same with nextpnr-xilinx-meta + `site_type_XADC.json` (`install/patches/nextpnr-xilinx-meta/`) | has the XADC bel; used by `ofx build` when the netlist has an XADC |
| `cal/chipdb-xc7a50t.bin` | the `ofx/` chipdb made with `--cell-timing install/patches/chipdb/cell-timing-xc7a50t.json` | LUT/FF timing measured against Vivado (xc7a35t-1); used by `ofx build` with `cell_timing = "auto"` (opt-in) for xc7a35t*-1 parts |
| `share/ofx/yosys-plugins/` | `xilinx_dsp_qor.so`, `xilinx_asyncreg.so`, `clkbufmap_gapfix.so` from yosys `3718f7f13` + 3 patches (`install/patches/yosys/`), built against the oss-cad-suite headers | loaded by `ofx build` (see "yosys: plugins, not a rebuilt binary") |
| `byteman` | FPGA-Research/byteman `24752871` | |
| `openFPGALoader` | trabucayre/openFPGALoader v1.2.0 + `--partial` (`install/patches/openfpgaloader/`) | |
| `yosys` (+ iverilog, sby, ...) | YosysHQ oss-cad-suite 2026-10-21 release | see "Why oss-cad-suite" |
| `ghdl` + yosys `ghdl` plugin (VHDL) | in the same oss-cad-suite release (`GHDL 7.0.0-dev (6.0.0.r546.g71b3e1ac7)`, `share/yosys/plugins/ghdl.so`) | needed only for VHDL sources (docs/ofx.md, VHDL); `--yosys source` installs no GHDL, so VHDL is unavailable there |

Every pin, with where it was taken from, is in `install/sources.toml`.

## Quickstart

Linux x86_64 with `bash git curl tar gzip` (Debian/Ubuntu: `sudo apt-get install git curl ca-certificates`).

```bash
git clone <this repository> open-dfx-xc7 && cd open-dfx-xc7
bash install/install.sh                          # dry run: prints every step
bash install/install.sh --run                    # installs into ~/.local/ofx, cache in ~/.cache/ofx
source ~/.local/ofx/env.sh
bash install/link_repo.sh --run                  # point this checkout's toolchain/ at the prefix
python3 flow/build_openxc7.py blinky --run       # a full bitstream
python3 flow/build_pr_native.py --design rv_ppa --rms xor andn --run   # partial reconfiguration
bash install/smoke_test.sh --run                 # end-to-end check of an installed prefix
```

Options (or the matching `OFX_*` environment variables):

| Option | Default | |
|---|---|---|
| `--prefix DIR` | `~/.local/ofx` | install location |
| `--cache DIR` | `~/.cache/ofx` | downloads, git sources, build trees, logs (`logs/<step>.log`) |
| `--devices "..."` | `xc7a50t` | chipdbs to generate (the board presets also need `xc7a100t`, `xc7s50`, `xc7z020`, `xc7a200t`) |
| `--all-devices` | | all 11 dies the openXC7 nightly ships |
| `--yosys oss-cad-suite\|source\|none` | `oss-cad-suite` | |
| `--jobs N` | 4 | parallel compile jobs |
| `--steps "..."` | all | any of `micromamba env sources nextpnr prjxray byteman openfpgaloader yosys chipdb envsh` |

The script is idempotent: each step records a stamp in `<prefix>/share/ofx/stamps/` and is skipped when its
inputs (pinned revision, patch series, lock file) are unchanged. Downloads are verified (sha256, or md5 for
conda packages from the lock), and every git checkout is checked against its pinned commit.

### How the build environment is made

The compilers and libraries come from conda-forge through micromamba, as in `docs/buildenv.md`: the micromamba
2.9.0 static binary (sha256-checked) creates `<prefix>/env` from `install/conda-linux-64.lock`, which is
`toolchain/buildenv/env-explicit.txt`, the environment every variant binary in this repository was built with
(GCC 14.4.0, Boost 1.81, Eigen 3.4.0, CMake 4.4.3, Python 3.12.15). The packages are downloaded with curl
(retried, md5-checked) and the environment is then created with `micromamba create --offline`. The python
packages that `fasm2frames`/`bit2fasm` need (PyYAML, simplejson, sortedcontainers, intervaltree, textX,
Arpeggio, at the versions in the openXC7 nightly) come from PyPI by URL and sha256
(`install/python-wheels.txt`).

### Using the prefix with this repository

The scripts in `flow/` look for their tools under `toolchain/` of the checkout, and the native flow looks for
its nextpnr variants under `build/nextpnr-build/<variant>/`. `install/link_repo.sh --run` creates those paths
as symbolic links into the prefix (`toolchain/openxc7`, `toolchain/oss-cad-suite`,
`toolchain/openxc7-BUILD-INFO.json`, `toolchain/byteman-build/byteman`, and
`build/nextpnr-build/{stock,router,router_nokeepout,pblock,replay,rtkeep,partpin,partpin2}/nextpnr-himbaechel`).
It never replaces an existing file or a link that points elsewhere.

### Why oss-cad-suite for yosys

- Every result in this repository was synthesized with exactly this binary (Yosys 0.70+186, git
  `3718f7f13`, from oss-cad-suite 20261021). Using the same release keeps the synthesized netlists
  byte-identical to the recorded builds; a yosys compiled here with another compiler is not guaranteed to
  give the same ABC results.
- The flow also uses other programs from the suite (iverilog for `flow/region2v.py` and `gl_sim.sh`, sby and
  the solvers for the region proofs, GHDL for VHDL).
- `--yosys source` builds yosys `3718f7f13` with CMake instead (experimental, see "What is untested"). It needs
  `bison >= 3.6` and `flex` on the host, because the conda lock does not have them. It does not apply the yosys
  patch series.

### yosys: plugins, not a rebuilt binary (ofx 0.1)

The three yosys drafts (`xilinx-dsp-pipeline`, `xilinx-asyncreg`, `clkbufmap-keep-buffer-inputs`) form
`install/patches/yosys/` (applied in that order to `3718f7f13` without a conflict). The installer builds them as
three plugins against the oss-cad-suite headers, with the prefix's conda g++ 14.4, into
`<prefix>/share/ofx/yosys-plugins/`: `xilinx_dsp_qor.so` (the patched `xilinx_dsp`, pass renamed, with the patched
pmgen matchers), `xilinx_asyncreg.so` (the new pass), `clkbufmap_gapfix.so` (the patched `clkbufmap`, pass
renamed). Why plugins and not a yosys built from source with the patches:

- The plugins leave the yosys binary identical to the one every recorded result was made with, so every flow
  script that does not load them gives the same netlist as before. A source build is another binary (another
  compiler) and would have to be shown equivalent on every recorded design; its JSON already differs textually,
  e.g. in every `src` attribute that names its share directory
  (`build/yosys-build/yosys-dspqor/share/abc9_model.v:...` in `build/qor/dsp/yfull/*.json`). It would also need
  bison/flex on the host.
- The flow needs oss-cad-suite anyway (GHDL, iverilog, sby).
- A plugin pass is only used when a script asks for it, so the drafts stay opt-in per flow: `ofx build` loads them
  (docs/ofx.md, release defaults), nothing else does.
- Checked: the installed `xilinx_dsp_qor.so` (conda g++ 14.4) gives yosys JSON byte-identical to the recorded
  plugin builds (host g++ 15.2) with `-pipeline` on rv_mul, rv_big, fir and rv_soc
  (`build/rel01_plugin_eq/summary.json`), and the installed `xilinx_asyncreg.so` gives JSON byte-identical to the
  recorded xdc2 builds of x_async_rtl, x_async_xdc and x_async_none (`build/rel01_plugin_eq/async/`). Finding 8 of
  docs/qor-vivado.md showed the plugin and the in-tree build give the same cells and DSP register settings.
- Cost: the plugins depend on the exact oss-cad-suite release (pinned by sha256), and `synth_xilinx -dsp_pipeline`
  itself does not exist; ofx runs `synth_xilinx` in parts around the plugin passes (`ofx/defaults.py`).

## The nextpnr patch series

`install/patches/nextpnr/` is generated from `docs/drafts/` by `install/gen_patch_series.sh` (which commits each
draft on a temporary worktree and runs `git format-patch`; the drafts themselves are unchanged). Where a draft was
made on another base and does not apply to the stack, the generator takes the rebased copy in
`install/patches/rebased/` instead (the resolution is described below); commit messages for drafts without a header
are in `install/patches/messages/`.

| # | Patch | From draft |
|---|---|---|
| 0001 | xilinx: read pblocks from the XDC | `nextpnr-pblock-xdc.patch` |
| 0002 | router2: hold the routes inside a region to it | `nextpnr-router-region.patch` |
| 0003 | xilinx: a pblock member on its own pblock's bel is not new in a closed tile | `nextpnr-pblock-replay.patch` |
| 0004 | xilinx: no LUT route-through in a routing-contained pblock for a net that leaves it | `nextpnr-pblock-routethru.patch` |
| 0005 | router2, xilinx: partition pins for routing regions | `nextpnr-partition-pins.patch` |
| 0006 | xilinx: do not pair a flipflop with a LUT or CARRY4 of another pblock | `nextpnr-pblock-lutff.patch` |
| 0007 | xilinx: pack shared carry S sources the same way whatever else is in the netlist | `nextpnr-carry-replay-order.patch` |
| 0008 | xilinx: route a greybox build's static side to given partition pins | `nextpnr-partition-pins-route.patch` |
| 0009 | xilinx: write DSP48E1 MASK[47:0] and AREG/BREG=1 like Vivado | `nextpnr-dsp-mask-areg.patch` |
| 0010 | xilinx: disconnect constant-tied ISERDESE2 dedicated pins | `nextpnr-iserdes-const-pins.patch` |
| 0011 | xilinx: keep a MUXF7 that also feeds fabric in its MUXF8 tree | `nextpnr-muxf7-mixed-loads.patch` |
| 0012 | xilinx: keep the pre-router partition-pin routes off other cells' pin-feed wires | `nextpnr-partition-pins-pinfeed.patch` |
| 0013 | xilinx, timing: read the XDC timing commands Vivado designs use | `nextpnr-xdc-timing.patch` (rebased) |
| 0014 | xilinx, timing: ASYNC_REG, I/O delays, IOB, path exceptions, uncertainty | `nextpnr-xdc2-constraints.patch` |
| 0015 | xilinx: time DSP48E1, ICAPE2 and RAMB36E1 pins (-o hardblock-timing) | `nextpnr-hardblock-timing.patch` (rebased) |
| 0016 | xilinx: gen: --cell-timing FILE for measured LUT and FF timing | `nextpnr-cell-timing-cal.patch` |
| 0017 | xilinx: place a DSP48E1 cascade along the chipdb wires (-o dsp-cascade-place) | `nextpnr-dsp-cascade-place.patch` (rebased) |
| 0018 | router2: --router2-region-keep-out-crit C | `nextpnr-router-keepout-crit.patch` (rebased) |
| 0019 | placer: opt-in placement options for the static placer and placer1 | `nextpnr-placer-tuning.patch` (rebased) |
| 0020 | xilinx: take IOSTANDARD/DRIVE/SLEW/DIFF_TERM from the IO buffer | `nextpnr-io-buffer-params.patch` |
| 0021 | xilinx: tie MMCME2_BASE/PLLE2_BASE inputs like the library cells | `nextpnr-mmcm-base-ties.patch` |
| 0022 | xilinx: keep BUFHCE loads in its clock region and route it on clock wires | `nextpnr-bufh-region.patch` |
| 0023 | xilinx: write DIFF_TERM for an LVDS_25 input | `nextpnr-diff-term.patch` (rebased) |
| 0024 | xilinx: write the ICAPE2 and DNA_PORT enable bits | `nextpnr-cfg-in-use.patch` |
| 0025 | xilinx: program unused MMCM/PLL outputs as Vivado does | `nextpnr-clkout-unused.patch` |
| 0026 | xilinx: FIFO18E1 and FIFO36E1 | `nextpnr-fifo.patch` |
| 0027 | xilinx: XADC | `nextpnr-xadc.patch` |
| 0028 | xilinx: partition-pin pre-route: FAN and CTRL wires are on the direct approach to a CE or SR pin (fixes dfxpp_a50, after 0.1) | `nextpnr-partition-pins-ce-sr.patch` |
| 0029 | timing_log: skip a cross-clock Fmax line when neither clock has an Fmax (crash with latches, after 0.1) | `nextpnr-timing-log-xclock.patch` |
| 0030 | xilinx: LDCE and LDPE latches (after 0.1) | `nextpnr-latch.patch` |
| 0031 | xilinx: -o carry-di-bypass, carry DI through the slice X pin (opt-in in nextpnr; on in ofx, after 0.1) | `nextpnr-carry-di-bypass.patch` (the carry part of `nextpnr-packing-dpl.patch`) |
| 0032 | xilinx: a LUT-RAM or SRL only in slice 0 of a CLBLM tile (fixes agent; regression flow/slicem_check.sh, after 0.1) | `nextpnr-slicem-slice0.patch` |

0001-0011 are byte-identical to the previous series. The patched tree is `install/patches/nextpnr/TREE`
(`961ea46e`); the installer refuses a worktree whose tree differs. It was built as variant `rel01`
(`build/src/nextpnr-rel01`, log `build/nextpnr-build/rel01.build.log`) and by the installer; both have only the
pre-existing `xilinx.cc` `-Wsign-compare` warning. The installed binary reports `ce3f7c18-ofx`.

Conflicts and how they were resolved (each as small as possible; the rebased patches are in `install/patches/rebased/`):

| Patch | Conflict | Resolution |
|---|---|---|
| 0013 xdc-timing | `xilinx.h`: the draft (made on router-region) adds the XDC clock-exception declarations where 0006 added `cells_in_different_pblocks` | both kept |
| 0015 hardblock-timing | both it and 0014 override `XilinxImpl::getCellDelay` (0014: pad buffers and BUFGCTRL for port paths; 0015: DSP48E1/ICAPE2 SDF arcs); the build would have had two definitions | 0014's function is renamed `buffer_cell_delay`, and 0015's `getCellDelay` calls it for every cell without hard-block timing where it called `get_cell_delay_default` (which `buffer_cell_delay` calls first). Without `-o hardblock-timing` every cell takes exactly 0014's path |
| 0017 dsp-cascade-place | `getClusterPlacement`: 0014 added the ASYNC_REG-chain case before the RAMB36 case the draft extends | the DSP case is added after the synchronizer case |
| 0018 router-keepout-crit | `router2.cc` `ArcData`: 0005 added the partition-pin fields where the draft adds `keep_out_exempt` | both kept |
| 0019 placer-tuning | `compute_criticality`: 0014 gives an exception path its criticality from its own requirement; the draft adds the period-aware criticality | exception paths first, then `--tmg-crit-target`, else the unchanged formula; with neither, the code path is 0014's |
| 0023 diff-term | 0014's XDC reader warns `set_property DIFF_TERM ... is NOT applied` (nothing wrote it) | `DIFF_TERM` moved to the applied properties and its "NOT applied" reason removed, in the same patch that makes it applied |

### prjxray-db and nextpnr-xilinx-meta additions

- `install/patches/prjxray-db/` holds copies of the five database drafts and a `SERIES` file (`<family> <file>`):
  `prjxray-db-diff-term.segbits`, `-fifo.segbits`, `-cfg-in-use.segbits`, `-monitor-bot.ppips`,
  `-xadc-init.segbits`, all for artix7. After copying the pinned families into the prefix, the installer runs
  `install/db_patch.py`, which appends each line to `segbits_<tile>.db` / `ppips_<tile>.db` (the same mapping as
  `flow/prim_db.py`) and refuses a feature the database already has. The installed artix7 tree is identical to the
  verified `build/prjxray-db-prim-xadc/artix7` (`diff -rq`, no output). Other families are not changed (the bits
  were measured on xc7a35t only).
- `install/patches/nextpnr-xilinx-meta/` holds `site_type_XADC.json` for artix7. The installer copies the pinned
  meta to `<cache>/work/nextpnr-xilinx-meta-ofx`, adds the file (refusing to overwrite one), and uses it only for
  the `ofx/` and `cal/` chipdbs.
- Chipdbs per device: `chipdb-<dev>.bin` from the pinned meta (checked against the nightly sha256: identical for
  xc7a50t, xc7a100t, xc7s50, xc7z020 in the test install), `ofx/chipdb-<dev>.bin` for artix7 dies with the meta
  addition (`[chipdb-sha256-ofx]`: xc7a50t identical to the verified `build/chipdb-prim` chipdb), and
  `cal/chipdb-<dev>.bin` where `install/patches/chipdb/cell-timing-<dev>.json` exists (only xc7a50t: the file is
  `build/chipdb-cal/cell_timing_xc7a35t_1.json`, sha256 `b50cdc4a...`). All three are generated from the pinned,
  unpatched prjxray-db, as the verified chipdbs were.
- Why the XADC chipdb is not the default one: with it, a design without any XADC places differently (rv_pp `xor_a`:
  24664 FASM lines differ, also with the previous `ofx` binary, `build/rel01_bisect/rv_pp/partpin/xor_a/ofx_xadc`;
  with the nightly chipdb the release binary differs only by the ICAP line,
  `build/rel01_bisect/rv_pp/partpin/xor_a/rel_nightly`). The extra bel changes the placer's bel order. Keeping the
  nightly chipdb as `chipdb-<dev>.bin` keeps every flow script's recorded result reproducible. `ofx build` uses the
  `ofx/` chipdb only for a netlist with an XADC cell, and the `cal/` chipdb only with `cell_timing = "auto"`
  (docs/ofx.md, "Release defaults").

### Does the combined binary change results?

`install/noop_check.py --run` reruns every recorded nextpnr call of the native flow with the `ofx` binary
(`build/nextpnr-build/ofx`, built from the same tree) on the same inputs (linked JSON, XDC, `-o preplaced`,
`-o prerouted`, `-o partition-pins`) and compares `.frames` with the variant's own output; where they differ it reruns
the variant binary too. Summaries: `build/ofx_noop/summary_all.json`, `build/ofx_noop/summary_rv_ppa_rv_pp.json`;
logs under `build/ofx_noop/<design>/<variant>/<build>/`.

| Design / variant | Builds | `.frames` identical to the variant's binary |
|---|---|---|
| blinky / stock | 1 | **1/1** |
| rv_soc / stock | 1 | **1/1** |
| rv_pp / partpin | 5 | **5/5** |
| rv_ppa / partpin2 | 10 | **10/10** |
| rv_pr / router (6 RMs) | 7 | 0/7: `xor_a` differs; the 6 replay builds fail |
| rv_b / router | 4 | 0/4: `xor_a` differs; 3 replay builds fail |
| rv_c / router | 4 | 0/4: `xor_a` differs; 3 replay builds fail |
| rv_m / replay | 4 | 0/4: `tbl_a` differs; 3 replay builds fail |
| rv2 / rtkeep | 7 | 0/7: `xor_add_a` differs; 6 builds fail |

So `ofx` is a no-op for every design built with the partition-pin binaries (`partpin`, `partpin2`) and for designs
without pblocks, but **not** for the five older designs, whose binaries predate two of the patches. For those, the
reference build (`*_a`) places and routes differently, and every replay build fails at once, because the recorded
`static.preplaced` names and places cells as the older binary packed them (for example
`ERROR: Bel 'X42Y12/SLICE_X0Y0.A6LUT' ... is not valid for cell '$abc$71968$lut$aiger$o489$S_DUP1'`): those replay
inputs cannot be reused with `ofx`; the design has to be rebuilt from its reference build.

Which patch changes `rv_pr/router/xor_a` (same inputs, `build/ofx_noop/attribution/rv_pr/xor_a/`): `router` (0001-0002)
= `replay` (+0003) ≠ `rtkeep` (+0004) = `ofx5` (+0005) = `ofx6` (+0006) ≠ `partpin` (+0007) = `ofx` (+0008-0011).
The two that change it are 0004 (no LUT route-through in a routing-contained pblock for a net that leaves it) and
0007 (carry S-source copies numbered per source, and with pblocks chains packed in name order), both intended
changes for pblock designs. The three gap fixes (0009-0011) are the only difference between `partpin2` and `ofx`
and changed none of the 10 rv_ppa builds, nor rv_pr `xor_a` (`partpin` = `ofx`); these designs have 4 MUXF7 + 2
MUXF8 and no DSP48E1 or ISERDESE2. `rv_m`'s `tbl`/`tbl2` contain one DSP48E1 each, so the DSP patch may change their
FASM, but that comparison cannot isolate it because placement already differs there.

Rebuilt from scratch with `ofx` (the installed prefix, see below), the older designs still pass their checks:
`install/revalidate.sh --run` (log `~/ofx-test-revalidate.log`; work dir `~/ofx-test/smoke`) and the rv_pr smoke test:

| Design | Built with `ofx` | pr_check | region_pips (every build) |
|---|---|---|---|
| rv_pr, RMs xor, andn | yes (163 s) | xor_n vs andn_n: STATIC IDENTICAL OUTSIDE REGION; native_check 6 PASS / 0 FAIL (2 partials simulated exact, byteman 0 frames differ, region2v simulation PASS) | not summarised |
| rv_b | yes (128 s) | 3/3 pairs STATIC IDENTICAL OUTSIDE REGION | 4 builds: 0 static pips in the region, 0 RM pips outside |
| rv_c | yes (175 s) | 3/3 pairs STATIC IDENTICAL OUTSIDE REGION | 4 builds: 0 / 0 |
| rv2 (two partitions) | yes (215 s) | 4/4 pairs STATIC IDENTICAL; `pr_check_multi` 21/21 pairs pass; routethru scan: 0 route-throughs on nets that leave a region | 7 builds x 2 partitions: 0 / 0 |
| rv_m (BRAM + DSP) | **not finished**: stopped during `tbl_a` (router2 at iteration 9 after 25 min). One rv_m route took 2834 s with `ofx` in the no-op run, so the 4 builds would take about 3 h on this loaded machine. Run `install/revalidate.sh --run --designs rv_m` | | |

These checks say the partitions are confined and the static design is unchanged between modules, as before; they
do not compare with the old bitstreams, which differ.

## Supported devices

A chipdb is per die; nextpnr maps the part name to its die (`himbaechel/uarch/xilinx/xilinx.cc`), and prjxray-db's
`mapping/devices.yaml` does the same for the bitstream side.

| `--devices` | Parts it serves | prjxray-db family | Generated and checked in the test install |
|---|---|---|---|
| `xc7a50t` (default) | xc7a35t, xc7a50t (Arty A7-35T is xc7a35tcsg324-1) | artix7 | **yes**: sha256 `ee4ff400…` = the openXC7 nightly's chipdb |
| `xc7a100t` | xc7a100t | artix7 | no |
| `xc7a200t` | xc7a200t | artix7 | no |
| `xc7s25`, `xc7s50` | xc7s25, xc7s50 | spartan7 | no |
| `xc7s100` | xc7s75, xc7s100 | spartan7 | no |
| `xc7z010` | xc7z007s, xc7z010 | zynq7 | no |
| `xc7z020` | xc7z020 | zynq7 | no |
| `xc7z030` | xc7z030 | zynq7 | no |
| `xc7z045` | xc7z035, xc7z045 | zynq7 | no |
| `xc7z100` | xc7z100 | zynq7 | no |

For each of these the installer compares the generated chipdb with the sha256 of the openXC7 nightly
upstream-2026-11-04 chipdb (`[chipdb-sha256]` in `install/sources.toml`) and prints a warning if it differs. The
partial-reconfiguration flow itself has only been run on xc7a35t (Arty A7-35T). Kintex-7 (`xc7k*`) is mapped to
prjxray-db's kintex7 family by the installer, but the nightly ships no Kintex-7 chipdb and none was tried.

## Licences

Read from each project's licence file at the pinned revision:

| Project | Licence (file) |
|---|---|
| openXC7/nextpnr | ISC (`COPYING`) |
| openXC7/nextpnr-xilinx-meta | CC0 1.0 (`COPYING`) |
| openXC7/prjxray | ISC (`LICENSE`) |
| openXC7/prjxray-db | CC0 1.0 (`LICENSE`) |
| openXC7/fasm | Apache-2.0 (`LICENSE`) |
| prjxray build submodules: abseil-cpp, cctz | Apache-2.0 (`LICENSE`, `LICENSE.txt`) |
| prjxray build submodules: googletest, gflags | BSD-3-Clause (`LICENSE`, `COPYING.txt`) |
| prjxray build submodules: yaml-cpp, sanitizers-cmake | MIT (`LICENSE`) |
| YosysHQ/yosys | ISC (`COPYING`) |
| YosysHQ/oss-cad-suite-build | build scripts ISC (`COPYING`); each bundled program under its own licence, collected in `license/` of the archive |
| trabucayre/openFPGALoader | Apache-2.0 (`LICENSE`) |
| FPGA-Research/byteman | Apache-2.0 (`LICENSE`) |
| mamba-org micromamba | BSD-3-Clause (mamba-org/mamba `LICENSE`) |
| conda-forge packages (GCC, Boost, ...) | each package's own licence, recorded in `<prefix>/env/conda-meta/*.json` |
| PyPI packages | PyYAML MIT, simplejson MIT, Arpeggio MIT, sortedcontainers Apache-2.0, intervaltree Apache-2.0, textX MIT (PyPI metadata) |

The patches in `install/patches/` are changes to nextpnr (ISC) and openFPGALoader (Apache-2.0) and are meant to be
offered under those projects' licences.

## Results of the test install

Run on 2026-11-06 in WSL2 Ubuntu (12 GB) into a new, empty prefix `~/ofx-test/prefix` with cache `~/ofx-test/cache`
(log `~/ofx-test-install.log`, step logs `~/ofx-test/cache/logs/`), `--devices xc7a50t`, `--jobs 4`, with other
nextpnr jobs running on the machine:

| Step | Result | Time |
|---|---|---|
| micromamba | downloaded from GitHub, sha256 OK | |
| env | 68 conda packages from conda.anaconda.org, md5 OK; 6 PyPI files, sha256 OK | 1948 s for all fetch steps, mostly TLS retries to conda.anaconda.org |
| sources | nextpnr, nextpnr-xilinx-meta, prjxray (+7 submodules at their gitlinks), prjxray-db (artix7 only, sparse), byteman, openFPGALoader fetched from GitHub; every HEAD verified | (in the above) |
| yosys | oss-cad-suite 20261021 extracted; `yosys -V`: `Yosys 0.70+186 (git sha1 3718f7f13, ...)` | |
| nextpnr | 11 patches applied, built; `--version`: `ce3f7c18-ofx`; 1 compiler warning (the pre-existing `-Wsign-compare`) | 131 s |
| prjxray | bitread, xc7frames2bit, xc7patch built; fasm + prjxray python import OK | 67 s |
| byteman | `byteman 1.3 (Build #226 ...)` | 27 s |
| openFPGALoader | v1.2.0 + 2 patches; `--help` lists `--partial` | 66 s |
| chipdb | `chipdb-xc7a50t.bin` sha256 `ee4ff400cfbeddd1eab0e19914b5cffeeec513bdecb4156f932208659bd59b21` = the nightly's | 48 s |
| total | 3290 s wall, including waits for free nextpnr slots | |

Notes on that run, so that nothing is overstated:
- The conda downloads failed with TLS errors about two times in three. 41 of the 68 packages came through the
  installer's own retry loop; the other 27 were fetched in parallel into the same cache by a separate curl loop over
  the same lock URLs (same md5 check), to save time. The installer then verified all 68 and created the env offline.
- The oss-cad-suite archive (748,284,197 bytes) was placed in the cache from `toolchain/dl/` instead of being
  downloaded again; the installer checked its sha256 before extracting it.
- The first run installed `fasm2frames`/`bit2fasm` as `libexec/*.py`, but `flow/bit2fasm.py` loads
  `libexec/bit2fasm` (the nightly's layout), so region2v failed in the first smoke run. install.sh was fixed and only
  its prjxray step was rerun on the test prefix.
- A second `install.sh --run` on the finished prefix exited 0 with every step cached (`~/ofx-test-rerun.log`).
- The prjxray-db artix7 tree installed is identical to the nightly's (`diff -rq`, no output).
- Sizes: prefix 4.3 GB (oss-cad-suite is most of it), cache 2.1 GB.

Smoke test (`install/smoke_test.sh --run --prefix ~/ofx-test/prefix --work ~/ofx-test/smoke`, log
`~/ofx-test-smoke2.log`, flow logs in `~/ofx-test/smoke/logs/`). Only the prefix and `/usr/bin:/bin` were on `PATH`;
every tool resolved inside the prefix (`logs/tools.txt`), and the work directory has copies of `flow/` and `designs/`
only, with `toolchain/` linked to the prefix.

| Check | Result |
|---|---|
| blinky, full flow | built (8 s); `.frames` identical to `build/openxc7/blinky/xc7a35tcsg324-1_s1/blinky.frames` |
| rv_ppa (partpin2) with RMs xor, andn: yosys, greybox placement, pin assignment, greybox static, proxies, replay builds | built (167 s); `.frames` of all 6 builds (`greybuf_p`, `grey_s`, `xor_p`, `xor_n`, `andn_p`, `andn_n`) identical to `build/patched/rv_ppa_native/partpin2/` |
| pr_check xor_n vs andn_n | STATIC IDENTICAL OUTSIDE REGION |
| pr_check grey_s vs xor_n, andn_n | STATIC DIFFERS, the same verdict as the reference build (expected, docs/phase14 section 6) |
| native_check: 2 partials with `partial.py --simulate`, byteman merge, region2v | 6 PASS, 0 FAIL: partials gate+CRC+simulated exact, byteman vs original target 0 frames differ, region2v simulation PASS (formal proof not run: `FORMAL=0` default, for memory) |

The same smoke test with `PR_DESIGN=rv_pr PR_VARIANT=router` (`~/ofx-test-smoke-rvpr.log`): built (163 s),
pr_check xor_n vs andn_n STATIC IDENTICAL, native_check 6 PASS / 0 FAIL, but the `.frames` differ from the recorded
router-binary builds, as explained above; they are identical to the `ofx` no-op run on the recorded inputs
(`build/ofx_noop/rv_pr/router/xor_a/ofx`).

## What is untested

- `install/Dockerfile`: written, never built. Docker is not usable on the machine this was written on without
  changing system settings (Docker Desktop's WSL integration is off).
- `--yosys source`: never run. The CMake options are taken from yosys `3718f7f13`'s `CMakeLists.txt`; a yosys built
  this way is not guaranteed to give the same netlists as the oss-cad-suite binary.
- Chipdbs other than `xc7a50t`: the code path is the same, but none was generated here.
- A machine other than this WSL2 Ubuntu, a distribution other than Ubuntu, and a fully clean `$HOME`.
- The region2v formal proofs in the smoke test (`FORMAL=1`), and anything on hardware.
- rv_m rebuilt from scratch with `ofx` (see above), and so the DSP48E1 FASM change of patch 0009 on a PR design.
- Drafts not in the 0.1 series: `nextpnr-timing-report`, `nextpnr-lut-perm-timing`, `nextpnr-route-timing-cal`,
  `nextpnr-area-pack`, `nextpnr-muxf-const-inputs`, `yosys-xilinx-area-opts`, `yosys-xilinx-dsp-init`. Add them with
  `NEXTPNR_SERIES="..." DRY_RUN=0 bash install/gen_patch_series.sh` and rerun `install/release_regress.sh --run`.
- `link_repo.sh` also links the `pblock` and `router_nokeepout` variant paths to `ofx`; the no-op check did not cover
  those two variants.

## Files

| File | |
|---|---|
| `install/install.sh` | the installer (dry run unless `--run`) |
| `install/sources.toml` | pinned sources, chipdb reference sha256s |
| `install/conda-linux-64.lock`, `install/python-wheels.txt` | the build environment |
| `install/patches/{nextpnr,openfpgaloader,yosys}/` | patch series (`TREE` = the patched tree id the installer checks); `messages/` holds the commit messages for drafts that had none, `rebased/` the conflict resolutions |
| `install/patches/{prjxray-db,nextpnr-xilinx-meta,chipdb}/` | database additions (`SERIES`), the XADC site type, the measured cell timing for `cal/` |
| `install/db_patch.py` | appends the prjxray-db additions to the installed database, refusing features it already has |
| `install/gen_patch_series.sh` | regenerates the series from `docs/drafts/` |
| `install/link_repo.sh` | links a checkout's `toolchain/` and variant paths to a prefix |
| `install/release_regress.sh` | the release regression (install, series, noop, defaults, ofx, smoke, identity, revalidate) |
| `install/smoke_test.sh` | end-to-end test of a prefix |
| `install/revalidate.sh` | rebuilds the native DFX designs with the installed nextpnr; PASS/FAIL on pr_check and region pips |
| `install/noop_check.py` | the `.frames` comparison of the release nextpnr against each variant binary on the recorded netlists |
| `install/defaults_noop.py` | the default-on `ofx build` options are no-ops where they must be; all options off = plain flow |
| `install/Dockerfile` | untested container build |

## Troubleshooting

- **`SSL connect error` / `unexpected eof while reading` from conda.anaconda.org.** Seen repeatedly on the
  machine this was written on (WSL2), for micromamba and for plain curl alike. The installer retries each
  package (`OFX_RETRIES`, default 4, each with curl's own 5 retries) and keeps what it has: rerun the same
  command and it continues where it stopped.
- **A step failed:** the last lines of `<cache>/logs/<step>.log` are printed; the full log stays there.
- **Out of memory while compiling:** lower `--jobs`. nextpnr with `-j4` peaked at 0.87 GB resident here.
- **Large chipdbs:** `xc7a200t` and the larger Zynq dies take much longer and more memory to generate than
  `xc7a50t`; generate them one at a time (`--devices xc7z045 --steps chipdb`).
- **`toolchain/openxc7` already exists:** `link_repo.sh` leaves existing paths alone; use a fresh checkout, or
  move your own links away first.
- **Starting over:** delete the prefix and the cache. Nothing else is touched.

## rv_m revalidated with the installed ofx nextpnr (2026-11-06, the 11-patch series)
- rv_m: build_pr_native exit 0, 3109 s.
- pr_check: STATIC IDENTICAL OUTSIDE REGION, 3/3 pairs.
- region_pips: 0 static pips in the region and 0 RM pips outside, 4/4 builds.
- Log: build/revalidate_rv_m.log.
- Every native DFX design (rv_pr, rv_b, rv_c, rv_m, rv2, rv_pp, rv_ppa) is now verified with the single combined ofx nextpnr.
