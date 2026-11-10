"""One independent contingency: Maryland, 2013 paired Chesapeake Conservancy / NAIP release.
Only design metadata and one 64 KiB GeoTIFF header per asset are requested.
"""
import argparse,csv,hashlib,io,json,zipfile,struct
from pathlib import Path
from urllib.request import Request,urlopen
import numpy as np
import pandas as pd
import shapefile,shapely,tifffile
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
from shapely.strtree import STRtree
ROOT='https://storage.googleapis.com/public-datasets-lila/lcmcvpr2019/cvpr_chesapeake_landcover/'
CENSUS='https://www2.census.gov/'
SUMMARY=CENSUS+'programs-surveys/acs/summary_file/2013/data/5_year_seq_by_state/Maryland/Tracts_Block_Groups_Only/'
def verify(cache,out):
    cache.mkdir(exist_ok=True,parents=True)
    sources={'tracts.zip':CENSUS+'geo/tiger/TIGER2013/TRACT/tl_2013_24_tract.zip','index.json':ROOT+'spatial_index.geojson','lookup':CENSUS+'programs-surveys/acs/summary_file/2013/documentation/user_tools/ACS_5yr_Seq_Table_Number_Lookup.txt'}
    for f in ['20135md0005000.zip','20135md0048000.zip','g20135md.csv']:sources[f]=SUMMARY+f
    for f,u in sources.items():
        if not (cache/f).exists():(cache/f).write_bytes(urlopen(u,timeout=40).read())
    estimates={}
    for seq,cols in [(5,[37,40]),(48,[6,7])]:
        z=zipfile.ZipFile(cache/f'20135md{seq:04}000.zip')
        r=csv.reader(io.TextIOWrapper(z.open(next(s for s in z.namelist() if s.startswith('e'))),encoding='latin1'))
        estimates[seq]={row[5]:[float(row[i]) for i in cols] for row in r if all(row[i].isdigit() for i in cols)}
    demographics={}
    for r in csv.reader((cache/'g20135md.csv').open(encoding='latin1')):
        if r[2:4]!=['140','00'] or r[4] not in estimates[5] or r[4] not in estimates[48]:continue
        total,black=estimates[5][r[4]];universe,poor=estimates[48][r[4]]
        if total and universe:demographics[r[9]+r[10]+r[13]]=(poor/universe,black/total)
    med=np.median(list(demographics.values()),axis=0)
    features=[f for f in json.loads((cache/'index.json').read_text())['features'] if f['properties']['split']=='md-train']
    g=[shape(f['geometry']) for f in features];tree=STRtree(g);union=shapely.union_all(g)
    project=Transformer.from_crs(4269,3857,always_xy=True).transform
    rows=[]
    for r in shapefile.Reader(str(cache/'tracts.zip')).iterShapeRecords():
        gid=r.record['GEOID']
        if gid not in demographics:continue
        poly=transform(project,shape(r.shape.__geo_interface__))
        inds=tree.query(poly,predicate='intersects')
        candidates=[int(i) for i in inds if g[i].covers(poly)]
        pov,black=demographics[gid]
        rows.append(dict(geoid=gid,poverty=pov,black=black,cell=f'{int(pov>=med[0])}{int(black>=med[1])}',tile='|'.join(features[i]['properties']['lc'] for i in candidates),whole_union=union.covers(poly),touching=len(inds)))
    d=pd.DataFrame(rows);d.to_csv(out/'maryland_frame.csv',index=False)
    ex=next((f for f in features if f['properties']['lc'] in set(d.tile)),features[0])
    headers={}
    for k in ['naip-new','lc']:
        u=ROOT+ex['properties'][k]
        with urlopen(Request(u,headers={'Range':'bytes=0-65535'}),timeout=35) as resp:
            assert resp.status==206
            b=resp.read(65536)
        # Some source TIFFs put their first IFD at EOF; retrieve a bounded suffix.
        endian='<' if b[:2]==b'II' else '>'
        ifd=struct.unpack(endian+'I',b[4:8])[0]
        with io.BytesIO() as sparse:
            sparse.write(b)
            if ifd>=len(b):
                with urlopen(Request(u,headers={'Range':f'bytes={ifd}-'}),timeout=35) as resp:
                    assert resp.status==206
                    suffix=resp.read(262145)
                assert len(suffix)<=262144
                sparse.seek(ifd);sparse.write(suffix)
            sparse.seek(0)
            tif=tifffile.TiffFile(sparse)
            page=tif.pages[0]
            headers[k]=dict(url=u,first_65536_sha256=hashlib.sha256(b).hexdigest(),shape=page.shape,dtype=str(page.dtype),scale=page.tags['ModelPixelScaleTag'].value,tiepoint=page.tags['ModelTiepointTag'].value,geokeys=page.tags['GeoKeyDirectoryTag'].value)
    assert headers['naip-new']['shape'][:2]==headers['lc']['shape'][:2] and all(headers['naip-new'][k]==headers['lc'][k] for k in ['scale','tiepoint','geokeys'])
    result=dict(sources={f:{'url':u,'sha256':hashlib.sha256((cache/f).read_bytes()).hexdigest()} for f,u in sources.items()},headers=headers,cutpoints=med.tolist(),n=len(d),tiles=len(features),whole_cells=d[d.whole_union].cell.value_counts().to_dict(),single_tile_clusters=d[d.tile!=''].groupby('cell').tile.nunique().to_dict(),baltimore_touching=int(((d.geoid.str.startswith('24510'))&(d.touching>0)).sum()))
    (out/'maryland_verification.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('cache',type=Path);verify(p.parse_args().cache,Path('manifests/g6g'))
