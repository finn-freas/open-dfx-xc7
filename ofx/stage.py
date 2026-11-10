import json
import re
from pathlib import Path

from . import debug as debugmod
from . import hls as hlsmod
from . import ip as ipmod
from . import vhdl
from .project import CONFIG as PCONFIG, ProjectError, defines_module

CONFIG = {
    "rm_unit": "rm_core",
    "clock_re": r"create_clock\b[^\n]*get_ports\s*\{?\s*([A-Za-z_]\w*(?:\[\d+\])?)",
}


def xdc_text(proj):
    text = "".join(Path(f).read_text() for f in proj.constraints)
    have = set(re.findall(CONFIG["clock_re"], text))
    extra = [f"create_clock -name ofx_{re.sub(r'[^A-Za-z0-9_]', '_', port)} -period {period:.3f} [get_ports {port}]\n"
             for port, period in proj.clocks.items() if port not in have]
    return text + "".join(extra)


def write_if_changed(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != text:
        path.write_text(text)
    return path


def stub_text(module, spec):
    decl = lambda d, n, w: f"{d} wire {'' if w == 1 else f'[{w - 1}:0] '}{n}"
    ports = [f"input wire {spec['clk']}"] + [decl("input", n, w) for n, w in spec["inputs"]] + \
            [decl("output", n, w) for n, w in spec["outputs"]]
    return f"(* blackbox *)\nmodule {module} ({', '.join(ports)});\nendmodule\n"


def vhdl_sources(proj, d, tool_dry):
    vf = [f for f in proj.sources if vhdl.is_vhdl(f)]
    if not vf:
        return list(proj.sources)
    try:
        units = vhdl.units_for(vf, proj.top, proj.vhdl_units)
        outs = vhdl.convert(vf, units, proj.vhdl_std, d / vhdl.CONFIG["out_dir"], tool_dry,
                            generics=proj.vhdl_generics)
    except vhdl.VhdlError as e:
        raise ProjectError(str(e))
    return [f for f in proj.sources if not vhdl.is_vhdl(f)] + outs


def greybox_text(spec):
    """Vivado's greybox (update_design -buffer_ports) as an RM core: inputs unused, every output driven by 0."""
    ports = (([("input", "clk", 1)] if spec.get("core_clk") else [])
             + [("input", n, w) for n, w in spec["inputs"]] + [("output", n, w) for n, w in spec["outputs"]])
    decl = ", ".join(f"{d} wire {'' if w == 1 else f'[{w - 1}:0] '}{n}" for d, n, w in ports)
    body = "".join(f"    assign {n} = {w}'d0;\n" for n, w in spec["outputs"])
    return f"module rm_core ({decl});\n{body}endmodule\n"


def vhdl_rm(proj, d, pname, rm, f, tool_dry):
    if not vhdl.is_vhdl(f):
        return f
    try:
        return vhdl.convert([f], [CONFIG["rm_unit"]], proj.vhdl_std, d / vhdl.CONFIG["out_dir"], tool_dry,
                            tag=f"rm_{pname}_{rm}")[0]
    except vhdl.VhdlError as e:
        raise ProjectError(str(e))


def stage(proj, dry, tool_dry=False):
    d = proj.build / "stage"
    xdc = d / f"{proj.top}.xdc"
    if not dry:
        write_if_changed(xdc, xdc_text(proj))
    sources = vhdl_sources(proj, d, tool_dry)
    inputs = [f for f in proj.sources]
    if proj.raw.get("hls"):
        try:
            hf, hin = hlsmod.generate(proj, proj.build / hlsmod.CONFIG["out_dir"], dry or tool_dry)
        except hlsmod.HlsError as e:
            raise ProjectError(str(e))
        sources = sources + hf
        inputs += hin + ([] if (dry or tool_dry) else hf)
    if proj.raw.get("ip"):
        try:
            ipf, ipin = ipmod.gen_all(proj, proj.build / ipmod.CONFIG["dir"], dry or tool_dry)
        except ipmod.IpError as e:
            raise ProjectError(str(e))
        sources = sources + ipf
        inputs += ipin + ([] if (dry or tool_dry) else ipf)
    if proj.raw.get("debug", {}).get("insert"):
        if proj.dfx:
            raise ProjectError("[debug] insert works on flat builds only (not with [dfx])")
        try:
            sources, xdc = debugmod.insert(proj, sources, proj.constraints, proj.build / debugmod.CONFIG["out"],
                                           dry or tool_dry)
        except debugmod.DebugError as e:
            raise ProjectError(str(e))
        if not (dry or tool_dry):
            write_if_changed(d / f"{proj.top}.xdc", Path(xdc).read_text() + xdc_text(proj)[len(
                "".join(Path(f).read_text() for f in proj.constraints)):])
        xdc = d / f"{proj.top}.xdc"
        if not (dry or tool_dry):
            inputs += [Path(f) for f in sources]
    info = {"dir": d, "xdc": xdc, "sources": sources, "specs": {}, "r2v_rtl": {}, "rms": {},
            "inputs": inputs}
    if proj.dfx:
        if proj.dfx["decoupler"] and PCONFIG["decoupler_rtl"] not in sources:
            sources.append(PCONFIG["decoupler_rtl"])
            info["inputs"].append(PCONFIG["decoupler_rtl"])
        for p in proj.dfx["partitions"]:
            spec_file = p["spec_file"] or d / f"ports_{p['name']}.json"
            if not dry and not p["spec_file"]:
                write_if_changed(spec_file, json.dumps(p["spec"]) + "\n")
            info["specs"][p["name"]] = spec_file
            if p.get("greybox"):
                write_if_changed(d / f"greybox_{p['name']}.v", greybox_text(p["spec"]))
            info["rms"][p["name"]] = {rm: vhdl_rm(proj, d, p["name"], rm, f, tool_dry) for rm, f in p["rms"].items()}
            if p["stub"]:
                sources.append(proj.path(p["stub"]))
                info["inputs"].append(proj.path(p["stub"]))
            elif not defines_module(proj.sources, p["module"]):
                stub = d / f"stub_{p['module']}.v"
                if not dry:
                    write_if_changed(stub, stub_text(p["module"], p["spec"]))
                sources.append(stub)
                info["inputs"].append(stub)
            rd = d / f"r2v_{p['name']}"
            info["r2v_rtl"][p["name"]] = rd
            if not dry:
                rd.mkdir(parents=True, exist_ok=True)
                for rm, f in info["rms"][p["name"]].items():
                    if not Path(f).exists():
                        continue
                    link = rd / f"rm_core_{rm}.v"
                    if link.is_symlink() or link.exists():
                        if link.resolve() == f:
                            continue
                        link.unlink()
                    link.symlink_to(f)
    return info
