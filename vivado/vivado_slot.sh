#!/usr/bin/env bash
_viv_mkdir() { MSYS_NO_PATHCONV=1 cmd.exe /c "mkdir C:\\Users\\finnf\\${1}" >/dev/null 2>&1; }
_viv_rmdir() { MSYS_NO_PATHCONV=1 cmd.exe /c "rmdir C:\\Users\\finnf\\${1}" >/dev/null 2>&1; }
win_avail_mb() { powershell.exe -NoProfile -Command "[int](Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue" 2>/dev/null | tr -d '\r'; }
vivado_acquire() {
  while true; do
    if _viv_mkdir vivado.lock; then VIV_HELD=vivado.lock; break; fi
    a=$(win_avail_mb); if [ -n "$a" ] && [ "$a" -ge 3500 ] && _viv_mkdir vivado.lock2; then VIV_HELD=vivado.lock2; break; fi
    sleep 30
  done
  trap '_viv_rmdir "$VIV_HELD"' EXIT
}
vivado_release() { _viv_rmdir "$VIV_HELD"; trap - EXIT; }
