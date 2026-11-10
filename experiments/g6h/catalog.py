"""Fetch central directories only; locate members citywide, independent of borough label."""
import io,zipfile,requests,os,csv,collections,json
from pathlib import Path
class Range(io.RawIOBase):
    def __init__(self,m):self.pos=0;self.m=m;self.s=requests.Session()
    def tell(self):return self.pos
    def seek(self,n,whence=0):
        self.pos=[0,self.pos,self.m['bytes']][whence]+n
        if self.pos<0:raise OSError()
        return self.pos
    def read(self,n=-1):
        end=self.m['bytes'] if n<0 else min(self.m['bytes'],self.pos+n)
        if end<=self.pos:return b''
        r=self.s.get(self.m['url'],headers={'If-Match':self.m['etag'],'Range':f'bytes={self.pos}-{end-1}'},timeout=45)
        assert r.status_code==206 and len(r.content)==end-self.pos
        self.pos=end;return r.content
def main():
    loc=collections.defaultdict(list)
    for b,m in json.loads(Path('archive_sources.json').read_text()).items():
        with zipfile.ZipFile(Range(m)) as z:
            for n in z.namelist():
                if n.lower().endswith('.jp2'):loc[Path(n).name.lower()].append(b)
    ix=list(csv.DictReader(open('index_links.csv')));allr={r['image']:r for r in ix}
    paths={k:(r['archive'] if r['archive'] in loc[k] else next(iter(loc[k]),None)) for k,r in allr.items()}
    Path('source_locations.json').write_text(json.dumps(paths,sort_keys=True))
    print('misfiled or absent:',[(k,r['archive'],paths[k]) for k,r in allr.items() if r['archive']!=paths[k]])
if __name__=='__main__':main()
