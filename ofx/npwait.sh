#!/usr/bin/env bash
np_count() {
  { pgrep -x 'nextpnr-.*'; pgrep -f 'ld-linux[^ ]* .*bin/nextpn[r]'; } 2>/dev/null | sort -u | wc -l
}
if [ "$1" != "--version" ]; then
  w0=$(date +%s)
  while [ "$(np_count)" -ge "${OFX_MAX_NEXTPNR:-6}" ]; do sleep 20; done
  [ -n "$OFX_NPWAIT_LOG" ] && echo "waited $(( $(date +%s) - w0 ))" >> "$OFX_NPWAIT_LOG"
fi
exec "$OFX_NEXTPNR_BIN" "$@"
