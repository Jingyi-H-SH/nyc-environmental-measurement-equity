"""Track loss of original target mass separately from restandardization after qualification."""
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import t
from summarize import O,read

def run():
    d=read(O/'coverage.csv'); w=read('manifests/g6g/standardization_weights.csv').query('design=="reserve8"')
    x=w.merge(d[['geoid','eligible95','block','mapped','paired']],on='geoid',validate='many_to_one')
    assert len(w)==len(x)
    cells=['00','01','10','11'];out=[];loss=[]
    for scope,g in x.groupby('scope'):
        miss=[]; inside=[]; m=[];sq=[];eff=[]
        blocks=sorted(g.block.unique());coord=np.array([b.split(',') for b in blocks],float)
        K=.35**(.5*cdist(coord,coord,'cityblock'))
        for c in cells:
            v=g[g.cell==c];e=v[v.eligible95];a=v.loc[~v.eligible95,'weight'].sum()
            assert abs(v.weight.sum()-1)<1e-8 and a<1
            miss.append(a);inside.append((e.weight*(1-e.paired/e.mapped)).sum())
            z=e.weight/e.weight.sum()
            mass=z.groupby(e.block).sum().reindex(blocks,fill_value=0).values
            m.append(mass);sq.append(z@z);eff.append(1/(mass@mass))
            loss.append(dict(scope=scope,cell=c,excluded_tracts=len(v)-len(e),excluded_weight=a,unpaired_pixel_weight_among_retained=inside[-1]))
        for name,cs,lim in [('extreme',[-1,0,0,1],3),('factorial',[1,-1,-1,1],5)]:
            co=np.array(cs);cm=co@m;df=min(k for k,c in zip(eff,co) if c)-1
            for scenario,sd,icc in [('central',5,.25),('stress',6,.35),('inherited_high_SD',8,.25)]:
                width=sd*t.ppf(.975,df)*np.sqrt((1-icc)*(co**2@sq)+icc*(cm@K@cm))
                out.append(dict(scope=scope,contrast=name,scenario=scenario,restricted_weight_halfwidth_pp=width,target_pp=lim,whole_exclusion_span_pp=100*abs(co)@miss,original_target_total_span_pp=100*abs(co)@(np.array(miss)+inside)))
    pd.DataFrame(loss).to_csv(O/'original_target_loss.csv',index=False)
    pd.DataFrame(out).to_csv(O/'original_weight_sensitivity.csv',index=False)
if __name__=='__main__':run()
