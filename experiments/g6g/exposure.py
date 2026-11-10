"""Rebuild requested source ids from archived output-window inventories without opening prediction pixels."""
from pathlib import Path
import json,math,re
import numpy as np
import pandas as pd
import shapely,tifffile
from shapely.geometry import box
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer
from design import M,O,geoms,load,web
def recover(root):
    receipts=(M/'g6e/raster_checksums.txt').read_text().splitlines()
    ti=load(O/'nyc_service_metadata.json')['tileInfo']
    ox,oy=ti['origin'].values()
    span=ti['cols']*next(v['resolution'] for v in ti['lods'] if v['level']==20)
    p=next((M/'g6c/whole').glob('*.tif'))
    ix,iy=map(int,p.stem.split('-')[-2:])
    with tifffile.TiffFile(p) as ds:
        _,_,_,left,top,_=ds.pages[0].tags['ModelTiepointTag'].value
    x0=round(left-.5*ix,2);y0=round(top+.5*iy,2)
    fwd=Transformer.from_crs(2263,3857,always_xy=True)
    rows=[]; pairs=[];lookup={};parts=[]
    def window(stage,gid,x,y,sha=None,known=None):
        b=(x0+x*.5,y0-(y+512)*.5,x0+(x+512)*.5,y0-y*.5)
        l,bot,r,top=fwd.transform_bounds(*b)
        coords=[(i,j) for i in range(math.floor((oy-top)/span),math.floor((oy-bot)/span)+1) for j in range(math.floor((l-ox)/span),math.floor((r-ox)/span)+1)]
        if known is not None:assert set(coords)==known
        for i,j in coords:
            pairs.append((stage,gid,x,y,i,j))
            if (i,j) not in lookup:lookup[i,j]=transform(web,box(ox+j*span,oy-(i+1)*span,ox+(j+1)*span,oy-i*span))
        rows.append((stage,gid,x,y,*b,sha))
        parts.append(box(*b))
    for line in receipts:
        m=re.fullmatch(r'([a-f0-9]{64})  g6e/(\d{11})/(\d+)-(\d+)\.tif',line)
        if m:
            sha,gid,x,y=m.groups()
            window('G6E',gid,int(x),int(y),sha)
    assert len(set(row[1] for row in rows))==34
    pilot=geoms(root/'tl_2017_36_tract.zip')
    for gid in ['36061008602','36047079802','36085007000']:
        p=pilot[gid].representative_point()
        window('registration',gid,math.floor((p.x-x0)/.5)-256,math.floor((y0-p.y)/.5)-256)
    whole=load(M/'g6c/full_tract.json')
    for w in whole['tiles']:
        window('G6C_full',whole['geoid'],w['x'],w['y'],w['sha'],{tuple(map(int,url.split('/')[-2:])) for url in w['tiles']})
    for stage,path in [('G6C',M/'g6c/patches.json'),('G6D',M/'g6d/windows/patches.json')]:
        for w in load(path):
            if 'bounds' in w:
                x,_,_,y=w['bounds']
                window(stage,w['geoid'],round((x-x0)*2),round((y0-y)*2),w['rgb_sha'],{tuple(map(int,url.split('/')[-2:])) for url in w['tiles']})
    pd.DataFrame(rows,columns='stage geoid col row left bottom right top archive_sha256'.split()).to_csv(O/'historical_windows.csv',index=False)
    pd.DataFrame(pairs,columns='stage geoid col row source_row source_col'.split()).to_csv(O/'historical_window_tiles.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    tile_tree=STRtree(list(lookup.values())); image_tree=STRtree(parts)
    geo=geoms(root/'tl_2019_36_tract.zip')
    old=pd.read_csv(O/'historical_screen.csv',dtype={'geoid':str})
    grid=[]
    for r in old.itertuples():
        g=geo[r.geoid]
        def overlap(tree):
            return sum(g.intersection(tree.geometries[k]).area>0 for k in tree.query(g,predicate='intersects'))
        it=image_tree.nearest(g);st=tile_tree.nearest(g)
        grid.append((r.geoid,overlap(image_tree),overlap(tile_tree),g.distance(parts[it]),g.distance(tile_tree.geometries[st])))
    pd.DataFrame(grid,columns='geoid overlapping_window_occurrences overlapping_source_keys distance_window_ft distance_source_ft'.split()).to_csv(O/'historical_exact_screen.csv',index=False)
    (O/'recovery.json').write_text(json.dumps({'registered_windows':len(rows),'unique_windows':len(set((r[2],r[3]) for r in rows)),'source_occurrences':len(pairs),'unique_requested_source_keys':len(lookup),'raster_origin_epsg2263':[x0,y0],'service':ti['spatialReference'],'successful_bytes':'G6C/D hashed where listed; G6E and pilot archive reconstructed request keys treated as exposed regardless of response'},indent=2))
if __name__=='__main__':
    import sys
    recover(Path(sys.argv[1]))
