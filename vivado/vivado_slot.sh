#!/usr/bin/env bash
_viv_mkdir() { (cd /mnt/c && MSYS_NO_PATHCONV=1 cmd.exe /c "mkdir C:\\Users\\finnf\\${1}" >/dev/null 2>&1); }
_viv_rmdir() { (cd /mnt/c && MSYS_NO_PATHCONV=1 cmd.exe /c "rmdir C:\\Users\\finnf\\${1}" >/dev/null 2>&1); }
win_avail_mb() { (cd /mnt/c && timeout 30 powershell.exe -NoProfile -Command "[int](Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue" 2>/dev/null | tr -d '\r'); }
vivado_acquire() {
  while true; do
    a=$(win_avail_mb)
    if { [ -z "$a" ] || [ "$a" -ge 1500 ]; } && _viv_mkdir vivado.lock; then VIV_HELD=vivado.lock; break; fi
    if [ -n "$a" ] && [ "$a" -ge 3500 ] && _viv_mkdir vivado.lock2; then VIV_HELD=vivado.lock2; break; fi
    if [ -n "$a" ] && [ "$a" -ge 5000 ] && _viv_mkdir vivado.lock3; then VIV_HELD=vivado.lock3; break; fi
    sleep 10
  done
  trap '_viv_rmdir "$VIV_HELD"' EXIT
}
vivado_acquire3() {
  while true; do
    a=$(win_avail_mb); if [ -n "$a" ] && [ "$a" -ge 5000 ] && _viv_mkdir vivado.lock3; then VIV_HELD=vivado.lock3; break; fi
    sleep 15
  done
  trap '_viv_rmdir "$VIV_HELD"' EXIT
}
vivado_release() { _viv_rmdir "$VIV_HELD"; trap - EXIT; sleep "${VIV_GAP_S:-45}"; }
