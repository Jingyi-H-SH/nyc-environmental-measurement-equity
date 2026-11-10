"""Materialize previously qualified RGB/reference geography. No model access."""
import csv
import json
import os
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

H = Path.home() / 'work/jev-g6h-v1'
I = Path.home() / 'work/jev-g6i-v1'
J = Path.home() / 'work/jev-g6j-v1'
sys.path.insert(0, str(I))
import prepare as prep


def prepare_one(item):
    key, windows = item
    gid = key[1]
    receipt = J / 'inputs' / (gid + '.json')
    if receipt.exists():
        data=json.loads(receipt.read_text())
        if all(Path(r['path']).exists() and prep.sha(Path(r['path']))==r['sha256'] for r in data):
            return gid
    rows = prep.tract(item)
    counts = json.loads((H/'qualification'/(gid+'.json')).read_text())['paired_class_counts']
    assert sum(r['n'] for r in rows) == sum(counts[1:])
    tmp = receipt.with_suffix('.tmp')
    tmp.write_text(json.dumps(rows))
    tmp.replace(receipt)
    return gid


def main():
    assert sys.platform.startswith('linux')
    (J / 'inputs').mkdir(parents=True, exist_ok=True)
    roster=H/'manifests/g6g/reserve8_roster.csv'
    assert prep.sha(roster)=='d480029349025da34db421f384745ce9f7303e88633c01ae71c214b24c71fc5e'
    with roster.open() as f:
        assigned={r['geoid'] for r in csv.DictReader(f) if r['split']=='test'}
    with (J/'coverage.csv').open() as f:
        coverage=[r for r in csv.DictReader(f) if r['split']=='test']
    assert {r['geoid'] for r in coverage}==assigned and len(assigned)==267
    ids={r['geoid'] for r in coverage if r['eligible95']=='True'}
    assert len(ids)==265
    db=H/'footprints-v1/planned.sqlite'
    assert prep.sha(db)=='2f89b66d0a393a9035257745feeea943ba8121ff75a63a57c95122022c3ce58a'
    prep.G=prep.geoms(Path.home()/'work/jev-g6a/tl_2019_36_tract.zip')
    prep.LINKS={}
    with (H/'index_links.csv').open() as f:
        for row in csv.DictReader(f):
            if row['geoid'] in ids:
                assert row['split']=='test'
                prep.LINKS.setdefault(row['geoid'],[]).append(row)
    groups={}
    with sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True) as conn:
        for gid,x,y in conn.execute("SELECT id,x,y FROM windows WHERE split='test' ORDER BY id,x,y"):
            if gid in ids:
                groups.setdefault(('test',gid),[]).append(dict(geoid=gid,x=x,y=y))
    assert {g for _,g in groups}==ids
    names=sorted({r['image'] for rows in prep.LINKS.values() for r in rows})
    remaining=sum(not (prep.S/(n+'.npy')).exists() for n in names)*75_000_000
    remaining+=sum(len(rs)*1_050_000 for (_,g),rs in groups.items() if not (J/'inputs'/(g+'.json')).exists())
    fs=os.statvfs(prep.S)
    assert remaining+5_000_000_000 < fs.f_bavail*fs.f_frsize,(remaining,fs.f_bavail*fs.f_frsize)
    print('tracts, windows, unique tiles, projected bytes',len(ids),sum(map(len,groups.values())),len(names),remaining,flush=True)
    with ProcessPoolExecutor(4) as pool:
        list(pool.map(prep.tile,names))
    with ProcessPoolExecutor(4) as pool:
        for n,gid in enumerate(pool.map(prepare_one,groups.items()),1):
            if n%25==0:print('prepared',n,flush=True)
    print('COMPLETE',len(groups),flush=True)


if __name__=='__main__':
    main()
