import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import ROOT

CONFIG = {
    "bambu": ROOT / "toolchain" / "bambu" / "install" / "bin" / "bambu",
    "path_extra": [ROOT / "toolchain" / "oss-cad-suite" / "bin"],
    "out_dir": "hls",
    "clock_ns": 10.0,
    "devices": {"artix7": "xc7a100t-1csg324", "spartan7": "xc7a100t-1csg324", "zynq7": "xc7z020-1clg484",
                "kintex7": "xc7z045-2ffg900"},
    "default_device": "xc7a100t-1csg324",
    "args": ["--generate-interface=INFER"],
    "sim_args": ["--simulate", "--simulator=VERILATOR"],
    "keys": {"top", "sources", "testbench", "clock_ns", "device", "args", "include"},
    "c_exts": (".c", ".cc", ".cpp", ".cxx"),
    "module_re": r"^\s*module\s+\\?(\w+)",
    "cycles_re": r"(?:Total cycles|cycles)\s*[:=]?\s*(\d+)",
}


class HlsError(Exception):
    pass


def bambu():
    b = Path(os.environ.get("OFX_BAMBU", CONFIG["bambu"]))
    return b


def env():
    e = dict(os.environ)
    e["PATH"] = os.pathsep.join([str(p) for p in CONFIG["path_extra"]] + [e.get("PATH", "")])
    return e


def kernels(proj):
    raw = proj.raw.get("hls")
    if not raw:
        return []
    if isinstance(raw, dict):
        raw = [raw]
    out, tops = [], set()
    for i, k in enumerate(raw):
        bad = set(k) - CONFIG["keys"]
        if bad:
            raise HlsError(f"[[hls]] #{i + 1}: unknown keys {sorted(bad)} (known: {sorted(CONFIG['keys'])})")
        for need in ("top", "sources"):
            if need not in k:
                raise HlsError(f"[[hls]] #{i + 1} needs '{need}'")
        top = str(k["top"])
        if not re.fullmatch(r"[A-Za-z_]\w*", top):
            raise HlsError(f"[[hls]] #{i + 1}: top {top!r} is not a C identifier")
        if top in tops:
            raise HlsError(f"[[hls]] top {top} given twice")
        tops.add(top)
        srcs = [proj.path(s) for s in k["sources"]]
        tb = proj.path(k["testbench"]) if k.get("testbench") else None
        inc = [proj.path(s) for s in k.get("include", [])]
        miss = [str(f) for f in srcs + ([tb] if tb else []) if not f.exists()]
        if miss:
            raise HlsError(f"[[hls]] {top}: missing files {miss}")
        if any(f.suffix.lower() not in CONFIG["c_exts"] for f in srcs):
            raise HlsError(f"[[hls]] {top}: sources must be C/C++ files ({', '.join(CONFIG['c_exts'])})")
        clk = float(k.get("clock_ns") or (min(proj.clocks.values()) if proj.clocks else CONFIG["clock_ns"]))
        dev = k.get("device") or CONFIG["devices"].get(proj.device.get("family"), CONFIG["default_device"])
        args = [str(x) for x in k.get("args", [])]
        out.append({"top": top, "sources": srcs, "testbench": tb, "include": inc, "clock_ns": clk, "device": dev,
                    "args": args})
    return out


def inputs(k):
    files = list(k["sources"])
    for d in k["include"]:
        files += sorted(p for p in Path(d).rglob("*") if p.is_file()) if Path(d).is_dir() else [Path(d)]
    return files


def key(k):
    h = hashlib.sha256()
    for f in inputs(k):
        h.update(str(f).encode())
        h.update(Path(f).read_bytes())
    b = bambu()
    extra = {"top": k["top"], "clock_ns": k["clock_ns"], "device": k["device"], "args": CONFIG["args"] + k["args"],
             "bambu": str(b), "bambu_size": b.stat().st_size if b.exists() else None}
    h.update(json.dumps(extra, sort_keys=True).encode())
    return h.hexdigest()[:16]


def command(k, tb=None):
    cmd = [str(bambu())] + [str(s) for s in k["sources"]] + [f"--top-fname={k['top']}",
                                                             f"--clock-period={k['clock_ns']:g}",
                                                             f"--device-name={k['device']}"]
    for d in k["include"]:
        cmd.append(f"-I{d}")
    cmd += CONFIG["args"] + k["args"]
    if tb:
        cmd += [f"--generate-tb={tb}"] + CONFIG["sim_args"]
    return cmd


def prefix_modules(text, top):
    """Bambu names its library modules generically (register_STD, ADD_EXPR_FU, ...): prefix every module but the
    top with '<top>__' so that two kernels, or a kernel and the user's RTL, can share a build."""
    mods = [m for m in re.findall(CONFIG["module_re"], text, re.M) if m != top]
    if not mods:
        return text
    alt = "|".join(sorted((re.escape(m) for m in set(mods)), key=len, reverse=True))
    text = re.sub(rf"^(\s*module\s+)({alt})\b", rf"\g<1>{top}__\g<2>", text, flags=re.M)
    return re.sub(rf"^(\s*)({alt})(\s*(?:#|\\?[A-Za-z_]))", rf"\g<1>{top}__\g<2>\g<3>", text, flags=re.M)


def run_bambu(k, work, cmd, log):
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    with open(log, "w") as f:
        f.write(" ".join(cmd) + "\n")
        f.flush()
        r = subprocess.run(cmd, cwd=work, stdout=f, stderr=subprocess.STDOUT, env=env())
    return r.returncode


def generate(proj, out_dir, dry):
    """Run Bambu for every [[hls]] kernel; return (verilog files, input files)."""
    ks = kernels(proj)
    if not ks:
        return [], []
    if not dry and not bambu().exists():
        raise HlsError(f"Bambu not found at {bambu()} (see docs/hls.md, or set OFX_BAMBU)")
    out_dir = Path(out_dir)
    outs, ins = [], []
    for k in ks:
        ins += inputs(k)
        kk = key(k) if not dry or bambu().exists() else "dry"
        out = out_dir / k["top"] / f"{k['top']}_{kk}.v"
        outs.append(out)
        if out.exists():
            print(f"[skip] hls {k['top']}: {out.name} exists")
            continue
        cmd = command(k)
        print(f"[{'dry' if dry else 'run'}] hls {k['top']} (Bambu, {k['clock_ns']:g} ns, {k['device']}) -> {out}",
              flush=True)
        if dry:
            continue
        work = out_dir / k["top"] / "work"
        log = out_dir / k["top"] / f"bambu_{kk}.log"
        rc = run_bambu(k, work, cmd, log)
        gen = work / f"{k['top']}.v"
        if rc != 0 or not gen.exists():
            sys.stdout.write("".join(log.read_text(errors="replace").splitlines(True)[-30:]))
            raise HlsError(f"Bambu failed for {k['top']} (exit {rc}), see {log}")
        out.write_text(prefix_modules(gen.read_text(), k["top"]))
    if not dry:
        seen = {}
        for o in outs:
            for m in re.findall(CONFIG["module_re"], o.read_text(), re.M):
                if m in seen and seen[m] != o:
                    raise HlsError(f"module {m} is defined by both {seen[m].name} and {o.name}")
                seen[m] = o
    return outs, ins


def cycles(text):
    m = re.findall(CONFIG["cycles_re"], text, re.I)
    return int(m[-1]) if m else None


def simulate(proj, out_dir, dry):
    """Bambu co-simulation of every kernel with a testbench: the C testbench runs against the generated RTL in
    Verilator. Returns {top: {"rc": exit code, "cycles": simulated cycles or None, "log": path}}."""
    res = {}
    for k in kernels(proj):
        if not k["testbench"]:
            print(f"ofx hls: {k['top']} has no testbench, skipped")
            continue
        cmd = command(k, tb=k["testbench"])
        work = Path(out_dir) / k["top"] / "sim"
        log = Path(out_dir) / k["top"] / "sim.log"
        print(f"[{'dry' if dry else 'run'}] hls sim {k['top']}: {k['testbench'].name} against the RTL  > {log}",
              flush=True)
        if dry:
            continue
        if not bambu().exists():
            raise HlsError(f"Bambu not found at {bambu()} (see docs/hls.md, or set OFX_BAMBU)")
        rc = run_bambu(k, work, cmd, log)
        res[k["top"]] = {"rc": rc, "cycles": cycles(log.read_text(errors="replace")), "log": str(log)}
    return res
