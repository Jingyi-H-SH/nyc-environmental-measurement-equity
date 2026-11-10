"""Pair valid share outputs to their exact reference area, tracking abstentions."""
import json
from pathlib import Path
import numpy as np

def reduce():
    out=Path('runs/qwen')
    assert (out/'receipt.json').is_file()
    rows=json.loads(Path('prepared/dev.json').read_text())
    index={(r['geoid'],r['x'],r['y']):r for r in rows if r['n']}
    result={};observed=set()
    dense=[p.parent for p in Path('runs').glob('*/tract_confusion.json')]
    matched={f.name:{} for f in dense}
    for path in sorted(out.glob('batch_*.json')):
        for pred in json.loads(path.read_text()):
            key=(pred['geoid'],pred['x'],pred['y'])
            assert key in index and key not in observed
            observed.add(key)
            rec=index[key]
            n=rec['n']
            assert n==pred['area']
            a=result.setdefault(key[0],dict(area=0,valid=0,windows=0,failed=0,
                                            pred=np.zeros(8),ref=np.zeros(8),full_ref=np.zeros(8)))
            ref=np.bincount(np.load(rec['path'])[:,:,3].ravel(),minlength=9)[1:]
            assert ref.sum()==n
            a['area']+=n
            a['windows']+=1
            a['full_ref']+=ref
            if pred['shares'] is None:
                a['failed']+=1
                continue
            a['pred']+=n*np.array(pred['shares'])/100
            a['ref']+=ref
            a['valid']+=n
            for f in dense:
                path=f/'predictions'/key[0]/f'{key[1]}_{key[2]}.npz'
                with np.load(path) as blob:counts=np.bincount(blob['labels'].ravel(),minlength=9)[1:]
                assert counts.sum()==n
                matched[f.name].setdefault(key[0],np.zeros(8,dtype=np.int64))
                matched[f.name][key[0]]+=counts
    assert set(index)==observed and len(result)==53
    for a in result.values():
        for k in ('pred','ref','full_ref'):a[k]=a[k].tolist()
    (out/'matched_dense_counts.json').write_text(json.dumps({f:{k:v.tolist() for k,v in a.items()} for f,a in matched.items()}))
    (out/'tract_shares.json').write_text(json.dumps(result))
if __name__=='__main__':reduce()
