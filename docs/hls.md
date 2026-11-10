# High-level synthesis: C to bitstream with Bambu

`ofx` turns C/C++ functions into Verilog with PandA-Bambu (Politecnico di Milano), the open counterpart of
Vitis HLS (static scheduling, FSM + datapath, C testbench co-simulation), and feeds the RTL into the normal
Yosys / nextpnr-xilinx / Project X-Ray build. Without an `[[hls]]` table in `ofx.toml` nothing changes
(checked: see "No-change check").

## Usage

```toml
[[hls]]
top = "isqrt"                # C function to synthesize; also the Verilog module name
sources = ["c/isqrt.c"]      # C/C++ sources (relative to ofx.toml)
testbench = "c/tb.c"         # optional: a C main() that calls top and returns 0 on success
clock_ns = 10.0              # optional: default the fastest [clocks] period, else 10 ns
device = "xc7a100t-1csg324"  # optional: Bambu device model (default per family, see below)
args = ["-O3"]               # optional: extra Bambu options
include = ["c"]              # optional: include directories
```

```
ofx hls [--sim] [--run]      # Bambu for every [[hls]] kernel into build/hls/<top>/; --sim co-simulates the C testbench
ofx build --run              # runs the hls step first (cached), then synth/P&R/bitstream as usual
```

- Several `[[hls]]` tables may be given. The RTL of a kernel is `build/hls/<top>/<top>_<hash>.v`; the hash covers the
  C sources, the include directories, the options and the Bambu binary, so a change re-runs Bambu and the build,
  and an unchanged kernel is skipped. The generated file is part of the build's input digest like any source.
- Bambu names its library modules generically (`register_STD`, `ADD_EXPR_FU`, ...). ofx prefixes every module but
  the top with `<top>__`, so several kernels (or a kernel and user RTL) can share a design. The user's Verilog
  instantiates the kernel under its C name.
- ofx always passes `--top-fname`, `--clock-period`, `--device-name` and `--generate-interface=INFER` (the
  interface follows the function signature and `#pragma HLS interface`, as in Vitis HLS: arrays become
  `ap_memory`-style ports `<arg>_address0/_ce0/_we0/_d0/_q0`, scalars plain inputs, the return value
  `return_port`); everything else is Bambu's default. Control ports: `clock`, `reset` (active low), `start_port`
  (pulse), `done_port` (pulse when the result is valid).
- `ofx hls --sim` runs `bambu --generate-tb=<testbench> --simulate --simulator=VERILATOR` (Verilator from the
  toolchain's oss-cad-suite): the testbench's `main()` runs natively, each call of the top function is replayed on the
  generated RTL and its outputs are compared; the simulated cycle count is printed.
- Default Bambu device model by family: artix7 and spartan7 `xc7a100t-1csg324`, zynq7 `xc7z020-1clg484`, kintex7
  `xc7z045-2ffg900`. Bambu has no xc7a35t model; the -1 Artix-7 delay model is the same die family and speed grade.
  The device model only steers Bambu's scheduling and operator choice; the bitstream is for the project's part.
- `OFX_BAMBU=/path/to/bambu` overrides the Bambu binary (default `toolchain/bambu/install/bin/bambu`).

`examples/hls_isqrt` goes from C to a bitstream for the Arty A7-35T: `isqrt()` in C (bit-by-bit integer square
root), a Verilog top that starts it about six times a second on a counter and shows the low four result bits on
the LEDs. `ofx hls --sim --run` checks it against `c/tb.c`; `ofx build --run` makes the bitstream.

## Bambu vs Vitis HLS

### Method

- Kernels: `designs/hls/<kernel>/` — `fir` (128 samples, 16 constant taps, `short` in, `int` out), `matmul`
  (16x16 `short`, `int` result), `crc32` (256 bytes, bitwise, 8 steps per byte), `hist` (256 bytes into 16 bins,
  read-modify-write), `dotprod` (256 `short` pairs). Plain C, no pragmas, the same source for both tools; each has a
  self-checking `tb.c` (`main()` returns the error count; all pass natively, in Vitis csim and cosim).
- Both tools at 10 ns, defaults otherwise. Vitis HLS 2025.2: part xc7a35tcsg324-1, `csim_design`, `csynth_design`,
  `cosim_design -rtl verilog` (`flow/hls_vitis.sh`, one `vitis-run --mode hls --tcl` process in a Vivado slot).
  Bambu 2026.11: device model xc7a100t-1csg324, `--generate-interface=INFER`, co-simulation of the same `tb.c` in
  Verilator (`flow/hls_compare.py bambu`).
- Equal terms: each tool's RTL goes into the same generated wrapper (`flow/hls_compare.py`): every kernel input bit
  comes from a shift register fed by one pin, every output bit is XORed into a second shift register that drives one
  pin. All kernel ports become register-to-register paths and any kernel fits the package. The array ports
  (`ap_memory`-style address/ce/we/d/q) are left as ports, so no memory is counted for the tools' interfaces.
- Implementation of the wrapped design, xc7a35tcsg324-1, 10 ns clock:
  - ofx: `ofx build --run` (yosys `synth_xilinx`, nextpnr-xilinx, bitstream). Resources are the kernel alone through
    the same `synth_xilinx -flatten -abc9` (+ `-noiopad -noclkbuf`), counted per cell type. Fmax is nextpnr's
    ("Max frequency for clock"), and also Vivado's timer on our placement (`flow/hls_xtime.sh`: the yosys netlist
    with every cell fixed where nextpnr put it, routed by Vivado, `report_timing_summary`; the xtime method of
    docs/timing-reports.md).
  - Vivado 2025.2: `synth_design` (the kernel instance kept as a hierarchy), `opt/place/phys_opt/route_design`
    (`flow/hls_vivado.sh`, one Vivado process in a slot). Resources are the kernel instance's primitives per cell
    type; Fmax = 1000 / (10 - WNS).
- Fmax at a 10 ns target is the slack-derived figure both tools report; neither placer works harder once 10 ns is
  met, so differences of 10-20 % between runs are noise, not quality. LUT counts are LUT cells (Vivado's "Total LUTs"
  counts LUT sites and is lower when two LUT5s share a site); BRAM36 counts RAMB18 as 0.5; LUTRAM and SRL are not in
  the LUT column.

### Results

Latency is from co-simulation of the C testbench (Vitis: cosim, with the csynth estimate in brackets; Bambu:
Verilator co-simulation in Bambu's testbench), for one call of the kernel.

TABLE_PLACEHOLDER

What Vitis HLS did without pragmas (csynth report): it pipelines loops by itself. `fir`: inner tap loop unrolled,
outer loop pipelined, II 8 (two reads per cycle from the 2-port `x` memory, 16 taps); `matmul`: `k` unrolled,
`i`/`j` flattened and pipelined, II 8; `crc32`: bit loop unrolled, byte loop II 2; `dotprod`: II 1; `hist`: the
read-modify-write on `bins` keeps it sequential.

### What Bambu supports, compared with Vitis HLS

| Vitis HLS feature | Bambu 2026.11 |
|---|---|
| automatic loop pipelining (default in Vitis HLS) | not by default: loop iterations run one after the other (FSM over basic blocks, operation chaining inside a block) |
| `#pragma HLS pipeline` on a loop | no ("Loop pipelining pragma not supported"); a loop body moved into a function can be pipelined |
| `#pragma HLS pipeline` on a function, `II=` | yes (`--pipelining=func[=II]` or the pragma at function scope) |
| `#pragma HLS unroll` | yes |
| `#pragma HLS inline` | yes (and `--inline-fname`) |
| `#pragma HLS interface` | yes: `ap_none`, `ap_vld`, `ap_ovld`, `ap_ack`, `ap_hs`, `ap_fifo`, `ap_memory`/`bram` (`array`), `m_axi`, `axis`; no `s_axilite` (Bambu has `--memory-mapped-top` instead) |
| `#pragma HLS array_partition` | yes |
| `#pragma HLS dataflow` | yes (task-level, with `hls::stream` / `ac_channel` FIFOs) |
| `#pragma HLS cache` (m_axi cache) | yes |
| `array_reshape`, `bind_op`, `bind_storage`, `allocation`, `latency`, `loop_tripcount`, `loop_flatten`, `loop_merge`, `dependence`, `stable`, `stream depth` and the `config_*` commands | no pragma; partly as options (`--channels-type`, `--memory-allocation-policy`, `--DSP-allocation-coefficient`, `--distram-threshold`) |
| `ap_int`/`ap_fixed`, `hls::stream` | `ac_int`/`ac_fixed` (Algorithmic C types) and `ac_channel`; `hls::stream` is accepted |
| floating point | yes (soft-float library or custom formats, `--fp-format`), no DSP-based FP cores |
| C/RTL co-simulation | yes: the same C `main()` testbench, Verilator, XSim, Modelsim or VCS |
| export to IP catalog / `export_design -flow impl` | no; ofx consumes the Verilog directly, and `ofx build` is the implementation |

## Bambu install

Built from source (no unsigned binaries): `install/bambu.sh`.

| item | value |
|---|---|
| source | https://github.com/ferrandi/PandA-bambu, tag `2026.11` (latest release, 2026-11-04) |
| commit | `cda4db2e724df357f749c0c41b12bdc065462ced` (checked: `git rev-parse HEAD` and the remote tag ref) |
| submodules (pinned by the tag's gitlinks) | ext/abseil/abseil-cpp 9ac7062b, ext/mockturtle/mockturtle 25beb0e2, ext/pugixml 27b68329, ext/buddy 678ac672, ext/gcem 012ae73c (v1.18.0), ext/glaze 2dfb3555, etc/ac_types 684c510a, etc/ac_math d49214e1 |
| licence | Apache-2.0 with LLVM exceptions (LICENSE, LICENSES/) |
| build | out of tree, `toolchain/bambu/{src,build,install}`, CMake Release, eucalyptus off, -j4, nice 10 |
| Ubuntu packages (26.04, Ubuntu's own repositories) | `sudo apt-get install -y cmake ninja-build bison flex libboost-dev zlib1g-dev clang-19 llvm-19 llvm-19-dev libclang-19-dev gcc-multilib g++-multilib` |

Why each package: cmake/ninja-build (Bambu 2026.11 builds with CMake), bison/flex (required by `src/CMakeLists.txt`),
libboost-dev (headers, at least 1.70) and zlib1g-dev (required by the top-level CMakeLists), clang-19, llvm-19,
llvm-19-dev, libclang-19-dev (Bambu's C/C++ front end is a clang plugin; 2026.11 accepts clang below 20),
gcc-multilib/g++-multilib (the 32-bit headers Bambu's I386 compiler targets use). Verilator for co-simulation
comes from the toolchain's oss-cad-suite.

Not used: the AppImage `https://release.bambuhls.eu/bambu-2024.10.AppImage` linked from the 2024.10 GitHub release
(no checksum or signature published; its AppImage signature section is empty), and there is no binary for 2026.11.

## Dynamatic (not installed)

Dynamatic (EPFL-LAP, dynamically scheduled, elastic dataflow circuits) has tagged releases on GitHub
(`dynamatic-v2.0.0`, 2024-03) but no binaries. A build compiles its pinned Polygeist/LLVM/MLIR/CIRCT tree from
source: tens of GB of disk for the LLVM build tree and many hours at -j4, with several GB of RAM per link job, plus
Ubuntu packages along the lines of clang, lld, cmake, ninja-build, libboost-dev, graphviz, a MILP solver
(coinor-cbc, or a Gurobi licence for its buffer placement) and a VHDL/Verilog simulator. It was left out here for
disk (C: holds the WSL disk) and memory; it would need a machine or WSL disk with about 100 GB to spare.

## No-change check

Projects without `[[hls]]` take no new code path (`stage.py` calls the hls step only when `ofx.toml` has an `hls`
key; `project.py` and the build commands are unchanged). Checked by building copies of `examples/axi_xbar` and
`examples/vhdl_blinky` with `ofx build --run` before and after the change: `.frames` and `.fasm` are byte-identical
(sha256 below); the `.bit` files differ only in the header, which holds the `.frames` path and the build date and
time.

| example | file | sha256 (before = after) |
|---|---|---|
| axi_xbar | axi_xbar.frames | 1d7697903b93ed528b62f23bad33d671bed9d9131b20e630cd9a8d44bc1988b5 |
| axi_xbar | axi_xbar.fasm | dc6b21bbbcef74b7ea0c64bb586abeea11ed51c495eaeba4eaac230df22356de |
| vhdl_blinky | vhdl_blinky.frames | 83d494c5b819f9981dcf5ed05d260c656fcb8b5495eb4a1a1be59f374290cc60 |
| vhdl_blinky | vhdl_blinky.fasm | 88926bb55f9bd8db41bbed688e1f861bd59333cae0115ee3342ad951d0fb1a79 |

## Notes and limits

- Vitis HLS 2025.2 from WSL: csynth stopped with "Dataflow strict check failed" (the dataflow checker exits with an
  error and no message, on kernels without any dataflow); `config_dataflow -strict_mode off` avoids it
  (`HLS_DF_STRICT=off flow/hls_vitis.sh ...`).
- nextpnr's timer is optimistic against Vivado's on the same placement (fir 186 vs 132 MHz, crc32 309 vs 193 MHz):
  the timer and route-delay gap of docs/timing-reports.md, not something HLS-specific. Compare the "Vivado timer"
  column with Vivado's own implementation.
