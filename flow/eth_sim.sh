#!/bin/bash
ROOT=$HOME/open-dfx-xc7
LX=$ROOT/toolchain/litex
DRY_RUN=${DRY_RUN:-1}
OUT=${OUT:-$ROOT/build/eth/sim/litex_sim_eth}
JOBS=${JOBS:-4}
SIM_ARGS=${SIM_ARGS:-"--cpu-type vexriscv --with-ethernet --with-etherbone --with-analyzer --non-interactive"}
EB_IP=${EB_IP:-192.168.1.51}
MAC_IP=${MAC_IP:-192.168.1.50}
BOOT_WAIT_S=${BOOT_WAIT_S:-1800}
SIM_TIMEOUT_S=${SIM_TIMEOUT_S:-3600}
SYSROOT=$LX/sysroot/usr
ZROOT=$ROOT/toolchain/buildenv/env
MAX_NEXTPNR=2

export PATH=$LX/venv/bin:$LX/riscv/usr/bin:$ROOT/toolchain/oss-cad-suite/bin:$PATH
export CFLAGS="-I$SYSROOT/include -I$ZROOT/include"
export LDFLAGS="-L$SYSROOT/lib/x86_64-linux-gnu -Wl,-rpath,$SYSROOT/lib/x86_64-linux-gnu -L$ZROOT/lib -Wl,-rpath,$ZROOT/lib"
export LD_LIBRARY_PATH=$SYSROOT/lib/x86_64-linux-gnu

log() { echo "[$(date -Is)] $*" | tee -a $OUT/run.log; }

inner() {
  ip link set lo up
  mkdir -p $OUT/shim
  cat > $OUT/shim/sudo <<'EOS'
#!/bin/sh
while [ "$#" -gt 0 ] && [ "${1#-}" != "$1" ]; do shift; done
exec "$@"
EOS
  chmod +x $OUT/shim/sudo
  export PATH=$OUT/shim:$PATH
  cd $OUT
  log "netns: $(readlink /proc/self/ns/net), uid $(id -u)"
  log "start litex_sim $SIM_ARGS"
  rm -f $OUT/ping_*.log $OUT/*.vcd $OUT/analyzer.csv
  timeout $SIM_TIMEOUT_S python3 $ROOT/flow/eth_sim_soc.py $SIM_ARGS --jobs $JOBS --output-dir $OUT/build --csr-csv $OUT/csr.csv \
    < /dev/null > $OUT/litex_sim.log 2>&1 &
  SIM=$!
  t0=$(date +%s)
  until ip -4 addr show tap0 2>/dev/null | grep -q inet; do
    kill -0 $SIM 2>/dev/null || { log "litex_sim exited before tap0 came up"; return 1; }
    [ $(( $(date +%s) - t0 )) -gt $BOOT_WAIT_S ] && { log "tap0 timeout"; kill $SIM; return 1; }
    sleep 5
  done
  log "tap0 up: $(ip -4 -br addr show tap0)"
  ok=0
  for i in $(seq 1 60); do
    if ping -c 1 -W 20 $EB_IP >> $OUT/ping_etherbone.log 2>&1; then ok=1; break; fi
  done
  log "ping etherbone $EB_IP: $([ $ok = 1 ] && echo replied || echo no-reply)"
  ping -c 3 -W 20 $EB_IP >> $OUT/ping_etherbone.log 2>&1
  log "ping summary: $(grep -a 'packets transmitted' $OUT/ping_etherbone.log | tail -n 1)"
  litex_server --udp --udp-ip $EB_IP > $OUT/litex_server.log 2>&1 &
  SRV=$!
  sleep 5
  timeout 600 litex_cli --ident > $OUT/litex_cli_ident.log 2>&1
  log "litex_cli --ident rc $?: $(tr -d '\0' < $OUT/litex_cli_ident.log | tail -n 1)"
  timeout 900 litex_cli --regs > $OUT/litex_cli_regs.log 2>&1
  log "litex_cli --regs rc $?: $(grep -c '0x' $OUT/litex_cli_regs.log) lines"
  timeout 1200 litescope_cli --csv $OUT/analyzer.csv --csr-csv $OUT/csr.csv --length 128 --offset 16 \
    --dump $OUT/scope_immediate.vcd > $OUT/litescope_immediate.log 2>&1
  log "litescope_cli immediate rc $?: $(tail -n 2 $OUT/litescope_immediate.log | tr '\n' ' ')"
  TRIG=$(grep -m1 -E '^signal,0,.*dbus_stb,' $OUT/analyzer.csv | cut -d, -f3)
  timeout 1200 litescope_cli --csv $OUT/analyzer.csv --csr-csv $OUT/csr.csv --length 128 --offset 16 \
    -r $TRIG --timeout 900 --dump $OUT/scope_rising_dbus_stb.vcd > $OUT/litescope_trigger.log 2>&1
  log "litescope_cli -r $TRIG rc $?: $(tail -n 2 $OUT/litescope_trigger.log | tr '\n' ' ')"
  timeout 1200 litescope_cli --csv $OUT/analyzer.csv --csr-csv $OUT/csr.csv --length 128 --offset 16 \
    -r $TRIG --json --dump $OUT/scope_json.vcd > $OUT/litescope_json.log 2>&1
  log "litescope_cli --json rc $?"
  ping -c 3 -W 20 $MAC_IP > $OUT/ping_ethmac.log 2>&1
  log "ping ethmac/BIOS $MAC_IP: $(grep -a 'packets transmitted' $OUT/ping_ethmac.log)"
  kill $SRV $SIM 2>/dev/null
  wait
  log "done"
}

if [ "$1" = "--inner" ]; then
  inner
  exit $?
fi
if [ "$DRY_RUN" = 1 ]; then
  echo "[dry] unshare -r -n $0 --inner: litex_sim $SIM_ARGS in a private network namespace, then ping $EB_IP,"
  echo "      litex_server --udp, litex_cli --ident/--regs, litescope_cli captures; logs in $OUT. DRY_RUN=0 to run"
  exit 0
fi
while [ "$(pgrep -c nextpnr)" -ge $MAX_NEXTPNR ]; do sleep 30; done
mkdir -p $OUT
: > $OUT/run.log
unshare -r -n bash "$0" --inner
