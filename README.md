# open-dfx-xc7

Partial reconfiguration for Xilinx 7-series FPGAs, without Vivado. Vivado calls this DFX: you swap out one part of
the design while the rest of it keeps running. I wanted that with only the open-source tools (Yosys, nextpnr and
Project X-Ray), so I built the flow for it.

Vivado is still on my machine, but only to check my bitstreams against its own. It's never used to build anything.

Nothing here has run on a real board yet - everything is checked offline for now. Still being worked on!

- made for the Digilent Arty A7-35T (XC7A35T-CSG324-1)
- the demo is a little RISC-V computer (PicoRV32) that swaps its own custom-instruction hardware while it's
  running, from UART or from SPI flash
- the partial bitstreams are compared against Vivado's
- no vendor IDE anywhere in the flow

`PROGRESS.md` has where things are at right now.

## Running it

First build the tools. This takes a while, but it doesn't need root and it puts everything in `~/.local/ofx`:

```bash
bash install/install.sh --run
```

Then it works a lot like a Vivado project. There's one project file (`ofx.toml`) with your top module, sources,
XDC, board, clocks and the parts you want to swap, and one command:

```
bin/ofx new arty-a7-35t myproj [--dfx]   # skeleton project (board presets in boards/)
bin/ofx build --run                       # synth -> place and route -> bitstream
bin/ofx report / bin/ofx timing           # utilisation and Fmax
bin/ofx program [--flash]                 # openFPGALoader (dry run unless --run)
bin/ofx dfx build --run                   # native DFX flow, pr_check, partials with safety records
bin/ofx dfx verify --run                  # DRC, pr_check, records, byteman, region2v
bin/ofx dfx load <partial> [--via jtag]   # ICAP UART loader or openFPGALoader --partial (dry run unless --run)
```

Most commands only print what they would do until you add `--run`. If you don't pick a device you get the Arty
A7-35T. The xc7a100t (Arty A7-100T) builds too, also only offline so far. Everything `ofx` can do is in
`docs/ofx.md`.

The install builds nextpnr (openXC7, with my patches), the Project X-Ray tools and database, the chipdbs, byteman,
openFPGALoader with `--partial`, and yosys, all from pinned versions. If it breaks, look at `docs/install.md`. The
tools themselves aren't in the repo (`toolchain/`, `build/` and `upstream/` are git-ignored), and
`docs/buildenv.md` lists the exact versions.

## What's in here

| Where | What it has |
|-|-|
| `PROGRESS.md` | where things are at and what's been verified |
| `docs/dfx-vs-vivado.md` | Vivado DFX feature by feature: what this can do, what it can't, and the proof |
| `docs/hardware-test-plan.md` | the plan for the first time it goes on the board, step by step, with what to expect and when to stop |
| `docs/phase*.md` | the details, one file per phase |
| `docs/drafts/` | my patches for nextpnr, openFPGALoader, prjxray-db and yosys. None of them have been sent upstream yet. `docs/drafts/README.md` lists them |
| `flow/` | the actual tools. `build_pr_native.py` is the normal flow (needs the patched nextpnr), `build_pr.py` works with stock nextpnr, `partial.py` writes the partials, and `full_check.sh` / `full_check_native.sh` run all the checks |
| `designs/` | test designs, plus the ones I build in Vivado to compare against |
| `vivado/` | the Tcl and PowerShell that build those Vivado bitstreams |
