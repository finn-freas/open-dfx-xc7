cd ~/open-dfx-xc7
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado/ip
mkdir -p $W/ff $W/fb1 $W/fb2
cp designs/ip/fifo_configs.txt $W/ff/
grep -E '^(b01|b02|b03|b04) ' designs/ip/bram_configs.txt > $W/fb1/bram_configs.txt
grep -E '^(b05|b06|b07) ' designs/ip/bram_configs.txt > $W/fb2/bram_configs.txt
export OFX_VIVADO_PRIORITY=low
flow/ip_vivado.sh --run vivado/ip_clk_ref.tcl clk @clk_requests.txt @out
flow/ip_vivado.sh --run vivado/ip_fb_ref.tcl ff @fifo_configs.txt - - @out
flow/ip_vivado.sh --run vivado/ip_fb_ref.tcl fb1 - @bram_configs.txt $(wslpath -m $W/fb/bsrc) @out
flow/ip_vivado.sh --run vivado/ip_fb_ref.tcl fb2 - @bram_configs.txt $(wslpath -m $W/fb/bsrc) @out
echo ALL_DONE
