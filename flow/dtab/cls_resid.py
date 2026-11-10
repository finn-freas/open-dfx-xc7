import sys
from collections import defaultdict
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import dl, dtab
acc = defaultdict(lambda: [0, 0.0, 0.0])
for r in dl.runs(r"_s3_exact$"):
    for a in dl.arcs(r):
        if a["rel"] != "inter" or dl.is_carry_cascade(a): continue
        e = dtab.m_fo(a) - a["viv"]
        d = abs(dl.IX[a["dx"]] - dl.IX[a["sx"]]) + abs(dl.IY[a["dy"]] - dl.IY[a["sy"]])
        db = 0 if d <= 2 else 1 if d <= 6 else 2 if d <= 15 else 3
        for k in (("src", a["sc"], db), ("dst", a["dc"], db)):
            x = acc[k]; x[0] += 1; x[1] += e; x[2] += abs(e)
rows = defaultdict(dict)
for (kind, c, db), (n, se, sae) in acc.items():
    rows[(kind, c)][db] = (n, se / n)
print("mean residual (model - Vivado, ps) by distance d<=2 | 3-6 | 7-15 | 16+   (n)")
for k in sorted(rows):
    print(k, " | ".join(f"{rows[k][b][1]:+5.0f} ({rows[k][b][0]})" if b in rows[k] else "-" for b in range(4)))
