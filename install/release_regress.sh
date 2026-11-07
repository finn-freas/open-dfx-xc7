#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REPO:-$(cd "$HERE/.." && pwd)}"
PREFIX="${OFX_PREFIX:-$HOME/ofx-test/prefix}"
CACHE="${OFX_CACHE:-$HOME/ofx-test/cache}"
WORK="${WORK:-$HOME/ofx-test/regress}"
JOBS="${OFX_JOBS:-2}"
DEVICES="${OFX_DEVICES:-xc7a50t}"
STAGES="${STAGES:-install series noop defaults ofx cli smoke smoke_rvpr identity revalidate}"
CLI_FLAT="${CLI_FLAT:-blinky_a50 blinky_b3 blinky_cma7 vhdl_blinky vhdl_mixed}"
CLI_DFX="${CLI_DFX:-rv_pr dfx_a50 dfxpp_a50 dfx_vhdl}"
OFX_BOARD="${OFX_BOARD:-arty-a7-35t}"
REVAL_DESIGNS="${REVAL_DESIGNS:-rv_pr rv_b rv_c rv2 rv_ppa rv_ppt rv_m}"
NATIVE_DESIGNS="${NATIVE_DESIGNS:-rv_pr rv_b rv_c rv2 rv_ppa rv_ppt}"
NOOP_DESIGNS="${NOOP_DESIGNS:-blinky rv_soc rv_pp rv_ppa rv_ppt}"
IDENTITY="${IDENTITY:-blinky/stock rv_soc/stock}"
OLD_NPNR="${OLD_NPNR:-$REPO/build/nextpnr-build/ofx/nextpnr-himbaechel}"
ID_DESIGN="${ID_DESIGN:-rv_pr}"
ID_VARIANT="${ID_VARIANT:-router}"
ID_RMS="${ID_RMS:-xor andn}"
EXPECTED_FASM="${EXPECTED_FASM:-+CFG_CENTER_MID_X46Y32.ICAP.IN_USE}"
FORMAL_MEM_KB="${FORMAL_MEM_KB:-3000000}"
MAX_NEXTPNR="${OFX_MAX_NEXTPNR:-2}"
DRY_RUN=1

usage() {
    cat <<EOF
usage: release_regress.sh [--run] [--prefix DIR] [--cache DIR] [--work DIR] [--stages "stage ..."]

Release regression for the ofx toolchain built from install/patches:
  install     install/install.sh into the prefix (cached steps are skipped)
  series      the nextpnr, yosys and openFPGALoader series apply with git am on the pinned revs; tree = TREE
  noop        install/noop_check.py on $NOOP_DESIGNS: the release nextpnr on each recorded netlist against the
              variant's .frames (the older variants router/replay/rtkeep predate patches 0004/0007, which change
              pblock designs on purpose; those designs are covered by revalidate and identity)
  defaults    install/defaults_noop.py: the ofx default-on options are no-ops on designs they must not change,
              and all options off is the plain flow
  ofx         bin/ofx new $OFX_BOARD + ofx build --run, with the release defaults and with every option off
  cli         the ofx CLI end to end in a copy of the repo linked to the prefix: on $CLI_FLAT
              build --run, timing, drc, power, report, program (dry run); on $CLI_DFX dfx build --run,
              dfx verify --run (0 FAIL), timing --dfx, dfx load (dry run)
  smoke       install/smoke_test.sh (rv_ppt): blinky + DFX design from RTL in the prefix, native_check, .frames
  smoke_rvpr  the same for rv_pr (router)
  revalidate  install/revalidate.sh: DFX builds, pr_check STATIC IDENTICAL OUTSIDE REGION, region pips 0/0
  identity    .frames identity against the current builds: $IDENTITY from the noop summary (recorded netlists,
              nightly nextpnr), and $ID_DESIGN native ($ID_VARIANT, RMs $ID_RMS) built from RTL twice in one work
              directory, with the previous release nextpnr ($OLD_NPNR) and with the prefix's
              (cell names carry the source path, so both builds must come from the same directory)
  native      (not in the default list) flow/native_check*.sh on the revalidate builds: partials, byteman, region2v
Every stage after install/series runs against \$WORK/gated: the prefix with nextpnr-himbaechel (and the old
nextpnr) replaced by ofx/npwait.sh wrappers, so at most OFX_MAX_NEXTPNR=$MAX_NEXTPNR nextpnr run machine-wide.
stages: $STAGES
prefix: $PREFIX  cache: $CACHE  work: $WORK
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --run) DRY_RUN=0 ;;
        --prefix) PREFIX="$2"; shift ;;
        --cache) CACHE="$2"; shift ;;
        --work) WORK="$2"; shift ;;
        --stages) STAGES="$2"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown option $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done
PREFIX="$(realpath -m "$PREFIX")"
CACHE="$(realpath -m "$CACHE")"
WORK="$(realpath -m "$WORK")"
LOGS="$WORK/logs"
GATED="$WORK/gated"
CLEAN_PATH="$GATED/bin:$GATED/opt/oss-cad-suite/bin:$GATED/py3bin:/usr/bin:/bin"
REAL_NPNR="$PREFIX/bin/nextpnr-himbaechel"
NPNR="$GATED/bin/nextpnr-himbaechel"
GATED_OLD_NPNR="$GATED/old/nextpnr-himbaechel"
CHIPDB="$PREFIX/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin"
DB="$PREFIX/share/nextpnr/external/prjxray-db"
M=SLICE_X8Y100:SLICE_X11Y149,RAMB36_X0Y20:RAMB36_X0Y29,DSP48_X0Y40:DSP48_X0Y59

declare -A STATUS
ORDER=()
record() { STATUS[$1]=$2; ORDER+=("$1"); echo "== $1: $2"; }
stage_cmd() {
    local name=$1; shift
    echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $* > $LOGS/$name.log"
    [ "$DRY_RUN" = 1 ] && return 0
    local t0=$SECONDS
    "$@" > "$LOGS/$name.log" 2>&1
    local rc=$?
    echo "   exit $rc, $((SECONDS - t0))s"
    return $rc
}

gate_wrapper() {
    printf '#!/usr/bin/env bash\nOFX_NEXTPNR_BIN=%q OFX_MAX_NEXTPNR=%q exec %q "$@"\n' "$1" "$MAX_NEXTPNR" "$REPO/ofx/npwait.sh" > "$2"
    chmod +x "$2"
}

make_gated() {
    [ "$DRY_RUN" = 1 ] && { echo "[dry] $GATED: links to $PREFIX, nextpnr-himbaechel/-xilinx and $OLD_NPNR through ofx/npwait.sh"; return 0; }
    local e
    rm -rf "$GATED"
    mkdir -p "$GATED/bin" "$GATED/old"
    for e in "$PREFIX"/*; do
        case "${e##*/}" in bin|env.sh) ;; *) ln -s "$e" "$GATED/${e##*/}" ;; esac
    done
    for e in "$PREFIX"/bin/*; do
        case "${e##*/}" in nextpnr-himbaechel|nextpnr-xilinx) gate_wrapper "$REAL_NPNR" "$GATED/bin/${e##*/}" ;;
            *) ln -s "$e" "$GATED/bin/${e##*/}" ;; esac
    done
    gate_wrapper "$OLD_NPNR" "$GATED_OLD_NPNR"
    sed "s#$PREFIX#$GATED#g" "$PREFIX/env.sh" > "$GATED/env.sh"
}

st_install() {
    stage_cmd install bash "$HERE/install.sh" --run --prefix "$PREFIX" --cache "$CACHE" --jobs "$JOBS" --devices "$DEVICES" &&
        { [ "$DRY_RUN" = 1 ] || { grep -E 'WARNING|sha256|plugin ' "$LOGS/install.log" || true; [ -x "$REAL_NPNR" ] &&
            ! grep -q 'differs from openXC7 nightly' "$LOGS/install.log"; }; }
}

series_am() {
    local name=$1 src="$CACHE/src/$1" tmp rev ok=0
    rev="$(awk -v s="[$name]" '/^\[/ {i = ($0 == s); next} i && $1 == "rev" {gsub(/"/, "", $3); print $3; exit}' "$HERE/sources.toml")"
    tmp="$(mktemp -d "$WORK/series.XXXX")"
    git -C "$src" worktree add -q --detach "$tmp/w" "$rev" || return 1
    if git -C "$tmp/w" -c user.name=ofx -c user.email=ofx@localhost am -q "$HERE/patches/$2"/[0-9]*.patch; then
        local tree n
        tree="$(git -C "$tmp/w" rev-parse 'HEAD^{tree}')"
        n="$(git -C "$tmp/w" rev-list --count "HEAD" "^$rev")"
        if [ "$tree" = "$(cat "$HERE/patches/$2/TREE")" ]; then echo "PASS $name: $n patches apply with git am on $rev, tree $tree = TREE"
        else echo "FAIL $name: tree $tree differs from TREE $(cat "$HERE/patches/$2/TREE")"; ok=1; fi
    else
        echo "FAIL $name: git am stopped"; git -C "$tmp/w" am --abort; ok=1
    fi
    git -C "$src" worktree remove --force "$tmp/w"
    rm -rf "$tmp"
    return $ok
}

st_series() {
    [ "$DRY_RUN" = 1 ] && { echo "[dry] git am install/patches/{nextpnr,yosys,openfpgaloader} on the pinned revs, compare with TREE"; return 0; }
    { series_am nextpnr nextpnr && series_am yosys yosys && series_am openfpgaloader openfpgaloader; } > "$LOGS/series.log" 2>&1
    local rc=$?
    cat "$LOGS/series.log"
    return $rc
}

st_noop() {
    stage_cmd noop python3 "$HERE/noop_check.py" --run --candidate "$NPNR" --candidate-chipdb "$CHIPDB" \
        --candidate-db "$DB" --out "$WORK/noop" --only $NOOP_DESIGNS
    local rc=$?
    [ "$DRY_RUN" = 1 ] || tail -1 "$LOGS/noop.log"
    return $rc
}

st_defaults() {
    stage_cmd defaults env OFX_PREFIX="$PREFIX" OFX_MAX_NEXTPNR="$MAX_NEXTPNR" python3 "$HERE/defaults_noop.py" --run --prefix "$PREFIX" \
        --out "$WORK/defaults"
    local rc=$?
    [ "$DRY_RUN" = 1 ] || grep -E '^(PASS|FAIL|==)' "$LOGS/defaults.log"
    return $rc
}

st_smoke() {
    stage_cmd smoke bash "$HERE/smoke_test.sh" --run --prefix "$GATED" --work "$WORK/smoke"
    local rc=$?
    [ "$DRY_RUN" = 1 ] || grep -E '^(PASS|FAIL|INFO|==)' "$LOGS/smoke.log" | cut -c1-240
    return $rc
}

st_smoke_rvpr() {
    stage_cmd smoke_rvpr env PR_DESIGN=rv_pr PR_VARIANT=router bash "$HERE/smoke_test.sh" --run --prefix "$GATED" \
        --work "$WORK/smoke_rvpr"
    local rc=$?
    [ "$DRY_RUN" = 1 ] || grep -E '^(PASS|FAIL|INFO|==)' "$LOGS/smoke_rvpr.log" | cut -c1-240
    return $rc
}

st_revalidate() {
    stage_cmd revalidate env MAX_NEXTPNR="$MAX_NEXTPNR" bash "$HERE/revalidate.sh" --run --prefix "$GATED" --work "$WORK/reval" \
        --designs "$REVAL_DESIGNS"
    local rc=$?
    [ "$DRY_RUN" = 1 ] || cat "$LOGS/revalidate.log"
    return $rc
}

st_identity() {
    local w="$WORK/identity" side npnr rc=0
    if [ "$DRY_RUN" = 1 ]; then
        echo "[dry] read $WORK/noop/summary_${NOOP_DESIGNS// /_}.json for $IDENTITY"
        echo "[dry] in $w: build_pr_native --design $ID_DESIGN --variant $ID_VARIANT --rms $ID_RMS from RTL twice, with $OLD_NPNR (old) and $NPNR (new); cmp every .frames"
        return 0
    fi
    identity_recorded || rc=1
    mkdir -p "$w"
    cp -a "$REPO/flow" "$REPO/designs" "$w/"
    find "$w/flow" -name __pycache__ -prune -exec rm -rf {} +
    NATIVE_VARIANTS=" " bash "$HERE/link_repo.sh" --run --prefix "$GATED" --repo "$w" > "$LOGS/identity_link.log"
    for side in old new; do
        npnr="$NPNR"
        [ "$side" = old ] && npnr="$GATED_OLD_NPNR"
        mkdir -p "$w/build/nextpnr-build/$ID_VARIANT"
        ln -sfn "$npnr" "$w/build/nextpnr-build/$ID_VARIANT/nextpnr-himbaechel"
        stage_cmd "identity_$side" env -i HOME="$HOME" LANG=C.UTF-8 PATH="$CLEAN_PATH" bash -c \
            "cd '$w' && python3 flow/build_pr_native.py --design $ID_DESIGN --variant $ID_VARIANT --rms $ID_RMS --out build/identity/$side --run" || rc=1
    done
    python3 - "$w/build/identity/old" "$w/build/identity/new" "$EXPECTED_FASM" <<'PY' | tee -a "$LOGS/identity.log" || rc=1
import sys
from pathlib import Path
old, new, expected = Path(sys.argv[1]), Path(sys.argv[2]), set(sys.argv[3].split())


def fasm(p):
    return {l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")} if p.exists() else set()


bad = n = 0
for f in sorted(old.rglob("*.frames")):
    rel = f.relative_to(old)
    g = new / rel
    n += 1
    if f.stat().st_size and g.exists() and f.read_bytes() == g.read_bytes():
        print(f"PASS {rel.parent}: .frames identical (old {f}, new {g})")
        continue
    a, b = fasm(g.with_suffix(".fasm")), fasm(f.with_suffix(".fasm"))
    extra = sorted("+" + x for x in a - b) + sorted("-" + x for x in b - a)
    if a and b and g.exists() and g.stat().st_size and set(extra) <= expected:
        print(f"PASS {rel.parent}: .frames differ only by {' '.join(extra)}")
    else:
        bad += 1
        print(f"FAIL {rel.parent}: {len(extra)} FASM lines differ (e.g. {' '.join(extra[:3])})")
print(f"{n - bad}/{n} from-RTL builds identical apart from {sorted(expected)}")
sys.exit(1 if bad or not n else 0)
PY
    return $rc
}

identity_recorded() {
    python3 - "$WORK/noop/summary_${NOOP_DESIGNS// /_}.json" $IDENTITY <<'PY' | tee "$LOGS/identity.log"
import json, sys
rows = json.load(open(sys.argv[1]))
ok = {"identical", "identical-to-rerun", "expected-difference", "expected-difference-to-rerun"}
bad = 0
for want in sys.argv[2:]:
    sel = [r for r in rows if r["build"] == want or r["build"].startswith(want + "/")]
    if not sel:
        print(f"FAIL {want}: not in the noop summary")
        bad += 1
    for r in sel:
        extra = " ".join(r.get("fasm_only_candidate", []))
        print(f"{'PASS' if r['result'] in ok else 'FAIL'} {r['build']}: {r['result']}{' (+' + extra + ')' if extra and r['result'] in ok else ''}")
        bad += r["result"] not in ok
sys.exit(1 if bad else 0)
PY
}

st_ofx() {
    local w="$WORK/ofx" rc=0 p
    if [ "$DRY_RUN" = 1 ]; then
        echo "[dry] in $w: ofx new $OFX_BOARD blinky; ofx build --run with the release defaults and with every option off"
        return 0
    fi
    rm -rf "$w"
    mkdir -p "$w"
    cp -a "$REPO/bin" "$REPO/ofx" "$REPO/flow" "$REPO/designs" "$REPO/boards" "$REPO/VERSION" "$w/"
    find "$w" -name __pycache__ -prune -exec rm -rf {} +
    bash "$HERE/link_repo.sh" --run --prefix "$GATED" --repo "$w" > "$LOGS/ofx_link.log"
    in_ofx() { env -i HOME="$HOME" LANG=C.UTF-8 PATH="$CLEAN_PATH" bash -c "cd '$w' && $1"; }
    in_ofx "python3 bin/ofx new $OFX_BOARD proj/blinky" > "$LOGS/ofx_new.log" 2>&1 || rc=1
    cp -a "$w/proj/blinky" "$w/proj/blinky_off"
    printf '\n[build]\nhardblock_timing = false\ndsp_cascade = false\ndsp_pipeline = false\nasync_reg = false\nclkbuf_keep_buffer_inputs = false\ncell_timing = "stub"\nplacer = "heap"\n' >> "$w/proj/blinky_off/ofx.toml"
    for p in blinky blinky_off; do
        stage_cmd "ofx_$p" in_ofx "python3 bin/ofx -p proj/$p build --run" || rc=1
    done
    python3 - "$w/proj/blinky" "$w/proj/blinky_off" "$LOGS/ofx_blinky_off.log" <<'PY' | tee "$LOGS/ofx.log" || rc=1
import json, sys
from pathlib import Path
bad = 0
for d in sys.argv[1:3]:
    impl = Path(d) / "build" / "impl"
    j = impl / "ofx_defaults.json"
    bits = sorted(impl.rglob("*.bit"))
    if not j.exists() or not bits:
        print(f"FAIL {Path(d).name}: no ofx_defaults.json or bitstream under {impl}")
        bad += 1
        continue
    r = json.loads(j.read_text())
    dec = r.get("decision", {})
    print(f"PASS {Path(d).name}: bitstream {bits[0].name}; release {r['release']}; synth {r['synth']!r}; nextpnr args "
          f"{r['nextpnr_args'] + dec.get('nextpnr_args', [])}; chipdb {dec.get('chipdb') or 'default'}; {'; '.join(dec.get('why', []))}")
    if d == sys.argv[2]:
        plain = r["synth"] is None and not r["nextpnr_args"] and not dec.get("nextpnr_args") and not dec.get("chipdb")
        log = Path(sys.argv[3]).read_text()
        cmdline = [l for l in log.splitlines() if "build_openxc7.py" in l]
        extra = [w for l in cmdline for w in ("--synth", "--nextpnr-arg", "--chipdb", "--db-root") if w in l]
        ok = plain and not extra
        print(f"{'PASS' if ok else 'FAIL'} all options off: plain flow ({'no' if not extra else ' '.join(sorted(set(extra)))} "
              f"extra build_openxc7 arguments)")
        bad += not ok
sys.exit(1 if bad else 0)
PY
    return $rc
}

st_cli() {
    local w="$WORK/cli" rc=0 e d n
    if [ "$DRY_RUN" = 1 ]; then
        echo "[dry] in $w (repo copy linked to $GATED): flat $CLI_FLAT: build --run, timing, drc, power, report, program"
        echo "[dry] dfx $CLI_DFX: dfx build --run, dfx verify --run, timing --dfx, dfx load (dry)"
        return 0
    fi
    rm -rf "$w"
    mkdir -p "$w"
    cp -a "$REPO/bin" "$REPO/ofx" "$REPO/flow" "$REPO/designs" "$REPO/boards" "$REPO/VERSION" "$REPO/host" "$w/" 2>/dev/null
    rsync -a --exclude build "$REPO/examples/" "$w/examples/"
    find "$w" -name __pycache__ -prune -exec rm -rf {} +
    bash "$HERE/link_repo.sh" --run --prefix "$GATED" --repo "$w" > "$LOGS/cli_link.log"
    in_cli() { env -i HOME="$HOME" LANG=C.UTF-8 PATH="$CLEAN_PATH" OFX_MAX_NEXTPNR="$MAX_NEXTPNR" bash -c "cd '$w' && $1"; }
    : > "$LOGS/cli.log"
    cli_step() {
        local tag=$1 cmd=$2 log="$LOGS/cli_$1.log" t0=$SECONDS r
        in_cli "$cmd" > "$log" 2>&1
        r=$?
        printf '%s %-34s exit %d, %4ds  %s\n' "$([ $r = 0 ] && echo PASS || echo FAIL)" "$tag" $r $((SECONDS - t0)) "$cmd" | tee -a "$LOGS/cli.log"
        return $r
    }
    for e in $CLI_FLAT; do
        d="examples/$e"
        cli_step "${e}_build" "python3 bin/ofx -p $d build --run" || { rc=1; continue; }
        n=$(find "$w/$d/build" -name '*.bit' | wc -l)
        [ "$n" -gt 0 ] || { echo "FAIL ${e}: no bitstream under $d/build" | tee -a "$LOGS/cli.log"; rc=1; }
        cli_step "${e}_timing" "python3 bin/ofx -p $d timing --paths 2" || rc=1
        cli_step "${e}_drc" "python3 bin/ofx -p $d drc" || rc=1
        if ! cli_step "${e}_power" "python3 bin/ofx -p $d power"; then
            if grep -q 'no model at' "$LOGS/cli_${e}_power.log"; then
                echo "SKIP ${e}_power: no fitted ofx/power_model.json in the release (known 0.1 gap)" | tee -a "$LOGS/cli.log"
            else
                rc=1
            fi
        fi
        cli_step "${e}_report" "python3 bin/ofx -p $d report" || rc=1
        cli_step "${e}_program_dry" "python3 bin/ofx -p $d program" || rc=1
    done
    for e in $CLI_DFX; do
        d="examples/$e"
        cli_step "${e}_dfx_build" "python3 bin/ofx -p $d dfx build --run" || { rc=1; continue; }
        cli_step "${e}_dfx_verify" "python3 bin/ofx -p $d dfx verify --run" || rc=1
        echo "     ${e} verify: $(grep -c '^PASS' "$LOGS/cli_${e}_dfx_verify.log") PASS, $(grep -c '^FAIL' "$LOGS/cli_${e}_dfx_verify.log") FAIL, $(grep -c '^INFO' "$LOGS/cli_${e}_dfx_verify.log") INFO" | tee -a "$LOGS/cli.log"
        grep -q '^FAIL' "$LOGS/cli_${e}_dfx_verify.log" && rc=1
        cli_step "${e}_timing_dfx" "python3 bin/ofx -p $d timing --dfx" || rc=1
        n=$(find "$w/$d/build" -name '*.check.json' | head -1)
        if [ -n "$n" ]; then
            cli_step "${e}_load_dry" "python3 bin/ofx -p $d dfx load $(basename "${n%.check.json}") --via jtag" || rc=1
        else
            echo "FAIL ${e}: no partial with a .check.json safety record" | tee -a "$LOGS/cli.log"; rc=1
        fi
    done
    echo "== cli: $(grep -c '^PASS' "$LOGS/cli.log") PASS, $(grep -c '^FAIL' "$LOGS/cli.log") FAIL ($(grep -c '^SKIP' "$LOGS/cli.log") of them known-gap SKIPs)" | tee -a "$LOGS/cli.log"
    return $rc
}

native_cmd() {
    case "$1" in
        rv_pr) echo "NAT=build/patched/rv_pr_native/router FORMAL_SKIP_RMS=popc bash flow/native_check.sh" ;;
        rv_b) echo "NAT=build/patched/rv_b_native/router OUT=build/patched/partials/rv_b_native BMO=build/patched/byteman_check/rv_b_native REGION=SLICE_X12Y0:SLICE_X15Y49 TAGP=native_rv_b bash flow/native_check.sh" ;;
        rv_c) echo "NAT=build/patched/rv_c_native/router OUT=build/patched/partials/rv_c_native BMO=build/patched/byteman_check/rv_c_native REGION=SLICE_X12Y75:SLICE_X15Y124 TAGP=native_rv_c bash flow/native_check.sh" ;;
        rv_m) echo "NAT=build/patched/rv_m_native/replay OUT=build/patched/partials/rv_m_native BMO=build/patched/byteman_check/rv_m_native REGION=$M TAGP=native_rv_m FORMAL_TIMEOUT=300 BRAM_RMS='tbl tbl2' R2V_ARGS='--sweep 1024' FORMAL_SKIP_RMS='tbl tbl2' bash flow/native_check.sh" ;;
        rv2) echo "NAT=build/patched/rv2_native/rtkeep OUT=build/patched/partials/rv2/rtkeep BMO=build/patched/rv2_native/byteman/rtkeep TAGP=rv2rt bash flow/native_check_multi.sh" ;;
        rv_ppa|rv_ppt)
            local v=partpin2
            [ "$1" = rv_ppt ] && v=partpin3
            local nat="build/patched/${1}_native/$v"
            echo "NAT=$nat OUT=build/partials/$1 BMO=build/byteman_check/$1 TAGP=native_$1 PARTPINS=$nat/static_pp.json STATIC_PIPS=$nat/static_pp.prerouted SHELLV=$nat/rm_shell_pp.v bash flow/native_check.sh" ;;
    esac
}

st_native() {
    local fail=0 d
    for d in $NATIVE_DESIGNS; do
        stage_cmd "native_$d" env -i HOME="$HOME" LANG=C.UTF-8 PATH="$CLEAN_PATH" bash -c \
            "cd '$WORK/reval' && FORMAL_MEM_KB=$FORMAL_MEM_KB $(native_cmd "$d")" || fail=1
        [ "$DRY_RUN" = 1 ] || echo "   native $d: $(grep -c '^PASS' "$LOGS/native_$d.log") PASS, $(grep -c '^FAIL' "$LOGS/native_$d.log") FAIL"
    done
    return $fail
}

{
echo "== release regression $(cat "$REPO/VERSION" 2>/dev/null): prefix $PREFIX, cache $CACHE, work $WORK, stages '$STAGES'$([ "$DRY_RUN" = 1 ] && echo ', DRY RUN (pass --run)')"
[ "$DRY_RUN" = 1 ] || mkdir -p "$LOGS"
gated=0
for s in $STAGES; do
    declare -F "st_$s" > /dev/null || { echo "unknown stage $s" >&2; exit 2; }
    case "$s" in install|series) ;; *) [ $gated = 1 ] || { make_gated; gated=1; } ;; esac
    echo "== stage $s"
    if "st_$s"; then record "$s" PASS; else record "$s" FAIL; fi
    if [ "$s" = install ] && [ "${STATUS[install]}" = FAIL ]; then echo "install failed; stopping"; break; fi
done
fail=0
echo "== summary"
for s in "${ORDER[@]}"; do
    printf '   %-11s %s\n' "$s" "${STATUS[$s]}"
    [ "${STATUS[$s]}" = PASS ] || fail=1
done
echo "== release regression $([ "$DRY_RUN" = 1 ] && echo 'dry run done' || { [ $fail = 0 ] && echo PASSED || echo FAILED; }); logs in $LOGS"
exit $fail
}
