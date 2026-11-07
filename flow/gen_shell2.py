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
    "centre_y": None,
    "lanes": "ABCD",
}


def shell_ports(spec):
    decl = lambda d, n, w: f"{d} wire {'' if w == 1 else f'[{w - 1}:0] '}{n}"
    ports = [f"input wire {spec['clk']}"] + [decl("input", n, w) for n, w in spec["inputs"]] + \
            [decl("output", n, w) for n, w in spec["outputs"]]
    return ports, decl


def write_partpin_shell(spec, out, registered):
    ports, decl = shell_ports(spec)
    widths = dict(spec["outputs"])
    bad = [r for r in registered if r not in widths]
    if bad:
        sys.exit(f"gen_shell2: --register {bad}: not an output of the spec")
    lines = [f"module rm_slot ({', '.join(ports)});"]
    for n, w in spec["outputs"]:
        lines.append(f"    {decl('', 'c_' + n, w).strip()};")
    conns = [f".{n}({n})" for n, _ in spec["inputs"]] + [f".{n}(c_{n})" for n, _ in spec["outputs"]]
    if spec.get("core_clk"):
        conns.insert(0, f".{spec['clk']}({spec['clk']})")
    lines.append(f"    rm_core core ({', '.join(conns)});")
    nreg = 0
    for n, w in spec["outputs"]:
        if n not in registered:
            lines.append(f"    assign {n} = c_{n};")
            continue
        for i in range(w):
            ref = (lambda b: b if w == 1 else f"{b}[{i}]")
            lines.append(f"    FDRE r_{n}_{i} (.C({spec['clk']}), .CE(1'b1), .R(1'b0), .D({ref('c_' + n)}), .Q({ref(n)}));")
            nreg += 1
    lines.append("endmodule")
    Path(out).write_text("\n".join(lines) + "\n")
    stub = ["(* blackbox *)", f"module rm_slot ({', '.join(ports)});", "endmodule"]
    Path(out).with_name("rm_stub.v").write_text("\n".join(stub) + "\n")
    nin = sum(w for _, w in spec["inputs"])
    nout = sum(w for _, w in spec["outputs"])
    print(f"wrote {out} (+ rm_stub.v): partition-pin shell, {nin} inputs, {nout} outputs ({nreg} registered by "
          f"unplaced FFs), 0 anchors, 0 blockers")


def write_union_core(spec, out, rms, select):
    widths = dict(spec["inputs"] + spec["outputs"])
    if select not in dict(spec["inputs"]):
        sys.exit(f"gen_shell2: --union-select {select}: not an input of the spec")
    nsel = max(1, (len(rms) - 1).bit_length())
    if nsel > widths[select]:
        sys.exit(f"gen_shell2: {len(rms)} cores need {nsel} select bits, {select} has {widths[select]}")
    decl = lambda d, n, w: f"{d} wire {'' if w == 1 else f'[{w - 1}:0] '}{n}"
    ports = [decl("input", n, w) for n, w in spec["inputs"]] + [decl("output", n, w) for n, w in spec["outputs"]]
    lines = [f"module rm_core ({', '.join(ports)});"]
    for rm in rms:
        for n, w in spec["outputs"]:
            lines.append(f"    {decl('', f'u_{rm}_{n}', w).strip()};")
        conns = [f".{n}({n})" for n, _ in spec["inputs"]] + [f".{n}(u_{rm}_{n})" for n, _ in spec["outputs"]]
        lines.append(f"    rm_core_{rm} core_{rm} ({', '.join(conns)});")
    hi = widths[select] - 1
    sel = f"{select}[{hi}:{hi - nsel + 1}]" if widths[select] > 1 else select
    for n, w in spec["outputs"]:
        expr = f"u_{rms[-1]}_{n}"
        for k in range(len(rms) - 2, -1, -1):
            expr = f"({sel} == {nsel}'d{k}) ? u_{rms[k]}_{n} : {expr}"
        lines.append(f"    assign {n} = {expr};")
    lines.append("endmodule")
    Path(out).write_text("\n".join(lines) + "\n")
    print(f"wrote {out}: rm_core selecting among {len(rms)} cores ({', '.join('rm_core_' + r for r in rms)}) by "
          f"{sel}; a placement model only")


def write_greybox(spec, out, buffers, clock_leaf=False):
    ports, _ = shell_ports(spec)
    lines = [f"module rm_slot ({', '.join(ports)});"]
    ref = lambda n, w, i: n if w == 1 else f"{n}[{i}]"
    if clock_leaf:
        lines.append(f"    (* keep *) FDRE gb_clock_leaf (.C({spec['clk']}), .CE(1'b1), .R(1'b0), .D(1'b0), .Q());")
    if buffers:
        for n, w in spec["inputs"]:
            for i in range(w):
                lines.append(f"    (* keep *) LUT1 #(.INIT(2'b10)) gb_in_{n}_{i} (.I0({ref(n, w, i)}), .O());")
        for n, w in spec["outputs"]:
            for i in range(w):
                lines.append(f"    (* keep *) LUT1 #(.INIT(2'b00)) gb_out_{n}_{i} (.I0(1'b0), .O({ref(n, w, i)}));")
    lines.append("endmodule")
    Path(out).write_text("\n".join(lines) + "\n")
    nin = sum(w for _, w in spec["inputs"])
    nout = sum(w for _, w in spec["outputs"])
    if buffers:
        print(f"wrote {out}: greybox with port buffers, {nin} input LUT1s with no load, {nout} output LUT1s "
              f"tied to 0, none placed")
    elif clock_leaf:
        print(f"wrote {out}: greybox, {nin} inputs with no load, {nout} outputs with no driver, 1 unplaced clock-leaf "
              f"FF (D=0, Q unused)")
    else:
        print(f"wrote {out}: greybox, {nin} inputs with no load, {nout} outputs with no driver, 0 cells")


def main():
    ap = argparse.ArgumentParser(description="Write an RM shell from a port spec: pinned input anchors, "
                                             "output anchor+FF pairs, region blockers; rm_core is combinational")
    ap.add_argument("spec", help='json: {"clk": "clk", "inputs": [["valid", 1], ...], "outputs": [["rd", 32], ...]}')
    ap.add_argument("out")
    ap.add_argument("--region", default=CONFIG["region"])
    ap.add_argument("--no-keepout", dest="keepout", action="store_false",
                    help="do not freeze static LUTRAM-capable tiles that share frames with the region")
    ap.add_argument("--centre-y", type=int, default=CONFIG["centre_y"])
    ap.add_argument("--partpins", action="store_true",
                    help="no anchors and no blockers: the ports cross the region at partition pins (nextpnr "
                         "-o partition-pins); outputs are combinational unless named in --register")
    ap.add_argument("--register", action="append", default=[],
                    help="with --partpins: output registered by an unplaced FF of the module (repeatable)")
    ap.add_argument("--greybox", action="store_true",
                    help="the ports only: no cells, inputs unloaded, outputs undriven (static build before the "
                         "partition pins are placed, flow/partpin_assign.py)")
    ap.add_argument("--buffers", action="store_true",
                    help="with --greybox: one unplaced LUT1 per port bit (input -> LUT1 with no load, LUT1 tied to 0 "
                         "-> output), so that placement sees the region's ports")
    ap.add_argument("--clock-leaf", action="store_true",
                    help="with --greybox: one unplaced FF on the clock (D=0, Q unused), so that the static clock "
                         "tree reaches the region as it does for every module")
    ap.add_argument("--union", nargs="+", metavar="RM",
                    help="write rm_core selecting among rm_core_<RM> (one per RM) instead of a shell: a placement "
                         "model that has every module's paths")
    ap.add_argument("--union-select", default="funct", help="with --union: input whose top bits select the core")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text())
    if a.union:
        write_union_core(spec, a.out, a.union, a.union_select)
        return
    if a.greybox:
        write_greybox(spec, a.out, a.buffers, a.clock_leaf)
        return
    if a.partpins:
        write_partpin_shell(spec, a.out, a.register)
        return
    grid = region.load_grid()
    smap = replay_dump.site_map(grid)
    x0, y0, x1, y1 = region.parse_slice_range(a.region)
    cy = a.centre_y if a.centre_y is not None else (y0 + y1 + 1) // 2
    sites = {}
    for site, (tile, local) in smap.items():
        m = re.fullmatch(r"SLICE_X(\d+)Y(\d+)", site)
        if m and x0 <= int(m.group(1)) <= x1 and y0 <= int(m.group(2)) <= y1:
            sites[(int(m.group(1)), int(m.group(2)))] = (tile, local)
    order = sorted(sites, key=lambda xy: (abs(xy[1] - cy), xy[1], xy[0]))
    ins = [(n, i) for n, w in spec["inputs"] for i in range(w)]
    outs = [(n, i) for n, w in spec["outputs"] for i in range(w)]
    in_pos, out_pos = {}, {}
    sb = spec.get("slice_by")
    if sb:
        tiles_xy = {}
        for xy, (tile, local) in sites.items():
            tiles_xy.setdefault(tile, {})[local] = xy
        torder = sorted(tiles_xy, key=lambda t: min(abs(xy[1] - cy) for xy in tiles_xy[t].values()))
        bin_ = [n for n, w in spec["inputs"] if w == sb]
        bout = [n for n, w in spec["outputs"] if w == sb]
        per_tile = 4 // max(1, len(bin_))
        k = 0
        for t in torder:
            if k >= sb:
                break
            sx0, sx1 = tiles_xy[t]["SLICE_X0Y0"], tiles_xy[t]["SLICE_X1Y0"]
            lane = 0
            for j in range(per_tile):
                if k >= sb:
                    break
                for n in bin_:
                    in_pos[(n, k)] = (sx0, lane)
                    lane += 1
                for m, n in enumerate(bout):
                    out_pos[(n, k)] = (sx1, j * len(bout) + m)
                k += 1
        used_xy = {p[0] for p in in_pos.values()} | {p[0] for p in out_pos.values()}
        order = [xy for xy in order if xy not in used_xy and sites[xy][0] not in {sites[u][0] for u in used_xy}]
    rest_in = [x for x in ins if x not in in_pos]
    rest_out = [x for x in outs if x not in out_pos]
    n_in_sl = -(-len(rest_in) // 4)
    n_out_sl = -(-len(rest_out) // 4)
    if n_in_sl + n_out_sl > len(order):
        sys.exit("gen_shell2: region too small for the shell")
    for k, x in enumerate(rest_in):
        in_pos[x] = (order[k // 4], k % 4)
    for k, x in enumerate(rest_out):
        out_pos[x] = (order[n_in_sl + k // 4], k % 4)
    in_sl = sorted({p[0] for p in in_pos.values()})
    out_sl = sorted({p[0] for p in out_pos.values()})

    def bel(xy, b):
        tile, local = sites[xy]
        return f"{tile}/{local}.{b}"

    def ref(n, w, i):
        return n if w == 1 else f"{n}[{i}]"

    widths = dict(spec["inputs"] + spec["outputs"])
    decl = lambda d, n, w: f"{d} wire {'' if w == 1 else f'[{w - 1}:0] '}{n}"
    ports = [f"input wire {spec['clk']}"] + [decl("input", n, w) for n, w in spec["inputs"]] + \
            [decl("output", n, w) for n, w in spec["outputs"]]
    lines = [f"module rm_slot ({', '.join(ports)});"]
    for n, w in spec["inputs"]:
        lines.append(f"    {decl('', 'a_' + n, w).strip()};")
    for n, w in spec["outputs"]:
        lines.append(f"    {decl('', 'c_' + n, w).strip()};")
        lines.append(f"    {decl('', 'e_' + n, w).strip()};")
    for n, i in ins:
        xy, ln = in_pos[(n, i)]
        b = bel(xy, CONFIG["lanes"][ln] + "6LUT")
        lines.append(f'    (* keep, BEL = "{b}" *) LUT1 #(.INIT(2\'b10)) ain_{n}_{i} '
                     f"(.I0({ref(n, widths[n], i)}), .O({ref('a_' + n, widths[n], i)}));")
    conns = [f".{n}(a_{n})" for n, _ in spec["inputs"]] + [f".{n}(c_{n})" for n, _ in spec["outputs"]]
    if spec.get("core_clk"):
        conns.insert(0, f".{spec['clk']}({spec['clk']})")
    lines.append(f"    rm_core core ({', '.join(conns)});")
    for n, i in outs:
        xy, ln = out_pos[(n, i)]
        lane = CONFIG["lanes"][ln]
        lines.append(f'    (* keep, BEL = "{bel(xy, lane + "6LUT")}" *) LUT1 #(.INIT(2\'b10)) aout_{n}_{i} '
                     f"(.I0({ref('c_' + n, widths[n], i)}), .O({ref('e_' + n, widths[n], i)}));")
        lines.append(f'    (* keep, BEL = "{bel(xy, lane + "FF")}" *) FDRE q_{n}_{i} '
                     f"(.C({spec['clk']}), .CE(1'b1), .R(1'b0), .D({ref('e_' + n, widths[n], i)}), .Q({ref(n, widths[n], i)}));")
    used_tiles = {sites[xy][0] for xy in in_sl + out_sl}
    nb = 0
    for xy in sorted(sites):
        tile, local = sites[xy]
        if tile in used_tiles or local != "SLICE_X0Y0":
            continue
        used_tiles.add(tile)
        lines.append(f'    (* keep, BEL = "{tile}/{local}.A6LUT" *) LUT1 #(.INIT(2\'b00)) blk{nb} (.I0(), .O());')
        nb += 1
    nk = 0
    if a.keepout:
        for tname in sorted(region.shared_frame_tiles(grid, a.region)):
            t = grid[tname]
            if not tname.startswith("CLBLM"):
                continue
            lines.append(f'    (* keep, BEL = "X{t["grid_x"]}Y{t["grid_y"]}/SLICE_X0Y0.A6LUT" *) LUT1 #(.INIT(2\'b00)) '
                         f"kout{nk} (.I0(), .O());")
            nk += 1
    lines.append("endmodule")
    Path(a.out).write_text("\n".join(lines) + "\n")
    stub = [f"(* blackbox *)", f"module rm_slot ({', '.join(ports)});", "endmodule"]
    Path(a.out).with_name("rm_stub.v").write_text("\n".join(stub) + "\n")
    print(f"wrote {a.out} (+ rm_stub.v): {len(ins)} input anchors in {len(in_sl)} slices, {len(outs)} output FFs in "
          f"{len(out_sl)} slices, {nb} blockers, {nk} shared-frame keep-outs{', bit-sliced by ' + str(sb) if sb else ''}")


if __name__ == "__main__":
    main()
