"""Cache of nextpnr's xilinx delay matrix (`-o delay-matrix=FILE`).

nextpnr (himbaechel xilinx, delay_matrix.cc) measures a routing-delay table before placement by running
Dijkstra over the device from three fixed sources. The table depends only on the binary, the chipdb and the
part (measure_from() never looks at the design or at bound wires), so it is the same for every design on a
device. It is written as integers and loading it recomputes the edge rates exactly as a fresh build does, so a
cached run places and routes exactly like a fresh one (checked on .frames, docs/runtime.md).

Key: binary and chipdb (resolved path, size, mtime), part, and every nextpnr argument that is not a
per-design file, seed or frequency. Unknown binaries (no way to tell their default chipdb) are not cached.
The shared copy is only replaced atomically, and nextpnr only ever sees a private copy in the build directory.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path

CONFIG = {
    "dir": Path(__file__).resolve().parent.parent / "build" / "cache" / "delay_matrix",
    "env_off": "OFX_DM_CACHE",
    "wrappers": ("npwait.sh", "runtime_np.sh"),
    "real_bin_env": "OFX_NEXTPNR_BIN",
    "file": "delay_matrix.txt",
    "skip_args": ("--json", "--write", "--report", "--seed", "--freq", "--log", "--sdc", "--pcf", "--threads"),
    "skip_flags": ("--parallel-refine", "--timing-allow-fail"),
    "skip_opts": ("xdc=", "fasm=", "preplaced=", "fixed_routing=", "partition_pins="),
}


def _ident(p):
    p = Path(p).resolve()
    st = p.stat()
    return [str(p), st.st_size, st.st_mtime_ns]


def _toolchain_wrapper(p):
    try:
        head = Path(p).read_bytes()[:4096]
    except OSError:
        return None
    if not head.startswith(b"#!") or b"libexec/nextpnr-xilinx" not in head:
        return None
    return Path(p).resolve().parent.parent


def _filtered(args):
    out, skip = [], False
    for i, x in enumerate(args):
        if skip:
            skip = False
            continue
        if x in CONFIG["skip_flags"]:
            continue
        if x in CONFIG["skip_args"]:
            skip = True
            continue
        if x == "-o" and i + 1 < len(args) and args[i + 1].startswith(CONFIG["skip_opts"]):
            skip = True
            continue
        out.append(x)
    return out


def key(npnr, part, fabric, args, chipdb=None):
    if os.environ.get(CONFIG["env_off"]) == "0":
        return None
    if any("delay-matrix" in a or "delayMatrix" in a for a in args):
        return None
    real = Path(npnr)
    if real.name in CONFIG["wrappers"]:
        env = os.environ.get(CONFIG["real_bin_env"])
        if not env:
            return None
        real = Path(env)
    top = _toolchain_wrapper(real)
    if top is not None:
        binary = top / "libexec" / "nextpnr-xilinx"
        if chipdb is None:
            chipdb = top / "share" / "nextpnr" / "himbaechel" / "xilinx" / f"chipdb-{fabric}.bin"
    else:
        binary = real
    if chipdb is None or not Path(chipdb).exists() or not binary.exists():
        return None
    blob = json.dumps({"bin": _ident(binary), "chipdb": _ident(chipdb), "part": part, "args": _filtered(args)},
                      sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


def prepare(k, out):
    """Returns the nextpnr option value for this run, or None without a key."""
    if not k:
        return None
    local = Path(out) / CONFIG["file"]
    shared = CONFIG["dir"] / f"{k}.txt"
    if local.exists():
        local.unlink()
    if shared.exists():
        shutil.copyfile(shared, local)
    return str(local)


def publish(k, out):
    local = Path(out) / CONFIG["file"]
    if not k or not local.exists():
        return
    shared = CONFIG["dir"] / f"{k}.txt"
    if shared.exists():
        return
    CONFIG["dir"].mkdir(parents=True, exist_ok=True)
    tmp = shared.with_suffix(f".{os.getpid()}.tmp")
    shutil.copyfile(local, tmp)
    os.replace(tmp, shared)
