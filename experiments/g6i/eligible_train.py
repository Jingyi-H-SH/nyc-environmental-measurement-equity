"""Apply frozen rank to positive paired-land windows, retaining up to 32 per tract."""
import csv,hashlib,json,sqlite3
from pathlib import Path
import prepare as prep
p=Path('prepared/train.json')
rows=json.loads(p.read_text())
original=Path('prepared/train_initial.json')
if not original.exists():original.write_bytes(p.read_bytes())
rows=json.loads(original.read_text())
prep.G=prep.geoms(Path.home()/'work/jev-g6a/tl_2019_36_tract.zip')
prep.LINKS={}
for r in csv.DictReader((prep.H/'index_links.csv').open()):
    if r['split']=='train':prep.LINKS.setdefault(r['geoid'],[]).append(r)
db=sqlite3.connect('file:'+str(prep.H/'footprints-v1/planned.sqlite')+'?mode=ro',uri=True)
def key(r):
    return hashlib.sha256(f"62029:{r['geoid']}:{r['x']}:{r['y']}".encode()).digest()
output=[]
for gid in sorted({r['geoid'] for r in rows}):
    initial=[r for r in rows if r['geoid']==gid]
    valid=[r for r in initial if r['n']]
    if len(valid)<len(initial):
        seen={(r['x'],r['y']) for r in initial}
        remaining=[dict(geoid=gid,x=x,y=y) for x,y in db.execute("SELECT x,y FROM windows WHERE split='train' AND id=?",(gid,)) if (x,y) not in seen]
        for r in sorted(remaining,key=key):
            new=prep.tract((('train',gid),[r]))[0]
            if new['n']:valid.append(new)
            if len(valid)==32:break
    output.extend(sorted(valid,key=key))
tmp=p.with_suffix('.tmp')
tmp.write_text(json.dumps(output))
tmp.replace(p)
print('training sample verified',len(output),'eligible positive windows',flush=True)
