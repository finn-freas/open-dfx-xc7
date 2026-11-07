#!/usr/bin/env bash
rep=${1:-1}; shift
names=${*:-"blinky rv_soc litex_ddr3 mc12_a100"}
lock=/mnt/c/Users/finnf/vivado.lock
ps1=$(wslpath -w "$(dirname "$(readlink -f "$0")")/run_runtime.ps1")
free_now() { [ ! -e $lock ] && ! tasklist.exe 2>/dev/null | grep -qi vivado.exe; }
for n in $names; do
  while :; do
    until free_now; do sleep 30; done
    sleep 300
    free_now && mkdir $lock 2>/dev/null && break
  done
  trap 'rmdir $lock 2>/dev/null' EXIT INT TERM
  echo "$n r$rep start $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg) nextpnr $(pgrep -c nextpnr)"
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ps1" -Names $n -Rep $rep -Run | tr -d '\r'
  echo "$n r$rep end $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg) nextpnr $(pgrep -c nextpnr)"
  rmdir $lock
  trap - EXIT INT TERM
done
