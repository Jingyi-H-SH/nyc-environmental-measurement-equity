"""Prepare only reserve8 fitting and development inputs on Featurize."""
import os
os.environ.update(OPJ_NUM_THREADS='1', GDAL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
import csv
import hashlib
import json
import sqlite3
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import Window
from rasterio.features import geometry_mask

H = Path.home() / 'work/jev-g6h-v1'
sys.path.insert(0, str(H/'experiments/g6h'))
from footprints import geoms
from loader import select
S = Path('/tmp/g6i-reserve8')
S.mkdir(exist_ok=True)
OUT = Path('prepared')
OUT.mkdir(exist_ok=True)
def sha(p):
    return hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
def tile(name):
    dest = S/(name+'.npy')
    if dest.exists(): return
    r = json.loads((H/'qualification'/(name+'.json')).read_text())
    with zipfile.ZipFile(Path('/tmp/g6h-ortho')/(r['archive']+'.zip')) as z:
        data = z.read(r['member'])
    assert hashlib.sha256(data).hexdigest()==r['sha256']
    with MemoryFile(data) as f, f.open() as ds:
        rgb = ds.read([1,2,3]).transpose(1,2,0)
    tmp = dest.with_suffix('.partial.npy')
    np.save(tmp, rgb)
    tmp.replace(dest)
@lru_cache(maxsize=24)
def arrays(name):
    return (np.load(S/(name+'.npy'),mmap_mode='r'),
            np.load(Path('/tmp/g6h-ortho/masks')/(name+'.npy'),mmap_mode='r'))
def tract(item):
    (split,gid), windows = item
    dest = S/split/gid
    dest.mkdir(exist_ok=True,parents=True)
    counts=np.zeros(9,dtype=np.int64)
    rows=[]
    with rasterio.open(Path.home()/'g6a-native/NYC_2017_LiDAR_LandCover.img') as ds:
        for r in windows:
            x,y=r['x'],r['y']
            w=Window(x,y,512,512)
            af=ds.window_transform(w)
            inside=geometry_mask([G[gid]],(512,512),af,invert=True)
            label=ds.read(1,window=w,boundless=True,fill_value=0)
            rgb=np.zeros((512,512,3),np.uint8)
            ok=np.zeros((512,512),bool)
            xs=af.c+(np.arange(512)+.5)*.5
            ys=af.f-(np.arange(512)+.5)*.5
            for q in LINKS[gid]:
                left,bottom,right,top=[int(q[k]) for k in ('xmin','ymin','xmax','ymax')]
                cols=np.where((xs>=left)&(xs<right))[0]
                rr=np.where((ys>bottom)&(ys<=top))[0]
                u=(xs[cols]-left)*2-.5
                v=(top-ys[rr])*2-.5
                cols,u=cols[u>=0],u[u>=0]
                rr,v=rr[v>=0],v[v>=0]
                if not len(cols) or not len(rr):continue
                a,m=arrays(q['image'])
                i,j=u.astype(int),v.astype(int)
                valid=(m[j[:,None],i//8]>>(7-i%8))&1
                idx=np.ix_(rr,cols)
                ok[idx]=valid
                dx=(u-i)[None,:,None]; dy=(v-j)[:,None,None]
                i1=np.minimum(i+1,4999); j1=np.minimum(j+1,4999)
                interp=(1-dy)*((1-dx)*a[np.ix_(j,i)]+dx*a[np.ix_(j,i1)])+dy*((1-dx)*a[np.ix_(j1,i)]+dx*a[np.ix_(j1,i1)])
                rgb[idx]=np.rint(interp).astype(np.uint8)
            # Only source-valid pixels supply image information. Neither tract nor label mask alters RGB.
            rgb[~ok]=0
            lab=np.where(inside & ok,label,0).astype(np.uint8)
            counts+=np.bincount(lab.ravel(),minlength=9)
            p=dest/f'{x}_{y}.npy'
            np.save(p,np.dstack((rgb,lab)))
            rows.append(dict(geoid=gid,x=x,y=y,path=str(p),sha256=sha(p),n=int((lab>0).sum())))
    if split=='dev':
        expected=json.loads((H/'qualification'/(gid+'.json')).read_text())['paired_class_counts']
        assert counts[1:].tolist()==expected[1:],(gid,counts,expected)
    return rows
if __name__=='__main__':
    roster=H/'manifests/g6g/reserve8_roster.csv'
    db=H/'footprints-v1/planned.sqlite'
    assert sha(db)=='2f89b66d0a393a9035257745feeea943ba8121ff75a63a57c95122022c3ce58a'
    G=geoms(Path.home()/'work/jev-g6a/tl_2019_36_tract.zip')
    LINKS={}
    for r in csv.DictReader((H/'index_links.csv').open()):
        if r['split'] in ('train','dev'):LINKS.setdefault(r['geoid'],[]).append(r)
    conn=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
    for split in ['train','dev']:
        if (OUT/(split+'.json')).exists():continue
        groups={}
        raw=[dict(geoid=g,x=x,y=y) for g,x,y in conn.execute('SELECT id,x,y FROM windows WHERE split=?',(split,))]
        for r in select(raw,split,roster):groups.setdefault((split,r['geoid']),[]).append(r)
        names=sorted({r['image'] for _,gid in groups for r in LINKS[gid]})
        with ProcessPoolExecutor(7) as pool:list(pool.map(tile,names))
        print(split,'tiles',len(names),flush=True)
        with ProcessPoolExecutor(6) as pool:
            rows=[r for part in pool.map(tract,groups.items()) for r in part]
        assert len(groups)=={'train':163,'dev':53}[split]
        tmp=OUT/(split+'.tmp')
        tmp.write_text(json.dumps(rows))
        tmp.replace(OUT/(split+'.json'))
        print(split,'verified',len(rows),flush=True)
