"""Run from the project root. Only geographic and reference inputs are opened."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
import shapefile
import shapely
from shapely.geometry import shape, box, mapping, MultiPoint
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer
from scipy.spatial.distance import cdist
from scipy.stats import t

M = Path('manifests')
O = M/'g6g'
E = Path('experiments/g6g')
cfg = json.loads((E/'freeze.json').read_text())
cells = ['00','01','10','11']
project = Transformer.from_crs(4269,2263,always_xy=True).transform
web = Transformer.from_crs(3857,2263,always_xy=True).transform
native = ['tree','grass','bare','water','building','road','other_impervious','rail']
def load(path):
    return json.loads(Path(path).read_text())
def save(name, rows):
    pd.DataFrame(rows).to_csv(O/(name+'.csv'),index=False)
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def unit(s):
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8],'big')/2**64
def geoms(path):
    return {sr.record['GEOID']:transform(project,shape(sr.shape.__geo_interface__)) for sr in shapefile.Reader(str(path)).iterShapeRecords() if sr.record['COUNTYFP'] in ['005','047','061','081','085']}
def tilepoly(r,c):
    origin=20037508.342789244
    side=2*origin/2**20
    return transform(web,box(-origin+c*side,origin-(r+1)*side,-origin+(c+1)*side,origin-r*side))
def block(g,side,offset):
    p=g.representative_point()
    return math.floor((p.x-offset)/side),math.floor((p.y-offset)/side)
def labels(p):
    return 'test' if p<.45 else 'dev' if p<.60 else 'train'
def run(args):
    O.mkdir(exist_ok=True)
    path=args.geometry/'tl_2019_36_tract.zip'
    assert digest(path)=='38043e7276be9bd05c6f95ed2e95e8783eeb086ca1fb2a88c3e2e6788019a566'
    geo=geoms(path)
    old=geoms(args.geometry/'tl_2017_36_tract.zip')
    frame={r['geoid']:r for r in load(M/'g6d/frame.json')}
    cov=list(csv.DictReader((M/'g6e/coverage.csv').open()))
    seal={r['geoid'] for r in cov if r['partition']=='final' and r['selected']=='1'}
    assert len(seal)==74
    geom=[]; feats=[]; tiles={}; sources=[]
    def add(g,stage,gid,part,kind):
        geom.append(g)
        feats.append(dict(stage=stage,geoid=gid,partition=part,kind=kind))
    def register(d,stage,gid):
        for url,h in d.items():
            r,c=map(int,url.split('/')[-2:])
            if (r,c) in tiles:
                assert tiles[r,c]==h
            tiles[r,c]=h
            sources.append(dict(stage=stage,geoid=gid,row=r,col=c,sha256=h))
    for stage,f in [('G6C',M/'g6c/patches.json'),('G6D',M/'g6d/windows/patches.json')]:
        for r in load(f):
            if 'bounds' in r:
                assert r['partition']!='final'
                add(box(*r['bounds']),stage,r['geoid'],r['partition'],'exact_window')
                register(r['tiles'],stage,r['geoid'])
    for gid in ['36061008602','36047079802','36085007000']:
        p=old[gid].representative_point()
        add(box(p.x-129,p.y-129,p.x+129,p.y+129),'registration',gid,'train','outer_bound_grid_snap')
    whole=load(M/'g6c/full_tract.json')
    gid=whole['geoid']
    add(geo[gid],'G6C_full',gid,'dev','polygon')
    for row in whole['tiles']:register(row['tiles'],'G6C_full',gid)
    for r in cov:
        if r['candidate']=='1':
            assert r['partition']=='dev'
            add(geo[r['geoid']],'G6E_full',r['geoid'],'dev','polygon')
    save('source_tile_occurrences',sources)
    # A 256-foot window diagonal plus a zoom-20 tile diagonal is under 600 ft in NYC.
    # Missing whole-tract sidecar IDs are bounded at the full polygon, also covers pilot snap.
    tile_geoms=[tilepoly(*key) for key in tiles]
    tile_union=shapely.union_all(tile_geoms)
    envelope=shapely.union_all([g.buffer(600) for g,f in zip(geom,feats) if f['stage'] in ['G6E_full','registration']])
    historical=shapely.union_all(geom)
    extent=shapely.union_all([historical,tile_union,envelope])
    seal_union=shapely.union_all([geo[g] for g in seal])
    all_historical_ids={f['geoid'] for f in feats}
    (O/'footprints.geojson').write_text(json.dumps(dict(type='FeatureCollection',crs={'type':'name','properties':{'name':'EPSG:2263'}},features=[dict(type='Feature',properties=f,geometry=mapping(g)) for f,g in zip(feats,geom)])))
    rows=[]
    for r in cov:
        gid=r['geoid']
        if r['strict']!='1':continue
        g=geo[gid]; f=frame[gid]
        a=np.array(f['mapped_share'])
        rows.append(dict(geoid=gid,borough=f['borough'],cell=r['cell_black'],older=r['cell_older'],rent=r['cell_rent'],poverty=f['poverty'],black=f['black'],old_block=f['block'],old_partition=r['partition'],seal=gid in seal,seal_distance=g.distance(seal_union),historical_id=gid in all_historical_ids,window_or_polygon_intersection=g.intersection(historical).area>0,confirmed_tile_intersection=g.intersection(tile_union).area>0,conservative_tile_intersection=g.intersects(envelope),distance_ft=g.distance(extent),veg=a[:2].sum(),built=a[4:].sum(),**dict(zip(native,a))))
    df=pd.DataFrame(rows)
    assert len(df)==1642 and list(df.cell.value_counts().sort_index())==[512,309,309,512]
    save('historical_screen',rows)
    polygons=[geo[g] for g in df.geoid]
    # Kernels and tiles must be clipped to the assigned tract support; 800 extra feet
    # guard two 256 ft square windows and their zoom-20 source tiles across splits.
    threshold=cfg['minimum_cross_split_ft']+cfg['extra_window_and_tile_margin_ft']
    tree=STRtree(polygons)
    edges=[list(tree.query(g,predicate='dwithin',distance=threshold)) for g in polygons]
    available=(~df.seal)&(df.seal_distance>threshold)
    clean=available&(~df.historical_id)&(df.distance_ft>cfg['historical_standoff_ft']+400)
    sim=[]; summary=[]; supports=[];cont=[]; raw=[]
    for name,side,offset,method in cfg['designs']+load(E/'census_sensitivity.json')['designs']:
        d=df.copy()
        blocks=[block(g,side,offset) for g in polygons]
        roles={b:labels(unit(str((cfg['allocation_seed'],name,b)))) for b in set(blocks)}
        if method=='census':
            test_blocks={blocks[i] for i in range(len(d)) if clean[i]}
            roles={b:('test' if b in test_blocks else ('train' if unit(str((cfg['allocation_seed'],name,b)))<.75 else 'dev')) for b in set(blocks)}
        d['block']=[f'{x},{y}' for x,y in blocks]
        d['draw']=[roles[b] for b in blocks]
        d['p_test']=np.where(clean,1. if method=='census' else .45,0.)
        reasons=[]; spl=[]; pt=[]; pdv=[]
        for i,(g,b) in enumerate(zip(polygons,blocks)):
            x,y=b; peers={blocks[j] for j in edges[i] if available[j] and blocks[j]!=b}
            test_peers={blocks[j] for j in edges[i] if clean[j] and blocks[j]!=b}
            role=roles[b]
            reason=''
            if not available[i]:reason='sealed_or_guard'
            elif method=='core':
                margin=threshold/2
                if not box(offset+x*side+margin,offset+y*side+margin,offset+(x+1)*side-margin,offset+(y+1)*side-margin).covers(g):
                    reason='crosses_fixed_core'
            if reason:d.loc[i,'p_test']=0.
            pt.append(0 if reason else .4*(.4**len(test_peers)*.85**len(peers-test_peers) if method=='priority' else 1))
            pdv.append(0 if reason else .15*(.55**len(test_peers) if method=='priority' else 1))
            if method=='census':
                viable=not reason and role!='test' and not (test_peers & test_blocks)
                pt[-1]=.75**(1+len(peers-test_blocks)) if viable else 0.
                pdv[-1]=.25 if viable else 0.
            if not reason:
                if role=='test' and not clean[i]:reason='historical_guard'
                elif method!='core' and role!='test' and any(roles[p]=='test' for p in test_peers):reason='test_neighbor_guard'
                elif method!='core' and role=='train' and any(roles[p]=='dev' for p in peers):reason='dev_neighbor_guard'
            reasons.append(reason);spl.append('excluded' if reason else role)
        d['p_train']=pt;d['p_dev']=pdv;d['reason']=reasons;d['split']=spl
        for i in range(len(d)):
            if spl[i]!='excluded':
                assert all(spl[j] in ('excluded',spl[i]) for j in edges[i])
        d.to_csv(O/(name+'_roster.csv'),index=False)
        q=d[d.split=='test'].copy()
        hulls=[MultiPoint(v[['veg','built']].values).convex_hull for _,v in q.groupby('cell')]
        common=shapely.intersection_all(hulls) if len(hulls)==4 else shapely.GeometryCollection()
        q['shared']=[common.covers(shapely.Point(a,b)) for a,b in zip(q.veg,q.built)]
        for split in ('train','dev','test'):
            sub=d[d.split==split]
            summary.append(dict(design=name,split=split,n=len(sub),blocks=sub.block.nunique(),cells=dict(sub.cell.value_counts()),boroughs=dict(sub.borough.value_counts()),positive_test_pi=int((d.p_test>0).sum())))
        for scope,v in [('all',q),('hull',q[q.shared])]:
            for c in cells:
                z=v[v.cell==c]; cnt=z.block.value_counts()
                supports.append(dict(design=name,scope=scope,cell=c,n=len(z),blocks=len(cnt),effective_blocks=1/np.sum((cnt/len(z))**2) if len(z) else 0,boroughs='|'.join(sorted(set(z.borough))),rare_bare_gt1pct=int((z.bare>.01).sum()),rare_rail_gt1pct=int((z.rail>.01).sum()),rare_rail_blocks=z[z.rail>.01].block.nunique(),rare_bare_blocks=z[z.bare>.01].block.nunique()))
            if not len(v):continue
            if v.cell.nunique()!=4:continue
            for axis in ['cell','older','rent']:
                table=pd.crosstab(v.block,v[axis]).reindex(columns=cells,fill_value=0)
                support=table.to_numpy().T
                if np.any(support.sum(1)==0):continue
                frac=support/support.sum(1)[:,None]
                coords=[list(map(int,b.split(','))) for b in table.index]
                dist=cdist(coords,coords,metric='cityblock')
                for key,coef in [('extreme',[-1,0,0,1]),('factorial',[1,-1,-1,1])]:
                    coef=np.array(coef)
                    a=coef@frac
                    independent=np.sum(coef**2/support.sum(1))
                    for rho in [.05,.25,.50]:
                        for corr in [0,.35]:
                            variance=(1-rho)*independent+rho*(a @ (corr**dist) @ a)
                            effective=min(1/np.sum(f**2) for f,k in zip(frac,coef) if k)
                            dfree=max(1,effective-1)
                            mult=t.ppf(.975,dfree)
                            for sd in [3,5,8]:
                                width=mult*sd*np.sqrt(variance)
                                sim.append(dict(design=name,scope=scope,axis=axis,contrast=key,icc=rho,neighbor=corr,sd=sd,halfwidth_pp=width,conservative_df=dfree,shared_blocks=int(((support>0).sum(0)>1).sum())))
            x=v[['poverty','black']].to_numpy();x-=x.mean(0)
            mat=np.column_stack([np.ones(len(v)),x,x.prod(1)])
            res=mat[:,-1]-mat[:,:3]@np.linalg.lstsq(mat[:,:3],mat[:,-1],rcond=None)[0]
            lever=pd.Series(res**2,index=v.index).groupby(v.block).sum()
            cont.append(dict(design=name,scope=scope,rank=int(np.linalg.matrix_rank(mat)),interaction_residual_ss=round(float(res@res),5),max_block_information_fraction=float(lever.max()/lever.sum()) if lever.sum()>0 else None))
        raw.append((name,d,polygons))
    save('allocations',summary);save('support',supports);save('precision',sim);save('continuous_interaction',cont)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig,axes=plt.subplots(3,2,figsize=(10,14))
    colors={'test':'#166d8f','dev':'#e8a435','train':'#518b52','excluded':'#e2e2e2'}
    for ax,(name,d,gs) in zip(axes.flat,raw):
        paths=[]; cs=[]
        for g,s in zip(gs,d.split):
            for poly in shapely.get_parts(g):
                paths.append(np.asarray(poly.exterior.coords));cs.append(colors[s])
        ax.add_collection(PolyCollection(paths,facecolors=cs,edgecolors='none'))
        ax.autoscale();ax.set_aspect('equal');ax.axis('off');ax.set_title(name)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=c,label=s) for s,c in colors.items()],loc='lower center',ncol=4)
    fig.savefig(O/'candidate_maps.png',dpi=145);plt.close(fig)
    print(pd.DataFrame(summary).to_string(index=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('geometry',type=Path);run(p.parse_args())
