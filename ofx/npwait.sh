#!/usr/bin/env bash
if [ "$1" != "--version" ]; then
  while [ "$(pgrep -c nextpnr)" -ge "${OFX_MAX_NEXTPNR:-2}" ]; do sleep 20; done
fi
exec "$OFX_NEXTPNR_BIN" "$@"
