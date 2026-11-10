"""Render the release record from retrieved completed-family receipts."""
import json
from pathlib import Path
import pandas as pd
base=Path('manifests/g6i')
runs=base/'run/runs'
reports=Path('reports')
def put(name,body):
    (reports/('G6I_'+name+'.md')).write_text(body.strip()+'\n')
def table(rows):
    return '\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)
def num(x):return f'{x:.3f}'
families=('cnn','segformer','yolo','ijepa','dinov3','qwen')
receipt={}
status={}
for f in families:
    path=runs/f/'receipt.json'
    if path.exists():
        receipt[f]=json.loads(path.read_text())
        status[f]='COMPLETE'
    elif f=='dinov3':status[f]='BLOCKED — official gated weight unavailable'
    elif f=='qwen' and (runs/f/'config.json').is_file():
        status[f]='STARTED — pending receipt'
    elif (runs/f/'run.log').exists():
        log=(runs/f/'run.log').read_text(errors='replace')
        status[f]='FAILED' if 'Traceback (most recent call last)' in log else 'RUNNING'
    else:status[f]='QUEUED or pending receipt'
rows=[['Family','Status','Peak allocated GiB','Elapsed seconds in last attempt'],['---','---','---:','---:']]
for f in families:
    rec=receipt.get(f,{})
    rows.append([f,status[f],num(rec['peak_bytes']/2**30) if rec else '—',num(rec['seconds_this_invocation']) if rec else '—'])
put('MULTIFAMILY_DEVELOPMENT_RESULTS','# Prospective family execution\n\n'+table(rows)+"""

All dense families use 5,196 positive-area windows on 163 fitting tracts, eight passes and one shared ordering. The planned development census comprises 6,314 windows on 53 tracts. Tract-level class shares use 1,368,453,171 paired pixels. Input manifests and per-window digests reside in the Featurize job directory. Four distinct dense backends passed independent synthetic forward and backward checks. Synthetic losses do not estimate geographic performance. Pinned family configurations, input normalization, fitted parameters and environment are archived with the run.

The persistent Featurize directory is `~/work/jev-g6i-v1`. Each completed dense backend has a final checkpoint including optimizer state, individual development masks, a tract confusion file and a completion receipt. Runtime covers loading, fitting and inference in that invocation. Retained-instance allocation and billed charges can differ. [Receipts and logs](../manifests/g6i/run/) · [Frozen configuration](../experiments/g6i/freeze.json)
""")
validity='# Multidimensional measurement validity\n\n'
if (base/'equal_tract_summary.csv').exists():
    summary=pd.read_csv(base/'equal_tract_summary.csv')
    rows=[['Family','Aggregate','Bias (pp)','MAE (pp)'],['---','---','---:','---:']]
    for r in summary[summary.outcome.isin(['vegetation','constructed'])].itertuples():
        rows.append([r.model,r.outcome,num(r.signed_pp),num(r.absolute_pp)])
    validity+=table(rows)+'\n\n'
else:validity+='Complete development predictions are pending. No tract-level validity estimate has been released.\n\n'
put('MULTIDIMENSIONAL_MEASUREMENT_VALIDITY',validity+"""Native errors are measured over the same tract pixels. Vegetation sums tree and grass/shrub. Constructed cover sums buildings, roads, other impervious surfaces and rail. Errors can cancel inside either sum. Pixel confusion retains all eight surface types, including distinctions among roads, buildings and other impervious areas. Share closure makes the eight errors dependent. Interpret hard-surface area in local environmental context. Prediction error includes differences between 2016 imagery and the 2017 reference map. Exposure of external pretraining to these locations is unknown.""")
projection='# RQ2 precision for the frozen evaluation\n\n'
if (base/'projected_precision.csv').exists():
    p=pd.read_csv(base/'projected_precision.csv')
    rows=[['Family','Outcome','Error','Dev SD (pp)','Dev block ICC','265 extreme half-width (pp)','265 factorial half-width (pp)'],['---','---','---','---:','---:','---:','---:']]
    for (f,k,e),g in p[(p.scope=='all') & p.outcome.isin(['vegetation','constructed'])].groupby(['model','outcome','error_type']):
        g=g.set_index('contrast')
        rows.append([f,k,e,num(g.iloc[0].sd_pp),num(g.iloc[0].icc),num(g.at['extreme','halfwidth_pp']),num(g.at['factorial','halfwidth_pp'])])
    projection+=table(rows)+'\n\n[Class-specific projections for both scopes](../manifests/g6i/projected_precision.csv).\n\n'
else:projection+='Family-specific development SD and block ICC estimates await complete tract predictions.\n\n'
put('RQ2_PRECISION_REASSESSMENT',projection+"""Planning targets are half-widths of 3 pp (11−00) and 5 pp (factorial). G6-H's central SD 5 pp, ICC 0.25 projects 2.65/3.82 pp across the 265 eligible tracts and 3.00/4.24 pp among 221 morphology-comparable tracts. Its stress scenario projects 3.41/4.92 and 3.81/5.29 pp, respectively. The 221-tract estimate conditions on common morphology; spatial weighting does not restore omitted geography. For the original 267-tract equal-cell target, excluded geography plus unpaired mapped area contributes worst-case signed-error identification spans of 1.285/3.461 pp. These spans are distinct from sampling half-widths.

Development SD is the observed tract-level SD. The block ICC uses an unbalanced one-way random-intercept method-of-moments estimate, with negative between-block variance truncated at zero. This plug-in calculation assumes development variance transports to the sealed cohort. Development cell 01 contains only three tracts in three blocks. Retain frozen stress projections and disclose instability. RQ3 signed gap distortion inherits the corresponding RQ2 signed-error contrast. No final errors enter these calculations. [G6-H qualification and support](G6H_INTERSECTIONAL_PRECISION_RECHECK.md) · [Original-target sensitivity](../manifests/g6h/original_weight_sensitivity.csv)""")
put('DECISION',"""# G6-I decision

**B — PARTIAL READINESS** (development-stage status). The spatial gate, common paired-area denominators and four dense output interfaces are verified. """+
    ('Prospective development receipts exist for '+', '.join(receipt)+'. ' if receipt else 'Completed prospective measurement receipts have yet to be retrieved. ')+
    """DINOv3 remains gated. Release for sealed formal evaluation requires freezing completed, qualified model identities and checking RQ2 precision and RQ3 interpretation against their actual development errors. A statistically significant disparity is not a release requirement. The 267 frozen assignments and the historical seals remain intact. [Execution status](G6I_MULTIFAMILY_DEVELOPMENT_RESULTS.md) · [Formal release criteria](G6I_FINAL_EVALUATION_READINESS.md)""")

def append(report,body):
    with (reports/('G6I_'+report+'.md')).open('a') as handle:
        handle.write('\n'+body.strip()+'\n')

append('MULTIFAMILY_DEVELOPMENT_RESULTS',"""## Checkpoint provenance and use

| Family | External initialization and interface | Source terms |
|---|---|---|
| CNN | ImageNet ResNet-34 IMAGENET1K_V1, new U-Net decoder | [Torchvision weights and dataset-use notice](https://docs.pytorch.org/vision/stable/models.html) |
| SegFormer | NVIDIA ADE B0, revision `489d5cd`, reset classifier | [Model card](https://huggingface.co/nvidia/segformer-b0-finetuned-ade-512-512) · [NVIDIA research license](https://github.com/NVlabs/SegFormer/blob/master/LICENSE) |
| YOLO | YOLO26n-sem semantic initialization, eight logits | [Ultralytics license](https://www.ultralytics.com/license) |
| I-JEPA | Frozen ViT-H/14 revision `f157467`, trained decoder | [CC BY-NC 4.0 model card](https://huggingface.co/facebook/ijepa_vith14_1k) |
| DINOv3 | SAT493M ViT-L/16 revision `f692fa4`, official client HTTP 401 and no cached authorized copy | [Gated model card and terms](https://huggingface.co/facebook/dinov3-vitl16-pretrain-sat493m) |
| Qwen | Qwen3.5-9B revision `c202236`, image-only structured shares | [Apache 2.0 model card](https://huggingface.co/Qwen/Qwen3.5-9B) |

Source-byte digests and environment locks accompany the run. Prior NYC-fitted SegFormer weights were excluded. These records document research execution; redistribution of third-party materials requires review of the applicable terms.""")
if (base/'resources.csv').exists():
    append('MULTIFAMILY_DEVELOPMENT_RESULTS',"""[Actual training steps, end-to-end throughput, sampled device utilization, power and memory](../manifests/g6i/resources.csv). End-to-end throughput divides all processed training and development windows by runtime, including checkpoint I/O. Sampled power estimates cover the device alone. They exclude host power and retained-instance idle time. Active-time cost uses the preceding G6-H observation of ¥3 per instance-hour. The provider invoice and the total cost of keeping the instance allocated are unverified.""")
if (base/'pixel_metrics.csv').exists():
    pix=pd.read_csv(base/'pixel_metrics.csv')
    conf=pd.read_csv(base/'confusion.csv')
    tr=pd.read_csv(base/'tract_measurements.csv')
    rr=[['Family','Supported classes','Macro-F1','Lowest class recall','Building → other impervious','Road → other impervious','Other impervious → building / road'],['---','---:','---:','---','---:','---:','---:']]
    for f,g in pix.groupby('model'):
        weak=g.loc[g.recall.idxmin()]
        m=conf[conf.model==f].pivot(index='reference',columns='predicted',values='pixels')
        m=m.div(m.sum(axis=1),axis=0)*100
        rr.append([f,int(g.f1.count()),num(g.f1.mean()),f'{weak.outcome} {num(weak.recall)}',f"{m.at['building','other_impervious']:.1f}%",f"{m.at['road','other_impervious']:.1f}%",f"{m.at['other_impervious','building']:.1f}% / {m.at['other_impervious','road']:.1f}%"])
    append('MULTIDIMENSIONAL_MEASUREMENT_VALIDITY',table(rr)+'\n\nPercentages condition on the native reference class. All native class counts, IoU, precision, recall and F1 are available in the [class table](../manifests/g6i/pixel_metrics.csv) and [eight-by-eight confusions](../manifests/g6i/confusion.csv). Pixel metrics give larger tracts more weight. The [signed and absolute share errors](../manifests/g6i/tract_measurements.csv) retain one observation per tract and outcome.')
if (base/'qwen_coverage.csv').exists():
    c=pd.read_csv(base/'qwen_coverage.csv')
    append('MULTIDIMENSIONAL_MEASUREMENT_VALIDITY',f"Qwen returned {int(c.windows.sum()-c.invalid_windows.sum()):,} valid arrays from {int(c.windows.sum()):,} windows. Valid outputs cover {100*c.valid_area.sum()/c.total_area.sum():.2f}% of all paired pixels. Tract share errors are conditional on returned area. The [matched comparisons](../manifests/g6i/qwen_matched_dense.csv) use identical windows for each dense–Qwen contrast. [Full-area signed-error bounds](../manifests/g6i/qwen_missing_area_bounds.csv) allow any missing-window share between 0 and 100%. Qwen supplies no pixel-level labels.")
validation=base/'release_validation.json'
if validation.is_file():
    checked=json.loads(validation.read_text())
    verified=[f for f in families if checked.get(f,{}).get('status')=='VERIFIED']
    rows=[['Family','Development release','Final fitted checkpoint or frozen source'],['---','---','---']]
    for f in families:
        h=receipt.get(f,{}).get('checkpoint_sha256')
        if f=='qwen' and f in verified:h='c202236235762e1c871ad0ccb60c8ee5ba337b9a'
        rows.append([f,'Verified' if f in verified else status[f],h or '—'])
    append('DECISION',table(rows)+'\n\nA verified dense checkpoint can advance to the separate authorization gate for sealed evaluation on common support. The VLM has separate execution and tract-coverage criteria; its coverage decision follows below. DINOv3 has no fitted task head or prospective evidence. Prespecified plug-in and stress projections govern claims about attainable precision. Spatially independent replication remains outstanding until formal evaluation. [Validation receipts](../manifests/g6i/release_validation.json).')
    if (base/'projected_precision.csv').is_file():
        z=pd.read_csv(base/'projected_precision.csv')
        z=z[z.outcome.isin(['vegetation','constructed'])].copy()
        z['within_target']=z.halfwidth_pp<=z.target_pp
        rr=[['Model','Geography','Extreme range (pp)','Factorial range (pp)','Within planned width'],['---','---','---:','---:','---:']]
        for (f,scope),g in z.groupby(['model','scope']):
            rg=lambda c: '–'.join(f'{x:.2f}' for x in (g[g.contrast==c].halfwidth_pp.min(),g[g.contrast==c].halfwidth_pp.max()))
            rr.append([f,scope,rg('extreme'),rg('factorial'),f'{g.within_target.sum()}/{len(g)}'])
        append('RQ2_PRECISION_REASSESSMENT',table(rr)+'\n\nRanges span both environmental domains and signed/absolute errors. Each denominator counts prespecified projections. The limits address planned precision and do not test for differential error.')
paired=base/'paired_development.csv'
if paired.is_file() and paired.stat().st_size>2:
    append('MULTIDIMENSIONAL_MEASUREMENT_VALIDITY',"""[Paired differences in tract MAE](../manifests/g6i/paired_development.csv) compare every completed dense pair on identical tracts, for each native class and aggregate. Leave-one-block ranges describe geographic sensitivity. They are not confidence intervals.""")
if (base/'tract_measurements.csv').is_file():
    dev_frame=pd.read_csv(base/'tract_measurements.csv')
    sources=dev_frame[dev_frame.model!='qwen_valid_windows'].drop_duplicates(['geoid','outcome'])
    sources=sources[~sources.outcome.isin(['vegetation','constructed'])]
    support=sources.groupby('outcome').reference_pp.agg(tracts='size',positive_tracts=lambda x:(x>0).sum(),median_share_pp='median')
    support.to_csv(base/'native_tract_support.csv')
    append('MULTIDIMENSIONAL_MEASUREMENT_VALIDITY','Of 53 development tracts, the reference includes rail in '+str(support.at['rail','positive_tracts'])+', bare soil in '+str(support.at['bare_soil','positive_tracts'])+' and water in '+str(support.at['water','positive_tracts'])+'. Large pixel counts for these classes coexist with few supporting neighborhoods. See [class support by tract](../manifests/g6i/native_tract_support.csv).')
if (base/'qwen_coverage.csv').exists():
    cov=pd.read_csv(base/'qwen_coverage.csv')
    complete=int((cov.valid_area==cov.total_area).sum())
    observed=int((cov.valid_area>0).sum())
    append('DECISION',f'Qwen returned some valid area in {observed}/53 tracts and the entire paired area in {complete}/53. '+('It can proceed for the complete-share estimand.' if complete==53 else 'The complete-tract VLM point-estimation gate remains closed. Failure rates and missing-area bounds are reportable.'))
    if complete<53:
        append('RQ2_PRECISION_REASSESSMENT','Full-area Qwen error variance and the corresponding primary RQ2 precision are unidentified from partially returned windows. Its failure bounds are retained. Applying the full-area weights to conditional observed-window errors would change the estimand.')
