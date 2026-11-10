"""Distributional and association consequences of measurement, with geographic deletion."""
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance,t
from analyze import ROOT,read,CELLS


def midrank(values, weights):
    order=np.argsort(values,kind='stable')
    v,w=values[order],weights[order]
    _,idx,inverse=np.unique(v,return_index=True,return_inverse=True)
    mass=np.add.reduceat(w,idx)
    rank=np.empty(len(v))
    rank[order]=(np.cumsum(mass)-.5*mass)[inverse]/mass.sum()
    return rank


def estimate(g):
    # Keep the empirical tract fractions of the four social cells in each scope.
    w=g.weight.to_numpy().copy()
    groups=g.cell.to_numpy()
    r,p=g.reference.to_numpy(),g.predicted.to_numpy()
    out={}
    for cell in CELLS:
        sel=groups==cell
        if not np.any(sel):return {}
        w[sel]*=sel.mean()/w[sel].sum()
        out['wasserstein_'+cell]=wasserstein_distance(r[sel],p[sel],u_weights=w[sel],v_weights=w[sel])
    a,b=midrank(r,w),midrank(p,w)
    a0,b0=a-np.average(a,weights=w),b-np.average(b,weights=w)
    denom=np.sqrt((w@a0**2)*(w@b0**2))
    out['spearman']=w@(a0*b0)/denom if denom else np.nan
    out['rank_shift_ge10_fraction']=w@(abs(a-b)>=.10-1e-12)
    s=g.poverty.to_numpy()*10
    v=g.black.to_numpy()*10
    s-=np.average(s,weights=w)
    v-=np.average(v,weights=w)
    x=np.column_stack([np.ones(len(g)),s,v,s*v])
    wx=np.sqrt(w[:,None])*x
    if np.linalg.matrix_rank(wx)==4:
        # RQ3 slopes are the paired difference of two regressions with identical X and W.
        coeff=np.linalg.lstsq(wx,np.sqrt(w)*(p-r),rcond=None)[0]
        for key,coef in zip(['intercept','poverty10','black10','interaction10x10'],coeff):
            out[key]=coef
        rr=x[:,3]-x[:,:3]@np.linalg.lstsq(wx[:,:3],wx[:,3],rcond=None)[0]
        info=w*rr**2
        out['max_block_product_information_fraction']=pd.Series(info,index=g.block).groupby(level=0).sum().max()/info.sum()
    return out


def main():
    frame=read(ROOT/'tract_measurement.csv')
    roster=read('manifests/g6g/reserve8_roster.csv')
    weights=read('manifests/g6h/qualified_weights.csv').merge(roster[['geoid','block','poverty','black']],on='geoid')
    rows=[]
    for (scope,family,outcome),g in frame.merge(weights,on='geoid').groupby(['scope','family','outcome']):
        values=estimate(g)
        deleted=pd.DataFrame([estimate(g[g.block!=b]) for b in sorted(g.block.unique())])
        B=g.block.nunique()
        for key,val in values.items():
            d=deleted[key].dropna()
            ok=len(d)==B
            se=np.sqrt((B-1)/B*((d-d.mean())**2).sum()) if ok else np.nan
            width=t.ppf(.975,B-1)*se
            rows.append(dict(scope=scope,family=family,outcome=outcome,statistic=key,estimate=val,
                             lower=val-width,upper=val+width,leave_min=d.min(),leave_max=d.max(),valid_deletions=len(d),blocks=B))
    pd.DataFrame(rows).to_csv(ROOT/'rq3_distributions_slopes.csv',index=False)

if __name__=='__main__':
    main()
