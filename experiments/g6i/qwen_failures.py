"""Describe failures without altering frozen predictions or recovering partial values."""
from collections import Counter
import json,math
from pathlib import Path

def reason(row):
    if row['shares'] is not None:
        return 'valid'
    try:
        values=json.loads(row['raw'].strip())
    except ValueError:
        return 'not_complete_bare_json'
    if not isinstance(values,list) or len(values)!=8:
        return 'wrong_structure'
    if any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=100 for x in values):
        return 'invalid_element'
    if abs(sum(values)-100)>1:
        return 'sum_out_of_tolerance'
    raise AssertionError('Stored invalid record passes frozen parser')

if __name__=='__main__':
    path=Path('runs/qwen')
    receipt=json.loads((path/'receipt.json').read_text())
    counts=Counter()
    area=Counter()
    for batch in sorted(path.glob('batch_*.json')):
        for row in json.loads(batch.read_text()):
            key=reason(row)
            counts[key]+=1
            area[key]+=row['area']
    assert sum(counts.values())==receipt['windows']
    print(json.dumps({'windows':dict(counts),'pixels':dict(area)},indent=2))
