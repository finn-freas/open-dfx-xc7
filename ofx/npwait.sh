#!/usr/bin/env bash
np_count() {
  { pgrep -x 'nextpnr-.*'; pgrep -f 'ld-linux[^ ]* .*bin/nextpn[r]'; } 2>/dev/null | sort -u | wc -l
}
if [ "$1" != "--version" ]; then
  while [ "$(np_count)" -ge "${OFX_MAX_NEXTPNR:-2}" ]; do sleep 20; done
fi
exec "$OFX_NEXTPNR_BIN" "$@"
