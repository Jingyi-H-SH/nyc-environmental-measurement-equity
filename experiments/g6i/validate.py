"""Verify completion receipts against the frozen window identities and release digests."""
import json
from pathlib import Path
import hashlib
import tarfile

root=Path('manifests/g6i')
runs=root/'run/runs'
def load(path):
    return json.loads(path.read_text())
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    train=load(root/'prepared/train.json')
    dev=load(root/'prepared/dev.json')
    assert len(train)==5196 and all(r['n']>0 for r in train)
    assert len(dev)==6314 and all(r['n']>0 for r in dev)
    assert len({r['geoid'] for r in train})==163
    assert len({r['geoid'] for r in dev})==53
    assert not {r['geoid'] for r in dev}&{r['geoid'] for r in train}
    expected={f"predictions/{r['geoid']}/{r['x']}_{r['y']}.npz" for r in dev}
    assert len(expected)==len(dev)
    result={}
    for f in ['cnn','segformer','yolo','ijepa','qwen']:
        folder=runs/f
        receipt=folder/'receipt.json'
        if not receipt.is_file():
            result[f]={'status':'NO_COMPLETION_RECEIPT'}
            continue
        rec=load(receipt)
        hashes=load(folder/'sha256.json')
        config=load(folder/'config.json')
        for key in ['config.json','receipt.json']:
            assert hashes[key]==digest(folder/key),(f,key)
        if f=='qwen':
            batches={f'batch_{i:05}.json' for i in range(0,len(dev),4)}
            assert batches=={k for k in hashes if k.startswith('batch_')}
            with tarfile.open(root/'qwen_development_outputs.tar.gz','r:gz') as archive:
                names=archive.getnames()
                assert len(names)==len(batches) and set(names)==batches
                ordered=[]
                for name in sorted(names):
                    raw=archive.extractfile(name).read()
                    assert hashlib.sha256(raw).hexdigest()==hashes[name],name
                    ordered.extend((r['geoid'],r['x'],r['y'],r['area']) for r in json.loads(raw))
                assert ordered==[(r['geoid'],r['x'],r['y'],r['n']) for r in dev]
            assert rec['windows']==len(dev)
            assert config['dev_sha256']==digest(root/'prepared/dev.json')
            assert config['code_sha256']==digest(Path('experiments/g6i/qwen.py'))
            for key in ['tract_shares.json','matched_dense_counts.json']:
                assert hashes[key]==digest(folder/key)
        else:
            assert hashes['checkpoint.pt']==rec['checkpoint_sha256']
            assert expected=={k for k in hashes if k.startswith('predictions/')}
            assert hashes['tract_confusion.json']==digest(folder/'tract_confusion.json')
            for key,value in config['identity'].items():
                local=(root/key if key.startswith('prepared/') else Path('experiments/g6i')/key)
                assert digest(local)==value,(f,key)
            assert rec['dev_windows']==len(dev) and rec['passes']*rec['steps_per_pass']==5200
        result[f]={'status':'VERIFIED','receipt_sha256':digest(receipt),'file_manifest_sha256':digest(folder/'sha256.json')}
    (root/'release_validation.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
