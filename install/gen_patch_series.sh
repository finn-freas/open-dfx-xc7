#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRAFTS="${DRAFTS:-$ROOT/docs/drafts}"
MSGS="${MSGS:-$ROOT/install/patches/messages}"
REBASED="${REBASED:-$ROOT/install/patches/rebased}"
OUT="${OUT:-$ROOT/install/patches}"
WORK="${WORK:-$ROOT/build/patch-series}"
NEXTPNR_REPO="${NEXTPNR_REPO:-$ROOT/upstream/openXC7_nextpnr}"
NEXTPNR_BASE="${NEXTPNR_BASE:-ce3f7c18c6b589b9645ccf156aaa198c0fcd8fc4}"
NEXTPNR_SERIES="${NEXTPNR_SERIES:-pblock-xdc router-region pblock-replay pblock-routethru partition-pins pblock-lutff carry-replay-order partition-pins-route dsp-mask-areg iserdes-const-pins muxf7-mixed-loads partition-pins-pinfeed xdc-timing xdc2-constraints hardblock-timing cell-timing-cal dsp-cascade-place router-keepout-crit placer-tuning io-buffer-params mmcm-base-ties bufh-region diff-term cfg-in-use clkout-unused fifo xadc}"
YOSYS_REPO="${YOSYS_REPO:-$ROOT/upstream/YosysHQ_yosys}"
YOSYS_BASE="${YOSYS_BASE:-3718f7f135dc25381c50f18e550bdc5f48663ec3}"
YOSYS_SERIES="${YOSYS_SERIES:-xilinx-dsp-pipeline xilinx-asyncreg clkbufmap-keep-buffer-inputs}"
DB_SERIES="${DB_SERIES:-artix7:prjxray-db-diff-term.segbits artix7:prjxray-db-fifo.segbits artix7:prjxray-db-cfg-in-use.segbits artix7:prjxray-db-monitor-bot.ppips artix7:prjxray-db-xadc-init.segbits}"
META_SERIES="${META_SERIES:-artix7:nextpnr-xilinx-meta-site_type_XADC.json}"
OFL_REPO="${OFL_REPO:-$ROOT/upstream/trabucayre_openFPGALoader}"
OFL_BASE="${OFL_BASE:-befbab4f646207dbaf1daf8b144dd980ad283dd5}"
OFL_SERIES="${OFL_SERIES:-openfpgaloader-partial.patch openfpgaloader-partial-fix1.diff}"
AUTHOR="${AUTHOR:-Finn Freas <finn.freas@gmail.com>}"
DATE="${DATE:-2026-11-05T12:00:00+0000}"
DRY_RUN="${DRY_RUN:-1}"

run() { echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $*"; [ "$DRY_RUN" = 1 ] || "$@"; }

message_of() {
    local draft=$1 name=$2
    if [ -f "$MSGS/$name.txt" ]; then
        cat "$MSGS/$name.txt"
        return
    fi
    python3 -I - "$draft" <<'PY'
import re, sys
head = []
for line in open(sys.argv[1], encoding="utf-8"):
    if line.startswith("diff --git") or line.startswith("--- a/") or line.rstrip("\n") == "---":
        break
    head.append(line.rstrip("\n"))
out = []
in_subject = False
for line in head:
    if re.match(r"From [0-9a-f]{40} ", line) or line.startswith("From: ") or line.startswith("Date: "):
        continue
    if in_subject and line.startswith(" "):
        out[-1] += line
        continue
    in_subject = line.startswith("Subject: ")
    out.append(re.sub(r"^Subject: (\[PATCH[^\]]*\] )?", "", line))
text = "\n".join(out).strip("\n")
paras = [p for p in text.split("\n\n")
         if not re.match(r"(Base:|Draft, not posted|Not compiled:|Local draft)", p.strip())]
print("\n\n".join(paras).strip())
PY
}

series() {
    local repo=$1 base=$2 tree=$3 dest=$4; shift 4
    run rm -rf "$tree"
    run git -C "$repo" worktree prune
    run git -C "$repo" worktree add --detach "$tree" "$base"
    for f in "$@"; do
        local name=${f%.patch}
        name=${name%.diff}
        local src="$DRAFTS/$f"
        [ -f "$REBASED/$f" ] && src="$REBASED/$f"
        if [ "$DRY_RUN" = 1 ]; then
            echo "[dry] apply $src and commit"
            continue
        fi
        git -C "$tree" apply --index "$src"
        message_of "$DRAFTS/$f" "$name" > "$tree/.git-msg"
        GIT_AUTHOR_DATE="$DATE" GIT_COMMITTER_DATE="$DATE" \
            git -C "$tree" -c user.name="${AUTHOR% <*}" -c user.email="${AUTHOR##*<}" \
            commit -q --no-verify --author="$AUTHOR" -F "$tree/.git-msg"
        rm -f "$tree/.git-msg"
    done
    run mkdir -p "$dest"
    [ "$DRY_RUN" = 1 ] || rm -f "$dest"/[0-9][0-9][0-9][0-9]-*.patch
    run git -C "$tree" format-patch -q --zero-commit --no-signature --no-numbered -o "$dest" "$base..HEAD"
    [ "$DRY_RUN" = 1 ] || git -C "$tree" rev-parse HEAD^{tree} > "$dest/TREE"
    run git -C "$repo" worktree remove --force "$tree"
}

nextpnr_files=()
for p in $NEXTPNR_SERIES; do nextpnr_files+=("nextpnr-$p.patch"); done
series "$NEXTPNR_REPO" "$NEXTPNR_BASE" "$WORK/nextpnr" "$OUT/nextpnr" "${nextpnr_files[@]}"
read -r -a ofl_files <<< "$OFL_SERIES"
series "$OFL_REPO" "$OFL_BASE" "$WORK/openfpgaloader" "$OUT/openfpgaloader" "${ofl_files[@]}"
yosys_files=()
for p in $YOSYS_SERIES; do yosys_files+=("yosys-$p.patch"); done
series "$YOSYS_REPO" "$YOSYS_BASE" "$WORK/yosys" "$OUT/yosys" "${yosys_files[@]}"

copy_series() {
    local dest=$1; shift
    run mkdir -p "$dest"
    [ "$DRY_RUN" = 1 ] || rm -f "$dest/SERIES"
    for entry in "$@"; do
        local fam=${entry%%:*} f=${entry#*:}
        run cp "$DRAFTS/$f" "$dest/$f"
        [ "$DRY_RUN" = 1 ] || echo "$fam $f" >> "$dest/SERIES"
    done
}
copy_series "$OUT/prjxray-db" $DB_SERIES
copy_series "$OUT/nextpnr-xilinx-meta" $META_SERIES
[ "$DRY_RUN" = 1 ] || ls -1 "$OUT/nextpnr" "$OUT/openfpgaloader" "$OUT/yosys" "$OUT/prjxray-db" "$OUT/nextpnr-xilinx-meta"
