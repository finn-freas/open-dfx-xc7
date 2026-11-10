"""Make an exact-import source that imposes Vivado's own placement (vref_exact cells.txt) on the same netlist,
no LUT pin locks: the control for the exact-import measurement."""
import sys, shutil, re
from pathlib import Path
from collections import defaultdict
VW=Path('/mnt/c/Users/finnf/open-dfx-xc7-vivado')
d, base, out = sys.argv[1], sys.argv[2], sys.argv[3]
src=VW/'designs/exact'/base; dst=VW/'designs/viv_strategy'/out
dst.mkdir(parents=True, exist_ok=True)
for f in ('netlist.edf','constraints.xdc','top.txt','mode.txt'): shutil.copy(src/f, dst/f)
for f in ('lockpins.txt','routes.txt','const_routes.txt'): (dst/f).write_text('')
(dst/'dump.flag').write_text('')
place=[]; mac=defaultdict(list)
for ln in open(VW/f'build/exact/{d}_p5_vref_exact/cells.txt'):
    p=ln.rstrip('\n').split('\t')
    if len(p)<4 or not p[2]: continue
    n,ref,site,bel=p; b=bel.split('.')[-1]
    if ref in ('IBUF','OBUF','GND','VCC'): continue
    if ref in ('RAMD32','RAMS32','RAMD64E','RAMS64E') and '/' in n:
        m,sub=n.rsplit('/',1); mac[m].append(f'{{{sub}}} {site}/{b}'); continue
    if ref.startswith('BUFG'): place.append(f'{{{n}}} {site}'); continue
    place.append(f'{{{n}}} {site}/{b}')
(dst/'place.txt').write_text('\n'.join(place)+'\n')
(dst/'macros.txt').write_text(''.join(f'{{{m}}} '+' '.join(v)+'\n' for m,v in mac.items()))
print(out, len(place), 'cells', len(mac), 'macros')
