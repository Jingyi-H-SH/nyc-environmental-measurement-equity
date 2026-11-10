"""Pack/unpack small source/tract receipts as portable sorted JSONL; no raster or model output."""
import gzip,json,re,sys
from pathlib import Path
from summarize import D,O
pack=O/'run'/'qualification.jsonl.gz'
def valid(k):return re.fullmatch(r'(?:[0-9]{11}|[0-9]{6}\.jp2)\.json',k)
def main(action):
    if action=='pack':
        files=sorted(D.glob('*.json'))
        assert len(files)==1154 and all(valid(f.name) for f in files)
        with pack.open('wb') as out,gzip.GzipFile(filename='',fileobj=out,mode='wb',mtime=0) as z:
            for f in files:z.write((json.dumps([f.name,json.loads(f.read_text())],separators=(',',':'))+'\n').encode())
    elif action=='unpack':
        D.mkdir(exist_ok=True); seen=set()
        with gzip.open(pack,'rt') as f:
            for line in f:
                k,v=json.loads(line);assert valid(k) and k not in seen;seen.add(k)
                p=D/k
                if p.exists():assert json.loads(p.read_text())==v
                else:p.write_text(json.dumps(v,allow_nan=False))
        assert len(seen)==1154
    else:raise ValueError(action)
if __name__=='__main__':main(sys.argv[1])
