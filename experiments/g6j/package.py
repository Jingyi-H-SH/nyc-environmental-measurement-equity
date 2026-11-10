"""Export only the NYC research materials into an empty standalone repository tree."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def export(out):
    if out.exists() and any(out.iterdir()):
        raise ValueError('destination must be empty')
    out.mkdir(exist_ok=True,parents=True)
    files=set()
    def add(*patterns):
        for pattern in patterns:
            paths=[p for p in Path('.').glob(pattern) if p.is_file() and not p.name.startswith('.')]
            if not paths:
                raise FileNotFoundError(pattern)
            files.update(paths)
    add('docs/G6_ENVIRONMENTAL_JUSTICE_SCIENTIFIC_FRAMEWORK.md','manifests/g6/source_fingerprints.json',
        'manifests/g6g/reserve8_roster.csv','manifests/g6g/frozen_proposal.json','manifests/g6g/nyc_service_metadata.json',
        'manifests/g6g/standardization_weights.csv','manifests/g6g/geometric_verification.csv',
        'manifests/g6h/*.csv','manifests/g6h/*.json','manifests/g6h/sources/archive_sources.json',
        'manifests/g6h/run/analysis_environment.json','manifests/g6h/run/planned.sqlite.gz','manifests/g6h/run/qualification.jsonl.gz',
        'manifests/g6i/*.csv','manifests/g6i/*.json','manifests/g6i/qwen_development_outputs.tar.gz',
        'manifests/g6i/prepared/*.json','manifests/g6i/run/*.sha','manifests/g6i/run/dino_access.json',
        'manifests/g6i/run/*environment.txt','manifests/g6i/run/qwen_official_revision.json',
        'manifests/g6i/run/runs/*/*.json','manifests/g6j/*.csv','manifests/g6j/release.json','manifests/g6j/secondary_design.json','manifests/g6d/social_frame.json','manifests/g6d/intersection_support.json','reports/G6_MULTIDIMENSIONAL_RQ3_DESIGN.md','experiments/g6a/checkpoints.json',
        'manifests/g6j/run/*.json','manifests/g6j/run/*.log','manifests/g6j/run/*.csv','manifests/g6j/run/formal.sha256',
        'manifests/g6j/run/results/*/*.json','manifests/g6j/run/inputs/*.json',
        'reports/G6G_RQ2_RQ3_ESTIMAND_FREEZE.md','reports/G6H_RGB_QUALIFICATION.md','reports/G6I_*.md','reports/G6J_*.md')
    for stage in ('g6g','g6h','g6i','g6j'):
        files.update(p for p in Path('experiments',stage).iterdir() if p.suffix in {'.py','.sh','.json','.md','.txt'})
    forbidden=re.compile(rb'(?:hf_[a-zA-Z0-9]{24,}|gh[pousr]_[a-zA-Z0-9]{26,}|BEGIN (?:OPENSSH |RSA )?PRIVATE KEY|https?://[^/\s]+:[^/\s]+@|/volume1/cloud/[A-Za-z0-9]{12,})')
    for src in sorted(files):
        if src.suffix not in {'.gz','.zip'} and forbidden.search(src.read_bytes()):
            raise ValueError('credential or private infrastructure pattern in '+str(src))
        dest=out/src
        dest.parent.mkdir(exist_ok=True,parents=True)
        shutil.copyfile(src,dest)
    (out/'README.md').write_text(
        '# Intersectional measurement equity in neighborhood physical environments\n\n'
        'A prospective spatial evaluation of eight NYC mapped land-cover classes, tract composition, intersectional measurement error and its effect on estimates of environmental inequality.\n\n'
        'Start with [scientific results](reports/G6J_FINAL_DECISION.md), [geographic estimands](reports/G6G_RQ2_RQ3_ESTIMAND_FREEZE.md) and [offline reproduction](experiments/g6j/README.md).\n\n'
        'The formal statistics can be regenerated from the supplied tract-level sufficient statistics without model downloads or paid compute. Verify the archive with `shasum -a 256 -c SHA256SUMS`. The checksums in prior stage receipts refer to the original full research archive and may name additional internal files. Provider-hosted imagery, model weights, optimizer states and account credentials are outside this Git distribution.\n')
    paths=sorted(p for p in out.rglob('*') if p.is_file())
    (out/'SHA256SUMS').write_text(''.join(digest(p)+'  '+str(p.relative_to(out))+'\n' for p in paths))
    print('exported',len(paths),'files')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('destination',type=Path)
    export(parser.parse_args().destination)
