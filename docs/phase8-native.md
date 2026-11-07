# Phase 8: confinement inside nextpnr (native flow), now the default

Offline work, 2026-11-05. Nothing here has run on hardware.

## Why
The external flow (flow/build_pr.py) confines a reconfigurable module with:
- input-less blocker LUTs;
- pinned placement (rm_place, packer_pins);
- an external region router (region_route).

The static design is still routed freely in the first build, and then replayed. On rv_pr, 545 static nets used the region's tiles, so a dense RM (rot) could not route (docs/phase7-regions.md).

The external fix, flow/static_detour.py, produced route loops that hung nextpnr, so it is experimental and not used.

## What
The patched nextpnr is ce3f7c18 plus the drafts docs/drafts/nextpnr-pblock-xdc.patch and nextpnr-router-region.patch. It is built with toolchain/buildenv; see docs/buildenv.md.

- The stock build from source is identical to the openXC7 nightly (frames and chipdb byte-identical).
- Without a pblock, both patched binaries give frames identical to stock.

The driver is flow/build_pr_native.py:
- pblock with EXCLUDE_PLACEMENT and CONTAIN_ROUTING;
- `--router2-region-keep-out`;
- an RM shell with anchors but no blockers;
- no rm_place, packer_pins, region_route or static_detour.

## Results on rv_pr (region SLICE_X12Y100:SLICE_X15Y149), verified by run
Each variant was built once with one seed, measured by flow/region_pips.py and flow/pr_check.py.

| variant | static pips in region / nets | RM pips outside region | pr_check |
|---|---|---|---|
| router + keep-out (default) | 0 / 0 in all 7 builds | 0 | static identical outside the region, 15/15 RM pairs (xor, andn, add, rot, popc, minmax) |
| router, no keep-out | 958 / 402 | 0 | identical |
| pblock binary only | 953 / 412 | 25–26 | fails (33 frames outside differ) |
| external flow, rv_pr_xor_c | 955 / 434 | 0 | identical |

Other results:
- **rot:** routes in 2.97 s of router2 time. In the external flow it stopped at iteration 39,064.
- **Timing:**
  - popc misses 100 MHz at 99.45 MHz, so it was built with timing failure allowed (`_taf`).
  - The first build reaches 141.16 MHz, against 160 MHz for the external flow. The critical path is in the static PicoRV32. With one seed, it is not established whether keep-out costs Fmax in general.

## Verification of native builds (flow/native_check.sh, complete run)
Run: `FORMAL_SKIP_RMS=popc FORMAL_MEM_KB=3000000 flow/native_check.sh`, log build/native_check_final.log. Result: **42 PASS, 0 FAIL**, exit 0.

- **Full builds (6):** region2v decodes the region's bits into a netlist and simulates 3582 vectors against the RTL, plus a Yosys SAT proof with a 600 s, 3 GB limit.
  - rot, add, andn, minmax, xor: simulated and PROVED.
  - popc: simulated only. The proof of a 32-bit popcount did not finish in 600 s in an earlier run, so it is skipped here.
  - 6 BRAM-init lines are PASS (no BRAM in these RMs).
- **Partials (30, every target × base pair):** each one passes:
  - the region gate and CRC;
  - an exact simulated load;
  - byteman applied to the base, equal to the ORIGINAL target in all 5408 frames (the frames byteman omits are kept from the base);
  - region2v on the byteman result.
- An earlier run had 6 partials fail. They ran while partial.py was mid-edit by the Phase 10 work (`build()` returned 6 values and `main()` still expected 5). It was a crash, not a wrong bitstream. All 6 pass in this run.

## Other tools built
- openFPGALoader v1.2.0 plus docs/drafts/openfpgaloader-partial.patch, and fix1.
  - On a virtual XVC TAP (flow/xvc_trace.py), `--partial` sends only CFG_IN with the 59,272-byte partial, then 2000 TCK, TLR and BYPASS. Without the flag the sequence is JPROGRAM … CFG_IN … JSTART.
  - Not run on hardware.

## Status of the flows
- **Default:** the native flow. It needs the patched nextpnr, which is not upstream (drafts only, nothing posted).
- **Fallback:** the external flow with stock openXC7 (flow/build_pr.py). It is verified for rv_pr, rv_b, rv_c and rv_flash with xor/andn/add. Dense RMs such as rot may fail to route.

## Reproducibility (2026-11-05 evening)
- flow/native_rebuild_compare.sh rebuilt rv_pr, rv_b, rv_c, rv2 and rv_m from scratch into build/patched/fresh with the current code, then compared every bitstream frame for frame with the verified builds: **26/26 identical**, 0 differing, 0 missing (log build/fresh.out). The native flow is deterministic, and the verified bitstreams are what the current code produces.
