# ICAPE2 bit order: checked against UG470 (not yet on silicon)

## Source
UG470 v1.10 (June 24, 2015). The copy used is the mirror PDF saved at build/rv_flash/ref/ug470_v1.10_mirror.pdf; its text extract is build/rv_flash/ref/ug470.txt. The current v1.17 was not read.

What it says:
- **Chapter 5, "Parallel Bus Bit Order":** "The bit-swap rule also applies to 7 series FPGA BPI x8 modes and to the ICAPE2 interface … In 7 series devices, the bit-swap rule is extended to x16 and x32 bus widths, i.e., the data is bit swapped within each byte."
- **Same section:** the examples "illustrate what is expected at the FPGA data pins when using parallel configuration modes … and when using the ICAPE2 interface."
- **Table 5-5, sync word data sequence:** D[31:0] for x32 is **0x5599AA66**. The bitstream word is 0xAA995566.
- **Chapter 7, ICAPE2:** "The ICAPE2 interface is similar to the SelectMAP interface, including bit-swapping".

## Our implementation
- designs/pr_uart/uart_icap.v (SWAP=1) and designs/rv_soc/rv_soc.v (and rv_flash) apply `bswap(w)[i] = w[(i & ~7) + (7 - (i & 7))]`. That reverses the bits within each byte and keeps the byte positions.
- Computed (run): bswap(0xAA995566) = 0x5599AA66. This equals Table 5-5.
- The same function is applied to ICAP readback data (O bus), on the assumption that the output bus uses the same ordering. That part of the text was not checked.

## Status
- The write path matches the documented ICAPE2 bit order.
- Still unverified on silicon. The IDCODE readback step (docs/phase3-open-swap.md, step 2) is the hardware check: expect 0x0362D093.
