# WIP: Vivado IP wizards (clk/fifo/bram) + ILA debug (`ofx ip`, `ofx debug`)

Results so far: docs/ip.md; roadmap rows updated (db62882); CLI in docs/ofx.md (1ecbf3d).

## Done (verified, committed)
- ofx debug insert/capture (examples/dbg_ila builds to a bitstream; dbg_ila + dbg_rtl simulated captures PASS).
- ofx ip bram: 7 configs read back 0 mismatches (unisims); 7 open-flow bitstreams built (build/ip_compare/bram_bits).
- ofx ip clk: 26/26 requests simulate correctly with Vivado unisims.
- CLI `ofx ip clk|fifo|bram|gen`, `ofx debug insert|capture`; `[[ip.*]]` and `[debug]` in ofx.toml via ofx/stage.py.

## Vivado references NOT yet made (queue stopped 2026-11-07 after ~2.5 h waiting behind placer/router Vivado jobs)
Restart: `bash flow/ip_vivado_queue.sh` (4 batches, each < 20 min, OFX_VIVADO_PRIORITY=low, lock released between).
- Also done meanwhile: `ip_compare.py fifo-self`: 10 FIFOs scoreboarded with unisims, 0 mismatches (95f0b26).
- clk refs -> C:\Users\finnf\open-dfx-xc7-vivado\ip\clk\out ; then `python3 flow/ip_compare.py clk --run`
  (param/frequency compare + Vivado clk_wiz sim); tune ip_clk.rank() to Vivado's choices if they differ.
- fifo refs -> ip\ff\out\fifo ; then set CONFIG vivado_fb to ...\ff\out (fifo) and run `ip_compare.py fifo --run`,
  iterate ofx/ip_fifo.py until cycle-exact (builtin: compare cell params in <n>.cells).
- bram refs -> ip\fb1\out\bram, ip\fb2\out\bram ; then `ip_compare.py bram-bits --run` (open bits cached).
  NOTE: ip_compare CONFIG vivado_fb points at ip/fb/out: adjust paths to ff/fb1/fb2.

## Then
- Fill docs/ip.md + roadmap rows with the Vivado comparisons; final report.
