cd ~/open-dfx-xc7
export OFX_MAX_NEXTPNR=2
for s in 1 3; do
  until [ "$(free -m | awk '/Mem:/{print $7}')" -ge 4000 ]; do sleep 30; done
  start=$(date +%s); python3 ofx/_native_run.py docs/wip/dfx-gaps/ppt_seed${s}_nofix_job.json > build/dfxgaps/ppt_seed${s}_nofix.out 2>&1; echo "exit $? wall $(( $(date +%s)-start )) s" >> build/dfxgaps/ppt_seed${s}_nofix.out
done
