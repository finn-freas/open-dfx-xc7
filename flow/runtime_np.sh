#!/usr/bin/env bash
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$1" = "--version" ]; then exec "$here/../ofx/npwait.sh" "$@"; fi
while [ "$(pgrep -c nextpnr)" -ge "${OFX_MAX_NEXTPNR:-2}" ]; do sleep 5; done
t0=$(python3 -c 'import time; print(time.time())')
set -o pipefail
/usr/bin/time -o "${RT_TIME:-/dev/null}" -f "%e %U %S %M" "$here/../ofx/npwait.sh" "$@" 2>&1 | python3 "$here/runtime_ts.py" "${RT_TS:-/dev/null}" "$t0"
