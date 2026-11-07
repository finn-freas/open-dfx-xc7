#!/usr/bin/env bash
PART="${PART:-${OFX_PART:-xc7a35tcsg324-1}}"
FAMILY="${FAMILY:-${OFX_FAMILY:-artix7}}"
OUT="${OUT:-build/b2n}"
VENV="${VENV:-toolchain/fasm2bels/venv}"
F2B_SRC="${F2B_SRC:-toolchain/fasm2bels/src}"
PRJXRAY_WT="${PRJXRAY_WT:-build/src/prjxray-a5589d51}"
PRJXRAY_CLONE="${PRJXRAY_CLONE:-upstream/openXC7_prjxray}"
PRJXRAY_REV="${PRJXRAY_REV:-a5589d51}"
OXC7="${OXC7:-toolchain/openxc7}"
TOOLS="${TOOLS:-toolchain/oss-cad-suite}"
DB_ROOT="${DB_ROOT:-$OXC7/share/nextpnr/external/prjxray-db/$FAMILY}"
CONN_DB="${CONN_DB:-$OUT/conn_$PART.db}"
ICAP_SITES="${ICAP_SITES-ICAP_X0Y0}"
ORPHAN_OK="${ORPHAN_OK-/BRAM_(CLK[01]_[04]|(FIFO18|FIFO36|RAMB18)_REGCLK(ARDRCLK|B)[LU]?)\)$}"
SIM_TB="${SIM_TB:-designs/rv_soc/tb/b2n_tb_rv_soc.v}"
SIM_TOP="${SIM_TOP:-b2n_tb_rv_soc}"
SIM_PRIMS="${SIM_PRIMS:-designs/rv_soc/tb/b2n_ramb36e1.v designs/rv_soc/tb/icape2_model.v}"
SIM_BRAM_CORE_SRC="${SIM_BRAM_CORE_SRC:-designs/rv_soc/tb/gl_ramb36e1.v}"
NVEC="${NVEC:-11}"
JOBS="${JOBS:-6}"
FULL_DIR="${FULL_DIR:-build/openxc7/rv_soc}"
FULL_RMS="${FULL_RMS-xor andn add}"
BM_DIR="${BM_DIR:-build/byteman_check}"
NEG="${NEG-rv_pr_xor_c:andn rv_pr_andn_c:add}"
STUBS="rr_graph rr_graph.capnp rr_graph.capnp.graph2 fpga_interchange fpga_interchange.interchange_capnp fpga_interchange.logical_netlist fpga_interchange.physical_netlist"
declare -A DTOP=([rv_soc]=rv_soc [rv_flash]=rv_flash [pr_uart]=top [qor_rv_soc]=qor_rv_soc [qor_rv_mul]=qor_rv_mul [qor_rv_big]=qor_rv_big)
declare -A DXDC=([rv_soc]=designs/rv_soc/arty_a7_35t.xdc [rv_flash]=designs/rv_flash/arty_a7_35t.xdc [pr_uart]=designs/pr_uart/arty_a7_35t.xdc [qor_rv_soc]=designs/gap/qor_rv_soc/arty_a7_35t.xdc [qor_rv_mul]=designs/gap/qor_rv_mul/arty_a7_35t.xdc [qor_rv_big]=designs/qor/qor_rv_big/arty_a7_35t.xdc)
declare -A DSIM=([rv_soc]=1 [rv_flash]=1 [pr_uart]= [qor_rv_soc]=1 [qor_rv_mul]=1 [qor_rv_big]=1)

usage() {
  echo "usage: flow/bit2netlist.sh --setup"
  echo "       flow/bit2netlist.sh <name> <bitstream> <rv_soc|rv_flash|pr_uart> [rm|-] [pass|fail]"
  echo "       flow/bit2netlist.sh --batch"
  exit 2
}

cd "$(dirname "$0")/.."
ROOT=$PWD
PY=$ROOT/$VENV/bin/python
export PATH=$ROOT/$TOOLS/bin:$PATH
SIM_LIB=$OUT/cells_sim_b2n.v
BRAM_CORE=$OUT/b2n_ramb36e1_core.v

setup() {
  if [ ! -d "$PRJXRAY_WT" ]; then
    git -C "$PRJXRAY_CLONE" worktree add --detach "$ROOT/$PRJXRAY_WT" "$PRJXRAY_REV" || return 1
  fi
  [ -x "$PY" ] || python3 -m venv "$VENV" || return 1
  "$PY" -c 'import yaml, simplejson, intervaltree, progressbar, lxml, textx' 2>/dev/null \
    || "$PY" -m pip install --disable-pip-version-check -r "$VENV/b2n-requirements.txt" || return 1
  mkdir -p "$OUT/pylib"
  ln -sfn "$(readlink -f "$OXC7")/lib/python3.12/site-packages/fasm" "$OUT/pylib/fasm"
  local sp
  sp=$("$PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
  printf '%s\n' "$ROOT/$PRJXRAY_WT" "$ROOT/$OUT/pylib" "$ROOT/$F2B_SRC" > "$sp/b2n_local.pth"
  "$PY" -W ignore -c 'import prjxray, fasm; print("ok   prjxray", prjxray.__file__); print("ok   fasm", fasm.__file__)'
  echo "ok   prjxray rev $(git -C "$PRJXRAY_WT" rev-parse --short HEAD), fasm2bels rev $(git -C "$F2B_SRC" rev-parse --short HEAD)"
}

f2b() {
  "$PY" -W ignore - "$STUBS" "$@" <<'EOF'
import sys, types
def stub(n):
    m = types.ModuleType(n)
    def ga(a):
        if a.startswith("__"):
            raise AttributeError(a)
        def init(self, *x, **k):
            raise RuntimeError(n + "." + a + " is not installed")
        return type(a, (), {"__init__": init})
    m.__getattr__ = ga
    m.__path__ = []
    sys.modules[n] = m
for n in sys.argv[1].split():
    stub(n)
mode = sys.argv[2]
args = sys.argv[3:]
if mode == "db":
    from fasm2bels.database.create_channels import create_channels
    create_channels(args[0], args[1], args[2])
else:
    import os
    from fasm2bels.fasm2bels import main
    from fasm2bels.models.verilog_modeling import Module, Bel, Site
    icap_sites = os.environ.get("B2N_ICAP_SITES", "").split()
    orig_make_routes = Module.make_routes
    def add_icap(top):
        for tile_name in top.grid.tiles():
            gi = top.grid.gridinfo_at_tilename(tile_name)
            if gi.tile_type != "CFG_CENTER_MID":
                continue
            for site in top.db.get_tile_type(gi.tile_type).get_instance_sites(gi):
                if site.name not in icap_sites:
                    continue
                s = Site([], site=site, tile=tile_name)
                bel = Bel("ICAPE2")
                bel.set_bel("ICAP")
                bel.parameters["ICAP_WIDTH"] = '"X32"'
                for p in ("CLK", "CSIB", "RDWRB"):
                    s.add_sink(bel, p, p, bel.bel, p)
                for k in range(32):
                    s.add_sink(bel, "I[%d]" % k, "I%d" % k, bel.bel, "I%d" % k)
                    s.add_source(bel, "O[%d]" % k, "O%d" % k, bel.bel, "O%d" % k)
                s.add_bel(bel)
                top.add_site(s)
                print("b2n: added ICAPE2 at %s %s" % (tile_name, site.name))
    def make_routes(self, *a, **k):
        add_icap(self)
        return orig_make_routes(self, *a, **k)
    Module.make_routes = make_routes
    def find_source_from_sink(self, site, site_wire):
        sources = self.find_sources_from_sink(site, site_wire)
        assert len(sources) <= 1
        return next(iter(sources), None)
    Module.find_source_from_sink = find_source_from_sink
    sys.argv = ["fasm2bels"] + args
    main()
EOF
}

fill_fasm() {
  "$PY" -W ignore - "$@" <<'EOF'
import contextlib, subprocess, sys
sys.path.insert(0, "flow")
import bitparse, bit2fasm
bm, base, ref, out, bitread, work = sys.argv[1:7]
part = bitparse.Part()
pf = {k: bitparse.parse(k, part)["frames"] for k in {bm, base, ref}}
present = set(pf[bm])
fill = sorted(set(pf[base]) - present)
z = [0] * 101
bad = [f for f in fill if bitparse.without_ecc(pf[base].get(f, z)) != bitparse.without_ecc(pf[ref].get(f, z))]
if bad:
    print("FAIL fill: %d filled frames differ between base %s and reference %s, e.g. 0x%08x" % (len(bad), base, ref, bad[0]))
    sys.exit(1)
nz = [f for f in fill if any(bitparse.without_ecc(pf[base][f]))]
cols = sorted({((f >> 22) & 1, (f >> 17) & 31, (f >> 7) & 1023) for f in nz})
print("fill %d frames absent from %s taken from %s (%d non-zero, top/row/col %s); all equal to %s" % (len(fill), bm, base, len(nz), cols, ref))
part_yaml = bit2fasm.DB / bit2fasm.CONFIG["part"] / "part.yaml"
lines = {}
for k, name in ((bm, "bm"), (base, "base")):
    p = "%s/%s.bits" % (work, name)
    subprocess.run([bitread, "--part_file", str(part_yaml), "-o", p, "-z", "-y", k], check=True, stdout=subprocess.DEVNULL)
    lines[name] = open(p).read().split()
fs = set(fill)
merged = lines["bm"] + [l for l in lines["base"] if int(l[4:12], 16) in fs]
mp = "%s/merged.bits" % work
open(mp, "w").write("\n".join(merged) + "\n")
mod = bit2fasm.load_bit2fasm()
with open(out, "w") as f, contextlib.redirect_stdout(f):
    mod.bits_to_fasm(str(bit2fasm.DB), bit2fasm.CONFIG["part"], mp, False, False)
EOF
}

conn_db() {
  [ -f "$CONN_DB" ] && return 0
  mkdir -p "$(dirname "$CONN_DB")"
  echo "info building connection database $CONN_DB"
  rm -f "$CONN_DB.tmp"
  f2b db "$ROOT/$DB_ROOT" "$PART" "$ROOT/$CONN_DB.tmp" > "$CONN_DB.log" 2>&1 \
    || { echo "FAIL connection db ($CONN_DB.log)"; rm -f "$CONN_DB.tmp"; return 1; }
  mv "$CONN_DB.tmp" "$CONN_DB"
}

prep_sim() {
  local cells
  cells=$(yosys-config --datdir 2>/dev/null)/xilinx/cells_sim.v
  [ -f "$cells" ] || cells=$TOOLS/share/yosys/xilinx/cells_sim.v
  [ -f "$cells" ] || { echo "FAIL no cells_sim.v"; return 1; }
  mkdir -p "$OUT"
  sed -E 's/^module RAMB36E1 /module B2N_RAMB36E1_CORE /' "$SIM_BRAM_CORE_SRC" > "$BRAM_CORE"
  local over
  over=$(sed -nE 's/^module ([A-Za-z0-9_]+).*/\1/p' $SIM_PRIMS | paste -sd'|')
  awk -v re="^module ($over)[ (#]" '$0 ~ re {skip=1} !skip {print} skip && /^endmodule/ {skip=0}' "$cells" > "$SIM_LIB"
}

one() {
  local name=$1 bit=$2 design=$3 rm=${4:--} expect=${5:-pass} base=${6:-} ref=${7:-}
  local d=$OUT/$name top=${DTOP[$design]} xdc=${DXDC[$design]}
  [ -f "$bit" ] || { echo "FAIL $name: no bitstream $bit"; return 1; }
  [ -n "$top" ] || { echo "FAIL $name: unknown design $design"; return 1; }
  mkdir -p "$d"
  echo "info $name: $bit ($design, expect $rm, sha256 $(sha256sum "$bit" | cut -c1-16))"
  if [ ! -f "$d/design.fasm" ] || [ "$bit" -nt "$d/design.fasm" ] || { [ -n "$base" ] && ! grep -q "^fill " "$d/bit2fasm.log"; }; then
    rm -f "$d/design.fasm" "$d/design.v"
    if [ -n "$base" ]; then
      fill_fasm "$bit" "$base" "${ref:-$base}" "$d/design.fasm.tmp" "$ROOT/$OXC7/bin/bitread" "$d" > "$d/bit2fasm.log" 2>&1 \
        || { cat "$d/bit2fasm.log" | grep FAIL; echo "FAIL $name: fill/bit2fasm ($d/bit2fasm.log)"; return 1; }
    else
      "$PY" -W ignore flow/bit2fasm.py "$bit" "$d/design.fasm.tmp" > "$d/bit2fasm.log" 2>&1 \
        || { echo "FAIL $name: bit2fasm ($d/bit2fasm.log)"; return 1; }
    fi
    mv "$d/design.fasm.tmp" "$d/design.fasm"
  fi
  grep '^fill ' "$d/bit2fasm.log"
  echo "ok   $name fasm: $(grep -c . "$d/design.fasm") lines"
  if [ ! -f "$d/design.v" ] || [ "$d/design.fasm" -nt "$d/design.v" ]; then
    local a=(--connection_database "$ROOT/$CONN_DB" --db_root "$ROOT/$DB_ROOT" --part "$PART"
             --fasm_file "$ROOT/$d/design.fasm" --verilog_file "$ROOT/$d/design.v.tmp" --xdc_file "$ROOT/$d/design.xdc"
             --allow_orphan_sinks --top "$top" --input_xdc "$ROOT/$xdc")
    local t0=$SECONDS
    B2N_ICAP_SITES="$ICAP_SITES" f2b run "${a[@]}" > "$d/fasm2bels.log" 2>&1 \
      || { echo "FAIL $name: fasm2bels ($d/fasm2bels.log)"; return 1; }
    mv "$d/design.v.tmp" "$d/design.v"
    echo "info $name fasm2bels: $((SECONDS - t0)) s"
  fi
  local orph bad
  orph=$(grep -c '^// ERROR, failed to find source' "$d/fasm2bels.log")
  bad=$(grep '^// ERROR, failed to find source' "$d/fasm2bels.log" | grep -vE "$ORPHAN_OK")
  if [ -n "$bad" ]; then
    echo "$bad" | head -20
    echo "FAIL $name: $(echo "$bad" | wc -l) orphan sinks outside ORPHAN_OK ($d/fasm2bels.log)"
    return 1
  fi
  echo "ok   $name orphan sinks: $orph, all BRAM REGCLK (ORPHAN_OK)"
  echo "ok   $name verilog: $(grep -oE '^  [A-Z][A-Z0-9_]+ ' "$d/design.v" | sort | uniq -c | awk '{printf "%s%s=%s", s, $2, $1; s=" "}')"
  if [ "$rm" = "-" ] || [ -z "${DSIM[$design]}" ]; then
    echo "note $name: decode only, no simulation"
    return 0
  fi
  [ -f "$SIM_LIB" ] && [ -f "$BRAM_CORE" ] || prep_sim || return 1
  iverilog -g2012 -o "$d/sim.vvp" -s "$SIM_TOP" -DB2N_DUT="$top" "$d/design.v" "$SIM_LIB" $SIM_PRIMS "$BRAM_CORE" "$SIM_TB" > "$d/iverilog.log" 2>&1 \
    || { echo "FAIL $name: iverilog ($d/iverilog.log)"; return 1; }
  local t0=$SECONDS
  vvp -n "$d/sim.vvp" +RM="$rm" +TAG="$name" +NVEC="$NVEC" > "$d/sim.log" 2>&1
  grep -E '^GLSIM-UNSUPPORTED' "$d/sim.log" && { echo "FAIL $name: unsupported primitive configuration ($d/sim.log)"; return 1; }
  grep -E '^(PASS|FAIL|DONE) ' "$d/sim.log"
  echo "time $name: $((SECONDS - t0)) s"
  grep -q '^DONE ' "$d/sim.log" || { echo "FAIL $name: simulation did not finish ($d/sim.log)"; return 1; }
  local nf
  nf=$(grep -c '^FAIL ' "$d/sim.log")
  if [ "$expect" = "fail" ]; then
    if [ "$nf" -gt 0 ]; then echo "ok   $name: negative control failed as required ($nf FAIL lines)"; return 0; fi
    echo "FAIL $name: negative control passed"; return 1
  fi
  [ "$nf" -eq 0 ] && grep -q '^PASS ' "$d/sim.log"
}

orig_bit() {
  case "$1" in
    rv_pr|rv_b|rv_c) echo "build/openxc7/rv_soc/${1}_${2}_c/rv_soc.bit" ;;
    rv_flash) echo "build/openxc7/rv_flash/pr_${2}_c/rv_flash.bit" ;;
    pr_uart) echo "build/openxc7/pr_uart/pr_${2}_c/top.bit" ;;
  esac
}

infer() {
  local n=$1 design pfx rm src
  case "$n" in
    rv_flash_*) design=rv_flash; pfx=rv_flash ;;
    rv_pr_*|rv_b_*|rv_c_*) design=rv_soc; pfx=$(echo "$n" | cut -d_ -f1-2) ;;
    pr_uart_*) design=pr_uart; pfx=pr_uart ;;
    *) echo "SKIP $n: design not identifiable from name"; return 1 ;;
  esac
  local s=${n#${pfx}_}
  case "$s" in
    rm_*_from_*) rm=$(echo "$s" | sed -E 's/^rm_(.*)_from_(.*)$/\1/'); src=$(echo "$s" | sed -E 's/^rm_(.*)_from_(.*)$/\2/') ;;
    *_plus_*) rm=${s#*_plus_}; src=${s%%_plus_*} ;;
    *_rt) rm=${s%_rt}; src=$rm ;;
    *) echo "SKIP $n: RM not identifiable from name"; return 1 ;;
  esac
  echo "$design $rm $(orig_bit $pfx $src) $(orig_bit $pfx $rm)"
}

batch() {
  conn_db || return 1
  prep_sim || return 1
  local jobs=() n
  for rm in $FULL_RMS; do
    jobs+=("rv_pr_${rm}_c|$FULL_DIR/rv_pr_${rm}_c/rv_soc.bit|rv_soc|$rm|pass")
  done
  for b in "$BM_DIR"/*.bit; do
    n=$(basename "$b" .bit)
    local r
    r=$(infer "$n") || { echo "$r"; continue; }
    set -- $r
    jobs+=("bm_$n|$b|$1|$2|pass|$3|$4")
  done
  for x in $NEG; do
    local src=${x%%:*} wrong=${x##*:}
    jobs+=("neg_${src}_as_${wrong}|$FULL_DIR/$src/rv_soc.bit|rv_soc|$wrong|fail")
  done
  for j in "${jobs[@]}"; do
    IFS="|" read -r name bit design rm expect base ref <<< "$j"
    while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do wait -n; done
    ( one "$name" "$bit" "$design" "$rm" "$expect" "$base" "$ref" > "$OUT/$name.result" 2>&1; echo "rc=$?" >> "$OUT/$name.result" ) &
  done
  wait
  local fail=0 np=0 nf=0
  for j in "${jobs[@]}"; do
    IFS="|" read -r name bit design rm expect base ref <<< "$j"
    grep -vE '^rc=' "$OUT/$name.result"
    if grep -q '^rc=0$' "$OUT/$name.result"; then np=$((np + 1)); echo "RESULT ok   $name"
    else nf=$((nf + 1)); fail=1; echo "RESULT FAIL $name"; fi
  done
  echo "SUMMARY $np ok, $nf failed, of ${#jobs[@]}"
  return $fail
}

case "$1" in
  --setup) setup; exit $? ;;
  --batch) batch; exit $? ;;
esac
[ $# -ge 3 ] || usage
conn_db || exit 1
one "$@"
