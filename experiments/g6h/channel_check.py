"""Verify ambiguous JP2 channel metadata against the official 2016 display on training-side chips only."""
import zipfile,csv,json,itertools,io,math
from pathlib import Path
from collections import defaultdict
import numpy as np,requests,rasterio
from rasterio.io import MemoryFile
from rasterio.warp import reproject,Resampling
from rasterio.transform import from_origin
from PIL import Image
from pyproj import Transformer
from footprints import geoms
root=Path.home()/'work/jev-g6a'
def main():
    geo=geoms(root/'tl_2019_36_tract.zip'); ix=json.loads(Path('manifests/g6g/nyc_service_metadata.json').read_text())['tileInfo']
    ox,oy=ix['origin']['x'],ix['origin']['y'];res=next(v['resolution'] for v in ix['lods'] if v['level']==20);t=res*256
    chips=[]; rows=list(csv.DictReader(open('index_links.csv')))
    locations=json.loads(Path('source_locations.json').read_text())
    for r in rows:r['archive']=locations[r['image']]
    for b in sorted({r['archive'] for r in rows}):
        pp=Path('/tmp/g6h-ortho')/(b+'.zip')
        if not pp.exists():pp=pp.with_suffix('.snapshot')
        if not pp.exists():continue
        seen=set()
        with zipfile.ZipFile(pp) as z:
            names={Path(n).name:n for n in z.namelist()}
            for r in rows:
                if r['split']!='train' or r['archive']!=b or r['geoid'] in seen:continue
                p=geo[r['geoid']].representative_point()
                if not (int(r['xmin'])+200<p.x<int(r['xmax'])-200 and int(r['ymin'])+200<p.y<int(r['ymax'])-200):continue
                x,y=Transformer.from_crs(2263,3857,always_xy=True).transform(p.x,p.y);i=math.floor((oy-y)/t);j=math.floor((x-ox)/t)
                path=root/'g6e/tiles'/f'{i}_{j}.img'
                try:
                    url=f'https://tiles.arcgis.com/tiles/yG5s3afENB5iO9fj/arcgis/rest/services/NYC_Orthos_2016/MapServer/tile/20/{i}/{j}'
                    data=path.read_bytes() if path.exists() else requests.get(url,timeout=12).content
                    ref=np.asarray(Image.open(io.BytesIO(data)).convert('RGB')).astype(float)
                except (OSError,requests.RequestException):continue
                if ref.std()<8:continue
                with MemoryFile(z.read(names[r['image']])) as f,f.open() as ds:
                    ar=np.zeros((4,256,256),np.uint8)
                    for n in range(4):reproject(rasterio.band(ds,n+1),ar[n],dst_transform=from_origin(ox+j*t,oy-i*t,res,res),dst_crs='EPSG:3857',resampling=Resampling.bilinear)
                vv=ar.astype(float); mae=lambda order:float(abs(vv[list(order)].transpose(1,2,0)-ref).mean())
                ranking=sorted((mae(order),order) for order in itertools.permutations(range(4),3))
                chips.append(dict(archive=b,image=r['image'],tile=[i,j],best_order_one_based=[k+1 for k in ranking[0][1]],best_mae=ranking[0][0],runner_up_mae=ranking[1][0],rgb123_mae=mae([0,1,2])))
                seen.add(r['geoid'])
                if len(seen)>=2:break
    Path('channel_check.json').write_text(json.dumps(chips,indent=2))
if __name__=='__main__':main()
