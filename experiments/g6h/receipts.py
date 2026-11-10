"""Report actual cloud resources, integrity and footprint after source/tract jobs finish."""
import json,sqlite3,hashlib,sys,platform,os
from pathlib import Path
from importlib.metadata import version
import rasterio
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    base=Path('/tmp/g6h-ortho');sources=json.loads(Path('archive_sources.json').read_text())
    archives={b:dict(bytes=(base/(b+'.zip')).stat().st_size,sha256=sha(base/(b+'.zip'))) for b in sources}
    assert all(v['bytes']==sources[b]['bytes'] for b,v in archives.items())
    tids=list(Path('qualification').glob('*.jp2.json'));rr=[p for p in Path('qualification').glob('*.json') if p not in set(tids)]
    assert len(tids)==671 and len(rr)==483
    meta=dict(versions={k:version(k) for k in ['numpy','rasterio','pyproj','pyshp','shapely','requests','Pillow']},python=sys.version,gdal=rasterio.__gdal_version__,platform=platform.platform(),archives=archives,
           mask_bytes=sum(p.stat().st_size for p in (base/'masks').glob('*.npy')),decode_worker_seconds=sum(json.loads(p.read_text())['seconds'] for p in tids),
           source_start_utc=Path('acquire.log').stat().st_ctime,first_range_utc=min(p.stat().st_mtime for p in base.glob('*.ok')),last_range_utc=max(p.stat().st_mtime for p in base.glob('*.ok')),last_tract_utc=max(p.stat().st_mtime for p in rr))
    # ctime of a growing log is not a start time. Supply first durable metadata receipt instead.
    meta['source_start_utc']=Path('archive_sources.json').stat().st_mtime
    db=sqlite3.connect('file:footprints-v1/planned.sqlite?mode=ro',uri=True)
    meta['windows']=[list(r) for r in db.execute('select split,count(*),count(distinct id) from windows group by split')]
    meta['display_keys']=[list(r) for r in db.execute('select split,count(*) from tiles group by split')]
    meta['planned_sqlite_sha256']=sha(Path('footprints-v1/planned.sqlite'))
    Path('execution_receipt.json').write_text(json.dumps(meta,indent=2))
if __name__=='__main__':main()
