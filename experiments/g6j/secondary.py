"""Prespecified secondary greening screen, stable-ACS subset and coverage denominators."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from analyze import ROOT, read, CELLS, CONTRASTS, Design

FREEZE=ROOT/'secondary_design.json'


def freeze():
    coverage=read('manifests/g6h/coverage.csv')
    train=coverage[(coverage.split=='train') & coverage.eligible95 & coverage.cell.str.startswith('1')]
    a=np.asarray([json.loads(x)[1:] for x in train.paired_class_counts],float)
    a*=100/a.sum(1)[:,None]
    cuts=json.loads(Path('manifests/g6d/intersection_support.json').read_text())['cuts']
    design=dict(n=len(a),vegetation=sorted(a[:,:2].sum(1)),road=sorted(a[:,5]),cuts=cuts,
                qualifiers='Prospective reserve8 high-poverty training reference, identical mapped paired denominator, equal tracts.',
                seed=614,bootstrap=2000,minimum_selected_blocks=10)
    if FREEZE.exists():
        assert json.loads(FREEZE.read_text())==design
    else:
        FREEZE.write_text(json.dumps(design,indent=2)+'\n')
    return design


def mid(x,train):
    return (np.searchsorted(train,x,'left')+np.searchsorted(train,x,'right'))/(2*len(train))


def scores(v,r,d,q):
    tv,tr=np.quantile(d['vegetation'],q),np.quantile(d['road'],1-q)
    vpass=v<=tv
    rpass=r>=tr
    return vpass,rpass,np.minimum(1-mid(v,d['vegetation']),mid(r,d['road']))


def choose(conditions,ids,cap):
    v,r,score=conditions
    indexes=np.flatnonzero(v&r)
    # IDs can repeat in a block bootstrap. Draw order breaks equal-ID ties.
    order=np.lexsort((indexes,ids[indexes],-score[indexes]))
    keep=np.zeros(len(v),bool)
    keep[indexes[order[:cap]]]=True
    return keep


def screening(g,design,q):
    cols=[(g['vegetation',arm].to_numpy(),g['road',arm].to_numpy()) for arm in ('reference','predicted')]
    ids=g.index.to_numpy()
    block=g['block',''].to_numpy()
    cell=g['cell',''].to_numpy()
    cond=[scores(v,r,design,q) for v,r in cols]
    capacity=int(np.ceil(.10*len(g)))
    selected=[choose(arm,ids,capacity) for arm in cond]
    a,b=selected
    group_masks={'all':np.ones(len(g),bool),'10':cell=='10','11':cell=='11'}
    cells=[]
    for label,mask in group_masks.items():
        nr=int((a&mask).sum())
        nb=len(np.unique(block[a&mask]))
        cells.append(dict(cell=label,n=mask.sum(),blocks=len(np.unique(block[mask])),reference_selected=nr,selected_blocks=nb,
                          ai_selected=(b&mask).sum(),omitted=(a&~b&mask).sum(),added=(b&~a&mask).sum(),
                          capture=(a&b&mask).sum()/nr if nr else np.nan,
                          interval_status='eligible' if nb>=10 and mask.sum()>=20 else 'insufficient_selected_block_support'))
    if any(x['interval_status']=='eligible' for x in cells):
        rng=np.random.default_rng(614)
        blocks=np.unique(block)
        lookup=[np.flatnonzero(block==k) for k in blocks]
        draws={k:[] for k in group_masks}
        for i in range(2000):
            idx=np.concatenate([lookup[j] for j in rng.integers(len(blocks),size=len(blocks))])
            cap=int(np.ceil(.10*len(idx)))
            ar,br=[choose(tuple(x[idx] for x in arm),ids[idx],cap) for arm in cond]
            for k,m in group_masks.items():
                nr=sum(ar&m[idx])
                if nr:draws[k].append(sum(ar&br&m[idx])/nr)
        for item in cells:
            if item['interval_status']=='eligible':
                vals=draws[item['cell']]
                item.update(valid_draws=len(vals),capture_lo=np.quantile(vals,.025),capture_hi=np.quantile(vals,.975))
    diagnostics=[]
    for (v,r),arm,sel,name in zip(cols,cond,selected,('reference','predicted')):
        diagnostics.append(dict(arm=name,capacity=capacity,vegetation_only_pass=arm[0].sum(),road_only_pass=arm[1].sum(),
                                joint_candidates=sum(arm[0]&arm[1]),unfilled=capacity-sum(sel),
                                road_excludes_veg_candidates=sum(arm[0]&~arm[1]),veg_road_spearman=spearmanr(v,r).statistic))
    return cells,diagnostics


def main():
    design=freeze()
    roster=read('manifests/g6g/reserve8_roster.csv').set_index('geoid')
    cohort=read('manifests/g6h/coverage.csv').query("split=='test'")
    source=json.loads(Path('manifests/g6d/social_frame.json').read_text())
    margins={r['geoid']:r['moe90'] for r in source}
    rows=[];diag=[];stable=[];support=[]
    data=read(ROOT/'tract_measurement.csv')
    for family,f in data.groupby('family'):
        p=f.pivot(index='geoid',columns='outcome',values=['reference','predicted']).swaplevel(axis=1)
        p['block','']=roster.block
        p['cell','']=roster.cell
        pool=p[p['cell',''].str.startswith('1')]
        for q in (.20,.25,.30):
            counts,checks=screening(pool,design,q)
            rows.extend(dict(family=family,q=q,**r) for r in counts)
            diag.extend(dict(family=family,q=q,**r) for r in checks)
        stable_ids=[i for i in p.index if all(margins[i][k] is not None and
                    abs(roster.at[i,k]-design['cuts'][k])>margins[i][k] for k in ('poverty','black'))]
        sub=roster.loc[stable_ids]
        des=Design(sub.cell,sub.block,np.ones(len(sub)))
        for outcome in ('vegetation','constructed'):
            err=(p[outcome,'predicted']-p[outcome,'reference']).loc[stable_ids]
            for metric,y in [('signed',err),('absolute',abs(err))]:
                for k,c in CONTRASTS.items():
                    stable.append(dict(family=family,scope='axes_clear_of_individual_90pct_margins',outcome=outcome,
                                       metric=metric,contrast=k,n=len(sub),**des.contrast(y.to_numpy(),c)))
        for name,group in f.groupby('outcome'):
            g=group[group.reference>0]
            support.append(dict(family=family,outcome=name,tracts=len(group),positive_reference_tracts=len(g),
                                positive_reference_blocks=roster.loc[g.geoid,'block'].nunique(),
                                positive_prediction_tracts=sum(group.predicted>0)))
    for filename,records in [('screening',rows),('screen_diagnostics',diag),('acs_stability',stable),('native_support',support)]:
        pd.DataFrame(records).to_csv(ROOT/(filename+'.csv'),index=False)
    sums=cohort.groupby('cell').agg(frozen=('geoid','size'),eligible=('eligible95','sum'),blocks=('block','nunique'),
                                      mapped=('mapped','sum'),paired=('paired','sum'))
    sums['paired_fraction']=sums.paired/sums.mapped
    sums.to_csv(ROOT/'coverage_by_cell.csv')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--freeze-only',action='store_true')
    if p.parse_args().freeze_only:freeze()
    else:main()
