#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${OFX_PREFIX:-$HOME/.local/ofx}"
REPO="${REPO:-$(cd "$HERE/.." && pwd)}"
WORK="${WORK:-$HOME/.cache/ofx/smoke}"
DESIGNS="${DESIGNS:-rv_pr rv_b rv_c rv2 rv_ppa rv_ppt rv_m}"
MAX_NEXTPNR="${MAX_NEXTPNR:-2}"
DRY_RUN=1

while [ $# -gt 0 ]; do
    case "$1" in
        --run) DRY_RUN=0 ;;
        --prefix) PREFIX="$2"; shift ;;
        --work) WORK="$2"; shift ;;
        --designs) DESIGNS="$2"; shift ;;
        -h|--help) echo "usage: revalidate.sh [--run] [--prefix DIR] [--work DIR] [--designs 'rv_b ...']: rebuild native-flow designs with the installed nextpnr and summarise pr_check and region_pips"; exit 0 ;;
        *) echo "unknown option $1" >&2; exit 2 ;;
    esac
    shift
done
PREFIX="$(realpath -m "$PREFIX")"
WORK="$(realpath -m "$WORK")"
CLEAN_PATH="$PREFIX/bin:$PREFIX/opt/oss-cad-suite/bin:$PREFIX/py3bin:/usr/bin:/bin"

if [ "$DRY_RUN" = 1 ]; then
    for d in $DESIGNS; do echo "[dry] (in $WORK, PATH=$CLEAN_PATH) python3 flow/build_pr_native.py --design $d --run"; done
    exit 0
fi
mkdir -p "$WORK/logs"
cp -a "$REPO/flow" "$REPO/designs" "$WORK/"
find "$WORK/flow" -name __pycache__ -prune -exec rm -rf {} +
bash "$HERE/link_repo.sh" --run --prefix "$PREFIX" --repo "$WORK" > "$WORK/link_repo.log"
fail=0
bad() { echo "   FAIL $*"; fail=1; }
for d in $DESIGNS; do
    while [ "$(pgrep -c nextpnr)" -ge "$MAX_NEXTPNR" ]; do sleep 30; done
    t0=$(date +%s)
    env -i HOME="$HOME" LANG=C.UTF-8 PATH="$CLEAN_PATH" bash -c "cd '$WORK' && python3 flow/build_pr_native.py --design $d --run" \
        > "$WORK/logs/revalidate_$d.log" 2>&1
    rc=$?
    echo "== $d: build_pr_native exit $rc, $(( $(date +%s) - t0 ))s (logs/revalidate_$d.log)"
    [ $rc = 0 ] || bad "$d: build_pr_native exit $rc"
    out="$(grep -o 'builds under .*' "$WORK/logs/revalidate_$d.log" | tail -1 | sed 's/builds under //')"
    [ -n "$out" ] || { bad "$d: no build directory in the log"; continue; }
    ref="$REPO/${out#$WORK/}"
    n=0
    for l in "$out"/checks/pr_check_*.log; do
        [ -f "$l" ] || continue
        n=$((n + 1))
        v="$(tail -1 "$l")"
        rv="$(tail -1 "$ref/checks/$(basename "$l")" 2>/dev/null)"
        case "$l" in */pr_check_multi.log) ;; *)
            if [ "$v" = "STATIC IDENTICAL OUTSIDE REGION" ]; then echo "   $(basename "$l" .log): $v"
            elif [ -n "$rv" ] && [ "$v" = "$rv" ]; then echo "   $(basename "$l" .log): $v (the reference build's verdict too)"
            else bad "$(basename "$l" .log): '$v' (reference: '$rv')"; fi ;;
        esac
    done
    if [ -f "$out/checks/pr_check_multi.log" ]; then
        v="$(tail -1 "$out/checks/pr_check_multi.log")"
        case "$v" in
            *" pass") [ "${v%%/*}" = "$(echo "$v" | sed 's#^[0-9]*/\([0-9]*\) .*#\1#')" ] && echo "   pr_check_multi: $v" || bad "pr_check_multi: $v" ;;
            *) bad "pr_check_multi: $v" ;;
        esac
    fi
    [ $n -gt 0 ] || bad "$d: no pr_check log"
    for l in "$out"/checks/pips_*.log; do
        [ -f "$l" ] || continue
        python3 - "$l" "$ref/checks/$(basename "$l")" <<'PY' || fail=1
import ast, re, sys
from pathlib import Path


def counts(p):
    s = {}
    if Path(p).exists():
        for line in open(p):
            m = re.match(r"\s+(static|boundary|rm)\s+(\{.*\})", line)
            if m:
                s[m.group(1)] = ast.literal_eval(m.group(2))
    return (s.get("static", {}).get("pips_in_region"), s.get("rm", {}).get("pips_outside_region")) if s else None


name = sys.argv[1].rsplit("/", 1)[-1][:-4]
mine, ref = counts(sys.argv[1]), counts(sys.argv[2])
if mine is None:
    sys.exit(0)
ok = mine == (0, 0) or mine == ref
note = "" if mine == (0, 0) else f" (reference {ref})"
print(f"   {'' if ok else 'FAIL '}{name}: static pips in region {mine[0]}, RM pips outside region {mine[1]}{note}")
sys.exit(0 if ok else 1)
PY
    done
done
echo "== revalidate $([ $fail = 0 ] && echo PASSED || echo FAILED)"
exit $fail
