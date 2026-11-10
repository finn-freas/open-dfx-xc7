"""Regenerate docs/dreamplace-eval.md from flow/dpf_summary.py and the text parts in docs/drafts/dreamplacefpga/eval/."""
import json, subprocess, sys
from pathlib import Path
R = Path.home() / "open-dfx-xc7"
B = R / "build" / "dpf"
T = R / "docs" / "drafts" / "dreamplacefpga" / "eval"
V = ["pl14_off_stub", "pl_dpf_wl", "pl_dpf_warm", "pl_dpf_td", "pl_dpf_td_warm"]
def summary(seeds):
    out = subprocess.run([sys.executable, str(R / "flow/dpf_summary.py"), "--variants"] + V + ["--seeds"] + seeds,
                         capture_output=True, text=True, cwd=R).stdout
    return out, json.loads((B / "summary.json").read_text())
_, s12 = summary(["1", "2"])
res = (T / "eval_result.md").read_text()
for d in ("rv_soc", "bram", "rv_big"):
    o = s12[f"{d}|pl14_off_stub"]["vivado_mean"]
    for v in V:
        m = s12[f"{d}|{v}"]["vivado_mean"]
        txt = f"{m:.2f}" if v == V[0] else f"{m:.2f} ({100 * (m / o - 1):+.1f} %)"
        res = res.replace(f"@@{d}|{v}@@", txt)
table, s = summary(["1", "2", "3"])
nviv = sum(sum(1 for x in s[f"{d}|{v}"]["vivado"] if x is not None) for d in ("rv_soc", "bram", "rv_big") for v in V) + 3
reco = (T / "eval_reco.md").read_text().replace("@@NVIV@@", str(nviv))
doc = (T / "eval_template.md").read_text()
doc = doc.replace("@@RESULT@@", res.strip()).replace("@@TABLE@@", "Vivado columns: Vivado timer, exact import, Vivado "
      "routes, 5 ns constraint, Fmax = 1000 / (5 - WNS). The mean is over the seeds present. nextpnr column: nextpnr "
      "timer. HPWL/wires: nextpnr. `python3 flow/dpf_summary.py --variants " + " ".join(V) + "` regenerates it.\n\n" + table.strip())
doc = doc.replace("@@ANALYSIS@@", (T / "eval_analysis.md").read_text().strip()).replace("@@RECO@@", reco.strip())
(R / "docs" / "dreamplace-eval.md").write_text(doc)
print("vivado runs:", nviv)
