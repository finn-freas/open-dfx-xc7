r"""Re-time finished DFX configuration builds with the hard-block timer (matrix row 15).

Every DFX configuration build (a `*_n`, `*_n_taf` or `grey_s` directory of flow/build_pr_native.py) was timed by
nextpnr without `-o hardblock-timing`, so the ICAPE2 (and DSP48E1) pins were untimed. This replays each build's own
placement and routing (flow/replay_dump.py, -o preplaced / -o prerouted) with a nextpnr that has
`-o hardblock-timing` built on the same patch stack as the DFX variants (variant pp3hb: the partpin3 stack plus
docs/drafts/nextpnr-hardblock-timing.patch; the release binary rel01tr packs CARRY4/LUTs differently and refuses the
replayed BELs) and the same netlist, XDC, device and chipdb, then checks
that the replay reproduces the placement and routing exactly (replay_dump of the replayed routed JSON equal to the
original's). The timer of every number is nextpnr's; `ofx timing --build OUT` prints the Vivado-style report.

  dfx_retime.py OUT BUILD_DIR... [--run] [--report-paths N]
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "dry_run": True,
    "nextpnr": ROOT / "build" / "nextpnr-build" / "pp3hb" / "nextpnr-himbaechel",
    "npwait": ROOT / "ofx" / "npwait.sh",
    "max_nextpnr": 2,
    "top": "rv_soc",
    "report_paths": 0,
}

DROP_VALUE = {"--write", "--report", "--json", "--chipdb", "--device", "--seed", "--freq"}
DROP_OPT = {"xdc", "fasm", "preplaced", "prerouted", "partition-pins", "partition-pins-route", "pinfeed"}


def build_cmd(d, top):
    log = (d / f"{top}.log").read_text()
    m = re.search(r"^\[run\] nextpnr: (.*)$", log, re.M)
    if not m:
        sys.exit(f"{d}: no nextpnr command line in {top}.log")
    cmd = shlex.split(m.group(1))
    val = {}
    opts = {}
    flags = []
    i = 1
    while i < len(cmd):
        c = cmd[i]
        if c in DROP_VALUE:
            val[c] = cmd[i + 1]
            i += 2
        elif c == "-o":
            k, _, v = cmd[i + 1].partition("=")
            opts[k] = v
            i += 2
        else:
            flags.append(c)
            i += 1
    return val, opts, flags


def replay_files(routed, prefix, log):
    with open(log, "w") as f:
        r = subprocess.run([sys.executable, str(ROOT / "flow" / "replay_dump.py"), str(routed), str(prefix)],
                           stdout=f, stderr=subprocess.STDOUT)
    return r.returncode == 0


def routes(prerouted):
    """Per net, the set of (wire, pip) pairs of a .prerouted file; the strength field and the order of the wires
    differ between a build and its replay (the replay's wires are locked) and are ignored."""
    out = {}
    for ln in prerouted.read_text().splitlines():
        net, _, rest = ln.partition("\t")
        f = rest.split(";")
        out[net] = frozenset((f[i], f[i + 1]) for i in range(0, len(f) - 2, 3))
    return out


def sinkless(routed_json, nets):
    """Nets of the routed json that no cell input uses (e.g. partition-pin nets a module leaves unconnected)."""
    m = json.loads(Path(routed_json).read_text())
    top = next(v for v in m["modules"].values() if v.get("attributes", {}).get("top"))
    bits = {n: v["bits"][0] for n, v in top["netnames"].items() if n in nets and v["bits"]}
    used = set()
    for c in top["cells"].values():
        for port, bb in c.get("connections", {}).items():
            if c.get("port_directions", {}).get(port) == "input":
                used.update(b for b in bb if isinstance(b, int))
    return {n for n in nets if n in bits and bits[n] not in used}


def route_check(ref, chk, rec, routed_json):
    a, b = routes(ref), routes(chk)
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    rec["route_identical"] = not diff
    rec["route_diff_nets"] = len(diff)
    rec["route_diff_examples"] = diff[:5]
    rec["route_diff_replay_subset"] = all(b.get(k, frozenset()) <= a.get(k, frozenset()) for k in diff)
    rec["route_diff_sinkless"] = len(sinkless(routed_json, set(diff))) if diff else 0
    return not diff


def timing_equivalent(rec):
    """Same placement, and for every net whose routing differs the replay kept a subset of the original's wires.
    nextpnr routed every sink in the replay and a route tree has one path per sink, so each sink's path is the
    original's: only branches that reach no sink were dropped (partition-pin branches; route_diff_sinkless counts
    the differing nets that have no sink at all)."""
    return bool(rec.get("place_identical")) and bool(rec.get("route_identical") or rec.get("route_diff_replay_subset"))


def retime(d, out, top, rp, dry):
    val, opts, flags = build_cmd(d, top)
    xdc = Path(opts["xdc"])
    if not xdc.exists():
        alt = d.parent / xdc.name
        if not alt.exists():
            sys.exit(f"{d}: XDC {xdc} not found")
        xdc = alt
    rec = {"build": str(d), "orig_fmax": None, "dropped_flags": [f for f in flags if f.startswith("--")]}
    rep = d / "report.json"
    if rep.exists():
        rec["orig_fmax"] = {k: v["achieved"] for k, v in json.loads(rep.read_text())["fmax"].items()}
    o = out / d.name
    if dry:
        print(f"[dry] {d.name}: replay_dump {d / (top + '_routed.json')}; {CONFIG['nextpnr'].name} -o hardblock-timing "
              f"--report-paths {rp} -o preplaced/prerouted (replay), xdc {xdc}")
        return rec
    done = o / "retime.json"
    if done.exists():
        old = json.loads(done.read_text())
        chk = o / "chk.prerouted"
        if "error" not in old and "route_diff_sinkless" not in old and chk.exists():
            same_place = (o / "ref.preplaced").read_bytes() == (o / "chk.preplaced").read_bytes()
            same_route = route_check(o / "ref.prerouted", chk, old, d / f"{top}_routed.json")
            old["place_identical"] = same_place
            old["place_route_identical"] = same_place and same_route
            done.write_text(json.dumps(old, indent=1))
        return old
    o.mkdir(parents=True, exist_ok=True)
    ref = o / "ref"
    if not replay_files(d / f"{top}_routed.json", ref, o / "replay_dump.log"):
        rec["error"] = f"replay_dump failed ({o / 'replay_dump.log'})"
        return rec
    loc = Path(str(ref) + ".loc.xdc")
    rx = o / "replay.xdc"
    base = xdc.read_text()
    have = set(re.findall(r"set_property\s+LOC\s+\S+\s+\[get_cells\s+(.*?)\]\s*$", base, re.M))
    extra = [l for l in (loc.read_text().splitlines() if loc.exists() else [])
             if not (m := re.search(r"\[get_cells\s+(.*?)\]\s*$", l)) or m.group(1) not in have]
    rx.write_text(base + "".join(l + "\n" for l in extra))
    cmd = [str(CONFIG["npwait"]), "--device", val["--device"], "--json", val["--json"], "-o", f"xdc={rx}",
           "--seed", val.get("--seed", "1"), "--freq", val.get("--freq", "100"),
           "--write", str(o / f"{top}_routed.json"), "-o", f"fasm={o / (top + '.fasm')}", "--report", str(o / "report.json"),
           "-o", "hardblock-timing", "-o", f"preplaced={ref}.preplaced", "-o", f"prerouted={ref}.prerouted",
           "--chipdb", val["--chipdb"]] + (["--report-paths", str(rp)] if rp else []) + [f for f in flags if f == "--timing-allow-fail"]
    rec["cmd"] = cmd
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(CONFIG["nextpnr"]), OFX_MAX_NEXTPNR=str(CONFIG["max_nextpnr"]))
    t0 = time.time()
    with open(o / "nextpnr.log", "w") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env)
    rec["seconds"] = round(time.time() - t0, 1)
    if r.returncode:
        rec["error"] = f"nextpnr exit {r.returncode} ({o / 'nextpnr.log'})"
        done.write_text(json.dumps(rec, indent=1))
        return rec
    chk = o / "chk"
    replay_files(o / f"{top}_routed.json", chk, o / "replay_dump_chk.log")
    same_place = Path(str(ref) + ".preplaced").read_bytes() == Path(str(chk) + ".preplaced").read_bytes()
    same_route = route_check(Path(str(ref) + ".prerouted"), Path(str(chk) + ".prerouted"), rec,
                             d / f"{top}_routed.json")
    rec["place_identical"] = same_place
    rec["place_route_identical"] = same_place and same_route
    rep = json.loads((o / "report.json").read_text())
    rec["hardblock_fmax"] = {k: v["achieved"] for k, v in rep["fmax"].items()}
    lg = (o / "nextpnr.log").read_text()
    m = re.search(r"hardblock-timing: SDF timing on (\d+) DSP48E1/ICAPE2 cell", lg)
    rec["hardblock_cells"] = int(m.group(1)) if m else None
    done.write_text(json.dumps(rec, indent=1))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("builds", nargs="+")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--top", default=CONFIG["top"])
    ap.add_argument("--report-paths", type=int, default=CONFIG["report_paths"],
                    help="needs a nextpnr with docs/drafts/nextpnr-timing-report.patch")
    ap.add_argument("--nextpnr", help="nextpnr binary (default: variant pp3hb, the partpin3 stack plus "
                                      "docs/drafts/nextpnr-hardblock-timing.patch, so the packer matches the DFX builds)")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    if a.nextpnr:
        CONFIG["nextpnr"] = Path(a.nextpnr).resolve()
    out = Path(a.out).resolve()
    recs = [retime(Path(b).resolve(), out, a.top, a.report_paths, dry) for b in a.builds]
    if dry:
        return
    (out / "summary.json").write_text(json.dumps(recs, indent=1))
    bad = 0
    for r in recs:
        name = Path(r["build"]).name
        if "error" in r:
            print(f"FAIL {name}: {r['error']}")
            bad = 1
            continue
        r["timing_equivalent"] = timing_equivalent(r)
        ok = r["timing_equivalent"]
        bad |= not ok
        extra = "" if r.get("place_route_identical") else (
            f" (placement identical {r.get('place_identical')}; {r.get('route_diff_nets')} net(s) differ, "
            f"{r.get('route_diff_sinkless')} of them without sinks, replay a subset of the original: "
            f"{r.get('route_diff_replay_subset')}, e.g. {r.get('route_diff_examples')})")
        print(f"{'PASS' if ok else 'FAIL'} {name}: replay identical {r.get('place_route_identical')}, timing-equivalent "
              f"{ok}{extra}; hard-block cells timed {r['hardblock_cells']}; "
              f"nextpnr Fmax without hardblock-timing {r['orig_fmax']}, with {r['hardblock_fmax']}")
    sys.exit(bad)


if __name__ == "__main__":
    main()
