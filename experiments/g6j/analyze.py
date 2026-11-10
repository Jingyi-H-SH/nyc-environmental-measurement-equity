"""Formal tract-level measurement, contrast and missing-area analyses."""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, wasserstein_distance
from spatial import CELLS, CONTRASTS, Design, bounds, holm

ROOT=Path('manifests/g6j')
sys.path.insert(0,str(Path('experiments/g6i').resolve()))
from measure import DOMAINS,NAMES

def read(path):
    return pd.read_csv(path,dtype={k:str for k in ('geoid','cell','older','rent','block')},keep_default_na=False)


def long_table(results,cohort,registry):
    rows=[];conf=[];composition=[]
    for family,w in registry.items():
        total=np.zeros((8,8),dtype=np.int64)
        paths=sorted((results/family).glob('*.json'))
        assert {p.stem for p in paths}==set(cohort.index)
        for path in paths:
            obj=json.loads(path.read_text())
            assert obj['checkpoint']==w
            m=np.array(obj['matrix'],dtype=np.int64)
            assert m.shape==(8,8) and np.all(m>=0)
            np.testing.assert_array_equal(m.sum(1),json.loads(cohort.at[path.stem,'paired_class_counts'])[1:])
            total+=m
            a,b=m.sum(1)*100/m.sum(),m.sum(0)*100/m.sum()
            composition.append(dict(family=family,geoid=path.stem,total_variation_pp=abs(b-a).sum()/2))
            for name,ids in DOMAINS.items():
                r,p=a[ids].sum(),b[ids].sum()
                rows.append(dict(family=family,geoid=path.stem,outcome=name,reference=r,predicted=p,
                                 signed=p-r,absolute=abs(p-r),pixels=m.sum()))
        for i,j in itertools.product(range(8),repeat=2):
            conf.append(dict(family=family,reference=NAMES[i],prediction=NAMES[j],pixels=total[i,j]))
    pd.DataFrame(conf).to_csv(ROOT/'dense_confusion.csv',index=False)
    pd.DataFrame(composition).to_csv(ROOT/'composition.csv',index=False)
    return pd.DataFrame(rows)


def original_bounds(frame,original):
    rows=[]
    design=Design(original.cell,original.block,np.ones(len(original)))
    for (family,name),g in frame.groupby(['family','outcome']):
        ids=DOMAINS[name]
        truth=np.array([np.array(json.loads(s)[1:])[ids].sum() for s in original.reference_class_counts])
        pred=g.set_index('geoid').reindex(original.index)
        have=pred.pixels.fillna(0).to_numpy()
        observed=pred.predicted.fillna(0).to_numpy()*have/100
        n=original.mapped.to_numpy()
        lo=(observed-truth)*100/n
        hi=(observed+n-have-truth)*100/n
        for metric,left,right in [('signed',lo,hi),('absolute',np.maximum.reduce([lo,-hi,np.zeros(len(lo))]),np.maximum(abs(lo),abs(hi)))]:
            for contrast,c in CONTRASTS.items():
                lower,upper=bounds(left,right,design,c)
                rows.append(dict(family=family,outcome=name,metric=metric,contrast=contrast,lower=lower,upper=upper,
                                 n=len(n),no_predictions=sum(have==0),unobserved_pixels=int(sum(n-have))))
    pd.DataFrame(rows).to_csv(ROOT/'original267_bounds.csv',index=False)


def main(results):
    roster=read('manifests/g6g/reserve8_roster.csv').set_index('geoid')
    orig=read('manifests/g6h/coverage.csv').query("split=='test'").set_index('geoid').sort_index()
    cohort=orig[orig.eligible95.astype(str)=='True']
    assert len(orig)==267 and len(cohort)==265
    weights=read('manifests/g6h/qualified_weights.csv')
    registry=json.loads((ROOT/'release.json').read_text())['families']
    frame=long_table(results,cohort,registry)
    frame.to_csv(ROOT/'tract_measurement.csv',index=False)
    original_bounds(frame,orig)
    contrasts=[];cells=[];gaps=[];pair=[];secondary=[]
    for scope,w in weights.groupby('scope'):
        w=w.merge(roster[['block','older','rent']],left_on='geoid',right_index=True,validate='one_to_one').sort_values('geoid')
        des=Design(w.cell,w.block,w.weight)
        for name,g in frame.groupby('outcome'):
            matrix={}
            for family,group in g.groupby('family'):
                values=group.set_index('geoid').loc[w.geoid]
                matrix[family]=values
                base=dict(scope=scope,family=family,outcome=name)
                for metric in ('signed','absolute'):
                    y=values[metric].to_numpy()
                    for j,cell in enumerate(CELLS):
                        cells.append(dict(**base,metric=metric,cell=cell,mean=des.W[j]@y,
                                          n=int(sum(w.cell==cell)),blocks=w.loc[w.cell==cell,'block'].nunique()))
                    for k,c in CONTRASTS.items():
                        result=des.contrast(y,c)
                        contrasts.append(dict(**base,metric=metric,contrast=k,**result))
                        if metric=='signed':
                            ref=c@(des.W@values.reference.to_numpy())
                            pred=c@(des.W@values.predicted.to_numpy())
                            assert abs(pred-ref-result['estimate'])<1e-8
                            gaps.append(dict(**base,contrast=k,reference_gap=ref,ai_gap=pred,distortion=pred-ref,
                                             lower=result['primary_lo'],upper=result['primary_hi']))
                    if scope=='all' and name in ('vegetation','constructed'):
                        for axis in ('older','rent'):
                            keep=w[axis].isin(CELLS).to_numpy()
                            d=Design(w[axis].to_numpy()[keep],w.block.to_numpy()[keep],np.ones(sum(keep)))
                            for k,c in CONTRASTS.items():
                                secondary.append(dict(**base,metric=metric,axis=axis,n=sum(keep),contrast=k,**d.contrast(y[keep],c)))
            for f,h in itertools.combinations(sorted(matrix),2):
                for metric in ('absolute','signed'):
                    y=(matrix[f][metric]-matrix[h][metric]).to_numpy()
                    for k,c in CONTRASTS.items():
                        pair.append(dict(scope=scope,outcome=name,family=f,minus=h,metric=metric,contrast=k,**des.contrast(y,c)))
    res=pd.DataFrame(contrasts)
    for _,g in res[res.outcome.isin(['vegetation','constructed'])].groupby(['scope','family']):
        assert len(g)==8
        res.loc[g.index,'holm_p']=holm(g.p.to_numpy())
    for filename,data in [('rq2_contrasts',res),('cell_means',cells),('rq3_gaps',gaps),('paired_models',pair),('secondary_axes',secondary)]:
        pd.DataFrame(data).to_csv(ROOT/(filename+'.csv'),index=False)
    print('verified',len(frame),'tract/outcome/model records')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('results',type=Path)
    main(ap.parse_args().results)
