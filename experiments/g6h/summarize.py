"""Local metadata-only summary after cloud qualification. Never reads prediction files."""
import json,hashlib
from pathlib import Path
import pandas as pd, numpy as np, shapely
from scipy.spatial.distance import cdist
from scipy.optimize import root
from scipy.special import softmax
from scipy.stats import t
O=Path('manifests/g6h');D=O/'qualification'
def read(p):return pd.read_csv(p,dtype={'geoid':str,'cell':str},float_precision='round_trip')
def summary():
    a=read(O/'baseline_coverage.csv')
    rr=read('manifests/g6g/reserve8_roster.csv'); geo=a.merge(rr[['geoid','veg','built','borough','pop']] if 'pop' in rr else rr[['geoid','veg','built','borough']],on='geoid',validate='one_to_one')
    sources=read(O/'index_links.csv')
    assert len(geo)==483 and set(geo.geoid)==set(sources.geoid)
    assert sources.groupby('image').split.nunique().max()==1
    src=pd.DataFrame([json.loads(p.read_text()) for p in sorted(D.glob('*.jp2.json'))]);assert set(src.image)==set(sources.image)
    src.to_csv(O/'source_files.csv',index=False)
    native={r['geoid']:r for r in json.loads(Path('manifests/g6d/frame.json').read_text())}
    out=[]
    for r in geo.to_dict('records'):
        q=json.loads((D/(r['geoid']+'.json')).read_text())
        assert q['reference_class_counts']==native[r['geoid']]['counts'] and sum(q['paired_class_counts'])==q['paired']
        assert np.all(np.array(q['reference_class_counts'])>=q['paired_class_counts'])
        assert q['geoid']==r['geoid'] and q['mapped']==r['reference_pixels'] and q['land']==r['terrestrial_pixels']
        assert 0<=q['paired_land']<=q['paired']<=q['rgb']<=q['decoded']<=q['polygon']
        assert sum(z[0] for z in q['land_missing_quadrants_NW_NE_SW_SE'])==q['land']
        assert sum(z[1] for z in q['land_missing_quadrants_NW_NE_SW_SE'])==q['land']-q['paired_land']
        r.pop('prospective_rgb_status')
        r.update({k:v for k,v in q.items() if k!='land_missing_quadrants_NW_NE_SW_SE'})
        r.update(official_index='MATCH',public_archive_directory='FOUND',source_file_availability='CONFIRMED',raw_download='COMPLETE',raw_cache='INSTANCE_LOCAL',decoder='VERIFIED',historical_pair_record='FOUND' if pd.notna(r['historical_paired_fraction']) else 'NOT_RECORDED')
        r.update(source_status='indexed; downloaded; CRC checked; decoded',paired_ft2=.25*q['paired'],paired_land_ft2=.25*q['paired_land'],
                 outside_index_ft2=.25*(q['polygon']-q['decoded']),invalid_rgb_in_footprint_ft2=.25*(q['decoded']-q['rgb']),
                 valid_rgb_but_unmapped_ft2=.25*(q['rgb']-q['paired']),paired_fraction=q['paired']/q['polygon'],paired_land_fraction=q['paired_land']/q['land'])
        for k,z in zip(['NW','NE','SW','SE'],q['land_missing_quadrants_NW_NE_SW_SE']):r['missing_land_ft2_'+k]=.25*z[1]
        r['eligible95']=min(r['paired_fraction'],r['paired_land_fraction'])>=.95;out.append(r)
    d=pd.DataFrame(out);d.to_csv(O/'coverage.csv',index=False)
    missing=[]
    for keys in [['split'],['split','cell'],['split','borough']]:
        for group,h in d.groupby(keys):
            group=(group,) if not isinstance(group,tuple) else group
            ratio=1-h.paired/h.polygon;lm=1-h.paired_land/h.land
            missing.append(dict(axis='+'.join(keys),**dict(zip(keys,group)),tracts=len(h),qualified=int(h.eligible95.sum()),reference_land_ft2=.25*h.land.sum(),paired_land_ft2=h.paired_land_ft2.sum(),missing_polygon_ft2=.25*(h.polygon-h.paired).sum(),missing_land_ft2=.25*(h.land-h.paired_land).sum(),median_missing_land_pct=100*lm.median(),p95_missing_land_pct=100*lm.quantile(.95),max_missing_polygon_pct=100*ratio.max()))
    pd.DataFrame(missing).to_csv(O/'missing_distribution.csv',index=False)
    classes=['tree','grass','bare','water','building','road','other_impervious','rail'];rows=[]
    for (split,cell),h in d.groupby(['split','cell']):
        mapped=np.stack(h.reference_class_counts).sum(axis=0)[1:];paired=np.stack(h.paired_class_counts).sum(axis=0)[1:]
        rows.extend(dict(split=split,cell=cell,native_class=k,reference_ft2=.25*a,paired_ft2=.25*b,unpaired_ft2=.25*(a-b),paired_fraction=b/a if a else None) for k,a,b in zip(classes,mapped,paired))
    pd.DataFrame(rows).to_csv(O/'class_coverage.csv',index=False)
    results=[];sup=[]; weights=[];cells=['00','01','10','11']
    for (s,c),f in d.groupby(['split','cell']):
        e=f[f.eligible95];sup.append(dict(split=s,scope='all',cell=c,n=len(e),blocks=e.block.nunique(),planned=len(f),effective_blocks=1/(e.block.value_counts(normalize=True)**2).sum() if len(e) else None))
    ev=d[d.eligible95 & (d.split=='test')]
    hull=shapely.intersection_all([shapely.MultiPoint(ev.loc[ev.cell==c,['veg','built']].values).convex_hull for c in cells])
    for scope,z in [('all',ev),('balanced_hull',ev[[hull.covers(shapely.Point(a)) for a in ev[['veg','built']].values]])]:
        target=z[['veg','built']].mean().values;blocks=sorted(z.block.unique());coords=[b.split(',') for b in blocks];mass=[];sq=[];eff=[]
        for c in cells:
            v=z[z.cell==c];x=(v[['veg','built']].values-target)*10
            if len(v)<2:break
            w=np.full(len(v),1/len(v)) if scope=='all' else softmax(x@root(lambda b:softmax(x@b)@x,[0.,0.]).x)
            if scope!='all' and max(abs(w@x))>1e-6:break
            m=pd.Series(w,index=v.block).groupby(level=0).sum().reindex(blocks,fill_value=0).values
            mass.append(m);sq.append(w@w);eff.append(1/(m@m))
            if scope!='all':sup.append(dict(split='test',scope=scope,cell=c,n=len(v),blocks=v.block.nunique(),effective_blocks=eff[-1]))
            weights.extend(dict(scope=scope,geoid=i,cell=c,weight=j) for i,j in zip(v.geoid,w))
        if len(eff)<4 or min(eff)<=1:
            results.append(dict(scope=scope,status='INSUFFICIENT_SUPPORT'));continue
        K=.35**(.5*cdist(np.array(coords,float),np.array(coords,float),'cityblock'))
        for name,co,limit in [('extreme',[-1,0,0,1],3),('factorial',[1,-1,-1,1],5)]:
            a=np.array(co)@mass;df=max(1,min(e for e,k in zip(eff,co) if k)-1)
            for scenario,sd,icc in [('central',5,.25),('stress',6,.35),('inherited_high_SD',8,.25)]:
                half=sd*t.ppf(.975,df)*np.sqrt((1-icc)*(np.square(co)@sq)+icc*(a@K@a))
                results.append(dict(scope=scope,status='PROJECTED',contrast=name,scenario=scenario,sd_pp=sd,icc=icc,df=df,halfwidth_pp=half,target_pp=limit,meets_target=half<=limit,break_even_sd_pp=sd*limit/half))
    W=pd.DataFrame(weights); old=read('manifests/g6g/standardization_weights.csv').query('design=="reserve8"')
    match=old.merge(W,on=['geoid','scope','cell'],how='outer',suffixes=('_frozen','_qualified'),indicator=True)
    match.to_csv(O/'weight_comparison.csv',index=False)
    wq=W.merge(d[['geoid','mapped','paired']],on='geoid',validate='many_to_one')
    wq['missing_mass']=100*wq.weight*(1-wq.paired/wq.mapped)
    bounds=[]
    for scope,h in wq.groupby('scope'):
        m=h.groupby('cell').missing_mass.sum()
        for name,co in [('extreme',[-1,0,0,1]),('factorial',[1,-1,-1,1])]:
            bounds.append(dict(scope=scope,contrast=name,worst_case_span_pp=sum(abs(k)*m.get(c,0) for c,k in zip(cells,co)),interpretation='uncertainty width from unconstrained predicted class on unpaired mapped pixels; fixed full reference, qualified tracts'))
    pd.DataFrame(bounds).to_csv(O/'missing_area_bounds.csv',index=False)
    pd.DataFrame(weights).to_csv(O/'qualified_weights.csv',index=False);pd.DataFrame(results).to_csv(O/'qualified_precision.csv',index=False);pd.DataFrame(sup).to_csv(O/'qualified_support.csv',index=False)
if __name__=='__main__':summary()
