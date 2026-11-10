import json
import re
import sys
import tomllib
from pathlib import Path

from . import BOARDS, FLOW, ROOT
from . import defaults, vhdl

sys.path.insert(0, str(FLOW))
import device

CONFIG = {
    "file": "ofx.toml",
    "build_dir": "build",
    "seed": 1,
    "seeds": "auto",
    "seeds_auto_max": 3,
    "partpins": "auto",
    "variants": {"auto": "partpin2", "anchors": "router"},
    "timed_variants": {"auto": "pp3hb28_t", "anchors": "pp3hb28_t"},
    "module": "rm_slot",
    "decoupler_rtl": ROOT / "designs" / "common" / "dfx_decoupler.v",
    "report_paths": 0,
    "timing_nextpnr": "build/nextpnr-build/timrep/nextpnr-himbaechel",
}


class ProjectError(Exception):
    pass


def find(start=None):
    p = Path(start or ".").resolve()
    if p.is_file():
        return p
    for d in [p] + list(p.parents):
        if (d / CONFIG["file"]).exists():
            return d / CONFIG["file"]
    raise ProjectError(f"no {CONFIG['file']} in {p} or its parents (create one with `ofx new`)")


def load_board(name):
    f = BOARDS / f"{name}.toml"
    if not f.exists():
        known = sorted(x.stem for x in BOARDS.glob("*.toml"))
        raise ProjectError(f"unknown board {name}; presets: {known}")
    b = tomllib.loads(f.read_text())
    b["file"] = str(f)
    return b


def boards():
    return {f.stem: tomllib.loads(f.read_text()) for f in sorted(BOARDS.glob("*.toml"))}


def ports_spec(raw, base):
    if isinstance(raw, str):
        f = (base / raw).resolve()
        return json.loads(f.read_text()), f
    return {"clk": raw.get("clk", "clk"), "inputs": [list(x) for x in raw["inputs"]],
            "outputs": [list(x) for x in raw["outputs"]], **({"slice_by": raw["slice_by"]} if "slice_by" in raw else {})}, None


def port_regexes(spec):
    out = [spec["clk"]]
    for n, w in spec["inputs"] + spec["outputs"]:
        out.append(n if w == 1 else rf"{n}\[\d+\]")
    return out


class Project:
    def __init__(self, path):
        self.file = Path(path).resolve()
        self.dir = self.file.parent
        self.raw = tomllib.loads(self.file.read_text())
        p = self.raw.get("project", {})
        for k in ("name", "top"):
            if k not in p:
                raise ProjectError(f"{self.file}: [project] needs '{k}'")
        self.name, self.top = p["name"], p["top"]
        self.board = load_board(p["board"]) if p.get("board") else None
        self.part = p.get("part") or (self.board or {}).get("board", {}).get("part")
        if not self.part:
            raise ProjectError(f"{self.file}: give [project] part or board")
        try:
            self.device = device.resolve(self.part)
        except ValueError as e:
            raise ProjectError(str(e))
        if self.device["problems"]:
            raise ProjectError(f"part {self.part}: " + "; ".join(self.device["problems"]))
        self.seed = int(p.get("seed", CONFIG["seed"]))
        sv = p.get("seeds", CONFIG["seeds"])
        m = re.fullmatch(r"auto(?::(\d+))?", sv) if isinstance(sv, str) else None
        try:
            self.seeds = (int(m.group(1) or CONFIG["seeds_auto_max"]) if m else int(sv))
        except (TypeError, ValueError):
            self.seeds = 0
        self.seeds_auto = bool(m) and self.seeds > 1
        if self.seeds < 1 or isinstance(sv, (bool, float)):
            raise ProjectError(f"{self.file}: seeds must be a number >= 1, \"auto\" or \"auto:N\" (got {sv!r})")
        self.sources = [self.path(s) for s in p.get("sources", [])]
        self.constraints = [self.path(s) for s in p.get("constraints", [])]
        self.build = self.path(p.get("build_dir", CONFIG["build_dir"]))
        self.clocks = {k: float(v) for k, v in self.raw.get("clocks", {}).items()}
        try:
            self.vhdl_std = vhdl.check_std(str(p.get("vhdl_std", vhdl.CONFIG["std"])))
        except vhdl.VhdlError as e:
            raise ProjectError(f"{self.file}: {e}")
        self.vhdl_units = list(p.get("vhdl_units", []))
        self.vhdl_generics = dict(p.get("vhdl_generics", {}))
        tm = self.raw.get("timing", {})
        self.timing = {"nextpnr": self.tool_path(tm["nextpnr"]) if tm.get("nextpnr") else None,
                       "report_paths": int(tm.get("report_paths", CONFIG["report_paths"]))}
        if self.timing["report_paths"] and not self.timing["nextpnr"]:
            raise ProjectError(f"{self.file}: [timing] report_paths needs [timing] nextpnr, a build with "
                               f"docs/drafts/nextpnr-timing-report.patch (e.g. {CONFIG['timing_nextpnr']})")
        self.build_opts = dict(self.raw.get("build", {}))
        try:
            defaults.options(self.build_opts)
        except defaults.DefaultsError as e:
            raise ProjectError(f"{self.file}: {e}")
        self.dfx = self._dfx(self.raw.get("dfx"))
        missing = [str(f) for f in self.sources + self.constraints if not f.exists()]
        if missing:
            raise ProjectError(f"{self.file}: missing files {missing}")
        if not self.sources:
            raise ProjectError(f"{self.file}: [project] sources is empty")
        if not self.constraints:
            raise ProjectError(f"{self.file}: [project] constraints is empty")

    def path(self, s):
        return (self.dir / s).resolve()

    def tool_path(self, s):
        p = Path(s).expanduser()
        return p if p.is_absolute() else (ROOT / p).resolve()

    def env(self):
        return device.env(self.part)

    def freq_mhz(self):
        if not self.clocks:
            return None
        fast = min(self.clocks.values())
        f = 1000.0 / fast
        return int(f) if f == int(f) else round(f, 3)

    def _dfx(self, d):
        if not d:
            return None
        mode = d.get("partpins", CONFIG["partpins"])
        if mode not in CONFIG["variants"]:
            raise ProjectError(f"[dfx] partpins must be one of {sorted(CONFIG['variants'])}, not {mode!r}")
        parts = d.get("partition", [])
        if not parts:
            raise ProjectError("[dfx] needs at least one [[dfx.partition]]")
        timed = bool(d.get("timed", False))
        variant = d.get("variant") or (CONFIG["timed_variants"][mode] if timed else CONFIG["variants"][mode])
        out = {"partpins": mode, "variant": variant, "timed": timed,
               "rar": bool(d.get("rar", False)), "compress": bool(d.get("compress", False)),
               "decoupler": bool(d.get("decoupler", False)), "timing_allow_fail": list(d.get("timing_allow_fail", [])),
               "configs": [list(c) for c in d.get("configs", [])], "partitions": []}
        names = set()
        for i, q in enumerate(parts):
            for k in ("name", "inst", "region", "rms"):
                if k not in q:
                    raise ProjectError(f"[[dfx.partition]] #{i + 1} needs '{k}'")
            if q["name"] in names:
                raise ProjectError(f"duplicate partition name {q['name']}")
            names.add(q["name"])
            if "ports" not in q:
                raise ProjectError(f"partition {q['name']}: needs 'ports' (a ports.json path or an inline table)")
            spec, spec_file = ports_spec(q["ports"], self.dir)
            rms = {k: self.path(v) for k, v in q["rms"].items()}
            miss = [str(v) for v in rms.values() if not v.exists()]
            if miss:
                raise ProjectError(f"partition {q['name']}: missing RM sources {miss}")
            if q.get("greybox"):
                gname = "grey" if len(parts) == 1 else f"grey{i + 1}"
                if gname in rms:
                    raise ProjectError(f"partition {q['name']}: greybox = true adds the RM '{gname}', which is taken")
                rms[gname] = self.build / "stage" / f"greybox_{q['name']}.v"
            if len(rms) < 2:
                raise ProjectError(f"partition {q['name']}: needs at least two RMs")
            shell = self.path(q["shell"]) if q.get("shell") else None
            if shell and mode == "auto":
                raise ProjectError(f"partition {q['name']}: 'shell' is for partpins = \"anchors\" only")
            out["partitions"].append({
                "name": q["name"], "inst": q["inst"], "module": q.get("module", CONFIG["module"]),
                "region": q["region"], "spec": spec, "spec_file": spec_file, "shell": shell,
                "register": list(q.get("register", [])), "rms": rms, "greybox": bool(q.get("greybox", False)),
                "default_rms": list(q.get("default_rms", list(rms))), "stub": q.get("stub")})
        if len(out["partitions"]) > 1 and mode != "anchors":
            raise ProjectError("several partitions need partpins = \"anchors\" (the multi-partition native flow)")
        return out


def defines_module(files, module):
    pat = re.compile(rf"^\s*module\s+{re.escape(module)}\b", re.M)
    if any(pat.search(Path(f).read_text(errors="replace")) for f in files if Path(f).suffix in (".v", ".sv")):
        return True
    return module.lower() in vhdl.entities([f for f in files if vhdl.is_vhdl(f)])
