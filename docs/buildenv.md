# Build environment and tool builds (2026-11-05)

Everything here lives under `~/open-dfx-xc7`. Nothing was installed system-wide, and no sudo was used.
`~/.bashrc` is untouched. Exact versions are in `toolchain/buildenv/VERSIONS.txt`, and the full pinned
package list (URL plus md5 per package) is in `toolchain/buildenv/env-explicit.txt`.

## 1. micromamba and the conda-forge environment

micromamba 2.9.0 is the official static release binary, checked against the release's own `.sha256` file:

```bash
B=~/open-dfx-xc7/toolchain/buildenv
mkdir -p $B/bin $B/dl && cd $B/dl
curl -sSLO https://github.com/mamba-org/micromamba-releases/releases/download/2.9.0-0/micromamba-linux-64
curl -sSLO https://github.com/mamba-org/micromamba-releases/releases/download/2.9.0-0/micromamba-linux-64.sha256
echo "$(cut -d' ' -f1 micromamba-linux-64.sha256)  micromamba-linux-64" | sha256sum -c
install -m755 micromamba-linux-64 $B/bin/micromamba
```

The environment comes from conda-forge only. Set `MAMBA_ROOT_PREFIX` so the package cache stays inside `buildenv`:

```bash
export MAMBA_ROOT_PREFIX=$B/mamba MAMBA_DOWNLOAD_THREADS=2
$B/bin/micromamba create -y -p $B/env -c conda-forge --override-channels \
  python=3.12 cmake ninja make pkg-config "boost-cpp=1.81" "eigen=3.4.0" \
  libftdi libusb zlib hidapi "gcc_linux-64=14" "gxx_linux-64=14"
```

To reproduce the exact same set:
`$B/bin/micromamba create -y -p $B/env --file $B/env-explicit.txt`. With the default 5 download
threads, conda.anaconda.org dropped TLS connections ("SSL connect error"); 2 threads worked.

Boost 1.81 and Eigen 3.4.0 were chosen to match the nightly. Its `lib/openxc7/libboost_*.so.1.81.0` and
`BUILD-INFO.json` `eigen-version: 3.4.0` give those versions. The compiler is conda-forge GCC 14.4.0.

Each build shell sources `toolchain/buildenv/env.sh`. It puts the env first on `PATH`, sets `CC`/`CXX`
to the conda compilers and an rpath to `env/lib`, and clears `CFLAGS`/`CXXFLAGS`. This keeps conda's
default optimisation flags out of the build.

## 2. nextpnr (openXC7/nextpnr, himbaechel xilinx uarch)

`ce3f7c18` is in `upstream/openXC7_nextpnr`, not in `upstream/openXC7_nextpnr-xilinx`
(`git cat-file -t ce3f7c18` fails there). The nightly's recipe is
`cavearr/toolchain-openxc7-releases` @ `7796f727`, `nix/nextpnr-xilinx.nix`:

- `-DARCH=himbaechel -DHIMBAECHEL_UARCH=xilinx -DHIMBAECHEL_XILINX_DEVICES=`, with no device built into the binary;
- `BUILD_PYTHON=OFF`, `BUILD_GUI=OFF`, `BUILD_TESTS=OFF`;
- "ZERO local patches";
- it installs `nextpnr-himbaechel` as `bin/nextpnr-xilinx`.

The cmake flags below are taken from that recipe:

```bash
cd ~/open-dfx-xc7
R=upstream/openXC7_nextpnr
git -C $R worktree add --detach $PWD/build/src/nextpnr-stock ce3f7c18
git -C $R worktree add -b pblock-xdc-build    $PWD/build/src/nextpnr-pblock pblock-xdc
git -C $R worktree add -b router-region-build $PWD/build/src/nextpnr-router router-region
source toolchain/buildenv/env.sh
for v in stock pblock router; do
  cmake -S build/src/nextpnr-$v -B build/nextpnr-build/$v -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCURRENT_GIT_VERSION=$(git -C build/src/nextpnr-$v rev-parse --short=8 HEAD) \
    -DARCH=himbaechel -DHIMBAECHEL_UARCH=xilinx -DHIMBAECHEL_XILINX_DEVICES= \
    -DHIMBAECHEL_PRJXRAY_DB=$PWD/toolchain/openxc7/share/nextpnr/external/prjxray-db \
    -DBUILD_GUI=OFF -DBUILD_TESTS=OFF -DBUILD_PYTHON=OFF \
    -DPython3_EXECUTABLE=$BUILDENV_PREFIX/bin/python3.12 -Wno-deprecated
  ninja -C build/nextpnr-build/$v nextpnr-himbaechel
done
ninja -C build/nextpnr-build/stock bbasm
```

The stock build took 1m21s wall time with `-j12`. Each of the three builds prints exactly one compiler warning,
the pre-existing `xilinx.cc:1240` `-Wsign-compare`. The patches add no warnings or errors.

### chipdb

The binary has no chipdb built in. Pass the nightly's chipdb with `--chipdb`:
`toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin` (sha256 `ee4ff400…`).

- **How the nightly made it:** `pack/chipdb.py` and `.github/workflows/chipdb.yml` in the same repo and commit. It runs `python3.12 <nextpnr src>/himbaechel/uarch/xilinx/gen/xilinx_gen.py --xray <prjxray-db>/artix7 --device xc7a50t --bba …`, then `bbasm --le`.
- **Compatible:** the chipdb comes from the same nextpnr source (ce3f7c18) as our binaries. Neither draft patch touches `gen/` or `constids.inc` (`git diff --stat ce3f7c18 router-region`).
- **Regenerated and compared:** `toolchain/buildenv/gen_chipdb.sh` (DRY_RUN=1 by default, cached in `build/chipdb/`) does the same two steps. It uses the generator of `build/src/nextpnr-stock`, `nextpnr-xilinx-meta` at `8a3f5a09` (the submodule pin of ce3f7c18), the toolchain's prjxray-db and our `bbasm`. Its output is **byte-identical** to the nightly's `chipdb-xc7a50t.bin` (`cmp`, run 2026-11-05).

```bash
DRY_RUN=0 bash toolchain/buildenv/gen_chipdb.sh
```

## 3. Running a design with another nextpnr

`flow/build_openxc7.py` has four new options. Without them the defaults and commands are unchanged.

| Option | Effect |
|---|---|
| `--nextpnr PATH` | binary to use instead of `toolchain/openxc7/bin/nextpnr-xilinx` |
| `--chipdb PATH` | passed to nextpnr as `--chipdb` |
| `--out DIR` | output directory |
| `--nextpnr-arg=ARG` | extra raw nextpnr argument (repeatable) |

When `--nextpnr` or `--chipdb` is given, `versions.json` records the binary and its `--version`.

```bash
python3 flow/build_openxc7.py rv_soc --json build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.json \
  --nextpnr build/nextpnr-build/stock/nextpnr-himbaechel \
  --chipdb toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin \
  --out build/patched/baseline/rv_soc_stock --run
```

## 4. openFPGALoader

`v1.2.0` = `befbab4f` matches the oss-cad-suite binary (`openFPGALoader --Version` prints v1.2.0).

```bash
R=upstream/trabucayre_openFPGALoader
git -C $R worktree add --detach $PWD/build/src/ofl-stock v1.2.0
git -C $R worktree add -b partial-load-build $PWD/build/src/ofl-partial partial-load
git -C build/src/ofl-partial apply ~/open-dfx-xc7/docs/drafts/openfpgaloader-partial-fix1.diff
source toolchain/buildenv/env.sh
for v in stock partial; do
  cmake -S build/src/ofl-$v -B build/ofl-build/$v -G Ninja -DCMAKE_BUILD_TYPE=Release -DENABLE_UDEV=OFF -DENABLE_LIBGPIOD=OFF
  ninja -C build/ofl-build/$v
done
```

- `ENABLE_UDEV` and `ENABLE_LIBGPIOD` are off because the env has no libudev or libgpiod.
- cmake reports "hidapi-libusb not found: cmsis_dap v1 support disabled". conda-forge's hidapi did not provide the pkg-config name it looks for. The XVC client, remote-bitbang and FTDI cables are built.
- Both builds print 0 warnings.
- `fix1.diff` is left uncommitted in the worktree. The `git apply` line is needed only on a fresh worktree.

## 5. What runs where

| Path | Content |
|---|---|
| `toolchain/buildenv/` | micromamba, env, package cache, `env.sh`, `VERSIONS.txt`, `env-explicit.txt`, `gen_chipdb.sh` |
| `build/src/` | git worktrees (nextpnr stock/pblock/router, openFPGALoader stock/partial) |
| `build/nextpnr-build/`, `build/ofl-build/` | build trees and binaries |
| `build/chipdb/` | regenerated chipdb and the `nextpnr-xilinx-meta` clone |
| `build/patched/` | experiments: baseline, native PR flow, openFPGALoader virtual-cable traces |

## 6. Reproducing the tests

```bash
cd ~/open-dfx-xc7
DB=toolchain/openxc7/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin
J=build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.json
python3 flow/build_openxc7.py rv_soc --json $J --nextpnr build/nextpnr-build/stock/nextpnr-himbaechel --chipdb $DB --out build/patched/baseline/rv_soc_stock --run
python3 flow/build_openxc7.py rv_soc --json $J --out build/patched/baseline/rv_soc_nightly --run
cmp build/patched/baseline/rv_soc_{stock,nightly}/rv_soc.fasm
python3 flow/build_pr_native.py --rms xor andn add rot popc minmax --timing-allow-fail popc minmax --run
python3 flow/build_pr_native.py --variant router_nokeepout --run
python3 flow/build_pr_native.py --variant pblock --run
DRY_RUN=0 bash flow/ofl_virtual_test.sh
```

### Baseline results (2026-11-05)

Stock ce3f7c18 built here, compared with the nightly `toolchain/openxc7/bin/nextpnr-xilinx` (same JSON, seed 1):

| design | FASM | .frames | routed JSON | .bit |
|---|---|---|---|---|
| blinky (526 FASM lines) | identical | identical | identical | identical from the sync word on; the 213/215-byte header differs only in the embedded `.frames` path |
| rv_soc (40,319 FASM lines) | identical | identical | identical | (not compared; frames identical) |

The nightly rerun of rv_soc also reproduces the earlier `build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.fasm` byte for byte.

## 7. Gap-fix variants (2026-11-05)

`toolchain/buildenv/build_nextpnr_variant.sh` (DRY_RUN=1 by default) makes a detached worktree
`build/src/nextpnr-<VARIANT>` at ce3f7c18, applies the listed drafts from `docs/drafts/` (uncommitted),
and builds `build/nextpnr-build/<VARIANT>` with the cmake flags of section 2. It refuses `stock`,
`router` and `pblock`. `CURRENT_GIT_VERSION` is `ce3f7c18-<VARIANT>`, so `--version` and the first FASM
comment line name the variant.

```bash
DRY_RUN=0 VARIANT=dsp     PATCHES=nextpnr-dsp-mask-areg.patch       bash toolchain/buildenv/build_nextpnr_variant.sh
DRY_RUN=0 VARIANT=iserdes PATCHES=nextpnr-iserdes-const-pins.patch  bash toolchain/buildenv/build_nextpnr_variant.sh
DRY_RUN=0 VARIANT=muxf7   PATCHES=nextpnr-muxf7-mixed-loads.patch   bash toolchain/buildenv/build_nextpnr_variant.sh
DRY_RUN=0 VARIANT=gapfix  PATCHES="nextpnr-dsp-mask-areg.patch nextpnr-iserdes-const-pins.patch nextpnr-muxf7-mixed-loads.patch"   bash toolchain/buildenv/build_nextpnr_variant.sh
```

Each build prints only the pre-existing `xilinx.cc:1240` warning (build/nextpnr-build/<VARIANT>.build.log).

`ofx-prim` (2026-11-06) is the 11-patch `ofx` series plus the seven primitive drafts of docs/drafts/nextpnr-prim-gaps.md
(command there; `DRY_RUN=0 bash toolchain/buildenv/check_prim_series.sh` checks the series against the worktree).
`ofx-prim-xadc` adds docs/drafts/nextpnr-xadc.patch and needs its own chipdb:

```bash
python3 flow/prim_xadc_meta.py --run      # meta copy build/chipdb-prim/meta + site_type_XADC.json
OUT=build/chipdb-prim META=build/chipdb-prim/meta SRC=build/src/nextpnr-ofx-prim DRY_RUN=0 bash toolchain/buildenv/gen_chipdb.sh
python3 flow/prim_db.py --run             # build/prjxray-db-prim: toolchain db + DIFF_TERM/FIFO/ICAP drafts
python3 flow/prim_db.py --out build/prjxray-db-prim-xadc --run \
  --extra docs/drafts/prjxray-db-xadc-init.segbits docs/drafts/prjxray-db-monitor-bot.ppips
```

`flow/gap_build.py` takes `tools["db"]` (prjxray-db root for fasm2frames/xc7frames2bit) and `flow/bit2fasm.py` takes
`--db-root`; without them both use the toolchain's database as before.
The iserdes worktree was patched once more after its first build (CLKDIVP); the patch file in
docs/drafts is the final state.

yosys: `upstream/YosysHQ_yosys` is a blob-less clone of github.com/YosysHQ/yosys, worktree
`build/src/yosys-clkbuf` at 3718f7f13 with the clkbufmap draft. A full yosys build needs flex and bison.
`micromamba install bison flex` (conda-forge) failed twice on TLS resets while fetching repodata
(build/buildenv_bison_flex.log); the env was not changed. The patched pass is instead built as a plugin
against the oss-cad-suite headers:

```bash
DRY_RUN=0 bash toolchain/buildenv/build_yosys_plugin.sh   # -> build/yosys-plugin/clkbufmap_gapfix.so
```

`flow/gap_build.py --yosys-plugin SO --clkbuf-pass clkbufmap_gapfix` then runs synth_xilinx up to
`finalize`, the plugin pass, `clean`, and synth_xilinx from `check`. With the stock `clkbufmap` in the
same split the JSON is byte-identical to the normal flow (14 designs, build/gap/<d>/ystock/).
