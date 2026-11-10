"""Outcome-free precision under a common physical correlation range and calibrated morphology."""
from design import O, E, cells, cfg, geoms
from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
import shapely
from scipy.optimize import root
from scipy.special import softmax
from scipy.spatial.distance import cdist
from scipy.stats import t

rng=np.random.default_rng(cfg['simulation_seed'])
geography=geoms(Path(sys.argv[1])/'tl_2019_36_tract.zip')
records=[]; weights=[]; guards=[]
for name,side,offset,method in cfg['designs']+json.loads((E/'census_sensitivity.json').read_text())['designs']:
    d=pd.read_csv(O/f'{name}_roster.csv',dtype={'geoid':str,'cell':str},float_precision='round_trip')
    s={k:d[d.split==k] for k in ['train','dev','test']}
    unions={k:shapely.union_all([geography[x] for x in v.geoid]) for k,v in s.items()}
    for a,b in [('train','dev'),('dev','test'),('train','test')]:
        dist=unions[a].distance(unions[b])
        assert dist>4000 and not set(s[a].block)&set(s[b].block)
        guards.append(dict(design=name,a=a,b=b,min_ft=dist))
    q=s['test']
    assert (q.distance_ft>3600).all() and (q.seal_distance>4000).all()
    hull=shapely.intersection_all([shapely.MultiPoint(v[['veg','built']].values).convex_hull for _,v in q.groupby('cell')])
    for scope in ['all','balanced_hull']:
        z=q if scope=='all' else q[[hull.covers(shapely.Point(x)) for x in q[['veg','built']].values]]
        target=z[['veg','built']].mean().values
        ws=[]; reasons=[]
        for c in cells:
            v=z[z.cell==c]
            if v.empty:
                reasons.append(c+' empty');continue
            x=(v[['veg','built']].values-target)*10
            w=np.full(len(v),1/len(v))
            if scope!='all':
                sol=root(lambda b:softmax(x@b)@x,np.zeros(2))
                w=softmax(x@sol.x)
                if np.max(abs(w@x))>1e-6:
                    reasons.append(c+' lacks mean support');continue
            if v.block.nunique()<2: reasons.append(c+' single block')
            ws.append(pd.Series(w,index=v.index))
            weights.extend(dict(design=name,scope=scope,geoid=i,cell=c,weight=p) for i,p in zip(v.geoid,w))
        if reasons:
            records.append(dict(design=name,scope=scope,status='; '.join(reasons)));continue
        blocks=sorted(set(z.block))
        coords=[list(map(int,b.split(','))) for b in blocks]
        K=.35**(cdist(coords,coords,metric='cityblock')*side/16000)
        latent=rng.normal(size=(10000,len(blocks)))@np.linalg.cholesky(K).T
        for contrast,coef in [('extreme',[-1,0,0,1]),('factorial',[1,-1,-1,1])]:
            masses=[w.groupby(z.loc[w.index,'block']).sum().reindex(blocks,fill_value=0).values for w in ws]
            eff=min(1/(m@m) for m,k in zip(masses,coef) if k)
            a=np.array(coef)@np.array(masses)
            residual=sum(k*k*(w@w) for k,w in zip(coef,ws))
            sd=5*np.sqrt(.75*residual+.25*(a@K@a))
            draws=5*(np.sqrt(.25)*(latent@a)+np.sqrt(.75*residual)*rng.normal(size=len(latent)))
            records.append(dict(design=name,scope=scope,status='estimated',contrast=contrast,n=len(z),effective_min=eff,sd_pp=sd,simulation_sd_pp=draws.std(ddof=1),halfwidth_pp=t.ppf(.975,max(1,eff-1))*sd))
pd.DataFrame(records).to_csv(O/'physical_precision.csv',index=False)
pd.DataFrame(weights).to_csv(O/'standardization_weights.csv',index=False)
pd.DataFrame(guards).to_csv(O/'geometric_verification.csv',index=False)
