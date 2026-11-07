# WIP: GTP / PCIe workstream (agent state, paused 2026-11-07 00:35)

Done and committed: see docs/gtp.md sections 1-4 and 7 (audit, nextpnr default findings, pcie_bare equal to Vivado,
flow-side UNISIM defaults in build_openxc7, gtp_b3/gtp_lbm/gtp_nv/pcie_bare open builds with 0 unknown bits).

Not run (no Vivado slot in ~2.5 h; my queued jobs were stopped before taking the lock, nothing of mine is running):
- `flow/gt_vivado_queue.sh` (all steps): wizard sources, gtp_b3, pcie_ip, fuzz (5 specimens), gtp_nv, gtp_lbm.

Next, once Vivado is free:
1. `flow/gt_vivado_queue.sh`
2. `python3 flow/gt_compare.py <part> examples/<d>/build/impl/<d>.bit /mnt/c/Users/finnf/open-dfx-xc7-vivado/ip/<sub>/out/<d>/<d>.bit build/ofx/gt/cmp_<d>`
   for gtp_b3 (gtpb), gtp_nv (gtpn, xc7a200tsbg484-1), gtp_lbm (gtpl).
3. `python3 examples/gtp_lb/gen_top.py /mnt/c/Users/finnf/open-dfx-xc7-vivado/ip/gtp/out`, build gtp_lb in both flows, compare.
4. fuzz: decode fz_gref_* bitstreams (gtpf/out_fz_*), diff -> IS_GTGREFCLK0/1_INVERTED, GTGREFCLK1_USED bits.
5. pcie_7x sources (ip/pcie/out/src) through the open flow and Vivado (stretch).
