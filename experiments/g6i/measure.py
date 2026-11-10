"""Reduce complete dense predictions to tract measurements and planning projections.

Call with the project root as cwd and the directory containing family receipts as argument.
"""
from pathlib import Path
import json,sys
from itertools import combinations
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import t
ROOT=Path('manifests/g6i')
NAMES=['tree','grass_shrub','bare_soil','water','building','road','other_impervious','rail']
DOMAINS={**{n:[i] for i,n in enumerate(NAMES)},'vegetation':[0,1],'constructed':[4,5,6,7]}
def read(path):
    return pd.read_csv(path,dtype={'geoid':str,'cell':str})
def ratio(a,b):return a/b if b else np.nan

def sd_icc(frame):
    groups=frame.groupby('block').error
    n=len(frame)
    k=groups.ngroups
    if k<2 or n<=k:return np.nan,np.nan
    counts=groups.size()
    within=(groups.var().fillna(0)*(counts-1)).sum()/(n-k)
    between=(counts*(groups.mean()-frame.error.mean())**2).sum()/(k-1)
    n0=(n-(counts**2).sum()/n)/(k-1)
    variance=max(0,(between-within)/n0)
    return frame.error.std(),ratio(variance,variance+within)

def project(weights,sd,icc):
    cells=['00','01','10','11']
    for scope,w in weights.groupby('scope'):
        idx=sorted(w.block.unique())
        xy=np.array([b.split(',') for b in idx],float)
        kernel=.35**(.5*cdist(xy,xy,'cityblock'))
        mass=[];sq=[];eff=[]
        for c in cells:
            sub=w[w.cell==c]
            z=sub.groupby('block').weight.sum().reindex(idx,fill_value=0).to_numpy()
            assert abs(z.sum()-1)<1e-7
            mass.append(z);eff.append(1/(z@z));sq.append(sub.weight@sub.weight)
        for name,cs,lim in [('extreme',[-1,0,0,1],3),('factorial',[1,-1,-1,1],5)]:
            co=np.array(cs)
            v=co@mass
            df=min(e for e,c in zip(eff,co) if c)-1
            width=sd*t.ppf(.975,df)*np.sqrt((1-icc)*((co**2)@sq)+icc*(v@kernel@v))
            yield dict(scope=scope,contrast=name,halfwidth_pp=width,df=df,target_pp=lim)

def main(run_dir):
    roster=read('manifests/g6g/reserve8_roster.csv')
    dev=roster[roster.split=='dev'].set_index('geoid')
    w=read('manifests/g6h/qualified_weights.csv').merge(roster[['geoid','block']],on='geoid',validate='many_to_one')
    qualified=read('manifests/g6h/coverage.csv').query("split == 'dev'").set_index('geoid')
    metrics=[];tract=[];precision=[];closure=[];confusions=[]
    for receipt in sorted(run_dir.glob('*/receipt.json')):
        family=receipt.parent.name
        if family=='qwen':continue
        matrix=json.loads((receipt.parent/'tract_confusion.json').read_text())
        assert set(matrix)==set(dev.index)
        total=np.zeros((8,8),dtype='int64')
        for gid,m in matrix.items():
            m=np.asarray(m,dtype='int64')
            assert m.shape==(8,8) and m.min()>=0 and m.sum()>0
            expected=json.loads(qualified.at[gid,'paired_class_counts'])[1:]
            np.testing.assert_array_equal(m.sum(1),expected)
            total+=m
            ref=m.sum(1)*100/m.sum()
            hat=m.sum(0)*100/m.sum()
            assert abs(ref.sum()-100)<1e-8 and abs(hat.sum()-100)<1e-8
            closure.append(dict(model=family,geoid=gid,half_l1_pp=abs(hat-ref).sum()/2))
            for key,classes in DOMAINS.items():
                a,b=ref[classes].sum(),hat[classes].sum()
                tract.append(dict(model=family,geoid=gid,block=dev.at[gid,'block'],cell=dev.at[gid,'cell'],outcome=key,pixels=m.sum(),reference_pp=a,predicted_pp=b,signed_pp=b-a,absolute_pp=abs(b-a)))
        for i,key in enumerate(NAMES):
            for j,predicted in enumerate(NAMES):
                confusions.append(dict(model=family,reference=key,predicted=predicted,pixels=total[i,j]))
            a,b,hit=total[i,:].sum(),total[:,i].sum(),total[i,i]
            metrics.append(dict(model=family,outcome=key,reference_pixels=a,predicted_pixels=b,precision=ratio(hit,b),recall=ratio(hit,a),iou=ratio(hit,a+b-hit),f1=ratio(2*hit,a+b)))
    qpath=run_dir/'qwen/tract_shares.json'
    if qpath.exists():
        q=json.loads(qpath.read_text())
        assert set(q)==set(dev.index)
        coverage=[]
        bounds=[]
        matched=[]
        dense=json.loads((qpath.parent/'matched_dense_counts.json').read_text())
        for gid,v in q.items():
            coverage.append(dict(geoid=gid,windows=v['windows'],invalid_windows=v['failed'],total_area=v['area'],valid_area=v['valid'],valid_fraction=v['valid']/v['area']))
            np.testing.assert_array_equal(v['full_ref'],json.loads(qualified.at[gid,'paired_class_counts'])[1:])
            for name,ids in DOMAINS.items():
                reference=100*np.asarray(v['full_ref'])[ids].sum()/v['area']
                low=100*np.asarray(v['pred'])[ids].sum()/v['area']
                high=low+100*(1-v['valid']/v['area'])
                bounds.append(dict(geoid=gid,outcome=name,reference_pp=reference,lower_bias_pp=low-reference,upper_bias_pp=high-reference))
            if not v['valid']:continue
            for key,ids in DOMAINS.items():
                ref,hat=[100*np.sum(np.asarray(v[k])[ids])/v['valid'] for k in ('ref','pred')]
                for f,by_id in dense.items():
                    counts=by_id[gid]
                    assert sum(counts)==v['valid']
                    h=100*np.asarray(counts)[ids].sum()/v['valid']
                    matched.append(dict(geoid=gid,outcome=key,dense_family=f,paired_pixels=v['valid'],reference_pp=ref,dense_pp=h,qwen_pp=hat,delta_absolute_pp=abs(hat-ref)-abs(h-ref)))
                tract.append(dict(model='qwen_valid_windows',geoid=gid,block=dev.at[gid,'block'],cell=dev.at[gid,'cell'],outcome=key,pixels=v['valid'],reference_pp=ref,predicted_pp=hat,signed_pp=hat-ref,absolute_pp=abs(hat-ref)))
        pd.DataFrame(bounds).to_csv(ROOT/'qwen_missing_area_bounds.csv',index=False)
        pd.DataFrame(matched,columns=['geoid','outcome','dense_family','paired_pixels','reference_pp','dense_pp','qwen_pp','delta_absolute_pp']).to_csv(ROOT/'qwen_matched_dense.csv',index=False)
        pd.DataFrame(coverage).to_csv(ROOT/'qwen_coverage.csv',index=False)
    if not tract:return
    frame=pd.DataFrame(tract)
    for (family,key),g in frame.groupby(['model','outcome']):
        if family=='qwen_valid_windows' and any(r['invalid_windows'] for r in coverage):
            # Frozen weights target complete paired tract shares. Returned windows select a different area.
            continue
        for mode in ['signed_pp','absolute_pp']:
            sd,icc=sd_icc(g.assign(error=g[mode]))
            for p in project(w,sd,icc):
                precision.append(dict(model=family,outcome=key,error_type=mode,dev_n=len(g),dev_blocks=g.block.nunique(),sd_pp=sd,icc=icc,**p))
    ROOT.mkdir(exist_ok=True)
    for name,data in [('tract_measurements',frame),('pixel_metrics',pd.DataFrame(metrics)),('confusion',pd.DataFrame(confusions)),('projected_precision',pd.DataFrame(precision)),('composition',pd.DataFrame(closure))]:
        data.to_csv(ROOT/(name+'.csv'),index=False)
    comparisons=[]
    for outcome,g in frame[frame.model!='qwen_valid_windows'].groupby('outcome'):
        losses=g.pivot(index=['geoid','block'],columns='model',values='absolute_pp')
        for a,b in combinations(losses.columns,2):
            delta=(losses[b]-losses[a]).dropna()
            assert len(delta)==len(dev)
            deletion=[delta[delta.index.get_level_values('block')!=block].mean()
                      for block in delta.index.get_level_values('block').unique()]
            comparisons.append(dict(outcome=outcome,model_a=a,model_b=b,n=len(delta),
                                    paired_mae_b_minus_a_pp=delta.mean(),
                                    leave_one_block_min_pp=min(deletion),
                                    leave_one_block_max_pp=max(deletion)))
    pd.DataFrame(comparisons).to_csv(ROOT/'paired_development.csv',index=False)
    frame.groupby(['model','outcome'])[['signed_pp','absolute_pp']].mean().to_csv(ROOT/'equal_tract_summary.csv')
    pd.DataFrame(metrics).groupby('model').f1.agg(['mean','count']).to_csv(ROOT/'pixel_macro_f1.csv')
if __name__=='__main__':main(Path(sys.argv[1]))
