"""Issue one immutable release from complete G6-I receipts and spatial checks."""
from pathlib import Path
from datetime import datetime,timezone
import csv
import hashlib
import json
import sys

ROOT=Path('manifests/g6j')
I=Path('manifests/g6i')
H=Path('manifests/g6h')
CODE=Path('experiments/g6j')

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    receipt=load(I/'release_validation.json')
    assert all(receipt[f]['status']=='VERIFIED' for f in ('cnn','segformer','yolo','ijepa','qwen'))
    cover=list(csv.DictReader((I/'qwen_coverage.csv').open()))
    assert len(cover)==53 and sum(int(r['windows']) for r in cover)==6314
    if all(int(r['invalid_windows'])==0 for r in cover):
        raise RuntimeError('Qwen achieved complete development support: freeze separate exploratory share interface')
    footprint=load(H/'footprint.json')
    assert footprint['shared_keys']==0 and min(footprint['planned_source_min_ft'].values())>=3200
    links={}
    for row in csv.DictReader((H/'index_links.csv').open()):
        links.setdefault(row['split'],set()).add(row['image'])
    assert not any(links[a]&links[b] for a,b in [('train','dev'),('train','test'),('dev','test')])
    proj=list(csv.DictReader((I/'projected_precision.csv').open()))
    for family in ('cnn','segformer','yolo','ijepa'):
        primary=[r for r in proj if r['model']==family and r['outcome'] in ('vegetation','constructed')]
        assert len(primary)==16
        assert all((float(r['halfwidth_pp']) <= float(r['target_pp']))==(family!='ijepa') for r in primary)
    families={}
    for f in ('cnn','segformer','yolo','ijepa'):
        p=I/'run/runs'/f/'receipt.json'
        assert sha(p)==receipt[f]['receipt_sha256']
        families[f]=load(p)['checkpoint_sha256']
    paths=[CODE/name for name in ('infer.py','prepare_inputs.py','analyze.py','spatial.py','distribution.py','secondary.py','freeze.py')]
    paths+=list(map(Path,['reports/G6G_RQ2_RQ3_ESTIMAND_FREEZE.md','experiments/g6i/freeze.json',
        'manifests/g6g/reserve8_roster.csv','manifests/g6h/qualified_weights.csv','manifests/g6h/index_links.csv',
        'manifests/g6j/secondary_design.json','manifests/g6d/social_frame.json','manifests/g6d/intersection_support.json','reports/G6_MULTIDIMENSIONAL_RQ3_DESIGN.md','manifests/g6i/release_validation.json','manifests/g6i/sha256.json','manifests/g6h/footprint.json']))
    release=dict(stage='G6-J',released=True,formal=['cnn','segformer','yolo'],exploratory=['ijepa'],
        families=families,models_sha256=sha(Path('experiments/g6i/models.py')),coverage_sha256=sha(H/'coverage.csv'),
        qwen='incomplete valid share support on development; retained in G6-I only',
        dense_analysis='One pass, paired valid area, all eight classes. No checkpoint selection or test refitting.',
        targets='265 qualified, 221 common morphology, worst-case bounds for all 267',
        scope='NYC reserve8 geography; mapped reference and tract-level ecological contrasts',
        hashes={str(p):sha(p) for p in paths})
    out=ROOT/'release.json'
    if out.exists():
        previous=load(out)
        previous.pop('released_utc')
        assert release==previous
        return
    release['released_utc']=datetime.now(timezone.utc).isoformat()
    with out.open('x') as f:json.dump(release,f,indent=2)
if __name__=='__main__':main()
