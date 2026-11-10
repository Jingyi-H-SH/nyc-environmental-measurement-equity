"""Run on Featurize in stage directory. Intersect the official raw NYC index, no outcome reads."""
import csv, hashlib, zipfile
from pathlib import Path
from footprints import geoms
from pyproj import CRS
import shapefile
from shapely.geometry import shape
from shapely import STRtree
root=Path.home()/'work/jev-g6a'
def run():
    p=Path('index.zip'); assert hashlib.sha256(p.read_bytes()).hexdigest()=='f8e6439b08e61ee217feec97acb0842c79e6856a7f5d70aad04c51319b0aeea6'
    with zipfile.ZipFile(p) as z:assert CRS.from_wkt(z.read(next(n for n in z.namelist() if n.endswith('.prj'))).decode()).to_epsg()==2263
    ix=list(shapefile.Reader(str(p)).iterShapeRecords()); gg=[shape(i.shape.__geo_interface__) for i in ix];tree=STRtree(gg)
    tr=geoms(root/'tl_2019_36_tract.zip')
    with open('index_links.csv','w') as f:
        w=csv.writer(f);w.writerow('geoid split archive image xmin ymin xmax ymax intersection_ft2'.split())
        for r in csv.DictReader(open('manifests/g6g/reserve8_roster.csv')):
            if r['split']=='excluded':continue
            g=tr[r['geoid']]
            for i in sorted(tree.query(g)):
                a=g.intersection(gg[i]).area
                if a<=1e-5:continue
                t=ix[i].record;b={'Richmond':'staten_island','Kings':'brooklyn','New York':'manhattan'}.get(t.COUNTY,t.COUNTY.lower())
                w.writerow([r['geoid'],r['split'],b,t.IMAGE,t.XMIN,t.YMIN,t.XMAX,t.YMAX,a])
if __name__=='__main__':run()
