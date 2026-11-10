import sys
from collections import defaultdict
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import dl, dtab
acc = defaultdict(lambda: [0, 0.0, 0.0])
for r in dl.runs(r"_s3_exact$"):
    for a in dl.arcs(r):
        if a["rel"] != "inter": continue
        p = dtab.m_fo(a); e = p - a["viv"]
        d = abs(dl.IX[a["dx"]] - dl.IX[a["sx"]]) + abs(dl.IY[a["dy"]] - dl.IY[a["sy"]])
        db = "0-2" if d <= 2 else "3-5" if d <= 5 else "6-10" if d <= 10 else "11-20" if d <= 20 else "21+"
        crit = "crit" if 0 <= a["rank"] < 50 else ("near" if 0 <= a["rank"] < 200 else "rest")
        fb = "fo1" if a["fo"] == 1 else "fo2-7" if a["fo"] < 8 else "fo8+"
        for k in ((crit, db), (crit, a["dc"]), (crit, a["sc"]), (crit, fb), (crit, a["design"])):
            x = acc[k]; x[0] += 1; x[1] += e; x[2] += a["viv"]
for k in sorted(acc):
    n, se, sv = acc[k]
    if n >= 30: print(k, n, f"err {se/n:+.0f} viv {sv/n:.0f} ratio {(se/n)/(sv/n)*100:+.1f}%")
