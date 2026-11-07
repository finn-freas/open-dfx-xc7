# open-dfx-xc7

An open-source partial-reconfiguration flow, the equivalent of Vivado's DFX, for Xilinx 7-series FPGAs, built from Yosys, nextpnr (openXC7) and Project X-Ray. Vivado is used only as a reference to compare outputs against, never in the flow.

- Board: Digilent Arty A7-35T (XC7A35T-CSG324-1).
- Demo: a PicoRV32 RISC-V SoC that swaps its own custom-instruction hardware at runtime through ICAPE2, from UART or from SPI flash.

**Status:** everything is verified offline. **Nothing has run on hardware yet.** See `PROGRESS.md` for the current-status summary.

## Where to look
- `PROGRESS.md`: current status and verified results.
- `docs/dfx-vs-vivado.md`: feature-by-feature comparison with Vivado DFX, with evidence.
- `docs/hardware-test-plan.md`: the ordered board bring-up plan, with expected values and stop conditions.
- `docs/phase*.md`: details per phase.
- `docs/drafts/`: patches for nextpnr, openFPGALoader, prjxray-db and yosys. All are local drafts; nothing has been sent upstream. `docs/drafts/README.md` is the index.
- `flow/`: the tools.
  - `build_pr_native.py` is the default flow (patched nextpnr); `build_pr.py` is the stock-nextpnr fallback.
  - `partial.py` writes partials.
  - `full_check.sh` and `full_check_native.sh` run the regressions.
- `designs/`: test designs and Vivado reference designs.
- `vivado/`: Tcl and PowerShell for building the Vivado reference bitstreams.

## Project flow: `bin/ofx`
A Vivado-like project flow over the scripts in `flow/`: one project file (`ofx.toml`: top, sources, XDC, part or
board, clocks, DFX partitions with their RMs) and one command.

```
bin/ofx new arty-a7-35t myproj [--dfx]   # skeleton project (board presets in boards/)
bin/ofx build --run                       # synth -> place and route -> bitstream
bin/ofx report / bin/ofx timing           # utilisation and Fmax
bin/ofx program [--flash]                 # openFPGALoader (dry run unless --run)
bin/ofx dfx build --run                   # native DFX flow, pr_check, partials with safety records
bin/ofx dfx verify --run                  # DRC, pr_check, records, byteman, region2v
bin/ofx dfx load <partial> [--via jtag]   # ICAP UART loader or openFPGALoader --partial (dry run unless --run)
```

The device is a parameter (`flow/device.py`: part to family, fabric and chipdb). Defaults stay the Arty A7-35T.
Second device built offline with it: xc7a100t (Arty A7-100T). Reference and results: `docs/ofx.md`.

## Building
- **Install the toolchain:** `bash install/install.sh --run` builds the whole toolchain (openXC7 nextpnr with this project's patch series, Project X-Ray tools and database, chipdbs, byteman, openFPGALoader with `--partial`, yosys from the pinned oss-cad-suite) from pinned upstream sources into `~/.local/ofx`, without root. `docs/install.md` has the quickstart, the supported devices, every upstream project with its licence, and troubleshooting.
- The toolchain and build environment are not in the repo. `docs/buildenv.md` and `PROGRESS.md` list the exact pinned versions and how to reproduce them.
- `toolchain/`, `build/` and `upstream/` are git-ignored.
