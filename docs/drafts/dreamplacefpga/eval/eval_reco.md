- **Adopt as an external option: no.**
  - It is not better on Vivado's timer.
  - It costs 70-145 s of CPU per placement against a few seconds for our global placer.
  - It drags a PyTorch-1.8 / Python-3.8 / CUDA<12 stack (no GPU support for current cards) into the toolchain.
  - It still needs nextpnr to legalise.
- **Port DREAMPlaceFPGA: no.**
  - Our placer_static.cc is already the same family: ePlace/elfPlace-style electrostatics with Nesterov.
  - The parts that would matter for 7-series are its packer-legaliser and detailed placer. Those would have to be
    rewritten anyway: slice = 4 LUT6 + 8 FF, one CE/SR per slice, CARRY4 columns, LUTRAM/SRL in SLICEM, F7/F8.
  - That is about 3-5 weeks for a 7-series DL (direct legalisation) in DREAMPlaceFPGA's C++/CUDA, before any
    evidence that it beats nextpnr's.
- **Drop it as a placer, keep the bridge as a measurement tool** (docs/drafts/nextpnr-placer-gp-exchange.patch,
  flow/dpf_*.py). It is opt-in and no-op when off: `.frames` identical on rv_soc seeds 1-3.
  - `--placer-static-gp-dump` / `--placer-static-gp-import[-warm]` / `--placer-static-gp-out` let any external
    global placer be tried against nextpnr's legaliser in under a day.
  - flow/dpf_gpcmp.py compares global placements in one metric.
- **What this says about our own placer:**
  1. **The global placement is not the main loss on the CPUs, the legalisation/packing step is.**
     - A GP with 21-30 % less wirelength and Vivado's flat shape gives no Fmax after nextpnr's strict legaliser.
     - The cold import loses 40-50 % HPWL in legalisation, against +17 % for our own GP (rv_soc s1).
     - Next lever: a packing-aware legaliser, elfPlace/DREAMPlaceFPGA-style direct legalisation (DL) for 7-series
       slices. It would cluster LUT/FF/carry by GP position and control set before site assignment, instead of
       nextpnr's greedy cell-by-cell strict legalisation. Effort about 2-3 weeks in xilinx_place.cc / placer_static.cc.
     - This fits Finding 15's packing work (dp4, carry-di-bypass).
  2. **Do not let block RAMs spread vertically.** bram shows what scattered RAMs cost (-11 %).
     Our `static-ram-assign` draft goes the other way and is the right direction.
  3. **The flat shape alone does not explain the Vivado gap.** rv_soc warm and td_warm have Vivado-like shape in GP,
     but the final Fmax stays about 100 MHz against Vivado's 136/149. This agrees with Finding 15/17: the remaining
     gap is in the detailed packing/legalisation and the delay model, not the global shape.
- **Effort spent:** about 1 working day, including the environment, two upstream fixes, the bridge, 45 nextpnr runs
  and @@NVIV@@ Vivado runs.
  - About half of the Vivado time was waiting for slots: other queues held slot 1 back to back, and the coordinator's
    priority windows applied.
