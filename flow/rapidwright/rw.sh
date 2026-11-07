#!/usr/bin/env bash
set -e
R=$(cd "$(dirname "$0")/../.." && pwd)
T=$R/toolchain/rapidwright
export RAPIDWRIGHT_PATH=$T
JAVA="$T/jdk/bin/java -Xmx${RW_XMX:-3g} -XX:-OmitStackTraceInFastThrow"
CP=$T/rapidwright.jar:$R/build/rapidwright/classes
waitmem() { until [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -ge 4 ]; do sleep 30; done; }
cmd=$1; shift
case $cmd in
  build)  mkdir -p $R/build/rapidwright/classes
          $T/jdk/bin/javac -nowarn -cp $T/rapidwright.jar -d $R/build/rapidwright/classes $R/flow/rapidwright/*.java ;;
  xdcp)   waitmem; mkdir -p "$(dirname "$2")"; $JAVA -cp $CP XrouteDcp "$@" ;;
  export) waitmem; $JAVA -cp $CP DcpExport "$@" ;;
  jython) waitmem; $JAVA -jar $T/rapidwright.jar "$@" ;;
  *) echo "usage: rw.sh build|xdcp|export|jython" >&2; exit 2 ;;
esac
