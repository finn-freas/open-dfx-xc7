#!/usr/bin/env bash
set -u
R="$(cd "$(dirname "$0")/.." && pwd)"
NEXTPNR="${NEXTPNR:?nextpnr-himbaechel}"
OUT="${OUT:-$R/build/slicem_check}"
D="$R/designs/gap/slicem_ram64x1s"
T="$R/toolchain/openxc7"
export OFX_NEXTPNR_BIN="$NEXTPNR" OFX_MAX_NEXTPNR="${OFX_MAX_NEXTPNR:-1}"
mkdir -p "$OUT"
np() {
    local o=$1; shift; mkdir -p "$o"
    "$R/ofx/npwait.sh" --device xc7a35tcsg324-1 --json "$OUT/net.json" -o xdc="$D/arty_a7_35t.xdc" --seed 1 \
        -o fasm="$o/net.fasm" --write "$o/routed.json" --chipdb "$T/share/nextpnr/himbaechel/xilinx/chipdb-xc7a50t.bin" \
        "$@" > "$o/nextpnr.log" 2>&1
}
"$R/toolchain/oss-cad-suite/bin/yosys" -q -p "read_verilog -sv $D/slicem_ram64x1s.v; synth_xilinx -flatten -abc9 -arch xc7 -top slicem_ram64x1s; write_json $OUT/net.json" > "$OUT/yosys.log" 2>&1 ||
    { echo "FAIL yosys"; exit 1; }
np "$OUT/free" || { echo "FAIL free build ($OUT/free/nextpnr.log)"; exit 1; }
python3 - "$OUT" "$T/share/nextpnr/external/prjxray-db/artix7/xc7a50t/tilegrid.json" <<'PY' || { echo "FAIL replay files"; exit 1; }
import json, re, sys
out, tg = sys.argv[1], json.load(open(sys.argv[2]))
site_of = {}
for t, v in tg.items():
    sl = sorted((s for s, ty in v["sites"].items() if ty.startswith("SLICE")), key=lambda s: int(re.search(r"X(\d+)", s).group(1)))
    for i, s in enumerate(sl):
        site_of[s] = (f"X{v['grid_x']}Y{v['grid_y']}", i, t, sl)
m = list(json.load(open(f"{out}/free/routed.json"))["modules"].values())[0]
ok, bad, ram = [], [], None
for n, c in m["cells"].items():
    b = c["attributes"].get("NEXTPNR_BEL", "")
    site, _, bel = b.partition("/")
    if site not in site_of:
        continue
    tile, idx, tname, sl = site_of[site]
    ok.append(f"{n}\t{tile}/SLICE_X{idx}Y0.{bel}")
    if n == "u_ram/ADDR":
        ram = (tile, idx, tname, bel)
assert ram and ram[1] == 0 and ram[2].startswith("CLBLM"), ram
open(f"{out}/ok.preplaced", "w").write("\n".join(ok) + "\n")
# move the LUT-RAM's whole position (its LUTs and flipflops, letter ram[3][0]) from slice 0 to slice 1 of the tile
pos = ram[3][0]
dst = [l for l in ok if f"{ram[0]}/SLICE_X1Y0.{pos}" in l]
assert not dst, dst
bad = [l.replace(f"{ram[0]}/SLICE_X0Y0.{pos}", f"{ram[0]}/SLICE_X1Y0.{pos}") for l in ok]
open(f"{out}/bad.preplaced", "w").write("\n".join(bad) + "\n")
open(f"{out}/ram_tile.txt", "w").write(f"{ram[2]} {ram[3]} {ram[0]}\n")
PY
read -r TNAME RBEL TILE < "$OUT/ram_tile.txt"
fail=0
for tag in ok bad; do
    o="$OUT/$tag"
    np "$o" -o preplaced="$OUT/$tag.preplaced"; rc=$?
    routed=$(grep -c "Running router2\|router2 time\|Routing globals" "$o/nextpnr.log")
    first=$(grep -m1 -E "ERROR|Assert|terminate|illegal placement" "$o/nextpnr.log" | cut -c1-170)
    if [ $tag = ok ]; then
        if [ $rc = 0 ] && grep -q "$TNAME.SLICEM_X0.${RBEL%6LUT}LUT.RAM" "$o/net.fasm"; then
            echo "PASS ok: replay with the LUT-RAM in the SLICEM of $TNAME builds"
        else echo "FAIL ok: replay does not build (rc $rc) $first"; fail=1; fi
    else
        refused=$(grep -c "illegal placement in logic tile $TILE\|is not valid for cell 'u_ram/ADDR'" "$o/nextpnr.log")
        crashed=$(grep -c "Assertion failure\|terminate called" "$o/nextpnr.log")
        if [ $rc != 0 ] && [ "$refused" != 0 ] && [ "$crashed" = 0 ] && [ "$routed" = 0 ]; then
            echo "PASS bad: LUT-RAM moved to the SLICEL half of $TNAME refused by the placement check: $first"
        else
            echo "FAIL bad: LUT-RAM in the SLICEL half of $TNAME: rc $rc, routing reached $routed, $first"; fail=1
        fi
    fi
done
exit $fail
