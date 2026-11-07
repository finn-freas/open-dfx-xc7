import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xroute_cmp

ROOT = xroute_cmp.ROOT

CONFIG = {
    "train": ["blinky_p5_cal_static_s1", "rv_soc_p5_cal_static_s1", "bram_p5_cal_static_s1"],
    "test": ["rv_mul_p5_dspq_cal_s1", "rv_big_p5_dspq_cal_s1"],
    "timer": "perm",
    "out": ROOT / "build" / "xroute" / "fit",
    "cal_json": ROOT / "build" / "chipdb-rcal" / "route_timing_xc7a35t_1.json",
    "dry_run": True,
    "min_arcs": 30,
    "classes": [
        ["single", r"^(NN|SS|EE|WW|NE|NW|SE|SW|NL|NR|SL|SR|EL|ER|WL|WR)1BEG"],
        ["double", r"^(NN|SS|EE|WW|NE|NW|SE|SW)2BEG"],
        ["quad", r"^(NN|SS|EE|WW|NE|NW|SE|SW)4BEG"],
        ["hex", r"^(NN|SS|EE|WW|NE|NW|SE|SW)6BEG"],
        ["long", r"^(LH|LV|LVB)(_L)?\d+$"],
        ["bounce", r"^(BYP_ALT|FAN_ALT|BYP_BOUNCE|FAN_BOUNCE|GFAN)"],
        ["imux", r"^IMUX(_L)?\d+$"],
        ["byp", r"^BYP(_L)?\d+$"],
        ["ctrl", r"^(FAN(_L)?\d+|CTRL(_L)?\d+)$"],
        ["clb_out", r"^CLBL[LM]_(L_|LL_|M_)?LOGIC_OUTS\d+$"],
        ["clb_in", r"^CLBL[LM]_(L|LL|M)_([A-D][1-6]|[A-D]X|[A-D]I|CE|SR|CIN|BYP)"],
        ["int_out", r"^LOGIC_OUTS(_L)?\d+$"],
        ["hard_out", r"^(BRAM|DSP|INT_INTERFACE|IO_INT_INTERFACE|BRAM_INT_INTERFACE)_.*LOGIC_OUTS"],
        ["bram_in", r"^BRAM_"],
        ["dsp_in", r"^DSP_"],
        ["clb_site_out", r"^CLBL[LM]_(L|LL|M)_([A-D]|[A-D]MUX|[A-D]Q|COUT)"],
    ],
    "exclude_cls": {"clock", "intrasite"},
    "fit_skip": {"clb_in", "clb_out", "other"},
}


def pip_class(pip):
    if not pip:
        return None
    dst = pip.split("/")[-1]
    for name, pat in CONFIG["classes"]:
        if re.match(pat, dst):
            return name
    return "other"


def fit_class(pip):
    c = pip_class(pip)
    return None if c in CONFIG["fit_skip"] else c


def features(row):
    return Counter(c for c in (pip_class(p) for p in row["pips"] if p) if c not in CONFIG["fit_skip"])


def load(names, timer):
    rows = []
    for n in names:
        st = xroute_cmp.CONFIG["vivado"] / n / "status.txt"
        if not st.exists() or not (st.read_text().startswith("rc 0") or "step bitstream" in st.read_text()):
            print(f"[skip] {n}: no complete Vivado result")
            continue
        r, _ = xroute_cmp.all_net_arcs(n, timer)
        for a in r:
            if a["cls"] in CONFIG["exclude_cls"] or not a["pips"] or None in a["pips"]:
                continue
            a["design"] = n
            a["f"] = features(a)
            rows.append(a)
    return rows


def fit(rows):
    cls = sorted({k for a in rows for k in a["f"]})
    cnt = Counter(k for a in rows for k in a["f"])
    cls = [c for c in cls if cnt[c] >= CONFIG["min_arcs"]]
    X = [[a["f"].get(c, 0) for c in cls] for a in rows]
    y = [a["viv"] - a["npr"] for a in rows]
    w = xroute_cmp.lstsq(X, y)
    return dict(zip(cls, w))


def apply(rows, add):
    return [a["npr"] + sum(add.get(c, 0.0) * k for c, k in a["f"].items()) for a in rows]


def summarize(rows, pred):
    by = defaultdict(list)
    for a, p in zip(rows, pred):
        by[a["cls"]].append(p - a["viv"])
        by["all"].append(p - a["viv"])
    return {k: xroute_cmp.stat(v) for k, v in by.items()}


def main():
    ap = argparse.ArgumentParser(description="Fit per-wire-class additive pip delays (nextpnr chipdb, slow corner) to "
                                             "Vivado's net delays on identical routes; validate on other designs")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--eval-only", action="store_true", help="evaluate the existing calibration JSON, do not refit")
    a = ap.parse_args()
    dry = CONFIG["dry_run"] and not a.run
    train, test = load(CONFIG["train"], CONFIG["timer"]), load(CONFIG["test"], CONFIG["timer"])
    if a.eval_only:
        add = {k: v[1] / 1000.0 for k, v in json.loads(CONFIG["cal_json"].read_text())["pip_add"].items()}
    else:
        add = fit(train)
    res = {"add_ns": add, "n_train": len(train), "n_test": len(test),
           "train_before": summarize(train, [r["npr"] for r in train]), "train_after": summarize(train, apply(train, add)),
           "test_before": summarize(test, [r["npr"] for r in test]), "test_after": summarize(test, apply(test, add))}
    paths = {}
    for n in CONFIG["train"] + CONFIG["test"]:
        st = xroute_cmp.CONFIG["vivado"] / n / "status.txt"
        if not st.exists() or not (st.read_text().startswith("rc 0") or "step bitstream" in st.read_text()):
            continue
        b = xroute_cmp.compare(n, "setup", CONFIG["timer"])["paths"]
        c = xroute_cmp.compare(n, "setup", CONFIG["timer"], add, fit_class)["paths"]
        paths[n] = {"before": xroute_cmp.stat([p["npr_T"] - p["viv_T"] for p in b]),
                    "after": xroute_cmp.stat([p["npr_T"] - p["viv_T"] for p in c]),
                    "worst_viv_T": max(p["viv_T"] for p in b), "worst_npr_T_before": max(p["npr_T"] for p in b),
                    "worst_npr_T_after": max(p["npr_T"] for p in c), "n": len(b)}
        print(f"{n}: setup paths {len(b)}: err mean {paths[n]['before']['mean'] * 1000:+.0f} ps mae "
              f"{paths[n]['before']['mae'] * 1000:.0f} -> mean {paths[n]['after']['mean'] * 1000:+.0f} mae "
              f"{paths[n]['after']['mae'] * 1000:.0f}; worst T viv {paths[n]['worst_viv_T']:.3f} npr "
              f"{paths[n]['worst_npr_T_before']:.3f} -> {paths[n]['worst_npr_T_after']:.3f} ns")
    res["paths"] = paths
    cal = {"classes": [c for c in CONFIG["classes"] if c[0] in add],
           "pip_add": {c: [0, int(round(v * 1000))] for c, v in add.items()},
           "source": {"train": CONFIG["train"], "timer": CONFIG["timer"], "arcs": len(train)}}
    for k in ("train_before", "train_after", "test_before", "test_after"):
        s = res[k]["all"]
        print(f"{k}: n {s['n']} mean {s['mean'] * 1000:+.0f} ps, mae {s['mae'] * 1000:.0f} ps, p90 {s['p90abs'] * 1000:.0f} ps")
    print("add (ps): " + ", ".join(f"{c} {v * 1000:+.0f}" for c, v in sorted(add.items())))
    if a.eval_only:
        if not dry:
            CONFIG["out"].mkdir(parents=True, exist_ok=True)
            (CONFIG["out"] / "eval.json").write_text(json.dumps(res, indent=1))
        return
    print(f"[{'dry' if dry else 'run'}] write {CONFIG['out'] / 'fit.json'} and {CONFIG['cal_json']}")
    if not dry:
        CONFIG["out"].mkdir(parents=True, exist_ok=True)
        (CONFIG["out"] / "fit.json").write_text(json.dumps(res, indent=1))
        CONFIG["cal_json"].parent.mkdir(parents=True, exist_ok=True)
        CONFIG["cal_json"].write_text(json.dumps(cal, indent=1) + "\n")


if __name__ == "__main__":
    main()
