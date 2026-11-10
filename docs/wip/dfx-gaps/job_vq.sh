cd ~/open-dfx-xc7
WIN=/mnt/c/Users/finnf/open-dfx-xc7-vivado
VIV='C:\AMDDesignTools\2025.2\Vivado\bin\vivado.bat'
W=C:/Users/finnf/open-dfx-xc7-vivado
export VIV_SLOT=3
source vivado/vivado_slot.sh
take() { vivado_acquire; echo "$(date) acquired $VIV_HELD" >> $log; }
give() { vivado_release; sleep 90; }
log=build/dfxgaps/vq.log
echo "$(date) start" >> $log
for n in dsp_um_none dsp_um_multiply dsp_um_dynamic; do mkdir -p $WIN/designs/gap/$n; cp designs/gap/$n/* $WIN/designs/gap/$n/; done
cp vivado/build_gap.tcl $WIN/vivado/build_gap.tcl; mkdir -p $WIN/build/dspum
for n in dsp_um_none dsp_um_multiply dsp_um_dynamic; do
  [ -f $WIN/build/dspum/$n/status.txt ] && continue
  take
  cmd.exe /c "$VIV" -mode batch -nojournal -log "$W/build/dspum/vivado_$n.log" -source "$W/vivado/build_gap.tcl" -tclargs "$W/designs/gap" "$W/build/dspum" $n >> build/dfxgaps/vivado_dspum.out 2>&1
  echo "$(date) dspum $n exit $?" >> $log; give
done
cp vivado/build_dfx_dev.tcl $WIN/vivado/
for pd in xc7a50t:xc7a50tcsg324-1 xc7a100t:xc7a100tcsg324-1 xc7a200t:xc7a200tsbg484-1; do
  die=${pd%%:*}; part=${pd#*:}; n=dfx_dev_$die
  mkdir -p $WIN/designs/$n $WIN/build/$n
  cp designs/dfx_dev/top.v designs/dfx_dev/rm_xor.v designs/dfx_dev/rm_andn.v designs/dfx_dev/rm_stub.v designs/dfx_dev/pblock.xdc $WIN/designs/$n/
  cp designs/dfx_dev/$die.xdc $WIN/designs/$n/top.xdc
  [ -f $WIN/build/$n/DONE ] && continue
  take; t0=$(date +%s)
  cmd.exe /c "$VIV" -mode batch -nojournal -log "$W/build/$n/vivado.log" -source "$W/vivado/build_dfx_dev.tcl" -tclargs $n top "$W/designs/$n" "$W/designs/$n/top.xdc" "$W/build/$n" $part rm_xor,rm_andn > build/dfxgaps/vivado_$n.out 2>&1
  rc=$?; echo "$(date) $n exit $rc wall $(( $(date +%s)-t0 )) s" >> $log; [ $rc = 0 ] && touch $WIN/build/$n/DONE; give
done
mkdir -p $WIN/designs/dfx_xtime $WIN/build/dfx_xtime
cp -r build/dfxgaps/xtime/src/* $WIN/designs/dfx_xtime/; cp vivado/build_xtime.tcl $WIN/vivado/build_xtime.tcl
for d in ppt_xor_placed ppt_andn_placed ppt_add_placed ppt_rot_placed anc_xor_placed anc_andn_placed anc_add_placed anc_rot_placed ppt_xor_p5 ppt_andn_p5 ppt_add_p5 ppt_rot_p5 anc_xor_p5 anc_andn_p5 anc_add_p5 anc_rot_p5; do
  [ -f $WIN/build/dfx_xtime/$d/status.txt ] && continue
  take; t0=$(date +%s)
  cmd.exe /c "$VIV" -mode batch -nojournal -log "$W/build/dfx_xtime/vivado_$d.log" -source "$W/vivado/build_xtime.tcl" -tclargs "$W/designs/dfx_xtime" "$W/build/dfx_xtime" $d >> build/dfxgaps/vivado_xtime.out 2>&1
  echo "$(date) xtime $d exit $? wall $(( $(date +%s)-t0 )) s" >> $log; give
done
bash vivado/run_dfx_rv.sh dfx_rv_p10 10.0 > build/dfxgaps/vivado_dfx_rv_p10.out 2>&1; echo "$(date) dfx_rv_p10 done" >> $log; sleep 90
bash vivado/run_dfx_rv.sh dfx_rv_p5 5.0 > build/dfxgaps/vivado_dfx_rv_p5.out 2>&1; echo "$(date) dfx_rv_p5 done" >> $log
echo "$(date) end" >> $log
