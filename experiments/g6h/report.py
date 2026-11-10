"""Publish aggregate source qualification and planning projections. No model outcomes."""
from pathlib import Path
import json,numpy as np,pandas as pd
from summarize import read,O
R=Path('reports')
def table(df):
    lines=['| '+' | '.join(map(str,df.columns))+' |','| '+' | '.join('---' for _ in df.columns)+' |']
    return '\n'.join(lines+['| '+' | '.join(map(str,row))+' |' for row in df.itertuples(index=False,name=None)])
def put(name,s):(R/('G6H_'+name+'.md')).write_text(s+'\n')
def run():
    c=read(O/'coverage.csv');w=read(O/'qualified_weights.csv');p=read(O/'qualified_precision.csv');s=read(O/'qualified_support.csv')
    f=json.loads((O/'footprint.json').read_text());m=json.loads((O/'execution_receipt.json').read_text())
    sources=read(O/'source_files.csv');sect=read(O/'index_links.csv');bounds=read(O/'missing_area_bounds.csv')
    fixed=read(O/'weight_comparison.csv'); frozen_equal=fixed['_merge'].eq('both').all() and np.allclose(fixed.weight_frozen,fixed.weight_qualified,atol=1e-10)
    identical={k:bool(g["_merge"].eq("both").all() and np.allclose(g.weight_frozen,g.weight_qualified,atol=1e-10)) for k,g in fixed.groupby("scope")}
    cuts={k:json.loads(Path('manifests/g6d/intersection_support.json').read_text())['cuts'][k] for k in ['poverty','black']}
    z=c[c.eligible95];ev=z[z.split=='test'];fail=c[~c.eligible95];allproj=len(p)==12 and p.status.eq('PROJECTED').all()
    alt=read(O/'original_weight_sensitivity.csv'); primary=alt.query('scenario=="central"')
    ok=frozen_equal and primary.restricted_weight_halfwidth_pp.le(primary.target_pp).all() and allproj and p[p.scenario=='central'].meets_target.all() and s.blocks.min()>=2 and len(s)==16 and min(f['planned_source_min_ft'].values())>=3200 and f['shared_keys']==0
    decision='GO' if ok else 'CONDITIONAL'
    if not len(ev) or not len(z[z.split=='train']) or f['shared_keys'] or min(f['planned_source_min_ft'].values())<3200:decision='NO-GO'
    qualification=dict(design='reserve8',decision=decision,n_frozen=len(c),n_qualified=len(z),evaluation_frozen=267,evaluation_qualified=len(ev),raw_jp2_count=len(sources),frozen_weights_preserved=True,qualified_weights_identical_by_scope=identical,coverage_threshold=.95,assignment_changes=0,new_training=False,model_outcomes_read=False,estimates='planning only',coverage_manifest='coverage.csv',precision_manifest='qualified_precision.csv')
    (O/'gate.json').write_text(json.dumps(qualification,indent=2)+'\n')
    pct=lambda x:round(100*x,3)
    rows=[]
    for k,d in c.groupby('split'):
        rows.append([k,len(d),d.eligible95.sum(),d.block.nunique(),d[d.eligible95].block.nunique(),pct(d.paired.sum()/d.polygon.sum()),pct(d.paired_land.sum()/d.land.sum()),pct(d.paired_fraction.min()),pct(d.paired_land_fraction.min())])
    cohort=table(pd.DataFrame(rows,columns='split frozen qualify blocks qualified_blocks paired_polygon_% paired_land_% min_polygon_% min_land_%'.split()))
    loss=table(s[['split','scope','cell','n','blocks','effective_blocks']].round(2))
    runtime=(m['last_tract_utc']-m['source_start_utc'])/60;gb=sum(v['bytes'] for v in m['archives'].values())/1e9
    wall=(m['last_range_utc']-m['first_range_utc']);rate=gb*1000/wall
    proj=table(p[['scope','contrast','scenario','sd_pp','icc','halfwidth_pp','target_pp','meets_target']].round(5)) if allproj else table(p)
    chips=json.loads((O/'run'/'channel_check.json').read_text()); pairedchips=sum(x['best_order_one_based']==[1,2,3] for x in chips)
    iso=json.dumps({k:round(v,2) for k,v in f['planned_source_min_ft'].items()})
    put('RGB_QUALIFICATION',f"""# reserve8: observed raw-image and reference qualification
Decision for the RGB prerequisite: **{decision}**. Actual source archives, decoded files and raster overlays, on Featurize. No model predictions were generated or inspected.
    
{cohort}

The original historical pairing counts (5 train, 2 development, 0 evaluation) are an inventory of prior processing. All {len(c)} tracts intersect the official [NYC 2016 raw orthophoto index](https://data.cityofnewyork.us/City-Government/2016-Orthoimagery-Tile-Index/sms6-sm5p). The five official borough distributions supplied all {sources.image.nunique()} needed JP2s, verified by ZIP-member CRC and SHA-256 after acquisition. {len(sect)} tract/file links; three index county labels pointed to a different ZIP. File member names and embedded bounds, rather than county guesses, resolved them. Source ZIPs and masks are now cached in instance-local scratch; receipts are persistent and copied to the repository. Preexisting web-tile caches are distinct from these raw files. [Source provenance](../manifests/g6h/sources/archive_sources.json) · [Per-file receipts](../manifests/g6h/source_files.csv).

{int(c.polygon.sum()):,} polygon pixel centers; {int(c.decoded.sum()):,} inside decodable source footprints; {int(c.rgb.sum()):,} passed the conservative visible-pixel mask. {int(c.paired.sum()):,} paired mapped pixels and {int(c.paired_land.sum()):,} paired nonwater pixels. Each represents 0.25 ft². Outside the source footprint: {c.outside_index_ft2.sum():,.2f} ft². Inside a footprint but masked (including interpolation seams): {c.invalid_rgb_in_footprint_ft2.sum():,.2f} ft². Valid RGB over unmapped reference accounts for another {c.valid_rgb_but_unmapped_ft2.sum():,.2f} ft². These three mutually exclusive reasons sum to the unpaired polygon area; none denotes a failed download. [Loss by borough and intersectional cell](../manifests/g6h/missing_distribution.csv) · [Area missing by reference class](../manifests/g6h/class_coverage.csv). No requested member is unresolved. [Tract manifest with quadrant-specific losses](../manifests/g6h/coverage.csv); eight-class denominators and paired counts are retained per tract.

The [city acquisition metadata](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_AerialImagery.md) describe the 2016 product. For coverage we used bands 1–3, valid data masks, excluded RGB triplets of all zero or all 255 and required four valid neighbors on a single raw tile. Some valid very dark/bright pixels may be conservatively lost. Comparing training-side display chips against all band orderings gave the lowest color MAE for (1,2,3) in {pairedchips}/{len(chips)} chips; see [chip-level differences](../manifests/g6h/run/channel_check.json). Rendering differences make this a diagnostic, not a guarantee of radiometric equivalence to web tiles.

Frozen inclusion: paired mapped / all polygon pixels **and** paired nonwater / reference nonwater ≥0.95. Qualifying counts at joint 90%, 95%, 99%: {[(t,int((c[['paired_fraction','paired_land_fraction']].min(axis=1)>=t).sum())) for t in [.90,.95,.99]]}. The last thresholds are sensitivities, not new selections. Frozen records below the primary threshold: {', '.join(fail.geoid) or 'none'}. For each below-threshold tract, the two denominators can be inspected separately:

{table(fail[['geoid','split','cell','borough','paired_fraction','paired_land_fraction']].round(5))}

Independent checks compare all nine reference counts (unmapped and eight classes) against the original reference frame; no final errors were read.

No shared raw JP2 between splits and {f['shared_keys']} shared level-20 delivery tile keys. Minimum distances (feet) of planned buffered input tile envelopes: {iso}. The ~4,004 ft minimum is a tract-polygon distance, not a window distance. Blocks are partition-disjoint but neighboring blocks are not assumed statistically independent. See [execution receipt](../manifests/g6h/execution_receipt.json).

Featurize profile: {gb:.2f} GB downloaded (archive SHA-256s archived), {rate:.1f} MB/s average over transfer; {sources.bytes.sum()/1e9:.2f} GB of required compressed-in-JP2 members decoded; {m['mask_bytes']/1e9:.2f} GB mask cache; {m['decode_worker_seconds']/60:.1f} aggregate decode-worker minutes. {runtime:.1f} elapsed minutes from source inventory to last tract receipt, including debugging and acquisition; the concurrent window enumeration and final QA have separate timestamps. Cold reproduction: allow 30 GB additional scratch plus the existing 97.74 GB native reference data member and geometry, 7 decode workers and 4 overlapping tract workers, approximately {max(1,round(runtime/60*1.5,1))} hour(s) allowing network variability. The instance exposed 14 CPU cores and 60,262 MiB RAM. A [mid-decode snapshot](../manifests/g6h/run/resource_sample.txt) is included; it is not peak-memory telemetry. No CUDA workload. At the observed ¥3/instance-hour, source-to-tract elapsed allocation ≈¥{runtime/60*3:.2f}; this is not an invoice or the total cost of retaining the already running instance. No extra instance or storage was provisioned.""")
    put('INTERSECTIONAL_PRECISION_RECHECK',f"""# RQ2: qualified geography and projected precision
Frozen neighborhood-level poverty and non-Hispanic Black population-share cuts: {cuts}. Cell digits follow that order. These are tract composition, not person-level identities. Qualified support:
    
{loss}

{proj}

Half-widths in percentage points are planning projections for signed and absolute vegetation/constructed-share errors, not measured disparities or observed confidence intervals. Use equal tracts within cells; the common vegetation/constructed reference hull uses entropy weights matching both reference means. Qualified and frozen membership and weights agree by scope: {identical}. The 221-tract common-morphology cohort retains its original membership and weights; only the all-tract target loses two members. Independent spatial units are blocks; cells can share a block. Use the frozen covariance kernel (.35 correlation per 16,000 ft Manhattan distance), within-block ICC, and effective-block t multiplier. SD=5 pp/ICC=.25 is the G6-G central assumption. SD=8 pp repeats the earlier high-variance sensitivity; SD=6/ICC=.35 stresses both dispersion and clustering. Recomputing the hull or weights changes the target. As a separate sensitivity, retaining original relative weights among qualifying tracts gives the central projections below; this restriction need not preserve covariate balance. Neither calculation recovers errors on the original full cohort.

{table(primary[['scope','contrast','restricted_weight_halfwidth_pp','target_pp']].round(4))}

No sealed residual variance is available to certify the planning assumptions. [Full projections and break-even SDs](../manifests/g6h/qualified_precision.csv).""")
    put('COMMON_MEASUREMENT_VALIDITY',f"""# Measurement implications of observed coverage

RQ1: vegetation, constructed cover and all eight native classes remain distinct. Compare shares on identical mapped pixels. Tract-specific missing pixels, reference exclusions, water, and conservative mask/seam losses are recorded; they need not be random. 2016 imagery and 2017 reference are not contemporaneous. Decodability does not establish visibility under shadow, freedom from occlusion, radiometric fidelity, or the accuracy of the 2017 reference. Coverage alone cannot establish model accuracy or reliability.

RQ2: {len(ev)} evaluation tracts qualify on observed geography. The primary measurement-equity comparisons are neighborhood 11−00 and 11−10−01+00 error contrasts. Geographic replication, ACS uncertainty, variance sensitivity and common morphology remain necessary. Coverage differences are a possible measurement mechanism, not an observed equity finding.

RQ3: for identical weights and geography, AI-minus-reference distortion of a gap equals the corresponding signed measurement-error contrast. Do not extrapolate to excluded NYC geography or infer personal exposure. With a known full reference and unconstrained predictions in missing mapped pixels, the following are the **widths** of worst-case intervals from missing pixels alone (pp), not estimated effects:

{table(bounds[['scope','contrast','worst_case_span_pp']].round(3))}

On the **original** target, the further uncertainty from whole-tract exclusion is shown below. The total allows both full exclusion and uncovered pixels in retained tracts. Widths bound signed aggregate contrasts using the known reference and predictions bounded in [0,1]; they are not sampling intervals and do not apply to absolute error without further work.

{table(primary[['scope','contrast','whole_exclusion_span_pp','original_target_total_span_pp']].round(3))}

 Direction, ranking and size of inequality distortion require later authorized model predictions.""")
    put('MULTIFAMILY_DEVELOPMENT_RESULTS','''# Development status
Training and inference were not launched in this RGB qualification stage. No prospective checkpoint, development prediction, confusion matrix, or model ranking is claimed. Historical weights and the sealed evaluation outputs were not opened or changed.''')
    put('FINAL_EVALUATION_READINESS','''# Sealed evaluation stays closed
The coverage manifest is an input qualification artifact. It does not authorize final inference. The original historical 74 and all 483 prospective assignments are unchanged. Subsequent development must validate model interfaces and common-pixel estimands before formal evaluation. No model-performance filtering occurred.''')
    put('DECISION',f'''# RGB qualification: {decision}

{len(z)}/{len(c)} frozen tracts meet both coverage thresholds, including {len(ev)}/267 evaluation tracts. {('The observed support meets the frozen central precision rule.' if ok else 'The original full-cohort estimand is not fully observed at the frozen coverage standard. Eligible-cohort precision and the restricted original-weight sensitivity are reported separately; neither substitutes for validation of the full target.')} The unchanged 221-tract common-morphology target has a central projected extreme-contrast half-width of {p.query('scope=="balanced_hull" and scenario=="central" and contrast=="extreme"').halfwidth_pp.iloc[0]:.5f} pp (limit 3 pp); the stress assumptions fail this limit. Descriptive analysis on eligible paired geography is supported; confirmatory claims about the entire frozen evaluation population are not. This gate concerns the data prerequisite for studying intersectional measurement equity; it is neither evidence of a disparity nor authorization to open sealed results. No new training or design cycle was initiated.

[Actual RGB coverage and resource profile](G6H_RGB_QUALIFICATION.md) · [Primary precision scenarios](G6H_INTERSECTIONAL_PRECISION_RECHECK.md) · [RQ1–RQ3 interpretation](G6H_COMMON_MEASUREMENT_VALIDITY.md) · [Executable reproduction](../experiments/g6h/README.md)''')
if __name__=='__main__':run()
