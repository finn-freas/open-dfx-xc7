"""`[[ip.clk]]`, `[[ip.fifo]]`, `[[ip.bram]]` in ofx.toml: generated into <build>/ip/ and added to the sources."""
import json
from pathlib import Path

from . import ip_bram, ip_clk, ip_fifo

CONFIG = {"dir": "ip"}


class IpError(Exception):
    pass


def fifo_props(t):
    """ofx.toml keys -> fifo_generator property names (Vivado's names are accepted as they are)."""
    m = {"impl": "Fifo_Implementation", "width": "Input_Data_Width", "depth": "Input_Depth",
         "almost_full": "Almost_Full_Flag", "almost_empty": "Almost_Empty_Flag", "valid": "Valid_Flag",
         "overflow": "Overflow_Flag", "underflow": "Underflow_Flag", "data_count": "Data_Count",
         "wr_data_count": "Write_Data_Count", "rd_data_count": "Read_Data_Count"}
    p = {}
    for k, v in t.items():
        if k in ("name",):
            continue
        if k == "fwft":
            p["Performance_Options"] = "First_Word_Fall_Through" if v else "Standard_FIFO"
        elif k == "prog_full":
            p["Programmable_Full_Type"] = "Single_Programmable_Full_Threshold_Constant"
            p["Full_Threshold_Assert_Value"] = v
        elif k == "prog_empty":
            p["Programmable_Empty_Type"] = "Single_Programmable_Empty_Threshold_Constant"
            p["Empty_Threshold_Assert_Value"] = v
        else:
            p[m.get(k, k)] = str(v).lower() if isinstance(v, bool) else v
    return p


def gen_clk(t, part):
    outs = ip_clk.from_table(t)
    res = ip_clk.solve(float(t["input_mhz"]), outs, t.get("primitive", "auto"), part, t.get("jitter", "balanced"))
    v = ip_clk.verilog(t["name"], res, in_buf=t.get("in_buf", "none"), use_reset=t.get("reset", True),
                       use_locked=t.get("locked", True))
    return v, ip_clk.table(res), res


def gen_fifo(t):
    o = ip_fifo.options(fifo_props(t))
    return ip_fifo.verilog(t["name"], o), ip_fifo.summary(t["name"], o), o


def gen_bram(t, base):
    init = (base / t["init"]).resolve() if t.get("init") else None
    cfg = ip_bram.build(t["name"], t.get("type", "Single_Port_RAM"), int(t["width"]), int(t["depth"]), init,
                        bool(t.get("reg_a", False)), bool(t.get("reg_b", False)), t.get("write_mode"))
    return ip_bram.verilog(cfg), ip_bram.summary(cfg), cfg


def gen_all(proj, out, dry):
    """Returns (verilog files, inputs) for every [[ip.*]] entry."""
    ip = proj.raw.get("ip", {})
    files, inputs = [], []
    for kind in ("clk", "fifo", "bram"):
        for t in ip.get(kind, []):
            if "name" not in t:
                raise IpError(f"[[ip.{kind}]] needs name")
            try:
                if kind == "clk":
                    v, info, _ = gen_clk(t, proj.part)
                elif kind == "fifo":
                    v, info, _ = gen_fifo(t)
                else:
                    v, info, cfg = gen_bram(t, proj.dir)
                    if cfg["init_file"]:
                        inputs.append(Path(cfg["init_file"]))
            except (ip_clk.ClkError, ip_fifo.FifoError, ip_bram.BramError, KeyError, ValueError) as e:
                raise IpError(f"[[ip.{kind}]] {t.get('name')}: {e}")
            f = out / f"{t['name']}.v"
            print(f"[{'dry' if dry else 'run'}] ip {kind} -> {f}\n" + "\n".join("    " + x for x in info.splitlines()))
            if not dry:
                out.mkdir(parents=True, exist_ok=True)
                if not f.exists() or f.read_text() != v:
                    f.write_text(v)
            files.append(f)
    return files, inputs
