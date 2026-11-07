#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${OFX_PREFIX:-$HOME/.local/ofx}"
CACHE="${OFX_CACHE:-$HOME/.cache/ofx}"
JOBS="${OFX_JOBS:-4}"
DEVICES="${OFX_DEVICES:-xc7a50t}"
ALL_DEVICES="xc7a50t xc7a100t xc7a200t xc7s25 xc7s50 xc7s100 xc7z010 xc7z020 xc7z030 xc7z045 xc7z100"
YOSYS="${OFX_YOSYS:-oss-cad-suite}"
STEPS="${OFX_STEPS:-micromamba env sources nextpnr prjxray byteman openfpgaloader yosys chipdb envsh}"
SOURCES="${OFX_SOURCES:-$HERE/sources.toml}"
LOCK="${OFX_LOCK:-$HERE/conda-linux-64.lock}"
WHEELS="${OFX_WHEELS:-$HERE/python-wheels.txt}"
PATCHES="${OFX_PATCHES:-$HERE/patches}"
VARIANT="ofx"
RELEASE="$(cat "$HERE/../VERSION" 2>/dev/null || echo unknown)"
MAMBA_THREADS="${OFX_MAMBA_THREADS:-1}"
RETRIES="${OFX_RETRIES:-4}"
PRJXRAY_SUBMODULES="third_party/abseil-cpp third_party/cctz third_party/googletest third_party/gflags third_party/yaml-cpp third_party/sanitizers-cmake third_party/fasm"
YOSYS_SUBMODULES="abc libs/cxxopts libs/fmt libs/tomlplusplus libs/boost_regex"
DRY_RUN=1

usage() {
    cat <<EOF
usage: install.sh [--run] [--prefix DIR] [--cache DIR] [--devices "xc7a50t ..."] [--all-devices]
                  [--yosys oss-cad-suite|source|none] [--jobs N] [--steps "step ..."]

Builds the open-dfx-xc7 toolchain (patched openXC7 nextpnr, prjxray tools, byteman, openFPGALoader
with --partial, chipdbs) into a user-local prefix. Nothing is changed without --run.
steps: $STEPS
prefix: $PREFIX   cache: $CACHE
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --run) DRY_RUN=0 ;;
        --prefix) PREFIX="$2"; shift ;;
        --cache) CACHE="$2"; shift ;;
        --devices) DEVICES="$2"; shift ;;
        --all-devices) DEVICES="$ALL_DEVICES" ;;
        --yosys) YOSYS="$2"; shift ;;
        --jobs) JOBS="$2"; shift ;;
        --steps) STEPS="$2"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown option $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done
PREFIX="$(realpath -m "$PREFIX")"
CACHE="$(realpath -m "$CACHE")"
ENV="$PREFIX/env"
MAMBA="$PREFIX/libexec/micromamba"
DB="$PREFIX/share/nextpnr/external/prjxray-db"
CHIPDB_DIR="$PREFIX/share/nextpnr/himbaechel/xilinx"
PLUGINS="$PREFIX/share/ofx/yosys-plugins"
STAMPS="$PREFIX/share/ofx/stamps"
LOG="$CACHE/logs"

say() { echo "== $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }
run() {
    echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $*"
    [ "$DRY_RUN" = 1 ] || "$@"
}
logged() {
    local name=$1; shift
    echo "[$([ "$DRY_RUN" = 1 ] && echo dry || echo run)] $* > $LOG/$name.log"
    [ "$DRY_RUN" = 1 ] && return 0
    mkdir -p "$LOG"
    if ! "$@" >> "$LOG/$name.log" 2>&1; then
        tail -20 "$LOG/$name.log" >&2
        die "$name failed, see $LOG/$name.log"
    fi
}
retry() {
    local i
    for i in $(seq "$RETRIES"); do
        "$@" && return 0
        echo "   attempt $i of $RETRIES failed: $*" >&2
        sleep $((i * 5))
    done
    return 1
}
toml() {
    awk -v s="[$1]" -v k="$2" '
        /^\[/ { inside = ($0 == s); next }
        inside && $1 == k { sub(/^[^=]*= *"/, ""); sub(/" *$/, ""); print; exit }' "$SOURCES"
}
stamp_ok() { [ -f "$STAMPS/$1" ] && [ "$(cat "$STAMPS/$1")" = "$2" ]; }
stamp_set() { [ "$DRY_RUN" = 1 ] || { mkdir -p "$STAMPS"; echo "$2" > "$STAMPS/$1"; }; }
has_step() { case " $STEPS " in *" $1 "*) return 0 ;; esac; return 1; }
family_of() {
    case "$1" in
        xc7a*) echo artix7 ;;
        xc7s*) echo spartan7 ;;
        xc7z*) echo zynq7 ;;
        xc7k*) echo kintex7 ;;
        *) die "no prjxray-db family for device $1" ;;
    esac
}

check_host() {
    local missing=()
    local tools="bash git curl tar gzip sha256sum md5sum awk sed find realpath"
    [ "$YOSYS" = source ] && tools="$tools bison flex"
    for t in $tools; do
        command -v "$t" >/dev/null 2>&1 || missing+=("$t")
    done
    [ "$(uname -s)-$(uname -m)" = "Linux-x86_64" ] || die "only Linux x86_64 is supported (micromamba, oss-cad-suite and the lock are linux-64)"
    if [ ${#missing[@]} -gt 0 ]; then
        echo "missing host tools: ${missing[*]} (Debian/Ubuntu: apt-get install git curl ca-certificates tar gzip)" >&2
        [ "$DRY_RUN" = 1 ] || exit 1
    fi
}

fetch_file() {
    local url=$1 dest=$2 sha=$3
    if [ -f "$dest" ] && echo "$sha  $dest" | sha256sum -c --status; then
        echo "[cached] $dest"
        return
    fi
    run mkdir -p "$(dirname "$dest")"
    run retry curl -fL --proto '=https' --tlsv1.2 -sS -o "$dest.part" "$url"
    if [ "$DRY_RUN" = 0 ]; then
        echo "$sha  $dest.part" | sha256sum -c --status || die "sha256 mismatch for $url"
        mv "$dest.part" "$dest"
    fi
}

git_fetch() {
    local name=$1; shift
    local url rev dir want_sparse
    url="$(toml "$name" url)"
    rev="$(toml "$name" rev)"
    dir="$CACHE/src/$name"
    want_sparse="$(printf '%s
' "$@")"
    [ -n "$url" ] && [ -n "$rev" ] || die "no url/rev for $name in $SOURCES"
    if [ -d "$dir/.git" ] && [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null)" = "$rev" ] &&
        { [ $# -eq 0 ] || [ "$(cat "$dir/.git/info/sparse-checkout" 2>/dev/null)" = "$want_sparse" ]; }; then
        echo "[cached] $name $rev"
        return
    fi
    if [ ! -d "$dir/.git" ]; then
        run mkdir -p "$dir"
        run git -C "$dir" init -q
        run git -C "$dir" remote add origin "$url"
    fi
    if [ $# -gt 0 ]; then
        run git -C "$dir" config core.sparseCheckout true
        run git -C "$dir" config core.sparseCheckoutCone false
        if [ "$DRY_RUN" = 0 ]; then
            mkdir -p "$dir/.git/info"
            echo "$want_sparse" > "$dir/.git/info/sparse-checkout"
        fi
        run retry git -C "$dir" fetch -q --depth 1 --filter=blob:none origin "$rev"
    else
        run retry git -C "$dir" fetch -q --depth 1 origin "$rev"
    fi
    run retry git -C "$dir" -c advice.detachedHead=false checkout -q -f --detach "$rev"
    if [ "$DRY_RUN" = 0 ]; then
        [ "$(git -C "$dir" rev-parse HEAD)" = "$rev" ] || die "$name: HEAD is not $rev"
        echo "   $name verified at $rev"
    fi
}

patched_tree() {
    local name=$1 pdir=$2 work=$3
    local rev key
    rev="$(toml "$name" rev)"
    key="$rev $(cat "$pdir"/[0-9]*.patch | sha256sum | cut -d' ' -f1)"
    if [ -d "$work" ] && [ -f "$work/.ofx-series" ] && [ "$(cat "$work/.ofx-series")" = "$key" ]; then
        echo "[cached] $work (series applied)"
        return
    fi
    run rm -rf "$work"
    run git -C "$CACHE/src/$name" worktree prune
    run git -C "$CACHE/src/$name" worktree add -q --detach "$work" "$rev"
    for p in "$pdir"/[0-9]*.patch; do
        run git -C "$work" apply --whitespace=nowarn "$p"
    done
    [ "$DRY_RUN" = 1 ] || [ ! -f "$pdir/TREE" ] || { git -C "$work" add -A && [ "$(git -C "$work" write-tree)" = "$(cat "$pdir/TREE")" ]; } ||
        die "$work: the patched tree differs from $pdir/TREE"
    [ "$DRY_RUN" = 1 ] || echo "$key" > "$work/.ofx-series"
}

build_env() {
    export PATH="$ENV/bin:$PATH"
    export CC="$ENV/bin/x86_64-conda-linux-gnu-gcc"
    export CXX="$ENV/bin/x86_64-conda-linux-gnu-g++"
    export CMAKE_PREFIX_PATH="$ENV"
    export PKG_CONFIG_PATH="$ENV/lib/pkgconfig:$ENV/share/pkgconfig"
    export LDFLAGS="-L$ENV/lib -Wl,-rpath,$ENV/lib"
    unset CFLAGS CXXFLAGS CPPFLAGS
}

step_micromamba() {
    say "micromamba"
    fetch_file "$(toml micromamba url)" "$CACHE/dl/micromamba-linux-64" "$(toml micromamba sha256)"
    if [ ! -x "$MAMBA" ]; then
        run mkdir -p "$PREFIX/libexec"
        run install -m755 "$CACHE/dl/micromamba-linux-64" "$MAMBA"
    fi
}

conda_prefetch() {
    local pkgs="$MAMBA_ROOT_PREFIX/pkgs" url md5 f n=0 got=0
    mkdir -p "$pkgs"
    while IFS='#' read -r url md5; do
        case "$url" in https://*) ;; *) continue ;; esac
        n=$((n + 1))
        f="$pkgs/$(basename "$url")"
        if [ -f "$f" ] && [ "$(md5sum "$f" | cut -d' ' -f1)" = "$md5" ]; then continue; fi
        retry curl -fL --proto '=https' --tlsv1.2 -sS --retry 5 --retry-all-errors -o "$f.part" "$url" || return 1
        [ "$(md5sum "$f.part" | cut -d' ' -f1)" = "$md5" ] || { echo "md5 mismatch: $url" >&2; rm -f "$f.part"; return 1; }
        mv "$f.part" "$f"
        got=$((got + 1))
    done < "$LOCK"
    echo "conda packages: $n in the lock, $got downloaded, $((n - got)) cached"
}

env_create() {
    rm -rf "$ENV"
    "$MAMBA" create -y -q --offline -p "$ENV" --file "$LOCK"
}

step_env() {
    say "conda-forge build environment ($LOCK)"
    local key
    key="$(cat "$LOCK" "$WHEELS" | sha256sum | cut -d' ' -f1)"
    if stamp_ok env "$key" && [ -x "$ENV/bin/python3" ]; then
        echo "[cached] $ENV"
        return
    fi
    export MAMBA_ROOT_PREFIX="$CACHE/mamba" MAMBA_DOWNLOAD_THREADS="$MAMBA_THREADS"
    logged conda-download conda_prefetch
    logged env env_create
    say "python packages for fasm2frames/bit2fasm ($WHEELS)"
    local files=()
    while read -r url sha; do
        [ -n "$url" ] || continue
        fetch_file "$url" "$CACHE/dl/pypi/$(basename "$url")" "$sha"
        files+=("$CACHE/dl/pypi/$(basename "$url")")
    done < "$WHEELS"
    logged env-pip env PIP_CONFIG_FILE=/dev/null "$ENV/bin/python3" -I -m pip install -q --no-index --no-deps \
        --no-build-isolation --no-cache-dir "${files[@]}"
    stamp_set env "$key"
}

step_sources() {
    say "sources ($SOURCES)"
    local fams=("artix7")
    for d in $DEVICES; do fams+=("$(family_of "$d")"); done
    local sparse=(/COPYING /LICENSE /README.md /Info.md)
    for f in $(printf '%s\n' "${fams[@]}" | sort -u); do sparse+=("/$f/"); done
    git_fetch nextpnr
    git_fetch nextpnr-xilinx-meta
    git_fetch prjxray
    git_fetch prjxray-db "${sparse[@]}"
    git_fetch byteman
    git_fetch openfpgaloader
    if [ "$YOSYS" != none ]; then git_fetch yosys; fi
    if [ "$DRY_RUN" = 0 ]; then
        local meta_link
        meta_link="$(git -C "$CACHE/src/nextpnr" ls-tree HEAD himbaechel/uarch/xilinx/meta | awk '{print $3}')"
        [ "$meta_link" = "$(toml nextpnr-xilinx-meta rev)" ] || die "nextpnr's meta gitlink $meta_link differs from sources.toml"
        local fasm_link
        fasm_link="$(git -C "$CACHE/src/prjxray" ls-tree HEAD third_party/fasm | awk '{print $3}')"
        [ "$fasm_link" = "$(toml fasm rev)" ] || die "prjxray's fasm gitlink $fasm_link differs from sources.toml"
    fi
    say "prjxray submodules (pinned by prjxray's gitlinks)"
    logged prjxray-submodules retry git -C "$CACHE/src/prjxray" submodule update --init --depth 1 $PRJXRAY_SUBMODULES
    if [ "$YOSYS" = source ]; then
            logged yosys-submodules retry git -C "$CACHE/src/yosys" submodule update --init --depth 1 $YOSYS_SUBMODULES
    fi
    if [ "$DRY_RUN" = 0 ]; then
        git -C "$CACHE/src/prjxray" submodule status $PRJXRAY_SUBMODULES | grep -v '^ ' && die "a prjxray submodule is not at its gitlink"
        true
    fi
    local key
    key="$(toml prjxray-db rev) ${fams[*]} $(series_key prjxray-db)"
    if stamp_ok prjxray-db "$key" && [ -d "$DB/artix7" ]; then
        echo "[cached] $DB"
    else
        run rm -rf "$DB"
        run mkdir -p "$DB"
        for f in $(printf '%s\n' "${fams[@]}" | sort -u); do
            run cp -a "$CACHE/src/prjxray-db/$f" "$DB/"
        done
        run cp "$CACHE/src/prjxray-db/LICENSE" "$DB/"
        say "prjxray-db additions ($PATCHES/prjxray-db/SERIES)"
        logged prjxray-db-patch "$ENV/bin/python3" -I "$HERE/db_patch.py" "$DB" --series "$PATCHES/prjxray-db/SERIES" --run
        stamp_set prjxray-db "$key"
    fi
}

series_key() {
    local d="$PATCHES/$1"
    (cat "$d/SERIES" && awk -v d="$d" '{print d "/" $2}' "$d/SERIES" | xargs cat) | sha256sum | cut -d' ' -f1
}

patched_meta() {
    local work=$1 key
    key="$(toml nextpnr-xilinx-meta rev) $(series_key nextpnr-xilinx-meta)"
    if [ -d "$work" ] && [ "$(cat "$work/.ofx-series" 2>/dev/null)" = "$key" ]; then
        echo "[cached] $work (meta additions applied)"
        return
    fi
    run rm -rf "$work"
    run cp -a "$CACHE/src/nextpnr-xilinx-meta" "$work"
    run rm -rf "$work/.git"
    while read -r fam name; do
        [ -n "$fam" ] || continue
        local dest="${name#nextpnr-xilinx-meta-}"
        if [ "$DRY_RUN" = 0 ] && [ -e "$work/$fam/$dest" ]; then
            die "$work/$fam/$dest exists in the pinned meta; refusing to replace it"
        fi
        run cp "$PATCHES/nextpnr-xilinx-meta/$name" "$work/$fam/$dest"
    done < "$PATCHES/nextpnr-xilinx-meta/SERIES"
    [ "$DRY_RUN" = 1 ] || echo "$key" > "$work/.ofx-series"
}

step_nextpnr() {
    say "nextpnr-himbaechel (xilinx) + $(ls "$PATCHES"/nextpnr/[0-9]*.patch | wc -l) patches"
    local src="$CACHE/work/nextpnr-$VARIANT" bld="$CACHE/build/nextpnr-$VARIANT" rev
    rev="$(toml nextpnr rev)"
    patched_tree nextpnr "$PATCHES/nextpnr" "$src"
    build_env
    local key="$rev $(cat "$PATCHES"/nextpnr/[0-9]*.patch | sha256sum | cut -d' ' -f1)"
    if stamp_ok nextpnr "$key" && [ -x "$PREFIX/bin/nextpnr-himbaechel" ]; then
        echo "[cached] $PREFIX/bin/nextpnr-himbaechel"
        return
    fi
    logged nextpnr-cmake cmake -S "$src" -B "$bld" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCURRENT_GIT_VERSION="${rev:0:8}-$VARIANT" \
        -DARCH=himbaechel -DHIMBAECHEL_UARCH=xilinx -DHIMBAECHEL_XILINX_DEVICES= \
        -DHIMBAECHEL_PRJXRAY_DB="$DB" \
        -DBUILD_GUI=OFF -DBUILD_TESTS=OFF -DBUILD_PYTHON=OFF \
        -DPython3_EXECUTABLE="$ENV/bin/python3.12" -Wno-deprecated
    logged nextpnr-build ninja -C "$bld" -j"$JOBS" nextpnr-himbaechel bbasm
    run mkdir -p "$PREFIX/bin"
    run install -m755 "$bld/nextpnr-himbaechel" "$PREFIX/bin/nextpnr-himbaechel"
    run install -m755 "$bld/bba/bbasm" "$PREFIX/bin/bbasm"
    run ln -sf nextpnr-himbaechel "$PREFIX/bin/nextpnr-xilinx"
    stamp_set nextpnr "$key"
}

write_wrapper() {
    local path=$1 body=$2
    [ "$DRY_RUN" = 1 ] && { echo "[dry] write $path"; return; }
    mkdir -p "$(dirname "$path")"
    printf '#!/usr/bin/env bash\nP="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"\n%s\n' "$body" > "$path"
    chmod 755 "$path"
}

step_prjxray() {
    say "prjxray tools + fasm (python)"
    local src="$CACHE/src/prjxray" bld="$CACHE/build/prjxray" key
    key="$(toml prjxray rev) $(toml fasm rev)"
    build_env
    if stamp_ok prjxray "$key" && [ -x "$PREFIX/bin/xc7frames2bit" ]; then
        echo "[cached] prjxray tools"
    else
        logged prjxray-cmake cmake -S "$src" -B "$bld" -G Ninja -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DPRJXRAY_BUILD_TESTING=OFF -Wno-dev
        logged prjxray-build ninja -C "$bld" -j"$JOBS" bitread xc7frames2bit xc7patch
        run mkdir -p "$PREFIX/bin" "$PREFIX/lib/ofx-python" "$PREFIX/libexec"
        for t in bitread xc7frames2bit xc7patch; do
            run install -m755 "$bld/tools/$t" "$PREFIX/bin/$t"
        done
        run rm -rf "$PREFIX/lib/ofx-python/prjxray" "$PREFIX/lib/ofx-python/fasm"
        run cp -a "$src/prjxray" "$PREFIX/lib/ofx-python/prjxray"
        run cp -a "$src/third_party/fasm/fasm" "$PREFIX/lib/ofx-python/fasm"
        run install -m644 "$src/utils/fasm2frames.py" "$PREFIX/libexec/fasm2frames"
        run install -m644 "$src/utils/bit2fasm.py" "$PREFIX/libexec/bit2fasm"
        stamp_set prjxray "$key"
    fi
    write_wrapper "$PREFIX/libexec/tabbypy3" 'export PYTHONPATH="$P/lib/ofx-python${PYTHONPATH:+:$PYTHONPATH}" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
exec "$P/env/bin/python3" "$@"'
    write_wrapper "$PREFIX/bin/fasm2frames" 'exec "$P/libexec/tabbypy3" "$P/libexec/fasm2frames" "$@"'
    write_wrapper "$PREFIX/bin/bit2fasm" 'exec "$P/libexec/tabbypy3" "$P/libexec/bit2fasm" "$@"'
    run mkdir -p "$PREFIX/py3bin"
    run ln -sf ../libexec/tabbypy3 "$PREFIX/py3bin/python3"
}

step_byteman() {
    say "byteman"
    local src="$CACHE/src/byteman" bld="$CACHE/build/byteman" key
    key="$(toml byteman rev)"
    if stamp_ok byteman "$key" && [ -x "$PREFIX/bin/byteman" ]; then
        echo "[cached] $PREFIX/bin/byteman"
        return
    fi
    build_env
    logged byteman-cmake cmake -S "$src" -B "$bld" -G Ninja -DCMAKE_BUILD_TYPE=Release
    logged byteman-build ninja -C "$bld" -j"$JOBS"
    run install -m755 "$bld/byteman" "$PREFIX/bin/byteman"
    stamp_set byteman "$key"
}

step_openfpgaloader() {
    say "openFPGALoader $(toml openfpgaloader tag) + --partial"
    local src="$CACHE/work/openfpgaloader-$VARIANT" bld="$CACHE/build/openfpgaloader-$VARIANT" key
    patched_tree openfpgaloader "$PATCHES/openfpgaloader" "$src"
    key="$(toml openfpgaloader rev) $(cat "$PATCHES"/openfpgaloader/[0-9]*.patch | sha256sum | cut -d' ' -f1)"
    if stamp_ok openfpgaloader "$key" && [ -x "$PREFIX/bin/openFPGALoader" ]; then
        echo "[cached] $PREFIX/bin/openFPGALoader"
        return
    fi
    build_env
    logged openfpgaloader-cmake cmake -S "$src" -B "$bld" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$PREFIX" -DENABLE_UDEV=OFF -DENABLE_LIBGPIOD=OFF
    logged openfpgaloader-build ninja -C "$bld" -j"$JOBS"
    logged openfpgaloader-install ninja -C "$bld" install
    stamp_set openfpgaloader "$key"
}

step_yosys() {
    case "$YOSYS" in
        none) say "yosys: skipped (--yosys none); put a yosys on PATH yourself" ;;
        oss-cad-suite)
            say "yosys from the pinned oss-cad-suite release"
            local url sha tgz
            url="$(toml oss-cad-suite url)"
            sha="$(toml oss-cad-suite sha256)"
            tgz="$CACHE/dl/$(basename "$url")"
            fetch_file "$url" "$tgz" "$sha"
            if stamp_ok oss-cad-suite "$sha" && [ -x "$PREFIX/opt/oss-cad-suite/bin/yosys" ]; then
                echo "[cached] $PREFIX/opt/oss-cad-suite"
            else
                run rm -rf "$PREFIX/opt/oss-cad-suite"
                run mkdir -p "$PREFIX/opt"
                logged oss-cad-suite-extract tar -xzf "$tgz" -C "$PREFIX/opt"
                stamp_set oss-cad-suite "$sha"
            fi
            yosys_plugins ;;
        source)
            say "yosys from source (experimental)"
            local src="$CACHE/src/yosys" bld="$CACHE/build/yosys" key
            key="$(toml yosys rev)"
            if stamp_ok yosys "$key" && [ -x "$PREFIX/opt/yosys/bin/yosys" ]; then
                echo "[cached] $PREFIX/opt/yosys"
                return
            fi
            build_env
            logged yosys-cmake cmake -S "$src" -B "$bld" -G Ninja -DCMAKE_BUILD_TYPE=Release \
                -DCMAKE_INSTALL_PREFIX="$PREFIX/opt/yosys" -DYOSYS_ENABLE_UNIT_TESTS=OFF \
                -DYOSYS_WITHOUT_SLANG=ON -DYOSYS_WITHOUT_TCL=ON -DYOSYS_WITHOUT_READLINE=ON \
                -DYOSYS_WITHOUT_EDITLINE=ON -DYOSYS_USE_BUNDLED_LIBS=ON
            logged yosys-build ninja -C "$bld" -j"$JOBS"
            logged yosys-install ninja -C "$bld" install
            stamp_set yosys "$key" ;;
        *) die "--yosys must be oss-cad-suite, source or none" ;;
    esac
}

plugin_cxx() {
    local out=$1; shift
    "$ENV/bin/x86_64-conda-linux-gnu-g++" -std=c++20 -fPIC -O2 -D_YOSYS_ '-DYOSYS_VER="0.70+186"' -DYOSYS_MAJOR=0 \
        -DYOSYS_MINOR=70 -DYOSYS_COMMIT=186 -I"$PREFIX/opt/oss-cad-suite/share/yosys/include" "$@" -shared -o "$out"
}

build_yosys_plugins() {
    local src=$1 gen=$2
    mkdir -p "$gen/techlibs/xilinx" "$PLUGINS"
    for p in xilinx_dsp xilinx_dsp48a xilinx_dsp_CREG xilinx_dsp_cascade; do
        "$ENV/bin/python3" -I "$src/passes/pmgen/pmgen.py" -o "$gen/techlibs/xilinx/${p}_pm.h" "$src/techlibs/xilinx/$p.pmg"
    done
    sed -e 's/XilinxDspPass() : Pass("xilinx_dsp"/XilinxDspPass() : Pass("xilinx_dsp_qor"/' \
        -e 's/XilinxDspPass/XilinxDspQorPass/g' "$src/techlibs/xilinx/xilinx_dsp.cc" > "$gen/xilinx_dsp_qor.cc"
    sed -e 's/Pass("clkbufmap",/Pass("clkbufmap_gapfix",/' -e 's/ClkbufmapPass/ClkbufmapGapfixPass/g' \
        "$src/passes/techmap/clkbufmap.cc" > "$gen/clkbufmap_gapfix.cc"
    cp "$src/techlibs/xilinx/xilinx_asyncreg.cc" "$gen/xilinx_asyncreg.cc"
    plugin_cxx "$PLUGINS/xilinx_dsp_qor.so" -I"$gen" "$gen/xilinx_dsp_qor.cc"
    plugin_cxx "$PLUGINS/xilinx_asyncreg.so" "$gen/xilinx_asyncreg.cc"
    plugin_cxx "$PLUGINS/clkbufmap_gapfix.so" "$gen/clkbufmap_gapfix.cc"
    for p in xilinx_dsp_qor xilinx_asyncreg clkbufmap_gapfix; do
        "$PREFIX/opt/oss-cad-suite/bin/yosys" -m "$PLUGINS/$p.so" -q -p "help $p" > /dev/null
        echo "plugin $p: $(sha256sum "$PLUGINS/$p.so" | cut -d' ' -f1)"
    done
}

yosys_plugins() {
    say "yosys plugins: $(ls "$PATCHES"/yosys/[0-9]*.patch | wc -l) patches on yosys $(toml yosys rev | cut -c1-9), built against the oss-cad-suite headers"
    local src="$CACHE/work/yosys-$VARIANT" key
    patched_tree yosys "$PATCHES/yosys" "$src"
    key="$(toml oss-cad-suite sha256) $(toml yosys rev) $(cat "$PATCHES"/yosys/[0-9]*.patch | sha256sum | cut -d' ' -f1)"
    if stamp_ok yosys-plugins "$key" && [ -f "$PLUGINS/xilinx_dsp_qor.so" ]; then
        echo "[cached] $PLUGINS"
        return
    fi
    logged yosys-plugins env -u LDFLAGS ENV="$ENV" PREFIX="$PREFIX" PLUGINS="$PLUGINS" bash -c \
        "$(declare -f plugin_cxx build_yosys_plugins); set -e; build_yosys_plugins '$src' '$CACHE/build/yosys-plugins'"
    stamp_set yosys-plugins "$key"
}

gen_chipdb() {
    local dev=$1 bin=$2 name=$3 meta=$4; shift 4
    local fam src="$CACHE/work/nextpnr-$VARIANT" out="$CACHE/chipdb" key
    fam="$(family_of "$dev")"
    key="$(toml nextpnr rev) $(cat "$PATCHES"/nextpnr/[0-9]*.patch | sha256sum | cut -d' ' -f1) $(toml prjxray-db rev)"
    key="$key $meta $([ "$meta" = "$CACHE/src/nextpnr-xilinx-meta" ] || series_key nextpnr-xilinx-meta) $*"
    if [ -f "$bin" ] && stamp_ok "$name" "$key $(sha256sum "$bin" | cut -d' ' -f1)"; then
        echo "[cached] $bin"
        return 1
    fi
    if [ "$DRY_RUN" = 0 ] && [ ! -d "$CACHE/src/prjxray-db/$fam" ]; then
        die "prjxray-db $fam is missing; run the sources step with --devices including $dev"
    fi
    run mkdir -p "$(dirname "$bin")" "$out"
    logged "$name-gen" env PYTHONDONTWRITEBYTECODE=1 "$ENV/bin/python3" \
        "$src/himbaechel/uarch/xilinx/gen/xilinx_gen.py" --xray "$CACHE/src/prjxray-db/$fam" --device "$dev" \
        --metadata "$meta/$fam" --bba "$out/$name.bba" "$@"
    logged "$name-bbasm" "$PREFIX/bin/bbasm" --le "$out/$name.bba" "$bin"
    [ "$DRY_RUN" = 1 ] && return 1
    rm -f "$out/$name.bba"
    stamp_set "$name" "$key $(sha256sum "$bin" | cut -d' ' -f1)"
}

check_chipdb() {
    local bin=$1 table=$2 dev=$3 what=$4 want got
    want="$(toml "$table" "$dev")"
    got="$(sha256sum "$bin" | cut -d' ' -f1)"
    if [ -n "$want" ] && [ "$got" = "$want" ]; then
        echo "   $bin sha256 $got = $what"
    elif [ -n "$want" ]; then
        echo "   WARNING $bin sha256 $got differs from $what ($want)"
    else
        echo "   $bin sha256 $got (no reference value)"
    fi
}

step_chipdb() {
    say "chipdbs: $DEVICES"
    local pristine="$CACHE/src/nextpnr-xilinx-meta" meta="$CACHE/work/nextpnr-xilinx-meta-$VARIANT"
    patched_meta "$meta"
    for dev in $DEVICES; do
        local bin="$CHIPDB_DIR/chipdb-$dev.bin"
        if gen_chipdb "$dev" "$bin" "chipdb-$dev" "$pristine"; then
            check_chipdb "$bin" chipdb-sha256 "$dev" "openXC7 nightly upstream-2026-11-04"
        fi
        grep -q "^$(family_of "$dev") " "$PATCHES/nextpnr-xilinx-meta/SERIES" || continue
        bin="$CHIPDB_DIR/ofx/chipdb-$dev.bin"
        if gen_chipdb "$dev" "$bin" "chipdb-$dev-ofx" "$meta"; then
            check_chipdb "$bin" chipdb-sha256-ofx "$dev" "the reference chipdb with the meta additions"
        fi
        local cal="$PATCHES/chipdb/cell-timing-$dev.json"
        [ -f "$cal" ] || continue
        bin="$CHIPDB_DIR/cal/chipdb-$dev.bin"
        if gen_chipdb "$dev" "$bin" "chipdb-$dev-cal" "$meta" --cell-timing "$cal"; then
            check_chipdb "$bin" chipdb-sha256-cal "$dev" "the reference calibrated chipdb"
        fi
    done
}

step_envsh() {
    say "env.sh and build info"
    [ "$DRY_RUN" = 1 ] && { echo "[dry] write $PREFIX/env.sh, $PREFIX/share/ofx/openxc7-BUILD-INFO.json"; return; }
    local ocs=""
    [ "$YOSYS" = oss-cad-suite ] && ocs='$OFX_PREFIX/opt/oss-cad-suite/bin:'
    [ "$YOSYS" = source ] && ocs='$OFX_PREFIX/opt/yosys/bin:'
    cat > "$PREFIX/env.sh" <<EOF
export OFX_PREFIX="$PREFIX"
export PATH="\$OFX_PREFIX/bin:${ocs}\$PATH:\$OFX_PREFIX/py3bin"
EOF
    mkdir -p "$PREFIX/share/ofx"
    cat > "$PREFIX/share/ofx/openxc7-BUILD-INFO.json" <<EOF
{
  "package-name": "open-dfx-xc7 ofx toolchain",
  "release-tag": "ofx-$(toml nextpnr rev | cut -c1-8)-$(cat "$PATCHES"/nextpnr/[0-9]*.patch | sha256sum | cut -c1-8)",
  "nextpnr-xilinx-revision": "$(toml nextpnr rev)",
  "nextpnr-patches": "$(cd "$PATCHES/nextpnr" && ls [0-9]*.patch | tr '\n' ' ' | sed 's/ $//')",
  "prjxray-db-revision": "$(toml prjxray-db rev)",
  "prjxray-revision": "$(toml prjxray rev)",
  "fasm-revision": "$(toml fasm rev)",
  "openfpgaloader-revision": "$(toml openfpgaloader rev)",
  "byteman-revision": "$(toml byteman rev)",
  "yosys": "$YOSYS",
  "yosys-patches": "$(cd "$PATCHES/yosys" && ls [0-9]*.patch | tr '\n' ' ' | sed 's/ $//')",
  "yosys-plugins": "$(cd "$PLUGINS" 2>/dev/null && ls *.so 2>/dev/null | tr '\n' ' ' | sed 's/ $//')",
  "prjxray-db-additions": "$(awk '{print $2}' "$PATCHES/prjxray-db/SERIES" | tr '\n' ' ' | sed 's/ $//')",
  "nextpnr-xilinx-meta-additions": "$(awk '{print $2}' "$PATCHES/nextpnr-xilinx-meta/SERIES" | tr '\n' ' ' | sed 's/ $//')",
  "chipdbs": "$(cd "$CHIPDB_DIR" 2>/dev/null && ls chipdb-*.bin 2>/dev/null | tr '\n' ' ' | sed 's/ $//')",
  "chipdbs-ofx": "$(cd "$CHIPDB_DIR/ofx" 2>/dev/null && ls chipdb-*.bin 2>/dev/null | tr '\n' ' ' | sed 's/ $//')",
  "chipdbs-cal": "$(cd "$CHIPDB_DIR/cal" 2>/dev/null && ls chipdb-*.bin 2>/dev/null | tr '\n' ' ' | sed 's/ $//')",
  "ofx-release": "$RELEASE"
}
EOF
    cp "$SOURCES" "$PREFIX/share/ofx/sources.toml"
    cp -r "$PATCHES" "$PREFIX/share/ofx/"
    echo "$RELEASE" > "$PREFIX/share/ofx/VERSION"
    echo "   source $PREFIX/env.sh"
}

say "open-dfx-xc7 install: prefix $PREFIX, cache $CACHE, devices '$DEVICES', yosys $YOSYS, jobs $JOBS$([ "$DRY_RUN" = 1 ] && echo ', DRY RUN (pass --run)')"
check_host
for s in $STEPS; do
    has_step "$s" || continue
    "step_$s"
done
say "done$([ "$DRY_RUN" = 1 ] && echo ' (dry run, nothing changed)')"
