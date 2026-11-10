"""Arc dataset from Vivado exact imports: every routed sink pin of our placements (and Vivado's own, vref) with
driver/sink cell type, BEL, tile grid position, fanout and Vivado's routed SLOW_MAX net delay (net_delays.txt).
Output: ~/open-dfx-xc7/build/dtab/arcs/<run>.tsv.gz"""
import gzip, json, re, sys, os
from collections import defaultdict
from pathlib import Path
V = Path("/mnt/c/Users/finnf/open-dfx-xc7-vivado")
E, S = V / "build/exact", V / "designs/exact"
OUT = Path("/home/finnf/open-dfx-xc7/build/dtab/arcs"); OUT.mkdir(parents=True, exist_ok=True)
TG = "/home/finnf/open-dfx-xc7/toolchain/openxc7/share/nextpnr/external/prjxray-db/artix7/xc7a50t/tilegrid.json"
tg = json.load(open(TG))
site = {}
for tn, t in tg.items():
    for s in t.get("sites", {}):
        site[s] = (t["grid_x"], t["grid_y"], tn)
OUTP = re.compile(r"^(O|O5|O6|Q|CO|DO|DOADO|DOBDO|DOPADOP|DOPBDOP|P|PCOUT|ACOUT|BCOUT|CARRYCASCOUT|MULTSIGNOUT|Q31|CASCADEOUT\w*|SPO|DPO|DOA|DOB|DOC|DOD)(\[\d+\])?$")
DES = ("rv_soc", "bram", "rv_big", "rv_mul")

def netlist(fn):
    d = json.loads(Path(fn).read_text())
    m = next(v for v in d["modules"].values() if len(v.get("cells", {})) > 10)
    cells = {n: c for n, c in m["cells"].items() if not c["type"].startswith("$")}
    pin, drv, nsink = {}, {}, defaultdict(int)
    for n, c in cells.items():
        pd = c.get("port_directions", {})
        for p, bits in c["connections"].items():
            for i, b in enumerate(bits):
                if not isinstance(b, int):
                    continue
                pn = p if len(bits) == 1 else f"{p}[{i}]"
                out = pd.get(p) == "output" if pd else bool(OUTP.match(pn))
                if out:
                    drv[b] = (n, pn)
                else:
                    pin[(n, pn)] = b
                    nsink[b] += 1
    return cells, pin, drv, nsink

def place_txt(fn):
    out = {}
    for ln in Path(fn).read_text().splitlines():
        m = re.match(r"\{?(.*?)\}?\s+(\S+)/(\S+)$", ln)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out

def cells_txt(fn):
    out = {}
    for ln in Path(fn).read_text().splitlines():
        p = ln.split("\t")
        if len(p) >= 4 and p[2]:
            out[p[0]] = (p[2], p[3].split(".")[-1])
    return out

def one(name):
    o = OUT / f"{name}.tsv.gz"
    if o.exists():
        return "skip"
    e = E / name
    if not (e / "net_delays.txt").exists() or not (e / "slack.txt").exists():
        return "nodata"
    d = next(x for x in DES if name.startswith(x + "_"))
    if "_vref" in name:
        ref = f"{d}_p5_ua_dxy{'_dq' if d == 'rv_mul' else ''}_s1_exact"
        nl, pl = S / ref / "netlist.json", cells_txt(e / "cells.txt") if (e / "cells.txt").exists() else None
    else:
        nl = S / name / "netlist.json"
        pl = place_txt(S / name / "place.txt") if (S / name / "place.txt").exists() else None
    if pl is None or not nl.exists():
        return "nosrc"
    cells, pin, drv, nsink = netlist(nl)
    rank = {}
    if (e / "paths_noicap.txt").exists():
        for k, ln in enumerate((e / "paths_noicap.txt").read_text().splitlines()):
            f = ln.split("\t")
            if len(f) >= 4:
                for p in f[3].split():
                    rank.setdefault(p, k)
    rows = []
    for ln in (e / "net_delays.txt").read_text(errors="replace").splitlines():
        f = ln.split("\t")
        if len(f) < 2 or not f[1].strip().lstrip("-").isdigit():
            continue
        c, p = f[0].rsplit("/", 1)
        b = pin.get((c, p))
        if b is None or b not in drv:
            continue
        dc, dp = drv[b]
        if dc not in pl or c not in pl or dc not in cells or c not in cells:
            continue
        st, dt = cells[dc]["type"], cells[c]["type"]
        if st.startswith("BUFG") or st in ("IBUF", "IBUFG") and p == "C":
            continue
        (ss, sb), (ds, db) = pl[dc], pl[c]
        a, z = site.get(ss), site.get(ds)
        if a is None or z is None:
            continue
        rel = "site" if ss == ds else ("tile" if a[2] == z[2] else "inter")
        rows.append("\t".join(map(str, (d, st, sb, dp, dt, db, p, a[0], a[1], z[0], z[1], rel, nsink[b], f[1].strip(), rank.get(f[0], -1)))))
    with gzip.open(o, "wt") as fh:
        fh.write("\n".join(rows) + "\n")
    return len(rows)

if __name__ == "__main__":
    pat = re.compile(r"^(rv_soc|bram|rv_big|rv_mul)_p5_.*_exact$")
    names = sorted(n for n in os.listdir(E) if pat.match(n))
    if len(sys.argv) > 1:
        names = [n for n in names if re.search(sys.argv[1], n)]
    tot = 0
    for n in names:
        try:
            r = one(n)
        except Exception as ex:
            r = f"ERR {ex}"
        print(n, r, flush=True)
