"""One-pass frozen dense census on authorized G6-J geography, with per-tract recovery."""
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

I=Path.home()/'work/jev-g6i-v1'
J=Path.home()/'work/jev-g6j-v1'
sys.path.insert(0,str(I))
from models import Dense


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


class PairedWindows(Dataset):
    def __init__(self, path):
        self.rows=[r for r in json.loads(path.read_text()) if r['n']]
        assert all(Path(r['path']).parent==Path('/tmp/g6i-reserve8/test')/path.stem and r['geoid']==path.stem for r in self.rows)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r=self.rows[i]
        path=Path(r['path'])
        assert sha(path)==r['sha256']
        a=np.load(path,allow_pickle=False)
        y=a[:,:,3].copy()
        x=a[:,:,:3].copy()
        x[y==0]=127
        assert (y>0).sum()==r['n']
        return torch.from_numpy(x.transpose(2,0,1)),torch.from_numpy(y)


def main():
    os.chdir(I)
    release=json.loads((J/'release.json').read_text())
    assert release['stage']=='G6-J' and release['released']
    for name in ('infer.py','prepare_inputs.py'):
        assert sha(J/name)==release['hashes']['experiments/g6j/'+name]
    assert sha(I/'models.py')==release['models_sha256']
    assert sha(J/'coverage.csv')==release['coverage_sha256']
    with (J/'coverage.csv').open() as f:
        expected={r['geoid']:json.loads(r['paired_class_counts'])[1:] for r in csv.DictReader(f)
                  if r['split']=='test' and r['eligible95']=='True'}
    assert len(expected)==265
    assert set(expected)=={p.stem for p in (J/'inputs').glob('*.json')}
    torch.set_num_threads(2)
    torch.backends.cudnn.benchmark=False
    for family,checkpoint_hash in release['families'].items():
        start=time.monotonic()
        checkpoint=I/'runs'/family/'checkpoint.pt'
        assert sha(checkpoint)==checkpoint_hash
        model=Dense(family).cuda()
        state=torch.load(checkpoint,map_location='cpu')
        assert state['passes']==8
        keys=model.load_state_dict(state['weights'],strict=family!='ijepa')
        assert not keys.unexpected_keys
        assert all(family=='ijepa' and k.startswith('model.') for k in keys.missing_keys)
        del state
        model.eval()
        folder=J/'results'/family
        folder.mkdir(parents=True,exist_ok=True)
        torch.cuda.reset_peak_memory_stats()
        windows=0
        with torch.inference_mode(),torch.autocast('cuda',torch.bfloat16):
            for i,(gid,counts) in enumerate(sorted(expected.items()),1):
                out=folder/(gid+'.json')
                inp=J/'inputs'/(gid+'.json')
                input_hash=sha(inp)
                if out.exists():
                    old=json.loads(out.read_text())
                    assert old['checkpoint']==checkpoint_hash and old['input']==input_hash
                    np.testing.assert_array_equal(np.sum(old['matrix'],axis=1),counts)
                    windows+=old['windows']
                    continue
                data=PairedWindows(inp)
                matrix=np.zeros((8,8),dtype='int64')
                for x,y in DataLoader(data,batch_size=8,num_workers=0):
                    logits=model(x.cuda().float()/255)
                    if not torch.isfinite(logits).all():
                        raise ValueError('non-finite dense prediction')
                    pred=logits.argmax(1)
                    ref=y.cuda().long()-1
                    valid=ref>=0
                    matrix+=torch.bincount((8*ref[valid]+pred[valid]),minlength=64).cpu().numpy().reshape(8,8)
                np.testing.assert_array_equal(matrix.sum(1),counts)
                tmp=out.with_suffix('.tmp')
                tmp.write_text(json.dumps(dict(checkpoint=checkpoint_hash,input=input_hash,windows=len(data),matrix=matrix.tolist())))
                tmp.replace(out)
                windows+=len(data)
                if i%25==0:print(family,i,'tracts',flush=True)
        assert len(list(folder.glob('*.json')))==265
        (J/(family+'-receipt.json')).write_text(json.dumps(dict(tracts=265,windows=windows,
            elapsed_seconds=time.monotonic()-start,peak_bytes=torch.cuda.max_memory_allocated(),checkpoint=checkpoint_hash)))
        del model
        torch.cuda.empty_cache()
        print(family,'COMPLETE',flush=True)


if __name__=='__main__':
    main()
