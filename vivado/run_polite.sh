#!/usr/bin/env bash
label=$1; shift
lock=/mnt/c/Users/finnf/vivado.lock
others() {
  pgrep -af 'vivado.loc[k]|run_runtim[e]|run_qo[r]|run_df[x]|run_vivad[o]|run_ga[p]|run_xdc[.]ps1|run_device[s]|run_ddr[3]' \
    | grep -v -e "run_polite" -e "^$$ " -e "^$PPID " | grep -q .
}
while true; do
  if ! tasklist.exe 2>/dev/null < /dev/null | grep -qi '^vivado.exe' && [ ! -d $lock ]; then
    if others; then sleep 300; continue; fi
    if mkdir $lock 2>/dev/null; then break; fi
  fi
  sleep 30
done
trap 'rmdir $lock 2>/dev/null' EXIT INT TERM
echo "$label start $(date +%T)"
"$@" < /dev/null
echo "$label end $(date +%T) rc=$?"
