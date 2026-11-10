import json, re, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "open-dfx-xc7/flow"))
import place_compare as pc
grid = pc.site_grid()
R = Path.home() / "open-dfx-xc7/build/qor/oxc7"
for v in sys.argv[1:]:
    rows = []
    for s in (1, 2, 3):
        f = R / v / "rv_soc_p5" / f"s{s}" / "qor_rv_soc_routed.json"
        if not f.exists():
            continue
        m = next(iter(json.loads(f.read_text())["modules"].values()))
        pts = []
        for c in m["cells"].values():
            b = c.get("attributes", {}).get("NEXTPNR_BEL", "")
            site = b.split("/")[0]
            if site.startswith("SLICE") and site in grid:
                pts.append(grid[site])
        sites = {c.get("attributes", {}).get("NEXTPNR_BEL", "").split("/")[0] for c in m["cells"].values()}
        rows.append((statistics.pstdev([p[0] for p in pts]), statistics.pstdev([p[1] for p in pts]), len([x for x in sites if x.startswith("SLICE")])))
    if rows:
        print(v, "sd_x %.1f sd_y %.1f slices %.0f" % tuple(statistics.mean(r[i] for r in rows) for i in range(3)), "per seed sd_y", [round(r[1], 1) for r in rows])
