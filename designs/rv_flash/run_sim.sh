#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../.."
export PATH=$PWD/toolchain/oss-cad-suite/bin:$PATH
D=designs/rv_flash
B=build/rv_flash/sim
PARTIAL=${PARTIAL:-build/partials/rv_pr/rm_andn_from_xor.bin}
SPI_DIV=${SPI_DIV:-2}
mkdir -p $B
python3 flow/rvasm.py $D/fw/main.s -o $D/fw/main.hex --lst $B/main.lst
python3 flow/flash_image.py --slot 0=$PARTIAL --slot 2=$PARTIAL --out $B/slots \
  --sim-hex $B/flash_window.hex --sim-words $B/slot0_words.hex --sim-corrupt 2
sed -n '/^module rm_bridge /,/^endmodule/p' designs/rv_soc/rv_soc.v > $B/rm_bridge_rv_soc.v
iverilog -g2005 -DOLD -o $B/tb_bridge_old.vvp -s tb_bridge $B/rm_bridge_rv_soc.v $D/tb/rm_lat.v $D/tb/tb_bridge.v
vvp -n $B/tb_bridge_old.vvp | tee $B/tb_bridge_old.log
iverilog -g2005 -o $B/tb_bridge_new.vvp -s tb_bridge $D/rm_bridge_fenced.v $D/tb/rm_lat.v $D/tb/tb_bridge.v
vvp -n $B/tb_bridge_new.vvp | tee $B/tb_bridge_new.log
RTL="designs/common/dfx_decoupler.v $D/rv_flash.v $D/rm_bridge_fenced.v $D/spi_master.v $D/uart.v $D/picorv32.v $D/tb/icape2_rec.v $D/tb/spiflash_model.v"
iverilog -g2005 -DSPI_DIV=$SPI_DIV -o $B/tb_rv_flash.vvp -s tb_rv_flash $RTL designs/rv_soc/sim/rm_add.v $D/tb/tb_rv_flash.v
vvp -n $B/tb_rv_flash.vvp | tee $B/tb_rv_flash.log
python3 $D/tb/check_icap.py $B/icap_words_s0.hex $PARTIAL | tee $B/check_icap.log
grep -h -E "^(PASS|FAIL|REPRODUCED|NOT REPRODUCED)" $B/tb_bridge_old.log $B/tb_bridge_new.log $B/tb_rv_flash.log
grep -q IDENTICAL $B/check_icap.log
