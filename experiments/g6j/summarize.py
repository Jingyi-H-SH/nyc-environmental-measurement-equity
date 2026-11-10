"""Produce the manuscript-facing accounting directly from the frozen result tables."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import t
from analyze import ROOT, NAMES, read
from scipy.spatial.distance import cdist

def mean_interval(values, blocks):
    mean=values.mean()
    residual=(values-mean).groupby(blocks).sum().div(len(values))
    mass=blocks.value_counts(normalize=True)
    xy=np.array([key.split(',') for key in residual.index],float)
    kernel=.35**(cdist(xy,xy,'cityblock')/2)
    width=t.ppf(.975,1/(mass@mass)-1)*np.sqrt(residual@kernel@residual)
    return mean,mean-width,mean+width

def table(frame):
    def fmt(x):
        return f'{x:.3f}' if isinstance(x,float) else str(x)
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','|'+'---|'*len(frame.columns)]+[
        '| '+' | '.join(fmt(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)])

def main():
    frame=read(ROOT/'tract_measurement.csv')
    roster=read('manifests/g6g/reserve8_roster.csv')
    frame=frame.merge(roster[['geoid','block']],on='geoid',validate='many_to_one')
    means=[]
    for (f,o),g in frame.groupby(['family','outcome']):
        for metric in ('signed','absolute'):
            est,lo,hi=mean_interval(g[metric],g.block)
            means.append(dict(family=f,outcome=o,metric=metric,estimate=est,lower=lo,upper=hi))
    means=pd.DataFrame(means)
    means.to_csv(ROOT/'rq1_equal_tract_errors.csv',index=False)
    scores=[]
    for f,g in read(ROOT/'dense_confusion.csv').groupby('family'):
        m=g.pivot(index='reference',columns='prediction',values='pixels').loc[NAMES,NAMES].to_numpy()
        for k,name in enumerate(NAMES):
            tp=m[k,k]; n=m[k].sum(); p=m[:,k].sum()
            scores.append(dict(family=f,outcome=name,reference_pixels=n,predicted_pixels=p,precision=tp/p if p else np.nan,
                recall=tp/n if n else np.nan,f1=2*tp/(n+p),iou=tp/(n+p-tp)))
    scores=pd.DataFrame(scores)
    scores.to_csv(ROOT/'rq1_native_scores.csv',index=False)
    q=read(ROOT/'rq2_contrasts.csv')
    main=q[q.outcome.isin(['vegetation','constructed'])]
    gaps=read(ROOT/'rq3_gaps.csv')
    gaps=gaps[gaps.outcome.isin(['vegetation','constructed'])]
    compact=gaps.merge(main.query("metric=='signed'")[['scope','family','outcome','contrast','holm_p']],
                       on=['scope','family','outcome','contrast'],validate='one_to_one')
    dist=read(ROOT/'rq3_distributions_slopes.csv')
    bounds=read(ROOT/'original267_bounds.csv')
    bounds=bounds[bounds.outcome.isin(['vegetation','constructed']) & (bounds.metric=='signed')]
    rows=int(frame.geoid.nunique())
    blocks=frame.block.nunique()
    assert rows==265 and len(scores)==32 and len(main)==64
    pixels=frame.groupby(['family','outcome']).pixels.sum()
    assert pixels.nunique()==1
    release=json.loads((ROOT/'release.json').read_text())
    receipts=pd.DataFrame([dict(family=f,**json.loads((ROOT/'run'/(f+'-receipt.json')).read_text())) for f in release['families']])
    composition=read(ROOT/'composition.csv').groupby('family',as_index=False).total_variation_pp.mean()
    summary=scores.groupby('family',as_index=False)[['f1','iou']].mean().merge(composition,on='family')
    docs=Path('reports')
    def report(file,title,sections):
        (docs/file).write_text('# '+title+'\n\n'+'\n\n'.join(sections)+'\n')
    report('G6J_MEASUREMENT_VALIDITY.md','RQ1. Environmental measurement on held-out NYC geography',[
        f'{rows} tracts in {blocks} spatial blocks contributed {pixels.iloc[0]:,} common mapped pixels per family. The table gives pixel-pooled native macro-F1 and mean IoU and equal-tract mean compositional total variation in percentage points. I-JEPA is exploratory throughout.',
        table(summary),'Equal-tract signed error and absolute error, in pp. Intervals describe geographic replication under the prespecified spatial kernel.',
        table(means[means.outcome.isin(['vegetation','constructed'])]),table(scores),'The native-class tables include rare outcomes. Land-cover aggregates can mask opposite-signed native errors.',
        'Inference resources for each completed model',table(receipts.drop(columns='checkpoint'))])
    report('G6J_INTERSECTIONAL_EQUITY.md','RQ2. Intersectional differences in tract-level measurement error',[
        'The four cells cross neighborhood poverty and non-Hispanic Black population share. The extreme contrast compares high–high with low–low. The factorial contrast subtracts both single-high cells from the sum of the high–high and low–low cells. Positive absolute-error contrasts denote greater error for the specified contrast. Signed-error contrasts give the direction of bias.',
        'The unrestricted target includes 265 eligible tracts. Common-morphology weights describe 221 tracts in a restricted population. Each family and scope has eight prespecified Holm-adjusted tests. Spatial pointwise intervals, kernel sensitivities, effective blocks and block deletions accompany all estimates in rq2_contrasts.csv.',
        table(main[['scope','family','outcome','metric','contrast','estimate','primary_lo','primary_hi','holm_p']]),
        'Population composition comes from tract-level ACS estimates. These contrasts concern the accuracy of neighborhood measurements. Attribution to individuals or discrimination by a particular mechanism is unidentifiable. Common-morphology weighting balances the specified first moments only.'])
    report('G6J_INFERENTIAL_DISTORTION.md','RQ3. Consequences for estimated neighborhood inequalities',[
        'All reported gaps use identical tract weights for AI and mapped reference. AI minus reference reproduces the RQ2 signed-error contrast exactly. This identity gives one evidence chain and one statistical test.',
        table(compact),'Secondary distributional results. Rank shift is the fraction of tracts moving at least ten percentile points.',
        table(dist[dist.outcome.isin(['vegetation','constructed']) & dist.statistic.isin(['spearman','rank_shift_ge10_fraction'])][['scope','family','outcome','statistic','estimate','lower','upper']]),
        'Worst-case identification bounds on signed gap distortion in the original 267-tract target include all unpaired mapped pixels and both omitted tracts. These bounds describe missing-area uncertainty separately from geographic replication.',
        table(bounds[['family','outcome','contrast','lower','upper']]),
        'Hypothetical greening screen among high-poverty tracts using training-side quartiles and a ten-percent capacity. Omitted and added count tracts changing selection relative to mapped reference. Sparse selected blocks limit uncertainty estimates.',
        table(read(ROOT/'screening.csv').query('q == 0.25')[['family','cell','n','reference_selected','selected_blocks','ai_selected','omitted','added','interval_status']]),
        'All conditional Wasserstein distances, regression differences per ten percentage points, interaction leverage, and delete-one-block ranges are archived. Geographic replication intervals exclude ACS uncertainty, mapped-reference error, historical image dependence and unknown pretraining exposure. No citywide, health-outcome or causal extrapolation is identified.'])
if __name__=='__main__':main()
