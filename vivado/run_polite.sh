#!/usr/bin/env bash
label=$1; shift
others() {
  pgrep -af 'vivado.loc[k]|run_runtim[e]|run_qo[r]|run_df[x]|run_vivad[o]|run_ga[p]|run_xdc[.]ps1|run_device[s]|run_ddr[3]' \
    | grep -v -e "run_polite" -e "^$$ " -e "^$PPID " | grep -q .
}
while others; do sleep 300; done
source "$(dirname "$0")/vivado_slot.sh"
vivado_acquire
trap 'vivado_release' INT TERM
echo "$label start $(date +%T)"
"$@" < /dev/null
echo "$label end $(date +%T) rc=$?"
