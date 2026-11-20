# open-dfx-xc7

> **This is still a work in progress!** It hasn't run on a real board yet - everything is only checked on my
> computer for now. Stuff will change.

You know how Vivado lets you swap out one piece of your FPGA design while the rest keeps running? (they call it
DFX) I wanted to do that without Vivado. So this is that, made out of the open-source tools: Yosys, nextpnr and
Project X-Ray.

Yeah - Vivado is still on my computer. But I only use it to check my bitstreams against its own, it never builds
anything here.

- made for the Digilent Arty A7-35T (XC7A35T-CSG324-1)
- the demo is a little RISC-V computer (PicoRV32) that swaps out its own custom-instruction hardware while it's
  running (over UART, or from the SPI flash)
- the partial bitstreams get compared against the ones Vivado makes
- no vendor IDE anywhere in the flow!

`PROGRESS.md` has where things are at right now.

To try it you have to build the tools first. It takes a while, but you don't need root and it all goes in
`~/.local/ofx`:

```bash
bash install/install.sh --run
```

After that it works pretty much like a Vivado project. You write one project file (`ofx.toml`) with your top
module, sources, XDC, board, clocks and the parts you want to swap, and then it's just one command:

```
bin/ofx new arty-a7-35t myproj [--dfx]   # skeleton project (board presets in boards/)
bin/ofx build --run                       # synth -> place and route -> bitstream
bin/ofx report / bin/ofx timing           # utilisation and Fmax
bin/ofx program [--flash]                 # openFPGALoader (dry run unless --run)
bin/ofx dfx build --run                   # native DFX flow, pr_check, partials with safety records
bin/ofx dfx verify --run                  # DRC, pr_check, records, byteman, region2v
bin/ofx dfx load <partial> [--via jtag]   # ICAP UART loader or openFPGALoader --partial (dry run unless --run)
```

Most of these only tell you what they would do until you add `--run`. If you don't pick a device you get the Arty
A7-35T. The bigger Arty (A7-100T, xc7a100t) builds too, but that one is also only checked on my computer so far.
Everything `ofx` can do is in `docs/ofx.md`.

The install builds a bunch of stuff: nextpnr (openXC7, with my patches on top), the Project X-Ray tools and
database, the chipdbs, byteman, openFPGALoader with `--partial`, and yosys, all from pinned versions. If it breaks,
look at `docs/install.md`. The tools themselves aren't in the repo (`toolchain/`, `build/` and `upstream/` are
git-ignored), and `docs/buildenv.md` has the exact versions.

Here's what's in the repo:

| Where | What it has |
|-|-|
| `PROGRESS.md` | where things are at and what I've actually verified |
| `docs/dfx-vs-vivado.md` | Vivado DFX feature by feature: what this can do, what it can't yet, and the proof |
| `docs/hardware-test-plan.md` | the plan for the first time it goes on the board, step by step, with what I expect to see and when to stop |
| `docs/phase*.md` | the details, one file per phase |
| `docs/drafts/` | my patches for nextpnr, openFPGALoader, prjxray-db and yosys. I haven't sent any of them upstream yet. `docs/drafts/README.md` lists them |
| `flow/` | the actual tools. `build_pr_native.py` is the normal flow (it needs the patched nextpnr), `build_pr.py` works with stock nextpnr, `partial.py` writes the partials, and `full_check.sh` / `full_check_native.sh` run all the checks |
| `designs/` | test designs, plus the ones I build in Vivado to compare against |
| `vivado/` | the Tcl and PowerShell that build those Vivado bitstreams |
