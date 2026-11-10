"""Load verified prepared reserve8 train/dev windows. No test mode. Array axes: HWC/HW."""
import csv,hashlib,numpy as np
from pathlib import Path
ROSTER='d480029349025da34db421f384745ce9f7303e88633c01ae71c214b24c71fc5e'
def select(rows, split, roster=Path('manifests/g6g/reserve8_roster.csv')):
    if split not in ('train','dev') or hashlib.sha256(roster.read_bytes()).hexdigest()!=ROSTER:raise ValueError('seal or roster')
    eligible={x['geoid'] for x in csv.DictReader(roster.open()) if x['split']==split}
    groups={}; seen=set()
    for r in rows:
        gid=r['geoid']; origin=(gid,int(r['x']),int(r['y']))
        if gid not in eligible or origin in seen:raise ValueError('foreign ID or duplicate origin')
        seen.add(origin);groups.setdefault(gid,[]).append(r)
    def key(r):return hashlib.sha256(f"62029:{r['geoid']}:{int(r['x'])}:{int(r['y'])}".encode()).digest()
    return [r for gid,rs in sorted(groups.items()) for r in sorted(rs,key=key)[:32 if split=='train' else None]]
def load(row):
    p=Path(row['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('changed window')
    with np.load(p,allow_pickle=False) as z:
        im,y,inside,ok=(z[k] for k in ('rgb','label','inside','available'))
    if im.shape!=(512,512,3) or im.dtype!=np.uint8 or any(v.shape!=(512,512) for v in (y,inside,ok)) or inside.dtype!=bool or ok.dtype!=bool or y.dtype!=np.uint8 or y.max()>8:raise ValueError('window schema')
    mask=inside & ok & (y>=1)
    return im,np.where(mask,y.astype('int64')-1,-100),mask
