"""Cloud-only, source planning, no model/prediction imports. Arguments: TIGER ZIP, reference TIFF, NEW output dir."""
import sys, csv, hashlib, math, json, sqlite3
from pathlib import Path
import rasterio
from rasterio.windows import Window, from_bounds
from rasterio.warp import transform_bounds
from rasterio.features import geometry_mask
from shapely import union_all
from shapely.geometry import box
from pyproj import Transformer
from shapely.ops import transform
from shapely.geometry import shape
import shapefile
web=Transformer.from_crs(3857,2263,always_xy=True).transform
def geoms(path):
    project=Transformer.from_crs(4269,2263,always_xy=True).transform
    return {s.record.GEOID:transform(project,shape(s.shape.__geo_interface__)) for s in shapefile.Reader(str(path)).iterShapeRecords() if s.record.COUNTYFP in ['005','047','061','081','085']}
def run(geom,ref,out):
    roster=Path('manifests/g6g/reserve8_roster.csv')
    assert hashlib.sha256(roster.read_bytes()).hexdigest()=='d480029349025da34db421f384745ce9f7303e88633c01ae71c214b24c71fc5e'
    assert hashlib.sha256(geom.read_bytes()).hexdigest()=='38043e7276be9bd05c6f95ed2e95e8783eeb086ca1fb2a88c3e2e6788019a566'
    out.mkdir(exist_ok=False); db=sqlite3.connect(out/'planned.sqlite')
    db.executescript('CREATE TABLE windows(id TEXT,split TEXT,x INT,y INT,PRIMARY KEY(id,x,y));CREATE TABLE tiles(split TEXT,r INT,c INT,PRIMARY KEY(split,r,c));')
    geog=geoms(geom); tile=json.loads(Path('manifests/g6g/nyc_service_metadata.json').read_text())['tileInfo']
    ox,oy=tile['origin']['x'],tile['origin']['y']; size=tile['cols']*next(v['resolution'] for v in tile['lods'] if v['level']==20)
    with rasterio.open(ref) as ds:
        assert ds.crs.to_epsg()==2263 and ds.res==(.5,.5) and ds.transform.b==ds.transform.d==0
        for row in csv.DictReader(roster.open()):
            split,gid=row['split'],row['geoid']
            if split not in ('train','dev','test'):continue
            g=geog[gid]; w=from_bounds(*g.bounds,transform=ds.transform)
            for y in range(math.floor(w.row_off),math.ceil(w.row_off+w.height),512):
                for x in range(math.floor(w.col_off),math.ceil(w.col_off+w.width),512):
                    win=Window(x,y,512,512)
                    if not geometry_mask([g],(512,512),ds.window_transform(win),invert=True).any():continue
                    l,b,r,t=transform_bounds(ds.crs,3857,*ds.window_bounds(win))
                    keys=[(split,i,j) for i in range(math.floor((oy-t)/size),math.floor((oy-b)/size)+1) for j in range(math.floor((l-ox)/size),math.floor((r-ox)/size)+1)]
                    db.execute('INSERT INTO windows VALUES (?,?,?,?)',(gid,split,x,y));db.executemany('INSERT OR IGNORE INTO tiles VALUES (?,?,?)',keys)
            db.commit()
    # Verify keys; union contiguous horizontal runs, not hundreds of thousands of individual tiles.
    from shapely.ops import transform
    import itertools
    areas={}
    for split in ('train','dev','test'):
        strips=[]
        for r,grp in itertools.groupby(db.execute('SELECT r,c FROM tiles WHERE split=? ORDER BY r,c',(split,)),lambda rc:rc[0]):
            for _,seq in itertools.groupby(enumerate([c for _,c in grp]),lambda kv:kv[1]-kv[0]):
                cs=[c for _,c in seq];strips.append(box(ox+cs[0]*size,oy-(r+1)*size,ox+(cs[-1]+1)*size,oy-r*size))
        from shapely import segmentize
        areas[split]=transform(web,segmentize(union_all(strips),size))
    dist={a+'_'+b:areas[a].distance(areas[b]) for a,b in [('train','dev'),('train','test'),('dev','test')]}
    overlap=db.execute('SELECT COUNT(*) FROM (SELECT r,c FROM tiles GROUP BY r,c HAVING COUNT(*)>1)').fetchone()[0]
    (out/'footprint.json').write_text(json.dumps(dict(planned_source_min_ft=dist,shared_keys=overlap,coverage_verified=False),indent=2))
    if overlap or min(dist.values())<3200:raise ValueError('source isolation failed; stop')
if __name__=='__main__':run(*map(Path,sys.argv[1:]))
