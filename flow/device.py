import json
import os
import re
import sys
from pathlib import Path

CONFIG = {
    "root": Path(__file__).resolve().parent.parent,
    "part": "xc7a35tcsg324-1",
    "family": "artix7",
    "fabric": "xc7a50t",
    "env": {"part": "OFX_PART", "family": "OFX_FAMILY", "fabric": "OFX_FABRIC", "part_name": "OFX_PART_NAME",
            "db_root": "OFX_DB_ROOT"},
    "db": "toolchain/openxc7/share/nextpnr/external/prjxray-db",
    "extra_dbs": ("build/src/meta-openXC7-prjxray-db",),
    "chipdb_dir": "toolchain/openxc7/share/nextpnr/himbaechel/xilinx",
    "extra_chipdb_dirs": ("build/chipdb/k7",),
    "inventory": "XILINX-PARTS-INVENTORY.json",
    "families": ("artix7", "kintex7", "spartan7", "zynq7"),
}


def get(key):
    return os.environ.get(CONFIG["env"][key]) or CONFIG[key]


def db_root():
    env = os.environ.get(CONFIG["env"]["db_root"])
    return Path(env) if env else CONFIG["root"] / CONFIG["db"]


def part_name(part=None):
    env = os.environ.get(CONFIG["env"]["part_name"])
    if env and part is None:
        return env
    p = part or get("part")
    return re.sub(r"^xc", "", p).split("-")[0]


def chipdb(fabric=None):
    name = f"chipdb-{fabric or get('fabric')}.bin"
    main = CONFIG["root"] / CONFIG["chipdb_dir"] / name
    if main.exists():
        return main
    return next((CONFIG["root"] / d / name for d in CONFIG["extra_chipdb_dirs"] if (CONFIG["root"] / d / name).exists()), main)


def _yaml_map(path):
    out, key = {}, None
    for line in Path(path).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.fullmatch(r'"?([^":\s]+)"?:\s*', line)
        if m and not line.startswith(" "):
            key = m.group(1)
            out[key] = {}
            continue
        m = re.fullmatch(r'\s+(\w+):\s*"?\'?([^"\']*)"?\'?\s*', line)
        if m and key:
            out[key][m.group(1)] = m.group(2)
    return out


def resolve(part):
    roots = [CONFIG["root"] / CONFIG["db"]] + [CONFIG["root"] / d for d in CONFIG["extra_dbs"]]
    db = roots[0]
    inv_path = CONFIG["root"] / CONFIG["chipdb_dir"] / CONFIG["inventory"]
    inv = json.loads(inv_path.read_text())["parts"] if inv_path.exists() else {}
    family = inv.get(part, {}).get("family")
    if family is None:
        family = next((f for f in CONFIG["families"] if (db / f / part / "part.json").exists()), None)
    if family is None or not (db / family / part / "part.json").exists():
        hit = next(((r, f) for r in roots[1:] for f in CONFIG["families"] if (r / f / part / "part.json").exists()), None)
        if hit:
            db, family = hit
    if family is None:
        raise ValueError(f"part {part}: not in the openXC7 parts inventory or prjxray-db")
    parts = _yaml_map(db / family / "mapping" / "parts.yaml")
    devices = _yaml_map(db / family / "mapping" / "devices.yaml")
    dev = parts.get(part, {}).get("device")
    fabric = devices.get(dev, {}).get("fabric") if dev else None
    if fabric is None:
        raise ValueError(f"part {part}: no device/fabric entry in {db / family / 'mapping'}")
    problems = []
    for f, what in ((db / family / part / "part.json", "part.json"), (db / family / part / "part.yaml", "part.yaml"),
                    (db / family / fabric / "tilegrid.json", "tilegrid.json"), (chipdb(fabric), "chipdb")):
        if not f.exists():
            problems.append(f"missing {what}: {f}")
    return {"part": part, "family": family, "device": dev, "fabric": fabric, "part_name": part_name(part),
            "chipdb": str(chipdb(fabric)), "db_root": str(db), "db_extra": db != roots[0], "generated": inv.get(part, {}).get("generated"), "problems": problems}


def env(part):
    r = resolve(part)
    e = {CONFIG["env"]["part"]: r["part"], CONFIG["env"]["family"]: r["family"], CONFIG["env"]["fabric"]: r["fabric"],
         CONFIG["env"]["part_name"]: r["part_name"]}
    if r["db_extra"]:
        e[CONFIG["env"]["db_root"]] = r["db_root"]
    return e


if __name__ == "__main__":
    print(json.dumps(resolve(sys.argv[1] if len(sys.argv) > 1 else get("part")), indent=1))
