"""Footprint and LUT/FF bel use of QoR-suite designs: Vivado's own run (build/qor_suite/<d>__free/run0/nets_sites.txt)
against the open flow's base run (build/qor_suite/<d>/open/base/<p>_s1/impl/suite_top_routed.json)."""
import json, re, statistics as st, sys
from collections import Counter
from pathlib import Path
VW=Path('/mnt/c/Users/finnf/open-dfx-xc7-vivado/build/qor_suite'); R=Path.home()/'open-dfx-xc7/build/qor_suite'
def xy(s):
    m=re.match(r'SLICE_X(\d+)Y(\d+)$',s); return (int(m.group(1)),int(m.group(2))) if m else None
def shape(sl):
    xs=[p[0] for p in sl]; ys=[p[1] for p in sl]
    return len(sl), (max(xs)-min(xs)+1), (max(ys)-min(ys)+1), round(st.pstdev(xs),1), round(st.pstdev(ys),1), round(100*len(sl)/((max(xs)-min(xs)+1)*(max(ys)-min(ys)+1)),1)
print('| design | Vivado slices / bbox w x h / sd x,y / bbox fill | ours slices / bbox / sd / fill | ours lone 5LUT / LUTs; x5FF / FFs |')
print('|---|---|---|---|')
for d in sys.argv[1:]:
    ns=VW/f'{d}__free/run0/nets_sites.txt'
    if not ns.exists(): continue
    vs={xy(s) for ln in ns.read_text().splitlines() for s in ln.split()[1:] if xy(s)}
    runs=sorted((R/d/'open/base').glob('*_s1/impl/*_routed.json'))
    if not runs: continue
    m=next(iter(json.loads(runs[0].read_text())['modules'].values()))
    bels=[c.get('attributes',{}).get('NEXTPNR_BEL','') for c in m['cells'].values()]
    os_={xy(b.split('/')[0]) for b in bels if xy(b.split('/')[0])}
    occ=set(bels)
    l5=[b for b in bels if re.search(r'/[A-D]5LUT$',b)]; lone=sum(1 for b in l5 if b[:-4]+'6LUT' not in occ)
    luts=sum(1 for b in bels if re.search(r'/[A-D][56]LUT$',b)); f5=sum(1 for b in bels if re.search(r'/[A-D]5FF$',b)); ff=sum(1 for b in bels if re.search(r'/[A-D]5?FF$',b))
    v=shape(vs); o=shape(os_)
    print(f'| {d} ({runs[0].parts[-3]}) | {v[0]} / {v[1]}x{v[2]} / {v[3]},{v[4]} / {v[5]} % | {o[0]} / {o[1]}x{o[2]} / {o[3]},{o[4]} / {o[5]} % | {lone} / {luts}; {f5} / {ff} |')
