#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
W=/mnt/c/Users/finnf/open-dfx-xc7-vivado/ip
LOG=build/ofx/gt/queue.log
mkdir -p build/ofx/gt
steps=("$@")
[ ${#steps[@]} -eq 0 ] && steps=(wizard gtp_b3 pcie_ip fuzz gtp_nv gtp_lbm)
design() {
  mkdir -p "$W/$1/designs/$2"
  cp "examples/$2/src/$3.v" "examples/$2/constraints/$3.xdc" "$W/$1/designs/$2/"
  flow/vivado_polite.sh vivado/build_gtp.tcl "$1" @designs @out "$2:$3:$4" >> "$LOG" 2>&1
}
for s in "${steps[@]}"; do
  echo "$(date +%T) $s" >> "$LOG"
  case $s in
    wizard) flow/vivado_polite.sh vivado/gtp_wizard.tcl gtp @out >> "$LOG" 2>&1 ;;
    pcie_ip) flow/vivado_polite.sh vivado/pcie_ip.tcl pcie @out >> "$LOG" 2>&1 ;;
    gtp_b3) design gtpb gtp_b3 gtp_b3 xc7a35tcpg236-1 ;;
    gtp_nv) design gtpn gtp_nv gtp_nv xc7a200tsbg484-1 ;;
    gtp_lbm) design gtpl gtp_lbm gtp_lbm xc7a35tcpg236-1 ;;
    fuzz)
      python3 flow/gt_fuzz_gtgrefclk.py "$W/gtpf/designs" >> "$LOG"
      for f in fz_gref_base fz_gref_inv0 fz_gref_inv1 fz_gref_g0 fz_gref_g1; do
        flow/vivado_polite.sh vivado/build_gtp.tcl gtpf @designs "@out_$f" "$f:$f:xc7a35tcpg236-1" >> "$LOG" 2>&1
      done ;;
    *) echo "unknown step $s" >> "$LOG" ;;
  esac
done
echo "$(date +%T) end" >> "$LOG"
