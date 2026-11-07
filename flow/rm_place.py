import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region
import replay_dump

CONFIG = {
    "region": "SLICE_X12Y100:SLICE_X15Y149",
    "module": "rm_slot",
    "lanes": "ABCD",
    "ff_types": ["FDRE", "FDSE", "FDCE", "FDPE"],
    "lut_types": ["LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6"],
    "ignore_types": ["$scopeinfo"],
    "packed_carry_suffix": "$split$muxcy0$PACKED_CARRY4$",
}

CTRL = {"FDRE": "R", "FDSE": "S", "FDCE": "CLR", "FDPE": "PRE"}


class Slices:
    def __init__(self, spec, smap):
        x0, y0, x1, y1 = region.parse_slice_range(spec)
        self.sites = {}
        for site, (tile, local) in smap.items():
            m = re.fullmatch(r"SLICE_X(\d+)Y(\d+)", site)
            if m and x0 <= int(m.group(1)) <= x1 and y0 <= int(m.group(2)) <= y1:
                self.sites[(int(m.group(1)), int(m.group(2)))] = f"{tile}/{local}"
        self.used = set()
        self.ctrl = {}
        self.carry = set()

    def bel(self, xy, b):
        return f"{self.sites[xy]}.{b}"

    def free(self, xy, b):
        return self.bel(xy, b) not in self.used

    def take(self, xy, b):
        self.used.add(self.bel(xy, b))
        return self.bel(xy, b)

    def mark_pinned(self, bel):
        self.used.add(bel)
        site, _, b = bel.rpartition(".")
        for xy, s in self.sites.items():
            if s == site and b.endswith("FF"):
                self.ctrl.setdefault(xy, "pinned")


def drivers(cells):
    out = {}
    for name, c in cells.items():
        dirs = c.get("port_directions", {})
        for p, bits in c["connections"].items():
            if dirs.get(p) == "output":
                for i, b in enumerate(bits):
                    if isinstance(b, int):
                        out[b] = (name, p, i)
    return out


def fanout(cells):
    out = {}
    for c in cells.values():
        dirs = c.get("port_directions", {})
        for p, bits in c["connections"].items():
            if dirs.get(p) == "input":
                for b in bits:
                    if isinstance(b, int):
                        out[b] = out.get(b, 0) + 1
    return out


def main():
    ap = argparse.ArgumentParser(description="Pin every cell of a small RM netlist to legal bels inside the region")
    ap.add_argument("rm_json")
    ap.add_argument("out_json")
    ap.add_argument("--region", default=CONFIG["region"])
    a = ap.parse_args()
    out = Path(a.out_json)
    if out.exists():
        print(f"[skip] {out} exists")
        return
    d = json.loads(Path(a.rm_json).read_text())
    m = d["modules"][CONFIG["module"]]
    cells = m["cells"]
    for c in cells.values():
        if c["type"] == "INV":
            c["type"] = "LUT1"
            c["parameters"] = {"INIT": "01"}
            c["port_directions"] = {"I0": "input", "O": "output"}
            c["connections"] = {"I0": c["connections"]["I"], "O": c["connections"]["O"]}
    sl = Slices(a.region, replay_dump.site_map(region.load_grid()))
    for c in cells.values():
        if "BEL" in c["attributes"]:
            sl.mark_pinned(c["attributes"]["BEL"])
    pinned_xy = [xy for xy, s in sl.sites.items() if any(u.startswith(s + ".") for u in sl.used)]
    if pinned_xy:
        cx = sum(x for x, _ in pinned_xy) / len(pinned_xy)
        cy = sum(y for _, y in pinned_xy) / len(pinned_xy)
    else:
        cx = cy = 0
    near = lambda xy: (abs(xy[1] - cy) + abs(xy[0] - cx), xy)
    todo = {n: c for n, c in cells.items() if "BEL" not in c["attributes"] and c["type"] not in CONFIG["ignore_types"]}
    bad = [f"{n} ({c['type']})" for n, c in todo.items()
           if c["type"] not in CONFIG["lut_types"] + CONFIG["ff_types"] + ["CARRY4"]]
    if bad:
        sys.exit(f"rm_place: unsupported cell types: {bad[:10]}")
    drv = drivers(cells)
    fo = fanout(cells)
    placed = {}
    lut_at = {}
    carry_at = {}
    carries = {n: c for n, c in todo.items() if c["type"] == "CARRY4"}
    nxt = {}
    has_prev = set()
    for n, c in carries.items():
        co3 = c["connections"]["CO"][3]
        for n2, c2 in carries.items():
            if c2["connections"]["CI"][0] == co3 and isinstance(co3, int):
                nxt[n] = n2
                has_prev.add(n2)
    chains = []
    for n in carries:
        if n in has_prev:
            continue
        ch = [n]
        while ch[-1] in nxt:
            ch.append(nxt[ch[-1]])
        chains.append(ch)
    cols = sorted({x for x, _ in sl.sites}, key=lambda x: (x % 2 == 0, x))
    for ch in chains:
        done = False
        starts = sorted(((x, y) for x, y in sl.sites if x in cols), key=near)
        for x, y0 in starts:
            rows = [(x, y0 + k) for k in range(len(ch))]
            if not all(r in sl.sites and sl.free(r, "CARRY4") and all(sl.free(r, l + "6LUT") for l in CONFIG["lanes"])
                       and r not in sl.ctrl and r not in sl.carry for r in rows):
                continue
            for cname, r in zip(ch, rows):
                placed[cname] = sl.take(r, "CARRY4")
                carry_at[cname] = r
                for i, s in enumerate(carries[cname]["connections"]["S"]):
                    src = drv.get(s)
                    if src and src[0] in todo and cells[src[0]]["type"] in CONFIG["lut_types"] and src[0] not in placed:
                        placed[src[0]] = sl.take(r, CONFIG["lanes"][i] + "6LUT")
                        lut_at[src[0]] = (r, CONFIG["lanes"][i])
                sl.carry.add(r)
            done = True
            break
        if not done:
            sys.exit(f"rm_place: no room for a carry chain of {len(ch)}")
    free_luts = [(xy, l) for xy in sorted(sl.sites, key=near) for l in CONFIG["lanes"]
                 if sl.free(xy, l + "6LUT") and xy not in sl.carry and sl.ctrl.get(xy) != "pinned"]
    site_xy = {s: xy for xy, s in sl.sites.items()}

    def pos_of(cell):
        b = placed.get(cell) or cells[cell]["attributes"].get("BEL")
        return site_xy.get(b.rpartition(".")[0]) if b else None

    sinks = {}
    for cn, c in cells.items():
        dirs = c.get("port_directions", {})
        for p, bits in c["connections"].items():
            if dirs.get(p) == "input":
                for b in bits:
                    if isinstance(b, int):
                        sinks.setdefault(b, []).append(cn)

    def neighbours(n):
        c = cells[n]
        dirs = c.get("port_directions", {})
        out = []
        for p, bits in c["connections"].items():
            for b in bits:
                if not isinstance(b, int):
                    continue
                if dirs.get(p) == "input" and b in drv:
                    out.append(drv[b][0])
                elif dirs.get(p) == "output":
                    out += sinks.get(b, [])
        return [q for q in (pos_of(x) for x in out if x != n) if q]

    luts = [n for n, c in todo.items() if c["type"] in CONFIG["lut_types"] and n not in placed]
    luts.sort(key=lambda n: -len(neighbours(n)))
    for n in luts:
        if not free_luts:
            sys.exit("rm_place: out of LUTs")
        nb = neighbours(n)
        if nb:
            k = min(range(len(free_luts)), key=lambda i: sum(abs(free_luts[i][0][0] - x) + abs(free_luts[i][0][1] - y)
                                                             for x, y in nb))
        else:
            k = 0
        xy, l = free_luts.pop(k)
        placed[n] = sl.take(xy, l + "6LUT")
        lut_at[n] = (xy, l)
    for n, c in todo.items():
        if c["type"] not in CONFIG["ff_types"]:
            continue
        cn = c["connections"]
        key = (c["type"], str(cn.get("C")), str(cn.get("CE")), str(cn.get(CTRL[c["type"]])))
        dbit = cn["D"][0]
        src = drv.get(dbit) if isinstance(dbit, int) else None
        spot = None
        must = None
        if src and src[0] in lut_at and src[1] == "O":
            must = lut_at[src[0]]
        elif src and src[0] in carry_at and src[1] == "O" and fo.get(dbit, 0) == 1:
            must = (carry_at[src[0]], CONFIG["lanes"][src[2]])
        if src and src[0] in cells and "BEL" in cells[src[0]]["attributes"] and src[0] not in placed and src[1] == "O":
            sys.exit(f"rm_place: FF {n} is fed by pinned {src[0]}; nextpnr pairs them, pin the FF next to it in the RTL")
        if must is not None:
            xy, l = must
            if not (sl.free(xy, l + "FF") and sl.ctrl.get(xy) in (None, key)):
                sys.exit(f"rm_place: FF {n} must sit with its driver {src[0]} in lane {l}, but that FF bel or control set is taken")
            spot = must
        if spot is None:
            for xy in sorted(sl.sites, key=near):
                if sl.ctrl.get(xy) not in (None, key) or xy in sl.carry:
                    continue
                if any(not sl.free(xy, l + "6LUT") for l in CONFIG["lanes"]) and sl.ctrl.get(xy) is None:
                    continue
                for l in CONFIG["lanes"]:
                    if sl.free(xy, l + "FF"):
                        spot = (xy, l)
                        break
                if spot:
                    break
        if spot is None:
            sys.exit("rm_place: out of FF slots")
        sl.ctrl[spot[0]] = key
        placed[n] = sl.take(spot[0], spot[1] + "FF")
    for n, b in placed.items():
        cells[n]["attributes"]["BEL"] = b
    out.write_text(json.dumps(d))
    packer = [f"{n}{CONFIG['packed_carry_suffix']}\t{placed[n]}" for n in carries]
    Path(str(out) + ".packer.preplaced").write_text("".join(l + "\n" for l in packer))
    kinds = {}
    for n in placed:
        kinds[cells[n]["type"]] = kinds.get(cells[n]["type"], 0) + 1
    print(f"rm_place: pinned {len(placed)} cells {kinds}, {len(chains)} carry chain(s)")


if __name__ == "__main__":
    main()
