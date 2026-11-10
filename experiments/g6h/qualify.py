"""Cloud-only source qualification, no model artifacts. Run from persistent G6-H root after source_index.py."""
import os
os.environ.update(OPJ_NUM_THREADS='1',GDAL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
import csv, json, time, hashlib, math, zipfile, itertools, sys, traceback
import concurrent.futures as cf
from pathlib import Path
import numpy as np, rasterio
from rasterio.io import MemoryFile
from rasterio.windows import Window,from_bounds
from rasterio.features import geometry_mask
from footprints import geoms
from pyproj import Transformer
scratch=Path('/tmp/g6h-ortho'); out=Path('qualification'); out.mkdir(exist_ok=True)
cache=scratch/'masks';cache.mkdir(exist_ok=True)
def save(p,v):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(v,allow_nan=False));t.replace(p)
def decode(arg):
    r,archive=arg; name=r['image']; start=time.monotonic()
    with zipfile.ZipFile(archive) as z:
        item=next(x for x in z.infolist() if Path(x.filename).name.lower()==name.lower());data=z.read(item)
    with MemoryFile(data) as m,m.open() as d:
        bound=[int(r[k]) for k in ('xmin','ymin','xmax','ymax')]
        # NYC explicitly designates this index as the georeferencing grid. Assert embedded bounds agree.
        assert d.crs.to_epsg() in (6539,2263) and np.max(np.abs(np.array(d.bounds)-bound))<.01
        assert d.count>=3 and d.shape==(5000,5000) and d.res==(.5,.5) and all(x=='uint8' for x in d.dtypes[:3])
        rgb=d.read([1,2,3]); valid=(rgb.max(axis=0)>0)&(rgb.min(axis=0)<255)
        if any(v.name!='all_valid' for flags in d.mask_flag_enums[:3] for v in flags):valid &= (d.read_masks([1,2,3]).min(axis=0)==255)
        # Conservative all four native neighbours (bilinear footprint) incl. one-pixel edge guard.
        ok=valid.copy();ok[:-1,:-1]&=valid[1:,:-1]&valid[:-1,1:]&valid[1:,1:];ok[-1,:]=False;ok[:,-1]=False
        np.save(cache/(name+'.npy'),np.packbits(ok,axis=1))
        rec=dict(image=name,archive=r['archive'],member=item.filename,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),crc32=item.CRC,
                 bounds=bound,crs=d.crs.to_string(),bands=d.count,native_valid=int(valid.sum()),seconds=time.monotonic()-start)
    save(out/(name+'.json'),rec)
def masks():
    sources=json.loads(Path('archive_sources.json').read_text());rows={r['image']:r for r in csv.DictReader(open('index_links.csv'))}
    locations=json.loads(Path('source_locations.json').read_text());assert all(locations.values())
    for r in rows.values():r['archive']=locations[r['image']]
    for b,s in sources.items():
        group=[r for r in rows.values() if r['archive']==b and not ((out/(r['image']+'.json')).exists() and (cache/(r['image']+'.npy')).exists())]
        if not group:continue
        p=scratch/(b+'.zip');part=scratch/(b+'.part');expected=math.ceil(s['bytes']/(8<<20))
        until=time.monotonic()+3600
        while not p.exists():
            if len(list(scratch.glob(b+'.*.ok')))==expected and part.exists():
                p=scratch/(b+'.snapshot'); 
                if not p.exists():os.link(part,p)
                break
            if time.monotonic()>until:raise TimeoutError(b)
            time.sleep(4)
        print('decode',b,len(group),flush=True)
        with cf.ProcessPoolExecutor(7) as pool:
            for _ in pool.map(decode,[(r,p) for r in group]):pass
        print('decoded',b,time.time(),flush=True)
def tract(r):
    import fcntl
    with (cache/(r['geoid']+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);return _tract(r)
def _tract(r):
    gid=r['geoid'];dest=out/(gid+'.json')
    previous=json.loads(dest.read_text()) if dest.exists() else None
    if previous and 'paired_class_counts' in previous:return
    g=G[gid];tiles=[]
    for row in links.get(gid,[]):
        x,y,xx,yy=[int(row[k]) for k in ('xmin','ymin','xmax','ymax')]
        tiles.append((x,y,xx,yy,np.load(cache/(row['image']+'.npy'),mmap_mode='r')))
    class_n=np.zeros(9,np.int64);pair_n=class_n.copy()
    n=np.zeros(7,np.int64); quadrants=np.zeros((4,2),np.int64)
    with rasterio.open(Path.home()/'g6a-native/NYC_2017_LiDAR_LandCover.img') as ds:
        w=from_bounds(*g.bounds,transform=ds.transform);x0=math.floor(w.col_off);y0=math.floor(w.row_off);xe=math.ceil(w.col_off+w.width);ye=math.ceil(w.row_off+w.height)
        for j in range(y0,ye,1024):
            for i in range(x0,xe,1024):
                h=min(1024,ye-j);l=min(1024,xe-i);win=Window(i,j,l,h);af=ds.window_transform(win)
                inside=geometry_mask([g],(h,l),af,invert=True)
                if not inside.any():continue
                lab=ds.read(1,window=win,boundless=True,fill_value=0);assert lab.max()<=8
                ref=inside&(lab>0);land=ref&(lab!=4)
                ok=np.zeros((h,l),bool);raw=ok.copy()
                xs=af.c+(np.arange(l)+.5)*.5;ys=af.f-(np.arange(h)+.5)*.5
                for x,y,xx,yy,m in tiles:
                    cols=np.flatnonzero((xs>=x)&(xs<xx));rows=np.flatnonzero((ys>y)&(ys<=yy))
                    if not len(cols) or not len(rows):continue
                    raw[rows[0]:rows[-1]+1,cols[0]:cols[-1]+1]=True
                    cx=np.floor((xs[cols]-x)*2-.5).astype(int);cy=np.floor((yy-ys[rows])*2-.5).astype(int)
                    cols=cols[cx>=0];rows=rows[cy>=0];cx=cx[cx>=0];cy=cy[cy>=0]
                    if len(cols) and len(rows):ok[rows[0]:rows[-1]+1,cols[0]:cols[-1]+1]|=((m[cy[:,None],cx//8]>>(7-cx%8))&1).astype(bool)
                class_n+=np.bincount(lab[inside],minlength=9);pair_n+=np.bincount(lab[ref&ok],minlength=9)
                n += [inside.sum(),ref.sum(),land.sum(),(inside&raw).sum(),(inside&ok).sum(),(ref&ok).sum(),(land&ok).sum()]
                for k,(a,b) in enumerate(itertools.product([ys>=g.centroid.y,ys<g.centroid.y],[xs<g.centroid.x,xs>=g.centroid.x])):
                    loc=a[:,None]&b;quadrants[k]+=[(loc&land).sum(),(loc&land&~ok).sum()]
    assert n[1]==int(r['reference_pixels']) and n[2]==int(r['terrestrial_pixels']),(gid,n.tolist(),r)
    measured=dict(zip('polygon mapped land decoded rgb paired paired_land'.split(),map(int,n)),geoid=gid,source_tiles=len(tiles),land_missing_quadrants_NW_NE_SW_SE=quadrants.tolist())
    if previous:assert measured==previous,'early validation changed'
    measured.update(reference_class_counts=class_n.tolist(),paired_class_counts=pair_n.tolist());save(dest,measured)
if __name__=='__main__':
    if sys.argv[1]=='masks':masks()
    else:
        G=geoms(Path.home()/'work/jev-g6a/tl_2019_36_tract.zip')
        links={}
        for r in csv.DictReader(open('index_links.csv')):links.setdefault(r['geoid'],[]).append(r)
        with cf.ProcessPoolExecutor(7) as pool:list(pool.map(tract,list(csv.DictReader(open('baseline_coverage.csv')))))
        print('completed all tract reference checks',flush=True)
