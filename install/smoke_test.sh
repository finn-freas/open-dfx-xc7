#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${OFX_PREFIX:-$HOME/.local/ofx}"
REPO="${REPO:-$(cd "$HERE/.." && pwd)}"
WORK="${WORK:-$HOME/.cache/ofx/smoke}"
REF="${REF:-$REPO/build}"
PR_DESIGN="${PR_DESIGN:-rv_ppt}"
PR_VARIANT="${PR_VARIANT:-partpin3}"
PR_RMS="${PR_RMS:-xor andn}"
FORMAL="${FORMAL:-0}"
EXPECTED_FASM="${EXPECTED_FASM:-+CFG_CENTER_MID_X46Y32.ICAP.IN_USE}"
DRY_RUN=1

while [ $# -gt 0 ]; do
    case "$1" in
        --run) DRY_RUN=0 ;;
        --prefix) PREFIX="$2"; shift ;;
        --work) WORK="$2"; shift ;;
        --ref) REF="$2"; shift ;;
        -h|--help) echo "usage: smoke_test.sh [--run] [--prefix DIR] [--work DIR] [--ref BUILD_DIR]"; exit 0 ;;
        *) echo "unknown option $1" >&2; exit 2 ;;
    esac
    shift
done
PREFIX="$(realpath -m "$PREFIX")"
WORK="$(realpath -m "$WORK")"
NAT="build/patched/${PR_DESIGN}_native/$PR_VARIANT"
CLEAN_PATH="$PREFIX/bin:$PREFIX/opt/oss-cad-suite/bin:$PREFIX/py3bin:/usr/bin:/bin"

echo "== smoke test: prefix $PREFIX, work $WORK, PR design $PR_DESIGN/$PR_VARIANT ($PR_RMS)$([ "$DRY_RUN" = 1 ] && echo ', DRY RUN (pass --run)')"
if [ "$DRY_RUN" = 1 ]; then
    echo "[dry] copy $REPO/flow and $REPO/designs to $WORK; install/link_repo.sh --run --prefix $PREFIX --repo $WORK"
    echo "[dry] PATH=$CLEAN_PATH"
    echo "[dry] python3 flow/build_openxc7.py blinky --run"
    echo "[dry] python3 flow/build_pr_native.py --design $PR_DESIGN --rms $PR_RMS --run"
    echo "[dry] flow/native_check.sh on $NAT (partials --simulate, byteman, region2v sim$([ "$FORMAL" = 1 ] && echo ' + proof'))"
    echo "[dry] cmp every .frames with $REF"
    exit 0
fi
[ -x "$PREFIX/bin/nextpnr-himbaechel" ] || { echo "no toolchain in $PREFIX" >&2; exit 1; }
[ -d "$WORK/build" ] && echo "   reusing $WORK (cached stages are skipped by the flow)"
mkdir -p "$WORK"
cp -a "$REPO/flow" "$REPO/designs" "$WORK/"
find "$WORK/flow" -name __pycache__ -prune -exec rm -rf {} +
bash "$HERE/link_repo.sh" --run --prefix "$PREFIX" --repo "$WORK" > "$WORK/link_repo.log"
mkdir -p "$WORK/logs"

in_prefix() {
    env -i HOME="$HOME" LANG=C.UTF-8 PATH="$CLEAN_PATH" bash -c "cd '$WORK' && $1"
}

fail=0
result() { printf '%-6s %s\n' "$1" "$2"; [ "$1" = PASS ] || [ "$1" = INFO ] || fail=1; }

in_prefix 'for t in python3 yosys nextpnr-himbaechel fasm2frames xc7frames2bit byteman openFPGALoader; do printf "%-20s %s\n" "$t" "$(command -v $t)"; done' | tee "$WORK/logs/tools.txt"
grep -v " $PREFIX/" "$WORK/logs/tools.txt" | grep -q . && result FAIL "a tool resolved outside $PREFIX (logs/tools.txt)"

t0=$(date +%s)
if in_prefix "python3 flow/build_openxc7.py blinky --run" > "$WORK/logs/blinky.log" 2>&1; then
    result PASS "blinky built ($(( $(date +%s) - t0 ))s, logs/blinky.log)"
else
    result FAIL "blinky build (logs/blinky.log)"
fi

t0=$(date +%s)
if in_prefix "python3 flow/build_pr_native.py --design $PR_DESIGN --rms $PR_RMS --run" > "$WORK/logs/pr.log" 2>&1; then
    result PASS "$PR_DESIGN built ($(( $(date +%s) - t0 ))s, logs/pr.log)"
else
    result FAIL "$PR_DESIGN build (logs/pr.log)"
fi

for j in "$WORK/$NAT"/checks/pr_check_*.json; do
    [ -f "$j" ] || continue
    verdict="$(tail -1 "${j%.json}.log" 2>/dev/null)"
    ref_log="$REF/${NAT#build/}/checks/$(basename "${j%.json}.log")"
    ref_verdict="$(tail -1 "$ref_log" 2>/dev/null)"
    if [ "$verdict" = "STATIC IDENTICAL OUTSIDE REGION" ]; then
        result PASS "pr_check $(basename "$j" .json): static identical outside the region"
    elif [ -n "$ref_verdict" ] && [ "$verdict" = "$ref_verdict" ]; then
        result PASS "pr_check $(basename "$j" .json): '$verdict', the same verdict as the reference build ($ref_log)"
    else
        result FAIL "pr_check $(basename "$j" .json): '$verdict' (${j%.json}.log)"
    fi
done

nc_env="NAT=$NAT OUT=build/partials/smoke BMO=build/byteman_check/smoke BM=$PREFIX/bin/byteman"
case "$PR_DESIGN" in
    rv_pp|rv_ppa|rv_ppt) nc_env="$nc_env PARTPINS=$NAT/static_pp.json STATIC_PIPS=$NAT/static_pp.prerouted SHELLV=$NAT/rm_shell_pp.v" ;;
esac
[ "$FORMAL" = 1 ] || nc_env="$nc_env FORMAL_SKIP_RMS='$PR_RMS'"
t0=$(date +%s)
if in_prefix "env $nc_env bash flow/native_check.sh" > "$WORK/logs/native_check.log" 2>&1; then
    result PASS "native_check: $(grep -c '^PASS' "$WORK/logs/native_check.log") PASS lines, 0 FAIL ($(( $(date +%s) - t0 ))s, logs/native_check.log)"
else
    result FAIL "native_check: $(grep -c '^FAIL' "$WORK/logs/native_check.log") FAIL lines (logs/native_check.log)"
fi

cmp_frames() {
    local mine=$1 ref=$2
    if [ ! -f "$ref" ]; then result INFO "no reference for ${mine#$WORK/}"; return; fi
    if [ ! -f "$mine" ]; then result FAIL "missing ${mine#$WORK/}"; return; fi
    if cmp -s "$mine" "$ref"; then result PASS ".frames identical: ${mine#$WORK/}"; return; fi
    local extra
    extra="$(fasm_extra "${mine%.frames}.fasm" "${ref%.frames}.fasm")"
    if [ "$extra" = "$EXPECTED_FASM" ]; then
        result PASS ".frames differ only by the expected FASM line $extra: ${mine#$WORK/}"
    elif path_only "$(dirname "$mine")" "$(dirname "$ref")"; then
        result INFO ".frames differ, but the netlist differs from the reference only in the source paths yosys puts in cell names (built under $WORK, not $REPO); not comparable here, install/noop_check.py compares P&R on the recorded netlist: ${mine#$WORK/}"
    else
        result FAIL ".frames differ: ${mine#$WORK/} vs $ref (FASM difference: $(echo "$extra" | cut -c1-300))"
    fi
}
path_only() {
    python3 - "$1" "$2" "$WORK" "$REPO" "$PREFIX/opt/oss-cad-suite" "$(realpath -m "$PREFIX/opt/oss-cad-suite")" <<'PY'
import sys
from pathlib import Path
mine, ref, work, repo, ocs, ocs_real = sys.argv[1:]
a = sorted(Path(mine).glob("*.json"))
a = [p for p in a if not p.name.endswith(("_routed.json", "report.json", "versions.json"))]
if not a or not (Path(ref) / a[0].name).exists():
    sys.exit(1)
x = a[0].read_text()
y = (Path(ref) / a[0].name).read_text()
if x == y:
    sys.exit(1)
x = x.replace(ocs_real, repo + "/toolchain/oss-cad-suite").replace(ocs, repo + "/toolchain/oss-cad-suite").replace(work, repo)
sys.exit(0 if x == y else 1)
PY
}
fasm_extra() {
    python3 - "$1" "$2" <<'PY'
import sys
from pathlib import Path
lines = [{l.strip() for l in Path(p).read_text().splitlines() if l.strip() and not l.startswith("#")}
         if Path(p).exists() else set() for p in sys.argv[1:]]
print(" ".join(sorted("+" + x for x in lines[0] - lines[1]) + sorted("-" + x for x in lines[1] - lines[0])))
PY
}
cmp_frames "$WORK/build/openxc7/blinky/xc7a35tcsg324-1_s1/blinky.frames" "$REF/openxc7/blinky/xc7a35tcsg324-1_s1/blinky.frames"
for d in "$WORK/$NAT"/*/; do
    f="$d/rv_soc.frames"
    [ -f "$f" ] || continue
    cmp_frames "$f" "$REF/${NAT#build/}/$(basename "$d")/rv_soc.frames"
done
echo "== smoke test $([ $fail = 0 ] && echo PASSED || echo FAILED); logs in $WORK/logs"
exit $fail
