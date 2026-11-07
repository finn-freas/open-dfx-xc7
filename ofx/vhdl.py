import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from . import ROOT

CONFIG = {
    "yosys": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "yosys",
    "plugin": "ghdl",
    "std": "08",
    "stds": ("87", "93", "93c", "00", "02", "08"),
    "exts": (".vhd", ".vhdl"),
    "entity_re": r"^\s*entity\s+(\w+)\s+is\b",
    "ref_re": r"\bentity\s+\w+\s*\.\s*(\w+)|^\s*\w+\s*:\s*(?:component\s+)?(\w+)\s*(?:generic|port)\s+map\b",
    "module_re": r"^\s*module\s+\\?(\w+)",
    "out_dir": "vhdl",
}


class VhdlError(Exception):
    pass


def is_vhdl(f):
    return Path(f).suffix.lower() in CONFIG["exts"]


def strip_comments(text):
    return re.sub(r"--[^\n]*", "", text)


def entities(files):
    out = []
    for f in files:
        out += [m.lower() for m in re.findall(CONFIG["entity_re"], strip_comments(Path(f).read_text(errors="replace")),
                                              re.M | re.I)]
    return out


def references(files):
    refs = set()
    for f in files:
        for a, b in re.findall(CONFIG["ref_re"], strip_comments(Path(f).read_text(errors="replace")), re.M | re.I):
            refs.add((a or b).lower())
    return refs


def roots(files):
    ents = entities(files)
    refs = references(files)
    return [e for e in ents if e not in refs]


def units_for(files, top, units):
    if units:
        return [u.lower() for u in units]
    ents = entities(files)
    if top and top.lower() in ents:
        return [top.lower()]
    r = roots(files)
    if not r:
        raise VhdlError(f"no VHDL entity found in {[str(f) for f in files]}")
    return r


def check_std(std):
    if std not in CONFIG["stds"]:
        raise VhdlError(f"vhdl_std must be one of {list(CONFIG['stds'])}, not {std!r}")
    return std


def gen_args(generics):
    out = []
    for k, v in sorted((generics or {}).items()):
        if not re.fullmatch(r"\w+", str(k)) or not re.fullmatch(r"[\w.\-+#\"']+", str(v)):
            raise VhdlError(f"vhdl_generics: bad entry {k!r} = {v!r}")
        out.append(f"-g{k}={v}")
    return out


def script(files, unit, std, out, generics=None):
    names = " ".join(str(f) for f in files)
    g = "".join(f"{x} " for x in gen_args(generics))
    return f"plugin -i {CONFIG['plugin']}; ghdl --std={std} {g}{names} -e {unit}; write_verilog {out}"


def key(files, unit, std, generics=None):
    h = hashlib.sha256()
    for f in files:
        h.update(str(f).encode())
        h.update(Path(f).read_bytes())
    extra = {"unit": unit, "std": std, "yosys": str(CONFIG["yosys"])}
    if generics:
        extra["generics"] = {str(k): str(v) for k, v in sorted(generics.items())}
    h.update(json.dumps(extra).encode())
    return h.hexdigest()[:16]


def convert(files, units, std, out_dir, dry, tag="vhdl", generics=None):
    files = [Path(f) for f in files]
    out_dir = Path(out_dir)
    outs = []
    for unit in units:
        out = out_dir / f"{tag}_{unit}_{key(files, unit, std, generics)}.v"
        log = out.with_suffix(".log")
        outs.append(out)
        cmd = [str(CONFIG["yosys"]), "-q", "-l", str(log), "-p", script(files, unit, std, out, generics)]
        if out.exists():
            print(f"[skip] vhdl {unit}: {out.name} exists")
            continue
        print(f"[{'dry' if dry else 'run'}] vhdl {unit} (GHDL --std={std}) -> {out}", flush=True)
        if dry:
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if r.returncode != 0 or not out.exists():
            out.unlink(missing_ok=True)
            sys.stdout.write(r.stdout)
            raise VhdlError(f"GHDL/yosys failed for unit {unit} (exit {r.returncode}), see {log}")
    if not dry:
        seen = {}
        for o in outs:
            for m in re.findall(CONFIG["module_re"], o.read_text(), re.M):
                if m in seen:
                    raise VhdlError(f"module {m} is defined by both {seen[m].name} and {o.name}: two VHDL roots share an "
                                    f"entity; set [project] vhdl_units to a single root")
                seen[m] = o
    return outs
