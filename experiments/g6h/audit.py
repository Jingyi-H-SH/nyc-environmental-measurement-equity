"""From project root: .venv/bin/python experiments/g6h/audit.py. Metadata only."""
import csv, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import t
P=Path('manifests/g6g'); O=Path('manifests/g6h')
def check(ok,reason):
    if not ok: raise ValueError(reason)
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    for line in (P/'SHA256SUMS').read_text().splitlines():
        h,p=line.split(maxsplit=1); check(digest(p)==h,p)
    read=lambda p: pd.read_csv(p,dtype={'cell':str,'geoid':str,'cell_black':str},float_precision='round_trip')
    roster=read(P/'reserve8_roster.csv'); r=roster.query('split!="excluded"').copy()
    original=set(read(P/'original_seal_ids.csv').geoid)
    check(len(original)==74 and not original.intersection(r.geoid),'original seal')
    check(r.geoid.is_unique and r.groupby('block').split.nunique().max()==1,'partition')
    check(r.groupby('split').size().to_dict()=={'dev':53,'train':163,'test':267},'roster')
    f={x['geoid']:x for x in json.loads(Path('manifests/g6d/frame.json').read_text())}
    prev=pd.read_csv('manifests/g6e/coverage.csv',usecols=['geoid','paired_fraction','paired_land_fraction'],dtype={'geoid':str}).set_index('geoid')
    med=roster[["poverty","black"]].median()
    rows=[]
    for x in r.itertuples():
        v=f[x.geoid]
        check(v['eligible'] and (''.join(str(int(v[k]>=med[k])) for k in ['poverty','black']))==x.cell and np.allclose([v['poverty'],v['black']],[x.poverty,x.black],atol=1e-14,rtol=0),x.geoid)
        check(np.allclose(v['mapped_share'],[getattr(x,k) for k in 'tree grass bare water building road other_impervious rail'.split()]),'class shares')
        rows.append(dict(geoid=x.geoid,split=x.split,block=x.block,cell=x.cell,reference_pixels=sum(v['counts'][1:]),terrestrial_pixels=sum(v['counts'][1:])-v['counts'][4],historical_paired_fraction=prev.loc[x.geoid,'paired_fraction'],historical_paired_land_fraction=prev.loc[x.geoid,'paired_land_fraction'],prospective_rgb_status='NOT_VERIFIED'))
    df=pd.DataFrame(rows);df.to_csv(O/'baseline_coverage.csv',index=False)
    w=read(P/'standardization_weights.csv').query('design=="reserve8"').merge(r.query('split=="test"')[['geoid','block','cell']],on=['geoid','cell'],validate='many_to_one')
    out=[]; support=[]
    for scope,s in w.groupby('scope'):
        blocks=sorted(s.block.unique());xy=np.array([b.split(',') for b in blocks],float)
        K=.35**(cdist(xy,xy,'cityblock')*.5)
        mass=[]; sq=[]; eff=[]
        for c in ['00','01','10','11']:
            z=s[s.cell==c]; m=z.groupby('block').weight.sum().reindex(blocks,fill_value=0).to_numpy()
            check(np.isclose(m.sum(),1),'weights')
            mass.append(m);sq.append(z.weight@z.weight);eff.append(1/(m@m))
            support.append(dict(scope=scope,cell=c,tracts=len(z),blocks=z.block.nunique(),effective_blocks=eff[-1]))
        for contrast,co,limit in [('extreme',[-1,0,0,1],3),('factorial',[1,-1,-1,1],5)]:
            a=np.array(co)@mass; dof=min(e for e,k in zip(eff,co) if k)-1
            for scenario,sd,icc in [('G6G central',5,.25),('G6H stress assumption',6,.35)]:
                factor=t.ppf(.975,dof)*np.sqrt((1-icc)*(np.square(co)@sq)+icc*(a@K@a))
                out.append(dict(scope=scope,contrast=contrast,scenario=scenario,sd_pp=sd,icc=icc,halfwidth_pp=sd*factor,limit_pp=limit,break_even_sd_pp=limit/factor))
    pd.DataFrame(out).to_csv(O/'design_only_precision.csv',index=False);pd.DataFrame(support).to_csv(O/'design_only_support.csv',index=False)
    print(df.groupby('split').agg(tracts=('geoid','size'),blocks=('block','nunique'),historical_paired=('historical_paired_fraction','count')))
if __name__=='__main__': main()
